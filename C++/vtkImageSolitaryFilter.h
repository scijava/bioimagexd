/*=========================================================================

  Program:   BioImageXD
  Module:    $RCSfile: vtkImageSolitaryFilter.h,v $

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
// .NAME vtkImageSolitaryFilter - select piece (e.g., volume of interest) and/or subsample structured points dataset

// .SECTION Description
// vtkImageSolitaryFilter is a filter that sets to zero pixels/voxels that have scalar
// values over a specified threshold but do not have horizontal/vertical neighborhood pixels
//  with scalar values over the respective thresholds


// .SECTION See Also
// vtkGeometryFilter vtkExtractGeometry vtkExtractGrid

#ifndef __vtkImageSolitaryFilter_h
#define __vtkImageSolitaryFilter_h

#include "vtkThreadedImageAlgorithm.h"

class VTK_IMAGING_EXPORT vtkImageSolitaryFilter : public vtkThreadedImageAlgorithm
{
public:
  vtkTypeRevisionMacro(vtkImageSolitaryFilter, vtkThreadedImageAlgorithm);
  void PrintSelf(ostream& os, vtkIndent indent);

  // Description:
  // Construct object to extract all of the input data.
  static vtkImageSolitaryFilter *New();
     
  // Description:
  // Specify the X threshold. Horizontal neighboring pixels that 
  // have lower scalar value than this will be set to zero
  vtkSetMacro(HorizontalThreshold,int);
  vtkGetMacro(HorizontalThreshold,int);
  // Description:
  // Specify the Y threshold. Vertical neighboring pixels that 
  // have lower scalar value than this will be set to zero
  vtkSetMacro(VerticalThreshold,int);
  vtkGetMacro(VerticalThreshold,int);
  // Description:
  // Specify the filtering threshold. Pixels with scalar value over
  // this threshold are inspected.
  vtkSetMacro(FilteringThreshold,int);  
  vtkGetMacro(FilteringThreshold,int);


protected:
  vtkImageSolitaryFilter();
  ~vtkImageSolitaryFilter() {};


  virtual int RequestUpdateExtent (
  vtkInformation* vtkNotUsed(request),
  vtkInformationVector** inputVector,
  vtkInformationVector* outputVector);  
  // Method that can be called by multiple threads that is given the input data and an input extent
  // and is responsible for producing the matching output data.
  void ThreadedRequestData (vtkInformation* request, vtkInformationVector** inputVector,
                            vtkInformationVector* outputVector,vtkImageData ***inData, vtkImageData **outData,
                            int ext[6], int id);

  // Implement methods required by vtkAlgorithm.
  virtual int FillInputPortInformation(int, vtkInformation*);  
  int HorizontalThreshold;
  int VerticalThreshold;
  int FilteringThreshold;
private:
  vtkImageSolitaryFilter(const vtkImageSolitaryFilter&);  // Not implemented.
  void operator=(const vtkImageSolitaryFilter&);  // Not implemented.
};

#endif


