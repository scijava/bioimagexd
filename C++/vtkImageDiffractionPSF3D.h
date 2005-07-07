/*=========================================================================

  Program:   BioImageXD
  Module:    $RCSfile: vtkImageDiffractionPSF3D.h,v $

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
// .NAME vtkImageDiffractionPSF3D - select piece (e.g., volume of interest) and/or subsample structured points dataset

// .SECTION Description
// vtkImageDiffractionPSF3D is a filter that sets to zero pixels/voxels that have scalar
// values over a specified threshold but do not have horizontal/vertical neighborhood pixels
//  with scalar values over the respective thresholds


// .SECTION See Also
// vtkGeometryFilter vtkExtractGeometry vtkExtractGrid

#ifndef __vtkImageDiffractionPSF3D_h
#define __vtkImageDiffractionPSF3D_h

#include "vtkImageSource.h"

double t[] = {
		1,
		-2.2499997,
		1.2656208,
		-0.3163866,
		0.0444479,
		-0.0039444,
    0.0002100};
	double p[] = {
		-.78539816,
		-.04166397,
		-.00003954,
		0.00262573,
		-.00054125,
		-.00029333,
		.00013558};
	double f[] = {
		.79788456,
		-0.00000077,
		-.00552740,
		-.00009512,
		0.00137237,
		-0.00072805,
		0.00014476};


class VTK_IMAGING_EXPORT vtkImageDiffractionPSF3D : public vtkImageSource
{
public:
  vtkTypeRevisionMacro(vtkImageDiffractionPSF3D,vtkImageSource);
  void PrintSelf(ostream& os, vtkIndent indent);

  // Description:
  // Construct object to extract all of the input data.
  static vtkImageDiffractionPSF3D *New();     

  // Description:
  // Set / Get the Wavelength (perhaps in nm)
  vtkSetMacro(Lambda,double);
  vtkGetMacro(Lambda,double);
      
  // Description:
  // Set / Get the Index of Refraction of the media
  vtkSetMacro(RefractionIndex,double);
  vtkGetMacro(RefractionIndex,double);
      
  // Description:
  // Set / Get the spacing between pixels of an optical slice
  vtkSetMacro(PixelSpacing,double);
  vtkGetMacro(PixelSpacing,double);

  // Description:
  // Set / Get the spacing two optical slices
  vtkSetMacro(SliceSpacing,double);
  vtkGetMacro(SliceSpacing,double);
 
  // Description:
  // Set / Get the Numerical Aperture n*sin(theta)
  vtkSetMacro(NumericalAperture,double);
  vtkGetMacro(NumericalAperture,double);

  // Description:
  // Set / Get the longitudinal spherical aberration at max. aperture, same units
  vtkSetMacro(SphericalAberration,double);
  vtkGetMacro(SphericalAberration,double);


  // Description:
  // Set / Get the normalization. Which is
  // 1 = Peak = 1
  // 2 = Peak = 255
  // 3 = Sum of pixel values = 1 
  vtkSetMacro(Normalization,int);
  vtkGetMacro(Normalization,int);

  // Description:
  // Toggle whether the result should be in dB
  vtkSetMacro(dB,bool);
  vtkGetMacro(dB,bool);

  // Description:
  // The dimensions of the dataset
  vtkSetVector3Macro(Dimensions,int);
  vtkGetVectorMacro(Dimensions,int,3);
      
	float interp(float y[], float x);
	double J0(double xIn);
  
  

protected:
  vtkImageDiffractionPSF3D();
  ~vtkImageDiffractionPSF3D() {};

  void ExecuteInformation();
  virtual void ExecuteData(vtkDataObject *);

  
private:
  vtkImageDiffractionPSF3D(const vtkImageDiffractionPSF3D&);  // Not implemented.
void operator=(const vtkImageDiffractionPSF3D&);  // Not implemented.

  double Lambda;
  double RefractionIndex;
  double PixelSpacing;
  double SliceSpacing;
  double NumericalAperture;
  double SphericalAberration;
  int Normalization;
  int Dimensions[3];
  bool dB;
};

#endif


