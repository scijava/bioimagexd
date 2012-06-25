/*=========================================================================

  Program:   BioImageXD
  Module:    vtkOMETIFFWriter.h
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

#ifndef __vtkOMETIFFWriter_h
#define __vtOMETIFFWriter_h

#include "vtkImageAlgorithm.h"
#include <vtkstd/vector>
#include "vtk_tiff.h"
#include "vtkBXDProcessingWin32Header.h"

//BTX
class OMEChannel;
typedef vtkstd::vector<OMEChannel*> ChannelVector;
//ETX

class VTK_BXD_PROCESSING_EXPORT vtkOMETIFFWriter : public vtkImageAlgorithm
{
public:
  static vtkOMETIFFWriter *New();
  vtkTypeMacro(vtkOMETIFFWriter,vtkImageAlgorithm);
  virtual void PrintSelf(ostream&, vtkIndent);

  int SetFileName(const char*);
  int SetUUID(unsigned int, const char*);
  void SetTimePoints(unsigned int);
  void SetChannels(unsigned int);
  void SetChannelInfo(const char*, int, int);
  void Write();

  // Macros
  vtkSetMacro(XResolution, double);
  vtkSetMacro(YResolution, double);
  vtkSetMacro(ZResolution, double);
  vtkSetMacro(CurrentTimePoint, unsigned int);
  vtkSetMacro(CurrentChannel, unsigned int);
  vtkSetMacro(UseXML, int);
  vtkBooleanMacro(UseXML, int);
  vtkSetStringMacro(ImageName);
  vtkSetStringMacro(FileNamePattern);
  vtkSetMacro(TimeIncrement, double);

  vtkGetMacro(XResolution, double);
  vtkGetMacro(YResolution, double);
  vtkGetMacro(ZResolution, double);
  vtkGetMacro(CurrentTimePoint, unsigned int);
  vtkGetMacro(CurrentChannel, unsigned int);
  vtkGetStringMacro(FileName);
  vtkGetMacro(UseXML, int);
  vtkGetMacro(TimePoints, int);
  vtkGetMacro(Channels, int);
  vtkGetStringMacro(ImageName);
  vtkGetStringMacro(FileNamePattern);
  vtkGetMacro(TimeIncrement, double);

protected:
  vtkOMETIFFWriter();
  ~vtkOMETIFFWriter();

  int WriteXMLHeader(TIFF*, vtkImageData*, int*, unsigned int, const char*);
  int WriteTIFFHeader(TIFF*, vtkImageData*, int*, unsigned int, unsigned int);
  virtual int RequestData(vtkInformation*,
						  vtkInformationVector**,
						  vtkInformationVector*);
  int CreateFileName(char*, unsigned int, unsigned int xmlPath = 0);
  void UpdateUUIDs(unsigned int, unsigned int);

  char* FileName;
  int UseXML;
  int TimePoints;
  int Channels;
  double XResolution; // Pixels physical size in x-direction in um
  double YResolution; // Pixels physical size in y-direction in um
  double ZResolution; // Pixels physical size in z-direction in um
  double TimeIncrement;
  unsigned int CurrentTimePoint; // Time point of input data
  unsigned int CurrentChannel; // Channel number of input data
  char* ImageName;
  char* FileNamePattern;
  char** UUIDs;
  ChannelVector* ChannelsInfo;

private:
  vtkOMETIFFWriter(const vtkOMETIFFWriter&); // Not implemented
  void operator=(const vtkOMETIFFWriter&); // Not implemented
};

//BTX
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
//ETX

#endif
