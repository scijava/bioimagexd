#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
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

import scripting
import lib.ProcessingFilter
import lib.FilterTypes
import lib.messenger
import GUI.GUIBuilder
import vtk
import types
import Logging

class ThresholdFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	Created: 15.04.2006, KP
	Description: A thresholding filter
	"""		
	name = "Threshold"
	category = lib.FilterTypes.SEGMENTATION
	level = scripting.COLOR_BEGINNER
	
	def __init__(self):
		"""
		Initialization
		"""
		self.defaultLower = 128
		self.defaultUpper = 255
		lib.ProcessingFilter.ProcessingFilter.__init__(self, (1, 1))
		self.vtkfilter = vtk.vtkImageThreshold()
		self.vtkfilter.AddObserver("ProgressEvent", self.updateProgress)

		self.origCtf = None
		
		self.ignoreObjects = 1
		self.descs = {"ReplaceInValue": "Value for voxels inside thresholds",
			"ReplaceOutValue": "Value for voxels outside thresholds",
			"ReplaceIn": "Inside thresholds", "ReplaceOut": "Outside thresholds",
			"LowerThreshold": "Lower Threshold", "UpperThreshold": "Upper threshold",
			"Demonstrate": "Use lookup table to demonstrate effect"}
			
	def getParameterLevel(self, parameter):
		"""
		Return the level of the given parameter
		"""
		if parameter in ["ReplaceInValue", "ReplaceOutValue"]:
			return scripting.COLOR_INTERMEDIATE
		return scripting.COLOR_BEGINNER
	
	def setParameter(self, parameter, value):
		"""
		Set a value for the parameter
		"""
		oldval = self.parameters.get(parameter, "ThisIsABadValueThatNoOneWillEverUse")
		lib.ProcessingFilter.ProcessingFilter.setParameter(self, parameter, value)
		if self.initDone and self.gui and value != oldval:
			lib.messenger.send(None, "data_changed", 0)
		
	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""			   
		return [["Threshold", (("LowerThreshold", "UpperThreshold"), )],
				["Replace voxels", (("ReplaceIn", "ReplaceOut"), )],
				["", ("ReplaceInValue", )],
				["", ("ReplaceOutValue", )],
				["", ("Demonstrate", )]
				]
		
	def getDesc(self, parameter):
		"""
		Return the description of the parameter
		"""	   
		return self.descs[parameter]
		
	def getLongDesc(self, parameter):
		"""
		Return a long description of the parameter
		""" 
		return ""
		
		
	def getType(self, parameter):
		"""
		Return the type of the parameter
		"""	   
		if parameter in ["LowerThreshold", "UpperThreshold"]:
			return GUI.GUIBuilder.THRESHOLD
		elif parameter in ["ReplaceIn", "ReplaceOut", "Demonstrate"]:
			return types.BooleanType
		return types.IntType
		
	def getDefaultValue(self, parameter):
		"""
		Return the default value of a parameter
		"""
		if parameter == "LowerThreshold":
			return self.defaultLower
		if parameter == "UpperThreshold":
			return self.defaultUpper
		if parameter == "ReplaceInValue":
			return self.defaultUpper
		if parameter == "ReplaceOutValue":
			return 0
		if parameter == "Demonstrate":
			return 0
		if parameter in ["ReplaceIn", "ReplaceOut"]:
			return True
			
	def setDataUnit(self,dataUnit):
		"""
		set the dataunit used as input for this filter
		"""
		if dataUnit:
			sourceDataUnits = dataUnit.getSourceDataUnits()
			if sourceDataUnits:
				self.defaultUpper = sourceDataUnits[0].getScalarRange()[1]
				self.defaultLower = self.defaultUpper / 2
		lib.ProcessingFilter.ProcessingFilter.setDataUnit(self, dataUnit)
		

	def onRemove(self):
		"""
		Restore palette upon filter removal
		"""
		if self.origCtf:
			self.dataUnit.getSettings().set("ColorTransferFunction", self.origCtf)
			
	def setInputChannel(self, inputNum,n):
		"""
		
		"""
		lib.ProcessingFilter.ProcessingFilter.setInputChannel(self, inputNum, n)
		
		if self.dataUnit:
			dataUnit = self.getInputDataUnit(inputNum)
			if dataUnit:
				lib.messenger.send(self, "set_UpperThreshold_dataunit", dataUnit)
		
	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute the filter with given inputs and return the output
		"""
		
		if not lib.ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None
		image = self.getInput(1)
		self.eventDesc="Thresholding image"

			
			
		if not self.parameters["Demonstrate"]:
			if self.origCtf:
				self.dataUnit.getSettings().set("ColorTransferFunction", self.origCtf)
				if self.gui:
					self.gui.histograms[0].setReplacementCTF(None)
					self.gui.histograms[0].updatePreview(renew = 1)
			self.vtkfilter.SetInput(image)
			
			self.vtkfilter.ThresholdByLower(self.parameters["UpperThreshold"])
			self.vtkfilter.ThresholdByUpper(self.parameters["LowerThreshold"])
		
		
			self.vtkfilter.SetReplaceIn(self.parameters["ReplaceIn"])
			if self.parameters["ReplaceIn"]:
				self.vtkfilter.SetInValue(self.parameters["ReplaceInValue"])
			
			self.vtkfilter.SetReplaceOut(self.parameters["ReplaceOut"])
			if self.parameters["ReplaceOut"]:
				self.vtkfilter.SetOutValue(self.parameters["ReplaceOutValue"])
			
			if update:
				self.vtkfilter.Update()
			return self.vtkfilter.GetOutput()
		else:
			lower = self.parameters["LowerThreshold"]
			upper = self.parameters["UpperThreshold"]
			origCtf = self.dataUnit.getSourceDataUnits()[0].getColorTransferFunction()
			self.origCtf = origCtf
			ctf = vtk.vtkColorTransferFunction()
			ctf.AddRGBPoint(0, 0, 0, 0.0)
			if lower > 0:
				ctf.AddRGBPoint(lower, 0, 0, 1.0)
				ctf.AddRGBPoint(lower + 1, 0, 0, 0)
			
			
			val = [0, 0, 0]
			origCtf.GetColor(255, val)
			r, g, b = val
			ctf.AddRGBPoint(upper, r, g, b)
			if upper < 255:
				ctf.AddRGBPoint(upper + 1, 0, 0, 0)
				ctf.AddRGBPoint(255, 1.0, 0, 0)
			self.dataUnit.getSettings().set("ColorTransferFunction", ctf)
			if self.gui:
				self.gui.histograms[0].setReplacementCTF(ctf)
				self.gui.histograms[0].updatePreview(renew = 1)
				self.gui.histograms[0].Refresh()
			
			return image
			