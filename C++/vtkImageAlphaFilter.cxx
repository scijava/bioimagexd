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

vtkCxxRevisionMacro(vtkImageAlphaFilter, "$Revision: 1.25 $");
vtkStandardNewMacro(vtkImageAlphaFilter);

//----------------------------------------------------------------------------
vtkImageAlphaFilter::vtkImageAlphaFilter()
{
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
void vtkImageAlphaFilter::ComputeInputUpdateExtent(int inExt[6],
                                              int outExt[6], int whichInput)
{
  int min, max, shift, tmp, idx;
  int *extent;

  if (this->GetInput() == NULL)
    {
    vtkErrorMacro("No input");
    return;
    }
  
  // default input extent will be that of output extent
  memcpy(inExt,outExt,sizeof(int)*6);
}



//----------------------------------------------------------------------------
// This templated function executes the filter for any type of data.
template <class T>
void vtkImageAlphaFilterExecute(vtkImageAlphaFilter *self, int id, 
                           int inExt[6], vtkImageData *inData, T *inPtr,
                           int outExt[6], vtkImageData *outData, T *outPtr)
{
  int idxR, idxY, idxZ;
  int maxY, maxZ;
  int inIncX, inIncY, inIncZ;
  int outIncX, outIncY, outIncZ;
  int rowLength;
  unsigned long count = 0;
  unsigned long target;
  int oldVal = 0, currVal = 0;

  // Get increments to march through data 
  inData->GetContinuousIncrements(inExt, inIncX, inIncY, inIncZ);
  outData->GetContinuousIncrements(outExt, outIncX, outIncY, outIncZ);

  // find the region to loop over
  rowLength = inExt[1] - inExt[0]
  maxY = inExt[3] - inExt[2]; 
  maxZ = inExt[5] - inExt[4];
  target = (unsigned long)((maxZ+1)*(maxY+1)/50.0);
  target++;
  

  // Loop through input pixels
  for (idxZ = 0; idxZ <= maxZ; idxZ++)
    {
    for (idxY = 0; !self->AbortExecute && idxY <= maxY; idxY++)
      {
      if (!id) 
        {
        if (!(count%target))
          {
          self->UpdateProgress(count/(50.0*target));
          }
        count++;
        }
      for (idxR = 0; idxR < rowLength; idxR++)
        {
        // Pixel operation
        oldVal = *outPtr;
        currVal = *inPtr;
        if( oldVal < currVal ) *outPtr = currVal;
        outPtr++;
        inPtr++;
        }
      outPtr += outIncY;
      inPtr += inIncY;
      }
    outPtr += outIncZ;
    inPtr += inIncZ;
    }
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
  void *inPtr;
  void *outPtr;

  if(this->MaximumMode) {
    
      for (idx1 = 0; idx1 < this->NumberOfInputs; ++idx1)
        {
        if (inData[idx1] != NULL)
          {
          // Get the input extent and output extent
          // the real out extent for this input may be clipped.
          memcpy(inExt, outExt, 6*sizeof(int));
          this->ComputeInputUpdateExtent(inExt, outExt, idx1);
          memcpy(cOutExt, inExt, 6*sizeof(int));
          
          // doo a quick check to see if the input is used at all.
          if (inExt[this->AlphaFilterAxis*2] <= inExt[this->AlphaFilterAxis*2 + 1])
            {
            inPtr = inData[idx1]->GetScalarPointerForExtent(inExt);
            outPtr = outData->GetScalarPointerForExtent(cOutExt);
    
            if (inData[idx1]->GetNumberOfScalarComponents() !=
                outData->GetNumberOfScalarComponents())
              {
              vtkErrorMacro("Components of the inputs do not match");
              return;
              }
            
            // this filter expects that input is the same type as output.
            if (inData[idx1]->GetScalarType() != outData->GetScalarType())
              {
              vtkErrorMacro(<< "Execute: input" << idx1 << " ScalarType (" << 
                  inData[idx1]->GetScalarType() << 
                  "), must match output ScalarType (" << outData->GetScalarType() 
                  << ")");
              return;
              }
                switch (inData[idx1]->GetScalarType())
                  {
                  vtkTemplateMacro8(vtkImageAlphaFilterExecute, this, id, 
                                    inExt, inData[idx1], (VTK_TT *)(inPtr),
                                    cOutExt, outData, (VTK_TT *)(outPtr));
                  default:
                    vtkErrorMacro(<< "Execute: Unknown ScalarType");
                  return;
                  }
            }
          }
        }
    }
}



//----------------------------------------------------------------------------
void vtkImageAlphaFilter::PrintSelf(ostream& os, vtkIndent indent)
{
  this->Superclass::PrintSelf(os, indent);
}














