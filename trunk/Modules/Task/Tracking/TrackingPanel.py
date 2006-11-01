#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: TrackingPanel
 Project: BioImageXD
 Created: 10.04.2005, KP
 Description:

 A task window for manipulating the dataset with various filters.
                            
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
__version__ = "$Revision: 1.42 $"
__date__ = "$Date: 2005/01/13 14:52:39 $"

import wx

import os.path
import Dialogs

from PreviewFrame import *
from Logging import *

import sys
import time

import TrackingFilters

from GUI import FilterBasedTaskPanel
import UIElements
import string
import scripting
import types


class TrackingPanel(FilterBasedTaskPanel.FilterBasedTaskPanel):
    """
    Created: 03.11.2004, KP
    Description: A window for restoring a single dataunit
    """
    def __init__(self,parent,tb):
        """
        Created: 03.11.2004, KP
        Description: Initialization
        Parameters:
                root    Is the parent widget of this window
        """
        self.timePoint = 0
        self.operationName="Tracking"
        self.filtersModule =  TrackingFilters
        self.trackingFilter = None        
        FilterBasedTaskPanel.FilterBasedTaskPanel.__init__(self,parent,tb)
        # Preview has to be generated here
        # self.colorChooser=None
        self.timePoint = 0
        self.menu = None
        self.currentGUI = None
        self.parser = None
        self.onByDefault = 0
        self.Show()
        self.currentSelected = -1
        
        self.mainsizer.Layout()
        self.mainsizer.Fit(self)
        
        messenger.connect(None,"timepoint_changed",self.updateTimepoint)
        
    def getFilters(self, name):
        """
        Created: 21.07.2006, KP
        Description: Retrieve the filters with the given name
        """   
        return self.filters
        
    def getFilter(self, name, index=0):
        """
        Created: 21.07.2006, KP
        Description: Retrieve the filter with the given name, using optionally an index 
                     if there are more than one filter with the same name
        """   
        return self.filters[0]
        
    def updateTimepoint(self,obj,event,timePoint):
        """
        Created: 27.04.2006, KP
        Description: A callback function called when the timepoint is changed
        """
        self.timePoint=timePoint
        
    def createButtonBox(self):
        """
        Created: 03.11.2004, KP
        Description: Creates a button box containing the buttons Render,
                     Preview and Close
        """
        FilterBasedTaskPanel.FilterBasedTaskPanel.createButtonBox(self)
        
        #self.TrackingButton.SetLabel("Tracking Dataset Series")
        
        messenger.connect(None,"process_dataset",self.doProcessingCallback)       
        
    def createTrackingPanel(self):
        """
        Created: 19.06.2004, KP
        Description: Creates a panel that contains the thresholding tool
        """
        panel = wx.Panel(self.settingsNotebook,-1,size=(200,200))
        sizer = wx.GridBagSizer()
        panel.SetSizer(sizer)
        self.trackingSizer = sizer
        
        
        panel.SetAutoLayout(1)
        
        return panel
        
        

    def createPlottingPanel(self):
        """
        Created: 19.06.2004, KP
        Description: Creates a panel that contains the thresholding tool
        """
        panel = wx.Panel(self.settingsNotebook,-1,size=(200,200))
        sizer = wx.GridBagSizer()
        panel.SetSizer(sizer)
        panel.SetAutoLayout(1)
        return panel

    def createOptionsFrame(self):
        """
        Created: 03.11.2004, KP
        Description: Creates a frame that contains the various widgets
                     used to control the colocalization settings
        """
        FilterBasedTaskPanel.FilterBasedTaskPanel.createOptionsFrame(self)

        self.trackingPanel = self.createTrackingPanel()
        #self.plotPanel = self.createPlottingPanel()
        
        self.settingsNotebook.AddPage(self.trackingPanel,"Track")
        #self.settingsNotebook.AddPage(self.plotPanel,"Plot")
   


    def doFilterCheckCallback(self,event=None):
        """
        Created: 14.12.2004, JV
        Description: A callback function called when the neither of the
                     filtering checkbox changes state
        """
        pass
        
    def updateSettings(self,force=0):
        """
        Created: 03.11.2004, KP
        Description: A method used to set the GUI widgets to their proper values
        """
        pass
        
        
    def doProcessingCallback(self,*args):
        """
        Method: doProcessingCallback()
        Created: 03.11.2004, KP
        Description: A callback for the button "Tracking Dataset Series"
        """
        self.updateFilterData()
        FilterBasedTaskPanel.FilterBasedTaskPanel.doOperation(self)

    def doPreviewCallback(self,event=None,*args):
        """
        Method: doPreviewCallback()
        Created: 03.11.2004, KP
        Description: A callback for the button "Preview" and other events
                     that wish to update the preview
        """
        self.updateFilterData()
        FilterBasedTaskPanel.FilterBasedTaskPanel.doPreviewCallback(self,event)

    def createItemToolbar(self):
        """
        Method: createItemToolbar()
        Created: 16.04.2006, KP
        Description: Method to create a toolbar for the window that allows use to select processed channel
        """      
        # Pass flag force which indicates that we do want an item toolbar
        # although we only have one input channel
        n=FilterBasedTaskPanel.FilterBasedTaskPanel.createItemToolbar(self,force=1)
        for i,tid in enumerate(self.toolIds):
            self.dataUnit.setOutputChannel(i,0)
            self.toolMgr.toggleTool(tid,0)
        
        
        ctf=vtk.vtkColorTransferFunction()
        ctf.AddRGBPoint(0,0,0,0)
        ctf.AddRGBPoint(255,1,1,1)
        imagedata=ImageOperations.getMIP(self.dataUnit.getSourceDataUnits()[0].getTimePoint(0),ctf)
        bmp=ImageOperations.vtkImageDataToWxImage(imagedata)

        bmp=bmp.Rescale(30,30).ConvertToBitmap()
        dc= wx.MemoryDC()

        dc.SelectObject(bmp)
        dc.BeginDrawing()
        val=[0,0,0]
        ctf.GetColor(255,val)
        dc.SetBrush(wx.TRANSPARENT_BRUSH)
        r,g,b=val
        r*=255
        g*=255
        b*=255
        dc.SetPen(wx.Pen(wx.Colour(r,g,b),4))
        dc.DrawRectangle(0,0,32,32)
        dc.EndDrawing()
        #dc.SelectObject(wx.EmptyBitmap(0,0))
        dc.SelectObject(wx.NullBitmap)
        toolid=wx.NewId()
        #n=n+1
        name="Tracking"
        self.toolMgr.addItem(name,bmp,toolid,lambda e,x=n,s=self:s.setPreviewedData(e,x))        
        
        self.toolIds.append(toolid)
        self.dataUnit.setOutputChannel(len(self.toolIds),1)
        self.toolMgr.toggleTool(toolid,1)

    def setCombinedDataUnit(self,dataUnit):
        """
        Created: 23.11.2004, KP
        Description: Sets the the dataunit that is the basis for the trackign.
        """
        FilterBasedTaskPanel.FilterBasedTaskPanel.setCombinedDataUnit(self,dataUnit)
        n=0
        for i,dataunit in enumerate(dataUnit.getSourceDataUnits()):
            dataUnit.setOutputChannel(i,0)
            n=i
        self.dataUnit.setOutputChannel(n+1,1)
        self.updateSettings()

        self.trackingFilter = TrackingFilters.CreateTracksFilter()
        self.filters = [self.trackingFilter]
        self.trackingFilter.setDataUnit(self.dataUnit)
        gui = self.trackingFilter.getGUI(self.trackingPanel, self)
        self.trackingSizer.Add(gui, (0,0), flag=wx.EXPAND|wx.ALL)
        
        self.trackingSizer.Fit(self.trackingPanel)

        print "Adding GUI",gui
        self.Layout()
        self.restoreFromCache()
        
