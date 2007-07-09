/*=========================================================================

  Program:   BioImageXD
  Module:    $RCSfile: vtkImageAutoThresholdColocalization.cxx,v $

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
#include "vtkImageAutoThresholdColocalization.h"

#include "vtkImageData.h"
#include "vtkObjectFactory.h"
#include "vtkImageProgressIterator.h"
#include "vtkPointData.h"
#include <math.h>
#include "vtkMath.h"

#define GET_AT(x,y,z,ptr) *(ptr+(z)*inIncZ+(y)*inIncY+(x)*inIncX)
#define SET_AT(x,y,z,ptr,val) *(ptr+(z)*outIncZ+(y)*outIncY+(x)*outIncX)=val
#define SET_AT_COMP(x,y,z,c,ptr,val) *(ptr+(int)((z)*outIncZ)+(int)((y)*outIncY)+(int)((x)*outIncX)+(c))=val
#define GET_AT_OUT(x,y,z,ptr) *(ptr+(z)*outIncZ+(y)*outIncY+(x)*outIncX)
#define SET_AT_OUT(x,y,z,ptr,val) *(ptr+(z)*outIncZ+(y)*outIncY+(x)*outIncX)=val

#define GET_AT_PLOT(x,y,z,ptr) *(ptr+(z)*plotIncZ+(y)*plotIncY+(x)*plotIncX)
#define SET_AT_PLOT(x,y,z,ptr,val) *(ptr+(z)*plotIncZ+(y)*plotIncY+(x)*plotIncX)=val


void calculate_pearson(double* p1, double*p2, double*p3, double sumX, double sumY, double sumXX, double sumYY, double sumXY, double N) {
    *p1 = sumXY - (sumX * sumY / N);
    *p2 = sumXX - (sumX * sumX / N);
    *p3 = sumYY - (sumY * sumY / N);
}

vtkCxxRevisionMacro(vtkImageAutoThresholdColocalization,
            "$Revision: 1.25 $");
vtkStandardNewMacro(vtkImageAutoThresholdColocalization);

//----------------------------------------------------------------------------
vtkImageAutoThresholdColocalization::vtkImageAutoThresholdColocalization()
{
    IncludeZeroPixels = 0;
    ConstantVoxelValue = 0;
    LowerThresholdCh1 = LowerThresholdCh2 = -1;
    UpperThresholdCh1 = UpperThresholdCh2 = 255;
    vtkImageData *plot;
    
    OverThresholdCh1 = OverThresholdCh2 = NonZeroCh1 = NonZeroCh2 = 0;
    plot = vtkImageData::New();
    plot->ReleaseData();
    this->AddOutput(plot);
    plot->Delete();
}


//----------------------------------------------------------------------------
vtkImageAutoThresholdColocalization::~vtkImageAutoThresholdColocalization()
{
}

//----------------------------------------------------------------------------
void vtkImageAutoThresholdColocalization::
ComputeInputUpdateExtents(vtkDataObject * output)
{
    int inExt[6];
    inExt[0] = inExt[1] = inExt[2] = inExt[3] = inExt[4] = inExt[5] =
        0;

    for (int idx = 0; idx < this->NumberOfInputs; idx++) {
        if (this->Inputs[idx] != NULL) {
            //      this->Inputs[idx]->SetUpdateExtent( this->Inputs[idx]->GetWholeExtent() );
            this->Inputs[idx]->SetUpdateExtent(inExt);
        }
    }
}

//----------------------------------------------------------------------------
void vtkImageAutoThresholdColocalization::
ExecuteInformation(vtkImageData ** inputs, vtkImageData ** outputs)
{
    vtkImageMultipleInputOutputFilter::ExecuteInformation(inputs,
                                  outputs);

    /*int wholeExt[6];

    wholeExt[1] = wholeExt[3] = 255;
    wholeExt[0] = wholeExt[2] = 0;
    wholeExt[4] = wholeExt[5] = 0;
    // We're gonna produce image one slice thick and 255x255 in size
    outputs[1]->SetWholeExtent(wholeExt);
    outputs[1]->RequestExactExtentOff();
    outputs[1]->SetUpdateExtent(wholeExt);
*/

}

