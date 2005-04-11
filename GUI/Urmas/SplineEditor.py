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

 Copyright (c) 2004, Heikki Uuksulainen.
 Modified 2005 for BioImageXD Project: Kalle Pahajoki
 
 BioImageXD includes the following persons:
 
 DW - Dan White, dan@chalkie.org.uk
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 PK - Pasi Kankaanpää, ppkank@bytl.jyu.fi
 
"""

__author__ = "Heikki Uuksulainen and Prabhu Ramachandran"
__version__ = "$Revision: 0.1 $"
__date__ = "$Date: 2004/01/20 22:41:28 $"


import types, os
import string

import vtk
from mayavi import Common
from vtk.util.colors import tomato, banana

import wx
import wx.lib.scrolledpanel as scrolled
from vtk.wx.wxVTKRenderWindowInteractor import wxVTKRenderWindowInteractor

import PreviewFrame


math = vtk.vtkMath()
            
class SplineEditor(wx.Panel):
    """
    Class: SplineEditor
    Created: Heikki Uuksulainen
    Description: A class for editing a spline
    """           

    def __init__(self, parent, width=400,height=400):
        """
        Method: __init__
        Created: Heikki Uuksulainen
        Description: Initialization
        """           
        wx.Panel.__init__(self,parent,size=(width,height))
        self.sizer=wx.GridBagSizer(5,5)
       
        self.cameraHandles={}
       
        self.parent=parent
        self.data = None

        self.wxrenwin=wxVTKRenderWindowInteractor(self,-1,size=(width,height))

        self.initializeVTK()
        
        self.sizer.Add(self.wxrenwin,(0,0),flag=wx.EXPAND|wx.ALL)
            
        self.SetSizer(self.sizer)
        self.SetAutoLayout(True)
        self.sizer.Fit(self)

    def initializeVTK(self):
        """
        Method: initializeVTK()
        Created: 20.03.2005, HU, KP
        Description: Code to initialize VTK portions of this widget
        """           
        self.renderer = ren = vtk.vtkRenderer ()
        self.renWin = self.wxrenwin.GetRenderWindow()
        self.renWin.GetInteractor().SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())
        self.renWin.AddRenderer(ren)
        self.renWin.Render()
        ren.SetBackground(1.0,1.0,1.0)

        self.dataExtensionX = 50
        self.dataExtensionY = 50
        self.dataExtensionZ = 50
        
        self.data = None
        self.interactionCallback=None
        
        self.outline = vtk.vtkOutlineFilter ()
        self.outlinemapper = vtk.vtkPolyDataMapper ()
        self.outlineactor = vtk.vtkActor ()  
        self.axes = vtk.vtkCubeAxesActor2D ()
        self.spline = False

        self.spline = spline = vtk.vtkSplineWidget()
        self.spline.SetResolution(1000)
        
        self.spline.AddObserver("EndInteractionEvent",self.endInteraction)
                
        self.renderer=vtk.vtkRenderer()
        self.renWin.AddRenderer(self.renderer)
        ren = self.renderer

        if not ren:
            raise "No renderer in SplineEditor!"
        self.iren = iren = self.renWin.GetInteractor()
        print "Initializing camera"
        self.initCamera()
    
    def findControlPoint(self,pt):
        """
        Method: findControlPoint(point)
        Created: 20.03.2005, KP
        Description: This method returns the point that contains the given
                     spline handle
        """           
        pps=self.getControlPoints()
        return pps[pt]
        
        
        
    def addCameraHandle(self,sp):
        """
        Method: addCameraHandle(sp)
        Created: 20.03.2005, KP
        Description: Adds a handle that can be used to control the camera
                     position on a particular spline point
        """           
        if sp in self.cameraHandles:
            return
        cone=vtk.vtkConeSource()
        
        cone.SetHeight(30.0)
        cone.SetRadius(10.0)
        cone.SetResolution(10)
        
        mapper=vtk.vtkPolyDataMapper()
        
        mapper.SetInput(cone.GetOutput())
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.VisibilityOn()
        box=vtk.vtkBoxWidget()
        box.SetInteractor(self.iren)
        box.SetPlaceFactor(1.25)
        
        self.renderer.AddActor(actor)
        self.render()
        t=vtk.vtkTransform()
        p=self.findControlPoint(sp)
        p1=[1.1*a for a in p]
        print "Positioning handle in ",p1,"near",p
        t.Translate(p1)
        #actor.SetUserTransform(t)
        
        box.SetTransform(t)
        box.SetProp3D(actor)
        box.PlaceWidget()
        
        text=vtk.vtkVectorText()
        text.SetText("Camera %d"%sp)
        textmapper=vtk.vtkPolyDataMapper()
        textmapper.SetInput(text.GetOutput())
        textactor=vtk.vtkFollower()
        textactor.SetMapper(textmapper)
        textactor.SetScale(0.1,0.1,0.1)
        textactor.AddPosition(0,-0.1,0)
        textactor.SetUserTransform(t)
        
        self.renderer.AddActor(textactor)
        
        lst=[actor,mapper,box,t,textmapper,textactor,text]
        box.AddObserver("InteractionEvent",self.transformCameraHandle)
        box.On()
        box.OutlineFaceWiresOff()
        box.HandlesOff()
        box.OutlineCursorWiresOff()
        #box.ScalingEnabledOff()
        op = box.GetOutlineProperty()
        op.SetRepresentationToWireframe()
        op.SetLineWidth(0)
        self.cameraHandles[sp]=lst
        self.text=textactor
        
    def transformCameraHandle(self,obj,event):
        print "Transform camera handle"
        t=vtk.vtkTransform()
        obj.GetTransform(t)
        obj.GetProp3D().SetUserTransform(t)
        self.text.SetUserTransform(t)
        
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

        p0,p1=pps[ip0],pps[ip1]
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
        
    def getCameraPosition(self,p0,p1,percentage):
        """
        Method: getCameraPosition(p0,p1,percentage)
        Created: KP, 05.04.2005
        Description: Method that returns the camera position when it is located a given percentage
                     of the way from point p0 to p1
        """        
        points = self.getPoints()
        n=points.GetNumberOfPoints()
        pps=self.getControlPoints()
        if p1[0]==-1:
            print "Using last point as p1"
            p1=points.GetPoint(points.GetNumberOfPoints()-1)
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
        p=int((pp1-pp0)*percentage)
        return (p,points.GetPoint(p))
         
    
        
    def updateData(self,data):
        """
        Method: updateData(data)
        Created: Heikki Uuksulainen
        Description: Method that initializes the VTK rendering based
                     on a dataset
        """        
    
        print "Updating data..."
        if self.data:
            del self.data

        self.data = data
        
        self.outline.SetInput(self.data)
        self.outlinemapper.SetInput (self.outline.GetOutput ())
        self.outlineactor.SetMapper (self.outlinemapper)
        self.outlineactor.GetProperty().SetColor((255,255,255))
        
        self.renderer.AddActor(self.outlineactor)
        
        txt = ("X", "Y", "Z")
        for t in txt:
                eval ("self.axes.%sAxisVisibilityOn ()"%t)
                #eval ("self.axes.Get%sAxisActor2D().LabelVisibilityOff()"%(txt[i]))
                #eval ("self.axes.Get%sAxisActor2D().SetPoint1(0.0,0.0)"%(txt[i]))
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
        
        self.renderer.AddActor (self.axes)
        self.axes.SetInput (self.outline.GetOutput ())
        
        #print "Axes actor inertia: %d"%(self.axes.GetInertia())

        self.renderer.Render()

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

    def initSpline(self,points):
        """
        Method: initSpline(number_of_points)
        Created: Heikki Uuksulainen
        Description: Creates a random spline with given amount of points
        """        
        lst=[]
        for i in range(points):
            pt=(math.Random(-self.dataExtensionX,self.dataWidth()+self.dataExtensionX),
                math.Random(-self.dataExtensionY,self.dataHeight()+self.dataExtensionY),
                math.Random(-self.dataExtensionZ,self.dataDepth()+self.dataExtensionZ))
            lst.append(pt)
        self.setSplinePoints(lst)
            
    def setSplinePoints(self,pointlist):
        """
        Method: setSplinePoints(pointlist)
        Created: KP, 06.04.2005
        Description: Sets the handles of the spline widget to the given point list
        """        
        self.spline.SetInteractor(self.iren)        
        self.spline.GetLineProperty().SetColor(1,0,0)
        self.spline.SetNumberOfHandles(len(pointlist))
        for i in range(self.spline.GetNumberOfHandles()):
            self.spline.SetHandlePosition(i,pointlist[i])
        self.spline.On()
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
        #del self.renWin
        #del self.renderer
        #self.tkwidget.destroy()
        #del self.tkwidget
        
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
        self.renderer.Render()
