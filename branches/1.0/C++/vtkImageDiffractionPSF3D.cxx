/*=========================================================================

  Program:   BioImageXD
  Module:    $RCSfile: vtkImageDiffractionPSF3D.cxx,v $

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
#include "vtkImageDiffractionPSF3D.h"

#include "vtkCellData.h"
#include "vtkImageData.h"
#include "vtkObjectFactory.h"
#include "vtkPointData.h"

#include "vtkMath.h"
#include <ostream.h>
#include <math.h>

vtkCxxRevisionMacro(vtkImageDiffractionPSF3D, "$Revision: 1.36 $");
vtkStandardNewMacro(vtkImageDiffractionPSF3D);

//-----------------------------------------------------------------------------
// Construct object to extract all of the input data.
vtkImageDiffractionPSF3D::vtkImageDiffractionPSF3D()
{
    this->SetLambda(510);
    this->SetRefractionIndex(1);
    this->SetNumericalAperture(0.6);
    this->SetSphericalAberration(0);
    this->SetNormalization(3);
    this->SetdB(0);
}

//-----------------------------------------------------------------------------
	float vtkImageDiffractionPSF3D::interp(float y[], float x){
		int i = (int)x;
		float fract = x - i;
		return (1 - fract)*y[i] + fract*y[i+1];
	}
	//Bessel function J0(x).  Uses the polynomial approximations on p. 369-70 of Abramowitz & Stegun
	//The error in J0 is supposed to be less than or equal to 5 x 10^-8.
	double vtkImageDiffractionPSF3D::J0(double xIn){
		double x = xIn;
		if (x < 0) x *= -1;
		double r;
		if (x <= 3){
			double y = x*x/9;
			r = t[0] + y*(t[1] + y*(t[2] + y*(t[3] + y*(t[4] + y*(t[5] + y*t[6])))));
		}else{
			double y = 3/x;
			double theta0 = x + p[0] + y*(p[1] + y*(p[2] + y*(p[3] + y*(p[4] + y*(p[5] + y*p[6])))));
			double f0 = f[0] + y*(f[1] + y*(f[2] + y*(f[3] + y*(f[4] + y*(f[5] + y*f[6])))));
			r = sqrt(1/x)*f0*cos(theta0);
		}
		return r;
	}


//-----------------------------------------------------------------------------
void 
vtkImageDiffractionPSF3D::ExecuteInformation()
{
  double spp,spp2,sps;
  vtkImageData*output = this->GetOutput();
  //this->vtkImageSource::ExecuteInformation();
  output->SetNumberOfScalarComponents(1);
  output->SetScalarTypeToFloat();
  int uExtent[6];
  output->SetDimensions(Dimensions[0],Dimensions[1],Dimensions[2]); 
  uExtent[0]=uExtent[2]=uExtent[4]=0;
  uExtent[1]=Dimensions[0]-1;
  uExtent[3]=Dimensions[1]-1;
  uExtent[5]=Dimensions[2]-1;    
//  printf("Setting extents to %d,%d,%d\n",Dimensions[0]-1,Dimensions[1]-1,Dimensions[2]-1);
  output->SetExtent(uExtent);
  output->SetWholeExtent(uExtent);
  
}
//-----------------------------------------------------------------------------
template<class T>
void vtkImageDiffractionPSF3DExecute(vtkImageDiffractionPSF3D *self,
                               vtkImageData *output, T *outPtr,
                               int outExt[6], int id)
{


  int uExtent[6];

//  printf("Estimated memory size %d\n",output->GetEstimatedMemorySize());
//  output->PrintSelf(cout,indent);
  int outIncX,outIncY,outIncZ;
  int maxX,maxY,maxZ,maxC;
  int idxX,idxY,idxZ,idxC;
  int dims[3];
    
  double Lambda=self->GetLambda();
  double RefractionIndex=self->GetRefractionIndex();
  double PixelSpacing=self->GetPixelSpacing();
  double SliceSpacing=self->GetSliceSpacing();
  double NumericalAperture=self->GetNumericalAperture();
  double SphericalAberration=self->GetSphericalAberration();
  int dB=self->GetdB();
  int Normalization=self->GetNormalization();
  
  uExtent[0]=uExtent[2]=uExtent[4]=0;
  uExtent[1]=self->GetDimensions()[0]-1;
  uExtent[3]=self->GetDimensions()[1]-1;
  uExtent[5]=self->GetDimensions()[2]-1;    
    
  int w = self->GetDimensions()[0];
  int h = self->GetDimensions()[1];
  int d = self->GetDimensions()[2];
  int ic = w/2;
  int jc = h/2;
  int kc = d/2;
  int stepsPerCycle = 8;
  

  //output->AllocateScalars();
  output->GetIncrements(outIncX, outIncY, outIncZ);
  maxX = uExtent[1] - uExtent[0];
  maxY = uExtent[3] - uExtent[2];
  maxZ = uExtent[5] - uExtent[4];

  float a = 2*vtkMath::Pi()*RefractionIndex/Lambda;
  double dRing = 0.6*Lambda/(PixelSpacing*NumericalAperture);
  vtkDebugMacro(<<"PSF: peak to first dark ring (w/o sph. aber.). Rayleigh resolution = " << dRing <<" pixels\n");

  int rMax = 2+(int)sqrt(ic*ic+jc*jc);
  vtkDebugMacro(<<"rMax="<<rMax<<"\n");
  float *integral = new float[rMax];
  double upperLimit = tan(asin(NumericalAperture/RefractionIndex));
	double waveNumber = 2*vtkMath::Pi()*RefractionIndex/Lambda;

  
  #define GET_AT(x,y,z,ptr) *(ptr+(z)*inIncZ+(y)*inIncY+(x)*inIncX)
  #define SET_AT(x,y,z,ptr,val) *(ptr+(z)*outIncZ+(y)*outIncY+(x)*outIncX)=val

  float **pixels=new float*[d];
    
  for(int i=0;i<d;i++)pixels[i]=new float[w*h];
  for(int k = 0; k < d; k++ ) {
      double kz = waveNumber*(k - kc)*SliceSpacing;
			for (int r = 0; r < rMax; r++)
       {
    
				double kr = waveNumber*r*PixelSpacing;
				int numCyclesJ = 1 + (int)(kr*upperLimit/3);
				int numCyclesCos = 1 + (int)(fabs(kz)*0.36*upperLimit/6);
				int numCycles = numCyclesJ;
				if(numCyclesCos > numCycles)numCycles = numCyclesCos;
				int nStep = 2*stepsPerCycle*numCycles;
				int m = nStep/2;
				double step = upperLimit/nStep;
				double sumR = 0;
				double sumI = 0;
				//Simpson's rule
				//Assume that the sperical aberration varies with the  (% aperture)^4
				//f(a) = f(0) = 0, so no contribution
				double u = 0;
				double bessel = 1;
				double root = 1;
				double angle = kz;
				//2j terms
				for (int j = 1; j < m; j++){
					u = 2*j*step;
					kz = waveNumber*((k - kc)*SliceSpacing +
						SphericalAberration*(u/upperLimit)*(u/upperLimit)*(u/upperLimit)*(u/upperLimit));
					root = sqrt(1 + u*u);
					bessel = self->J0(kr*u/root);
					angle = kz/root;
					sumR += 2*cos(angle)*u*bessel/2;
					sumI += 2*sin(angle)*u*bessel/2;
				}

				//2j - 1 terms
				for (int j = 1; j <= m; j++){
					u = (2*j-1)*step;
					kz = waveNumber*((k - kc)*SliceSpacing +
						SphericalAberration*(u/upperLimit)*(u/upperLimit)*(u/upperLimit)*(u/upperLimit));
					root = sqrt(1 + u*u);
					bessel = self->J0(kr*u/root);
					angle = kz/root;
					sumR += 4*cos(angle)*u*bessel/2;
					sumI += 4*sin(angle)*u*bessel/2;
				}
				//f(b)
				u = upperLimit;
				kz = waveNumber*((k - kc)*SliceSpacing + SphericalAberration);
				root = sqrt(1 + u*u);
				bessel = self->J0(kr*u/root);
				angle = kz/root;
				sumR += cos(angle)*u*bessel/2;
				sumI += sin(angle)*u*bessel/2;

				integral[r] = (float)(step*step*(sumR*sumR + sumI*sumI)/9);
			}
			double uSlices = (k - kc);
			for (int j = 0; j < h; j++){
//				IJ.showProgress((float)j/h);
				for (int i = 0; i < w; i++){
					double rPixels = sqrt((i - ic)*(i-ic) + (j-jc)*(j - jc));
           
					pixels[k][i + w*j] = self->interp(integral,(float)rPixels);
           
					//pixels[kSym][i + w*j] = interp(integral,(float)rPixels);
				}
			}
		}
		int n = w*h;
		if(Normalization == 1){
			float peak = pixels[kc][ic + w*jc];
			for (int k = 0; k < d; k++){
				for (int ind = 0; ind < n; ind++){
					if(pixels[k][ind] > peak)
						peak = pixels[k][ind];
				}
			}
			float f = 1/peak;
			for (int k = 0; k < d; k++){
				for (int ind = 0; ind < n; ind++){
					pixels[k][ind] *= f;
				}
			}
		}else if(Normalization == 2){
			float peak = pixels[kc][ic + w*jc];
			for (int k = 0; k < d; k++){
				for (int ind = 0; ind < n; ind++){
					if(pixels[k][ind] > peak)
						peak = pixels[k][ind];
				}
			}
			float f = 255/peak;
			for (int k = 0; k < d; k++){
				for (int ind = 0; ind < n; ind++){
					pixels[k][ind] *= f;
					if(pixels[k][ind] > 255)pixels[k][ind] = 255;
				}
			}
		}else if(Normalization == 3){
			float area = 0;
			for (int k = 0; k < d; k++){
				for (int ind = 0; ind < n; ind++){
					area += pixels[k][ind];
				}
			}
			for (int k = 0; k < d; k++){
				for (int ind = 0; ind < n; ind++){
					pixels[k][ind] /= area;
				}
			}
		}
		if(dB){
			double SCALE = 10/log(10);
			for (int k = 0; k < d; k++){
				for (int ind = 0; ind < n; ind++){
					if(pixels[k][ind] > 0.000000001)
						pixels[k][ind] = (float)(SCALE*log(pixels[k][ind]));
					else
						pixels[k][ind] = -90;
				}
			}
		}

float*ptr=(float*)pixels;
for(int k=0;k<d;k++) {
    for(int j = 0 ; j < w*h; j++) {
    *outPtr=(T)pixels[k][j];
    outPtr++;
    }
}
        
delete[] integral;
  
for(int i=0;i<d;i++)delete[] pixels[i];
delete[] pixels;
}

void vtkImageDiffractionPSF3D::ExecuteData(vtkDataObject *output)
{
  vtkImageData *data = this->AllocateOutputData(output);
  int *outExt = data->GetExtent();
  void *outPtr = data->GetScalarPointerForExtent(outExt);

  // Call the correct templated function for the output
  switch (VTK_FLOAT)
    {
    vtkTemplateMacro5(vtkImageDiffractionPSF3DExecute, this, data,
                      (VTK_TT *)(outPtr), outExt, 0);
    default:
      vtkErrorMacro(<< "Execute: Unknown data type");
    }
}

void vtkImageDiffractionPSF3D::PrintSelf(ostream& os, vtkIndent indent)
{
  this->Superclass::PrintSelf(os,indent);

  os << indent << "Wavelength: "<< Lambda << "\n";
  os << indent << "Index of Refraction: "<< RefractionIndex << "\n";
  os << indent << "Spacing: (" << PixelSpacing << ","<< PixelSpacing << ","<<SliceSpacing<<")\n";
  os << indent << "Numerical Aperture n*sin(theta): " << NumericalAperture << "\n";
  os << indent << "Longitudal Spherical Aberration at max. Aperture:" << SphericalAberration << "\n";
    os << indent << "Normalization: ";
  switch(Normalization) {
      case 1:os << "Peak = 1\n"; break;
      case 2:os << "Peak = 255\n"; break;
      case 3:os << "Area = 1\n"; break;
      default:
          os << "*** MALFORMED NORMALIZATION PARAMETER ***\n";
  }
  os << indent << "Dimensions: (" << Dimensions[0] << ","<<Dimensions[1] <<","<<Dimensions[2]<<")\n";
  os << indent << "Output in dB: " << (dB?"yes":"no") << "\n";

}
