/*=========================================================================

  Program:   Visualization Toolkit
  Module:    $RCSfile: vtkLSMReader.cxx,v $
  Language:  C++
  Date:      $Date: 2003/08/22 14:46:02 $
  Version:   $Revision: 1.39 $


Copyright (c) 2004, 2005 Heikki Uuksulainen
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
#include "vtkLSMReader.h"
#include "vtkObjectFactory.h"
#include "vtkImageData.h"
#include "vtkSource.h"
#include "vtkPointData.h"
#include "vtkByteSwap.h"

vtkStandardNewMacro(vtkLSMReader);

vtkLSMReader::vtkLSMReader()
{
  this->Clean();
}

vtkLSMReader::~vtkLSMReader()
{
  this->ClearFileName();
  this->ClearChannelNames();
  this->ChannelColors->Delete();
  this->BitsPerSample->Delete();
  this->StripOffset->Delete();
  this->StripByteCount->Delete();
}

void vtkLSMReader::ClearFileName()
{
  if (this->File)
    {
    this->File->close();
    delete this->File;
    this->File = NULL;
    }
  
  if (this->FileName)
    {
    delete [] this->FileName;
    this->FileName = NULL;
    }
}
//----------------------------------------------------------------------------
// This function sets the name of the file. 
void vtkLSMReader::SetFileName(const char *name)
{
  if ( this->FileName && name && (!strcmp(this->FileName,name)))
    {
    return;
    }
  if (!name && !this->FileName)
    {
    return;
    }
  if (this->FileName)
    {
    delete [] this->FileName;
    }
  if (name)
    {
    this->FileName = new char[strlen(name) + 1];
    strcpy(this->FileName, name);
    }
  else
    {
    this->FileName = NULL;
    }
  this->NeedToReadHeaderInformationOn();
  this->Modified();
}


void vtkLSMReader::Clean()
{
  this->UpdateExtent[0] = this->UpdateExtent[1] = this->UpdateExtent[2] = this->UpdateExtent[4] = 0;
  this->UpdateExtent[3] = 0;
  this->OffsetToLastAccessedImage = 0;
  this->NumberOfLastAccessedImage = 0;
  this->FileNameChanged = 0;
  this->FileName = NULL;
  this->File = NULL;
  this->VoxelSizes[0] = this->VoxelSizes[1] = this->VoxelSizes[2] = 0.0;
  this->Identifier = 0;
  this->Dimensions[0] = this->Dimensions[1] = this->Dimensions[2] = this->Dimensions[3] = this->Dimensions[4] = 0;
  this->NewSubFileType = 0;
  this->BitsPerSample = vtkUnsignedShortArray::New();
  this->BitsPerSample->SetNumberOfTuples(4);
  this->BitsPerSample->SetNumberOfComponents(1);  
  this->Compression = 0;
  this->StripOffset = vtkUnsignedIntArray::New();
  this->StripOffset->SetNumberOfTuples(4);
  this->StripOffset->SetNumberOfComponents(1);  
  this->SamplesPerPixel = 0;
  this->StripByteCount = vtkUnsignedIntArray::New();
  this->StripByteCount->SetNumberOfTuples(4);
  this->StripByteCount->SetNumberOfComponents(1);  
  this->Predictor = 0;
  this->PhotometricInterpretation = 0;
  this->PlanarConfiguration = 0;
  this->ColorMapOffset = 0;
  this->LSMSpecificInfoOffset = 0;
  this->NumberOfIntensityValues[0] = this->NumberOfIntensityValues[1] = 
  this->NumberOfIntensityValues[2] = this->NumberOfIntensityValues[3] = 0;
  this->ScanType = 0;
  this->DataType = 0;
  this->ChannelColors = vtkIntArray::New();
  this->ChannelNames = NULL;
  this->TimeStampInformation = vtkDoubleArray::New();
}

int vtkLSMReader::OpenFile()
{
  if (!this->FileName)
    {
    vtkErrorMacro(<<"FileName must be specified.");
    return 0;
    }

  // Close file from any previous image
  if (this->File)
    {
    this->File->close();
    delete this->File;
    this->File = NULL;
    }
  
  // Open the new file
#ifdef _WIN32
  this->File = new ifstream(this->FileName, ios::in | ios::binary);
#else
  this->File = new ifstream(this->FileName, ios::in);
#endif
  if (! this->File || this->File->fail())
    {
    vtkErrorMacro(<< "OpenFile: Could not open file " <<this->FileName);
    return 0;
    }
  return 1;
}


void vtkLSMReader::SetDataByteOrderToBigEndian()
{
#ifndef VTK_WORDS_BIGENDIAN
  this->SwapBytesOn();
#else
  this->SwapBytesOff();
#endif
}

void vtkLSMReader::SetDataByteOrderToLittleEndian()
{
#ifdef VTK_WORDS_BIGENDIAN
  this->SwapBytesOn();
#else
  this->SwapBytesOff();
#endif
}

void vtkLSMReader::SetDataByteOrder(int byteOrder)
{
  if ( byteOrder == VTK_FILE_BYTE_ORDER_BIG_ENDIAN )
    {
    this->SetDataByteOrderToBigEndian();
    }
  else
    {
    this->SetDataByteOrderToLittleEndian();
    }
}

int vtkLSMReader::GetDataByteOrder()
{
#ifdef VTK_WORDS_BIGENDIAN
  if ( this->SwapBytes )
    {
    return VTK_FILE_BYTE_ORDER_LITTLE_ENDIAN;
    }
  else
    {
    return VTK_FILE_BYTE_ORDER_BIG_ENDIAN;
    }
#else
  if ( this->SwapBytes )
    {
    return VTK_FILE_BYTE_ORDER_BIG_ENDIAN;
    }
  else
    {
    return VTK_FILE_BYTE_ORDER_LITTLE_ENDIAN;
    }
#endif
}

const char *vtkLSMReader::GetDataByteOrderAsString()
{
#ifdef VTK_WORDS_BIGENDIAN
  if ( this->SwapBytes )
    {
    return "LittleEndian";
    }
  else
    {
    return "BigEndian";
    }
#else
  if ( this->SwapBytes )
    {
    return "BigEndian";
    }
  else
    {
    return "LittleEndian";
    }
#endif
}


char* vtkLSMReader::GetChannelName(int chNum)
{
  if(!this->ChannelNames || chNum < 0 || chNum > this->GetNumberOfChannels()-1)
    {
    vtkDebugMacro(<<"GetChannelName: Illegal channel index!");
    return "";
    }
  return this->ChannelNames[chNum];
}

int vtkLSMReader::ClearChannelNames()
{
  if(!this->ChannelNames || this->GetNumberOfChannels() < 1)
    {
    return 0;
    }
  for(int i=0;i<this->GetNumberOfChannels();i++)
    {
    delete [] this->ChannelNames[i];
    }
  delete [] this->ChannelNames;

  return 0;
}

int vtkLSMReader::AllocateChannelNames(int chNum)
{
  this->ClearChannelNames();
  this->ChannelNames = new char*[chNum];
  if(!this->ChannelNames)
    {
    vtkErrorMacro(<<"Could not allocate memory for channel name table!");
    return 1;
    }
  for(int i=0;i<chNum;i++)
    {
    this->ChannelNames[i] = NULL;
    }
  return 0;
}

int vtkLSMReader::SetChannelName(const char *chName, int chNum)
{
  char *name;
  int length;
  if(!chName || chNum > this->GetNumberOfChannels())
    {
    return 0;
    }
  if(!this->ChannelNames)
    {
    this->AllocateChannelNames(this->GetNumberOfChannels());
    }
  length = strlen(chName);
  name = new char[length+1];
  if(!name)
    {
    vtkErrorMacro(<<"Could not allocate memory for channel name");
    return 1;
    }
  strncpy(name,chName,length);
  name[length] = 0;
  this->ChannelNames[chNum] = name;
  return 0;
}

int vtkLSMReader::FindChannelNameStart(const char *nameBuff, int length)
{
  int i;
  char ch;
  for(i=0;i<length;i++)
    {
    ch = *(nameBuff+i);
    if(ch > 32)
      {
      break;
      }
    }
  if(i >= length)
    {
    vtkWarningMacro(<<"Start of the channel name may not be found!");
    }
  return i;
}

int vtkLSMReader::ReadChannelName(const char *nameBuff, int length, char *buffer)
{
  int i;
  char component;
  for(i=0;i<length;i++)
    {
    component = *(nameBuff+i);
    *(buffer+i) = component;
    if(component == 0)
      {
      break;
      }
    }
  return i;
}

int vtkLSMReader::ReadChannelColorsAndNames(ifstream *f,unsigned long start)
{
  int colNum,nameNum,sizeOfStructure,sizeOfNames,nameLength, nameSkip;
  unsigned long colorOffset,nameOffset,pos;
  char *nameBuff,*colorBuff,*name,*tempBuff;
  unsigned char component;

  colorBuff = new char[4];

  pos = start;
  sizeOfStructure = this->ReadInt(f,&pos);
  colNum = this->ReadInt(f,&pos);
  nameNum = this->ReadInt(f,&pos);
  sizeOfNames = sizeOfStructure - ( (10*4) + (colNum*4) );

  nameBuff = new char[sizeOfNames];
  name = new char[sizeOfNames];

  if(colNum != this->GetNumberOfChannels())
    {
    vtkWarningMacro(<<"Number of channel colors is not same as number of channels!");
    }
  if(nameNum != this->GetNumberOfChannels())
    {
    vtkWarningMacro(<<"Number of channel names is not same as number of channels!");
    }

  colorOffset = this->ReadInt(f,&pos) + start;
  nameOffset = this->ReadInt(f,&pos) + start;

  this->ChannelColors->Reset();
  this->ChannelColors->SetNumberOfValues(3*colNum);
  this->ChannelColors->SetNumberOfComponents(3);

  for(int j=0;j<colNum;j++)
    {
    this->ReadFile(f,&colorOffset,4,colorBuff);
    for(int i=0;i<3;i++)
      {
      component = this->CharPointerToUnsignedChar(colorBuff+i);
      this->ChannelColors->SetValue(i+((colNum+1)*j),component);
      }
    }

  this->ReadFile(f,&nameOffset,sizeOfNames,nameBuff);

  nameLength = nameSkip = 0;
  tempBuff = nameBuff;
  for(int i=0;i<nameNum;i++)
    {
    nameSkip = this->FindChannelNameStart(tempBuff,sizeOfNames-nameSkip);
    nameLength = this->ReadChannelName(tempBuff+nameSkip,sizeOfNames-nameSkip,name);
    tempBuff += nameSkip + nameLength;
    this->SetChannelName(name,i);
    }
  delete [] nameBuff;
  delete [] name;
  delete [] colorBuff;

  return 0;
}

int vtkLSMReader::ReadTimeStampInformation(ifstream *f,unsigned long offset)
{
  int numOffStamps = 0;
  if( offset == 0 ) // position is 0 for non-timeseries files!
    {
    return 0;
    }
  offset += 4;
  numOffStamps = this->ReadInt(f,&offset);
  if(numOffStamps != this->GetNumberOfTimePoints())
    {
    vtkWarningMacro(<<"Number of time stamps does not correspond to the number off time points!");
    }
  this->TimeStampInformation->Reset();
  this->TimeStampInformation->SetNumberOfTuples(numOffStamps);
  this->TimeStampInformation->SetNumberOfComponents(1);
  for(int i=0;i<numOffStamps;i++)
    {
    this->TimeStampInformation->SetValue(i,this->ReadDouble(f,&offset));
    }
  return 0;
}

int vtkLSMReader::ReadLSMSpecificInfo(ifstream *f,unsigned long pos)
{
  unsigned long offset;
  pos += 2 * 4; // skip over the start of the LSMInfo

  this->NumberOfIntensityValues[0] = this->ReadInt(f,&pos); 
  this->Dimensions[0] = this->NumberOfIntensityValues[0];
  this->NumberOfIntensityValues[1] = this->ReadInt(f,&pos); 
  this->Dimensions[1] = this->NumberOfIntensityValues[1];
  this->NumberOfIntensityValues[2] = this->ReadInt(f,&pos); 
  this->Dimensions[2] = this->NumberOfIntensityValues[2];

  this->Dimensions[4] = this->ReadInt(f,&pos); 

  this->NumberOfIntensityValues[3] = this->ReadInt(f,&pos);
  this->Dimensions[3] = this->NumberOfIntensityValues[3];

  this->DataType = this->ReadInt(f,&pos);

  pos += 2 * 4;

  this->VoxelSizes[0] = this->ReadDouble(f,&pos);
  this->VoxelSizes[1] = this->ReadDouble(f,&pos);
  this->VoxelSizes[2] = this->ReadDouble(f,&pos);

  pos += 3*8;

  this->ScanType = this->ReadShort(f,&pos);

  pos += 1*2 + 4*4;// + 1*8 + 3*4;

  this->ChannelInfoOffset = this->ReadUnsignedInt(f,&pos);

  this->ReadChannelColorsAndNames(f,this->ChannelInfoOffset);

  pos += 1*8 + 3*4;

  offset = this->ReadUnsignedInt(f,&pos);
  this->ReadTimeStampInformation(f,offset);

  
  return 1;
}

int vtkLSMReader::AnalyzeTag(ifstream *f,unsigned long startPos)
{
  unsigned short type,length,tag;
  unsigned long readSize;
  int value, dataSize,i;
  char tempValue[4];
  char *actualValue = NULL;

  tag = this->ReadUnsignedShort(f,&startPos);
  type = this->ReadUnsignedShort(f,&startPos);
  length = this->ReadUnsignedInt(f,&startPos);
  this->ReadFile(f,&startPos,4,tempValue);
  value = this->CharPointerToUnsignedInt(tempValue);

  // if there is more than 4 bytes in value, 
  // value is an offset to the actual data
  dataSize = this->TIFF_BYTES(type);
  readSize = dataSize*length;
  if(readSize > 4 && tag != 34412)
    {
    actualValue = new char[readSize];
    startPos = value;
    if( !this->ReadFile(f,&startPos,readSize,actualValue) ) return 0;
    }
  else
    {
      actualValue = new char[4];
      //strcpy(actualValue,tempValue);
      // stupid..
      for(int o=0;o<4;o++)actualValue[o] = tempValue[o];
    }
  switch(tag)
    {
    case 254: 
      this->NewSubFileType = this->CharPointerToUnsignedInt(actualValue);
      break;
    case 256: 
      //this->Dimensions[0] = this->CharPointerToUnsignedInt(actualValue);
      //this->Dimensions[0] = value;
      break;
    case 257: 
      //this->Dimensions[1] = this->CharPointerToUnsignedInt(actualValue);
      //this->Dimensions[1] = value;
      break;
    case 258: 
      this->BitsPerSample->SetNumberOfValues(length);
      for(i=0;i<length;i++)
	{
	this->BitsPerSample->SetValue(i,this->CharPointerToUnsignedShort(actualValue + (this->TIFF_BYTES(TIFF_SHORT)*i)));
	}
	break;
    case 259: 
      this->Compression = this->CharPointerToUnsignedShort(actualValue);
      break;
    case 262:
      this->PhotometricInterpretation = this->CharPointerToUnsignedShort(actualValue);
      break;
    case 273: 
      this->StripOffset->SetNumberOfValues(length);      
      for(i=0;i<length;i++)
	{
	this->StripOffset->SetValue(i,this->CharPointerToUnsignedInt(actualValue + (this->TIFF_BYTES(TIFF_LONG)*i)));
	}
      break;
    case 277: 
      this->SamplesPerPixel = this->CharPointerToUnsignedInt(actualValue);
      break;
    case 279: 
      this->StripByteCount->SetNumberOfValues(length);
      for(i=0;i<length;i++)
	{
	this->StripByteCount->SetValue(i,this->CharPointerToUnsignedInt(actualValue + (this->TIFF_BYTES(TIFF_LONG)*i)));
	}
      break;
    case 284: 
      this->PlanarConfiguration = this->CharPointerToUnsignedShort(actualValue);
      break;
    case 317: 
      this->Predictor = this->CharPointerToUnsignedShort(actualValue);
      break;
    case 320: 
      //this->ColorMapOffset = this->CharPointerToUnsignedInt(actualValue);
      break;
    case 34412: 
      this->LSMSpecificInfoOffset = this->CharPointerToUnsignedInt(actualValue);
      break;
    }
  if(actualValue) 
    {
    delete [] actualValue;
    }
  return 0;
}


/*------------------------------------------------------------------------------------------*/

