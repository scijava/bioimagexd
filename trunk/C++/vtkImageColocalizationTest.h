/*=========================================================================

  Program:   BioImageXD
  Module:    $RCSfile: vtkImageColocalizationTest.h,v $

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
// .NAME vtkImageColocalizationTest - Collects data from multiple inputs into one image.
// .SECTION Description
// vtkImageColocalizationTest takes the components from multiple inputs and ColocalizationTests
// them into one output. The output images are ColocalizationTest along the "ColocalizationTestAxis".
// Except for the ColocalizationTest axis, all inputs must have the same extent.  
// All inputs must have the same number of scalar components.  
// A future extension might be to pad or clip inputs to have the same extent.
// The output has the same origin and spacing as the first input.
// The origin and spacing of all other inputs are ignored.  All inputs
// must have the same scalar type.


#ifndef __vtkImageColocalizationTest_h
#define __vtkImageColocalizationTest_h


#include "vtkImageMultipleInputFilter.h"


float* makeKernel(double radius);
        
class VTK_IMAGING_EXPORT vtkImageColocalizationTest : public vtkImageMultipleInputFilter
{
public:
  static vtkImageColocalizationTest *New();
  vtkTypeRevisionMacro(vtkImageColocalizationTest,vtkImageMultipleInputFilter);
  void PrintSelf(ostream& os, vtkIndent indent);


  // Ignore zero-zero pixel pairs in colocalization
  vtkGetMacro(IgnoreZeroPixels,int);
  vtkSetMacro(IgnoreZeroPixels,int);
  // Description:
  // Randomize in Z direction also
  vtkGetMacro(RandomizeZ,int);
  vtkSetMacro(RandomizeZ,int);

  // Description:
  // Set the size of the PSF (in pixels) manually
  vtkGetMacro(ManualPSFSize,double);
  vtkSetMacro(ManualPSFSize,double);

  // Description:
  // Set the number of iterations
  vtkGetMacro(NumIterations,int);
  vtkSetMacro(NumIterations,int);
  
  
  // Description:
  // Set the randomization method
  // 0 = Fay
  // 1 = Costes X, Y
  // 2 = van Steensel
  vtkGetMacro(Method,int);
  vtkSetMacro(Method,int);
  
  // Description:
  // Do the thang only on given slice
  vtkGetMacro(CurrentSlice,int);
  vtkSetMacro(CurrentSlice,int);
  
  // Description:
  // Set the numerical aperture
  vtkGetMacro(NumericalAperture,double);
  vtkSetMacro(NumericalAperture,double);
  
  // Description:
  // Set the pixel size
  vtkGetMacro(PixelSize,double);
  vtkSetMacro(PixelSize,double);  
  // Description:
  // Set the lambda for channel 2
  vtkGetMacro(Ch2Lambda,int);
  vtkSetMacro(Ch2Lambda,int);  
  
  // Description:
  // Set the P value
  vtkGetMacro(PValue,double);
  vtkSetMacro(PValue,double);    

  // Description:
  // Set the R(obs)
  vtkGetMacro(RObserved,double);
  vtkSetMacro(RObserved,double);    
  // Description:
  // Set the R(rand) mean
  vtkGetMacro(RRandMean,double);
  vtkSetMacro(RRandMean,double);    
  // Description:
  // Set the R(rand) sd
  vtkGetMacro(RRandSD,double);
  vtkSetMacro(RRandSD,double);    
  // Description:
  // Set the coloc count
  vtkGetMacro(ColocCount,int);
  vtkSetMacro(ColocCount,int);    
  // Description:
  // Set the PSF
  vtkGetMacro(PSF,double);
  vtkSetMacro(PSF,double);    
    

protected:
  vtkImageColocalizationTest();
  ~vtkImageColocalizationTest();

  //void ComputeInputUpdateExtents( vtkDataObject*output );

  void ExecuteInformation(vtkImageData **inputs, vtkImageData *output);
  void ComputeInputUpdateExtent(int inExt[6], int outExt[6]);
  
  void ThreadedExecute(vtkImageData **inDatas, vtkImageData *outData,
                       int extent[6], int id);
  

  void InitOutput(int outExt[6], vtkImageData *outData);
private:
  vtkImageColocalizationTest(const vtkImageColocalizationTest&);  // Not implemented.
  void operator=(const vtkImageColocalizationTest&);  // Not implemented.

  int IgnoreZeroPixels;
  int RandomizeZ;
  int Smooth;
  double ManualPSFSize;
  int NumIterations;
  int Ch2Lambda;
  double NumericalAperture;
  double PixelSize;
    
  int Method;
  int CurrentSlice;
  
  double PValue;
  double RObserved;
  double RRandMean;
  double RRandSD;
  double PSF;
  int ColocCount;
  
};

#endif
