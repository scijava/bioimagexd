/*=========================================================================

  Program:   BioImageXD
  Module:    $RCSfile: vtkImageLabelAverage.h,v $

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
// .NAME vtkImageLabelAverage - select piece (e.g., volume of interest) and/or subsample structured points dataset

// .SECTION Description
// vtkImageLabelAverage is a filter that sets to zero pixels/voxels that have scalar
// values over a specified threshold but do not have horizontal/vertical neighborhood pixels
//  with scalar values over the respective thresholds


// .SECTION See Also
// vtkGeometryFilter vtkExtractGeometry vtkExtractGrid

#ifndef __vtkImageLabelAverage_h
#define __vtkImageLabelAverage_h

#include "vtkBXDProcessingWin32Header.h"

#include "vtkImageData.h"
#include "vtkInformationVector.h"
#include "vtkObjectFactory.h"
#include "vtkThreadedImageAlgorithm.h"
#include "vtkDoubleArray.h"
#include "vtkUnsignedLongArray.h"

class VTK_BXD_PROCESSING_EXPORT vtkImageLabelAverage : public vtkThreadedImageAlgorithm
{
public:
  vtkTypeRevisionMacro(vtkImageLabelAverage,vtkThreadedImageAlgorithm);
  void PrintSelf(ostream& os, vtkIndent indent);

  // Description:
  // Construct object to extract all of the input data.
  static vtkImageLabelAverage *New();     

  //virtual void ComputeInputUpdateExtent(int inExt[6], int outExt[6]);

  int GetNumberOfLabels() { return NumberOfItems; }
  double GetAverage(int label) { return AverageArray->GetValue(label); }
  void SetAverage(int label, int value) { AverageArray->SetValue(label, value); }
  vtkDoubleArray* GetAverageArray() { return AverageArray; }
protected:
  vtkImageLabelAverage();
  ~vtkImageLabelAverage() {};

  
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
  vtkDoubleArray* AverageArray;
  int NumberOfItems;
  vtkImageLabelAverage(const vtkImageLabelAverage&);  // Not implemented.
  void operator=(const vtkImageLabelAverage&);  // Not implemented.
};

#endif


