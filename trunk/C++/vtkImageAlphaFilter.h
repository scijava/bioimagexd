/*=========================================================================

  Program:   BioImageXD
  Module:    $RCSfile: vtkImageAlphaFilter.h,v $

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
// .NAME vtkImageAlphaFilter - Collects data from multiple inputs into one image.
// .SECTION Description
// vtkImageAlphaFilter takes the components from multiple inputs and AlphaFilters
// them into one output. The output images are AlphaFilter along the "AlphaFilterAxis".
// Except for the AlphaFilter axis, all inputs must have the same extent.  
// All inputs must have the same number of scalar components.  
// A future extension might be to pad or clip inputs to have the same extent.
// The output has the same origin and spacing as the first input.
// The origin and spacing of all other inputs are ignored.  All inputs
// must have the same scalar type.


#ifndef __vtkImageAlphaFilter_h
#define __vtkImageAlphaFilter_h


#include "vtkImageMultipleInputFilter.h"

class VTK_IMAGING_EXPORT vtkImageAlphaFilter : public vtkImageMultipleInputFilter
{
public:
  static vtkImageAlphaFilter *New();
  vtkTypeRevisionMacro(vtkImageAlphaFilter,vtkImageMultipleInputFilter);
  void PrintSelf(ostream& os, vtkIndent indent);

  // Description:
  // In the maximum mode, the alpha channel value will be the 
  // largest scalar value in a particular voxel
  vtkBooleanMacro(MaximumMode,int);
  vtkSetMacro(MaximumMode,int);
  vtkGetMacro(MaximumMode,int);
  // Description:
  // In the average mode, the alpha channel value will be the
  // average of all scalar values that are larger than AverageThreshold
  vtkBooleanMacro(AverageMode,int);
  vtkSetMacro(AverageMode,int);
  vtkGetMacro(AverageMode,int);

  vtkSetMacro(AverageThreshold,int);
  vtkGetMacro(AverageThreshold,int);

protected:
  vtkImageAlphaFilter();
  ~vtkImageAlphaFilter();


  void ExecuteInformation(vtkImageData **inputs, vtkImageData *output);
  void ComputeInputUpdateExtent(int inExt[6], int outExt[6]);
  
  void ThreadedExecute(vtkImageData **inDatas, vtkImageData *outData,
                       int extent[6], int id);
  

  void InitOutput(int outExt[6], vtkImageData *outData);
private:
  vtkImageAlphaFilter(const vtkImageAlphaFilter&);  // Not implemented.
  void operator=(const vtkImageAlphaFilter&);  // Not implemented.

  int AverageMode;
  int AverageThreshold;
  int MaximumMode;
};

#endif




