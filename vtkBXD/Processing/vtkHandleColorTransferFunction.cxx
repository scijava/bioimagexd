/*=========================================================================

  Program:   BioImageXD
  Module:    vtkHandleColorTransferFunction.cxx

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

#include "vtkHandleColorTransferFunction.h"
#include "vtkObjectFactory.h"
#include "vtkUnsignedCharArray.h"
#include <cstdlib>
#include <ctime>

vtkStandardNewMacro(vtkHandleColorTransferFunction);

vtkHandleColorTransferFunction::vtkHandleColorTransferFunction()
{
  this->FileName = 0;
  this->InputString = 0;
  this->InputStrLen = 0;
  this->OutputArray = 0;
  this->OutputString = vtkUnsignedCharArray::New();
}

vtkHandleColorTransferFunction::~vtkHandleColorTransferFunction()
{
  this->SetFileName(0);
  this->InputString = 0;
  if (this->OutputArray) delete[] this->OutputArray;
  this->OutputArray = 0;
  if (this->OutputString) this->OutputString->Delete();
  this->OutputString = 0;
}

void vtkHandleColorTransferFunction::PrintSelf(ostream &os, vtkIndent indent)
{
  this->Superclass::PrintSelf(os,indent);
  os << indent << "FileName: " << this->FileName;
}

int vtkHandleColorTransferFunction::
SaveColorTransferFunction(vtkColorTransferFunction *ctf)
{
  if (!this->FileName)
	{
	  vtkErrorMacro(<< "FileName is not defined");
	  return 0;
	}

  ofstream *of = new ofstream(this->FileName, ios::out | ios::binary);
  if (!of || of->fail())
	{
	  if (of) delete of;
	  vtkErrorMacro(<< "Couldn't open file " << this->FileName);
	  return 0;
	}

  double min;
  double max;
  ctf->GetRange(min,max);
  int size = static_cast<int>(max-min+1);
  const char *table;
  table = reinterpret_cast<const char*>(ctf->GetTable(min, max, size));
  of->write(table,size*3);

  delete of;

  return 1;
}

int vtkHandleColorTransferFunction::
ReadColorTransferFunction(vtkColorTransferFunction *ctf)
{
  if (!this->FileName)
	{
	  vtkErrorMacro(<< "FileName is not defined");
	  return 0;
	}

  ifstream *is = new ifstream(this->FileName, ios::in | ios::binary);
  if (!is || is->fail())
	{
	  if (is) delete is;
	  vtkErrorMacro(<< "Couldn't open file " << this->FileName);
	  return 0;
	}

  is->seekg(0, ios::end);
  int size = is->tellg();
  is->seekg(0, ios::beg);

  char *table = new char[size];
  is->read(table,size);

  double *convTable = new double[size];
  double *doublePtr = convTable;
  const unsigned char *tablePtr = reinterpret_cast<unsigned char*>(table);
  for (int i = 0; i < size; ++i)
	{
	  *doublePtr = *tablePtr / 255.0;
	  doublePtr++;
	  tablePtr++;
	}
  ctf->BuildFunctionFromTable(0.0, size/3-1, size/3, convTable);

  delete[] convTable;
  delete[] table;
  delete is;

  return 1;
}

int vtkHandleColorTransferFunction::
LoadColorTransferFunctionFromString(vtkColorTransferFunction *ctf, int start, int end)
{
  if (!this->InputString)
	{
	  vtkErrorMacro(<< "String is not defined");
	  return 0;
	}

  ctf->RemoveAllPoints();

  int points = (end-start+1);
  double *table = new double[points*3];
  double *tablePtr = table;
  double red;
  double green;
  double blue;
  int gPoint = this->InputStrLen / 3;
  int bPoint = gPoint * 2;

  for (int i = 0; (i < points) && (bPoint + i < this->InputStrLen); ++i)
	{
	  red = this->InputString[i] / 255.0;
	  green = this->InputString[gPoint+i] / 255.0;
	  blue = this->InputString[bPoint+i] / 255.0;
	  tablePtr[0] = red;
	  tablePtr[1] = green;
	  tablePtr[2] = blue;
	  tablePtr += 3;
	}

  ctf->BuildFunctionFromTable(start, end, points, table);
  delete[] table;

  return 1;
}

int vtkHandleColorTransferFunction::
ColorTransferFunctionToString(vtkColorTransferFunction *ctf, int perColor)
{
  double min = 0.0;
  double max = 0.0;
  ctf->GetRange(min,max);
  int size = static_cast<int>(max-min+1);

  const char *table;
  table = reinterpret_cast<const char*>(ctf->GetTable(min, max, size));

  if (this->OutputArray) delete this->OutputArray;
  int outputSize = static_cast<int>(3 * size / perColor);
  this->OutputArray = new unsigned char[outputSize];

  for (int i = 0; i < 3; ++i)
	{
	  for (int j = 0; j < size; j += perColor)
		{
		  this->OutputArray[i*size+j] = table[j*3+i];
		  int elemId = i*size + j;
		}
	}
  this->OutputString->SetArray(this->OutputArray,outputSize,1);

  return 1;
}

void vtkHandleColorTransferFunction::
CreateRandomColorTransferFunction(vtkColorTransferFunction *ctf, int min, int max, double threshold)
{
  double rangeMin = 0.0;
  double rangeMax = 0.0;
  ctf->GetRange(rangeMin,rangeMax);
  int originalSize = static_cast<int>(rangeMax - rangeMin + 1);
  double *originalTable = new double[originalSize*3];
  ctf->GetTable(rangeMin, rangeMax, originalSize, originalTable);

  if (min < 0) min = 0;
  int size = (max - min + originalSize + 1) * 3;
  if (size < originalSize*3) size = originalSize * 3;
  if (size <= 0)
	{
	  delete[] originalTable;
	  vtkDebugMacro(<< "No points were created since max < min");
	  return;
	}

  double *table = new double[size];
  double *tablePtr = table;
  if (threshold > 2.5) threshold = 2.5;
  for (int i = 0; i < originalSize * 3; ++i, ++tablePtr)
	{
	  *tablePtr = originalTable[i];
	}

  srand(time(NULL));
  double random;
  double red;
  double green;
  double blue;
  for (int i = min; i <= max; ++i)
	{
	  red = green = blue = 0.0;
	  while (red + green + blue < threshold)
		{
		  random = static_cast<double>(rand() % 256);
		  red = random / 256.0;
		  random = static_cast<double>(rand() % 256);
		  green = random / 256.0;
		  random = static_cast<double>(rand() % 256);
		  blue = random / 256.0;
		}
	  tablePtr[0] = red;
	  tablePtr[1] = green;
	  tablePtr[2] = blue;
	  tablePtr += 3;
	}

  ctf->BuildFunctionFromTable(0.0,size/3-1,size/3,table);
  delete[] table;
  delete[] originalTable;
}

int vtkHandleColorTransferFunction::SetInputString(void *str, int len)
{
  if (!str)
	{
	  vtkErrorMacro(<< "str is not defined");
	  return 0;
	}

  this->InputString = static_cast<unsigned char*>(str);
  this->InputStrLen = len;

  return 1;
}

vtkUnsignedCharArray* vtkHandleColorTransferFunction::GetOutputString()
{
  return this->OutputString;
}

unsigned char* vtkHandleColorTransferFunction::GetOutputArray()
{
  return this->OutputArray;
}
