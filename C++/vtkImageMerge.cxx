/*=========================================================================

  Program:   Visualization Toolkit
  Module:    $RCSfile: vtkImageMerge.cxx,v $

  Copyright (c) Ken Martin, Will Schroeder, Bill Lorensen
  All rights reserved.
  See Copyright.txt or http://www.kitware.com/Copyright.htm for details.

     This software is distributed WITHOUT ANY WARRANTY; without even
     the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
     PURPOSE.  See the above copyright notice for more information.

=========================================================================*/
#include "vtkImageMerge.h"

#include "vtkImageData.h"
#include "vtkObjectFactory.h"

vtkCxxRevisionMacro(vtkImageMerge, "$Revision: 1.25 $");
vtkStandardNewMacro(vtkImageMerge);

//----------------------------------------------------------------------------
vtkImageMerge::vtkImageMerge()
{
}

//----------------------------------------------------------------------------
vtkImageMerge::~vtkImageMerge()
{
}

//----------------------------------------------------------------------------
// This method tells the ouput it will have more components
void vtkImageMerge::ExecuteInformation(vtkImageData **inputs, 
                                        vtkImageData *output)
{
  vtkImageMultipleInputFilter::ExecuteInformation(inputs,output);
}



//----------------------------------------------------------------------------
// This templated function executes the filter for any type of data.
template <class T>
void vtkImageMergeExecute(vtkImageMerge *self, int id,int NumberOfInputs,
                           vtkImageData **inData,vtkImageData*outData,int outExt[6],
                            T*)
{
    int i;
    int inIncX,inIncY,inIncZ;
    int outIncX,outIncY,outIncZ;
    int maxX,maxY,maxZ;
    int idxX,idxY,idxZ;

    T** inPtrs;
    T* outPtr;
    inPtrs=new T*[NumberOfInputs];
    for(i=0; i < NumberOfInputs; i++) {
        inPtrs[i]=(T*)inData[i]->GetScalarPointerForExtent(outExt);
    }
    outPtr=(T*)outData->GetScalarPointerForExtent(outExt);
    
    
    inData[0]->GetContinuousIncrements(outExt,inIncX, inIncY, inIncZ);
    outData->GetContinuousIncrements(outExt,outIncX, outIncY, outIncZ);
    maxX = outExt[1] - outExt[0];
    maxY = outExt[3] - outExt[2];
    maxZ = outExt[5] - outExt[4];
    
    T scalar = 0, currScalar = 0;
    int maxval = 0, n = 0;
    maxval=int(pow(2,8*sizeof(T)));
    T val;
    maxX *= (inData[0]->GetNumberOfScalarComponents());
    for(idxZ = 0; idxZ <= maxZ; idxZ++ ) {
        for(idxY = 0; idxY <= maxY; idxY++ ) {
          for(idxX = 0; idxX <= maxX; idxX++ ) {
            scalar = currScalar = 0;
            for(i=0; i < NumberOfInputs; i++ ) {
                currScalar = *inPtrs[i];
                scalar += currScalar;
                inPtrs[i]++;
            }
            if(scalar > maxval)scalar=maxval;
            *outPtr = scalar;
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
void vtkImageMerge::ThreadedExecute(vtkImageData **inData, 
                                     vtkImageData *outData,
                                     int outExt[6], int id)
{
  int idx1;
  int inExt[6], cOutExt[6];

  switch (inData[0]->GetScalarType())
  {
  vtkTemplateMacro7(vtkImageMergeExecute, this, id, 
                    this->NumberOfInputs,inData, 
                    outData, outExt,static_cast<VTK_TT *>(0));
  default:
    vtkErrorMacro(<< "Execute: Unknown ScalarType");
  return;
  }    
    
}



//----------------------------------------------------------------------------
void vtkImageMerge::PrintSelf(ostream& os, vtkIndent indent)
{
  this->Superclass::PrintSelf(os, indent);
}














