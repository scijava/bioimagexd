/*=========================================================================

  Program:   BioImageXD
  Module:    $RCSfile: vtkImageIterativeDeconvolution3D.cxx,v $

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
#include "vtkImageIterativeDeconvolution3D.h"

#include "vtkImageData.h"
#include "vtkObjectFactory.h"
#include <math.h>
#include <float.h>
#define GET_AT(x,y,z,ptr) *(ptr+(z)*inIncZ+(y)*inIncY+(x)*inIncX)
#define SET_AT(x,y,z,ptr,val) *(ptr+(z)*outIncZ+(y)*outIncY+(x)*outIncX)=val
#define MAX(x,y) (x)>(y)?(x):(y)
#define MIN(x,y) (x)<(y)?(x):(y)
#ifndef M_PI
#define M_PI 3.14159265358979
#endif

int mod(int i,int n) { return ((i % n) + n) % n;  };

int mylog2 (int x);
#define CREATE_ARRAY(name, type, z, wh) type** name = new type*[z]; for(int xkk = 0; xkk < z; xkk++) name[xkk] = new type[(wh)];
#define RELEASE_ARRAY(name, z) for(int xkk2 = 0; xkk2 < z; xkk2++) delete[] name[xkk2]; delete[] name;

void FastHartleyTransform3D(float** data,int w, int h, int d, bool inverse);
void swapQuadrants(int w,int h,int d,float** x);
void copyDataAverage(int w, int h, int d,int wE,int hE,int dE,float sum,
				float** dataIn,float** dataOut,float** result);
void copyData(int w, int h, int d,float** data, float** data2);
void dfht3 (float* x, int base, int maxN, float* s, float* c);
void convolveFreqDom(int w,int h,int d,float** h1,float** h2, float** result);
void deconvolveFreqDom(float gamma, double magMax, int w,int h,int d,float** h1,float** h2, float** result);
double findMagMax(int w,int h,int d,float** h2);
int mirror(int i, int n);
void makeSinCosTables(int maxN, float* s, float* c);
void rc2DFHT(float* x, int w, int h, float* sw, float* cw, float* sh, float* ch);
float* hartleyCoefs(int max);
void slowHT(float* u, float* cas, int max, float* work);
void BitRevRArr (float* x, int base, int bitlen, int maxN);
bool btst (int  x, int bit);
int BitRevX (int  x, int bitlen);
void copyDataMirror(int w, int h, int d,float** data,int wE,int hE,int dE,float** dataE);
void copyDataMask(int w, int h, int d,float** data,int wE,int hE,int dE,float** dataE);

int expandedSize(int maxN){
	//Expand this to a power of 2 that is at least 1.5* as large, to avoid wrap effects
	//Start with 4 to avoid apparent normalization problems with n = 2
	int iN=4;
	if(maxN > 1){
		while(iN<1.5 * maxN) iN *= 2;
	}
	return iN;
}

vtkCxxRevisionMacro(vtkImageIterativeDeconvolution3D, "$Revision: 1.25 $");
vtkStandardNewMacro(vtkImageIterativeDeconvolution3D);

//----------------------------------------------------------------------------
vtkImageIterativeDeconvolution3D::vtkImageIterativeDeconvolution3D()
{
    NumberOfIterations=100;
    Gamma=0;
    FilterX=FilterY=1;
    FilterZ=1;
    Normalize=false;
    LogMean=true;
    AntiRing=true;
    ChangeThresholdPercent=.01;
    DetectDivergence=true;
  this->SetNumberOfInputPorts(2);
}

//----------------------------------------------------------------------------
vtkImageIterativeDeconvolution3D::~vtkImageIterativeDeconvolution3D()
{
}




//----------------------------------------------------------------------------
// This templated function executes the filter for any type of data.
template <class T>
void vtkImageIterativeDeconvolution3DExecute(vtkImageIterativeDeconvolution3D *self, int id,int NumberOfInputs,
                           vtkImageData ***inData,vtkImageData**outData,int outExt[6],
                            T*)
{
    int i;
    int inIncX,inIncY,inIncZ;
    int psfIncX,psfIncY,psfIncZ;
    int outIncX,outIncY,outIncZ;
    int maxX,maxY,maxZ;
    int idxX,idxY,idxZ;
    float* inPtr;
    float* psfPtr;
    float* outPtr;
    inPtr = (float*)inData[0][0]->GetScalarPointer();
    psfPtr = (float*)inData[1][0]->GetScalarPointer();
    outPtr=(float*)outData[0]->GetScalarPointer();
    
    int dims[3];
    
    inData[0][0]->GetIncrements(inIncX, inIncY, inIncZ);
     inData[1][0]->GetIncrements(psfIncX, psfIncY, psfIncZ);
   outData[0]->GetIncrements(outIncX, outIncY, outIncZ);
    maxX = outExt[1] - outExt[0];
    maxY = outExt[3] - outExt[2];
    maxZ = outExt[5] - outExt[4];
    
    T scalar = 0, currScalar = 0;
    int maxval = 0, n = 0;
    maxval=int(pow(2,8*sizeof(T)))-1;
    T val;
    
    inData[0][0]->GetDimensions(dims);
    int imageWidth = dims[0];
	int imageHeight = dims[1];
	int imageDepth = dims[2];
	
	printf("Dimensions of dataset = %d, %d, %d\n", imageWidth,imageHeight,imageDepth);
	printf("inInCZ=%d\n", inIncZ);
	printf("psfIncZ=%d\n",psfIncZ);
	float** dataSourceImagein = new float*[imageDepth];
	for(int i = 0; i < imageDepth; i++) {
		dataSourceImagein[i] = &inPtr[i*inIncZ];
	}
    inData[1][0]->GetDimensions(dims);
    int psfWidth = dims[0];
	int psfHeight = dims[1];
	int psfDepth = dims[2];
	
	printf("Dimensions of PSF = %d, %d, %d\n", psfWidth, psfHeight, psfDepth);

	float** dataPSFin = new float*[psfDepth];
	for(int i = 0; i < psfDepth; i++) {
		dataPSFin[i] = &psfPtr[i*psfIncZ];
	}

	double minA = 0;
	double minY = 0;

	float* aw = 0, ah = 0,ad = 0;

	float scalePSF = 1;
	float sum = 0;
	for (int k = 0; k < psfDepth; k++){
		for (int ind = 0; ind < psfHeight*psfWidth; ind++){
			sum += dataPSFin[k][ind];
		}
	}
	printf("Sum = %f\n", sum);
	if((sum != 0) && self->GetNormalize())scalePSF /= sum;

	int imageWidthE = expandedSize(imageWidth);
	int imageHeightE = expandedSize(imageHeight);
	int imageDepthE = (imageDepth == 1) ? 1 : expandedSize(imageDepth);
	int psfWidthE = expandedSize(psfWidth);
	int psfHeightE = expandedSize(psfHeight);
	int psfDepthE = (psfDepth == 1) ? 1 : expandedSize(psfDepth);
	//w and h will always be at least 4.  d can be 1 as a special case.
	int w = (int)MAX(imageWidthE,psfWidthE);
	int h = (int)MAX(imageHeightE,psfHeightE);
	int d = (int)MAX(imageDepthE,psfDepthE);
	printf("w, h, d = %d, %d, %d\n", w,h,d);

	//Compute Gaussian filter weights
	float* gi = new float[w];
	double ic = w/(self->GetFilterX() + 0.000001);
	for(int i = 0; i < w; i++){
		int iShifted = i;
		if(iShifted > w/2) iShifted = w - iShifted;
		gi[i] = (float)exp(-(iShifted/ic)*(iShifted/ic));
	}
	float* gj = new float[h];
	double jc = h/(self->GetFilterY() + 0.000001);
	for(int j = 0; j < h; j++){
		int jShifted = j;
		if(jShifted > h/2)jShifted = h - jShifted;
		gj[j] = (float)exp(-(jShifted/jc)*(jShifted/jc));
	}
	float* gk = new float[d];
	double kc = d/(self->GetFilterZ() + 0.000001);
	for(int k = 0; k < d; k++){
		int kShifted = k;
		if(kShifted > d/2) kShifted = d - kShifted;
		gk[k] = (float)exp(-(kShifted/kc)*(kShifted/kc));
	}
	
	
//	for(int i = 0; i < imageDepth; i++) {
//		for(int j = 0; j < imageWidth*imageHeight; j++) {
//			if(dataSourceImagein[i][j])printf("data at %d,%d = %f\n", i,j,dataSourceImagein[i][j]);
//		}
//	}
	
	printf("Creating expanded arrays, %dx%dx%d\n",w,h,d);
	CREATE_ARRAY(dataSourceImage, float, d, w*h);
	copyDataMirror(imageWidth,imageHeight,imageDepth,dataSourceImagein,w,h,d,dataSourceImage);
	CREATE_ARRAY(dataPSF, float, d,w*h);
	copyDataMask(psfWidth,psfHeight,psfDepth,dataPSFin,w,h,d,dataPSF);
	
//	for(int i = 0; i < d; i++) {
//		for(int j = 0; j < w*h; j++) {
//			if(dataSourceImage[i][j])printf("data at %d,%d = %f\n", i,j,dataSourceImage[i][j]);
//		}
//	}

	printf("Swapping quadrants of the PSF\n");
	swapQuadrants(w,h,d,dataPSF);

	printf("Transforming PSF\n");
	FastHartleyTransform3D(dataPSF,w,h,d,false);
	
	CREATE_ARRAY(dataX, float, d, w*h);
	CREATE_ARRAY(AX, float, d, w*h);

	if(self->GetAntiRing()){
		//Anti-ringing step.
		printf("Performing anti-ringing step.\n");
		copyData(w,h,d,dataSourceImage,dataX);
		FastHartleyTransform3D(dataX,w,h,d,false);
		
		// convolve dataX (source image) with PSF and store it to AX
		convolveFreqDom(w,h,d,dataPSF,dataX,AX);
		FastHartleyTransform3D(AX,w,h,d,true);
		copyDataAverage(imageWidth,imageHeight,imageDepth,w,h,d,sum,dataSourceImage,AX,dataSourceImage);
	}

	//Optional premultiplication step
	if(self->GetGamma() > 0.0001){
		printf("Finding largest spectral element");
		double magMax = findMagMax(w,h,d,dataPSF);
		printf("Transforming blurred image");
		FastHartleyTransform3D(dataSourceImage,w,h,d,false);
		printf("Premultiplying PSF and blured image");
		//Use dataX storage temporarily for FD PSF (could be more efficient)
		//Use AX storage temporarily to store FD Y (could be more efficient)
		copyData(w,h,d,dataPSF,dataX);
		deconvolveFreqDom(self->GetGamma(),magMax,w,h,d,dataX,dataX,dataPSF);
		copyData(w,h,d,dataSourceImage,AX);
		deconvolveFreqDom(self->GetGamma(),magMax,w,h,d,AX,dataX,dataSourceImage);
		//printf("Inverse transforming blurred image");
		FastHartleyTransform3D(dataSourceImage,w,h,d,true);
	}

	//Finished with optional premultiplication step

	int wh = w*h;
	int kOff = (d - imageDepth + 1)/2;
	int jOff = (h - imageHeight + 1)/2;
	int iOff = (w - imageWidth + 1)/2;

	//Convert PSF back to the spatial domain in order to
	//compute aSum after the premultiplication step
	FastHartleyTransform3D(dataPSF,w,h,d,true);
	float aSum = 0;
	for(int k = 0; k < d; k++){
		for (int ind = 0; ind < wh; ind++){
			aSum += (float)fabs(dataPSF[k][ind]);
		}
	}
	printf("aSum = %f\n", aSum);
	//Apply scale factors
	if(scalePSF != 1){
		printf("Normalizing\n");
		for (int k = 0; k < d; k++){
			for (int ind = 0; ind < h*w; ind++){
				dataSourceImage[k][ind] /= scalePSF;
			}
		}
	}
	// convert PSF to frequency domain
	FastHartleyTransform3D(dataPSF,w,h,d,false);
	
	// copy the source image to dataX
	copyData(w,h,d,dataSourceImage,dataX);
	
	int iter;
	float oldPercentChange = FLT_MAX;
	for (iter = 0; iter < self->GetNumberOfIterations(); iter++){
		printf("Starting iteration %d of %d\n",(iter+1),self->GetNumberOfIterations());
		// take dataX over to frequency domain
		FastHartleyTransform3D(dataX,w,h,d,false);
		//Gaussian filter
		printf("Applying gaussian\n");
		for(int k = 0; k < d; k++){
			for (int j = 0; j < h; j++){
				for (int i = 0; i < w; i++){
					dataX[k][i + w*j] *= gk[k]*gj[j]*gi[i];
				//	if(dataX[k][i+w*j]) 
				//		printf("dataX[%d][%d] *= %f = %d\n", k,i+w*j, gk[k]*gj[j]*gi[i], dataX[k][i + w*j]);
				}
			}
		}
		convolveFreqDom(w,h,d,dataPSF,dataX,AX);
		FastHartleyTransform3D(AX,w,h,d,true);
		FastHartleyTransform3D(dataX,w,h,d,true);
		float meanDelta = 0;
		float delta;
		for(int k = 0; k < d; k++){
			for (int ind = 0; ind < wh; ind++){
				delta = (dataSourceImage[k][ind] - AX[k][ind]/aSum);
				dataX[k][ind] += delta;
				if(dataX[k][ind] < 0){
					dataX[k][ind] = 0;
				}else{
					meanDelta += fabs(delta);
				}
			}
		}
	
		//Energy sum to track convergence
		float sumPixels = 0;
		for (int k = 0; k < imageDepth; k++){
			for (int j = 0; j < imageHeight; j++){
				for (int i = 0; i < imageWidth; i++){
					sumPixels += dataX[k+kOff][i + iOff + w*(j+jOff)];
				}
			}
		}
		float percentChange = 100*meanDelta/sumPixels;
		
		printf("Percent change=%f, meanDelta = %f, sumPixels=%f\n", percentChange, meanDelta, sumPixels);
		//if(logMean)IJ.write(Float.toString(percentChange));
		if((oldPercentChange - percentChange) < self->GetChangeThresholdPercent()){
			printf("Percentage change = %f (diff=%f)\n", percentChange, oldPercentChange - percentChange);
			printf("Terminated after %d iterations\n", iter);
			//if(logMean)IJ.write("Automatically terminated after "+iter+" iterations.");
			break;
		}
		if((oldPercentChange < percentChange)&& self->GetDetectDivergence()){
			//if(logMean)IJ.write("Automatically terminated due to divergence "+iter+" iterations.");
			break;
		}
		oldPercentChange = percentChange;
		printf("%d iterations complete.\n",iter);
	}
	printf("Final filter.");
	FastHartleyTransform3D(dataX,w,h,d,false);
	//Gaussian filter and scaling
	for(int k = 0; k < d; k++){
		for (int j = 0; j < h; j++){
			for (int i = 0; i < w; i++){
				//printf("gk[%d] = %f, gj[%d] = %f, gi[%d]= %f / %d\n", k,gk[k], j, gj[j], i, gi[i], aSum);
				dataX[k][i + w*j] *= gk[k]*gj[j]*gi[i]/aSum;
			}
		}
	}

	
	FastHartleyTransform3D(dataX,w,h,d,true);
	for (int k = 0; k < imageDepth; k++){
		for (int j = 0; j < imageHeight; j++){
			for (int i = 0; i < imageWidth; i++){
//					if(dataX[k+kOff][i + iOff + w*(j+jOff)]>0.1)printf("Setting at %d,%d,%d=%f\n", i,j,k,dataX[k+kOff][i + iOff + w*(j+jOff)]);
				SET_AT(i, j, k, outPtr, dataX[k+kOff][i + iOff + w*(j+jOff)]);
//					px[i + imageWidth*j] = dataX[k+kOff][i + iOff + w*(j+jOff)];
			}
		}
	}
	
	delete[] dataSourceImagein;
	delete[] dataPSFin;
	delete[] gi;
	delete[] gj;
	delete[] gk;
	RELEASE_ARRAY(dataSourceImage, d);
	RELEASE_ARRAY(dataX, d );
	RELEASE_ARRAY(dataPSF, d);
	RELEASE_ARRAY(AX, d);
	

}

//----------------------------------------------------------------------------
// This method is passed a input and output regions, and executes the filter
// algorithm to fill the output from the inputs.
// It just executes a switch statement to call the correct function for
// the regions data types.
void vtkImageIterativeDeconvolution3D::ThreadedRequestData (
  vtkInformation * vtkNotUsed( request ),
  vtkInformationVector** vtkNotUsed( inputVector ),
  vtkInformationVector * vtkNotUsed( outputVector ),
  vtkImageData ***inData,
  vtkImageData **outData,
  int outExt[6], int id)
{
  int idx1;
  int inExt[6], cOutExt[6];
  // Require that both inputs be float
  if(inData[0][0]->GetScalarType() != 10 || inData[1][0]->GetScalarType() != 10) {
  	vtkErrorMacro(<<"Both input images for vtkImageIterativeDeconvolution3D need to be float type");
  }
  switch (inData[0][0]->GetScalarType())
  {
  vtkTemplateMacro7(vtkImageIterativeDeconvolution3DExecute, this, id, 
                    this->GetNumberOfInputConnections(0),inData, 
                    outData, outExt,static_cast<VTK_TT *>(0));
  default:
    vtkErrorMacro(<< "Execute: Unknown ScalarType");
  return;
  }    
    
}



//----------------------------------------------------------------------------

int vtkImageIterativeDeconvolution3D::SplitExtent(int splitExt[6], 
                                                int startExt[6], 
                                                int num, int total) {
                                                
                                               
    memcpy(splitExt, startExt, 6 * sizeof(int));
	                                          
     return 1;                                           
}

//----------------------------------------------------------------------------

int vtkImageIterativeDeconvolution3D::FillInputPortInformation(int port, vtkInformation* info)
{
  info->Set(vtkAlgorithm::INPUT_IS_REPEATABLE(), 1);

  info->Set(vtkAlgorithm::INPUT_REQUIRED_DATA_TYPE(), "vtkImageData");

  return 1;
}


//----------------------------------------------------------------------------

int vtkImageIterativeDeconvolution3D::RequestUpdateExtent (
  vtkInformation* vtkNotUsed(request),
  vtkInformationVector** inputVector,
  vtkInformationVector* outputVector)
{
  int uext[6], ext[6];
  vtkInformation* outInfo = outputVector->GetInformationObject(0);
  vtkInformation *inInfo = inputVector[0]->GetInformationObject(0);
  inInfo->Get(vtkStreamingDemandDrivenPipeline::WHOLE_EXTENT(),ext);
//  printf("\n\nRequestUpdateExtent update extent to %d,%d,%d,%d,%d,%d\n", uext[0], uext[1], uext[2], uext[3], uext[4], uext[5]);
  inInfo->Set(vtkStreamingDemandDrivenPipeline::UPDATE_EXTENT(), ext,6);

 inInfo = inputVector[1]->GetInformationObject(0);
  inInfo->Get(vtkStreamingDemandDrivenPipeline::WHOLE_EXTENT(),ext);
//  printf("\n\nRequestUpdateExtent update extent to %d,%d,%d,%d,%d,%d\n", uext[0], uext[1], uext[2], uext[3], uext[4], uext[5]);
  inInfo->Set(vtkStreamingDemandDrivenPipeline::UPDATE_EXTENT(), ext,6);
  return 1;    
}

//----------------------------------------------------------------------------

// Computes any global image information associated with regions.
int vtkImageIterativeDeconvolution3D::RequestInformation (
  vtkInformation * vtkNotUsed(request),
  vtkInformationVector **inputVector,
  vtkInformationVector *outputVector)
{
  // get the info objects
  vtkInformation* outInfo = outputVector->GetInformationObject(0);
  vtkInformation *inInfo = inputVector[0]->GetInformationObject(0);

  double spacing[3];
  int idx;
  int inExt[6], outExt[6];
  
  inInfo->Get(vtkStreamingDemandDrivenPipeline::WHOLE_EXTENT(), inExt);
  outInfo->Set(vtkStreamingDemandDrivenPipeline::WHOLE_EXTENT(),inExt,6);

  return 1;
}


//----------------------------------------------------------------------------
void vtkImageIterativeDeconvolution3D::PrintSelf(ostream& os, vtkIndent indent)
{
  this->Superclass::PrintSelf(os, indent);
  os << indent << "Number of iterations:" << this->GetNumberOfIterations() << "\n";
  os << indent << "Wiener gamma: " << this->GetGamma() << "\n";
  os << indent << "Low-pass filtering: " << (this->GetFilterX()?"X, ":"") << (this->GetFilterY()?"Y, ":"")<<(this->GetFilterZ()?"Z":"")<<"\n";
  os << indent << "Normalize PSF: " << (this->GetNormalize()?"Yes":"No") << "\n";
  os << indent << "Anti-ringing: " << (this->GetAntiRing()?"Yes":"No")<<"\n";
  os << indent << "Detect divergence: "<< (this->GetDetectDivergence()?"Yes":"No") <<"\n";
  os << indent << "Change threshold percent: " << this->GetChangeThresholdPercent() << "\n";
}



void copyDataMask(int w, int h, int d,float** data,int wE,int hE,int dE,float** dataE){
	int kOff = (dE - d + 1)/2;
	int jOff = (hE - h + 1)/2;
	int iOff = (wE - w + 1)/2;
	for(int k = 0; k < d; k++){
		for (int j = 0; j < h; j++){
			for (int i = 0; i < w; i++){
				dataE[k+kOff][i+iOff + wE*(j+jOff)] = data[k][i + w*j];
			}
		}
	}
}


void copyDataAverage(int w, int h, int d,int wE,int hE,int dE,float sum,
				float** dataIn,float** dataOut,float** result){
	int kOff = (dE - d + 1)/2;
	int jOff = (hE - h + 1)/2;
	int iOff = (wE - w + 1)/2;
	int iIn,jIn,kIn,iOut,jOut,kOut;
	float alphaI,alphaJ,alphaK;
	float a;
	for(int k = -kOff; k < dE-kOff; k++){
		kOut = k + kOff;
		if(k < 0){
			alphaK = -k/((float)kOff);
		}else if(k > (d-1)){
			alphaK = (k - d)/((float)kOff);
		}else{
			alphaK = 0;
		}
		for (int j = -jOff; j < hE-jOff; j++){
			jOut = j + jOff;
			if(j < 0){
				alphaJ = -j/((float)jOff);
			}else if(j > (h-1)){
				alphaJ = (j - h)/((float)jOff);
			}else{
				alphaJ = 0;
			}
			for (int i = -iOff; i < wE-iOff; i++){
				iOut = i + iOff;
				if(i < 0){
					alphaI = -i/((float)iOff);
				}else if(i > (w-1)){
					alphaI = (i - w)/((float)iOff);
				}else{
					alphaI = 0;
				}
				a = alphaK;
				if(alphaJ > a) a = alphaJ;
				if(alphaI > a) a = alphaI;
				result[kOut][iOut + wE*jOut] = (1-a)*dataIn[kOut][iOut + wE*jOut] +
							a*dataOut[kOut][iOut + wE*jOut]/sum;
			}
		}
	}
}
void copyData(int w, int h, int d,float** data, float** data2){
	int wh = w*h;
	for(int k = 0; k < d; k++){
		for (int ind = 0; ind < wh; ind++){
			data2[k][ind] = data[k][ind];
		}
	}
}
void copyDataMirror(int w, int h, int d,float** data,int wE,int hE,int dE,float** dataE){
	int kOff = (dE - d + 1)/2;
	int jOff = (hE - h + 1)/2;
	int iOff = (wE - w + 1)/2;
	int iIn,jIn,kIn,iOut,jOut,kOut;
	for(int k = -kOff; k < dE-kOff; k++){
		kOut = k + kOff;
		kIn = mirror(k,d);
		for (int j = -jOff; j < hE-jOff; j++){
			jOut = j + jOff;
			jIn = mirror(j,h);
			for (int i = -iOff; i < wE-iOff; i++){
				iOut = i + iOff;
				iIn = mirror(i,w);
				dataE[kOut][iOut + wE*jOut] = data[kIn][iIn + w*jIn];
			}
		}
	}
}

int mirror(int i, int n){
	int ip = mod(i,2*n);
	if(ip < n){
		return ip;
	}else{
		return n - (ip % n) - 1;
	}
}


	

void swapQuadrants(int w,int h,int d,float** x){
	int k1P,k2P,k3P;
	float temp;
	int wHalf = w/2;
	int hHalf = h/2;
	int dHalf = d/2;
	//Shift by half of the grid, less one pixel, in each direction
	for(int k3 = 0; k3 < dHalf; k3++){
		k3P = k3 + dHalf;
		for (int k2 = 0; k2 < h; k2++){
			for (int k1 = 0; k1 < w; k1++){
				temp = x[k3][k1 + w*k2];
				x[k3][k1 + w*k2] = x[k3P][k1 + w*k2];
				x[k3P][k1 + w*k2] = temp;
			}
		}
	}
	for(int k2 = 0; k2 < hHalf; k2++){
		k2P = k2 + hHalf;
		for (int k3 = 0; k3 < d; k3++){
			for (int k1 = 0; k1 < w; k1++){
				temp = x[k3][k1 + w*k2];
				x[k3][k1 + w*k2] = x[k3][k1 + w*k2P];
				x[k3][k1 + w*k2P] = temp;
			}
		}
	}
	for(int k1 = 0; k1 < wHalf; k1++){
		k1P = k1 + wHalf;
		for (int k2 = 0; k2 < h; k2++){
			for (int k3 = 0; k3 < d; k3++){
				temp = x[k3][k1 + w*k2];
				x[k3][k1 + w*k2] = x[k3][k1P + w*k2];
				x[k3][k1P + w*k2] = temp;
			}
		}
	}
}
void convolveFreqDom(int w,int h,int d,float** h1,float** h2, float** result){
	int k1C,k2C,k3C;
	double h2e,h2o;
	for(int k3 = 0; k3 < d; k3++){
		k3C = (d - k3) % d;
		for (int k2 = 0; k2 < h; k2++){
			k2C = (h - k2) % h;
			for (int k1 = 0; k1 < w; k1++){
				k1C = (w - k1) % w;
				h2e = (h2[k3][k1 + w*k2] + h2[k3C][k1C + w*k2C])/2;
				h2o = (h2[k3][k1 + w*k2] - h2[k3C][k1C + w*k2C])/2;
				result[k3][k1 + w*k2] = (float)(h1[k3][k1 + w*k2]*h2e + h1[k3C][k1C + w*k2C]*h2o);
			}
		}
	}
}
	
void deconvolveFreqDom(float gamma, double magMax, int w,int h,int d,float** h1,float** h2, float** result){
	int k1C,k2C,k3C;
	double mag,h2e,h2o;
	double gammaScaled = gamma*magMax;
	for(int k3 = 0; k3 < d; k3++){
		k3C = (d - k3) % d;
		for (int k2 = 0; k2 < h; k2++){
			k2C = (h - k2) % h;
			for (int k1 = 0; k1 < w; k1++){
				k1C = (w - k1) % w;
				h2e = (h2[k3][k1 + w*k2] + h2[k3C][k1C + w*k2C])/2;
				h2o = (h2[k3][k1 + w*k2] - h2[k3C][k1C + w*k2C])/2;
				mag =h2[k3][k1 + w*k2]*h2[k3][k1 + w*k2] + h2[k3C][k1C + w*k2C]*h2[k3C][k1C + w*k2C];
				double tmp = h1[k3][k1 + w*k2]*h2e - h1[k3C][k1C + w*k2C]*h2o;
				result[k3][k1 + w*k2] = (float)(tmp/(mag+gammaScaled));
			}
		}
	}
}
double findMagMax(int w,int h,int d,float** h2){
	int k1C,k2C,k3C;
	double magMax = 0;
	double mag;
	for(int k3 = 0; k3 < d; k3++){
		k3C = (d - k3) % d;
		for (int k2 = 0; k2 < h; k2++){
			k2C = (h - k2) % h;
			for (int k1 = 0; k1 < w; k1++){
				k1C = (w - k1) % w;
				mag =h2[k3][k1 + w*k2]*h2[k3][k1 + w*k2] + h2[k3C][k1C + w*k2C]*h2[k3C][k1C + w*k2C];
				if(mag > magMax) magMax = mag;
			}
		}
	}
	return magMax;
}
	
bool powerOf2Size(int w) {
	int i=2;
	while(i<w) i *= 2;
	return i==w;
}

void FastHartleyTransform3D(float** data,int w, int h, int d, bool inverse) {
	float* sw = new float[w/4];
	float* cw = new float[w/4];
	float* sh = new float[h/4];
	float* ch = new float[h/4];
	makeSinCosTables(w,sw,cw);
	makeSinCosTables(h,sh,ch);
	for (int i = 0; i < d; i++){
		rc2DFHT(data[i], w, h, sw, cw, sh, ch);
	}
	float* u = new float[d];
	if(powerOf2Size(d)){
		float* s = new float[d/4];
		float* c = new float[d/4];
		makeSinCosTables(d,s,c);
		for(int k2 = 0; k2 < h; k2++){
			for(int k1 = 0; k1 < w; k1++){
				int ind = k1 + k2*w;
				for(int k3 = 0; k3 < d; k3++){
					u[k3] = data[k3][ind];
				}
				dfht3(u, 0, d, s, c);
				for(int k3 = 0; k3 < d; k3++){
					data[k3][ind] = u[k3];
				}
			}
		}
		delete[] s;
		delete[] c;
	}else{
		float* cas = hartleyCoefs(d);
		float* work = new float[d];
		for(int k2 = 0; k2 < h; k2++){
			for(int k1 = 0; k1 < w; k1++){
				int ind = k1 + k2*w;
				for(int k3 = 0; k3 < d; k3++){
					u[k3] = data[k3][ind];
				}
				slowHT(u,cas,d,work);
				for(int k3 = 0; k3 < d; k3++){
					data[k3][ind] = u[k3];
				}
			}
		}
		delete[] cas;
		delete[] work;
	}
	//Convert to actual Hartley transform
	float A,B,C,D,E,F,G,H;
	int k1C,k2C,k3C;
	for(int k3 = 0; k3 <= d/2; k3++){
		k3C = (d - k3) % d;
		for(int k2 = 0; k2 <= h/2; k2++){
			k2C = (h - k2) % h;
			for (int k1 = 0; k1 <= w/2; k1++){
				k1C = (w - k1) % w;
				A = data[k3][k1 + w*k2C];
				B = data[k3][k1C + w*k2];
				C = data[k3C][k1 + w*k2];
				D = data[k3C][k1C + w*k2C];
				E = data[k3C][k1 + w*k2C];
				F = data[k3C][k1C + w*k2];
				G = data[k3][k1 + w*k2];
				H = data[k3][k1C + w*k2C];
				data[k3][k1 + w*k2] = (A+B+C-D)/2;
				data[k3C][k1 + w*k2] = (E+F+G-H)/2;
				data[k3][k1 + w*k2C] = (G+H+E-F)/2;
				data[k3C][k1 + w*k2C] = (C+D+A-B)/2;
				data[k3][k1C + w*k2] = (H+G+F-E)/2;
				data[k3C][k1C + w*k2] = (D+C+B-A)/2;
				data[k3][k1C + w*k2C] = (B+A+D-C)/2;
				data[k3C][k1C + w*k2C] = (F+E+H-G)/2;
			}
		}
	}
	if(inverse){
		//float norm = (float)Math.sqrt(d*h*w);
		float norm = d*h*w;
		for(int k3 = 0; k3 < d; k3++){
			for(int k2 = 0; k2 < h; k2++){
				for (int k1 = 0; k1 < w; k1++){
				data[k3][k1 + w*k2] /= norm;
				}
			}
		}
	}
	delete[] u;
	delete[] sw;
	delete[] cw;
	delete[] sh;
	delete[] ch;
}
float* hartleyCoefs(int max){
	float* cas = new float[max*max];
	int ind = 0;
	for(int n = 0; n < max; n++){
		for (int k = 0; k < max; k++){
			double arg = (2*M_PI*k*n)/max;
			cas[ind++] = (float)(cos(arg) + sin(arg));
		}
	}
	return cas;
}
void slowHT(float* u, float* cas, int max, float* work){
	int ind = 0;
	for(int k = 0; k < max; k++){
		float sum = 0;
		for(int n = 0; n < max; n++){
			sum += u[n]*cas[ind++];
		}
		work[k] = sum;
	}
	for (int k = 0; k < max; k++){
		u[k] = work[k];
	}
}
void makeSinCosTables(int maxN, float* s, float* c) {
	int n = maxN/4;
	double theta = 0.0;
	double dTheta = 2.0 * M_PI/maxN;
	for (int i=0; i<n; i++) {
		c[i] = (float)cos(theta);
		s[i] = (float)sin(theta);
		theta += dTheta;
	}
}
/** Row-column Fast Hartley Transform */
void rc2DFHT(float* x, int w, int h, float* sw, float* cw, float* sh, float* ch) {
	for (int row=0; row<h; row++)
		dfht3(x, row*w, w, sw, cw);
	float* temp = new float[h];
	for(int col = 0; col < w; col++){
		for (int row = 0; row < h; row++){
			temp[row] = x[col + w*row];
		}
		dfht3(temp, 0, h, sh, ch);
		for (int row = 0; row < h; row++){
			x[col + w*row] = temp[row];
		}
	}
	delete[] temp;
}
/* An optimized real FHT */
void dfht3 (float* x, int base, int maxN, float* s, float* c) {
	int i, stage, gpNum, gpIndex, gpSize, numGps, Nlog2;
	int bfNum, numBfs;
	int Ad0, Ad1, Ad2, Ad3, Ad4, CSAd;
	float rt1, rt2, rt3, rt4;

	Nlog2 = mylog2(maxN);
	BitRevRArr(x, base, Nlog2, maxN);	//bitReverse the input array
	gpSize = 2;     //first & second stages - do radix 4 butterflies once thru
	numGps = maxN / 4;
	for (gpNum=0; gpNum<numGps; gpNum++)  {
		Ad1 = gpNum * 4;
		Ad2 = Ad1 + 1;
		Ad3 = Ad1 + gpSize;
		Ad4 = Ad2 + gpSize;
		rt1 = x[base+Ad1] + x[base+Ad2];   // a + b
		rt2 = x[base+Ad1] - x[base+Ad2];   // a - b
		rt3 = x[base+Ad3] + x[base+Ad4];   // c + d
		rt4 = x[base+Ad3] - x[base+Ad4];   // c - d
		x[base+Ad1] = rt1 + rt3;      // a + b + (c + d)
		x[base+Ad2] = rt2 + rt4;      // a - b + (c - d)
		x[base+Ad3] = rt1 - rt3;      // a + b - (c + d)
		x[base+Ad4] = rt2 - rt4;      // a - b - (c - d)
	}
	if (Nlog2 > 2) {
		 // third + stages computed here
		gpSize = 4;
		numBfs = 2;
		numGps = numGps / 2;
		//IJ.write("FFT: dfht3 "+Nlog2+" "+numGps+" "+numBfs);
		for (stage=2; stage<Nlog2; stage++) {
			for (gpNum=0; gpNum<numGps; gpNum++) {
				Ad0 = gpNum * gpSize * 2;
				Ad1 = Ad0;     // 1st butterfly is different from others - no mults needed
				Ad2 = Ad1 + gpSize;
				Ad3 = Ad1 + gpSize / 2;
				Ad4 = Ad3 + gpSize;
				rt1 = x[base+Ad1];
				x[base+Ad1] = x[base+Ad1] + x[base+Ad2];
				x[base+Ad2] = rt1 - x[base+Ad2];
				rt1 = x[base+Ad3];
				x[base+Ad3] = x[base+Ad3] + x[base+Ad4];
				x[base+Ad4] = rt1 - x[base+Ad4];
				for (bfNum=1; bfNum<numBfs; bfNum++) {
				// subsequent BF's dealt with together
					Ad1 = bfNum + Ad0;
					Ad2 = Ad1 + gpSize;
					Ad3 = gpSize - bfNum + Ad0;
					Ad4 = Ad3 + gpSize;

					CSAd = bfNum * numGps;
					rt1 = x[base+Ad2] * c[CSAd] + x[base+Ad4] * s[CSAd];
					rt2 = x[base+Ad4] * c[CSAd] - x[base+Ad2] * s[CSAd];

					x[base+Ad2] = x[base+Ad1] - rt1;
					x[base+Ad1] = x[base+Ad1] + rt1;
					x[base+Ad4] = x[base+Ad3] + rt2;
					x[base+Ad3] = x[base+Ad3] - rt2;

				} /* end bfNum loop */
			} /* end gpNum loop */
			gpSize *= 2;
			numBfs *= 2;
			numGps = numGps / 2;
		} /* end for all stages */
	} /* end if Nlog2 > 2 */
}

	int mylog2 (int x) {
		int count = 15;
		while (!btst(x, count))
			count--;
		return count;
	}
bool btst (int  x, int bit) {
	//int mask = 1;
	return ((x & (1<<bit)) != 0);
}
	
void BitRevRArr (float* x, int base, int bitlen, int maxN) {
	int    l;
	float* tempArr = new float[maxN];
	for (int i=0; i<maxN; i++)  {
		l = BitRevX (i, bitlen);  //i=1, l=32767, bitlen=15
		tempArr[i] = x[base+l];
	}
	for (int i=0; i<maxN; i++)
		x[base+i] = tempArr[i];
	delete[] tempArr;
}
	
int BitRevX (int  x, int bitlen) {
	int  temp = 0;
	for (int i=0; i<=bitlen; i++)
		if ((x & (1<<i)) !=0)
			temp  |= (1<<(bitlen-i-1));
	return temp & 0x0000ffff;
}

int bset (int x, int bit) {
	x |= (1<<bit);
	return x;
}

