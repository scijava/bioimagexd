/*=========================================================================

  Program:   BioImageXD
  Module:    $RCSfile: vtkImageColocalizationFilter.cxx,v $

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
#include "vtkImageColocalizationFilter.h"

#include "vtkImageData.h"
#include "vtkObjectFactory.h"
#include "vtkImageProgressIterator.h"

vtkCxxRevisionMacro(vtkImageColocalizationFilter, "$Revision: 1.25 $");
vtkStandardNewMacro(vtkImageColocalizationFilter);

//----------------------------------------------------------------------------
vtkImageColocalizationFilter::vtkImageColocalizationFilter()
{
    this->OutputDepth = 8;
    this->NumberOfDatasets = 8;
    this->ColocalizationLowerThresholds = new int[this->NumberOfDatasets];
    this->ColocalizationUpperThresholds = new int[this->NumberOfDatasets];
    for(int i = 0; i < this->NumberOfDatasets; i++) {
        this->ColocalizationUpperThresholds[i]=255;
        this->ColocalizationLowerThresholds[i]=0;
    }
}

void vtkImageColocalizationFilter::SetColocalizationLowerThreshold(int dataset, int threshold) {
    int *NewThresholds;
    if (this->NumberOfDatasets < dataset) {            
            NewThresholds = new int[this->NumberOfDatasets *2];
            
            for(int i = 0; i< this->NumberOfDatasets ; i++) {
                NewThresholds[i] = this->ColocalizationLowerThresholds[i];
            }
            for(int i = this->NumberOfDatasets; i < this->NumberOfDatasets*2; i++) {
                NewThresholds[i]=0;
            }
            this->NumberOfDatasets *= 2;
            delete[] this->ColocalizationLowerThresholds;
            this->ColocalizationLowerThresholds = NewThresholds;
    }
    this->ColocalizationLowerThresholds[dataset] = threshold;
}
void vtkImageColocalizationFilter::SetColocalizationUpperThreshold(int dataset, int threshold) {
    int *NewThresholds;
    if (this->NumberOfDatasets < dataset) {
            
            NewThresholds = new int[this->NumberOfDatasets *2];
            
            for(int i = 0; i< this->NumberOfDatasets ; i++) {
                NewThresholds[i] = this->ColocalizationUpperThresholds[i];
            }
            for(int i = this->NumberOfDatasets; i < this->NumberOfDatasets*2; i++) {
                NewThresholds[i]=0;
            }
            this->NumberOfDatasets *= 2;
            delete[] this->ColocalizationUpperThresholds;
            this->ColocalizationUpperThresholds = NewThresholds;
    }
    this->ColocalizationUpperThresholds[dataset] = threshold;
}

//----------------------------------------------------------------------------
vtkImageColocalizationFilter::~vtkImageColocalizationFilter()
{
        delete[] this->ColocalizationLowerThresholds;
        delete[] this->ColocalizationUpperThresholds;
}

//----------------------------------------------------------------------------
void vtkImageColocalizationFilter::ExecuteInformation(vtkImageData **inputs, 
                                        vtkImageData *output)
{
  vtkImageMultipleInputFilter::ExecuteInformation(inputs,output);
 
}



//----------------------------------------------------------------------------
// This templated function executes the filter for any type of data.
template <class T>
void vtkImageColocalizationFilterExecute(vtkImageColocalizationFilter *self, int id,int NumberOfInputs, 
                           vtkImageData **inData,vtkImageData*outData,int outExt[6],
                            T*)
{
    int i;
    int inIncX,inIncY,inIncZ;
    int outIncX,outIncY,outIncZ;
    int maxX,maxY,maxZ;
    int idxX,idxY,idxZ;
    

    int *ColocThresholds = self->GetColocalizationLowerThresholds();
    int *UpperThresholds = self->GetColocalizationUpperThresholds();
    int BitDepth = self->GetOutputDepth();
    T** inPtrs;
    T* outPtr;
    inPtrs=new T*[NumberOfInputs];
    //printf("outext=[%d,%d,%d,%d,%d,%d]\n",outExt[0],outExt[1],outExt[2],outExt[3],outExt[4],outExt[5]);
    for(i=0; i < NumberOfInputs; i++) {
        inPtrs[i]=(T*)inData[i]->GetScalarPointerForExtent(outExt);
    }
    outPtr=(T*)outData->GetScalarPointerForExtent(outExt);
    
    
    inData[0]->GetContinuousIncrements(outExt,inIncX, inIncY, inIncZ);
    outData->GetContinuousIncrements(outExt,outIncX, outIncY, outIncZ);
    maxX = outExt[1] - outExt[0];
    maxY = outExt[3] - outExt[2];
    maxZ = outExt[5] - outExt[4];
    
    T currScalar = 0, ColocalizationScalar = 0;
    int maxval = 0, n = 0;
    char colocFlag = 0;
    double mul=0;
    maxval=int(pow(2,8*sizeof(T)))-1;
    //printf("Colocalization depth = %d, maxval=%d\n",BitDepth,maxval);
    char progressText[200];
    for(idxZ = 0; idxZ <= maxZ; idxZ++ ) {
        sprintf(progressText,"Calculating colocalization (slice %d / %d)",idxZ,maxZ);
        self->SetProgressText(progressText);
        self->UpdateProgress(idxZ/float(maxZ));
        
        for(idxY = 0; idxY <= maxY; idxY++ ) {
          for(idxX = 0; idxX <= maxX; idxX++ ) {
            currScalar = n = 0;
            colocFlag = 1;
            for(i=0; i < NumberOfInputs; i++ ) {
                currScalar = *inPtrs[i]; 
                if(currScalar > ColocThresholds[i] && currScalar < UpperThresholds[i]) {
                    ColocalizationScalar += currScalar;
                    n++;
                } else {
                    colocFlag = 0;
                }
                inPtrs[i]++;
            }
            if(colocFlag > 0) {
                
                if (BitDepth == 1 ) ColocalizationScalar = maxval;
                if (BitDepth == 8 ) ColocalizationScalar /= n;
                if(ColocalizationScalar > maxval) ColocalizationScalar=maxval;
                
            } else ColocalizationScalar = 0;
            
            *outPtr = ColocalizationScalar;
            outPtr++;
          }
          for(i=0; i < NumberOfInputs; i++ ) {
              inPtrs[i]+=inIncY;
          }
          outPtr += outIncY;
        }  
        for(i=0; i < NumberOfInputs; i++ ) {
          inPtrs[i]+=inIncZ;
        }
        outPtr += outIncZ;      
    }

    delete[] inPtrs;
}
//----------------------------------------------------------------------------
// This method is passed a input and output regions, and executes the filter
// algorithm to fill the output from the inputs.
// It just executes a switch statement to call the correct function for
// the regions data types.
void vtkImageColocalizationFilter::ThreadedExecute(vtkImageData **inData, 
                                     vtkImageData *outData,
                                     int outExt[6], int id)
{
  int idx1;
  int inExt[6], cOutExt[6];

  switch (inData[0]->GetScalarType())
  {
  vtkTemplateMacro7(vtkImageColocalizationFilterExecute, this, id, 
                    this->NumberOfInputs,inData, 
                    outData, outExt,static_cast<VTK_TT *>(0));
  default:
    vtkErrorMacro(<< "Execute: Unknown ScalarType");
  return;
  }    
    
}



//----------------------------------------------------------------------------
void vtkImageColocalizationFilter::PrintSelf(ostream& os, vtkIndent indent)
{
  this->Superclass::PrintSelf(os, indent);
}














