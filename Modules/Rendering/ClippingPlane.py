# -*- coding: iso-8859-1 -*-

"""
 Unit: ClippingPlane
 Project: BioImageXD
 Created: 24.06.2005, KP
 Description:

 A module containing a clipping plane module
           
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

import vtk
import ColorTransferEditor
import Dialogs

from Visualizer.VisualizationModules import *

def getClass():return ClippingPlaneModule
def getConfigPanel():return ClippingPlaneConfigurationPanel
def getName():return "Clipping Plane"


class ClippingPlaneModule(VisualizationModule):
    """
    Class: ClippingPlaneModule
    Created: 24.06.2005, KP
    Description: A module for clipping the dataset
    """    
    def __init__(self,parent,visualizer,**kws):
        """
        Method: __init__(parent)
        Created: 03.05.2005, KP
        Description: Initialization
        """     
        self.x,self.y,self.z=-1,-1,-1
        VisualizationModule.__init__(self,parent,visualizer,**kws)   
        #self.name = "Clipping Plane"
        self.on = 0
        self.renew = 1
        self.currentPlane=None
        self.clipped = 0
        self.planeWidget = vtk.vtkPlaneWidget()
        self.planeWidget.AddObserver("InteractionEvent",self.clipVolumeRendering)
        self.planeWidget.SetResolution(20)
        self.planeWidget.SetRepresentationToOutline()
        self.planeWidget.NormalToXAxisOn()
        self.renderer = self.parent.getRenderer()
        self.plane=vtk.vtkPlane()
        iactor = self.wxrenwin.GetRenderWindow().GetInteractor()
        self.planeWidget.SetInteractor(iactor)
        print "adding actor"
        #self.updateRendering()
        
    def __getstate__(self):
        """
        Method: __getstate__
        Created: 02.08.2005, KP
        Description: A getstate method that saves the lights
        """            
        odict=VisualizationModule.__getstate__(self)
        odict.update({"planeWidget":self.getVTKState(self.planeWidget)})
        odict.update({"currentPlane":self.getVTKState(self.currentPlane)})
        odict.update({"renderer":self.getVTKState(self.renderer)})
        odict.update({"camera":self.getVTKState(self.renderer.GetActiveCamera())})
        odict.update({"clipped":self.clipped})
        return odict
        
    def __set_pure_state__(self,state):
        """
        Method: __set_pure_state__()
        Created: 02.08.2005, KP
        Description: Set the state of the light
        """        
        self.setVTKState(self.planeWidget,state.planeWidget)
        self.setVTKState(self.currentPlane,state.currentPlane)
        self.setVTKState(self.renderer,state.renderer)
        self.setVTKState(self.renderer.GetActiveCamera(),state.camera)

        self.clipped = state.clipped
        if self.clipped:
            self.clipVolumeRendering(self.planeWidget,None)
        VisualizationModule.__set_pure_state__(self,state)
                
        
    def removeClippingPlane(self,plane):
        """
        Method: removeClippingPlane(plane)
        Created: 24.06.2005, KP
        Description: Remove a clipping plane
        """       
        for module in self.parent.getModules():
            if hasattr(module,"mapper") and hasattr(module.mapper,"SetClippingPlanes"):
                module.mapper.RemoveClippingPlane(plane)
                self.clipped = 0
        
    def clipVolumeRendering(self,object,event):
        """
        Method: clipVolumeRendering(object,event)
        Created: 24.06.2005, KP
        Description: Called when the plane is interacted with
        """       
        if self.currentPlane:
            self.removeClippingPlane(self.currentPlane)
            self.currentPlane=None
        object.GetPlane(self.plane)
        for module in self.parent.getModules():
            if hasattr(module,"mapper") and hasattr(module.mapper,"SetClippingPlanes"):
                module.mapper.AddClippingPlane(self.plane)
                self.currentPlane=self.plane
                self.clipped = 1
        
    def setDataUnit(self,dataunit):
        """
        Method: setDataUnit(self)
        Created: 28.04.2005, KP
        Description: Sets the dataunit this module uses for visualization
        """       
        VisualizationModule.setDataUnit(self,dataunit)
        print "got dataunit",dataunit
        if self.visualizer.getProcessedMode():
            data=self.dataUnit.getSourceDataUnits()[0].getTimePoint(0)
        else:
            data=self.dataUnit.getTimePoint(0)
        self.origin = data.GetOrigin()
        self.spacing = data.GetSpacing()
        self.extent = data.GetWholeExtent()
        
        y=self.extent[3]
        x=self.extent[1]
        
        self.planeWidget.SetInput(data)
        self.planeWidget.SetOrigin(-32,-32,-32)
        self.planeWidget.SetPoint1(0,y+32,0)
        self.planeWidget.SetPoint2(x+32,0,0)
        self.planeWidget.PlaceWidget()

    def showTimepoint(self,value):
        """
        Method: showTimepoint(tp)
        Created: 28.04.2005, KP
        Description: Set the timepoint to be displayed
        """          
        self.renew=1
        VisualizationModule.showTimepoint(self,value)

        
    def updateRendering(self):
        """
        Method: updateRendering()
        Created: 03.05.2005, KP
        Description: Update the Rendering of this module
        """             
        #self.outline.SetInput(self.data)
        #self.outlineMapper.SetInput(self.outline.GetOutput())
        
        #self.outlineMapper.Update()

        if self.renew:

            self.planeWidget.SetInput(self.data)
            self.renew=0
        
        if not self.on:
            self.planeWidget.On()
            self.on = 1
        
        #self.mapper.Update()
        VisualizationModule.updateRendering(self,input)
        self.parent.Render()    

    def disableRendering(self):
        """
        Method: disableRendering()
        Created: 15.05.2005, KP
        Description: Disable the Rendering of this module
        """          
        if self.currentPlane:
            self.removeClippingPlane(self.currentPlane)        
        self.planeWidget.Off()
        self.wxrenwin.Render()
        
    def showPlane(self,flag):
        """
        Method: showPlane
        Created: 24.06.2005, KP
        Description: Show / hide the plane controls
        """          
        if flag:
            self.planeWidget.On()
        else:
            self.planeWidget.Off()
        
        
    def enableRendering(self):
        """
        Method: enableRendering()
        Created: 24.06.2005, KP
        Description: Enable the Rendering of this module
        """          
        self.planeWidget.On()
        self.wxrenwin.Render()
        
    def setProperties(self,ambient,diffuse,specular,specularpower):
        """
        Method: setProperties(ambient,diffuse,specular,specularpower)
        Created: 16.05.2005, KP
        Description: Set the ambient, diffuse and specular lighting of this module
        """         
        pass
    def setShading(self,shading):
        """
        Method: setShading(shading)
        Created: 16.05.2005, KP
        Description: Set shading on / off
        """          
        pass


class ClippingPlaneConfiguration(ModuleConfiguration):
    def __init__(self,parent,visualizer):
        """
        Method: __init__(parent)
        Created: 04.05.2005, KP
        Description: Initialization
        """     
        ModuleConfiguration.__init__(self,parent,"Clipping Plane")
        self.panel=ClippingPlaneConfigurationPanel(self,visualizer)

class ClippingPlaneConfigurationPanel(ModuleConfigurationPanel):
    def __init__(self,parent,visualizer,name="Clipping Plane",**kws):
        """
        Method: __init__(parent)
        Created: 04.05.2005, KP
        Description: Initialization
        """     
        ModuleConfigurationPanel.__init__(self,parent,visualizer,name,**kws)
    
    def initializeGUI(self):
        """
        Method: initializeGUI()
        Created: 28.04.2005, KP
        Description: Initialization
        """  
        self.visibleBox=wx.CheckBox(self,-1,"Show plane controls")
        self.contentSizer.Add(self.visibleBox,(0,0))
        
    def setModule(self,module):
        """
        Method: setModule(module)
        Created: 28.04.2005, KP
        Description: Set the module to be configured
        """  
        ModuleConfigurationPanel.setModule(self,module)
        print "module=",module
        self.module=module
        
    def onApply(self,event):
        """
        Method: onApply()
        Created: 28.04.2005, KP
        Description: Apply the changes
        """     
        visible=self.visibleBox.GetValue()
        self.module.showPlane(visible)
