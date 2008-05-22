/*=========================================================================

  Program:   BioImageXD
  Module:    $RCSfile: vtkImageIterativeDeconvolution3D.h,v $

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
// .NAME vtkImageIterativeDeconvolution3D - Collects data from multiple inputs into one image.
// .SECTION Description


#ifndef __vtkImageIterativeDeconvolution3D_h
#define __vtkImageIterativeDeconvolution3D_h

#include "vtkBXDProcessingWin32Header.h"
#include "vtkThreadedImageAlgorithm.h"
#include "vtkInformation.h"
#include "vtkInformationVector.h"
#include "vtkStreamingDemandDrivenPipeline.h"

class VTK_BXD_PROCESSING_EXPORT vtkImageIterativeDeconvolution3D : public vtkThreadedImageAlgorithm
{
public:
  static vtkImageIterativeDeconvolution3D *New();
  vtkTypeRevisionMacro(vtkImageIterativeDeconvolution3D,vtkThreadedImageAlgorithm);
  void PrintSelf(ostream& os, vtkIndent indent);  

  // Description:
  // Set / Get the number of iterations the code will run
  vtkSetMacro(NumberOfIterations,int);
  vtkGetMacro(NumberOfIterations,int);
  // Description:
  // Set / Get the wiener filter gamma
  // (suggested 0 [< .0001] to turn off, 0.0001-0.1 as tests)
  vtkSetMacro(Gamma,float);
  vtkGetMacro(Gamma,float);
  // Description:
  // Set / Get the Low pass filter X, Y and Z, pixels
  // (suggested 1, 0 to turn off)
  vtkSetMacro(FilterX,float);
  vtkGetMacro(FilterX,float);
  vtkSetMacro(FilterY,float);
  vtkGetMacro(FilterY,float);
  vtkSetMacro(FilterZ,float);
  vtkGetMacro(FilterZ,float);
  
  // Description:
  // Toggle whether the PSF should be normalized
  vtkSetMacro(Normalize,bool);
  vtkGetMacro(Normalize,bool);
  // Description:
  // Log mean pixel value to track convergence
  vtkSetMacro(LogMean,bool);
  vtkGetMacro(LogMean,bool);
  // Description:
  // Perform anti ringing step
  vtkSetMacro(AntiRing,bool);
  vtkGetMacro(AntiRing,bool);
  // Description:
  // Detect divergence
  vtkSetMacro(DetectDivergence,bool);
  vtkGetMacro(DetectDivergence,bool);
  // Description:
  // Threshold percentage (x%) used to terminate iteration:
  // Terminate iteration if mean delta < x%
  // (suggest 0.01, 0 to turn off)
  vtkSetMacro(ChangeThresholdPercent,double);
  vtkGetMacro(ChangeThresholdPercent,double);

 protected:
  vtkImageIterativeDeconvolution3D();
  ~vtkImageIterativeDeconvolution3D();

int RequestInformation(vtkInformation * vtkNotUsed(request), vtkInformationVector **inputVector, vtkInformationVector *outputVector);
int RequestUpdateExtent (vtkInformation* vtkNotUsed(request), vtkInformationVector** inputVector, vtkInformationVector* outputVector);
int SplitExtent(int splitExt[6],int startExt[6], int num, int total);
void ThreadedRequestData (vtkInformation * vtkNotUsed( request ), vtkInformationVector** vtkNotUsed( inputVector ), vtkInformationVector * vtkNotUsed( outputVector ),
  vtkImageData ***inData, vtkImageData **outData, int outExt[6], int id);

int FillInputPortInformation(int port, vtkInformation* info);

  void InitOutput(int outExt[6], vtkImageData *outData);
private:
  vtkImageIterativeDeconvolution3D(const vtkImageIterativeDeconvolution3D&);  // Not implemented.
  void operator=(const vtkImageIterativeDeconvolution3D&);  // Not implemented.


    int NumberOfIterations;
    float Gamma;
    double FilterX;
    double FilterY;
    double FilterZ;
    bool Normalize;
    bool LogMean;
    bool AntiRing;
    double ChangeThresholdPercent;
    bool DetectDivergence;
};

#endif




