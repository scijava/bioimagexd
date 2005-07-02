#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: ColocalizationPanel
 Project: BioImageXD
 Created: 03.11.2004, KP
 Description:

 A wx.Python wx.Dialog window that is used to control the settings for the
 colocalization module. Expects to be handed a ColocalizationDataUnit()
 containing the datasets from which the colocalization map is generated.
 Uses the PreviewFrame for previewing.

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
__author__ = "BioImageXD Project <http://www.bioimagexd.org>"
__version__ = "$Revision: 1.40 $"
__date__ = "$Date: 2005/01/13 14:52:39 $"

import os.path

from PreviewFrame import *
from ColorSelectionDialog import *
from Logging import *
import Scattergram
import ImageOperations
import sys
import Colocalization
import time

from GUI import Events

import TaskPanel
print TaskPanel,dir(TaskPanel)

infoString="""<html><body bgcolor=%(bgcolor)s">
<table>
<tr><td>Colocalization amount:</td><td>%(amount)d voxels</td></tr>
<tr><td>Least voxels over the thresholds:</td><td>%(least)d voxels</td></tr>
<tr><td>Colocalization percent:</td><td>%(percent).3f</td></tr>
<tr><td>Pearson's Correlation:</td><td>%(pearson).3f</td></tr>
<tr><td>Overlap Coefficient:</td><td>%(overlap).3f</td></tr>
<tr><td>Overlap coefficient k1:</td><td>%(k1).3f</td></tr>
<tr><td>Overlap coefficient k2:</td><td>%(k2).3f</td></tr>
<tr><td>Colocalization coefficient m1:</td><td>%(m1).3f</td></tr>
<tr><td>Colocalization coefficient m2:</td><td>%(m2).3f</td></tr>
</table>
</body></html>
"""    

