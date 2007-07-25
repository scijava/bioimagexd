
/*=========================================================================

  Program:   BioImageXD
  Module:    $RCSfile: vtkImageAutoThresholdColocalization.h,v $

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
// .NAME vtkImageAutoThresholdColocalization - Collects data from multiple inputs into one image.
// .SECTION Description
// vtkImageAutoThresholdColocalization takes the components from multiple inputs and AutoThresholdColocalizations
// them into one output. The output images are AutoThresholdColocalization along the "AutoThresholdColocalizationAxis".
// Except for the AutoThresholdColocalization axis, all inputs must have the same extent.  
// All inputs must have the same number of scalar components.  
// A future extension might be to pad or clip inputs to have the same extent.
// The output has the same origin and spacing as the first input.
// The origin and spacing of all other inputs are ignored.  All inputs
// must have the same scalar type.


#ifndef __vtkImageAutoThresholdColocalization_h
#define __vtkImageAutoThresholdColocalization_h


#include "vtkBXDProcessingWin32Header.h"
#include "vtkImageMultipleInputOutputFilter.h"
#include "vtkImageAlgorithm.h"
#include "vtkInformationVector.h"
#include "vtkInformation.h"
#include "vtkStreamingDemandDrivenPipeline.h"

class VTK_BXD_PROCESSING_EXPORT vtkImageAutoThresholdColocalization : public vtkImageMultipleInputOutputFilter
{
public:
  static vtkImageAutoThresholdColocalization *New();
  vtkTypeRevisionMacro(vtkImageAutoThresholdColocalization,vtkImageMultipleInputOutputFilter);
  void PrintSelf(ostream& os, vtkIndent indent);


  // Description:
  // Include zero-zero pixel pairs in colocalization
  vtkGetMacro(IncludeZeroPixels,bool);
  vtkSetMacro(IncludeZeroPixels,bool);

  // Description:
  // Set colocalized voxels to this value
  vtkGetMacro(ConstantVoxelValue,int);
  vtkSetMacro(ConstantVoxelValue,int);

  // Description:
  // Pearson's correlation for whole volume, voxels above threshold and 
  // voxels below threshold
  vtkGetMacro(PearsonWholeImage,double);
  vtkSetMacro(PearsonWholeImage,double);
  vtkGetMacro(PearsonImageAbove,double);
  vtkSetMacro(PearsonImageAbove,double);
  vtkGetMacro(PearsonImageBelow,double);
  vtkSetMacro(PearsonImageBelow,double);
  
  // Description:
  // Manders' original colocalization coefficients M1 and M2
  // voxels below threshold
  vtkGetMacro(M1,double);
  vtkSetMacro(M1,double);
  vtkGetMacro(M2,double);
  vtkSetMacro(M2,double);
  // Description:
  // Overlap coefficients k1 and k2

  vtkGetMacro(K1,double);
  vtkSetMacro(K1,double);
  vtkGetMacro(K2,double);
  vtkSetMacro(K2,double);
  // Description:
  // Manders' colocalization coefficients M1 and M2 for thresholded areas
  vtkGetMacro(ThresholdM1,double);
  vtkSetMacro(ThresholdM1,double);
  vtkGetMacro(ThresholdM2,double);
  vtkSetMacro(ThresholdM2,double);
      
  // Description:
  // Costes' colocalization coefficients C1 and C2 
  vtkGetMacro(C1,double);
  vtkSetMacro(C1,double);
  vtkGetMacro(C2,double);
  vtkSetMacro(C2,double);  
      
  // Description:
  // Imaris percentage volume
  vtkGetMacro(PercentageVolumeCh1,double);
  vtkSetMacro(PercentageVolumeCh1,double);
  vtkGetMacro(PercentageVolumeCh2,double);
  vtkSetMacro(PercentageVolumeCh2,double);

    // Description:
  // Imaris percentage total
  vtkGetMacro(PercentageTotalCh1,double);
  vtkSetMacro(PercentageTotalCh1,double);
  vtkGetMacro(PercentageTotalCh2,double);
  vtkSetMacro(PercentageTotalCh2,double);
      
    // Description:
  // Imaris percentage material
  vtkGetMacro(PercentageMaterialCh1,double);
  vtkSetMacro(PercentageMaterialCh1,double);
  vtkGetMacro(PercentageMaterialCh2,double);
  vtkSetMacro(PercentageMaterialCh2,double);  

  // Description:
  // Maximum Threshold of Channel 1 and 2
  vtkGetMacro(Ch1ThresholdMax,double);
  vtkSetMacro(Ch1ThresholdMax,double);
  vtkGetMacro(Ch2ThresholdMax,double);
  vtkSetMacro(Ch2ThresholdMax,double);  
      
  // Description:
  // Sum of voxels over threshold for channels 1 and 2
  vtkGetMacro(SumOverThresholdCh1,double);
  vtkSetMacro(SumOverThresholdCh1,double);
  vtkGetMacro(SumOverThresholdCh2,double);
  vtkSetMacro(SumOverThresholdCh2,double);
        
  // Description:
  // Sum of all voxels for channels 1 and 2
  vtkGetMacro(SumCh1,double);
  vtkSetMacro(SumCh1,double);
  vtkGetMacro(SumCh2,double);
  vtkSetMacro(SumCh2,double);
      
  // Description:
  // Slope of the regression
  vtkGetMacro(Slope,double);
  vtkSetMacro(Slope,double);  
  
  // Description:
  // Intercept of the regression
  vtkGetMacro(Intercept,double);
  vtkSetMacro(Intercept,double);  
  
  // Description:
  // Colocalization amount
  vtkGetMacro(ColocAmount,double);
  vtkSetMacro(ColocAmount,double);  
      
  // Description:
  // Colocalization percentage
  vtkGetMacro(ColocPercent,double);
  vtkSetMacro(ColocPercent,double);    
      
  // Description:
  // Differential staining calculated using intensity / voxel amount
  //
  // Differential staining
  // Is calculated as the percentage of one channel to another
  // Where the colocalized voxels are subtracted from the second channel
  //
  //             I_r + I_coloc
  // DiffStain = ------------------
  //             I_g - I_coloc
  // Where I_coloc is the sum of intensities of colocalized voxels in green
  // channel
  vtkGetMacro(DiffStainIntCh1,double);
  vtkSetMacro(DiffStainIntCh1,double);
  // Description:
  // Differential staining calculated using intensity / voxel amount
  vtkGetMacro(DiffStainVoxelsCh1,double);
  vtkSetMacro(DiffStainVoxelsCh1,double);
  // Description:
  // Differential staining calculated using intensity / voxel amount
  vtkGetMacro(DiffStainIntCh2,double);
  vtkSetMacro(DiffStainIntCh2,double);
  // Description:
  // Differential staining calculated using intensity / voxel amount
  vtkGetMacro(DiffStainVoxelsCh2,double);
  vtkSetMacro(DiffStainVoxelsCh2,double);     

  // Description:
  // Instead of calculating thresholds, use the given thresholds
  vtkGetMacro(LowerThresholdCh1,int);
  vtkSetMacro(LowerThresholdCh1,int);    
  vtkGetMacro(LowerThresholdCh2,int);
  vtkSetMacro(LowerThresholdCh2,int);     
  vtkGetMacro(UpperThresholdCh1,int);
  vtkSetMacro(UpperThresholdCh1,int);    
  vtkGetMacro(UpperThresholdCh2,int);
  vtkSetMacro(UpperThresholdCh2,int);    
  
  // Description:
  // The number of voxels in channel 1 and 2 that are between the lower and upper thresholds.
  vtkSetMacro(OverThresholdCh1,int);
  vtkGetMacro(OverThresholdCh1,int)
  vtkSetMacro(OverThresholdCh2,int);
  vtkGetMacro(OverThresholdCh2,int)

  // Description:
  // The number of non-zero voxels in channel 1 and 2
  vtkSetMacro(NonZeroCh1,int);
  vtkGetMacro(NonZeroCh1,int)
  vtkSetMacro(NonZeroCh2,int);
  vtkGetMacro(NonZeroCh2,int)

protected:
  vtkImageAutoThresholdColocalization();
  ~vtkImageAutoThresholdColocalization();
int RequestUpdateExtent (
  vtkInformation* vtkNotUsed(request),
  vtkInformationVector** inputVector,
  vtkInformationVector* outputVector);  

  void ComputeInputUpdateExtents( vtkDataObject*output );

  void ExecuteInformation(vtkImageData **inputs, vtkImageData **output);
  void ComputeInputUpdateExtent(int inExt[6], int outExt[6]);
  
  void ThreadedExecute(vtkImageData **inDatas, vtkImageData **outData,
                       int extent[6], int id);
  

int SplitExtent(int splitExt[6],int startExt[6],int num, int total) {
     memcpy(splitExt, startExt, 6 * sizeof(int));
     return 1;                                             
                                                
   }
  void InitOutput(int outExt[6], vtkImageData *outData);
private:
  vtkImageAutoThresholdColocalization(const vtkImageAutoThresholdColocalization&);  // Not implemented.
  void operator=(const vtkImageAutoThresholdColocalization&);  // Not implemented.

  int ConstantVoxelValue;
  bool IncludeZeroPixels;

  double PearsonWholeImage;
  double PearsonImageAbove;
  double PearsonImageBelow;
      
  double M1;
  double M2;
  double ThresholdM1;
  double ThresholdM2;
  double C1;
  double C2;
  double K1;
  double K2;
  
  double PercentageVolumeCh1;
  double PercentageVolumeCh2;
  double PercentageTotalCh1;
  double PercentageTotalCh2;
  double Ch1ThresholdMax;
  double Ch2ThresholdMax;
      
  double PercentageMaterialCh1;
  double PercentageMaterialCh2;
      
  double ColocAmount;
  double ColocPercent;
  double SumOverThresholdCh1;
  double SumOverThresholdCh2;
  double SumCh1;
  double SumCh2;
      
  double DiffStainIntCh1;
  double DiffStainVoxelsCh1; 
  double DiffStainIntCh2;
  double DiffStainVoxelsCh2;       

  double Slope;
  double Intercept;
      
  int LowerThresholdCh1;
  int LowerThresholdCh2;
  int UpperThresholdCh1;
  int UpperThresholdCh2;  
  
  int OverThresholdCh1;
  int OverThresholdCh2;
  int NonZeroCh1;
  int NonZeroCh2;
};

#endif
