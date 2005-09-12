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
    this->SetReferencePoint( (this->MaximumThreshold - this->MinimumThreshold) / 2,
                             (this->MaximumValue - this->MinimumValue) / 2);  
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

void vtkIntensityTransferFunction::GetSlopeStart(int *x,int *y) {
    int b;
    
    b = int(this->ReferencePoint[1]-this->Contrast*this->ReferencePoint[0]);
    *y = this->MinimumValue;
    *x = int( (this->MinimumValue - b ) / this->Contrast );
}

void vtkIntensityTransferFunction::GetSlopeEnd(int *x, int *y) {
    int b;
    b = int(this->ReferencePoint[1]-this->Contrast*this->ReferencePoint[0]);
    *y = this->MaximumValue;
    *x = int( (this->MaximumValue - b ) / this->Contrast );
}
void vtkIntensityTransferFunction::GetGammaPoints(int *gx0, int *gy0, int *gx1, int *gy1) {
    int x0=0,y0=0,x1=0,y1=0;
    int y = 0, x = 0, b = 0;
    int minX = 0, minY = 0;
    // Calculate where the slope ends (x = 255)
    b = int(this->ReferencePoint[1]-this->Contrast*this->ReferencePoint[0]);
    y = LineValue(255);
    
    // If we cross the ceiling
    if ( y > 255 ) {
        minY = LineValue(this->MaximumThreshold);
        if(minY >255)minY = 255;
        //x = int( (this->MaximumValue - b) / this->Contrast );
        x = int( (minY - b) / this->Contrast );        
        x1=x;
        //printf("x1=%d\n",x1);
        y1= minY;
        vtkDebugMacro(<<"Cross the ceiling, x1="<<x1<<",y1="<<y1<<"\n");


    } else { // If we do not cross the ceiling
        x1 = this->MaximumThreshold;
        //y1 = y;
        y1 = LineValue(x1);
        vtkDebugMacro(<<"Don't cross the ceiling, x1="<<x1<<",y1="<<y1<<"\n");
    }

    y = int( this->Contrast*0 + b );
    // If we cross the floor
    if ( y < 0 ) {
        minX = LineValue(this->MinimumThreshold);
        if(minX<0)minX=0;
        if (this->MinimumValue > minX) minX = this->MinimumValue;

        x = int( ( minX - b) / this->Contrast );
        x0 = x;
        //printf("minX=%d\n",minX);
        y0 = minX;
        vtkDebugMacro(<<"Cross the floor, x1="<<x1<<",y1="<<y1<<"\n");

    } else {
        x0 = this->MinimumThreshold;
        y0 = LineValue(x0);
        vtkDebugMacro(<<"Don't cross the floor, x1="<<x1<<",y1="<<y1<<"\n");
    }
    *gx0 = x0;
    *gy0 = y0;
    *gx1 = x1;
    *gy1 = y1;
}

void vtkIntensityTransferFunction::CalculateReferencePoint(void) {
    int x=0,y=0;
    x=this->ReferencePoint[0];
    //y=this->ReferencePoint[1];
    y = (this->MaximumValue - this->MinimumValue) / 2;
    //x= 128 + this->Brightness;
    x= 128 - this->Brightness;
    this->SetReferencePoint(x,y);
}

int vtkIntensityTransferFunction:: LineValue(int x) {
    int b;
    b = int(this->ReferencePoint[1]-this->Contrast*this->ReferencePoint[0]);
    return int(this->Contrast * x + b);
//      int b=this->Brightness;
//      return int(this->Contrast * x + ((255+b)/2.0)-this->Contrast*((255-b)/2.0));
}

void vtkIntensityTransferFunction::ComputeFunction(void) {
    // These are the slope start and end points (x0,y0) and (x1,y1)
    int x0=0,y0=0,x1=0,y1=0;    
    // These are the variables holding the x coordinate and 
    // the function's value at that point 
    int x=0,y=0;
    // These are the start and end points of the gamma
    int gx0=0,gy0=0,gx1=0,gy1=0;
    int flag = 0;
    int refX, refY;

    CalculateReferencePoint();
    
    GetSlopeStart(&x0,&y0);
    GetSlopeEnd(&x1,&y1);
    //printf("Slope starts at (%d,%d) and ends to (%d,%d)\n",x0,y0,x1,y1);
    //printf("Contrast = %f\n",this->Contrast);
    // There's no harm in calculating these
    GetGammaPoints(&gx0,&gy0,&gx1,&gy1); 
    this->GammaStart[0]=gx0;
    this->GammaStart[1]=gy0;
    this->GammaEnd[0]=gx1;
    this->GammaEnd[1]=gy1;  
//    this->ReferencePoint[0]=gx0+((gx1-gx0)/2.0);
//    this->ReferencePoint[1]=gy0+((gy1-gy0)/2.0);

    for(x = 0;x < this->ArraySize; x++) {
    
        
        // If we're below the processing threshold,
        // then the function is identical, i.e. y=x
        if(x < this->ProcessingThreshold) {
            this->Function[x]=x;
            continue;
        }
        // If we're below minimum threshold, the function should get the
        // minimum value. But if processing threshold has a larger value than 
        // the minimum value, then we use that instead.
        if(x < this->MinimumThreshold) {
            if(this->ProcessingThreshold <= MinimumValue) {
                this->Function[x]=this->MinimumValue;
                //printf("Value = minval %d,",MinimumValue);
            } else {
                this->Function[x]=ProcessingThreshold;
                //printf("Value = processing threshold (%d)\n",ProcessingThreshold);
            }
            continue;
        }
        
        if(x >= this->MinimumThreshold) {
            y = this->MinimumValue;
        }
        
        // If the point is on the slope region
        if( x >= x0 && x <= x1 ) {
            if(x0 < this->MinimumThreshold) {
                x0 = this->MinimumThreshold;
                y = LineValue(x0);
                //printf("Value at point x0=%d is %d\n",x0,y);
            }
            if(x1 > this->MaximumThreshold) {
                x1 = this->MaximumThreshold;
                y = LineValue(x1);
                //printf("Value at point x1=%d is %d\n",x1,y);                
            }
            
            if( fabs(this->Gamma-1.0) > 0.0001 ) {
                y = this->GammaValue(gx0,gy0,gx1,gy1,x,this->Gamma);
                vtkDebugMacro(<<"Y = gamma value from "<<gx0<<","<<gy0<<","<<gx1<<","<<gy1<<","<<x<<","<<y<<"\n");
            } else {
                y = LineValue(x);
                //printf("Y = linevalue(%d)=%d,",x,y);
            }
        }
        if( y > this->MaximumValue || (x > x1 && x <= this->MaximumThreshold) ) {
            y = this->MaximumValue;
        }
        
        // Once we go over the processing threshold, set a flag
        if( x > this->ProcessingThreshold && 
            y > this->ProcessingThreshold    ) flag = 1;
        
        if(y < this->MinimumValue) y = this->MinimumValue;
        // If the functions value tries to go below
        // processing threshold before we've reached
        // value above processing threshold,
        // we use the processing threshold as a minimum value
        if ( this->ProcessingThreshold     && 
            x >= this->ProcessingThreshold && 
            y < this->ProcessingThreshold  &&
            flag == 0) {
            y = this->ProcessingThreshold;
        }
        
        if( x > this->MaximumThreshold ) {
            y = this->MinimumValue;
        }
        //printf("y=%d\n",y);
        this->Function[x]=y;
    }
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
