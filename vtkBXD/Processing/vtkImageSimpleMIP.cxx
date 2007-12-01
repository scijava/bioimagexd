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
 // if( numComponents > 3 ) numComponents = 3;
      
  vtkDataObject::SetPointDataActiveScalarInfo(outInfo, scalarType, numComponents);
//    printf("vtkImageSimpleMIP RequestInformation DONE!\n");

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
  unsigned long target, count = 0;
  int uExt[6],uExt2[6];
  //inData[0]->GetUpdateExtent(uExt);
  inData[0]->GetWholeExtent(uExt2);
//  printf("Thread id = %d whole extent of input=%d,%d,%d,%d,%d,%d\n",id,PRT_EXT(uExt2));
  T scalar,outScalar;
    
  
  memcpy(uExt,outExt,6*sizeof(int));
  uExt[5] = uExt2[5];


  T* outPtr;
  T* inPtr;
  //printf("Getting pointers...\n");  
 //printf("got\n");
  maxX = uExt[1] - uExt[0];
  maxY = uExt[3] - uExt[2];
  maxZ = uExt[5] - uExt[4];

  maxC = inData[0]->GetNumberOfScalarComponents();
//  if(maxC>3) {
//        vtkErrorWithObjectMacro(self, <<"macC = " <<maxC<<" > 3");
//        maxC=3;
//  }
//  vtkDebugMacro(<<"maxC="<<maxC);
//  printf("Thread id = %d, maxX=%d, maxY=%d, maxZ=%d\n",id, maxX,maxY,maxZ);

  //printf("Getting scalar pointer\n");
  
  outPtr = (T*)outData->GetScalarPointerForExtent(outExt);
  inPtr=(T*)inData[0]->GetScalarPointerForExtent(uExt);
  
  inData[0]->GetContinuousIncrements(uExt,inIncX, inIncY, inIncZ);
  outData->GetContinuousIncrements(outExt, outIncX, outIncY, outIncZ);
  //printf("Thread id = %d, uext=%d,%d,%d,%d,%d,%d inIncX=%d, inIncY=%d, inIncZ=%d\n",id,PRT_EXT(uExt), inIncX,inIncY,inIncZ);
//  printf("Thread id = %d, outIncX=%d, outIncY=%d, outIncZ=%d\n",id, outIncX,outIncY,outIncZ);
  //printf("Thread id = %d, Out ext = %d,%d,%d,%d,%d,%d\n",id, PRT_EXT(outExt));
//  printf("Thread id = %d Update ext = %d,%d,%d,%d,%d,%d\n",id, PRT_EXT(uExt));


  char progressText[200];
  target = (unsigned long)((maxZ+1)*(maxY+1)/50.0);


  //  for(int i=0;i<(maxX+1)*(maxY+1)*maxC;i++)*outPtr++=0;
    for(int ly = 0; ly <= maxY; ly++) {
        for(int lx = 0; lx <= maxX; lx++) {
            for(int lc = 0; lc < maxC; lc++) {
                *outPtr++=0;
            }
            outPtr+=outIncX;
        }
        outPtr+=outIncY;
    }
    
    
    
  //printf("THREAD %d PROCESSING  X = %d-%d, Y=%d-%d\n", id,uExt[0], uExt[1],uExt[2], uExt[3]);
  for(idxZ = 0; idxZ <= maxZ; idxZ++ ) {
    // For each slice, we loop through the output image again
    outPtr = (T*)outData->GetScalarPointerForExtent(outExt);
    sprintf(progressText,"Creating Maximum Intensity Projection...");
    self->SetProgressText(progressText);  
    for(idxY = 0; idxY <= maxY; idxY++ ) {
        if (!id)
        {
            if (!(count%target))
            {
                self->UpdateProgress(count/(50.0*target));
            }
            count++;
       }          
       for(idxX = 0; idxX <= maxX; idxX++ ) {
          for(idxC = 0; idxC < maxC; idxC++) {
              scalar = *inPtr;
              outScalar = *outPtr;
              if(scalar > outScalar) {
                  *outPtr = scalar;
              }
              outPtr++;
              inPtr++;
          }
          inPtr+=inIncX;
          outPtr+=outIncX;
       }
       inPtr+=inIncY;
       outPtr+=outIncY;
    }
    inPtr+=inIncZ;
    
  }
// printf("Thread id = %d MIP done\n", id);
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
  
