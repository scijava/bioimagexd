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
#include "vtkImageLabelDistanceToSurface.h"

#include "vtkCellData.h"
#include "vtkImageData.h"
#include "vtkObjectFactory.h"
#include "vtkPointData.h"
#include "vtkInformation.h"
#include "vtkInformationVector.h"
#include "vtkStreamingDemandDrivenPipeline.h"
#include "vtkUnsignedLongArray.h"
#include "vtkDoubleArray.h"
#include "vtkPolyData.h"
#include "vtkPointLocator.h"
#include "vtkMath.h"

#include <vtkstd/map>
#include <vtkstd/list>
#include <vtkstd/algorithm>

vtkCxxRevisionMacro(vtkImageLabelDistanceToSurface, "$Revision: 1.36 $");
vtkStandardNewMacro(vtkImageLabelDistanceToSurface);

//-----------------------------------------------------------------------------
// Construct object to extract all of the input data.
vtkImageLabelDistanceToSurface::vtkImageLabelDistanceToSurface()
{
  BackgroundLevel = 1;
  this->DistanceToSurfaceArray = vtkDoubleArray::New();
  this->DistanceToPointArray = vtkDoubleArray::New();
  this->DistanceToSurfaceStdErrArray = vtkDoubleArray::New();
  this->DistanceToPointStdErrArray = vtkDoubleArray::New();
  this->InsideCountArray = vtkUnsignedIntArray::New();
  this->OutsideCountArray = vtkUnsignedIntArray::New();
  this->MeasurePoint[0] = this->MeasurePoint[1] = this->MeasurePoint[2] = 0;
  this->SurfaceLocator = 0;
  this->VoxelSize[0] = this->VoxelSize[1] = this->VoxelSize[2] = 0.0;
  this->VoxelsInside = 0;
  this->BackgroundLevel = 0;
  this->SetNumberOfInputPorts(2);
}


