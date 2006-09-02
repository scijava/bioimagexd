/*=========================================================================

  Program:   BioImageXD
  Module:    $RCSfile: vtkImageColorMerge.h,v $

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
// .NAME vtkImageColorMerge - Collects data from multiple inputs into one image.
// .SECTION Description
// vtkImageColorMerge takes the components from multiple inputs and merges
// them into one output. The output images are Merge along the "MergeAxis".
// Except for the Merge axis, all inputs must have the same extent.  
// All inputs must have the same number of scalar components.  
// A future extension might be to pad or clip inputs to have the same extent.
// The output has the same origin and spacing as the first input.
// The origin and spacing of all other inputs are ignored.  All inputs
// must have the same scalar type.


#ifndef __vtkImageColorMerge_h
#define __vtkImageColorMerge_h

#include "vtkIntensityTransferFunction.h"
#include "vtkColorTransferFunction.h"

#include "vtkThreadedImageAlgorithm.h"

class VTK_IMAGING_EXPORT vtkImageColorMerge : public vtkThreadedImageAlgorithm
{
public:
  static vtkImageColorMerge *New();
  vtkTypeRevisionMacro(vtkImageColorMerge, vtkThreadedImageAlgorithm);

  void PrintSelf(ostream& os, vtkIndent indent);  
  vtkColorTransferFunction* GetColorTransferFunction(int i) { return ColorTransferFunctions[i]; }
  vtkIntensityTransferFunction* GetIntensityTransferFunction(int i) { return IntensityTransferFunctions[i]; }

  void AddLookupTable(vtkColorTransferFunction* ctf) { 
      ColorTransferFunctions[CTFCount++] = ctf; this->Modified(); 
  }
  
  void AddIntensityTransferFunction(vtkIntensityTransferFunction* itf) { 
        IntensityTransferFunctions[ITFCount++] = itf;
        this->Modified();
  }
  vtkGetMacro(ITFCount,int);
  vtkGetMacro(CTFCount,int);
  
  vtkBooleanMacro(BuildAlpha,int);
  vtkSetMacro(BuildAlpha,int);
  vtkGetMacro(BuildAlpha,int);
  
  // Description:
  // In the maximum mode, the alpha channel value will be the 
  // largest scalar value in a particular voxel
  vtkBooleanMacro(MaximumMode,int);
  vtkSetMacro(MaximumMode,int);
  vtkGetMacro(MaximumMode,int);
  // Description:
  // In the luminance mode, the alpha channel value will be the 
  // weighted sum of the intensities of R, G and B
  vtkBooleanMacro(LuminanceMode,int);
  vtkSetMacro(LuminanceMode,int);
  vtkGetMacro(LuminanceMode,int);  
  // Description:
  // In the average mode, the alpha channel value will be the
  // average of all scalar values that are larger than AverageThreshold
  vtkBooleanMacro(AverageMode,int);
  vtkSetMacro(AverageMode,int);
  vtkGetMacro(AverageMode,int);

  
  vtkSetMacro(AverageThreshold,int);
  vtkGetMacro(AverageThreshold,int);  
  
 protected:
  vtkImageColorMerge();
  ~vtkImageColorMerge();

/* 
  void ExecuteInformation(vtkImageData **inputs, vtkImageData *output);
  void ComputeInputUpdateExtent(int inExt[6], int outExt[6]);
  void ExecuteInformation(){this->vtkImageMultipleInputFilter::ExecuteInformation();};
 
  void ThreadedExecute(vtkImageData **inDatas, vtkImageData *outData,
                       int extent[6], int id);
*/ 

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
  
  void ClearItfs();
 
private:
  vtkImageColorMerge(const vtkImageColorMerge&);  // Not implemented.
  void operator=(const vtkImageColorMerge&);  // Not implemented.

  vtkIntensityTransferFunction* IntensityTransferFunctions[10];
  vtkColorTransferFunction* ColorTransferFunctions[10];
  int ITFCount;
  int CTFCount;
  int BuildAlpha;

  int AverageMode;
  int AverageThreshold;
  int MaximumMode;
  int LuminanceMode;

};

#endif




