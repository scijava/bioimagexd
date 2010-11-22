#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: Pad.py
 Project: BioImageXD
 Description:

 A module that implements padding filter for the processing task.
 
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
import itk
import lib.FilterTypes
import types
import Logging

class PadFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	A padding filter.
	"""
	name = "Pad data"
	category = lib.FilterTypes.CONVERSION
	level = scripting.COLOR_BEGINNER

	def __init__(self, inputs = (1,1)):
		"""
		Initialization
		"""
		lib.ProcessingFilter.ProcessingFilter.__init__(self,(1,1))
		self.itkFlag = 1
		self.descs = {"OutputX": "X:", "OutputY": "Y:", "OutputZ": "Z:",
					  "IndexX": "X:", "IndexY": "Y:", "IndexZ": "Z:",
					  "PadIntensity": "Padding intensity"}
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
		return [["Output data size", ("OutputX","OutputY","OutputZ")],["Start index", ("IndexX","IndexY","IndexZ")], ["", ("PadIntensity",)]]

	def getType(self, param):
		"""
		Returns the types of parameters for GUI.
		@param param Parameter name
		"""
		return types.IntType

	def getDefaultValue(self, param):
		"""
		Returns the default value of the parameter
		@param param Parameter name
		"""
		if param in ["OutputX", "OutputY"]:
			return 0
		if param == "OutputZ":
			return 0
		if param in ["IndexX", "IndexY", "IndexZ", "PadIntensity"]:
			return 0

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

		self.eventDesc = "Padding data"
		inputImage = self.getInput(1)
		inputImage = self.convertVTKtoITK(inputImage)
		imageType = self.getITKImageType(inputImage)
		
		currentRegion = inputImage.GetLargestPossibleRegion()
		currentIndex = currentRegion.GetIndex()
		currentSize = currentRegion.GetSize()

		outputDim = imageType[1]
		
		outputSize = eval("itk.Size._%d()"%outputDim)
		outputSize[0] = self.parameters["OutputX"]
		outputSize[1] = self.parameters["OutputY"]
		if outputDim == 3:
			outputSize[2] = self.parameters["OutputZ"]
		outputIndex = eval("itk.Index._%d()"%outputDim)
		for i in range(outputDim):
			outputIndex[i] = 0

		dataIndex = eval("itk.Index._%d()"%outputDim)
		dataIndex[0] = self.parameters["IndexX"]
		dataIndex[1] = self.parameters["IndexY"]
		if outputDim == 3:
			dataIndex[2] = self.parameters["IndexZ"]

		# Check that given index and data size fits into wanter output size
		paramsOk = 1
		for i in range(outputDim):
			if dataIndex[i] + currentSize[i] > outputSize[i]:
				paramsOk = 0
		if not paramsOk:
			Logging.error("Padding dataset failed", "Data starting from given index doesn't fit into output size.")
			return inputImage

		# Create output image
		outputImage = eval("itk.Image.%s%d.New()"%(imageType[0],outputDim))
		outputRegion = eval("itk.ImageRegion._%d()"%outputDim)
		outputRegion.SetSize(outputSize)
		outputRegion.SetIndex(outputIndex)
		outputImage.SetRegions(outputRegion)
		outputImage.SetSpacing(inputImage.GetSpacing())
		outputImage.SetOrigin(inputImage.GetOrigin())
		outputImage.Allocate()
		outputImage.FillBuffer(self.parameters["PadIntensity"])
		
		self.filter = itk.PasteImageFilter[outputImage].New()
		self.filter.SetDestinationImage(outputImage)
		self.filter.SetSourceImage(inputImage)
		self.filter.SetSourceRegion(currentRegion)
		self.filter.SetDestinationIndex(dataIndex)
		self.filter.Update()
		outputImage = self.filter.GetOutput()

		return outputImage
