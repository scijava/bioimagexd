/*=========================================================================

  Program:   Visualization Toolkit
  Module:    $RCSfile: vtkImageMerge.h,v $

  Copyright (c) Ken Martin, Will Schroeder, Bill Lorensen
  All rights reserved.
  See Copyright.txt or http://www.kitware.com/Copyright.htm for details.

     This software is distributed WITHOUT ANY WARRANTY; without even
     the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
     PURPOSE.  See the above copyright notice for more information.

=========================================================================*/
// .NAME vtkImageMerge - Collects data from multiple inputs into one image.
// .SECTION Description
// vtkImageMerge takes the components from multiple inputs and merges
// them into one output. The output images are Merge along the "MergeAxis".
// Except for the Merge axis, all inputs must have the same extent.  
// All inputs must have the same number of scalar components.  
// A future extension might be to pad or clip inputs to have the same extent.
// The output has the same origin and spacing as the first input.
// The origin and spacing of all other inputs are ignored.  All inputs
// must have the same scalar type.


#ifndef __vtkImageMerge_h
#define __vtkImageMerge_h


#include "vtkImageMultipleInputFilter.h"

class VTK_IMAGING_EXPORT vtkImageMerge : public vtkImageMultipleInputFilter
{
public:
  static vtkImageMerge *New();
  vtkTypeRevisionMacro(vtkImageMerge,vtkImageMultipleInputFilter);
  void PrintSelf(ostream& os, vtkIndent indent);  

 protected:
  vtkImageMerge();
  ~vtkImageMerge();


  void ExecuteInformation(vtkImageData **inputs, vtkImageData *output);
  void ComputeInputUpdateExtent(int inExt[6], int outExt[6]);
  void ExecuteInformation(){this->vtkImageMultipleInputFilter::ExecuteInformation();};
  
  void ThreadedExecute(vtkImageData **inDatas, vtkImageData *outData,
                       int extent[6], int id);

  void InitOutput(int outExt[6], vtkImageData *outData);
private:
  vtkImageMerge(const vtkImageMerge&);  // Not implemented.
  void operator=(const vtkImageMerge&);  // Not implemented.

};

#endif




