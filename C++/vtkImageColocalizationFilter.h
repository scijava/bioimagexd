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
// .NAME vtkImageColocalizationFilter - Collects data from multiple inputs into one image.
// .SECTION Description
// vtkImageColocalizationFilter takes the components from multiple inputs and ColocalizationFilters

#ifndef __vtkImageColocalizationFilter_h
#define __vtkImageColocalizationFilter_h


#include "vtkImageMultipleInputFilter.h"

class VTK_IMAGING_EXPORT vtkImageColocalizationFilter : public vtkImageMultipleInputFilter
{
public:
  static vtkImageColocalizationFilter *New();
  vtkTypeRevisionMacro(vtkImageColocalizationFilter,vtkImageMultipleInputFilter);
  void PrintSelf(ostream& os, vtkIndent indent);

  // Description:
  // Set the bit depth of the generated colocalization map
  vtkSetMacro(OutputDepth,int);
  vtkGetMacro(OutputDepth,int);
  void SetOutputDepthTo24Bit() { this->SetOutputDepth(24); }
  void SetOutputDepthTo8Bit() { this->SetOutputDepth(8); }
  void SetOutputDepthTo1Bit() { this->SetOutputDepth(1); }
  
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
  vtkGetMacro(OutputScalar,double);
  vtkSetMacro(OutputScalar,double);   

protected:
  vtkImageColocalizationFilter();
  ~vtkImageColocalizationFilter();


  void ExecuteInformation(vtkImageData **inputs, vtkImageData *output);
  void ComputeInputUpdateExtent(int inExt[6], int outExt[6]);
  
  void ThreadedExecute(vtkImageData **inDatas, vtkImageData *outData,
                       int extent[6], int id);
  

  void InitOutput(int outExt[6], vtkImageData *outData);
private:
  vtkImageColocalizationFilter(const vtkImageColocalizationFilter&);  // Not implemented.
  void operator=(const vtkImageColocalizationFilter&);  // Not implemented.

  int OutputDepth;
  int *ColocalizationLowerThresholds;
  int *ColocalizationUpperThresholds;
  int NumberOfDatasets;
  double OutputScalar;

};

#endif




