/*=========================================================================

  Program:   BioImageXD
  Module:    $RCSfile: vtkImageSimpleMIP.cxx,v $

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
#include "vtkImageSimpleMIP.h"

#include "vtkCellData.h"
#include "vtkImageData.h"
#include "vtkObjectFactory.h"
#include "vtkPointData.h"

#define PRT_EXT(ext) ext[0],ext[1],ext[2],ext[3],ext[4],ext[5]

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
    int wholeExt[6];
    //printf("Getting input update extent from output extent\n");
    //printf("inExt=%d,%d,%d,%d,%d,%d\n",inExt[0],inExt[1],inExt[2],inExt[3],inExt[4],inExt[5]);
    //printf("outExt=%d,%d,%d,%d,%d,%d\n",outExt[0],outExt[1],outExt[2],outExt[3],outExt[4],outExt[5]);
    this->GetInput()->GetWholeExtent(wholeExt);
    memcpy(inExt,wholeExt,sizeof(int)*6);
    
}

//-----------------------------------------------------------------------------
void 
vtkImageSimpleMIP::ExecuteInformation(vtkImageData *input, vtkImageData *output)
{
  this->vtkImageToImageFilter::ExecuteInformation( input, output );
  int wholeExt[6];
  this->GetInput()->GetWholeExtent(wholeExt);
  wholeExt[5]=0;
  // We're gonna produce image one slice thick
  output->SetWholeExtent(wholeExt);
//  printf("Setting number of components to %d\n",input->GetNumberOfScalarComponents());
  output->SetNumberOfScalarComponents(input->GetNumberOfScalarComponents());
  
}

//-----------------------------------------------------------------------------
void vtkImageSimpleMIP::ExecuteData(vtkDataObject *)
{
  int uExtent[6];
  printf("GetOutput()\n");
  vtkImageData* output = this->GetOutput();
  vtkImageData* input = this->GetInput();
  int inIncX,inIncY,inIncZ;
  int outIncX,outIncY,outIncZ;
  int maxX,maxY,maxZ,maxC;
  int idxX,idxY,idxZ,idxC;
  char *inPtr1;

  unsigned char scalar,outScalar;
  if(!output) {
      printf("No output\n");
  }
  output->GetUpdateExtent(uExtent);
  printf("update extent=%d,%d,%d,%d,%d,%d",PRT_EXT(uExtent));
  output->SetExtent(uExtent);

  // We will want the input update extent to be the one we go through
  input->GetUpdateExtent(uExtent);
  printf("Update extent is %d,%d,%d,%d,%d,%d",PRT_EXT(uExtent));
 
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
  maxC = input->GetNumberOfScalarComponents();
    
  input->GetIncrements(inIncX, inIncY, inIncZ);
  output->GetIncrements(outIncX, outIncY, outIncZ);
  //printf("inIncX=%d,inIncY=%d,inIncZ=%d\n",inIncX,inIncY,inIncZ);
  //printf("outIncX=%d,outIncY=%d,outIncZ=%d\n",outIncX,outIncY,outIncZ);
  printf("x=%d,y=%d,z=%d\n",maxX,maxY,maxZ);
  #define GET_AT(x,y,z,c,ptr) *(ptr+(z)*inIncZ+(y)*inIncY+(x)*inIncX+c)
  #define SET_AT(x,y,z,c,ptr,val) *(ptr+(z)*outIncZ+(y)*outIncY+(x)*outIncX+c)=val
  
  //printf("maxX=%d,maxY=%d,maxZ=%d\n",maxX,maxY,maxZ);
  for(idxZ = 0; idxZ <= maxZ; idxZ++ ) {
    UpdateProgress(idxZ/float(maxZ));
    for(idxY = 0; idxY <= maxY; idxY++ ) {
      for(idxX = 0; idxX <= maxX; idxX++ ) {
	  for(idxC = 0; idxC <= maxC; idxC++) {
	      scalar = GET_AT(idxX,idxY,idxZ,idxC,inPtr);
	      outScalar = GET_AT(idxX,idxY,0,idxC,outPtr);
	      if(scalar > outScalar) SET_AT(idxX,idxY,0,idxC,outPtr,scalar);
	  }
      }
    }  
  }
  
}


//-----------------------------------------------------------------------------
void vtkImageSimpleMIP::PrintSelf(ostream& os, vtkIndent indent)
{
  this->Superclass::PrintSelf(os,indent);

}




