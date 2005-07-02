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

import Dialogs

import DataUnit
import DataUnitProcessing
import MenuManager

from GUI import Events
import PreviewFrame
import os.path
import sys

visualizerInstance=None

def getVisualizer():
    print "getVisualizer() called! returning",visualizerInstance
    global visualizerInstance
    return visualizerInstance

def getModes():
    path=reduce(os.path.join,["GUI","Visualization","Modes","*.py"])
    spath=reduce(os.path.join,[os.getcwd(),"GUI","Visualization","Modes"])
    print "adding ",spath
    sys.path=sys.path+[spath]
    print "path=",path
    modules=glob.glob(path)
    moddict={}
    for file in modules:
        mod=file.split(".")[0:-1]
        mod=".".join(mod)
        print "mod=",mod
        mod=mod.replace("/",".")
        mod=mod.replace("\\",".")
        frompath=mod.split(".")[:-1]
        frompath=".".join(frompath)
        mod=mod.split(".")[-1]
        print "importing %s from %s"%(mod,frompath)
        module = __import__(mod,globals(),locals(),mod)
        print "module=",module
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
    def __init__(self,parent,menuManager,mainwin,**kws):
        """
        Method: __init__(parent)
        Created: 28.04.2005, KP
        Description: Initialization
        """
        global visualizerInstance
        visualizerInstance=self
        self.mainwin=mainwin
        self.menuManager=menuManager
        self.renderingTime=0
        self.parent = parent
        self.closed = 0
        self.initialized = 0
        self.renderer=None
        self.dataUnit = None
        self.enabled=1
        self.timepoint = -1
        self.preload=0
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
        self.toolWin.SetDefaultSize((500,44))
        
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

        self.sliderPanel=wx.Panel(self.sliderWin,-1)
        self.prev=wx.Button(self.sliderPanel,-1,"<")
        self.prev.SetSize((64,64))
        self.next=wx.Button(self.sliderPanel,-1,">")
        self.next.SetSize((64,64))
        self.sliderbox=wx.BoxSizer(wx.HORIZONTAL)
        self.prev.Bind(wx.EVT_BUTTON,self.onPrevTimepoint)
        self.next.Bind(wx.EVT_BUTTON,self.onNextTimepoint)
        
        self.timeslider=wx.Slider(self.sliderPanel,value=0,minValue=0,maxValue=1,
        style=wx.SL_HORIZONTAL|wx.SL_AUTOTICKS|wx.SL_LABELS)
        self.timeslider.Bind(wx.EVT_SCROLL,self.onChangeTimepoint)

        self.sliderbox.Add(self.prev)
        self.sliderbox.Add(self.timeslider,1)
        self.sliderbox.Add(self.next)
        self.sliderPanel.SetSizer(self.sliderbox)
        self.sliderPanel.SetAutoLayout(1)
        self.sliderbox.Fit(self.sliderPanel)

        self.currMode=None
        self.currModeModule = None
        self.currentWindow=None
        self.galleryPanel=None
        self.preview=None
        self.sectionsPanel=None
        self.mode = None
        
        self.createToolbar()
        self.parent.Bind(wx.EVT_SIZE,self.OnSize)
        
    def onNextTimepoint(self,evt):
        """
        Method: onNextTimepoint
        Created: 26.06.2005, KP
        Description: Go to next timepoint
        """ 
        if self.timepoint<self.maxTimepoint:
            self.setTimepoint(self.timepoint+1)
        
    def onPrevTimepoint(self,evt):
        """
        Method: onPrevTimepoint
        Created: 26.06.2005, KP
        Description: Go to previous timepoint
        """        
        if self.timepoint>=1:
            self.setTimepoint(self.timepoint-1)
    def createToolbar(self):
        """
        Method: createToolBar()
        Created: 28.05.2005, KP
        Description: Method to create a toolbar for the window
        """        
        self.tb = wx.ToolBar(self.toolWin,-1,style=wx.TB_HORIZONTAL)
        self.tb.SetToolBitmapSize((32,32))
        self.tb.AddSimpleTool(MenuManager.ID_ZOOM_OUT,wx.Image(os.path.join("Icons","zoom-out.gif"),wx.BITMAP_TYPE_GIF).ConvertToBitmap(),"Zoom out","Zoom out on the optical slice")
        #EVT_TOOL(self,ID_OPEN,self.menuOpen)

        self.zoomCombo=wx.ComboBox(self.tb,-1,"100%",choices=["12.5%","25%","33.33%","50%","66.67%","75%","100%","125%","150%","200%","300%","400%","600%","800%"],size=(100,-1),style=wx.CB_DROPDOWN)
        self.zoomCombo.SetSelection(6)
        self.tb.AddControl(self.zoomCombo)
        #self.preview.setZoomCombobox(self.zoomCombo)
        self.tb.AddSimpleTool(MenuManager.ID_ZOOM_IN,wx.Image(os.path.join("Icons","zoom-in.gif"),wx.BITMAP_TYPE_GIF).ConvertToBitmap(),"Zoom in","Zoom in on the slice")
        self.tb.AddSimpleTool(MenuManager.ID_ZOOM_TO_FIT,wx.Image(os.path.join("Icons","zoom-to-fit.gif"),wx.BITMAP_TYPE_GIF).ConvertToBitmap(),"Zoom to Fit","Zoom the slice so that it fits in the window")
        self.tb.AddSimpleTool(MenuManager.ID_ZOOM_OBJECT,wx.Image(os.path.join("Icons","zoom-object.gif"),wx.BITMAP_TYPE_GIF).ConvertToBitmap(),"Zoom object","Zoom user selected portion of the slice")

        wx.EVT_TOOL(self.parent,MenuManager.ID_ZOOM_IN,self.zoomIn)
        wx.EVT_TOOL(self.parent,MenuManager.ID_ZOOM_OUT,self.zoomOut)
        wx.EVT_TOOL(self.parent,MenuManager.ID_ZOOM_TO_FIT,self.zoomToFit)
        wx.EVT_TOOL(self.parent,MenuManager.ID_ZOOM_OBJECT,self.zoomObject)
        self.zoomCombo.Bind(wx.EVT_COMBOBOX,self.zoomToComboSelection)
        self.tb.Realize()

    def zoomObject(self,evt):
        """
        Method: zoomObject()
        Created: 19.03.2005, KP
        Description: Lets the user select the part of the object that is zoomed
        """
        pass
        #self.renderpanel.startZoom()
        
    def zoomOut(self,evt):
        """
        Method: zoomOut()
        Created: 19.03.2005, KP
        Description: Makes the zoom factor smaller
        """
        return self.zoomComboDirection(-1)
        
    def zoomToComboSelection(self,evt):
        """
        Method: zoomToComboSelection()
        Created: 19.03.2005, KP
        Description: Sets the zoom according to the combo selection
        """
        return self.zoomComboDirection(0)        
        
    def zoomComboDirection(self,dir):
        """
        Method: zoomComboDirection()
        Created: 21.02.2005, KP
        Description: Makes the zoom factor larger/smaller based on values in the zoom combobox
        """
        pos=self.zoomCombo.GetSelection()
        s=self.zoomCombo.GetString(pos)
        if dir>0 and pos >= self.zoomCombo.GetCount():
            #print "Zoom at max: ",s
            return
        if dir<0 and pos==0:
            #print "Zoom at min: ",s
            return
        pos+=dir
        s=self.zoomCombo.GetString(pos)
        factor = float(s[:-1])/100.0
        self.zoomCombo.SetSelection(pos)
        self.currMode.setZoomFactor(factor)
        self.currMode.Render()
        
        
    def zoomIn(self,evt,factor=-1):
        """
        Method: zoomIn()
        Created: 21.02.2005, KP0
        Description: Makes the zoom factor larger 
        """
        return self.zoomComboDirection(1)
              
    def zoomToFit(self,evt):
        """
        Method: zoomToFit()
        Created: 21.02.2005, KP
        Description: Sets the zoom factor to fit the image into the preview window
        """
        self.currMode.zoomToFit()
        self.currMode.Render()
        
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
#        if not self.enabled:return
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
        
    def getCurrentMode(self):
        """
        Method: setCurrentMode
        Created: 20.06.2005, KP
        Description: Return the current visualization mode
        """
        return self.currMode
        
    def getCurrentModeName(self):
        """
        Method: setCurrentModeName
        Created: 20.06.2005, KP
        Description: Return the current visualization mode
        """
        return self.mode
        
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
            if self.dataUnit and self.currMode.dataUnit != self.dataUnit:
                print "Re-setting dataunit"
                self.currMode.setDataUnit(self.dataUnit)
                return
        self.mode=mode

        if self.currMode:
            self.currMode.deactivate()

        modeinst,modeclass,module=self.modes[mode]
        if not modeinst:
            modeinst=modeclass(self.visWin,self)
            self.modes[mode]=(modeinst,modeclass,module)
        if not module.showZoomToolbar():
            self.toolWin.SetDefaultSize((500,0))
        else:
            self.toolWin.SetDefaultSize((500,44))

        # dataunit might have been changed so set it every time a
        # mode is loaded

        self.currMode=modeinst
        self.currModeModule=module

        if not modeinst.showSideBar():
            self.sidebarWin.SetDefaultSize((0,1024))
        else:
            self.sidebarWin.SetDefaultSize((200,1024))

        self.currentWindow = modeinst.activate(self.sidebarWin)
        #self.currentWindow.enable(self.enabled)

        if self.dataUnit and modeinst.dataUnit != self.dataUnit:
            print "Re-setting dataunit"
            modeinst.setDataUnit(self.dataUnit)
        wx.LayoutAlgorithm().LayoutWindow(self.parent, self.visWin)

        self.currentWindow.Show()

    def showItemToolbar(self,flag):
        """
        Method: showItemToolbar()
        Created: 01.06.2005, KP
        Description: Show / hide item toolbar
        """
        pass
        #if flag:
        #    self.itemWin.SetDefaultSize((500,64))
        #else:
        #    self.itemWin.SetDefaultSize((500,0))
        
    def enable(self,flag,**kws):
        """
        Method: enable(flag)
        Created: 23.05.2005, KP
        Description: Enable/Disable updates
        """
        self.preload=0
        if kws.has_key("preload"):
            self.preload=kws["preload"]
        print "\n\nenable(%d)\n\n"%flag
        self.enabled=flag
        if self.currentWindow:
            try:
                self.currentWindow.enable(flag)
            except:
                pass
        if flag:        
           wx.LayoutAlgorithm().LayoutWindow(self.parent, self.visWin)
           print "Setting size to",self.visWin.GetSize()
           self.currentWindow.SetSize(self.visWin.GetSize())
        if flag:        
           wx.LayoutAlgorithm().LayoutWindow(self.parent, self.visWin)
           self.currentWindow.SetSize(self.visWin.GetSize())

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
        print "visualizer.setDataUnit(",dataunit,")"
        self.dataUnit = dataunit
        count=dataunit.getLength()
        print "Setting range to",count
        self.maxTimepoint=count-1
        self.timeslider.SetRange(0,count-1)
        showItems=0
        if self.processedMode:
            n=len(dataunit.getSourceDataUnits())
            if n>1:
                showItems=1
        self.showItemToolbar(showItems)
            
        if self.enabled and self.currMode:                 
            print "calling current modes setDataUnit"
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
        if self.enabled:
            print "Render()"
            self.currMode.Render()
        
    def onSetTimepoint(self,event):
        """
        Method: onSetTimepoint
        Created: 21.06.2005, KP
        Description: Update the timepoint according to an evnet
        """
        tp=event.getValue()
        self.setTimepoint(tp)
        
    def onChangeTimepoint(self,event):
        """
        Method: onChangeTimepoint
        Created: 28.04.2005, KP
        Description: Set the timepoint to be shown
        """
        tp=self.timeslider.GetValue()
        if self.timepoint != tp:
            self.setTimepoint(tp)
            evt=Events.ChangeEvent(Events.myEVT_TIMEPOINT_CHANGED,self.parent.GetId())
            evt.setValue(tp)
            print "Sending change event",tp
            self.parent.GetEventHandler().ProcessEvent(evt)

    def onSnapshot(self,event):
        """
        Method: onSnapshot
        Created: 05.06.2005, KP
        Description: Save a snapshot of current visualization
        """  
        if self.currMode and self.dataUnit:
            wc="PNG file|*.png|JPEG file|*.jpeg|TIFF file|*.tiff|BMP file|*.bmp"
            initFile="%s.png"%(self.dataUnit.getName())
            dlg=wx.FileDialog(self.parent,"Save snapshot of rendered scene",defaultFile=initFile,wildcard=wc,style=wx.SAVE)
            filename=None
            if dlg.ShowModal()==wx.ID_OK:
                filename=dlg.GetPath()
            self.currMode.saveSnapshot(filename)
        

    def setRenderWindowSize(self,size):
        """
        Method: setRenderWindowSize(size)
        Created: 28.04.2005, KP
        Description: Set the render window size
        """  
        self.currentWindow.SetSize((size))
        #self.wxrenwin.SetSize((size))
        #self.renwin.SetSize((size))
        self.OnSize(None)
        self.parent.Layout()
        self.parent.Refresh()
        self.Render()
        
    def setTimepoint(self,timepoint):
        """
        Method: setTimepoint(timepoint)
        Created: 28.04.2005, KP
        Description: Set the timepoint to be shown
        """  
        print "setTimepoint()"
        if self.timeslider.GetValue()!=timepoint:
            self.timeslider.SetValue(timepoint)
        self.timepoint = timepoint
        if "setTimepoint" in dir(self.currentWindow):
            self.currentWindow.setTimepoint(self.timepoint)
        self.currMode.setTimepoint(self.timepoint)
        
