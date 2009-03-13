/*=========================================================================

  Program:   BioImageXD
  Module:    vtkTestMemory.h
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

#ifndef __vtkTestMemory_h
#define __vtkTestMemory_h

#include "vtkObject.h"
#include "vtkObjectFactory.h"
#include "vtkBXDProcessingWin32Header.h"

class VTK_BXD_PROCESSING_EXPORT vtkTestMemory: public vtkObject
{
 public:
  vtkTypeMacro(vtkTestMemory,vtkObject);
  static vtkTestMemory *New();
  virtual void PrintSelf(ostream&, vtkIndent);
  long long CheckMemory();
  vtkGetMacro(MaxMemory, long long);

 protected:
  vtkTestMemory();
  ~vtkTestMemory();
  long long MaxMemory;

 private: // Only define operator= and copy constructor to prevent illegal use
  void operator=(const vtkTestMemory&);
  vtkTestMemory(const vtkTestMemory&);
};

#endif
