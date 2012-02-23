/*=========================================================================

  Program:   BioImageXD
  Module:    vtkOMETIFFReader.h
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

#ifndef __vtkOMETIFFReader_h
#define __vtOMETIFFReader_h

#include "vtkImageAlgorithm.h"
#include "vtkXMLDataElement.h"
#include "vtk_tiff.h"
#include <vtkstd/vector>

#include "vtkBXDProcessingWin32Header.h"

//BTX
class OMEImage;
class Tuple;
typedef vtkstd::vector<OMEImage*> OMEImageVector;
typedef vtkstd::vector<const char*> CharVector;
typedef vtkstd::vector<Tuple*> TupleVector;
typedef vtkstd::vector<vtkXMLDataElement*> TiffDataVector;
//ETX

class VTK_BXD_PROCESSING_EXPORT vtkOMETIFFReader : public vtkImageAlgorithm
{
public:
  static vtkOMETIFFReader *New();
  vtkTypeMacro(vtkOMETIFFReader,vtkImageAlgorithm);
  virtual void PrintSelf(ostream&, vtkIndent);

  int SetFileName(const char*);
  int ReadOMEHeader();
  int SetCurrentImage(unsigned int);
  int SetCurrentTimePoint(unsigned int);
  int SetCurrentChannel(unsigned int);

  int GetNumberOfImages() { return this->Images->size(); }
  int GetNumberOfTimePoints();
  int GetNumberOfChannels();
  const char* GetImageName();
  unsigned int GetPixelType();
  const char* GetChannelName();
  int GetExcitationWavelength();
  int GetEmissionWavelength();
  double GetTimeIncrement();

  // Public Get macros
  vtkGetStringMacro(FileName);
  vtkGetMacro(CurrentImage,unsigned int);
  vtkGetMacro(CurrentTimePoint,unsigned int);
  vtkGetMacro(CurrentChannel,unsigned int);
  vtkGetVectorMacro(ImageDimensions,int,3);
  vtkGetVectorMacro(VoxelSize,double,3);

//BTX
  template <typename OT> friend void vtkOMETIFFReaderUpdate(vtkOMETIFFReader*, vtkImageData*, OT*);
//ETX

protected:
  vtkOMETIFFReader();
  ~vtkOMETIFFReader();

  int RequestInformation(vtkInformation*,
						 vtkInformationVector**,
						 vtkInformationVector*);
  int RequestUpdateExtent(vtkInformation*, 
						  vtkInformationVector**,
						  vtkInformationVector*);
  int RequestData(vtkInformation*,
				  vtkInformationVector**,
				  vtkInformationVector*);

  int Clean();
  int ParseXMLHeader(const char*, size_t);
  int CreateImages(vtkXMLDataElement*);
  int CreateImage(vtkXMLDataElement*, vtkXMLDataElement*);
  void CreateImageMapping();
  void SetImageDimensions();
  void SetVoxelSize();
  // Find file where specific image is
  unsigned int FindFilePosition(unsigned int, unsigned int, unsigned int,
								unsigned int, unsigned int, unsigned int);

  char* FileName;
  char* FilePath;
  int HeaderRead;
  unsigned int CurrentImage;
  unsigned int CurrentTimePoint;
  unsigned int CurrentChannel;
  TIFF* File;
  CharVector* Files;
  OMEImageVector* Images;
  TiffDataVector* TiffDatas;
// Defines (filename,ifd) mapping for images in order image,z,t,c
  TupleVector* Mapping;
  int ImageDimensions[3];
  double VoxelSize[3];

private:
  vtkOMETIFFReader(const vtkOMETIFFReader&); // Not implemented
  void operator=(const vtkOMETIFFReader&); // Not implemented
};

//BTX
// Channel data class
class OMEChannel
{
public:
  OMEChannel()
  {
	this->Name = NULL;
	this->Color = 0xffffff;
	this->EmissionWavelength = this->ExcitationWavelength = 0;
  }
  ~OMEChannel()
  {
	if (this->Name) delete[] this->Name;
  }

  char* Name;
  int Color;
  int EmissionWavelength;
  int ExcitationWavelength;
};

// Plane data class
class OMEPlane
{
public:
  OMEPlane()
  {
	this->DeltaT = this->ExposureTime = this->PositionX = this->PositionY = this->PositionZ = 0.0;
  }
  ~OMEPlane()
  {
  }

  double DeltaT;
  double ExposureTime;
  double PositionX;
  double PositionY;
  double PositionZ;
};

// Pixels data class
typedef vtkstd::vector<OMEChannel*> ChannelVector;
typedef vtkstd::vector<OMEPlane*> PlaneVector;

class OMEPixels
{
public:
  OMEPixels()
  {
	this->SizeX = this->SizeY = this->SizeZ = this->SizeT = this->SizeC = 0;
	this->PhysicalSizeX = this->PhysicalSizeY = this->PhysicalSizeZ = this->TimeIncrement = 0.0;
	this->DimensionOrder = NULL;
	this->Type = NULL;
	this->TypeID = 0;
	this->Channels = new ChannelVector;
	this->Planes = new PlaneVector;
  }
  ~OMEPixels()
  {
	if (this->DimensionOrder) delete[] this->DimensionOrder;
	if (this->Type) delete[] this->Type;
	if (this->Channels) delete this->Channels;
	if (this->Planes) delete this->Planes;
  }

  ChannelVector* Channels;
  PlaneVector* Planes;
  char* DimensionOrder;
  char* Type;
  unsigned int TypeID;
  int SizeX;
  int SizeY;
  int SizeZ;
  int SizeT;
  int SizeC;
  double PhysicalSizeX;
  double PhysicalSizeY;
  double PhysicalSizeZ;
  double TimeIncrement;
};

// Image data class
class OMEImage
{
public:
  OMEImage()
  {
	this->Name = NULL;
	this->Pixels = new OMEPixels();
  }
  ~OMEImage()
  {
	delete this->Pixels;
	if (this->Name) delete[] this->Name;
  }

  char* Name;
  OMEPixels* Pixels;
};

class Tuple
{
public:
  Tuple(unsigned int a = 0, unsigned int b = 0)
  {
	first = a;
	second = b;
  }
  ~Tuple() { }

  unsigned int first;
  unsigned int second;
};

//ETX

#endif
