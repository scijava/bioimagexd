#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: Mean.py
 Project: BioImageXD
 Created: 20.09.2009, LP
 Description:

 A module that contains mean filter for the processing task.
 
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
import itk
import lib.FilterTypes

class MeanFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	A mean filter. Uses itk's MeanImageFilter.
	"""
	name = "Mean"
	category = lib.FilterTypes.FILTERING
	level = scripting.COLOR_BEGINNER

	def __init__(self, inputs = (1,1)):
		"""
		Initialization
		"""
		self.defRadius = (2,2,2)
		lib.ProcessingFilter.ProcessingFilter.__init__(self,(1,1))
		self.itkFlag = 1
		self.descs = {"X": "X:", "Y": "Y:", "Z": "Z", "UseImageSpacing": "Use image spacing"}
		self.filter = None
		self.pc = itk.PyCommand.New()
		self.pc.SetCommandCallable(self.updateProgress)
	

	def updateProgress(self):
		"""
		Update progress event handler
		"""
		lib.ProcessingFilter.ProcessingFilter.updateProgress(self,self.filter,"ProgressEvent")

	def getParameters(self):
		"""
		Returns the parameters for GUI.
		"""
		return [["Radius",("X","Y","Z")],["",("UseImageSpacing",)]]

	def getType(self, param):
		"""
		Returns the types of parameters for GUI.
		@param param Parameter name
		"""
		if param == "UseImageSpacing":
			return types.BooleanType
		return types.IntType

	def getDefaultValue(self, param):
		"""
		Returns the default value of the parameter
		@param param Parameter name
		"""
		if param == "X":
			return self.defRadius[0]
		elif param == "Y":
			return self.defRadius[1]
		elif param == "Z":
			return self.defRadius[2]
		elif param == "UseImageSpacing":
			return True

	def getParameterLevel(self, param):
		"""
		Returns the level of knowledge for using parameter
		@param param Parameter name
		"""
		return scripting.COLOR_BEGINNER

	def execute(self, inputs = (1,1), update = 0, last = 0):
		"""
		Execute filter in input image and return output image
		"""
		if not lib.ProcessingFilter.ProcessingFilter.execute(self,inputs):
			return None

		self.eventDesc = "Mean filter"
		inputImage = self.getInput(1)
		inputImage = self.convertVTKtoITK(inputImage)

		self.filter = itk.MeanImageFilter[inputImage,inputImage].New()
		self.filter.AddObserver(itk.ProgressEvent(),self.pc.GetPointer())

		radiusX = self.parameters["X"]
		radiusY = self.parameters["Y"]
		radiusZ = self.parameters["Z"]
		spacing = inputImage.GetSpacing()
		dim = inputImage.GetLargestPossibleRegion().GetImageDimension()

		if self.parameters["UseImageSpacing"]:
			radiusX = int(radiusX * (1.0 / spacing.GetElement(0)) + 0.5)
			radiusY = int(radiusY * (1.0 / spacing.GetElement(1)) + 0.5)
			if dim > 2:
				radiusZ = int(radiusZ * (1.0 / spacing.GetElement(2)) + 0.5)

		if dim == 2:
			self.filter.SetRadius((radiusX,radiusY))
		elif dim == 3:
			self.filter.SetRadius((radiusX,radiusY,radiusZ))
		
		self.filter.SetInput(inputImage)

		outputImage = self.filter.GetOutput()
		if update:
			outputImage.Update()

		return outputImage
