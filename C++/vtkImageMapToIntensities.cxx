/*=========================================================================

  Program:   BioImageXD
  Module:    $RCSfile: vtkImageMapToIntensities.cxx,v $

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
#include "vtkImageMapToIntensities.h"

#include "vtkCellData.h"
#include "vtkImageData.h"
#include "vtkObjectFactory.h"
#include "vtkPointData.h"
#include "vtkInformation.h"
#include "vtkInformationVector.h"
#include "vtkStreamingDemandDrivenPipeline.h"

vtkCxxRevisionMacro(vtkImageMapToIntensities, "$Revision: 1.36 $");
vtkStandardNewMacro(vtkImageMapToIntensities);

//-----------------------------------------------------------------------------
// Construct object to extract all of the input data.
vtkImageMapToIntensities::vtkImageMapToIntensities()
{
    this->IntensityTransferFunction = 0;
}


int vtkImageMapToIntensities::FillInputPortInformation(
  int port, vtkInformation* info)
{
  info->Set(vtkAlgorithm::INPUT_IS_REPEATABLE(), 0);

  info->Set(vtkAlgorithm::INPUT_REQUIRED_DATA_TYPE(), "vtkImageData");

  return 1;
}
//-----------------------------------------------------------------------------
// This templated function executes the filter for any type of data.
template <class T>
void vtkImageMapToIntensitiesExecute(vtkImageMapToIntensities *self, int id,int NumberOfInputs,
                           vtkImageData **inData,vtkImageData*outData,int outExt[6],
                            T*)
{    
  int uExtent[6];
  vtkIdType inIncX,inIncY,inIncZ;
  vtkIdType outIncX,outIncY,outIncZ;
  int maxX,maxY,maxZ,maxC;
  int idxX,idxY,idxZ,idxC;
  T *inPtr, *outPtr;
  int* table;
    
  vtkIntensityTransferFunction * IntensityTransferFunction;
    
  IntensityTransferFunction = self->GetIntensityTransferFunction();

  T scalar,newScalar,cmpScalar;
  if(!IntensityTransferFunction) {
      vtkErrorWithObjectMacro(self,"No IntensityTransferFunction specified");
      return;
  }
  table = IntensityTransferFunction->GetDataPointer();
 
  inPtr = (T*) inData[0]->GetScalarPointerForExtent(outExt);
  
  outPtr = (T *) outData->GetScalarPointerForExtent(outExt);
    
  
//  output->SetExtent(output->GetWholeExtent());
//  output->AllocateScalars();
  if (IntensityTransferFunction->IsIdentical()) {
      outData->DeepCopy(inData[0]);
      return;
  }
  //input->GetIncrements(inIncX, inIncY, inIncZ);
  //output->GetIncrements(outIncX, outIncY, outIncZ);
  
  inData[0]->GetContinuousIncrements(outExt,inIncX, inIncY, inIncZ);
  outData->GetContinuousIncrements(outExt,outIncX, outIncY, outIncZ);
  
  maxX = outExt[1] - outExt[0];
  maxY = outExt[3] - outExt[2];
  maxZ = outExt[5] - outExt[4];
  maxC = inData[0]->GetNumberOfScalarComponents();


  #define GET_AT(x,y,z,c,ptr) *(ptr+(z)*inIncZ+(y)*inIncY+(x)*inIncX+c)
  #define SET_AT(x,y,z,c,ptr,val) *(ptr+(z)*outIncZ+(y)*outIncY+(x)*outIncX+c)=val

  char progressText[200];
  for(idxZ = 0; idxZ <= maxZ; idxZ++ ) {
    self->UpdateProgress(idxZ/float(maxZ));
    sprintf(progressText,"Applying intensity transfer function (slice %d / %d)",idxZ,maxZ);
    self->SetProgressText(progressText);

    for(idxY = 0; idxY <= maxY; idxY++ ) {
      for(idxX = 0; idxX <= maxX; idxX++ ) {
          for(idxC = 0; idxC < maxC; idxC++ ) {
            //scalar = *inPtr++;
            //scalar = GET_AT(idxX+uExtent[0],idxY+uExtent[2],idxZ+uExtent[4],idxC,inPtr);
            scalar = *inPtr++;
            
            newScalar=table[(int)scalar];
            //SET_AT(idxX+uExtent[0],idxY+uExtent[2],idxZ+uExtent[4],idxC,outPtr,newScalar);
              
            *outPtr=newScalar;
             outPtr++;
          }
          outPtr+=outIncX;
          inPtr+=inIncX;
      }
      inPtr += inIncY;
      outPtr += outIncY;
    }  
    inPtr += inIncZ;
    outPtr += outIncZ;      
  }
  //printf("done\n");
  
}

//----------------------------------------------------------------------------
// This method is passed a input and output regions, and executes the filter
// algorithm to fill the output from the inputs.
// It just executes a switch statement to call the correct function for
// the regions data types.
void vtkImageMapToIntensities::ThreadedRequestData (
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

//  printf("Number of connections=%d, outExt=%d,%d,%d,%d,%d,%d\n",this->GetNumberOfInputConnections(0),
//                 outExt[0],outExt[1],outExt[2],outExt[3],outExt[4],outExt[5]);

    switch (inData[0][0]->GetScalarType())
  {
    vtkTemplateMacro(vtkImageMapToIntensitiesExecute(this, id,
                    this->GetNumberOfInputConnections(0),inData[0],
                    outData[0], outExt,static_cast<VTK_TT *>(0)));
  default:
    vtkErrorMacro(<< "Execute: Unknown ScalarType");
  return;
  }

}


//-----------------------------------------------------------------------------
void vtkImageMapToIntensities::PrintSelf(ostream& os, vtkIndent indent)
{
  this->Superclass::PrintSelf(os,indent);

  os << indent << "IntensityTransferFunction "<< this->IntensityTransferFunction << "\n";

}




