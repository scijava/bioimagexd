/*=========================================================================

  Program:   BioImageXD
  Module:    vtkLIFReader.cxx
  Language:  C++
  Date:      $Date: 2008-01-29 10:11:17 +0200 (Tue, 29 Jan 2008) $
  Version:   $Revision: 1366 $


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

#include "vtkMRCReader.h"
#include "vtkObjectFactory.h"
#include "vtkInformation.h"
#include "vtkDataObject.h"
#include "vtkInformationVector.h"
#include "vtkStreamingDemandDrivenPipeline.h"
#include "vtkImageData.h"
#include "vtkPointData.h"
#include "vtkUnsignedCharArray.h"
#include "vtkShortArray.h"
#include "vtkFloatArray.h"
#include "vtkByteSwap.h"
#include <limits>

// Template function for setting different type image scalars
template<class TArray, class TBuffer>
void SetImageScalars(vtkImageData*, TBuffer*, unsigned int);
// Template function for returning array as stream
template<class TArray>
ostream& PutArrayToStream(ostream &os, TArray*, int);

vtkStandardNewMacro(vtkMRCReader);

static const int HeaderSize = 1024;
vtkMRCReader::vtkMRCReader()
{
  this->SetNumberOfInputPorts(0);
  this->SetNumberOfOutputPorts(1);
  this->Clear();
}

vtkMRCReader::~vtkMRCReader()
{
  this->Clear();
}

const char* vtkMRCReader::GetFileExtensions()
{
  return ".mrc .MRC .st .ST";
}

void vtkMRCReader::PrintSelf(ostream& os, vtkIndent indent)
{
  this->Superclass::PrintSelf(os,indent);
  if (this->File)
	{
	  os << indent << "File name: " << this->FileName << std::endl;
	  os << indent << "File size: " << this->FileSize << std::endl;
	}
  if (this->HeaderInfoRead)
	{
	  os << indent << "Little endian: " << this->LittleEndian << std::endl;
	  os << indent << "Dimensions: ";
	  PutArrayToStream<int>(os,this->ImageDims,3) << std::endl;
	  os << indent << "Header values:" << std::endl;
	  os << indent << indent << "N: ";
	  PutArrayToStream<int>(os,this->N,3) << std::endl;
	  os << indent << indent << "Mode: " << this->Mode << std::endl;
	  os << indent << indent << "NStart: ";
	  PutArrayToStream<int>(os,this->NStart,3) << std::endl;
	  os << indent << indent << "M: ";
	  PutArrayToStream<int>(os,this->M,3) << std::endl;
	  os << indent << indent << "Len: ";
	  PutArrayToStream<float>(os,this->Len,3) << std::endl;
	  os << indent << indent << "Angles: ";
	  PutArrayToStream<float>(os,this->Angles,3) << std::endl;
	  os << indent << indent << "Map: ";
	  PutArrayToStream<int>(os,this->Map,3) << std::endl;
	  os << indent << indent << "Min: " << this->Min << std::endl;
	  os << indent << indent << "Max: " << this->Max << std::endl;
	  os << indent << indent << "Mean: " << this->Mean << std::endl;
	  os << indent << indent << "Bytes in extended header: " << this->Next << std::endl;
	  os << indent << indent << "Origin: ";
	  PutArrayToStream<float>(os,this->Origin,3) << std::endl;
	  os << indent << indent << "Number of labels: " << this->NLabl << std::endl;
	  for (int i = 0; i < this->NLabl; ++i)
		{
		  os << indent << indent << indent << "Label " << (i+1) << ": " << this->Labels[i] << std::endl;
		}
	}
}

void vtkMRCReader::SetFileName(const char* filename)
{
  if (!filename && !this->FileName)
	{
	  return;
	}
  if (this->FileName && filename && !strcmp(this->FileName,filename))
	{
	  vtkDebugMacro(<< "Same file name already set, " << filename);
	  return;
	}

  // Remove earlier info
  this->Clear();
 
  if (filename)
	{
	  this->FileName = new char[strlen(filename) + 1];
	  strcpy(this->FileName,filename);
	  this->FileName[strlen(filename)] = '\0';
	}
  this->Modified();
  this->State = 1;
}

int vtkMRCReader::OpenFile()
{
  if (!this->FileName)
	{
	  vtkErrorMacro(<< "File name is not specified.");
	  return 0;
	}

  if (this->State > 1) this->Initialize(); // Initialize reader

  this->File = new ifstream(this->FileName, ios::in | ios::binary);
  if (!this->File || this->File->fail())
	{
	  delete this->File;
	  vtkErrorMacro(<< "OpenFile: Could not open file " << this->FileName);
	  this->Modified();
	  return 0;
	}
  this->File->exceptions(ifstream::eofbit | ifstream::failbit | ifstream::badbit);

  this->File->seekg(0,ios::end);
  this->FileSize = this->File->tellg();
  this->File->seekg(0,ios::beg);

  this->Modified();
  this->State = 2;
  return 1;
}

void vtkMRCReader::CloseFile()
{
  this->Clear();
  this->Modified();
}

int vtkMRCReader::ReadHeader()
{
  if (!this->File)
	{
	  if (!this->OpenFile())
		{
		  vtkErrorMacro(<< "ReadHeader: Could not read header of unopened file.");
		  return 0;
		}
	}

  this->File->seekg(0,ios::beg);
  char buffer[HeaderSize];
  char *pointer = buffer;

  try 
	{
	  this->File->read(buffer,HeaderSize);
	}
  catch (ifstream::failure e)
	{
	  vtkErrorMacro(<< "Failed to read " << HeaderSize << " bytes of header from file " << this->FileName);
	  return 0;
	}
  vtkDebugMacro(<< "Read " << HeaderSize << " bytes of header.");

  // Check if file is in little endian or not
  this->LittleEndian = int(buffer[212]) == 68 || int(buffer[213]) == 68 || int(buffer[214] == 68) || int(buffer[215] == 68);

  // Read values of header
  this->ReadVector(&pointer,this->N,3);
  this->Mode = this->ReadInt(&pointer);
  this->ReadVector(&pointer,this->NStart,3);
  this->ReadVector(&pointer,this->M,3);
  this->ReadVector(&pointer,this->Len,3);
  this->ReadVector(&pointer,this->Angles,3);
  this->ReadVector(&pointer,this->Map,3);
  this->Min = this->ReadFloat(&pointer);
  this->Max = this->ReadFloat(&pointer);
  this->Mean = this->ReadFloat(&pointer);
  this->ISPG = this->ReadShort(&pointer);
  this->NSymbt = this->ReadShort(&pointer);
  this->Next = this->ReadInt(&pointer);
  this->CreatorID = this->ReadShort(&pointer);

  pointer += 30; // Not used bytes
  this->NInt = this->ReadShort(&pointer);
  this->NReal = this->ReadShort(&pointer);
  pointer += 28; // Not used bytes

  this->IDType = this->ReadShort(&pointer);
  this->Lens = this->ReadShort(&pointer);
  this->ReadVector(&pointer,this->ND,2);
  this->ReadVector(&pointer,this->VD,2);
  this->ReadVector(&pointer,this->TiltAngles,6);
  this->ReadVector(&pointer,this->Origin,3);

  strncpy(this->CMap,pointer,4);
  pointer += 4;
  strncpy(this->Stamp,pointer,4);
  pointer += 4;

  this->RMS = this->ReadFloat(&pointer);
  this->NLabl = this->ReadInt(&pointer);
  if (this->NLabl > 0)
	{
	  this->Labels = new char*[this->NLabl];
	  for (int i = 0; i < this->NLabl; ++i)
		{
		  this->Labels[i] = new char[81];
		  strncpy(this->Labels[i],pointer,80);
		  (this->Labels[i])[80] = '\0';
		  pointer += 80;
		}
	}

  this->SetImageDims();
  this->CalculateVoxelSize();
  this->HeaderInfoRead = 1;
  this->Modified();

  return 1;
}

int vtkMRCReader::RequestInformation(vtkInformation* vtkNotUsed(request),
									 vtkInformationVector** vtkNotUsed(inputVector),
									 vtkInformationVector *outputVector)
{
  if (!this->HeaderInfoRead)
	{
	  if (!this->ReadHeader())
		{
		  vtkErrorMacro(<< "Couldn't read header of file: " << this->FileName);
		  return 0;
		}
	}

  vtkInformation *info = outputVector->GetInformationObject(0);

  double spacing[3];
  int extent[6];
  this->CalculateExtentAndSpacing(extent,spacing);
  info->Set(vtkDataObject::SPACING(),spacing,3);
  info->Set(vtkStreamingDemandDrivenPipeline::WHOLE_EXTENT(),extent,6);
  info->Set(vtkDataObject::ORIGIN(),(double*)this->Origin,3);

  vtkDebugMacro(<< "Set extent: " << extent[0] << "," << extent[1] << "," << extent[2] << "," << extent[3] << "," << extent[4] << "," << extent[5]);
  vtkDebugMacro(<< "Set spacing: " << spacing[0] << "," << spacing[1] << "," << spacing[2]);
  vtkDebugMacro(<< "Set origin: " << this->Origin[0] << "," << this->Origin[1] << "," << this->Origin[2]);

  if (this->Mode == 0)
	{
	  vtkDataObject::SetPointDataActiveScalarInfo(info,VTK_UNSIGNED_CHAR,1);
	}
  else if (this->Mode == 1)
	{
	  vtkDataObject::SetPointDataActiveScalarInfo(info,VTK_SHORT,1);
	}
  else if (this->Mode == 2)
	{
	  vtkDataObject::SetPointDataActiveScalarInfo(info,VTK_FLOAT,1);
	}

  return 1;
}

int vtkMRCReader::RequestUpdateExtent(vtkInformation* vtkNotUsed(request),
									  vtkInformationVector** vtkNotUsed(inputVector),
									  vtkInformationVector *outputVector)
{
  int uext[6];
  int ext[6];

  vtkInformation *outInfo = outputVector->GetInformationObject(0);
  outInfo->Get(vtkStreamingDemandDrivenPipeline::WHOLE_EXTENT(),ext);
  outInfo->Get(vtkStreamingDemandDrivenPipeline::UPDATE_EXTENT(),uext);

  vtkDebugMacro(<< "Requested update extent: " << uext[0] << "," << uext[1] << "," << uext[2] << "," << uext[3] << "," << uext[4] << "," << uext[5]);
  if (uext[0] > ext[0]) uext[0] = ext[0];
  if (uext[1] < ext[1]) uext[1] = ext[1];
  if (uext[2] > ext[2]) uext[2] = ext[2];
  if (uext[3] < ext[3]) uext[3] = ext[3];
  outInfo->Set(vtkStreamingDemandDrivenPipeline::UPDATE_EXTENT(),uext,6);
  vtkDebugMacro("Set update extent: " << uext[0] << "," << uext[1] << "," << uext[2] << "," << uext[3] << "," << uext[4] << "," << uext[5]);

  return 1;
}

int vtkMRCReader::RequestData(vtkInformation* vtkNotUsed(request),
							  vtkInformationVector** vtkNotUsed(inputVector),
							  vtkInformationVector *outputVector)
{
  if (!this->HeaderInfoRead)
	{
	  vtkErrorMacro(<< "RequestData: Header info isn't read.");
	  return 0;
	}

  int extent[6];
  vtkInformation *outInfo = outputVector->GetInformationObject(0);
  vtkImageData *imageData = this->AllocateOutputData(outInfo->Get(vtkDataObject::DATA_OBJECT()));
  imageData->GetPointData()->GetScalars()->SetName("MRC Scalars");
  imageData->GetExtent(extent);

  unsigned int slices = extent[5] - extent[4] + 1;
  unsigned int pixelsX = extent[1] - extent[0] + 1;
  unsigned int pixelsY = extent[3] - extent[2] + 1;
  unsigned int slicePixels = pixelsX * pixelsY;
  unsigned int bufferVoxels = slicePixels * slices;

  void *buffer;
  char *bufPointer;
  unsigned int pixelBytes;
  if (this->Mode == 0)
	{
	  buffer = new unsigned char[bufferVoxels];
	  bufPointer = static_cast<char*>(buffer);
	  pixelBytes = 1;
	}
  else if (this->Mode == 1)
	{
	  buffer = new short[bufferVoxels];
	  bufPointer = static_cast<char*>(buffer);
	  pixelBytes = 2;
	}
  else if (this->Mode == 2)
	{
	  buffer = new float[bufferVoxels];
	  bufPointer = static_cast<char*>(buffer);
	  pixelBytes = 4;
	}
  else
	{
	  vtkErrorMacro(<< "Types of pixels in image are not supported: " << this->FileName);
	  return 0;
	}

  unsigned int headersSize = HeaderSize + this->Next;
  unsigned int sliceSize = slicePixels * pixelBytes;
  for (int i = extent[4]; i <= extent[5]; ++i)
	{
	  this->File->seekg(headersSize + sliceSize * i,ios::beg);
	  this->File->read(bufPointer,sliceSize);
	  vtkDebugMacro(<< "Read " << sliceSize << " bytes into buffer.");
	  bufPointer += sliceSize;
	}

  switch (this->Mode)
	{
	case 0:
	  SetImageScalars<vtkUnsignedCharArray,unsigned char>(imageData,static_cast<unsigned char*>(buffer),bufferVoxels);
	  break;
	case 1:
	  SetImageScalars<vtkShortArray,short>(imageData,static_cast<short*>(buffer),bufferVoxels);
	  break;
	case 2:
	  SetImageScalars<vtkFloatArray,float>(imageData,static_cast<float*>(buffer),bufferVoxels);
	  break;
	}

  return 1;
}

void vtkMRCReader::Initialize()
{
  /*  if (this->State > 0 && this->FileName)
	{
	  //delete [] this->FileName;
	  this->FileName = NULL;
	}
  if (this->State > 1 && this->File)
	{
	  //delete this->File;
	  this->File = NULL;
	  }*/
  this->FileSize = 0;
  this->ImageDims[0] = this->ImageDims[1] = this->ImageDims[2] = 0;
  this->VoxelSize[0] = this->VoxelSize[1] = this->VoxelSize[2] = 0.0;
  this->HeaderInfoRead = 0;
  this->LittleEndian = 0;
  this->N[0] = this->N[1] = this->N[2] = 0;
  this->Mode = -1;
  this->NStart[0] = this->NStart[1] = this->NStart[2] = 0;
  this->M[0] = this->M[1] = this->M[2] = 0;
  this->Len[0] = this->Len[1] = this->Len[2] = 0.0;
  this->Angles[0] = this->Angles[1] = this->Angles[2] = 0.0;
  this->Map[0] = this->Map[1] = this->Map[2] = 0;
  this->Min = this->Max = this->Mean = 0.0;
  this->ISPG = 0;
  this->NSymbt = 0;
  this->Next = 0;
  this->CreatorID = 0;
  this->NInt = 0;
  this->NReal = 0;
  this->IDType = -1;
  this->Lens = 0;
  this->ND[0] = this->ND[1] = 0;
  this->VD[0] = this->VD[1] = 0;
  for (int i = 0; i < 6; ++i)
	{
	  this->TiltAngles[i] = 0.0;
	}
  this->Origin[0] = this->Origin[1] = this->Origin[2] = 0.0;
  for (int i = 0; i < 4; ++i)
	{
	  CMap[i] = '\0';
	  Stamp[i] = '\0';
	}
  this->RMS = 0.0;

  if (this->Labels && this->NLabl > 0 && this->HeaderInfoRead)
	{
	  for (int i = 0; i < this->NLabl; ++i)
		{
		  delete [] this->Labels[i];
		}
	  delete [] this->Labels;
	}
  this->NLabl = 0;
  this->Labels = NULL;
}

