/*=========================================================================

  Program:   Visualization Toolkit
  Module:    $RCSfile: vtkImageSimpleMIP.cxx,v $

  Copyright (c) Ken Martin, Will Schroeder, Bill Lorensen
  All rights reserved.
  See Copyright.txt or http://www.kitware.com/Copyright.htm for details.

     This software is distributed WITHOUT ANY WARRANTY; without even
     the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
     PURPOSE.  See the above copyright notice for more information.

=========================================================================*/
#include "vtkImageSimpleMIP.h"

#include "vtkCellData.h"
#include "vtkImageData.h"
#include "vtkObjectFactory.h"
#include "vtkPointData.h"

vtkCxxRevisionMacro(vtkImageSimpleMIP, "$Revision: 1.36 $");
vtkStandardNewMacro(vtkImageSimpleMIP);

//-----------------------------------------------------------------------------
// Construct object to extract all of the input data.
vtkImageSimpleMIP::vtkImageSimpleMIP()
{

}

//-----------------------------------------------------------------------------

void vtkImageSimpleMIP::ComputeInputUpdateExtent(int inExt[6], 
                                             int outExt[6])
{
    int i = 0, k = 0;
    int wholeExt[3];
    this->GetInput()->GetWholeExtent(wholeExt);
    memcpy(outExt,wholeExt,sizeof(int)*6);
    
}

//-----------------------------------------------------------------------------
void 
vtkImageSimpleMIP::ExecuteInformation(vtkImageData *input, vtkImageData *output)
{
  this->vtkImageToImageFilter::ExecuteInformation( input, output );
  int wholeExt[3];
  this->GetInput()->GetWholeExtent(wholeExt);
  wholeExt[5]=0;
  // We're gonna produce image one slice thick
  output->SetWholeExtent(wholeExt);
  
}

//-----------------------------------------------------------------------------
void vtkImageSimpleMIP::ExecuteData(vtkDataObject *)
{
  int uExtent[6];
  vtkImageData* output = this->GetOutput();
  vtkImageData* input = this->GetInput();
  int inIncX,inIncY,inIncZ;
  int outIncX,outIncY,outIncZ;
  int maxX,maxY,maxZ;
  int idxX,idxY,idxZ;
  char *inPtr1;

  unsigned char scalar,outScalar;

  output->GetUpdateExtent(uExtent);
  output->SetExtent(uExtent);

  // We will want the input update extent to be the one we go through
  input->GetUpdateExtent(uExtent);
 
  // Get pointers for input and output
  char *inPtr = (char *) input->GetScalarPointerForExtent(uExtent);
  char *outPtr = (char *) output->GetScalarPointerForExtent(uExtent);
      
  if(!input) {
    vtkErrorMacro("No input is specified.");
  } 
  if(this->UpdateExtentIsEmpty(output)) {
      return;
  }
  output->AllocateScalars();

  maxX = uExtent[1] - uExtent[0];
  maxY = uExtent[3] - uExtent[2];
  maxZ = uExtent[5] - uExtent[4];

  input->GetIncrements(inIncX, inIncY, inIncZ);
  output->GetIncrements(outIncX, outIncY, outIncZ);
  
  #define GET_AT(x,y,z,ptr) *(ptr+(z)*inIncZ+(y)*inIncY+(x)*inIncX)
  #define SET_AT(x,y,z,ptr,val) *(ptr+(z)*outIncZ+(y)*outIncY+(x)*outIncX)=val
  
//  printf("maxX=%d,maxY=%d,maxZ=%d\n",maxX,maxY,maxZ);
  for(idxZ = 0; idxZ <= maxZ; idxZ++ ) {
    
    for(idxY = 0; idxY <= maxY; idxY++ ) {
      for(idxX = 0; idxX <= maxX; idxX++ ) {          
          scalar = GET_AT(idxX,idxY,idxZ,inPtr);
          outScalar = GET_AT(idxX,idxY,0,outPtr);
          if(scalar > outScalar) SET_AT(idxX,idxY,0,outPtr,scalar);
      }
    }  
  }
  
}


//-----------------------------------------------------------------------------
void vtkImageSimpleMIP::PrintSelf(ostream& os, vtkIndent indent)
{
  this->Superclass::PrintSelf(os,indent);

}




