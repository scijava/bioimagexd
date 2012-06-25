#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: ManipulationPanel
 Project: BioImageXD
 Description:

 A task that allows the user to process the input data through a chain of different filters.
							
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


import GUI.Dialogs
import GUI.FilterBasedTaskPanel
import GUI.FilterEditor

import glob 
import lib.Command
import lib.ImageOperations
import lib.messenger

import scripting
import ConfigParser

import ManipulationFilters
import SegmentationFilters
import os.path
import GUI.PreviewFrame
import types
import GUI.UIElements
import vtk
import wx


class ManipulationPanel(GUI.FilterBasedTaskPanel.FilterBasedTaskPanel):
	"""
	Description: A window for restoring a single dataunit
	"""
	def __init__(self, parent, tb):
		"""
		Initialization
		Parameters:
				root    Is the parent widget of this window
		"""
		self.timePoint = 0
		self.operationName = "Process"
		self.filtersModule = ManipulationFilters
		GUI.FilterBasedTaskPanel.FilterBasedTaskPanel.__init__(self, parent, tb, wantNotebook  = 0)
		# Preview has to be generated here
		self.timePoint = 0
		self.currentGUI = None
		self.presetMenu = None
		self.parser = None
		self.onByDefault = 0
		self.Show()
		self.currentSelected = -1
		
		self.mainsizer.Layout()
		self.mainsizer.Fit(self)
		
		lib.messenger.send(None, "enable_dataunits_cache", True)
		lib.messenger.connect(None, "timepoint_changed", self.updateTimepoint)
		
	def updateTimepoint(self, obj, event, timePoint):
		"""
		A callback function called when the timepoint is changed
		"""
		self.timePoint = timePoint
		
	def createButtonBox(self):
		"""
		Creates a button box containing the buttons Render,
					 Preview and Close
		"""
		GUI.FilterBasedTaskPanel.FilterBasedTaskPanel.createButtonBox(self)
		
		lib.messenger.connect(None, "process_dataset", self.doProcessingCallback)        

	def createOptionsFrame(self):
		"""
		Creates a frame that contains the various widgets
					 used to control the colocalization settings
		"""
		GUI.FilterBasedTaskPanel.FilterBasedTaskPanel.createOptionsFrame(self)
		self.filterEditor = GUI.FilterEditor.FilterEditor(self, ManipulationFilters, taskPanel = self)
		lib.messenger.connect(self.filterEditor, "updateFilterList", self.updateFilterData)
		
		self.settingsSizer.Add(self.filterEditor, (1, 0), flag = wx.EXPAND | wx.ALL)
		

	def doFilterCheckCallback(self, event = None):
		"""
		A callback function called when the neither of the
					 filtering checkbox changes state
		"""
		pass

		
	def doProcessingCallback(self, *args):
		"""
		A callback for the button "Manipulation Dataset Series"
		"""
		self.updateFilterData()
		GUI.FilterBasedTaskPanel.FilterBasedTaskPanel.doOperation(self)

	def doPreviewCallback(self, event = None, *args):
		"""
		A callback for the button "Preview" and other events
					 that wish to update the preview
		"""
		self.updateFilterData()
		GUI.FilterBasedTaskPanel.FilterBasedTaskPanel.doPreviewCallback(self, event)

	def createItemToolbar(self):
		"""
		Method to create a toolbar for the window that allows use to select processed channel
		"""
		# Pass flag force which indicates that we do want an item toolbar
		# although we only have one input channel
		n = GUI.FilterBasedTaskPanel.FilterBasedTaskPanel.createItemToolbar(self, force = 1)
		for i, tid in enumerate(self.toolIds):
			self.dataUnit.setOutputChannel(i, 0)
			self.toolMgr.toggleTool(tid, 0)
		
		ctf = vtk.vtkColorTransferFunction()
		ctf.AddRGBPoint(0, 0, 0, 0)
		ctf.AddRGBPoint(255, 1, 1, 1)
		imagedata = self.itemMips[0]
		
		ctf = vtk.vtkColorTransferFunction()
		ctf.AddRGBPoint(0, 0, 0, 0)
		ctf.AddRGBPoint(255, 1, 1, 1)
		maptocolor = vtk.vtkImageMapToColors()
		maptocolor.SetInput(imagedata)
		maptocolor.SetLookupTable(ctf)
		maptocolor.SetOutputFormatToRGB()
		maptocolor.Update()
		imagedata = maptocolor.GetOutput()
		
		bmp = lib.ImageOperations.vtkImageDataToWxImage(imagedata).ConvertToBitmap()
		bmp = self.getChannelItemBitmap(bmp, (255, 255, 255))
		toolid = wx.NewId()
		name = "Manipulation"
		self.toolMgr.addChannelItem(name, bmp, toolid, lambda e, x = n, s = self:s.setPreviewedData(e, x))        
		
		self.toolIds.append(toolid)
		self.dataUnit.setOutputChannel(len(self.toolIds), 1)
		self.toolMgr.toggleTool(toolid, 1)

	def setCombinedDataUnit(self, dataUnit):
		"""
		Set the combined dataunit to be processed. Also initialize the output channels to be off by default.
		"""
		sources = dataUnit.getSourceDataUnits()
		for s in sources:
			if "FilterList" not in s.getSettings().registered:
				s.getSettings().register("FilterList")
			s.getSettings().set("FilterList", self.filterList)
		GUI.FilterBasedTaskPanel.FilterBasedTaskPanel.setCombinedDataUnit(self, dataUnit)
		self.filterEditor.setDataUnit(dataUnit)
		n = 0
		for i, dataunit in enumerate(dataUnit.getSourceDataUnits()):
			dataUnit.setOutputChannel(i, 0)
			n = i
		self.dataUnit.setOutputChannel(n + 1, 1)
		self.updateFilterData()
		self.restoreFromCache()
		self.updateSettings()
		
	def updateFilterData(self, *args):
		"""
		A method used to set the right values in dataset
								from filter GUI widgets
		"""
		filterList = self.filterEditor.getFilterList()
		self.settings.set("FilterList", filterList)
