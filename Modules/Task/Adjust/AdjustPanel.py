#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: AdjustPanel
 Project: BioImageXD
 Created: 24.11.2004, KP
 Description:

 A configuration panel for module that is used to process a single dataset series in 
 various ways, including Correction of bleaching, mapping intensities 
 through intensity transfer function

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
__version__ = "$Revision: 1.42 $"
__date__ = "$Date: 2005/01/13 14:52:39 $"

import wx
import messenger
import os.path
import Dialogs

from PreviewFrame import *
from GUI.IntensityTransferEditor import *

import sys
import time


from GUI import TaskPanel
import ColorTransferEditor
import Logging

class AdjustPanel(TaskPanel.TaskPanel):
	"""
	Created: 03.11.2004, KP
	Description: A window for processing a single dataunit
	"""
	def __init__(self, parent, tb):
		"""
		Created: 03.11.2004, KP
		Description: Initialization
		Parameters:
				root    Is the parent widget of this window
		"""
		self.operationName = "Adjust"
		self.lbls = []
		self.btns = []
		self.entries = []
		self.timePoint = 0
		TaskPanel.TaskPanel.__init__(self, parent, tb)
		# Preview has to be generated heregoto
		# self.colorChooser=None
		self.createIntensityTransferPage()
		messenger.connect(None, "timepoint_changed", self.updateTimepoint)
		self.Show()

		self.mainsizer.Layout()
		self.mainsizer.Fit(self)

	def createIntensityInterpolationPanel(self):
		"""
		Created: 09.12.2004, KP
		Description: Creates a frame holding the entries for configuring 
					 interpolation
		"""        
		self.interpolationPanel = wx.Panel(self.settingsNotebook)
		#self.interpolationPanel=wx.Panel(self.iTFEditor)
		self.interpolationSizer = wx.GridBagSizer()
		lbl = wx.StaticText(self.interpolationPanel, -1, "Interpolate intensities:")
		self.interpolationSizer.Add(lbl, (0, 0))

		lbl = wx.StaticText(self.interpolationPanel, -1, "from timepoint")
		self.lbls.append(lbl)
		self.numOfPoints = 5
		for i in range(self.numOfPoints - 2):
			lbl = wx.StaticText(self.interpolationPanel, -1, "thru")
			self.lbls.append(lbl)
		lbl = wx.StaticText(self.interpolationPanel, -1, "to timepoint")
		self.lbls.append(lbl)

		for i in range(self.numOfPoints):
			btn = wx.Button(self.interpolationPanel, -1, "goto")
			btn.Bind(wx.EVT_BUTTON, lambda event, x = i: self.gotoInterpolationTimePoint(x))
			entry = wx.TextCtrl(self.interpolationPanel, size = (50, -1))
			self.btns.append(btn)
			self.entries.append(entry)

		for entry in self.entries:
			entry.Bind(wx.EVT_TEXT, self.setInterpolationTimePoints)

		last = 0
		for i in range(self.numOfPoints):
			lbl, entry, btn = self.lbls[i], self.entries[i], self.btns[i]
			self.interpolationSizer.Add(lbl, (i + 1, 0))
			self.interpolationSizer.Add(entry, (i + 1, 1))
			self.interpolationSizer.Add(btn, (i + 1, 2))
			last = i + 1

		#self.editIntensitySizer.Add(self.interpolationPanel,(0,1))
		self.interpolationPanel.SetSizer(self.interpolationSizer)
		self.interpolationPanel.SetAutoLayout(1)
		self.interpolationSizer.SetSizeHints(self.interpolationPanel)

		self.settingsNotebook.AddPage(self.interpolationPanel, "Interpolation")

		self.interpolationBox = wx.BoxSizer(wx.HORIZONTAL)

		self.reset2Btn = wx.Button(self.interpolationPanel, -1, "Reset all timepoints")
		self.reset2Btn.Bind(wx.EVT_BUTTON, self.resetTransferFunctions)
		self.interpolationBox.Add(self.reset2Btn)

		self.interpolateBtn = wx.Button(self.interpolationPanel, -1, "Interpolate")
		self.interpolateBtn.Bind(wx.EVT_BUTTON, self.startInterpolation)
		self.interpolationBox.Add(self.interpolateBtn)
		self.interpolationSizer.Add(self.interpolationBox, (last + 1, 0))


		#self.mainsizer.Add(self.interpolationPanel,(1,0))
		#self.panel.Layout()
		#self.mainsizer.Fit(self.panel)


	def createIntensityTransferPage(self):
		"""
		Created: 09.12.2004, KP
		Description: Creates a frame holding the entries for configuring 
					 intensity
		"""
		self.editIntensityPanel = wx.Panel(self.settingsNotebook, -1)
		self.editIntensitySizer = wx.GridBagSizer()

		self.iTFEditor = IntensityTransferEditor(self.editIntensityPanel)
		self.editIntensitySizer.Add(self.iTFEditor, (0, 0))#,span=(1,2))

		self.box = wx.BoxSizer(wx.HORIZONTAL)
		self.editIntensitySizer.Add(self.box, (2, 0))
		self.createIntensityInterpolationPanel()

		self.restoreBtn = wx.Button(self.editIntensityPanel, -1, "Reset current")
		self.restoreBtn.Bind(wx.EVT_BUTTON, self.iTFEditor.restoreDefaults)
		self.box.Add(self.restoreBtn)

		self.resetBtn = wx.Button(self.editIntensityPanel, -1, "Reset all")
		self.resetBtn.Bind(wx.EVT_BUTTON, self.resetTransferFunctions)
		self.box.Add(self.resetBtn)

		self.copyiTFBtn = wx.Button(self.editIntensityPanel, -1, "Copy to all")
		self.copyiTFBtn.Bind(wx.EVT_BUTTON, self.copyTransferFunctionToAll)
		self.box.Add(self.copyiTFBtn)

		self.editIntensityPanel.SetSizer(self.editIntensitySizer)
		self.editIntensityPanel.SetAutoLayout(1)
		self.settingsNotebook.InsertPage(0, self.editIntensityPanel, "Transfer Function")
		self.settingsNotebook.SetSelection(0)

		self.updateSettings()

	def setInterpolationTimePoints(self, event):
		"""
		Created: 13.12.2004, KP
		Description: A callback that is called when a timepoint entry for
					 intensity interpolation changes. Updates the list of 
					 timepoints between which the interpolation is carried out
					 by the dataunit
		"""
		lst = []
		for i in self.entries:
			val = i.GetValue()
			try:
				n = int(val)
				n -= 1
				lst.append(n)
			except:
				# For entries that have no value, add -1 as a place holder
				lst.append(-1)
		#self.dataUnit.setInterpolationTimePoints(lst)
		self.settings.set("InterpolationTimepoints", lst)


	def gotoInterpolationTimePoint(self, entrynum):
		"""
		Created: 09.12.2004, KP
		Description: The previewed timepoint is set to timepoint specified in
					 self.entries[entrynum]
		"""
		try:
			tp = int(self.entries[entrynum].GetValue())
		except:
			pass
		else:
			tp -= 1
			Logging.info("Previewing timepoint ", tp, "(will send change event)", kw = "task")

			messenger.send(None, "timepoint_changed", tp)
			#self.updateTimepoint(evt)

	def createButtonBox(self):
		"""
		Created: 03.11.2004, KP
		Description: Creates a button box containing the buttons Render,
					 Preview and Close
		"""
		TaskPanel.TaskPanel.createButtonBox(self)

		#self.processButton.SetLabel("Process Dataset Series")
		#self.processButton.Bind(wx.EVT_BUTTON,self.doProcessingCallback)
		messenger.connect(None, "process_dataset", self.doProcessingCallback)

	def createOptionsFrame(self):
		"""
		Created: 03.11.2004, KP
		Description: Creates a frame that contains the various widgets
					 used to control the colocalization settings
		"""
		TaskPanel.TaskPanel.createOptionsFrame(self)

		self.paletteLbl = wx.StaticText(self, -1, "Channel palette:")
		self.commonSettingsSizer.Add(self.paletteLbl, (1, 0))
		self.colorBtn = ColorTransferEditor.CTFButton(self)
		self.commonSettingsSizer.Add(self.colorBtn, (2, 0))
		self.Layout()

	def updateTimepoint(self, obj, evt, timePoint):
		"""
		Created: 04.04.2005, KP
		Description: A callback function called when the timepoint is changed
		"""
		#timePoint=event.getValue()
		Logging.info("Now configuring timepoint", timePoint, kw = "task")
		itf = self.settings.getCounted("IntensityTransferFunctions", timePoint)
		self.iTFEditor.setIntensityTransferFunction(itf)
		self.timePoint = timePoint
 
	def copyTransferFunctionToAll(self, event = None):
		"""
		Created: 10.03.2005, KP
		Description: A method to copy this transfer function to all timepooints
		"""
		itf = self.settings.getCounted("IntensityTransferFunctions", self.timePoint)
		l = self.dataUnit.getNumberOfTimepoints()
		for i in range(l):
			if i != self.timePoint:
				self.settings.setCounted("IntensityTransferFunctions", i, itf)
		
				

	def resetTransferFunctions(self, event = None):
		"""
		Created: 30.11.2004, KP
		Description: A method to reset all the intensity transfer functions
		"""
		l = self.dataUnit.getNumberOfTimepoints()
		sources = self.dataUnit.getSourceDataUnits()
		for i in range(l):
			minval, maxval = min([a.getScalarRange()[0] for a in sources]), max([a.getScalarRange()[1] for a in sources])
			itf = vtk.vtkIntensityTransferFunction()
			itf.SetRangeMax(maxval)
			
			self.settings.setCounted("IntensityTransferFunctions", i, itf)
			
		itf = self.settings.getCounted("IntensityTransferFunctions", self.timePoint)

		self.iTFEditor.setIntensityTransferFunction(itf)
		
	def startInterpolation(self, evt):
		"""
		Created: 24.11.2004, KP
		Description: A callback to interpolate intensity transfer functions
					 between the specified timepoints
		"""
		self.dataUnit.interpolateIntensities()
