# -*- coding: iso-8859-1 -*-

"""
 Unit: VisualizerWindow
 Project: BioImageXD
 Created: 15.05.2005, KP
 Description:

 A framework for replacing MayaVi for simple rendering tasks.
 
 Modified 15.05.2005 KP - Split the VisualizerWindow to a module of it's own
          
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
__author__ = "BioImageXD Project"
__version__ = "$Revision: 1.9 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import wx
import time

import vtk
from vtk.wx.wxVTKRenderWindowInteractor import wxVTKRenderWindowInteractor
from Events import *
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


    def initializeVTK(self):
        """
        Method: initializeVTK
        Created: 29.04.2005, KP
        Description: initialize the vtk renderer
        """
        self.iren = iren = self.GetRenderWindow().GetInteractor()
        self.iren.SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())
        self.getRenderer()
        self.renderer.SetBackground(0,0,0.3)
        self.iren.SetSize(self.GetRenderWindow().GetSize())
        self.renderer.AddObserver("StartEvent",self.onRenderBegin)
        self.renderer.AddObserver("EndEvent",self.onRenderEnd)


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

    def save_jpeg(self,filename):
        """
        Method: save_jpeg(self,filename)
        Created: 28.04.2005, KP
        Description: Save the rendered screen as jpeg
        """            
        self.saveScreen(vtk.vtkJPEGWriter(),filename)
        
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
                print "Adding renderer"
                self.renderer = vtk.vtkRenderer()
                self.GetRenderWindow().AddRenderer(self.renderer)
            else:
                print "Using existing rendererer"
                self.renderer=collection.GetItemAsObject(0)
        return self.renderer
    
