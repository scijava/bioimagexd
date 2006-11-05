/*=========================================================================

  Program:   Visualization Toolkit
  Module:    $RCSfile: vtkDistanceRepresentationScaled2D.h,v $

  Copyright (c) Ken Martin, Will Schroeder, Bill Lorensen
  All rights reserved.
  See Copyright.txt or http://www.kitware.com/Copyright.htm for details.

     This software is distributed WITHOUT ANY WARRANTY; without even
     the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
     PURPOSE.  See the above copyright notice for more information.

=========================================================================*/
// .NAME vtkDistanceRepresentationScaled2D - represent the vtkDistanceWidget
// .SECTION Description
// The vtkDistanceRepresentationScaled2D is a representation for the
// vtkDistanceWidget. This representation consists of a measuring line (axis)
// and two vtkHandleWidgets to place the end points of the line. Note that
// this particular widget draws its representation in the overlay plane.

// .SECTION See Also
// vtkDistanceWidget vtkDistanceRepresentation


#ifndef __vtkDistanceRepresentationScaled2D_h
#define __vtkDistanceRepresentationScaled2D_h

#include "vtkBXDProcessingWin32Header.h"
#include "vtkDistanceRepresentation.h"

class vtkAxisActor2D;
class vtkProperty2D;


class VTK_BXD_PROCESSING_EXPORT vtkDistanceRepresentationScaled2D : public vtkDistanceRepresentation
{
public:
  // Description:
  // Instantiate class.
  static vtkDistanceRepresentationScaled2D *New();

  // Description:
  // Standard VTK methods.
  vtkTypeRevisionMacro(vtkDistanceRepresentationScaled2D,vtkDistanceRepresentation);
  void PrintSelf(ostream& os, vtkIndent indent);

  // Description:
  // Satisfy the superclasses API.
  virtual double GetDistance() 
    {return this->Distance;}

  // Description:
  // Methods to Set/Get the coordinates of the two points defining
  // this representation. Note that methods are available for both
  // display and world coordinates.
  void GetPoint1WorldPosition(double pos[3]);
  void GetPoint2WorldPosition(double pos[3]);
  void SetPoint1DisplayPosition(double pos[3]);
  void SetPoint2DisplayPosition(double pos[3]);
  void GetPoint1DisplayPosition(double pos[3]);
  void GetPoint2DisplayPosition(double pos[3]);

  // Description:
  // Retrieve the vtkAxisActorScaled2D used to draw the measurement axis. With this 
  // properties can be set and so on.
  vtkAxisActor2D *GetAxis();

     
  vtkSetMacro(ScaleX,double);
  vtkGetMacro(ScaleX,double);
     vtkSetMacro(ScaleZ,double);
     vtkGetMacro(ScaleZ,double);
  // Description:
  // Method to satisfy superclasses' API.
  virtual void BuildRepresentation();

  // Description:
  // Methods required by vtkProp superclass.
  virtual void ReleaseGraphicsResources(vtkWindow *w);
  virtual int RenderOverlay(vtkViewport *viewport);
  virtual int RenderOpaqueGeometry(vtkViewport *viewport);

protected:
  vtkDistanceRepresentationScaled2D();
  ~vtkDistanceRepresentationScaled2D();

  // Add a line to the mix
  vtkAxisActor2D *AxisActor;
  vtkProperty2D  *AxisProperty;
  
  // The distance between the two points
  double Distance;
  double ScaleX;
  double ScaleZ;

private:
  vtkDistanceRepresentationScaled2D(const vtkDistanceRepresentationScaled2D&);  //Not implemented
  void operator=(const vtkDistanceRepresentationScaled2D&);  //Not implemented
};

#endif
