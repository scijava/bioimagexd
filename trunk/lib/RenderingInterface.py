# -*- coding: iso-8859-1 -*-
"""
 Unit: RenderingInterface.py
 Project: BioImageXD
 Created: 17.11.2004, KP
 Description:

           
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
__version__ = "$Revision: 1.21 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import vtk
import math
import os.path
import Logging
import Configuration
import wx
import time
import sys


rendint=None


def getRenderingInterface(mayavi=0):
    global rendint
    if not rendint:
        rendint=RenderingInterface()
    return rendint

class RenderingInterface:
    """
    Created: 17.11.2004, KP
    Description: The interface to visualizer used for animator rendering
    """
    def __init__(self,dataUnit=None,timePoints=[],**kws):
        """
        Created: 17.11.2004, KP
        Description: Initialization
        """
        self.dataUnit=dataUnit
        self.currentData=None
        self.timePoints=timePoints
        
        self.settings_mode=0
        self.frameName=""
        self.thread = None
        self.stop=0
        self.currentTimePoint=-1
        # XXX: Make this configurable
        self.type=Configuration.getConfiguration().getConfigItem("ImageFormat","Output")
        
        if not self.type:
            self.type="pnm"
            
        self.visualizer = None
        self.frameList = []
        
    def setType(self,type):
        """
        Created: 13.12.2005, KP
        Description: Set the type of the rendered frame
        """            
        self.type = type
        
    def getColorTransferFunction(self):
        """
        Created: 18.04.2005, KP
        Description: Return the current ctf
        """
        return self.ctf

        
    def getCurrentData(self):
        """
        Created: n/a
        Description: Return the current timepoint
        """
    
        if not self.currentData:
            n=self.currentTimePoint
            if n<0:n=0
            self.setCurrentTimepoint(n)
        return self.currentData
        
    def setCurrentTimepoint(self,n):
        """
        Created: 22.02.2005, KP
        Description: Sets the current timepoint to be the specified timepoint.
                     This will also update relevant information about the dataset
        """        
        self.currentTimePoint = n
        if self.dataUnit.isProcessed():
            self.currentData = self.dataUnit.doPreview(-1,0,n)
        else:
            self.currentData = self.dataUnit.getTimePoint(n)
        self.dimensions = self.currentData.GetDimensions()
        
    def setRenderWindowSize(self,size):
        """
        Created: 27.04.2005, KP
        Description: Sets the mayavi render window size
        """        
        x,y=size
        if self.visualizer:
            self.visualizer.setRenderWindowSize((x,y))
            
    def getRenderWindow(self):
        """
        Created: 22.02.2005, KP
        Description: Returns the mayavi's render window. Added for Animator compatibility
        """
        return self.visualizer.getCurrentMode().GetRenderWindow()
    
    def setParent(self,parent):
        """
        Created: 28.04.2005, KP
        Description: Set the parent of this window
        """        
        self.parent=parent
        
    def getRenderer(self):
        """
        Created: 28.04.2005, KP
        Description: Returns the renderer
        """        
        return self.visualizer.getCurrentMode().GetRenderer()
        
    def render(self):
        self.visualizer.currMode.Render()
    
    def setVisualizer(self,visualizer):
        """
        Created: 20.06.2005, KP
        Description: Set the visualizer instance to use
        """        
        self.visualizer=visualizer
        self.frameList = []
        
    def setDataUnit(self,dataUnit):
        """
        Created: 17.11.2004, KP
        Description: Set the dataunit from which the rendered datasets are read
        """
        self.dataUnit=dataUnit
        # Calculate how many digits there will be in the rendered output
        # file names, with a running counter
        ndigits=1+int(math.log(self.dataUnit.getLength(),10))
        # Format, the format will be /path/to/data/image_001.png        
        self.format="%%s%s%%s_%%.%dd.%s"%(os.path.sep,ndigits,self.type)
        #Logging.info("File name format=",self.format)
        self.ctf=dataUnit.getColorTransferFunction()
        #self.ctf = dataUnit.getSettings().get("ColorTransferFunction")
        self.frameName=self.dataUnit.getName()

    def setTimePoints(self,timepoints):
        """
        Created: 17.11.2004, KP
        Description: Set the list of timepoints to be rendered
        """
        self.timePoints=timepoints

    def createVisualization(self,filename):
        """
        Created: 14.12.2004, KP
        Description: Method for starting Mayavi with a datapoint for the
                     purpose of creating a .mv file to use in rendering.
        """
        self.stop=0
        self.runTk()#interGUI()
        data=self.dataUnit.getTimePoint(0)
        self.settings_mode=1
        self.doRendering(preview=data)
        self.mayavi.master.wait_window()
        self.mayavi.mayavi.save_visualization(filename)
        Logging.info("createVisualization setting mayavi to None")
        self.mayavi=None
        self.not_loaded=1
        self.settings_mode=0
        self.stop=1

    def isVisualizationSoftwareRunning(self):
        """
        Created: 11.1.2005, KP
        Description: A method that returns true if a mayavi window exists that 
                     can be used for rendering
        """
        return (self.visualizer and not self.visualizer.isClosed())
        
    def isVisualizationModuleLoaded(self):
        """
        Created: 22.02.2005, KP
        Description: A method that returns true if the visualizer has a visualization module loaded.
        """
        return len(self.visualizer.getCurrentMode().getModules())        
        
    def doRendering(self,**kws):
        """
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
        
    def getFrameList(self):
        """
        Created: 07.11.2006, KP
        Description: Return the list of the names of the frames that have been rendered
        """
        return self.frameList
        
    def setOutputPath(self,path):
        """
        Created: 17.11.2004, KP
        Description: Sets the path where the rendered frames are stored.
        """
        self.dirname=path
 
    def renderData(self,data,n):
        """
        Created: 17.11.2004, KP
        Description: Sends the specified timepoint to Mayavi to be rendered.
        Parameters:
                data               The dataset to be rendered
                n                  The timepoint
        """
