/*=========================================================================

  Program:   BioImageXD
  Module:    vtkOMETIFFReader.cxx
  Language:  C++
  Date:      $Date$
  Version:   $Revision$

 This is an open-source copyright as follows:
 Copyright (c) 2012 BioImageXD Development Team
 
 All rights reserved.
 
 Redistribution and use in source and binary forms, with or without
 modification, are permitted provided that the following conditions are met: 
 
 * Redistributions of source code must retain the above copyright notice,
   this list of conditions and the following disclaimer. 

 * Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.   

 * Modified source versions must be plainly marked as such, and must not be
   misrepresented as being the original software.   

 THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS ``AS
 IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
 THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
 PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHORS OR CONTRIBUTORS BE
 LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
 CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
 SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
 CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 POSSIBILITY OF SUCH DAMAGE.          

=========================================================================*/

#include "vtkOMETIFFReader.h"
#include "vtkXMLDataParser.h"
#include "vtkObjectFactory.h"
#include "vtkInformation.h"
#include "vtkInformationVector.h"
#include "vtkStreamingDemandDrivenPipeline.h"
#include "vtkDataObject.h"
#include "vtkImageData.h"
#include "vtkPointData.h"
#include <limits>

vtkStandardNewMacro(vtkOMETIFFReader);

vtkOMETIFFReader::vtkOMETIFFReader()
{
  this->SetNumberOfInputPorts(0);
  this->SetNumberOfOutputPorts(1);

  this->File = NULL;
  this->FileName = NULL;
  this->FilePath = NULL;
  this->Files = new CharVector;
  this->Images = new OMEImageVector;
  this->TiffDatas = new TiffDataVector;
  this->Mapping = new TupleVector;

  this->Clean();
}

vtkOMETIFFReader::~vtkOMETIFFReader()
{
  this->Clean();
  delete this->Mapping;
  delete this->TiffDatas;
  delete this->Images;
  delete this->Files;
}

int vtkOMETIFFReader::Clean()
{
  this->Files->clear();
  this->Images->clear();
  this->TiffDatas->clear();
  this->Mapping->clear();

  if (this->File) this->File = NULL;
  if (this->FileName) delete [] this->FileName;
  this->FileName = NULL;
  if (this->FilePath) delete [] this->FilePath;
  this->FilePath = NULL;

  this->HeaderRead = 0;
  this->CurrentImage = 0;
  this->CurrentTimePoint = 0;
  this->CurrentChannel = 0;
  for (int i = 0; i < 3; ++i)
	{
	  this->ImageDimensions[i] = 0;
	  this->VoxelSize[i] = 0.0;
	}

  this->Modified();
}

int vtkOMETIFFReader::SetFileName(const char* filename)
{
  if (!filename)
	{
	  vtkDebugMacro(<< "Filename not given");
	  return 0;
	}
  if (this->FileName && !strcmp(this->FileName,filename))
	{
	  vtkDebugMacro(<< "Filename already set");
	  return 0;
	}

  this->Clean();

  this->FileName = new char[strlen(filename)+1];
  strcpy(this->FileName, filename);
  std::string str(this->FileName);
  std::string sep("/");

#ifdef _WIN32
  sep = "\\";
#endif

  const char* path = str.substr(0, str.find_last_of(sep) + 1).c_str();
  this->FilePath = new char[strlen(path)+1];
  strcpy(this->FilePath, path);
  this->Files->push_back(this->FileName);

  return 1;
}

int vtkOMETIFFReader::ReadOMEHeader()
{
  if (!this->FileName)
	{
	  vtkErrorMacro(<< "ReadOMEHeader: Filename not specified");
	  return 0;
	}

  this->File = TIFFOpen(this->FileName, "r");
  if (!this->File)
	{
	  vtkErrorMacro(<< "ReadOMEHeader: Could not open file " << this->FileName);
	  return 0;
	}

  char* header = NULL;
  int returncode;
  size_t chars;

  TIFFGetField(this->File, TIFFTAG_IMAGEDESCRIPTION, &header);
  chars = strlen(header);
  returncode = this->ParseXMLHeader(header,chars);
  TIFFClose(this->File);

  if (returncode)
	{
	  this->HeaderRead = 1;
	  this->SetImageDimensions();
	  this->SetVoxelSize();
	  this->CreateImageMapping();
	  return 1;
	}

  return 0;
}

