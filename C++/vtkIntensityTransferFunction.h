/*=========================================================================

  Program:   Visualization Toolkit
  Module:    $RCSfile: vtkPiecewiseFunction.h,v $

  Copyright (c) Ken Martin, Will Schroeder, Bill Lorensen
  All rights reserved.
  See Copyright.txt or http://www.kitware.com/Copyright.htm for details.

     This software is distributed WITHOUT ANY WARRANTY; without even
     the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
     PURPOSE.  See the above copyright notice for more information.

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

class VTK_FILTERING_EXPORT vtkIntensityTransferFunction : public vtkPiecewiseFunction
{
public:
  static vtkPiecewiseFunction *New();
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
  // Returns a pointer to the data stored in the table.
  // Fills from a pointer to data stored in a similar table.
  int *GetDataPointer() {return this->Function;};
  void FillFromDataPointer(int, int*);

  // Description:
  // Returns the min and max point locations of the function.
  int *GetRange();


  // Description:
  // Return the type of function:
  // Function Types:
  //    0 : Constant        (No change in slope between end points)
  //    1 : NonDecreasing   (Always increasing or zero slope)
  //    2 : NonIncreasing   (Always decreasing or zero slope)
  //    3 : Varied          (Contains both decreasing and increasing slopes)
  const char  *GetType();

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
  vtkSetMacro(MinimumValue,int);
  // Description:
  // Set / Get the maximum value of the function
  vtkSetMacro(MaximumValue,int);
  // Description:
  // Set / Get the minimum threshold of the function
  vtkSetMacro(MinimumThreshold,int);
  // Description:
  // Set / Get the maximum threshold of the function
  vtkSetMacro(MaximumThreshold,int);     
  // Description:
  // Set / Get the processing threshold of the function, under which the function is identical
  vtkSetMacro(ProcessingThreshold,int);          
  // Description:
  // Set / Get the contrast
  vtkSetMacro(Contrast,int);     
  // Description:
  // Set / Get the brightness
  vtkSetMacro(Brightness,int);          
  // Description:
  // Set / Get the gamma
  vtkSetMacro(Gamma,double);
     
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

  int MinimumValue;
  int MaximumValue;
  int MinimumThreshold;
  int MaximumThreshold;
  int ProcessingThreshold;
  int Contrast;
  int Brightness;
  double Gamma;
   
     
private:
  vtkIntensityTransferFunction(const vtkIntensityTransferFunction&);  // Not implemented.
  void operator=(const vtkIntensityTransferFunction&);  // Not implemented.
};

#endif

