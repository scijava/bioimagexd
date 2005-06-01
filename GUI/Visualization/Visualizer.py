# -*- coding: iso-8859-1 -*-

"""
 Unit: Visualizer
 Project: BioImageXD
 Created: 28.04.2005, KP
 Description:

 A framework for replacing MayaVi for simple rendering tasks.
 
 Modified 28.04.2005 KP - Created the class
          23.05.2005 KP - Split the class to a module of it's own
          
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
import os
import glob

from Events import *
import Dialogs

import DataUnit
import DataUnitProcessing

from Lights import *
from Events import *

import PreviewFrame

visualizerInstance=None

def getVisualizer():
    global visualizerInstance
    return visualizerInstance
    
def getModes():
    modules=glob.glob("GUI/Visualization/Modes/*.py")
    moddict={}
    for file in modules:
        mod=file.split(".")[0:-1]
        mod=".".join(mod)
        mod.replace("/",".")
        print "Importing mode ",mod
        module = __import__(mod)
        name=module.getName()
        modclass=module.getClass()
        moddict[name]=(None,modclass,module)
    return moddict
    

class Visualizer:
    """
    Class: Visualizer
    Created: 05.04.2005, KP
    Description: A class that is the controller for the visualization
    """
    def __init__(self,parent,menuManager,**kws):
        """
        Method: __init__(parent)
        Created: 28.04.2005, KP
        Description: Initialization
        """
        global visualizerInstance
        visualizerInstance=self
        
        self.menuManager=menuManager
        self.renderingTime=0
        self.parent = parent
        self.closed = 0
        self.initialized = 0
        self.renderer=None
        self.dataUnit = None
        self.enabled=1
        self.timepoint = -1
        self.processedMode = 0
        self.modes=getModes()
        
        
        self.ID_TOOL_WIN=wx.NewId()
        self.ID_VISAREA_WIN=wx.NewId()
        self.ID_VISTREE_WIN=wx.NewId()
        self.ID_VISSLIDER_WIN=wx.NewId()
        
        self.parent.Bind(
            wx.EVT_SASH_DRAGGED_RANGE, self.onSashDrag,
            id=self.ID_TOOL_WIN, id2=self.ID_VISSLIDER_WIN,
        )

        
        self.sidebarWin=wx.SashLayoutWindow(self.parent,self.ID_VISTREE_WIN,style=wx.RAISED_BORDER|wx.SW_3D)
        self.sidebarWin.SetOrientation(wx.LAYOUT_VERTICAL)
        self.sidebarWin.SetAlignment(wx.LAYOUT_LEFT)
        self.sidebarWin.SetSashVisible(wx.SASH_RIGHT,True)
        self.sidebarWin.SetSashBorder(wx.SASH_RIGHT,True)
        self.sidebarWin.SetDefaultSize((200,768))

        self.toolWin=wx.SashLayoutWindow(self.parent,self.ID_TOOL_WIN,style=wx.NO_BORDER)
        self.toolWin.SetOrientation(wx.LAYOUT_HORIZONTAL)
        self.toolWin.SetAlignment(wx.LAYOUT_TOP)
        self.toolWin.SetSashVisible(wx.SASH_BOTTOM,False)
        self.toolWin.SetDefaultSize((500,32))
        
        self.visWin=wx.SashLayoutWindow(self.parent,self.ID_VISAREA_WIN,style=wx.NO_BORDER|wx.SW_3D)
        self.visWin.SetOrientation(wx.LAYOUT_VERTICAL)
        self.visWin.SetAlignment(wx.LAYOUT_LEFT)
        self.visWin.SetSashVisible(wx.SASH_RIGHT,False)
        self.visWin.SetSashVisible(wx.SASH_LEFT,False)
        self.visWin.SetDefaultSize((512,768))

        
        self.sliderWin=wx.SashLayoutWindow(self.parent,self.ID_VISSLIDER_WIN,style=wx.NO_BORDER)
        self.sliderWin.SetOrientation(wx.LAYOUT_HORIZONTAL)
        self.sliderWin.SetAlignment(wx.LAYOUT_BOTTOM)
        self.sliderWin.SetSashVisible(wx.SASH_TOP,False)
        self.sliderWin.SetDefaultSize((500,32))
        
        self.itemWin=wx.SashLayoutWindow(self.parent,self.ID_TOOL_WIN,style=wx.NO_BORDER)
        self.itemWin.SetOrientation(wx.LAYOUT_HORIZONTAL)
        self.itemWin.SetAlignment(wx.LAYOUT_BOTTOM)
        self.itemWin.SetSashVisible(wx.SASH_TOP,False)
        self.itemWin.SetDefaultSize((500,64))

        self.timeslider=wx.Slider(self.sliderWin,value=0,minValue=0,maxValue=1,
        style=wx.SL_HORIZONTAL|wx.SL_AUTOTICKS|wx.SL_LABELS)
        #self.sizer.Add(self.timeslider,(1,0),flag=wx.EXPAND|wx.LEFT|wx.RIGHT,span=(1,2))
        self.timeslider.Bind(wx.EVT_SCROLL,self.onChangeTimepoint)

        self.currMode=None
        self.currModeModule = None
        self.currentWindow=None
        self.galleryPanel=None
        self.preview=None
        self.sectionsPanel=None
        self.mode = None
        
        self.createToolbar()
        self.parent.Bind(wx.EVT_SIZE,self.OnSize)
        
    def createToolbar(self):
        """
        Method: createToolBar()
        Created: 28.05.2005, KP
        Description: Method to create a toolbar for the window
        """        
        self.tb = wx.ToolBar(self.toolWin,-1,style=wx.TB_HORIZONTAL)
        ID_CAPTURE=wx.NewId()
        ID_ZOOM_OUT=wx.NewId()
        ID_ZOOM_IN=wx.NewId()
        ID_ZOOM_TO_FIT=wx.NewId()
        ID_ZOOM_OBJECT=wx.NewId()
        self.tb.AddSimpleTool(ID_CAPTURE,wx.Image(os.path.join("Icons","camera.gif"),wx.BITMAP_TYPE_GIF).ConvertToBitmap(),"Capture slice","Capture the current optical slice")
        self.tb.AddSimpleTool(ID_ZOOM_OUT,wx.Image(os.path.join("Icons","zoom-out.gif"),wx.BITMAP_TYPE_GIF).ConvertToBitmap(),"Zoom out","Zoom out on the optical slice")
        #EVT_TOOL(self,ID_OPEN,self.menuOpen)

        self.zoomCombo=wx.ComboBox(self.tb,-1,"100%",choices=["12.5%","25%","33.33%","50%","66.67%","75%","100%","125%","150%","200%","300%","400%","600%","800%"],size=(100,-1),style=wx.CB_DROPDOWN)
        self.zoomCombo.SetSelection(6)
        self.tb.AddControl(self.zoomCombo)
        #self.preview.setZoomCombobox(self.zoomCombo)
        self.tb.AddSimpleTool(ID_ZOOM_IN,wx.Image(os.path.join("Icons","zoom-in.gif"),wx.BITMAP_TYPE_GIF).ConvertToBitmap(),"Zoom in","Zoom in on the slice")
        self.tb.AddSimpleTool(ID_ZOOM_TO_FIT,wx.Image(os.path.join("Icons","zoom-to-fit.gif"),wx.BITMAP_TYPE_GIF).ConvertToBitmap(),"Zoom to Fit","Zoom the slice so that it fits in the window")
        self.tb.AddSimpleTool(ID_ZOOM_OBJECT,wx.Image(os.path.join("Icons","zoom-object.gif"),wx.BITMAP_TYPE_GIF).ConvertToBitmap(),"Zoom object","Zoom user selected portion of the slice")

        #wx.EVT_TOOL(self,ID_CAPTURE,self.preview.captureSlice)
        #wx.EVT_TOOL(self,ID_ZOOM_IN,self.preview.zoomIn)
        #wx.EVT_TOOL(self,ID_ZOOM_OUT,self.preview.zoomOut)
        #wx.EVT_TOOL(self,ID_ZOOM_TO_FIT,self.preview.zoomToFit)
        #wx.EVT_TOOL(self,ID_ZOOM_OBJECT,self.preview.zoomObject)
        #self.zoomCombo.Bind(wx.EVT_COMBOBOX,self.preview.zoomToComboSelection)
        self.tb.Realize()

        
    def onSashDrag(self, event):
        """
        Method: onSashDrag
        Created: 24.5.2005, KP
        Description: A method for laying out the window
        """        
        if event.GetDragStatus() == wx.SASH_STATUS_OUT_OF_RANGE:
            print "Out of range!!!!!!!!!\n"
            return

        eID = event.GetId()

        if eID == self.ID_VISTREE_WIN:
            w,h=self.sidebarWin.GetSize()
            print "setting sidebarWin size"
            self.sidebarWin.SetDefaultSize((event.GetDragRect().width,h))
        
        #elif eID == ID_VISAREA_WIN:
        #    w,h=self.taskWin.GetSize()
        #    self.taskWin.SetDefaultSize((event.GetDragRect().width,h))
        
        #self.visWin.Refresh()
        wx.LayoutAlgorithm().LayoutWindow(self.parent, self.visWin)
        
    def OnSize(self, event):
        """
        Method: onSize
        Created: 23.05.2005, KP
        Description: Handle size events
        """
        wx.LayoutAlgorithm().LayoutWindow(self.parent, self.visWin)
        self.currentWindow.SetSize(self.visWin.GetSize())
                
    def __del__(self):
        global visualizerInstance
        visualizerInstance=None
        
    def reloadModules(self):
        """
        Method: reloadModules()
        Created: 24.05.2005, KP
        Description: Reload all the visualization modules.
        """
        if "reloadModules" in dir(self.currMode):
            self.currMode.reloadModules()
        for key in self.modes.keys():
            mod,module=self.modes[key]
            module=reload(module)
            print "Reloaded mode ",module
            self.modes[key]=(mod,module)
        return
        # Borrowed from mayavi
        my_dir = os.path.dirname (os.path.abspath (__file__))
        dont_load = list (sys.builtin_module_names)

        for key in sys.modules.keys ():
            if key not in dont_load:
                mod = sys.modules[key]
                if mod and hasattr (mod, '__file__'):
                    p = os.path.abspath (mod.__file__)
                    if os.path.commonprefix ([p, my_dir]) == my_dir:
                        debug ("Reloading %s"%key)
                        reload (mod)
   
    def setProcessedMode(self,mode):
        """
        Method: setProcessedMode
        Created: 25.05.2005, KP
        Description: Set the visualizer to processed/unprocessed mode
        """
        self.processedMode=mode
        
    def getProcessedMode(self):
        """
        Method: setProcessedMode
        Created: 25.05.2005, KP
        Description: Return whether visualizer is in processed/unprocessed mode
        """
        return self.processedMode
        
    def setVisualizationMode(self,mode):
        """
        Method: setVisualizationMode
        Created: 23.05.2005, KP
        Description: Set the mode of visualization
        Parameters:
            mode     The mode.
        """
        if self.mode == mode:
            print "%s already selected"%mode
            return
        self.mode=mode
        
        if self.currMode:
            self.currMode.deactivate()
            
        modeinst,modeclass,module=self.modes[mode]
        if not modeinst:
            modeinst=modeclass(self.visWin,self)
            self.modes[mode]=(modeinst,modeclass,module)
        
        # dataunit might have been changed so set it every time a 
        # mode is loaded
        
        self.currMode=modeinst
        self.currModeModule=module
        
        if not modeinst.showSideBar():
            self.sidebarWin.SetDefaultSize((0,1024))
        else:
            self.sidebarWin.SetDefaultSize((200,1024))
            
        self.currentWindow = modeinst.activate(self.sidebarWin)
        modeinst.setDataUnit(self.dataUnit)    
        wx.LayoutAlgorithm().LayoutWindow(self.parent, self.visWin)            
        
        self.currentWindow.Show()
        
    def enable(self,flag):
        """
        Method: enable(flag)
        Created: 23.05.2005, KP
        Description: Enable/Disable updates
        """
        self.enabled=flag

    def setBackground(self,r,g,b):
        """
        Method: setBackground(r,g,b)
        Created: 16.05.2005, KP
        Description: Set the background color
        """
        self.currMode.setBackground(r,g,b)

    def onClose(self,event):
        """
        Method: onClose()
        Created: 28.04.2005, KP
        Description: Called when this window is closed
        """
        self.closed = 1l

    def isClosed(self):
        """
        Method: isClosed()
        Created: 28.04.2005, KP
        Description: Returns flag indicating the closure of this window
        """
        return self.closed
        
    def setDataUnit(self,dataunit):
        """
        Method: setDataUnit(self)
        Created: 28.04.2005, KP
        Description: Sets the dataunit this module uses for visualization
        """
        self.dataUnit = dataunit
        count=dataunit.getLength()
        print "Setting range to",count
        self.timeslider.SetRange(0,count-1)
        if self.enabled:                 
            if "setDataUnit" in dir(self.currentWindow):
                self.currentWindow.setDataUnit(dataunit)
            self.currMode.setDataUnit(self.dataUnit)
            
    def updateRendering(self,event=None):
        """
        Method: updateRendering
        Created: 25.05.2005, KP
        Description: Update the rendering
        """
        print "Updating rendering"
        # If the visualization mode doesn't want immediate rendering
        # then we will delay a bit with this
        imm=self.currModeModule.getImmediateRendering()
        if not imm:
            t=time.time()
            delay = self.currModeModule.getRenderingDelay()/1000.0
            if abs(self.renderingTime-t) < delay: 
                print "Delaying, delay=",delay,"diff=",abs(self.renderingTime-t)
                return
        self.renderingTime=time.time()
        self.currMode.updateRendering()
                
    def Render(self,evt=None):
        """
        Method: Render()
        Created: 28.04.2005, KP
        Description: Render the scene
        """
        self.currMode.Render()
        
    def onChangeTimepoint(self,event):
        """
        Method: onChangeTimepoint
        Created: 28.04.2005, KP
        Description: Set the timepoint to be shown
        """
        tp=self.timeslider.GetValue()
        if self.timepoint != tp:
            self.setTimepoint(tp)
            evt=ChangeEvent(myEVT_TIMEPOINT_CHANGED,self.parent.GetId())
            evt.setValue(tp)
            print "Sending change event",tp
            self.parent.GetEventHandler().ProcessEvent(evt)


    def setRenderWindowSize(self,size):
        """
        Method: setRenderWindowSize(size)
        Created: 28.04.2005, KP
        Description: Set the render window size
        """  
        self.currentWindow.SetSize((size))
        #self.wxrenwin.SetSize((size))
        #self.renwin.SetSize((size))
        self.sizer.Fit(self.parent)
        self.parent.Layout()
        self.parent.Refresh()
        self.Render()
        
    def setTimepoint(self,timepoint):
        """
        Method: setTimepoint(timepoint)
        Created: 28.04.2005, KP
        Description: Set the timepoint to be shown
        """  
        if self.timeslider.GetValue()!=timepoint:
            self.timeslider.SetValue(timepoint)
        self.timepoint = timepoint
        if "setTimepoint" in dir(self.currentWindow):
            self.currentWindow.setTimepoint(self.timepoint)
        self.currMode.setTimepoint(self.timepoint)
        