void vtkMRCReader::Clear()
{
  this->FileName = NULL;
  this->Initialize();
  this->State = 0;
}

void vtkMRCReader::SetImageDims()
{
  for (int i = 0; i < 3; ++i)
	{
	  switch (this->Map[i])
		{
		case 1:
		  this->ImageDims[0] = this->N[i];
		  break; 
		case 2:
		  this->ImageDims[1] = this->N[i];
		  break;
		case 3:
		  this->ImageDims[2] = this->N[i];
		  break;
		}
	}
}

void vtkMRCReader::CalculateVoxelSize()
{
  this->VoxelSize[0] = this->Len[0] / this->M[0];
  this->VoxelSize[1] = this->Len[1] / this->M[1];
  this->VoxelSize[2] = this->Len[2] / this->M[2];
}

void vtkMRCReader::CalculateExtentAndSpacing(int *extent, double *spacing)
{
  // Set extent straight from dimensions. We could also calculate extent using
  // NStart but we need extent as ex. 0-24 not 5-29
  extent[0] = extent[2] = extent[4] = 0;
  extent[1] = this->ImageDims[0] - 1;
  extent[3] = this->ImageDims[1] - 1;
  extent[5] = this->ImageDims[2] - 1;

  double pixelX = this->Len[0] / this->ImageDims[0];
  double pixelY = this->Len[1] / this->ImageDims[1];
  double pixelZ = this->Len[2] / this->ImageDims[2];
  spacing[0] = spacing[1] = spacing[2] = 1.0;
  if (pixelX > std::numeric_limits<float>::epsilon())
	{
	  spacing[1] = pixelY / pixelX;
	  spacing[2] = pixelZ / pixelX;
	}
}

