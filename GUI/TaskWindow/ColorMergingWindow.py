#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: ColorMergingWindow
 Project: BioImageXD
 Created: 10.11.2004, JV
 Description:

 A wxPython Dialog window that is used to control the settings for the
 colocalization module. Expects to be handed a ColorCombinationDataUnit() 
 containing the datasets from which the color combination is generated.
 Uses the PreviewFrame for previewingge.

 Modified from ColocalizationWindow.py.

 Modified:  28.01.2005 KP - Changed the class over to wxPython
            02.02.2005 KP - Converted the class to use a notebook

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
__version__ = "$Revision: 1.28 $"
__date__ = "$Date: 2005/01/13 14:52:39 $"

import os.path

from PreviewFrame import *
from IntensityTransferEditor import *
from Logging import *

import TaskWindow
import sys
import ColorMerging

import Dialogs
import time
import vtk


class ColorMergingWindow(TaskWindow.TaskWindow):
    """
    Class: ColorMergingWindow
    Created: 10.11.2004, JV
    Description: A window for controlling the settings of the color
                 combination module
    """
    def __init__(self,parent,tb):
        """
        Method: __init__(parent)
        Created: 10.11.2004, JV
        Description: Initialization
        Parameters:
                parent    Is the parent widget of this window
        """
        self.alphaTF=vtk.vtkIntensityTransferFunction()
        self.operationName="Color Merging"
        TaskWindow.TaskWindow.__init__(self,parent,tb)
        self.SetTitle("Color Merging")

        
        self.oldBg=self.GetBackgroundColour()
        
        self.mainsizer.Layout()
        self.mainsizer.Fit(self)

    def createButtonBox(self):
        """
        Method: createButtonBox()
        Created: 10.11.2004, JV
        Description: Creates a button box containing the buttons Render,
                     Preview and Close
        """
        TaskWindow.TaskWindow.createButtonBox(self)
        #self.processButton.SetLabel("Do Color Merging")
        self.processButton.Bind(wx.EVT_BUTTON,self.doColorMergingCallback)
        
    def createOptionsFrame(self):
        """
        Method: createOptionsFrame()
        Created: 10.11.2004, JV
        Description: Creates a frame that contains the various widgets
                     used to control the colocalization settings
        """
        TaskWindow.TaskWindow.createOptionsFrame(self)
        self.taskNameLbl.SetLabel("Merged dataset name:")

        self.paletteLbl = wx.StaticText(self,-1,"Channel palette:")
        self.commonSettingsSizer.Add(self.paletteLbl,(1,0))
        self.colorBtn = ColorTransferEditor.CTFButton(self)
        self.commonSettingsSizer.Add(self.colorBtn,(2,0))

        self.editIntensityPanel=wx.Panel(self.settingsNotebook,-1)
        self.editIntensitySizer=wx.GridBagSizer()
        
        self.intensityTransferEditor=IntensityTransferEditor(self.editIntensityPanel)
        self.editIntensitySizer.Add(self.intensityTransferEditor,(0,0),span=(1,2))        

        self.box=wx.BoxSizer(wx.HORIZONTAL)
        self.editIntensitySizer.Add(self.box,(3,0))
        
        self.restoreBtn=wx.Button(self.editIntensityPanel,-1,"Reset defaults")
        self.restoreBtn.Bind(wx.EVT_BUTTON,self.intensityTransferEditor.restoreDefaults)
        self.box.Add(self.restoreBtn)
        
        self.resetBtn=wx.Button(self.editIntensityPanel,-1,"Reset all timepoints")
        self.resetBtn.Bind(wx.EVT_BUTTON,self.resetTransferFunctions)
        self.box.Add(self.resetBtn)

        self.copyiTFBtn=wx.Button(self.editIntensityPanel,-1,"Copy to all timepoints")
        #self.copyiTFBtn.Bind(wx.EVT_BUTTON,self.copyTransferFunctionToAll)
        self.box.Add(self.copyiTFBtn)        
        
        
        self.editIntensityPanel.SetSizer(self.editIntensitySizer)
        self.editIntensityPanel.SetAutoLayout(1)
        self.settingsNotebook.InsertPage(1,self.editIntensityPanel,"Intensity Transfer Function")

        
        self.editIntensityPanel.Layout()
        self.editIntensitySizer.Fit(self.editIntensityPanel)

        self.editAlphaPanel=wx.Panel(self.settingsNotebook,-1)
        self.editAlphaSizer=wx.GridBagSizer()
        
        self.alphaEditor=IntensityTransferEditor(self.editAlphaPanel)
        self.alphaEditor.setIntensityTransferFunction(self.alphaTF)
        self.alphaEditor.setAlphaMode(1)
        self.editAlphaSizer.Add(self.alphaEditor,(0,0),span=(1,2))        
        
        self.alphaModeBox=wx.RadioBox(self.editAlphaPanel,-1,"Alpha mode",
        choices=["Maximum Mode","Average Mode","Image Luminance"],majorDimension=2,style=wx.RA_SPECIFY_COLS)
        
        self.editAlphaSizer.Add(self.alphaModeBox,(1,0))
        self.alphaModeBox.Bind(wx.EVT_RADIOBOX,self.modeSelect)
        
        self.averageLbl=wx.StaticText(self.editAlphaPanel,-1,"Average Threshold:")
        self.averageEdit=wx.TextCtrl(self.editAlphaPanel,-1,"",size=(150,-1))
        self.averageEdit.Enable(0)
        
        box=wx.BoxSizer(wx.HORIZONTAL)
        box.Add(self.averageLbl)
        box.Add(self.averageEdit)
        self.editAlphaSizer.Add(box,(2,0))
        self.editAlphaPanel.SetSizer(self.editAlphaSizer)
        self.editAlphaSizer.Fit(self.editAlphaPanel)
        
        self.settingsNotebook.AddPage(self.editAlphaPanel,"Alpha Channel")
        
