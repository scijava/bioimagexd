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
#include "vtkInformation.h"
#include "vtkInformationVector.h"
#include "vtkStreamingDemandDrivenPipeline.h"


#define PRT_EXT(ext) ext[0],ext[1],ext[2],ext[3],ext[4],ext[5]
#define PRT_EXT2(ext) ext[0]<<","<<ext[1]<<","<<ext[2]<<","<<ext[3]<<","<<ext[4]<<","<<ext[5]
vtkCxxRevisionMacro(vtkImageSimpleMIP, "$Revision: 1.36 $");
vtkStandardNewMacro(vtkImageSimpleMIP);

//-----------------------------------------------------------------------------
// Construct object to extract all of the input data.
vtkImageSimpleMIP::vtkImageSimpleMIP()
{

}


int vtkImageSimpleMIP::RequestInformation (
  vtkInformation * vtkNotUsed(request),
  vtkInformationVector **inputVector,
  vtkInformationVector *outputVector)
{
  int ext[6], ext2[6],idx;
  // get the info objects
  vtkInformation* outInfo = outputVector->GetInformationObject(0);
  vtkInformation *inInfo = inputVector[0]->GetInformationObject(0);
     
  vtkInformation *scalarInfo = vtkDataObject::GetActiveFieldInformation(inInfo,
  vtkDataObject::FIELD_ASSOCIATION_POINTS, vtkDataSetAttributes::SCALARS);
  
    
  int numComponents = scalarInfo->Get(vtkDataObject::FIELD_NUMBER_OF_COMPONENTS());
  int scalarType = scalarInfo->Get(vtkDataObject::FIELD_ARRAY_TYPE());
  inInfo->Get(vtkStreamingDemandDrivenPipeline::WHOLE_EXTENT(),ext);
  ext[5] = 0;
  outInfo->Set(vtkStreamingDemandDrivenPipeline::WHOLE_EXTENT(),ext,6);
  //printf("Setting whole extent of output to %d,%d,%d,%d,%d,%d\n",PRT_EXT(ext));
  if( numComponents > 3 ) numComponents = 3;
      
  vtkDataObject::SetPointDataActiveScalarInfo(outInfo, scalarType, numComponents);
  return 1;
}


int vtkImageSimpleMIP::FillInputPortInformation(
  int port, vtkInformation* info)
{
  info->Set(vtkAlgorithm::INPUT_IS_REPEATABLE(), 0);

  info->Set(vtkAlgorithm::INPUT_REQUIRED_DATA_TYPE(), "vtkImageData");

  return 1;
}


