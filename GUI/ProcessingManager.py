#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: ProcessingManager
 Project: Selli 2
 Created: 2.2.2005
 Creator: KP
 Description:
 
 This is a dialog used to control the execution of all operations. The dialog
 will give the option to select the processed timepoints
 
 Modified:  
            03.02.2005 KP - Created the class

 Selli 2 includes the following persons:
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 
 Copyright (c) 2004 Selli 2 Project.
"""
__author__ = "Selli 2 Project <http://sovellusprojektit.it.jyu.fi/selli/>"
__version__ = "$Revision: 1.28 $"
__date__ = "$Date: 2005/01/13 14:52:39 $"

import wx
from TimepointSelection import *
import time

class ProcessingManager(TimepointSelection):
    """
    Class: ProcessingManager
    Created: 03.11.2004
    Creator: KP
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
        
        self.timepointLbl.SetLabel("Select Time Points to be Processed")
        self.SetTitle("Processing - %s"%operation)
        
    def createButtonBox(self):
        """
        Method: createButtonBox()
        Created: 03.2.2005
        Creator: KP
        Description: Creates the standard control buttons
        """
        TimepointSelection.createButtonBox(self)

        self.actionBtn.SetLabel("Process Time Points")
        self.actionBtn.Bind(EVT_BUTTON,self.doProcessing)
    
    def updateProgressMeter(self,tp,nth,total):
        """
        Method: updateProgressMeter(tp,nth,total)
        Created: 15.11.2004
        Creator: KP
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
        Created: 09.02.2005
        Creator: KP
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

