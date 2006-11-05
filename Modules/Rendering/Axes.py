# -*- coding: iso-8859-1 -*-

"""
 Unit: Axes
 Project: BioImageXD
 Created: 20.06.2005, KP
 Description:

 A module containing axes for visualization
 
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
from Visualizer.VisualizationModules import *


def getClass():return AxesModule
def getConfigPanel():return AxesConfigurationPanel
def getName():return "Axes"

class AxesModule(VisualizationModule):
    """
    Created: 05.06.2005, KP
    Description: A module for showing a scale bar
    """    
    def __init__(self,parent,visualizer,**kws):
        """
        Created: 03.05.2005, KP
        Description: Initialization
        """     
        self.x,self.y,self.z=-1,-1,-1
        VisualizationModule.__init__(self,parent,visualizer,**kws)   
        #self.name = "Axes"
        self.renew = 1
        self.mapper = vtk.vtkPolyDataMapper()
                
        iactor = self.wxrenwin.GetRenderWindow().GetInteractor()

        self.axes = axes = vtk.vtkAxesActor()
        axes.SetShaftTypeToCylinder()
        axes.SetXAxisLabelText("X")
        axes.SetYAxisLabelText("Y")
        axes.SetZAxisLabelText("Z")
        axes.SetTotalLength(1.5, 1.5, 1.5)
        tprop = vtk.vtkTextProperty()
        tprop.ItalicOn()
        tprop.ShadowOn()
        tprop.SetFontFamilyToTimes()
        axes.GetXAxisCaptionActor2D().SetCaptionTextProperty(tprop)
        tprop2=vtk.vtkTextProperty()
        tprop2.ShallowCopy(tprop)
        axes.GetYAxisCaptionActor2D().SetCaptionTextProperty(tprop2)
        tprop3=vtk.vtkTextProperty()
        tprop3.ShallowCopy(tprop)
        axes.GetZAxisCaptionActor2D().SetCaptionTextProperty(tprop3)  
        self.renderer = self.parent.getRenderer()
        self.actor = self.axes
        self.marker = vtk.vtkOrientationMarkerWidget()
        self.marker.SetOutlineColor(0.93,0.57,0.13)
        self.marker.SetOrientationMarker(axes)
        self.marker.SetViewport(0.0, 0.0, 0.15, 0.3)
        
        self.marker.SetInteractor(iactor)
        self.marker.SetEnabled(1)
        self.marker.InteractiveOff()
        
    def setDataUnit(self,dataunit):
        """
        Created: 28.04.2005, KP
        Description: Sets the dataunit this module uses for visualization
        """       
        VisualizationModule.setDataUnit(self,dataunit)
                
 
    
    def showTimepoint(self,value):
        """
        Created: 28.04.2005, KP
        Description: Set the timepoint to be displayed
        """          
        self.updateRendering()
 
        
    def updateRendering(self,e1=None,e2=None):
        """
        Created: 03.05.2005, KP
        Description: Update the Rendering of this module
        """             
        #self.mapper.Update()
        VisualizationModule.updateRendering(self,input)
        self.wxrenwin.Render()    

    def disableRendering(self):
        """
        Created: 15.05.2005, KP
        Description: Disable the Rendering of this module
        """          
        #self.renderer.RemoveActor(self.actor)
        self.marker.Off()
        self.wxrenwin.Render()
        
        
    def enableRendering(self):
        """
        Created: 15.05.2005, KP
        Description: Enable the Rendering of this module
        """          
        #self.renderer.AddActor(self.actor)
        self.marker.On()
        self.wxrenwin.Render()
        
    def setProperties(self, ambient,diffuse,specular,specularpower):
        """
        Created: 5.11.2006, KP
        Description: A dummy method that captures the call for setting the
                     different properties
        """
        pass
        

class AxesConfiguration(ModuleConfiguration):
    def __init__(self,parent,visualizer):
        """
        Created: 04.05.2005, KP
        Description: Initialization
        """     
        ModuleConfiguration.__init__(self,parent,"Axes")
        self.panel=AxesConfigurationPanel(self,visualizer)
        
class AxesConfigurationPanel(ModuleConfigurationPanel):
    def __init__(self,parent,visualizer,name="Axes",**kws):
        """
        Created: 04.05.2005, KP
        Description: Initialization
        """     
        ModuleConfigurationPanel.__init__(self,parent,visualizer,name,**kws)
    
    def initializeGUI(self):
        """
        Created: 28.04.2005, KP
        Description: Initialization
        """  
        pass

    def setModule(self,module):
        """
        Method: setModule(module)
        Created: 28.04.2005, KP
        Description: Set the module to be configured
        """  
        ModuleConfigurationPanel.setModule(self,module)
