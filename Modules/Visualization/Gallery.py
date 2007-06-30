# -*- coding: iso-8859-1 -*-
"""
 Unit: Gallery
 Project: BioImageXD
 Created: 28.04.2005, KP
 Description:

 A gallery view for Visualizer
          
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

import PreviewFrame
import Logging
import DataUnit
import wx
import wx.lib.scrolledpanel as scrolled
from Visualizer.VisualizationMode import VisualizationMode

def getName():return "gallery"
def isDefaultMode(): return 0    
def getShortDesc(): return "Gallery view"
def getDesc(): return "Show the dataset as a gallery of slices"    
def getIcon(): return "view_gallery.jpg"
    
def getToolbarPos(): return 1
    
    
def showInfoWindow(): return 1
def showFileTree(): return 1 
def showSeparator(): return (0,0) 

def getClass():return GalleryMode
def getImmediateRendering(): return False
def getConfigPanel(): return None
def getRenderingDelay(): return 2000
def showZoomToolbar(): return True
    
class GalleryConfigurationPanel(scrolled.ScrolledPanel):
    """
    Created: 21.07.2005, KP
    Description: A panel that can be used to configure gallery view
    """
    def __init__(self,parent,visualizer,mode,**kws):
        """
        Created: 28.04.2005, KP
        Description: Initialization
        """
        scrolled.ScrolledPanel.__init__(self,parent,-1,size=(200,500))    
        self.visualizer=visualizer
        self.mode=mode
    
        #self.box=wx.StaticBox(self,-1,"Show gallery")
        #self.sizer=wx.StaticBoxSizer(self.box,wx.VERTICAL)
        self.sizer=wx.GridBagSizer()
        self.radiobox=wx.RadioBox(self,-1,"View in gallery",
        choices=["Slices","Timepoints"],majorDimension=2,
        style=wx.RA_SPECIFY_COLS
        )
        z=1
        if visualizer.dataUnit:
            x,y,z=visualizer.dataUnit.getDimensions()
#        self.zslider=wx.Slider(self,value=0,minValue=0,maxValue=z-1,
#        style=wx.SL_HORIZONTAL|wx.SL_AUTOTICKS|wx.SL_LABELS)
        #self.zslider.Bind(wx.EVT_SCROLL,self.onChangeTimepoint)

        self.okbutton=wx.Button(self,-1,"Update")
        self.okbutton.Bind(wx.EVT_BUTTON,self.onSetViewMode)
        self.sizer.Add(self.radiobox,(0,0))
 #       self.sizer.Add(self.zslider,(1,0),flag=wx.EXPAND|wx.LEFT|wx.RIGHT)
        self.sizer.Add(self.okbutton,(2,0))
        
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.SetupScrolling()

         
    def setDataUnit(self,dataUnit):
        """
        Created: 21.07.2005, KP
        Description: Set the dataunit
        """       
        x,y,z=dataUnit.getDimensions()
        #self.zslider.SetRange(0,z-1)
        #w,h2=self.GetSize()
        #w2,h=self.zslider.GetSize()
        #self.zslider.SetSize((w,h))
        #self.Layout()
        
    def onSetViewMode(self,event):
        """
        Created: 21.07.2005, KP
        Description: Configure whether to show timepoints or slices
        """       
        pos=self.radiobox.GetSelection()
#        print "Showing timepoints: %s,zslider=%d"%(not not pos,self.zslider.GetValue())
        if pos==0:
            val = self.visualizer.zslider.GetValue()
        else: 
            val = self.visualizer.getTimepoint()
        
        print "setShowTimepoints(",pos,val,")"
        self.mode.galleryPanel.setShowTimepoints(pos,val)

    
class GalleryMode(VisualizationMode):
    def __init__(self,parent,visualizer):
        """
        Created: 24.05.2005, KP
        Description: Initialization
        """
        VisualizationMode.__init__(self,parent,visualizer)
        self.galleryPanel=None
        self.configPanel=None
        
    def updateRendering(self):
        """
        Created: 26.05.2005, KP
        Description: Update the rendering
        """      
        if not self.enabled:
            Logging.info("Visualizer is disabled, won't update gallery",kw="visualizer")
            return
        Logging.info("Updating gallery",kw="visualizer")
        #self.galleryPanel.setTimepoint(self.timepoint)
        #self.galleryPanel.updatePreview()
        #self.galleryPanel.Refresh()
        self.galleryPanel.forceUpdate()
        
    def showSliceSlider(self):
        """
        Created: 29.06.2007 KP
        Description: Method that is queried to determine whether
                     to show the zslider
        """
        return True
        
    def showSideBar(self):
        """
        Created: 24.05.2005, KP
        Description: Method that is queried to determine whether
                     to show the sidebar
        """
        return True  
    def activate(self,sidebarwin):
        """
        Created: 24.05.2005, KP
        Description: Set the mode of visualization
        """
        self.sidebarWin=sidebarwin
        if not self.galleryPanel:
            x,y=self.visualizer.visWin.GetSize()
            self.galleryPanel=PreviewFrame.GalleryPanel(self.parent,self.visualizer,size=(x,y))
            self.iactivePanel=self.galleryPanel
        if not self.configPanel:
            # When we embed the sidebar in a sashlayoutwindow, the size
            # is set correctly
            self.container = wx.SashLayoutWindow(self.sidebarWin)

            self.configPanel = GalleryConfigurationPanel(self.container,self.visualizer,self,size=(x,y))
            if self.dataUnit:
                self.configPanel.setDataUnit(self.dataUnit)
            self.configPanel.Show()
        else:
            self.configPanel.Show()
            self.container.Show()
        return self.galleryPanel
        

    def setDataUnit(self,dataUnit):
        """
        Created: 25.05.2005, KP
        Description: Set the dataunit to be visualized
        """

        VisualizationMode.setDataUnit(self,dataUnit)
        if self.configPanel:
            self.configPanel.setDataUnit(dataUnit)
        
    def deactivate(self,newmode=None):
        """
        Created: 24.05.2005, KP
        Description: Unset the mode of visualization
        """
        self.container.Show(0)
        self.configPanel.Show(0)
        

        
        
