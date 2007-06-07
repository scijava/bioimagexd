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
#include "vtkMath.h"
#include "vtkExtractVOI.h"
#include "vtkPNGWriter.h"
#include <math.h>
#include <time.h>
#define GET_AT(x,y,z,ptr) *(ptr+(z)*inIncZ+(y)*inIncY+(x)*inIncX)
#define SET_AT(x,y,z,ptr,val) *(ptr+(z)*outIncZ+(y)*outIncY+(x)*outIncX)=val
#define SET_AT_COMP(x,y,z,c,ptr,val) *(ptr+(int)((z)*outIncZ)+(int)((y)*outIncY)+(int)((x)*outIncX)+(c))=val
#define GET_AT_OUT(x,y,z,ptr) *(ptr+(z)*outIncZ+(y)*outIncY+(x)*outIncX)
#define SET_AT_OUT(x,y,z,ptr,val) *(ptr+(z)*outIncZ+(y)*outIncY+(x)*outIncX)=val

//#define OUT_T unsigned int
//#define VTK_OUT_TYPE VTK_UNSIGNED_INT
#define OUT_T unsigned char
#define VTK_OUT_TYPE VTK_UNSIGNED_CHAR
//#define VTK_OUT_TYPE VTK_DOUBLE
//#define OUT_T double

double mysqr(double x) { return x*x; }

vtkCxxRevisionMacro(vtkImageColocalizationTest, "$Revision: 1.25 $");
vtkStandardNewMacro(vtkImageColocalizationTest);

