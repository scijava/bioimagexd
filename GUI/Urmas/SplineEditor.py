# -*- coding: iso-8859-1 -*-
"""
 Unit: SplineEditor
 Project: BioImageXD
 Created: n/a
 Creator: Heikki Uuksulainen
 Description:

 This module defines gui for editing the spline which defines the
 camera path.

 Changes:
            10.02.2005 KP - Started integration with wxPython and Selli
            20.03.2005 KP - Integrated the classes SplineWidget3D and SplineEditor
                            into one. Unnecessary repetition together with minimal
                            effort required to convert the new SplineEditor to any
                            other GUI library give this move justification.
 
 Bugs:
      Lots of them.
      Creating a new spline curve crashes the animator.

 This code is distributed under the conditions of the BSD license.  See
 LICENSE.txt for details.

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
"""

__author__ = "Heikki Uuksulainen and Prabhu Ramachandran"
__version__ = "$Revision: 0.1 $"
__date__ = "$Date: 2004/01/20 22:41:28 $"


import types, os
import string

import vtk
from vtk.util.colors import tomato, banana

import wx
import wx.lib.scrolledpanel as scrolled
from vtk.wx.wxVTKRenderWindowInteractor import wxVTKRenderWindowInteractor
from vtk.wx.wxVTKRenderWindow import wxVTKRenderWindow
import PreviewFrame


math = vtk.vtkMath()
            
class SplineEditor:
    """
    Class: SplineEditor
    Created: Heikki Uuksulainen
    Description: A class for editing a spline
    """           

    def __init__(self, parent, renwin, width=600,height=400):
        """
        Method: __init__
        Created: Heikki Uuksulainen
        Description: Initialization
        """                  
        self.cameraHandles={}
       
        self.parent=parent
        self.data = None
        self.wxrenwin=renwin
        self.initializeVTK()

    def initializeVTK(self):
        """
        Method: initializeVTK()
        Created: 20.03.2005, HU, KP
        Description: Code to initialize VTK portions of this widget
        """           

        self.renWin = self.wxrenwin.GetRenderWindow()
        self.renderer = ren = vtk.vtkRenderer ()
        self.renWin.AddRenderer(ren)
        ren.SetBackground(0,0,0)
        self.wxrenwin.Render()

        self.iren = iren = self.renWin.GetInteractor()
        self.iren.SetSize(self.renWin.GetSize())
        self.iren.SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())

        self.dataExtensionX = 50
        self.dataExtensionY = 50
        self.dataExtensionZ = 50

        self.data = None
        self.interactionCallback=None


        self.outline = vtk.vtkOutlineFilter ()
        self.outlinemapper = vtk.vtkPolyDataMapper ()
        self.outlineactor = vtk.vtkActor ()
        self.axes = vtk.vtkCubeAxesActor2D ()

        self.spline = spline = vtk.vtkSplineWidget()
        self.spline.GetLineProperty().SetColor(1,0,0)
        self.spline.GetHandleProperty().SetColor(0,1,0)