//    printf("Whole extent is %d,%d,%d,%d,%d,%d\n",PRT_EXT(ext));
//    printf("Update extent is %d,%d,%d,%d,%d,%d\n",PRT_EXT(uext));

  // If they request an update extent that doesn't cover the whole z-stack then modify it
  if(uext[1]==-1) uext[1] = ext[1];
  if(uext[3]==-1) uext[3] = ext[3];    
  if(uext[5] < ext[5] ) uext[5] = ext[5];
  if(uext[4] > ext[4] ) uext[4] = ext[4];
  // printf("vtkImageSimpleMIP Setting uextent to %d,%d,%d,%d,%d,%d\n",PRT_EXT(uext));
 // outInfo->Set(vtkStreamingDemandDrivenPipeline::UPDATE_EXTENT(), uext,6);
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
  vtkInformationVector *  outputVector ,
  vtkImageData ***inData,
  vtkImageData **outData,
  int outExt[6], int id)
{
    // printf("vtkImageSimpleMIP ThreadedRequestData outExt=%d,%d,%d,%d,%d,%d\n",outExt[0],outExt[1],outExt[2],outExt[3],outExt[4],outExt[5]);
    int uExt[6],wholeExt[6];
  vtkInformation *inInfo = inputVector[0]->GetInformationObject(0);
    vtkInformation* outInfo = outputVector->GetInformationObject(0);
  inInfo->Get(vtkStreamingDemandDrivenPipeline::UPDATE_EXTENT(),uExt);
    //printf("vtkImageSimpleMIP update extent=%d,%d,%d,%d,%d,%d\n",PRT_EXT(uExt));

    
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
    //memcpy(wholeExt,uExt,6*sizeof(int));
    //wholeExt[5]=0;
    //printf("Setting output update extent to %d,%d,%d,%d,%d,%d\n",PRT_EXT(wholeExt));
     // outInfo->Set(vtkStreamingDemandDrivenPipeline::WHOLE_EXTENT(),wholeExt,6);
    //  outInfo->Set(vtkStreamingDemandDrivenPipeline::UPDATE_EXTENT(),wholeExt,6);

}
//----------------------------------------------------------------------------
// For streaming and threads.  Splits output update extent into num pieces.
// This method needs to be called num times.  Results must not overlap for
// consistent starting extent.  Subclass can override this method.
// This method returns the number of peices resulting from a successful split.
// This can be from 1 to "total".  
// If 1 is returned, the extent cannot be split.
int vtkImageSimpleMIP::SplitExtent(int splitExt[6], 
                                                int startExt[6], 
                                                int num, int total)
{
  int splitAxis;
  int min, max;
  vtkDebugMacro("SplitExtent: ( " << startExt[0] << ", " << startExt[1] << ", "
                << startExt[2] << ", " << startExt[3] << ", "
                << startExt[4] << ", " << startExt[5] << "), " 
                << num << " of " << total);

  // start with same extent
  memcpy(splitExt, startExt, 6 * sizeof(int));

  splitAxis = 0;
  min = startExt[splitAxis*2];
  max = startExt[splitAxis*2+1];
  while (min >= max)
    {
    // empty extent so cannot split
    if (min > max)
      {
      return 1;
      }
    --splitAxis;
    if (splitAxis < 0)
      { // cannot split
      vtkDebugMacro("  Cannot Split");
      return 1;
      }
    min = startExt[splitAxis*2];
    max = startExt[splitAxis*2+1];
    }

  // determine the actual number of pieces that will be generated
  int range = max - min + 1;
  int valuesPerThread = (int)ceil(range/(double)total);
  int maxThreadIdUsed = (int)ceil(range/(double)valuesPerThread) - 1;
  if (num < maxThreadIdUsed)
    {
    splitExt[splitAxis*2] = splitExt[splitAxis*2] + num*valuesPerThread;
    splitExt[splitAxis*2+1] = splitExt[splitAxis*2] + valuesPerThread - 1;
    }
  if (num == maxThreadIdUsed)
    {
    splitExt[splitAxis*2] = splitExt[splitAxis*2] + num*valuesPerThread;
    }
  
  vtkDebugMacro("  Split Piece: ( " <<splitExt[0]<< ", " <<splitExt[1]<< ", "
                << splitExt[2] << ", " << splitExt[3] << ", "
                << splitExt[4] << ", " << splitExt[5] << ")");

  // printf("Splitting into %d pieces\n",maxThreadIdUsed+1);
  return maxThreadIdUsed + 1;
}

//-----------------------------------------------------------------------------
void vtkImageSimpleMIP::PrintSelf(ostream& os, vtkIndent indent)
{
  this->Superclass::PrintSelf(os,indent);

}