int vtkLSMReader::GetHeaderIdentifier()
{  
  return this->Identifier;
}

int vtkLSMReader::IsValidLSMFile()
{
  if(this->GetHeaderIdentifier() == LSM_MAGIC_NUMBER) return 1;
  return 0;
}

int vtkLSMReader::IsCompressed()
{
  return (this->Compression == LSM_COMPRESSED ? 1 : 0);
}

int vtkLSMReader::GetNumberOfTimePoints()
{
  return this->Dimensions[3];
}

int vtkLSMReader::GetNumberOfChannels()
{
  return this->Dimensions[4];
}

unsigned long vtkLSMReader::GetOffsetToImage(int slice, int timepoint)
{
  return this->SeekFile(slice+(timepoint*this->Dimensions[2]));
}

unsigned long vtkLSMReader::SeekFile(int image)
{
  unsigned long offset = 4, finalOffset;
  int readSize = 4,i=0;
  unsigned short numberOfTags;  
  int imageCount = image+1;

  if(this->OffsetToLastAccessedImage && (this->NumberOfLastAccessedImage < image))
    {
    offset = this->OffsetToLastAccessedImage;
    imageCount = image - this->NumberOfLastAccessedImage;
    }
  else
    {
    offset = (unsigned long)this->ReadInt(this->GetFile(),&offset);
    }

  offset = this->ReadImageDirectory(this->GetFile(),offset);
  do
    {
    // we count only image directories and not thumbnail images
    if(this->NewSubFileType == 0) 
      {
      i++;
      }
    finalOffset = offset;
    offset = this->ReadImageDirectory(this->GetFile(),offset);
    }while(i<imageCount && offset != 0);

  this->OffsetToLastAccessedImage = finalOffset;
  this->NumberOfLastAccessedImage = image;

  return finalOffset;
}

