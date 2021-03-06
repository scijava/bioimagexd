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
#include "vtkInformation.h"
#include "vtkInformationVector.h"
#include "vtkStreamingDemandDrivenPipeline.h"


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


int vtkImageSolitaryFilter::RequestUpdateExtent (
  vtkInformation* vtkNotUsed(request),
  vtkInformationVector** inputVector,
  vtkInformationVector* outputVector)
{
  int inExt[6], wholeExt[6];
  vtkInformation* outInfo = outputVector->GetInformationObject(0);
  vtkInformation *inInfo = inputVector[0]->GetInformationObject(0);

  inInfo->Get(vtkStreamingDemandDrivenPipeline::WHOLE_EXTENT(),wholeExt);

  outInfo->Get(vtkStreamingDemandDrivenPipeline::UPDATE_EXTENT(), inExt);
  int k;
  for(int i=0;i<2;i++) {
        k=inExt[2*i];
        if(k > 0) k--;
        inExt[2*i]=k;
        k=inExt[2*i+1];
        if(k < wholeExt[2*i+1]-1)k++;
        inExt[2*i+1]=k;
    }
//  printf("Setting uext to %d,%d,%d,%d,%d,%d\n",inExt[0],inExt[1],inExt[2],inExt[3],inExt[4],inExt[5]);
  inInfo->Set(vtkStreamingDemandDrivenPipeline::UPDATE_EXTENT(), inExt,6);
  return 1;    
}

int vtkImageSolitaryFilter::FillInputPortInformation(
  int port, vtkInformation* info)
{
  info->Set(vtkAlgorithm::INPUT_IS_REPEATABLE(), 0);

  info->Set(vtkAlgorithm::INPUT_REQUIRED_DATA_TYPE(), "vtkImageData");

  return 1;
}

// This templated function executes the filter for any type of data.
template <class T>
void vtkImageSolitaryFilterExecute(vtkImageSolitaryFilter *self, int id,int NumberOfInputs,
                           vtkImageData **inData,vtkImageData*outData,int outExt[6],
                            T*)
{    
  int uExtent[6];
  vtkIdType inIncX,inIncY,inIncZ;
  vtkIdType jumpIncX,jumpIncY,jumpIncZ;
  vtkIdType outIncX,outIncY,outIncZ;
  int maxX,maxY,maxZ;
  int idxX,idxY,idxZ;
  
  unsigned long target = 0, count = 0;
  
 
  int FilteringThreshold = self->GetFilteringThreshold();
  int HorizontalThreshold = self->GetHorizontalThreshold();
  int VerticalThreshold = self->GetVerticalThreshold();
    
  T* inPtr, *outPtr;

  T scalar,newScalar,cmpScalar;

//  inData[0]->GetUpdateExtent(uExtent);
  inPtr = (T *) inData[0]->GetScalarPointerForExtent(outExt);
  outPtr = (T *) outData->GetScalarPointerForExtent(outExt);
    
 
  if(!inData) {
    vtkErrorWithObjectMacro(self,"No input is specified.");
      return;
  } 
  inData[0]->GetContinuousIncrements(outExt, inIncX, inIncY, inIncZ);
  inData[0]->GetIncrements(jumpIncX, jumpIncY, jumpIncZ);
  //printf("uExt =%d,%d,%d,%d,%d,%d\n",uExtent[0],uExtent[1],uExtent[2],uExtent[3],uExtent[4],uExtent[5]);
  
  outData->GetContinuousIncrements(outExt,outIncX, outIncY, outIncZ);
  maxX = outExt[1] - outExt[0];
  maxY = outExt[3] - outExt[2];
  maxZ = outExt[5] - outExt[4];
  
  

  target = (unsigned long)((maxZ+1)*(maxY+1)/50.0);
  target++;
  
  //printf("maxX=%d, maxY=%d, maxZ=%d\n", maxX, maxY, maxZ);

  char progressText[200];

  printf("maxZ=%d. count=%d. target=%d\n",maxZ,count,target);
  for(idxZ = 0; idxZ <= maxZ; idxZ++ ) {
    sprintf(progressText,"Removing solitary noise voxels");
    self->SetProgressText(progressText);
    if(!id) {
        if (!(count%target))
        {
            self->UpdateProgress(count/(50.0*target));
        }
       count++;        
    }

    for(idxY = 0; !self->AbortExecute && idxY <= maxY; idxY++ )
    {
      for(idxX = 0; idxX <= maxX; idxX++ )
      {
            newScalar = scalar = *inPtr;  
            if( (HorizontalThreshold || VerticalThreshold) && scalar > FilteringThreshold ) {
                  newScalar=0;
                  // Compare voxel to the left
                  if (HorizontalThreshold && idxX > 0) {
                    cmpScalar = inPtr[-1];
                    if( cmpScalar >= HorizontalThreshold ) newScalar = scalar;                
                  }
                  // Compare voxel to the right
                  if (HorizontalThreshold && idxX < maxX-1) {
                    cmpScalar = inPtr[1];
                    if( cmpScalar >= HorizontalThreshold ) newScalar = scalar;
                
                  }
                  // Compare voxel above
                  if (VerticalThreshold && idxY > 0) {
                    cmpScalar = inPtr[-jumpIncY];
                    if( cmpScalar >= VerticalThreshold ) newScalar = scalar;
                
                  }
                  // Compare voxel below
                  if (VerticalThreshold && idxY < maxY-1) {
                    cmpScalar = inPtr[jumpIncY];                    
                    if( cmpScalar >= VerticalThreshold ) newScalar=scalar;
                
                  }
            } 
            *outPtr = newScalar;
            
            inPtr++;
            outPtr++;
      }
      inPtr += inIncY;
      outPtr += outIncY;

    }  
    inPtr += inIncZ;
    outPtr += outIncZ;      
  }
  
}

//----------------------------------------------------------------------------
// This method is passed a input and output regions, and executes the filter
// algorithm to fill the output from the inputs.
// It just executes a switch statement to call the correct function for
// the regions data types.
void vtkImageSolitaryFilter::ThreadedRequestData (
  vtkInformation * vtkNotUsed( request ),
  vtkInformationVector** vtkNotUsed( inputVector ),
  vtkInformationVector * vtkNotUsed( outputVector ),
  vtkImageData ***inData,
  vtkImageData **outData,
  int outExt[6], int id)
{
  if (inData[0][0] == NULL)
    {
    vtkErrorMacro(<< "Input " << 0 << " must be specified.");
    return;
    }
  // this filter expects that input is the same type as output.
  if (inData[0][0]->GetScalarType() != outData[0]->GetScalarType())
    {
    vtkErrorMacro(<< "Execute: input ScalarType, "
                  << inData[0][0]->GetScalarType()
                  << ", must match out ScalarType "
                  << outData[0]->GetScalarType());
    return;
    }


  switch (inData[0][0]->GetScalarType())
  {
    vtkTemplateMacro(vtkImageSolitaryFilterExecute(this, id,
                    this->GetNumberOfInputConnections(0),inData[0],
                    outData[0], outExt,static_cast<VTK_TT *>(0)));
  default:
    vtkErrorMacro(<< "Execute: Unknown ScalarType");
  return;
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




