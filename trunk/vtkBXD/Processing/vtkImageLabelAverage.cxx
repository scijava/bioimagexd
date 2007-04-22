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
#include "vtkImageLabelAverage.h"

#include "vtkCellData.h"
#include "vtkImageData.h"
#include "vtkObjectFactory.h"
#include "vtkPointData.h"
#include "vtkInformation.h"
#include "vtkInformationVector.h"
#include "vtkStreamingDemandDrivenPipeline.h"


vtkCxxRevisionMacro(vtkImageLabelAverage, "$Revision: 1.36 $");
vtkStandardNewMacro(vtkImageLabelAverage);

//-----------------------------------------------------------------------------
// Construct object to extract all of the input data.
vtkImageLabelAverage::vtkImageLabelAverage()
{
    NumberOfItems = 0;
    AverageArray = vtkDoubleArray::New();
    
}


int vtkImageLabelAverage::FillInputPortInformation(
  int port, vtkInformation* info)
{
  info->Set(vtkAlgorithm::INPUT_IS_REPEATABLE(), 1);

  info->Set(vtkAlgorithm::INPUT_REQUIRED_DATA_TYPE(), "vtkImageData");

  return 1;
}
//-----------------------------------------------------------------------------
// This templated function executes the filter for any type of data.
template <class T>
void vtkImageLabelAverageExecute(vtkImageLabelAverage *self, int id,int NumberOfInputs,
                           vtkImageData **inData,vtkImageData*outData,int outExt[6],
                            T*)
{    
  int uExtent[6];
  vtkIdType inIncX,inIncY,inIncZ;
  vtkIdType maskIncX,maskIncY,maskIncZ;
  int maxX,maxY,maxZ,maxC;
  int idxX,idxY,idxZ,idxC;
  T *inPtr;
  unsigned long *maskPtr;
  int* table;
  unsigned long count = 0;
  unsigned long target;       
  vtkDoubleArray* avgArray = self->GetAverageArray();
  vtkUnsignedLongArray* numArray = vtkUnsignedLongArray::New();

  T scalar;
  unsigned long maskScalar;
  inPtr = (T*) inData[0]->GetScalarPointerForExtent(outExt);
  maskPtr = (unsigned long*) inData[1]->GetScalarPointerForExtent(outExt);
  
  int wext[6];
  outData->DeepCopy(inData[0]);
  //input->GetIncrements(inIncX, inIncY, inIncZ);
  //output->GetIncrements(outIncX, outIncY, outIncZ);
  
  inData[0]->GetContinuousIncrements(outExt,inIncX, inIncY, inIncZ);
  inData[1]->GetContinuousIncrements(outExt, maskIncX,maskIncY,maskIncZ);
  maxX = outExt[1] - outExt[0];
  maxY = outExt[3] - outExt[2];
  maxZ = outExt[5] - outExt[4];
  maxC = inData[0]->GetNumberOfScalarComponents();

  unsigned long n = 0,  numberOfValues = 0;
  double avg;

  double range[2]; 
  inData[1]->GetScalarRange(range);
  printf("Range = %f,%f\n",range[0],range[1]);
  avgArray -> SetNumberOfValues((unsigned long)range[1]+1);
  numArray -> SetNumberOfValues((unsigned long)range[1]+1);
  avgArray -> SetValue(0,0);
  numArray -> SetValue(0,0);
  char progressText[200];
  for(int i=0;i<range[1]+1;i++) {
      avgArray->SetValue(i,0);
      numArray->SetValue(i,0);
  }
  
  target = (unsigned long)((maxZ+1)*(maxY+1)/50.0);
  target++;
  for(idxZ = 0; idxZ <= maxZ; idxZ++ ) {

    sprintf(progressText,"Calculating average intensity of objects (slice %d / %d)",idxZ,maxZ);
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
          for(idxC = 0; idxC < maxC; idxC++ ) {
            scalar = *inPtr++;
            maskScalar = (unsigned long) *maskPtr++;
            
            if(maskScalar > n) {
                n = maskScalar;
            }
            
            avg = avgArray->GetValue((unsigned long)maskScalar);
            avg += scalar;
            avgArray->SetValue((unsigned long)maskScalar, avg);
            numberOfValues = numArray -> GetValue(maskScalar);
            numberOfValues++;
            //if(maskScalar!=1)printf("Number of values %d = %d, avgint=%f\n",maskScalar,numberOfValues,avg/numberOfValues);
            numArray -> SetValue(maskScalar, numberOfValues);
            
          }
          inPtr+=inIncX;
          maskPtr += maskIncX;
      }
      inPtr += inIncY;
      maskPtr += maskIncY;
    }  
    inPtr += inIncZ;
    maskPtr += maskIncZ;
  }
  
  //printf("done\n");
  for(int i=0;i<n;i++) {
     avg = avgArray->GetValue(i);
     numberOfValues = numArray -> GetValue(i);
     //printf("Setting value %d to %f / %d = %f",i,avg,numberOfValues,avg / numberOfValues);
     avg /= numberOfValues;     
     avgArray -> SetValue(i,avg);
  }
  
}

int vtkImageLabelAverage::SplitExtent(int splitExt[6], 
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
void vtkImageLabelAverage::ThreadedRequestData (
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
    vtkTemplateMacro(vtkImageLabelAverageExecute(this, id,
                    this->GetNumberOfInputConnections(0),inData[0],
                    outData[0], outExt,static_cast<VTK_TT *>(0)));
  default:
    vtkErrorMacro(<< "Execute: Unknown ScalarType");
  return;
  }

}


//-----------------------------------------------------------------------------
void vtkImageLabelAverage::PrintSelf(ostream& os, vtkIndent indent)
{
  this->Superclass::PrintSelf(os,indent);


}




