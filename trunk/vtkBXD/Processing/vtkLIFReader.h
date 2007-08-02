/*=========================================================================

  Program:   BioImageXD
  Module:    $RCSfile$
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

#ifndef __vtkLIFReader_h
#define __vtkLIFReader_h

#include "vtkImageAlgorithm.h"
#include "vtkBXDProcessingWin32Header.h"
#include "vtkXMLDataElement.h"
#include "vtkUnsignedIntArray.h"

typedef struct ChannelData;
typedef struct DimensionData;

// Non supported wrapper parser syntax must be surrounded with comments BTX and EXT
//BTX
class ChannelVector;
class DimensionVector;
class ImageVector;
//ETX

const int MemBlockCode = 0x70;
const int TestCode = 0x2a;
const int DimIDX = 1;
const int DimIDY = 2;
const int DimIDZ = 3;
const int DimIDT = 4;

class VTK_BXD_PROCESSING_EXPORT vtkLIFReader: public vtkImageAlgorithm
{
 public:
  vtkTypeMacro(vtkLIFReader,vtkImageAlgorithm);
  static vtkLIFReader *New();
  //virtual const char* GetClassName();
  //  virtual int isA(const char*);
  virtual void PrintSelf(ostream&, vtkIndent);
  void SetFileName(const char*);
  int OpenFile();
  void CloseFile();
  int ReadLIFHeader();

  int SetCurrentImage(int);
  int SetCurrentChannel(int);
  void SetCurrentImageAndChannel(int,int);
  int SetCurrentTimePoint(int);

  const char* GetFileExtensions();
  int GetImageCount();
  long GetFileSize();
  int GetChannelCount(int);
  int GetChannelCount();
  int GetDimensionCount(int);
  int GetDimensionCount();
  unsigned int GetImageVoxelCount(int);
  unsigned int GetImageVoxelCount();
  int GetImageSlicePixelCount(int);
  int GetImageSlicePixelCount();
  //  double* GetImageVoxelSizes(int);
  //  double* GetImageVoxelSizes();
  int SetImageVoxelSizes(int);
  int SetImageVoxelSizes();
  int* GetImageDimensions(int);
  int* GetImageDimensions();
  int SetImageDimensions(int);
  int SetImageDimensions();
  int GetImageChannelResolution(int,int);
  int GetImageChannelResolution();
  const char* GetImageChannelLUTName(int,int);
  const char* GetImageChannelLUTName();
  const char* GetImageName(int);
  const char* GetCurrentImageName();

  vtkGetMacro(CurrentImage,int);
  vtkGetMacro(CurrentChannel,int);
  vtkGetVectorMacro(Dims,int,4);
  vtkGetVector3Macro(Voxelss,double);
  vtkGetStringMacro(FileName);
  //  int IsValidLIFFile();
  //  int GetNumberOfChannels();
  void PrintData(vtkImageData*,int);
  void PrintColorData(vtkImageData*,int);

 protected:

  vtkLIFReader();
  ~vtkLIFReader();

// Protected methods
  int ParseXMLHeader(const char*, unsigned long);
  int ParseInfoHeader(vtkXMLDataElement*, int root = 1);
  void ReadImage(vtkXMLDataElement*);
  char ReadChar(ifstream*);
  int ReadInt(ifstream*);
  unsigned int ReadUnsignedInt(ifstream*);
  void LoadChannelInfoToStruct(vtkXMLDataElement*, ChannelData*);
  void LoadDimensionInfoToStruct(vtkXMLDataElement*, DimensionData*);
  void Clear();
  void CalculateExtentAndSpacingAndOrigin(int*, double*, double*);

  // Pipeline methods
  int RequestInformation(vtkInformation* vtkNotUsed(request),
                         vtkInformationVector** vtkNotUsed(inputVector),
                         vtkInformationVector*);    
  int RequestUpdateExtent(vtkInformation*, vtkInformationVector**,vtkInformationVector*);
  int RequestData(vtkInformation* vtkNotUsed(request),
                  vtkInformationVector** vtkNotUsed(inputVector),
                  vtkInformationVector*);

  unsigned int GetTimePointOffset(int, int);

// Protected attributes
  ifstream *File;
  char *FileName;
  long FileSize;
  int HeaderInfoRead;
  int CurrentImage;
  int CurrentChannel;
  int CurrentTimePoint;
  DimensionVector *Dimensions;
  ChannelVector *Channels;
  ImageVector *Images;
  vtkUnsignedIntArray *Offsets;
  vtkUnsignedIntArray *ImageSizes;
  int Dims[4];
  double Voxelss[3];
};

// Struct of channel data
struct ChannelData
{
  int DataType; // 0 Integer, 1 Float
  int ChannelTag; // 0 Gray value, 1 Red, 2 Green, 3 Blue
  int Resolution; // Bits per pixel
  const char *NameOfMeasuredQuantity;
  double Min;
  double Max;
  const char *Unit;
  const char *LUTName;
  int IsLUTInverted; // 0 Normal LUT, 1 Inverted Order
  int BytesInc; // Distance from the first channel in Bytes
  int BitInc;
};

// Struct of dimension data 
struct DimensionData
{
  int DimID; // 0 Not valid, 1 X, 2 Y, 3 Z, 4 T, 5 Lambda, 6 Rotation, 7 XT Slices, 8 T Slices
  int NumberOfElements; // Number of elements in this dimension
  double Origin; // Physical position of the first element (left pixel side)
  double Length; // Physical length from the first left pixel side to the last left pixel side
  const char *Unit; // Physical unit
  int BytesInc; // Distance from the first channel in Bytes
  int BitInc;
  };

#endif
