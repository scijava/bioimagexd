#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: SingleUnitProcessingWindow.py
 Project: Selli
 Created: 24.11.2004
 Creator: KP
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
#from IntensityTransferFunction import *
from Logging import *
from ColorSelectionDialog import *

import sys
import time

import TaskWindow

def showSingleUnitProcessingWindow(sourceUnit,mainwin):
    """
    Function: showSingleUnitProcessingWindow(sourceUnit,mainwin)
    Created: 24.11.2004
    Creator: KP
    Description: A function that displays the single unit processing window and
                 waits for the user to process the dataset. After
                 the deed is done or cancel is pressed, the results
                 are returned to the caller
    """

    result=TaskWindow.showTaskWindow(SingleUnitProcessingWindow,
                                     sourceUnit,mainwin)
    return result


class SingleUnitProcessingWindow(TaskWindow.TaskWindow):
    """
    Class: SingleUnitProcessingWindow
    Created: 03.11.2004
    Creator: KP
    Description: A window for processing a single dataunit
    """
    def __init__(self,parent):
        """
        Method: __init__(parent)
        Created: 03.11.2004
        Creator: KP
        Description: Initialization
        Parameters:
                root    Is the parent widget of this window
        """
        self.lbls=[]
        self.btns=[]
        self.entries=[]
        self.operationName="Single Dataset Series Processing"
        TaskWindow.TaskWindow.__init__(self,parent)
        self.settingsSizer.Show(self.listboxsizer,0)
        self.Layout()
        # Preview has to be generated here
        self.colorChooser=None
        self.createIntensityTransferPage()

        self.preview=SingleUnitProcessingPreview(self,self)
        self.previewSizer.Add(self.preview,(0,0))
        self.previewSizer.Fit(self.preview)

        self.SetTitle("Single Dataset Series Processing")        
        
        self.mainsizer.Layout()
        self.mainsizer.Fit(self)

    def createIntensityTransferPage(self):
        """
        Method: createInterpolationPanel()
        Created: 09.12.2004
        Creator: KP
        Description: Creates a frame holding the entries for configuring 
                     interpolation
        """
        self.editIntensityPanel=wx.Panel(self.settingsNotebook,-1)
        self.editIntensitySizer=wx.GridBagSizer()
        
        self.iTFEditor=IntensityTransferEditor(self.editIntensityPanel)
        self.editIntensitySizer.Add(self.iTFEditor,(0,0),span=(1,2))        

        self.box=wx.BoxSizer(wx.HORIZONTAL)
        self.editIntensitySizer.Add(self.box,(3,0))
        
        self.restoreBtn=wx.Button(self.editIntensityPanel,-1,"Reset defaults")
        self.restoreBtn.Bind(EVT_BUTTON,self.iTFEditor.restoreDefaults)
        self.box.Add(self.restoreBtn)
        
        self.resetBtn=wx.Button(self.editIntensityPanel,-1,"Reset all timepoints")
        self.resetBtn.Bind(EVT_BUTTON,self.resetTransferFunctions)
        self.box.Add(self.resetBtn)

        self.copyiTFBtn=wx.Button(self.editIntensityPanel,-1,"Copy to all timepoints")
        #self.copyiTFBtn.Bind(EVT_BUTTON,self.copyTransferFunctionToAll)
        self.box.Add(self.copyiTFBtn)

        self.interpolateBtn=wx.Button(self.editIntensityPanel,-1,"Interpolate")
        self.interpolateBtn.Bind(EVT_BUTTON,self.startInterpolation)
        self.box.Add(self.interpolateBtn)
        
        
        self.editIntensityPanel.SetSizer(self.editIntensitySizer)
        self.editIntensityPanel.SetAutoLayout(1)
        self.settingsNotebook.InsertPage(1,self.editIntensityPanel,"Intensity Transfer Function")
        
        self.interpolationPanel=wx.Panel(self.editIntensityPanel)
        self.interpolationSizer=wx.GridBagSizer()
        
        #self.infoSizer.Add(self.interpolationSizer,(0,0))

        lbl=wx.StaticText(self.interpolationPanel,-1,"Interpolate intensities:")
        self.interpolationSizer.Add(lbl,(1,0))

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
            btn.Bind(EVT_BUTTON,lambda event,x=i: self.gotoInterpolationTimePoint(x))
            entry=wx.TextCtrl(self.interpolationPanel,size=(50,-1))
            self.btns.append(btn)
            self.entries.append(entry)

        for entry in self.entries:
            entry.Bind(EVT_TEXT,self.setInterpolationTimePoints)

        for i in range(self.numOfPoints):
            lbl,entry,btn=self.lbls[i],self.entries[i],self.btns[i]
            self.interpolationSizer.Add(lbl,(i+2,0))
            self.interpolationSizer.Add(entry,(i+2,1))
            self.interpolationSizer.Add(btn,(i+2,2))

        self.editIntensitySizer.Add(self.interpolationPanel,(2,0))
        self.interpolationPanel.SetSizer(self.interpolationSizer)
        self.interpolationPanel.SetAutoLayout(1)
        self.interpolationSizer.SetSizeHints(self.interpolationPanel)

        self.editIntensityPanel.Layout()
        self.editIntensitySizer.Fit(self.editIntensityPanel)

    def setInterpolationTimePoints(self,event):
        """
        Method: setInterpolationTimePoints()
        Created: 13.12.2004
        Creator: KP
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
        print "Setting lst=",lst
        self.dataUnit.setInterpolationTimePoints(lst)


    def gotoInterpolationTimePoint(self,entrynum):
        """
        Method: gotoInterpolationTimePoint(entrynum)
        Created: 09.12.2004
        Creator: KP
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
        Created: 03.11.2004
        Creator: KP
        Description: Creates a button box containing the buttons Render, 
                     Preview and Close
        """
        TaskWindow.TaskWindow.createButtonBox(self)
        
        self.processButton.SetLabel("Process Dataset Series")
        self.processButton.Bind(EVT_BUTTON,self.doProcessingCallback)
                
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
            
        self.colorChooser=ColorSelectionDialog(self.commonSettingsPanel,self.setColor)
        self.commonSettingsSizer.Add(self.colorChooser,(1,0))

        #controls for filtering

        self.filtersPanel=wx.Panel(self.settingsNotebook,-1)
        self.filtersSizer=wx.GridBagSizer()
        
        #Median Filtering
        self.doMedianCheckbutton = wx.CheckBox(self.filtersPanel,
        -1,"Median Filtering")
        self.doMedianCheckbutton.Bind(EVT_CHECKBOX,self.doFilterCheckCallback)

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
        self.doSolitaryCheckbutton.Bind(EVT_CHECKBOX,self.doFilterCheckCallback)

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
        self.settingsNotebook.AddPage(self.filtersPanel,"Filtering")


########################## CALLBACK CODE #############################
    def timePointChanged(self,timePoint):
        """
        Method: timePointChanged(timepoint)
        Created: 24.11.2004
        Creator: KP
        Description: A callback that is called when the previewed timepoint 
                     changes.
        Parameters:
                timePoint   The timepoint we're previewing now
        """
        print "Now configuring timepoint %d"%(timePoint)
        self.iTFEditor.setIntensityTransferFunction(
        self.dataUnit.getIntensityTransferFunction(timePoint))
        self.timePoint=timePoint

    def resetTransferFunctions(self,event=None):
        """
        Method: resetTransferFunctions()
        Created: 30.11.2004
        Creator: KP
        Description: A method to reset all the intensity transfer functions
        """
        pass


    def startInterpolation(self):
        """
        Method: startInterpolation()
        Created: 24.11.2004
        Creator: KP
        Description: A callback to interpolate intensity transfer functions 
                     between the specified timepoints
        """
        self.dataUnit.interpolateIntensities()
#        self.doPreviewCallback()


    def doFilterCheckCallback(self,event=None):
        """
        Method: doFilterCheckCallback(self)
        Created: 14.12.2004
        Creator: JV
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



    def setColor(self,r,g,b):
        """
        Method: setColor(r,g,b)
        Created: 03.11.2004
        Creator: KP
        Description: A method that sets the color of the dataUnit and updates
                     the preview and Set color-button accordingly

        """
        if self.dataUnit:
            self.dataUnit.setColor(r,g,b)
            self.preview.updateColor()
            self.doPreviewCallback()

            #self.colorBtn.SetBackgroundColour((r,g,b))
