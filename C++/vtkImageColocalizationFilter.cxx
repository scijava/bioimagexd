/*=========================================================================

  Program:   Visualization Toolkit
  Module:    $RCSfile: vtkImageColocalizationFilter.cxx,v $

  Copyright (c) Ken Martin, Will Schroeder, Bill Lorensen
  All rights reserved.
  See Copyright.txt or http://www.kitware.com/Copyright.htm for details.

     This software is distributed WITHOUT ANY WARRANTY; without even
     the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
     PURPOSE.  See the above copyright notice for more information.

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
    this->LeastVoxelsOverThreshold = 0;
    this->ColocalizationAmount = 0;
    this->NumberOfDatasets = 8;
    this->ColocalizationThresholds = new int[this->NumberOfDatasets];
    for(int i = 0; i < this->NumberOfDatasets; i++) this->ColocalizationThresholds[i]=0;
}

void vtkImageColocalizationFilter::SetColocalizationThreshold(int dataset, int threshold) {
    int *NewThresholds;
    if (this->NumberOfDatasets < dataset) {
            
            NewThresholds = new int[this->NumberOfDatasets *2];
            
            for(int i = 0; i< this->NumberOfDatasets ; i++) {
                NewThresholds[i] = this->ColocalizationThresholds[i];
            }
            for(int i = this->NumberOfDatasets; i < this->NumberOfDatasets*2; i++) {
                NewThresholds[i]=0;
            }
            this->NumberOfDatasets *= 2;
            delete[] this->ColocalizationThresholds;
            this->ColocalizationThresholds = NewThresholds;
    }
    this->ColocalizationThresholds[dataset] = threshold;
}

//----------------------------------------------------------------------------
vtkImageColocalizationFilter::~vtkImageColocalizationFilter()
{
}

//----------------------------------------------------------------------------
// This method tells the ouput it will have more components
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

    int ColocalizationAmount = 0, LeastVoxelsOverThreshold = 0;

    int *ColocThresholds = self->GetColocalizationThresholds();
    int BitDepth = self->GetOutputDepth();
    int *ColocVoxels;
    T** inPtrs;
    T* outPtr;
    ColocVoxels = new int[NumberOfInputs];
    inPtrs=new T*[NumberOfInputs];
    printf("outext=[%d,%d,%d,%d,%d,%d]\n",outExt[0],outExt[1],outExt[2],outExt[3],outExt[4],outExt[5]);
    for(i=0; i < NumberOfInputs; i++) {
        inPtrs[i]=(T*)inData[i]->GetScalarPointerForExtent(outExt);
        ColocVoxels[i] = 0;
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
    maxval=int(pow(2,8*sizeof(T)))-1;
    printf("Colocalization depth = %d, maxval=%d\n",BitDepth,maxval);
    
    for(idxZ = 0; idxZ <= maxZ; idxZ++ ) {
        for(idxY = 0; idxY <= maxY; idxY++ ) {
          for(idxX = 0; idxX <= maxX; idxX++ ) {
            currScalar = n = 0;
            colocFlag = 1;
            for(i=0; i < NumberOfInputs; i++ ) {
                currScalar = *inPtrs[i]; 
                if(currScalar > ColocThresholds[i]) {
                    ColocVoxels[i]++;
                    ColocalizationScalar += currScalar;
                    n++;
                } else colocFlag = 0;
                inPtrs[i]++;
            }
            ColocalizationAmount += colocFlag;
            if (colocFlag == 0)    ColocalizationScalar = 0;
            else if (BitDepth == 1 ) ColocalizationScalar = maxval;
            else if (BitDepth == 8 ) ColocalizationScalar /= n;
            if(ColocalizationScalar > maxval) ColocalizationScalar=maxval;
            
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
    // Assume that every voxel was colocalizing
    LeastVoxelsOverThreshold = outExt[1]*outExt[3]*outExt[5];
    // Then find out what was the real lowest count of colocalized voxels
    for (i=0; i  < NumberOfInputs; i++) {
        if (ColocVoxels[i] < LeastVoxelsOverThreshold) LeastVoxelsOverThreshold = ColocVoxels[i];
    }
    delete[] ColocVoxels;
    self->SetLeastVoxelsOverThreshold(LeastVoxelsOverThreshold);
    self->SetColocalizationAmount(ColocalizationAmount);
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














