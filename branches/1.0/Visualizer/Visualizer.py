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
        self.currSliderPanel = None
        self.delayed=0
        self.immediateRender=1
        self.oldClientSize=0
        self.updateFactor = 0.001
        self.depthT=0
        self.zoomToFitFlag=1
        self.zoomFactor=1.0
        self.tb1=None
        self.tb=None
        self.tb2=None
        self.z=0
        self.PitchStep=2
        self.YawStep=2
        self.RollStep=2
        self.ElevationStep=5
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
        #messenger.connect(None,"set_timeslider_value",self.onSetTimeslider)
        #messenger.connect(None,"set_time_range",self.onSetTimeRange)
        messenger.connect(None,"timepoint_changed",self.onSetTimepoint)
        messenger.connect(None,"data_changed",self.updateRendering)
        messenger.connect(None,"itf_update",self.updateRendering)
        self.closed = 0
        self.initialized = 0
        self.renderer=None
        self.dataUnit = None
        self.enabled=1
        self.timepoint = 0
        self.preload=0
        self.processedMode = 0
        self.maxTimepoint = 0
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
        self.toolWin.origSize=(500,44)

        self.toolWin2=wx.SashLayoutWindow(self.parent,MenuManager.ID_TOOL_WIN2,style=wx.NO_BORDER)
        self.toolWin2.SetOrientation(wx.LAYOUT_HORIZONTAL)
        self.toolWin2.SetAlignment(wx.LAYOUT_TOP)
        self.toolWin2.SetSashVisible(wx.SASH_BOTTOM,False)
        self.toolWin2.SetDefaultSize((500,0))
        self.toolWin2.origSize=(500,0)        
        
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
        self.sliderWin.origSize=(500,64)
        
        self.zsliderWin=wx.SashLayoutWindow(self.parent,MenuManager.ID_ZSLIDER_WIN,style=wx.NO_BORDER|wx.SW_3D)
        self.zsliderWin.SetOrientation(wx.LAYOUT_VERTICAL)
        self.zsliderWin.SetAlignment(wx.LAYOUT_RIGHT)
        self.zsliderWin.SetSashVisible(wx.SASH_RIGHT,False)
        self.zsliderWin.SetSashVisible(wx.SASH_LEFT,False)
        self.zsliderWin.SetDefaultSize((32,768))        
        self.zsliderWin.origSize=(32,768)
        #self.zText=wx.StaticText(self.zsliderWin,-1,"Z")
        
        self.createSliders()

        self.currMode=None
        self.currModeModule = None
        self.currentWindow=None
        self.galleryPanel=None
        self.preview=None
        self.sectionsPanel=None
        self.mode = None
        
        self.parent.Bind(wx.EVT_SIZE,self.OnSize)
        
        #wx.FutureCall(50,self.createToolbar)
        self.createToolbar()
        

        
    def createSliders(self):
        """
        Method: createSliders
        Created: 1.08.2005, KP
        Description: Method that creates the sliders 
        """     
        self.sliderPanel=wx.Panel(self.sliderWin,-1)
        self.setCurrentSliderPanel(self.sliderPanel)
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
        style=wx.SL_HORIZONTAL|wx.SL_LABELS|wx.SL_AUTOTICKS)
        self.timeslider.SetHelpText("Use this slider to select the displayed timepoint.")
        self.bindTimeslider(self.onUpdateTimepoint)

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

    def bindTimeslider(self,method,all=0):
        """
        Method: bindTimeslider
        Created: 15.08.2005, KP
        Description: Bind the timeslider to a method
        """     
        if not all and platform.system() in ["Windows","Darwin"]:
            self.timeslider.Unbind(wx.EVT_SCROLL_ENDSCROLL)
            #self.timeslider.Unbind(wx.EVT_SCROLL_THUMBRELEASE)
            self.timeslider.Bind(wx.EVT_SCROLL_ENDSCROLL,method)
            #self.timeslider.Bind(wx.EVT_SCROLL_THUMBRELEASE,method)
        else:
            self.timesliderMethod = method
            self.timeslider.Unbind(wx.EVT_SCROLL)
            self.timeslider.Bind(wx.EVT_SCROLL,self.delayedTimesliderEvent)    
        
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
        if self.tb1:
            self.tb1.Destroy()
        self.tb1 = wx.ToolBar(self.toolWin,-1,style=wx.TB_HORIZONTAL)
        self.tb1.SetToolBitmapSize((32,32))
        
        if self.tb2:
            self.tb2.Destroy()    
        self.tb2 = wx.ToolBar(self.toolWin2,-1,style=wx.TB_HORIZONTAL)
        self.tb2.SetToolBitmapSize((32,32)) 
        
        self.maxWidth=self.parent.GetSize()[0]
        self.currWidth = 64
        self.tb = self.tb1
        toolSize=self.tb.GetToolSize()[0]
        
        
        self.viewCombo=wx.ComboBox(self.tb,MenuManager.ID_SET_VIEW,"Isometric",choices=["+X","-X","+Y","-Y","+Z","-Z","Isometric"],size=(100,-1),style=wx.CB_DROPDOWN)
        self.viewCombo.SetSelection(6)
        self.viewCombo.SetHelpText("This controls the view angle of 3D view mode.")
        self.tb.AddControl(self.viewCombo)

        self.currWidth+=self.viewCombo.GetSize()[0]
        if self.currWidth+toolSize>=self.maxWidth:self.tb=self.tb2
        
        wx.EVT_COMBOBOX(self.parent,MenuManager.ID_SET_VIEW,self.onSetView)
        #self.tb.Realize()                
        self.tb.AddSimpleTool(MenuManager.ID_ZOOM_OUT,wx.Image(os.path.join("Icons","zoom-out.gif"),wx.BITMAP_TYPE_GIF).ConvertToBitmap(),"Zoom out","Zoom out on the optical slice")
        #EVT_TOOL(self,ID_OPEN,self.menuOpen)
        
        self.currWidth+=toolSize
        if self.currWidth+toolSize>=self.maxWidth:self.tb=self.tb2
        
        self.zoomLevels=[0.125, 0.25, 0.3333, 0.5, 0.6667, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0,-1]
        self.zoomCombo=wx.ComboBox(self.tb,MenuManager.ID_ZOOM_COMBO,"Zoom to fit",
                          choices=["12.5%","25%","33.33%","50%","66.67%","75%","100%","125%","150%","200%","300%","400%","600%","800%","Zoom to fit"],size=(100,-1),style=wx.CB_DROPDOWN)
        self.zoomCombo.SetSelection(14)
        self.zoomCombo.SetHelpText("This controls the zoom level of visualization views.")        
        self.tb.AddControl(self.zoomCombo)
        
        self.currWidth+=self.zoomCombo.GetSize()[0]
        if self.currWidth+toolSize>=self.maxWidth:self.tb=self.tb2

        self.tb.AddSimpleTool(MenuManager.ID_ZOOM_IN,wx.Image(os.path.join("Icons","zoom-in.gif"),wx.BITMAP_TYPE_GIF).ConvertToBitmap(),"Zoom in","Zoom in on the slice")
        
        self.currWidth+=toolSize
        if self.currWidth+toolSize>=self.maxWidth:self.tb=self.tb2        
        
        self.tb.AddSimpleTool(MenuManager.ID_ZOOM_TO_FIT,wx.Image(os.path.join("Icons","zoom-to-fit.gif"),wx.BITMAP_TYPE_GIF).ConvertToBitmap(),"Zoom to Fit","Zoom the slice so that it fits in the window")
        
        self.currWidth+=toolSize
        if self.currWidth+toolSize>=self.maxWidth:self.tb=self.tb2
        
        self.tb.AddSimpleTool(MenuManager.ID_ZOOM_OBJECT,wx.Image(os.path.join("Icons","zoom-object.gif"),wx.BITMAP_TYPE_GIF).ConvertToBitmap(),"Zoom object","Zoom user selected portion of the slice")
        
        self.currWidth+=toolSize
        if self.currWidth+toolSize>=self.maxWidth:self.tb=self.tb2
        
        self.tb.AddSeparator()
        self.currWidth+=self.tb.GetToolSeparation()
        
        
        self.tb.AddSimpleTool(MenuManager.ID_DRAG_ANNOTATION,wx.Image(os.path.join("Icons","arrow.gif"),wx.BITMAP_TYPE_GIF).ConvertToBitmap(),"Manage annotations","Manage annotations on the image")
        
        self.currWidth+=toolSize
        if self.currWidth+toolSize>=self.maxWidth:self.tb=self.tb2
        
        bmp = wx.ArtProvider_GetBitmap(wx.ART_DELETE,wx.ART_TOOLBAR, (32,32))
        self.tb.AddSimpleTool(MenuManager.ID_DEL_ANNOTATION,bmp,"Delete annotation","Delete an annotation")
        
        self.currWidth+=toolSize
        if self.currWidth+toolSize>=self.maxWidth:self.tb=self.tb2
        
        self.tb.AddSimpleTool(MenuManager.ID_ADD_SCALE,wx.Image(os.path.join("Icons","scale.gif"),wx.BITMAP_TYPE_GIF).ConvertToBitmap(),"Draw scale","Draw a scale bar on the image")
        
        self.currWidth+=toolSize        
        self.tb.AddSeparator()
        self.currWidth+=self.tb.GetToolSeparation()
        
        if self.currWidth+90>=self.maxWidth:self.tb=self.tb2
       
        self.origBtn=wx.Button(self.tb,MenuManager.ORIG_BUTTON,"Original")
        self.origBtn.SetHelpText("Use this button to show how the unprocessed dataset looks like.")
        self.origBtn.Bind(wx.EVT_LEFT_DOWN,lambda x:self.onShowOriginal(x,1))
        self.origBtn.Bind(wx.EVT_LEFT_UP,lambda x:self.onShowOriginal(x,0))
                
        
        
        self.tb.AddControl(self.origBtn)
        self.currWidth+=self.origBtn.GetSize()[0]
        if self.currWidth+toolSize>=self.maxWidth:self.tb=self.tb2
        
        
 #       self.tb.AddSimpleTool(MenuManager.ID_ROI_CIRCLE,wx.Image(os.path.join("Icons","circle.gif"),wx.BITMAP_TYPE_GIF).ConvertToBitmap(),"Select circle","Select a circular area of the image")
 #       self.tb.AddSimpleTool(MenuManager.ID_ROI_RECTANGLE,wx.Image(os.path.join("Icons","rectangle.gif"),wx.BITMAP_TYPE_GIF).ConvertToBitmap(),"Select rectangle","Select a rectangular area of the image")
 #       self.tb.AddSimpleTool(MenuManager.ID_ROI_POLYGON,wx.Image(os.path.join("Icons","polygon.gif"),wx.BITMAP_TYPE_GIF).ConvertToBitmap(),"Select polygon","Select a polygonal area of the image")

    
        self.pitch=wx.SpinButton(self.tb, MenuManager.PITCH,style=wx.SP_VERTICAL)
        self.tb.AddControl(self.pitch)
        self.currWidth+=self.pitch.GetSize()[0]
        if self.currWidth+toolSize>=self.maxWidth:self.tb=self.tb2
        
        self.yaw=wx.SpinButton(self.tb, MenuManager.YAW,style=wx.SP_VERTICAL)
        self.tb.AddControl(self.yaw)
        self.currWidth+=self.yaw.GetSize()[0]
        if self.currWidth+toolSize>=self.maxWidth:self.tb=self.tb2
        
        self.roll=wx.SpinButton(self.tb, MenuManager.ROLL,style=wx.SP_VERTICAL)
        self.tb.AddControl(self.roll)
        self.currWidth+=self.roll.GetSize()[0]
        if self.currWidth+toolSize>=self.maxWidth:self.tb=self.tb2

        self.elevation=wx.SpinButton(self.tb, -1,style=wx.SP_VERTICAL)
        self.tb.AddControl(self.elevation)
        self.currWidth+=self.roll.GetSize()[0]
        if self.currWidth+toolSize>=self.maxWidth:self.tb=self.tb2        

        
        
        self.pitch.Bind(wx.EVT_SPIN_UP, self.onPitchUp)
        self.pitch.Bind(wx.EVT_SPIN_DOWN, self.onPitchDown)
        self.yaw.Bind(wx.EVT_SPIN_UP, self.onYawUp)
        self.yaw.Bind(wx.EVT_SPIN_DOWN, self.onYawDown)
        self.roll.Bind(wx.EVT_SPIN_UP, self.onRollUp)
        self.roll.Bind(wx.EVT_SPIN_DOWN, self.onRollDown)        
        self.elevation.Bind(wx.EVT_SPIN_UP, self.onElevationUp)
        self.elevation.Bind(wx.EVT_SPIN_DOWN, self.onElevationDown)  
        # Since there will potentially be > 2 MIP items on the toolbar and they should be 
        # in the same toolbar, make sure at least three of them will fit in the toolbar
        if self.currWidth+3*toolSize>=self.maxWidth:self.tb=self.tb2        
        
        wx.EVT_TOOL(self.parent,MenuManager.ID_ZOOM_IN,self.zoomIn)
        wx.EVT_TOOL(self.parent,MenuManager.ID_ZOOM_OUT,self.zoomOut)
        wx.EVT_TOOL(self.parent,MenuManager.ID_ZOOM_TO_FIT,self.zoomToFit)
        wx.EVT_TOOL(self.parent,MenuManager.ID_ZOOM_OBJECT,self.zoomObject)
        wx.EVT_TOOL(self.parent,MenuManager.ID_ADD_SCALE,self.addAnnotation)
        wx.EVT_TOOL(self.parent,MenuManager.ID_DRAG_ANNOTATION,self.manageAnnotation)
        wx.EVT_TOOL(self.parent,MenuManager.ID_DEL_ANNOTATION,self.deleteAnnotation)
