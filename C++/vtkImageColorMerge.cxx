/*=========================================================================

  Program:   BioImageXD
  Module:    $RCSfile: vtkImageColorMerge.cxx,v $

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
#include "vtkImageColorMerge.h"

#include "vtkImageData.h"
#include "vtkObjectFactory.h"

vtkCxxRevisionMacro(vtkImageColorMerge, "$Revision: 1.25 $");
vtkStandardNewMacro(vtkImageColorMerge);

//----------------------------------------------------------------------------
vtkImageColorMerge::vtkImageColorMerge()
{
    this->ITFCount = this->CTFCount = 0;
    this->AverageMode = 0;
    this->MaximumMode = 0;
    this->LuminanceMode = 0;
    this->AverageThreshold = 10;    
}

//----------------------------------------------------------------------------
vtkImageColorMerge::~vtkImageColorMerge()
{
}

//----------------------------------------------------------------------------
// This method tells the ouput it will have more components
void vtkImageColorMerge::ExecuteInformation(vtkImageData **inputs, 
                                        vtkImageData *output)
{
  vtkImageMultipleInputFilter::ExecuteInformation(inputs,output);
  if(!this->BuildAlpha)
    output->SetNumberOfScalarComponents(3);
  else output->SetNumberOfScalarComponents(4);
    
}



//----------------------------------------------------------------------------
// This templated function executes the filter for any type of data.
template <class T>
void vtkImageColorMergeExecute(vtkImageColorMerge *self, int id,int NumberOfInputs,
                           vtkImageData **inData,vtkImageData*outData,int outExt[6],
                            T*)
{
    int i;
    vtkIdType inIncX,inIncY,inIncZ;
    vtkIdType outIncX,outIncY,outIncZ;
    int maxX,maxY,maxZ;
    int idxX,idxY,idxZ;
    
    double **ctfs;
    double **modctfs;
    double **mapctfs;
    int **itfs;
    int itfCount = self->GetITFCount();
    
    int BuildAlpha = self->GetBuildAlpha();
    int AvgThreshold = self->GetAverageThreshold();
    int MaxMode = self->GetMaximumMode();                   
    int AvgMode = self->GetAverageMode();
    int LuminanceMode = self->GetLuminanceMode();
    if(!MaxMode&&!AvgMode)AvgMode=1;
    
    
    if(self->GetCTFCount() != NumberOfInputs) {
        vtkErrorWithObjectMacro(self,<< "Number of lookup tables ("<< self->GetCTFCount() <<") != number of inputs"<<NumberOfInputs);
    }
    if(itfCount && itfCount != NumberOfInputs) {
        vtkErrorWithObjectMacro(self, "Number of ITFs ("<<itfCount<<") != number of inputs"<<NumberOfInputs);
    }
    
    
    T** inPtrs;
    T* outPtr;
    ctfs = new double*[NumberOfInputs];
    modctfs = new double*[NumberOfInputs];
    itfs = new int*[NumberOfInputs];
    
    inPtrs=new T*[NumberOfInputs];
    int allIdentical = 1;
    mapctfs = ctfs;
    vtkIntensityTransferFunction* itf;
    vtkColorTransferFunction* ctf;
    for(i=0; i < NumberOfInputs; i++) {
        inPtrs[i]=(T*)inData[i]->GetScalarPointerForExtent(outExt);
        ctf = self->GetColorTransferFunction(i);
        //ctfs[i] = self->GetColorTransferFunction(i)->GetTable(0,255,256);
        ctfs[i] = new double[256*3];
        double val[3];
        for(int x = 0; x < 256; x++) {
                ctf->GetColor(x,val);
                
                ctfs[i][3*x] = val[0];
                ctfs[i][3*x+1] = val[1];
                ctfs[i][3*x+2] = val[2];
        }
        
        if( itfCount ) {
            itf = self->GetIntensityTransferFunction(i);
            
            itfs[i] = itf->GetDataPointer();
            if( !itf->IsIdentical() ) {
                allIdentical = 0;
            }
        }

    }
    // If all intensity transfer functions are not identical, then we construct a 
    // modified ctf for each input that reflects the ITF by mapping
    // ctf[x] -> ctf[ itf(x) ]
    
    if(!allIdentical ){
        mapctfs = modctfs;
        for(i=0; i < NumberOfInputs; i++) {
            modctfs[i] = new double[3*256];
            int newx;
            for(int x = 0; x < 256; x++) {
                newx=itfs[i][x];
                
                modctfs[i][3*x]=ctfs[i][3*newx];
                modctfs[i][3*x+1]=ctfs[i][3*newx+1];
                modctfs[i][3*x+2]=ctfs[i][3*newx+2];
            }
//            printf("ITF%d: Mapping %d to %d (%d,%d,%d)\n",i,255,itfs[i][255],modctfs[i][3*255],modctfs[i][3*255+1],modctfs[i][3*255+2]);
        } 
    }
    
    outPtr=(T*)outData->GetScalarPointerForExtent(outExt);
    
    
    inData[0]->GetContinuousIncrements(outExt,inIncX, inIncY, inIncZ);
    outData->GetContinuousIncrements(outExt,outIncX, outIncY, outIncZ);
    maxX = outExt[1] - outExt[0];
    maxY = outExt[3] - outExt[2];
    maxZ = outExt[5] - outExt[4];
    
    T currScalar = 0;
    double scalar, alphaScalar; 
    int maxval = 0, n = 0;
    maxval=int(pow(2,8*sizeof(T)))-1;
    T val;
    maxX *= (inData[0]->GetNumberOfScalarComponents());
    char progressText[200];
    
    double r,g,b;
    int i1,i2,i3;

    for(idxZ = 0; idxZ <= maxZ; idxZ++ ) {
        self->UpdateProgress(idxZ/float(maxZ));
        sprintf(progressText,"Merging channels (slice %d / %d)",idxZ,maxZ);
        self->SetProgressText(progressText);
        
        for(idxY = 0; idxY <= maxY; idxY++ ) {
          for(idxX = 0; idxX <= maxX; idxX++ ) {
            scalar = currScalar = 0;
            n = 0;
            alphaScalar =  0;
            for(i=0; i < NumberOfInputs; i++ ) {
                currScalar = *inPtrs[i];
                
                if(BuildAlpha && MaxMode) {
                        if(alphaScalar < currScalar) {
                            alphaScalar = currScalar;
                        }
                    // If the alpha channel should be in "average mode"
                    // then we take an average of all the scalars in the
                    // current voxel that are above the AverageThreshold
                } else if(BuildAlpha && AvgMode) {
                    if(currScalar > AvgThreshold) {
                        n++;
                        alphaScalar += currScalar;
                    }
                }              
                
                i1=int(3*currScalar);
                i2=int(3*currScalar)+1;
                i3=int(3*currScalar)+2;
                
                r += mapctfs[i][i1];
                g += mapctfs[i][i2];
                b += mapctfs[i][i3];
                
                //scalar += currScalar;
                inPtrs[i]++;
            }
            r*=255.0;
            g*=255.0;
            b*=255.0;
            if(r>maxval)r=maxval;
            if(g>maxval)g=maxval;
            if(b>maxval)b=maxval;
            if(BuildAlpha && LuminanceMode) {
                alphaScalar = 0.30*r + 0.59*g + 0.11*b;
            }   
            *outPtr++ = (T)(r);
            *outPtr++ = (T)(g);
            *outPtr++ = (T)(b);
            r=g=b=0;
            if(BuildAlpha) {
                if(AvgMode && n>0) alphaScalar /= n;
                if(alphaScalar > maxval)alphaScalar=maxval;
                *outPtr++ = (T)alphaScalar;
            }
          }
            
            
          
          for(i=0; i < NumberOfInputs; i++ ) {
              inPtrs[i]+=inIncY;
          }
          outPtr += outIncY;
        }  
        for(i=0; i < NumberOfInputs; i++ ) {
          inPtrs[i]+=inIncZ;
        }
        outPtr += outIncZ;      
//  printf("Processed slice %d\n",idxZ);
    }
  
    
    // If all itfs where not identical, then we need to release the individual modified ctfs as well
    if(!allIdentical) {
        for(int i = 0; i < NumberOfInputs; i++) {
            delete modctfs[i];
        }
    }
    delete itfs;
    delete modctfs;
    delete[] inPtrs;
}

//----------------------------------------------------------------------------
// This method is passed a input and output regions, and executes the filter
// algorithm to fill the output from the inputs.
// It just executes a switch statement to call the correct function for
// the regions data types.
void vtkImageColorMerge::ThreadedExecute(vtkImageData **inData, 
                                     vtkImageData *outData,
                                     int outExt[6], int id)
{
  int idx1;
  int inExt[6], cOutExt[6];

  switch (inData[0]->GetScalarType())
  {
  vtkTemplateMacro7(vtkImageColorMergeExecute, this, id, 
                    this->NumberOfInputs,inData, 
                    outData, outExt,static_cast<VTK_TT *>(0));
  default:
    vtkErrorMacro(<< "Execute: Unknown ScalarType");
  return;
  }    
    
}



//----------------------------------------------------------------------------
void vtkImageColorMerge::PrintSelf(ostream& os, vtkIndent indent)
{
  this->Superclass::PrintSelf(os, indent);
}














