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

import Logging
import os.path
import wx
import TimepointSelection
import time
import lib.messenger
import scripting
import GUI.Dialogs
import lib.Command

class ProcessingManager(TimepointSelection.TimepointSelection):
	"""
	Created: 03.11.2004, KP
	Description: A dialog for selecting timepoints for processing
	"""
	def __init__(self, parent, operation):
		"""
		Created: 10.11.2004
		Description: Initialization
		"""
		TimepointSelection.TimepointSelection.__init__(self, parent)
		self.progressDialog = None
		self.operationName = operation
		scripting.processingManager = self
		
		self.SetTitle("Processing - %s" % operation)
		
		self.Layout()
		self.mainsizer.Fit(self)

	def createButtonBox(self):
		"""
		Created: 03.2.2005, KP
		Description: Creates the standard control buttons
		"""
		TimepointSelection.TimepointSelection.createButtonBox(self)

		self.actionBtn.SetLabel("Process Time Points")
		self.actionBtn.Bind(wx.EVT_BUTTON, self.onDoProcessing)
	
	def updateProgressMeter(self, obj, eventt, tp, nth, total):
		"""
		Created: 15.11.2004, KP
		Description: A callback for the dataunit to give info on the
					 progress of the task
		Parameters:
				tp      The number of the timepoint the module is processing
				nth     This is the Nth timepoint to be processed
				total   There are a total of this many timepoints to be processed
		"""
		if not self.progressDialog:
			self.progressDialog = wx.ProgressDialog("Processing data", "Timepoint   (  /  ) (0%) Time remaining:   mins   seconds",
			maximum = total, parent = self,
			style = wx.PD_ELAPSED_TIME | wx.PD_CAN_ABORT | wx.PD_APP_MODAL | wx.PD_AUTO_HIDE)
			
		t2 = time.time()
		diff = t2 - self.t1
		self.t1 = t2
		totsecs = diff * (total - nth)
		print "Diff=%f, total=%d, n=%d, secs=%d" % (diff, total, nth, totsecs)
		mins = totsecs / 60
		secs = totsecs % 60
		self.progressDialog.Update(nth, "Timepoint %d (%d/%d) (%d%%) Time remaining: "
		"%d mins %d seconds" % (tp + 1, nth, total, 100 * (1.0 * nth) / total, mins, secs))
		if nth == total:
			self.progressDialog.Destroy()
			
		wx.GetApp().Yield(1)
		
	def onDoProcessing(self, event):
		"""
		Created: 09.02.2005, KP
		Description: A method that tells the dataunit to process the selected timepoints
		"""          
		self.Show(0)
		name = self.dataUnit.getName()

		filename = GUI.Dialogs.askSaveAsFileName(self, "Save %s dataset as" % self.operationName, "%s.bxd" % name, "BioImageXD Dataset (*.bxd)|*.bxd")
		filename = filename.replace("\\", "\\\\")
		do_cmd = "scripting.processingManager.doProcessing('%s')" % filename
		undo_cmd = ""
		
		cmd = lib.Command.Command(lib.Command.GUI_CMD, None, None, do_cmd, undo_cmd, desc = "Process the selected timepoints")
		cmd.run()        
		
	def doProcessing(self, filename):
		"""
		Created: 18.07.2006, KP
		Description: A method that tells the dataunit to process the selected timepoints
		"""    
		self.status = wx.ID_CANCEL
	
		name = os.path.basename(filename)
		name = ".".join(name.split(".")[:-1])
		self.dataUnit.setName(name)
		
		
		if not filename:
			return
		self.status = wx.ID_OK
		# Set file path for returning to the mainwindow
		self.filePath = filename
		self.t1 = time.time()
		
		tps = self.getSelectedTimepoints()
		lib.messenger.connect(None, "update_processing_progress", self.updateProgressMeter)
		try:
			filename = self.dataUnit.doProcessing(filename, timepoints = tps)
		except Logging.GUIError, ex:
			ex.show()
		# then we close this window...
		lib.messenger.send(None, "load_dataunit", filename)
		self.Close()