#        wx.EVT_TOOL(self.parent,MenuManager.ID_ROI_CIRCLE,self.addAnnotation)
#        wx.EVT_TOOL(self.parent,MenuManager.ID_ROI_RECTANGLE,self.addAnnotation)
#        wx.EVT_TOOL(self.parent,MenuManager.ID_ROI_POLYGON,self.addAnnotation)
        
        self.zoomCombo.Bind(wx.EVT_COMBOBOX,self.zoomToComboSelection)
        self.tb1.Realize()     
        if self.tb == self.tb2:
            self.toolWin2.SetDefaultSize((500,44))
            self.tb2.Realize()
        else:
            self.toolWin2.SetDefaultSize((500,0))
            
        self.viewCombo.Enable(0)
        self.menuManager.restoreItemToolbar() 
        
    def onElevationUp(self,evt):
        if self.mode=="3d":
            self.currMode.getRenderer().GetActiveCamera().Elevation(self.ElevationStep)
            self.currMode.Render()
    def onElevationDown(self,evt):
        if self.mode=="3d":
            self.currMode.getRenderer().GetActiveCamera().Elevation(-self.ElevationStep)
            self.currMode.Render()        
        
    def onPitchUp(self,evt):
        if self.mode=="3d":
            self.currMode.getRenderer().GetActiveCamera().Pitch(self.PitchStep)
            self.currMode.Render()
    def onPitchDown(self,evt):
        if self.mode=="3d":
            self.currMode.getRenderer().GetActiveCamera().Pitch(-self.PitchStep)
            self.currMode.Render()
    def onRollUp(self,evt):
        if self.mode=="3d":
            self.currMode.getRenderer().GetActiveCamera().Roll(self.RollStep)
            self.currMode.Render()
        
    def onRollDown(self,evt):
        if self.mode=="3d":
            self.currMode.getRenderer().GetActiveCamera().Roll(-self.RollStep)
            self.currMode.Render()
    def onYawUp(self,evt):
        if self.mode=="3d":
            self.currMode.getRenderer().GetActiveCamera().Yaw(self.YawStep)    
            self.currMode.Render()
    
    def onYawDown(self,evt):
        if self.mode=="3d":
            self.currMode.getRenderer().GetActiveCamera().Yaw(-self.YawStep)    
            self.currMode.Render()

    def onShowOriginal(self,evt,flag=1):
        """
        Method: onShowOriginal
        Created: 27.07.2005, KP
        Description: Show the original datasets instead of processed ones
        """
        print "flag=",flag
        if evt=="hide":flag=0
        if self.dataUnit:
            self.dataUnit.getSettings().set("ShowOriginal",flag)
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
        self.zoomToFitFlag=0
        self.currMode.zoomObject()
        #self.zoomFactor=self.currMode.getZoomFactor()

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
        
    def deleteAnnotation(self,event):
        """
        Method: deleteAnnotation()
        Created: 04.07.2005, KP
        Description: DElete annotations on the image
        """
        self.currMode.deleteAnnotation()

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
        self.zoomFactor=self.currMode.getZoomFactor()
            
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
        self.zoomFactor=self.currMode.getZoomFactor()    
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
        self.zoomToFitFlag=1
        self.currMode.zoomToFit()
        self.zoomCombo.SetStringSelection("Zoom to fit")
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
        Method: OnSize
        Created: 23.05.2005, KP
        Description: Handle size events
        """
#        if not self.enabled:return
        wx.LayoutAlgorithm().LayoutWindow(self.parent, self.visWin)
        x,y=self.zsliderWin.GetSize()
        x,y2=self.zslider.GetSize()
        self.zslider.SetSize((x,y))
        visSize=self.visWin.GetClientSize()
        # was here
        

        
        newsize=visSize[0]
        if abs(newsize-self.oldClientSize)>10:
            self.createToolbar()
        
        if self.currentWindow:            
            self.currentWindow.SetSize(visSize)
            self.currMode.relayout()
            if self.currMode.layoutTwice() and event:
                wx.CallAfter(self.OnSize)
    
        self.oldClientSize=newsize    
        if self.currSliderPanel:
            self.currSliderPanel.SetSize(self.sliderWin.GetSize())        
        
    def setCurrentSliderPanel(self,p):
        """
        Method: setCurrentSliderPanel
        Created: 26.01.2006, KP
        Description: Set the currently visible timeslider panel
        """    
        self.currSliderPanel=p
        
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
        Method: closeVisualizer
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
        oldmode=self.mode
        if self.mode == mode:
            Logging.info("Mode %s already selected"%mode,kw="visualizer")
            if self.dataUnit and self.currMode.dataUnit != self.dataUnit:
                Logging.info("Re-setting dataunit",kw="visualizer")
                self.currMode.setDataUnit(self.dataUnit)
                return
        self.mode=mode

        if self.currMode:
            self.zoomFactor=self.currMode.getZoomFactor()
            self.currMode.deactivate(self.mode)
            if hasattr(self.currentWindow,"enable"):
                self.currentWindow.enable(0)
            self.currentWindow.Show(0)
        
        modeclass,settingclass,module=self.modes[mode]
        modeinst=self.instances[mode]
        new=0
        if reload:
            del self.instances[mode]
            modeinst=None
            
        if not modeinst:
            modeinst=modeclass(self.visWin,self)
            self.instances[mode]=modeinst
            self.currMode=modeinst
            new=1
            
        if not module.showZoomToolbar():
            self.toolWin.SetDefaultSize((500,0))
            self.toolWin2.SetDefaultSize((500,0))
        else:
            self.toolWin.SetDefaultSize((500,44))
            if self.tb==self.tb2:
                self.toolWin2.SetDefaultSize((500,44))
            


        # dataunit might have been changed so set it every time a
        # mode is loaded

        self.currMode=modeinst
        self.currModeModule=module
        
        
        if mode=="animator":
            self.sliderWin.SetDefaultSize(self.sliderWin.origSize)        

        if self.dataUnit:
            count=self.dataUnit.getLength()
            if count==1:
                self.sliderWin.SetDefaultSize((0,0))
            else:
                self.sliderWin.SetDefaultSize(self.sliderWin.origSize)
            # We restore the time slider if it's not a
            # transition from animator to 3d
            if not ((oldmode=="animator" and mode=="3d") or (mode=="animator" and oldmode=="3d")):
                self.timeslider.SetRange(1,count) 
            else:
                self.sliderWin.SetDefaultSize(self.sliderWin.origSize)        
        # We restore the default binding, but before the activate()
        # call so the mode can still overwrite the timeslider behaviour
        # We restore the time slider if it's not a
        # transition from animator to 3d
        if not ((oldmode=="animator" and mode=="3d") or (mode=="animator" and oldmode=="3d")):
            self.bindTimeslider(self.onUpdateTimepoint)
        else:
            self.sliderWin.SetDefaultSize(self.sliderWin.origSize)        
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
        if self.zoomToFitFlag:
            self.currMode.zoomToFit()
        else:
            self.currMode.setZoomFactor(self.zoomFactor)        
        if not self.zoomToFitFlag and hasattr(self.currMode,"getZoomFactor"):
            self.setComboBoxToFactor(self.currMode.getZoomFactor())        
            
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
        if hasattr(self.currentWindow,"enable"):
            self.currentWindow.enable(1)
#        if self.zoomToFitFlag:
#            self.currMode.zoomToFit()
#        else:
#            self.currMode.setZoomFactor(self.zoomFactor)        
#        if not self.zoomToFitFlag and hasattr(self.currMode,"getZoomFactor"):
#            self.setComboBoxToFactor(self.currMode.getZoomFactor())        
        
        
        
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
        if count==1:
            self.sliderWin.SetDefaultSize((0,0))
        else:
            self.sliderWin.SetDefaultSize(self.sliderWin.origSize)        
        self.timeslider.SetRange(1,count)
        
        x,y,z=dataunit.getDimensions()
        print "Dataset dimensions = ",x,y,z
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
            if self.zoomToFitFlag:
                self.currMode.zoomToFit()
            else:
                self.currMode.setZoomFactor(self.zoomFactor)             

            self.currMode.setTimepoint(self.timepoint)
        if self.histogramIsShowing:
            self.createHistogram()             

        self.OnSize(None)
            
    def setImmediateRender(self,flag):
        """
        Method: setImmediateRender
        Created: 14.02.2006, KP
        Description: Toggle immediate rendering on or off
        """
        self.immediateRender = flag
            
    def updateRendering(self,event=None,object=None,delay=0):
        """
        Method: updateRendering
        Created: 25.05.2005, KP
        Description: Update the rendering
        """
        if not self.enabled:
            Logging.info("Disabled, will not update rendering",kw="visualizer")
            return
            
        print "immediate render=",self.immediateRender,"delay=",delay
        if not self.immediateRender and delay>=0:
            Logging.info("Will not update rendering on other than apply button",kw="visualizer")
            return
            
        Logging.info("Updating rendering",kw="visualizer")
        imm=1
        # If the visualization mode doesn't want immediate rendering
        # then we will delay a bit with this
        # If the delay is negative, then rendering will be immediate
        if delay>=0:
            imm=self.currModeModule.getImmediateRendering()
        delay = self.currModeModule.getRenderingDelay()
        Logging.info("Immediate rendering=",imm,"delay=",delay,kw="visualizer")
        if not imm:
            t=time.time()
            delay/=1000.0
            #Logging.info("diff=",self.renderingTime-t,"delay=",delay)
            #print "self.renderingTime=",self.renderingTime,"t=",t
            if not self.renderingTime:
                self.renderingTime=t-(delay*2)
            diff=t-self.renderingTime
            Logging.info("diff in renderTime=",diff,kw="visualizer")
            if diff < delay and not self.delayed: 
                diff=200+int(1000*diff)
                Logging.info("Delaying, delay=%f, diff=%d"%(delay,diff),kw="visualizer")
                self.delayed=1
                wx.FutureCall(diff,self.updateRendering)
                return
        Logging.info("Updating rendering",kw="visualizer")
        self.renderingTime=time.time()                
        self.currMode.updateRendering()
        self.delayed=0
                        
    def Render(self,evt=None):
        """
        Method: Render()
        Created: 28.04.2005, KP
        Description: Render the scene
        """
        if self.enabled:
            self.currMode.Render()
            
    def onSetTimeRange(self,obj,event,r1,r2):
        """
        Method: onSetTimeRange
        Created: 15.08.2005, KP
        Description: Set the range that the time slider shows
        """        
        self.timeslider.SetRange(r1,r2)
        self.timeslider.Refresh()
        
    def onSetTimepoint(self,obj,event,tp):
        """
        Method: onSetTimepoint
        Created: 21.06.2005, KP
        Description: Update the timepoint according to an event
        """
        #tp=event.getValue()
        self.setTimepoint(tp)

    def onSetTimeslider(self,obj,event,tp):
        """
        Method: onSetTimeslider
        Created: 21.08.2005, KP
        Description: Update the timeslider according to an event
        """
        self.timeslider.SetValue(tp)
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
            
            
    def delayedTimesliderEvent(self,event):
        """
        Method: delayedTimesliderEvent
        Created: 28.04.2005, KP
        Description: Set the timepoint to be shown
        """
        self.changing=time.time()
        wx.FutureCall(200,lambda e=event,s=self:s.timesliderMethod(e))
        
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
        
    def restoreWindowSizes(self):
        """
        Method: restoreWindowSizes
        Created: 15.08.2005, KP
        Description: Restores the window sizes that may be changed by setRenderWIndowSize
        """  
        self.visWin.SetDefaultSize(self.visWin.origSize)
        self.sidebarWin.SetDefaultSize(self.sidebarWin.origSize)
        self.sliderWin.SetDefaultSize(self.sliderWin.origSize)
        self.toolWin.SetDefaultSize(self.toolWin.origSize)
        self.OnSize(None)
        
    def setRenderWindowSize(self,size,taskwin):
        """
        Method: setRenderWindowSize(size)
        Created: 28.04.2005, KP
        Description: Set the render window size
        """  
        x,y=size
        #self.currentWindow.SetSize((size))
        
        currx,curry=self.visWin.GetSize()
        self.visWin.origSize=(currx,curry)
        Logging.info("Current window size=",currx,curry)
        diffx=currx-x
        diffy=curry-y
        Logging.info("Need to modify renderwindow size by ",diffx,",",diffy)#,kw="visualizer")
        sx,sy=self.sidebarWin.GetSize()
        self.sidebarWin.origSize=(sx,sy)
        sx2,sy2=taskwin.GetSize()
        d2=sx2-sx
        if sx2<abs(diffx/2):
            diffx-=sx
            sx2=0
        else:
            d=diffx/2
            d-=(d2/2)
            sx2+=d
            diffx+=-d
        taskwin.SetDefaultSize((sx2,sy2))
        taskwin.parent.OnSize(None)
            
        if sx:
            sx+=diffx
            self.sidebarWin.SetDefaultSize((sx,sy))
            Logging.info("Size of siderbar window after modification=",sx,sy)
        slx,sly=self.sliderWin.GetSize()
        self.sliderWin.origSize=(slx,sly)
        
        if diffy<0 and abs(diffy)>abs(sly):
            Logging.info("Hiding toolbar to get more space in y-direction")#,kw="visualizer")
            tx,ty=self.toolWin.GetSize()
            self.toolWin.origSize=(tx,ty)
            self.toolWin.SetDefaultSize((0,0))
            diffy+=ty
        if diffy:
            Logging.info("I'm told to set renderwindow size to %d,%d with a %d modification of y-size."%(x,y,diffy))#,kw="visualizer")
            
            if diffy < 0 and sly<diffy:
                Logging.info("Giving %d more to y-size is the best I can do"%sy)#,kw="visualizer")
                sly=0
            else:
                sly+=diffy
                Logging.info("Size of slider win after modification=",sx,sy)
            
            self.sliderWin.SetDefaultSize((slx,sly))
        #self.wxrenwin.SetSize((size))
        #self.renwin.SetSize((size))
        self.OnSize(None)
        self.parent.Layout()
        self.parent.Refresh()
        self.currentWindow.Update()
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
        