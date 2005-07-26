# -*- coding: iso-8859-1 -*-
"""
 Unit: Simple
 Project: BioImageXD
 Created: 28.04.2005, KP
 Description:

 A view for Visualizer that shows a simple preview of the data
          
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
import DataUnit

import Logging
import vtk
import wx
import wx.lib.scrolledpanel as scrolled
from Visualizer.VisualizationMode import VisualizationMode

import Visualizer.VisualizerWindow as VisualizerWindow

import Modules

def getName():return "simple"
def getClass():return SimpleMode
def getImmediateRendering(): return False
def getConfigPanel(): return None
def getRenderingDelay(): return 500
def showZoomToolbar(): return True
    
class SimpleConfigurationPanel(scrolled.ScrolledPanel):
    """
    Class: SimpleConfigurationPanel
    Created: 21.07.2005, KP
    Description: A panel that can be used to configure MIP view
    """
    def __init__(self,parent,visualizer,mode,**kws):
        """
        Method: __init__(parent)
        Created: 28.04.2005, KP
        Description: Initialization
        """
        scrolled.ScrolledPanel.__init__(self,parent,-1,size=(200,500))    
        self.visualizer=visualizer
        self.mode=mode
    
        self.sizer=wx.GridBagSizer()
        self.radiobox=wx.RadioBox(self,-1,"View data",
        choices=["Fixed","Rotate"],majorDimension=2,
        style=wx.RA_SPECIFY_COLS
        )
        self.okbutton=wx.Button(self,-1,"Select")
        self.okbutton.Bind(wx.EVT_BUTTON,self.onSetViewMode)
        self.sizer.Add(self.radiobox,(0,0))
        
        self.sizer.Add(self.okbutton,(1,0))
        
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.SetupScrolling()

        
    def onSetViewMode(self,event):
        """
        Method: onSetViewMode
        Created: 21.07.2005, KP
        Description: Configure whether to show timepoints or slices
        """       
        pos=self.radiobox.GetSelection()
        self.mode.setRenderedMode(pos)

    
class SimpleMode(VisualizationMode):
    def __init__(self,parent,visualizer):
        """
        Method: __init__
        Created: 24.05.2005, KP
        Description: Initialization
        """
        VisualizationMode.__init__(self,parent,visualizer)
        self.configPanel=None
        self.renderedMode=0
        self.module=None
        self.wxrenwin=None
        self.mapping=Modules.DynamicLoader.getRenderingModules()

    def setRenderedMode(self,mode):
        """
        Method: setRenderedMode
        Created: 22.07.2005, KP
        Description: Set the method of visualization
        """
        self.iren = iren = self.GetRenderWindow().GetInteractor()
        if mode:
            self.iren.Enable()
        else:
            self.wxrenwin.setView((0,0,1,0,1,0))
            self.visualizer.viewCombo.SetSelection(4)
            self.iren.Disable()
            self.Render()
        
    def showSideBar(self):
        """
        Method: showSideBar()
        Created: 24.05.2005, KP
        Description: Method that is queried to determine whether
                     to show the sidebar
        """
        return True
  
    def enable(self,flag):
        """
        Method: enable(flag)
        Created: 02.06.2005, KP
        Description: Enable/Disable updates
        """
        self.enabled=flag        
        
    def zoomObject(self):
        """
        Method: zoomObject()
        Created: 04.07.2005, KP
        Description: Zoom to a user selected portion of the image
        """            
        self.wxrenwin.zoomToRubberband()        
        
    def Render(self):
        """
        Method: Render()
        Created: 24.05.2005, KP
        Description: Update the rendering
        """      
        self.wxrenwin.Render()              
      
             
    def deactivate(self):
        """
        Method: deactivate()
        Created: 22.07.2005, KP
        Description: Unset the mode of visualization
        """
        if self.wxrenwin:
            self.wxrenwin.Show(0)       
        self.configPanel.Show(0) 
        
        
    def updateRendering(self):
        """
        Method: updateRendering
        Created: 26.05.2005, KP
        Description: Update the rendering
        """      
        if not self.enabled:
            Logging.info("Visualizer is disabled, won't update simple view",kw="visualizer")
            return
        Logging.info("Updating simple view",kw="visualizer")
        self.module.showTimepoint(self.timepoint)        
    def setTimepoint(self,tp):
        """
        Method: setTimepoint
        Created: 25.05.2005, KP
        Description: Set the timepoint to be visualized
        """
        self.timepoint=tp
        self.module.showTimepoint(self.timepoint)
        
  
    def activate(self,sidebarwin):
        """
        Method: activate()
        Created: 24.05.2005, KP
        Description: Set the mode of visualization
        """
        self.sidebarWin=sidebarwin
        if not self.wxrenwin:
            self.wxrenwin = VisualizerWindow.VisualizerWindow(self.parent,size=(512,512))
            self.wxrenwin.Render()
            self.GetRenderWindow=self.wxrenwin.GetRenderWindow
            self.renwin=self.wxrenwin.GetRenderWindow()
    
            self.wxrenwin.Render()
    
            self.getRenderer=self.GetRenderer=self.wxrenwin.getRenderer        
        print "configPanel=",self.configPanel
        if not self.configPanel:
            # When we embed the sidebar in a sashlayoutwindow, the size
            # is set correctly
            print "Showing configPanel"
            self.container = wx.SashLayoutWindow(self.sidebarWin)

            self.configPanel = SimpleConfigurationPanel(self.container,self.visualizer,self)
            if self.dataUnit:
                self.configPanel.setDataUnit(self.dataUnit)
            self.configPanel.Show()
        else:
            self.configPanel.Show()
        return self.wxrenwin
        

        
    def setDataUnit(self,dataUnit):
        """
        Method: setDataUnit
        Created: 25.05.2005, KP
        Description: Set the dataunit to be visualized
        """
        VisualizationMode.setDataUnit(self,dataUnit)

        self.wxrenwin.initializeVTK()
        if not self.module:
            self.module = self.mapping["Volume Rendering"][0](self,self.visualizer,label="Volume")
            self.module.setMethod(2)
            otf=vtk.vtkPiecewiseFunction()
            otf.AddPoint(0, 0.0)
            otf.AddPoint(255, 1.0)
            self.module.setOpacityTransferFunction(otf)
        self.module.setDataUnit(self.dataUnit)
        self.module.showTimepoint(self.timepoint)
        self.setRenderedMode(0)

    def saveSnapshot(self,filename):
        """
        Method: saveSnapshot(filename)
        Created: 05.06.2005, KP
        Description: Save a snapshot of the scene
        """      
        self.wxrenwin.save_screen(filename)
        