unsigned long vtkLSMReader::ReadImageDirectory(ifstream *f,unsigned long offset)
{
  unsigned short numberOfTags=0;
  unsigned long nextOffset = offset;

  numberOfTags = this->ReadUnsignedShort(f,&offset);
  for(int i=0;i<numberOfTags;i++)
    {
    this->AnalyzeTag(f,offset);
    if(this->NewSubFileType == 1) break; //thumbnail image
    offset = offset + 12;
    }
  nextOffset += 2 + numberOfTags * 12;
  return this->ReadUnsignedInt(f,&nextOffset);
}

/*
void vtkLSMReader::DecodeHorizontalDifferencing(unsigned char *buffer, int size)
{
  for(int i=1;i<size;i++)
    {
      //printf("%d",*(buffer+i));
      *(buffer+i) = *(buffer+i) + *(buffer+i-1);
    }
  printf("\n");
}
*/


//----------------------------------------------------------------------------
// Convert to Imaging API
void vtkLSMReader::ExecuteData(vtkDataObject *output)
{
  unsigned long offset, imageOffset;;
  unsigned char *buf, *tempBuf;
  int size,readSize,numberOfPix,timepoint,channel;
  time_t start, end;
  
  vtkDebugMacro(<<"Executing data.");

  vtkImageData *data = this->GetOutput();

  data->SetExtent(data->GetWholeExtent());
  data->SetUpdateExtent(data->GetWholeExtent());

  data->AllocateScalars();

  if(!this->Identifier)
    {
    vtkDebugMacro(<<"Can not execute data since information has not been executed!");
    return;
    }

  // if given time point or channel index is bigger than maximum,
  // we use maximum
  timepoint = (this->UpdateExtent[3]>this->GetNumberOfTimePoints()-1?this->GetNumberOfTimePoints()-1:this->UpdateExtent[3]);
  channel = (this->UpdateExtent[4]>this->GetNumberOfChannels()-1?this->GetNumberOfChannels()-1:this->UpdateExtent[4]);

  numberOfPix = this->Dimensions[0]*this->Dimensions[1]*this->Dimensions[2];
  size = numberOfPix*this->BYTES_BY_DATA_TYPE(this->DataType);

  // this buffer will be deleted by the vtkXXXArray when the array is destroyed.
  buf = new unsigned char[size];
  tempBuf = buf;

  start = time (NULL);
  for(int i=0;i<this->Dimensions[2];i++)
  //for(int i=0;i<1;i++)
    {
    imageOffset = this->GetOffsetToImage(i,timepoint);
    this->ReadImageDirectory(this->GetFile(),imageOffset);
    offset = this->StripOffset->GetValue(channel);
    readSize = this->StripByteCount->GetValue(channel);
    this->ReadFile(this->GetFile(),&offset,readSize,(char *)tempBuf);
      
    /*
    if(this->IsCompressed())
      {
      this->DecodeLZWCompression(tempBuf,readSize);
      //this->DecodeHorizontalDifferencing(tempBuf,readSize);
      }
    */
    tempBuf += readSize;
    }
  end = time (NULL);

  vtkDebugMacro(<<"Dataset generation time: "<<end-start);


  vtkUnsignedCharArray *uscarray;
  vtkUnsignedShortArray *ussarray;
  if(this->BYTES_BY_DATA_TYPE(this->DataType) > 1)
    {
    ussarray = vtkUnsignedShortArray::New();
    ussarray->SetNumberOfComponents(1);
    ussarray->SetNumberOfValues(numberOfPix);
      
    ussarray->SetArray((unsigned short *)buf, numberOfPix, 0);
    data->GetPointData()->SetScalars(ussarray);
    
    ussarray->Delete();     
    }
  else
    {
    uscarray = vtkUnsignedCharArray::New();
    uscarray->SetNumberOfComponents(1);
    uscarray->SetNumberOfValues(numberOfPix);
    
    uscarray->SetArray(buf, numberOfPix, 0);
    data->GetPointData()->SetScalars(uscarray);
    
    uscarray->Delete();     
    }
  
  vtkDebugMacro(<<"Data executed.");
}

