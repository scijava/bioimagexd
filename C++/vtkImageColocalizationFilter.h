/*=========================================================================

  Program:   Visualization Toolkit
  Module:    $RCSfile: vtkImageColocalizationFilter.h,v $

  Copyright (c) Ken Martin, Will Schroeder, Bill Lorensen
  All rights reserved.
  See Copyright.txt or http://www.kitware.com/Copyright.htm for details.

     This software is distributed WITHOUT ANY WARRANTY; without even
     the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
     PURPOSE.  See the above copyright notice for more information.

=========================================================================*/
// .NAME vtkImageColocalizationFilter - Collects data from multiple inputs into one image.
// .SECTION Description
// vtkImageColocalizationFilter takes the components from multiple inputs and ColocalizationFilters
// them into one output. The output images are ColocalizationFilter along the "ColocalizationFilterAxis".
// Except for the ColocalizationFilter axis, all inputs must have the same extent.  
// All inputs must have the same number of scalar components.  
// A future extension might be to pad or clip inputs to have the same extent.
// The output has the same origin and spacing as the first input.
// The origin and spacing of all other inputs are ignored.  All inputs
// must have the same scalar type.


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
  // Voxels in the specified dataset that have a scalar value over 
  // this threshold are considered to be colocalizing
  void SetColocalizationThreshold(int dataset, int threshold);
  int GetColocalizationThreshold(int dataset) { 
      if (dataset < this->NumberOfDatasets) return ColocalizationThresholds[dataset];
      return 0;
  }
  int* GetColocalizationThresholds() { return this->ColocalizationThresholds; }
  
  // Description:
  // Get the amount of colocalization in the image
  vtkGetMacro(ColocalizationAmount,int);
  vtkSetMacro(ColocalizationAmount,int);
  // Description:
  // Get the number of voxels over the threshold from the
  // dataset that has the least number of voxels over the threshold.
  vtkGetMacro(LeastVoxelsOverThreshold,int);
  vtkSetMacro(LeastVoxelsOverThreshold,int);

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
  int *ColocalizationThresholds;
  int ColocalizationAmount;
  int LeastVoxelsOverThreshold;
  int NumberOfDatasets;

};

#endif




