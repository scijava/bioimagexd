/*=========================================================================

  Program)   BioImageXD
  Module)    $RCSfile) vtkPiecewiseFunction.cxx,v $

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
#include "vtkIntensityTransferFunction.h"
#include "vtkSource.h"
#include "vtkObjectFactory.h"

vtkCxxRevisionMacro(vtkIntensityTransferFunction, "$Revision) 1.37 $");
vtkStandardNewMacro(vtkIntensityTransferFunction);

// Construct a new vtkIntensityTransferFunction with default values
vtkIntensityTransferFunction::vtkIntensityTransferFunction()
{
  this->ArraySize        = 256;
  this->Function         = new int[this->ArraySize];
  this->FunctionRange[0] = 0;
  this->FunctionRange[1] = 0;
  this->SmoothStart=0;
  this->SmoothStartGamma=1;
  this->SmoothEnd=255;
  this->SmoothEndGamma=1;

  for (int i=0; i < this->ArraySize; i++)
    {
    this->Function[i] = 0;
    }
    this->Reset();
}

void vtkIntensityTransferFunction::Reset(void) {

    this->MinimumValue = 0;
    this->MaximumValue = 255;
    this->MinimumThreshold = 0;
    this->MaximumThreshold = 255;
    this->Gamma = 1;
    this->Contrast = 1;
    this->Brightness = 0;
    this->ProcessingThreshold = 0;
    this->SmoothStart=0;
    this->SmoothStartGamma=1;
    this->SmoothEnd=255;
    this->SmoothEndGamma=1;
    this->Modified();
}

// Destruct a vtkIntensityTransferFunction
vtkIntensityTransferFunction::~vtkIntensityTransferFunction()
{
  if( this->Function )
    {
    delete [] this->Function;
    }
}

void vtkIntensityTransferFunction::DeepCopy( vtkDataObject *o )
{
  vtkIntensityTransferFunction *f = vtkIntensityTransferFunction::SafeDownCast(o);

  if (f  !=  NULL)
    {
    this->ArraySize    = f->ArraySize;
    memcpy( this->FunctionRange, f->FunctionRange, sizeof(int) );
    if ( this->ArraySize > 0 )
      {
      delete [] this->Function;
      this->Function     = new int[this->ArraySize];
      memcpy( this->Function, f->Function, this->ArraySize*sizeof(int) );
      }

    this->Modified();
    }

  // Do the superclass
  this->vtkDataObject::DeepCopy(o);
}

void vtkIntensityTransferFunction::ShallowCopy( vtkDataObject *o )
{
  vtkIntensityTransferFunction *f = vtkIntensityTransferFunction::SafeDownCast(o);

  if (f  !=  NULL)
    {
    this->ArraySize    = f->ArraySize;
    this->Function     = new int[this->ArraySize];
    memcpy( this->FunctionRange, f->FunctionRange, sizeof(int) );
    memcpy( this->Function, f->Function, this->ArraySize*sizeof(int) );
    }

  // Do the superclass
  this->vtkDataObject::ShallowCopy(o);
}

void vtkIntensityTransferFunction::Initialize()
{
  if ( this->Function)
    {
    delete [] this->Function;
    }

  this->ArraySize        = 256;
  this->Function         = new int[this->ArraySize];
  this->FunctionRange[0] = 0;
  this->FunctionRange[1] = 0;

  for (int i=0; i < this->ArraySize; i++)
    {
    this->Function[i] = 0;
    }
}


// Return the number of points which specify this function
int vtkIntensityTransferFunction::GetSize()
{
  this->Update();
  return( this->ArraySize );
}


int vtkIntensityTransferFunction::GetValue( int x ) {
    if(this->LastMTime < this->GetMTime()) this->ComputeFunction();
    this->LastMTime=this->GetMTime();

    return this->Function[x];
}

// Return the mtime of this object, or the source - whicheve is greater
// This way the pipeline will update correctly
unsigned long vtkIntensityTransferFunction::GetMTime()
{
  unsigned long mt1, mt2, mtime;

  mt1 = this->vtkObject::GetMTime();

  if ( this->Source )
    {
    mt2 = this->Source->GetMTime();
    }
  else
    {
    mt2 = 0;
    }

  mtime = (mt1 > mt2)?(mt1):(mt2);

  return mtime;
}

// Returns the first point location which starts a non-zero segment of the
// function. Note that the value at this point may be zero.
double vtkIntensityTransferFunction::GetFirstNonZeroValue()
{
  int   i;
  int   all_zero = 1;
  int x = 0;

  this->Update();

  // Check if no points specified
  if( this->ArraySize == 0 )
    {
    return( 0 );
    }

  for( i=0; i < this->ArraySize; i++ )
    {
    if( this->Function[i]  !=  0 )
      {
      x = this->Function[i];
      all_zero = 0;
      break;
      }
    }

  // If every specified point has a zero value then return the first points
  // position
  if( all_zero )
    {
    x = this->Function[0];
    }
  else  // A point was found with a non-zero value
    {
    if( i > 0 )
      // Return the value of the point that precedes this one
      {
      x = this->Function[i];
      }
    else
      // If this is the first point in the function, return its value
      {
      x = this->Function[0];
      }
    }

  return( x );
}

// Removes all points from the function.
void vtkIntensityTransferFunction::RemoveAllPoints()
{
  if (!this->ArraySize)
    {
    return;
    }
  this->ArraySize     = 0;
  this->FunctionRange[0] = 0;
  this->FunctionRange[1] = 0;
  this->Modified();
}



// Increase the size of the array used to store the function
void vtkIntensityTransferFunction::IncreaseArraySize()
{
  int *old_function;
  int   old_size;

  int   i;

  old_function = this->Function;
  old_size     = this->ArraySize;

  // Create larger array to store points
  this->ArraySize = old_size * 2;
  this->Function  = new int[(this->ArraySize)];

  // Copy points from old array to new array
  for( i=0; i<old_size; i++ )
    {
    this->Function[(i)]   = old_function[i];
    }

  // Initialize the rest of the memory to avoid purify problems
  for ( ; i < this->ArraySize; i++ )
    {
    this->Function[i]   = 0;
    }

  delete [] old_function;
}

int vtkIntensityTransferFunction::GammaValue(int x0,int y0, int x1,int y1,int x, double g) {
    return int( ( (y1-y0)/ ( pow((x1-x0),g)) )* ( pow((x-x0),g) ) + y0 );
}


#define f2(x) (this->Contrast*(x)+(d))

void vtkIntensityTransferFunction::ComputeFunction(void) {
    int bx1,bx2,by1,by2;
    int midx,midy;
    int y;
    if(this->Brightness>0) {
        bx1 = 0;
        by1 = this->Brightness;
        bx2 = 255 - this->Brightness;
        by2 = 255;
    } else {
        bx1 = -this->Brightness;
        by1 = 0;
        bx2 = 255;
        by2 = 255 + this->Brightness;
    }
    if(bx1 < this->MinimumThreshold) {
        bx1 = this->MinimumThreshold;
        by1 = bx1 + this->Brightness;
    }
    if(by1 < this->MinimumValue) {
        by1 = this->MinimumValue;
        bx1 = by1 - this->Brightness;
    }
    if(bx2 > this->MaximumThreshold) {
        bx2 = this->MaximumThreshold;
        by2 = bx2 + this->Brightness;
    }
    if(by2 > this->MaximumValue) {
        by2 = this->MaximumValue;
        bx2 = by2 - this->Brightness;
    }
    midx = int(0.5*(bx1+bx2));
    midy= int(0.5*(by1+by2));
    this->ReferencePoint[0]=midx;
    this->ReferencePoint[1]=midy;

    int d = int(0.5*(by1+by2)-0.5*(bx1+bx2)*this->Contrast);

    int gx1,gx2,gy1,gy2;

    if(d >= 0 && f2(255)<= 255) {
        gx1 = 0; gy1 = d;
        gx2 = 255; gy2 = int(255*this->Contrast+d);
    }
    if(d >= 0 && f2(255)>255) {
        gx1 = 0; gy1 = d;
        gx2 = int((255 -d)/float(this->Contrast)); gy2 = 255;
    }
    if(d < 0 && f2(255)<= 255) {
        gx1 = int((0-d)/float(this->Contrast)); gy1 = 0;
        gx2 = int((255 -d)/float(this->Contrast)); gy2 = int(255*this->Contrast+d);
    }
    if(d < 0 && f2(255)> 255) {
        gx1 = int((0-d)/float(this->Contrast)); gy1 = 0;
        gx2 = int((255 -d)/float(this->Contrast)); gy2 = 255;
    }
    if(gx1 < this->MinimumThreshold) {
        gx1 = this->MinimumThreshold;
        gy1 = int(this->Contrast*gx1+d);
    }
    if(gy1 < this->MinimumValue) {
        gy1 = this->MinimumValue;
        gx1 = int((gy1 - d) / this->Contrast);
    }
    if(gx2 > this->MaximumThreshold) {
        gx2 = this->MaximumThreshold;
        gy2 = int(this->Contrast*gx2+d);
    }
    if(gy2 > this->MaximumValue) {
        gy2 = this->MaximumValue;
        gx2 = int((gy2 - d) / this->Contrast);
    }


    #define powsg(x) double(pow((x),this->SmoothStartGamma))
    #define poweg(x) double(pow((x),this->SmoothEndGamma))
    for(int x=0; x <= 255; x++) {

        y = f4(x,gx1,gy1,gx2,gy2);
        if(x < this->SmoothStart) {
            int f4val = f4(this->SmoothStart,gx1,gy1,gx2,gy2);
            y = int((powsg(x)*f4val)/powsg(this->SmoothStart));
        }
        if(x > this->SmoothEnd) {
            int f4val = f4(this->SmoothEnd,gx1,gy1,gx2,gy2);
            y = int(poweg(x-SmoothEnd)*(-f4val/poweg(255-SmoothEnd)))+f4val;
        }
        this->Function[x] = y;
    }


}

int vtkIntensityTransferFunction::f4(int x, int gx1,int gy1,int gx2,int gy2) {
    int y;
    if(x < gx1) {
        y = this->MinimumValue;
    }
    if(x <= gx2 && x >= gx1) {
        y = GammaValue(gx1,gy1,gx2,gy2,x,this->Gamma);

    }
    if(x > gx2 && x <= this->MaximumThreshold) {
        y = this->MaximumValue;
    }
    if(x > this->MaximumThreshold) {
        y = this->MinimumValue;
    }
    return y;
}

bool vtkIntensityTransferFunction::IsIdentical() {
    if(this->Gamma != 1) return 0;
    if(this->Contrast != 1) return 0;
    if(this->Brightness != 0) return 0;
    if(this->MinimumValue != 0) return 0;
    if(this->MaximumValue != 255) return 0;
    if(this->MinimumThreshold != 0) return 0;
    if(this->MaximumThreshold != 255) return 0;
    if(this->ProcessingThreshold != 0) return 0;
    if(this->SmoothStart != 0)return 0;
    if(this->SmoothStartGamma != 1)return 0;
    if(this->SmoothEnd != 0)return 0;
    if(this->SmoothEndGamma != 1)return 0;

    return 1;
}



// Print method for tkPiecewiseFunction
void vtkIntensityTransferFunction::PrintSelf(ostream& os, vtkIndent indent)
{
  this->Superclass::PrintSelf(os, indent);

  int i;

  os << indent << "Minimum Value: " << this->MinimumValue << "\n";
  os << indent << "Minimum Threshold: " << this->MinimumThreshold << "\n";
  os << indent << "Maximum Value: " << this->MaximumValue << "\n";
  os << indent << "Maximum Threshold: " << this->MaximumThreshold << "\n";
  os << indent << "Processing Threshold: " << this->ProcessingThreshold << "\n";
  os << indent << "Gamma: " << this->Gamma << "\n";
  os << indent << "Contrast: " << this->Contrast << "\n";
  os << indent << "Brightness: " << this->Brightness << "\n";
  if ( this->Gamma ) {
    os << indent << "Gamma Start Point: (" << this->GammaStart[0] <<", "<< this->GammaStart[1] << ")\n";
    os << indent << "Gamma End Point: (" << this->GammaEnd[0] <<", "<< this->GammaEnd[1] << ")\n";
  }
  os << indent << "Function Points: " << this->GetSize() << "\n";

  for( i = 0; i < this->ArraySize; i++ )
    {
    os << indent << indent
       << i << " -> " << this->GetValue(i) << ", ";
    }
    os << "\n";
}
