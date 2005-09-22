/*=========================================================================

  Program:   BioImageXD
  Module:    $RCSfile: vtkImageScatterPlot.cxx,v $

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
#include "vtkImageScatterPlot.h"

#include "vtkImageData.h"
#include "vtkObjectFactory.h"

vtkCxxRevisionMacro(vtkImageScatterPlot, "$Revision: 1.25 $");
vtkStandardNewMacro(vtkImageScatterPlot);

//----------------------------------------------------------------------------
vtkImageScatterPlot::vtkImageScatterPlot()
{
    ZSlice=-1;
    CountVoxels = 1;
}

//----------------------------------------------------------------------------
vtkImageScatterPlot::~vtkImageScatterPlot()
{
}


//----------------------------------------------------------------------------
// This method tells the ouput it will have more components
void vtkImageScatterPlot::ExecuteInformation(vtkImageData **inputs, 
                                        vtkImageData *output)
{
    vtkImageMultipleInputFilter::ExecuteInformation(inputs,output);

    int wholeExt[6];


    wholeExt[1]=wholeExt[3]=255;
    wholeExt[0]=wholeExt[2]=0;
    wholeExt[4]=wholeExt[5]=0;
    //printf("extent of scatterplot is (%d,%d,%d,%d,%d,%d)\n",wholeExt[0],wholeExt[1],wholeExt[2],wholeExt[3],wholeExt[4],wholeExt[5]);
    // We're gonna produce image one slice thick and 255x255 in size
    output->SetWholeExtent(wholeExt);
    output->RequestExactExtentOff();
    output->SetUpdateExtent(wholeExt);

    if (!CountVoxels) {
        output->SetNumberOfScalarComponents(3);    
    } else {
        output->SetScalarType(VTK_LONG);
        output->SetNumberOfScalarComponents(1);          
    }
}

void vtkImageScatterPlot::ComputeInputUpdateExtents( vtkDataObject*output )
{
      int outExt[6], inExt[6];
    inExt[0]=inExt[1]=inExt[2]=inExt[3]=inExt[4]=inExt[5]=0;
    //printf("Setting input update\n");
      for (int idx = 0; idx < this->NumberOfInputs; idx++)
    {
        if (this->Inputs[idx] != NULL)
        {
    //      this->Inputs[idx]->SetUpdateExtent( this->Inputs[idx]->GetWholeExtent() );
            this->Inputs[idx]->SetUpdateExtent( inExt);
        }
    }
}

//----------------------------------------------------------------------------
// This templated function executes the filter for any type of data.
template <class T>
void vtkImageScatterPlotExecute(vtkImageScatterPlot *self, int id,int NumberOfInputs, 
                           vtkImageData **inData,vtkImageData*outData,int outExt[6],
                            T*)
{
    int i;
    int inIncX,inIncY,inIncZ;
    int outIncX,outIncY,outIncZ;
    int maxX,maxY,maxZ;
    int z0 = 0, z1 = 0;
    int idxX,idxY,idxZ;
    int inExt[6];
    
    inData[0]->GetWholeExtent(inExt);
    T** inPtrs;
    inPtrs=new T*[NumberOfInputs];
    //printf("outext=[%d,%d,%d,%d,%d,%d]\n",outExt[0],outExt[1],outExt[2],outExt[3],outExt[4],outExt[5]);
    //printf("inext=[%d,%d,%d,%d,%d,%d]\n",inExt[0],inExt[1],inExt[2],inExt[3],inExt[4],inExt[5]);     
    for(i=0; i < NumberOfInputs; i++) {
        inPtrs[i]=(T*)inData[i]->GetScalarPointer();//ForExtent(inExt);
    }
    int countvox=self->GetCountVoxels();
    inData[0]->GetIncrements(inIncX,inIncY,inIncZ);
    maxX = inExt[1] - inExt[0];
    maxY = inExt[3] - inExt[2];
    maxZ = inExt[5] - inExt[4];
    
    long*outLongPtr=(long*)outData->GetScalarPointer();//ForExtent(outExt);
    T*outPtr=(T*)outData->GetScalarPointer();//ForExtent(outExt);
    for(int i=0;i<maxX*maxY;i++)*outPtr++=0;    
    outPtr=(T*)outData->GetScalarPointer();//ForExtent(outExt);        
//    inData[0]->GetContinuousIncrements(inExt,inIncX, inIncY, inIncZ);
    
    T redScalar = 0, greenScalar = 0;
    //double outScalar = 0;
    //double maxCount = 0;
    long outScalar = 0, maxCount = 0;
    int maxval = 0;
    maxval=int(pow(2,8*sizeof(T)))-1;
    T val;
    
     
     outData->GetIncrements(outIncX, outIncY, outIncZ);
    printf("outIncX=%d, outIncY=%d,outIncZ=%d",outIncX,outIncY,outIncZ);
     printf("inIncX=%d, inIncY=%d,inIncZ=%d",inIncX,inIncY,inIncZ);
    #define GET_AT(x,y,z,ptr) *(ptr+(z)*inIncZ+(y)*inIncY+(x)*inIncX)
    #define SET_AT(x,y,z,ptr,val) *(ptr+(z)*outIncZ+(y)*outIncY+(x)*outIncX)=val
    #define SET_AT_COMP(x,y,z,c,ptr,val) *(ptr+(int)((z)*outIncZ)+(int)((y)*outIncY)+(int)((x)*outIncX)+(c))=val
    #define GET_AT_OUT(x,y,z,ptr) *(ptr+(z)*outIncZ+(y)*outIncY+(x)*outIncX)
    #define SET_AT_OUT(x,y,z,ptr,val) *(ptr+(z)*outIncZ+(y)*outIncY+(x)*outIncX)=val
     
     if(0&&countvox) {
        outIncX*=sizeof(VTK_LONG_MAX);
        outIncY*=sizeof(VTK_LONG_MAX);
        outIncZ*=sizeof(VTK_LONG_MAX);         
     }

    if(self->GetZSlice()<0) {
        z0 = 0;
        z1 = maxZ;
    } else {
        z1 = z0 = self->GetZSlice();
    }
    
    printf("maxX=%d,maxY=%d,z0=%d,z1=%d\n",maxX,maxY,z0,z1);
    //for(idxY = 0; idxY <= maxY; idxY++) {
    //for(idxX = 0; idxX <= maxX; idxX++) {
    //        SET_AT(idxX,idxY,0,outPtr,0);
    //    }
    //}
 //   printf("sizeof(outScalar)=%d\n",sizeof(outScalar));
    
    
    for(idxY = 0; idxY <= maxY; idxY++) {
        for(idxX = 0; idxX <= maxX; idxX++) {
            for(idxZ = z0; idxZ <= z1; idxZ++) {
                redScalar=GET_AT(idxX,idxY,idxZ,inPtrs[0]);
                greenScalar=GET_AT(idxX,idxY,idxZ,inPtrs[1]);
                //printf("Got scalars %d,%d\n",redScalar,greenScalar);
                
                if (!countvox) {
                    SET_AT_COMP(greenScalar,redScalar,0,0,outPtr,redScalar);
                    SET_AT_COMP(greenScalar,redScalar,0,1,outPtr,greenScalar);
                    SET_AT_COMP(greenScalar,redScalar,0,2,outPtr,0);
                } else {
                    //printf("sizeof(output)=%d\n",sizeof(GET_AT_OUT((int)greenScalar,(int)redScalar,0,outLongPtr)));
                    outScalar = (long)GET_AT_OUT((int)greenScalar,(int)redScalar,0,outLongPtr);
                    //if(redScalar>100 && greenScalar > 100)
                    //    printf("Reading from %d,%d=%d\n",greenScalar,redScalar,outScalar);
                    outScalar++;
                    if (outScalar > maxCount) {
                        //printf("There are %d (%d,%d) pairs\n",maxCount,greenScalar,redScalar);
                        maxCount = outScalar;
                    }
                        
                    SET_AT_OUT((int)greenScalar,(int)redScalar,0,outLongPtr,outScalar);
                }
            }
        }
    }
    delete[] inPtrs;
    printf("maxCount=%d\n",maxCount);
    self->SetNumberOfPairs(maxCount);
}

// This method is passed a input and output regions, and executes the filter
//  algorithm to fill the output from the inputs.
//  It just executes a switch statement to call the correct function for
//  the regions data types.
 void vtkImageScatterPlot::ThreadedExecute(vtkImageData **inData,
                                      vtkImageData *outData,
                                      int outExt[6], int id)
 {
   int idx1;
   int inExt[6], cOutExt[6];
 
   switch (inData[0]->GetScalarType())
   {
   vtkTemplateMacro7(vtkImageScatterPlotExecute, this, id,
                     this->NumberOfInputs,inData,
                     outData, outExt,static_cast<VTK_TT *>(0));
   default:
     vtkErrorMacro(<< "Execute: Unknown ScalarType");
   return;
   }
 
 }
 
//----------------------------------------------------------------------------
void vtkImageScatterPlot::PrintSelf(ostream& os, vtkIndent indent)
{
  this->Superclass::PrintSelf(os, indent);
}














