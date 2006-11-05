/*=========================================================================

  Program:   BioImageXD
  Module:    $RCSfile: vtkVolumeRayCastRGBCompositeFunction.h,v $

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
// .NAME vtkVolumeRayCastRGBCompositeFunction - a ray function for compositing

// .SECTION Description
// vtkVolumeRayCastRGBCompositeFunction is a ray function that can be used
// within a vtkVolumeRayCastMapper. This function performs compositing along
// the ray according to the properties stored in the vtkVolumeProperty for
// the volume. 

// .SECTION See Also
// vtkVolumeRayCastMapper vtkVolumeProperty vtkVolume

#ifndef __vtkVolumeRayCastRGBCompositeFunction_h
#define __vtkVolumeRayCastRGBCompositeFunction_h

#include "vtkVolumeRayCastFunction.h"

#define VTK_COMPOSITE_CLASSIFY_FIRST 0
#define VTK_COMPOSITE_INTERPOLATE_FIRST 1

#include "vtkBXDProcessingWin32Header.h"

class VTK_BXD_PROCESSING_EXPORT vtkVolumeRayCastRGBCompositeFunction : public 
vtkVolumeRayCastFunction
{
public:
  static vtkVolumeRayCastRGBCompositeFunction *New();
  vtkTypeRevisionMacro(vtkVolumeRayCastRGBCompositeFunction,
  vtkVolumeRayCastFunction);
  void PrintSelf( ostream& os, vtkIndent indent );

  // Description:
  // Set the CompositeMethod to either Classify First or Interpolate First
  vtkSetClampMacro( CompositeMethod, int,
        VTK_COMPOSITE_CLASSIFY_FIRST, VTK_COMPOSITE_INTERPOLATE_FIRST );
  vtkGetMacro(CompositeMethod,int);
  void SetCompositeMethodToInterpolateFirst()
    {this->SetCompositeMethod(VTK_COMPOSITE_INTERPOLATE_FIRST);}
  void SetCompositeMethodToClassifyFirst() 
    {this->SetCompositeMethod(VTK_COMPOSITE_CLASSIFY_FIRST);}
  const char *GetCompositeMethodAsString(void);

//BTX
  void CastRay( vtkVolumeRayCastDynamicInfo *dynamicInfo,
                vtkVolumeRayCastStaticInfo *staticInfo);

  float GetZeroOpacityThreshold( vtkVolume *vol );
//ETX

protected:
  vtkVolumeRayCastRGBCompositeFunction();
  ~vtkVolumeRayCastRGBCompositeFunction();

//BTX
  void SpecificFunctionInitialize( vtkRenderer *ren,
                                   vtkVolume   *vol,
                                   vtkVolumeRayCastStaticInfo *staticInfo,
                                   vtkVolumeRayCastMapper *mapper );
//ETX
  
  int           CompositeMethod;
private:
  vtkVolumeRayCastRGBCompositeFunction(const 
  vtkVolumeRayCastRGBCompositeFunction&);  // Not implemented.
  void operator=(const vtkVolumeRayCastRGBCompositeFunction&); // Not implemented.
};


#endif
