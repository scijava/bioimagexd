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
void 
vtkImageMapToIntensities::ExecuteInformation(vtkImageData *input, vtkImageData *output)
{
  this->vtkImageToImageFilter::ExecuteInformation( input, output );
  output->SetNumberOfScalarComponents(input->GetNumberOfScalarComponents());
}

//-----------------------------------------------------------------------------
void vtkImageMapToIntensities::ExecuteData(vtkDataObject *)
{
  int uExtent[6];
  vtkImageData* output = this->GetOutput();
  vtkImageData* input = this->GetInput();
  int inIncX,inIncY,inIncZ;
  int outIncX,outIncY,outIncZ;
  int maxX,maxY,maxZ,maxC;
  int idxX,idxY,idxZ,idxC;
  char *inPtr1;
  int* table;

  unsigned char scalar,newScalar,cmpScalar;

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
  printf("uExtent=(%d,%d,%d,%d,%d,%d)\n",uExtent[0],uExtent[1],uExtent[2],uExtent[3],uExtent[4],uExtent[5]);
  maxX = uExtent[1] - uExtent[0];
  maxY = uExtent[3] - uExtent[2];
  maxZ = uExtent[5] - uExtent[4];
  maxC = input->GetNumberOfScalarComponents();
  printf("maxX=%d,maxY=%d,maxZ=%d, maxC=%d\n",maxX,maxY,maxZ,maxC);
  //inIncX *= input->GetScalarSize();
  //inIncY *= input->GetScalarSize();
  //inIncZ *= input->GetScalarSize();

  
  #define GET_AT(x,y,z,ptr) *(ptr+(z)*inIncZ+(y)*inIncY+(x)*inIncX)
  
  for(idxZ = 0; idxZ <= maxZ; idxZ++ ) {
    for(idxY = 0; idxY <= maxY; idxY++ ) {
      for(idxX = 0; idxX <= maxX; idxX++ ) {
          for(idxC = 0; idxC <= maxC; idxC++ ) {
            scalar = *inPtr++;
            newScalar=table[scalar];
            *outPtr++=newScalar;
          }
      }
      inPtr += inIncY;
      outPtr += outIncY;
    }  
    inPtr += inIncZ;
    outPtr += outIncZ;      
  }
  
}

void vtkImageMapToIntensities::ComputeInputUpdateExtent(int inExt[6], int outExt[6]) {

//    printf("required extent for (%d,%d,%d,%d,%d,%d)\n",outExt[0],outExt[1],outExt[2],outExt[3],outExt[4],outExt[5]);    
    memcpy(inExt,outExt,6*sizeof(int));
}


//-----------------------------------------------------------------------------
void vtkImageMapToIntensities::PrintSelf(ostream& os, vtkIndent indent)
{
  this->Superclass::PrintSelf(os,indent);

  os << indent << "IntensityTransferFunction "<< this->IntensityTransferFunction << "\n";

}




