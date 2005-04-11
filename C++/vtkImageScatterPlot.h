/*=========================================================================

  Program:   Visualization Toolkit
  Module:    $RCSfile: vtkImageScatterPlot.h,v $

  Copyright (c) Ken Martin, Will Schroeder, Bill Lorensen
  All rights reserved.
  See Copyright.txt or http://www.kitware.com/Copyright.htm for details.

     This software is distributed WITHOUT ANY WARRANTY; without even
     the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
     PURPOSE.  See the above copyright notice for more information.

=========================================================================*/
// .NAME vtkImageScatterPlot - Collects data from multiple inputs into one image.
// .SECTION Description
// vtkImageScatterPlot takes the components from multiple inputs and ScatterPlots
// them into one output. The output images are ScatterPlot along the "ScatterPlotAxis".
// Except for the ScatterPlot axis, all inputs must have the same extent.  
// All inputs must have the same number of scalar components.  
// A future extension might be to pad or clip inputs to have the same extent.
// The output has the same origin and spacing as the first input.
// The origin and spacing of all other inputs are ignored.  All inputs
// must have the same scalar type.


#ifndef __vtkImageScatterPlot_h
#define __vtkImageScatterPlot_h


#include "vtkImageMultipleInputFilter.h"

class VTK_IMAGING_EXPORT vtkImageScatterPlot : public vtkImageMultipleInputFilter
{
public:
  static vtkImageScatterPlot *New();
  vtkTypeRevisionMacro(vtkImageScatterPlot,vtkImageMultipleInputFilter);
  void PrintSelf(ostream& os, vtkIndent indent);
     
  vtkSetMacro(ZSlice,int);
  vtkGetMacro(ZSlice,int);

  vtkSetMacro(CountVoxels,int);
  vtkGetMacro(CountVoxels,int);
  vtkBooleanMacro(CountVoxels,int);

  vtkSetMacro(NumberOfPairs,long);
  vtkGetMacro(NumberOfPairs,long);
     
protected:
  vtkImageScatterPlot();
  ~vtkImageScatterPlot();

  void ExecuteInformation(vtkImageData **inputs, vtkImageData *output);
  void ComputeInputUpdateExtents( vtkDataObject*output );
	  
  void ThreadedExecute(vtkImageData **inData, 
                                     vtkImageData *outData,
                                     int outExt[6], int id);

  void InitOutput(int outExt[6], vtkImageData *outData);
private:
  vtkImageScatterPlot(const vtkImageScatterPlot&);  // Not implemented.
  void operator=(const vtkImageScatterPlot&);  // Not implemented.

  int ZSlice;
  int CountVoxels;
  long NumberOfPairs;
};

#endif




