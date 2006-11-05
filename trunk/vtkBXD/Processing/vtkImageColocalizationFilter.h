/*=========================================================================

  Program:   BioImageXD
  Module:    $RCSfile: vtkImageColocalizationFilter.h,v $

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
// .NAME vtkImageColocalizationFilter - Calculates a colocalization map from multiple input images
// .SECTION Description
// vtkImageColocalizationFilter takes as input multiple vtkImageData datasets and calculates the
// colocalized voxels in those datasets based on a lower and upper threshold that is defined for
// each of the input datasets.
//
// A voxel is considered colocalized if in every input dataset the intensity of the voxel I_v
// is between the lower and upper thresholds (T_l and T_u respectively).
//
// So, a voxel is colocalized if for each input datasets, the following holds:
//
// T_l <= I_v <= T_u

#ifndef __vtkImageColocalizationFilter_h
#define __vtkImageColocalizationFilter_h

#include "vtkBXDProcessingWin32Header.h"
#include "vtkThreadedImageAlgorithm.h"

// VTK_IMAGING_EXPORT declares that this class is part of the Imaging kit. If the code was placed
// in the Filtering- directory, it would say VTK_FILTERING_EXPORT
class VTK_BXD_PROCESSING_EXPORT vtkImageColocalizationFilter : public vtkThreadedImageAlgorithm
{
public:
  // These are required for the object factory scheme VTK uses to construct the objects.
  static vtkImageColocalizationFilter *New();
  vtkTypeRevisionMacro(vtkImageColocalizationFilter,vtkThreadedImageAlgorithm);
  // Method used to print out the details of the object
  void PrintSelf(ostream& os, vtkIndent indent);

  // Description:
  // Set the bit depth of the generated colocalization map. Can be one of 
  // 24 - produce unsigned char dataset with 4 components (RGBA)
  // 8 - produce 8-bit (unsigned char) dataset
  // 1 - produce a 8-bit dataset that is conceptually 1-bit, that is, set to the specified scalar value
  vtkSetMacro(OutputDepth,int);
  vtkGetMacro(OutputDepth,int);
  void SetOutputDepthTo24Bit() { this->OutputDepth = 24; this->Modified(); }
  void SetOutputDepthTo8Bit() { this->OutputDepth = 8; this->Modified(); }
  void SetOutputDepthTo1Bit() { this->OutputDepth = 1; this->Modified(); }

  // Description:
  // Voxels in the specified dataset that have a scalar value above
  // this threshold and below the upper threshold are considered to be colocalizing
  void SetColocalizationLowerThreshold(int dataset, int threshold);
  int GetColocalizationLowerThreshold(int dataset) {
      if (dataset < this->NumberOfDatasets) return ColocalizationLowerThresholds[dataset];
      return 0;
  }
  // Description:
  // Voxels in the specified dataset that have a scalar value below
  // this threshold and above the lower threshold are considered to be colocalizing
  void SetColocalizationUpperThreshold(int dataset, int threshold);
  int GetColocalizationUpperThreshold(int dataset) {
      if (dataset < this->NumberOfDatasets) return ColocalizationUpperThresholds[dataset];
      return 0;
  }
  int* GetColocalizationLowerThresholds() { return this->ColocalizationLowerThresholds; }
  int* GetColocalizationUpperThresholds() { return this->ColocalizationUpperThresholds; }

  // Description:
  // Set / Get the constant scalar used for colocalized voxels.
  // Defaults to 2**sizeof(datatype)
  vtkGetMacro(OutputScalarValue,double);
  vtkSetMacro(OutputScalarValue,double);

protected:
  vtkImageColocalizationFilter();
  ~vtkImageColocalizationFilter();

  // Method that is used to retrieve information about the resulting output dataset
  virtual int RequestInformation (vtkInformation *, vtkInformationVector **,
                                  vtkInformationVector *);

  // Method that can be called by multiple threads that is given the input data and an input extent
  // and is responsible for producing the matching output data.
  void ThreadedRequestData (vtkInformation* request,
                            vtkInformationVector** inputVector,
                            vtkInformationVector* outputVector,
                            vtkImageData ***inData, vtkImageData **outData,
                            int ext[6], int id);

  // Implement methods required by vtkAlgorithm.
  virtual int FillInputPortInformation(int, vtkInformation*);

  void InitOutput(int outExt[6], vtkImageData *outData);
private:
  vtkImageColocalizationFilter(const vtkImageColocalizationFilter&);  // Not implemented.
  void operator=(const vtkImageColocalizationFilter&);  // Not implemented.

  int OutputDepth;
  int *ColocalizationLowerThresholds;
  int *ColocalizationUpperThresholds;
  int NumberOfDatasets;
  double OutputScalarValue;

};

#endif




