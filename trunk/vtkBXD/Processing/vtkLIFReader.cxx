/*=========================================================================

  Program:   BioImageXD
  Module:    vtkLIFReader.cxx
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

// Handles currently only 8 bit data

#include "vtkLIFReader.h"
#include "vtkXMLDataParser.h"
#include "vtkObjectFactory.h"
#include "vtkInformationVector.h"
#include "vtkInformation.h"
#include "vtkDataObject.h"
#include "vtkStreamingDemandDrivenPipeline.h"
#include "vtkImageData.h"
#include "vtkPointData.h"
#include "vtkByteSwap.h"
#include "vtkUnsignedCharArray.h"
#include "vtkUnsignedShortArray.h"
#include <vtkstd/vector>
#include <iostream>

typedef unsigned  long OFFSET_TYPE;

// Vectors for one image
typedef vtkstd::vector<ChannelData*> ImageChannelsTypeBase;
typedef vtkstd::vector<DimensionData*> ImageDimensionsTypeBase;
class ImageChannels: public ImageChannelsTypeBase {};
class ImageDimensions: public ImageDimensionsTypeBase {};

// Vectors for all images
typedef vtkstd::vector<ImageChannels*> VectorChannelTypeBase;
typedef vtkstd::vector<ImageDimensions*> VectorDimensionTypeBase;
typedef vtkstd::vector<const char*> VectorImageTypeBase; 
class ChannelVector: public VectorChannelTypeBase {};
class DimensionVector: public VectorDimensionTypeBase {};
class ImageVector: public VectorImageTypeBase {};

vtkStandardNewMacro(vtkLIFReader);

vtkLIFReader::vtkLIFReader()
{
  this->InitializeAttributes();
  this->SetNumberOfInputPorts(0); // Source
  this->SetNumberOfOutputPorts(1);
}

vtkLIFReader::~vtkLIFReader()
{
  this->Clear();
}

void vtkLIFReader::PrintSelf(ostream& os, vtkIndent indent)
{
  this->Superclass::PrintSelf(os,indent);

  if (this->File)
    {
    os << indent << "Open File: " << this->FileName << endl;
    os << indent << indent << "File Size: " << this->FileSize << endl;
    os << indent << indent << "Images: " << this->GetImageCount() << endl;
	os << indent << indent << "Lif Version: " << this->LifVersion << endl;
    }

  os << indent << "Current Image: " << this->CurrentImage << endl;
  os << indent << "Current Channel: " << this->CurrentChannel << endl;
  os << indent << "Current Time Point: " << this->CurrentTimePoint << endl;

  if (this->Channels->size() > 0 && this->Dimensions->size() > 0)
    {
    VectorChannelTypeBase::const_iterator channelsIter = this->Channels->begin();
	VectorDimensionTypeBase::const_iterator dimensionsIter = this->Dimensions->begin();
	VectorImageTypeBase::const_iterator imagesIter = this->Images->begin();
	vtkIdType offsetId = 0;
		
	while (channelsIter != this->Channels->end() && dimensionsIter != this->Dimensions->end() &&
		   imagesIter != this->Images->end())
	  {
	  os << indent << "Image: " << (*imagesIter) << endl;
	  os << indent << indent << "Offset: " << this->Offsets->GetValue(offsetId) << endl;
	  os << indent << indent << "Size: " << this->ImageSizes->GetValue(offsetId) << endl;
	  ImageChannelsTypeBase::const_iterator imgChannels = (*channelsIter)->begin();
	  while (imgChannels != (*channelsIter)->end())
	    {
	    os << indent << indent << "Channel: " << endl;
		os << indent << indent << indent << "DataType: " << (*imgChannels)->DataType << endl;
		os << indent << indent << indent << "ChannelTag: " << (*imgChannels)->ChannelTag << endl;
		os << indent << indent << indent << "Resolution: " << (*imgChannels)->Resolution << endl;
		os << indent << indent << indent << "NameOfMeasuredQuantity: " << (*imgChannels)->NameOfMeasuredQuantity << endl;
		os << indent << indent << indent << "Min: " << (*imgChannels)->Min << endl;
		os << indent << indent << indent << "Max: " << (*imgChannels)->Max << endl;
		os << indent << indent << indent << "Unit: " << (*imgChannels)->Unit << endl;
		os << indent << indent << indent << "LUTName: " << (*imgChannels)->LUTName << endl;
		os << indent << indent << indent << "IsLUTInverted: " << (*imgChannels)->IsLUTInverted << endl;
		os << indent << indent << indent << "BytesInc: " << (*imgChannels)->BytesInc << endl;
		os << indent << indent << indent << "BitInc: " << (*imgChannels)->BitInc << endl;
		imgChannels++;
	    }
	
	  ImageDimensionsTypeBase::const_iterator imgDims = (*dimensionsIter)->begin();
	  while (imgDims != (*dimensionsIter)->end())
	    {
	    os << indent << indent << "Dimension: " << endl;
		os << indent << indent << indent << "DimID: " << (*imgDims)->DimID << endl;
		os << indent << indent << indent << "NumberOfElements: " << (*imgDims)->NumberOfElements << endl;
		os << indent << indent << indent << "Origin: " << (*imgDims)->Origin << endl;
		os << indent << indent << indent << "Length: " << (*imgDims)->Length << endl;
		os << indent << indent << indent << "Unit: " << (*imgDims)->Unit << endl;
		os << indent << indent << indent << "BytesInc: " << (*imgDims)->BytesInc << endl;
		os << indent << indent << indent << "BitInc: " << (*imgDims)->BitInc << endl;
		imgDims++;
	    }

	  channelsIter++;
	  dimensionsIter++;
	  imagesIter++;
	  offsetId++;
	  }
    }
}

const char* vtkLIFReader::GetFileExtensions()
{
  return ".lif .LIF";
}

int vtkLIFReader::OpenFile()
{
  if (!this->FileName)
	{
	  vtkErrorMacro(<< "File name isn't specified.");
	  return 0;
	}
  this->Clear(); // Remove info of possibly already opened file.

  this->File = new ifstream(this->FileName, ios::in | ios::binary);
  if (!this->File || this->File->fail())
    {
      vtkErrorMacro(<< "OpenFile: Could not open file " << this->FileName);
      return 0;
    }

  // Get size of the file
  this->File->seekg(0,ios::end);
  this->FileSize = this->File->tellg();
  this->File->seekg(0,ios::beg);
  
  this->Channels = new ChannelVector;
  this->Dimensions = new DimensionVector;
  this->Images = new ImageVector;
  this->Offsets = vtkUnsignedLongLongArray::New();
  this->ImageSizes = vtkUnsignedLongLongArray::New();
  this->Modified();
  
  return 1;
}

void vtkLIFReader::CloseFile()
{
  this->Clear();
}

void vtkLIFReader::SetFileName(const char *fname)
{
  if (!fname && !this->FileName)
	{
	  return;
	}
  if (this->FileName && fname && !strcmp(this->FileName,fname))
	{
	  return;
	}

  this->Clear();

  if (fname)
	{
	  this->FileName = new char[strlen(fname)];
	  strcpy(this->FileName,fname);
	}

  this->Modified();
}

int vtkLIFReader::GetImageCount()
{
  return this->Images->size();
}

unsigned long long vtkLIFReader::GetFileSize()
{
  return this->FileSize;
}

int vtkLIFReader::GetChannelCount(int image)
{
  if (image >= 0 && image < this->GetImageCount())
	{
	  if (this->Channels->at(image)->size() == 3 && this->Channels->at(image)->at(0)->ChannelTag > 0) return 1; // RGB image with 3 channels
	  return this->Channels->at(image)->size();
	}
  return 0;
}

int vtkLIFReader::GetChannelCount()
{
  return this->GetChannelCount(this->CurrentImage);
}

int vtkLIFReader::GetDimensionCount(int image)
{
  if (image >= 0 && image < this->GetImageCount()) return this->Dimensions->at(image)->size();
  return 0;
}

int vtkLIFReader::GetDimensionCount()
{
  return this->GetDimensionCount(this->CurrentImage);
}

int vtkLIFReader::SetCurrentImage(int image)
{
  this->Modified();
  if (image >= 0 && image < this->GetImageCount())
    {
      this->CurrentImage = image;
      this->CurrentChannel = -1;
      return 1;
    }
  else
    {
      this->CurrentImage = -1;
      this->CurrentChannel = -1;
      return 0;
    }
}

int vtkLIFReader::SetCurrentChannel(int channel)
{
  this->Modified();
  if (this->CurrentImage >= 0 && channel >= 0 && 
      channel < this->GetChannelCount(this->CurrentImage))
    {
      this->CurrentChannel = channel;
	  this->SetImageDimensions();
	  this->SetImageVoxelSizes();
      return 1;
    }

  else
    {
      this->CurrentChannel = -1;
      return 0;
    }
}

void vtkLIFReader::SetCurrentImageAndChannel(int image, int channel)
{
  this->SetCurrentImage(image);
  this->SetCurrentChannel(channel);
}

int vtkLIFReader::SetCurrentTimePoint(int i)
{
  this->Modified();
  if (this->CurrentImage >= 0 && i >= 0 && i < this->GetImageDims()[3])
    {
      this->CurrentTimePoint = i;
      return 1;
    }
  else
    {
      this->CurrentTimePoint = -1;
      return 0;
    }
}

unsigned int vtkLIFReader::GetImageVoxelCount(int image)
{
  if (image < 0 || image >= this->Dimensions->size()) return 0;

  unsigned int voxels = 1;
  for (ImageDimensionsTypeBase::const_iterator dimIter = this->Dimensions->at(image)->begin();
       dimIter != this->Dimensions->at(image)->end(); dimIter++)
    {
      if ((*dimIter)->DimID == DimIDX || (*dimIter)->DimID == DimIDY || 
	  (*dimIter)->DimID == DimIDZ) voxels *= (*dimIter)->NumberOfElements;
    }
  return voxels;
}

unsigned int vtkLIFReader::GetImageVoxelCount()
{
  return this->GetImageVoxelCount(this->CurrentImage);
}

int vtkLIFReader::GetImageSlicePixelCount(int image)
{
  if (image < 0 || image >= this->Dimensions->size()) return 0;

  int pixels = 1;
  for (ImageDimensionsTypeBase::const_iterator dimIter = this->Dimensions->at(image)->begin();
       dimIter != this->Dimensions->at(image)->end(); dimIter++)
    {
      if ((*dimIter)->DimID == DimIDX || (*dimIter)->DimID == DimIDY) pixels *= (*dimIter)->NumberOfElements;
    }
  return pixels;
}

int vtkLIFReader::GetImageSlicePixelCount()
{
  return this->GetImageSlicePixelCount(this->CurrentImage);
}

int vtkLIFReader::SetImageVoxelSizes()
{
  this->Modified();
  this->ImageVoxels[0] = this->ImageVoxels[1] = this->ImageVoxels[2] = 0.0;

  if (this->CurrentImage < 0 || this->CurrentImage >= this->Dimensions->size())
	return 0;

  for (ImageDimensionsTypeBase::const_iterator dimIter = this->Dimensions->at(this->CurrentImage)->begin();
       dimIter != this->Dimensions->at(this->CurrentImage)->end(); dimIter++)
    {
    if ((*dimIter)->DimID == DimIDX)
	  {
	  if (strcmp((*dimIter)->Unit,"m") == 0 || strcmp((*dimIter)->Unit,"M") == 0 ||
		  strcmp((*dimIter)->Unit,"") == 0)
		{
		  this->ImageVoxels[0] = fabs((*dimIter)->Length / (*dimIter)->NumberOfElements);
		}
	  }
      else if ((*dimIter)->DimID == DimIDY)
		{
		if (strcmp((*dimIter)->Unit,"m") == 0 || strcmp((*dimIter)->Unit,"M") == 0 ||
			strcmp((*dimIter)->Unit,"") == 0)
		  {
			this->ImageVoxels[1] = fabs((*dimIter)->Length / (*dimIter)->NumberOfElements);
		  }
		}
      else if ((*dimIter)->DimID == DimIDZ)
		{
		if (strcmp((*dimIter)->Unit,"m") == 0 || strcmp((*dimIter)->Unit,"M") == 0 ||
			strcmp((*dimIter)->Unit,"") == 0)
		  {
			this->ImageVoxels[2] = fabs((*dimIter)->Length / (*dimIter)->NumberOfElements);
		  }
		}
    }

  return 1;
}

int vtkLIFReader::SetImageDimensions()
{
  this->Modified();
  if (this->CurrentImage < 0 || this->CurrentImage >= this->Dimensions->size())
	return 0;

  this->ImageDims[0] = this->ImageDims[1] = this->ImageDims[2] = this->ImageDims[3] = 0;

  for (ImageDimensionsTypeBase::const_iterator dimIter = this->Dimensions->at(this->CurrentImage)->begin();
       dimIter != this->Dimensions->at(this->CurrentImage)->end(); dimIter++)
    {
    if ((*dimIter)->DimID == DimIDX) this->ImageDims[0] = (*dimIter)->NumberOfElements;
	else if ((*dimIter)->DimID == DimIDY) this->ImageDims[1] = (*dimIter)->NumberOfElements;
	else if ((*dimIter)->DimID == DimIDZ) this->ImageDims[2] = (*dimIter)->NumberOfElements;
	else if ((*dimIter)->DimID == DimIDT) this->ImageDims[3] = (*dimIter)->NumberOfElements;
    }

  // If image has x and y components, then make sure that z component is at
  // least 1. This way we don't have 3D image with dimensions (x,y,0)
  //  if (this->ImageDims[0] > 0 && this->ImageDims[1] > 0 && this->ImageDims[2] <= 0)
  //	this->ImageDims[2] = 1;
  // If image has x and y components, then make sure that t component is at
  // least 1. This way we don't have 4D image with dimensions (x,y,z,0)
  //  if (this->ImageDims[0] > 0 && this->ImageDims[1] > 0 && this->ImageDims[3] <= 0)
  //	this->ImageDims[3] = 1;

  // Earlier checks are moved from here because those are application specific.

  return 1;
}

int vtkLIFReader::GetImageChannelResolution(int image, int channel)
{
  if (image < 0 || image >= this->GetImageCount() || channel < 0 || channel > this->Channels->at(image)->size())
    {
      vtkErrorMacro(<< "GetImageChannelResolution: image number: " << image << ", or channel number: " << channel << " is out of bounds.");
      return 0;
    }
  return this->Channels->at(image)->at(channel)->Resolution;
}

int vtkLIFReader::GetImageChannelResolution()
{
  return this->GetImageChannelResolution(this->CurrentImage,this->CurrentChannel);
}


double vtkLIFReader::GetImageChannelMin(int image, int channel)
{
  if (image < 0 || image >= this->GetImageCount() || channel < 0 || channel > this->Channels->at(image)->size())
    {
      vtkErrorMacro(<< "GetImageChannelMin: image number: " << image << ", or channel number: " << channel << " is out of bounds.");
      return 0.0;
    }
  return this->Channels->at(image)->at(channel)->Min;
}

double vtkLIFReader::GetImageChannelMin()
{
  return this->GetImageChannelMin(this->CurrentImage,this->CurrentChannel);
}


double vtkLIFReader::GetImageChannelMax(int image, int channel)
{
  if (image < 0 || image >= this->GetImageCount() || channel < 0 || channel > this->Channels->at(image)->size())
    {
      vtkErrorMacro(<< "GetImageChannelMax: image number: " << image << ", or channel number: " << channel << " is out of bounds.");
      return 0.0;
    }
  return this->Channels->at(image)->at(channel)->Max;
}

double vtkLIFReader::GetImageChannelMax()
{
  return this->GetImageChannelMax(this->CurrentImage,this->CurrentChannel);
}

const char* vtkLIFReader::GetImageChannelLUTName(int image, int channel)
{
  if (image < 0 || image >= this->GetImageCount() || channel < 0 || channel > this->Channels->at(image)->size())
    {
      vtkErrorMacro(<< "GetImageChannelLUTName: image number: " << image << ", or channel number: " << channel << " is out of bounds.");
      return "";
    }

  return this->Channels->at(image)->at(channel)->LUTName;
}

const char* vtkLIFReader::GetImageChannelLUTName()
{
  return this->GetImageChannelLUTName(this->CurrentImage,this->CurrentChannel);
}

unsigned long long vtkLIFReader::GetTimePointOffset(int image, int timepoint)
{
  if (timepoint < 0) return 0;
  for (ImageDimensionsTypeBase::const_iterator dimIter = this->Dimensions->at(image)->begin();
       dimIter != this->Dimensions->at(image)->end(); dimIter++)
    {
      if ((*dimIter)->DimID == DimIDT) return (*dimIter)->BytesInc * timepoint;
    }

  return 0;
}

const char* vtkLIFReader::GetImageName(int image)
{
  if (image < 0 || image >= this->GetImageCount()) return "";
  return this->Images->at(image);
}

const char* vtkLIFReader::GetCurrentImageName()
{
  return this->GetImageName(this->CurrentImage);
}

double vtkLIFReader::GetTimeInterval(int image)
{
  if (image < 0 || image >= this->GetImageCount()) return -1.0;
  for (ImageDimensionsTypeBase::const_iterator dimIter = this->Dimensions->at(image)->begin();
	   dimIter != this->Dimensions->at(image)->end(); dimIter++)
	{
	  if ((*dimIter)->DimID == DimIDT) return (*dimIter)->Length;
	}

  return -1.0;
}

double vtkLIFReader::GetTimeInterval()
{
  return this->GetTimeInterval(this->CurrentImage);
}

int vtkLIFReader::ReadLIFHeader()
{
  if (!this->File) {
    vtkErrorMacro(<< "ReadLIFHeader: No open LIF file.");
    return 0;
  }

  if (this->HeaderInfoRead) return 1;

  // Check LIF test value from first 4 bytes of file
  int lifCheck = this->ReadInt(this->File);
  if (lifCheck != MemBlockCode) {
	long long fileOffset = this->File->tellg();
	fileOffset -= 4;
    vtkErrorMacro(<< "ReadLIFHeader: File contains wrong MemBlockCode: " << lifCheck << " at: " << fileOffset);
    return 0;
  }

  // Skip the size of next block
  this->File->seekg(4,ios::cur);

  // Check memblock separator code and read xml size
  char lifChar = this->ReadChar(this->File);
  if (lifChar != TestCode) {
	long long fileOffset = this->File->tellg();
	fileOffset -= 1;
    vtkErrorMacro(<< "ReadLIFHeader: File contains wrong TestCode: " << lifChar << " at: " << fileOffset);
    return 0;
  }

  unsigned int xmlChars = this->ReadUnsignedInt(this->File) * 2;
  char *xmlHeader = new char[xmlChars];
  // Read and parse xml header
  this->File->read(xmlHeader,xmlChars);
  this->ParseXMLHeader(xmlHeader,xmlChars);

  // Find image offsets
  this->Offsets->SetNumberOfValues(this->GetImageCount());
  vtkIdType offsetId = 0;

  while (this->File->tellg() < this->GetFileSize())
  {
    // Check LIF test value
    lifCheck = this->ReadInt(this->File);

    if (lifCheck != MemBlockCode) {
	  long long fileOffset = this->File->tellg();
	  fileOffset -= 4;
      vtkErrorMacro(<< "ReadLIFHeader: File contains wrong MemBlockCode: " << lifCheck << " at: " << fileOffset);
      return 0;
    }
  
    // Don't care about the size of the next block
    this->File->seekg(4,ios::cur);
    // Read testcode
    lifChar = this->ReadChar(this->File);
    if (lifChar != TestCode) {
	  long long fileOffset = this->File->tellg();
	  fileOffset -= 1;
      vtkErrorMacro(<< "ReadLIFHeader: File contains wrong TestCode: " << lifChar << " at: " << fileOffset);
      return 0;
    }
  
    // Read size of memory, this is 4 bytes in version 1 and 8 in version 2
	unsigned long long memorySize;
	if (this->LifVersion >= 2)
	  {
		memorySize = this->ReadUnsignedLongLong(this->File);
	  }
	else
	  {
		memorySize = this->ReadUnsignedInt(this->File);
	  }

    // Find next testcode
    while (this->ReadChar(this->File) != TestCode) {}
    unsigned int memDescrSize = this->ReadUnsignedInt(this->File) * 2;
    // Skip over memory description
    this->File->seekg(static_cast<OFFSET_TYPE>(memDescrSize),ios::cur);
  
    // Add image offset if memory size is > 0
    if (memorySize > 0)
    {
      this->Offsets->InsertValue(offsetId,this->File->tellg());
      this->ImageSizes->InsertValue(offsetId,memorySize);
      offsetId++;
      this->File->seekg(static_cast<OFFSET_TYPE>(memorySize),ios::cur);
    }
  }
  
  this->HeaderInfoRead = 1;
  this->SetCurrentImageAndChannel(0,0); // This sets Modified() if succeeds
  return 1;
}

int vtkLIFReader::ParseXMLHeader(const char *xmlHeader, unsigned long chars)
{
  vtkXMLDataParser *xmlDataParser = vtkXMLDataParser::New();
  xmlDataParser->InitializeParser();
  xmlDataParser->ParseChunk(xmlHeader,chars);

  if (!xmlDataParser->CleanupParser()) 
	{
    vtkErrorMacro(<< "ParserXMLHeader: Couldn't parse XML.");
    return 0;
	}

  vtkXMLDataElement *rootElement = xmlDataParser->GetRootElement();
  if (!rootElement)
	{
    vtkErrorMacro(<< "ParseXMLHeader: No root element found.");
    return 0;
	}

  rootElement->GetScalarAttribute("Version",this->LifVersion);
  return this->ParseInfoHeader(rootElement,1);
}

int vtkLIFReader::ParseInfoHeader(vtkXMLDataElement *rootElement, int root)
{
  vtkXMLDataElement *elementElement = rootElement;
  if (root)
	{
    elementElement = rootElement->FindNestedElementWithName("Element");
    if (!elementElement)
	  {
      vtkErrorMacro(<< "ParseXMLHeader: No element Element found after root element.");
      return 0;
	  }
	}

  vtkXMLDataElement *elementData = elementElement->FindNestedElementWithName("Data");
  vtkXMLDataElement *elementImage = elementData->FindNestedElementWithName("Image");
  vtkXMLDataElement *elementMemory = elementElement->FindNestedElementWithName("Memory");
  vtkXMLDataElement *elementChildren = elementElement->FindNestedElementWithName("Children");

  // If Image element found
  if (elementImage) 
	{
    this->ReadImage(elementImage);
    // Check that image info is read correctly and then add image name
    if (Channels->size() > Images->size() || Dimensions->size() > Images->size())
      {
	  const char *imageName = elementElement->GetAttribute("Name");
	  Images->push_back(imageName);
      }
	}

  // If Children element found
  if (elementChildren)
	{
    int numOfChildElements = elementChildren->GetNumberOfNestedElements();
    vtkXMLDataElement *childIterator;

    for (int i = 0; i < numOfChildElements; ++i)
	  {
      childIterator = elementChildren->GetNestedElement(i);
      this->ParseInfoHeader(childIterator,0);
	  }
	}

  this->Modified();
  return 1;
}

void vtkLIFReader::ReadImage(vtkXMLDataElement *elementImage)
{
  vtkXMLDataElement *elementImageDescription = elementImage->FindNestedElementWithName("ImageDescription");

  if (elementImageDescription)
    {
    vtkXMLDataElement *elementChannels = elementImageDescription->FindNestedElementWithName("Channels");
    vtkXMLDataElement *elementDimensions = elementImageDescription->FindNestedElementWithName("Dimensions");
    if (elementChannels && elementDimensions)
	  {
	  ImageChannels *ImgChannels = new ImageChannels;
	  ImageDimensions *ImgDimensions = new ImageDimensions;
	  vtkXMLDataElement *Iterator;

	  // Get info of channels
	  int channelCount = elementChannels->GetNumberOfNestedElements();
	  for (int i = 0; i < channelCount; ++i)
		{
		ChannelData *Data = new ChannelData;
		Iterator = elementChannels->GetNestedElement(i);
		this->LoadChannelInfoToStruct(Iterator,Data);
		ImgChannels->push_back(Data);
		}

	  // Get info of dimensions
	  int dimensionCount = elementDimensions->GetNumberOfNestedElements();
	  for (int i = 0; i < dimensionCount; ++i)
		{
		DimensionData *Data = new DimensionData;
		Iterator = elementDimensions->GetNestedElement(i);
		this->LoadDimensionInfoToStruct(Iterator,Data);
		ImgDimensions->push_back(Data);
		}
			
	  this->Channels->push_back(ImgChannels);
	  this->Dimensions->push_back(ImgDimensions);
	  }
    }
  this->Modified();
}

void vtkLIFReader::LoadChannelInfoToStruct(vtkXMLDataElement *Element, ChannelData *Data)
{
  Element->GetScalarAttribute("DataType",Data->DataType);
  Element->GetScalarAttribute("ChannelTag",Data->ChannelTag);
  Element->GetScalarAttribute("Resolution",Data->Resolution);
  Data->NameOfMeasuredQuantity = Element->GetAttribute("NameOfMeasuredQuantity");
  if (!Data->NameOfMeasuredQuantity) Data->NameOfMeasuredQuantity = "";
  Element->GetScalarAttribute("Min",Data->Min);
  Element->GetScalarAttribute("Max",Data->Max);
  Data->Unit = Element->GetAttribute("Unit");
  if (!Data->Unit) Data->Unit = "";
  Data->LUTName = Element->GetAttribute("LUTName");
  if (!Data->LUTName) Data->LUTName = "";
  Element->GetScalarAttribute("IsLUTInverted",Data->IsLUTInverted);
  // Bytes Inc is 64 bits in LIF version 2 but GetScalarAttribute only allows
  // maximum of unsigned long which can be 32 bits.
  Element->GetScalarAttribute("BytesInc",(unsigned long&)Data->BytesInc);
  Element->GetScalarAttribute("BitInc",Data->BitInc);
}

void vtkLIFReader::LoadDimensionInfoToStruct(vtkXMLDataElement *Element, DimensionData *Data)
{
  Element->GetScalarAttribute("DimID",Data->DimID);
  Element->GetScalarAttribute("NumberOfElements",Data->NumberOfElements);
  Element->GetScalarAttribute("Origin",Data->Origin);
  Element->GetScalarAttribute("Length",Data->Length);
  Data->Unit = Element->GetAttribute("Unit");
  if (!Data->Unit) Data->Unit = "";
  // Bytes Inc is 64 bits in LIF version 2 but GetScalarAttribute only allows
  // maximum of unsigned long which can be 32 bits.
  Element->GetScalarAttribute("BytesInc",(unsigned long&)Data->BytesInc);
  Element->GetScalarAttribute("BitInc",Data->BitInc);
}

void vtkLIFReader::InitializeAttributes()
{
  this->File = NULL;
  this->FileName = NULL;
  this->FileSize = 0;
  this->Dimensions = NULL;
  this->Channels = NULL;
  this->Images = NULL;
  this->Offsets = NULL;
  this->ImageSizes = NULL;
  this->HeaderInfoRead = 0;
  this->CurrentImage = -1;
  this->CurrentChannel = -1;
  this->CurrentTimePoint = -1;
  this->LifVersion = 0;
}

void vtkLIFReader::Clear()
{
  this->Modified();
  if (this->File)
    {
    this->File->close();
    delete this->File;
    delete [] this->FileName;
    }

// These deletes also every item in vectors
  if (this->Channels) delete this->Channels;
  if (this->Dimensions) delete this->Dimensions;
  if (this->Images) delete this->Images;
  if (this->Offsets) this->Offsets->Delete();
  if (this->ImageSizes) this->ImageSizes->Delete();
}

int vtkLIFReader::RequestInformation(vtkInformation* vtkNotUsed(request),
                                     vtkInformationVector** vtkNotUsed(inputVector),
                                     vtkInformationVector *outputVector)
{
  if (!this->HeaderInfoRead)
    {
      if (!this->ReadLIFHeader())
		{
		  vtkErrorMacro(<< "RequestInformation: Couldn't read file header.");
		  return 0;
		}
    }

  vtkInformation *info = outputVector->GetInformationObject(0);

  double *spacing = new double[3];
  int *extent =  new int[6];
  double *origin = new double[3];
  this->CalculateExtentAndSpacingAndOrigin(extent,spacing,origin);
  info->Set(vtkDataObject::SPACING(),spacing,3);
  info->Set(vtkStreamingDemandDrivenPipeline::WHOLE_EXTENT(),extent,6);
  info->Set(vtkDataObject::ORIGIN(),origin,3);

  int rgb = this->Channels->at(this->CurrentImage)->at(this->CurrentChannel)->ChannelTag > 0;

  if (this->GetImageChannelResolution(this->CurrentImage,this->CurrentChannel) == 8)
	{
	  if (!rgb)
		{
		vtkDataObject::SetPointDataActiveScalarInfo(info,VTK_UNSIGNED_CHAR,1);
		}
	  else
		{
		vtkDataObject::SetPointDataActiveScalarInfo(info,VTK_UNSIGNED_CHAR,3);
		}
	}
  else
	{
	  vtkDataObject::SetPointDataActiveScalarInfo(info,VTK_UNSIGNED_SHORT,1);
	}

  delete [] origin;
  delete [] extent;
  delete [] spacing;

  return 1;
}

int vtkLIFReader::RequestUpdateExtent(vtkInformation* vtkNotUsed(request),
                                      vtkInformationVector** vtkNotUsed(inputVector),
                                      vtkInformationVector *outputVector)
{
  int uext[6], ext[6];
    
  vtkInformation* outInfo = outputVector->GetInformationObject(0);
  //vtkInformation *inInfo = inputVector[0]->GetInformationObject(0);

  outInfo->Get(vtkStreamingDemandDrivenPipeline::WHOLE_EXTENT(),ext);
  // Get the requested update extent from the output.
  outInfo->Get(vtkStreamingDemandDrivenPipeline::UPDATE_EXTENT(), uext);
  printf("vtkLIFReader Requested update extent = %d, %d, %d, %d, %d, %d\n", uext[0], uext[1], uext[2], uext[3], uext[4], uext[5]);
  // If they request an update extent that doesn't cover the whole slice
  // then modify the uextent 
  if(uext[1] < ext[1] ) uext[1] = ext[1];
  if(uext[3] < ext[3] ) uext[3] = ext[3];
  outInfo->Set(vtkStreamingDemandDrivenPipeline::UPDATE_EXTENT(), uext,6);
  //request->Set(vtkStreamingDemandDrivenPipeline::REQUEST_UPDATE_EXTENT(), uext,6);

  return 1;
}

int vtkLIFReader::RequestData(vtkInformation *request,
                              vtkInformationVector **inputVector,
                              vtkInformationVector *outputVector)
{
  int extent[6];
  unsigned long long imageOffset;
  unsigned long long channelOffset;
  unsigned int bufferSize;
  unsigned int bufferItems;

  if (!this->HeaderInfoRead || this->CurrentImage < 0 || this->CurrentChannel < 0)
    {
      vtkErrorMacro(<< "RequestData: Header info isn't read or CurrentImage or CurrentChannel is less than 0.");
      return 0;
    }

  unsigned int resolution = this->GetImageChannelResolution(this->CurrentImage,this->CurrentChannel);
  int rgb = this->Channels->at(this->CurrentImage)->at(this->CurrentChannel)->ChannelTag > 0;
  vtkInformation *outInfo = outputVector->GetInformationObject(0);
  vtkImageData *imageData = this->AllocateOutputData(outInfo->Get(vtkDataObject::DATA_OBJECT()));
  imageData->GetPointData()->GetScalars()->SetName("LIF Scalars");
  imageData->GetExtent(extent);

  int nSlices = extent[5] > extent[4] ? extent[5]-extent[4]+1 : 1;
  unsigned int nVoxels = this->GetImageVoxelCount(this->CurrentImage);
  unsigned int voxelsSize = nVoxels;
  unsigned int slicePixels = this->GetImageSlicePixelCount(this->CurrentImage);
  unsigned int slicePixelsSize = slicePixels;
  if (resolution != 8)
	{
	  slicePixelsSize *= 2;
	  voxelsSize *= 2;
	}
  if (rgb)
	{
	  slicePixelsSize *= 3;
	  voxelsSize *= 3;
	}
  unsigned int sliceChannelsSize = slicePixelsSize * this->GetChannelCount(this->CurrentImage);

  if (nSlices > 1) // Allocate array for all slices and read all of them
    {
	  bufferItems = nVoxels;
      bufferSize = voxelsSize;
    }
  else // Allocate array only for one slice and read only one slice
    {
	  bufferItems = slicePixels;
      bufferSize = slicePixelsSize;
    }

  void *buffer;
  char *pos;
  if (resolution == 8)
	{
	  buffer = new unsigned char[bufferSize];
	  pos = static_cast<char*>(buffer);
	}
  else
	{
	  buffer = new unsigned short[bufferItems];
	  pos = static_cast<char*>(buffer);
	}
  vtkDebugMacro(<< "Allocated buffer of size: " << bufferSize);

  imageOffset = this->Offsets->GetValue(this->CurrentImage);
  imageOffset += this->GetTimePointOffset(this->CurrentImage,this->CurrentTimePoint);
  vtkDebugMacro(<< "Image Offset is: " << imageOffset);

  for (int i = extent[4]; i <= extent[5]; ++i)
    {
	  channelOffset = imageOffset + i * sliceChannelsSize;
      channelOffset += this->Channels->at(this->CurrentImage)->at(this->CurrentChannel)->BytesInc;

      this->File->seekg(static_cast<OFFSET_TYPE>(channelOffset),ios::beg);
      this->File->read(pos,slicePixelsSize);
      vtkDebugMacro(<< "Read " << slicePixelsSize << " bytes of data from " << channelOffset);

      pos += slicePixelsSize;
	}

  vtkDebugMacro(<< "Constructing point data array");
  if (resolution == 8)
	{
	  vtkUnsignedCharArray *pointDataArray;
	  pointDataArray = vtkUnsignedCharArray::New();
	  if (!rgb)
		{
		  pointDataArray->SetNumberOfComponents(1);
		}
	  else
		{
		  pointDataArray->SetNumberOfComponents(3);
		  // Change rgb order to bgr
		  unsigned char temp;
		  for (unsigned long long i = 2; i < bufferSize; i +=3)
			{
			  temp = (static_cast<unsigned char*>(buffer))[i-2];
			  (static_cast<unsigned char*>(buffer))[i-2] = (static_cast<unsigned char*>(buffer))[i];
			  (static_cast<unsigned char*>(buffer))[i] = temp;
			}
		}
	  pointDataArray->SetNumberOfValues(bufferItems);
	  pointDataArray->SetArray(static_cast<unsigned char*>(buffer),bufferSize,0);
	  imageData->GetPointData()->SetScalars(pointDataArray);
	  pointDataArray->Delete();
	}
  else
	{
	  vtkUnsignedShortArray *pointDataArray;
	  pointDataArray = vtkUnsignedShortArray::New();
	  pointDataArray->SetNumberOfComponents(1);
	  pointDataArray->SetNumberOfValues(bufferItems);
	  pointDataArray->SetArray(static_cast<unsigned short*>(buffer),bufferSize,0);
	  imageData->GetPointData()->SetScalars(pointDataArray);
	  pointDataArray->Delete();
	}

  vtkDebugMacro(<< "RequestData done");

  return 1;
}

void vtkLIFReader::CalculateExtentAndSpacingAndOrigin(int *extent, double *spacing, double *origin)
{
  extent[0] = extent[2] = extent[4] = 0;
  extent[1] = extent[3] = extent[5] = 0;
  spacing[0] = spacing[1] = spacing[2] = 1.0;
  origin[0] = origin[1] = origin[2] = 0.0;

  if (this->CurrentImage < 0) return;

  for (ImageDimensionsTypeBase::const_iterator imgDims = this->Dimensions->at(this->CurrentImage)->begin();
       imgDims != this->Dimensions->at(this->CurrentImage)->end(); imgDims++)
    {
      if ((*imgDims)->DimID == DimIDX)
		{
		extent[1] = (*imgDims)->NumberOfElements - 1;
		if (strcmp((*imgDims)->Unit,"m") == 0 || strcmp((*imgDims)->Unit,"M") == 0 ||
	        strcmp((*imgDims)->Unit,""))
		  {
	      spacing[0] = fabs((*imgDims)->Length / extent[1]);
	      origin[0] = (*imgDims)->Origin;
		  }
		}
      else if ((*imgDims)->DimID == DimIDY)
		{
		extent[3] = (*imgDims)->NumberOfElements - 1;
		if (strcmp((*imgDims)->Unit,"m") == 0 || strcmp((*imgDims)->Unit,"M") == 0 ||
	        strcmp((*imgDims)->Unit,""))
		  {
	      spacing[1] = fabs((*imgDims)->Length / extent[3]);
	      origin[1] = (*imgDims)->Origin;
		  }
		}
      else if ((*imgDims)->DimID == DimIDZ)
		{
		extent[5] = (*imgDims)->NumberOfElements - 1;
		if (strcmp((*imgDims)->Unit,"m") == 0 || strcmp((*imgDims)->Unit,"M") == 0 ||
	        strcmp((*imgDims)->Unit,""))
		  {
	      spacing[2] = fabs((*imgDims)->Length / extent[5]);
	      origin[2] = (*imgDims)->Origin;
		  }
		}
    }

  // Normalize spacing
  if (spacing[0] > 1.0e-15)
    {
      spacing[1] /= spacing[0];
      spacing[2] /= spacing[0];
      spacing[0] = 1.0;
    }
}

char vtkLIFReader::ReadChar(ifstream *ifs)
{
  char buffer[1];
  ifs->read(buffer,1);
  return buffer[0];
}

int vtkLIFReader::ReadInt(ifstream *ifs)
{
  char buffer[4];
  ifs->read(buffer,4);
 #ifdef VTK_WORDS_BIGENDIAN
 vtkByteSwap::Swap4LE((unsigned int*)buffer);
 #endif
  return *((int*)(buffer));
}

unsigned int vtkLIFReader::ReadUnsignedInt(ifstream *ifs)
{
  char buffer[4];
  ifs->read(buffer,4);
 #ifdef VTK_WORDS_BIGENDIAN
  vtkByteSwap::Swap4LE((unsigned int*)buffer);
 #endif
  return *((unsigned int*)(buffer));
}

unsigned long long vtkLIFReader::ReadUnsignedLongLong(ifstream *ifs)
{
  char buffer[8];
  ifs->read(buffer,8);
#ifdef VTK_WORDS_BIGENDIAN
  vtkByteSwap::Swap8LE((unsigned long long*)buffer);
#endif
  return *((unsigned long long*)(buffer));
}

int vtkLIFReader::CopyHeaderInfo(const vtkLIFReader *reader)
{
  if (strcmp(this->FileName,reader->FileName))
  	{
  	  return 0;
  	}

  this->Dimensions->resize(reader->Dimensions->size());
  copy(reader->Dimensions->begin(),reader->Dimensions->end(),this->Dimensions->begin());
  this->Channels->resize(reader->Channels->size());
  copy(reader->Channels->begin(),reader->Channels->end(),this->Channels->begin());
  this->Images->resize(reader->Images->size());
  copy(reader->Images->begin(),reader->Images->end(),this->Images->begin());
  this->Offsets->DeepCopy(reader->Offsets);
  this->ImageSizes->DeepCopy(reader->ImageSizes);
  this->LifVersion = reader->LifVersion;
  this->HeaderInfoRead = 1;

  return 1;
}
