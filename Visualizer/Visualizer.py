# -*- coding: iso-8859-1 -*-

"""
 Unit: Visualizer
 Project: BioImageXD
 Created: 28.04.2005, KP
 Description:

 A visualization framework for the BioImageXD software
           
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
#from enthought.tvtk import messenger
import messenger

import vtk
import os
import glob

import Dialogs
import Logging

import DataUnit
import MenuManager
import Histogram

import platform

import PreviewFrame
import os.path
import sys

import Modules
import Annotation

visualizerInstance=None

def getVisualizer():
    global visualizerInstance
    return visualizerInstance

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
        
        self.updateFactor = 0.001
        self.depthT=0
        
        self.z=0
        self.viewCombo = None
        self.histogramIsShowing=0
        self.histogramDataUnit=None
        self.histograms=[]
        self.changing=0
        self.mainwin=mainwin
        self.menuManager=menuManager
        self.renderingTime=0
        self.in_vtk=0
        self.parent = parent
        messenger.connect(None,"timepoint_changed",self.onSetTimepoint)
        messenger.connect(None,"data_changed",self.updateRendering)
        self.closed = 0
        self.initialized = 0
        self.renderer=None
        self.dataUnit = None
        self.enabled=1
        self.timepoint = 0
        self.preload=0
        self.processedMode = 0
        self.modes=Modules.DynamicLoader.getVisualizationModes()
        self.instances={}
        for key in self.modes.keys():
            self.instances[key]=None
        
        messenger.connect(None,"show",self.onSetVisibility)
        messenger.connect(None,"hide",self.onSetVisibility)
        
        self.sizes={}
        
        self.parent.Bind(
            wx.EVT_SASH_DRAGGED_RANGE, self.onSashDrag,
            id=MenuManager.ID_TOOL_WIN, id2=MenuManager.ID_HISTOGRAM_WIN,
        )

        
        self.sidebarWin=wx.SashLayoutWindow(self.parent,MenuManager.ID_VISTREE_WIN,style=wx.RAISED_BORDER|wx.SW_3D)
        self.sidebarWin.SetOrientation(wx.LAYOUT_VERTICAL)
        self.sidebarWin.SetAlignment(wx.LAYOUT_LEFT)
        self.sidebarWin.SetSashVisible(wx.SASH_RIGHT,True)
        self.sidebarWin.SetSashBorder(wx.SASH_RIGHT,True)
        self.sidebarWin.SetDefaultSize((200,768))
        self.sidebarWin.origSize=(200,768)

        self.toolWin=wx.SashLayoutWindow(self.parent,MenuManager.ID_TOOL_WIN,style=wx.NO_BORDER)
        self.toolWin.SetOrientation(wx.LAYOUT_HORIZONTAL)
        self.toolWin.SetAlignment(wx.LAYOUT_TOP)
        self.toolWin.SetSashVisible(wx.SASH_BOTTOM,False)
        self.toolWin.SetDefaultSize((500,44))

        self.histogramWin=wx.SashLayoutWindow(self.parent,MenuManager.ID_HISTOGRAM_WIN,style=wx.NO_BORDER)
        self.histogramWin.SetOrientation(wx.LAYOUT_HORIZONTAL)
        self.histogramWin.SetAlignment(wx.LAYOUT_TOP)
        #self.histogramWin.SetSashVisible(wx.SASH_BOTTOM,False)
        self.histogramWin.SetDefaultSize((500,0))
        
        self.histogramPanel=wx.Panel(self.histogramWin)
        self.histogramBox=wx.BoxSizer(wx.HORIZONTAL)

        self.histogramPanel.SetSizer(self.histogramBox)
        self.histogramPanel.SetAutoLayout(1)
        self.histogramBox.Fit(self.histogramPanel)


        self.visWin=wx.SashLayoutWindow(self.parent,MenuManager.ID_VISAREA_WIN,style=wx.NO_BORDER|wx.SW_3D)
        self.visWin.SetOrientation(wx.LAYOUT_VERTICAL)
        self.visWin.SetAlignment(wx.LAYOUT_LEFT)
        self.visWin.SetSashVisible(wx.SASH_RIGHT,False)
        self.visWin.SetSashVisible(wx.SASH_LEFT,False)
        self.visWin.SetDefaultSize((512,768))
        
        self.sliderWin=wx.SashLayoutWindow(self.parent,MenuManager.ID_VISSLIDER_WIN,style=wx.NO_BORDER)
        self.sliderWin.SetOrientation(wx.LAYOUT_HORIZONTAL)
        self.sliderWin.SetAlignment(wx.LAYOUT_BOTTOM)
        self.sliderWin.SetSashVisible(wx.SASH_TOP,False)
        self.sliderWin.SetDefaultSize((500,64))
        
        self.zsliderWin=wx.SashLayoutWindow(self.parent,MenuManager.ID_ZSLIDER_WIN,style=wx.NO_BORDER|wx.SW_3D)
        self.zsliderWin.SetOrientation(wx.LAYOUT_VERTICAL)
        self.zsliderWin.SetAlignment(wx.LAYOUT_RIGHT)
        self.zsliderWin.SetSashVisible(wx.SASH_RIGHT,False)
        self.zsliderWin.SetSashVisible(wx.SASH_LEFT,False)
        self.zsliderWin.SetDefaultSize((32,768))        
        self.zsliderWin.origSize=(32,768)
        
        self.createSliders()

        self.currMode=None
        self.currModeModule = None
        self.currentWindow=None
        self.galleryPanel=None
        self.preview=None
        self.sectionsPanel=None
        self.mode = None
        
        self.createToolbar()
        self.parent.Bind(wx.EVT_SIZE,self.OnSize)
        
    def createSliders(self):
        """
        Method: createSliders
        Created: 1.08.2005, KP
        Description: Method that creates the sliders 
        """     
        self.sliderPanel=wx.Panel(self.sliderWin,-1)
        iconpath=reduce(os.path.join,["Icons"])
        leftarrow = wx.Image(os.path.join(iconpath,"leftarrow.gif"),wx.BITMAP_TYPE_GIF).ConvertToBitmap()
        rightarrow = wx.Image(os.path.join(iconpath,"rightarrow.gif"),wx.BITMAP_TYPE_GIF).ConvertToBitmap()
        self.prev=wx.BitmapButton(self.sliderPanel,-1,leftarrow)
        self.prev.SetSize((64,64))
        self.next=wx.BitmapButton(self.sliderPanel,-1,rightarrow)
        self.next.SetSize((64,64))
        
        self.sliderbox=wx.BoxSizer(wx.HORIZONTAL)
        self.prev.Bind(wx.EVT_BUTTON,self.onPrevTimepoint)
        self.next.Bind(wx.EVT_BUTTON,self.onNextTimepoint)
        
        self.timeslider=wx.Slider(self.sliderPanel,value=1,minValue=1,maxValue=1,
        style=wx.SL_HORIZONTAL|wx.SL_LABELS)
        self.timeslider.SetHelpText("Use this slider to select the displayed timepoint.")
        if platform.system()=="Windows":
            self.timeslider.Bind(wx.EVT_SCROLL_ENDSCROLL,self.onUpdateTimepoint)
            self.timeslider.Bind(wx.EVT_SCROLL_THUMBRELEASE,self.onUpdateTimepoint)
        else:
            self.timeslider.Bind(wx.EVT_SCROLL,self.onChangeTimepoint)

        self.zslider=wx.Slider(self.zsliderWin,value=1,minValue=1,maxValue=1,
        style=wx.SL_VERTICAL|wx.SL_LABELS|wx.SL_AUTOTICKS)
        self.zslider.SetHelpText("Use this slider to select the displayed optical slice.")
        self.zslider.Bind(wx.EVT_SCROLL,self.onChangeZSlice)
        messenger.connect(None,"zslice_changed",self.onChangeZSlice)
        
        self.sliderbox.Add(self.prev)
        self.sliderbox.Add(self.timeslider,1)
        self.sliderbox.Add(self.next)
        self.sliderPanel.SetSizer(self.sliderbox)
        self.sliderPanel.SetAutoLayout(1)
        self.sliderbox.Fit(self.sliderPanel)
        
    def onSetVisibility(self,obj,evt,arg):
        """
        Method: onSetVisibility
        Created: 12.07.2005, KP
        Description: Set an object's visibility
        """ 
        obj=None
        if arg=="toolbar":obj=self.toolWin
        elif arg=="zslider":obj=self.zsliderWin
        elif arg=="histogram":
            obj=self.histogramWin
            w,h=0,0
            for i in self.histograms:
                w2,h2=i[0].GetSize()
                w=w2
                if h<h2:h=h2
            Logging.info("Got ",w,h,"for histogram size",kw="visualizer")
            if not h:h=200
            self.sizes["histogram"]=w,h
        elif arg=="config":obj=self.sidebarWin
        if evt=="hide":
            Logging.info("Hiding ",arg,"=",obj,kw="visualizer")
            if arg not in self.sizes:
                w,h=obj.GetSize()
                self.sizes[arg]=(w,h)
            obj.SetDefaultSize((0,0))
        else:
            Logging.info("Showing ",arg)
            if arg in self.sizes:
                obj.SetDefaultSize(self.sizes[arg])
            del self.sizes[arg]
        if evt=="show" and arg=="histogram":
            if not self.histogramIsShowing:
                self.createHistogram()
            self.histogramPanel.Layout()
            for histogram,sbox,sboxsizer in self.histograms:
                sboxsizer.Fit(histogram)
            self.histogramIsShowing=1
        elif evt=="hide" and arg=="histogram":
            self.histogramIsShowing=0
            
        self.OnSize(None)
            
        
    def getDataUnit(self):
        """
        Method: getDataUnit()
        Created: 09.07.2005, KP
        Description: Return the dataunit that is currently shown
        """ 
        return self.dataUnit
        
    def onNextTimepoint(self,evt):
        """
        Method: onNextTimepoint
        Created: 26.06.2005, KP
        Description: Go to next timepoint
        """ 
        if self.timepoint<self.maxTimepoint:
            Logging.info("Setting timepoint to ",self.timepoint+1,kw="visualizer")
            self.setTimepoint(self.timepoint+1)
            messenger.send(None,"timepoint_changed",self.timepoint)        
    def onPrevTimepoint(self,evt):
        """
        Method: onPrevTimepoint
        Created: 26.06.2005, KP
        Description: Go to previous timepoint
        """        
        if self.timepoint>=1:
            self.setTimepoint(self.timepoint-1)
            messenger.send(None,"timepoint_changed",self.timepoint)        
    def createHistogram(self):
        """
        Method: createHistogram()
        Created: 28.05.2005, KP
        Description: Method to create histograms of the dataunit
        """        
        if self.dataUnit != self.histogramDataUnit:
            self.histogramDataUnit=self.dataUnit
        for histogram,sbox,sboxsizer in self.histograms:
            print "Detaching ",sboxsizer
            self.histogramBox.Detach(sboxsizer)
            sboxsizer.Detach(histogram)
            sboxsizer.Destroy()
            sbox.Destroy()
            histogram.Destroy()
        self.histograms=[]
        units=[]
        if self.processedMode:
            units=self.dataUnit.getSourceDataUnits()
        else:
            units=[self.dataUnit]
        for unit in units:
            histogram=Histogram.Histogram(self.histogramPanel)
            name=unit.getName()
            sbox=wx.StaticBox(self.histogramPanel,-1,"Channel %s"%name)
            sboxsizer=wx.StaticBoxSizer(sbox,wx.VERTICAL)
            sboxsizer.Add(histogram)
            self.histogramBox.Add(sboxsizer,1,border=10,flag=wx.BOTTOM)
            histogram.setDataUnit(unit)
            self.histograms.append((histogram,sbox,sboxsizer))
        self.histogramPanel.Layout()
        self.OnSize(None)
            

            
    def createToolbar(self):
        """
        Method: createToolBar()
        Created: 28.05.2005, KP
        Description: Method to create a toolbar for the window
        """        
        self.tb = wx.ToolBar(self.toolWin,-1,style=wx.TB_HORIZONTAL)
        self.tb.SetToolBitmapSize((32,32))
        self.viewCombo=wx.ComboBox(self.tb,MenuManager.ID_SET_VIEW,"Isometric",choices=["+X","-X","+Y","-Y","+Z","-Z","Isometric"],size=(100,-1),style=wx.CB_DROPDOWN)
        self.viewCombo.SetSelection(6)
        self.viewCombo.SetHelpText("This controls the view angle of 3D view mode.")
        self.tb.InsertControl(0,self.viewCombo)
        wx.EVT_COMBOBOX(self.parent,MenuManager.ID_SET_VIEW,self.onSetView)
        self.tb.Realize()                
        self.tb.AddSimpleTool(MenuManager.ID_ZOOM_OUT,wx.Image(os.path.join("Icons","zoom-out.gif"),wx.BITMAP_TYPE_GIF).ConvertToBitmap(),"Zoom out","Zoom out on the optical slice")
        #EVT_TOOL(self,ID_OPEN,self.menuOpen)

        self.zoomLevels=[0.125, 0.25, 0.3333, 0.5, 0.6667, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0,-1]
        self.zoomCombo=wx.ComboBox(self.tb,-1,"100%",
                          choices=["12.5%","25%","33.33%","50%","66.67%","75%","100%","125%","150%","200%","300%","400%","600%","800%","Zoom to fit"],size=(100,-1),style=wx.CB_DROPDOWN)
        self.zoomCombo.SetSelection(6)
        self.zoomCombo.SetHelpText("This controls the zoom level of visualization views.")        
        self.tb.AddControl(self.zoomCombo)

        self.tb.AddSimpleTool(MenuManager.ID_ZOOM_IN,wx.Image(os.path.join("Icons","zoom-in.gif"),wx.BITMAP_TYPE_GIF).ConvertToBitmap(),"Zoom in","Zoom in on the slice")
        self.tb.AddSimpleTool(MenuManager.ID_ZOOM_TO_FIT,wx.Image(os.path.join("Icons","zoom-to-fit.gif"),wx.BITMAP_TYPE_GIF).ConvertToBitmap(),"Zoom to Fit","Zoom the slice so that it fits in the window")
        self.tb.AddSimpleTool(MenuManager.ID_ZOOM_OBJECT,wx.Image(os.path.join("Icons","zoom-object.gif"),wx.BITMAP_TYPE_GIF).ConvertToBitmap(),"Zoom object","Zoom user selected portion of the slice")
        self.tb.AddSeparator()
        self.tb.AddSimpleTool(MenuManager.ID_DRAG_ANNOTATION,wx.Image(os.path.join("Icons","arrow.gif"),wx.BITMAP_TYPE_GIF).ConvertToBitmap(),"Manage annotations","Manage annotations on the image")
        
        self.tb.AddSimpleTool(MenuManager.ID_ADD_SCALE,wx.Image(os.path.join("Icons","scale.gif"),wx.BITMAP_TYPE_GIF).ConvertToBitmap(),"Draw scale","Draw a scale bar on the image")
        self.tb.AddSeparator()
        self.origBtn=wx.Button(self.tb,-1,"Original")
        self.origBtn.SetHelpText("Use this button to show how the unprocessed dataset looks like.")
        self.origBtn.Bind(wx.EVT_LEFT_DOWN,self.onShowOriginal)
        self.origBtn.Bind(wx.EVT_LEFT_UP,self.onHideOriginal)
        self.tb.AddControl(self.origBtn)
 #       self.tb.AddSimpleTool(MenuManager.ID_ROI_CIRCLE,wx.Image(os.path.join("Icons","circle.gif"),wx.BITMAP_TYPE_GIF).ConvertToBitmap(),"Select circle","Select a circular area of the image")
 #       self.tb.AddSimpleTool(MenuManager.ID_ROI_RECTANGLE,wx.Image(os.path.join("Icons","rectangle.gif"),wx.BITMAP_TYPE_GIF).ConvertToBitmap(),"Select rectangle","Select a rectangular area of the image")
 #       self.tb.AddSimpleTool(MenuManager.ID_ROI_POLYGON,wx.Image(os.path.join("Icons","polygon.gif"),wx.BITMAP_TYPE_GIF).ConvertToBitmap(),"Select polygon","Select a polygonal area of the image")

        self.cBtn = wx.ContextHelpButton(self.tb)
        self.tb.AddControl(self.cBtn)
 
        wx.EVT_TOOL(self.parent,MenuManager.ID_ZOOM_IN,self.zoomIn)
        wx.EVT_TOOL(self.parent,MenuManager.ID_ZOOM_OUT,self.zoomOut)
        wx.EVT_TOOL(self.parent,MenuManager.ID_ZOOM_TO_FIT,self.zoomToFit)
        wx.EVT_TOOL(self.parent,MenuManager.ID_ZOOM_OBJECT,self.zoomObject)
        wx.EVT_TOOL(self.parent,MenuManager.ID_ADD_SCALE,self.addAnnotation)
        wx.EVT_TOOL(self.parent,MenuManager.ID_DRAG_ANNOTATION,self.manageAnnotation)
        
#        wx.EVT_TOOL(self.parent,MenuManager.ID_ROI_CIRCLE,self.addAnnotation)
#        wx.EVT_TOOL(self.parent,MenuManager.ID_ROI_RECTANGLE,self.addAnnotation)
#        wx.EVT_TOOL(self.parent,MenuManager.ID_ROI_POLYGON,self.addAnnotation)
        
        self.zoomCombo.Bind(wx.EVT_COMBOBOX,self.zoomToComboSelection)
        self.tb.Realize()       
        self.viewCombo.Enable(0)
    def onHideOriginal(self,evt):
        """
        Method: onShowOriginal
        Created: 27.07.2005, KP
        Description: Show the original datasets instead of processed ones
        """
        if self.dataUnit:
            self.dataUnit.getSettings().set("ShowOriginal",0)
        self.updateRendering()
        evt.Skip()
        
    def onShowOriginal(self,evt):
        """
        Method: onShowOriginal
        Created: 27.07.2005, KP
        Description: Show the original datasets instead of processed ones
        """
        if self.dataUnit:
            self.dataUnit.getSettings().set("ShowOriginal",1)
        self.updateRendering()
        evt.Skip()
    def onSetView(self,evt):
        """
        Method: onSetView
        Created: 22.07.2005, KP
        Description: Set view mode
        """
        item=evt.GetString()
        viewmapping={"+X":(1,0,0,0,0,1),"-X":(-1,0,0,0,0,1),
                     "+Y":(0,1,0,1,0,0),"-Y":(0,-1,0,1,0,0),
                     "+Z":(0,0,1,0,1,0),"-Z":(0,0,-1,0,1,0),
                     "Isometric":(1,1,1,0,0,1)}

        if hasattr(self.currMode,"wxrenwin"):
            self.currMode.wxrenwin.setView(viewmapping[item])
            self.currMode.wxrenwin.Render()
            
    def zoomObject(self,evt):
        """
        Method: zoomObject()
        Created: 19.03.2005, KP
        Description: Lets the user select the part of the object that is zoomed
        """
        self.currMode.zoomObject()

    def addAnnotation(self,event):
        """
        Method: addAnnotation()
        Created: 03.07.2005, KP
        Description: Draw a scale to the visualization
        """
        annclass=None
        eid=event.GetId()
        multiple=0
        if eid==MenuManager.ID_ADD_SCALE:
            annclass=Annotation.ScaleBar
        if eid == MenuManager.ID_ROI_CIRCLE:
            annclass=Annotation.Circle
        elif eid==MenuManager.ID_ROI_RECTANGLE:
            annclass=Annotation.Rectangle
        elif eid==MenuManager.ID_ROI_POLYGON:
            annclass=Annotation.Polygon
            multiple=1
        else:
            Logging.info("BOGUS ANNOTATION SELECTED!",kw="visualizer")
                        
        self.currMode.annotate(annclass,multiple=multiple)
        
    def manageAnnotation(self,event):
        """
        Method: manageAnnotation()
        Created: 04.07.2005, KP
        Description: Manage annotations on the image
        """
        self.currMode.manageAnnotation()
        


    def zoomOut(self,evt):
        """
        Method: zoomOut()
        Created: 19.03.2005, KP
        Description: Makes the zoom factor smaller
        """
        f=self.currMode.getZoomFactor()
        
        n=len(self.zoomLevels)
        for i in range(n-1,0,-1):
            if self.zoomLevels[i]>0 and self.zoomLevels[i]<f:
                level=self.zoomLevels[i]
                Logging.info("Current zoom factor=",f,"setting to",level,kw="visualizer")                
                self.setComboBoxToFactor(level)
                break
        return self.zoomComboDirection(0)
        
    def zoomToComboSelection(self,evt):
        """
        Method: zoomToComboSelection()
        Created: 19.03.2005, KP
        Description: Sets the zoom according to the combo selection
        """
        return self.zoomComboDirection(0)        
        
    def setComboBoxToFactor(self,factor):
        """
        Method: setComboBoxToFactor
        Created: 01.08.2005, KP
        Description: Set the value of the combobox to the correct zoom factor
        """     
        pos=6
        for i,f in enumerate(self.zoomLevels):
            if f == factor:
                pos=i
                break
        self.zoomCombo.SetSelection(pos)
        self.currMode.setZoomFactor(self.zoomLevels[pos])
            
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
        #s=self.zoomCombo.GetString(pos)
        #factor = float(s[:-1])/100.0
        factor=self.zoomLevels[pos]
        self.zoomCombo.SetSelection(pos)
        self.currMode.setZoomFactor(factor)
        if factor==-1:
            self.currMode.zoomToFit()
            
        self.currMode.Render()
        
        
    def zoomIn(self,evt,factor=-1):
        """
        Method: zoomIn()
        Created: 21.02.2005, KP0
        Description: Makes the zoom factor larger 
        """
        f=self.currMode.getZoomFactor()
        n=len(self.zoomLevels)
        for i in range(0,n):
            if self.zoomLevels[i]>f:
                level=self.zoomLevels[i]
                self.setComboBoxToFactor(level)
                break
        return self.zoomComboDirection(0)
        
    def zoomToFit(self,evt):
        """
        Method: zoomToFit()
        Created: 21.02.2005, KP
        Description: Sets the zoom factor to fit the image into the preview window
        """
        self.currMode.zoomToFit()
        self.currMode.Render()
        
    def onSashDrag(self, event=None):
        """
        Method: onSashDrag
        Created: 24.5.2005, KP
        Description: A method for laying out the window
        """        
        print "onSashDrag"
        if event and event.GetDragStatus() == wx.SASH_STATUS_OUT_OF_RANGE:
            Logging.info("Out of range",kw="visualizer")
            return
        w,h=self.sidebarWin.GetSize()
        if event:
            eID = event.GetId()
            newsize=(event.GetDragRect().width,h)
        else:
            eID = MenuManager.ID_VISTREE_WIN
            newsize = self.sidebarWin.origSize

        if eID == MenuManager.ID_VISTREE_WIN:
            Logging.info("Sidebar window size = %d,%d"%newsize,kw="visualizer")
            self.sidebarWin.SetDefaultSize(newsize)
            
            self.sidebarWin.origSize=newsize
        
        #wx.LayoutAlgorithm().LayoutWindow(self.parent, self.visWin)
        self.OnSize(None)        
    def OnSize(self, event=None):
        """
        Method: onSize
        Created: 23.05.2005, KP
        Description: Handle size events
        """
#        if not self.enabled:return
        wx.LayoutAlgorithm().LayoutWindow(self.parent, self.visWin)
        if self.currentWindow:
            self.currentWindow.SetSize(self.visWin.GetClientSize())
            self.currMode.relayout()
                
    def __del__(self):
        global visualizerInstance
        visualizerInstance=None
        
    def reloadModules(self):
        """
        Method: reloadModules()
        Created: 24.05.2005, KP
        Description: Reload all the visualization modules.
        """
        if hasattr(self.currMode,"reloadModules"):
            self.currMode.reloadModules()
        for key in self.modes.keys():
            mod,settingclass,module=self.modes[key]
            module=reload(module)
            print "Reloaded mode ",module
            self.modes[key]=(mod,settingclass,module)
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
        
    def closeVisualizer(self):
        """
        Method: setVisualizationMode
        Created: 12.08.2005, KP
        Description: Close the visualizer
        """
        if self.currMode:
            self.currMode.deactivate()
            self.currentWindow.Show(0)
            self.currMode=None
            self.currentWindow=None
            self.mode=None
            self.currModeModule=None
        self.sidebarWin.SetDefaultSize((0,1024))
        wx.LayoutAlgorithm().LayoutWindow(self.parent, self.visWin)
        self.dataUnit=None
        
        
    def setVisualizationMode(self,mode,reload=0):
        """
        Method: setVisualizationMode
        Created: 23.05.2005, KP
        Description: Set the mode of visualization
        """
        if self.mode == mode:
            Logging.info("Mode %s already selected"%mode,kw="visualizer")
            if self.dataUnit and self.currMode.dataUnit != self.dataUnit:
                Logging.info("Re-setting dataunit",kw="visualizer")
                self.currMode.setDataUnit(self.dataUnit)
                return
        self.mode=mode

        if self.currMode:
            self.currMode.deactivate()
            self.currentWindow.Show(0)
        modeclass,settingclass,module=self.modes[mode]
        modeinst=self.instances[mode]
        if not modeinst or reload:
            modeinst=modeclass(self.visWin,self)
            self.instances[mode]=modeinst
        if not module.showZoomToolbar():
            self.toolWin.SetDefaultSize((500,0))
        else:
            self.toolWin.SetDefaultSize((500,44))
            


        # dataunit might have been changed so set it every time a
        # mode is loaded

        self.currMode=modeinst
        self.currModeModule=module

        self.currentWindow = modeinst.activate(self.sidebarWin)        
        self.sidebarWin.SetDefaultSize((0,1024))
        wx.LayoutAlgorithm().LayoutWindow(self.parent, self.visWin)
        if not modeinst.showSliceSlider():
            if self.zsliderWin.GetSize()[0]:
                self.zsliderWin.SetDefaultSize((0,1024))
        else:
            if self.zsliderWin.GetSize()!=self.zsliderWin.origSize:
                self.zsliderWin.SetDefaultSize(self.zsliderWin.origSize)
            
        if modeinst.showViewAngleCombo():
            self.viewCombo.Enable(1)
#            self.tb.EnableTool(MenuManager.ID_SET_VIEW,1)
        else:
            self.viewCombo.Enable(0)
#            self.tb.EnableTool(MenuManager.ID_SET_VIEW,0)
            
        if not modeinst.showSideBar():
            if self.sidebarWin.GetSize()[0]:
                self.sidebarWin.SetDefaultSize((0,1024))
        else:
            if self.sidebarWin.GetSize()!=self.sidebarWin.origSize:
                self.sidebarWin.SetDefaultSize(self.sidebarWin.origSize)
        wx.LayoutAlgorithm().LayoutWindow(self.parent, self.visWin)
        #self.currentWindow.enable(self.enabled)

        if self.dataUnit and modeinst.dataUnit != self.dataUnit:
            Logging.info("Re-setting dataunit",kw="visualizer")
            modeinst.setDataUnit(self.dataUnit)
        self.currentWindow.Show()        
        if hasattr(self.currMode,"getZoomFactor"):
            self.setComboBoxToFactor(self.currentWindow.getZoomFactor())        
        
        
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
        
        Logging.info("\nenable(%s)\n"%(not not flag),kw="visualizer")
        self.enabled=flag
        if self.currentWindow:
            try:
                self.currentWindow.enable(flag)
            except:
                pass
        if flag:        
           wx.LayoutAlgorithm().LayoutWindow(self.parent, self.visWin)
           Logging.info("Setting visualizer window to ",self.visWin.GetSize(),kw="visualizer")
           self.currentWindow.SetSize(self.visWin.GetClientSize())
        if flag:        
           wx.LayoutAlgorithm().LayoutWindow(self.parent, self.visWin)
           self.currentWindow.SetSize(self.visWin.GetClientSize())

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
        Logging.info("visualizer.setDataUnit(%s)"%str(dataunit),kw="visualizer")
        self.dataUnit = dataunit
        count=dataunit.getLength()
        Logging.info("Setting range to %d"%count,kw="visualizer")
        self.maxTimepoint=count-1
        self.timeslider.SetRange(1,count)
        
        x,y,z=dataunit.getDimensions()
        self.zslider.SetRange(1,z)
        
        showItems=0

        if self.processedMode:
            n=len(dataunit.getSourceDataUnits())
            if n>1:
                showItems=1
        self.showItemToolbar(showItems)
            
        if self.enabled and self.currMode:           
            Logging.info("Setting dataunit to current mode",kw="visualizer")
            self.currMode.setDataUnit(self.dataUnit)
            self.currMode.setTimepoint(self.timepoint)
        if self.histogramIsShowing:
            self.createHistogram()             
            
    def updateRendering(self,event=None,object=None,delay=0):
        """
        Method: updateRendering
        Created: 25.05.2005, KP
        Description: Update the rendering
        """
        Logging.info("Updating rendering",kw="visualizer")
        # If the visualization mode doesn't want immediate rendering
        # then we will delay a bit with this
        imm=self.currModeModule.getImmediateRendering()
        if not imm:
            t=time.time()
            delay = self.currModeModule.getRenderingDelay()/1000.0
            if abs(self.renderingTime-t) < delay: 
                Logging.info("Delaying, delay=%f, diff=%f"%(delay,abs(self.renderingTime-t)),kw="visualizer")
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
            Logging.info("Render()",kw="visualizer")
            self.currMode.Render()
        
    def onSetTimepoint(self,obj,event,tp):
        """
        Method: onSetTimepoint
        Created: 21.06.2005, KP
        Description: Update the timepoint according to an event
        """
        #tp=event.getValue()
        self.setTimepoint(tp)
        
    def onUpdateTimepoint(self,evt=None):
        """
        Method: onUpdateTimepoint
        Created: 31.07.2005, KP
        Description: Set the timepoint to be shown
        """    
        if not evt:
            diff=abs(time.time()-self.changing)
            if diff < 0.01:
                Logging.info("delay too small: ",diff,kw="visualizer")
                wx.FutureCall(200,self.onUpdateTimepoint)
                self.changing=time.time()
                return
        if self.in_vtk:
            Logging.info("In vtk, delaying",kw="visualizer")
            wx.FutureCall(50,lambda e=evt:self.onUpdateTimepoint(evt))
            return
        tp=self.timeslider.GetValue()
        tp-=1 # slider starts from one
        if self.timepoint != tp:
            Logging.info("Sending timepoint change event (tp=%d)"%tp,kw="visualizer")
            messenger.send(None,"timepoint_changed",tp)
            self.setTimepoint(tp)
            
            
    def onChangeTimepoint(self,event):
        """
        Method: onChangeTimepoint
        Created: 28.04.2005, KP
        Description: Set the timepoint to be shown
        """
        self.changing=time.time()
        wx.FutureCall(200,self.onUpdateTimepoint)
        
    def onChangeZSlice(self,obj,event=None,arg=None):
        """
        Method: onChangeZSlice
        Created: 1.08.2005, KP
        Description: Set the z slice to be shown
        """        
        t=time.time()
        if abs(self.depthT-t) < self.updateFactor: return
        self.depthT=time.time()
        if arg:
            newz=arg
        else:
            newz=self.zslider.GetValue()-1
        if self.z != newz:
            self.z=newz
#            print "Sending zslice changed event"
            messenger.send(None,"zslice_changed",newz)        
        
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
        Logging.info("setTimepoint(%d)"%timepoint,kw="visualizer")
        curr=self.timeslider.GetValue()
        if curr-1!=timepoint:
            self.timeslider.SetValue(timepoint+1)
        self.timepoint = timepoint
        if hasattr(self.currentWindow,"setTimepoint"):
            self.currentWindow.setTimepoint(self.timepoint)
        self.currMode.setTimepoint(self.timepoint)
        