int vtkOMETIFFReader::ParseXMLHeader(const char* header, size_t chars)
{
  vtkXMLDataParser *parser = vtkXMLDataParser::New();
  parser->InitializeParser();
  parser->ParseChunk(header,chars);

  if (!parser->CleanupParser())
	{
	  parser->Delete();
	  vtkErrorMacro(<< "ParseXMLHeader: Couldn't parse XML");
	  return 0;
	}

  vtkXMLDataElement* rootElement = parser->GetRootElement();
  if (!rootElement)
	{
	parser->Delete();
    vtkErrorMacro(<< "ParseXMLHeader: No root element found")
    return 0;
	}

  int numOfNestedElements = rootElement->GetNumberOfNestedElements();
  vtkXMLDataElement* nestedIter;
  int found = 0;
  for (int i = 0; i < numOfNestedElements; ++i)
	{
	  nestedIter = rootElement->GetNestedElement(i);
	  if (!strcmp(nestedIter->GetName(),"Image"))
		{
		  this->CreateImages(nestedIter); // Create own Image for each Pixels
		  found = 1;
		}
	}

  parser->Delete();
  if (!found)
	{
	  vtkErrorMacro(<< "ParseXMLHeader: No image element found");
	  return 0;
	}

  return 1;
}

int vtkOMETIFFReader::CreateImages(vtkXMLDataElement* imageElement)
{
  // Create own Image for each Pixels, bit different from OME specs, but easier
  // to handle
  int numOfNestedElements = imageElement->GetNumberOfNestedElements();
  vtkXMLDataElement* nestedIter;
  for (int i = 0; i < numOfNestedElements; ++i)
	{
	  nestedIter = imageElement->GetNestedElement(i);
	  const char* name = nestedIter->GetName();
	  if (!strcmp(name,"Pixels")) this->CreateImage(imageElement, nestedIter);
	}
}

