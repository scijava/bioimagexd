/*=========================================================================

  Program:   Visualization Toolkit
  Module:    $RCSfile: vtkImageSimpleMIP.h,v $

  Copyright (c) Ken Martin, Will Schroeder, Bill Lorensen
  All rights reserved.
  See Copyright.txt or http://www.kitware.com/Copyright.htm for details.

     This software is distributed WITHOUT ANY WARRANTY; without even
     the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
     PURPOSE.  See the above copyright notice for more information.

=========================================================================*/
// .NAME vtkImageSimpleMIP - do a simple MIP of image (looking from above)

// .SECTION Description
// vtkImageSimpleMIP is a filter that sets to zero pixels/voxels that have scalar
// values over a specified threshold but do not have horizontal/vertical neighborhood pixels
//  with scalar values over the respective thresholds


// .SECTION See Also
// vtkGeometryFilter vtkExtractGeometry vtkExtractGrid

#ifndef __vtkImageSimpleMIP_h
#define __vtkImageSimpleMIP_h

#include "vtkImageToImageFilter.h"

class VTK_IMAGING_EXPORT vtkImageSimpleMIP : public vtkImageToImageFilter
{
public:
  vtkTypeRevisionMacro(vtkImageSimpleMIP,vtkImageToImageFilter);
  void PrintSelf(ostream& os, vtkIndent indent);

  // Description:
  // Construct object to extract all of the input data.
  static vtkImageSimpleMIP *New();
     


protected:
  vtkImageSimpleMIP();
  ~vtkImageSimpleMIP() {};

  virtual void ComputeInputUpdateExtent(int inExt[6], int outExt[6]);
  void ExecuteInformation(vtkImageData *input, vtkImageData *output);
  //void ExecuteInformation(){this->vtkImageToImageFilter::ExecuteInformation();};
  virtual void ExecuteData(vtkDataObject *);

private:
  vtkImageSimpleMIP(const vtkImageSimpleMIP&);  // Not implemented.
  void operator=(const vtkImageSimpleMIP&);  // Not implemented.
};

#endif