void vtkLSMReader::ExecuteInformation()
{
  unsigned long startPos;
  unsigned int imageDirOffset;
  int extent[6];
  double spacing[3];

  char buf[12];

  this->SetDataByteOrderToLittleEndian();

  if(!this->NeedToReadHeaderInformation())
    {
    vtkDebugMacro(<<"Don't need to read header information");
    return;
    }
  vtkDebugMacro(<<"Executing information.");

  if(!this->OpenFile())
    {
    this->Identifier = 0;
    return;
    }

  startPos = 2;  // header identifier

  this->Identifier = this->ReadUnsignedShort(this->GetFile(),&startPos);

  if(!this->IsValidLSMFile())
    {
    vtkErrorMacro("Given file is not a valid LSM-file.");
    return;
    }
  
  imageDirOffset = this->ReadUnsignedInt(this->GetFile(),&startPos);

  // get information from the first image directory
  this->ReadImageDirectory(this->GetFile(),imageDirOffset);

  if(this->LSMSpecificInfoOffset)
    {
      ReadLSMSpecificInfo(this->GetFile(),(unsigned long)this->LSMSpecificInfoOffset);
    }
  else
    {
      vtkErrorMacro("Did not found LSM specific info!");
      return;
    }
  if( !(this->ScanType == 6 || this->ScanType == 0) )
    {
      vtkErrorMacro("Sorry! Your LSM-file must be of type 6 LSM-file (time series x-y-z) or type 0 (normal x-y-z). Type of this file is " <<this->ScanType);
      return;
    }
  
  vtkDebugMacro(<<"Executing information: first directory has been read.");

  if(this->IsCompressed())
    {
      vtkErrorMacro("Can't handle compressed data!");
      return;
    }

  this->SetNumberOfOutputs(1);  
  this->CalculateExtentAndSpacing(extent,spacing);
  this->GetOutput()->SetWholeExtent(extent);
  this->GetOutput()->SetUpdateExtent(this->GetOutput()->GetWholeExtent());
  this->GetOutput()->SetSpacing(spacing[0],spacing[1],spacing[2]);  
  this->GetOutput()->SetNumberOfScalarComponents(1);
  if(this->DataType > 1)
    {
    this->GetOutput()->SetScalarType(VTK_UNSIGNED_SHORT);
    }
  else
    {
    this->GetOutput()->SetScalarType(VTK_UNSIGNED_CHAR);
    }

  this->NeedToReadHeaderInformationOff();
  vtkDebugMacro(<<"Executing information: executed.");
}

