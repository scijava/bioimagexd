#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: ColocalizationWindow.py
 Project: Selli
 Created: 03.11.2004
 Creator: KP
 Description:

 A wx.Python wx.Dialog window that is used to control the settings for the
 colocalization module. Expects to be handed a ColocalizationDataUnit()
 containing the datasets from which the colocalization map is generated.
 Uses the PreviewFrame for previewing.

 Modified: 03.11.2004 KP - Added support for getting the file names from the
                           DataUnits.
           08.11.2004 KP - Simplified the preview code. Now the preview frame
                           is just handed the dataunit and updatePreview() 
                           called when needed
           08.11.2004 KP - A button and supporting methods for setting 
                           colocalization color
           07.12.2004 JM - Fixed: Clicking cancel on color selection no longer
                           causes exception
                           Fixed: Color selection now shows the current color 
                           as default
           14.12.2004 JM - Colocalization depth is now saved and loaded properly
           03.02.2005 KP - Window converted to wx.Python and made to use a notebook

 Selli includes the following persons:
 JH - Juha Hyytiäinen, juhyytia@st.jyu.fi
 JM - Jaakko Mäntymaa, jahemant@cc.jyu.fi
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 JV - Jukka Varsaluoma,varsa@st.jyu.fi

 Copyright (c) 2004 Selli Project.
