#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: ProcessingManager
 Project: BioImageXD
 Created: 2.2.2005, KP
 Description:
 
 This is a dialog used to control the execution of all operations. The dialog
 will give the option to select the processed timepoints
 
 Modified:  
            03.02.2005 KP - Created the class

 BioImageXD includes the following persons:
 DW - Dan White, dan@chalkie.org.uk
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 PK - Pasi Kankaanpää, ppkank@bytl.jyu.fi
 
 Copyright (c) 2005 BioImageXD Project.
"""
__author__ = "BioImageXD Project"
__version__ = "$Revision: 1.28 $"
__date__ = "$Date: 2005/01/13 14:52:39 $"

import wx
from TimepointSelection import *
import time
import GuiGeneration
from Logging import *

class ProcessingManager(TimepointSelection):
    """
    Class: ProcessingManager
    Created: 03.11.2004, KP
    Description: A dialog for selecting timepoints for processing
    """
    def __init__(self,parent,operation):
        """
        Method: __init__
        Created: 10.11.2004
        Creator: KP
        Description: Initialization
        """
        TimepointSelection.__init__(self,parent)
        self.progressDialog=None
        self.operationName=operation
        
        #self.timepointLbl.SetLabel("Select Time Points to be Processed")
        self.SetTitle("Processing - %s"%operation)
        
        #self.configBox=wx.StaticBox(self,-1,"Output Settings")
        #self.configBoxSizer=wx.StaticBoxSizer(self.configBox,wx.VERTICAL)
        self.selectBox=wx.StaticBox(self,-1,"Select slices to the output")
        self.selectBoxSizer=wx.StaticBoxSizer(self.selectBox,wx.VERTICAL)
        self.selectSlice=GuiGeneration.getSliceSelection(self)
        self.selectBoxSizer.Add(self.selectSlice)
        
        self.outputBox=wx.StaticBox(self,-1,"Output Settings")
        self.outputBoxSizer=wx.StaticBoxSizer(self.outputBox,wx.VERTICAL)
        self.checkBox=wx.CheckBox(self,-1,"Output slices as images")
        self.checkBox.Bind(wx.EVT_CHECKBOX,self.updateOutputFormat)
        
    
        self.outputBoxSizer.Add(self.checkBox)
        self.outputFormat=GuiGeneration.getImageFormatMenu(self)
        self.outputFormat.menu.Enable(0)        
        self.outputBoxSizer.Add(self.outputFormat)
        
        self.formatLbl=wx.StaticText(self,-1,"Filename format:")
        self.formatEdit=wx.TextCtrl(self,-1,"%d_%d")
        self.outputBoxSizer.Add(self.formatLbl)
        self.outputBoxSizer.Add(self.formatEdit)
        
        #self.radioBox=wx.RadioBox(self,-1,"Filename Formatting",choices=["Use single numbering","Use double numbering"],majorDimension=1,style=wx.RA_SPECIFY_COLS)
        #self.outputBoxSizer.Add(self.radioBox)

        
        box=wx.BoxSizer(wx.VERTICAL)
        box.Add(self.selectBoxSizer,1,wx.EXPAND)
        box.Add(self.outputBoxSizer,1,wx.EXPAND)
        self.mainsizer.Add(box,(2,0),flag=wx.EXPAND|wx.ALL)
        self.Layout()
        self.mainsizer.Fit(self)

    def updateOutputFormat(self,event):
        """
        Method: updateOutputFormat
        Created: 16.03.2005, KP
        Description: A method to enable/disable the image format drop down menu
        """
        self.outputFormat.menu.Enable(self.checkBox.GetValue())
    
        
    def createButtonBox(self):
        """
        Method: createButtonBox()
        Created: 03.2.2005, KP
        Description: Creates the standard control buttons
        """
        TimepointSelection.createButtonBox(self)

        self.actionBtn.SetLabel("Process Time Points")
        self.actionBtn.Bind(wx.EVT_BUTTON,self.doProcessing)
    
    def updateProgressMeter(self,tp,nth,total):
        """
        Method: updateProgressMeter(tp,nth,total)
        Created: 15.11.2004, KP
        Description: A callback for the dataunit to give info on the
                     progress of the task
        Parameters:
                tp      The number of the timepoint the module is processing
                nth     This is the Nth timepoint to be processed
                total   There are a total of this many timepoints to be processed
        """
        if not self.progressDialog:
            self.progressDialog=wx.ProgressDialog("Processing data","Timepoint   (  /  ) (0%) ETA:   mins   seconds",
            maximum=total,parent=self,style=wx.PD_CAN_ABORT|wx.PD_APP_MODAL)
            
        t2=time.time()
        diff=t2-self.t1
        self.t1=t2
        totsecs=diff*(total-nth)
        print "Diff=%f, total=%d, n=%d, secs=%d"%(diff,total,nth,totsecs)
        mins=totsecs/60
        secs=totsecs%60
        self.progressDialog.Update(nth,"Timepoint %d (%d/%d) (%d%%) ETA: "
        "%d mins %d seconds"%(tp,nth,total,100*(1.0*nth)/total,mins,secs))

    
    def doProcessing(self,event):
        """
        Method: doProcessing()
        Created: 09.02.2005, KP
        Description: A method that tells the dataunit to process the selected timepoints
        """    
        self.status=wx.ID_CANCEL
                
        filename=Dialogs.askSaveAsFileName(self,self.operationName,self.dataUnit.getName())

        if not filename:
            return
        self.status=wx.ID_OK
        # Set file path for returning to the mainwindow
        self.filePath=filename
        self.t1=time.time()
        
        tps=self.getSelectedTimepoints()
        try:
            self.dataUnit.doProcessing(filename,callback=self.updateProgressMeter,timepoints=tps)
        except GUIError,ex:
            ex.show()
        else:
            # then we close this window...
            self.Close()

