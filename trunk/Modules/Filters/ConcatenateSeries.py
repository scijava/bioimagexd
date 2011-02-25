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

import lib.ProcessingFilter
import vtkbxd
import GUI.GUIBuilder
import lib.FilterTypes
import scripting
import types
import vtk

class ConcatenateSeriesFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	Concatenate several datasets into one
	"""		
	name = "Combine time series"
	category = lib.FilterTypes.CONVERSION
	level = scripting.COLOR_EXPERIENCED
	
	def __init__(self):
		"""
		Initialization
		"""		   
		lib.ProcessingFilter.ProcessingFilter.__init__(self, (1, 1))
		self.padFilter = None
		self.maxDimensions = None
		self.totalTimepoints = -1
		self.descs = {"UseTimestamps":"Use timestamps to position datasets",
		"PadDatasets":"Pad datasets to largest dimensions"}
		self.filterDesc = "Combines several time series datasets together. Used to create a single dataset of a time series that is in several parts.\nInput: All opened grayscale images\nOutput: Grayscale image"
	
	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""			   
		return [ "Positioning:", ["", ("UseTimestamps",)],
		"Dimensions:", ["", ("PadDatasets",)]]

	def getParameterLevel(self, parameter):
		"""
		Return parameter level
		"""
		return scripting.COLOR_EXPERIENCED
		
	def getLongDesc(self, parameter):
		"""
		Return a long description of the parameter
		""" 
		if parameter == "UseTimestamps":
			return "Use the absolute timestamps in the datasets to determine their relative positions in the timeline"
		
	def setParameter(self, parameter, value):
		"""
		A method to set the value of a parameter
		"""
		lib.ProcessingFilter.ProcessingFilter.setParameter(self, parameter, value)
		if parameter in ["PadDatasets"]:
			if self.dataUnit:
				self.calculateMaximumDimensions()
		
	def getType(self, parameter):
		"""
		Return the type of the parameter
		"""	   
		if parameter in ["UseTimestamps","PadDatasets"]:
			return types.BooleanType

	def getDefaultValue(self, parameter):
		"""
		Return the default value of a parameter
		"""		
		return True

	def calculateMaximumDimensions(self):
		"""
		Calculate the maximum dimensions of the output dataset
		"""
		maxX, maxY, maxZ = 0,0,0
		timePoints = 0
		dataunits = self.dataUnit.getSourceDataUnits()
		for i, dataUnit in enumerate(dataunits):
			x,y,z = dataUnit.getDimensions()
			maxX = max(maxX, x)
			maxY = max(maxY, y)
			maxZ = max(maxZ, z)
			timePoints += dataUnit.getNumberOfTimepoints()
		mod = False
		if self.totalTimepoints != timePoints:
			self.totalTimepoints = timePoints
			print "Number of timepoints = ",self.totalTimepoints
			self.dataUnit.setNumberOfTimepoints(self.totalTimepoints)
			mod = True
		if self.maxDimensions != (maxX, maxY, maxZ):
			mod = True
			self.maxDimensions = (maxX, maxY, maxZ)
			print "Maximum dimensions = ",self.maxDimensions
			self.dataUnit.setModifiedDimensions(self.maxDimensions)
		if mod:
			lib.messenger.send(None, "update_dataset_info")

	def orderByTime(self, unit1, unit2):
		"""
		Determine the ordering of two dataunits based on their absolute time stamps
		"""
		return cmp(unit1.getAbsoluteTimeStamp(0), unit2.getAbsoluteTimeStamp(0))

	def calculateTimepointMapping(self):
		"""
		Calculate the position of every timepoint in every input dataset
		"""
		self.timepointMapping = {}
		dataunits = self.dataUnit.getSourceDataUnits()
		dataunits.sort(self.orderByTime)
		timepoint = 0
		for i, dataunit in enumerate(dataunits):
			for tp in range(0, dataunit.getNumberOfTimepoints()):
				print "Timepoint",timepoint,"maps to",dataunit,tp
				print "Absolute time at tp 0 =",dataunit.getAbsoluteTimeStamp(0)
				self.timepointMapping[timepoint] = (dataunit, tp)
				timepoint += 1
				
	def getImageForTimepoint(self, timepoint):
		"""
		Return the source image for given timepoint
		"""
		dataunit, localTime = self.timepointMapping[timepoint]
		print "Timepoint",timepoint,"maps to timepoint",localTime,"of",dataunit
		return dataunit.getTimepoint(localTime)
		
	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute the filter with given inputs and return the output
		"""
		if not lib.ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None
			
		self.calculateMaximumDimensions()
		if self.parameters["PadDatasets"] and not self.padFilter:
			maxX, maxY, maxZ = self.maxDimensions
			self.padFilter = vtk.vtkImageConstantPad()
			self.padFilter.SetConstant(0)
			self.padFilter.SetOutputWholeExtent(0, maxX-1, 0, maxY-1, 0, maxZ-1)
			
		self.calculateTimepointMapping()
		
		image = self.getImageForTimepoint(self.getCurrentTimepoint())
		if self.parameters["PadDatasets"]:
			self.padFilter.RemoveAllInputs()
			self.padFilter.SetInput(image)
			image = self.padFilter.GetOutput()
			
		return image
