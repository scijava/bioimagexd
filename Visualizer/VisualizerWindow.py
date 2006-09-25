# -*- coding: iso-8859-1 -*-

"""
 Unit: VisualizerWindow
 Project: BioImageXD
 Created: 15.05.2005, KP
 Description:

 A window encapsulating wxVTKRenderWindowInteractor
           
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
__author__ = "BioImageXD Project <http://www.bioimagexd.org/>"
__version__ = "$Revision: 1.9 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import wx
import time

import vtk
from vtk.wx.wxVTKRenderWindowInteractor import wxVTKRenderWindowInteractor


import Dialogs
from VisualizationModules import *
from ModuleConfiguration import *
from Lights import *

        


class VisualizerWindow(wxVTKRenderWindowInteractor):
    """
    Class: VisualizationWindow
    Created: 3.5.2005, KP
    Description: A window for showing 3D visualizations
    """
    def __init__(self,parent,**kws):
        """
        Method: __init__(parent)
        Created: 3.05.2005, KP
        Description: Initialization
        """    
        wxVTKRenderWindowInteractor.__init__(self,parent,-1,**kws)
        self.renderer=None
        self.doSave=0
        self.zoomFactor=1.0
        self.rendering=0
        self.rubberband=0
        self.controlled="Camera"
        self.control="Joystick"
        self.enabled = 1
        self.origParallelScale = None
        self.origViewAngle = None
        
    def enable(self,flag):
        """
        Method: enable(flag)
        Created: 02.06.2005, KP
        Description: Enable/Disable updates
        """
        self.enabled = flag
        
    def isEnabled(self):
        return self.enabled
        
    def Render(self):
        """
        Method: Render()
        Created: 05.06.2005, KP
        Description: If this windows is enabled, call the super class Render()
        """
        if self.enabled:
            wxVTKRenderWindowInteractor.Render(self)

    def initializeVTK(self):
        """
        Method: initializeVTK
        Created: 29.04.2005, KP
        Description: initialize the vtk renderer
        """
        self.keyPressEvents=[]
        self.iren = iren = self.GetRenderWindow().GetInteractor()
        #self.iren.SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())
#        self.iren.SetInteractorStyle(vtk.vtkInteractorStyleTrackballActor())
        #self.irenStyle = vtk.vtkInteractorStyleSwitch()
        self.irenStyle = vtk.vtkInteractorStyleJoystickCamera()
        #self.irenStyle.SetCurrentStyleToJoystickActor()
        self.iren.SetInteractorStyle(self.irenStyle)
        
        
        self.iren.AddObserver("KeyPressEvent",self.onKeypress)
        
        self.getRenderer()
        self.renderer.SetBackground(0,0,0)
        self.iren.SetSize(self.GetRenderWindow().GetSize())
        self.renderer.AddObserver("StartEvent",self.onRenderBegin)
        self.renderer.AddObserver("EndEvent",self.onRenderEnd)
    
    def onKeypress(self,obj,evt):
        """
        Method: onKeypress
        Created: 02.11.2005
        Description: Catch keypresses from the window and do actions
        """    
        key=obj.GetKeyCode()
        print "Key event",key
        words={"j":"Joystick","a":"Actor","c":"Camera","t":"Trackball"}
        if key in ["a","c"]:
            self.controlled=words[key]
            messenger.send(None,"set_status","Now controlling %s"%words[key])
        elif key in ["j","t"]:
            self.control=words[key]
            messenger.send(None,"set_status","Control style is %s"%words[key])
        style="vtk.vtkInteractorStyle%s%s()"%(self.control,self.controlled)
        
        
        self.irenStyle=eval(style)
        self.iren.SetInteractorStyle(self.irenStyle)
        return 0
        
        
    def getZoomFactor(self):
        """
        Created: 22.07.2005
        Description: Set the view according to given params
        """
        return self.zoomFactor
        
    def setZoomFactor(self,factor):
        """
        Created: 22.07.2005
        Description: Set the view according to given params
        """
        cam=self.renderer.GetActiveCamera()
        if self.origParallelScale != None:            
            cam.SetParallelScale(self.origParallelScale)
            cam.SetViewAngle(self.origViewAngle)
        self.zoomFactor=factor
        print "Setting zoom factor to",factor
        self.renderer.GetActiveCamera().Zoom(factor)
    
        self.renderer.Render()
        
    def setView(self,params):
        """
        Created: 22.07.2005
        Description: Set the view according to given params
        """
        self.getRenderer()
        cam=self.renderer.GetActiveCamera()
        x,y,z,a,b,c=params
        cam.SetFocalPoint(0,0,0)
        cam.SetPosition(x,y,z)
        cam.SetViewUp(a,b,c)
        self.renderer.ResetCamera()
        self.origParallelScale=cam.GetParallelScale()
        self.origViewAngle=cam.GetViewAngle()

        

    def zoomToRubberband(self):        
        """
        Method: zoomToRubberband
        Created: 30.04.2005, KP
        Description: Zoom to rubberband
        """
        self.rubberband=1
        self.oldStyle=self.iren.GetInteractorStyle()
        self.iren.SetInteractorStyle(vtk.vtkInteractorStyleRubberBandZoom())    
    
    def onRenderBegin(self,event=None,e2=None):
        """
        Method: onRenderBegin
        Created: 30.04.2005, KP
        Description: Called when rendering begins
        """
        self.rendering=1

    def onRenderEnd(self,event=None,e2=None):
        """
        Method: onRenderEnd
        Created: 30.04.2005, KP
        Description: Called when rendering begins
        """
        self.rendering=0
        if self.rubberband:
            self.iren.SetInteractorStyle(self.oldStyle)
            self.rubberband=0
        
    def save_png(self,filename):
        """
        Method: save_png(self,filename)
        Created: 28.04.2005, KP
        Description: Save the rendered screen as png
        """            
        self.saveScreen(vtk.vtkPNGWriter(),filename)

    def save_png(self,filename):
        """
        Method: save_png(self,filename)
        Created: 28.04.2005, KP
        Description: Save the rendered screen as png
        """            
        self.saveScreen(vtk.vtkPNGWriter(),filename)
        
    def save_pnm(self,filename):
        """
        Method: save_pnm(self,filename)
        Created: 28.04.2005, KP
        Description: Save the rendered screen as png
        """
        self.saveScreen(vtk.vtkPNMWriter(),filename)
        
    def save_bmp(self,filename):
        """
        Method: save_bmp(self,filename)
        Created: 28.04.2005, KP
        Description: Save the rendered screen as bmp
        """
        self.saveScreen(vtk.vtkBMPWriter(),filename)    

    def save_jpg(self,filename):
        return self.save_jpeg(filename)
        
    
        
    def save_jpeg(self,filename):
        """
        Method: save_jpeg(self,filename)
        Created: 28.04.2005, KP
        Description: Save the rendered screen as jpeg
        """            
        self.saveScreen(vtk.vtkJPEGWriter(),filename)
        
    def save_screen(self,filename):
        """
        Method: save_tiff(self,filename)
        Created: 28.04.2005, KP
        Description: Save the rendered screen as image the format of which
                     is determined by the file extension
        """
        ext=filename.split(".")[-1].lower()
        eval("self.save_%s(filename)"%ext)
        
        
    def save_tif(self,filename):
        return self.save_tiff(filename)
        
    def save_tiff(self,filename):
        """
        Method: save_tiff(self,filename)
        Created: 28.04.2005, KP
        Description: Save the rendered screen as jpeg
        """
        self.saveScreen(vtk.vtkTIFFWriter(),filename)
        
    def saveScreen(self,writer,filename):
        """
        Method: saveScreen(writer,filename)
        Created: 28.04.2005, KP
        Description: Writes the screen to disk
        """

        while self.rendering:
            time.sleep(0.01)
        writer.SetFileName(filename)
        _filter = vtk.vtkWindowToImageFilter()
        _filter.SetInput(self.GetRenderWindow())
        writer.SetInput(_filter.GetOutput())
        writer.Write()

    def getRenderer(self):
        """
        Method: getRenderer
        Created: 28.04.2005, KP
        Description: Return the renderer
        """
        if not self.renderer:
            collection=self.GetRenderWindow().GetRenderers()
            if collection.GetNumberOfItems()==0:
                self.renderer = vtk.vtkRenderer()
                self.GetRenderWindow().AddRenderer(self.renderer)
            else:
                print "Using existing rendererer"
                self.renderer=collection.GetItemAsObject(0)
        return self.renderer

# safeguard
