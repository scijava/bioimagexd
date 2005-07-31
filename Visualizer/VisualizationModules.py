# -*- coding: iso-8859-1 -*-

"""
 Unit: VisualizationModules
 Project: BioImageXD
 Created: 28.04.2005, KP
 Description:

 A module containing the various Rendering modules for the visualization
          
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
from ModuleConfiguration import *
import Dialogs
import Logging
import Modules
#from enthought.tvtk import messenger
import messenger
import glob
import os,sys

class VisualizationModule:
    """
    Class: VisualizationModule
    Created: 28.04.2005, KP
    Description: A class representing a visualization module
    """
    def __init__(self,parent,visualizer,**kws):
        """
        Method: __init__(parent)
        Created: 28.04.2005, KP
        Description: Initialization
        """    
        #self.name="Module"
        self.name=kws["label"]
        self.timepoint = -1
        self.parent = parent
        self.visualizer=visualizer
        self.wxrenwin = parent.wxrenwin
        self.renWin = self.wxrenwin.GetRenderWindow()    
        self.renderer = self.parent.getRenderer()
        self.eventDesc="Rendering"
    
    def updateProgress(self,obj,event):
        """
        Method: updateProgress(object,event)
        Created: 13.07.2005, KP
        Description: Update the progress information
        """            
        progress=obj.GetProgress()
        txt=obj.GetProgressText()
        if not txt:txt=self.eventDesc
        messenger.send(None,"update_progress",progress,txt)        
    
    def getName(self):
        """
        Method: getName()
        Created: 28.04.2005, KP
        Description: Return the name of this module
        """            
        return self.name
        
    def setDataUnit(self,dataunit):
        """
        Method: setDataUnit(self)
        Created: 28.04.2005, KP
        Description: Sets the dataunit this module uses for visualization
        """            
        self.dataUnit = dataunit
        
    def getDataUnit(self):
        """
        Method: getDataUnit()
        Created: 28.04.2005, KP
        Description: Returns the dataunit this module uses for visualization
        """     
        return self.dataUnit

    def updateData(self):
        """
        Method: updateData()
        Created: 26.05.2005, KP
        Description:"OK Update the data that is displayed
        """          
        self.showTimepoint(self.timepoint)

    def showTimepoint(self,value):
        """
        Method: showTimepoint(tp)
        Created: 28.04.2005, KP
        Description: Set the timepoint to be displayed
        """          
        self.timepoint = value
        
        if self.visualizer.getProcessedMode():
            Logging.info("Will render processed data instead",kw="visualizer")
            self.data = self.dataUnit.doPreview(-1,1,self.timepoint)
        else:
            Logging.info("Using timepoint data for tp",value,kw="visualizer")
            self.data = self.dataUnit.getTimePoint(value)

        self.updateRendering()
        
    def disableRendering(self):
        """
        Method: disableRendering()
        Created: 30.04.2005, KP
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
        
    def setProperties(self, ambient,diffuse,specular,specularpower):
        """
        Method: setProperties(ambient,diffuse,specular,specularpower)
        Created: 16.05.2005, KP
        Description: Set the ambient, diffuse and specular lighting of this module
        """          
        property=self.actor.GetProperty()
        property.SetAmbient(ambient)
        property.SetDiffuse(diffuse)
        property.SetSpecular(specular)
        property.SetSpecularPower(specularpower)
        
    def setShading(self,shading):
        """
        Method: setShading(shading)
        Created: 16.05.2005, KP
        Description: Set shading on / off
        """          
        property=self.actor.GetProperty()
        if shading:
            property.ShadeOn()
        else:
            property.ShadeOff()
    