int vtkMRCReader::ReadInt(char **pointer)
{
  char buffer[4];
  memcpy(buffer,*pointer,4);
  *pointer += 4;
  int *value = (int*)buffer;
#ifdef VTK_WORDS_BIGENDIAN
  if (this->LittleEndian) vtkByteSwap::Swap4LE(value);
#else
  if (!this->LittleEndian) vtkByteSwap::Swap4BE(value);
#endif

  return *(value);
}

float vtkMRCReader::ReadFloat(char **pointer)
{
  char buffer[4];
  memcpy(buffer,*pointer,4);
  *pointer += 4;
  float *value = (float*)buffer;
#ifdef VTK_WORDS_BIGENDIAN
  if (this->LittleEndian) vtkByteSwap::Swap4LE(value);
#else
  if (!this->LittleEndian) vtkByteSwap::Swap4BE(value);
#endif

  return *(value);
}

short vtkMRCReader::ReadShort(char **pointer)
{
  char buffer[2];
  memcpy(buffer,*pointer,2);
  *pointer += 2;
  short *value = (short*)buffer;
#ifdef VTK_WORDS_BIGENDIAN
  if (this->LittleEndian) vtkByteSwap::Swap2LE(value);
#else
  if (!this->LittleEndian) vtkByteSwap::Swap2BE(value);
#endif
  return *(value);
}