void vtkLSMReader::CalculateExtentAndSpacing(int extent[6],double spacing[3])
{
  
  extent[0] = extent[2] = extent[4] = 0;
  extent[1] = this->Dimensions[0]-1;
  extent[3] = this->Dimensions[1]-1;
  extent[5] = this->Dimensions[2]-1;

  spacing[0] = 1;
  spacing[1] = this->VoxelSizes[1]/this->VoxelSizes[0];
  spacing[2] = this->VoxelSizes[2]/this->VoxelSizes[0];
}

//----------------------------------------------------------------------------

int vtkLSMReader::GetChannelColorComponent(int ch, int component)
{
  if(ch < 0 || ch > this->GetNumberOfChannels()-1 || component < 0 || component > 2)
    {
    return 0;
    }
  return *(this->ChannelColors->GetPointer((ch*3) + component));
}

vtkImageData* vtkLSMReader:: GetTimePointOutput(int timepoint, int channel)
{
  this->SetUpdateTimePoint(timepoint);
  this->SetUpdateChannel(channel);
  return this->GetOutput();
}

void vtkLSMReader::SetUpdateTimePoint(int timepoint)
{
  if(timepoint < 0 || timepoint == this->UpdateExtent[3]) 
    {
    return;
    }
  this->UpdateExtent[3] = timepoint;
  this->Modified();
}

