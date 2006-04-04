#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: ManipulationPanel
 Project: BioImageXD
 Created: 31.05.2005, KP
 Description:

 A task window for restoring a dataset. This includes any filtering,
 deblurring, deconvolution etc. 
                            
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
from GUI import ColorTransferEditor

from GUI import TaskPanel
import UIElements
import string

class ManipulationPanel(TaskPanel.TaskPanel):
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
        self.operationName="Manipulation"
        TaskPanel.TaskPanel.__init__(self,parent,tb)
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
        TaskPanel.TaskPanel.createButtonBox(self)
        
        #self.ManipulationButton.SetLabel("Manipulation Dataset Series")
        self.ManipulationButton.Bind(wx.EVT_BUTTON,self.doManipulationingCallback)

    def createOptionsFrame(self):
        """
        Method: createOptionsFrame()
        Created: 03.11.2004
        Creator: KP
        Description: Creates a frame that contains the various widgets
                     used to control the colocalization settings
        """
        TaskPanel.TaskPanel.createOptionsFrame(self)
            
        self.paletteLbl = wx.StaticText(self,-1,"Channel palette:")
        self.commonSettingsSizer.Add(self.paletteLbl,(1,0))
        self.colorBtn = ColorTransferEditor.CTFButton(self)
        self.commonSettingsSizer.Add(self.colorBtn,(2,0))
        
        #controls for filtering

        self.filtersPanel=wx.Panel(self.settingsNotebook,-1)
        self.settingsNotebook.AddPage(self.filtersPanel,"Filtering")
        
        self.filtersSizer=wx.GridBagSizer()
        n=0
        #Median Filtering
        self.doMedianCheckbutton = wx.CheckBox(self.filtersPanel,
        -1,"Median Filtering")
        medianSbox=wx.StaticBox(self.filtersPanel,-1,"Median filtering")
        self.medianSizer=wx.StaticBoxSizer(medianSbox,wx.VERTICAL)
        self.doMedianCheckbutton.Bind(wx.EVT_CHECKBOX,self.doFilterCheckCallback)
        self.doMedianCheckbutton.SetHelpText("Smooth data with a median filter. A median filter replaces each pixel with the median value from a rectangular neighborhood around that pixel.")
        val=UIElements.AcceptedValidator
        j=0
        lsizer=wx.GridBagSizer()
        for i in ["X","Y","Z"]:
            self.__dict__["neighborhood%s"%i]=eval('wx.TextCtrl(self.filtersPanel,-1,"1",validator=val(string.digits))')
            self.__dict__["neighborhood%sLbl"%i]=eval('wx.StaticText(self.filtersPanel,-1,"%s:")'%i)
            eval("self.neighborhood%s.SetHelpText('Size of the median neighborhood in %s direction.')"%(i,i))
            eval("self.neighborhood%sLbl.SetHelpText('Size of the median neighborhood in %s direction.')"%(i,i))
            lbl=eval("self.neighborhood%sLbl"%i)
            ctrl=eval("self.neighborhood%s"%i)
            lsizer.Add(lbl,(j,0))
            lsizer.Add(ctrl,(j,1))
            j+=1
        self.neighborhoodLbl=wx.StaticText(self.filtersPanel,-1,
        "Neighborhood:")

        n+=1
        self.medianSizer.Add(self.doMedianCheckbutton)
        self.medianSizer.Add(self.neighborhoodLbl)
        self.medianSizer.Add(lsizer)
        
        self.filtersSizer.Add(self.medianSizer,(n,0),flag=wx.EXPAND|wx.LEFT|wx.RIGHT)
        n+=1
        
        #Solitary Filtering

        self.doSolitaryCheckbutton = wx.CheckBox(self.filtersPanel,
        -1,"Solitary Filtering")
        self.doSolitaryCheckbutton.SetHelpText("Remove solitary noise pixels from the data by comparing them with their neighborhood.")
        self.doSolitaryCheckbutton.Bind(wx.EVT_CHECKBOX,self.doFilterCheckCallback)

        solitarySbox=wx.StaticBox(self.filtersPanel,-1,"Solitary Filtering")
        self.solitarySizer=wx.StaticBoxSizer(solitarySbox,wx.VERTICAL)

        self.solitaryLbl=wx.StaticText(self.filtersPanel,-1,"Thresholds:")
        Xhelp="Threshold that a pixel's horizontal neighbor needs to be over so that the pixel is not removed."
        Yhelp="Threshold that a pixel's vertical neighbor needs to be over so that the pixel is not removed."
        Thresholdhelp="Threshold that a pixel needs to be over to get Manipulationed by solitary filter."
        j=0
        lsizer=wx.GridBagSizer()
        for i in ["X","Y","Threshold"]:
            self.__dict__["solitary%s"%i]=eval('wx.TextCtrl(self.filtersPanel,-1,"1",validator=val(string.digits))')
            self.__dict__["solitary%sLbl"%i]=eval('wx.StaticText(self.filtersPanel,-1,"%s:")'%i)
            eval("self.solitary%s.SetHelpText(%shelp)"%(i,i))
            eval("self.solitary%sLbl.SetHelpText(%shelp)"%(i,i))
            lbl=eval("self.solitary%sLbl"%i)
            ctrl=eval("self.solitary%s"%i)
            lsizer.Add(lbl,(j,0))
            lsizer.Add(ctrl,(j,1))
            j+=1
        self.solitaryThresholdLbl.SetLabel("Manipulationing threshold:")
        
        self.solitarySizer.Add(self.doSolitaryCheckbutton)
        self.solitarySizer.Add(self.solitaryLbl)
        self.solitarySizer.Add(lsizer)            
        self.filtersSizer.Add(self.solitarySizer,(n,0),flag=wx.EXPAND|wx.LEFT|wx.RIGHT)
        n+=1
        # Edge preserving smoothing
        self.doAnisoptropicCheckbutton = wx.CheckBox(self.filtersPanel,
        -1,"Edge Preserving Smoothing")
        self.doAnisoptropicCheckbutton.Bind(wx.EVT_CHECKBOX,self.doFilterCheckCallback)
        self.doAnisoptropicCheckbutton.SetHelpText("Smooth data with anisotropic diffusion. An anisotropic diffusion preserves the edges in the image.")
        
        anisoSbox=wx.StaticBox(self.filtersPanel,-1,"Edge preserving smoothing")
        self.anisoSizer=wx.StaticBoxSizer(anisoSbox,wx.VERTICAL)
        self.anisoSizer.Add(self.doAnisoptropicCheckbutton)
        
        self.anisoLbl=wx.StaticText(self.filtersPanel,-1,"Neighborhood:")
        self.anisoSizer.Add(self.anisoLbl)
        Faceshelp="Toggle whether the 6 voxels adjoined by faces are included in the neighborhood."
        Cornershelp="Toggle whether the 8 corner connected voxels are included in the neighborhood."
        Edgeshelp="Toggle whether the 12 edge connected voxels are included in the neighborhood."
        lsizer=wx.GridBagSizer()
        j=0
        for i in ["Faces","Corners","Edges"]:
            self.__dict__["anisoNeighborhood%s"%i]=eval('wx.CheckBox(self.filtersPanel,-1,"%s")'%i)
            eval("self.anisoNeighborhood%s.SetHelpText(%shelp)"%(i,i))
            ctrl=eval("self.anisoNeighborhood%s"%i)
            ctrl.SetValue(1)
            lsizer.Add(ctrl,(0,j))
            j+=1            
        self.anisoSizer.Add(lsizer)    
        
        self.anisoThresholdLbl=wx.StaticText(self.filtersPanel,-1,"Threshold:")
        self.anisoSizer.Add(self.anisoThresholdLbl)
        
        self.anisoMeasureBox=wx.RadioBox(self.filtersPanel,-1,"Gradient measure",
        choices=["Central difference","Gradient to neighbor"],majorDimension=2,
        style=wx.RA_SPECIFY_COLS
        )
        self.anisoMeasureBox.SetSelection(1)
        self.anisoSizer.Add(self.anisoMeasureBox)
        self.anisoDiffusionThresholdLbl=wx.StaticText(self.filtersPanel,-1,"Diffusion threshold:")
        self.anisoDiffusionThreshold=wx.TextCtrl(self.filtersPanel,-1,"5.0")
        self.anisoDiffusionFactorLbl=wx.StaticText(self.filtersPanel,-1,"Diffusion factor:")
        self.anisoDiffusionFactor=wx.TextCtrl(self.filtersPanel,-1,"1.0")
        lsizer=wx.GridBagSizer()
        lsizer.Add(self.anisoDiffusionThresholdLbl,(0,0))
        lsizer.Add(self.anisoDiffusionThreshold,(0,1))
        lsizer.Add(self.anisoDiffusionFactorLbl,(1,0))
        lsizer.Add(self.anisoDiffusionFactor,(1,1))
        self.anisoSizer.Add(lsizer)
        
        self.filtersSizer.Add(self.anisoSizer,(n,0),flag=wx.EXPAND|wx.LEFT|wx.RIGHT)                
        self.filtersPanel.SetSizer(self.filtersSizer)
        self.filtersPanel.SetAutoLayout(1)
        self.filtersSizer.Fit(self.filtersPanel)

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

    def updateSettings(self):
        """
        Method: updateSettings()
        Created: 03.11.2004, KP
        Description: A method used to set the GUI widgets to their proper values
        """

        if self.dataUnit:
            get=self.settings.get
            set=self.settings.set
                
    def updateFilterData(self):
        """
        Method: updateFilterData()
        Created: 13.12.2004, JV
        Description: A method used to set the right values in dataset
                     from filter GUI widgets
        """
        pass
        
    def doManipulationingCallback(self,event=None):
        """
        Method: doManipulationingCallback()
        Created: 03.11.2004, KP
        Description: A callback for the button "Manipulation Dataset Series"
        """
        self.updateFilterData()
        TaskPanel.TaskPanel.doOperation(self)

    def doPreviewCallback(self,event=None,*args):
        """
        Method: doPreviewCallback()
        Created: 03.11.2004, KP
        Description: A callback for the button "Preview" and other events
                     that wish to update the preview
        """
        self.updateFilterData()
        TaskPanel.TaskPanel.doPreviewCallback(self,event)

    def setCombinedDataUnit(self,dataUnit):
        """
        Method: setCombinedDataUnit(dataUnit)
        Created: 23.11.2004, KP
        Description: Sets the Manipulationed dataunit that is to be Manipulationed.
                     It is then used to get the names of all the source data
                     units and they are added to the menu.
                     This is overwritten from TaskPanel since we only Manipulation
                     one dataunit here, not multiple source data units
        """
        TaskPanel.TaskPanel.setCombinedDataUnit(self,dataUnit)
        self.updateSettings()
