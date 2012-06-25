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

import lib.ProcessingFilter
import lib.FilterTypes
import scripting
import itk
import types
import Logging

class WatershedFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	A filter for doing watershed segmentation
	"""
	name = "Watershed segmentation"
	category = lib.FilterTypes.WATERSHED
	
	def __init__(self, inputs = (1, 1)):
		"""
		Initialization
		"""
		lib.ProcessingFilter.ProcessingFilter.__init__(self, inputs)
		
		
		self.descs = {"Threshold": "Segmentation Threshold", "Level": "Segmentation Level",
		"ObjThreshold": "Remove objects with less voxels than:"}
		self.itkFlag = 1
		self.itkfilter = None
		self.relabelFilter = None
		self.origCtf = None
		self.n = 0
		self.ignoreObjects = 2
		self.data = None

	def getParameterLevel(self, parameter):
		"""
		Return the level of the given parameter
		"""
		return scripting.COLOR_INTERMEDIATE
		
	def getDefaultValue(self, parameter):
		"""
		Return the default value of a parameter
		"""	   
		if parameter == "Threshold":
			return 0.01
		if parameter == "Level":
			return 0.2
		return 0
		
	def getType(self, parameter):
		"""
		Return the type of the parameter
		"""	   
		return types.FloatType
		
	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""			   
		return [["", ("Threshold", "Level")],["Minimum object size (in pixels)", ("ObjThreshold", )]]
	
	def onRemove(self):
		"""
		Callback for when filter is removed
		"""
		self.restoreCtf()

	def onDisable(self):
		"""
		Callback for when filter is disabled
		"""
		self.restoreCtf()

	def restoreCtf(self):
		"""
		Restore palette to the state before using this module
		"""
		if self.origCtf:
			self.dataUnit.getSettings().set("ColorTransferFunction", self.origCtf)
		self.origCtf = None		
	
	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute the filter with given inputs and return the output
		"""					   
		if not lib.ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None
			
		self.eventDesc = "Performing watershed segmentation"
		image = self.getInput(1)
		image = self.convertVTKtoITK(image, cast = types.FloatType)
		self.itkfilter = itk.WatershedImageFilter.IF3.New()
		self.itkfilter.SetInput(image)
		self.itkfilter.SetThreshold(self.parameters["Threshold"])
		self.itkfilter.SetLevel(self.parameters["Level"])
				
		self.setImageType("UL3")
		if update:
			self.itkfilter.Update()
		data = self.itkfilter.GetOutput()
		if not self.relabelFilter:
			self.relabelFilter = itk.RelabelComponentImageFilter[data, data].New()
		self.relabelFilter.SetInput(data)

		th = self.parameters["ObjThreshold"]
		self.relabelFilter.SetMinimumObjectSize(th)
	
		data = self.relabelFilter.GetOutput()
				
		self.relabelFilter.Update()
		n = self.relabelFilter.GetNumberOfObjects()
		settings = self.dataUnit.getSettings()
		ncolors = settings.get("PaletteColors")
		if not self.origCtf or not ncolors or ncolors < n:
			ctf = lib.ImageOperations.watershedPalette(2, n)
			self.data = data
			if not self.origCtf:
				self.origCtf = settings.get("ColorTransferFunction")
			settings.set("ColorTransferFunction", ctf)
			val = [0, 0, 0]
			ctf.GetColor(1, val)
			print "ctf value at 1 =", val, "n colors =", n
			settings.set("PaletteColors", n)

		return data