void vtkMRCReader::ReadVector(char **pointer, int *buffer, int items)
{
  for (int i = 0; i < items; ++i)
	{
	  buffer[i] = this->ReadInt(pointer);
	}
}

void vtkMRCReader::ReadVector(char **pointer, float *buffer, int items)
{
  for (int i = 0; i < items; ++i)
	{
	  buffer[i] = this->ReadFloat(pointer);
	}
}

void vtkMRCReader::ReadVector(char **pointer, short *buffer, int items)
{
  for (int i = 0; i < items; ++i)
	{
	  buffer[i] = this->ReadShort(pointer);
	}
}

// Template function for setting different type image scalars
template<class TArray, class TBuffer>
void SetImageScalars(vtkImageData *imageData, TBuffer *buffer, unsigned int size)
{
  TArray *pointDataArray;
  pointDataArray = TArray::New();
  pointDataArray->SetNumberOfComponents(1);
  pointDataArray->SetNumberOfValues(size);
  pointDataArray->SetArray(buffer,size,0);
  imageData->GetPointData()->SetScalars(pointDataArray);
  pointDataArray->Delete();
}

// Template function for returning array as ostream
template<class TArray>
ostream& PutArrayToStream(ostream &os, TArray *array, int size)
{
  os << "(";
  for (int i = 0; i < size - 1; ++i)
	{
	  os << array[i] << ",";
	}
  os << array[size-1];
  os << ")";
  return os;
}
