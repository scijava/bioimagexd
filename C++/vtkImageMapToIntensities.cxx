/*=========================================================================

  Program:   Visualization Toolkit
  Module:    $RCSfile: vtkImageMapToIntensities.cxx,v $

  Copyright (c) Ken Martin, Will Schroeder, Bill Lorensen
  All rights reserved.
  See Copyright.txt or http://www.kitware.com/Copyright.htm for details.

     This software is distributed WITHOUT ANY WARRANTY; without even
     the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
     PURPOSE.  See the above copyright notice for more information.

=========================================================================*/
#include "vtkImageMapToIntensities.h"

#include "vtkCellData.h"
#include "vtkImageData.h"
#include "vtkObjectFactory.h"
#include "vtkPointData.h"

vtkCxxRevisionMacro(vtkImageMapToIntensities, "$Revision: 1.36 $");
vtkStandardNewMacro(vtkImageMapToIntensities);

//-----------------------------------------------------------------------------
// Construct object to extract all of the input data.
vtkImageMapToIntensities::vtkImageMapToIntensities()
{
    this->IntensityTransferFunction = 0;
}

//-----------------------------------------------------------------------------
// Get ALL of the input.
void vtkImageMapToIntensities::ComputeInputUpdateExtent(int inExt[6], 
                                             int *)
{
  // request all of the VOI
  int *wholeExtent;
  int i;
  
  wholeExtent = this->GetInput()->GetWholeExtent();
  memcpy(inExt, wholeExtent, 6*sizeof(int));

}

//-----------------------------------------------------------------------------
void 
vtkImageMapToIntensities::ExecuteInformation(vtkImageData *input, vtkImageData *output)
{
  this->vtkImageToImageFilter::ExecuteInformation( input, output );
}

//-----------------------------------------------------------------------------
void vtkImageMapToIntensities::ExecuteData(vtkDataObject *)
{
  int uExtent[6];
  vtkImageData* output = this->GetOutput();
  vtkImageData* input = this->GetInput();
  int inIncX,inIncY,inIncZ;
  int outIncX,outIncY,outIncZ;
  int maxX,maxY,maxZ;
  int idxX,idxY,idxZ;
  char *inPtr1;
  int* table;

  unsigned char scalar,newScalar,cmpScalar;

  //output->GetUpdateExtent(uExtent);
  output->GetUpdateExtent(uExtent);
  output->SetExtent(uExtent);
  if(!this->IntensityTransferFunction) {
      vtkErrorMacro("No IntensityTransferFunction specified");
  }
  table = this->IntensityTransferFunction->GetDataPointer();
  char *inPtr = (char *) input->GetScalarPointerForExtent(uExtent);
  char *outPtr = (char *) output->GetScalarPointerForExtent(uExtent);
    
  //output->GetDimensions(dims);
  
  if(!input) {
    vtkErrorMacro("No input is specified.");
  } 
  if(this->UpdateExtentIsEmpty(output)) {
      return;
  }
//  output->SetExtent(output->GetWholeExtent());
  output->AllocateScalars();
  if (this->IntensityTransferFunction->IsIdentical()) {
      printf("Identical function!\n");
      output->DeepCopy(input);
      return;
  }
  input->GetContinuousIncrements(uExtent,inIncX, inIncY, inIncZ);
  output->GetContinuousIncrements(uExtent,outIncX, outIncY, outIncZ);
  maxX = uExtent[1] - uExtent[0];
  maxY = uExtent[3] - uExtent[2];
  maxZ = uExtent[5] - uExtent[4];
  
  //inIncX *= input->GetScalarSize();
  //inIncY *= input->GetScalarSize();
  //inIncZ *= input->GetScalarSize();

  
  #define GET_AT(x,y,z,ptr) *(ptr+(z)*inIncZ+(y)*inIncY+(x)*inIncX)
  
  for(idxZ = 0; idxZ <= maxZ; idxZ++ ) {
    
    for(idxY = 0; idxY <= maxY; idxY++ ) {
      for(idxX = 0; idxX <= maxX; idxX++ ) {
          scalar = *inPtr++;
          newScalar=table[scalar];
          *outPtr++=newScalar;
      }
      inPtr += inIncY;
      outPtr += outIncY;
    }  
    inPtr += inIncZ;
    outPtr += outIncZ;      
  }
  
}


//-----------------------------------------------------------------------------
void vtkImageMapToIntensities::PrintSelf(ostream& os, vtkIndent indent)
{
  this->Superclass::PrintSelf(os,indent);

  os << indent << "IntensityTransferFunction "<< this->IntensityTransferFunction << "\n";

}




