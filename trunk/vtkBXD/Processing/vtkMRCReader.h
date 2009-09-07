/*=========================================================================

  Program:   BioImageXD
  Module:    vtkMRCReader.h
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

#ifndef __vtkMRCReader_h
#define __vtkMRCReader_h

#include "vtkBXDProcessingWin32Header.h"
#include "vtkImageAlgorithm.h"

class VTK_BXD_PROCESSING_EXPORT vtkMRCReader: public vtkImageAlgorithm
{
 public:
  vtkTypeMacro(vtkMRCReader,vtkImageAlgorithm);
  static vtkMRCReader *New();
  virtual void PrintSelf(ostream&, vtkIndent);

  // Description:
  // Set file name to be read
  void SetFileName(const char*);

  // Description:
  // Open file and close file methods
  int OpenFile();
  void CloseFile();

  // Description:
  // Read header of MRC file
  int ReadHeader();

  const char* GetFileExtensions();

  // Description:
  // VTK Get Macros
  vtkGetVector3Macro(ImageDims,int);
  vtkGetStringMacro(FileName);
  vtkGetVector3Macro(Len,float);
  vtkGetVector3Macro(VoxelSize,float);
  vtkGetMacro(Mode,int);
  vtkGetMacro(Min,float);
  vtkGetMacro(Max,float);
  vtkGetMacro(Mean,float);

 protected:
  vtkMRCReader();
  ~vtkMRCReader();

  // Protected methods

  // Description:
  // Produce information about data to be created
  int RequestInformation(vtkInformation* vtkNotUsed(request),
						 vtkInformationVector** vtkNotUsed(inputVector),
						 vtkInformationVector*);

  // Description:
  // Deal with extent update request
  int RequestUpdateExtent(vtkInformation* vtkNotUsed(request),
						  vtkInformationVector** vtkNotUsed(inputVector),
						  vtkInformationVector*);

  // Description:
  // Create data to pipeline
  int RequestData(vtkInformation* vtkNotUsed(request),
				  vtkInformationVector** vtkNotUsed(inputVector),
				  vtkInformationVector*);

  // Description:
  // Initialize reader to be ready for new input file
  void Initialize();

  // Description:
  // Clear all information from reader
  void Clear();

  // Description:
  // Defines correct mapping of dimensions and sets those in ImageDims
  void SetImageDims();

  // Description:
  // Calculate voxel size and store it in VoxelSize
  void CalculateVoxelSize();

  // Description:
  // Defined extent and spacing values
  void CalculateExtentAndSpacing(int*, double*);

  // Description:
  // Reading of 4-bit integer, 4-bit float and 2-bit integer from buffer
  int ReadInt(char**);
  float ReadFloat(char**);
  short ReadShort(char**);

  // Description:
  // Reading vector of 4-bit integers, 4-bit floats and 2-bit integers from buffer
  void ReadVector(char**, int*, int);
  void ReadVector(char**, float*, int);
  void ReadVector(char**, short*, int);

  // Protected attributes
  ifstream *File;
  char *FileName;
  unsigned long long FileSize;
  int ImageDims[3];
  float VoxelSize[3];
  int HeaderInfoRead;
  int LittleEndian; // If file is in little endian encoding
  int State; // 0 = nothing done, 1 = file name set, 2 = file opened

  int N[3]; // Num of columns (fastest changing), rows, and sections (slowest)
  int Mode; // 0 = unsigned bytes, 1 = signed short, 2 = float, 3 = complex short * 2, 4 = complex float * 2
  int NStart[3]; // Num of first column, row, and section
  int M[3]; // Number of intervals along X, Y, Z
  float Len[3]; // Cell dimensions X, Y, Z (Angstroms)
  float Angles[3]; // Cell Angles Alpha, Beta, Gamma (Degrees)
  int Map[3]; // Which axis corresponds to cols, rows, sections (1,2,3 = X,Y,Z)
  float Min; // Minimum density value
  float Max; // Maximum density value
  float Mean; // Mean density value
  short ISPG; // Space group number, 0 for images
  short NSymbt; // Number of bytes used for storing symmetry operators
  int Next; // Number of bytes in extended header
  short CreatorID;
  short NInt; // Number of integers per section
  short NReal; // Number of reals per section
  short IDType; // 0 = mono, 1 = tilt, 2 = tilts, 3 = lina, 4 = lins
  short Lens;
  short ND[2];
  short VD[2];
  float TiltAngles[6];
  float Origin[3]; // Origin in X,Y,Z dimension
  char CMap[4];
  char Stamp[4];
  float RMS;
  int NLabl;
  char **Labels;

 private: // Only defined operator= and copy costructor to prevent illegal use
  void operator=(const vtkMRCReader&);
  vtkMRCReader(const vtkMRCReader&);
};



#endif