#        if self.colorChooser:
#            self.colorChooser.SetValue(wx.Colour(r,g,b))


    def updateSettings(self):
        """
        Method: updateSettings()
        Created: 03.11.2004
        Creator: KP
        Description: A method used to set the GUI widgets to their proper values
        """

        if self.dataUnit:
            self.iTFEditor.setIntensityTransferFunction(
            self.dataUnit.getIntensityTransferFunction(self.timePoint))
            tps=self.dataUnit.getInterpolationTimePoints()
	    
            for i in range(len(tps)):
                n=tps[i]
                # If there was nothing in the entry at this position, the 
                # value is -1 in that case, we leave the entry empty
                if n!=-1:
                    self.entries[i].SetValue(str(n))

            # median filtering
            self.doMedianCheckbutton.SetValue(self.dataUnit.getDoMedianFiltering())
            neighborhood=self.dataUnit.getNeighborhood()
            self.neighborhoodX.SetValue(str(neighborhood[0]))
            self.neighborhoodY.SetValue(str(neighborhood[1]))
            self.neighborhoodZ.SetValue(str(neighborhood[2]))

            # solitary filtering
            self.doSolitaryCheckbutton.SetValue(self.dataUnit.getRemoveSolitary())
            self.solitaryX.SetValue(str(
            self.dataUnit.getHorizontalSolitaryThreshold()))
            self.solitaryY.SetValue(str(
            self.dataUnit.getVerticalSolitaryThreshold()))
            self.solitaryThreshold.SetValue(str(
            self.dataUnit.getProcessingSolitaryThreshold()))

            self.doFilterCheckCallback()

    def updateFilterData(self):
        """
        Method: updateFilterData()
        Created: 13.12.2004
        Creator: JV
        Description: A method used to set the right values in dataset
                     from filter GUI widgets
        """

        self.dataUnit.setDoMedianFiltering(self.doMedianCheckbutton.GetValue())
        self.dataUnit.setRemoveSolitary(self.doSolitaryCheckbutton.GetValue())

        self.dataUnit.setNeighborhood(self.neighborhoodX.GetValue(),
                                      self.neighborhoodY.GetValue(),
                                      self.neighborhoodZ.GetValue())

        self.dataUnit.setHorizontalSolitaryThreshold(self.solitaryX.GetValue())
        self.dataUnit.setVerticalSolitaryThreshold(self.solitaryY.GetValue())
        self.dataUnit.setProcessingSolitaryThreshold(
        self.solitaryThreshold.GetValue())


    def doProcessingCallback(self):
        """
        Method: doProcessingCallback()
        Created: 03.11.2004
        Creator: KP
        Description: A callback for the button "Process Dataset Series"
        """
        self.updateFilterData()
        TaskWindow.TaskWindow.doOperation(self)

    def doPreviewCallback(self,event=None):
        """
        Method: doPreviewCallback()
        Created: 03.11.2004
        Creator: KP
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
        Created: 23.11.2004
        Creator: KP
        Description: Sets the processed dataunit that is to be processed.
                     It is then used to get the names of all the source data 
                     units and they are added to the listbox.
                     This is overwritten from taskwindow since we only process 
                     one dataunit here, not multiple source data units
        """
        self.dataUnit=dataUnit
        name=dataUnit.getName()
        print "Name of dataUnit=%s"%name
        self.taskName.SetValue(name)
        try:
            self.preview.setDataUnit(dataUnit)
        except GUIError, ex:
            ex.show()
        self.listbox.Unbind(EVT_LISTBOX)            
        names=[dataUnit.getName()]
        self.listbox.InsertItems(names,0)
        self.listbox.SetSelection(0)
        self.listbox.SetSize((40,120))
        
        #set the color of the colorBtn to the current color
        #self.colorBtn.SetBackgroundColour(self.dataUnit.getColor())
        r,g,b=self.dataUnit.getColor()
        if self.colorChooser:
            self.colorChooser.SetValue(wx.Colour(r,g,b))
        self.configSetting=self.dataUnit

        # We register a callback to be notified when the timepoint changes
        # We do it here because the timePointChanged() code requires the dataunit
        self.preview.setTimePointCallback(self.timePointChanged)

        self.iTFEditor.setIntensityTransferFunction(
        self.configSetting.getIntensityTransferFunction(self.timePoint))
        self.iTFEditor.updateCallback=self.doPreviewCallback
        
        self.updateSettings()