// This templated function executes the filter for any type of data.
template <class T>
void vtkImageSimpleMIPExecute(vtkImageSimpleMIP *self, int id,int NumberOfInputs,
                           vtkImageData **inData,vtkImageData*outData,int outExt[6],
                            T*)
{    
    
  vtkIdType inIncX,inIncY,inIncZ;
  vtkIdType outIncX,outIncY,outIncZ;
  int maxX,maxY,maxZ,maxC;
  int idxX,idxY,idxZ,idxC;

  int uExt[6],uExt2[6];
  //inData[0]->GetUpdateExtent(uExt);
  inData[0]->GetWholeExtent(uExt2);
  //printf("whole extent of input=%d,%d,%d,%d,%d,%d\n",PRT_EXT(uExt2));
  //printf("Using outext for output=%d,%d,%d,%d,%d,%d\n",PRT_EXT(outExt));
  T scalar,outScalar;
    
  
  memcpy(uExt,outExt,6*sizeof(int));
  uExt[5] = uExt2[5];
    //printf("Using ext for processing=%d,%d,%d,%d,%d,%d\n",PRT_EXT(uExt));
    //outData->ReleaseData();

  //outData->SetWholeExtent(uExt2);
  //outData->SetExtent(uExt2);
  //outData->AllocateScalars();

  T* outPtr;
  T* inPtr;
  //printf("Getting pointers...\n");  
  outPtr=(T*)outData->GetScalarPointerForExtent(outExt);
  inPtr=(T*)inData[0]->GetScalarPointerForExtent(uExt);
 //printf("got\n");
  maxX = uExt[1] - uExt[0];
  maxY = uExt[3] - uExt[2];
  maxZ = uExt[5] - uExt[4];

  maxC = inData[0]->GetNumberOfScalarComponents();
  if(maxC>3)maxC=3;
//  vtkDebugMacro(<<"maxC="<<maxC);
  //printf("maxX=%d, maxY=%d, maxZ=%d\n",maxX,maxY,maxZ);
  for(int i=0;i<(maxX+1)*(maxY+1)*maxC;i++)*outPtr++=0;

  //printf("Getting scalar pointer\n");
  
  outPtr = (T*)outData->GetScalarPointerForExtent(outExt);
  
  inData[0]->GetIncrements(inIncX, inIncY, inIncZ);
  outData->GetIncrements(outIncX, outIncY, outIncZ);
  
  //printf("Out ext = %d,%d,%d,%d,%d,%d\n",PRT_EXT(outExt));
  //printf("Update ext = %d,%d,%d,%d,%d,%d\n",PRT_EXT(uExt));

  #define GET_AT(x,y,z,c,ptr) *(ptr+(z)*inIncZ+(y)*inIncY+(x)*inIncX+c)
  #define GET_AT_OUT(x,y,z,c,ptr) *(ptr+(z)*outIncZ+(y)*outIncY+(x)*outIncX+c)
  #define SET_AT(x,y,z,c,ptr,val) *(ptr+(z)*outIncZ+(y)*outIncY+(x)*outIncX+c)=val

  //printf("maxX=%d, maxY=%d, maxZ=%d, maxC=%d\n",maxX,maxY,maxZ,maxC);
  //printf("inIncX=%d,inIncY=%d, inIncZ=%d\n",inIncX,inIncY,inIncZ);
  //printf("outIncX=%d,outIncY=%d, outIncZ=%d\n",outIncX,outIncY,outIncZ);
  for(idxZ = 0; idxZ <= maxZ; idxZ++ ) {
    self->UpdateProgress(idxZ/float(maxZ));
    for(idxY = 0; idxY <= maxY; idxY++ ) {
      for(idxX = 0; idxX <= maxX; idxX++ ) {
          for(idxC = 0; idxC < maxC; idxC++) {
              scalar = GET_AT(idxX,idxY,idxZ,idxC,inPtr);
              outScalar = GET_AT_OUT(idxX,idxY,0,idxC,outPtr);
              
              if(scalar > outScalar) {
                  SET_AT(idxX,idxY,0,idxC,outPtr,scalar);
              }
          }
      }
    }
  }
}
int vtkImageSimpleMIP::RequestUpdateExtent (
  vtkInformation* vtkNotUsed(request),
  vtkInformationVector** inputVector,
  vtkInformationVector* outputVector)
{
  int uext[6], ext[6];
  //printf("\n\n\n+++++ REQUEST UPDATE EXTENT FOR SIMPLE MIP\n");
  vtkInformation* outInfo = outputVector->GetInformationObject(0);
  vtkInformation *inInfo = inputVector[0]->GetInformationObject(0);

  inInfo->Get(vtkStreamingDemandDrivenPipeline::WHOLE_EXTENT(),ext);
  // Get the requested update extent from the output.
  outInfo->Get(vtkStreamingDemandDrivenPipeline::UPDATE_EXTENT(), uext);
  
    //printf("Whole extent is %d,%d,%d,%d,%d,%d\n",PRT_EXT(ext));
    //printf("Update extent is %d,%d,%d,%d,%d,%d\n",PRT_EXT(uext));

  // If they request an update extent that doesn't cover the whole z-stack then modify it
  if(uext[5] < ext[5] ) uext[5] = ext[5];
  if(uext[4] > ext[4] ) uext[4] = ext[4];
  printf("vtkImageSimpleMIP Setting uextent to %d,%d,%d,%d,%d,%d\n",PRT_EXT(uext));
  inInfo->Set(vtkStreamingDemandDrivenPipeline::UPDATE_EXTENT(), uext,6);
  return 1;    
}


//----------------------------------------------------------------------------
// This method is passed a input and output regions, and executes the filter
// algorithm to fill the output from the inputs.
// It just executes a switch statement to call the correct function for
// the regions data types.
void vtkImageSimpleMIP::ThreadedRequestData (
  vtkInformation * vtkNotUsed( request ),
  vtkInformationVector**  inputVector ,
  vtkInformationVector * vtkNotUsed( outputVector ),
  vtkImageData ***inData,
  vtkImageData **outData,
  int outExt[6], int id)
{
    int uExt[6];
  vtkInformation *inInfo = inputVector[0]->GetInformationObject(0);
  inInfo->Get(vtkStreamingDemandDrivenPipeline::UPDATE_EXTENT(),uExt);
    printf("Update extent=%d,%d,%d,%d,%d,%d\n",PRT_EXT(uExt));
    printf("vtkImageSimpleMIP ThreadedRequestData outExt=%d,%d,%d,%d,%d,%d\n",outExt[0],outExt[1],outExt[2],outExt[3],outExt[4],outExt[5]);
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
    vtkTemplateMacro(vtkImageSimpleMIPExecute(this, id,
                    this->GetNumberOfInputConnections(0),inData[0],
                    outData[0], outExt,static_cast<VTK_TT *>(0)));
  default:
    vtkErrorMacro(<< "Execute: Unknown ScalarType");
  return;
  }

}

//-----------------------------------------------------------------------------
void vtkImageSimpleMIP::PrintSelf(ostream& os, vtkIndent indent)
{
  this->Superclass::PrintSelf(os,indent);

}