#        self.doPreviewCallback()



	def updateSettings(self, force = 0):
		"""
		Created: 03.11.2004, KP
		Description: A method used to set the GUI widgets to their proper values
		"""

		if self.dataUnit:
			self.iTFEditor.setIntensityTransferFunction(
			self.settings.getCounted("IntensityTransferFunctions", self.timePoint)
			)
			tps = self.settings.get("InterpolationTimepoints")
			if not tps:
				tps = []
			
			for i in range(len(tps)):
				n = tps[i]
				# If there was nothing in the entry at this position, the 
				# value is -1 in that case, we leave the entry empty
				if n != -1:
					self.entries[i].SetValue(str(n))

			ctf = self.settings.get("ColorTransferFunction")
			if ctf and self.colorBtn:
				self.colorBtn.setColorTransferFunction(ctf)
				self.colorBtn.Refresh()


	def doProcessingCallback(self, *args):
		"""
		Created: 03.11.2004, KP
		Description: A callback for the button "Process Dataset Series"
		"""
		TaskPanel.TaskPanel.doOperation(self)

	def setCombinedDataUnit(self, dataUnit):
		"""
		Created: 23.11.2004, KP
		Description: Sets the processed dataunit that is to be processed.
					 It is then used to get the names of all the source data
					 units and they are added to the menu.
					 This is overwritten from TaskPanel since we only process
					 one dataunit here, not multiple source data units
		"""
		TaskPanel.TaskPanel.setCombinedDataUnit(self, dataUnit)
	
		ctf = self.settings.get("ColorTransferFunction")
		if ctf and self.colorBtn:
			self.colorBtn.setColorTransferFunction(ctf)
		
		# We register a callback to be notified when the timepoint changes
		# We do it here because the timePointChanged() code requires the dataunit
		#self.Bind(EVT_TIMEPOINT_CHANGED,self.timePointChanged,id=ID_TIMEPOINT)

		tf = self.settings.getCounted("IntensityTransferFunctions", self.timePoint)
		self.iTFEditor.setIntensityTransferFunction(tf)
		self.iTFEditor.updateCallback = self.doPreviewCallback
		self.restoreFromCache()
		self.updateSettings()