void vtkLSMReader::SetUpdateChannel(int ch)
{
  if(ch < 0 || ch == this->UpdateExtent[4])
    {
    return;
    }
  this->UpdateExtent[4] = ch;
  this->Modified();
}

void vtkLSMReader::NeedToReadHeaderInformationOn()
{
  this->FileNameChanged = 1;
}

void vtkLSMReader::NeedToReadHeaderInformationOff()
{
  this->FileNameChanged = 0;
}

int vtkLSMReader::NeedToReadHeaderInformation()
{
  return this->FileNameChanged;
}

ifstream *vtkLSMReader::GetFile()
{
  return this->File;
}

int vtkLSMReader::BYTES_BY_DATA_TYPE(int type)
{
  int bytes = 1;
  switch(type)
    {
    case(1): 
      return 1;
    case(2):
      return 2;
    case(5):
      return 4;
    }
  return bytes;
}

int vtkLSMReader::TIFF_BYTES(unsigned short type)
{
  int bytes = 1;
  switch(type)
    {
    case(TIFF_BYTE): 
      return 1;
    case(TIFF_ASCII):
    case(TIFF_SHORT): 
      return 2;
    case(TIFF_LONG):
    case(TIFF_RATIONAL):
      return 4;
    }
  return bytes;
}

unsigned char vtkLSMReader::CharPointerToUnsignedChar(char *buf)
{
  return *((unsigned char*)(buf));
}