int vtkImageLabelDistanceToSurface::FillInputPortInformation(
  int port, vtkInformation* info)
{
  info->Set(vtkAlgorithm::INPUT_IS_REPEATABLE(), 1);

  if(port == 0) {
	  info->Set(vtkAlgorithm::INPUT_REQUIRED_DATA_TYPE(), "vtkImageData");
  } else {
	  info->Set(vtkAlgorithm::INPUT_REQUIRED_DATA_TYPE(), "vtkPolyData");
  }
  return 1;
}
//-----------------------------------------------------------------------------
// This templated function executes the filter for any type of data.
template <class T>
void vtkImageLabelDistanceToSurfaceExecute(vtkImageLabelDistanceToSurface *self, int id,int NumberOfInputs,
                           vtkImageData **inData,vtkImageData*outData,vtkPolyData* surface, int outExt[6], T*)
{
  vtkIdType inIncX,inIncY,inIncZ;
  int maxX,maxY,maxZ,maxC;
  int idxX,idxY,idxZ,idxC;
  T *fgPtr;
  
  int inside = 0;
  unsigned long count = 0;
  unsigned long target;

  double VoxelSize[3];
  self->GetVoxelSize(VoxelSize);
  double* MeasurePoint = self->GetMeasurePoint();
  for (int i = 0; i < 3; ++i)
	{
	  MeasurePoint[i] *= VoxelSize[i];
	}

  vtkDoubleArray* distanceToSurfaceArray = self->GetAverageDistanceToSurfaceArray();
  vtkDoubleArray* distanceToSurfaceStdErrArray = self->GetAverageDistanceToSurfaceStdErrArray();
  vtkDoubleArray* distanceToPointArray = self->GetAverageDistanceToPointArray();
  vtkDoubleArray* distanceToPointStdErrArray = self->GetAverageDistanceToPointStdErrArray();
  vtkOBBTree* insideLocator = self->GetSurfaceLocator();
  vtkUnsignedLongArray* ObjectSizeArray =  vtkUnsignedLongArray::New();
  vtkUnsignedIntArray *inCount = self->GetInsideCountArray();
  vtkUnsignedIntArray* outCount = self->GetOutsideCountArray();
  int bgLevel = self->GetBackgroundLevel();
  T fgScalar;
  
  fgPtr = (T*) inData[0]->GetScalarPointerForExtent(outExt);
  
  double Spacing[3];
  double Point[3], Point2[3];
  printf("Calculating average distance...\n");

  inData[0]->GetSpacing(Spacing);
  printf("Spacing = %f, %f, %f\n", Spacing[0], Spacing[1], Spacing[2]);
  outData->DeepCopy(inData[0]);
  
  inData[0]->GetContinuousIncrements(outExt,inIncX, inIncY, inIncZ);
  maxX = outExt[1] - outExt[0];
  maxY = outExt[3] - outExt[2];
  maxZ = outExt[5] - outExt[4];
  maxC = inData[0]->GetNumberOfScalarComponents();

  unsigned long n = 0,  numberOfValues = 0;

  double range[2]; 

  inData[0]->GetScalarRange(range);
  printf("Range = %f, %f\n", range[0], range[1]);
  ObjectSizeArray->SetNumberOfValues((unsigned long)range[1]+1);
  distanceToSurfaceArray->SetNumberOfValues((unsigned long)range[1]+1);
  distanceToPointArray->SetNumberOfValues((unsigned long)range[1]+1);
  distanceToSurfaceStdErrArray->SetNumberOfValues((unsigned long)range[1]+1);
  distanceToPointStdErrArray->SetNumberOfValues((unsigned long)range[1]+1);
  outCount->SetNumberOfValues((unsigned long)range[1]+1);
  inCount->SetNumberOfValues((unsigned long)range[1]+1);
	
  char progressText[200];


  for(int i=0;i<range[1]+1;i++) {
     ObjectSizeArray->SetValue(i, 0);
     distanceToSurfaceArray->SetValue(i, 0);
     distanceToPointArray->SetValue(i, 0);
     distanceToSurfaceStdErrArray->SetValue(i, 0);
     distanceToPointStdErrArray->SetValue(i, 0);
     inCount->SetValue(i, 0);
     outCount->SetValue(i, 0);
  }
  
  vtkPointLocator *locator = vtkPointLocator::New();
  locator->SetDataSet(surface);
  locator->BuildLocator();  
  
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
            if(fgScalar) {
				ObjectSizeArray->SetValue(fgScalar, ObjectSizeArray->GetValue(fgScalar)+1);
				// First convert current voxel to position in VTK space (use vtk Spacing)
				double x = idxX*Spacing[0], y = idxY*Spacing[1], z = idxZ*Spacing[2];
				
				double currPos[3];
				currPos[0] = x; currPos[1] = y; currPos[2] = z;
				inside = insideLocator->InsideOrOutside(currPos);
				if(inside==-1) inCount->SetValue(fgScalar, inCount->GetValue(fgScalar)+1);
				else outCount->SetValue(fgScalar, outCount->GetValue(fgScalar)+1);

				// Locate the nearest point on the given surface 
				double findPoint[3];
				findPoint[0] = x;
				findPoint[1] = y;
				findPoint[2] = z;
				vtkIdType objId = locator->FindClosestPoint(findPoint);
				surface->GetPoint(objId, Point);
				 //printf("Point = %f, %f, %f\n", Point[0], Point[1], Point[2]);

				 // descale it from the VTK spacing
				Point[0] /= Spacing[0];
				Point[1] /= Spacing[1];
				Point[2] /= Spacing[2];
				 // and rescale it using the voxel sizes
				 //printf("Voxel size = %f, %f, %f\n", VoxelSize[0], VoxelSize[1], VoxelSize[2]);
				Point[0] *= VoxelSize[0];
				Point[1] *= VoxelSize[1];
				Point[2] *= VoxelSize[2];
				 
				 // finally scale the current voxel pos using voxel sizes
				Point2[0] = idxX*VoxelSize[0];
				Point2[1] = idxY*VoxelSize[1];
				Point2[2] = idxZ*VoxelSize[2];
				
	
				// calculate the resulting distance and add it to the array
				double distancepow = vtkMath::Distance2BetweenPoints(Point, Point2);
				double distance = sqrt(distancepow);
				distanceToSurfaceArray->SetValue(fgScalar, distanceToSurfaceArray->GetValue(fgScalar)+distance);
				distanceToSurfaceStdErrArray->SetValue(fgScalar, distanceToSurfaceStdErrArray->GetValue(fgScalar)+distancepow);

				distancepow = vtkMath::Distance2BetweenPoints(MeasurePoint, Point2);
				distance = sqrt(distancepow);
				
				distanceToPointArray->SetValue(fgScalar, distanceToPointArray->GetValue(fgScalar)+distance);
				distanceToPointStdErrArray->SetValue(fgScalar, distanceToPointStdErrArray->GetValue(fgScalar)+distancepow);
	         }
          }
          fgPtr+=inIncX;
      }
      fgPtr += inIncY;
    }
    fgPtr += inIncZ;
  }
  
  for(int i = 0; i < range[1] + 1; i++) {
	double numberOfValues = ObjectSizeArray->GetValue(i);
	double newValue = distanceToSurfaceArray->GetValue(i);
	if (numberOfValues > 0) newValue /= numberOfValues;
     //printf("Dividing %d sum %f by %d = %f\n", i,  distanceToSurfaceArray->GetValue(i), ObjectSizeArray->GetValue(i), newValue);
	distanceToSurfaceArray->SetValue(i, newValue);
	double distanceStdErr = distanceToSurfaceStdErrArray->GetValue(i);
	if (numberOfValues > 0) distanceStdErr /= numberOfValues;
	distanceStdErr -= pow(newValue,2);
	distanceStdErr = sqrt(fabs(distanceStdErr)); // fabs here just in case we have a rounding error when only one voxel is in object
	if (numberOfValues > 0) distanceStdErr /= sqrt(numberOfValues);
	distanceToSurfaceStdErrArray->SetValue(i, distanceStdErr);

	newValue = distanceToPointArray->GetValue(i);
	if (numberOfValues > 0) newValue /= numberOfValues;
	distanceToPointArray->SetValue(i, newValue);
	distanceStdErr = distanceToPointStdErrArray->GetValue(i);
	if (numberOfValues > 0) distanceStdErr /= numberOfValues;
	distanceStdErr -= pow(newValue,2);
	distanceStdErr = sqrt(fabs(distanceStdErr));
	if (numberOfValues > 0) distanceStdErr /= numberOfValues;
	distanceToPointStdErrArray->SetValue(i, distanceStdErr);
  }

  ObjectSizeArray->Delete();
}

int vtkImageLabelDistanceToSurface::SplitExtent(int splitExt[6], 
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
void vtkImageLabelDistanceToSurface::ThreadedRequestData (
  vtkInformation * vtkNotUsed( request ),
  vtkInformationVector** inputVector,
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


  vtkInformation *inInfo = inputVector[1]->GetInformationObject(0);
  vtkPolyData* surface = 
    vtkPolyData::SafeDownCast(inInfo->Get(vtkDataObject::DATA_OBJECT()));

    switch (inData[0][0]->GetScalarType())
  {
    vtkTemplateMacro(vtkImageLabelDistanceToSurfaceExecute(this, id,
                    this->GetNumberOfInputConnections(0),inData[0],  
                    outData[0],surface, outExt,static_cast<VTK_TT *>(0)));
  default:
    vtkErrorMacro(<< "Execute: Unknown ScalarType");
  return;
  }

}


//-----------------------------------------------------------------------------
void vtkImageLabelDistanceToSurface::PrintSelf(ostream& os, vtkIndent indent)
{
  this->Superclass::PrintSelf(os,indent);


}




