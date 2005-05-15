# -*- coding: iso-8859-1 -*-

"""
 Unit: VisualizationFrame
 Project: BioImageXD
 Created: 28.04.2005, KP
 Description:

 A framework for replacing MayaVi for simple rendering tasks.
 
 Modified 28.04.2005 KP - Created the class
          
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
from vtk.wx.wxVTKRenderWindowInteractor import wxVTKRenderWindowInteractor
from Events import *
import Dialogs
from VisualizationModules import *
from ModuleConfiguration import *
from VisualizerWindow import *
from Lights import *

visualizerInstance=None

def getVisualizer():
    global visualizerInstance
    return visualizerInstance

class ConfigurationPanel(wx.Panel):
    """
    Class: ConfigurationPanel
    Created: 28.04.2005, KP
    Description: A panel that can be used to configure the rendering
    """
    def __init__(self,parent,visualizer,**kws):
        """
        Method: __init__(parent)
        Created: 28.04.2005, KP
        Description: Initialization
        """
        wx.Panel.__init__(self,parent,-1)
        self.sizer = wx.GridBagSizer()
        self.parent = parent
        self.visualizer = visualizer

        self.moduleLbl = wx.StaticText(self,-1,"Rendering module:")
        self.moduleChoice = wx.Choice(self,-1,choices=["Volume Rendering","Surface Rendering","Orthogonal Slices","Arbitrary Slices"])
        self.moduleChoice.SetSelection(0)
        
        self.moduleListbox = wx.CheckListBox(self,-1)
        self.moduleListbox.Bind(wx.EVT_CHECKLISTBOX,self.onCheckItem)
        self.moduleListbox.Bind(wx.EVT_LISTBOX,self.onSelectItem)
        
        self.moduleLoad = wx.Button(self,-1,"Load")
        self.moduleLoad.Bind(wx.EVT_BUTTON,self.onLoadModule)
        
        self.moduleRemove = wx.Button(self,-1,"Remove")
        self.moduleRemove.Bind(wx.EVT_BUTTON,self.onRemoveModule)
        
        self.lightsBtn = wx.Button(self,-1,"Lights")
        self.lightsBtn.Bind(wx.EVT_BUTTON,self.onConfigureLights)
        

        self.sizer.Add(self.moduleLbl,(0,0))
        self.sizer.Add(self.moduleChoice,(1,0))
        self.sizer.Add(self.moduleListbox,(2,0))
        
        
        box=wx.BoxSizer(wx.HORIZONTAL)
        self.configureBtn = wx.Button(self,-1,"Configure")
        self.configureBtn.Bind(wx.EVT_BUTTON,self.onConfigureModule)
  
        box.Add(self.moduleLoad)
        box.Add(self.moduleRemove)
        self.sizer.Add(box,(3,0))
        box2=wx.BoxSizer(wx.HORIZONTAL)
        box2.Add(self.configureBtn)
        box2.Add(self.lightsBtn)
        self.sizer.Add(box2,(4,0))
        self.selected = -1
        
        #self.sizer.Add(self.configureBtn,(3,0))
        
        
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)
        
    def onSelectItem(self,event):
        """
        Method: onSelectItem
        Created: 15.05.2005, KP
        Description: Select a module
        """
        self.selected = event.GetSelection()
        
        
    def onCheckItem(self,event):
        """
        Method: onCheckItem
        Created: 15.05.2005, KP
        Description: Enable / Disable a module
        """
        index = event.GetSelection()
        lbl = self.moduleListbox.GetString(index)
        status=self.moduleListbox.IsChecked(index)
        print "Setting rendering of %s to %s"%(lbl,status)
        self.visualizer.setRenderingStatus(lbl,status)

    def onConfigureLights(self,event):
        """
        Method: onConfigureLights
        Created: 29.04.2005, KP
        Description: Configure the lights
        """
        ren=self.visualizer.getRenderer()
        lm = LightManager(self, self.visualizer.wxrenwin, ren, mode='raymond')
        lm.config()


    def onLoadModule(self,event):
        """
        Method: onLoadModule
        Created: 28.04.2005, KP
        Description: Load the selected module
        """
        lbl = self.moduleChoice.GetStringSelection()
        self.visualizer.loadModule(lbl)
        n=self.moduleListbox.GetCount()
        self.moduleListbox.InsertItems([lbl],n)
        self.moduleListbox.Check(n)

    def onRemoveModule(self,event):
        """
        Method: onRemoveModule
        Created: 03.05.2005, KP
        Description: Remove the selected module
        """
        if self.selected == -1:
            Dialogs.showerror(self,"You have to select a module to be removed","No module selected")
            return
        lbl=self.moduleListbox.GetString(self.selected)
        self.visualizer.removeModule(lbl)
        self.moduleListBox.Delete(self.selected)
        self.selected=-1


    def onConfigureModule(self,event):
        """
        Method: onConfigureModule
        Created: 28.04.2005, KP
        Description: Load the selected module
        """            
        if self.selected ==-1:
            Dialogs.showerror(self,"You have to select a module to be configured","No module selected")
            return
        lbl =self.moduleListbox.GetString(self.selected)
        self.visualizer.configureModule(lbl)        



class VisualizationFrame(wx.Frame):
    """
    Class: VisualizationFrame
    Created: 28.04.2005, KP
    Description: A window for showing 3D visualizations
    """
    def __init__(self,parent,**kws):
        """
        Method: __init__(parent)
        Created: 28.04.2005, KP
        Description: Initialization
        """
        wx.Frame.__init__(self,parent,-1,"BioImageXD Visualization",**kws)

class Visualizer:
    """
    Class: Visualizer
    Created: 05.04.2005, KP
    Description: A class that is the controller for the visualization
    """
    def __init__(self,parent,**kws):
        """
        Method: __init__(parent)
        Created: 28.04.2005, KP
        Description: Initialization
        """
        global visualizerInstance
        visualizerInstance=self

        self.parent = parent
        self.closed = 0
        self.initialized = 0
        self.renderer=None
        self.dataUnit = None
        self.timepoint = -1
        self.mapping= {"Volume Rendering":(VolumeModule,VolumeConfiguration),
                       "Surface Rendering":(SurfaceModule,SurfaceConfiguration),
                       "Orthogonal Slices":(ImagePlaneModule,ImagePlaneConfiguration),
                       "Arbitrary Slices":(ArbitrarySliceModule,ImagePlaneConfiguration)

                       }
        self.modules = []
        self.sizer = wx.GridBagSizer()
        self.wxrenwin = VisualizerWindow(self.parent,size=(512,512))
        self.wxrenwin.Render()

        self.GetRenderWindow=self.wxrenwin.GetRenderWindow
        self.renwin=self.wxrenwin.GetRenderWindow()

        self.wxrenwin.Render()

        self.getRenderer=self.GetRenderer=self.wxrenwin.getRenderer

        self.configPanel = ConfigurationPanel(self.parent,self)
        self.sizer.Add(self.configPanel,(0,0),flag=wx.EXPAND|wx.TOP|wx.BOTTOM)

        self.sizer.Add(self.wxrenwin,(0,1),flag=wx.EXPAND|wx.ALL)
        self.timeslider=wx.Slider(self.parent,value=0,minValue=0,maxValue=1,
        style=wx.SL_HORIZONTAL|wx.SL_AUTOTICKS|wx.SL_LABELS)
        self.sizer.Add(self.timeslider,(1,0),flag=wx.EXPAND|wx.LEFT|wx.RIGHT,span=(1,2))
        self.timeslider.Bind(wx.EVT_SCROLL,self.onChangeTimepoint)

        self.parent.SetSizer(self.sizer)
        self.parent.SetAutoLayout(1)
        self.sizer.Fit(self.parent)

    def __del__(self):
        global visualizerInstance
        visualizerInstance=None

    def onClose(self,event):
        """
        Method: onClose()
        Created: 28.04.2005, KP
        Description: Called when this window is closed
        """
        self.closed = 1

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
        
    def getModules(self):
        """
        Method: getModules()
        Created: 28.04.2005, KP
        Description: Return the modules
        """  
        return self.modules
        
    def Render(self):
        """
        Method: Render()
        Created: 28.04.2005, KP
        Description: Render the scene
        """
        #self.renwin.Render()
        self.wxrenwin.Render()
        #self.wxrenwin.Refresh()

    def configureModule(self,name):
        """
        Method: configureModule(name)
        Created: 28.04.2005, KP
        Description: Configure a visualization module
        """
        conf = self.mapping[name][1](self)
        conf.Show()

    def removeModule(self,name):
        """
        Method: removeModule(name)
        Created: 28.04.2005, KP
        Description: Remove a visualization module
        """
        
        to_be_removed=[]
        for module in self.modules:
            if module.getName()==name:
                to_be_removed.append(module)
        for module in to_be_removed:
            print "Removing module ",module
            module.disableRendering()
            self.modules.remove(module)
            del module
            
    def setRenderingStatus(self,name,status):
        """
        Method: setRenderingStatus(name,status)
        Created: 15.05.2005, KP
        Description: Enable / disable rendering of a module
        """
        for module in self.modules:
            if module.getName()==name:
                if not status:
                    module.disableRendering()
                else:
                    module.enableRendering()

    def loadModule(self,name):
        """
        Method: loadModule(name)
        Created: 28.04.2005, KP
        Description: Load a visualization module
        """
        if not self.dataUnit:
            Dialogs.showerror(self,"No dataset has been loaded for visualization","Cannot load visualization module")
            return
        self.wxrenwin.initializeVTK()
        module = self.mapping[name][0](self)
        self.modules.append(module)
        module.setDataUnit(self.dataUnit)
        module.showTimepoint(self.timepoint)
        
    def onChangeTimepoint(self,event):
        """
        Method: onChangeTimepoint
        Created: 28.04.2005, KP
        Description: Set the timepoint to be shown
        """
        tp=self.timeslider.GetValue()
        if self.timepoint != tp:
            self.setTimepoint(tp)

    def setRenderWindowSize(self,size):
        """
        Method: setRenderWindowSize(size)
        Created: 28.04.2005, KP
        Description: Set the render window size
        """  
        self.wxrenwin.SetSize((size))
        self.renwin.SetSize((size))
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
        for module in self.modules:
            module.showTimepoint(self.timepoint)
