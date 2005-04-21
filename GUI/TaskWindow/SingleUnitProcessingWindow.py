#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: SingleUnitProcessingWindow.py
 Project: Selli
 Created: 24.11.2004, KP
 Description:

 A wxPython Dialog window that is used to process a single dataset series in 
 various ways,
 including but not limited to: Correction of bleaching, mapping intensities 
 through intensity transfer
 function and noise removal.

 Modified: 24.11.2004 KP - Created the module
           26.11.2004 JV - Added gui controls for filtering, no functionality
            07.12.2004 JM - Fixed: Clicking cancel on color selection no longer 
                            causes exception
                            Fixed: Color selection now shows the current color 
                            as default
           10.12.2004 JV - Added: Passes settings to dataset in preview
           14.12.2004 JV - Added: Disabling of filter settings
           17.12.2004 JV - Fixed: get right filter settings when changing 
                           timepoint
           02.02.2005 KP - Conversion to wxPython complete, using Notebook
                           
 Selli includes the following persons:
 JH - Juha Hyytiäinen, juhyytia@st.jyu.fi
 JM - Jaakko Mäntymaa, jahemant@cc.jyu.fi
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 JV - Jukka Varsaluoma,varsa@st.jyu.fi

 Copyright (c) 2004 Selli Project.