int vtkOMETIFFReader::CreateImage(vtkXMLDataElement* imageElement, vtkXMLDataElement* pixelsElement)
{
  OMEImage* Image = new OMEImage();
  const char* attr_name = imageElement->GetAttribute("Name");
  const char* attr_dimorder = pixelsElement->GetAttribute("DimensionOrder");
  const char* attr_type = pixelsElement->GetAttribute("Type");
  if (attr_type == NULL) attr_type = pixelsElement->GetAttribute("PixelType");

  int strlen_type = strlen(attr_type);
  int strlen_dimorder = strlen(attr_dimorder);
  Image->Name = new char[strlen(attr_name)+1];
  Image->Pixels->DimensionOrder = new char[strlen_dimorder+1];
  Image->Pixels->Type = new char[strlen_type+1];
  strcpy(Image->Name,attr_name);
  for (int i = 0; i < strlen_dimorder; ++i) Image->Pixels->DimensionOrder[i] = toupper(attr_dimorder[i]);
  for (int i = 0; i < strlen_type; ++i) Image->Pixels->Type[i] = tolower(attr_type[i]);
  Image->Pixels->DimensionOrder[strlen_dimorder] = '\0';
  Image->Pixels->Type[strlen_type] = '\0';

  if (!strcmp(Image->Pixels->Type,"uint8"))
	Image->Pixels->TypeID = VTK_UNSIGNED_CHAR;
  else if (!strcmp(Image->Pixels->Type,"uint16"))
	Image->Pixels->TypeID = VTK_UNSIGNED_SHORT;
  else if (!strcmp(Image->Pixels->Type,"uint32"))
	Image->Pixels->TypeID = VTK_UNSIGNED_INT;
  else if (!strcmp(Image->Pixels->Type,"int8"))
	Image->Pixels->TypeID = VTK_CHAR;
  else if (!strcmp(Image->Pixels->Type,"int16"))
	Image->Pixels->TypeID = VTK_SHORT;
  else if (!strcmp(Image->Pixels->Type,"int32"))
	Image->Pixels->TypeID = VTK_INT;
  else if (!strcmp(Image->Pixels->Type,"float"))
	Image->Pixels->TypeID = VTK_FLOAT;
  else if (!strcmp(Image->Pixels->Type,"double"))
	Image->Pixels->TypeID = VTK_DOUBLE;

  pixelsElement->GetScalarAttribute("SizeX", Image->Pixels->SizeX);
  pixelsElement->GetScalarAttribute("SizeY", Image->Pixels->SizeY);
  pixelsElement->GetScalarAttribute("SizeZ", Image->Pixels->SizeZ);
  pixelsElement->GetScalarAttribute("SizeT", Image->Pixels->SizeT);
  pixelsElement->GetScalarAttribute("SizeC", Image->Pixels->SizeC);
  pixelsElement->GetScalarAttribute("PhysicalSizeX", Image->Pixels->PhysicalSizeX);
  pixelsElement->GetScalarAttribute("PhysicalSizeY", Image->Pixels->PhysicalSizeY);
  pixelsElement->GetScalarAttribute("PhysicalSizeZ", Image->Pixels->PhysicalSizeZ);

  // Create channel and plane objects
  int numOfNestedElements = pixelsElement->GetNumberOfNestedElements();
  vtkXMLDataElement* nestedIter;
  for (int i = 0; i < numOfNestedElements; ++i)
	{
	  nestedIter = pixelsElement->GetNestedElement(i);
	  const char* name = nestedIter->GetName();
	  if (!strcmp(name,"Channel"))
		{
		  OMEChannel* Channel = new OMEChannel();
		  Channel->Name = nestedIter->GetAttribute("Name");
		  nestedIter->GetScalarAttribute("Color", Channel->Color);
		  nestedIter->GetScalarAttribute("EmissionWavelength", Channel->EmissionWavelength);
		  nestedIter->GetScalarAttribute("ExcitationWavelength", Channel->ExcitationWavelength);
		  Image->Pixels->Channels->push_back(Channel);
		}
	  else if (!strcmp(name,"Plane"))
		{
		  OMEPlane* Plane = new OMEPlane();
		  nestedIter->GetScalarAttribute("DeltaT", Plane->DeltaT);
		  nestedIter->GetScalarAttribute("ExposureTime", Plane->ExposureTime);
		  nestedIter->GetScalarAttribute("PositionX", Plane->PositionX);
		  nestedIter->GetScalarAttribute("PositionY", Plane->PositionY);
		  nestedIter->GetScalarAttribute("PositionZ", Plane->PositionZ);
		  Image->Pixels->Planes->push_back(Plane);
		}
	  else if (!strcmp(name,"TiffData"))
		{
		  vtkXMLDataElement* saveTiffData = vtkXMLDataElement::New();
		  saveTiffData->DeepCopy(nestedIter);
		  this->TiffDatas->push_back(saveTiffData);
		  vtkXMLDataElement* uuidElement = nestedIter->FindNestedElementWithName("UUID");
		  if (uuidElement)
			{
			  const char* fname = uuidElement->GetAttribute("FileName");
			  if (fname)
				{
				  std::string relpathstr(fname);
				  std::string abspathstr(this->FilePath);
				  abspathstr += relpathstr;
				  const char* relpath = relpathstr.c_str();
				  const char* abspath = abspathstr.c_str();
				  int found = 0;
				  CharVector::const_iterator fiter;
				  for (fiter = this->Files->begin(); fiter != this->Files->end(); fiter++)
					{
					  if (!(strcmp(relpath,*fiter) && strcmp(abspath,*fiter))) found = 1;
					}
				  if (!found) {
				// Test whether original filename can be opened or if absolute
				// file path is needed and save the one that is working
					const char* fname2;
					ifstream* openFile = new ifstream(relpath, ios::in | ios::binary);
					if (!openFile || openFile->fail()) {
					  fname2 = abspath;
					}
					else {
					  openFile->close();
					  fname2 = relpath;
					}
					if (openFile) delete openFile;

					char* cpy_fname = new char[strlen(fname2)+1];
					strcpy(cpy_fname,fname2);
					this->Files->push_back(cpy_fname);
				  }
				}
			}
		}
	}

  // Do Leica matrix screener hack. Individual ome.tif file from Leica matrix
  // defines SizeZ, SizeT and SizeC to be 1 even though there are many files
  // referenced in TiffDatas. Check the largest values and save in Pixels
  int largestSizeZ = Image->Pixels->SizeZ;
  int largestSizeT = Image->Pixels->SizeT;
  int largestSizeC = Image->Pixels->SizeC;
  int readFirstZ, readFirstT, readFirstC;
  TiffDataVector::const_iterator iter;
  for (iter = this->TiffDatas->begin(); iter != this->TiffDatas->end(); ++iter)
	{
	  if ((*iter)->GetScalarAttribute("FirstZ",readFirstZ) && readFirstZ + 1 > largestSizeZ)
		largestSizeZ = readFirstZ + 1;
	  if ((*iter)->GetScalarAttribute("FirstT",readFirstT) && readFirstT + 1 > largestSizeT)
		largestSizeT = readFirstT + 1;
	  if ((*iter)->GetScalarAttribute("FirstC",readFirstC) && readFirstC + 1 > largestSizeC)
		largestSizeC = readFirstC + 1;
	}
  Image->Pixels->SizeZ = largestSizeZ;
  Image->Pixels->SizeT = largestSizeT;
  Image->Pixels->SizeC = largestSizeC;

  this->Images->push_back(Image);

  return 1;
}

