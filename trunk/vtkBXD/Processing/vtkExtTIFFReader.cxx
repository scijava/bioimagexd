/*=========================================================================

  Program:   Visualization Toolkit
  Module:    $RCSfile: vtkExtTIFFReader.cxx,v $
  Language:  C++
  Date:      $Date: 2003/08/22 14:46:02 $
  Version:   $Revision: 1.39 $


Copyright (c) 1993-2001 Ken Martin, Will Schroeder, Bill Lorensen 
Copyright (c) 2005 Kalle Pahajoki Modifications for raw mode support
Copyright (c) 2008 Lassi Paavolainen Support for multipage tiffs
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
#include "vtkExtTIFFReader.h"

#include "vtkImageData.h"
#include "vtkObjectFactory.h"
#include "vtkPointData.h"   

#include <sys/stat.h>
#include "vtkInformation.h"
#include "vtkInformationVector.h"
#include "vtkStreamingDemandDrivenPipeline.h"
#include "vtkStringArray.h"
#include "vtkUnsignedShortArray.h"

extern "C" {
#include "vtk_tiff.h"
}
#define PRT_EXT(ext) ext[0],ext[1],ext[2],ext[3],ext[4],ext[5]
#define PRT_EXT2(ext) ext[0]<<","<<ext[1]<<","<<ext[2]<<","<<ext[3]<<","<<ext[4]<<","<<ext[5]


//-------------------------------------------------------------------------
vtkStandardNewMacro(vtkExtTIFFReader);
vtkCxxRevisionMacro(vtkExtTIFFReader, "$Revision: 1.39 $");

class vtkExtTIFFReaderInternal
{
public:
  vtkExtTIFFReaderInternal();
  int Initialize();
  void Clean();
  int CanRead();
  int Open( const char *filename );
  int GetNumberOfSubFiles();
  TIFF *Image;
  unsigned int Width;
  unsigned int Height;
  unsigned short SamplesPerPixel;
  unsigned short Compression;
  unsigned short BitsPerSample;
  unsigned short Photometrics;
  unsigned short PlanarConfig;
  unsigned long int TileDepth;
  unsigned short NumberOfPages;
  vtkUnsignedShortArray* SubFiles;
  static void ErrorHandler(const char* module, const char* fmt, va_list ap);
};


extern "C" {
void vtkExtTIFFReaderInternalErrorHandler(const char* vtkNotUsed(module), 
                                const char* vtkNotUsed(fmt), 
                                va_list vtkNotUsed(ap))
{
  // Do nothing
  // Ignore errors
}
}

int vtkExtTIFFReaderInternal::Open( const char *filename )
{
  this->Clean();
  struct stat fs;
  if ( stat(filename, &fs) )
    {
    return 0;
    }
  this->Image = TIFFOpen(filename, "r");
  if ( !this->Image)
    {
    this->Clean();
    return 0;
    }
  if ( !this->Initialize() )
    {
    this->Clean();
    return 0;
    }
  return 1;
}

void vtkExtTIFFReaderInternal::Clean()
{
  if ( this->Image )
    {
    TIFFClose(this->Image);
    }
  this->Image=NULL;
  this->Width = 0;
  this->Height = 0;
  this->SamplesPerPixel = 0;
  this->Compression = 0;
  this->BitsPerSample = 0;
  this->Photometrics = 0;
  this->PlanarConfig = 0;
  this->TileDepth = 0;
  this->NumberOfPages = 0;
  if (this->SubFiles)
	{
	  this->SubFiles->Delete();
	  this->SubFiles = 0;
	}
}

vtkExtTIFFReaderInternal::vtkExtTIFFReaderInternal()
{
  this->Image           = NULL;
  this->SubFiles = NULL;
  TIFFSetErrorHandler(&vtkExtTIFFReaderInternalErrorHandler);
  TIFFSetWarningHandler(&vtkExtTIFFReaderInternalErrorHandler);
  this->Clean();
}

int vtkExtTIFFReaderInternal::Initialize()
{
  if ( this->Image )
    {
    if ( !TIFFGetField(this->Image, TIFFTAG_IMAGEWIDTH, &this->Width) ||
         !TIFFGetField(this->Image, TIFFTAG_IMAGELENGTH, &this->Height) )
      {
      return 0;
      }
    TIFFGetFieldDefaulted(this->Image, TIFFTAG_SAMPLESPERPIXEL, 
                 &this->SamplesPerPixel);
    TIFFGetField(this->Image, TIFFTAG_COMPRESSION, &this->Compression);
    TIFFGetField(this->Image, TIFFTAG_BITSPERSAMPLE, 
                 &this->BitsPerSample);
    TIFFGetField(this->Image, TIFFTAG_PHOTOMETRIC, &this->Photometrics);
    TIFFGetField(this->Image, TIFFTAG_PLANARCONFIG, &this->PlanarConfig);
//      printf("Planar configuration=%d\n",this->PlanarConfig);
    if ( !TIFFGetField(this->Image, TIFFTAG_TILEDEPTH, &this->TileDepth) )
      {
      this->TileDepth = 0;
      }

	this->NumberOfPages = TIFFNumberOfDirectories(this->Image);
	this->SubFiles = vtkUnsignedShortArray::New();

	if (this->NumberOfPages > 1)
	  {
		for (unsigned short page = 0; page < this->NumberOfPages; ++page)
		  {
			long subfiletype = 6;
			if (TIFFGetField(this->Image, TIFFTAG_SUBFILETYPE, &subfiletype))
			  {
				if (subfiletype == 0 || subfiletype == 2) this->SubFiles->InsertNextValue(page);
			  }
			TIFFReadDirectory(this->Image);
		  }
		TIFFSetDirectory(this->Image,0);
	  }
	}
  return 1;
}

int vtkExtTIFFReaderInternal::CanRead()
{
    return ( this->Image && ( this->Width > 0 ) && ( this->Height > 0 ) &&
           ( this->SamplesPerPixel > 0 ) && 
           ( this->Compression == COMPRESSION_NONE ) &&
           ( this->Photometrics == PHOTOMETRIC_RGB ||
             this->Photometrics == PHOTOMETRIC_MINISWHITE ||
             this->Photometrics == PHOTOMETRIC_MINISBLACK ||
             this->Photometrics == PHOTOMETRIC_PALETTE ) &&
           this->PlanarConfig == PLANARCONFIG_CONTIG &&
           ( !this->TileDepth ) &&
           ( this->BitsPerSample == 8) );
}

int vtkExtTIFFReaderInternal::GetNumberOfSubFiles()
{
  return this->SubFiles->GetMaxId() + 1;
}

vtkExtTIFFReader::vtkExtTIFFReader()
{
  this->InitializeColors();
  this->InternalImage = new vtkExtTIFFReaderInternal;
  this->InternalExtents = 0;
  this->RawMode = 0;
}

vtkExtTIFFReader::~vtkExtTIFFReader()
{
  delete this->InternalImage;
}

void vtkExtTIFFReader::ExecuteInformation()
{
  this->InitializeColors();
  //printf("vtkExtTIFFReader::ExecuteInformation()\n");
  this->ComputeInternalFileName(this->DataExtent[4]);
  if (this->InternalFileName == NULL)
    {
    return;
    }
  //printf("Internal name=%s\n",this->InternalFileName);
  if ( !this->InternalImage->Open(this->InternalFileName) )
    {  
    vtkErrorMacro("Unable to open file " <<this->InternalFileName );
    this->DataExtent[0] = 0;
    this->DataExtent[1] = 0;
    this->DataExtent[2] = 0;
    this->DataExtent[3] = 0;
    this->DataExtent[4] = 0;
    this->DataExtent[5] = 0;
    this->SetNumberOfScalarComponents(1);
    this->vtkImageReader2::ExecuteInformation();
    return;
    }

  // pull out the width/height, etc.
  this->DataExtent[0] = 0;
  this->DataExtent[1] = this->GetInternalImage()->Width - 1;
  this->DataExtent[2] = 0;
  this->DataExtent[3] = this->GetInternalImage()->Height - 1;

  if (this->GetInternalImage()->NumberOfPages > 1 && !this->FileNames)
	{
	  this->DataExtent[4] = 0;
	  this->DataExtent[5] = this->GetInternalImage()->SubFiles->GetMaxId() + 1 > 0 ? this->GetInternalImage()->SubFiles->GetMaxId() : this->GetInternalImage()->NumberOfPages - 1;
	  }

  //printf("Computing Internal File Name for dataextent %d,%d,%d,%d,%d,%d\n", DataExtent[0], DataExtent[1], DataExtent[2], DataExtent[3], DataExtent[4], DataExtent[5]);

  if(this->GetInternalImage()->BitsPerSample==16) {
    this->SetDataScalarTypeToUnsignedShort();
  }  else this->SetDataScalarTypeToUnsignedChar();     
      
    
  switch ( this->GetFormat() )
    {
    case vtkExtTIFFReader::GRAYSCALE:
    case vtkExtTIFFReader::PALETTE_GRAYSCALE:
      this->SetNumberOfScalarComponents( 1 );
      break;
    case vtkExtTIFFReader::RGB:      
      this->SetNumberOfScalarComponents( 
        this->GetInternalImage()->SamplesPerPixel );
      break;
    case vtkExtTIFFReader::PALETTE_RGB:      
      this->SetNumberOfScalarComponents( 3 );
      break;
    default:
      this->SetNumberOfScalarComponents( 4 );
    }   

  if ( !this->GetInternalImage()->CanRead() )
    {
        if(this->GetInternalImage()->BitsPerSample!=16) {
            this->SetNumberOfScalarComponents( 4 );
        }
    }
    
  //printf("vtkImageReader2::ExecuteInformation()\n");

  this->vtkImageReader2::ExecuteInformation();

      
  // close the file
  this->GetInternalImage()->Clean();
}


template <class OT>
void vtkExtTIFFReaderUpdate2(vtkExtTIFFReader *self, OT *outPtr, int *outExt,
							 vtkIdType* vtkNotUsed(outInc), long , int idx)
{
  if ( !self->GetInternalImage()->Open(self->GetInternalFileName()) )
    {
    return;
    }
  //printf("Initializing colors\n");
  self->InitializeColors();
    
  //printf("Reading image...\n");
  self->ReadImageInternal(self->GetInternalImage()->Image, 
                          outPtr, outExt, sizeof(OT), idx );

  // close the file
  //printf("Closing the file\n");
  self->GetInternalImage()->Clean();
  //printf("Done\n");
}

//----------------------------------------------------------------------------
// This function reads in one data of data.
// templated to handle different data types.
template <class OT>
void vtkExtTIFFReaderUpdate(vtkExtTIFFReader *self, vtkImageData *data, OT *outPtr)
{
  vtkIdType outIncr[3];
  int outExtent[6],uExtent[6];
  OT *outPtr2;

  data->GetExtent(outExtent);
    //data->GetUpdateExtent(uExtent);
  data->GetIncrements(outIncr);
  //printf("out extent=%d,%d,%d,%d,%d,%d\n",outExtent[0],outExtent[1],outExtent[2],outExtent[3],outExtent[4],outExtent[5]);
   //printf("update extent=%d,%d,%d,%d,%d,%d\n",uExtent[0],uExtent[1],uExtent[2],uExtent[3],uExtent[4],uExtent[5]);
  long pixSize = data->GetNumberOfScalarComponents()*sizeof(OT);  

   //printf("out increments=%d,%d,%d\n",outIncr[0],outIncr[1],outIncr[2]);  
  outPtr2 = outPtr;
  int idx2;
  char progressText[100];

  for (idx2 = outExtent[4]; idx2 <= outExtent[5]; ++idx2)
	{
	  self->ComputeInternalFileName(idx2);

    // read in a TIFF file
	  vtkExtTIFFReaderUpdate2(self, outPtr2, outExtent, outIncr, pixSize, idx2);
	  self->UpdateProgress((idx2 - outExtent[4])/
						   (outExtent[5] - outExtent[4] + 1.0));
	  sprintf(progressText,"slice %d",idx2);
	  self->SetProgressText(progressText);
	  outPtr2 += outIncr[2];
	}
}


//----------------------------------------------------------------------------
// This function reads a data from a file.  The datas extent/axes
// are assumed to be the same as the file extent/order.
void vtkExtTIFFReader::ExecuteData(vtkDataObject *output)
{
    
  //printf("Allocating output data\n");
  vtkImageData *data = this->AllocateOutputData(output);
  
  //int dims[3];
  //data->GetDimensions(dims);
  //printf("Dims=%d,%d,%d\n",dims[0],dims[1],dims[2]);
  //int ext[6];
  //output->GetWholeExtent(ext);
  //printf("Ext=%d,%d,%d,%d,%d,%d\n",PRT_EXT(ext));
  //printf("Data type=%s\n",data->GetScalarTypeAsString());
  if (this->InternalFileName == NULL)
    {
    vtkErrorMacro("Either a FileName or FilePrefix must be specified.");
    return;
    }

  this->ComputeDataIncrements();
  //printf("Computed data increments\n");
  // Call the correct templated function for the output
  void *outPtr;

  // Call the correct templated function for the input
  outPtr = data->GetScalarPointer();
  switch (data->GetScalarType())
    {
    vtkTemplateMacro3(vtkExtTIFFReaderUpdate, this, data, (VTK_TT *)(outPtr));
    default:
      vtkErrorMacro("UpdateFromFile: Unknown data type");
    }
   data->GetPointData()->GetScalars()->SetName("Tiff Scalars");
}

int vtkExtTIFFReader::RequestUpdateExtent (
  vtkInformation* request,
  vtkInformationVector** inputVector,
  vtkInformationVector* outputVector)
{
    //printf("\n\n\n****** REQUEST UPDATE EXTENT FOR TIFF READER\n");
  int uext[6], ext[6];
    
  vtkInformation* outInfo = outputVector->GetInformationObject(0);
 // vtkInformation *inInfo = inputVector[0]->GetInformationObject(0);

  outInfo->Get(vtkStreamingDemandDrivenPipeline::WHOLE_EXTENT(),ext);
   //printf("extent request %d,%d,%d,%d,%d,%d\n",PRT_EXT(ext));
  // Get the requested update extent from the output.
  outInfo->Get(vtkStreamingDemandDrivenPipeline::UPDATE_EXTENT(), uext);
  
  //printf("uextent request %d,%d,%d,%d,%d,%d\n",PRT_EXT(uext));

  // If they request an update extent that doesn't cover the whole slice
  // then modify the uextent 
  if(uext[1] < ext[1]) uext[1] = ext[1];
  if(uext[3] < ext[3]) uext[3] = ext[3];
  if(uext[0] > ext[0]) uext[0] = ext[0];
  if(uext[2] > ext[2]) uext[2] = ext[2];
  //printf("Setting uextent to %d,%d,%d,%d,%d,%d\n",PRT_EXT(uext));
  outInfo->Set(vtkStreamingDemandDrivenPipeline::UPDATE_EXTENT(), uext,6);
  //inInfo->Set(vtkStreamingDemandDrivenPipeline::UPDATE_EXTENT(), uext,6);

  //request->Set(vtkStreamingDemandDrivenPipeline::REQUEST_UPDATE_EXTENT(), uext,6);
  return 1;    
}

unsigned int vtkExtTIFFReader::GetFormat( )
{
  unsigned int cc; 
  if(this->RawMode) return vtkExtTIFFReader::GRAYSCALE;
  if ( this->ImageFormat != vtkExtTIFFReader::NOFORMAT )
    {
    return this->ImageFormat;
    }


  switch ( this->GetInternalImage()->Photometrics )
    {
    case PHOTOMETRIC_RGB: 
    case PHOTOMETRIC_YCBCR: 
      this->ImageFormat = vtkExtTIFFReader::RGB;
      return this->ImageFormat;
    case PHOTOMETRIC_MINISWHITE:
    case PHOTOMETRIC_MINISBLACK:
      this->ImageFormat = vtkExtTIFFReader::GRAYSCALE;
      return this->ImageFormat;
    case PHOTOMETRIC_PALETTE:
      for( cc=0; cc<256; cc++ ) 
        {
        unsigned short red, green, blue;
        this->GetColor( cc, &red, &green, &blue );
        if ( red != green || red != blue )
          {
          this->ImageFormat = vtkExtTIFFReader::PALETTE_RGB;
          return this->ImageFormat;
          }
        }
      this->ImageFormat = vtkExtTIFFReader::PALETTE_GRAYSCALE;
      return this->ImageFormat;
    }
  this->ImageFormat = vtkExtTIFFReader::OTHER;
  return this->ImageFormat;
}

void vtkExtTIFFReader::GetColor( int index, unsigned short *red, 
                                 unsigned short *green, unsigned short *blue )
{
  *red   = 0;
  *green = 0;
  *blue  = 0;
  if ( index < 0 ) 
    {
    vtkErrorMacro("Color index has to be greater than 0");
    return;
    }
  if ( this->TotalColors > 0 && 
       this->ColorRed && this->ColorGreen && this->ColorBlue )
    {
    if ( index >= this->TotalColors )
      {
      vtkErrorMacro("Color index has to be less than number of colors ("
                    << this->TotalColors << ")");
      return;
      }
    *red   = *(this->ColorRed   + index);
    *green = *(this->ColorGreen + index);
    *blue  = *(this->ColorBlue  + index);
    return;
    }

  unsigned short photometric;
  
  if (!TIFFGetField(this->GetInternalImage()->Image, TIFFTAG_PHOTOMETRIC, &photometric)) 
    {
    if ( this->GetInternalImage()->Photometrics != PHOTOMETRIC_PALETTE )
      {
      vtkErrorMacro("You can only access colors for palette images");
      return;
      }
    }
  
  unsigned short *red_orig, *green_orig, *blue_orig; 
  
  switch (this->GetInternalImage()->BitsPerSample) 
    {
    case 1: case 2: case 4:
    case 8: case 16:
        break;
    default:
      vtkErrorMacro( "Sorry, can not image with " 
                     << this->GetInternalImage()->BitsPerSample
                     << "-bit samples" );
        return;
    }
  if (!TIFFGetField(this->GetInternalImage()->Image, TIFFTAG_COLORMAP,
                    &red_orig, &green_orig, &blue_orig)) 
    {
    vtkErrorMacro("Missing required \"Colormap\" tag");
    return;
    }
//  printf("Bits per sample = %d\n",this->GetInternalImage()->BitsPerSample);
  this->TotalColors = (1L << this->GetInternalImage()->BitsPerSample);

  if ( index >= this->TotalColors )
    {
    vtkErrorMacro("Color index has to be less than number of colors ("
                  << this->TotalColors << ")");
    return;
    }
  this->ColorRed   =   red_orig;
  this->ColorGreen = green_orig;
  this->ColorBlue  =  blue_orig;
  
  *red   = *(red_orig   + index);
  *green = *(green_orig + index);
  *blue  = *(blue_orig  + index);
}

void vtkExtTIFFReader::InitializeColors()
{
  this->ColorRed    = 0;
  this->ColorGreen  = 0;
  this->ColorBlue   = 0;
  this->TotalColors = -1;  
  if(RawMode) { this->ImageFormat = vtkExtTIFFReader::GRAYSCALE; }
  else this->ImageFormat = vtkExtTIFFReader::NOFORMAT;
}

void vtkExtTIFFReader::ReadImageInternal(void* vtkNotUsed(in), void* outPtr, 
										 int* outExt, unsigned int size,
										 int idx)
{
  if ( this->GetInternalImage()->Compression == COMPRESSION_OJPEG )
      {
      vtkErrorMacro("This reader cannot read old JPEG compression");
      return;
      }

    int width  = this->GetInternalImage()->Width;
    int height = this->GetInternalImage()->Height;
	// printf("width=%d, height=%d, size=%d\n",width,height,size);
    this->InternalExtents = outExt;
    unsigned int isize = TIFFScanlineSize(this->GetInternalImage()->Image);
	//printf("isize=%d, height=%d\n",isize,height);
    unsigned int cc;
    int row, inc = 1;
    tdata_t buf = _TIFFmalloc(isize);

	// Open right directory if multipage tiff file
	if (this->InternalImage->SubFiles->GetMaxId() >= 0 && this->InternalImage->SubFiles->GetMaxId() >= idx)
	  {
		TIFFSetDirectory(this->InternalImage->Image,idx);
	  }

     // special case for 16-bit grayscale
    if(this->GetInternalImage()->BitsPerSample==16 && this->GetFormat()== vtkExtTIFFReader::GRAYSCALE)
    {
        isize /= 2;
        unsigned short* image;
        image = (unsigned short*)outPtr;
            
        if (InternalImage->PlanarConfig == PLANARCONFIG_CONTIG)
          {
          for ( row = 0; row < (int)height; row ++ )
            {
            if (TIFFReadScanline(InternalImage->Image, buf, row, 0) <= 0)
              {
                vtkErrorMacro( << "Problem reading the row: " << row <<"of file"<<GetInternalFileName());
                break;
              }
			unsigned short* buf2 = (unsigned short*)buf;
			for(cc = 0; cc < isize; cc += InternalImage->SamplesPerPixel)
			  {
				*image++ = *buf2++;
			  }
            }
		  _TIFFfree(buf);
		  return;
          }
  }
  else if(this->GetInternalImage()->BitsPerSample==8) {
        unsigned char* image;
        image = (unsigned char*)outPtr;
            
        if (InternalImage->PlanarConfig == PLANARCONFIG_CONTIG)
          {
          for ( row = 0; row < (int)height; row ++ )
            {
            if (TIFFReadScanline(InternalImage->Image, buf, row, 0) <= 0)
              {
                vtkErrorMacro( << "Problem reading the row: " << row <<"of file"<<GetInternalFileName());
                break;
              }
              unsigned char* buf2 = (unsigned char*)buf;
              for(cc = 0; cc < isize; cc += InternalImage->SamplesPerPixel) {
                    *image++ = *buf2++;
              }
            }
		  _TIFFfree(buf);
		  return;
          }
  }
}

int vtkExtTIFFReader::CanReadFile(const char* fname)
{
  vtkExtTIFFReaderInternal tf;
  int res = tf.Open(fname);
  tf.Clean();
  if (res)
    {
    return 3;
    }
  return 0;
}

//----------------------------------------------------------------------------
void vtkExtTIFFReader::PrintSelf(ostream& os, vtkIndent indent)
{
  this->Superclass::PrintSelf(os,indent);
}

int vtkExtTIFFReader::GetNumberOfSubFiles() const
{
  this->InternalImage->Open(this->FileName);
  this->InternalImage->Initialize();
  int subPages = this->InternalImage->GetNumberOfSubFiles();
  this->InternalImage->Clean();
  return subPages;
}