class ColocalizationPanel(TaskPanel.TaskPanel):
    """
    Class: ColocalizationPanel
    Created: 03.11.2004, KP
    Description: A window for controlling the settings of the
                 colocalization module
    """
    def __init__(self,root,tb):
        """
        Method: __init__(root)
        Created: 03.11.2004
        Creator: KP
        Description: Initialization
        Parameters:
                root    Is the parent widget of this window
        """
        self.scatterGram=None
        self.htmlpage=None
        TaskPanel.TaskPanel.__init__(self,root,tb)
        self.operationName="Colocalization"
        
        self.SetTitle("Colocalization")
    
        self.mainsizer.Layout()
        self.mainsizer.Fit(self)
        
    def updateHtmlPage(self):
        """
        Method: updateHtmlPage()
        Created: 31.03.2005, KP
        Description: Updates the html page
        """
        if not self.htmlpage:
            return
        if not self.settings:
            print "No settings present"
            percent,amnt,pearson,overlap,k1,k2,m1,m2,least=0,0,0,0,0,0,0,0,0
            
        else:
            amnt=self.settings.get("ColocalizationAmount")
            pearson=self.settings.get("PearsonsCorrelation")
            overlap=self.settings.get("OverlapCoefficient")
            k1=self.settings.get("OverlapCoefficientK1")
            k2=self.settings.get("OverlapCoefficientK2")
            m1=self.settings.get("ColocalizationCoefficientM1")
            m2=self.settings.get("ColocalizationCoefficientM2")
            least=self.settings.get("ColocalizationLeastVoxelsOverThreshold")
            if least==0:
                percent = 0
            else:
                percent=(float(amnt) / float(least))*100.0
        col=self.GetBackgroundColour()
        bgcol="#%2x%2x%2x"%(col.Red(),col.Green(),col.Blue())
        variables={"amount":amnt,"pearson":pearson,"overlap":overlap,"k1":k1,"k2":k2,"m1":m1,"m2":m2,"bgcolor":bgcol,
        "least":least,"percent":percent}
 
        infostr=infoString%variables
        self.htmlpage.SetPage(infostr)
        

    

    def createButtonBox(self):
        """
        Method: createButtonBox()
        Created: 03.11.2004, KP
        Description: Creates a button box containing the buttons Render, 
                     Preview and Close
        """
        TaskPanel.TaskPanel.createButtonBox(self)
        self.processButton.SetLabel("Do Colocalization")
        self.processButton.Bind(wx.EVT_BUTTON,self.doColocalizationCallback)

    def createOptionsFrame(self):
        """
        Method: createOptionsFrame()
        Created: 03.11.2004, KP
        Description: Creates a frame that contains the various widgets
                     used to control the colocalization settings
        """
        TaskPanel.TaskPanel.createOptionsFrame(self)

        self.taskNameLbl.SetLabel("Colocalization name:")

        #self.colorChooser=ColorSelectionDialog(self.commonSettingsPanel,self.setColor)
        #self.commonSettingsSizer.Add(self.colorChooser,(1,0))
        self.paletteLbl = wx.StaticText(self,-1,"Channel palette:")
        self.commonSettingsSizer.Add(self.paletteLbl,(1,0))
        self.colorBtn = ColorTransferEditor.CTFButton(self)
        self.commonSettingsSizer.Add(self.colorBtn,(2,0))

        self.colocalizationPanel=wx.Panel(self.settingsNotebook,-1)
        self.colocalizationSizer=wx.GridBagSizer()
        
        self.depthLbl=wx.StaticText(self.colocalizationPanel,-1,"Colocalization Depth:")
        self.colocalizationSizer.Add(self.depthLbl,(0,0))
   
        self.depthMenu=wx.Choice(self.colocalizationPanel,-1,choices=["1-bit","8-bit"])
        self.colocalizationSizer.Add(self.depthMenu,(1,0))
        self.depthMenu.Bind(wx.EVT_CHOICE,self.updateBitDepth)

        self.lowerThresholdLbl=wx.StaticText(self.colocalizationPanel,-1,"Lower threshold:")
        self.upperThresholdLbl=wx.StaticText(self.colocalizationPanel,-1,"Upper threshold:")
        
        self.lowerthreshold=wx.Slider(self.colocalizationPanel,value=128,minValue=1,maxValue=255,size=(300,-1),
        style=wx.SL_HORIZONTAL|wx.SL_AUTOTICKS|wx.SL_LABELS)
        self.lowerthreshold.Bind(wx.EVT_SCROLL,self.updateThreshold)
        self.upperthreshold=wx.Slider(self.colocalizationPanel,value=128,minValue=1,maxValue=255,size=(300,-1),
        style=wx.SL_HORIZONTAL|wx.SL_AUTOTICKS|wx.SL_LABELS)
        self.upperthreshold.Bind(wx.EVT_SCROLL,self.updateThreshold)
        
        self.colocalizationSizer.Add(self.lowerThresholdLbl,(2,0))
        self.colocalizationSizer.Add(self.lowerthreshold,(3,0))
        self.colocalizationSizer.Add(self.upperThresholdLbl,(4,0))
        self.colocalizationSizer.Add(self.upperthreshold,(5,0))

        self.scatterGram=Scattergram.Scattergram(self.colocalizationPanel,size=(256,256))
        self.scatterGram.setTimepoint(0)
        self.Bind(Scattergram.EVT_THRESHOLD_CHANGED,self.updateSettings,id=self.scatterGram.GetId())
        self.colocalizationSizer.Add(self.scatterGram,(6,0))

        self.htmlpage=wx.html.HtmlWindow(self.colocalizationPanel,-1,size=(400,200))
        if "gtk2" in wx.PlatformInfo:
            self.htmlpage.SetStandardFonts()        
        self.colocalizationSizer.Add(self.htmlpage,(7,0))
        self.updateHtmlPage()
        
        self.colocalizationPanel.SetSizer(self.colocalizationSizer)
        self.colocalizationPanel.SetAutoLayout(1)
        
        self.settingsNotebook.AddPage(self.colocalizationPanel,"Colocalization")
        
    def updateZSlice(self,event):
        """
        Method: updateZSlice(event)
        Created: 25.03.2005, KP
        Description: A callback function called when the zslice is changed
        """
        if self.scatterGram:
            self.scatterGram.setZSlice(event.getValue())
            self.scatterGram.update()
            self.updateHtmlPage()

    def updateTimepoint(self,event):
        """
        Method: updateTimepoint(event)
        Created: 25.03.2005, KP
        Description: A callback function called when the zslice is changed
        """
        print "UpdateTimepoint"
        if self.scatterGram:
            self.scatterGram.setTimepoint(event.getValue())            
            self.scatterGram.update()


            
    def updateThreshold(self,event):
        """
        Method: updateThreshold(event)
        Created: 03.11.2004, KP
        Description: A callback function called when the threshold is 
        configured via the slider
        """
        # We might get called before any channel has been selected. 
        # In that case, do nothing
        if self.settings:
            oldlthreshold=self.settings.get("ColocalizationLowerThreshold")
            olduthreshold=self.settings.get("ColocalizationUpperThreshold")
            newlthreshold=int(self.lowerthreshold.GetValue())
            newuthreshold=int(self.upperthreshold.GetValue())
            self.settings.set("ColocalizationLowerThreshold",newlthreshold)
            self.settings.set("ColocalizationUpperThreshold",newuthreshold)            
            if (oldlthreshold != newlthreshold) or (olduthreshold != newuthreshold):
                self.doPreviewCallback()

    def updateSettings(self,event=None):
        """
        Method: updateSettings()
        Created: 03.11.2004, KP
        Description: A method used to set the GUI widgets to their proper values
                     based on the selected channel, the settings of which are 
                     stored in the instance variable self.settings
        """
        print "UPDATESETTINGS"
        if self.settings:
            format = self.settings.get("ColocalizationDepth")
            formattable={1:0,8:1,32:2}
            format=formattable[format]
            self.depthMenu.SetSelection(format)
            print "Settings.n=",self.settings.n
            #for key in self.settings.settings.keys():
            #    if "Threshold" in key:
            #        print key,self.settings.settings[key]
            
            th=self.settings.get("ColocalizationLowerThreshold")
            if th != None:
                self.lowerthreshold.SetValue(th)
            th=self.settings.get("ColocalizationUpperThreshold")
            if th != None:
                self.upperthreshold.SetValue(th)
            
        if self.dataUnit and self.settings:
            ctf = self.settings.get("ColocalizationColorTransferFunction")
            if ctf and self.colorBtn:
                print "Setting colorBtn.ctf"
                self.colorBtn.setColorTransferFunction(ctf)
                self.colorBtn.Refresh()

    def doColocalizationCallback(self,event):
        """
        Method: doColocalizationCallback()
        Created: 03.11.2004
        Creator: KP
        Description: A callback for the button "Do colocalization"
        """
        self.updateBitDepth()
        TaskPanel.TaskPanel.doOperation(self)

    def updateBitDepth(self,event=None):
        """
        Method: updateBitDepth(event)
        Created: 17.11.2004, KP
        Description: Updates the preview to be done at the selected depth
        """
        if self.settings and self.settings.get("Type")=="ColocalizationSettings":
            depth=self.depthMenu.GetSelection()
            table=[1,8,32]
            self.settings.set("ColocalizationDepth",table[depth])

    def doPreviewCallback(self,event=None):
        """
        Method: doPreviewCallback()
        Created: 03.11.2004, KP
        Description: A callback for the button "Preview" and other events
                     that wish to update the preview
        """
        self.updateBitDepth()
        TaskPanel.TaskPanel.doPreviewCallback(self,event)
        if self.scatterGram:
            #self.scatterGram.setZSlice(self.preview.z)
            self.scatterGram.setZSlice(0)
            #self.scatterGram.setTimepoint(self.preview.timePoint)
            self.scatterGram.update()
        self.updateHtmlPage()
        
    def setCombinedDataUnit(self,dataUnit):
        """
        Method: setCombinedDataUnit(dataUnit)
        Created: 25.03.2005, KP
        Description: Set the dataunit used by scattergram
        """
        TaskPanel.TaskPanel.setCombinedDataUnit(self,dataUnit)
        self.scatterGram.setDataunit(dataUnit)
        ctf = self.settings.get("ColocalizationColorTransferFunction")
        if self.colorBtn:
            self.colorBtn.setColorTransferFunction(ctf)

    def timePointChanged(self,event):
        """
        Method: timePointChanged(timepoint)
        Created: 30.03.2005, KP
        Description: A callback that is called when the previewed timepoint
                     changes.
        Parameters:
                event   Event object who'se getValue() returns the timepoint
        """

        tp=event.getValue()
        print "timePointChanged",tp
        self.scatterGram.setTimepoint(tp)
        
    def createItemToolbar(self):
        """
        Method: createItemToolbar()
        Created: 31.03.2005, KP
        Description: Method to create a toolbar for the window that allows use to select processed channel
        """      
        n=TaskPanel.TaskPanel.createItemToolbar(self)
        
        coloc=vtk.vtkImageColocalizationFilter()
        coloc.SetOutputDepth(8)
        i=0
        for dataunit in self.dataUnit.getSourceDataUnits():
            coloc.AddInput(dataunit.getTimePoint(0))
            coloc.SetColocalizationLowerThreshold(i,10)
            coloc.SetColocalizationUpperThreshold(i,255)
            i=i+1
        coloc.Update()
        ctf=vtk.vtkColorTransferFunction()
        ctf.AddRGBPoint(0,0,0,0)
        ctf.AddRGBPoint(255,1,1,1)
        bmp=ImageOperations.vtkImageDataToPreviewBitmap(coloc.GetOutput(),ctf,30,30)
        dc= wx.MemoryDC()

        dc.SelectObject(bmp)
        dc.BeginDrawing()
        val=[0,0,0]
        ctf.GetColor(255,val)
        dc.SetBrush(wx.TRANSPARENT_BRUSH)
        r,g,b=val
        r*=255
        g*=255
        b*=255
        dc.SetPen(wx.Pen(wx.Colour(r,g,b),4))
        dc.DrawRectangle(0,0,32,32)
        dc.EndDrawing()
        dc.SelectObject(wx.EmptyBitmap(0,0))
        toolid=wx.NewId()
        n=n+1
        name="Colocalization"
        self.toolMgr.addItem(name,bmp,toolid,lambda e,x=n,s=self:s.selectItem(e,x))
        
