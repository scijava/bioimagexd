# -*- coding: iso-8859-1 -*-
"""
 Unit: LightRenderingInterface.py
 Project: BioImageXD
 Created: 28.04.2005,KP
 Description:

 The module used to render selected timepoints in a dataunit. Uses the BioImageXD
 visualization framework

 Modified: 28.04.2005 KP - Derived the class from original rendering interface
           
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
__version__ = "$Revision: 1.28 $"
__date__ = "$Date: 2005/01/13 14:52:39 $"

import vtk
import math
import os.path
import Logging
import Configuration
import wx
import time
import sys

import RenderingInterface

import Visualizer

class LightRenderingInterface(RenderingInterface.RenderingInterface):
    """
    Class: LightRenderingInterface
    Created: 28.04.2005, KP
    Description: The interface between LSM and BioImageXD Visualizer for rendering
    """
    def __init__(self,dataUnit=None,timePoints=[],**kws):
        """
        Method: __init__
        Created: 17.11.2004, KP
        Description: Initialization
        """
        RenderingInterface.RenderingInterface.__init__(self,dataUnit,timePoints,**kws)
        self.visualizer=None
        
    
    def runTk(self):pass
    def runTkinterGUI(self):pass
        
            
    def updateDataset(self):
        """
        Method: updateDataset()
        Created: 28.04.2005, KP
        Description: Updates the dataset to the current timepoint
        """
        if self.visualizer:
            self.visualizer.setTimepoint(self.currentTimePoint)
        
    def setRenderWindowSize(self,size):
        """
        Method: setRenderWindowSize()
        Created: 27.04.2005, KP
        Description: Sets the mayavi render window size
        """        
        x,y=size
        if self.visualizer:
            self.visualizer.setRenderWindowSize((x,y))
            
    def setParent(self,parent):
        """
        Method: setParent(parent)
        Created: 28.04.2005, KP
        Description: Set the parent of this window
        """        
        self.parent=parent
        
    def getRenderWindow(self):
        """
        Method: getRenderWindow()
        Created: 22.02.2005, KP
        Description: Returns the mayavi's render window. Added for Animator compatibility
        """
        return self.visualizer.getCurrentMode().GetRenderWindow()
        
    def render(self):
#        self.visualizer.Raise()
#        self.visualizer.Refresh()
        #self.visualizer.Render()
        self.visualizer.currMode.Render()


    def getRenderer(self):
        """
        Method: getRenderer
        Created: 28.04.2005, KP
        Description: Returns the renderer
        """        
        return self.visualizer.getCurrentMode().GetRenderer()
        
    def setVisualizer(self,visualizer):
        """
        Method: setVisualizer(visualizer)
        Created: 20.06.2005, KP
        Description: Set the visualizer instance to use
        """        
        self.visualizer=visualizer

    def createVisualizerWindow(self):
        """
        Method: createVisualizerWindow()
        Created: 22.02.2005, KP
        Description: A method that creates an instance of mayavi
        """    
        raise "createVisualizerWindow"
        vis=Visualizer.VisualizationFrame(self.parent)
        if not self.dataUnit:
            raise "No dataunit given but attempt to create Visualizer window"
        vis.setDataUnit(self.dataUnit)
        self.visualizer=vis
        vis.Show()

    def isVisualizationSoftwareRunning(self):
        """
        Method: isVisualizationSoftwareRunning()
        Created: 11.1.2005, KP
        Description: A method that returns true if a mayavi window exists that
                     can be used for rendering
        """
        # Attempt to get a running instance of visualizer
        #if not self.visualizer:
        #   self.visualizer=Visualizer.getVisualizer()
        #   self.visualizer.setDataUnit(self.dataUnit)
        #   if self.visualizer:
        #       Logging.info("Visualizer is running",kw="visualizer")
        return (self.visualizer and not self.visualizer.isClosed())


    def isVisualizationModuleLoaded(self):
        """
        Method: isVisualizationModuleLoaded()
        Created: 22.02.2005, KP
        Description: A method that returns true if a visualizer has a visualization module loaded.
        """
        return len(self.visualizer.getCurrentMode().getModules())

        
    def doRendering(self,**kws):
        """
        Method: doRendering()
        Created: 17.11.2004, KP
        Description: Sends each timepoint one at a time to be rendered in mayavi
        Parameters:
            preview     If this flag is true, the results are not rendered out
        """
        if kws.has_key("preview"):
            self.showPreview=kws["preview"]
        if kws.has_key("ctf"):
            self.ctf=kws["ctf"]

        if not self.showPreview:
            raise "Cannot handle non-previews"

        if not self.dataUnit or not self.timePoints:
            raise "No dataunit or timepoints defined"

        # If there is no visualizer instance to do the rendering
        # create one
        if not self.isVisualizationSoftwareRunning():
            Logging.info("Creating visualizer",kw="visualizer")
            self.createVisualizerWindow()
        self.visualizer.setTimepoint(self.currentTimePoint)

    def saveFrame(self,filename):
        """
        Method: saveFrame(filename)
        Created: 22.02.2005, KP
        Description: Saves a frame with a given name
        """
        visualizer=self.visualizer
        type=self.type
        Logging.info("Saving screenshot to ",filename,kw="visualizer")
        comm = "visualizer.getCurrentMode().saveSnapshot(filename)"
        eval(comm)
