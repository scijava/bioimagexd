/*=========================================================================

  Program:   Visualization Toolkit
  Module:    $RCSfile: vtkImageSolitaryFilter.cxx,v $

  Copyright (c) Ken Martin, Will Schroeder, Bill Lorensen
  All rights reserved.
  See Copyright.txt or http://www.kitware.com/Copyright.htm for details.

     This software is distributed WITHOUT ANY WARRANTY; without even
     the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
     PURPOSE.  See the above copyright notice for more information.

=========================================================================*/
#include "vtkImageSolitaryFilter.h"

#include "vtkCellData.h"
#include "vtkImageData.h"
#include "vtkObjectFactory.h"
#include "vtkPointData.h"

vtkCxxRevisionMacro(vtkImageSolitaryFilter, "$Revision: 1.36 $");
vtkStandardNewMacro(vtkImageSolitaryFilter);

//-----------------------------------------------------------------------------
// Construct object to extract all of the input data.
vtkImageSolitaryFilter::vtkImageSolitaryFilter()
{
  this->FilteringThreshold = 0;
  this->HorizontalThreshold = 0;
  this->VerticalThreshold = 0;

}

//-----------------------------------------------------------------------------
// Get ALL of the input.
void vtkImageSolitaryFilter::ComputeInputUpdateExtent(int inExt[6], 
                                             int *)
{
  // request all of the VOI
  int *wholeExtent;
  int i;
  
  wholeExtent = this->GetInput()->GetWholeExtent();
  memcpy(inExt, wholeExtent, 6*sizeof(int));

}

//-----------------------------------------------------------------------------
void 
vtkImageSolitaryFilter::ExecuteInformation(vtkImageData *input, vtkImageData *output)
{
  this->vtkImageToImageFilter::ExecuteInformation( input, output );
}

//-----------------------------------------------------------------------------
void vtkImageSolitaryFilter::ExecuteData(vtkDataObject *)
{

}


//-----------------------------------------------------------------------------
void vtkImageSolitaryFilter::PrintSelf(ostream& os, vtkIndent indent)
{
  this->Superclass::PrintSelf(os,indent);

  os << indent << "Filtering Threshold: "<< this->FilteringThreshold << "\n";
  os << indent << "Horizontal Threshold: "<< this->HorizontalThreshold << "\n";
  os << indent << "Vertical Threshold: "<< this->VerticalThreshold << "\n";    

}