void vtkOMETIFFReader::CreateImageMapping()
{
// Map how each image is distributed into files and where each slice,
// time point and channel can be found
  OMEImageVector::const_iterator image_iter = this->Images->begin();
  OMEPixels* pixels;
  unsigned int earlierImages = 0;
  for (image_iter = this->Images->begin(); image_iter != this->Images->end(); image_iter++)
	{
	  pixels = (*image_iter)->Pixels;
	  unsigned int zinc, tinc, cinc;
	  if (!strcmp(pixels->DimensionOrder,"XYZTC"))
		{
		  zinc = 1;
		  tinc = pixels->SizeZ;
		  cinc = pixels->SizeZ * pixels->SizeT;
		}
	  else if (!strcmp(pixels->DimensionOrder,"XYZCT"))
		{
		  zinc = 1;
		  cinc = pixels->SizeZ;
		  tinc = pixels->SizeZ * pixels->SizeC;
		}
	  else if (!strcmp(pixels->DimensionOrder,"XYTZC"))
		{
		  tinc = 1;
		  zinc = pixels->SizeT;
		  cinc = pixels->SizeT * pixels->SizeZ;
		}
	  else if (!strcmp(pixels->DimensionOrder,"XYTCZ"))
		{
		  tinc = 1;
		  cinc = pixels->SizeT;
		  zinc = pixels->SizeT * pixels->SizeC;
		}
	  else if (!strcmp(pixels->DimensionOrder,"XYCZT"))
		{
		  cinc = 1;
		  zinc = pixels->SizeC;
		  tinc = pixels->SizeC * pixels->SizeZ;
		}
	  else
		{
		  cinc = 1;
		  tinc = pixels->SizeC;
		  zinc = pixels->SizeC * pixels->SizeT;
		}

	  unsigned int numberOfImages = pixels->SizeZ * pixels->SizeT * pixels->SizeC;
	  unsigned int imagesPerFile = numberOfImages / this->Files->size();

	  for (unsigned int c = 0; c < pixels->SizeC; ++c)
		{
		  for (unsigned int t = 0; t < pixels->SizeT; ++t)
			{
			  for (unsigned int z = 0; z < pixels->SizeZ; ++z)
				{
				  unsigned int position = z*zinc + t*tinc + c*cinc;
				  unsigned int file_position = this->FindFilePosition(z,t,c,zinc,tinc,cinc);
				  position -= file_position * imagesPerFile;
				  position += earlierImages;
				  printf("Add to mapping (%d,%d)\n",file_position,position);
				  Tuple* tpl = new Tuple(file_position, position);
				  this->Mapping->push_back(tpl);
				}
			}
		}
	  earlierImages += pixels->SizeZ * pixels->SizeT * pixels->SizeC;
	}
}

