/*=========================================================================

  Program:   BioImageXD
  Module:    vtkHandleColorTransferFunction.h
  Language:  C++
  Date:      $Date$
  Version:   $Revision$

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
// .NAME vtkHandleColorTransferFunction - Fast saving to and reading from ctf file 

// .SECTION Description

#ifndef __vtkHandleColorTransferFunction_h
#define __vtkHandleColorTransferFunction_h

#include "vtkObject.h"
#include "vtkBXDProcessingWin32Header.h"
#include "vtkColorTransferFunction.h"

class VTK_BXD_PROCESSING_EXPORT vtkHandleColorTransferFunction: public vtkObject
{
public:
  vtkTypeMacro(vtkHandleColorTransferFunction,vtkObject);
  static vtkHandleColorTransferFunction *New();
  virtual void PrintSelf(ostream&, vtkIndent);

  int SaveColorTransferFunction(vtkColorTransferFunction*);
  int ReadColorTransferFunction(vtkColorTransferFunction*);
  int LoadColorTransferFunctionFromString(vtkColorTransferFunction*, int, int);
  int ColorTransferFunctionToString(vtkColorTransferFunction*, int);
  void CreateRandomColorTransferFunction(vtkColorTransferFunction*, int, int, double);
  int SetInputString(void*, int);
  vtkUnsignedCharArray* GetOutputString();
  unsigned char* GetOutputArray();

  // Set and Get macros
  vtkSetStringMacro(FileName);
  vtkGetStringMacro(FileName);

protected:
  vtkHandleColorTransferFunction();
  ~vtkHandleColorTransferFunction();

  char* FileName;
  vtkUnsignedCharArray* OutputString;
  unsigned char* OutputArray;
  unsigned char* InputString;
  int InputStrLen;


private:
  vtkHandleColorTransferFunction(const vtkHandleColorTransferFunction&); // Not implemented
  void operator=(const vtkHandleColorTransferFunction&); // Not implemented
};

#endif