int vtkLSMReader::CharPointerToInt(char *buf)
{
  return *((int*)(buf));
}

unsigned int vtkLSMReader::CharPointerToUnsignedInt(char *buf)
{
  return *((unsigned int*)(buf));
}

short vtkLSMReader::CharPointerToShort(char *buf)
{
  return *((short*)(buf));
}

unsigned short vtkLSMReader::CharPointerToUnsignedShort(char *buf)
{
  return *((unsigned short*)(buf));
}

double vtkLSMReader::CharPointerToDouble(char *buf)
{
  return *((double*)(buf));
}

int vtkLSMReader::ReadInt(ifstream *f,unsigned long *pos)
{
  char buff[4];
  this->ReadFile(f,pos,4,buff);
  return CharPointerToInt(buff);
}

unsigned int vtkLSMReader::ReadUnsignedInt(ifstream *f,unsigned long *pos)
{
  char buff[4];
  this->ReadFile(f,pos,4,buff);
  return this->CharPointerToUnsignedInt(buff);
}

short vtkLSMReader::ReadShort(ifstream *f,unsigned long *pos)
{
  char buff[2];
  this->ReadFile(f,pos,2,buff);
  return this->CharPointerToShort(buff);
}

unsigned short vtkLSMReader::ReadUnsignedShort(ifstream *f,unsigned long *pos)
{
  char buff[2];
  this->ReadFile(f,pos,2,buff);
  /*
  if(this->GetSwapBytes())
    {
    vtkByteSwap::Swap2BE((unsigned short *)buff);
    }
  */
  return this->CharPointerToUnsignedShort(buff);
}

