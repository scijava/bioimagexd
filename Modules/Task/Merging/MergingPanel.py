#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: MergingPanel
 Project: BioImageXD
 Created: 10.11.2004, JV
 Description:

 A wxPython Dialog window that is used to control the settings for the
 colocalization module. Expects to be handed a ColorCombinationDataUnit() 
 containing the datasets from which the color combination is generated.
 Uses the PreviewFrame for previewingge.

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

import TaskPanel
import sys

import Dialogs
import time
import vtk


class MergingPanel(TaskPanel.TaskPanel):
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
        TaskPanel.TaskPanel.__init__(self,parent,tb)
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
        TaskPanel.TaskPanel.createButtonBox(self)
        #self.processButton.SetLabel("Do Color Merging")
        self.processButton.Bind(wx.EVT_BUTTON,self.doColorMergingCallback)
        
    def createOptionsFrame(self):
        """
        Method: createOptionsFrame()
        Created: 10.11.2004, JV
        Description: Creates a frame that contains the various widgets
                     used to control the colocalization settings
        """
        TaskPanel.TaskPanel.createOptionsFrame(self)
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
        
        self.settingsNotebook.AddPage(self.editIntensityPanel,"Intensity")
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
                Logging.info("Setting ctf of color button",kw="ctf")
                self.colorBtn.setColorTransferFunction(ctf)
                self.colorBtn.Refresh()
    
            Logging.info("settings=",self.settings,kw="task")
            tf = self.settings.get("IntensityTransferFunction")
            self.intensityTransferEditor.setIntensityTransferFunction(tf)

    def doPreviewCallback(self,event=None):
        """
        Method: doPreviewCallback()
        Created: 23.11.2004, JV
        Description: A callback for the button "Preview" and other events
                     that wish to update the preview
        """
        TaskPanel.TaskPanel.doPreviewCallback(self,event)

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
        Logging.info("Setting alpha mode to ",lst,kw="task")
        #self.dataUnit.setAlphaMode(lst)
        self.settings.set("AlphaMode",lst)

        TaskPanel.TaskPanel.doOperation(self)
        
    def createItemToolbar(self):
        """
        Method: createItemToolbar()
        Created: 31.03.2005, KP
        Description: Method to create a toolbar for the window that allows use to select processed channel
        """      
        n=TaskPanel.TaskPanel.createItemToolbar(self)
        
        merge=vtk.vtkImageMerge()
        
        lst=[]
        for dataunit in self.dataUnit.getSourceDataUnits():
            ctf = dataunit.getColorTransferFunction()
            Logging.info("Adding to toolbar",dataunit,"with ctf",ctf,kw="init")
            maptocol=vtk.vtkImageMapToColors()
            maptocol.SetOutputFormatToRGB()
            maptocol.SetLookupTable(ctf)
            maptocol.SetInput(dataunit.getTimePoint(0))
            maptocol.Update()
            lst.append(maptocol.GetOutput())
        lst.reverse()
        for i in lst:
            merge.AddInput(i)
        merge.Update()
        bmp=ImageOperations.vtkImageDataToPreviewBitmap(merge.GetOutput(),ctf,30,30)
        #dc= wx.MemoryDC()
        #dc.SelectObject(bmp)
        #dc.BeginDrawing()
        #val=[0,0,0]
        #ctf.GetColor(255,val)
        #dc.SetBrush(wx.TRANSPARENT_BRUSH)
        #r,g,b=val
        #r*=255
        #g*=255
        #b*=255
        #dc.SetPen(wx.Pen(wx.Colour(r,g,b),4))
        #dc.DrawRectangle(0,0,32,32)
        #dc.EndDrawing()
        #dc.SelectObject(wx.EmptyBitmap(0,0))
        toolid=wx.NewId()
        n=n+1
        name="Colocalization"
        self.toolMgr.addItem(name,bmp,toolid,lambda e,x=n,s=self:s.selectItem(e,x))
                

    def setCombinedDataUnit(self,dataUnit):
        """
        Method: setCombinedDataUnit(dataUnit)
        Created: 23.11.2004, KP
        Description: Sets the combined dataunit that is to be processed.
                     It is then used to get the names of all the source 
                     data units and they are added to the menu.
        """
        TaskPanel.TaskPanel.setCombinedDataUnit(self,dataUnit)
        # We add entry "Alpha Channel" to the list of channels to allow
        # the user to edit the alpha channel for the 24-bit color merging
        #self.dataUnit.setOpacityTransfer(self.alphaTF)
        self.settings.set("AlphaTransferFunction",self.alphaTF)
        ctf = self.settings.get("MergingColorTransferFunction")
        self.intensityTransferEditor.updateCallback=self.doPreviewCallback

        if self.colorBtn:
            Logging.info("Setting ctf of colorbutton to ",ctf,kw="ctf")
            self.colorBtn.setColorTransferFunction(ctf)
        else:
            Logging.info("No color button to set ctf to ",kw="ctf")
