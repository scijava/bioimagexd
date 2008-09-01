/*=========================================================================

  Program:   Visualization Toolkit
  Module:    $RCSfile: vtkExtTIFFReader.h,v $
  Language:  C++
  Date:      $Date: 2003/11/04 21:26:04 $
  Version:   $Revision: 1.28 $


Copyright (c) 1993-2001 Ken Martin, Will Schroeder, Bill Lorensen 
Copyright (c) 2005 Kalle Pahajoki. Modifications for raw mode support
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
// .NAME vtkExtTIFFReader - read TIFF files
// .SECTION Description
// vtkExtTIFFReader is a source object that reads TIFF files.
// It should be able to read most any TIFF file
//
// .SECTION See Also
// vtkTIFFWriter

#ifndef __vtkExtTIFFReader_h
#define __vtkExtTIFFReader_h

#include "vtkBXDProcessingWin32Header.h"
#include "vtkImageReader2.h"

//BTX
class vtkExtTIFFReaderInternal;
//ETX

class VTK_BXD_PROCESSING_EXPORT vtkExtTIFFReader : public vtkImageReader2
{
public:
  static vtkExtTIFFReader *New();
  vtkTypeRevisionMacro(vtkExtTIFFReader,vtkImageReader2);
  virtual void PrintSelf(ostream& os, vtkIndent indent);

  // Description:
  // Is the given file name a tiff file file?
  virtual int CanReadFile(const char* fname);

  // Description:
  // Get the file extensions for this format.
  // Returns a string with a space separated list of extensions in 
  // the format .extension
  virtual const char* GetFileExtensions()
    {
    return ".tif .tiff";
    }

  // Description: 
  // Return a descriptive name for the file format that might be useful 
  // in a GUI.
  virtual const char* GetDescriptiveName()
    {
    return "TIFF";
    }

  // Description:
  // Auxilary methods used by the reader internally.
  void InitializeColors();
 
  vtkSetMacro(RawMode,int);
  vtkGetMacro(RawMode,int);
  vtkBooleanMacro(RawMode,int);
     
//BTX
  enum { NOFORMAT, RGB, GRAYSCALE, PALETTE_RGB, PALETTE_GRAYSCALE, OTHER };



  void ReadImageInternal( void *, void *outPtr,  
                          int *outExt, unsigned int size, int );
  

  // Description:
  // Method to access internal image. Not to be used outside the class.
  vtkExtTIFFReaderInternal *GetInternalImage()
    { return this->InternalImage; }
//ETX

  // Description:
  // Method to check if set TIFF file is multipage
  int GetNumberOfSubFiles() const;

protected:
  vtkExtTIFFReader();
  ~vtkExtTIFFReader();

  void GetColor( int index, 
                 unsigned short *r, unsigned short *g, unsigned short *b );
  unsigned int  GetFormat();
  virtual void ExecuteInformation();
  virtual void ExecuteData(vtkDataObject *out);
int RequestUpdateExtent (
  vtkInformation* vtkNotUsed(request),
  vtkInformationVector** inputVector,
  vtkInformationVector* outputVector);

  void ReadGenericImage( void *out, 
                         unsigned int width, unsigned int height,
                         unsigned int size );
  
  int EvaluateImageAt( void*, void* ); 

private:
  vtkExtTIFFReader(const vtkExtTIFFReader&);  // Not implemented.
  void operator=(const vtkExtTIFFReader&);  // Not implemented.

  unsigned short *ColorRed;
  unsigned short *ColorGreen;
  unsigned short *ColorBlue;
  int TotalColors;
  unsigned int ImageFormat;
  vtkExtTIFFReaderInternal *InternalImage;
  int *InternalExtents;
  int RawMode;
};
#endif


