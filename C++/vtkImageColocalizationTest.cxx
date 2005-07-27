/*=========================================================================

  Program:   BioImageXD
  Module:    $RCSfile: vtkImageColocalizationTest.cxx,v $

 Copyright (C) 2005  BioImageXD Project
 See CREDITS.txt for details

 This program is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program; if not, write to the Free Software
 Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA


=========================================================================*/
#include "vtkImageColocalizationTest.h"

#include "vtkImageData.h"
#include "vtkObjectFactory.h"
#include "vtkImageProgressIterator.h"
#include "vtkPointData.h"
#include "vtkImageGaussianSmooth.h"
#include "vtkMath.h"
#include "vtkExtractVOI.h"
#include "vtkPNGWriter.h"

#define GET_AT(x,y,z,ptr) *(ptr+(z)*inIncZ+(y)*inIncY+(x)*inIncX)
#define SET_AT(x,y,z,ptr,val) *(ptr+(z)*outIncZ+(y)*outIncY+(x)*outIncX)=val
#define SET_AT_COMP(x,y,z,c,ptr,val) *(ptr+(int)((z)*outIncZ)+(int)((y)*outIncY)+(int)((x)*outIncX)+(c))=val
#define GET_AT_OUT(x,y,z,ptr) *(ptr+(z)*outIncZ+(y)*outIncY+(x)*outIncX)
#define SET_AT_OUT(x,y,z,ptr,val) *(ptr+(z)*outIncZ+(y)*outIncY+(x)*outIncX)=val



vtkCxxRevisionMacro(vtkImageColocalizationTest, "$Revision: 1.25 $");
vtkStandardNewMacro(vtkImageColocalizationTest);

//----------------------------------------------------------------------------
vtkImageColocalizationTest::vtkImageColocalizationTest()
{
	RandomizeZ = false;
	IgnoreZeroPixels = true;
	Smooth = true;
	ManualPSFSize = 0;
	NumIterations = 0;
	Ch2Lambda = 520;
	NumericalAperture = 1.4;
	PixelSize = 0.10;
  CurrentSlice = -1;
}


//----------------------------------------------------------------------------
vtkImageColocalizationTest::~vtkImageColocalizationTest()
{
}


//----------------------------------------------------------------------------
void vtkImageColocalizationTest::
ExecuteInformation(vtkImageData ** inputs, vtkImageData * output)
{
	vtkImageMultipleInputFilter::ExecuteInformation(inputs, output);
}