template <class T> void calculateThreshold
    (
    vtkImageAutoThresholdColocalization * self,int id,
    vtkImageData ** inData, int outExt[6], 
    int Ch1Th, int Ch2Th,
    double*ch1BestThresh, double *m, double*b, double*best
    )
{
    printf("Calculating threshold\n");
    bool thresholdFound = false, divByZero = false;
    int iteration = 0;
    int N = 0, N2 = 0, Nzero = 0;
    int ch1 = 0, ch2 = 0;
    double r2Prev = 0, r2Prev2 = 1;
    
    double oldMax = 0, newMax=0;
    double range[2];
    double pearsons1 = 0, pearsons2 = 0, pearsons3 = 0;
    double sumX = 0, sumY = 0, sumXY = 0, sumXX = 0, sumYY = 0;    
    double r2 = 1, bestr2 = -1;
    double tolerance = 0.01;        
    double ch1threshmax = 0, ch2threshmax = 0;
    vtkIdType inIncX, inIncY, inIncZ;
    
    
    vtkIdType maxX, maxY, maxZ;
    vtkIdType idxX, idxY, idxZ;
    
    T* inPtr1, *inPtr2;
    char progressText[200];
    
    
    *ch1BestThresh = 0;
    inData[0]->GetScalarRange(range);
    int ch1Max = (int)range[1];
    int ch1Min = 0;
    
    inData[1]->GetScalarRange(range); 
    int ch2Max = (int)range[1];
    int ch2Min = 0;
    
    newMax = ch1threshmax = ch1Max;
    ch2threshmax = ch2Max;
    
    inData[0]->GetContinuousIncrements(outExt, inIncX, inIncY, inIncZ);
    
    maxX = outExt[1] - outExt[0];
    maxY = outExt[3] - outExt[2];
    maxZ = outExt[5] - outExt[4];    
    
    while ((thresholdFound == false) && iteration < 30) {
        
        if (iteration == 2 && r2 < 0) {
           //vtkDebugMacro(<<"No positive correlations found. Ending\n");
           printf("No positive correlations found. Ending\n");
            return;
        }
            
        ch1threshmax = vtkMath::Round(newMax);
        //printf("Setting ch1threshmax to %f\n", ch1threshmax);
        ch2threshmax =
            vtkMath::Round(((double) ch1threshmax * (double) *m) +
              (double) *b);
        if(!id) {
            self->UpdateProgress(0.5*(iteration/30.0));
        }
        
        sprintf(progressText,"Calculating threshold (iteration %d) ch1 = %f, ch2 = %f",iteration,ch1threshmax, ch2threshmax);
        self->SetProgressText(progressText);                  

       // If a user specified threshold has been given, then it will be used
       // instead of the calculated threshold        
        if(Ch1Th >= 0 && Ch2Th >= 0) {
            printf("Using given thresholds %d and %d\n",Ch1Th, Ch2Th);
            thresholdFound = 1;
            
            ch1threshmax = Ch1Th;
            ch2threshmax = Ch2Th;
        }
        
        // Zero the counters
        sumX = sumXY = sumXX = sumYY = sumY = N2 = N = Nzero = 0;
        
        //printf("Acquiring input pointers\n");
        inPtr1 =
            (T *) inData[0]->GetScalarPointerForExtent(outExt);
        inPtr2 =
            (T *) inData[1]->GetScalarPointerForExtent(outExt);

        for (idxZ = 0; idxZ <= maxZ; idxZ++) {
            for (idxY = 0; idxY <= maxY; idxY++) {
                for (idxX = 0; idxX <= maxX; idxX++) {
                    ch1 = (int) *inPtr1++;
                    ch2 = (int) *inPtr2++;

                    // Calculate pearson's for voxels below
                    // lower threshold
                    if ((ch1 <= (ch1threshmax))
                        || (ch2 <= (ch2threshmax))) {
                        if (ch1 + ch2 == 0)
                            Nzero++;
                        //calc pearsons
                        sumX = sumX + ch1;
                        sumXY =
                            sumXY + (ch1 * ch2);
                        sumXX =
                            sumXX + (ch1 * ch1);
                        sumYY =
                            sumYY + (ch2 * ch2);
                        sumY = sumY + ch2;
                        N++;

                    }
                    inPtr1 += inIncY;
                    inPtr2 += inIncY;
                }
                inPtr1 += inIncZ;
                inPtr2 += inIncZ;
            }
        }


        if (!self->GetIncludeZeroPixels())
            N = N - Nzero;
        
        calculate_pearson(&pearsons1, &pearsons2, &pearsons3,
        sumX, sumY, sumXX,sumYY,sumXY,N);

        r2Prev2 = r2Prev;
        r2Prev = r2;
        r2 = pearsons1 / (sqrt(pearsons2 * pearsons3));


        //if r is not a number then set divide by zero to be true  
        if (((sqrt(pearsons2 * pearsons3)) == 0) || N == 0)
            divByZero = true;
        else
            divByZero = false;

        //check to see if we're getting colser to zero for r                                               
        if ((bestr2 * bestr2 > r2 * r2)) {
            *ch1BestThresh = ch1threshmax;
            bestr2 = r2;
            *best = bestr2;
        
        }
        //if our r is close to our level of tolerance then set threshold has been found
        if ((r2 < tolerance) && (r2 > -tolerance)) {
            
            thresholdFound = true;
        }
        //if we've reached ch1 =1 then we've exhausted posibilities
        if (vtkMath::Round(ch1threshmax) == 0) {
            
            thresholdFound = true;
        }
        oldMax = newMax;
        //change threshold max
        if (r2 >= 0) {
            if ((r2 >= r2Prev) && (!divByZero))
                newMax = newMax / 2;
            if ((r2 < r2Prev) || (divByZero))
                newMax = newMax + (newMax / 2);
        }
        if ((r2 < 0) || divByZero) {
            newMax = newMax + (newMax / 2);
        }
        iteration++;
    }
}

