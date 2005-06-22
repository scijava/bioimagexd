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
from Visualization.VisualizationModules import *


def getClass():return AxesModule
def getConfig():return AxesConfigurationPanel
def getName():return "Axes"

class AxesModule(VisualizationModule):
    """
    Class: ScaleBarModule
    Created: 05.06.2005, KP
    Description: A module for showing a scale bar
    """    
    def __init__(self,parent,visualizer):
        """
        Method: __init__(parent)
        Created: 03.05.2005, KP
        Description: Initialization
        """     
        self.x,self.y,self.z=-1,-1,-1
        VisualizationModule.__init__(self,parent,visualizer)   
        self.name = "Axes"
        self.renew = 1
        self.mapper = vtk.vtkPolyDataMapper()
        
        self.axes = vtk.vtkAxes()
        self.axesTubes = vtk.vtkTubeFilter()
        self.axesTubes.SetNumberOfSides(6)
        
        self.mapper.SetInput(self.axesTubes.GetOutput())
                
        self.actor = vtk.vtkActor()
        self.actor.SetMapper(self.mapper)
        
        self.renderer = self.parent.getRenderer()
        
        
        self.renderer.AddActor(self.actor)
        
    def setDataUnit(self,dataunit):
        """
        Method: setDataUnit(self)
        Created: 28.04.2005, KP
        Description: Sets the dataunit this module uses for visualization
        """       
        VisualizationModule.setDataUnit(self,dataunit)
        
        
        if self.visualizer.getProcessedMode():
            data=dataunit.getSourceDataUnits()[0].getTimePoint(0)
        else:
            data=dataunit.getTimePoint(0)  
        self.axes.SetOrigin(data.GetOrigin())
        self.axes.SetScaleFactor(data.GetDimensions()[0]/5.0)
        self.axesTubes.SetInput(self.axes.GetOutput())
        self.axesTubes.SetRadius(self.axes.GetScaleFactor()/25.0)
    
    def showTimepoint(self,value):
        """
        Method: showTimepoint(tp)
        Created: 28.04.2005, KP
        Description: Set the timepoint to be displayed
        """          
        pass
        
    def updateRendering(self,e1=None,e2=None):
        """
        Method: updateRendering()
        Created: 03.05.2005, KP
        Description: Update the Rendering of this module
        """             
        self.mapper.Update()
        self.wxrenwin.Render()    

    def disableRendering(self):
        """
        Method: disableRendering()
        Created: 15.05.2005, KP
        Description: Disable the Rendering of this module
        """          
        self.renderer.RemoveActor(self.actor)
        self.wxrenwin.Render()
        
        
    def enableRendering(self):
        """
        Method: enableRendering()
        Created: 15.05.2005, KP
        Description: Enable the Rendering of this module
        """          
        self.renderer.AddActor(self.actor)
        self.wxrenwin.Render()
        

class AxesConfiguration(ModuleConfiguration):
    def __init__(self,parent,visualizer):
        """
        Method: __init__(parent)
        Created: 04.05.2005, KP
        Description: Initialization
        """     
        ModuleConfiguration.__init__(self,parent,"Axes")
        self.panel=AxesConfigurationPanel(self,visualizer)
        
class AxesConfigurationPanel(ModuleConfigurationPanel):
    def __init__(self,parent,visualizer,**kws):
        """Scale bar
        Method: __init__(parent)
        Created: 04.05.2005, KP
        Description: Initialization
        """     
        ModuleConfigurationPanel.__init__(self,parent,visualizer,"Axes",**kws)
    
    def initializeGUI(self):
        """
        Method: initializeGUI()
        Created: 28.04.2005, KP
        Description: Initialization
        """  
#        self.addButton=wx.Button(self,-1,"Add plane")
#        self.addButton.Bind(wx.EVT_BUTTON,self.onAddPlane)
#        self.contentSizer.Add(self.addButton,(0,0),flag=wx.EXPAND|wx.LEFT|wx.RIGHT)
        
        

    def setModule(self,module):
        """
        Method: setModule(module)
        Created: 28.04.2005, KP
        Description: Set the module to be configured
        """  
        ModuleConfigurationPanel.setModule(self,module)
