/*=========================================================================

  Program:   BioImageXD
  Module:    $RCSfile: vtkImageColocalizationFilter.cxx,v $

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
#include "vtkImageColocalizationFilter.h"

#include "vtkImageData.h"
#include "vtkObjectFactory.h"
#include "vtkImageIterator.h"
#include "vtkInformation.h"
#include "vtkInformationVector.h"
#include "vtkStreamingDemandDrivenPipeline.h"
vtkCxxRevisionMacro(vtkImageColocalizationFilter, "$Revision: 1.25 $");
vtkStandardNewMacro(vtkImageColocalizationFilter);

//----------------------------------------------------------------------------
vtkImageColocalizationFilter::vtkImageColocalizationFilter()
{
    this->SetNumberOfThreads(1);
    this->OutputDepth = 8;
    this->NumberOfDatasets = 8;
    this->OutputScalarValue = -1;
    this->ColocalizationLowerThresholds = new int[this->NumberOfDatasets];
    this->ColocalizationUpperThresholds = new int[this->NumberOfDatasets];
    for(int i = 0; i < this->NumberOfDatasets; i++) {
        this->ColocalizationUpperThresholds[i]=255;
        this->ColocalizationLowerThresholds[i]=0;
    }
}

void vtkImageColocalizationFilter::SetColocalizationLowerThreshold(int dataset, int threshold) {
    int *NewThresholds;
    if (this->NumberOfDatasets < dataset) {
            NewThresholds = new int[this->NumberOfDatasets *2];

            for(int i = 0; i< this->NumberOfDatasets ; i++) {
                NewThresholds[i] = this->ColocalizationLowerThresholds[i];
            }
            for(int i = this->NumberOfDatasets; i < this->NumberOfDatasets*2; i++) {
                NewThresholds[i]=0;
            }
            this->NumberOfDatasets *= 2;
            delete[] this->ColocalizationLowerThresholds;
            this->ColocalizationLowerThresholds = NewThresholds;
    }
    this->ColocalizationLowerThresholds[dataset] = threshold;
}
void vtkImageColocalizationFilter::SetColocalizationUpperThreshold(int dataset, int threshold) {
    int *NewThresholds;
    if (this->NumberOfDatasets < dataset) {

            NewThresholds = new int[this->NumberOfDatasets *2];
            
            for(int i = 0; i< this->NumberOfDatasets ; i++) {
                NewThresholds[i] = this->ColocalizationUpperThresholds[i];
            }
            for(int i = this->NumberOfDatasets; i < this->NumberOfDatasets*2; i++) {
                NewThresholds[i]=0;
            }
            this->NumberOfDatasets *= 2;
            delete[] this->ColocalizationUpperThresholds;
            this->ColocalizationUpperThresholds = NewThresholds;
    }
    this->ColocalizationUpperThresholds[dataset] = threshold;
}

//----------------------------------------------------------------------------
vtkImageColocalizationFilter::~vtkImageColocalizationFilter()
{
        delete[] this->ColocalizationLowerThresholds;
        delete[] this->ColocalizationUpperThresholds;
}

// The output extent is the same as the input extent.
int vtkImageColocalizationFilter::RequestInformation (
  vtkInformation * vtkNotUsed(request),
  vtkInformationVector **inputVector,
  vtkInformationVector *outputVector)
{
  // get the info objects
  vtkInformation* outInfo = outputVector->GetInformationObject(0);
  vtkInformation *inInfo = inputVector[0]->GetInformationObject(0);

  int ext[6], ext2[6], idx;

  inInfo->Get(vtkStreamingDemandDrivenPipeline::WHOLE_EXTENT(),ext);
  outInfo->Set(vtkStreamingDemandDrivenPipeline::WHOLE_EXTENT(),ext,6);

  return 1;
}

//----------------------------------------------------------------------------
// This templated function executes the filter for any type of data.
template <class T>
void vtkImageColocalizationFilterExecute(vtkImageColocalizationFilter *self, int id,int NumberOfInputs,
                           vtkImageData **inData,vtkImageData *outData,int outExt[6],
                            T*)
{
    int i, maxval = 0, n =0;
    vtkIdType inIncX,inIncY,inIncZ;
    vtkIdType outIncX,outIncY,outIncZ;
    int maxX,maxY,maxZ;
    int idxX,idxY,idxZ;
    unsigned long count = 0;
    unsigned long target;        
    double ColocalizationScalar=0;
    T currScalar = 0;
    char colocFlag = 0;

    double OutputScalar = self->GetOutputScalarValue();

    int *ColocThresholds = self->GetColocalizationLowerThresholds();
    int *UpperThresholds = self->GetColocalizationUpperThresholds();
    int BitDepth = self->GetOutputDepth();

    T** inPtrs;
    T* outPtr;

    inPtrs = new T*[NumberOfInputs];

    for (i=0; i < NumberOfInputs; i++) {
        inPtrs[i] = (T*)inData[i]->GetScalarPointerForExtent(outExt);
    }
    outPtr = (T*)outData->GetScalarPointerForExtent(outExt);

    inData[0]->GetContinuousIncrements(outExt, inIncX, inIncY, inIncZ);
    outData->GetContinuousIncrements(outExt, outIncX, outIncY, outIncZ);

    maxX = outExt[1] - outExt[0];
    maxY = outExt[3] - outExt[2];
    maxZ = outExt[5] - outExt[4];

    maxval = int(pow(2.0f,8.0f*sizeof(T)))-1;
    
    if (OutputScalar < 0) {
        OutputScalar = maxval;    
    }

    char progressText[200];
    target = (unsigned long)((maxZ+1)*(maxY+1)/50.0);
    target++;

    for (idxZ = 0; idxZ <= maxZ; idxZ++ ) {
        sprintf(progressText,"Calculating colocalization (slice %d / %d)",idxZ,maxZ);
        self->SetProgressText(progressText);

        for (idxY = 0; idxY <= maxY; idxY++ ) {
           if (!id)
           {
                if (!(count%target))
                {
                    self->UpdateProgress(count/(50.0*target));
                }
                count++;
           }             
          
          for (idxX = 0; idxX <= maxX; idxX++ ) {
            currScalar = n = 0;
            colocFlag = 1;
            for (i=0; i < NumberOfInputs; i++ ) {
                currScalar = *inPtrs[i];
                if(currScalar >= ColocThresholds[i] && currScalar <= UpperThresholds[i]) {
                    ColocalizationScalar += currScalar;
                    n++;
                } 
				else {
                    colocFlag = 0;
                }
                inPtrs[i]++;
            }
            if (colocFlag > 0) {
                if (BitDepth == 1 ) ColocalizationScalar = OutputScalar;
                if (BitDepth == 8 ) {
                    ColocalizationScalar /= n;
                }
                if (ColocalizationScalar > maxval) ColocalizationScalar=maxval;
            }
			else ColocalizationScalar = 0;
            
            *outPtr = (T)ColocalizationScalar;
            outPtr++;
            ColocalizationScalar = 0;
          }
          for (i=0; i < NumberOfInputs; i++ ) {
              inPtrs[i]+=inIncY;
          }
          outPtr += outIncY;
        }
        for (i=0; i < NumberOfInputs; i++ ) {
          inPtrs[i]+=inIncZ;
        }
        outPtr += outIncZ;      
    }
    delete[] inPtrs;
}

//----------------------------------------------------------------------------
// This method is passed a input and output regions, and executes the filter
// algorithm to fill the output from the inputs.
// It just executes a switch statement to call the correct function for
// the regions data types.
void vtkImageColocalizationFilter::ThreadedRequestData (
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
    vtkTemplateMacro(vtkImageColocalizationFilterExecute(this, id,
                    this->GetNumberOfInputConnections(0),inData[0],
                    outData[0],outExt,static_cast<VTK_TT *>(0)));
  default:
    vtkErrorMacro(<< "Execute: Unknown ScalarType");
  return;
  }

}

int vtkImageColocalizationFilter::FillInputPortInformation(
  int port, vtkInformation* info)
{
  info->Set(vtkAlgorithm::INPUT_IS_REPEATABLE(), 1);

  info->Set(vtkAlgorithm::INPUT_REQUIRED_DATA_TYPE(), "vtkImageData");
  return 1;
}

void vtkImageColocalizationFilter::PrintSelf(ostream& os, vtkIndent indent)
{
  this->Superclass::PrintSelf(os,indent);
  for(int i=0;i<this->GetNumberOfInputConnections(0);i++) {
          os << indent << "Lower Threshold ("<<i<<"):" <<this->ColocalizationLowerThresholds[i] << "\n";
          os << indent << "Upper Threshold ("<<i<<"):" <<this->ColocalizationUpperThresholds[i]<< "\n";
  }
}