//----------------------------------------------------------------------------
// This templated function executes the filter for any type of data.
template < class T >
    void
    vtkImageAutoThresholdColocalizationExecute
    (vtkImageAutoThresholdColocalization * self, int id,
     int NumberOfInputs, vtkImageData ** inData, vtkImageData ** outData,
     int outExt[6], T *) {
    char progressText[200];
    vtkIdType inIncX, inIncY, inIncZ;
    vtkIdType outIncX, outIncY, outIncZ;

    vtkIdType maxX, maxY, maxZ;
    vtkIdType idxX, idxY, idxZ;
    
    double range[2];
    
    inData[0]->GetScalarRange(range);
    int ch1Min = 0, ch1Max = (int)range[1];
    
    inData[1]->GetScalarRange(range); 
    int ch2Min = 0, ch2Max = (int)range[1];
    
         
    int LowerThresholdCh1 = self->GetLowerThresholdCh1(), LowerThresholdCh2 = self->GetLowerThresholdCh2();        
    int UpperThresholdCh1 = self->GetUpperThresholdCh1(), UpperThresholdCh2 = self->GetUpperThresholdCh2();
         
    int ch1, ch2, ch3;
    double pearsons1, pearsons2, pearsons3, pearsonsBelowTh;
    
    
    double sumX = 0, sumY = 0, sumXY = 0, sumXX = 0, sumYY = 0;
    double countX = 0, countY = 0, colocX = 0, colocY = 0;
    int count = 0,Nch1 = 0, Nch2 =0;

    int sumCh2gtT = 0, sumCh1gtT = 0;
    double sumCh1total = 0, sumCh2total = 0;
    
    double mCh2coloc = 0, mCh1coloc = 0;
    
    
    int Ncoloc = 0,sumColocCh1 = 0, sumColocCh2 = 0;
    

    int N = 0, N2 = 0, Nzero = 0;
    int Nch1gtT = 0, Nch2gtT = 0;
    
    double ch1threshmin = 0, ch2threshmin = 0;
    double ch1threshmax = ch1Max, ch2threshmax = ch2Max;
    
    int Nnonzeroch1 = 0, Nnonzeroch2 = 0;      
    double ch1BestThresh = 0;
    
    //start regression
//    vtkDebugMacro(<<"1/3: Performing regression\n");

    int ch1Sum = 0, ch2Sum = 0, ch3Sum = 0;
    
    double ch1mch1MeanSqSum = 0;
    double ch2mch2MeanSqSum = 0;
    double ch3mch3MeanSqSum = 0;


    T *inPtr1, *inPtr2;
    inPtr1 = (T *) inData[0]->GetScalarPointerForExtent(outExt);
    inPtr2 = (T *) inData[1]->GetScalarPointerForExtent(outExt);

    inData[0]->GetContinuousIncrements(outExt, inIncX, inIncY, inIncZ);
    outData[0]->GetIncrements(outIncX, outIncY,
                        outIncZ);
    
    maxX = outExt[1] - outExt[0];
    maxY = outExt[3] - outExt[2];
    maxZ = outExt[5] - outExt[4];
    
    vtkPointData* pd = outData[0]->GetPointData();
    pd->GetScalars()->SetName("Colocalization map");

     
    int maxval=(int)pow(2.0f,sizeof(T)*8.0f)-1;
    

    for (idxZ = 0; idxZ <= maxZ; idxZ++) {
        for (idxY = 0; idxY <= maxY; idxY++) {
            for (idxX = 0; idxX <= maxX; idxX++) {
                ch1 = (int) *inPtr1++;
                ch2 = (int) *inPtr2++;
                ch3 = ch1 + ch2;
                ch1Sum += ch1;
                ch2Sum += ch2;
                ch3Sum += ch3;
                if (ch1 + ch2 != 0)
                    N++;
            }
            inPtr1 += inIncY;
            inPtr2 += inIncY;
        }
        inPtr1 += inIncZ;
        inPtr2 += inIncZ;
    }
    double ch1Mean = ch1Sum / N;
    double ch2Mean = ch2Sum / N;
    double ch3Mean = ch3Sum / N;
    N = 0;
    inPtr1 = (T *) inData[0]->GetScalarPointerForExtent(outExt);
    inPtr2 = (T *) inData[1]->GetScalarPointerForExtent(outExt);

    for (idxZ = 0; idxZ <= maxZ; idxZ++) {
        for (idxY = 0; idxY <= maxY; idxY++) {
            for (idxX = 0; idxX <= maxX; idxX++) {
                ch1 = (int) *inPtr1++;
                ch2 = (int) *inPtr2++;
                if(ch1)Nnonzeroch1++;
                if(ch2)Nnonzeroch2++;
                ch3 = ch1 + ch2;
                ch1mch1MeanSqSum +=
                    (ch1 - ch1Mean) * (ch1 - ch1Mean);
                ch2mch2MeanSqSum +=
                    (ch2 - ch2Mean) * (ch2 - ch2Mean);
                ch3mch3MeanSqSum +=
                    (ch3 - ch3Mean) * (ch3 - ch3Mean);

                if (ch1 + ch2 == 0)
                    Nzero++;
                //calc pearsons for original image
                sumX = sumX + ch1;
                sumXY = sumXY + (ch1 * ch2);
                sumXX = sumXX + (ch1 * ch1);
                sumYY = sumYY + (ch2 * ch2);
                sumY = sumY + ch2;
                N++;
            }
            inPtr1 += inIncY;
            inPtr2 += inIncY;
        }
        inPtr1 += inIncZ;
        inPtr2 += inIncZ;
    }
    N = N - Nzero;
    calculate_pearson(&pearsons1, &pearsons2, &pearsons3,
    sumX, sumY, sumXX,sumYY,sumXY,N);        
    double rTotal = pearsons1 / (sqrt(float(pearsons2) * float(pearsons3)));

    //http://mathworld.wolfram.com/Covariance.html
    //?2 = X2?(X)2 
    // = E[X2]?(E[X])2 
    //var (x+y) = var(x)+var(y)+2(covar(x,y));
    //2(covar(x,y)) = var(x+y) - var(x)-var(y);

    double ch1Var = ch1mch1MeanSqSum / (N - 1);
    double ch2Var = ch2mch2MeanSqSum / (N - 1);
    double ch3Var = ch3mch3MeanSqSum / (N - 1);
    double ch1ch2covar = 0.5 * (ch3Var - (ch1Var + ch2Var));

    //do regression 
    //See:Dissanaike and Wang
    // http://papers.ssrn.com/sol3/papers.cfm?abstract_id=407560
    // 
    double denom = 2 * ch1ch2covar;
    double num =
        ch2Var - ch1Var +
        sqrt((  ch2Var - ch1Var) * (ch2Var - ch1Var) +
         (4 * ch1ch2covar * ch1ch2covar));

    double m = num / denom;
    double b = ch2Mean - m * ch1Mean;

    // Calculate the thresholds 
    printf("Calculating thresholds based on %d and %d\n",LowerThresholdCh1, LowerThresholdCh2);
    calculateThreshold<T>(self,id, inData,outExt, LowerThresholdCh1, LowerThresholdCh2,&ch1BestThresh, &m, &b, &pearsonsBelowTh);
    
    
    ch1threshmax = vtkMath::Round((ch1BestThresh));
    ch2threshmax = vtkMath::Round(((double) ch1BestThresh * (double) m) + (double) b);
    printf("Calculated ch1 threshmax = %f, ch2Threshmax = %f\n",ch1threshmax, ch2threshmax);    
    // If the user has specified the thresholds, then simply use them.
    // We still need to calculate them, to get the bestr2 value
    if(LowerThresholdCh1 >= 0) {
        ch1threshmax = LowerThresholdCh1;
    }
    if(LowerThresholdCh2 >= 0) {
        ch2threshmax = LowerThresholdCh2;
    }
    
    if(ch1threshmax>maxval)ch1threshmax=maxval;
    if(ch2threshmax>maxval)ch2threshmax=maxval;
    
    Nzero = Ncoloc = 0;
    sumColocCh1 = sumColocCh2 = 0;
       
    sumCh1gtT = sumCh2gtT = 0;
    mCh1coloc = mCh2coloc = 0;    
    sumCh1total = sumCh2total = 0;

    sumX = sumXY = sumXX = sumYY = sumY = N2 = N = Ncoloc = 0;
    
    //printf("Acquiring input pointers again.\n");
    inPtr1 = (T *) inData[0]->GetScalarPointerForExtent(outExt);
    inPtr2 = (T *) inData[1]->GetScalarPointerForExtent(outExt);
    
    for (idxZ = 0; idxZ <= maxZ; idxZ++) {
        if(!id) {
            sprintf(progressText,"Performing final regression (slice %d / %d)",idxZ,maxZ);
            self->SetProgressText(progressText);

            self->UpdateProgress(0.5+idxZ/float(maxZ));        
        }
        
        for (idxY = 0; idxY <= maxY; idxY++) {
            for (idxX = 0; idxX <= maxX; idxX++) {
                ch1 = (int) *inPtr1++;
                ch2 = (int) *inPtr2++;

                sumCh1total = sumCh1total + ch1;
                sumCh2total = sumCh2total + ch2;
                N++;

                if (ch1 + ch2 == 0)
                    Nzero++;
                if (ch1 > 0) {
                    Nch1++;
                    mCh2coloc = mCh2coloc + ch2;
                }
                if (ch2 > 0) {
                    Nch2++;
                    mCh1coloc = mCh1coloc + ch1;
                }

                if ((double) ch2 >= ch2threshmax && (double)ch2 <= UpperThresholdCh2) {
                    Nch2gtT++;
                    sumCh2gtT = sumCh2gtT + ch2;
                    colocX = colocX + ch1;
                }
                if ((double) ch1 >= ch1threshmax && (double)ch1 <= UpperThresholdCh1) {
                    Nch1gtT++;
                    sumCh1gtT = sumCh1gtT + ch1;
                    colocY = colocY + ch2;
                }
                //printf("upper=%d,%d\n",UpperThresholdCh1, UpperThresholdCh2);
                //printf("ch1=%d,ch2=%d,ch1threshmax=%f,ch2threshmax=%f\n",ch1,ch2,ch1threshmax,ch2threshmax);
                if (((double) ch1 >= ch1threshmax  && (double)ch1 <= UpperThresholdCh1)
                    && ((double) ch2 >= ch2threshmax)  && (double)ch2 <= UpperThresholdCh2) {
                    sumColocCh1 = sumColocCh1 + ch1;
                    sumColocCh2 = sumColocCh2 + ch2;
                    Ncoloc++;
                    
                    //calc pearsons
                    sumX = sumX + ch1;
                    sumXY = sumXY + (ch1 * ch2);
                    sumXX = sumXX + (ch1 * ch1);
                    sumYY = sumYY + (ch2 * ch2);
                    sumY = sumY + ch2;
                }
            }

            inPtr1 += inIncY;
            inPtr2 += inIncY;
        }
        inPtr1 += inIncZ;
        inPtr2 += inIncZ;
    }



    self->SetSlope(m);
    self->SetIntercept(b);

    calculate_pearson(&pearsons1, &pearsons2, &pearsons3,
    sumX, sumY, sumXX,sumYY,sumXY,N);   

    //Pearsons for colocalised volume
    double Rcoloc = pearsons1 / (sqrt(pearsons2 * pearsons3));

    self->SetPearsonWholeImage(rTotal);
    self->SetPearsonImageAbove(Rcoloc);
    self->SetPearsonImageBelow(pearsonsBelowTh);


    //Mander's original
    //[i.e. E(ch1if ch2>0) ÷ E(ch1total)]
    double M1 = mCh1coloc / sumCh1total;
    double M2 = mCh2coloc / sumCh2total;

    //printf("M2=%f,ch2coloc=%f,totalch2=%f\n",M2,mCh2coloc,sumCh2total);
    self->SetM1(M1);
    self->SetM2(M2);
    
    // Overlap coefficient k1 and k2
    // k_n = S1*S2/Sn
    double K1 = sqrt(sumCh1total*sumCh2total)/sqrt(sumCh1total*sumCh1total);
    double K2 = sqrt(sumCh1total*sumCh2total)/sqrt(sumCh2total*sumCh2total);
    self->SetK1(K1);
    self->SetK2(K2);
    //Manders using threshold
    //[i.e. E(ch1 if ch2>ch2threshold) ÷ (Ech1total)]
    double colocM1 = (double) colocX / (double) sumCh1total;
    double colocM2 = (double) colocY / (double) sumCh2total;
    self->SetThresholdM1(colocM1);
    self->SetThresholdM2(colocM2);

    //as in Costes' paper
    //[i.e. E(ch1>ch1threshold) ÷ E(ch1total)]

    double colocC1 = (double) sumCh1gtT / (double) sumCh1total;
    double colocC2 = (double) sumCh2gtT / (double) sumCh2total;
    self->SetC1(colocC1);
    self->SetC2(colocC2);

    //Imaris percentage volume
    double percVolCh1 = (double) Ncoloc / (double) Nch1gtT;
    double percVolCh2 = (double) Ncoloc / (double) Nch2gtT;

    self->SetPercentageVolumeCh1(percVolCh1);
    self->SetPercentageVolumeCh2(percVolCh2);

    double percTotCh1 = (double) sumColocCh1 / (double) sumCh1total;
    double percTotCh2 = (double) sumColocCh2 / (double) sumCh2total;
    self->SetPercentageTotalCh1(percTotCh1);
    self->SetPercentageTotalCh2(percTotCh2);

    //Imaris percentage material
    double percMatCh1 = (double) sumColocCh1 / (double) sumCh1gtT;
    double percMatCh2 = (double) sumColocCh2 / (double) sumCh2gtT;

    self->SetPercentageMaterialCh1(percMatCh1);
    self->SetPercentageMaterialCh2(percMatCh2);

    self->SetCh1ThresholdMax(ch1threshmax);
    self->SetCh2ThresholdMax(ch2threshmax);

    // Differential staining
    // Is calculated as the percentage of one channel to another
    // Where the colocalized voxels are subtracted from the second channel
    // 
    //             I_r 
    // DiffStain = ------------------
    //             I_g - I_coloc
    // Where I_coloc is the sum of intensities of colocalized voxels in green
    // channel
    
    
    self->SetDiffStainVoxelsCh1( (Nch1gtT)/float((Nch2gtT - Ncoloc)));
    self->SetDiffStainVoxelsCh2( (Nch2gtT)/float((Nch1gtT - Ncoloc)));
    
    self->SetOverThresholdCh1(Nch1gtT);
    self->SetOverThresholdCh2(Nch2gtT);
    self->SetNonZeroCh1(Nnonzeroch1);
    self->SetNonZeroCh2(Nnonzeroch2);
    
    self->SetDiffStainIntCh1( (sumCh1gtT)/float((sumCh2gtT - sumColocCh2)));
    self->SetDiffStainIntCh2( (sumCh2gtT)/float((sumCh1gtT - sumColocCh1)));
    
    self->SetColocAmount(Ncoloc);
    self->SetColocPercent((double)Ncoloc / (maxX * maxY * maxZ));

    self->SetSumOverThresholdCh1(sumCh1gtT);
    self->SetSumOverThresholdCh2(sumCh2gtT);
    self->SetSumCh1(sumCh1total);
    self->SetSumCh2(sumCh2total);
}

