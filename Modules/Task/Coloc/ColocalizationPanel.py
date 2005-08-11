# -*- coding: iso-8859-1 -*-
"""
 Unit: ColocalizationPanel
 Project: BioImageXD
 Created: 03.11.2004, KP
 Description:

 A window that is used to control the settings for the
 colocalization module. Expects to be handed a ColocalizationDataUnit()
 containing the datasets from which the colocalization map is generated.

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
import csv
import time
import messenger
import Dialogs
from GUI import Events
from PreviewFrame import *

from Logging import *
from GUI import Scatterplot
from lib import ImageOperations
import sys
import Colocalization
import time

import string
import UIElements

from GUI import ColorTransferEditor

from GUI import TaskPanel

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
        self.scatterPlot=None
        
        self.timePoint=0
        TaskPanel.TaskPanel.__init__(self,root,tb)
        self.operationName="Colocalization"
        
        self.SetTitle("Colocalization")
    
        self.mainsizer.Layout()
        self.mainsizer.Fit(self)
        messenger.connect(None,"timepoint_changed",self.updateTimepoint)
        messenger.connect(None,"zslice_changed",self.updateZSlice)
        messenger.connect(None,"threshold_changed",self.updateSettings)
        
        
        #wx.FutureCall(500,self.getAutoThreshold)
        
    def updateListCtrl(self):
        """
        Method: updateListCtrl
        Created: 12.07.2005, KP
        Description: Updates the list ctrl
        """
        fs="%.2f%%"
        fs2="%.4f"
        ds="%d"
        ss="%s"
        offset=-2
        coloffset=1
        n=2
        mapping={ "Ch1Th":(n,0,ss),
                  "Ch2Th":(n+1,0,ss),
                  "PValue":(n+2,0,fs2),
                  "ColocAmount":(n+3,0,ds),
                  "ColocPercent":(n+4,0,fs,100),
                  "PercentageVolumeCh1":(n+5,0,fs,100),
                  "PercentageMaterialCh1":(n+5,1,fs,100),
                  "PercentageVolumeCh2":(n+6,0,fs,100),
                  "PercentageMaterialCh2":(n+6,1,fs,100),
                  "PearsonWholeImage":(n+7,0,fs2),
                  "PearsonImageAbove":(n+7,1,fs2),
                  "PearsonImageBelow":(n+8,0,fs2),
#                  "M1":(9,0,fs2),
#                  "M2":(10,0,fs2),
                  "ThresholdM1":(n+9,0,fs2),
                  "ThresholdM2":(n+10,0,fs2),
                  "K1":(n+11,0,fs2),
                  "K2":(n+12,0,fs2),
                  
                  "SumCh1":(n+13,0,ds),
                  "SumOverThresholdCh1":(n+13,1,ds),
                  "SumCh2":(n+14,0,ds),
                  "SumOverThresholdCh2":(n+14,1,ds)
        }
        
        sources=[]
        if self.dataUnit:
            sources=self.dataUnit.getSourceDataUnits()                  
        for item in mapping.keys():
            val=0.0
            if item == "Ch1Th":
                if sources:
                    th1=sources[0].getSettings().get("ColocalizationLowerThreshold")
                    th2=sources[0].getSettings().get("ColocalizationUpperThreshold")                
                    val="%d / %d"%(th1,th2)
                else:
                    val="0 / 128"
            elif item == "Ch2Th":
                if sources:
                    th1=sources[1].getSettings().get("ColocalizationLowerThreshold")
                    th2=sources[1].getSettings().get("ColocalizationUpperThreshold")
                    val="%d / %d"%(th1,th2)
                else:
                    val="0 / 128"
            elif self.settings:
                val=self.settings.get(item)
            if not val:val=0
            try:
                index,col,format,scale=mapping[item]
            except:
                index,col,format=mapping[item]
                scale=1
            index+=offset
            col+=coloffset
            val*=scale
            self.listctrl.SetStringItem(index,col,format%val)

    def getAutoThreshold(self,event=None):
        """
        Method: getAutoThreshold
        Created: 11.07.2004, KP
        Description: Use vtkAutoThresholdColocalization to determine thresholds
                     for colocalization and calculate statistics
        """
        self.dataUnit.getSourceDataUnits()[0].getSettings().set("CalculateThresholds",1)
        self.eventDesc="Calculating thresholds"
        
        self.doPreviewCallback(event)
        self.dataUnit.getSourceDataUnits()[0].getSettings().set("CalculateThresholds",0) 
        messenger.send(None,"threshold_changed")
        
        pos=self.radiobox.GetSelection()
        if pos:
            map=[1,0,2]
            method=map[pos-1]
            self.getPValue(method)
        
        
    def getPValue(self,method=1):
        """
        Method: getPValue
        Created: 13.07.2005, KP
        Description: Get the P value for colocalization
        """
        coloctest=vtk.vtkImageColocalizationTest()
        sources=self.dataUnit.getSourceDataUnits()
        self.eventDesc="Calculating P-Value"
        methods=["Fay","Costes","van Steensel"]
        Logging.info("Using %s method (%d)"%(methods[method],method),kw="processing")
    
        coloctest.SetMethod(method)
        coloctest.SetManualPSFSize(10)
        coloctest.SetNumIterations(100)
        
        for i in sources:
            data=i.getTimePoint(self.timePoint)
            coloctest.AddInput(data)
        coloctest.AddObserver("ProgressEvent",self.updateProgress)
        print "Running..."
        coloctest.Update()
        set=sources[0].getSettings().set
        for i in ["PValue","RObserved","RRandMean","RRandSD",
                  "NumIterations","ColocCount","Method"]:
            val=eval("coloctest.Get%s()"%i)
            set(i,val)
        messenger.send(None,"update_progress",100,"Done.")
        self.updateListCtrl()
        
        
    def updateProgress(self,obj,evt,*args):
        """
        Method: updateProgress
        Created: 13.07.2005, KP
        Description: Sends a update_progress event and yields time for the GUI
        """
        wx.GetApp().Yield(1)
        progress=obj.GetProgress()
        txt=obj.GetProgressText()
        if not txt:txt=self.eventDesc
        messenger.send(None,"update_progress",progress,txt)
        
    def createButtonBox(self):
        """
        Method: createButtonBox()
        Created: 03.11.2004, KP
        Description: Creates a button box containing the buttons Render, 
                     Preview and Close
        """
        TaskPanel.TaskPanel.createButtonBox(self)
        #self.processButton.SetLabel("Do Colocalization")
        self.processButton.Bind(wx.EVT_BUTTON,self.doColocalizationCallback)
 
    def createOptionsFrame(self):
        """
        Method: createOptionsFrame()
        Created: 03.11.2004, KP
        Description: Creates a frame that contains the various widgets
                     used to control the colocalization settings
        """
        TaskPanel.TaskPanel.createOptionsFrame(self)

        self.colocalizationPanel=wx.Panel(self.settingsNotebook,-1)
        self.colocalizationSizer=wx.GridBagSizer()
        n=0
        #self.depthLbl=wx.StaticText(self.colocalizationPanel,-1,"Colocalization Depth:")
        #self.colocalizationSizer.Add(self.depthLbl,(n,0))
        #n+=1
        #self.depthMenu=wx.Choice(self.colocalizationPanel,-1,choices=["1-bit","8-bit"])
        #self.colocalizationSizer.Add(self.depthMenu,(n,0))
        #n+=1
        #self.depthMenu.Bind(wx.EVT_CHOICE,self.updateBitDepth)

        self.lowerThresholdLbl=wx.StaticText(self.colocalizationPanel,-1,"Lower threshold:")
        self.upperThresholdLbl=wx.StaticText(self.colocalizationPanel,-1,"Upper threshold:")
        
        self.lowerthreshold=wx.Slider(self.colocalizationPanel,value=128,minValue=1,maxValue=255,size=(300,-1),
        style=wx.SL_HORIZONTAL|wx.SL_LABELS)
        self.lowerthreshold.Bind(wx.EVT_SCROLL,self.updateThreshold)
        self.upperthreshold=wx.Slider(self.colocalizationPanel,value=128,minValue=1,maxValue=255,size=(300,-1),
        style=wx.SL_HORIZONTAL|wx.SL_LABELS)
        self.upperthreshold.Bind(wx.EVT_SCROLL,self.updateThreshold)
        
        self.colocalizationSizer.Add(self.lowerThresholdLbl,(n,0))
        n+=1
        self.colocalizationSizer.Add(self.lowerthreshold,(n,0))
        n+=1
        self.colocalizationSizer.Add(self.upperThresholdLbl,(n,0))
        n+=1
        self.colocalizationSizer.Add(self.upperthreshold,(n,0))
        n+=1
        
        sbox=wx.StaticBox(self.colocalizationPanel,-1,"2D histogram")
        box=wx.StaticBoxSizer(sbox,wx.VERTICAL)
        self.scatterPlot=Scatterplot.Scatterplot(self.colocalizationPanel,size=(256,256))
        box.Add(self.scatterPlot)
        self.colocalizationSizer.Add(box,(n,0))
        n+=1
        
        sbox=wx.StaticBox(self.colocalizationPanel,-1,"Automatic threshold")
        box=wx.StaticBoxSizer(sbox,wx.VERTICAL)
        self.radiobox=wx.RadioBox(self.colocalizationPanel,-1,"Calculate P-Value",
        choices=["None","Costes","Fay","van Steensel"],majorDimension=2,
        style=wx.RA_SPECIFY_COLS
        )
        box.Add(self.radiobox)
        
        self.thresholdButton=wx.Button(self.colocalizationPanel,-1,"Calculate")
        self.thresholdButton.Bind(wx.EVT_BUTTON,self.getAutoThreshold)
        box.Add(self.thresholdButton)        

        self.colocalizationSizer.Add(box,(n,0),flag=wx.EXPAND|wx.LEFT|wx.RIGHT)
        n+=1
        

        
        sbox=wx.StaticBox(self.colocalizationPanel,-1,"Coloc Volume Statistics")
        box=wx.StaticBoxSizer(sbox,wx.VERTICAL)
        self.listctrl=wx.ListCtrl(self.colocalizationPanel,-1,size=(350,300),
        style=wx.BORDER_RAISED|wx.LC_REPORT)
        box.Add(self.listctrl)
        self.statsButton=wx.Button(self.colocalizationPanel,-1,"Export")
        self.statsButton.Bind(wx.EVT_BUTTON,self.onExportStatistics)
        box.Add(self.statsButton)

        self.populateListCtrl()
        
        self.updateListCtrl()
        self.colocalizationSizer.Add(box,(n,0))
        n+=1
        sbox=wx.StaticBox(self.colocalizationPanel,-1,"Colocalization color")
        sboxsizer=wx.StaticBoxSizer(sbox,wx.VERTICAL)
        self.colorBtn = ColorTransferEditor.CTFButton(self.colocalizationPanel)
        sboxsizer.Add(self.colorBtn)

        val=UIElements.AcceptedValidator
 
        self.constColocCheckbox=wx.CheckBox(self.colocalizationPanel,-1,"Use single (1-bit) value for colocalization")
        self.constColocValue=wx.TextCtrl(self.colocalizationPanel,-1,"255",
                                    validator=val(string.digits,below=255))
        self.constColocValue.Enable(0)

        self.constColocCheckbox.Bind(wx.EVT_CHECKBOX,
        lambda e,s=self,v=self.constColocValue:v.Enable(e.IsChecked()))
        
        sboxsizer.Add(self.constColocCheckbox)
        sboxsizer.Add(self.constColocValue)
        
        self.colocalizationSizer.Add(sboxsizer,(n,0))
        n+=1
        
        
        self.colocalizationPanel.SetSizer(self.colocalizationSizer)
        self.colocalizationPanel.SetAutoLayout(1)
        
        self.settingsNotebook.AddPage(self.colocalizationPanel,"Colocalization")

    def onExportStatistics(self,event):
        """
        Method: onExportStatistics
        Created: 13.07.2005, KP
        Description: Export colocalization statistics to file
        """
        name=self.dataUnit.getName()
        sources=self.dataUnit.getSourceDataUnits()
        names=[]
        for i in sources:
            names.append(i.getName())
        namestr=" and ".join(names)
        filename=Dialogs.askSaveAsFileName(self,"Save colocalization statistics as","%s.csv"%name,"CSV File (*.csv)|*.csv")

        if not filename:
            Logging.info("Got no name for coloc statistics",kw="processing")
            return
        f=open(filename,"wb")
        w=csv.writer(f)
        get1=sources[0].getSettings().get
        get2=sources[1].getSettings().get

        w.writerow(["Statistics for colocalization","Channels %s"%namestr])
        w.writerow([time.ctime()])
        w.writerow(["","Channel 1","Channel 2"])
        w.writerow([""]+names)
        w.writerow(["Sum of channel",get1("SumCh1"),get2("SumCh2")])
        w.writerow(["Sum of voxels > threshold",get1("SumOverThresholdCh1"),get2("SumOverThresholdCh2")])

        lows=["Lower threshold"]
        ups=["Upper threshold"]
        for i in sources:
            settings=i.getSettings()
            lower=settings.get("ColocalizationLowerThreshold")
            upper=settings.get("ColocalizationUpperThreshold")
            lows.append(lower)
            ups.append(upper)
        w.writerow(lows)
        w.writerow(ups)
        
        w.writerow(["Number of colocalized voxels",get1("ColocAmount")])
        w.writerow(["% of volume colocalized",100*get1("ColocPercent")])
        w.writerow(["Correlation (total)",get1("PearsonWholeImage")])
        w.writerow(["Correlation (voxels > threshold)",get1("PearsonImageAbove")])
        w.writerow(["Correlation (voxels < threshold)",get1("PearsonImageBelow")])
        w.writerow([""])
        w.writerow([""]+names)
        w.writerow(["% of channel colocalized",100*get1("PercentageVolumeCh1"),100*get2("PercentageVolumeCh2")])
        w.writerow(["% of channel colocalized (voxels > threshold)",100*get1("PercentageMaterialCh1"),100*get2("PercentageMaterialCh2")])
        w.writerow(["Manders' coefficient m1 / m2",get1("M1"),get2("M2")])
        w.writerow(["Manders' coefficient M1 / M2 (voxels > threshold)",get1("ThresholdM1"),get2("ThresholdM2")])
        w.writerow(["Overlap coefficient k1 / k2",get1("K1"),get2("K2")])        
        w.writerow([""])
        mapping=["Fay's","Costes'","van Steensel's"]
        method=get1("Method")
        if method != None:
            w.writerow(["P-Value (%s method)"%mapping[method],get1("PValue")])
        w.writerow(["Correlation (observed)",get1("RObserved")])
        w.writerow(["Mean of Correlation (randomized)",get1("RRandMean")])
        w.writerow(["Standard deviation of Correlation (randomized)",get1("RRandSD")])
        if method==1:
            w.writerow(["PSF width (px)",get1("PSF")])
        its=get1("NumIterations")
        cc=get1("ColocCount")
        perc=(its-cc)/float(its)
        w.writerow(["Number of iterations",get1("NumIterations")])
        w.writerow(["# of iterations where R(rand) > R(obs)",(its-cc)])
        w.writerow(["% of iterations where R(rand) > R(obs)",perc])
        f.close()


        
    def populateListCtrl(self):
        """
        Method: populateListCtrl
        Created: 12.07.2005, KP
        Description: Add information to the list control
        """
        self.listctrl.InsertColumn(0,"Quantity")
        self.listctrl.InsertColumn(1,"Total")
        self.listctrl.InsertColumn(2,"Over threshold")
        
        self.listctrl.SetColumnWidth(0,180)
        self.listctrl.SetColumnWidth(1,60)
        self.listctrl.SetColumnWidth(2,120)
        n=0
        self.listctrl.InsertStringItem(n,"Ch1 Lower / Upper threshold")
        n+=1
        self.listctrl.InsertStringItem(n,"Ch2 Lower / Upper threshold")
        n+=1
        self.listctrl.InsertStringItem(n,"P-Value")
        n+=1
        self.listctrl.InsertStringItem(n,"# of colocalized voxels")
        n+=1
        self.listctrl.InsertStringItem(n,"% of volume colocalized")
        n+=1
        self.listctrl.InsertStringItem(n,"% of ch 1 colocalized")
        n+=1
        self.listctrl.InsertStringItem(n,"% of ch 2 colocalized")
        n+=1
        self.listctrl.InsertStringItem(n,"Correlation")
        n+=1
        self.listctrl.InsertStringItem(n,"Correlation (<threshold)")
        n+=1
        self.listctrl.InsertStringItem(n,"M1")
        n+=1
        self.listctrl.InsertStringItem(n,"M2")
        n+=1
        self.listctrl.InsertStringItem(n,"K1")
        n+=1
        self.listctrl.InsertStringItem(n,"K2")
        n+=1
        self.listctrl.InsertStringItem(n,"Sum of channel 1")
        n+=1
        self.listctrl.InsertStringItem(n,"Sum of channel 2")
        
    def updateZSlice(self,obj,event,zslice):
        """
        Method: updateZSlice(event)
        Created: 25.03.2005, KP
        Description: A callback function called when the zslice is changed
        """
        if self.scatterPlot:
            self.scatterPlot.setZSlice(zslice)
            self.scatterPlot.updatePreview()
            self.updateListCtrl()

    def updateTimepoint(self,obj,event,timePoint):
        """
        Method: updateTimepoint(event)
        Created: 25.03.2005, KP
        Description: A callback function called when the zslice is changed
        """
        self.timePoint=timePoint
        if self.scatterPlot:
            self.scatterPlot.setTimepoint(self.timePoint)
            self.scatterPlot.updatePreview()
            
    def updateThreshold(self,event):
        """
        Method: updateThreshold(event)
        Created: 03.11.2004, KP
        Description: A callback function called when the threshold is configured via the slider
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
                messenger.send(None,"threshold_changed")                
                self.doPreviewCallback()
                

    def updateSettings(self,*args):
        """
        Method: updateSettings()
        Created: 03.11.2004, KP
        Description: A method used to set the GUI widgets to their proper values
                     based on the selected channel, the settings of which are 
                     stored in the instance variable self.settings
        """
        if self.settings:
            format = self.settings.get("ColocalizationDepth")
            scalar = self.settings.get("OutputScalar")
            self.constColocCheckbox.SetValue(format==1)
            self.constColocValue.SetValue("%d"%scalar)
            
            th=self.settings.get("ColocalizationLowerThreshold")
            if th != None:
                self.lowerthreshold.SetValue(th)
            th=self.settings.get("ColocalizationUpperThreshold")
            if th != None:
                self.upperthreshold.SetValue(th)
            
        if self.dataUnit and self.settings:
            ctf = self.dataUnit.getSettings().get("ColorTransferFunction")
            if ctf and self.colorBtn:
                Logging.info("Setting colorBtn.ctf=",ctf,kw="ctf")
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
        if self.settings:
            #depth=self.depthMenu.GetSelection()
            #table=[1,8,32]
            #self.settings.set("ColocalizationDepth",table[depth])
            if self.constColocCheckbox.GetValue():
                self.settings.set("ColocalizationDepth",1)
                colocval=self.constColocValue.GetValue()
                colocval=int(colocval)
                self.settings.set("OutputScalar",colocval)
            else:
                self.settings.set("ColocalizationDepth",8)
            

    def doPreviewCallback(self,event=None,*args):
        """
        Method: doPreviewCallback()
        Created: 03.11.2004, KP
        Description: A callback for the button "Preview" and other events
                     that wish to update the preview
        """
        self.updateBitDepth()
        TaskPanel.TaskPanel.doPreviewCallback(self,event)
        if self.scatterPlot:
            #self.scatterPlot.setZSlice(self.preview.z)
            self.scatterPlot.setZSlice(0)
            self.scatterPlot.setTimepoint(self.timePoint)
            self.scatterPlot.updatePreview()
        ctf = self.dataUnit.getSettings().get("ColorTransferFunction")
        self.dataUnit.getSettings().set("ColocalizationColorTransferFunction",ctf)            
        self.updateListCtrl()
        
    def setCombinedDataUnit(self,dataUnit):
        """
        Method: setCombinedDataUnit(dataUnit)
        Created: 25.03.2005, KP
        Description: Set the dataunit used by scatterplot
        """
        TaskPanel.TaskPanel.setCombinedDataUnit(self,dataUnit)
        #self.scatterPlot.setDataunit(dataUnit)
        # See if the dataunit has a stored colocalizationctf
        # then use that.
        ctf=self.dataUnit.getSettings().get("ColocalizationColorTransferFunction")
        if not ctf:
            ctf = self.dataUnit.getSettings().get("ColorTransferFunction")
        else:
            Logging.info("Using ColocalizationColorTransferFunction",kw="task")
        if self.colorBtn:
            self.colorBtn.setColorTransferFunction(ctf)
        self.scatterPlot.setDataUnit(dataUnit)
        self.colocalizationPanel.Layout()
        
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
        #n=n+1
        name="Colocalization"
        self.toolMgr.addItem(name,bmp,toolid,lambda e,x=n,s=self:s.setPreviewedData(e,x))        
        
        for i,tid in enumerate(self.toolIds):
            self.dataUnit.setOutputChannel(i,0)
            self.toolMgr.toggleTool(tid,0)
        
        self.dataUnit.setOutputChannel(len(self.toolIds),1)
        self.toolIds.append(toolid)
        self.toolMgr.toggleTool(toolid,1)
