#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: ColorCombinationWindow.py
 Project: Selli
 Created: 10.11.2004
 Creator: JV
 Description:

 A wxPython Dialog window that is used to control the settings for the
 colocalization module. Expects to be handed a ColorCombinationDataUnit() 
 containing the datasets from which the color combination is generated.
 Uses the PreviewFrame for previewing.

 Modified from ColocalizationWindow.py.

 Modified:  11.11.2004 JV - Updated: setColor(), setIntensityCallback(), 
                            updateSettings()
                            Added the TransferWidget

            23.11.2004 JV - Updated to match colocalizationwindow
            03.12.2004 JV - Transferwidget updates when dataset is selected
            07.12.2004 JM - Fixed: Clicking cancel on color selection no longer 
                                   causes exception
                            Fixed: Color selection now shows the current color 
                                   as default
                            Fixed: The default color is now shown in the color 
                                   selection button
            28.01.2005 KP - Changed the class over to wxPython
            02.02.2005 KP - Converted the class to use a notebook

 Selli includes the following persons:
 JH - Juha Hyytiäinen, juhyytia@st.jyu.fi
 JM - Jaakko Mäntymaa, jahemant@cc.jyu.fi
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 JV - Jukka Varsaluoma,varsa@st.jyu.fi

 Copyright (c) 2004 Selli Project.
"""
__author__ = "Selli Project <http://sovellusprojektit.it.jyu.fi/selli/>"
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
from ColorSelectionDialog import *
import time
import vtk


class ColorMergingWindow(TaskWindow.TaskWindow):
    """
    Class: ColorMergingWindow
    Created: 10.11.2004, JV
    Description: A window for controlling the settings of the color
                 combination module
    """
    def __init__(self,parent):
        """
        Method: __init__(parent)
        Created: 10.11.2004, JV
        Description: Initialization
        Parameters:
                parent    Is the parent widget of this window
        """
        self.alphaTF=vtk.vtkIntensityTransferFunction()
        self.operationName="Color Merging"
        TaskWindow.TaskWindow.__init__(self,parent)
        self.SetTitle("Color Merging")

        
        self.oldBg=self.GetBackgroundColour()
        self.createToolBar()                
        self.mainsizer.Layout()
        self.mainsizer.Fit(self.panel)

    def createButtonBox(self):
        """
        Method: createButtonBox()
        Created: 10.11.2004, JV
        Description: Creates a button box containing the buttons Render,
                     Preview and Close
        """
        TaskWindow.TaskWindow.createButtonBox(self)
        self.processButton.SetLabel("Do Color Merging")
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

        self.colorChooser=ColorSelectionDialog(self.commonSettingsPanel,self.setColor)
        self.commonSettingsSizer.Add(self.colorChooser,(1,0))

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
        Created: 30.11.2004
        Creator: KP
        Description: A method to reset all the intensity transfer functions
        """
        pass

    def setColor(self,r,g,b):
        """
        Method: setColor(r,g,b)
        Created: 10.11.2004
        Creator: JV
        Description: A method that sets the color of the selected dataUnit and 
                     updates the preview and Set color-button accordingly
        """
        # We might get called before any channel has been selected. 
        # In that case, do nothing
        if not self.settings:return

        oldrgb=self.settings.get("Color")
            #newrgb=(r,g,b)
        if oldrgb != (r,g,b):
            self.settings.set("Color",(r,g,b))
            self.updateSettings()
            self.doPreviewCallback()

    def updateSettings(self):
        """
        Method: updateSettings()
        Created: 10.11.2004, JV
        Description: A method used to set the GUI widgets to their proper values
                     based on the selected channel, the settings of which are 
                     stored in the instance variable self.configSetting
        """
        if self.dataUnit and self.settings:
            r,g,b=self.settings.get("Color")
            if self.colorChooser:
                self.colorChooser.SetValue(wx.Colour(r,g,b))

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