//----------------------------------------------------------------------------
// This templated function executes the filter for any type of data.
template < class T >
    void
    vtkImageColocalizationTestExecute
    (vtkImageColocalizationTest * self, int id,
     int NumberOfInputs, vtkImageData ** inData, vtkImageData * outData,
     int outExt[6], T *) {
	int inIncX, inIncY, inIncZ;
	int outIncX, outIncY, outIncZ;
	int maxX, maxY, maxZ;
	int idxX, idxY, idxZ;
  T* outPtr;
         
 bool Costes = false;
 bool Fay = false; 
 bool vanS = false;
 bool rBlocks= false;
 bool randZ = self->GetRandomizeZ();
// printf("Randomizing in Z: %s\n",randZ?"yes":"no");
         
    
  if(self->GetMethod()==0) Fay = true;
  if(self->GetMethod()==1) Costes = true;      
  if(self->GetMethod()==2) vanS = true;
  //printf("Using Fay: %s\n",Fay?"yes":"no");
  //printf("Using Costes: %s\n",Costes?"yes":"no");
  //printf("Using van Steensel: %s\n",vanS?"yes":"no");
  if(!Fay&&!Costes&&!vanS) {
    vtkErrorWithObjectMacro(self,<<"No randomisation method selected!");
  }
  maxX = outExt[1] - outExt[0];
  maxY = outExt[3] - outExt[2];
  maxZ = outExt[5] - outExt[4];
	inData[0]->GetIncrements(inIncX, inIncY, inIncZ);
	outData->GetIncrements(outIncX, outIncY,outIncZ);
  
  vtkImageData* outbuf = vtkImageData::New();
  outbuf->SetExtent(outData->GetExtent());
  outbuf->SetScalarType(outData->GetScalarType());
  outbuf->AllocateScalars();
  
  
  outPtr = (T *) outbuf->GetScalarPointer();
	int width = maxX;
	int height = maxY;

	int currentSliceNo = self->GetCurrentSlice();

  bool ignoreZeroZero = self->GetIgnoreZeroPixels();
  
  int rwidth, rheight, xOffset, yOffset, mask;
  double psf = 0;
  double pearsons1 = 0;
	double pearsons2 = 0;
	double pearsons3 = 0;
	double r2 = 1;
	double r = 1;
	double ch1Max = 0;
	double ch1Min = 255;
	double ch2Max = 0;
	double ch2Min = 255;
	int nslices = maxZ;
	int ch1, ch2, count;
	double sumX = 0;
	double sumXY = 0;
	double sumXX = 0;
	double sumYY = 0;
	double sumY = 0;
	double sumXtotal = 0;
	double sumYtotal = 0;
	double colocX = 0;
	double colocY = 0;
	int N = 0;
	int N2 = 0;
	double r2min = 1;
	double r2max = -1;
	sumX = 0;
	sumXY = 0;
	sumXX = 0;
	sumYY = 0;
	sumY = 0;
	int i = 1;
	double coloc2M1 = 0;
	double coloc2M2 = 0;
	int colocCount = 0;
	int colocCount1 = 0;
	int colocCount2 = 0;
	double r2sd = 0;
	double sumr2sqrd = 0;
	double sumr2 = 0;
	double ICQ2mean = 0;
	double sumICQ2sqrd = 0;
	double sumICQ2 = 0;
	double ICQobs = 0;
	int countICQ = 0;
	int Nr = 0;
	int Ng = 0;
  char progressText[300];  
  psf = (0.61*self->GetCh2Lambda())/self->GetNumericalAperture();
	psf = (psf)/(self->GetPixelSize()*1000);
	if (self->GetManualPSFSize()) psf = self->GetManualPSFSize();
  //printf("psf = %f\n",psf);
    
  int iterations = self->GetNumIterations();
 
  xOffset = 0;
	yOffset = 0;
	rwidth = width;
	rheight = height;
	
	int g1 = 0;
	int g2 = 0;
	int histCount = 0;

//  printf("Acuiring inpointers\n");
  T* inPtr1 = (T *) inData[0]->GetScalarPointer();
  T* inPtr2 = (T *) inData[1]->GetScalarPointer();
  
//calulate pearsons for existing image;
  //printf("Calculate Pearson's correlation for existing images\n");
  //printf("nslices=%d, rheight = %d, rwidth = %d\n",nslices,rheight,rwidth);
	for (int s = 0; s < nslices; s++) {
		if (currentSliceNo>=0) {
		    //printf("Only for slice %d\n",currentSliceNo);
			s = currentSliceNo;
			nslices = s;
		}
		for (int y = 0; y < rheight; y++) {
			//printf("Calculating r for original images.");
			for (int x = 0; x < rwidth; x++) {
					ch1 = (int)GET_AT(x+xOffset,y+yOffset,s,inPtr1);
					ch2 = (int)GET_AT(x+xOffset,y+yOffset,s,inPtr2);
					if (ch1Max < ch1)
						ch1Max = ch1;
					if (ch1Min > ch1)
						ch1Min = ch1;
					if (ch2Max < ch2)
						ch2Max = ch2;
					if (ch2Min > ch2)
						ch2Min = ch2;
					N++;
					if (ch1 + ch2 != 0)
						N2++;
					sumXtotal += ch1;
					sumYtotal += ch2;
					if (ch2 > 0)
						colocX += ch1;
					if (ch1 > 0)
						colocY += ch2;
					sumX += ch1;
					sumXY += (ch1 * ch2);
					sumXX += (ch1 * ch1);
					sumYY += (ch2 * ch2);
					sumY += ch2;
					if (ch1 > 0)
						Nr++;
					if (ch2 > 0)
						Ng++;

			}
		}
	}

	if (ignoreZeroZero)
		N = N2;
	//N = N2;
	//double ch1Mean = sumX/Nr;
	//double ch2Mean = sumY/Ng;
	double ch1Mean = sumX / N;
	double ch2Mean = sumY / N;
  //printf("Ch1: %f Ch2: %f\nCount NonZeroZero: %d\n",ch1Mean,ch2Mean,N);
  pearsons1 = sumXY - (sumX * sumY / N);
	pearsons2 = sumXX - (sumX * sumX / N);
	pearsons3 = sumYY - (sumY * sumY / N);
	//IJ.showMessage("p1: "+pearsons1+"    p2: "+pearsons2+"     p3: "+pearsons3);
  //printf("Pearson's p1=%f, p2=%f, p3=%f\n",pearsons1,pearsons2,pearsons3);
	r = pearsons1 / (sqrt(pearsons2 * pearsons3));
  //printf("R=%f\n",r);
	double colocM1 = (double) (colocX / sumXtotal);
	double colocM2 = (double) (colocY / sumYtotal);

//calucalte ICQ
	int countAll = 0;
	int countPos = 0;
	double PDMobs = 0;
	double PDM = 0;
	double ICQ2;
	int countAll2 = 0;
  inPtr1 = (T *) inData[0]->GetScalarPointerForExtent(outExt);
  inPtr2 = (T *) inData[1]->GetScalarPointerForExtent(outExt);

	for (int s = 0; s < nslices; s++) {
		if (currentSliceNo>=0) {
     // printf("Only for slice %d\n",currentSliceNo);            
			s = currentSliceNo;
			nslices = s;
		}
		for (int y = 0; y <= rheight; y++) {
       //printf("Calculating r for original images.");

			for (int x = 0; x <= rwidth; x++) {
				mask = 1;
				if (mask != 0) {
					ch1 = (int)GET_AT(x+xOffset,y+yOffset,s,inPtr1);
					ch2 = (int)GET_AT(x+xOffset,y+yOffset,s,inPtr2);
                    
					if (ch1 + ch2 != 0) {
						PDMobs =
						    ((double) ch1 - (double)ch1Mean) *
						    ((double) ch2 - (double)ch2Mean);
						if (PDMobs > 0)
							countPos++;
						countAll2++;
					}

				}
			}
		}
	}
 // printf("count+=%d CountNonZeropair=%d\n",countPos,countAll2);
	ICQobs = ((double) countPos / (double) countAll2) - 0.5;
	bool ch3found = false;
	//do random localisations
	int rx = 0;
	int ry = 0;
	int rz = 0;
	int ch3;
  vtkImageGaussianSmooth* gb = vtkImageGaussianSmooth::New();
  vtkExtractVOI* extract=vtkExtractVOI::New();
	
	double r2mean = 0;
	int slicesDone = 0;
	int xCount = 0;
	int xOffset2 = -15;
	int yOffset2 = -10;
	int zOffset2 = 0;
	int startSlice = 0;

	if (Costes) {
		xOffset2 = 0;
		yOffset2 = 0;
	}
	if (Fay)
		iterations = 25;
	if (nslices >= 1 && Fay)
		zOffset2 = -1;

	if (Fay && nslices >= 1) {
		startSlice = 1;
		nslices -= 1;
		iterations = 75;
	}

	if (vanS) {
		xOffset2 = -21;
		startSlice = 0;
		iterations = 41;
	}

	int blockNumberX = (int) (width / (psf * 2));
	int blockNumberY = (int) (height / (psf * 2));

	double vSx[41];
	double vSr[41];
	int ch4 = 0;
	int zUsed[nslices];
//stackRand = new ImageStack(rwidth,rheight);
	int blockCount = 0;
	bool rBlock = true;
	int vacant;
  int copyIteration = (int)vtkMath::Random(1,iterations);
  //printf("Copying at iteration %d\n",copyIteration);
//start randomisations and calculation or Rrands

	for (int c = 1; c <= iterations; c++) {
    self->UpdateProgress(float(c)/iterations);
    sprintf(progressText,"Calculating P-Value (iteration %d / %d)",c,iterations);
    self->SetProgressText(progressText);

    if(c-1 == copyIteration) {
        // Copy the sample random data
        //printf("Copying...\n");
        outData->CopyAndCastFrom(outbuf,0,maxX,0,maxY,0,maxZ);
    }
        
    outPtr = (T *) outbuf->GetScalarPointer();        
    inPtr1 = (T *) inData[0]->GetScalarPointer();
    inPtr2 = (T *) inData[1]->GetScalarPointer();

    // Clear the buffer
    for(int i=0;i<maxX*maxY*maxZ;i++)*outPtr++=0;
    outPtr = (T *) outbuf->GetScalarPointer();    
//		stackRand = new ImageStack(rwidth, rheight);
		if (Fay) {
			if (c == 26 || c == 51) {
				zOffset2 += 1;
				xOffset2 = -15;
				yOffset2 = -10;
			}
			if (xOffset2 < 10)
				xOffset2 += 5;
			else {
				xOffset2 = -15;
				yOffset2 += 5;
			}
		}
		if (vanS) {
         //printf("xOffset: %d\n",xOffset2);
			xOffset2 += 1;
		}

    int chRandz=0;
    float progress=0;
		for (int s = startSlice; s < nslices; s++) {
       progress=float(c)/iterations;
       progress+=s/float(100*nslices);
       self->UpdateProgress(progress);
            
			slicesDone++;
			if (currentSliceNo>=0) {
         //printf("Only for slice %d\n",currentSliceNo);
				s = currentSliceNo;
				nslices = s;
			}
			//printf("Iteration %d / %d Slice: %d / %d\n",c,iterations,s,nslices);
       int ch1z = s, ch2z=s+zOffset2;
            
			for (int y = 0; y < rheight; y++) {
				for (int x = 0; x <= rwidth; x++) {
             //printf("Reading ch1 and ch2 from %d, %d,%d\n",x+xOffset,y+yOffset,ch1z);
						ch1 =(int) GET_AT(x + xOffset, y + yOffset, ch1z,inPtr1);
						ch2 =(int) GET_AT(x + xOffset, y + yOffset, ch2z,inPtr2);
             //printf("got %d and %d\n",ch1,ch2);
						ch3 = 0;
             //printf("ignoreZeroZero=%d\n",ignoreZeroZero);
						if ((ignoreZeroZero)) {
                //printf("Fay=%d,vanS=%d,Costes=%d\n",Fay,vanS,Costes);

							if (Fay) {
                  //printf("Reading ch3 from %d,%d,%d\n",x+xOffset+xOffset2,
                  // y+yOffset+yOffset2,ch2z);
                 ch3=0;
                 int dx=x+xOffset+xOffset2;
                 int dy=y+yOffset+yOffset2;
                 if(dx>=0 && dy>=0 && dx<rwidth&&dy<=rheight) {
   			 	 		  ch3 =(int) GET_AT(dx, 
                                   dy,
                                   ch2z, inPtr2);
                 }
                 //printf("Got %d\n",ch3);
                  
                  SET_AT_OUT(x,y,chRandz,outPtr,ch3);
							}
							if (vanS) {
								//ch3 = (int)ip2.getPixel(x + xOffset + xOffset2,
								//     y + yOffset);
                 int dx=x+xOffset+xOffset2;
                 int dy=y+yOffset;
                ch3=0;
                 if(dx>=0 && dy>=0 && dx<rwidth&&dy<=rheight) {
                                
                    ch3 = (int)GET_AT(dx,
                                    y + yOffset,ch2z,inPtr2);
                  }
                  SET_AT_OUT(x,y,chRandz,outPtr,ch3);
                  
							}
							if ((Costes && !randZ) || (Costes && nslices < 1)) {
								ch4 = 1;
								while(ch4 != 0) {
									rx = (int) (vtkMath::Random() * (double) width);
									ry = (int) (vtkMath::Random() * (double) height);
                    ch4 = (int)GET_AT_OUT(rx,ry,chRandz,outPtr);
								}
                  //if(ch2)
                  //  printf("Writing at %d,%d,%d=%d\n",x,y,chRandz,ch2);
                  
                  SET_AT_OUT(rx,ry,chRandz,outPtr,ch2);
							}

							if ((Costes &&randZ && nslices > 1) && ch2 != 0) {
								ch3 =(int) 
                    ((vtkMath::Random() * (ch2Max - ch2Min)) + ch2Min);
                  
                  SET_AT_OUT(x,y,chRandz,outPtr,ch3);
							}

						}

						//add to random image

					
				}
			}
			if (Costes) {
            //gb.blur(ipRand, psf);
            gb->SetDimensionality(2);
            int uext[6];
            uext[0]=uext[2]=0;
            uext[1]=rwidth;
            uext[3]=rheight;
            uext[4]=0;
            uext[5]=maxZ;
            outData->SetUpdateExtent(uext);            
            uext[4]=uext[5]=chRandz;
            extract->SetInput(outData);
            extract->SetVOI(uext);
            extract->Update();
            //printf("Extracting slice %d...\n",chRandz);
            vtkImageData*slice=extract->GetOutput();
        
            uext[4]=uext[5]=0;
            
            gb->SetInput(extract->GetOutput());
            gb->SetStandardDeviations(2,2);
            gb->SetRadiusFactors(psf/2.0,psf/2.0,0);
            //printf("Smoothing...");
            gb->Update();
            vtkImageData* smoothed = gb->GetOutput();
            
            int d[3];
            smoothed->GetDimensions(d);
//            printf("smoothed dims= %d,%d,%d\n",d[0],d[1],d[2]);
            int ext[6];
            smoothed->GetWholeExtent(ext);
//            printf("smoothed ext=%d,%d,%d,%d,%d,%d\n",ext[0],ext[1],ext[2],ext[3],ext[4],ext[5]);
            
            uext[5]=uext[4]=chRandz;
            T* copyPtrOut = (T*)outData->GetScalarPointerForExtent(uext);
            uext[5]=uext[4]=chRandz;
            T* copyPtrIn = (T*)smoothed->GetScalarPointerForExtent(uext);
            for(int i=0;i<rwidth*rheight;i++) {
                *copyPtrOut++=*copyPtrIn++;
            }
            //printf("copied %d bytes of smoothed data\n",rwidth*rheight);
        }
			 //stackRand.addSlice("Correlation Plot", ipRand);
        chRandz++;
		}
		//random image created now calculate r

		//reset values for r
		sumXX = 0;
		sumX = 0;
		sumXY = 0;
		sumYY = 0;
		sumY = 0;
		N = 0;
		N2 = 0;
		int s2 = 0;
		sumXtotal = 0;
		sumYtotal = 0;
		colocX = 0;
		colocY = 0;
		double ICQrand = 0;
		int countPos2 = 0;
		countAll = 0;
		//xOffset2=-21;

		for (int s = startSlice; s < nslices; s++) {
			s2 = s;
			if (Fay && nslices > 1)
				s2 -= 1;
			if (currentSliceNo>=0) {
				s = currentSliceNo;
				nslices = s;
				s2 = 0;
			}
			//ip1 = img1.getProcessor(s);
			//ip2 = stackRand.getProcessor(s2);
       int ch1z=s;
       int chRandz=s2;
			for (int y = 0; y < rheight; y++) {
				for (int x = 0; x < rwidth; x++) {
					mask = 1;
					if (mask != 0) {
						//ch1 = (int) ip1.getPixel(x + xOffset,
						//	     y + yOffset);
             ch1 = (int)GET_AT(x + xOffset, y + yOffset,ch1z,inPtr1);
             //ch2 =(int) ip2.getPixel(x, y);
             ch2 =(int) GET_AT_OUT(x,y,chRandz,outPtr);
						
						if (ch1Max < ch1)
							ch1Max = ch1;
						if (ch1Min > ch1)
							ch1Min = ch1;
						if (ch2Max < ch2)
							ch2Max = ch2;
						if (ch2Min > ch2)
							ch2Min = ch2;
						N++;
						//Mander calc
						sumXtotal =
						    sumXtotal + ch1;
						sumYtotal =
						    sumYtotal + ch2;
						if (ch2 > 0)
							colocX = colocX + ch1;
						if (ch1 > 0)
							colocY = colocY + ch2;
						if ((ch1 + ch2 != 0))
							N2++;
						sumX = sumX + ch1;
						sumXY = sumXY + (ch1 * ch2);
						sumXX = sumXX + (ch1 * ch1);
						sumYY = sumYY + (ch2 * ch2);
						sumY = sumY + ch2;
						if (ch1 + ch2 != 0) {
							PDM =
							    ((double) ch1 - (double)ch1Mean) *
							    ((double) ch2 - (double)ch2Mean);
							if (PDM > 0)
								countPos2++;
							countAll++;
						}
					}
				}
			}
		}
		if (ignoreZeroZero)
			N = N2;
		ICQ2 = ((double) countPos2 / (double) countAll) - 0.5;
		ICQ2mean += ICQ2;
		if (ICQobs > ICQ2)
			countICQ++;
		pearsons1 = sumXY - (sumX * sumY / N);
		pearsons2 = sumXX - (sumX * sumX / N);
		pearsons3 = sumYY - (sumY * sumY / N);
		r2 = pearsons1 / (sqrt(pearsons2 * pearsons3));

		if (vanS) {
			vSx[c - 1] = (double) xOffset2;
			vSr[c - 1] = (double) r2;
		}

		if (r2 < r2min)
			r2min = r2;
		if (r2 > r2max)
			r2max = r2;
		//IJ.write("Random "+ c + "\t"+df3.format(r2)+ "\t"+ df3.format(coloc2M1)  + "\t"+df3.format(coloc2M2));
		//IJ.write(df3.format(r2));
		//rVals.append(r2 + "\n");
		r2mean = r2mean + r2;
		if (r > r2)
			colocCount++;
		sumr2sqrd = sumr2sqrd + (r2 * r2);
		sumr2 = sumr2 + r2;
		sumICQ2sqrd += (ICQ2 * ICQ2);
		sumICQ2 += ICQ2;
		//IJ.write(IJ.d2s(ICQ2,3));        
	}
//done randomisations
//calcualte mean Rrand
	r2mean = r2mean / iterations;
	r2sd =
	    sqrt(((iterations * (sumr2sqrd)) -
		  (sumr2 * sumr2)) / (iterations * (iterations - 1)));
	ICQ2mean = ICQ2mean / iterations;
	double ICQ2sd =
	    sqrt(((iterations * (sumICQ2sqrd)) -
		  (sumICQ2 * sumICQ2)) / (iterations * (iterations - 1)));
	double Zscore = (r - r2mean) / r2sd;
	double ZscoreICQ = (ICQobs - ICQ2mean) / ICQ2sd;
	//String icqPercentile = "<50%";

	//String Percentile =
	//    "" + (iterations - colocCount) + "/" + iterations;

//calculate percentage of Rrand that is less than Robs
//code from:
//http://www.cs.princeton.edu/introcs/26function/MyMath.java.html
//Thanks to Bob Dougherty
//50*{1 + erf[(V -mean)/(sqrt(2)*sdev)]

	double fx = 0.5 * (1 + erf(r - r2mean) / (sqrt(2) * r2sd));
  printf("fx=%f\n",fx);
	if (fx >= 1)
		fx = 1;
	if (fx <= 0)
		fx = 0;
	//String Percentile2 = IJ.d2s(fx, 3) + "";
	//if (keep)
	//	new ImagePlus("Example random image", stackRand).show();
	double percColoc =
	    ((double) colocCount / (double) iterations) * 100;
	double percICQ = ((double) countICQ / (double) iterations) * 100;
   
  self->SetRObserved(r);
  self->SetRRandMean(r2mean);    
  self->SetRRandSD(r2sd);
  printf("fx=%f\n",fx);
  self->SetPValue(fx);
  self->SetColocCount(colocCount);
  self->SetNumIterations(iterations);
  self->SetPSF(psf);
	//IJ.selectWindow("Results");
	//if (showR)
	//	new TextWindow("Random R values", "R(rand)",
	//		       rVals.toString(), 300, 400);
	//if (vanS) {
	//	PlotWindow plot = new PlotWindow("CCF", "x-translation",
	//					 "Pearsons", vSx, vSr);
		//r2min = (1.05*r2min);
		//r2max= (r2max*1.05);
		//plot.setLimits(-20, 20, r2min, r2max);
	//	plot.draw();
	//}
  gb->Delete();
  extract->Delete();
  outbuf->Delete();
	printf("Done!");
}

