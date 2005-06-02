#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: ProcessingWindow.py
 Project: BioImageXD
 Created: 31.05.2005, KP
 Description:

 A task window for restoring a dataset. This includes any filtering,
 deblurring, deconvolution etc. 
 
 Modified: 31.05.2005 KP - Split the module from dataunitprocessing
                           
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

import TaskWindow

class RestorationWindow(TaskWindow.TaskWindow):
    """
    Class: RestorationWindow
    Created: 03.11.2004, KP
    Description: A window for restoring a single dataunit
    """
    def __init__(self,parent,tb):
        """
        Method: __init__(parent)
        Created: 03.11.2004, KP
        Description: Initialization
        Parameters:
                root    Is the parent widget of this window
        """
        self.timePoint = 0
        TaskWindow.TaskWindow.__init__(self,parent,tb)
        # Preview has to be generated here
        # self.colorChooser=None
        
        self.Show()
      
        self.mainsizer.Layout()
        self.mainsizer.Fit(self)



    def createButtonBox(self):
        """
        Method: createButtonBox()
        Created: 03.11.2004, KP
        Description: Creates a button box containing the buttons Render,
                     Preview and Close
        """
        TaskWindow.TaskWindow.createButtonBox(self)
        
        #self.processButton.SetLabel("Process Dataset Series")
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
        self.taskNameLbl.SetLabel("Restored dataset series name:")
            
        self.paletteLbl = wx.StaticText(self,-1,"Channel palette:")
        self.commonSettingsSizer.Add(self.paletteLbl,(1,0))
        self.colorBtn = ColorTransferEditor.CTFButton(self)
        self.commonSettingsSizer.Add(self.colorBtn,(2,0))
        
        #controls for filtering

        self.filtersPanel=wx.Panel(self.settingsNotebook,-1)
        self.settingsNotebook.AddPage(self.filtersPanel,"Filtering")
        
        self.filtersSizer=wx.GridBagSizer()
        
        #Median Filtering
        self.doMedianCheckbutton = wx.CheckBox(self.filtersPanel,
        -1,"Median Filtering")
        self.doMedianCheckbutton.Bind(wx.EVT_CHECKBOX,self.doFilterCheckCallback)

        self.neighborhoodX=wx.TextCtrl(self.filtersPanel,-1,"1")
        self.neighborhoodY=wx.TextCtrl(self.filtersPanel,-1,"1")
        self.neighborhoodZ=wx.TextCtrl(self.filtersPanel,-1,"1")


        self.neighborhoodLbl=wx.StaticText(self.filtersPanel,-1,
        "Neighborhood:")
        self.neighborhoodXLbl=wx.StaticText(self.filtersPanel,-1,"X:")
        self.neighborhoodYLbl=wx.StaticText(self.filtersPanel,-1,"Y:")
        self.neighborhoodZLbl=wx.StaticText(self.filtersPanel,-1,"Z:")

        
        self.filtersSizer.Add(self.doMedianCheckbutton,(1,0))
        self.filtersSizer.Add(self.neighborhoodLbl,(2,0))

        self.filtersSizer.Add(self.neighborhoodXLbl,(3,0))
        self.filtersSizer.Add(self.neighborhoodX,(3,1))
        self.filtersSizer.Add(self.neighborhoodYLbl,(4,0))
        self.filtersSizer.Add(self.neighborhoodY,(4,1))
        self.filtersSizer.Add(self.neighborhoodZLbl,(5,0))
        self.filtersSizer.Add(self.neighborhoodZ,(5,1))

        #Solitary Filtering

        self.doSolitaryCheckbutton = wx.CheckBox(self.filtersPanel,
        -1,"Solitary Filtering")
        self.doSolitaryCheckbutton.Bind(wx.EVT_CHECKBOX,self.doFilterCheckCallback)

        self.solitaryX=wx.TextCtrl(self.filtersPanel,-1,"1")
        self.solitaryY=wx.TextCtrl(self.filtersPanel,-1,"1")
        self.solitaryThreshold=wx.TextCtrl(self.filtersPanel,
        -1,"0")

        self.solitaryLbl=wx.StaticText(self.filtersPanel,-1,"Thresholds:")
        self.solitaryXLbl=wx.StaticText(self.filtersPanel,-1,"X:")
        self.solitaryYLbl=wx.StaticText(self.filtersPanel,-1,"Y:")
        self.solitaryThresholdLbl=wx.StaticText(self.filtersPanel,-1,
        "Processing threshold:")

        self.filtersSizer.Add(self.doSolitaryCheckbutton,(6,0))
        self.filtersSizer.Add(self.solitaryLbl,(7,0))
        self.filtersSizer.Add(self.solitaryXLbl,(8,0))
        self.filtersSizer.Add(self.solitaryX,(8,1))
        self.filtersSizer.Add(self.solitaryYLbl,(9,0))
        self.filtersSizer.Add(self.solitaryY,(9,1))

        self.filtersSizer.Add(self.solitaryThresholdLbl,(10,0))
        self.filtersSizer.Add(self.solitaryThreshold,(10,1))
        
        self.filtersPanel.SetSizer(self.filtersSizer)
        self.filtersPanel.SetAutoLayout(1)

    def updateTimepoint(self,event):
        """
        Method: updateTimepoint(event)
        Created: 04.04.2005, KP
        Description: A callback function called when the timepoint is changed
        """
        timePoint=event.getValue()
        self.timePoint=timePoint
 

    def doFilterCheckCallback(self,event=None):
        """
        Method: doFilterCheckCallback(self)
        Created: 14.12.2004, JV
        Description: A callback function called when the neither of the
                     filtering checkbox changes state
        """

        if self.doMedianCheckbutton.GetValue():
            for widget in [self.neighborhoodX,self.neighborhoodY,self.neighborhoodZ,self.neighborhoodXLbl,\
            self.neighborhoodYLbl,self.neighborhoodZLbl]:
                widget.Enable(1)
        else:
            for widget in [self.neighborhoodX,self.neighborhoodY,self.neighborhoodZ,self.neighborhoodXLbl,\
            self.neighborhoodYLbl,self.neighborhoodZLbl]:
                widget.Enable(0)

        if self.doSolitaryCheckbutton.GetValue():
            for widget in [self.solitaryX,self.solitaryY,self.solitaryThreshold,self.solitaryXLbl,self.solitaryYLbl,\
            self.solitaryThresholdLbl]:
                widget.Enable(1)
        else:
            for widget in [self.solitaryX,self.solitaryY,self.solitaryThreshold,self.solitaryXLbl,self.solitaryYLbl,\
            self.solitaryThresholdLbl]:
                widget.Enable(0)

        self.updateFilterData()
        #self.doPreviewCallback()

    def updateSettings(self):
        """
        Method: updateSettings()
        Created: 03.11.2004, KP
        Description: A method used to set the GUI widgets to their proper values
        """

        if self.dataUnit:

            ctf = self.settings.get("ColorTransferFunction")
            if ctf and self.colorBtn:
                print "Setting colorBtn.ctf"
                self.colorBtn.setColorTransferFunction(ctf)
                self.colorBtn.Refresh()
            # median filtering
            #print self.settings
            median=self.settings.get("MedianFiltering")
            
            self.doMedianCheckbutton.SetValue(median)
            #neighborhood=self.dataUnit.getNeighborhood()
            neighborhood=self.settings.get("MedianNeighborhood")
            self.neighborhoodX.SetValue(str(neighborhood[0]))
            self.neighborhoodY.SetValue(str(neighborhood[1]))
            self.neighborhoodZ.SetValue(str(neighborhood[2]))

            # solitary filtering
            #solitary=self.dataUnit.getRemoveSolitary()
            solitary=self.settings.get("SolitaryFiltering")
            solitaryX=self.settings.get("SolitaryHorizontalThreshold")
            solitaryY=self.settings.get("SolitaryVerticalThreshold")
            solitaryThreshold=self.settings.get("SolitaryProcessingThreshold")
            self.doSolitaryCheckbutton.SetValue(solitary)
            self.solitaryX.SetValue(str(solitaryX))
            self.solitaryY.SetValue(str(solitaryY))
            self.solitaryThreshold.SetValue(str(solitaryThreshold))

            self.doFilterCheckCallback()

    def updateFilterData(self):
        """
        Method: updateFilterData()
        Created: 13.12.2004, JV
        Description: A method used to set the right values in dataset
                     from filter GUI widgets
        """

        self.settings.set("MedianFiltering",self.doMedianCheckbutton.GetValue())
        self.settings.set("SolitaryFiltering",self.doSolitaryCheckbutton.GetValue())
        nbh=(self.neighborhoodX.GetValue(),
            self.neighborhoodY.GetValue(),
            self.neighborhoodZ.GetValue())
        nbh=map(int,nbh)
        self.settings.set("MedianNeighborhood",nbh)

        sx,sy,st=0,0,0
        
        try:sx=int(self.solitaryX.GetValue())
        except:pass
        try:sy=int(self.solitaryY.GetValue())
        except:pass
        try:st=int(self.solitaryThreshold.GetValue())
        except:pass
        
        self.settings.set("SolitaryHorizontalThreshold",sx)
        self.settings.set("SolitaryVerticalThreshold",sy)
        self.settings.set("SolitaryProcessingThreshold",st)

    def doProcessingCallback(self,event=None):
        """
        Method: doProcessingCallback()
        Created: 03.11.2004, KP
        Description: A callback for the button "Process Dataset Series"
        """
        self.updateFilterData()
        TaskWindow.TaskWindow.doOperation(self)

    def doPreviewCallback(self,event=None):
        """
        Method: doPreviewCallback()
        Created: 03.11.2004, KP
        Description: A callback for the button "Preview" and other events
                     that wish to update the preview
        """
        # TODO: Validity checks, here or in dataunit

        #print "doMedianVar in window: "
        #print self.doMedianVar.get()
        self.updateFilterData()
        print "Update preview"

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
        
        ctf = self.settings.get("ColorTransferFunction")
        if self.colorBtn:
            print "Setting ctf"
            self.colorBtn.setColorTransferFunction(ctf)
        else:
            print "Won't set ctf!"
        
        # We register a callback to be notified when the timepoint changes
        # We do it here because the timePointChanged() code requires the dataunit
        #self.Bind(EVT_TIMEPOINT_CHANGED,self.timePointChanged,id=ID_TIMEPOINT)

        tf=self.settings.getCounted("IntensityTransferFunctions",self.timePoint)

        self.updateSettings()
