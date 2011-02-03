/*=========================================================================

  Program:   BioImageXD
  Module:    vtkLIFReader.h
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
#include "vtkUnsignedLongLongArray.h"

struct ChannelData;
struct DimensionData;

// Non supported wrapper parser syntax must be surrounded with comments BTX and ETX
//BTX
class ChannelVector;
class DimensionVector;
class ImageVector;
class TimeStampVector;
//ETX

const int MemBlockCode = 0x70;
const int TestCode = 0x2a;
const int DimIDX = 1;
const int DimIDY = 2;
const int DimIDZ = 3;
const int DimIDT = 4;
const int DimIDL = 5;
const int DimIDR = 6;

class VTK_BXD_PROCESSING_EXPORT vtkLIFReader: public vtkImageAlgorithm
{
 public:
  vtkTypeMacro(vtkLIFReader,vtkImageAlgorithm);
  static vtkLIFReader *New();
  virtual void PrintSelf(ostream&, vtkIndent);

  // Description:
  // Set file name with path to be read
  void SetFileName(const char*);

  // Description:
  // Use OpenFile to open file after SetFileName
  int OpenFile();
  void CloseFile();

  // Description:
  // Reads header of LIF file.
  // This must be done before images can be read
  int ReadLIFHeader();

  // Description:
  // Sets the current image of the object
  int SetCurrentImage(int);

  // Description:
  // Sets the current channel of the current image
  int SetCurrentChannel(int);
  void SetCurrentImageAndChannel(int,int);

  // Description:
  // Sets the current time point
  int SetCurrentTimePoint(int);

  // Description:
  // Copies already read header info from another LIFReader if filename is same
  int CopyHeaderInfo(const vtkLIFReader*);

  const char* GetFileExtensions();
  int GetImageCount();
  unsigned long long GetFileSize();
  int GetChannelCount(int);
  int GetChannelCount();
  int GetDimensionCount(int);
  int GetDimensionCount();
  unsigned int GetImageVoxelCount(int);
  unsigned int GetImageVoxelCount();
  int GetImageSlicePixelCount(int);
  int GetImageSlicePixelCount();
  int GetImageChannelResolution(int,int);
  int GetImageChannelResolution();
  double GetImageChannelMin(int,int);
  double GetImageChannelMin();
  double GetImageChannelMax(int,int);
  double GetImageChannelMax();
  const char* GetImageChannelLUTName(int,int);
  const char* GetImageChannelLUTName();
  const char* GetImageName(int);
  const char* GetCurrentImageName();
  double GetTimeInterval(int);
  double GetTimeInterval();
  vtkUnsignedLongLongArray* GetTimeStamps(int);
  vtkUnsignedLongLongArray* GetTimeStamps();
  int GetFramesPerTimePoint(int);
  int GetFramesPerTimePoint();
  int isRGB(int,int);
  int isRGB();

  vtkGetMacro(CurrentImage,int);
  vtkGetMacro(CurrentChannel,int);
  vtkGetVectorMacro(ImageDims,int,4);
  vtkGetVector3Macro(ImageVoxels,double);
  vtkGetStringMacro(FileName);

 protected:

  vtkLIFReader();
  ~vtkLIFReader();

// Protected methods
  int ParseXMLHeader(const char*, unsigned long);
  int ParseInfoHeader(vtkXMLDataElement*, int root = 1);
  void ParseImage(vtkXMLDataElement*);
  void ParseImageDescription(vtkXMLDataElement*);
  void ParseTimeStampList(vtkXMLDataElement*);
  void LoadChannelInfoToStruct(vtkXMLDataElement*, ChannelData*);
  void LoadDimensionInfoToStruct(vtkXMLDataElement*, DimensionData*);
  void InitializeAttributes();
  void Clear();
  void CalculateExtentAndSpacingAndOrigin(int*, double*, double*);
  int SetImageDimensions();
  int SetImageVoxelSizes();

  char ReadChar(ifstream*);
  int ReadInt(ifstream*);
  unsigned int ReadUnsignedInt(ifstream*);
  unsigned long long ReadUnsignedLongLong(ifstream*);

  // Pipeline methods
  int RequestInformation(vtkInformation* vtkNotUsed(request),
                         vtkInformationVector** vtkNotUsed(inputVector),
                         vtkInformationVector*);    
  int RequestUpdateExtent(vtkInformation* vtkNotUsed(request),
						  vtkInformationVector** vtkNotUsed(inputVector),
						  vtkInformationVector*);
  int RequestData(vtkInformation* vtkNotUsed(request),
                  vtkInformationVector** vtkNotUsed(inputVector),
                  vtkInformationVector*);

  unsigned long long GetTimePointOffset(int, int);

// Protected attributes
  ifstream *File;
  char *FileName;
  unsigned long long FileSize;
  int HeaderInfoRead;
  int CurrentImage;
  int CurrentChannel;
  int CurrentTimePoint;
  DimensionVector *Dimensions;
  ChannelVector *Channels;
  ImageVector *Images;
  vtkUnsignedLongLongArray *Offsets;
  vtkUnsignedLongLongArray *ImageSizes;
  int ImageDims[4];
  double ImageVoxels[3];
  int LifVersion;
  TimeStampVector *TimeStamps;

 private: // Only define operator= and copy constructor to prevent illegal use
  void operator=(const vtkLIFReader&);
  vtkLIFReader(const vtkLIFReader&);
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
  unsigned long long BytesInc; // Distance from the first channel in Bytes
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
  unsigned long long BytesInc; // Distance from the one element to the next in this dimension
  int BitInc;
};

#endif
