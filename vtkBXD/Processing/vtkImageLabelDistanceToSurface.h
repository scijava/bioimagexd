/*=========================================================================

  Program:   BioImageXD
  Module:    $RCSfile: vtkImageLabelDistanceToSurface.h,v $

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
// .NAME vtkImageLabelDistanceToSurface - select piece (e.g., volume of interest) and/or subsample structured points dataset

// .SECTION Description
// vtkImageLabelDistanceToSurface is a filter that sets to zero pixels/voxels that have scalar
// values over a specified threshold but do not have horizontal/vertical neighborhood pixels
//  with scalar values over the respective thresholds


// .SECTION See Also
// vtkGeometryFilter vtkExtractGeometry vtkExtractGrid

#ifndef __vtkImageLabelDistanceToSurface_h
#define __vtkImageLabelDistanceToSurface_h

#include "vtkBXDProcessingWin32Header.h"
#include "vtkOBBTree.h"

#include "vtkImageData.h"
#include "vtkInformationVector.h"
#include "vtkObjectFactory.h"
#include "vtkThreadedImageAlgorithm.h"
#include "vtkDoubleArray.h"
#include "vtkUnsignedIntArray.h"

class VTK_BXD_PROCESSING_EXPORT vtkImageLabelDistanceToSurface : public vtkThreadedImageAlgorithm
{
public:
  vtkTypeRevisionMacro(vtkImageLabelDistanceToSurface,vtkThreadedImageAlgorithm);
  void PrintSelf(ostream& os, vtkIndent indent);

  // Description:
  // Construct object to extract all of the input data.
  static vtkImageLabelDistanceToSurface *New();     

  //virtual void ComputeInputUpdateExtent(int inExt[6], int outExt[6]);

  vtkDoubleArray* GetAverageDistanceToSurfaceArray() { return DistanceToSurfaceArray; }  
  vtkDoubleArray* GetAverageDistanceToPointArray() { return DistanceToPointArray; }
  vtkDoubleArray* GetAverageDistanceToSurfaceStdErrArray() { return DistanceToSurfaceStdErrArray; }
  vtkDoubleArray* GetAverageDistanceToPointStdErrArray() { return DistanceToPointStdErrArray; }
  
  vtkUnsignedIntArray* GetOutsideCountArray() { return OutsideCountArray; }
  vtkUnsignedIntArray* GetInsideCountArray() { return InsideCountArray; }

  // Description:
  // The locator for determining whether a voxel position is inside or outside the surface
  vtkGetObjectMacro(SurfaceLocator, vtkOBBTree);
  vtkSetObjectMacro(SurfaceLocator, vtkOBBTree);

  int SplitExtent(int splitExt[6], 
                  int startExt[6], 
                  int num, int total);


  // Description:
  // Set the background level (number of objects in the label image to ignore in calculating the
  // inside and outside totals)
  vtkGetMacro(BackgroundLevel,int);
  vtkSetMacro(BackgroundLevel,int);   
  
  // Description:
  // Set a point to which an average distance from each label object will
  // be measured
  vtkGetVectorMacro(MeasurePoint,double,3);
  vtkSetVectorMacro(MeasurePoint,double,3);

  // Description:
  // Set the physical scaling of a single voxel
  vtkGetVectorMacro(VoxelSize,double,3);
  vtkSetVectorMacro(VoxelSize,double,3);
  
  // Description:
  // The number of voxels inside 

protected:
  vtkImageLabelDistanceToSurface();
  ~vtkImageLabelDistanceToSurface() {};

  
  // Method that can be called by multiple threads that is given the input data and an input extent
  // and is responsible for producing the matching output data.
  void ThreadedRequestData (vtkInformation* request,
                            vtkInformationVector** inputVector,
                            vtkInformationVector* outputVector,
                            vtkImageData ***inData, vtkImageData **outData,
                            int ext[6], int id);

  // Implement methods required by vtkAlgorithm.
  virtual int FillInputPortInformation(int, vtkInformation*);  
  
private:
  vtkDoubleArray* DistanceToSurfaceArray;
  vtkDoubleArray* DistanceToPointArray;
  vtkDoubleArray* DistanceToSurfaceStdErrArray;
  vtkDoubleArray* DistanceToPointStdErrArray;
  vtkUnsignedIntArray* InsideCountArray;
  vtkUnsignedIntArray* OutsideCountArray;
  vtkOBBTree* SurfaceLocator;
  double MeasurePoint[3];
  double VoxelSize[3];
  int VoxelsInside;
  int BackgroundLevel;
  vtkImageLabelDistanceToSurface(const vtkImageLabelDistanceToSurface&);  // Not implemented.
  void operator=(const vtkImageLabelDistanceToSurface&);  // Not implemented.
};

#endif
