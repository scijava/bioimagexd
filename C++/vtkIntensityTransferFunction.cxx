/*=========================================================================

  Program:   Visualization Toolkit
  Module:    $RCSfile: vtkPiecewiseFunction.cxx,v $

  Copyright (c) Ken Martin, Will Schroeder, Bill Lorensen
  All rights reserved.
  See Copyright.txt or http://www.kitware.com/Copyright.htm for details.

     This software is distributed WITHOUT ANY WARRANTY; without even
     the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
     PURPOSE.  See the above copyright notice for more information.

=========================================================================*/
#include "vtkIntensityTransferFunction.h"
#include "vtkSource.h"
#include "vtkObjectFactory.h"

vtkCxxRevisionMacro(vtkIntensityTransferFunction, "$Revision: 1.37 $");
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

  if (f != NULL)
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

  if (f != NULL)
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

// Return the type of function stored in object:
// Function Types:
//    0 : Constant        (No change in slope between end points)
//    1 : NonDecreasing   (Always increasing or zero slope)
//    2 : NonIncreasing   (Always decreasing or zero slope)
//    3 : Varied          (Contains both decreasing and increasing slopes)
//    4 : Unknown         (Error condition)
//
const char *vtkIntensityTransferFunction::GetType()
{
  int   i;
  int value;
  int prev_value = 0;
  int   function_type;

  this->Update();

  function_type = 0;

  if( this->FunctionSize )
    {
    prev_value = this->Function[0];
    }

  for( i=0; i < this->ArraySize; i++ )
    {
    value = this->Function[i];

    // Do not change the function type if equal
    if( value != prev_value )
      {
      if( value > prev_value )
        {
        switch( function_type )
          {
          case 0:
          case 1:
            function_type = 1;  // NonDecreasing
            break;
          case 2:
            function_type = 3;  // Varied
            break;
          }
        }
      else // value < prev_value
        {
        switch( function_type )
          {
          case 0:
          case 2:
            function_type = 2;  // NonIncreasing
            break;
          case 1:
            function_type = 3;  // Varied
            break;
          }
        } 
      }

    prev_value = value;

    // Exit loop if we find a Varied function
    if( function_type == 3 )
      {
      break;
      }
    }

  switch( function_type )
    {
    case 0:
      return( "Constant" );
    case 1:
      return( "NonDecreasing" );
    case 2:
      return( "NonIncreasing" );
    case 3:
      return( "Varied" );
    }

    return( "Unknown" );
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
    if( this->Function[i] != 0 )
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


// Return the smallest and largest position stored in function
double *vtkIntensityTransferFunction::GetRange()
{
  return( this->FunctionRange );
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
  this->Function  = new double[(this->ArraySize)];

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

void vtkIntensityTransferFunction::FillFromDataPointer(int nb, int *ptr)
{
  if (nb <= 0 || !ptr)
    {
    return;
    }

  this->RemoveAllPoints();
  int*fptr=this->Function;
  while (nb)
    {
	*fptr++=*ptr++;
	nb--;
    }
}

// Print method for tkPiecewiseFunction
void vtkIntensityTransferFunction::PrintSelf(ostream& os, vtkIndent indent)
{
  this->Superclass::PrintSelf(os, indent);
  
  int i;

  os << indent << "Function Points: " << this->GetSize() << "\n";
  for( i = 0; i < this->ArraySize; i++ )
    {
    os << indent << indent << i << ": " 
       << i << ", " << this->Function[i] << "\n";
    }
}