double vtkLSMReader::ReadDouble(ifstream *f,unsigned long *pos)
{
  char buff[8];
  this->ReadFile(f,pos,8,buff);
  return this->CharPointerToDouble(buff);
}

int vtkLSMReader::ReadData(ifstream *f,unsigned long *pos,int size,char *buf)
{
  return this->ReadFile(f,pos,size,buf);
}

int vtkLSMReader::ReadFile(ifstream *f,unsigned long *pos,int size,char *buf)
{
  f->seekg(*pos,ios::beg);
  f->read(buf,size);
  if( !f ) return 0;
  *pos = *pos + size;
  return 1;
}

void vtkLSMReader::Print()
{
  printf("Identifier:%d\n",this->Identifier);
  printf("DimensionX: %d\n",this->Dimensions[0]);  
  printf("DimensionY: %d\n",this->Dimensions[1]);  
  printf("DimensionZ: %d\n",this->Dimensions[2]);  
  printf("Time points: %d\n",this->Dimensions[3]);  
  printf("NumberOfIntensityValuesX: %d\n",this->NumberOfIntensityValues[0]);
  printf("NumberOfIntensityValuesY: %d\n",this->NumberOfIntensityValues[1]);
  printf("NumberOfIntensityValuesZ: %d\n",this->NumberOfIntensityValues[2]);
  printf("NumberOfIntensityValuesTime: %d\n",this->NumberOfIntensityValues[3]);
  cout << "VoxelSizeX: " << this->VoxelSizes[0] << "\n";
  cout << "VoxelSizeY: " << this->VoxelSizes[1] << "\n";
  cout << "VoxelSizeZ: " << this->VoxelSizes[2] << "\n";
  printf("ScanType: %d\n",this->ScanType);
  printf("DataType: %d\n",this->DataType);
  printf("Compression: %d\n",this->Compression);  
  printf("PlanarConfiguration: %d\n",this->PlanarConfiguration);
  printf("PhotometricInterpretation: %d\n",this->PhotometricInterpretation);
  printf("Predictor: %d\n",this->Predictor);
  printf("NumberOfChannels: %d\n",this->Dimensions[4]);
  printf("ChannelInfo:\n");
  for(int i=0;i<this->Dimensions[4];i++)
    {
    printf("\t%s,(%d,%d,%d)\n",this->GetChannelName(i),this->GetChannelColorComponent(i,0),this->GetChannelColorComponent(i,1),this->GetChannelColorComponent(i,2));
    }
  printf("StripByteCounts:\n");
  for(int i=0;i<this->Dimensions[4];i++)
    {
      printf("\t%d\n",this->StripByteCount->GetValue(i));
    }
}

void vtkLSMReader::PrintSelf(ostream& os, vtkIndent indent)
{
  this->Superclass::PrintSelf(os,indent);
  this->Print();
}

