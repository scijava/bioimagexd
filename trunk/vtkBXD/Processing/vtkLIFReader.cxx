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

// Handles currently only 8 bit data without time series

#include "vtkLIFReader.h"
#include "vtkXMLDataParser.h"
#include "vtkObjectFactory.h"
#include "vtkInformationVector.h"
#include "vtkInformation.h"
#include "vtkDataObject.h"
#include "vtkStreamingDemandDrivenPipeline.h"
#include "vtkImageData.h"
#include "vtkPointData.h"
#include "vtkUnsignedCharArray.h"
#include <vtkstd/vector>

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
  this->SetNumberOfInputPorts(0); // Source
  this->SetNumberOfOutputPorts(1);
  this->File = NULL;
  this->FileName = NULL;
  this->Dimensions = NULL;
  this->Channels = NULL;
  this->Images = NULL;
  this->Offsets = NULL;
  this->ImageSizes = NULL;
}

vtkLIFReader::~vtkLIFReader()
{
  this->Clear();
}

//const char* vtkLIFReader::GetClassName()
//{
//  return "";
//}

//int vtkLIFReader::isA(const char* )
//{
//}

void vtkLIFReader::PrintSelf(ostream& os, vtkIndent indent)
{
  this->Superclass::PrintSelf(os,indent);
  if (this->File)
    {
    os << indent << "Open File: " << this->FileName << endl;
    os << indent << indent << "File Size: " << this->FileSize << endl;
    os << indent << indent << "Images: " << this->GetImageCount() << endl;
    }
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

int vtkLIFReader::OpenFile(const char* filename)
{
  this->Clear(); // Remove info of possibly already opened file.

  this->File = new ifstream(filename, ios::in | ios::binary);
  if (!this->File || this->File->fail())
    {
      vtkErrorMacro(<< "OpenFile: Could not open file " << filename);
      return 0;
    }

  this->FileName = new char[strlen(filename)];
  strcpy(this->FileName, filename);
  
  // Get size of the file
  this->File->seekg(0,ios::end);
  this->FileSize = this->File->tellg();
  this->File->seekg(0,ios::beg);
  
  this->Channels = new ChannelVector;
  this->Dimensions = new DimensionVector;
  this->Images = new ImageVector;
  this->Offsets = vtkUnsignedIntArray::New();
  this->ImageSizes = vtkUnsignedIntArray::New();
  
  return 1;
}

void vtkLIFReader::CloseFile()
{
  this->Clear();
}

int vtkLIFReader::GetImageCount()
{
  return this->Images->size();
}

long vtkLIFReader::GetFileSize()
{
  return this->FileSize;
}

int vtkLIFReader::GetChannelCount(int image)
{
  if (image >= 0 && image < this->GetImageCount()) return this->Channels->at(image)->size();
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
  if (this->CurrentImage >= 0 && channel >= 0 && 
      channel < this->GetChannelCount(this->CurrentImage))
    {
      this->CurrentChannel = channel;
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
  if (this->CurrentImage >= 0 && i >= 0 && i < this->GetImageDimensions(this->CurrentImage)[3])
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

//double* vtkLIFReader::GetImageVoxelSizes(int image)
int vtkLIFReader::SetImageVoxelSizes(int image)
{
  double *voxelSizes = new double[3];
  voxelSizes[0] = voxelSizes[1] = voxelSizes[2] = 0.0;
  if (image < 0 || image >= this->Dimensions->size()) return 0; //voxelSizes;

  for (ImageDimensionsTypeBase::const_iterator dimIter = this->Dimensions->at(image)->begin();
       dimIter != this->Dimensions->at(image)->end(); dimIter++)
    {
      if ((*dimIter)->DimID == DimIDX)
	{
	  if (strcmp((*dimIter)->Unit,"m") == 0 || strcmp((*dimIter)->Unit,"M") == 0 ||
	      strcmp((*dimIter)->Unit,""))
	    {
	      voxelSizes[0] = (*dimIter)->Length / (*dimIter)->NumberOfElements;
	      this->Voxelss[0] = voxelSizes[0]; // Remove this when pointer can be returned
	    }
	}
      else if ((*dimIter)->DimID == DimIDY)
	{
	  if (strcmp((*dimIter)->Unit,"m") == 0 || strcmp((*dimIter)->Unit,"M") == 0 ||
	      strcmp((*dimIter)->Unit,""))
	    {
	      voxelSizes[1] = (*dimIter)->Length / (*dimIter)->NumberOfElements;
	      this->Voxelss[1] = voxelSizes[1]; // Remove this when pointer can be returned
	    }
	}
      else if ((*dimIter)->DimID == DimIDZ)
	{
	  if (strcmp((*dimIter)->Unit,"m") == 0 || strcmp((*dimIter)->Unit,"M") == 0 ||
	      strcmp((*dimIter)->Unit,""))
	    {
	      voxelSizes[2] = (*dimIter)->Length / (*dimIter)->NumberOfElements;
	      this->Voxelss[2] = voxelSizes[2]; // Remove this when pointer can be returned
	    }
	}
    }

  //  return voxelSizes;
  //  return this->GetVoxelss();
  return 1;
}

//double* vtkLIFReader::GetImageVoxelSizes()
int vtkLIFReader::SetImageVoxelSizes()
{
  return this->SetImageVoxelSizes(this->CurrentImage);
}

int* vtkLIFReader::GetImageDimensions(int image)
{
  static int imgDims[4];
  imgDims[0] = imgDims[1] = imgDims[2] = imgDims[3] = 0;
  if (image < 0 || image >= this->Dimensions->size()) return imgDims;

  for (ImageDimensionsTypeBase::const_iterator dimIter = this->Dimensions->at(image)->begin();
       dimIter != this->Dimensions->at(image)->end(); dimIter++)
    {
      if ((*dimIter)->DimID == DimIDX) imgDims[0] = (*dimIter)->NumberOfElements;
      else if ((*dimIter)->DimID == DimIDY) imgDims[1] = (*dimIter)->NumberOfElements;
      else if ((*dimIter)->DimID == DimIDZ) imgDims[2] = (*dimIter)->NumberOfElements;
      else if ((*dimIter)->DimID == DimIDT) imgDims[3] = (*dimIter)->NumberOfElements;
    }

  return imgDims;
}

// This method is useless if only previous could work
int vtkLIFReader::SetImageDimensions(int image)
{
  if (image < 0 || image >= this->Dimensions->size()) return 0;

  Dims[0] = Dims[1] = Dims[2] = Dims[3] = 0;

  for (ImageDimensionsTypeBase::const_iterator dimIter = this->Dimensions->at(image)->begin();
       dimIter != this->Dimensions->at(image)->end(); dimIter++)
    {
      if ((*dimIter)->DimID == DimIDX) Dims[0] = (*dimIter)->NumberOfElements;
      else if ((*dimIter)->DimID == DimIDY) Dims[1] = (*dimIter)->NumberOfElements;
      else if ((*dimIter)->DimID == DimIDZ) Dims[2] = (*dimIter)->NumberOfElements;
      else if ((*dimIter)->DimID == DimIDT) Dims[3] = (*dimIter)->NumberOfElements;
    }

  return 1;
}

int* vtkLIFReader::GetImageDimensions()
{
  return this->GetImageDimensions(this->CurrentImage);
}

// This method is useless if only previous could work
int vtkLIFReader::SetImageDimensions()
{
  return this->SetImageDimensions(this->CurrentImage);
}


int vtkLIFReader::GetImageChannelResolution(int image, int channel)
{
  if (image < 0 || image > this->Images->size() || channel < 0 || channel > this->Channels->at(image)->size())
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

const char* vtkLIFReader::GetImageChannelLUTName(int image, int channel)
{
  if (image < 0 || image > this->Images->size() || channel < 0 || channel > this->Channels->at(image)->size())
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

int vtkLIFReader::ReadLIFHeader()
{
  if (!this->File) {
    vtkErrorMacro(<< "ReadLIFHeader: No open LIF file.");
    return 0;
  }

  if (this->HeaderInfoRead) return 1;

  // Check LIF test value from first 4 bytes of file
  long lifCheck = this->ReadInt(this->File);
  if (lifCheck != MemBlockCode) {
    vtkErrorMacro(<< "ReadLIFHeader: File contains wrong MemBlockCode: " << lifCheck);
    return 0;
  }

  // Skip the size of next block
  this->File->seekg(4,ios::cur);

  // Check memblock separator code and read xml size
  char lifChar = this->ReadChar(this->File);
  if (lifChar != TestCode) {
    vtkErrorMacro(<< "ReadLIFHeader: File contains wrong TestCode" << lifChar);
    return 0;
  }
  unsigned long xmlChars = this->ReadUnsignedInt(this->File) * 2;
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
      vtkErrorMacro(<< "ReadLIFHeader: File contains wrong MemBlockCode: " << lifCheck);
      return 0;
    }
  
    // Don't care about the size of next block
    this->File->seekg(4,ios::cur);
    // Read testcode
    lifChar = this->ReadChar(this->File);
    if (lifChar != TestCode) {
      vtkErrorMacro(<< "ReadLIFHeader: File contains wrong TestCode " << lifChar);
      return 0;
    }
  
    // Read size of memory
    unsigned long memorySize = this->ReadUnsignedInt(this->File);
    // Find next testcode
    while (this->ReadChar(this->File) != TestCode) {}
    unsigned int memDescrSize = this->ReadUnsignedInt(this->File) * 2;
    // Skip over memory description
    this->File->seekg(memDescrSize,ios::cur);
  
    // Add image offset if memory size is > 0
    if (memorySize > 0)
    {
      this->Offsets->InsertValue(offsetId,this->File->tellg());
      this->ImageSizes->InsertValue(offsetId,memorySize);
      offsetId++;
      this->File->seekg(memorySize,ios::cur);
    }
  }
  
  this->HeaderInfoRead = 1;
  this->SetCurrentImageAndChannel(0,0);
  return 1;
}

int vtkLIFReader::ParseXMLHeader(const char *xmlHeader, unsigned long chars)
{
  vtkXMLDataParser *xmlDataParser = vtkXMLDataParser::New();
  xmlDataParser->InitializeParser();
  xmlDataParser->ParseChunk(xmlHeader,chars);
  if (!xmlDataParser->CleanupParser()) {
    vtkErrorMacro(<< "ParserXMLHeader: Couldn't parse XML.");
    return 0;
  }

  vtkXMLDataElement *rootElement = xmlDataParser->GetRootElement();
  if (!rootElement) {
    vtkErrorMacro(<< "ParseXMLHeader: No root element found.");
    return 0;
  }

  return this->ParseInfoHeader(rootElement,1);
}

int vtkLIFReader::ParseInfoHeader(vtkXMLDataElement *rootElement, int root)
{
  vtkXMLDataElement *elementElement = rootElement;
  if (root)
  {
    elementElement = rootElement->FindNestedElementWithName("Element");
    if (!elementElement) {
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
  if (elementChildren) {
    int numOfChildElements = elementChildren->GetNumberOfNestedElements();
    vtkXMLDataElement *childIterator;

    for (int i = 0; i < numOfChildElements; ++i) {
      childIterator = elementChildren->GetNestedElement(i);
      this->ParseInfoHeader(childIterator,0);
    }
  }
  
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
  Element->GetScalarAttribute("BytesInc",Data->BytesInc);
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
  Element->GetScalarAttribute("BytesInc",Data->BytesInc);
  Element->GetScalarAttribute("BitInc",Data->BitInc);
} 

//int vtkLIFReader::IsValidLIFFile()
//{
//}

//int vtkLIFReader::GetNumberOfChannels()
//{
//}

void vtkLIFReader::Clear()
{
  if (this->File)
    {
    this->File->close();
    delete this->File;
    this->File = NULL;
    delete [] this->FileName;
    this->FileName = NULL;
    this->FileSize = 0;
    }

// These deletes also every item in vectors
  if (this->Channels) delete this->Channels;
  if (this->Dimensions) delete this->Dimensions;
  if (this->Images) delete this->Images;
  if (this->Offsets) this->Offsets->Delete();
  if (this->ImageSizes) this->ImageSizes->Delete();

  this->Dimensions = NULL;
  this->Channels = NULL;
  this->Images = NULL;
  this->Offsets = NULL;
  this->ImageSizes = NULL;
  this->HeaderInfoRead = 0;
  this->CurrentImage = -1;
  this->CurrentChannel = -1;
  this->CurrentTimePoint = -1;
}

int vtkLIFReader::RequestInformation(vtkInformation* vtkNotUsed(request),
                                     vtkInformationVector** vtkNotUsed(inputVector),
                                     vtkInformationVector *outputVector)
{
  vtkInformation *info = outputVector->GetInformationObject(0);
  if (!this->HeaderInfoRead)
    {
      if (!this->ReadLIFHeader())
	{
	  vtkErrorMacro(<< "RequestInformation: Couldn't read file header.");
	  return 0;
	}
    }

  double *spacing = new double[3];
  int *extent =  new int[6];
  double *origin = new double[3];
  this->CalculateExtentAndSpacingAndOrigin(extent,spacing,origin);

  info->Set(vtkDataObject::SPACING(),spacing,3);
  info->Set(vtkStreamingDemandDrivenPipeline::WHOLE_EXTENT(),extent,6);
  info->Set(vtkDataObject::ORIGIN(),origin,3);
  vtkDataObject::SetPointDataActiveScalarInfo(info,VTK_UNSIGNED_SHORT,1);

  return 1;
}

int vtkLIFReader::RequestUpdateExtent(vtkInformation* vtkNotUsed(request),
                                      vtkInformationVector** vtkNotUsed(inputVector),
                                      vtkInformationVector *outputVector)
{
  return 1;
}

int vtkLIFReader::RequestData(vtkInformation *request,
                              vtkInformationVector **inputVector,
                              vtkInformationVector *outputVector)
{
  int extent[6];
  unsigned int imageOffset;
  unsigned int channelOffset;
  unsigned int bufferSize;
  unsigned char *buffer;

  if (!this->HeaderInfoRead || this->CurrentImage < 0 || this->CurrentChannel < 0)
    {
      vtkErrorMacro(<< "RequestData: Header info isn't read or CurrentImage or CurrentChannel is less than 0.");
      return 0;
    }
	
  vtkInformation *outInfo = outputVector->GetInformationObject(0);
  vtkImageData *imageData = this->AllocateOutputData(outInfo->Get(vtkDataObject::DATA_OBJECT()));
  imageData->GetPointData()->GetScalars()->SetName("LIF Scalars");
  imageData->GetExtent(extent);

  int nSlices = extent[5] > extent[4] ? extent[5]-extent[4]+1 : 1;
  unsigned int nVoxels = this->GetImageVoxelCount(this->CurrentImage);
  unsigned int slicePixels = this->GetImageSlicePixelCount(this->CurrentImage);
  unsigned int slicePixelsSize = slicePixels; // Currently only 8 bit data
  unsigned int sliceChannelsSize = slicePixelsSize * this->GetChannelCount(this->CurrentImage);

  if (nSlices > 1) // Allocate array for all slices and read all of them
    {
      if (nVoxels == 0) nVoxels = slicePixelsSize;
      bufferSize = nVoxels; // Currently only 8 bit data
    }
  else // Allocate array only for one slice and read only one slice
    {
      bufferSize = slicePixelsSize; // Currently only 8 bit data
    }

  cout << "extent: " << extent[4] << "," << extent[5] << endl;
  cout << "Allocated buffer of size: " << bufferSize << endl;
  buffer = new unsigned char[bufferSize];
  unsigned char *pos = buffer;
  imageOffset = this->Offsets->GetValue(this->CurrentImage);
  cout << "Image Offset is: " << imageOffset << endl;

  for (int i = extent[4]; i <= extent[5]; ++i)
    {
      channelOffset = imageOffset + i * sliceChannelsSize;
      channelOffset += this->Channels->at(this->CurrentImage)->at(this->CurrentChannel)->BytesInc;

      this->File->seekg(channelOffset,ios::beg);
      this->File->read((char*)pos,slicePixelsSize);
      cout << "Read " << slicePixelsSize << " bytes of data from " << channelOffset << endl;

      pos += slicePixelsSize;
    }

  vtkUnsignedCharArray *pointDataArray;
  pointDataArray = vtkUnsignedCharArray::New();

  pointDataArray->SetNumberOfComponents(1);
  pointDataArray->SetNumberOfValues(bufferSize);
  pointDataArray->SetArray(buffer,bufferSize,0);
  imageData->GetPointData()->SetScalars(pointDataArray);
  pointDataArray->Delete();

  return 1;
}

void vtkLIFReader::CalculateExtentAndSpacingAndOrigin(int *extent, double *spacing, double *origin)
{
  extent[0] = extent[2] = extent[4] = 0;
  extent[1] = extent[3] = extent[5] = -1;
  spacing[0] = spacing[1] = spacing[2] = 0.0;
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
	      spacing[0] = (*imgDims)->Length / extent[1];
	      origin[0] = (*imgDims)->Origin;
	    }
	}
      else if ((*imgDims)->DimID == DimIDY)
	{
	  extent[3] = (*imgDims)->NumberOfElements - 1;
	  if (strcmp((*imgDims)->Unit,"m") == 0 || strcmp((*imgDims)->Unit,"M") == 0 ||
	      strcmp((*imgDims)->Unit,""))
	    {
	      spacing[1] = (*imgDims)->Length / extent[3];
	      origin[1] = (*imgDims)->Origin;
	    }
	}
      else if ((*imgDims)->DimID == DimIDZ)
	{
	  extent[5] = (*imgDims)->NumberOfElements - 1;
	  if (strcmp((*imgDims)->Unit,"m") == 0 || strcmp((*imgDims)->Unit,"M") == 0 ||
	      strcmp((*imgDims)->Unit,""))
	    {
	      spacing[2] = (*imgDims)->Length / extent[5];
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
  vtkByteSwap::Swap4LE((unsigned int*)buff);
 #endif
  return *((int*)(buffer));
}

unsigned int vtkLIFReader::ReadUnsignedInt(ifstream *ifs)
{
  char buffer[4];
  ifs->read(buffer,4);
 #ifdef VTK_WORDS_BIGENDIAN
  vtkByteSwap::Swap4LE((unsigned int*)buff);
 #endif
  return *((unsigned int*)(buffer));
}

void vtkLIFReader::PrintData(vtkImageData *printArray, int i)
{
  int components = printArray->GetPointData()->GetScalars()->GetNumberOfComponents();
  cout << "Components: " << components << endl;
 
  vtkUnsignedCharArray *data = (vtkUnsignedCharArray*)(printArray->GetPointData()->GetScalars());
  int *value;
  value = (int*)(data->GetValue(i));
  cout << "Value " << i << " is " << value << endl;
}

void vtkLIFReader::PrintColorData(vtkImageData *printArray, int i)
{
  int components = printArray->GetPointData()->GetScalars()->GetNumberOfComponents();
  cout << "Components: " << components << endl;

  cout << "Component " << i << " is (" 
       << printArray->GetPointData()->GetScalars()->GetComponent(i,0) << ","
       << printArray->GetPointData()->GetScalars()->GetComponent(i,1) << ","
       << printArray->GetPointData()->GetScalars()->GetComponent(i,2) << ")"
       << endl;
}
