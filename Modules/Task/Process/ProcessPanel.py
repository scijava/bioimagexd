#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: ProcessPanel
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

class ProcessPanel(TaskPanel.TaskPanel):
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
        self.operationName="Process"
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
        Thresholdhelp="Threshold that a pixel needs to be over to get processed by solitary filter."
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
        self.solitaryThresholdLbl.SetLabel("Processing threshold:")
        
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
	self.doMedianCheckbutton.Enable(1)
	self.doSolitaryCheckbutton.Enable(1)
	self.doAnisotropicCheckbutton.Enable(1)	
        doMedian=self.doMedianCheckbutton.GetValue()
        doSolitary=self.doSolitaryCheckbutton.GetValue()
        doAniso=self.doAnisoptropicCheckbutton.GetValue()
        
        for widget in [self.neighborhoodX,self.neighborhoodY,self.neighborhoodZ,self.neighborhoodXLbl,\
        self.neighborhoodYLbl,self.neighborhoodZLbl]:
            widget.Enable(doMedian)
    

        for widget in [self.solitaryX,self.solitaryY,self.solitaryThreshold,self.solitaryXLbl,self.solitaryYLbl,\
        self.solitaryThresholdLbl]:
            widget.Enable(doSolitary)
        
        
        for widget in [self.anisoDiffusionFactor,self.anisoDiffusionThreshold,self.anisoNeighborhoodFaces,self.anisoNeighborhoodEdges,self.anisoNeighborhoodCorners,self.anisoMeasureBox]:
            widget.Enable(doAniso)

        self.updateFilterData()
        #self.doPreviewCallback()

    def updateSettings(self):
        """
        Method: updateSettings()
        Created: 03.11.2004, KP
        Description: A method used to set the GUI widgets to their proper values
        """

        if self.dataUnit:
            get=self.settings.get
            set=self.settings.set
            ctf = get("ColorTransferFunction")
            if ctf and self.colorBtn:
                print "Setting colorBtn.ctf"
                self.colorBtn.setColorTransferFunction(ctf)
                self.colorBtn.Refresh()
            # median filtering
            
            median=get("MedianFiltering")
            
            self.doMedianCheckbutton.SetValue(median)
            #neighborhood=self.dataUnit.getNeighborhood()
            neighborhood=get("MedianNeighborhood")
            self.neighborhoodX.SetValue(str(neighborhood[0]))
            self.neighborhoodY.SetValue(str(neighborhood[1]))
            self.neighborhoodZ.SetValue(str(neighborhood[2]))

            # solitary filtering
            #solitary=self.dataUnit.getRemoveSolitary()
            solitary=get("SolitaryFiltering")
            solitaryX=get("SolitaryHorizontalThreshold")
            solitaryY=get("SolitaryVerticalThreshold")
            solitaryThreshold=get("SolitaryProcessingThreshold")
            self.doSolitaryCheckbutton.SetValue(solitary)
            self.solitaryX.SetValue(str(solitaryX))
            self.solitaryY.SetValue(str(solitaryY))
            self.solitaryThreshold.SetValue(str(solitaryThreshold))
            
            diffFac=get("AnisotropicDiffusionFactor")
            diffMeasure=get("AnisotropicDiffusionMeasure")
            diffThreshold=get("AnisotropicDiffusionThreshold")
            doAniso=get("AnisotropicDiffusion")
            self.anisoDiffusionFactor.SetValue(str(diffFac))
            self.anisoDiffusionThreshold.SetValue(str(diffThreshold))
            self.anisoMeasureBox.SetSelection(int(diffMeasure))
            self.doAnisoptropicCheckbutton.SetValue((not not doAniso))

            self.doFilterCheckCallback()

            faces=get("AnisotropicDiffusionFaces")
            self.anisoNeighborhoodFaces.SetValue(faces)        
            edges=get("AnisotropicDiffusionEdges")
            self.anisoNeighborhoodEdges.SetValue(edges)
            corners=get("AnisotropicDiffusionCorners")
            self.anisoNeighborhoodCorners.SetValue(corners)
                
    def updateFilterData(self):
        """
        Method: updateFilterData()
        Created: 13.12.2004, JV
        Description: A method used to set the right values in dataset
                     from filter GUI widgets
        """
        set=self.settings.set
        get=self.settings.get
        def setval(name,value):
            if get(name)!=value:
                set(name,value)
                messenger.send(None,"renew_preview")
        
        setval("AnisotropicDiffusion",self.doAnisoptropicCheckbutton.GetValue())
        setval("MedianFiltering",self.doMedianCheckbutton.GetValue())
        setval("SolitaryFiltering",self.doSolitaryCheckbutton.GetValue())
        nbh=(self.neighborhoodX.GetValue(),
            self.neighborhoodY.GetValue(),
            self.neighborhoodZ.GetValue())
        try:
            nbh=map(int,nbh)
            setval("MedianNeighborhood",nbh)
        except ValueError:
            pass
        sx,sy,st=0,0,0
        
        try:
            sx=int(self.solitaryX.GetValue())
            sy=int(self.solitaryY.GetValue())
            st=int(self.solitaryThreshold.GetValue())
            setval("SolitaryHorizontalThreshold",sx)
            setval("SolitaryVerticalThreshold",sy)
            setval("SolitaryProcessingThreshold",st)
        except ValueError:
            pass
        try:
            anisoFac=float(self.anisoDiffusionFactor.GetValue())
            setval("AnisotropicDiffusionFactor",anisoFac)
        except:
            pass
        anisoMeasure=self.anisoMeasureBox.GetSelection()
        setval("AnisotropicDiffusionMeasure",anisoMeasure)
        try:
            anisoThreshold=float(self.anisoThreshold.GetValue())
            setval("AnisotropicDiffusionThreshold",anisoThreshold)
        except:
            pass
        
        setval("AnisotropicDiffusionFaces",self.anisoNeighborhoodFaces.GetValue())        
        setval("AnisotropicDiffusionEdges",self.anisoNeighborhoodEdges.GetValue())
        setval("AnisotropicDiffusionCorners",self.anisoNeighborhoodCorners.GetValue())
        
    def doProcessingCallback(self,event=None):
        """
        Method: doProcessingCallback()
        Created: 03.11.2004, KP
        Description: A callback for the button "Process Dataset Series"
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
        # TODO: Validity checks, here or in dataunit

        #print "doMedianVar in window: "
        #print self.doMedianVar.get()
        self.updateFilterData()
        TaskPanel.TaskPanel.doPreviewCallback(self,event)

    def setCombinedDataUnit(self,dataUnit):
        """
        Method: setCombinedDataUnit(dataUnit)
        Created: 23.11.2004, KP
        Description: Sets the processed dataunit that is to be processed.
                     It is then used to get the names of all the source data
                     units and they are added to the menu.
                     This is overwritten from TaskPanel since we only process
                     one dataunit here, not multiple source data units
        """
        TaskPanel.TaskPanel.setCombinedDataUnit(self,dataUnit)
        
        ctf = self.settings.get("ColorTransferFunction")
        if ctf and self.colorBtn:
            self.colorBtn.setColorTransferFunction(ctf)
        else:
            print "Won't set ctf!"
        
        # We register a callback to be notified when the timepoint changes
        # We do it here because the timePointChanged() code requires the dataunit
        #self.Bind(EVT_TIMEPOINT_CHANGED,self.timePointChanged,id=ID_TIMEPOINT)

        tf=self.settings.getCounted("IntensityTransferFunctions",self.timePoint)

        self.updateSettings()
