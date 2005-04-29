/*=========================================================================

  Program:   BioImageXD
  Module:    $RCSfile: vtkVolumeRayCastRGBCompositeFunction.cxx,v $

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
#include "vtkVolumeRayCastRGBCompositeFunction.h"

#include "vtkObjectFactory.h"
#include "vtkPiecewiseFunction.h"
#include "vtkVolume.h"
#include "vtkVolumeProperty.h"
#include "vtkVolumeRayCastMapper.h"

#include <math.h>
#include <stdio.h>

vtkCxxRevisionMacro(vtkVolumeRayCastRGBCompositeFunction, "$Revision: 1.39 $");
vtkStandardNewMacro(vtkVolumeRayCastRGBCompositeFunction);

#define VTK_REMAINING_OPACITY           0.02



// Constructor for the vtkVolumeRayCastRGBCompositeFunction class
vtkVolumeRayCastRGBCompositeFunction::vtkVolumeRayCastRGBCompositeFunction()
{
  this->CompositeMethod = VTK_COMPOSITE_INTERPOLATE_FIRST;
}

// Destruct the vtkVolumeRayCastRGBCompositeFunction
vtkVolumeRayCastRGBCompositeFunction::~vtkVolumeRayCastRGBCompositeFunction()
{
}

// This is the templated function that actually casts a ray and computes
// The composite value. This version uses nearest neighbor interpolation
// and does not perform shading.
template <class T>
void vtkCastRay_RGB_NN_Unshaded( T *data_ptr, vtkVolumeRayCastDynamicInfo 
        *dynamicInfo,  vtkVolumeRayCastStaticInfo *staticInfo )
{
  int             value=0;
  unsigned char   *grad_mag_ptr = NULL;
  float           accum_red_intensity;
  float           accum_green_intensity;
  float           accum_blue_intensity;
  float           remaining_opacity;
  float           opacity=0.0;
  int             scalar_opacity=0;
  float           gradient_opacity;
  int             loop;
  int             xinc, yinc, zinc;
  int             voxel[3];
  float           ray_position[3];
  int             prev_voxel[3];
  float           *SOTF;
  float           *CTF;
  float           *GTF;
  float           *GOTF;
  int             offset;
  int             steps_this_ray = 0;
  int             grad_op_is_constant;
  float           gradient_opacity_constant;
  int             num_steps;
  float           *ray_start, *ray_increment;
  int n=0;

  float redc=0,greenc=0,bluec=0;

  num_steps = dynamicInfo->NumberOfStepsToTake;
  ray_start = dynamicInfo->TransformedStart;
  ray_increment = dynamicInfo->TransformedIncrement;
 
  SOTF =  staticInfo->Volume->GetCorrectedScalarOpacityArray();
//  CTF  =  staticInfo->Volume->GetRGBArray();
//  GTF  =  staticInfo->Volume->GetGrayArray();
  GOTF =  staticInfo->Volume->GetGradientOpacityArray();

  // Get the gradient opacity constant. If this number is greater than
  // or equal to 0.0, then the gradient opacity transfer function is
  // a constant at that value, otherwise it is not a constant function
  gradient_opacity_constant = staticInfo->Volume->GetGradientOpacityConstant();
  grad_op_is_constant = ( gradient_opacity_constant >= 0.0 );

  // Move the increments into local variables
  xinc = 4;
  yinc = 4*staticInfo->DataSize[0];
  zinc = 4*staticInfo->DataSize[0]*staticInfo->DataSize[1];

  // Initialize the ray position and voxel location
  ray_position[0] = ray_start[0];
  ray_position[1] = ray_start[1];
  ray_position[2] = ray_start[2];
  voxel[0] = vtkRoundFuncMacro( ray_position[0] );
  voxel[1] = vtkRoundFuncMacro( ray_position[1] );
  voxel[2] = vtkRoundFuncMacro( ray_position[2] );

  // So far we haven't accumulated anything
  accum_red_intensity     = 0.0;
  accum_green_intensity   = 0.0;
  accum_blue_intensity    = 0.0;
  remaining_opacity       = 1.0;

  // Get a pointer to the gradient magnitudes for this volume
  if ( !grad_op_is_constant )
    {
    grad_mag_ptr = staticInfo->GradientMagnitudes;
    }


  // Keep track of previous voxel to know when we step into a new one
  // set it to something invalid to start with so that everything is
  // computed first time through
  prev_voxel[0] = voxel[0]-1;
  prev_voxel[1] = voxel[1]-1;
  prev_voxel[2] = voxel[2]-1;

    // For each step along the ray
    for ( loop = 0;
          loop < num_steps && remaining_opacity > VTK_REMAINING_OPACITY;
          loop++ )
      {
      // We've taken another step
      steps_this_ray++;

      // Access the value at this voxel location
      if ( prev_voxel[0] != voxel[0] ||
           prev_voxel[1] != voxel[1] ||
           prev_voxel[2] != voxel[2] )
        {
        offset = voxel[2] * zinc + voxel[1] * yinc + voxel[0] * xinc;

        value = *(data_ptr + offset);
        //opacity = SOTF[value];

        redc=*(data_ptr+offset);
        greenc=*(data_ptr+offset+1);
        bluec=*(data_ptr+offset+2);
        scalar_opacity=*(data_ptr+offset+3);

	//scalar_opacity = greenc;	    
        redc/=255.0;
        greenc/=255.0;
        bluec/=255.0;

	//printf("%f maps to %f\n",opacity,SOTF[int(opacity)]);
	opacity = SOTF[scalar_opacity];
	//opacity = scalar_opacity;
        //opacity/=255.0;
        //opacity=0.2*(scalar_opacity/255.0);


        if ( opacity )
          {
           if ( grad_op_is_constant )
            {
            gradient_opacity = gradient_opacity_constant;
            }
          else
            {

            gradient_opacity = GOTF[*(grad_mag_ptr + offset)];
            }
          opacity *= gradient_opacity;
          }
        prev_voxel[0] = voxel[0];
        prev_voxel[1] = voxel[1];
        prev_voxel[2] = voxel[2];
        }

      // Accumulate some light intensity and opacity
      accum_red_intensity   += ( opacity * remaining_opacity *
                                 redc );
      accum_green_intensity   += ( opacity * remaining_opacity *
                                 greenc );
      accum_blue_intensity   += ( opacity * remaining_opacity *
                                 bluec );
      remaining_opacity *= (1.0 - opacity);

//      printf("intensities = %f,%f,%f",accum_red_intensity,
// accum_green_intensity,accum_blue_intensity);

      // Increment our position and compute our voxel location
      ray_position[0] += ray_increment[0];
      ray_position[1] += ray_increment[1];
      ray_position[2] += ray_increment[2];
      voxel[0] = vtkRoundFuncMacro( ray_position[0] );
      voxel[1] = vtkRoundFuncMacro( ray_position[1] );
      voxel[2] = vtkRoundFuncMacro( ray_position[2] );
      }

  // Cap the intensity value at 1.0
  if ( accum_red_intensity > 1.0 )
    {
    accum_red_intensity = 1.0;
    }
  if ( accum_green_intensity > 1.0 )
    {
    accum_green_intensity = 1.0;
    }
  if ( accum_blue_intensity > 1.0 )
    {
    accum_blue_intensity = 1.0;
    }

  if( remaining_opacity < VTK_REMAINING_OPACITY )
    {
    remaining_opacity = 0.0;
    }

  // Set the return pixel value.  The depth value is the distance to the
  // center of the volume.
  dynamicInfo->Color[0] = accum_red_intensity;
  dynamicInfo->Color[1] = accum_green_intensity;
  dynamicInfo->Color[2] = accum_blue_intensity;
  dynamicInfo->Color[3] = 1.0 - remaining_opacity;
  dynamicInfo->NumberOfStepsTaken = steps_this_ray;
  
}


// This is called from RenderAnImage (in vtkDepthPARCMapper.cxx)
// It uses the integer data type flag that is passed in to
// determine what type of ray needs to be cast (which is handled
// by a templated function.  It also uses the shading and
// interpolation types to determine which templated function
// to call.
void vtkVolumeRayCastRGBCompositeFunction::CastRay( 
            vtkVolumeRayCastDynamicInfo *dynamicInfo,
            vtkVolumeRayCastStaticInfo *staticInfo )
{
  void *data_ptr;

  data_ptr = staticInfo->ScalarDataPointer;

      // Nearest neighbor and shading
      switch ( staticInfo->ScalarDataType )
        {
        case VTK_UNSIGNED_CHAR:
          vtkCastRay_RGB_NN_Unshaded( (unsigned char *)data_ptr, dynamicInfo,
           staticInfo);
          break;
        case VTK_UNSIGNED_SHORT:
          vtkCastRay_RGB_NN_Unshaded( (unsigned short *)data_ptr, dynamicInfo, 
          staticInfo);
          break;
        default:
          vtkWarningMacro ( <<"Unsigned char and unsigned short are the only "<<
          " supported datatypes for rendering" );
          break;
        }
}

float vtkVolumeRayCastRGBCompositeFunction::GetZeroOpacityThreshold( vtkVolume
                                                                  *vol )
{
  return vol->GetProperty()->GetScalarOpacity()->GetFirstNonZeroValue();
}

// We don't need to do any specific initialization here...
void vtkVolumeRayCastRGBCompositeFunction::SpecificFunctionInitialize(
                                vtkRenderer *vtkNotUsed(ren),
                                vtkVolume *vtkNotUsed(vol),
                                vtkVolumeRayCastStaticInfo *vtkNotUsed(staticInfo),
                                vtkVolumeRayCastMapper *vtkNotUsed(mapper) )
{
}

// Description:
// Return the composite method as a descriptive character string.
const char *vtkVolumeRayCastRGBCompositeFunction::GetCompositeMethodAsString(void)
{
  if( this->CompositeMethod == VTK_COMPOSITE_INTERPOLATE_FIRST )
    {
    return "Interpolate First";
    }
  if( this->CompositeMethod == VTK_COMPOSITE_CLASSIFY_FIRST )
    {
    return "Classify First";
    }
  else
    {
    return "Unknown";
    }
}

// Print method for vtkVolumeRayCastRGBCompositeFunction
// Since there is nothing local to print, just print the object stuff.
void vtkVolumeRayCastRGBCompositeFunction::PrintSelf(ostream& os, vtkIndent indent)
{
  this->Superclass::PrintSelf(os,indent);

  os << indent << "Composite Method: " << this->GetCompositeMethodAsString()
     << "\n";

}





