/*=========================================================================

  Program:   BioImageXD
  Module:    $RCSfile: vtkImageSolitaryFilter.cxx,v $

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
#include "vtkImageSolitaryFilter.h"

#include "vtkCellData.h"
#include "vtkImageData.h"
#include "vtkObjectFactory.h"
#include "vtkPointData.h"

vtkCxxRevisionMacro(vtkImageSolitaryFilter, "$Revision: 1.36 $");
vtkStandardNewMacro(vtkImageSolitaryFilter);

//-----------------------------------------------------------------------------
// Construct object to extract all of the input data.
vtkImageSolitaryFilter::vtkImageSolitaryFilter()
{
  this->FilteringThreshold = 0;
  this->HorizontalThreshold = 0;
  this->VerticalThreshold = 0;

}

//-----------------------------------------------------------------------------

void vtkImageSolitaryFilter::ComputeInputUpdateExtent(int inExt[6], 
                                             int outExt[6])
{
    int i = 0, k = 0;
    int wholeExt[6];
    this->GetInput()->GetWholeExtent(wholeExt);
    memcpy(inExt,wholeExt,6*sizeof(int));
    printf("Required ext for solitary = (");
    for(int i=0;i<3;i++) {
        k=inExt[2*i];
        if(k > 0) k--;
        printf("%d, ",k);
        inExt[2*i]=k;
        k=inExt[2*i+1];
        if(k < wholeExt[2*i+1]-1)k++;
        inExt[2*i+1]=k;
        printf("%d, ",k);
    }
    printf(")\n");   
}

//-----------------------------------------------------------------------------
void 
vtkImageSolitaryFilter::ExecuteInformation(vtkImageData *input, vtkImageData *output)
{
  this->vtkImageToImageFilter::ExecuteInformation( input, output );
}

//-----------------------------------------------------------------------------
void vtkImageSolitaryFilter::ExecuteData(vtkDataObject *)
{
  int uExtent[6];
  vtkImageData* output = this->GetOutput();
  vtkImageData* input = this->GetInput();
  int inIncX,inIncY,inIncZ;
  int outIncX,outIncY,outIncZ;
  int maxX,maxY,maxZ;
  int idxX,idxY,idxZ;
  char *inPtr1;

  unsigned char scalar,newScalar,cmpScalar;

  //output->GetUpdateExtent(uExtent);
  output->GetUpdateExtent(uExtent);
  output->SetExtent(uExtent);
  printf("Exent=(%d,%d,%d,%d,%d,%d)\n",uExtent[0],uExtent[1],uExtent[2],uExtent[3],uExtent[4],uExtent[5]);
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
  input->GetIncrements(inIncX, inIncY, inIncZ);
  output->GetContinuousIncrements(uExtent,outIncX, outIncY, outIncZ);
  printf("inIncX=%d,inIncY=%d,inIncZ=%d\n",inIncX,inIncY,inIncZ);
  printf("outIncX=%d,outIncY=%d,outIncZ=%d\n",outIncX,outIncY,outIncZ);
  maxX = uExtent[1] - uExtent[0];
  maxY = uExtent[3] - uExtent[2];
  maxZ = uExtent[5] - uExtent[4];
  
  //inIncX *= input->GetScalarSize();
  //inIncY *= input->GetScalarSize();
  //inIncZ *= input->GetScalarSize();

  
  #define GET_AT(x,y,z,ptr) *(ptr+(z)*inIncZ+(y)*inIncY+(x)*inIncX)
  
  printf("maxX=%d,maxY=%d,maxZ=%d\n",maxX,maxY,maxZ);
  printf("Filtering Threshold=%d,Horizontal=%d, Vertical=%d\n",this->FilteringThreshold,this->HorizontalThreshold,this->VerticalThreshold);
  for(idxZ = 0; idxZ <= maxZ; idxZ++ ) {
    
    for(idxY = 0; idxY <= maxY; idxY++ ) {
      for(idxX = 0; idxX <= maxX; idxX++ ) {
          
        scalar = GET_AT(idxX,idxY,idxZ,inPtr);          
        if( scalar > this->FilteringThreshold ) {
          newScalar=0;
          // Compare voxel to the left
          if (this->HorizontalThreshold && idxX > 0) {
            cmpScalar=GET_AT(idxX-1,idxY,idxZ,inPtr);
            if( cmpScalar >= this->HorizontalThreshold ) {
                newScalar=scalar;
            }
        
          }
          // Compare voxel to the right
          if (this->HorizontalThreshold && idxX < maxX-1) {
            cmpScalar=GET_AT(idxX+1,idxY,idxZ,inPtr);
            if( cmpScalar >= this->HorizontalThreshold ) newScalar=scalar;
        
          }
          // Compare voxel above
          if (this->VerticalThreshold && idxY > 0) {
            cmpScalar=GET_AT(idxX,idxY-1,idxZ,inPtr);
            if( cmpScalar >= this->VerticalThreshold ) newScalar=scalar;
        
          }
          // Compare voxel below
          if (this->VerticalThreshold && idxY < maxY-1) {
            cmpScalar=GET_AT(idxX,idxY+1,idxZ,inPtr);
            if( cmpScalar >= this->VerticalThreshold ) newScalar=scalar;
        
          }
          *outPtr=newScalar; 
        }
        outPtr++;
      }
      outPtr += outIncY;
    }  
    outPtr += outIncZ;      
  }
  
}


//-----------------------------------------------------------------------------
void vtkImageSolitaryFilter::PrintSelf(ostream& os, vtkIndent indent)
{
  this->Superclass::PrintSelf(os,indent);

  os << indent << "Filtering Threshold: "<< this->FilteringThreshold << "\n";
  os << indent << "Horizontal Threshold: "<< this->HorizontalThreshold << "\n";
  os << indent << "Vertical Threshold: "<< this->VerticalThreshold << "\n";    

}