"""
__author__ = "Selli Project <http://sovellusprojektit.it.jyu.fi/selli/>"
__version__ = "$Revision: 1.40 $"
__date__ = "$Date: 2005/01/13 14:52:39 $"

import os.path

from PreviewFrame import *
from ColorSelectionDialog import *
from Logging import *
import sys
import Colocalization
import time

import TaskWindow

def showColocalizationWindow(colocalizationUnit,mainwin):
    """
    Function: showColocalizationWindow(colocalizationUnit,mainwin)
    Created: 15.11.2004
    Creator: KP
    Description: A function that displays the colocalization window and
                 waits for the user to create the colocalization. After
                 the colocalization is done or cancel is pressed, the results
                 are returned to the caller
    """

    result=TaskWindow.showTaskWindow(ColocalizationWindow,colocalizationUnit,
                                     mainwin)

    return result


class ColocalizationWindow(TaskWindow.TaskWindow):
    """
    Class: ColocalizationWindow
    Created: 03.11.2004, KP
    Description: A window for controlling the settings of the
                 colocalization module
    """
    def __init__(self,root):
        """
        Method: __init__(root)
        Created: 03.11.2004
        Creator: KP
        Description: Initialization
        Parameters:
                root    Is the parent widget of this window
        """
        TaskWindow.TaskWindow.__init__(self,root)
        self.operationName="Colocalization"
        # Preview has to be generated here
        self.preview=ColocalizationPreview(self.panel,self)
        #self.preview = ColorMergingPreview(self)
        self.previewSizer.Add(self.preview,(0,0),flag=wx.EXPAND|wx.ALL)
        self.previewSizer.Fit(self.preview)
        self.SetTitle("Colocalization")
        self.mainsizer.Layout()
        self.mainsizer.Fit(self.panel)

########################## WIDGET CREATION CODE ##############################

    def createButtonBox(self):
        """
        Method: createButtonBox()
        Created: 03.11.2004
        Creator: KP
        Description: Creates a button box containing the buttons Render, 
                     Preview and Close
        """
        TaskWindow.TaskWindow.createButtonBox(self)
        self.processButton.SetLabel("Do Colocalization")
        self.processButton.Bind(EVT_BUTTON,self.doColocalizationCallback)

    def createOptionsFrame(self):
        """
        Method: createOptionsFrame()
        Created: 03.11.2004
        Creator: KP
        Description: Creates a frame that contains the various widgets
                     used to control the colocalization settings
        """
        TaskWindow.TaskWindow.createOptionsFrame(self)
        self.taskNameLbl.SetLabel("Colocalization name:")

        self.colorChooser=ColorSelectionDialog(self.commonSettingsPanel,self.setColor)
        self.commonSettingsSizer.Add(self.colorChooser,(1,0))

        self.colocalizationPanel=wx.Panel(self.settingsNotebook,-1)
        self.colocalizationSizer=wx.GridBagSizer()
        
        self.depthLbl=wx.StaticText(self.colocalizationPanel,-1,"Colocalization Depth:")
        self.colocalizationSizer.Add(self.depthLbl,(0,0))
   
        self.depthMenu=wx.Choice(self.colocalizationPanel,-1,choices=["1-bit","8-bit"])
        self.colocalizationSizer.Add(self.depthMenu,(1,0))
        self.depthMenu.Bind(EVT_CHOICE,self.updateBitDepth)

        self.thresholdLbl=wx.StaticText(self.colocalizationPanel,-1,"Channel threshold:")
        
        self.threshold=wx.Slider(self.colocalizationPanel,value=128,minValue=1,maxValue=255,size=(300,-1),
        style=wx.SL_HORIZONTAL|wx.SL_AUTOTICKS|wx.SL_LABELS)
        self.threshold.Bind(EVT_SCROLL,self.updateThreshold)
        
        self.colocalizationSizer.Add(self.thresholdLbl,(2,0))
        self.colocalizationSizer.Add(self.threshold,(3,0))

        self.colocalizationPanel.SetSizer(self.colocalizationSizer)
        self.colocalizationPanel.SetAutoLayout(1)
        
        self.settingsNotebook.AddPage(self.colocalizationPanel,"Colocalization")


    def setColor(self,r,g,b):
        """
        Method: setColor(r,g,b)
        Created: 03.11.2004
        Creator: KP
        Description: A method that sets the color of the dataUnit and 
                     updates the preview and Set color-button accordingly
        """
        if self.dataUnit:
            self.dataUnit.setColor(r,g,b)
            self.preview.updateColor()
#        self.colorBtn.SetBackgroundColour((r,g,b))
        self.doPreviewCallback()

    def updateThreshold(self,event):
        """
        Method: updateThreshold(event)
        Created: 03.11.2004
        Creator: KP
        Description: A callback function called when the threshold is 
        configured via the slider
        """
        # We might get called before any channel has been selected. 
        # In that case, do nothing
        if self.configSetting:
            oldthreshold=self.configSetting.getThreshold()
            newthreshold=int(self.threshold.GetValue())
        if oldthreshold != newthreshold:
            self.configSetting.setThreshold(int(self.threshold.GetValue()))
            self.doPreviewCallback()

    def updateSettings(self):
        """
        Method: updateSettings()
        Created: 03.11.2004
        Creator: KP
        Description: A method used to set the GUI widgets to their proper values
                     based on the selected channel, the settings of which are 
                     stored in the instance variable self.configSetting
        """
#                self.dataUnit.setFormat(self.depthVar.get())
        print "UPDATESETTINGS"
        self.depthMenu.SetStringSelection(self.dataUnit.getFormat())
        self.threshold.SetValue(self.configSetting.getThreshold())
        if self.dataUnit:
            r,g,b=self.dataUnit.getColor()
            self.colorChooser.SetValue(wx.Colour(r,g,b))

    def doColocalizationCallback(self,event):
        """
        Method: doColocalizationCallback()
        Created: 03.11.2004
        Creator: KP
        Description: A callback for the button "Do colocalization"
        """
        self.updateBitDepth()
        TaskWindow.TaskWindow.doOperation(self)

    def updateBitDepth(self,event=None):
        """
        Method: updateBitDepth(event)
        Created: 17.11.2004
        Creator: KP
        Description: Updates the preview to be done at the selected depth
        """
        if self.dataUnit:
            self.dataUnit.setFormat(self.depthMenu.GetString(self.depthMenu.GetSelection()))


    def doPreviewCallback(self,event=None):
        """
        Method: doPreviewCallback()
        Created: 03.11.2004
        Creator: KP
        Description: A callback for the button "Preview" and other events
	             that wish to update the preview
        """
        self.updateBitDepth()
        TaskWindow.TaskWindow.doPreviewCallback(self,event)
