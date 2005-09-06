#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: ProcessingManager
 Project: BioImageXD
 Created: 2.2.2005, KP
 Description:
 
 This is a dialog used to control the execution of all operations. The dialog
 will give the option to select the processed timepoints
 
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
__author__ = "BioImageXD Project"
__version__ = "$Revision: 1.28 $"
__date__ = "$Date: 2005/01/13 14:52:39 $"

import wx
from TimepointSelection import *
import time
import UIElements
import messenger
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
    
    def updateProgressMeter(self,obj,eventt,tp,nth,total):
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
            self.progressDialog=wx.ProgressDialog("Processing data","Timepoint   (  /  ) (0%) Time remaining:   mins   seconds",
            maximum=total,parent=self,style=wx.PD_CAN_ABORT|wx.PD_APP_MODAL|wx.PD_AUTO_HIDE)
            
        t2=time.time()
        diff=t2-self.t1
        self.t1=t2
        totsecs=diff*(total-nth)
        print "Diff=%f, total=%d, n=%d, secs=%d"%(diff,total,nth,totsecs)
        mins=totsecs/60
        secs=totsecs%60
        self.progressDialog.Update(nth,"Timepoint %d (%d/%d) (%d%%) Time remaining: "
        "%d mins %d seconds"%(tp+1,nth,total,100*(1.0*nth)/total,mins,secs))
        if nth==total:
            self.progressDialog.Destroy()
            
        wx.GetApp().Yield(1)
    
    def doProcessing(self,event):
        """
        Method: doProcessing()
        Created: 09.02.2005, KP
        Description: A method that tells the dataunit to process the selected timepoints
        """    
        self.status=wx.ID_CANCEL
                
        #name=self.operationName+" ("
        #name+=", ".join([x.getName() for x in self.dataUnit.getSourceDataUnits()])
        #name+=")"
        name=self.dataUnit.getName()
        
        filename=Dialogs.askSaveAsFileName(self,"Save %s dataset as"%self.operationName,"%s.bxd"%name,"BioImageXD Dataset (*.bxd)|*.bxd")
        name=os.path.basename(filename)
        name=".".join(name.split(".")[:-1])
        self.dataUnit.setName(name)
        
        
        if not filename:
            return
        self.status=wx.ID_OK
        # Set file path for returning to the mainwindow
        self.filePath=filename
        self.t1=time.time()
        
        tps=self.getSelectedTimepoints()
        messenger.connect(None,"update_processing_progress",self.updateProgressMeter)
        try:
            self.dataUnit.doProcessing(filename,timepoints=tps)
        except GUIError,ex:
            ex.show()
        # then we close this window...
        messenger.send(None,"load_dataunit",filename)
        self.Close()