//code from:
//http://www.cs.princeton.edu/introcs/26function/MyMath.java.html

double erf(double z)
{
	double t = 1.0 / (1.0 + 0.5 * fabs(z));
	// use Horner's method
	double ans = 1 - t * exp( -z*z   -   1.26551223 +
                                            t * ( 1.00002368 +
                                            t * ( 0.37409196 + 
                                            t * ( 0.09678418 + 
                                            t * (-0.18628806 + 
                                            t * ( 0.27886807 + 
                                            t * (-1.13520398 + 
                                            t * ( 1.48851587 + 
                                            t * (-0.82215223 + 
                                            t * ( 0.17087277))))))))));
	if (z >= 0)
		return ans;
	else
		return -ans;
}






//----------------------------------------------------------------------------
// This method is passed a input and output regions, and executes the filter
// algorithm to fill the output from the inputs.
// It just executes a switch statement to call the correct function for
// the regions data types.
void vtkImageColocalizationTest::ThreadedExecute(vtkImageData **
						 inData,
						 vtkImageData *
						 outData,
						 int outExt[6], int id)
{
	int idx1;
	int inExt[6], cOutExt[6];

	switch (inData[0]->GetScalarType()) {
		vtkTemplateMacro7
		    (vtkImageColocalizationTestExecute, this, id,
		     this->NumberOfInputs, inData, outData, outExt,
		     static_cast < VTK_TT * >(0));
	default:
		vtkErrorMacro(<<"Execute: Unknown ScalarType");
		return;
	}

}



//----------------------------------------------------------------------------
void vtkImageColocalizationTest::PrintSelf(ostream & os, vtkIndent indent)
{
	this->Superclass::PrintSelf(os, indent);
	os << "\n";
	os << indent << "R(obs): " << RObserved << "\n";
  os << indent << "R(rand) Mean: " << RRandMean << "\n";
  os << indent << "R(rand) sd: " << RRandSD << "\n";    
  os << indent << "P-Value: " << PValue << "\n";
  os << indent << "Iterations: " << NumIterations << "\n";    
    double perc = (NumIterations - ColocCount)/(double)NumIterations;
  os << indent << "R(rand) > R(obs)" << (NumIterations - ColocCount) << "/" << NumIterations << "("<< perc <<"%)" << "\n";
  os <<"\n";
  os << indent << "Randomisation: ";
  if(Method == 0)os << "Fay";
  else if(Method == 1)os << "Costes";
  else if(Method == 2)os << "van Steensel";
  else os << "*** BAD RANDOMISATION METHOD ***";
  os << "\n";
  if(Method == 1) {
      os << indent << "PSF width (px): " << PSF << "\n";
      if(PixelSize)
        os << indent << "PSF width (um): " << PSF*PixelSize*2 << "\n";
  }
}
