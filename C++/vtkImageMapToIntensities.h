/*=========================================================================

  Program:   Visualization Toolkit
  Module:    $RCSfile: vtkImageMapToIntensities.h,v $

  Copyright (c) Ken Martin, Will Schroeder, Bill Lorensen
  All rights reserved.
  See Copyright.txt or http://www.kitware.com/Copyright.htm for details.

     This software is distributed WITHOUT ANY WARRANTY; without even
     the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
     PURPOSE.  See the above copyright notice for more information.

=========================================================================*/
// .NAME vtkImageMapToIntensities - select piece (e.g., volume of interest) and/or subsample structured points dataset

// .SECTION Description
// vtkImageMapToIntensities is a filter that sets to zero pixels/voxels that have scalar
// values over a specified threshold but do not have horizontal/vertical neighborhood pixels
//  with scalar values over the respective thresholds


// .SECTION See Also
// vtkGeometryFilter vtkExtractGeometry vtkExtractGrid

#ifndef __vtkImageMapToIntensities_h
#define __vtkImageMapToIntensities_h

#include "vtkImageToImageFilter.h"
#include "vtkIntensityTransferFunction.h"

class VTK_IMAGING_EXPORT vtkImageMapToIntensities : public vtkImageToImageFilter
{
public:
  vtkTypeRevisionMacro(vtkImageMapToIntensities,vtkImageToImageFilter);
  void PrintSelf(ostream& os, vtkIndent indent);

  // Description:
  // Construct object to extract all of the input data.
  static vtkImageMapToIntensities *New();     
  // Description:
  // Set the vtkIntensityTransferFunction through which the scalars
  // are mapped
  void SetIntensityTransferFunction(vtkIntensityTransferFunction* itf) {
      this->IntensityTransferFunction = itf;
      this->Modified();
  }
  virtual void ComputeInputUpdateExtent(int inExt[6], int outExt[6]);



protected:
  vtkImageMapToIntensities();
  ~vtkImageMapToIntensities() {};

  void ExecuteInformation(vtkImageData *input, vtkImageData *output);
  void ExecuteInformation(){this->vtkImageToImageFilter::ExecuteInformation();};
  virtual void ExecuteData(vtkDataObject *);

  vtkIntensityTransferFunction* IntensityTransferFunction;
private:
  vtkImageMapToIntensities(const vtkImageMapToIntensities&);  // Not implemented.
  void operator=(const vtkImageMapToIntensities&);  // Not implemented.
};

#endif


