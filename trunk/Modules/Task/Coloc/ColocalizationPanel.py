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
import cStringIO
import messenger
import Dialogs
import codecs
from GUI import Events
from PreviewFrame import *

from Logging import *
from GUI import Scatterplot
from lib import ImageOperations
import sys
import types
import Colocalization
import time

import string
import UIElements
import Command

import  wx.lib.mixins.listctrl  as  listmix

from GUI import ColorTransferEditor

from GUI import TaskPanel


class MyListCtrl(wx.ListCtrl, listmix.TextEditMixin):
    def __init__(self, parent, ID, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        listmix.TextEditMixin.__init__(self) 

    def CloseEditor(self,row=0,col=0):
        self.editor.Hide()
        self.SetFocus()            
            
        
class ColocalizationPanel(TaskPanel.TaskPanel):
    """
    Created: 03.11.2004, KP
    Description: A window for controlling the settings of the
                 colocalization module
    """
    def __init__(self,parent,tb):
        """
        Created: 03.11.2004, KP
        Description: Initialization
        Parameters:
                root    Is the parent widget of this window
        """
        self.scatterPlot=None
        self.createItemSelection=1
        self.timePoint=0        
        self.beginner = wx.Colour(180,255,180)
        self.intermediate = wx.Colour(255,255,180)
        self.expert = wx.Colour(0,180,255)
        TaskPanel.TaskPanel.__init__(self,parent,tb, wantNotebook = 0)

        self.operationName="Colocalization"
        self.voxelSize=None
            
        self.mainsizer.Layout()
        self.mainsizer.Fit(self)
        messenger.connect(None,"timepoint_changed",self.updateTimepoint)
        messenger.connect(None,"zslice_changed",self.updateZSlice)
        messenger.connect(None,"threshold_changed",self.updateSettings)
        
        #wx.FutureCall(500,self.getAutoThreshold)
        
    def updateListCtrl(self):
        """
        Created: 12.07.2005, KP
        Description: Updates the list ctrl
        """
        fs="%.3f%%"
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
# volume = number of voxels (Imaris)
# material = intensity
                  "PercentageVolumeCh1":(n+5,0,ss),
#                  "PercentageMaterialCh1":(n+5,1,fs,100),
                  "PercentageVolumeCh2":(n+6,0,ss),
#                  "PercentageMaterialCh2":(n+6,1,fs,100),
                  "PercentageTotalCh1":(n+7,0,fs,100),
                  "PercentageTotalCh2":(n+8,0,fs,100),                  
                  "PearsonWholeImage":(n+9,0,fs2),
                  "PearsonImageAbove":(n+10,0,fs2),
                  "PearsonImageBelow":(n+11,0,fs2),
#                  "M1":(9,0,fs2),
#                  "M2":(10,0,fs2),
                  "ThresholdM1":(n+12,0,fs2),
                  "ThresholdM2":(n+13,0,fs2),
                  "SumCh1":(n+14,0,ss),
                  "SumCh2":(n+15,0,ss),
                  "NonZeroCh1":(n+16,0,ss),
                  "OverThresholdCh1":(n+17,0,ss),
                  "DiffStainVoxelsCh1":(n+18,0,ss),
                  "DiffStainVoxelsCh2":(n+19,0,ss),

                  "DiffStainPercentageCh1":(n+20,0,ss),
                  "DiffStainPercentageCh2":(n+21,0,ss),
                  "RObserved":(n+22,0,fs),
                  "RRandMean":(n+23,0,ss),
                  "NumIterations":(n+24,0,ss)
        }
     
        sources=[]
        if self.dataUnit:
            sources=self.dataUnit.getSourceDataUnits()                  
        for item in mapping.keys():
            val=0.0
            val1=""
            val2=""
                
            
            if item == "Ch1Th":
                if sources:
                    th1=sources[0].getSettings().get("ColocalizationLowerThreshold")
                    th2=sources[0].getSettings().get("ColocalizationUpperThreshold")                
                    val="%d / %d"%(th1,th2)
                    val1=th1
                    val2=th2
                else:
                    val="0 / 128"
                    val1=0
                    val2=128
            elif item == "Ch2Th":
                if sources:
                    th1=sources[1].getSettings().get("ColocalizationLowerThreshold")
                    th2=sources[1].getSettings().get("ColocalizationUpperThreshold")
                    val="%d / %d"%(th1,th2)
                    val1,val2=th1,th2
                else:
                    val="0 / 128"
                    val1,val2=0,128
            elif item == "PercentageVolumeCh1":
                if sources:
                    pvolch = sources[0].getSettings().get(item)
                    pmatch = sources[0].getSettings().get("PercentageMaterialCh1")
                    print "pvolch=",pvolch,type(pvolch)
                    if not pvolch:pvolch=0
                    if not pmatch:pmatch=0
                    val = "%.3f%% / %.3f%%"%(pvolch*100,pmatch*100)
                    val1="%.3f%%"%(pvolch*100)
                    val2="%.3f%%"%(pmatch*100)
                else:
                    val = "0.000% / 0.000%"
                    val1="0.000%"
                    val2="0.000%"
            elif item == "PercentageVolumeCh2":
                if sources:
                    pvolch = sources[1].getSettings().get(item)
                    pmatch = sources[1].getSettings().get("PercentageMaterialCh2")
                    if not pvolch:pvolch=0
                    if not pmatch:pmatch=0
                    val = "%.3f%% / %.3f%%"%(pvolch*100,pmatch*100)
                    if not pvolch:pvolch=0
                    if not pmatch:pmatch=0
                    val1 = "%.3f%%"%(pvolch*100)
                    val2="%.3f%%"%(pmatch*100)                    
                else:
                    val= "0.000% / 0.000%"
                    val1="0.000%"
                    val2="0.000%"                    
            elif item == "SumCh1":
                if sources:
                    sum = sources[0].getSettings().get(item)
                    sumth = sources[0].getSettings().get("SumOverThresholdCh1")
                    
                    if not sum:sum=0
                    if not sumth:sumth=0
                    val = "%d / %d"%(sum,sumth)
                    val1=sum
                    val2=sumth
                else:
                    val = "0 / 0"
                    val1=0
                    val2=0
            elif item == "SumCh2":                    
                if sources:
                    sum = sources[1].getSettings().get(item)
                    sumth = sources[1].getSettings().get("SumOverThresholdCh2")
                    if not sum:sum=0
                    if not sumth:sumth=0
                    val = "%d / %d"%(sum,sumth)
                    val1=sum
                    val2=sumth
                else:
                    val = "0 / 0"  
                    val1=0
                    val2=0
            elif item == "NonZeroCh1":                    
                if sources:
                    sum = sources[1].getSettings().get(item)
                    sumth = sources[1].getSettings().get("NonZeroCh2")
                    if not sum:sum=0
                    if not sumth:sumth=0
                    val = "%d / %d"%(sum,sumth)
                    val1=sum
                    val2=sumth
                else:
                    val = "0 / 0"  
                    val1=0
                    val2=0                    
            elif item == "OverThresholdCh1":                    
                if sources:
                    sum = sources[1].getSettings().get(item)
                    sumth = sources[1].getSettings().get("OverThresholdCh2")
                    if not sum:sum=0
                    if not sumth:sumth=0
                    val = "%d / %d"%(sum,sumth)
                    val1=sum
                    val2=sumth
                else:
                    val = "0 / 0"  
                    val1=0
                    val2=0   

            elif item == "DiffStainVoxelsCh1":
                if sources:
                    ds = sources[0].getSettings().get(item)
                    dsint = sources[0].getSettings().get("DiffStainIntCh1")
                    if not ds:ds=0
                    if not dsint:dsint=0
                    val = "%.3f / %.3f"%(ds,dsint)
                    val1=ds
                    val2=dsint
                else:
                    val = "0.000 / 0.000"              
                    val1=0.000
                    val2=0.000
            elif item == "DiffStainVoxelsCh2":
                if sources:
                    ds = sources[1].getSettings().get(item)
                    dsint = sources[1].getSettings().get("DiffStainIntCh2")
                    if not ds:ds=0
                    if not dsint:dsint=0
                    val = "%.3f / %.3f"%(ds,dsint)
                    val1=ds
                    val2=dsint
                else:
                    val = "0.000 / 0.000"                         
                    val1=0.000
                    val2=0.000
                    
            elif item == "DiffStainPercentageCh1":
                if sources:
                    ds = sources[0].getSettings().get("DiffStainVoxelsCh1")
                    dsint = sources[0].getSettings().get("DiffStainIntCh1")
                    if not ds:ds=0
                    if not dsint:dsint = 0
                    ds = 1.0/(ds+1)
                    dsint = 1.0 / (dsint+1.0)
                    val = "%.3f / %.3f"%(ds,dsint)
                    val1=ds
                    val2 = dsint
                else:
                    val = "0.000 / 0.000"
                    val1=0.0
                    val2=0.0
            elif item == "DiffStainPercentageCh2":
                if sources:
                    ds = sources[1].getSettings().get("DiffStainVoxelsCh2")
                    dsint = sources[1].getSettings().get("DiffStainIntCh2")
                    if not ds:ds=0
                    if not dsint:dsint = 0
                    ds = 1.0/(ds+1)
                    dsint = 1.0 / (dsint+1.0)
                    val = "%.3f / %.3f"%(ds,dsint)
                    val1=ds
                    val2 = dsint
                else:
                    val = "0.000 / 0.000"
                    val1=0.0
                    val2=0.0                    
            elif item == "RRandMean":
                if sources:
                    randmean = sources[0].getSettings().get(item)
                    stdev = sources[0].getSettings().get("RRandSD")
                    if not randmean:randmean=0
                    if not stdev:stdev=0
                else:
                    randmean = 0
                    stdev=0
                val=u"%.3f \u00B1 %.5f"%(randmean,stdev)
            elif item == "NumIterations":
                if sources:
                    n1 = sources[0].getSettings().get("NumIterations")
                    n2 = sources[0].getSettings().get("ColocCount")
                    if not n1:n1=0
                    if not n2:n2=0
                    val1 = int(n1-n2)
                    val2 = n2
                else:
                    val1=0
                    val2=0
                val = "%d / %d"%(val1,val2)
                
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
            
            if not val1:
                val1=val
                val2=""
            self.headervals[index][1]=val1
            self.headervals[index][2]=val2
            self.listctrl.SetStringItem(index,col,format%val)
            
    def autoThreshold(self):
        """
        Created: 11.07.2004, KP
        Description: Use vtkAutoThresholdColocalization to determine thresholds
                     for colocalization and calculate statistics
        """
        self.dataUnit.getSourceDataUnits()[0].getSettings().set("CalculateThresholds",1)        
        self.eventDesc="Calculating thresholds"
        
        self.doPreviewCallback(None)
        self.dataUnit.getSourceDataUnits()[0].getSettings().set("CalculateThresholds",0) 
        
        messenger.send(None,"threshold_changed")    
        
    def getAutoThreshold(self,event=None):
        """
        Created: 11.07.2004, KP
        Description: Calculate the automatic threshold for colocalization
        """
        do_cmd="""bxd.mainWindow.tasks['Colocalization'].autoThreshold()"""
        cmd = Command.Command(Command.GUI_CMD,None,None,do_cmd,"",desc="Calculate automatic threshold")
        cmd.run()
        
    def statistics(self):
        """
        Created: 17.07.2006, KP
        Description: Calculate the statistics
        """
        self.dataUnit.getSourceDataUnits()[0].getSettings().set("CalculateThresholds",2)
        self.eventDesc="Calculating statistics"
        self.doPreviewCallback(None)
        self.dataUnit.getSourceDataUnits()[0].getSettings().set("CalculateThresholds",0) 
                
        
        
    def getStatistics(self, event=None):
        """
        Method: getStatistics
        Created: 11.07.2004, KP
        Description: Use vtkAutoThresholdColocalization to determine thresholds
                     for colocalization and calculate statistics
        """
        do_cmd="""bxd.mainWindow.tasks['Colocalization'].statistics()"""
        cmd = Command.Command(Command.GUI_CMD,None,None,do_cmd,"",desc="Calculate colocalization statistics")
        cmd.run()
        pos=self.radiobox.GetSelection()
        if pos:
            map=[1,0,2]
            method=map[pos-1]
            smethod=""
            if method==0:smethod="Fay"
            if method==1:smethod="Costes"
            if method==2:smethod="van Steensel"
            
            try:
                n = int(self.iterations.GetValue())
                iterations=", iterations = %d"%n
            except:
                pass
            if method!=1:
                iterations=""
            do_cmd="bxd.mainWindow.tasks['Colocalization'].getPValue('%s'%s)"%(smethod, iterations)
            cmd = Command.Command(Command.GUI_CMD,None,None,do_cmd,"",desc="Calculate P-Value of colocalization")
            cmd.run()
        
    def getPValue(self,method=1, iterations = 100):
        """
        Method: getPValue
        Created: 13.07.2005, KP
        Description: Get the P value for colocalization
        """
        try:
            n = int(self.iterations.GetValue())
            if n != iterations:
                self.iterations.SetValue("%d"%iterations)
        except:
            pass
        coloctest=vtk.vtkImageColocalizationTest()
        #coloctest.SetRandomizeZ(1)
        sources=self.dataUnit.getSourceDataUnits()
        self.eventDesc="Calculating P-Value"
        methods=["Fay","Costes","van Steensel"]
        if type(method) == types.StringType:
            method = methods.index(method)
        
        Logging.info("Using %s method (%d)"%(methods[method],method),kw="processing")
        t=time.time()
        
        coloctest.SetMethod(method)
        #coloctest.SetPixelSize(vx)
        
        try:
            n=float(self.fixedPSF.GetValue())
        except:
            messenger.send(None,"show_error","Bad PSF width","The given width for point spread function is invalid.")
            return
        print "Setting PSF width",int(n)
        coloctest.SetManualPSFSize(int(n))        

        coloctest.SetNumIterations(iterations)
        
        for i in sources:
            data=i.getTimePoint(self.timePoint)
            coloctest.AddInput(data)
        coloctest.AddObserver("ProgressEvent",self.updateProgress)
        
        coloctest.Update()
        print "It took ",time.time()-t,"seconds to calculate p-value"
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
        Created: 03.11.2004, KP
        Description: Creates a button box containing the buttons Render, 
                     Preview and Close
        """
        TaskPanel.TaskPanel.createButtonBox(self)
        messenger.connect(None,"process_dataset",self.doColocalizationCallback)        

    def createOptionsFrame(self):
        """
        Created: 03.11.2004, KP
        Description: Creates a frame that contains the various widgets
                     used to control the colocalization settings
        """
        TaskPanel.TaskPanel.createOptionsFrame(self)
#        self.colocalizationPanel=wx.Panel(self.settingsNotebook,-1)
        self.colocalizationPanel = wx.Panel(self,-1)
        self.colocalizationSizer=wx.GridBagSizer()
        n=0
        
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
        self.scatterPlot=Scatterplot.Scatterplot(self.colocalizationPanel,drawLegend = 1)
        box.Add(self.scatterPlot)
        self.colocalizationSizer.Add(box,(n,0))
        n+=1
        
        sbox=wx.StaticBox(self.colocalizationPanel,-1,"Automatic threshold")
        box=wx.StaticBoxSizer(sbox,wx.VERTICAL)
        self.automaticThresholdStaticBox = sbox
        self.automaticThresholdSizer = box
        self.radiobox=wx.RadioBox(self.colocalizationPanel,-1,"Calculate P-Value",
        choices=["None","Costes","Fay","van Steensel"],majorDimension=2,
        style=wx.RA_SPECIFY_COLS
        )
        self.radiobox.Bind(wx.EVT_RADIOBOX,self.onSetTestMethod)
        box.Add(self.radiobox)
        self.iterLbl=wx.StaticText(self.colocalizationPanel,-1,"Iterations:")
        self.iterations = wx.SpinCtrl(self.colocalizationPanel,-1,"100",min=2,max=999,initial=100)
        
        fixedPSFLbl=wx.StaticText(self.colocalizationPanel,-1,"PSF radius (px):")
        self.fixedPSF = wx.TextCtrl(self.colocalizationPanel,-1,"")
        
        costesgrid=wx.GridBagSizer()
        #sboxsizer.Add(costesgrid)
        costesgrid.Add(self.iterLbl,(0,0))
        costesgrid.Add(self.iterations,(0,1))

        costesgrid.Add(fixedPSFLbl,(1,0))
        costesgrid.Add(self.fixedPSF,(1,1))
        NALbl = wx.StaticText(self.colocalizationPanel,-1,"Numerical Aperture:")
        self.NA = wx.TextCtrl(self.colocalizationPanel,-1,"1.4")
        costesgrid.Add(NALbl,(2,0))
        costesgrid.Add(self.NA,(2,1))
        Ch2LambdaLbl = wx.StaticText(self.colocalizationPanel,-1,u"Ch2 \u03BB (nm):")
        self.Ch2Lambda = wx.TextCtrl(self.colocalizationPanel,-1,"520")
        costesgrid.Add(Ch2LambdaLbl,(3,0))
        costesgrid.Add(self.Ch2Lambda,(3,1))
        
        self.NA.Bind(wx.EVT_TEXT,self.onUpdatePSF)
        self.Ch2Lambda.Bind(wx.EVT_TEXT,self.onUpdatePSF)

                
        self.iterations.Enable(0)
        self.NA.Enable(0)
        self.Ch2Lambda.Enable(0)
        self.fixedPSF.Enable(0)
 
        box.Add(costesgrid)
        
        box2=wx.BoxSizer(wx.HORIZONTAL)
        self.statsButton=wx.Button(self.colocalizationPanel,-1,"Statistics")
        self.statsButton.Bind(wx.EVT_BUTTON,self.getStatistics)
        box2.Add(self.statsButton)        
        self.thresholdButton=wx.Button(self.colocalizationPanel,-1,"Auto-Threshold")
        self.thresholdButton.Bind(wx.EVT_BUTTON,self.getAutoThreshold)
        box2.Add(self.thresholdButton) 
        self.statsButtonSizer = box2
        box.Add(box2)
        self.colocalizationSizer.Add(box,(n,0),flag=wx.EXPAND|wx.LEFT|wx.RIGHT)
        n+=1
        
        sbox=wx.StaticBox(self.colocalizationPanel,-1,"Coloc Volume Statistics")
        box=wx.StaticBoxSizer(sbox,wx.VERTICAL)
        self.colocStatsStaticBox = sbox
        self.colocStatsSizer = box
        
        self.listctrl=MyListCtrl(self.colocalizationPanel,-1,size=(350,300),
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
        self.colocColorBox = sbox
        self.colocColorSizer = sboxsizer
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
        
        self.settingsSizer.Add(self.colocalizationPanel,(1,0),flag=wx.EXPAND|wx.ALL)
        
#        self.settingsNotebook.AddPage(self.colocalizationPanel,"Colocalization")
    
    
    def onUpdatePSF(self,event):
        """
        Created: 06.04.2006, KP
        Description: Update the PSF based on the given NA and lambda
        """
        if event:
            event.Skip()
        if not self.voxelSize:
            sources=self.dataUnit.getSourceDataUnits()
            if sources:
                self.voxelSize = sources[0].getVoxelSize()
            else:
                return
        vx,vy,vz=self.voxelSize
        try:
            l=float(self.Ch2Lambda.GetValue())
            na=float(self.NA.GetValue())
        except:
            
            return
        
        psf = (0.61*l)/na
        
        # psf is now in nanometers
        psf /= (vx*1000*1000000)
        self.fixedPSF.SetValue("%.4f"%float(psf))
        
        
    def onSetTestMethod(self,event):
        """
        Created: 13.07.2005, KP
        Description: Set the method used for colocalisation test
        """
        n=self.radiobox.GetSelection()
        flag=(n==1)
        self.iterations.Enable(flag)
        self.NA.Enable(flag)
        self.Ch2Lambda.Enable(flag)
        self.fixedPSF.Enable(flag)
        

    def onExportStatistics(self,event):
        """
        Created: 13.07.2005, KP
        Description: Export colocalization statistics to file
        """
        
        name=self.dataUnit.getName()
        filename=Dialogs.askSaveAsFileName(self,"Save colocalization statistics as","%s.csv"%name,"CSV File (*.csv)|*.csv")
        if filename:
            filename=filename.replace("\\","\\\\")
            do_cmd="bxd.mainWindow.tasks['Colocalization'].exportStatistics('%s')"%filename
            cmd = Command.Command(Command.GUI_CMD,None,None,do_cmd,"",desc="Export colocalization statistics")
            cmd.run()
        
        
    def decode(self, d):
        """
        Created: 15.08.2006, KP
        Description: Replace any unicode characeters with their ascii counterparts
        """
        d=d.replace(u"\u00B1","+-")
        #d=d.replace("")
        return d
        
    def exportStatistics(self, filename):
        """
        Created: 18.07.2006, KP
        Description: Export the colocalization stats
        """   
        name=self.dataUnit.getName()        
        sources=self.dataUnit.getSourceDataUnits()
        names=[]
        names2=[]
        for i in sources:
            names.append(i.getName())
            dsn=i.getFileName()
            dsn=os.path.basename(dsn)
            names2.append(dsn)
        
        names3=[]
        for i in names2:
            if i not in names3:names3.append(i)
                
        namestr=" and ".join(names)
        leadstr="From file "
        if len(names3)>1:
            leadstr="From files "
        namestr2=leadstr+" and ".join(names3)

        if not filename:
            Logging.info("Got no name for coloc statistics",kw="processing")
            return
#        f=open(filename,"wb")
        f=codecs.open(filename,"wb","latin-1")
        
        w = csv.writer(f, dialect="excel",delimiter=";")
        get1=sources[0].getSettings().get
        get2=sources[1].getSettings().get

        w.writerow(["Statistics for colocalization of channels %s"%namestr])
        w.writerow([namestr2])
        w.writerow(["Timepoint",self.timePoint])
        w.writerow([time.ctime()])
        for item in self.headervals:
            #print item
            header,val1,val2,col=item
            header = self.decode(header)
            if type(val1)==types.UnicodeType:
                val1=self.decode(val1)
                
            if val2:
                if type(val2)==types.UnicodeType:   
                    val2=self.decode(val2)
                
                w.writerow([header,val1,val2])
            else:
                w.writerow([header,val1])
        f.close()
        del w
        del f
        

        
    def populateListCtrl(self):
        """
        Method: populateListCtrl
        Created: 12.07.2005, KP
        Description: Add information to the list control
        """
        self.cols=[self.beginner,self.intermediate,self.expert]
        self.headervals=[["%ch1% threshold (Lower / Upper)","","",0],
        ["%ch2% threshold (Lower / Upper)","","",0],
        ["P-Value","","",0],
        ["# of colocalized voxels","","",0],
        ["% of volume colocalized","","",0],
        ["% of %ch1% coloc. (voxels / intensity)","","",1],
        ["% of %ch2% coloc. (voxels / intensity)","","",1],
        ["% of %ch1% coloc. (total intensity)","","",1],
        ["% of %ch2% coloc. (total intensity)","","",1],
        ["Correlation","","",1],
        ["Correlation (voxels > threshold)","","",1],
        ["Correlation (voxels < threshold)","","",1],
        ["M1","","",1],
        ["M2","","",1],
        ["Sum of %ch1% (total / over threshold)","","",2],
        ["Sum of %ch2% (total / over threshold)","","",2],
        ["# of non-zero voxels (%ch1% / %ch2%)","","",2],
        ["# of voxels > threshold (%ch1% / %ch2%)","","",2],
        ["Differ. stain of %ch1% to %ch2% (voxels / intensity)","","",2],
        ["Differ. stain of %ch2% to %ch1% (voxels / intensity)","","",2],
        ["% of diff. stain of %ch1% (voxels / intensity)","","",2],
        ["% of diff. stain of %ch2% (voxels / intensity)","","",2],
        ["R(obs)","","",2],
        [u"R(rand) (mean \u00B1 sd)","","",2],
        ["R(rand) > R(obs)","","",2]

        ]

        self.listctrl.InsertColumn(0,"Quantity")
        self.listctrl.InsertColumn(1,"Value")
        #self.listctrl.InsertColumn(1,"")
        
        self.listctrl.SetColumnWidth(0,180)
        self.listctrl.SetColumnWidth(1,180)
        #self.listctrl.SetColumnWidth(2,120)
        for n,item in enumerate(self.headervals):
            txt,a,b,col=item
            self.listctrl.InsertStringItem(n,txt)
            self.listctrl.SetItemBackgroundColour(n,self.cols[col])
            
    def updateZSlice(self,obj,event,zslice):
        """
        Created: 25.03.2005, KP
        Description: A callback function called when the zslice is changed
        """
        if self.scatterPlot:
            self.scatterPlot.setZSlice(zslice)
            self.scatterPlot.updatePreview()
            self.updateListCtrl()

    def updateTimepoint(self,obj,event,timePoint):
        """
        Created: 25.03.2005, KP
        Description: A callback function called when the timepoint is changed
        """
        self.timePoint=timePoint
        if self.scatterPlot:
            self.scatterPlot.setTimepoint(self.timePoint)
            self.scatterPlot.updatePreview()

    def updateThreshold(self,event):
        """
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
                self.colorBtn.setColorTransferFunction(ctf)
                self.colorBtn.Refresh()

    def doColocalizationCallback(self,*args):
        """
        Created: 03.11.2004, KP
        Description: A callback for the button "Do colocalization"
        """
        self.updateBitDepth()
        TaskPanel.TaskPanel.doOperation(self)

    def updateBitDepth(self,event=None):
        """
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
        Created: 25.03.2005, KP
        Description: Set the dataunit used for the colocalization 
        """
        TaskPanel.TaskPanel.setCombinedDataUnit(self,dataUnit)
        #self.scatterPlot.setDataunit(dataUnit)
        # See if the dataunit has a stored colocalizationctf
        # then use that.


        sources = self.dataUnit.getSourceDataUnits()

        n1=sources[0].getName()
        n2=sources[1].getName()

        minval,maxval = sources[0].getScalarRange()
        minval2,maxval2 = sources[1].getScalarRange()
        if minval2<minval:minval=minval2
        if maxval2>maxval:maxval=maxval2
        self.lowerthreshold.SetRange(minval,maxval)
        self.lowerthreshold.SetValue((maxval-minval)/2)
        self.upperthreshold.SetRange(minval,maxval)
        self.upperthreshold.SetValue(maxval)        
        self.updateThreshold(None)
        
        for i,val in enumerate(self.headervals):
            s=val[0]
            s=s.replace("%ch1%",n1)
            s=s.replace("%ch2%",n2)
            self.headervals[i][0]=s
            self.listctrl.SetStringItem(i,0,s)



        na = sources[1].getNumericalAperture()
        emission = sources[1].getEmissionWavelength()

        if na:
            self.NA.SetValue("%.4f"%na)
        if emission:
            self.Ch2Lambda.SetValue("%d"%emission)
            
        self.onUpdatePSF(None)

        ctf=self.dataUnit.getSettings().get("ColocalizationColorTransferFunction")
        if not ctf:
            ctf = self.dataUnit.getSettings().get("ColorTransferFunction")
        else:
            Logging.info("Using ColocalizationColorTransferFunction",kw="task")
        if self.colorBtn:
            self.colorBtn.setColorTransferFunction(ctf)
        self.scatterPlot.setDataUnit(dataUnit)
        if self.scatterPlot:
            #self.scatterPlot.setZSlice(self.preview.z)
            self.scatterPlot.setZSlice(0)
            self.scatterPlot.setTimepoint(self.timePoint)
            self.scatterPlot.updatePreview()        
        
        self.colocalizationPanel.Layout()
        
    def createItemToolbar(self):
        """
        Created: 31.03.2005, KP
        Description: Method to create a toolbar for the window that allows use to select processed channel
        """      
        n=TaskPanel.TaskPanel.createItemToolbar(self)        
        
        coloc=vtk.vtkImageColocalizationFilter()
        coloc.SetOutputDepth(8)
        i=0
        #for dataunit in self.dataUnit.getSourceDataUnits():
        for data in self.itemMips:
            coloc.AddInput(data)
            coloc.SetColocalizationLowerThreshold(i,100)
            coloc.SetColocalizationUpperThreshold(i,255)
            i=i+1
        coloc.Update()
        ctf=vtk.vtkColorTransferFunction()
        ctf.AddRGBPoint(0,0,0,0)
        ctf.AddRGBPoint(255,1,1,1)
        #imagedata=ImageOperations.getMIP(coloc.GetOutput(),ctf)
        maptocolor=vtk.vtkImageMapToColors()
        maptocolor.SetInput(coloc.GetOutput())
        maptocolor.SetLookupTable(ctf)
        maptocolor.SetOutputFormatToRGB()
        maptocolor.Update()
        imagedata=maptocolor.GetOutput()
        bmp=ImageOperations.vtkImageDataToWxImage(imagedata).ConvertToBitmap()
        
        
        #print "BMP=",bmp.GetWidth(),bmp.GetHeight()
        
        bmp = self.getChannelItemBitmap(bmp,(255,255,0))
        toolid=wx.NewId()
        #n=n+1
        name="Colocalization"
        self.toolMgr.addChannelItem(name,bmp,toolid,lambda e,x=n,s=self:s.setPreviewedData(e,x))        
        
        for i,tid in enumerate(self.toolIds):
            self.dataUnit.setOutputChannel(i,0)
            self.toolMgr.toggleTool(tid,0)
        
        self.dataUnit.setOutputChannel(len(self.toolIds),1)
        self.toolIds.append(toolid)
        self.toolMgr.toggleTool(toolid,1)
        self.restoreFromCache()
