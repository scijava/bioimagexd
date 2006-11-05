/*=========================================================================

  Program:   BioImageXD
  Module:    $RCSfile: vtkPiecewiseFunction.h,v $

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

// .NAME vtkIntensityTransferFunction - Defines a 1D piecewise function for processing a volume's intensity
// 
// 
// .SECTION Description
// Defines a piecewise linear function mapping. Used for transfer functions
// in volume rendering.

#ifndef __vtkIntensityTransferFunction_h
#define __vtkIntensityTransferFunction_h

#include "vtkDataObject.h"
#include "vtkPiecewiseFunction.h"
#include "vtkBXDProcessingWin32Header.h"

class VTK_BXD_PROCESSING_EXPORT vtkIntensityTransferFunction : public vtkPiecewiseFunction
{
public:
  static vtkIntensityTransferFunction *New();
  vtkTypeRevisionMacro(vtkIntensityTransferFunction,vtkPiecewiseFunction);
  void PrintSelf(ostream& os, vtkIndent indent);

  void Initialize();
  void DeepCopy( vtkDataObject *f );
  void ShallowCopy( vtkDataObject *f );

  // Description:
  // Return what type of dataset this is.
  int GetDataObjectType() {return VTK_PIECEWISE_FUNCTION;};
  
  // Description:
  // Get the number of points used to specify the function
  int  GetSize();

  // Description:
  // Removes all points from the function. 
  void RemoveAllPoints();


  // Description:
  // Returns the value of the function at the specified location using
  // the specified interpolation. Returns zero if the specified location
  // is outside the min and max points of the function.
  int GetValue( int x );

  // Description:
  // Calculates the function table based on the Minimum / Maximum Value and Threshold
  // and the Brightness, Constrast and Gamma and the Processing Threshold
  void ComputeFunction(void);
  
  // Description:
  // Returns true if this is an identical function, i.e.
  // y = x
  int IsIdentical(void);
  
  // Description:
  // Returns a pointer to the data stored in the table.
  // Fills from a pointer to data stored in a similar table.
  int *GetDataPointer() { 
    if(this->GetMTime() > this->BuildTime.GetMTime()) this->ComputeFunction();
    
    return this->Function;
  }



  // Description:
  // Get the mtime of this object - override to consider the
  // mtime of the source as well.
  unsigned long GetMTime();

  // Description:
  // Returns the first point location which precedes a non-zero segment of the
  // function. Note that the value at this point may be zero.
  double GetFirstNonZeroValue();

  // Description:
  // Set / Get the minimum value of the function
  // Cannot clamp the value because the data might be 12- / 16-bit
  //vtkSetClampMacro(MinimumValue,int,0,255);
  vtkSetMacro(MinimumValue,int);
  vtkGetMacro(MinimumValue,int);
  // Description:
  // Set / Get the maximum value of the function
  //vtkSetClampMacro(MaximumValue,int,0,255);
  vtkSetMacro(MaximumValue,int);
  vtkGetMacro(MaximumValue,int);
  // Description:
  // Set / Get the minimum threshold of the function
  //vtkSetClampMacro(MinimumThreshold,int,0,255);
  vtkSetMacro(MinimumThreshold,int);
  vtkGetMacro(MinimumThreshold,int);
  
  // Description:
  // Set / Get the maximum threshold of the function
  //vtkSetClampMacro(MaximumThreshold,int,0,255);     
  vtkSetMacro(MaximumThreshold, int);
  vtkGetMacro(MaximumThreshold,int);
  
  void SetRangeMax(int rmx) {
       this->RangeMax = rmx;
       this->Reset();
       this->Initialize();
  }
  vtkGetMacro(RangeMax,int);  
  
  // Description:
  // Set / Get the processing threshold of the function, under which the function is identical
  //vtkSetClampMacro(ProcessingThreshold,int,0,255);          
  vtkSetMacro(ProcessingThreshold,int);          
  vtkGetMacro(ProcessingThreshold,int);
  // Description:
  // Set / Get the contrast
  vtkSetClampMacro(Contrast,double,0.0,255.0);         
  vtkGetMacro(Contrast,double);
  // Description:
  // Set / Get the brightness
  //vtkSetClampMacro(Brightness,int,-255,255);          
  vtkSetMacro(Brightness, int);
  vtkGetMacro(Brightness,int);
  // Description:
  // Set / Get the gamma
  vtkSetClampMacro(Gamma,double,0.0,255.0);
  vtkGetMacro(Gamma,double);      
  
  // Description:
  // Set / Get the smooth start gamma
  vtkSetClampMacro(SmoothStartGamma,double,0.0,255.0);
  vtkGetMacro(SmoothStartGamma,double);

  // Description:
  // Set / Get the smooth end gamma
  vtkSetClampMacro(SmoothEndGamma,double,0.0,255.0);
  vtkGetMacro(SmoothEndGamma,double);

  // Description:
  // Set / Get the smooth start
  vtkSetClampMacro(SmoothStart,int,0,255);
  vtkGetMacro(SmoothStart,int);
  // Description:
  // Set / Get the smooth end
  vtkSetClampMacro(SmoothEnd,int,0,255);
  vtkGetMacro(SmoothEnd,int);

  // Description:
  // Get the table representing this function
  //vtkGetVectorMacro(Function,int,255);
  
  // Description:
  // Get the point where the gamma curve starts
  vtkGetVector2Macro(GammaStart,int);
  // Description:
  // Get the point where the gamma curve ends
  vtkGetVector2Macro(GammaEnd,int);
  
  // Get the point where the gamma curve ends
  vtkGetVector2Macro(ReferencePoint,int);  
                     
  // Description:
  // A method that returns the y from the following formula:
  //                       (y2-y1)
  //               y =   ---------- * (x-x1)^g +y1
  //                      (x2-x1)^g
  //
  //                I.e the y coord of the gamma curve at point x, when the gamma
  //                curve starts at (x0,y0) and ends at (x1,y1) and the gamma 
  //                value is g
  //
  //      Parameters:
  //              x0,y0   The starting point of the gamma curve
  //              x1,y1   The end point of the gamma curve
  //              x       The point from which we want the gamma curves y coord
  //              g       The gamma value
  int GammaValue(int x0,int y0, int x1,int y1, int x, double gamma);
  // Description:
  // Returns the value of the function at slope point x
  // The function is of format:
  // y = contrast * x + b


  int f4(int x, int gx1,int gy1,int gx2,int gy2);
  void Reset(void);
protected:
  vtkIntensityTransferFunction();
  ~vtkIntensityTransferFunction();

  // Size of the array used to store function points
  int   ArraySize;

  // Array of points ((X,Y) pairs)
  int *Function;

  // Min and max range of function point locations
  int FunctionRange[2];

  // Increases size of the function array. The array grows by a factor of 2
  // when the array limit has been reached.
  void IncreaseArraySize();

  // Description:
  // Returns the starting point of the slope 
  void GetSlopeStart(int*x,int*y);
  // Description:
  // Returns the end point of the slope
  void GetSlopeEnd(int*x,int*y);

  // Description:
  // Returns the starting and ending point of the gamma curve
  void GetGammaPoints(int *gx0, int *gy0, int *gx1, int *gy1);

  int MinimumValue;
  int MaximumValue;
  int MinimumThreshold;
  int MaximumThreshold;
  int ProcessingThreshold;
  int Brightness;
  int SmoothStart;
  int SmoothEnd;
  double Gamma;
  double SmoothStartGamma;
  double SmoothEndGamma;
  double Contrast;
  int GammaStart[2];
  int GammaEnd[2];
  int ReferencePoint[2];
  int RangeMax;
  vtkTimeStamp BuildTime;
private:
  vtkIntensityTransferFunction(const vtkIntensityTransferFunction&);  // Not implemented.
  void operator=(const vtkIntensityTransferFunction&);  // Not implemented.
};

#endif

