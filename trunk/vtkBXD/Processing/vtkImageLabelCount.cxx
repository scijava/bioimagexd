/*=========================================================================

  Program:   BioImageXD
  Module:    $RCSfile: vtkImageLabelAverage.cxx,v $

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
#include "vtkImageLabelCount.h"

#include "vtkCellData.h"
#include "vtkImageData.h"
#include "vtkObjectFactory.h"
#include "vtkPointData.h"
#include "vtkInformation.h"
#include "vtkInformationVector.h"
#include "vtkStreamingDemandDrivenPipeline.h"
#include "vtkUnsignedCharArray.h"

#include <vtkstd/map>
#include <vtkstd/list>
#include <vtkstd/algorithm>

vtkCxxRevisionMacro(vtkImageLabelCount, "$Revision: 1.36 $");
vtkStandardNewMacro(vtkImageLabelCount);

//-----------------------------------------------------------------------------
// Construct object to extract all of the input data.
vtkImageLabelCount::vtkImageLabelCount()
{
    BackgroundLevel = 1;
   BackgroundToObjectCountArray = vtkUnsignedLongArray::New();
   ForegroundToBackgroundArray = vtkUnsignedLongArray::New();
   ObjectOverlapArray = vtkUnsignedLongArray::New();
   ObjectSizeArray = vtkUnsignedLongArray::New();
}


int vtkImageLabelCount::FillInputPortInformation(
  int port, vtkInformation* info)
{
  info->Set(vtkAlgorithm::INPUT_IS_REPEATABLE(), 1);

  info->Set(vtkAlgorithm::INPUT_REQUIRED_DATA_TYPE(), "vtkImageData");

  return 1;
}
//-----------------------------------------------------------------------------
// This templated function executes the filter for any type of data.
template <class T>
void vtkImageLabelCountExecute(vtkImageLabelCount *self, int id,int NumberOfInputs,
                           vtkImageData **inData,vtkImageData*outData,int outExt[6],
                            T*)
{    
  int uExtent[6];
  vtkIdType inIncX,inIncY,inIncZ;
  vtkIdType maskIncX,maskIncY,maskIncZ;
  int maxX,maxY,maxZ,maxC;
  int idxX,idxY,idxZ,idxC;
  T *fgPtr, *bgPtr;
  unsigned long nonZeroInsideCount = 0, nonZeroOutsideCount = 0;
  unsigned long nonZeroCount = 0;
  double insideSum = 0, outsideSum = 0;
  int* table;
  unsigned long count = 0;
  unsigned long target;       

  vtkUnsignedLongArray* bgToCountArray = self->GetBackgroundToObjectCountArray();
  vtkUnsignedLongArray* fgToBgArray = self->GetForegroundToBackgroundArray();
  vtkUnsignedLongArray* ObjectOverlapArray = self->GetObjectOverlapArray();
  vtkUnsignedLongArray* ObjectSizeArray = self->GetObjectSizeArray();
  int bgLevel = self->GetBackgroundLevel();
  T fgScalar, bgScalar;
  
  bgPtr = (T*) inData[0]->GetScalarPointerForExtent(outExt);
  fgPtr = (T*) inData[1]->GetScalarPointerForExtent(outExt);
  
  int wext[6];
  outData->DeepCopy(inData[0]);

  
  inData[0]->GetContinuousIncrements(outExt,inIncX, inIncY, inIncZ);
  inData[1]->GetContinuousIncrements(outExt, maskIncX,maskIncY,maskIncZ);
  maxX = outExt[1] - outExt[0];
  maxY = outExt[3] - outExt[2];
  maxZ = outExt[5] - outExt[4];
  maxC = inData[0]->GetNumberOfScalarComponents();

  unsigned long n = 0,  numberOfValues = 0;
  double avg;

  double range[2]; 
  inData[0]->GetScalarRange(range);
  bgToCountArray -> SetNumberOfValues((unsigned long)range[1]+1);
  for(int i=0;i<range[1]+1;i++) {
      bgToCountArray->SetValue(i, 0);
  }  
  inData[1]->GetScalarRange(range);
  fgToBgArray -> SetNumberOfValues((unsigned long)range[1]+1);
  ObjectSizeArray->SetNumberOfValues((unsigned long)range[1]+1);
  ObjectOverlapArray->SetNumberOfValues((unsigned long)range[1]+1);

  char progressText[200];


  for(int i=0;i<range[1]+1;i++) {
     fgToBgArray->SetValue(i, 0);
     ObjectSizeArray->SetValue(i, 0);
     ObjectOverlapArray->SetValue(i, 0);
  }
  
  std::map<unsigned long,std::list<unsigned long> > fgToBg;
  
  target = (unsigned long)((maxZ+1)*(maxY+1)/50.0);
  target++;
  for(idxZ = 0; idxZ <= maxZ; idxZ++ ) {

    sprintf(progressText,"Calculating object placement (slice %d / %d)",idxZ,maxZ);
    self->SetProgressText(progressText);
    for(idxY = 0; !self->AbortExecute &&  idxY <= maxY; idxY++ ) {
        if (!id)
        {
            if (!(count%target))
            {
                self->UpdateProgress(count/(50.0*target));
            }
            count++;
       }          
    
      for(idxX = 0; idxX <= maxX; idxX++ ) {
          for(idxC = 0; idxC < maxC; idxC++ ) {
            fgScalar = *fgPtr++;
            bgScalar = *bgPtr++;
            std::list<unsigned long>  *bgintlist = &fgToBg[fgScalar];
            std::list <unsigned long>::iterator result;
            result = std::find(bgintlist->begin(), bgintlist->end(), bgScalar);
            ObjectSizeArray->SetValue(fgScalar, ObjectSizeArray->GetValue(fgScalar)+1);
            if(bgScalar && fgScalar) {
            	ObjectOverlapArray->SetValue(fgScalar, ObjectOverlapArray->GetValue(fgScalar)+1);
            }
            
            
            if( fgScalar != 0 && result==bgintlist->end() )
            {
            	bgintlist->push_back(bgScalar);
            	bgToCountArray->SetValue(bgScalar, bgToCountArray->GetValue(bgScalar)+1);
   	        	fgToBgArray->SetValue(fgScalar, bgScalar);
   	        	printf("Foreground object %d is in background object %d\n", fgScalar, bgScalar);
            } 
            
          }
          fgPtr+=inIncX;
          bgPtr += maskIncX;
      }
      fgPtr += inIncY;
      bgPtr += maskIncY;
    }  
    fgPtr += inIncZ;
    bgPtr += maskIncZ;
  }
  
  
}

int vtkImageLabelCount::SplitExtent(int splitExt[6], 
                                                int startExt[6], 
                                                int num, int total)
{
  memcpy(splitExt, startExt, 6 * sizeof(int));
  return 1;
}

//----------------------------------------------------------------------------
// This method is passed a input and output regions, and executes the filter
// algorithm to fill the output from the inputs.
// It just executes a switch statement to call the correct function for
// the regions data types.
void vtkImageLabelCount::ThreadedRequestData (
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

 printf("Number of connections=%d, outExt=%d,%d,%d,%d,%d,%d\n",this->GetNumberOfInputConnections(0),
                 outExt[0],outExt[1],outExt[2],outExt[3],outExt[4],outExt[5]);

    switch (inData[0][0]->GetScalarType())
  {
    vtkTemplateMacro(vtkImageLabelCountExecute(this, id,
                    this->GetNumberOfInputConnections(0),inData[0],
                    outData[0], outExt,static_cast<VTK_TT *>(0)));
  default:
    vtkErrorMacro(<< "Execute: Unknown ScalarType");
  return;
  }

}


//-----------------------------------------------------------------------------
void vtkImageLabelCount::PrintSelf(ostream& os, vtkIndent indent)
{
  this->Superclass::PrintSelf(os,indent);


}




