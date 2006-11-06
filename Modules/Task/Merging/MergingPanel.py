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

 This program is direstributed in the hope that it will be useful,
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

import GUI.IntensityTransferEditor
from GUI.IntensityTransferEditor import *
from Logging import *

from GUI import TaskPanel
from GUI import ColorTransferEditor
import sys

import Dialogs
import time
import vtk


class MergingPanel(TaskPanel.TaskPanel):
    """
    Created: 10.11.2004, JV
    Description: A window for controlling the settings of the color
                 combination module
    """
    def __init__(self,parent,tb):
        """
        Created: 10.11.2004, JV
        Description: Initialization
        Parameters:
                parent    Is the parent widget of this window
        """
        self.alphaTF=vtk.vtkIntensityTransferFunction()
        self.operationName="Merge"
        self.createItemSelection=1
        TaskPanel.TaskPanel.__init__(self,parent,tb)

        
        self.oldBg=self.GetBackgroundColour()
        
        self.mainsizer.Layout()
        self.mainsizer.Fit(self)

    def createButtonBox(self):
        """
        Created: 10.11.2004, JV
        Description: Creates a button box containing the buttons Render,
                     Preview and Close
        """
        TaskPanel.TaskPanel.createButtonBox(self)
        #self.processButton.SetLabel("Do Color Merging")
        #self.processButton.Bind(wx.EVT_BUTTON,self.doColorMergingCallback)
        messenger.connect(None,"process_dataset",self.doColorMergingCallback)        

        
    def createOptionsFrame(self):
        """
        Created: 10.11.2004, JV
        Description: Creates a frame that contains the various widgets
                     used to control the colocalization settings
        """
        TaskPanel.TaskPanel.createOptionsFrame(self)

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
        
        self.restoreBtn=wx.Button(self.editIntensityPanel,-1,"Reset")
        self.restoreBtn.Bind(wx.EVT_BUTTON,self.intensityTransferEditor.restoreDefaults)
        self.box.Add(self.restoreBtn)        
        

        # The alpha function doesn't need to be edited
        # Code left if futher need shows ups
        
        #self.editAlphaPanel=wx.Panel(self.settingsNotebook,-1)
        self.editAlphaPanel=wx.Panel(self.editIntensityPanel,-1)
        self.editAlphaSizer=wx.GridBagSizer()
        
        #self.alphaEditor=IntensityTransferEditor(self.editAlphaPanel)
        #self.alphaEditor.setIntensityTransferFunction(self.alphaTF)
        #self.alphaEditor.setAlphaMode(1)
        #self.editAlphaSizer.Add(self.alphaEditor,(0,0),span=(1,2))        
        
        self.alphaModeBox=wx.RadioBox(self.editAlphaPanel,-1,"Alpha channel construction",
        choices=["Maximum Mode","Average Mode","Image Luminance"],majorDimension=2,style=wx.RA_SPECIFY_COLS)
        
        
        self.alphaModeBox.Bind(wx.EVT_RADIOBOX,self.modeSelect)
        
        self.averageLbl=wx.StaticText(self.editAlphaPanel,-1,"Average Threshold:")
        self.averageEdit=wx.TextCtrl(self.editAlphaPanel,-1,"",size=(150,-1))
        self.averageEdit.Enable(0)
        
        box=wx.BoxSizer(wx.HORIZONTAL)
        box.Add(self.averageLbl)
        box.Add(self.averageEdit)
        self.editAlphaSizer.Add(self.alphaModeBox,(0,0))
        self.editAlphaSizer.Add(box,(1,0))
        
        self.editAlphaPanel.SetSizer(self.editAlphaSizer)
        self.editAlphaSizer.Fit(self.editAlphaPanel)
        self.editIntensitySizer.Add(self.editAlphaPanel,(4,0))

        self.editIntensityPanel.SetSizer(self.editIntensitySizer)
        self.editIntensityPanel.SetAutoLayout(1)
        
        self.editIntensityPanel.Layout()
        self.editIntensitySizer.Fit(self.editIntensityPanel)        
        self.settingsNotebook.AddPage(self.editIntensityPanel,"Intensity")
        #self.settingsNotebook.AddPage(self.editAlphaPanel,"Alpha Channel")
        
#        self.optionssizer.Add(self.intensityTransferEditor,(3,0))

    def modeSelect(self,event):
        """
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
        Created: 30.11.2004, KP
        Description: A method to reset all the intensity transfer functions
        """
        dataunits = self.dataUnit.getSourceDataUnits()
        for unit in dataunits:
            setting=unit.getSettings()
            minval,maxval=unit.getScalarRange()
            itf = vtk.vtkIntensityTransferFunction()
            itf.SetRangeMax(maxval)
            self.alphaTF.SetRangeMax(maxval)
            setting.set("IntensityTransferFunction",itf)


    def updateSettings(self, force=0):
        """
        Created: 10.11.2004, JV
        Description: A method used to set the GUI widgets to their proper values
                     based on the selected channel, the settings of which are 
                     stored in the instance variable self.configSetting
        """
        if self.dataUnit and self.settings:
            ctf = self.settings.get("ColorTransferFunction")
            if ctf and self.colorBtn:
                Logging.info("Setting ctf of color button",kw="ctf")
                self.colorBtn.setColorTransferFunction(ctf)
                self.colorBtn.Refresh()
    
            #Logging.info("settings=",self.settings,kw="task")
            print self.settings.settings.keys()
            tf = self.settings.get("IntensityTransferFunction")
            #if tf:
            #    #print "\n\n\nGot itf with 0=",tf.GetValue(0)," 255=",tf.GetValue(255)
            #else:
            #    print "\n\n\n*** WTF NO ITF"
            self.intensityTransferEditor.setIntensityTransferFunction(tf)


    def doColorMergingCallback(self,*args):
        """
        Created: 10.11.2004, JV
        Description: A callback for the processing button
        """
        #print "\n\n\n\n\nDO COLOR MERGING"
        method=self.alphaModeBox.GetSelection()
        val=0
        if method == 1:
            val=int(self.averageEdit.GetValue())
        lst=[method,val]
        Logging.info("Setting alpha mode to ",lst,kw="task")
        #self.dataUnit.setAlphaMode(lst)
        self.settings.set("AlphaMode",lst)

        TaskPanel.TaskPanel.doOperation(self)

    def setCombinedDataUnit(self,dataUnit):
        """
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
        ctf = self.settings.get("ColorTransferFunction")
        
        sources =  dataUnit.getSourceDataUnits()
        totmax=0
        
        for i in sources:
            minval,maxval=i.getScalarRange()
            if maxval>totmax:totmax=maxval
        self.alphaTF.SetRangeMax(int(totmax))
        
        for i in range(len(sources)):
            tf=vtk.vtkIntensityTransferFunction()
            tf.SetRangeMax(int(totmax))
            #self.settings.setCounted("IntensityTransferFunction",i,tf,0)
            sources[i].getSettings().set("IntensityTransferFunction",tf)

        tf = sources[0].getSettings().get("IntensityTransferFunction")
        #print "\n\nSETTING ITF EDITOR FUNCTION"
        self.intensityTransferEditor.setIntensityTransferFunction(tf)


        for i in range(len(sources)):
            self.dataUnit.setOutputChannel(i,1)
        if self.colorBtn:
            #Logging.info("Setting ctf of colorbutton to ",ctf,kw="ctf")
            self.colorBtn.setColorTransferFunction(ctf)
        else:
            Logging.info("No color button to set ctf to ",kw="ctf")
        self.restoreFromCache()
        
