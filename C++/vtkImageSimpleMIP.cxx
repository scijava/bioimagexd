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
#define PRT_EXT2(ext) ext[0]<<","<<ext[1]<<","<<ext[2]<<","<<ext[3]<<","<<ext[4]<<","<<ext[5]
vtkCxxRevisionMacro(vtkImageSimpleMIP, "$Revision: 1.36 $");
vtkStandardNewMacro(vtkImageSimpleMIP);

//-----------------------------------------------------------------------------
// Construct object to extract all of the input data.
vtkImageSimpleMIP::vtkImageSimpleMIP()
{

}

//-----------------------------------------------------------------------------

// Given an xyz output extend, determine what input extent we need in order to execute
void vtkImageSimpleMIP::ComputeInputUpdateExtent(int inExt[6],
                                             int outExt[6])
{
    int i = 0, k = 0;
    int wholeExt[6];
    vtkDebugMacro("MIP: Getting input update extent from output extent\n");
    vtkDebugMacro("MIP: outExt="<<PRT_EXT2(outExt)<<"\n");
    this->GetInput()->GetWholeExtent(wholeExt);
    memcpy(wholeExt,inExt,sizeof(int)*6);
    
}

//-----------------------------------------------------------------------------
void
vtkImageSimpleMIP::ExecuteInformation(vtkImageData *input, vtkImageData *output)
{

  int wholeExt[6];
  this->GetInput()->GetWholeExtent(wholeExt);
  this->GetInput()->SetUpdateExtent(wholeExt);   
  this->vtkImageToImageFilter::ExecuteInformation( input, output ); 
  wholeExt[5]=0;
  // We're gonna produce image one slice thick
  output->SetWholeExtent(wholeExt);
  vtkDebugMacro("MIP: Setting number of components to "<<input->GetNumberOfScalarComponents()<<"\n");
  int ncomps = input->GetNumberOfScalarComponents();
  if(ncomps>3)ncomps=3;
  output->SetNumberOfScalarComponents(ncomps);
  
}

//-----------------------------------------------------------------------------
void vtkImageSimpleMIP::ExecuteData(vtkDataObject *)
{
  int uExtent[6];
  vtkImageData* output = this->GetOutput();
  vtkImageData* input = this->GetInput();
  int inIncX,inIncY,inIncZ;
  int outIncX,outIncY,outIncZ;
  int maxX,maxY,maxZ,maxC;
  int idxX,idxY,idxZ,idxC;
  char *inPtr1;

  unsigned char scalar,outScalar;
  if(!output) {
      vtkDebugMacro("MIP: No output\n");
  }
  output->GetUpdateExtent(uExtent);
  vtkDebugMacro("MIP: update extent of output="<<PRT_EXT2(uExtent)<<"\n");
  output->SetExtent(uExtent);
  input->GetUpdateExtent(uExtent);
  vtkDebugMacro("MIP: update extent of input="<<PRT_EXT2(uExtent)<<"\n");
   // WRONG!:
  // We will want the input whole extent to be the one we go through
 input->GetWholeExtent(uExtent);
 
 vtkDebugMacro("MIP: whole extent is"<<PRT_EXT2(uExtent)<<"\n");

  // Get pointers for input and output
  char *inPtr = (char *) input->GetScalarPointer();
  char *outPtr = (char *) output->GetScalarPointer();
  
  if(!input) {
    vtkErrorMacro("No input is specified.");
  }
  if(this->UpdateExtentIsEmpty(output)) {
      vtkErrorMacro(<<"MIP: Empty update extent\n");
      return;
  }
  
  
  output->AllocateScalars();

  maxX = uExtent[1] - uExtent[0];
  maxY = uExtent[3] - uExtent[2];
  maxZ = uExtent[5] - uExtent[4];
  maxC = input->GetNumberOfScalarComponents();
  if(maxC>3)maxC=3;
  for(int i=0;i<maxX*maxY*maxC;i++)*outPtr++=0;
  outPtr = (char *) output->GetScalarPointer();
  input->GetIncrements(inIncX, inIncY, inIncZ);
  output->GetIncrements(outIncX, outIncY, outIncZ);
  vtkDebugMacro(<<"MIP: inIncX="<<inIncX<<" inIncY="<<inIncY<<" inIncZ="<<inIncZ<<"\n");
  vtkDebugMacro(<<"MIP: outIncX="<<outIncX<<" outIncY="<<outIncY<<" outIncZ="<<outIncZ<<"\n");
  vtkDebugMacro(<<"MIP: x="<<maxX<<", y="<<maxY<<",z="<<maxZ<<",c="<<maxC<<"\n");

  #define GET_AT(x,y,z,c,ptr) *(ptr+(z)*inIncZ+(y)*inIncY+(x)*inIncX+c)
  #define GET_AT_OUT(x,y,z,c,ptr) *(ptr+(z)*outIncZ+(y)*outIncY+(x)*outIncX+c)
  #define SET_AT(x,y,z,c,ptr,val) *(ptr+(z)*outIncZ+(y)*outIncY+(x)*outIncX+c)=val

  for(idxZ = 0; idxZ <= maxZ; idxZ++ ) {
    UpdateProgress(idxZ/float(maxZ));
    for(idxY = 0; idxY <= maxY; idxY++ ) {
      for(idxX = 0; idxX <= maxX; idxX++ ) {
          for(idxC = 0; idxC < maxC; idxC++) {
              scalar = GET_AT(idxX,idxY,idxZ,idxC,inPtr);
              outScalar = GET_AT_OUT(idxX,idxY,0,idxC,outPtr);
              if(scalar > outScalar) SET_AT(idxX,idxY,0,idxC,outPtr,scalar);
          }
      }
    }
  }
  vtkDebugMacro(<<"MIP: done\n");
}


//-----------------------------------------------------------------------------
void vtkImageSimpleMIP::PrintSelf(ostream& os, vtkIndent indent)
{
  this->Superclass::PrintSelf(os,indent);

}