#        self.optionssizer.Add(self.intensityTransferEditor,(3,0))

    def modeSelect(self,event):
        """
        Method: modeSelect(event)
        Created: 21.03.2005, KP
        Description: A method that is called when the selection of alpha mode is chan ged
        """
        mode = event.GetInt()
        if mode == 1:
            self.averageEdit.Enable(1)
        else:
            self.averageEdit.Enable(0)

    def resetTransferFunctions(self,event=None):
        """
        Method: resetTransferFunctions()
        Created: 30.11.2004, KP
        Description: A method to reset all the intensity transfer functions
        """
        dataunits = self.dataUnit.getSourceDataUnits()
        for unit in dataunits:
            setting=unit.getSettings()
            itf = vtk.vtkIntensityTransferFunction()
            setting.set("IntensityTransferFunction",itf)


    def updateSettings(self):
        """
        Method: updateSettings()
        Created: 10.11.2004, JV
        Description: A method used to set the GUI widgets to their proper values
                     based on the selected channel, the settings of which are 
                     stored in the instance variable self.configSetting
        """
        if self.dataUnit and self.settings:
            ctf = self.settings.get("MergingColorTransferFunction")
            if ctf and self.colorBtn:
                print "Setting colorBtn.ctf"
                self.colorBtn.setColorTransferFunction(ctf)
                self.colorBtn.Refresh()

            tf = self.settings.get("IntensityTransferFunction")
            self.intensityTransferEditor.setIntensityTransferFunction(tf)

    def doPreviewCallback(self,event=None):
        """
        Method: doPreviewCallback()
        Created: 23.11.2004, JV
        Description: A callback for the button "Preview" and other events
                     that wish to update the preview
        """
        TaskWindow.TaskWindow.doPreviewCallback(self,event)

    def doColorMergingCallback(self,event):
        """
        Method: doColorMergingCallback()
        Created: 10.11.2004, JV
        Description: A callback for the button "Do color combination"
        """
        method=self.alphaModeBox.GetSelection()
        val=0
        if method == 1:
            val=int(self.averageEdit.GetValue())
        lst=[method,val]
        print "Setting alpha mode to",lst
        #self.dataUnit.setAlphaMode(lst)
        self.settings.set("AlphaMode",lst)

        TaskWindow.TaskWindow.doOperation(self)

    def setCombinedDataUnit(self,dataUnit):
        """
        Method: setCombinedDataUnit(dataUnit)
        Created: 23.11.2004
        Creator: KP
        Description: Sets the combined dataunit that is to be processed.
                     It is then used to get the names of all the source 
                     data units and they are added to the menu.
        """
        TaskWindow.TaskWindow.setCombinedDataUnit(self,dataUnit)
        # We add entry "Alpha Channel" to the list of channels to allow
        # the user to edit the alpha channel for the 24-bit color merging
        #self.dataUnit.setOpacityTransfer(self.alphaTF)
        self.settings.set("AlphaTransferFunction",self.alphaTF)
        ctf = self.settings.get("MergingColorTransferFunction")
        if self.colorBtn:
            print "Setting ctf"
            self.colorBtn.setColorTransferFunction(ctf)
        else:
            print "Won't set ctf!"        
