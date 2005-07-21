#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: SurfaceConstructionPanel
 Project: BioImageXD
 Created: 25.11.2004, JV
 Description:

 A wxPython Toplevel window that is used to process a single dataset series with
 VSIA.
 (write this)
 Modified from SingleUnitProcessingWindow

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
__version__ = "$Revision: 1.23 $"
__date__ = "$Date: 2005/01/14 09:23:07 $"

from Tkinter import *
import os.path
import Dialogs

from PreviewFrame import *
import GUI.IntensityTransferEditor
from GUI.IntensityTransferEditor import *
from Logging import *

import sys
import time

from GUI import TaskPanel


class SurfaceConstructionpanel(TaskPanel.TaskPanel):
    """
    Class: VSIAWindow
    Created: 25.11.2004, JV
    Description: A window for processing a single dataunit
    """
    def __init__(self,root):
        """
        Method: __init__(root)
        Created: 25.11.2004, JV
        Creator: JV
        Description: Initialization
        Parameters:
                root    Is the parent widget of this window
        """
        self.frames={}
        self.oldFilter=None

        TaskPanel.TaskPanel.__init__(self,root)
        # Preview has to be generated here
        self.preview=VSIAPreview(self)
        self.preview.grid(row=0,column=0,sticky=N)
        self.optionsFrame2=Frame(self)
        self.optionsFrame2.grid(row=1,column=0,sticky=N)
        self.wm_title("Visualization for Sparse Intensity Aggregations")
        self.listbox.unbind('<ButtonRelease-1>')


    def createButtonBox(self):
        """
        Method: createButtonBox()
        Created: 25.11.2004, JV
        Description: Creates a button box containing the buttons Render,
                     Preview and Close
        """
        # change button text
        self.buttonbox=ButtonBox(self,ok="Do Visualization",cancel="Close",
        apply="Preview",cancel_command=self.closeWindowCallback,
        ok_command=self.doVSIACallback,apply_command=self.doPreviewCallback)
        self.buttonbox.grid(row=4,column=0,columnspan=2,sticky=W+E)

    def createOptionsFrame(self):
        """
        Method: createOptionsFrame()
        Created: 25.11.2004, JV
        Description: Creates a frame that contains the various widgets
                     used to control the VSIA settings
        """
        TaskPanel.TaskPanel.createOptionsFrame(self)

        self.lowerLimitVar=StringVar()
        self.upperLimitVar=StringVar()
        self.surfaceCountVar=StringVar()
        self.useExactValuesVar=IntVar()

        self.lowerLimit=Entry(self.optionFrame,textvariable=self.lowerLimitVar)
        self.upperLimit=Entry(self.optionFrame,textvariable=self.upperLimitVar)

        self.surfaceCount=Entry(self.optionFrame,
        textvariable=self.surfaceCountVar)
        self.surfaceCount.bind('<Return>',self.setSurfaceCount)
        
        self.lowerLimit.bind('<Key>',lambda x,
        self=self:self.after(100,self.updateFilterData))

        self.upperLimit.bind('<Key>',lambda x,
        self=self:self.after(100,self.updateFilterData))

        self.surfaceCount.bind('<Key>',lambda x,
        self=self:self.after(100,self.setSurfaceCount))

        self.useExactValues=Checkbutton(self.optionFrame,
        text="Select only exact values", variable=self.useExactValuesVar)
        
        self.useExactValues.bind('<Button-1>',lambda x,
        self=self:self.after(500,self.updateFilterData))


        self.lowerLimit.insert(0,0)
        self.upperLimit.insert(0,255)
        self.surfaceCount.insert(0,1)

        self.lowerLimitLbl=Label(self.optionFrame,
        text="Lower limit value:",anchor=W)
        
        self.upperLimitLbl=Label(self.optionFrame,
        text="Upper limit value:",anchor=W)

        self.surfaceCountLbl=Label(self.optionFrame,
        text="Surface count:",anchor=W)

        self.lowerLimit.grid(row=2,column=0,sticky=W+E)
        self.lowerLimitLbl.grid(row=1,column=0,sticky=W+E)

        self.upperLimit.grid(row=4,column=0,sticky=W+E)
        self.upperLimitLbl.grid(row=3,column=0,sticky=W+E)

        self.surfaceCount.grid(row=6,column=0,sticky=W+E)
        self.surfaceCountLbl.grid(row=5,column=0,sticky=W+E)

        self.useExactValues.grid(row=8,column=0,sticky=W+E)
        self.filterLbl=Label(self.optionFrame,text="Select processing method:",
        anchor=W)
        
        self.filterLbl.grid(row=9,column=0,sticky=W+E)
        self.filterVar=StringVar()
    	self.filterVar.set("Gaussian Splat")
        self.filterMenu=OptionMenu(self.optionFrame,self.filterVar,
        "Gaussian Splat","Shepard Method","Delaunay Triangulation",
        "Surface Reconstruction")

        self.filterMenu.grid(row=10,column=0,sticky=W)

        self.filterMenu.bind('<ButtonRelease-1>',lambda x,
        self=self:self.after(100,self.updateSelectedFilter))

        self.gaussianFrame=Frame(self.optionFrame)
        self.shepardFrame=Frame(self.optionFrame)
        self.delaunayFrame=Frame(self.optionFrame)
        self.surfaceFrame=Frame(self.optionFrame)

        self.frames={"Gaussian Splat":self.gaussianFrame,
                     "Shepard Method":self.shepardFrame,
                     "Delaunay Triangulation":self.delaunayFrame,
                     "Surface Reconstruction":self.surfaceFrame}


        self.radiusLbl=Label(self.gaussianFrame,text="Radius:",anchor=W)
        self.radiusVar=StringVar()
        self.radius=Entry(self.gaussianFrame,textvariable=self.radiusVar)
        self.radiusLbl.grid(row=0,column=0,sticky=W+E)
        self.radius.grid(row=1,column=0,sticky=W+E)
        self.radiusVar.set("0.0001")

        self.neighborhoodSizeLbl=Label(self.surfaceFrame,
        text="Neighborhood size:",anchor=W)
        
        self.neighborhoodSizeVar=StringVar()
        self.neighborhoodSize=Entry(self.surfaceFrame,
        textvariable=self.neighborhoodSizeVar)
        
        self.neighborhoodSizeLbl.grid(row=0,column=0,sticky=W+E)
        self.neighborhoodSize.grid(row=1,column=0,sticky=W+E)
        self.neighborhoodSizeVar.set("1")

        # Gaussian is the default

        self.updateSelectedFilter()



    def setSurfaceCount(self,event=None):
        """
        Method: setSurfaceCount()
        Created: 15.12.2004, KP
        Description: A callback for setting the surface count slider to reflect
                     the surface count
        """
        try:
            count=int(self.surfaceCount.get())
            self.preview.surfslider.config(from_=0,to=count-1)
            self.updateFilterData()
        except:
            pass

    def updateSelectedFilter(self,event=None):
        """
        Method: updateSelectedFilter()
        Created: 16.12.2004, KP
        Description: A callback for selecting which class to use to convert
                     the data back to imagedata
        """
        filterClass=self.filterVar.get()
        # We might get called before we have a dataunit, then just update the GUi
        if self.dataUnit:
            filterSettings=[]
            if self.filterVar.get()=="Gaussian Splat":
                filterSettings.append(float(self.radiusVar.get()))
            if self.filterVar.get()=="Surface Reconstruction":
                filterSettings.append(float(self.neighborhoodSizeVar.get()))

            self.dataUnit.setFilter(filterClass,filterSettings)

        if self.oldFilter:
            self.frames[self.oldFilter].grid_forget()

        self.frames[filterClass].grid(row=11)

        self.oldFilter=filterClass

    def timePointChanged(self,timePoint):
        """
        Method: timePointChanged(timepoint)
        Created: 24.11.2004, KP
        Description: A callback that is called when the previewed
                     timepoint changes.
        Parameters:
                timePoint   The timepoint we're previewing now
        """
        print "Now configuring timepoint %d"%(timePoint)
        self.timePoint=timePoint

    def updateSettings(self):
        """
        Method: updateSettings()
        Created: 03.11.2004, KP
        Description: A method used to set the GUI widgets to their proper values
        """
        print "self.dataUnit",self.dataUnit
        if self.dataUnit:
            print "Updating settings..."
            print "lower limit=",self.dataUnit.getLowerLimit()
            print "Upper limit=",self.dataUnit.getUpperLimit()
            print "ll=",self.dataUnit.lowerLimit
            self.lowerLimitVar.set(self.dataUnit.getLowerLimit())
            self.upperLimitVar.set(self.dataUnit.getUpperLimit())
            self.surfaceCountVar.set(self.dataUnit.getSurfaceCount())
            self.useExactValuesVar.set(int(self.dataUnit.getExactValues()))

            fclass,fsettings = self.dataUnit.getFilterAndSettings()

            print fclass, fsettings

            if fclass=="Gaussian Splat":
                self.filterVar.set(fclass)
                if len(fsettings):
                    self.radiusVar.set(str(fsettings[0]))
                else:
                    print "DID NOT GET SETTINGS"

            if fclass=="Surface Reconstruction":
                self.filterVar.set(fclass)
                if len(fsettings):
                    self.self.neighborhoodSizeVar.set(str(fsettings[0]))
                else:
                    print "DID NOT GET SETTINGS"


        self.updateSelectedFilter()

    def closeWindowCallback(self):
        """
        Method: closeWindow()
        Created: 03.11.2004, KP
        Description: A method that withdraws (i.e. hides) the window,
                     but does not destory it.
        """
        self.cancelled=1
        del self.preview
        self.destroy()

    def doVSIACallback(self):
        """
        Method: doVSIACallback()
        Created: 25.11.2004, JV
        Description: A callback for the button "Do VSIA"
        """
        name=self.nameVar.get()
        self.dataUnit.setName(name)
        initFile="%s.du"%(name)
        filename=tkFileDialog.asksaveasfilename(initialfile=initFile,
        title="Save processed dataset series as",
        filetypes=[("Data Unit file",".du")])
        
        if not filename:
            return
        if filename[-3:].lower()!=".du":
            filename+=".du"            
        # Set file path for returning to the mainwindow
        self.filePath=filename

        self.t1=time.time()
        if not self.progressMeter:
            self.progressMeter=Meter(self,relief=RIDGE,bd=3,fillcolor='lightblue')
            self.progressMeter.set(0,"Timepoint  /   (0%) ETA:   mins   seconds")
            self.progressMeter.grid(row=3,column=0,columnspan=2,sticky=W+E)

        self.grayOut()
        try:
            self.dataUnit.doProcessing(filename,self.updateProgressMeter)
        except GUIError,ex:
            ex.show()
            self.progressMeter.grid_forget()
            self.grayOut(1)
        else:
            # then we close this window...
            self.destroy()

    def updateFilterData(self):
        """
        Method: updateFilterData()
        Created: 15.12.2004, KP
        Description: A callback to update the module's parameters from the gui
        """
        lowerLimit=0
        upperLimit=0
        surfaceCount=0
        exactValues=0
        try: lowerLimit=int(self.lowerLimitVar.get())
        except: pass
        try: upperLimit=int(self.upperLimitVar.get())
        except: pass
        try: surfaceCount=int(self.surfaceCountVar.get())
        except: pass
        try: exactValues=int(self.useExactValuesVar.get())
        except: pass

        print "exact values=",exactValues
        print "Setting upperLimit=",upperLimit
        self.dataUnit.setLowerLimit(lowerLimit)
        self.dataUnit.setUpperLimit(upperLimit)
        self.dataUnit.setSurfaceCount(surfaceCount)
        self.dataUnit.setExactValues(exactValues)

        self.updateSelectedFilter()

    def doPreviewCallback(self,event=None):
        """
        Method: doPreviewCallback()
        Created: 25.11.2004, JV
        Description: A callback for the button "Preview" and other events
                     that wish to update the preview
        """
        self.updateFilterData()
        TaskPanel.TaskPanel.doPreviewCallback(self,event)

    def setCombinedDataUnit(self,dataUnit):
        """
        Method: setCombinedDataUnit(dataUnit)
        Created: 23.11.2004, KP
        Description: Sets the processed dataunit that is to be processed.
                     It is then used to get the names of all the source data
                     units and they are added to the listbox.
                     This is overwritten from TaskPanel since we
                     only process one dataunit here, not multiple
                     source data units
        """
        self.dataUnit=dataUnit
        name=dataUnit.getName()
        print "Name of dataUnit=%s"%name
        self.nameVar.set(name)
        self.preview.setDataUnit(dataUnit)
        name=dataUnit.getName()
        self.listbox.insert(END,name)
        self.listbox.select_set(0)
        self.configSetting=self.dataUnit

        # We register a callback to be notified when the timepoint changes
        # We do it here because the timePointChanged() code requires the dataunit
        self.preview.setTimePointCallback(self.timePointChanged)
        self.updateSettings()