#        print "Setting current renderer to",self.renderer

        self.spline.SetResolution(1000)

        self.spline.AddObserver("EndInteractionEvent",self.endInteraction)
        self.spline.AddObserver("InteractionEvent",self.endInteraction)
        if not ren:
            raise "No renderer in SplineEditor!"
        print "Initializing camera"
        self.initCamera()
        self.spline.SetInteractor(self.iren)
        self.initSpline(2)
        self.spline.On()
        self.spline.SetEnabled(1)
        self.wxrenwin.Render()

    def setClosed(self,flag):
        """
        Method: setClosed(flag)
        Created: 14.04.2005, KP
        Description: Sets the spline closed or open
        """
        if flag:
            self.spline.ClosedOn()
        else:
            self.spline.ClosedOff()
        self.render()

    def getBounds(self):
        """
        Method: getBounds(self)
        Created: 18.04.2005, KP
        Description: Returns the bounds of the dataset
        Order of bounds returned:
        """
        xmin,xmax,ymin,ymax,zmin,zmax = self.data.GetBounds()
        #print xmin,xmax,ymin,ymax,zmin,zmax
        p1 = (xmin,ymin,zmin)
        p2 = (xmax,ymin,zmin)
        p3 = (xmax,ymax,zmin)
        p4 = (xmin,ymax,zmin)

        p5 = (xmin,ymin,zmax)
        p6 = (xmax,ymin,zmax)
        p7 = (xmax,ymax,zmax)
        p8 = (xmin,ymax,zmax)
        return [p1,p2,p3,p4,p5,p6,p7,p8]

        
        

    def findControlPoint(self,pt):
        """
        Method: findControlPoint(point)
        Created: 20.03.2005, KP
        Description: This method returns the point that contains the given
                     spline handle
        """           
        pps=self.getControlPoints()
        return pps[pt]
        


    def setInteractionCallback(self,cb):
        """
        Method: setInteractionCallback
        Created: 19.03.2005, KP
        Description: Method to set a callback that is called when an interaction
                     with the spline ends
        """
        self.interactionCallback=cb

    def getSplineLength(self,ip0=0,ip1=0):
        """
        Method: getSplineLength(point1,point2)
        Created: 19.03.2005, KP
        Description: Method that returns the length of the spline between
                     the given two points. If no points are given, the total
                     length of the spline is returned.
        """
        if not (ip0 or ip1):
            return self.spline.GetSummedLength()
        points = self.getPoints()
        n=points.GetNumberOfPoints()
        pps=self.getControlPoints()

        # If the second point goes beyond the control points, then use the
        # last point in the spline
        if ip1>=len(pps):
            p1=points.GetPoint(n-1)
        else:
            p1=pps[ip1]
        p0=pps[ip0]

        pp0,pp1=-1,-1
        d0,d1=2**64,2**64

        for i in range(n):
            p=points.GetPoint(i)
            d=vtk.vtkMath.Distance2BetweenPoints(p,p0)
            if d<d0:
                d0,pp0=d,i
            d=vtk.vtkMath.Distance2BetweenPoints(p,p1)
            if d<d1:
                d1,pp1=d,i
        d=0
        if pp0<0 or pp1<0:
            raise "Did not find point"
            
        p0=points.GetPoint(pp0)
        p1=points.GetPoint(pp1)
        sd=vtk.vtkMath.Distance2BetweenPoints(p0,p1)
        #print "Calculating distance from ",pp0,"to",pp1
        for x in range(pp0+1,pp1+1):
            p1=points.GetPoint(x)
            d+=vtk.vtkMath.Distance2BetweenPoints(p0,p1)
            p0=p1
        #print "Distance",d,", straight distance",sd
        return d
        
    def getCameraPosition(self,n,p0,percentage):
        """
        Method: getCameraPosition(n,p0,percentage)
        Created: KP, 05.04.2005
        Description: Method that returns the camera position when it is located a given percentage
                     of the way from point p0 (the nth control point) to next spline point
        """        
        pps = self.getControlPoints()
        cp0 = pps[n]
        nskip=0
        for i in range(n):
            if pps[i]==cp0:
                nskip+=1
        
        points = self.getPoints()
        npts = points.GetNumberOfPoints()
        d0 = 2**64
        pointindex =  -1
        pointindex2 = -1
        closest = -1
        d0 = 2**64
        for i in range(npts):
            p = points.GetPoint(i)
            d = vtk.vtkMath.Distance2BetweenPoints(p,cp0)
            if d < 1:
                if nskip:nskip-=1
                else:pointindex = i
                break
            if d<d0:
                closest = i
                d0 = d
        
        if pointindex != closest:
            if pointindex < 0 or abs(closest - pointindex) <5:
                #print "Using closest %d instead of the one we found %d"%(closest,pointindex)
                pointindex = closest
            else:
                raise "Didn't get closest!"
        if n == len(pps)-1:
            #print "Using last point"
            pointindex2 = npts-1
        else:
            cp1 = pps[n+1]
            closest = -1
            d0 = 2**64
            for i in range(pointindex,npts):
                p = points.GetPoint(i)
                d = vtk.vtkMath.Distance2BetweenPoints(p,cp1)
                if d < 1:
                    pointindex2 = i
                    break
                if d<d0:
                    closest = i
                    d0 = d
            if pointindex2 != closest:
                if pointindex2 < 0 or abs(closest - pointindex2) <5:
                    #print "Using closest %d instead of the one we found %d"%(closest,pointindex2)
                    pointindex2 = closest
                else:
                    raise "Didn't get closest!"                    
        #print "Pointindex = ",pointindex," to ",pointindex2,"percent=",percentage
        n = pointindex+(pointindex2-pointindex)*percentage
        return (n,points.GetPoint(n))
                    
    
        
    def updateData(self,data,ctf=None):
        """
        Method: updateData(data)
        Created: Heikki Uuksulainen
        Description: Method that initializes the VTK rendering based
                     on a dataset
        """            
        if self.data:
            del self.data

        self.data = data
        #print "Got data=",data
        
        self.outline.SetInput(self.data)
        self.outlinemapper.SetInput (self.outline.GetOutput ())
        self.outlineactor.SetMapper (self.outlinemapper)
        self.outlineactor.GetProperty().SetColor((255,255,255))

        self.renderer.AddActor(self.outlineactor)

        # Create transfer mapping scalar value to opacity
        opacityTransferFunction = vtk.vtkPiecewiseFunction()
        opacityTransferFunction.AddPoint(50, 0.0)
        opacityTransferFunction.AddPoint(255, 0.15)

        colorTransferFunction = ctf
        if not colorTransferFunction:
            print "DIDN'T GET CTF!!"
            # Create transfer mapping scalar value to color
            colorTransferFunction = vtk.vtkColorTransferFunction()
            colorTransferFunction.AddRGBPoint(0.0, 0.0, 0.0, 0.0)
            colorTransferFunction.AddRGBPoint(255.0, 0.0, 1.0, 0.0)
        
        volumeProperty = vtk.vtkVolumeProperty()
        volumeProperty.SetColor(colorTransferFunction)
        volumeProperty.SetScalarOpacity(opacityTransferFunction)
        #volumeProperty.ShadeOn()
        #volumeProperty.SetInterpolationTypeToLinear()

        
        volumeMapper = vtk.vtkVolumeTextureMapper2D()
        volumeMapper.SetMaximumNumberOfPlanes(18)
        data.Update()
        volumeMapper.SetInput(data)
        
        volume = vtk.vtkVolume()
        volume.SetMapper(volumeMapper)
        volume.SetProperty(volumeProperty)
        
        txt = ("X", "Y", "Z")
        for t in txt:
                eval ("self.axes.%sAxisVisibilityOn ()"%t)
                eval ("self.axes.Get%sAxisActor2D().SetLabelFactor(0.5)"%t)

        self.axes.GetProperty ().SetColor ((255,255,255))
        self.axes.SetNumberOfLabels (2)
        self.axes.SetFontFactor (1.0)
        self.axes.SetFlyModeToOuterEdges ()
        #self.axes.SetFlyModeToClosestTriad ()
        self.axes.SetCornerOffset (0.0)
        #self.axes.SetInertia(10)
        self.axes.ScalingOff ()
        self.axes.SetCamera (self.renderer.GetActiveCamera ())
        #if hasattr(self.axes, "GetAxisTitleTextProperty"):
        #    self.axes.GetAxisTitleTextProperty().ShadowOff()
        #    self.axes.GetAxisLabelTextProperty().ShadowOff()
        #else:
        #    self.axes.ShadowOff ()

        self.renderer.AddVolume(volume)
        self.renderer.AddActor (self.axes)
        self.axes.SetInput (self.outline.GetOutput ())

        #print "Axes actor inertia: %d"%(self.axes.GetInertia())

        self.renderer.Render()
        self.wxrenwin.Render()

    def getCamera(self):
        """
        Method: getCamera()
        Created: Heikki Uuksulainen
        Description: If there's a currently active camera, returns it
        """
        cam = None
        if self.renderer:
            cam = self.renderer.GetActiveCamera()
        return cam

    def getPoints(self):
        """
        Method: getPoints()
        Created: Heikki Uuksulainen
        Description: Returns the points of the polygon forming the spline
        """
        data = vtk.vtkPolyData()
        self.spline.GetPolyData(data)
        return data
        
    def getRandomPoint(self):
        """
        Method: getRandomPoint()
        Created: 14.04.2005, KP
        Description: Return a random point for the spline
        """        
        pt=(math.Random(-self.dataExtensionX,self.dataWidth()+self.dataExtensionX),
                math.Random(-self.dataExtensionY,self.dataHeight()+self.dataExtensionY),
                math.Random(-self.dataExtensionZ,self.dataDepth()+self.dataExtensionZ))
        return pt

    def initSpline(self,points):
        """
        Method: initSpline(number_of_points)
        Created: Heikki Uuksulainen
        Description: Creates a random spline with given amount of points
        """        
        lst=[]
        for i in range(points):
            pt = self.getRandomPoint()
            #self.spline.SetHandlePosition(i,pt)
            lst.append(pt)
        self.setSplinePoints(lst)
            
    def setSplinePoints(self,pointlist):
        """
        Method: setSplinePoints(pointlist)
        Created: KP, 06.04.2005
        Description: Sets the handles of the spline widget to the given point list
        """
        #print "Setting spline points to",pointlist

        n = len(pointlist)
        self.spline.SetNumberOfHandles(n)
        for i in range(n):
            self.spline.SetHandlePosition(i,pointlist[i])
            #self.spline.SetHandleSize(100)
        #
        #self.spline.GetHandleProperty().SetColor(0,0,1)
        self.spline.SetEnabled(1)

        self.renderer.Render()

    def setSplinePoint(self,pos,point):
        """
        Method: setSplinePoint(pos,point)
        Created: KP, 11.04.2005
        Description: Sets the a handle of the spline widget to a given point
        """        
        self.spline.SetHandlePosition(pos,point)
    
        
    def initCamera(self):
        """
        Method: initCamera()
        Created: Heikki Uuksulainen
        Description: Initializes the camera
        """        
        cam = self.getCamera()
        if cam:
            focal = self.getCameraFocalPointCenter()
            cam.SetFocalPoint(focal)
            cam.SetPosition(self.getInitialCameraPosition())
            cam.ComputeViewPlaneNormal()
        else:
            print "No camera in SplineEditor"



    def getInitialCameraPosition(self):
        """
        Method: getInitialCameraPosition()
        Created: Heikki Uuksulainen
        Description: Returns an initial position for the camera
        """        
        if not self.data:
            return [0,0,0]
        dims = self.data.GetDimensions()
        return 1.5*dims[0],0.5*dims[1],100.0*dims[2]
        
    def getCameraFocalPointCenter(self):
        """
        Method: getCameraFocalPointCenter()
        Created: Heikki Uuksulainen
        Description: Returns the center of the current dataset
        """        
    
        if not self.data:
            return [0,0,0]
        return self.data.GetCenter()
            
            
    def getControlPoints(self):
        """
        Method: getControlPoints
        Created: Heikki Uuksulainen
        Description: Returns the points for the handles of the widget
        """        
        points = []
        for i in range(self.spline.GetNumberOfHandles()):
            points.append(self.spline.GetHandlePosition(i))
            
        return points

    def isActive(self):
        """
        Method: isActive()
        Created: Heikki Uuksulainen
        Description: A method that tells whether the spline is enabled or not
        """            
        return self.spline.GetEnabled()

    def dataWidth(self):
        """
        Method: dataWidth()
        Created: Heikki Uuksulainen
        Description: Returns the width of the data
        """       
        if not self.data:
            return 0
        return (self.data.GetDimensions())[0]

    def dataHeight(self):
        """
        Method: dataHeight
        Created: Heikki Uuksulainen
        Description: Returns the height of the data
        """       
        if not self.data:
            return 0
        return (self.data.GetDimensions())[1]

    def dataDepth(self):
        """
        Method: dataDepth
        Created: Heikki Uuksulainen
        Description: Returns the depth of the data
        """           
        if not self.data:
            return 0
        return (self.data.GetDimensions())[2]
    
    def dataDimensions(self):
        """
        Method: dataDimensions()
        Created: Heikki Uuksulainen
        Description: Returns the dimensions of the data
        """           
        return self.data.GetDimensions()

    def getNumberOfPoints(self):
        """
        Method: getNumberOfPoints
        Created: Heikki Uuksulainen
        Description: Returns the number of points in the polygon that forms
                     the spline
        """           
        data = vtk.vtkPolyData()
        self.spline.GetPolyData(data)
        return data.GetNumberPoints()        

    def quit(self):
        """
        Method: quit
        Created: Heikki Uuksulainen
        Description: Destructs necessary objects upon quitting
        """           
        pass
        
    def endInteraction(self,event=-1,e2=-1):
        """
        Method: endInteraction()
        Created: 19.03.2005, KP
        Description: Method called when user manipulates the spline and then 
                     lets the mouse button up. Used to call a callback.
        """               
        if self.interactionCallback:
            self.interactionCallback()

    def __del__(self):     
        """
        Method: __del__()
        Created: Heikki Uuksulainen
        Description: Destructs renderwindow
        """           
        del self.renWin

    def render(self):
        """
        Method: render()
        Created: Heikki Uuksulainen
        Description: Render the widget
        """
        #self.renderer.Render()
        self.wxrenwin.Render()
