#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: FourierFilters.py
 Project: BioImageXD
 Description:

 A module that contains parent class for different low/high pass filters in
 fourier domain for the processing task.
 
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
import lib.FilterTypes
import vtk
import types
import scripting

class FourierFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	A parent class for different fourier filters
	"""
	name = "Fourier filter"
	category = lib.FilterTypes.FOURIER

	def __init__(self, inputs = (1,1)):
		"""
		Initialization
		"""
		lib.ProcessingFilter.ProcessingFilter.__init__(self,(1,1))
		self.descs = {"XCutOff": "X Cut off:", "YCutOff": "Y Cut off:", "ZCutOff": "Z Cut off"}
		self.filter = None

	def updateProgress(self):
		"""
		Update progress event handler
		"""
		lib.ProcessingFilter.ProcessingFilter.updateProgress(self,self.filter,"ProgressEvent")

	def getParameters(self):
		"""
		Return parameters for the GUI
		"""
		return [["Cut off", ("XCutOff", "YCutOff", "ZCutOff")],]

	def getDefaultValue(self, param):
		"""
		Returns the default value of param
		"""
		return 0.1
		
	def getParameterLevel(self, param):
		"""
		Returns the level of knowledge for using parameter
		@param param Parameter name
		"""
		return scripting.COLOR_EXPERIENCED

	def getType(self, param):
		"""
		Returns param type
		"""
		return types.FloatType

	def execute(self, inputs = (1,1), update = 0, last = 0):
		"""
		Execute filter in input image and return output image
		"""
		if not lib.ProcessingFilter.ProcessingFilter.execute(self,inputs):
			return None

		inputImage = self.getInput(1)
		self.filter.SetXCutOff(self.parameters["XCutOff"])
		self.filter.SetYCutOff(self.parameters["YCutOff"])
		self.filter.SetZCutOff(self.parameters["ZCutOff"])

		self.filter.SetInput(inputImage)
		outputImage = self.filter.GetOutput()
		
		if update:
			outputImage.Update()

		return outputImage

def getFilters():
	"""
	This function returns all the filter classes in this module and is used by
	ManipulationFilter.getFilterList()
	"""
	return []
