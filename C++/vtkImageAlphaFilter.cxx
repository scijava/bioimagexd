/*=========================================================================

  Program:   Visualization Toolkit
  Module:    $RCSfile: vtkImageAlphaFilter.cxx,v $

  Copyright (c) Ken Martin, Will Schroeder, Bill Lorensen
  All rights reserved.
  See Copyright.txt or http://www.kitware.com/Copyright.htm for details.

     This software is distributed WITHOUT ANY WARRANTY; without even
     the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
     PURPOSE.  See the above copyright notice for more information.

=========================================================================*/
#include "vtkImageAlphaFilter.h"

#include "vtkImageData.h"
#include "vtkObjectFactory.h"
#include "vtkImageProgressIterator.h"

vtkCxxRevisionMacro(vtkImageAlphaFilter, "$Revision: 1.25 $");
vtkStandardNewMacro(vtkImageAlphaFilter);

//----------------------------------------------------------------------------
vtkImageAlphaFilter::vtkImageAlphaFilter()
{
    this->AverageMode = 0;
    this->MaximumMode = 0;
    this->AverageThreshold = 10;
}

//----------------------------------------------------------------------------
vtkImageAlphaFilter::~vtkImageAlphaFilter()
{
}

//----------------------------------------------------------------------------
// This method tells the ouput it will have more components
void vtkImageAlphaFilter::ExecuteInformation(vtkImageData **inputs, 
                                        vtkImageData *output)
{
  vtkImageMultipleInputFilter::ExecuteInformation(inputs,output);
 
}



//----------------------------------------------------------------------------
// This templated function executes the filter for any type of data.
template <class T>
void vtkImageAlphaFilterExecute(vtkImageAlphaFilter *self, int id,int NumberOfInputs, 
                           vtkImageData **inData,vtkImageData*outData,int outExt[6],
                            T*)
{
    int i;
    int inIncX,inIncY,inIncZ;
    int outIncX,outIncY,outIncZ;
    int maxX,maxY,maxZ;
    int idxX,idxY,idxZ;
    int AvgThreshold = self->GetAverageThreshold();
    int MaxMode = self->GetMaximumMode();					
    int AvgMode = self->GetAverageMode();
    if(!MaxMode&&!AvgMode)AvgMode=1;
    printf("Using average mode=%d, maxMode=%d, threshold=%d\n",AvgMode,MaxMode,AvgThreshold);
    T** inPtrs;
    T* outPtr;
    inPtrs=new T*[NumberOfInputs];
    printf("outext=[%d,%d,%d,%d,%d,%d]\n",outExt[0],outExt[1],outExt[2],outExt[3],outExt[4],outExt[5]);
    for(i=0; i < NumberOfInputs; i++) {
        inPtrs[i]=(T*)inData[i]->GetScalarPointerForExtent(outExt);
    }
    outPtr=(T*)outData->GetScalarPointerForExtent(outExt);
    
    
    inData[0]->GetContinuousIncrements(outExt,inIncX, inIncY, inIncZ);
    outData->GetContinuousIncrements(outExt,outIncX, outIncY, outIncZ);
    maxX = outExt[1] - outExt[0];
    maxY = outExt[3] - outExt[2];
    maxZ = outExt[5] - outExt[4];
    
    T scalar = 0, currScalar = 0, alphaScalar = 0;
    int maxval = 0, n = 0;
    maxval=int(pow(2,8*sizeof(T)))-1;
    printf("maxval=%d\n",maxval);
    T val;
    
    for(idxZ = 0; idxZ <= maxZ; idxZ++ ) {
        for(idxY = 0; idxY <= maxY; idxY++ ) {
          for(idxX = 0; idxX <= maxX; idxX++ ) {
            scalar = currScalar = n = 0;
	    alphaScalar = 0;
            for(i=0; i < NumberOfInputs; i++ ) {
                currScalar = *inPtrs[i];                            
                    if(MaxMode) {
                        if(alphaScalar < currScalar) {
                            alphaScalar = currScalar;
                        }
                    // If the alpha channel should be in "average mode"
                    // then we take an average of all the scalars in the
                    // current voxel that are above the AverageThreshold
                    } else if(AvgMode) {
                        if(currScalar > AvgThreshold) {
                            n++;
                            alphaScalar += currScalar;
                        }
                    }
                inPtrs[i]++;
            }

	    if(AvgMode && n>0) alphaScalar /= n;
            if(alphaScalar > maxval)alphaScalar=maxval;
	    *outPtr = alphaScalar;
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
void vtkImageAlphaFilter::ThreadedExecute(vtkImageData **inData, 
                                     vtkImageData *outData,
                                     int outExt[6], int id)
{
  int idx1;
  int inExt[6], cOutExt[6];

  switch (inData[0]->GetScalarType())
  {
  vtkTemplateMacro7(vtkImageAlphaFilterExecute, this, id, 
                    this->NumberOfInputs,inData, 
                    outData, outExt,static_cast<VTK_TT *>(0));
  default:
    vtkErrorMacro(<< "Execute: Unknown ScalarType");
  return;
  }    
    
}



//----------------------------------------------------------------------------
void vtkImageAlphaFilter::PrintSelf(ostream& os, vtkIndent indent)
{
  this->Superclass::PrintSelf(os, indent);
}














