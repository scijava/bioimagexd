/*=========================================================================

  Program:   BioImageXD
  Module:    vtkOMETIFFWriter.cxx
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

#include "vtkOMETIFFWriter.h"
#include "vtkObjectFactory.h"
#include "vtkDataObject.h"
#include "vtkErrorCode.h"
#include "vtkInformation.h"
#include "vtkInformationVector.h"
#include "vtkStreamingDemandDrivenPipeline.h"
#include "vtkImageData.h"
#include "vtkCommand.h"
#include "vtkXMLDataElement.h"
#include "vtkExtXMLUtilities.h"
#include <sstream>
#include <limits>

vtkStandardNewMacro(vtkOMETIFFWriter);

vtkOMETIFFWriter::vtkOMETIFFWriter()
{
  this->SetNumberOfInputPorts(1);
  this->SetNumberOfOutputPorts(0);
  this->XResolution = 0.0;
  this->YResolution = 0.0;
  this->ZResolution = 0.0;
  this->TimeIncrement = 0.0;
  this->TimePoints = 1;
  this->Channels = 1;
  this->ImageName = NULL;
  this->UseXML = 1; // Whether to write OMETIFF at all or just TIFF stack
  this->FileName = NULL;
  this->FileNamePattern = NULL;
  this->CurrentTimePoint = 0;
  this->CurrentChannel = 0;
  this->UUIDs = NULL;
  this->ChannelsInfo = new ChannelVector();
}

vtkOMETIFFWriter::~vtkOMETIFFWriter()
{
  if (this->FileName) delete[] this->FileName;
  this->FileName = NULL;
  if (this->FileNamePattern) delete[] this->FileNamePattern;
  this->FileNamePattern = NULL;
  if (this->UUIDs) delete[] this->UUIDs;
  this->UUIDs = NULL;
  delete this->ChannelsInfo;
}

int vtkOMETIFFWriter::SetFileName(const char* fn)
{
  if (!fn)
	{
	  vtkErrorMacro(<< "No filename given.");
	  return 0;
	}

  if (this->FileName && !strcmp(this->FileName, fn)) return 0;

  if (this->FileName)
	{
	  delete[] this->FileName;
	  this->FileName = NULL;
	}

  this->FileName = new char[strlen(fn)+1];
  strcpy(this->FileName, fn);
  this->Modified();

  return 1;
}

int vtkOMETIFFWriter::SetUUID(unsigned int i, const char* uuid)
{
  if (this->UUIDs == NULL)
	{
	  vtkErrorMacro(<< "First set number of time points and channels");
	  return 0;
	}
  if (i >= 0 && i < this->TimePoints * this->Channels)
	{
	  char* uuid_str = new char[strlen(uuid)+1];
	  strcpy(uuid_str,uuid);
	  this->UUIDs[i] = uuid_str;
	}
  else
	{
	  vtkErrorMacro(<< "Index out of bounds: " << i);
	  return 0;
	}

  return 1;
}

void vtkOMETIFFWriter::SetTimePoints(unsigned int tp)
{
  if (this->TimePoints != tp)
	{
	  int old_images = this->TimePoints * this->Channels;
	  int images = tp * this->Channels;
	  this->TimePoints = tp;
	  this->UpdateUUIDs(old_images, images);
	}
}

void vtkOMETIFFWriter::SetChannels(unsigned int ch)
{
  if (this->Channels != ch)
	{
	  int old_images = this->TimePoints * this->Channels;
	  int images = this->TimePoints * ch;
	  this->Channels = ch;
	  this->UpdateUUIDs(old_images, images);
	}
}

void vtkOMETIFFWriter::SetChannelInfo(const char* name, int excitation, int emission)
{
  OMEChannel* channel = new OMEChannel();
  channel->ExcitationWavelength = excitation;
  channel->EmissionWavelength = emission;
  char* namestr = new char[strlen(name)+1];
  strcpy(namestr,name);
  channel->Name = namestr;
  this->ChannelsInfo->push_back(channel);
}

void vtkOMETIFFWriter::UpdateUUIDs(unsigned int oldAmnt, unsigned int newAmnt)
{
  if (this->UUIDs)
	{
	  char** new_uuids = new char*[newAmnt];
	  for (int i = 0; i < newAmnt; ++i)
		{
		  new_uuids[i] = NULL;
		}

	  int min = oldAmnt;
	  if (min > newAmnt) min = newAmnt;
	  for (int i = 0; i < min; ++i)
		{
		  if (this->UUIDs[i])
			{
			  char* old_uuid = this->UUIDs[i];
			  char* new_uuid = new char[strlen(old_uuid)+1];
			  strcpy(new_uuid,old_uuid);
			  new_uuids[i] = new_uuid;
			}
		}
	  delete[] this->UUIDs;
	  this->UUIDs = new_uuids;
	}
  else
	{
	  this->UUIDs = new char*[newAmnt];
	  for (int i = 0; i < newAmnt; ++i) // Initialize char*
		{
		  this->UUIDs[i] = NULL;
		}
	}
}

void vtkOMETIFFWriter::Write()
{
  this->UpdateInformation();
  this->GetInput()->SetUpdateExtent(this->GetInput()->GetWholeExtent());
  this->Update();
}

int vtkOMETIFFWriter::WriteXMLHeader(TIFF* tiff, vtkImageData* image, int* wext, unsigned int bps, const char* type)
{
  std::string xmlstring("<?xml version=\"1.0\" encoding=\"UTF-8\"?>");
  std::ostringstream os;
  unsigned int numtiffs = this->TimePoints * this->Channels;
  if (numtiffs == 0) numtiffs = 1;
  int sizeX = wext[1] - wext[0] + 1;
  int sizeY = wext[3] - wext[2] + 1;
  int sizeZ = wext[5] - wext[4] + 1;
  unsigned int imageNum = this->CurrentChannel * this->TimePoints + this->CurrentTimePoint;

  // Create XML structure
  vtkXMLDataElement* rootElement = vtkXMLDataElement::New();
  rootElement->SetName("OME");
  rootElement->SetAttribute("xmlns", "http://www.openmicroscopy.org/Schemas/OME/2011-06");
  rootElement->SetAttribute("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance");
  rootElement->SetAttribute("xsi:schemaLocation", "http://www.openmicroscopy.org/Schemas/OME/2011-06 http://www.openmicroscopy.org/Schemas/OME/2011-06/ome.xsd");
  if (numtiffs > 1)
	{
	  if (this->UUIDs[imageNum])
		{
		  rootElement->SetAttribute("UUID", this->UUIDs[imageNum]);
		}
	  else
		{
		  vtkErrorMacro(<< "UUID for image " << imageNum << " not set");
		  return 0;
		}
	}

  // Create Image element
  vtkXMLDataElement* imageElement = vtkXMLDataElement::New();
  imageElement->SetName("Image");
  imageElement->SetAttribute("ID", "Image:0");
  imageElement->SetAttribute("Name", this->ImageName);
  rootElement->AddNestedElement(imageElement);

  // Create Pixels element
  vtkXMLDataElement* pixelsElement = vtkXMLDataElement::New();
  pixelsElement->SetName("Pixels");
  pixelsElement->SetAttribute("DimensionOrder", "XYZTC");
  pixelsElement->SetAttribute("ID", "Pixels:0");
  pixelsElement->SetIntAttribute("SizeX", sizeX);
  pixelsElement->SetIntAttribute("SizeY", sizeY);
  pixelsElement->SetIntAttribute("SizeZ", sizeZ);
  pixelsElement->SetIntAttribute("SizeT", this->TimePoints);
  pixelsElement->SetIntAttribute("SizeC", this->Channels);
  pixelsElement->SetAttribute("Type", type);
  // Convert double to string, accuracy to Ångström, add only if defined
  char phys_size[12];
  if (this->XResolution > std::numeric_limits<float>::epsilon())
	{
	  sprintf(phys_size, "%6.4f", this->XResolution);
	  pixelsElement->SetAttribute("PhysicalSizeX", phys_size);
	}
  if (this->YResolution > std::numeric_limits<float>::epsilon())
	{
	  sprintf(phys_size, "%6.4f", this->YResolution);
	  pixelsElement->SetAttribute("PhysicalSizeY", phys_size);
	}
  if (this->XResolution > std::numeric_limits<float>::epsilon())
	{
	  sprintf(phys_size, "%6.4f", this->ZResolution);
	  pixelsElement->SetAttribute("PhysicalSizeZ", phys_size);
	}
  if (this->TimeIncrement > std::numeric_limits<float>::epsilon())
	{
	  sprintf(phys_size, "%6.4f", this->TimeIncrement);
	  pixelsElement->SetAttribute("TimeIncrement", phys_size);
	}
  imageElement->AddNestedElement(pixelsElement);

  // Create channels elements
  for (unsigned int i = 0; i < this->ChannelsInfo->size() && i < 1000; ++i)
	{
	  OMEChannel* channel = this->ChannelsInfo->at(i);
	  vtkXMLDataElement* channelElement = vtkXMLDataElement::New();
	  channelElement->SetName("Channel");
	  char ch_id[13];
	  sprintf(ch_id, "Channel:%d", i);
	  channelElement->SetAttribute("ID", ch_id);
	  channelElement->SetAttribute("Name", channel->Name);
	  channelElement->SetIntAttribute("ExcitationWavelength", channel->ExcitationWavelength);
	  channelElement->SetIntAttribute("EmissionWavelength", channel->EmissionWavelength);
	  pixelsElement->AddNestedElement(channelElement);
	}

  // Create TiffData elements
  unsigned int indT = 0;
  unsigned int indC = 0;
  for (unsigned int i = 0; i < numtiffs; ++i)
	{
	  indC = i / this->TimePoints;
	  indT = i - indC * this->TimePoints;

	  vtkXMLDataElement* tiffElement = vtkXMLDataElement::New();
	  tiffElement->SetName("TiffData");
	  pixelsElement->AddNestedElement(tiffElement);

	  if (numtiffs > 1)
		{
		  tiffElement->SetIntAttribute("FirstT", indT);
		  tiffElement->SetIntAttribute("FirstC", indC);

		  char* filename = new char[strlen(this->FileNamePattern) + 100];
		  if (!this->CreateFileName(filename, i, 1))
			{
			  vtkErrorMacro(<< "Could not create file name from pattern");
			  delete[] filename;
			  return 0;
			}
		  if (!this->UUIDs[i])
			{
			  vtkErrorMacro(<< "Not enough uuids set");
			  return 0;
			}
		  vtkXMLDataElement* UUIDElement = vtkXMLDataElement::New();
		  UUIDElement->SetName("UUID");
		  UUIDElement->SetAttribute("FileName", filename);
		  UUIDElement->SetCharacterData(this->UUIDs[i],strlen(this->UUIDs[i]));
		  tiffElement->AddNestedElement(UUIDElement);
		  delete[] filename;
		}
	}

  // Create XML string
  vtkExtXMLUtilities* utilities = vtkExtXMLUtilities::New();
  utilities->FlattenElement(rootElement, os);
  xmlstring += os.str();
  TIFFSetField(tiff, TIFFTAG_IMAGEDESCRIPTION, xmlstring.c_str());

  utilities->Delete();
  rootElement->Delete(); // Removes all nested elements

  return 1;
}

int vtkOMETIFFWriter::WriteTIFFHeader(TIFF* tiff, vtkImageData* image, int* wext, unsigned int bps, unsigned int page)
{
  if (!tiff || !image || !wext) return 0;

  int sampleperpixel = 1;
  int width = wext[1] - wext[0] + 1;
  int height = wext[3] - wext[2] + 1;
  int slices = wext[5] - wext[4] + 1;
  int bytes = bps / 8;
  TIFFSetField(tiff, TIFFTAG_IMAGEWIDTH, width);
  TIFFSetField(tiff, TIFFTAG_IMAGELENGTH, height);
  TIFFSetField(tiff, TIFFTAG_COMPRESSION, 1); // No compression
  TIFFSetField(tiff, TIFFTAG_SAMPLESPERPIXEL, sampleperpixel); // 1 channel
  TIFFSetField(tiff, TIFFTAG_BITSPERSAMPLE, bps);
  TIFFSetField(tiff, TIFFTAG_PHOTOMETRIC, PHOTOMETRIC_MINISBLACK);
  TIFFSetField(tiff, TIFFTAG_PLANARCONFIG, PLANARCONFIG_CONTIG);
  TIFFSetField(tiff, TIFFTAG_ROWSPERSTRIP, TIFFDefaultStripSize(tiff, width * sampleperpixel));
  TIFFSetField(tiff, TIFFTAG_RESOLUTIONUNIT, 3); // cm
  TIFFSetField(tiff, TIFFTAG_XRESOLUTION, this->XResolution / 1.0E4); // Convert to centimeters
  TIFFSetField(tiff, TIFFTAG_YRESOLUTION, this->YResolution / 1.0E4); // Convert to centimeters
  if (slices > 1)
	{
	  TIFFSetField(tiff, TIFFTAG_SUBFILETYPE, FILETYPE_PAGE);
	  TIFFSetField(tiff, TIFFTAG_PAGENUMBER, page, slices);
	}

  return 1;
}

int vtkOMETIFFWriter::RequestData(vtkInformation* vtkNotUsed(request),
								  vtkInformationVector** inputVector,
								  vtkInformationVector* vtkNotUsed(outputVector))
{
  this->SetErrorCode(vtkErrorCode::NoError);

  vtkInformation* inInfo = inputVector[0]->GetInformationObject(0);
  vtkImageData* input = vtkImageData::SafeDownCast(inInfo->Get(vtkDataObject::DATA_OBJECT()));

  if (!input)
	{
	  vtkErrorMacro(<< "Input not given");
	  return 0;
	}
  if (!this->FileName)
	{
	  vtkErrorMacro(<< "Filename not given");
	  this->SetErrorCode(vtkErrorCode::NoFileNameError);
	  return 0;
	}

  int* wext = inInfo->Get(vtkStreamingDemandDrivenPipeline::WHOLE_EXTENT());
  unsigned int slices = wext[5] - wext[4] + 1;
  unsigned int height = wext[3] - wext[2] + 1;
  unsigned int width = wext[1] - wext[0] + 1;
  unsigned int bps;
  std::string type;

  switch (input->GetScalarType())
	{
	case VTK_UNSIGNED_CHAR:
	  bps = 8;
	  type = "uint8";
	  break;
	case VTK_CHAR:
	case VTK_SIGNED_CHAR:
	  bps = 8;
	  type = "int8";
	  break;
	case VTK_UNSIGNED_SHORT:
	  bps = 16;
	  type = "uint16";
	  break;
	case VTK_SHORT:
	  bps = 16;
	  type = "int16";
	  break;
	case VTK_UNSIGNED_INT:
	  bps = 32;
	  type = "uint32";
	  break;
	case VTK_INT:
	  bps = 32;
	  type = "int32";
	  break;
	case VTK_FLOAT:
	  bps = 32;
	  type = "float";
	case VTK_DOUBLE:
	  bps = 64;
	  type = "double";
	  break;
	default:
	  vtkErrorMacro(<< "Can only write unsigned/signed char, short, int, and float and double");
	  this->SetErrorCode(vtkErrorCode::FileFormatError);
	  return 0;
	}

  tsize_t rowbytes = width * bps / 8;

  this->InvokeEvent(vtkCommand::StartEvent);
  this->UpdateProgress(0.0);

  TIFF* tiff;
  int numtiffs = this->TimePoints * this->Channels;
  if (numtiffs <= 1 && this->FileName)
	{
	  tiff = TIFFOpen(this->FileName, "w");
	}
  else if (numtiffs > 1 && this->FileNamePattern)
	{
	  char* filename = new char[strlen(this->FileNamePattern) + 100];
	  unsigned int currentImage = this->TimePoints * this->CurrentChannel + this->CurrentTimePoint;
	  this->CreateFileName(filename, currentImage);
	  tiff = TIFFOpen(filename, "w");
	  delete[] filename;
	}
  else
	{
	  vtkErrorMacro("No output file name or file pattern provided");
	  return 0;
	}

  if (!tiff)
	{
	  vtkErrorMacro(<< "Could not open file " << this->FileName);
	  this->SetErrorCode(vtkErrorCode::CannotOpenFileError);
	  return 0;
	}

  this->UpdateProgress(1.0 / (slices+1.0));
  // Write slices to TIFF image
  void* ptr;
  for (unsigned int i = 0; i < slices; ++i)
	{
	  TIFFSetDirectory(tiff, i);
	  // Writer directory header
	  if (!this->WriteTIFFHeader(tiff, input, wext, bps, i))
		{
		  vtkErrorMacro(<< "Writing TIFF header failed");
		  return 0;
		}
	  // Write XML header only to the first directory
	  if (i == 0 && this->UseXML && !this->WriteXMLHeader(tiff, input, wext, bps, type.c_str()))
		{
		  vtkErrorMacro(<< "Writing XML header failed");
		  return 0;
		}

	  for (unsigned int row = 0; row < height; ++row)
		{
		  ptr = input->GetScalarPointer(wext[0], row, i);
		  if (TIFFWriteScanline(tiff, static_cast<unsigned char*>(ptr), row, 0) < 0)
			{
			  vtkErrorMacro(<< "Cannot write to file " << this->FileName);
			  this->SetErrorCode(vtkErrorCode::OutOfDiskSpaceError);
			  break;
			}
		}

	  if (slices > 0) TIFFWriteDirectory(tiff);

	  this->UpdateProgress((i+2.0) / (slices+1.0));
	}

  this->UpdateProgress(1.0);
  this->InvokeEvent(vtkCommand::EndEvent);

  TIFFClose(tiff);

  return 1;
}

int vtkOMETIFFWriter::CreateFileName(char* filename, unsigned int i, unsigned int xmlPath)
{
  int patterns = 0;
  unsigned int indC = i / this->TimePoints;
  unsigned int indT = i - indC * this->TimePoints;
  indC++;
  indT++;

  for (int c = 0; this->FileNamePattern[c] != '\0'; c++)
	{
	  if (this->FileNamePattern[c] == '%') patterns++;
	}
  if (patterns == 1) sprintf(filename, this->FileNamePattern, i);
  else if (patterns == 2) sprintf(filename, this->FileNamePattern, indC, indT);
  else
	{
	  vtkErrorMacro(<< "Wrong number of \% characters in pattern, use 1 or 2");
	  return 0;
	}

  if (xmlPath == 1) // Remove everything before last \ or /
	{
	  char* last_ptr;
	  for (int c = 0; filename[c] != '\0'; c++)
		{
		  if (filename[c] == '\\' || filename[c] == '/') last_ptr = filename + c;
		}
	  strcpy(filename,last_ptr+1);
	}

  return 1;
}

void vtkOMETIFFWriter::PrintSelf(ostream& os, vtkIndent indent)
{
  this->Superclass::PrintSelf(os,indent);
}
