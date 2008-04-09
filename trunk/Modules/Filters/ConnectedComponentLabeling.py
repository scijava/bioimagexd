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
import itk
import types
import lib.ImageOperations

class ConnectedComponentLabelingFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	A filter for labeling all separate objects in an image
	"""
	name = "Connected component labeling"
	category = lib.FilterTypes.SEGMENTATION
	
	def __init__(self, inputs = (1, 1)):
		"""
		Initialization
		"""		   
		lib.ProcessingFilter.ProcessingFilter.__init__(self, inputs)
		self.ignoreObjects = 1
		
		self.descs = {"Threshold": "Remove objects with less voxels than:"}
		self.itkFlag = 1
		self.origCtf = None
		self.relabelFilter = None
		self.itkfilter = None
		
	def getParameterLevel(self, parameter):
		"""
		Return the level of the given parameter
		"""
		return scripting.COLOR_INTERMEDIATE
			
	def getDefaultValue(self, parameter):
		"""
		Return the default value of a parameter
		"""	   
		return 0
		
	def getType(self, parameter):
		"""
		Return the type of the parameter
		"""	   
		return types.IntType
		
	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""			   
		#return [["",("Level",)]]
		return [["Minimum object size (in pixels)", ("Threshold", )]]

	def onRemove(self):
		"""
		Restore palette upon filter removal
		"""		   
		if self.origCtf:
			self.dataUnit.getSettings().set("ColorTransferFunction", self.origCtf)
	
	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute the filter with given inputs and return the output
		"""					   
		if not lib.ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None
			
		image = self.getInput(1)
		image = self.convertVTKtoITK(image)
		self.itkfilter = itk.ConnectedComponentImageFilter[image, itk.Image.UL3].New()
		
		self.eventDesc = "Performing connected component labeling"
		self.itkfilter.SetInput(image)
				
		self.setImageType("UL3")
		self.itkfilter.Update()
		data = self.itkfilter.GetOutput()
	
		self.relabelFilter = itk.RelabelComponentImageFilter[data, data].New()
		self.relabelFilter.SetInput(data)
		th = self.parameters["Threshold"]
		if th:
			self.relabelFilter.SetMinimumObjectSize(th)
	
		data = self.relabelFilter.GetOutput()

		self.eventDesc = "Relabeling segmented image"
		self.relabelFilter.Update()
		n = self.relabelFilter.GetNumberOfObjects()
	
		settings = self.dataUnit.getSettings()
		ncolors = settings.get("PaletteColors")
		if not self.origCtf or not ncolors or ncolors < n:
			ctf = lib.ImageOperations.watershedPalette(1, n, ignoreColors = 1)
			if not self.origCtf:
				self.origCtf = self.dataUnit.getColorTransferFunction()
			self.dataUnit.getSettings().set("ColorTransferFunction", ctf)
			settings.set("PaletteColors", n)
		return data