"""
__author__ = "Selli Project <http://sovellusprojektit.it.jyu.fi/selli/>"
__version__ = "$Revision: 1.42 $"
__date__ = "$Date: 2005/01/13 14:52:39 $"

import wx

import os.path
import Dialogs

from PreviewFrame import *
from IntensityTransferEditor import *
from Logging import *
#from ColorSelectionDialog import *

import sys
import time

import TaskWindow
import ColorTransferEditor

class SingleUnitProcessingWindow(TaskWindow.TaskWindow):
    """
    Class: SingleUnitProcessingWindow
    Created: 03.11.2004, KP
    Description: A window for processing a single dataunit
    """
    def __init__(self,parent):
        """
        Method: __init__(parent)
        Created: 03.11.2004, KP
        Description: Initialization
        Parameters:
                root    Is the parent widget of this window
        """
        self.lbls=[]
        self.btns=[]
        self.entries=[]
        self.timePoint = 0
        self.operationName="Single Dataset Series Processing"
        TaskWindow.TaskWindow.__init__(self,parent)
        # Preview has to be generated here
        # self.colorChooser=None
        self.createIntensityTransferPage()
        
        self.Show()

        self.SetTitle("Single Dataset Series Processing")

        self.createToolBar()
        
        self.mainsizer.Layout()
        self.mainsizer.Fit(self.panel)

    def createIntensityInterpolationPanel(self):
        self.interpolationPanel=wx.Panel(self.settingsNotebook)
        #self.interpolationPanel=wx.Panel(self.iTFEditor)
        self.interpolationSizer=wx.GridBagSizer()
        lbl=wx.StaticText(self.interpolationPanel,-1,"Interpolate intensities:")
        self.interpolationSizer.Add(lbl,(0,0))

        lbl=wx.StaticText(self.interpolationPanel,-1,"from timepoint")
        self.lbls.append(lbl)
        self.numOfPoints=5
        for i in range(self.numOfPoints-2):
            lbl=wx.StaticText(self.interpolationPanel,-1,"thru")
            self.lbls.append(lbl)
        lbl=wx.StaticText(self.interpolationPanel,-1,"to timepoint")
        self.lbls.append(lbl)

        for i in range(self.numOfPoints):
            btn=wx.Button(self.interpolationPanel,-1,"goto")
            btn.Bind(wx.EVT_BUTTON,lambda event,x=i: self.gotoInterpolationTimePoint(x))
            entry=wx.TextCtrl(self.interpolationPanel,size=(50,-1))
            self.btns.append(btn)
            self.entries.append(entry)

        for entry in self.entries:
            entry.Bind(wx.EVT_TEXT,self.setInterpolationTimePoints)

        last=0
        for i in range(self.numOfPoints):
            lbl,entry,btn=self.lbls[i],self.entries[i],self.btns[i]
            self.interpolationSizer.Add(lbl,(i+1,0))
            self.interpolationSizer.Add(entry,(i+1,1))
            self.interpolationSizer.Add(btn,(i+1,2))
            last=i+1

        #self.editIntensitySizer.Add(self.interpolationPanel,(0,1))
        self.interpolationPanel.SetSizer(self.interpolationSizer)
        self.interpolationPanel.SetAutoLayout(1)
        self.interpolationSizer.SetSizeHints(self.interpolationPanel)

        self.settingsNotebook.InsertPage(1,self.interpolationPanel,"Interpolation")
        
        self.interpolationBox=wx.BoxSizer(wx.HORIZONTAL)

        self.reset2Btn=wx.Button(self.interpolationPanel,-1,"Reset all timepoints")
        self.reset2Btn.Bind(wx.EVT_BUTTON,self.resetTransferFunctions)
        self.interpolationBox.Add(self.reset2Btn)

        self.interpolateBtn=wx.Button(self.interpolationPanel,-1,"Interpolate")
        self.interpolateBtn.Bind(wx.EVT_BUTTON,self.startInterpolation)
        self.interpolationBox.Add(self.interpolateBtn)
        self.interpolationSizer.Add(self.interpolationBox,(last+1,0))
        
        
        #self.mainsizer.Add(self.interpolationPanel,(1,0))
        #self.panel.Layout()
        #self.mainsizer.Fit(self.panel)


    def createIntensityTransferPage(self):
        """
        Method: createIntensityInterpolationPanel()
        Created: 09.12.2004, KP
        Description: Creates a frame holding the entries for configuring 
                     interpolation
        """
        self.editIntensityPanel=wx.Panel(self.settingsNotebook,-1)
        self.editIntensitySizer=wx.GridBagSizer()

        self.iTFEditor=IntensityTransferEditor(self.editIntensityPanel)
        self.editIntensitySizer.Add(self.iTFEditor,(0,0))#,span=(1,2))

        self.box=wx.BoxSizer(wx.HORIZONTAL)
        self.editIntensitySizer.Add(self.box,(2,0))
        self.createIntensityInterpolationPanel()

        self.restoreBtn=wx.Button(self.editIntensityPanel,-1,"Reset defaults")
        self.restoreBtn.Bind(wx.EVT_BUTTON,self.iTFEditor.restoreDefaults)
        self.box.Add(self.restoreBtn)

        self.resetBtn=wx.Button(self.editIntensityPanel,-1,"Reset all timepoints")
        self.resetBtn.Bind(wx.EVT_BUTTON,self.resetTransferFunctions)
        self.box.Add(self.resetBtn)

        self.copyiTFBtn=wx.Button(self.editIntensityPanel,-1,"Copy to all timepoints")
        self.copyiTFBtn.Bind(wx.EVT_BUTTON,self.copyTransferFunctionToAll)
        self.box.Add(self.copyiTFBtn)

        self.editIntensityPanel.SetSizer(self.editIntensitySizer)
        self.editIntensityPanel.SetAutoLayout(1)
        self.settingsNotebook.InsertPage(1,self.editIntensityPanel,"Transfer Function")
        
        print "Updating settings!"
        self.updateSettings()
        
    def setInterpolationTimePoints(self,event):
        """
        Method: setInterpolationTimePoints()
        Created: 13.12.2004, KP
        Description: A callback that is called when a timepoint entry for
                     intensity interpolation changes. Updates the list of 
                     timepoints between which the interpolation is carried out
                     by the dataunit
        """
        lst=[]
        for i in self.entries:
            val=i.GetValue()
            try:
                n=int(val)
                lst.append(n)
            except:
                # For entries that have no value, add -1 as a place holder
                lst.append(-1)
        #print "Setting lst=",lst
        #self.dataUnit.setInterpolationTimePoints(lst)
        self.settings.set("InterpolationTimepoints",lst)


    def gotoInterpolationTimePoint(self,entrynum):
        """
        Method: gotoInterpolationTimePoint(entrynum)
        Created: 09.12.2004, KP
        Description: The previewed timepoint is set to timepoint specified in
                     self.entries[entrynum]
        """
        try:
            tp=int(self.entries[entrynum].GetValue())
        except:
            pass
        else:
            print "Previewing tp=",tp
            self.preview.gotoTimePoint(tp)


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
        self.taskNameLbl.SetLabel("Processed dataset series name:")
            
        self.paletteLbl = wx.StaticText(self.commonSettingsPanel,-1,"Channel palette:")
        self.commonSettingsSizer.Add(self.paletteLbl,(1,0))
        self.colorBtn = ColorTransferEditor.CTFButton(self.commonSettingsPanel)
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
        print "Now configuring timepoint %d"%(timePoint)
        self.iTFEditor.setIntensityTransferFunction(
        self.settings.getCounted("IntensityTransferFunctions",timePoint)
        )
        self.timePoint=timePoint
 
    def copyTransferFunctionToAll(self,event=None):
        """
        Method: copyTransferFunctionToAll
        Created: 10.03.2005, KP
        Description: A method to copy this transfer function to all timepooints
        """
        pass

    def resetTransferFunctions(self,event=None):
        """
        Method: resetTransferFunctions()
        Created: 30.11.2004, KP
        Description: A method to reset all the intensity transfer functions
        """
        pass

    def startInterpolation(self):
        """
        Method: startInterpolation()
        Created: 24.11.2004, KP
        Description: A callback to interpolate intensity transfer functions
                     between the specified timepoints
        """
        self.dataUnit.interpolateIntensities()
#        self.doPreviewCallback()


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
            self.iTFEditor.setIntensityTransferFunction(
            self.settings.getCounted("IntensityTransferFunctions",self.timePoint)
            )
            tps=self.settings.get("InterpolationTimepoints")
            #print "tps=",tps
            if not tps:
                tps=[]
            
            for i in range(len(tps)):
                n=tps[i]
                # If there was nothing in the entry at this position, the 
                # value is -1 in that case, we leave the entry empty
                if n!=-1:
                    self.entries[i].SetValue(str(n))

            ctf = self.settings.get("ColorTransferFunction")
            if ctf and self.colorBtn:
                print "Setting colorBtn.ctf"
                self.colorBtn.setColorTransferFunction(ctf)
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
        #self.dataUnit.setDoMedianFiltering(self.doMedianCheckbutton.GetValue())
        #self.dataUnit.setRemoveSolitary(self.doSolitaryCheckbutton.GetValue())

        #self.dataUnit.setNeighborhood(self.neighborhoodX.GetValue(),
        #                              self.neighborhoodY.GetValue(),
        #                              self.neighborhoodZ.GetValue())
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
        
        #set the color of the colorBtn to the current color
        #r,g,b=self.settings.get("Color")
        #if self.colorChooser:
        #    self.colorChooser.SetValue(wx.Colour(r,g,b))
        ctf = self.settings.get("ColorTransferFunction")
        if self.colorBtn:
            print "Setting ctf"
            self.colorBtn.setColorTransferFunction(ctf)
        else:
            print "Won't set ctf!"
        
        # We register a callback to be notified when the timepoint changes
        # We do it here because the timePointChanged() code requires the dataunit
        self.Bind(EVT_TIMEPOINT_CHANGED,self.timePointChanged,id=self.preview.GetId())

        tf=self.settings.getCounted("IntensityTransferFunctions",self.timePoint)
        self.iTFEditor.setIntensityTransferFunction(tf)
        self.iTFEditor.updateCallback=self.doPreviewCallback

        self.updateSettings()
