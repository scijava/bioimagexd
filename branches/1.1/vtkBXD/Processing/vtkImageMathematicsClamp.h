/*=========================================================================

  Program:   BioImageXD
  Module:    $RCSfile: vtkImageMathematicsClamp.h,v $

  Edited by Lassi Paavolainen to include clamping of overflow
  Copyright (C) 2009  BioImageXD Project
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

  Original file vtkImageMathematics.h
  Copyright (c) Ken Martin, Will Schroeder, Bill Lorensen
  All rights reserved.
  See Copyright.txt or http://www.kitware.com/Copyright.htm for details.

     This software is distributed WITHOUT ANY WARRANTY; without even
     the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
     PURPOSE.  See the above copyright notice for more information.

=========================================================================*/
// .NAME vtkImageMathematicsClamp - Add, subtract, multiply, divide, invert,
// sin, cos, exp, log.
// .SECTION Description
// vtkImageMathematicsClamp implements basic mathematic operations SetOperation
// is used to select the filters behavior.  The filter can take two or one
// input.


#ifndef __vtkImageMathematicsClamp_h
#define __vtkImageMathematicsClamp_h


// Operation options.
#define VTK_ADD                0
#define VTK_SUBTRACT           1
#define VTK_MULTIPLY           2
#define VTK_DIVIDE             3
#define VTK_INVERT             4
#define VTK_SIN                5
#define VTK_COS                6
#define VTK_EXP                7
#define VTK_LOG                8
#define VTK_ABS                9
#define VTK_SQR               10
#define VTK_SQRT              11
#define VTK_MIN               12
#define VTK_MAX               13
#define VTK_ATAN              14
#define VTK_ATAN2             15
#define VTK_MULTIPLYBYK       16
#define VTK_ADDC              17
#define VTK_CONJUGATE         18
#define VTK_COMPLEX_MULTIPLY  19
#define VTK_REPLACECBYK       20

#include "vtkBXDProcessingWin32Header.h"
#include "vtkThreadedImageAlgorithm.h"

class VTK_BXD_PROCESSING_EXPORT vtkImageMathematicsClamp : public vtkThreadedImageAlgorithm
{
public:
  static vtkImageMathematicsClamp *New();
  vtkTypeMacro(vtkImageMathematicsClamp,vtkThreadedImageAlgorithm);
  void PrintSelf(ostream& os, vtkIndent indent);

  // Description:
  // Set/Get the Operation to perform.
  vtkSetMacro(Operation,int);
  vtkGetMacro(Operation,int);
  void SetOperationToAdd() {this->SetOperation(VTK_ADD);};
  void SetOperationToSubtract() {this->SetOperation(VTK_SUBTRACT);};
  void SetOperationToMultiply() {this->SetOperation(VTK_MULTIPLY);};
  void SetOperationToDivide() {this->SetOperation(VTK_DIVIDE);};
  void SetOperationToConjugate() {this->SetOperation(VTK_CONJUGATE);};
  void SetOperationToComplexMultiply()
    {this->SetOperation(VTK_COMPLEX_MULTIPLY);};

  void SetOperationToInvert() {this->SetOperation(VTK_INVERT);};
  void SetOperationToSin() {this->SetOperation(VTK_SIN);};
  void SetOperationToCos() {this->SetOperation(VTK_COS);};
  void SetOperationToExp() {this->SetOperation(VTK_EXP);};
  void SetOperationToLog() {this->SetOperation(VTK_LOG);};
  void SetOperationToAbsoluteValue() {this->SetOperation(VTK_ABS);};
  void SetOperationToSquare() {this->SetOperation(VTK_SQR);};
  void SetOperationToSquareRoot() {this->SetOperation(VTK_SQRT);};
  void SetOperationToMin() {this->SetOperation(VTK_MIN);};
  void SetOperationToMax() {this->SetOperation(VTK_MAX);};

  void SetOperationToATAN() {this->SetOperation(VTK_ATAN);};
  void SetOperationToATAN2() {this->SetOperation(VTK_ATAN2);};
  void SetOperationToMultiplyByK() {this->SetOperation(VTK_MULTIPLYBYK);};
  void SetOperationToAddConstant() {this->SetOperation(VTK_ADDC);};
  void SetOperationToReplaceCByK() {this->SetOperation(VTK_REPLACECBYK);};
  vtkSetMacro(ConstantK,double);
  vtkGetMacro(ConstantK,double);
  vtkSetMacro(ConstantC,double);
  vtkGetMacro(ConstantC,double);

  // How to handle divide by zero
  vtkSetMacro(DivideByZeroToC,int);
  vtkGetMacro(DivideByZeroToC,int);
  vtkBooleanMacro(DivideByZeroToC,int);

  // Description:
  // Set the two inputs to this filter
  virtual void SetInput1(vtkDataObject *in) { this->SetInput(0,in); }
  virtual void SetInput2(vtkDataObject *in) { this->SetInput(1,in); }

  // Description:
  // When the ClampOverflow flag is on, the data is thresholded so that
  // the output value does not exceed the max or min of the data type.
  // By default, ClampOverflow is off.
  vtkSetMacro(ClampOverflow, int);
  vtkGetMacro(ClampOverflow, int);
  vtkBooleanMacro(ClampOverflow, int);

protected:
  vtkImageMathematicsClamp();
  ~vtkImageMathematicsClamp() {};

  int Operation;
  double ConstantK;
  double ConstantC;
  int DivideByZeroToC;
  int ClampOverflow;

  virtual int RequestInformation (vtkInformation *,
                                  vtkInformationVector **,
                                  vtkInformationVector *);

  virtual void ThreadedRequestData(vtkInformation *request,
                                   vtkInformationVector **inputVector,
                                   vtkInformationVector *outputVector,
                                   vtkImageData ***inData,
                                   vtkImageData **outData,
                                   int extent[6], int threadId);

  virtual int FillInputPortInformation(int port, vtkInformation* info);

private:
  vtkImageMathematicsClamp(const vtkImageMathematicsClamp&); // Not implemented.
  void operator=(const vtkImageMathematicsClamp&);  // Not implemented.
};

#endif
