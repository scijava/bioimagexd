/*=========================================================================

  Program:   BioImageXD
  Module:    vtkTestMemory.cxx
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

#include "vtkTestMemory.h"
#include "vtkUnsignedCharArray.h"

#define START_ALLOC 1024
#define MAX_ALLOC 2147483647
#define START_STEP 536870912

vtkStandardNewMacro(vtkTestMemory);

vtkTestMemory::vtkTestMemory()
{
	this->MaxMemory = 0;
}

vtkTestMemory::~vtkTestMemory()
{
}

void vtkTestMemory::PrintSelf(ostream& os, vtkIndent indent)
{
  this->Superclass::PrintSelf(os,indent);
}

long vtkTestMemory::CheckMemory()
{
	long alloc = START_ALLOC;
	long maxAlloc = MAX_ALLOC;
	long minAlloc = 0;
	long step = START_STEP;
	while(maxAlloc - minAlloc > START_ALLOC) {
		std::cout << "Allocating " << alloc << " bytes of memory." << std::endl;
		try {
			char *mem = new char[alloc];
			minAlloc = alloc;
			alloc += step;
			delete[] mem;
		}
		catch (std::bad_alloc &ba)
		{
			std::cout << "Couldn't allocate " << alloc / 1048576 << " MB of memory." << std::endl;
			maxAlloc = alloc;
			alloc = minAlloc;
			step /= 2;
			alloc += step;
		}
	}

	this->MaxMemory = minAlloc;

	return this->MaxMemory;
/*	long long bufferItems = 10;
	vtkUnsignedCharArray *pointDataArray;
	pointDataArray = vtkUnsignedCharArray::New();
	pointDataArray->SetNumberOfComponents(1);
	pointDataArray->SetNumberOfValues(bufferItems);
	//pointDataArray->SetArray(static_cast<unsigned char*>(buffer),bufferSize,0);
	//imageData->GetPointData()->SetScalars(pointDataArray);
	pointDataArray->Delete(); */
}