#        self.mayavi.close_all()
 
        if not self.visualizationFile and self.not_loaded:
            Logging.info("Loading data: self.mayavi.open_vtk_data(...)")
            # If this is the first run and there is no visualization file
            # Load the data
            #print "Loading ",data
            self.mayavi.open_vtk_data(data)
            Logging.info("done")
            # Set the first-run flag to 0
            self.not_loaded=0

            # If we were told to use the existing window, then we will not load 
            # any modules since they're already loaded
            if not self.use_existing:
                Logging.info("Loading mayavi module ",self.module)
                # Load volume module necesary for rendering
                module=self.mayavi.load_module(self.module,0)
                # And if a color transfer function has been specified, use that.
                if self.ctf:
                    Logging.info("Setting ctf",self.ctf)
                    prop=module.actor.GetProperty()
                    prop.SetColor(self.ctf)
                    module.legend.update_lut(prop)
                elif self.surfcolor:
                    prop=module.actor.GetProperty()
                    Logging.info("Setting color",self.surfcolor)
                    prop.SetColor(self.surfcolor)
        elif self.visualizationFile and self.not_loaded:
            Logging.info("Loading visualization ",self.visualizationFile)
            # If this is the first run, but use a visualization file
            self.mayavi.load_visualization(self.visualizationFile)
            self.not_loaded=0

        # substitute just the data
        self.setDataSet(data)


        if not self.isVisualizationSoftwareRunning():
            if self.settings_mode:
                Logging.error("Failed to create settings file",
                "The settings file could not be written, because "
                "MayaVi appears to\n"
                "have been shut down before the settings file could be written.")
            Logging.error("Failed to render all datasets",
            "All selected timepoints have not been rendered, "
            "because Mayavi appears to\n"
            "have been shut down before the rendering was finished.")
            return
        self.mayavi.root.lift()
        #self.mayavi.root.focus_force()
        self.mayavi.root.update()

        # Don't need to call Render since lift will already do it
        #self.mayavi.Render()

        if self.isVisualizationSoftwareRunning():
            #self.mayavi.root.update()
            #self.mayavi.root.lift()
            self.mayavi.root.focus_force()

        if not self.showPreview:
            filename=self.getFilename(n)
            print "Rendering timepoint %d with filename %s"%(n,filename)
            self.saveFrame(filename)
        print "done!"
            
    def saveFrame(self,filename):
        """
        Created: 22.02.2005, KP
        Description: Saves a frame with a given name
        """
        self.frameList.append(filename)
        visualizer=self.visualizer
        type=self.type
        Logging.info("Saving screenshot to ",filename,kw="visualizer")
        comm = "visualizer.getCurrentMode().saveSnapshot(filename)"
        eval(comm)
            
    def getFilenamePattern(self):
        """
        Created: 27.04.2005, KP
        Description: Returns output filename pattern
        """
        return self.format
        
    def getFrameName(self):
        """
        Created: 27.04.2005, KP
        Description: Returns name used to construct the filenames
        """
        return self.frameName
            
    def getFilename(self,frameNum):
        """
        Created: 22.02.2005, KP
        Description: Returns output filename of the frame we're rendering
        """
        return self.format%(self.dirname,self.frameName,frameNum)

    def getCenter(self,tp=-1):
        """
        Created: 22.02.2005, KP
        Description: Returns the center of the requested dataset. If none is specified, the
                     center of the current dataset is returned
        """
        if self.currentTimePoint<0 or not self.timePoints or tp>max(self.timePoints):
            return (0,0,0)
        if tp<0:
            return self.currentData.GetCenter()
        else:
            return self.dataUnit.getTimePoint(tp).GetCenter()
        
    def getDimensions(self,tp=-1):
        """
        Created: 22.02.2005, KP
        Description: Returns the dimensions of the requested dataset. If none is specified, the
                     dimensions of the current dataset is returned
        """    
        if self.currentTimePoint<0 or not self.timePoints or tp>max(self.timePoints):
            return (0,0,0)
        if tp<0:
            return self.dimensions
        else:
            return self.dataUnit.getTimePoint(tp).GetDimensions()
            
            
    def updateDataset(self):
        """
        Created: 28.04.2005, KP
        Description: Updates the dataset to the current timepoint
        """
        if self.visualizer:
            self.visualizer.setTimepoint(self.currentTimePoint)
            
            
