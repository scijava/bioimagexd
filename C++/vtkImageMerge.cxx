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
  int idx;
  int min, max, size, tmp;
  int *inExt, outExt[6];
  int unionExt[6];

  if (inputs[0] == NULL)
    {
    vtkErrorMacro("No input");
    return;
    }
  
  // Initialize the union.
  unionExt[0] = unionExt[2] = unionExt[4] = VTK_LARGE_INTEGER;
  unionExt[1] = unionExt[3] = unionExt[5] = -VTK_LARGE_INTEGER;

  // Initialize the shifts.
  if (this->Shifts)
    {
    delete [] this->Shifts;
    }
  this->Shifts = new int [this->NumberOfInputs];
  
  // Find the outMin/max of the AlphaFiltered axis for this input.
  inExt = inputs[0]->GetWholeExtent();
  min = tmp = inExt[this->AlphaFilterAxis * 2];
  for (idx = 0; idx < this->NumberOfInputs; ++idx)
    {
    if (inputs[idx] != NULL)
      {
      inExt = inputs[idx]->GetWholeExtent();

      if (this->PreserveExtents)
        {
        // Compute union for preseving extents.
        if (inExt[0] < unionExt[0])
          {
          unionExt[0] = inExt[0];
          }
        if (inExt[1] > unionExt[1])
          {
          unionExt[1] = inExt[1];
          }
        if (inExt[2] < unionExt[2])
          {
          unionExt[2] = inExt[2];
          }
        if (inExt[3] > unionExt[3])
          {
          unionExt[3] = inExt[3];
          }
        if (inExt[4] < unionExt[4])
          {
          unionExt[4] = inExt[4];
          }
        if (inExt[5] > unionExt[5])
          {
          unionExt[5] = inExt[5];
          }
        this->Shifts[idx] = 0;
        }
      else
        {
        // Compute shifts if we are not preserving extents.
        this->Shifts[idx] = tmp - inExt[this->AlphaFilterAxis*2];
        size = inExt[this->AlphaFilterAxis*2 + 1] - inExt[this->AlphaFilterAxis*2] + 1;
        tmp += size;
        }
      }
    }
  
  inputs[0]->GetWholeExtent(outExt);

  if (this->PreserveExtents)
    {
    output->SetWholeExtent(unionExt);
    }
  else
    {
    max = tmp - 1;
    outExt[this->AlphaFilterAxis*2] = min;
    outExt[this->AlphaFilterAxis*2 + 1] = max;
    output->SetWholeExtent(outExt);
    }
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

  // Find the outMin/max of the AlphaFiltered axis for this input.
  extent = this->GetInput(whichInput)->GetWholeExtent();
  shift = 0;
  if ( ! this->PreserveExtents)
    {
    shift = this->Shifts[whichInput];
    }
  min = extent[this->AlphaFilterAxis*2] + shift;
  max = extent[this->AlphaFilterAxis*2 + 1] + shift;

  // now clip the outExtent against the outExtent for this input (intersect)
  tmp = outExt[this->AlphaFilterAxis*2];
  if (min < tmp) {min = tmp;}
  tmp = outExt[this->AlphaFilterAxis*2 + 1];
  if (max > tmp) {max = tmp;}
  
  // now if min > max, we do not need the input at all.  I assume
  // the pipeline will interpret this extent this way.
  
  // convert back into input coordinates.
  inExt[this->AlphaFilterAxis*2] = min - shift;
  inExt[this->AlphaFilterAxis*2 + 1] = max - shift;
  
  // for robustness (in the execute method), 
  // do not ask for more than the whole extent of the other axes.
  for (idx = 0; idx < 3; ++idx)
    {
    if (inExt[idx*2] < extent[idx*2])
      {
      inExt[idx*2] = extent[idx*2];
      }
    if (inExt[idx*2 + 1] > extent[idx*2 + 1])
      {
      inExt[idx*2 + 1] = extent[idx*2 + 1];
      }
    }
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

  // Get increments to march through data 
  inData->GetContinuousIncrements(inExt, inIncX, inIncY, inIncZ);
  outData->GetContinuousIncrements(outExt, outIncX, outIncY, outIncZ);

  // find the region to loop over
  rowLength = (inExt[1] - inExt[0]+1)*inData->GetNumberOfScalarComponents();
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
        *outPtr = *inPtr;
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
void vtkImageAlphaFilter::InitOutput(int outExt[6], vtkImageData *outData)
{
  int idxY, idxZ;
  int maxY, maxZ;
  int outIncX, outIncY, outIncZ;
  int rowLength;
  int typeSize;
  unsigned char *outPtrZ, *outPtrY;
  

  typeSize = outData->GetScalarSize();  
  outPtrZ = (unsigned char *)(outData->GetScalarPointerForExtent(outExt));

  // Get increments to march through data 
  outData->GetIncrements(outIncX, outIncY, outIncZ);
  outIncX *= typeSize;
  outIncY *= typeSize;
  outIncZ *= typeSize;

  // Find the region to loop over
  rowLength = (outExt[1] - outExt[0]+1)*outData->GetNumberOfScalarComponents();
  rowLength *= typeSize;
  maxY = outExt[3] - outExt[2]; 
  maxZ = outExt[5] - outExt[4];

  // Loop through input pixels
  for (idxZ = 0; idxZ <= maxZ; idxZ++)
    {
    outPtrY = outPtrZ;
    for (idxY = 0; idxY <= maxY; idxY++)
      {
      memset(outPtrY, 0, rowLength);
      outPtrY += outIncY;
      }
    outPtrZ += outIncZ;
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
  
  this->InitOutput(outExt, outData);

  for (idx1 = 0; idx1 < this->NumberOfInputs; ++idx1)
    {
    if (inData[idx1] != NULL)
      {
      // Get the input extent and output extent
      // the real out extent for this input may be clipped.
      memcpy(inExt, outExt, 6*sizeof(int));
      this->ComputeInputUpdateExtent(inExt, outExt, idx1);
      memcpy(cOutExt, inExt, 6*sizeof(int));
      cOutExt[this->AlphaFilterAxis*2] = 
      inExt[this->AlphaFilterAxis*2] + this->Shifts[idx1];
      cOutExt[this->AlphaFilterAxis*2 + 1] = 
      inExt[this->AlphaFilterAxis*2 + 1] + this->Shifts[idx1];
      
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



//----------------------------------------------------------------------------
void vtkImageAlphaFilter::PrintSelf(ostream& os, vtkIndent indent)
{
  this->Superclass::PrintSelf(os, indent);
  os << indent << "AlphaFilterAxis: " << this->AlphaFilterAxis << endl;
  os << indent << "PreserveExtents: " << this->PreserveExtents << endl;
}