//----------------------------------------------------------------------------
// This method is passed a input and output regions, and executes the filter
// algorithm to fill the output from the inputs.
// It just executes a switch statement to call the correct function for
// the regions data types.
void vtkImageAutoThresholdColocalization::ThreadedExecute(vtkImageData **
                              inData,
                              vtkImageData **
                              outData,
                              int outExt[6],
                              int id)
{

    switch (inData[0]->GetScalarType()) {
        vtkTemplateMacro7
            (vtkImageAutoThresholdColocalizationExecute, this, id,
             this->NumberOfInputs, inData, outData, outExt,
             static_cast < VTK_TT * >(0));
    default:
        vtkErrorMacro(<<"Execute: Unknown ScalarType");
        return;
    }

}



//----------------------------------------------------------------------------
void vtkImageAutoThresholdColocalization::PrintSelf(ostream & os,
                            vtkIndent indent)
{
    this->Superclass::PrintSelf(os, indent);
    os << "\n";
    os << indent << "Channel 1 Threshold: " << Ch1ThresholdMax << "\n";
    os << indent << "Channel 2 Threshold: " << Ch2ThresholdMax << "\n";
    os << indent << "R_colocaliation: " << PearsonImageAbove << "\n";
    os << indent << "R_below: " << PearsonImageBelow << "\n";
    os << indent << "R_total: " << PearsonWholeImage << "\n";
    os << "\n";
    os << indent << "M1: " << M1 << "\n";
    os << indent << "M2: " << M2 << "\n";

    os << indent << "Colocalization M1: " << ThresholdM1 << "\n";
    os << indent << "Colocalization M2: " << ThresholdM2 << "\n";

    os << "\n";
    os << indent << "Amount of colocalization: " << ColocAmount <<
        "\n";
    os << indent << "Colocalization (% of volume): " << ColocPercent <<
        "\n";
    os << "\n";
    os << indent << "Colocalization (% of Ch1): " <<
        PercentageVolumeCh1 << "\n";
    os << indent << "Colocalization (% of Ch2): " <<
        PercentageVolumeCh2 << "\n";
    os << "\n";
    os << indent << "Colocalization (% of Ch1 Intensity): " <<
        PercentageTotalCh1 << "\n";
    os << indent << "Colocalization (% of Ch2 Intensity): " <<
        PercentageTotalCh2 << "\n";
    os << "\n";
    os << indent << "Colocalization (% of Ch1 Intensity > Threshold): "
        << PercentageMaterialCh1 << "\n";
    os << indent << "Colocalization (% of Ch2 Intensity > Threshold): "
        << PercentageMaterialCh2 << "\n";
    os << "\n";
    os << indent << "Sum of voxels > Threshold (Ch1): " <<
        SumOverThresholdCh1 << "\n";
    os << indent << "Sum of voxels > Threshold (Ch2): " <<
        SumOverThresholdCh2 << "\n";
    os << "\n";
    os << indent << "Sum of all voxels (Ch1): " << SumCh1 << "\n";
    os << indent << "Sum of all voxels (Ch2): " << SumCh2 << "\n";
}