int vtkOMETIFFReader::RequestInformation(vtkInformation* vtkNotUsed(request),
										 vtkInformationVector** vtkNotUsed(inputVector),
										 vtkInformationVector* outputVector)
{
  if (!this->HeaderRead)
	{
	  if (!this->ReadOMEHeader())
		{
		  vtkErrorMacro(<< "RequestInformation: Could not read file header");
		  return 0;
		}
	}

  double origin[3] = {0.0, 0.0, 0.0};
  double spacing[3] = {1.0, 1.0, 1.0};
  int extent[6] = {0, 0, 0, 0, 0, 0};

  OMEPixels* curPixels = this->Images->at(this->CurrentImage)->Pixels;
  if (curPixels->PhysicalSizeX > std::numeric_limits<double>::epsilon())
	{
	  spacing[1] = curPixels->PhysicalSizeY / curPixels->PhysicalSizeX;
	  spacing[2] = curPixels->PhysicalSizeZ / curPixels->PhysicalSizeX;
	}
  extent[1] = curPixels->SizeX - 1;
  extent[3] = curPixels->SizeY - 1;
  extent[5] = curPixels->SizeZ - 1;

  vtkInformation* info = outputVector->GetInformationObject(0);
  info->Set(vtkStreamingDemandDrivenPipeline::WHOLE_EXTENT(),extent,6);
  info->Set(vtkDataObject::ORIGIN(),origin,3);
  info->Set(vtkDataObject::SPACING(),spacing,3);

  if (curPixels->TypeID == VTK_UNSIGNED_CHAR)
	vtkDataObject::SetPointDataActiveScalarInfo(info,VTK_UNSIGNED_CHAR,1);
  else if (curPixels->TypeID == VTK_UNSIGNED_SHORT)
	vtkDataObject::SetPointDataActiveScalarInfo(info,VTK_UNSIGNED_SHORT,1);
  else if (curPixels->TypeID == VTK_UNSIGNED_INT)
	vtkDataObject::SetPointDataActiveScalarInfo(info,VTK_UNSIGNED_INT,1);
  else if (curPixels->TypeID == VTK_CHAR)
	vtkDataObject::SetPointDataActiveScalarInfo(info,VTK_CHAR,1);
  else if (curPixels->TypeID == VTK_SHORT)
	vtkDataObject::SetPointDataActiveScalarInfo(info,VTK_SHORT,1);
  else if (curPixels->TypeID == VTK_INT)
	vtkDataObject::SetPointDataActiveScalarInfo(info,VTK_INT,1);
  else if (curPixels->TypeID == VTK_FLOAT)
	vtkDataObject::SetPointDataActiveScalarInfo(info,VTK_FLOAT,1);
  else if (curPixels->TypeID == VTK_DOUBLE)
	vtkDataObject::SetPointDataActiveScalarInfo(info,VTK_DOUBLE,1);

  return 1;
}

int vtkOMETIFFReader::RequestUpdateExtent(vtkInformation* vtkNotUsed(request),
										 vtkInformationVector** vtkNotUsed(inputVector),
										 vtkInformationVector* outputVector)
{
  int uext[6], ext[6];
  vtkInformation* info = outputVector->GetInformationObject(0);
  info->Get(vtkStreamingDemandDrivenPipeline::WHOLE_EXTENT(), ext);
  info->Get(vtkStreamingDemandDrivenPipeline::UPDATE_EXTENT(), uext);
  // Make request to be at least single slice
  if (uext[1] < ext[1]) uext[1] = ext[1];
  if (uext[3] < ext[3]) uext[3] = ext[3];
  if (uext[0] > 0) uext[0] = 0;
  if (uext[2] > 0) uext[2] = 0;
  info->Set(vtkStreamingDemandDrivenPipeline::UPDATE_EXTENT(), uext, 6);

  return 1;
}

