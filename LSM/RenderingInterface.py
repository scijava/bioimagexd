# -*- coding: iso-8859-1 -*-
"""
 Unit: RenderingInterface.py
 Project: Selli
 Created: 17.11.2004
 Creator: KP
 Description:

 The module used to render selected timepoints in a dataunit. Works as an 
 interface between LSM and MayaVi

 Modified: 17.11.2004 KP - Created the class.
           13.12.2004 KP - Added code for previewing
           22.02.2005 KP - Added methods necessary to be compatible with Heikki's animator
           22.02.2005 KP - Introduced concept of current dataset
           
 Selli includes the following persons:
 JH - Juha Hyytiäinen, juhyytia@st.jyu.fi
 JM - Jaakko Mäntymaa, jahemant@cc.jyu.fi
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 JV - Jukka Varsaluoma, varsa@st.jyu.fi

 Copyright (c) 2004 Selli Project
"""

__author__ = "Selli Project <http://sovellusprojektit.it.jyu.fi/selli/>"
__version__ = "$Revision: 1.21 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import vtk
import mayavi
import math
import os.path
import Logging

import wx

rendint=None

def getRenderingInterface():
    global rendint
    if not rendint:
        rendint=RenderingInterface()
    return rendint

class RenderingInterface:
    """
    Class: RenderingInterface
    Created: 17.11.2004, KP
    Description: The interface between LSM and MayaVi for rendering
    """
    def __init__(self,dataUnit=None,timePoints=[],**kws):
        """
        Method: __init__
        Created: 17.11.2004, KP
        Description: Initialization
        """
        self.dataUnit=dataUnit
        self.currentData=None
        self.timePoints=timePoints
        Logging.info("Init setting mayavi to None")
        self.mayavi=None
        self.visualizationFile=None
        self.surfcolor=None
        self.settings_mode=0
        self.stop=0
        self.currentTimePoint=-1
        # XXX: Make this configurable
        self.type="png"
        
    def getCurrentData(self):
        if not self.currentData:
            n=self.currentTimePoint
            if n<0:n=0
            self.setCurrentTimepoint(n)
        return self.currentData
        
    def setCurrentTimepoint(self,n):
        """
        Method: setCurrentTimepoint(n)
        Created: 22.02.2005, KP
        Description: Sets the current timepoint to be the specified timepoint.
                     This will also update relevant information about the dataset
        """        
        self.currentTimePoint = n
        self.currentData = self.dataUnit.getTimePoint(n)
        self.dimensions = self.currentData.GetDimensions()
        
    def getRenderWindow(self):
        """
        Method: getRenderWindow()
        Created: 22.02.2005, KP
        Description: Returns the mayavi's render window. Added for Animator compatibility
        """        
        return self.mayavi.get_render_window()
        
    def render(self):
        return self.mayavi.Render()
        
    def runTkinterGUI(self,run=1):
        """
        Method: runTkinterGUI()
        Created: 15.01.2005, KP
        Description: Executes a Tkinter event loop using wxWidget's wxFutureCall()
                     that run every 100 ms. Will cease to execute when the flag
                     self.stop is set
        """ 
        if self.mayavi:
            self.mayavi.root.update()
        if not self.stop:
            wx.FutureCall(100, self.runTkinterGUI)


    def setDataUnit(self,dataUnit):
        """
        Method: setDataUnit(dataUnit)
        Created: 17.11.2004, KP
        Description: Set the dataunit from which the rendered datasets are read
        """
        self.dataUnit=dataUnit
        # Calculate how many digits there will be in the rendered output
        # file names, with a running counter
        ndigits=1+int(math.log(self.dataUnit.getLength(),10))
        # Format, the format will be /path/to/data/image_001.png
        self.format="%%s%s%%s_%%.%dd.png"%(os.path.sep,ndigits)
        Logging.info("File name format=",self.format)

    def setTimePoints(self,timepoints):
        """
        Method: setTimePoints(timepoints)
        Created: 17.11.2004, KP
        Description: Set the list of timepoints to be rendered
        """
        self.timePoints=timepoints

    def createVisualization(self,filename):
        """
        Method: createVisualization()
        Created: 14.12.2004, KP
        Description: Method for starting Mayavi with a datapoint for the
                     purpose of creating a .mv file to use in rendering.
        """
        self.stop=0
        self.runTkinterGUI()
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

    def isMayaviRunning(self):
        """
        Method: isMayaviRunning()
        Created: 11.1.2005, KP
        Description: A method that returns true if a mayavi window exists that 
                     can be used for rendering
        """
        Logging.info("Is mayavi running: self.mayavi=",self.mayavi)
        if self.mayavi:
            Logging.info("self.mayavi.root_winfo_exists()=",\
                self.mayavi.root.winfo_exists())
        return (self.mayavi and self.mayavi.root.winfo_exists())

    def getModuleManager(self):
        """
        Method: getModuleManager()
        Created: 22.02.2005, KP
        Description: A method that returns a current module manager in MayaVi.
                     If more than one module manager exists, it will return the
                     "last" one.
        """
        dvms = self.mayavi.get_dvm_names()
        if not self.mm:
            # Get the last module manager
            for i in dvms:
                mm = i.get_current_module_mgr()
                if self.mm and self.mm != mm:
                    Logging.warning("Discarding module manager",self.mm)
                self.mm=mm
        return self.mm

        
    def isMayaViModuleLoaded(self):
        """
        Method: isMayaviModuleLoaded()
        Created: 22.02.2005, KP
        Description: A method that returns true if a mayavi has a visualization module loaded.
        """
        mm=self.getModuleManager()
        if not mm.get_module(0):
            return 0
        return 1
        
    def createMayaVi(self):
        """
        Method: createMayaVi()
        Created: 22.02.2005, KP
        Description: A method that creates an instance of mayavi
        """    
        Logging.info("Creating new mayavi instance")
        del self.mayavi
        self.mayavi=mayavi.mayavi()
        # set flag indicating this is the first run
        self.not_loaded=1

        
    def doRendering(self,**kws):
        """
        Method: doRendering()
        Created: 17.11.2004, KP
        Description: Sends each timepoint one at a time to be rendered in mayavi
        Parameters:
            preview     If this flag is true, the results are not rendered out
        """
        self.showPreview=None
        self.stop=0
        self.runTkinterGUI()

        self.visualizationFile=None
        self.ctf=None
        self.showControlPanel=0
        self.use_existing=0
        if kws.has_key("use_existing"):
            self.use_existing=kws["use_existing"]
        self.module="Volume"
        if kws.has_key("module"):
            self.module=kws["module"]
        if kws.has_key("preview"):
            self.showControlPanel=1
            self.showPreview=kws["preview"]
        if kws.has_key("ctrl_panel"):
            self.showControlPanel=kws["ctrl_panel"]
        if kws.has_key("visualization"):
            self.visualizationFile=kws["visualization"]
        if kws.has_key("surface_color"):
            self.surfcolor=kws["surface_color"]
        if kws.has_key("ctf"):
            self.ctf=kws["ctf"]

        if not self.dataUnit or not self.timePoints:
            raise "No dataunit or timepoints defined"

        # If there is no mayavi instance to do the rendering
        # create one
        if self.isMayaviRunning() == False:
            self.createMayaVi()
            
        Logging.info("Mayavi exists:",self.mayavi.root.winfo_exists(), "it's state:",self.mayvia.root.state())

        # If this is not preview, we disable the control panel
        if not self.showControlPanel:
            self.mayavi.show_ctrl_panel(0)

        self.frameName=self.dataUnit.getName()

        # If this is not preview
        if not self.showPreview:
            # Render every selected timepoint
            for timepoint in self.timePoints:
                # Set the current dataset to be timepoint 
                self.setCurrentTimepoint(timepoint)
                self.renderData(self.currentData,timepoint)

        else:
            Logging.info("Previewing data")
            self.renderData(self.showPreview,0)
        self.stop=1

    def setOutputPath(self,path):
        """
        Method: setOutputPath(path)
        Created: 17.11.2004, KP
        Description: Sets the path where the rendered frames are stored.
        """
        self.dirname=path
 
    def renderData(self,data,n):
        """
        Method: renderData(data)
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
        Logging.info("lifting the window")

        self.mayavi.root.lift()
        self.mayavi.root.focus_force()
        self.mayavi.root.update()

        if not self.isMayaviRunning():
            if self.settings_mode:
                Logging.error("Failed to create settings file",
                "The settings file could not be written, because "
                "MayaVi appears to\n"
                "have been shut down before the settings file could be written.")
            Logging.error("Failed to render all datasets",
            "All selected timepoints have not been rendered, "
            "because Mayavi appears to\n"
            "have been shut down before the rendering was finished.")

        self.mayavi.Render()

        if self.isMayaviRunning():
            self.mayavi.root.update()
            self.mayavi.root.lift()
            self.mayavi.root.focus_force()

        if not self.showPreview:
            filename=self.getFilename(n)
            print "Rendering timepoint %d with filename %s"%(n,filename)
            self.saveFrame(filename)
            
    def saveFrame(self,filename):
        """
        Method: saveFrame(filename)
        Created: 22.02.2005, KP
        Description: Saves a frame with a given name
        """
        renwin=self.getRenderWindow()
        type=self.type
        comm = "renwin.save_%s(file)"
        eval(eval("comm%type"))      
        
            
    def getFilename(self,frameNum):
        """
        Method: getFilename()
        Created: 22.02.2005, KP
        Description: Returns output filename of the frame we're rendering
        """
        return self.format%(self.dirname,self.frameName,frameNum)

    def getCenter(self,tp=-1):
        """
        Method: getCenter()
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
        Method: getDimensions(timepoint)
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
            
    def setDataSet(self,dataset):
        """
        Method: setDataSet(dataset)
        Created: 22.02.2005, KP
        Description: Sets the dataset that is rendered in MayaVi                
        """
        dvms = self.mayavi.get_dvm_names()
        if len(dvms)> 1:
            Logging.info("There is more than one datavizmgr")
        for i in dvms:
            self.mm = i.get_current_module_mgr()
            Logging.info("Substituting data to dvm %s"%i)
            dvm=self.mayavi.mayavi.data_viz_mgr[i]
            ds=dvm.get_data_source()
            ds.data=dataset
            self.mayavi.update_label ()
            Logging.info("Updating datasource")
            ds.Update()
            ds.update_references()
