/*=========================================================================

  Program:   BioImageXD
  Module:    $RCSfile: vtkImageLabelAverage.h,v $

 This module is not used anymore in BioImageXD

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
  vtkDoubleArray* GetAverageArray() { return AverageArray; }
  
  int SplitExtent(int splitExt[6], 
				  int startExt[6],
				  int num, int total);
  // Description:
  // Get the total average of non-zero voxels inside and outside
  // the labels.
  vtkGetMacro(AverageInsideLabels,double);
  vtkGetMacro(AverageOutsideLabels,double);

  // Description:
  // Get the total voxels inside and outside the labels.
  vtkGetMacro(VoxelsInsideLabels, unsigned int);
  vtkGetMacro(VoxelsOutsideLabels, unsigned int);

  // Description:
  // Get the standard deviation of average inside / outside labels
  vtkGetMacro(InsideLabelsStdDev, double);
  vtkGetMacro(OutsideLabelsStdDev, double);

  // Description:
  // Set / Get the background level (number of objects in the label image to
  // ignore in calculating the inside and outside totals)
  vtkGetMacro(BackgroundLevel,int);
  vtkSetMacro(BackgroundLevel,int);   
  
  // Description:
  // Get the number of non-zero voxels
  vtkGetMacro(NonZeroVoxels, unsigned int);

  void SetAverage(int label, int value) { AverageArray->SetValue(label,value); }
  vtkSetMacro(VoxelsInsideLabels, unsigned int);
  vtkSetMacro(VoxelsOutsideLabels, unsigned int);
  vtkSetMacro(InsideLabelsStdDev, double);
  vtkSetMacro(OutsideLabelsStdDev, double);
  vtkSetMacro(AverageInsideLabels,double);
  vtkSetMacro(AverageOutsideLabels,double);
  vtkSetMacro(NonZeroVoxels, unsigned int);

protected:
  vtkImageLabelAverage();
  ~vtkImageLabelAverage() {};


  // Method that can be called by multiple threads that is given the input data
  // and an input extent and is responsible for producing the matching output
  // data.
  void ThreadedRequestData (vtkInformation* request,
                            vtkInformationVector** inputVector,
                            vtkInformationVector* outputVector,
                            vtkImageData ***inData, vtkImageData **outData,
                            int ext[6], int id);

  // Implement methods required by vtkAlgorithm.
  virtual int FillInputPortInformation(int, vtkInformation*);  
  
  
private:
  vtkDoubleArray* AverageArray;
  double AverageInsideLabels;
  double AverageOutsideLabels;
  double InsideLabelsStdDev;
  double OutsideLabelsStdDev;
  int BackgroundLevel;
  int NumberOfItems;
  unsigned int NonZeroVoxels;
  unsigned int VoxelsInsideLabels;
  unsigned int VoxelsOutsideLabels;
  vtkImageLabelAverage(const vtkImageLabelAverage&);  // Not implemented.
  void operator=(const vtkImageLabelAverage&);  // Not implemented.
};

#endif