// Templated function to handle different data types
template <typename OT>
void vtkOMETIFFReaderUpdate(vtkOMETIFFReader* self, vtkImageData* data, OT* outPtr)
{
  int ext[6], wext[6];
  data->GetExtent(ext);
  data->GetWholeExtent(wext);
  unsigned int currentImage = self->GetCurrentImage();
  unsigned int currentTimePoint = self->GetCurrentTimePoint();
  unsigned int currentChannel = self->GetCurrentChannel();

  int imgIncr = currentTimePoint * (wext[5]+1) + currentChannel * (wext[5]+1) * self->Images->at(currentImage)->Pixels->SizeT;
  // Add also other OMEImages images to increment
  OMEPixels* imgPixels;
  for (int i = 0; i < currentImage; ++i)
	{
	  imgPixels = self->Images->at(i)->Pixels;
	  imgIncr += imgPixels->SizeZ * imgPixels->SizeT * imgPixels->SizeC;
	}

  // Read images to buffer
  imgPixels = self->Images->at(currentImage)->Pixels;
  int imgIndex;
  unsigned int curFileNum;
  TIFF* tiffImage = NULL;
  unsigned int width = imgPixels->SizeX;
  unsigned int height = imgPixels->SizeY;
  unsigned int isize = (ext[5]-ext[4]+1) * width * height * sizeof(OT);
  tdata_t buf = _TIFFmalloc(isize);

  for (int zslice = ext[4]; zslice <= ext[5]; ++zslice)
	{
	  imgIndex = imgIncr + zslice;
	  Tuple* slicePointer = self->Mapping->at(imgIndex);

	  if (tiffImage == NULL || curFileNum != slicePointer->first)
		{
		  if (tiffImage != NULL) TIFFClose(tiffImage);
		  curFileNum = slicePointer->first;
		  tiffImage = TIFFOpen(self->Files->at(curFileNum), "r");
		}

	  TIFFSetDirectory(tiffImage,slicePointer->second);
	  for (unsigned int row = 0; row < height; ++row)
		{
		  if (TIFFReadScanline(tiffImage, buf, row) == -1)
			{
			  //vtkErrorMacro(<< "Problem reading row " << row << " of directory " << slicePointer->second << " of file " << self->Files->at(curFileNum));
			  break;
			}
		  OT* buf2 = (OT*)buf;
		  for (unsigned int counter = 0; counter < width; ++counter)
			{
			  *outPtr++ = *buf2++;
			}
		}
	}

  _TIFFfree(buf);
  if (tiffImage != NULL) TIFFClose(tiffImage);
}

int vtkOMETIFFReader::RequestData(vtkInformation* vtkNotUsed(request),
								  vtkInformationVector** vtkNotUsed(inputVector),
								  vtkInformationVector* outputVector)
{
  vtkInformation* info = outputVector->GetInformationObject(0);
  vtkImageData* imageData = this->AllocateOutputData(info->Get(vtkDataObject::DATA_OBJECT()));
  imageData->GetPointData()->GetScalars()->SetName("OME-TIFF scalars");

  void* outPtr = imageData->GetScalarPointer();
  switch (imageData->GetScalarType())
	{
	  vtkTemplateMacro3(vtkOMETIFFReaderUpdate, this, imageData, (VTK_TT*)(outPtr));
	default:
	  vtkErrorMacro(<< "Unknown data type");
	  return 0;
	}

  return 1;
}

int vtkOMETIFFReader::SetCurrentImage(unsigned int curimg)
{
  if (this->CurrentImage == curimg) return 1;

  this->Modified();
  if (curimg < 0 || curimg >= this->Images->size())
	{
	  this->CurrentImage = 0;
	  return 0;
	}

  this->CurrentImage = curimg;
  this->CurrentTimePoint = 0;
  this->CurrentChannel = 0;
  this->SetImageDimensions();
  this->SetVoxelSize();

  return 1;
}