//----------------------------------------------------------------------------
vtkImageColocalizationTest::vtkImageColocalizationTest()
{
    RandomizeZ = false;
    IgnoreZeroPixels = true;
    Smooth = true;
    ManualPSFSize = 0.0;
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

// Always request the whole input data
//
int vtkImageColocalizationTest::RequestUpdateExtent (
  vtkInformation* vtkNotUsed(request),
  vtkInformationVector** inputVector,
  vtkInformationVector* outputVector)
{
  int uext[6], ext[6];
  vtkInformation* outInfo = outputVector->GetInformationObject(0);
  vtkInformation *inInfo = inputVector[0]->GetInformationObject(0);
  inInfo->Get(vtkStreamingDemandDrivenPipeline::WHOLE_EXTENT(),ext);
  memcpy(uext, ext, 6*sizeof(int));
  inInfo->Set(vtkStreamingDemandDrivenPipeline::UPDATE_EXTENT(), uext,6);
  return 1;    
}


//----------------------------------------------------------------------------
void vtkImageColocalizationTest::
ExecuteInformation(vtkImageData ** inputs, vtkImageData * output)
{
    vtkImageMultipleInputFilter::ExecuteInformation(inputs, output);
    this->GetOutput()->SetScalarType(VTK_OUT_TYPE);
}

float* makeKernel(double radius,int*ksize) {        
        radius += 1;
        int size = (int)radius*2+1;
    
        float *kernel = new float[size*size];
        //float *kernel[] = new float[size][size];
        
        double v;
        for (int y=0; y<size; y++) {
            for(int x=0; x<size; x++) {
    //v = (float)exp(-0.5*(mysqr((x-radius)/(radius*2)))/mysqr(0.2));
                v = (double)exp(-0.5*((mysqr((x-radius)/((double)radius*2))+mysqr((y-radius)/((double)radius*2)))/mysqr(0.2)));
                if(v<0.0005) v = 0.0;
                
                kernel[y*size+x]=v;
                //krnl[y][x] = v;
            }
        }
        /*
        float *kernel2 = new float[size-2];
        for (int i=0; i<size-2; i++)
            kernel2[i] = kernel[i+1];
        if (size-2==1)
            kernel2[0] = 1;
        delete[] kernel;*/
        *ksize=size;
/*        return kernel2;*/
        return kernel;
}

void smooth(OUT_T* inPtr,OUT_T*outPtr,int,int ext[6],float*kernel,double scale,int size,
        int inIncX,int inIncY,int inIncZ,int outIncX,int outIncY,int outIncZ) {
        
        
  int uc,vc;

  uc = size / 2;
  vc = size / 2;
    
  if ((size&1)!=1) {
    printf("\n\n\n\n******* Error, convolution kernel size not odd *******\n\n\n");
  }
  int xmin,xmax,ymin,ymax;
  int z = ext[4];
  xmin=ext[0];
  xmax=ext[1];
  ymin=ext[2];
  ymax=ext[3];

  double sum;
  int xedge = xmax - uc;
  int yedge = ymax - vc;
  int i=0;
  OUT_T val;
  
  // Assuming (xmin,ymin) is top left corner
  // kernel is over top-edge, ymin <= y <vc
  int y = ymin;
  for(;y < vc; y++) {
    for(int x = xmin; x<=xmax; x++) {
      sum = 0.0;
      i=0;
      
      for(int v=-vc; v <= vc; v++) {
    int ny=y+v;
        for(int u = -uc; u <= uc; u++) {
          int nx;
          nx=x+u;
      if (nx<=0) nx = 0;
      else if (nx>xmax) nx = xmax;
      if (ny<=0) ny = 0;
      else if (ny>ymax) ny = ymax;
          val = GET_AT(nx,ny,z,inPtr);
          sum += val*kernel[i++];
        }
      }
      SET_AT_OUT(x,y,z,outPtr,(OUT_T)(scale*sum+0.5));  
    }
  }
  
  // kernel is not on any horizontal edge, vc <= y < ymax-vc
  for(; y <= yedge; y++) {
    int x=xmin;

    // kernel over left vertical edge, xmin <= x < uc
    for(; x < uc; x++) {
      i=0;
      sum = 0.0;
      for(int ny=y-vc; ny <= y+vc; ny++) {
        for(int u = -uc; u <= uc; u++) {
          int nx = x+u;
      if (nx < xmin) nx = xmin;
          val = GET_AT(nx,ny,z,inPtr);
          sum += val*kernel[i++];
        }
      }
      SET_AT_OUT(x,y,z,outPtr,(OUT_T)(scale*sum+0.5));  
    }

    // kernel is not over any edge, most of the time time will 
    // be spent here when using a large image and small kernel
    // uc <= x <= xmax-uc
    for(; x<=xedge; x++) {
      sum = 0.0; 
      i = 0;
      for(int ny=y-vc; ny <= y + vc; ny++) {
    for(int nx = x - uc; nx <= x + uc; nx++) {
      val = GET_AT(nx,ny,z,inPtr);
      sum += val*kernel[i++];
    }
      }
      SET_AT_OUT(x,y,z,outPtr,(OUT_T)(scale*sum+0.5));  
    }

    // kernel over right vertical edge, xmax-uc < x <= xmax
    for (; x<=xmax; x++) {
      i=0;
      sum = 0.0;
      for(int ny=y-vc; ny <= y+vc; ny++) {
        for(int u = -uc; u <= uc; u++) {
          int nx = x+u;
      if (nx > xmax) nx = xmax;
          val = GET_AT(nx,ny,z,inPtr);
          sum += val*kernel[i++];
        }
      }
      SET_AT_OUT(x,y,z,outPtr,(OUT_T)(scale*sum+0.5));  
    }
  }

  // kernel over bottom horizontal edge, ymax-vc <= y <= ymax
  for(;y<=ymax; y++) {
    for(int x=xmin; x<=xmax; x++) {
      sum = 0.0;
      i = 0;
      for(int v=-vc; v <= vc; v++) {
    int ny=y+v;
        for(int u = -uc; u <= uc; u++) {
          int nx;
          nx=x+u;
      if (nx<=0) nx = 0;
      else if (nx>xmax) nx = xmax;
      if (ny>ymax) ny = ymax;
          val = GET_AT(nx,ny,z,inPtr);
          sum += val*kernel[i++];
        }
      }
      SET_AT_OUT(x,y,z,outPtr,(OUT_T)(scale*sum+0.5));  
    }
  }
}


 
 
template < class T >
    void CalculateStatisticsOfExistingImage(vtkImageColocalizationTest * self,
  vtkImageData ** inData,  int rwidth, int rheight, int nslices, double*ch1Mean, double*ch2Mean,double *r) {
  
    //calulate pearsons for existing image;
    int currentSliceNo = self->GetCurrentSlice();
    vtkIdType inIncX, inIncY, inIncZ;
    double pearsons1 = 0, pearsons2 = 0, pearsons3 = 0;
    double ch1Max = 0, ch1Min = 255;
    double ch2Max = 0, ch2Min = 255;
    double r2 = 1;
    int N = 0, N2 = 0, Nr = 0, Ng = 0;
    double PDMobs = 0;
/*    double ICQ2; 
    double ICQ2mean = 0;
    int countICQ = 0;
       */
    double ICQobs = 0;
       

    double sumX = 0, sumXY = 0, sumXX = 0, sumYY = 0, sumY = 0, sumXtotal =0,
            sumYtotal = 0, colocX = 0, colocY = 0;
            
    //calucalte ICQ
    int countAll = 0, countAll2 = 0, countPos = 0;
    
            
    OUT_T ch1, ch2, ch3, ch4 = 0, count;
    T* inPtr1 = (T *) inData[0]->GetScalarPointer();
    T* inPtr2 = (T *) inData[1]->GetScalarPointer();
    inData[0]->GetIncrements(inIncX, inIncY, inIncZ);

    for (int s = 0; s < nslices; s++)
    {
        if (currentSliceNo>=0) {
            s = currentSliceNo;
            nslices = s;
        }
        for (int y = 0; y <= rheight; y++)
        {
            for (int x = 0; x <= rwidth; x++) 
            {
                ch1 = (int)GET_AT(x,y,s,inPtr1);
                ch2 = (int)GET_AT(x,y,s,inPtr2);

                if (ch1Max < ch1)
                    ch1Max = ch1;
                if (ch1Min > ch1)
                    ch1Min = ch1;
                if (ch2Max < ch2) {
                    ch2Max = ch2;
                    
                }
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

    if (self->GetIgnoreZeroPixels())
        N = N2;

    *ch1Mean = sumX / N;
    *ch2Mean = sumY / N;
    pearsons1 = sumXY - (sumX * sumY / N);
    pearsons2 = sumXX - (sumX * sumX / N);
    pearsons3 = sumYY - (sumY * sumY / N);
    
    // Pearson's correlation for existing channels
    *r = pearsons1 / (sqrt(pearsons2 * pearsons3));

    for (int s = 0; s < nslices; s++)
    {
        if (currentSliceNo>=0) {
            // printf("Only for slice %d\n",currentSliceNo);            
            s = currentSliceNo;
            nslices = s;
        }
        for (int y = 0; y <= rheight; y++)
        {
            //printf("Calculating r for original images.");
            for (int x = 0; x <= rwidth; x++)
            {
                ch1 = (int)GET_AT(x,y,s,inPtr1);
                ch2 = (int)GET_AT(x,y,s,inPtr2);
                    
                if (ch1 + ch2 != 0) {
                    PDMobs = ((double) ch1 - (double)*ch1Mean) *
                             ((double) ch2 - (double)*ch2Mean);
                    if (PDMobs > 0)
                        countPos++;
                    countAll2++;
                }                
            }
        }
    }
    ICQobs = ((double) countPos / (double) countAll2) - 0.5; 
 }

//----------------------------------------------------------------------------
// This templated function executes the filter for any type of data.
template < class T >
    void
    vtkImageColocalizationTestExecute
    (vtkImageColocalizationTest * self, int id,
     int NumberOfInputs, vtkImageData ** inData, vtkImageData * outData,
     int outExt[6], T *) {
    vtkIdType inIncX, inIncY, inIncZ;
    vtkIdType outIncX, outIncY, outIncZ;
    int maxX, maxY, maxZ;
    int idxX, idxY, idxZ;
    OUT_T* outPtr;
    double pearsons1 = 0, pearsons2 = 0, pearsons3 = 0;
         
    double PDM = 0;

    double ch1Mean, ch2Mean;                  
    double r=1, r2 = 1;
    bool Costes = false, Fay = false, vanS = false;

    bool randZ = self->GetRandomizeZ();
    bool ignoreZeroZero = (bool)self->GetIgnoreZeroPixels();
    // printf("Randomizing in Z: %s\n",randZ?"yes":"no");
         
    switch(self->GetMethod()) {
        case 0: Fay = true; break;
        case 1: Costes = true; break;
        case 2: vanS = true; break;
        default:
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
    vtkMath::RandomSeed(time(0));
    
    outPtr = (OUT_T *) outbuf->GetScalarPointer();
    int width = maxX, height = maxY;
    
    int nslices = maxZ+1;
    
    int currentSliceNo = self->GetCurrentSlice();
    
    int rwidth, rheight, xOffset, yOffset, mask;
    double psf = 0;
 

    double ch1Max = 0, ch1Min = 255;
    double ch2Max = 0, ch2Min = 255;
        
    OUT_T ch1, ch2, ch3, ch4 = 0, count;
    double sumX = 0, sumXY = 0, sumXX = 0, sumYY = 0, sumY = 0, sumXtotal =0,
            sumYtotal = 0, colocX = 0, colocY = 0;
    int N = 0, N2 = 0;
    
    double r2min = 1, r2max = -1;
    int i = 1;
    double coloc2M1 = 0, coloc2M2 = 0;
    
    int colocCount = 0, colocCount1 = 0, colocCount2 = 0;

    double r2sd = 0;
    double sumr2sqrd = 0;
    double sumr2 = 0;
    int Nr = 0, Ng = 0;
    
    double ICQ2; 
    double ICQ2mean = 0;
    double ICQobs = 0;
    int countICQ = 0;
    double sumICQ2sqrd = 0;
    double sumICQ2 = 0;
        
    char progressText[300];  
    psf = (0.61*self->GetCh2Lambda())/self->GetNumericalAperture();
    psf = (psf)/(self->GetPixelSize()*1000);
    if (self->GetManualPSFSize()) psf = self->GetManualPSFSize();

    
    int size;
    float*kernel = 0;
    double scale = 1.0, kernelsum = 0;
    if(Costes) {
        kernel = makeKernel(psf,&size);
        for(int i = 0; i < size*size; i++)
            kernelsum += kernel[i];
        if(kernelsum)
            scale = 1.0 / kernelsum;
        printf("Scale for smoothing=%f, kernelsize=%d\n",scale,size);
    }

    int iterations = self->GetNumIterations();
 
    xOffset = 0, yOffset = 0;
    
    rwidth = width;
    rheight = height;
    
    int g1 = 0, g2 = 0;
    
    int histCount = 0;

    //  printf("Acuiring inpointers\n");
    T* inPtr1 = (T *) inData[0]->GetScalarPointer();
    T* inPtr2 = (T *) inData[1]->GetScalarPointer();
  
    CalculateStatisticsOfExistingImage<T>(self, inData, width, height, nslices,&ch1Mean, &ch2Mean,&r);


    

    bool ch3found = false;
    //do random localisations
    int rx = 0, ry = 0, rz = 0;
    
    
    double r2mean = 0;
    int slicesDone = 0;
    int xCount = 0;
    int xOffset2 = -15, yOffset2 = -10, zOffset2 = 0;
    int startSlice = 0;

    if (Costes) {
        xOffset2 = yOffset2 = 0;
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


    double vSx[41], vSr[41];
    
    ch4 = 0;    
    
    for (int c = 1; c <= iterations; c++)
    {
        if(!id) {
            self->UpdateProgress(float(c)/iterations);
        }
        sprintf(progressText,"Calculating P-Value (iteration %d / %d)",c,iterations);
        self->SetProgressText(progressText);
        
        if(c == iterations) {
            // Copy the sample random data
            outData->CopyAndCastFrom(outbuf,0,maxX,0,maxY,0,maxZ);
        }
            
        outPtr = (OUT_T *) outbuf->GetScalarPointer();        
        inPtr1 = (T *) inData[0]->GetScalarPointer();
        inPtr2 = (T *) inData[1]->GetScalarPointer();
        

        if (Fay) {
            // At iterations 26 and 61 shift the parameters
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
            xOffset2 += 1;
        }
        int chRandz=0;
        float progress=0;
        
        for (int s = startSlice; s < nslices; s++)
        {
            progress=float(c)/iterations;
            progress+=s/float(100*nslices);
            if(!id) {
                self->UpdateProgress(progress);
            }        
            slicesDone++;
            if (currentSliceNo>=0) {
                s = currentSliceNo;
                nslices = s;
            }
            for(int y=0;y<= rheight;y++) {
                for(int x=0;x<=rwidth;x++) {
                    SET_AT_OUT(x,y,chRandz,outPtr,0);
                }
            }
            int ch1z = s, ch2z = s + zOffset2;
            //printf("ch2Min=%f, ch2Max=%f\n",ch2Min,ch2Max);
            for (int y = 0; y <= rheight; y++)
            {
                for (int x = 0; x <= rwidth; x++)
                {
                    ch1 =(int) GET_AT(x + xOffset, y + yOffset, ch1z,inPtr1);
                    ch2 =(int) GET_AT(x + xOffset, y + yOffset, ch2z,inPtr2);

                    ch3 = 0;
                    if ((ignoreZeroZero))
                    {
                        if (Fay)
                        {
                            ch3=0;
                            int dx = x + xOffset + xOffset2;
                            int dy = y + yOffset + yOffset2;
                            if(dx >= 0 && dy >= 0 && dx < rwidth+1 && dy <= rheight+1)
                            {
                                ch3 =(int) GET_AT(dx,dy,ch2z, inPtr2);
                            }
                            //printf("Got %d\n",ch3);
                  
                            SET_AT_OUT(x,y,chRandz,outPtr,ch3);
                        }
                        
                        if (vanS) 
                        {
                            //ch3 = (int)ip2.getPixel(x + xOffset + xOffset2,
                            //     y + yOffset);
                            int dx = x + xOffset + xOffset2;
                            int dy = y + yOffset;
                            ch3 = 0;
                            if(dx >= 0 && dy >= 0 && dx < rwidth+1 && dy <= rheight+1)
                            {                    
                                ch3 = (int)GET_AT(dx,y + yOffset,ch2z,inPtr2);
                            }
                            SET_AT_OUT(x,y,chRandz,outPtr,ch3);
                        }
                        
                        if ((Costes && !randZ) || (Costes && nslices < 1))
                        {
                            int flag=1;
                            int nnn=0;
                            while(flag!=0) {
                                nnn++;
                                rx = int(vtkMath::Random(0,width+1));
                                ry = int(vtkMath::Random(0,height+1));
                                //rx = (int) (vtkMath::Random() * (double) (width+1));
                                //ry = (int) (vtkMath::Random() * (double) (height+1));
                                flag = (int)GET_AT_OUT(rx,ry,chRandz,outPtr);
                                //if(flag)printf("Got at %d,%d=%d\n",rx,ry,flag);
//                                if(nnn>99999&& (nnn%100000)==0) {
//                                    printf("In eternal loop, flag=%d rx=%d,ry=%d,z=%d\n",flag,rx,ry,chRandz);
//                                }
                            }
                            SET_AT_OUT(rx,ry,chRandz,outPtr,ch2);
                        }
    
                        if ((Costes &&randZ && nslices > 1) && ch2 != 0) 
                        {                                
                            ch3 =(OUT_T) ((vtkMath::Random() * (ch2Max - ch2Min)) + ch2Min);
                            SET_AT_OUT(x,y,chRandz,outPtr,ch3);
                        }
                    }
                }
            }
            
            // If we're using Costes' method, we blur the dataset
            if (Costes) {
                // first create a buffer to store a copy of the dataset
                vtkImageData* copybuf = vtkImageData::New();
                copybuf->SetExtent(outbuf->GetExtent());
                copybuf->SetScalarType(outbuf->GetScalarType());
                copybuf->AllocateScalars();                                
                // Get pointer to the slice we need to blur
                OUT_T* outPtr = (OUT_T*)outbuf->GetScalarPointer();
                // Get pointer to the copy buffer
                OUT_T * copyPtr = (OUT_T*)copybuf->GetScalarPointer();
                for(int i=0;i<(maxX+1)*(maxY+1)*(maxZ+1);i++)*copyPtr++=0;
                
                copyPtr = (OUT_T *) copybuf->GetScalarPointer();                    
                // Calculate the bounds of the dataset
                int uext[6];
                uext[0]=uext[2]=0;
                uext[1]=rwidth;
                uext[3]=rheight;
                uext[4]=uext[5]=chRandz;        
                
                // Smooth the data in outPtr and store it in copyPtr
                smooth(outPtr,copyPtr,(int)(psf),uext,kernel,scale,size,inIncX,inIncY,inIncZ,outIncX,outIncY,outIncZ);
                // copy the data to the outbuf                
                outbuf->CopyAndCastFrom(copybuf,0,rwidth,0,rheight,chRandz,chRandz);
                copybuf->Delete();
                
            }
            chRandz++;
        }
        
        //random image created now calculate r    
        //reset values for r
        sumXX = sumX = sumXY = sumYY = sumY = 0;
        N = N2 = 0;
        
        int s2 = 0;
        sumXtotal = sumYtotal = 0;
        
        colocX = colocY = 0;
        
        double ICQrand = 0;
        int countPos2 = 0;
        int countAll = 0;
        
    
        for (int s = startSlice; s < nslices; s++) 
        {
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
            int ch1z = s;
            int chRandz = s2;
//            printf("ch2Min=%f, ch2Max=%f\n",ch2Min,ch2Max);
            for (int y = 0; y <= rheight; y++) 
            {
                for (int x = 0; x <= rwidth; x++)
                {
                    //ch1 = (int) ip1.getPixel(x + xOffset,
                    //       y + yOffset);
                    ch1 = (int)GET_AT(x + xOffset, y + yOffset,ch1z,inPtr1);
                    //ch2 =(int) ip2.getPixel(x, y);
                    ch2 =(int) GET_AT_OUT(x,y,chRandz,outPtr);
                    
                    if (ch1Max < ch1) ch1Max = ch1;
                    if (ch1Min > ch1) ch1Min = ch1;
                    if (ch2Max < ch2) ch2Max = ch2;
                    if (ch2Min > ch2) ch2Min = ch2;
                    N++;
                    //Mander calc
                    sumXtotal = sumXtotal + ch1;
                    sumYtotal = sumYtotal + ch2;
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
                    if (ch1 + ch2 != 0)
                    {
                        PDM = ((double) ch1 - (double)ch1Mean) *
                              ((double) ch2 - (double)ch2Mean);
                        if (PDM > 0)
                            countPos2++;
                        countAll++;
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
        printf("ch1Max=%f,ch2Max=%f, sumX=%f,sumY=%f,Pearson's p1=%f, p2=%f, p3=%f\n",ch1Max,ch2Max,sumX,sumY,pearsons1,pearsons2,pearsons3);  
        
        if (vanS) {
            vSx[c - 1] = (double) xOffset2;
            vSr[c - 1] = (double) r2;
        }
        if (r2 < r2min)
            r2min = r2;
        if (r2 > r2max)
            r2max = r2;
        //rVals.append(r2 + "\n");
        printf("r2=%f\n",r2);
        r2mean = r2mean + r2;
        if (r > r2)
            colocCount++;
        sumr2sqrd = sumr2sqrd + (r2 * r2);
        sumr2 = sumr2 + r2;
        sumICQ2sqrd += (ICQ2 * ICQ2);
        sumICQ2 += ICQ2;
    }
    
    //done randomisations
    //calcualte mean Rrand
    
    r2mean /= iterations;
    printf("sumr2sqrd=%f, sumr2=%f\n",sumr2sqrd,sumr2);
    r2sd = sqrt(((iterations * (sumr2sqrd)) -
           (sumr2 * sumr2)) / (iterations * (iterations - 1)));
    ICQ2mean = ICQ2mean / iterations;
    double ICQ2sd = sqrt(((iterations * (sumICQ2sqrd)) -
                    (sumICQ2 * sumICQ2)) / (iterations * (iterations - 1)));
    double Zscore = (r - r2mean) / r2sd;
    double ZscoreICQ = (ICQobs - ICQ2mean) / ICQ2sd;

    //calculate percentage of Rrand that is less than Robs
    //code from:
    //http://www.cs.princeton.edu/introcs/26function/MyMath.java.html
    //Thanks to Bob Dougherty
    //50*{1 + erf[(V -mean)/(sqrt(2.0f)*sdev)]
    double fx = 0.5 * (1 + erf(r - r2mean) / (sqrt(2.0f) * r2sd));
    printf("fx=%f\n",fx);
    if (fx >= 1.0)
        fx = 1.0;
    if (fx <= 0)
        fx = 0;

    double percColoc =
        ((double) colocCount / (double) iterations) * 100;
    double percICQ = ((double) countICQ / (double) iterations) * 100;
   
    self->SetRObserved(r);
    self->SetRRandMean(r2mean);    
    self->SetRRandSD(r2sd);

    
    self->SetPValue(fx);
    self->SetColocCount(colocCount);
    self->SetNumIterations(iterations);
    self->SetPSF(psf);
    
   
    outbuf->Delete();
    if(kernel) {
    delete[] kernel;
    }
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
