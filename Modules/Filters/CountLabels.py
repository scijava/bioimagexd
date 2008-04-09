#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: AnalyzePolydata
 Project: BioImageXD
 Description:

 A module for the imagedata to polydata conversion filter
 
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
__author__ = "BioImageXD Project <http://www.bioimagexd.net/>"
__version__ = "$Revision$"
__date__ = "$Date$"

import lib.ProcessingFilter
import scripting
import types
import GUI.GUIBuilder
import itk
import os
import lib.Particle
import lib.FilterTypes
import GUI.CSVListView
import wx
import vtk
import vtkbxd

class CountLabelsFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	A filter for analyzing polydata
	"""
	name = "Count labels"
	category = lib.FilterTypes.MEASUREMENT
	level = scripting.COLOR_INTERMEDIATE

	def __init__(self, inputs = (2,2)):
		"""
		Initialization
		"""
		self.defaultObjectsFile = u"statistics.csv"
		self.objectsBox = None
		self.timepointData = {}
		self.polyDataSource = None
		self.segmentedSource = None
		self.delayedData = None
		lib.ProcessingFilter.ProcessingFilter.__init__(self, inputs)
		self.descs = {}
			
		self.headers = ["Background object","# of objects inside"]
		
	def getParameters(self):
		"""
		Returns the parameters for GUI.
		"""
		return [
			]

	def getType(self, parameter):
		"""
		Returns the types of parameters for GUI.
		"""
		if parameter in ["DistanceToSurface","InsideSurface"]:
			return types.BooleanType
			
			
	def getDefaultValue(self, parameter):
		"""
		Description:
		"""
		if parameter in ["DistanceToSurface","InsideSurface"]:
			return True
		return 0

	def getParameterLevel(self, param):
		"""
		Description:
		"""
		return scripting.COLOR_BEGINNER
		
	def getGUI(self, parent, taskPanel):
		"""
		Return the GUI for this filter
		"""
		gui = lib.ProcessingFilter.ProcessingFilter.getGUI(self, parent, taskPanel)

		if not self.objectsBox:
			self.objectsBox = GUI.CSVListView.CSVListView(self.gui)
			if self.delayedData:
				self.objectsBox.setContents(self.delayedData)
				self.delayedData = None
			else:
				self.objectsBox.setContents([self.headers])
			sizer = wx.BoxSizer(wx.VERTICAL)

			sizer.Add(self.objectsBox, 1)
			box = wx.BoxSizer(wx.HORIZONTAL)

			sizer.Add(box)
			pos = (0, 0)
			item = gui.sizer.FindItemAtPosition(pos)
			if item.IsWindow():
				win = item.GetWindow()
			elif item.IsSizer():
				win = item.GetSizer()
			elif item.IsSpacer():
				win = item.GetSpacer()

			gui.sizer.Detach(win)
			gui.sizer.Add(sizer, (0, 0), flag = wx.EXPAND | wx.ALL)
			gui.sizer.Add(win, (1, 0), flag = wx.EXPAND | wx.ALL)

		return gui

	def setDataUnit(self, dataUnit):
		"""
		a method to set the dataunit used by this filter
		"""
		lib.ProcessingFilter.ProcessingFilter.setDataUnit(self, dataUnit)

	def getRange(self, param):
		"""
		Description:
		"""
		return 0,999
		
	def getInputName(self, n):
		"""
		Return the name of the input #n
		"""			 
		if n == 2: return "Counted objects"
		return "Background objects" 
		
	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute filter in input image and return output image
		"""
		if not lib.ProcessingFilter.ProcessingFilter.execute(self,inputs):
			return None

		bgImage = self.getInput(1)
		fgImage = self.getInput(2)
		
		labelcount = vtkbxd.vtkImageLabelCount()
		labelcount.AddInput(bgImage)
		labelcount.AddInput(fgImage)
		
		labelcount.Update()
		
		data = [self.headers[:]]
		countArray = labelcount.GetBackgroundToObjectCountArray()
		count = countArray.GetSize()
		
		totalCount = 0
		for i in range(0, count+1):
			entry = []
			entry.append("#%d"%i)
			objcount = countArray.GetValue(i)
			entry.append("%d objects"%objcount)
			totalCount += objcount
			data.append(entry)
		print "Total of ",totalCount,"objects"
		
		
		if self.objectsBox:
			self.objectsBox.setContents(data)
		else:
			self.delayedData = data
			
		return bgImage