int vtkOMETIFFReader::SetCurrentTimePoint(unsigned int curtp)
{
  if (this->CurrentTimePoint == curtp) return 1;

  this->Modified();
  if (this->Images->size() == 0 || curtp < 0 ||
	  curtp >= this->Images->at(this->CurrentImage)->Pixels->SizeT)
	{
	  this->CurrentTimePoint = 0;
	  return 0;
	}

  this->CurrentTimePoint = curtp;
  return 1;
}

int vtkOMETIFFReader::SetCurrentChannel(unsigned int curch)
{
  if (this->CurrentChannel == curch) return 1;

  this->Modified();
  if (this->Images->size() == 0 || curch < 0 ||
	  curch >= this->Images->at(this->CurrentImage)->Pixels->SizeC)
	{
	  this->CurrentChannel = 0;
	  return 0;
	}

  this->CurrentChannel = curch;
  return 1;
}

void vtkOMETIFFReader::SetImageDimensions()
{
  if (!this->HeaderRead)
	{
	  vtkErrorMacro(<< "OME header not read");
	  return;
	}

  OMEPixels* pixels = this->Images->at(this->CurrentImage)->Pixels;
  this->ImageDimensions[0] = pixels->SizeX;
  this->ImageDimensions[1] = pixels->SizeY;
  this->ImageDimensions[2] = pixels->SizeZ;
}

void vtkOMETIFFReader::SetVoxelSize()
{
  if (!this->HeaderRead)
	{
	  vtkErrorMacro(<< "Ome header not read");
	  return;
	}
  
  OMEPixels* pixels = this->Images->at(this->CurrentImage)->Pixels;
  this->VoxelSize[0] = pixels->PhysicalSizeX;
  this->VoxelSize[1] = pixels->PhysicalSizeY;
  this->VoxelSize[2] = pixels->PhysicalSizeZ;
}

unsigned int vtkOMETIFFReader::FindFilePosition(unsigned int z, unsigned int t, unsigned int c, unsigned int zinc, unsigned int tinc, unsigned int cinc)
{
  int num_files = this->Files->size();
  int num_channels = this->GetNumberOfChannels();
  int num_timepoints = this->GetNumberOfTimePoints();
  int num_slices = this->Images->at(this->CurrentImage)->Pixels->SizeZ;
  if (num_files == 1) return 0;

  int num_tc = num_timepoints * num_channels;
  int num_st = num_slices * num_timepoints;
  int num_sc = num_slices * num_channels;
  int num_stc = num_slices * num_timepoints * num_channels;

  if (this->TiffDatas->size() > 0 && this->TiffDatas->at(0)->FindNestedElementWithName("UUID"))
	{
	  int size = this->TiffDatas->size();
	  for (int i = 0; i < size; ++i)
		{
		  vtkXMLDataElement* element = this->TiffDatas->at(i);
		  int FirstZ, FirstT, FirstC = -1;
		  if (!element->GetScalarAttribute("FirstZ",FirstZ)) FirstZ = z;
		  if (!element->GetScalarAttribute("FirstT",FirstT)) FirstT = t;
		  if (!element->GetScalarAttribute("FirstC",FirstC)) FirstC = c;
		  if (FirstZ == z && FirstT == t && FirstC == c) return i;
		}
	}
  else // Check image files by dimension order
	{
	  if (zinc == 1)
		{
		  if (tinc < cinc)
			{
			  if (num_files == num_channels) return c;
			  if (num_files == num_tc) return t*num_channels + c;
			  if (num_files == num_stc) return z*num_tc + t*num_channels + c;
			}
		  else
			{
			  if (num_files == num_timepoints) return t;
			  if (num_files == num_tc) return c*num_timepoints + t;
			  if (num_files == num_stc) return z*num_tc + c*num_timepoints + t;
			}
		}
	  else if (tinc == 1)
		{
		  if (zinc < cinc)
			{
			  if (num_files == num_channels) return c;
			  if (num_files == num_sc) return z*num_channels + c;
			  if (num_files == num_stc) return t*num_sc + z*num_channels + c;
			}
		  else
			{
			  if (num_files == num_slices) return z;
			  if (num_files == num_sc) return c*num_slices + z;
			  if (num_files == num_stc) return t*num_sc + c*num_slices + z;
			}
		}
	  else if (cinc == 1)
		{
		  if (zinc < tinc)
			{
			  if (num_files == num_timepoints) return t;
			  if (num_files == num_st) return z*num_timepoints + t;
			  if (num_files == num_stc) return c*num_st + z*num_timepoints + t;
			}
		  else
			{
			  if (num_files == num_slices) return z;
			  if (num_files == num_st) return t*num_slices + z;
			  if (num_files == num_stc) return c*num_st + t*num_slices + z;
			}
		}
	}

  return 0;
}

