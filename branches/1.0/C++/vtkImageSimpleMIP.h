/*=========================================================================

  Program:   BioImageXD
  Module:    $RCSfile: vtkImageSimpleMIP.h,v $

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


