/*=========================================================================

  Program:   Visualization Toolkit
  Module:    $RCSfile: vtkTIFFReader.h,v $
  Language:  C++
  Date:      $Date: 2003/11/04 21:26:04 $
  Version:   $Revision: 1.28 $


Copyright (c) 1993-2001 Ken Martin, Will Schroeder, Bill Lorensen 
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

 * Redistributions of source code must retain the above copyright notice,
   this list of conditions and the following disclaimer.

 * Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

 * Neither name of Ken Martin, Will Schroeder, or Bill Lorensen nor the names
   of any contributors may be used to endorse or promote products derived
   from this software without specific prior written permission.

 * Modified source versions must be plainly marked as such, and must not be
   misrepresented as being the original software.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS ``AS IS''
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHORS OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

=========================================================================*/
// .NAME vtkLSMReader - read LSM files
// .SECTION Description
// vtkLSMReader is a source object that reads LSM files.
// It should be able to read most any LSM file
//
// .SECTION See Also
// vtkLSMWriter

#ifndef __vtkLSMReader_h
#define __vtkLSMReader_h

#include "vtkImageSource.h"
#include "vtkIntArray.h"
#include "vtkUnsignedIntArray.h"
#include "vtkDoubleArray.h"
#include "vtkUnsignedShortArray.h"
#include "vtkUnsignedCharArray.h"

#define TIFF_BYTE 1
#define TIFF_ASCII 2
#define TIFF_SHORT 3
#define TIFF_LONG 4
#define TIFF_RATIONAL 5

#define LSM_MAGIC_NUMBER 42

#define LSM_COMPRESSED 5

#define VTK_FILE_BYTE_ORDER_BIG_ENDIAN 0
#define VTK_FILE_BYTE_ORDER_LITTLE_ENDIAN 1


class VTK_IO_EXPORT vtkLSMReader : public vtkImageSource
{
public:

  static vtkLSMReader *New();
  vtkTypeMacro(vtkLSMReader,vtkImageSource);
  virtual void PrintSelf(ostream& os, vtkIndent indent);

  // Description:
  // Get the file extensions for this format.
  // Returns a string with a space separated list of extensions in 
  // the format .extension
  const char* GetFileExtensions()
    {
    return ".lsm .LSM";
    }

  int GetHeaderIdentifier();
  int IsValidLSMFile();
  int IsCompressed();
  int GetNumberOfTimePoints();
  int GetNumberOfChannels();
  int OpenFile();
  void Print();
  int GetChannelColorComponent(int,int);
  char* GetChannelName(int);
  void SetFileName(const char *);
  void ExecuteInformation();
  void SetUpdateTimePoint(int);
  void SetUpdateChannel(int);

  void SetDataByteOrderToBigEndian();
  void SetDataByteOrderToLittleEndian();
  void SetDataByteOrder(int);
  int GetDataByteOrder();
  const char *GetDataByteOrderAsString();

  // Description:
  // Set/Get the byte swapping to explicitly swap the bytes of a file.
  vtkSetMacro(SwapBytes,int);
  virtual int GetSwapBytes() {return this->SwapBytes;}
  vtkBooleanMacro(SwapBytes,int);

  vtkGetStringMacro(FileName);
  vtkGetVector3Macro(VoxelSizes,double);
  vtkGetVectorMacro(Dimensions,int,5);
  vtkGetVectorMacro(NumberOfIntensityValues,int,4);
  vtkGetMacro(Identifier,unsigned short);
  vtkGetMacro(NewSubFileType,unsigned int);
  vtkGetMacro(Compression,unsigned int);
  vtkGetMacro(SamplesPerPixel,unsigned int);
  vtkGetMacro(ScanType,unsigned short);
  vtkGetMacro(DataType,int);
  vtkGetObjectMacro(TimeStampInformation,vtkDoubleArray);
  vtkGetObjectMacro(ChannelColors,vtkIntArray);

  vtkImageData* GetTimePointOutput(int,int);

protected:

  vtkLSMReader();
  ~vtkLSMReader();

  int TIFF_BYTES(unsigned short);
  int BYTES_BY_DATA_TYPE(int);
  void ClearFileName();
  void Clean();
  unsigned long ReadImageDirectory(ifstream *,unsigned long);
  int AllocateChannelNames(int);
  int SetChannelName(const char *,int);
  int ClearChannelNames();
  int FindChannelNameStart(const char *, int);
  int ReadChannelName(const char *, int, char *);
  int ReadChannelColorsAndNames(ifstream *,unsigned long);
  int ReadTimeStampInformation(ifstream *,unsigned long);
  int ReadLSMSpecificInfo(ifstream *,unsigned long);
  int AnalyzeTag(ifstream *,unsigned long);
  int NeedToReadHeaderInformation();
  void NeedToReadHeaderInformationOn();
  void NeedToReadHeaderInformationOff();
  unsigned long SeekFile(int);
  unsigned long GetOffsetToImage(int, int);
  ifstream *GetFile();

  void ExecuteData(vtkDataObject *out);
  void CalculateExtentAndSpacing(int extent[6],double spacing[3]);
  //  void DecodeHorizontalDifferencing(unsigned char *,int);
  //  void DecodeLZWCompression(unsigned  char *,int);
  //  unsigned char *decode_string(unsigned char *buffer,unsigned int code);
  //  unsigned int input_code(char *input);

  int SwapBytes;

  int UpdateExtent[5];
  unsigned long OffsetToLastAccessedImage;
  int NumberOfLastAccessedImage;
  int FileNameChanged;
  ifstream *File;
  char *FileName;
  double VoxelSizes[3];
  int Dimensions[5];// x,y,z,time,channels
  int NumberOfIntensityValues[4];
  unsigned short Identifier;
  unsigned int NewSubFileType;
  vtkUnsignedShortArray *BitsPerSample;
  unsigned int Compression;
  vtkUnsignedIntArray *StripOffset;
  unsigned int SamplesPerPixel;
  vtkUnsignedIntArray *StripByteCount;
  unsigned int LSMSpecificInfoOffset;
  unsigned short PhotometricInterpretation;
  unsigned long ColorMapOffset;
  unsigned short PlanarConfiguration;
  unsigned short Predictor;
  unsigned short ScanType;
  int DataType;
  unsigned long ChannelInfoOffset;
  vtkIntArray *ChannelColors;
  char **ChannelNames;
  vtkDoubleArray *TimeStampInformation;

  unsigned char CharPointerToUnsignedChar(char *);
  int CharPointerToInt(char *);
  unsigned int CharPointerToUnsignedInt(char *);
  short CharPointerToShort(char *);
  unsigned short CharPointerToUnsignedShort(char *);
  double CharPointerToDouble(char *);

  int ReadInt(ifstream *,unsigned long *);
  unsigned int ReadUnsignedInt(ifstream *,unsigned long *);
  short ReadShort(ifstream *,unsigned long *);
  unsigned short ReadUnsignedShort(ifstream *,unsigned long *);
  double ReadDouble(ifstream *,unsigned long *);
  int ReadFile(ifstream *,unsigned long *,int,char *);
  int ReadData(ifstream *,unsigned long *,int,char *);


private:
  vtkLSMReader(const vtkLSMReader&);  // Not implemented.
  void operator=(const vtkLSMReader&);  // Not implemented.
};
#endif