const char* vtkOMETIFFReader::GetImageName()
{
  if (!this->HeaderRead)
	{
	  vtkErrorMacro(<< "Image not defined");
	  return "";
	}
  if (this->Images->at(this->CurrentImage)->Name != NULL)
	return this->Images->at(this->CurrentImage)->Name;
  else
	return "";
}

const char* vtkOMETIFFReader::GetChannelName()
{
  if (!this->HeaderRead)
	{
	  vtkErrorMacro(<< "Channel not defined");
	  return "";
	}

  OMEPixels* pixels = this->Images->at(this->CurrentImage)->Pixels;
  if (pixels->Channels->size() > this->CurrentChannel &&
	  pixels->Channels->at(this->CurrentChannel)->Name != NULL)
	return pixels->Channels->at(this->CurrentChannel)->Name;
  else
	return "";
}

int vtkOMETIFFReader::GetNumberOfTimePoints()
{
  if (!this->HeaderRead)
	{
	  vtkErrorMacro(<< "Header not read");
	  return 0;
	}
  return this->Images->at(this->CurrentImage)->Pixels->SizeT;
}

int vtkOMETIFFReader::GetNumberOfChannels()
{
  if (!this->HeaderRead)
	{
	  vtkErrorMacro(<< "Header not read");
	  return 0;
	}
  return this->Images->at(this->CurrentImage)->Pixels->SizeC;
}

unsigned int vtkOMETIFFReader::GetPixelType()
{
  if (!this->HeaderRead)
	{
	  vtkErrorMacro(<< "Header not read");
	  return 0;
	}
  return this->Images->at(this->CurrentImage)->Pixels->TypeID;
}

void vtkOMETIFFReader::PrintSelf(ostream& os, vtkIndent indent)
{
  this->Superclass::PrintSelf(os,indent);
  OMEPixels* pixels;
  OMEImage* image;
  for (int i = 0; i < this->Images->size(); ++i)
	{
	  image = this->Images->at(i);
	  pixels = image->Pixels;
	  os << indent << "Image: " << image->Name  << std::endl;
	  os << indent << indent << "SizeX: " << pixels->SizeX << std::endl;
	  os << indent << indent << "SizeY: " << pixels->SizeY << std::endl;
	  os << indent << indent << "SizeZ: " << pixels->SizeZ << std::endl;
	  os << indent << indent << "SizeT: " << pixels->SizeT << std::endl;
	  os << indent << indent << "SizeC: " << pixels->SizeC << std::endl;
	  os << indent << indent << "PhysicalSizeX: " << pixels->PhysicalSizeX << std::endl;
	  os << indent << indent << "PhysicalSizeY: " << pixels->PhysicalSizeY << std::endl;
	  os << indent << indent << "PhysicalSizeZ: " << pixels->PhysicalSizeZ << std::endl;
	  os << indent << indent << "TimeIncrement: " << pixels->TimeIncrement << std::endl;
	  os << indent << indent << "Type: " << pixels->Type << std::endl;
	  os << indent << indent << "DimensionOrder: " << pixels->DimensionOrder << std::endl;
	}
}
