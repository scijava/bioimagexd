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
 
 Bugs:
      Lots of them.
      Creating a new spline curve crashes the animator.

 This code is distributed under the conditions of the BSD license.  See
 LICENSE.txt for details.

 Copyright (c) 2004, Heikki Uuksulainen.
 Modified 2005 for BioImageXD Project: Kalle Pahajoki
"""

__author__ = "Heikki Uuksulainen and Prabhu Ramachandran"
__version__ = "$Revision: 0.1 $"
__date__ = "$Date: 2004/01/20 22:41:28 $"

import types, os
import string
#import vtk,vtkRenderWidget
import vtk
from mayavi import Common
from vtk.util.colors import tomato, banana

import wx
import wx.lib.scrolledpanel as scrolled
from vtk.wx.wxVTKRenderWindowInteractor import *

math = vtk.vtkMath()


class SplineWidget3D:
    """
    This class just wraps the vtkSplineWidget.
    """
    
    def __init__(self,wxrenwin):
        self.dataExtensionX = 50
        self.dataExtensionY = 50
        self.dataExtensionZ = 50
        
        self.data = None
        self.outline = vtk.vtkOutlineFilter ()
        self.outlinemapper = vtk.vtkPolyDataMapper ()
        self.outlineactor = vtk.vtkActor ()  
        self.axes = vtk.vtkCubeAxesActor2D ()
        self.spline = False

        self.spline = spline = vtk.vtkSplineWidget()
        
        
        self.wxrenwin = wxrenwin
       
        
        self.renWin = renWin = self.wxrenwin.GetRenderWindow()

        self.renderer=vtk.vtkRenderer()
        self.renWin.AddRenderer(self.renderer)
        ren = self.renderer

        if not ren:
            raise "No renderer in SplineEditor!"

        #self.iren = iren = renWin.GetInteractor()
        print "Initializing camera"
        self.init_camera()
        
        
    def init_spline(self,points=5):
        self.spline.SetInteractor(self.iren)        
        self.spline.GetLineProperty().SetColor(1,0,0)
        self.spline.SetNumberOfHandles(points)
        for i in range(self.spline.GetNumberOfHandles()):
            self.spline.SetHandlePosition(i,math.Random(-self.dataExtensionX,self.data_width()+self.dataExtensionX),
                                     math.Random(-self.dataExtensionY,self.data_height()+self.dataExtensionY),
                                     math.Random(-self.dataExtensionZ,self.data_depth()+self.dataExtensionZ))
        self.spline.On()
        self.rendererder()

    def update_data(self,data):
        print "Updating data..."
        if self.data:
            del self.data

        self.data = data
        self.outline.SetInput(self.data)
        self.outlinemapper.SetInput (self.outline.GetOutput ())
        self.outlineactor.SetMapper (self.outlinemapper)
        #self.outlineactor.GetProperty ().SetColor (*Common.config.fg_color)
        self.outlineactor.GetProperty().SetColor((255,255,255))
        self.renderer.AddActor(self.outlineactor)

        txt = ("X", "Y", "Z")
        for t in txt:
                eval ("self.axes.%sAxisVisibilityOn ()"%t)
                #eval ("self.axes.Get%sAxisActor2D().LabelVisibilityOff()"%(txt[i]))
                #eval ("self.axes.Get%sAxisActor2D().SetPoint1(0.0,0.0)"%(txt[i]))
                eval ("self.axes.Get%sAxisActor2D().SetLabelFactor(0.5)"%t)

        #self.axes.GetProperty ().SetColor (*Common.config.fg_color)
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

        #self.init_camera()

        #self.init_spline()

        #self.rendererder()

        #iren.Initialize()
        #renWin.Render()
        #iren.Start()

    def render(self):
        self.renderer.Render()

    def get_number_of_points(self):
        data = vtk.vtkPolyData()
        self.spline.GetPolyData(data)
        return data.GetNumberPoints()        

    def get_points(self):
        data = vtk.vtkPolyData()
        self.spline.GetPolyData(data)
        return data

    def get_control_points(self):
        points = []
        for i in range(self.spline.GetNumberOfHandles()):
            points.append(self.spline.GetHandlePosition(i))
            
        return points

    def is_active(self):
        return self.spline.GetEnabled()

    def get_camera(self):
        cam = None
        if self.renderer:
            cam = self.renderer.GetActiveCamera()
        return cam

    def init_camera(self):
        cam = self.get_camera()
        if cam:
            focal = self.get_camera_focal_point_center()
            cam.SetFocalPoint(focal)
            cam.SetPosition(self.get_initial_camera_position())
            cam.ComputeViewPlaneNormal()
        else:
            print "No camera in SplineWidget3D"


    def get_initial_camera_position(self):
        if not self.data:
            return [0,0,0]
        dims = self.data.GetDimensions()
        return 1.5*dims[0],0.5*dims[1],100.0*dims[2]
        
    def get_camera_focal_point_center(self):
        if not self.data:
            return [0,0,0]
        return self.data.GetCenter()

    def data_width(self):
        if not self.data:
            return 0
        return (self.data.GetDimensions())[0]

    def data_height(self):
        if not self.data:
            return 0
        return (self.data.GetDimensions())[1]

    def data_depth(self):
        if not self.data:
            return 0
        return (self.data.GetDimensions())[2]
    
    def data_dimensions(self):
        return self.data.GetDimensions()

    def __del__(self):
        print "In SplineWidget3D.__del__()"        
        del self.renWin


class SplineEditor(wxPanel):
    """
    Creates the window for spline.
    """

    def __init__(self, parent, width=250, height=100):
        wx.Panel.__init__(self,parent,size=(width,height))
        self.sizer=wxGridBagSizer(5,5)
       
        self.parent=parent
        self.data = None


        self.renderer = ren = vtk.vtkRenderer ()
        #self.renWin = renWin = vtk.vtkRenderWindow()
        #self.iren = vtk.vtkRenderWindowInteractor()
        #self.iren.SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())
        #self.renWin.SetInteractor(self.iren)
        #renWin.AddRenderer(ren)
        
        self.wxrenwin=wxVTKRenderWindowInteractor(self,-1,size=(400,400))

        self.renWin = self.wxrenwin.GetRenderWindow()
        self.renWin.GetInteractor().SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())
        self.renWin.AddRenderer(ren)
      
        self.sizer.Add(self.wxrenwin,(0,0),flag=wx.EXPAND|wx.ALL)

        ren.SetBackground(1.0,1.0,1.0)

        self.splinew = SplineWidget3D(self.wxrenwin)

        self.SetSizer(self.sizer)
        self.SetAutoLayout(True)
        self.sizer.Fit(self)


    def __del__(self):
        print "SplineEditor.__del__()"
        
    def  update_data(self,data):
        if self.data:
            del self.data
        self.data = data
        self.splinew.update_data(self.data)

    def render(self):
        self.splinew.render()

    def get_camera(self):
        return self.splinew.get_camera()

    def get_points(self):
        return self.splinew.get_points()


    def init_spline(self,num_of_points):
        self.splinew.init_spline(num_of_points)

    def init_camera(self):
        self.splinew.init_camera()

    def get_control_points(self):
        return self.splinew.get_control_points()


    def is_active(self):
        return self.splinew.is_active()

    def data_width(self):
        if not self.data:
            return 0
        return (self.data.GetDimensions())[0]

    def data_height(self):
        if not self.data:
            return 0
        return (self.data.GetDimensions())[1]

    def data_depth(self):
        if not self.data:
            return 0
        return (self.data.GetDimensions())[2]

    def quit(self):
        print "In SplineEditor.quit()"
        #del self.renWin
        #del self.renderer
        #self.tkwidget.destroy()
        #del self.tkwidget
        
