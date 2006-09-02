/*=========================================================================

  Program:   BioImageXD
  Module:    $RCSfile: vtkImageMapToIntensities.h,v $

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
// .NAME vtkImageMapToIntensities - select piece (e.g., volume of interest) and/or subsample structured points dataset

// .SECTION Description
// vtkImageMapToIntensities is a filter that sets to zero pixels/voxels that have scalar
// values over a specified threshold but do not have horizontal/vertical neighborhood pixels
//  with scalar values over the respective thresholds


// .SECTION See Also
// vtkGeometryFilter vtkExtractGeometry vtkExtractGrid

#ifndef __vtkImageMapToIntensities_h
#define __vtkImageMapToIntensities_h

#include "vtkThreadedImageAlgorithm.h"
#include "vtkIntensityTransferFunction.h"

class VTK_IMAGING_EXPORT vtkImageMapToIntensities : public vtkThreadedImageAlgorithm
{
public:
  vtkTypeRevisionMacro(vtkImageMapToIntensities,vtkThreadedImageAlgorithm);
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
  //virtual void ComputeInputUpdateExtent(int inExt[6], int outExt[6]);


  vtkGetObjectMacro(IntensityTransferFunction,vtkIntensityTransferFunction);

protected:
  vtkImageMapToIntensities();
  ~vtkImageMapToIntensities() {};

  
  // Method that can be called by multiple threads that is given the input data and an input extent
  // and is responsible for producing the matching output data.
  void ThreadedRequestData (vtkInformation* request,
                            vtkInformationVector** inputVector,
                            vtkInformationVector* outputVector,
                            vtkImageData ***inData, vtkImageData **outData,
                            int ext[6], int id);

  // Implement methods required by vtkAlgorithm.
  virtual int FillInputPortInformation(int, vtkInformation*);  
  
  vtkIntensityTransferFunction* IntensityTransferFunction;
private:
  vtkImageMapToIntensities(const vtkImageMapToIntensities&);  // Not implemented.
  void operator=(const vtkImageMapToIntensities&);  // Not implemented.
};

#endif


