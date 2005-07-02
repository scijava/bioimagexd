#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: ResliceWindow.py
 Project: BioImageXD
 Created: 04.04.2005, KP
 Description:

 A window for slicing the dataset in various ways
 
                           
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
__version__ = "$Revision: 1.40 $"
__date__ = "$Date: 2005/01/13 14:52:39 $"

import wx

import os.path
import Dialogs

from PreviewFrame import *

import sys
import time

import TaskWindow


class ResliceWindow(TaskWindow.TaskWindow):
    """
    Class: ResliceWindow
    Created: 04.04.2005, KP
    Description: A window for slicing a dataset
    """
    def __init__(self,parent):
        """
        Method: __init__(parent)
        Created: 04.04.2005, KP
        Description: Initialization
        """
        self.timePoint = 0
        self.operationName="Single Dataset Series Processing"
        TaskWindow.TaskWindow.__init__(self,parent)
        
        self.Show()

        self.SetTitle("Reslice dataset")

        self.createToolBar()
        
        self.mainsizer.Layout()
        self.mainsizer.Fit(self.panel)

    def createButtonBox(self):
        """
        Method: createButtonBox()
        Created: 03.11.2004, KP
        Description: Creates a button box containing the buttons Render,
                     Preview and Close
        """
        TaskWindow.TaskWindow.createButtonBox(self)
        
        self.processButton.SetLabel("Process Dataset Series")
        self.processButton.Bind(wx.EVT_BUTTON,self.doProcessingCallback)

    def createOptionsFrame(self):
        """
        Method: createOptionsFrame()
        Created: 03.11.2004
        Creator: KP
        Description: Creates a frame that contains the various widgets
                     used to control the colocalization settings
        """
        TaskWindow.TaskWindow.createOptionsFrame(self)
        self.taskNameLbl.SetLabel("Resliced dataset:")
            
        #controls for filtering

        self.slicePanel=wx.Panel(self.settingsNotebook,-1)
        self.settingsNotebook.AddPage(self.slicePanel,"Slicing")
        
        self.sliceSizer=wx.GridBagSizer()
        
        self.angleLbl=wx.StaticText(self.slicePanel,-1,"Angle of X,Y and Z axis:")
        self.xangle = wx.TextCtrl(self.slicePanel,-1,"0")
        self.yangle = wx.TextCtrl(self.slicePanel,-1,"90")
        self.zangle = wx.TextCtrl(self.slicePanel,-1,"90")
        
        self.sliceSizer.Add(self.angleLbl,(0,0),span=(1,3))
        self.sliceSizer.Add(self.xangle,(1,0))
        self.sliceSizer.Add(self.yangle,(1,1))
        self.sliceSizer.Add(self.zangle,(1,2))
        
        self.slicePanel.SetSizer(self.sliceSizer)
        self.slicePanel.SetAutoLayout(1)


    def timePointChanged(self,event):
        """
        Method: timePointChanged(timepoint)
        Created: 24.11.2004, KP
        Description: A callback that is called when the previewed timepoint
                     changes.
        Parameters:
                event   Event object who'se getValue() returns the timepoint
        """
        timePoint=event.getValue()
        self.timePoint=timePoint

    def updateSettings(self):
        """
        Method: updateSettings()
        Created: 03.11.2004, KP
        Description: A method used to set the GUI widgets to their proper values
        """
        if self.dataUnit:
            pass

    def doProcessingCallback(self,event=None):
        """
        Method: doProcessingCallback()
        Created: 03.11.2004, KP
        Description: A callback for the button "Process Dataset Series"
        """
        TaskWindow.TaskWindow.doOperation(self)

    def doPreviewCallback(self,event=None):
        """
        Method: doPreviewCallback()
        Created: 03.11.2004, KP
        Description: A callback for the button "Preview" and other events
                     that wish to update the preview
        """
        x=float(self.xangle.GetValue())
        y=float(self.yangle.GetValue())
        z=float(self.zangle.GetValue())
        self.settings.set("ResliceXAngle",x)
        self.settings.set("ResliceYAngle",y)
        self.settings.set("ResliceZAngle",z)
        

        TaskWindow.TaskWindow.doPreviewCallback(self,event)

    def setCombinedDataUnit(self,dataUnit):
        """
        Method: setCombinedDataUnit(dataUnit)
        Created: 23.11.2004, KP
        Description: Sets the processed dataunit that is to be processed.
                     It is then used to get the names of all the source data
                     units and they are added to the menu.
                     This is overwritten from taskwindow since we only process
                     one dataunit here, not multiple source data units
        """
        TaskWindow.TaskWindow.setCombinedDataUnit(self,dataUnit)

        # We register a callback to be notified when the timepoint changes
        # We do it here because the timePointChanged() code requires the dataunit
        self.Bind(EVT_TIMEPOINT_CHANGED,self.timePointChanged,id=self.preview.GetId())

        self.updateSettings()
