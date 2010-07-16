#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: SlicesTranslationRegistration.py
 Project: BioImageXD
 Description:

 A module containing the 2D slices translation registration filter for
 the processing task.
							
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

import scripting
import lib.ProcessingFilter
import lib.FilterTypes
import itk
import vtk
import types
import GUI.GUIBuilder
COM = 0
CENTROID = 1

class SlicesTranslationRegistrationFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	SlicesTranslationRegistrationFilter class
	"""
	name = "Slices Translation Registration"
	category = lib.FilterTypes.REGISTRATION
	level = scripting.COLOR_EXPERIENCED

	def __init__(self, inputs = (2,2)):
		"""
		Initializes new object
		"""
		lib.ProcessingFilter.ProcessingFilter.__init__(self,inputs)
		self.itkFlag = 1
		self.descs = {"BackgroundPixelValue": "Set background pixel value",
					  "Method": "Geometry measure",
					  "FixedSlice": "Slice for fixed image"}
		self.coms = []

	def updateProgress(self, slices, total):
		"""
		Updates progress of registration
		"""
		progress = float(slices) / total
		self.executive.updateITKProgress("Slices translation registration", progress)

	def getInputName(self, n):
		"""
		Return name of the input
		"""
		if n == 1:
			return "Segmented image"
		return "Source dataset"
		
	def getParameterLevel(self, param):
		"""
		Return experience level
		"""
		return scripting.COLOR_BEGINNER

	def getDefaultValue(self, param):
		"""
		Return default value of parameter
		"""
		if param == "BackgroundPixelValue":
			return 0
		if param == "Method":
			return COM
		if param == "FixedSlice":
			return 1

	def getType(self, param):
		"""
		Return type of parameter
		"""
		if param == "Method":
			return GUI.GUIBuilder.CHOICE
		if param == "FixedSlice":
			return GUI.GUIBuilder.SLICE
		return types.IntType

	def getParameters(self):
		"""
		Return the list of parameters for GUI configuration
		"""
		return [["", ("Method",)],["", ("BackgroundPixelValue",)],["", ("FixedSlice",)]]

	def getRange(self, param):
		"""
		Returns range of list parameter
		@param param Parameter name
		"""
		if param == "Method":
			return ("COM","Centroid")
		if param == "FixedSlice":
			return (1, self.dataUnit.getDimensions()[2])
		
	def execute(self, inputs, update = 0, last = 0):
		"""
		Executes registration process and returns translated result
		"""
		if not lib.ProcessingFilter.ProcessingFilter.execute(self,inputs):
			return None

		inputImage = self.getInput(1)
		origImage = self.getInput(2)
		inputImage = self.convertVTKtoITK(inputImage)
		inputImage.DisconnectPipeline()
		origImage = self.convertVTKtoITK(origImage)
		origImage.DisconnectPipeline()

		self.coms = []
		inputSlices = self.splitITKImageIntoSlices(inputImage)
		origSlices = self.splitITKImageIntoSlices(origImage)
		self.slices = [(inputSlices[i], origSlices[i]) for i in range(len(inputSlices))]

		bgValue = self.parameters["BackgroundPixelValue"]
		region = inputImage.GetLargestPossibleRegion()
		size = region.GetSize()
		index = region.GetIndex()
		imageType = self.getITKImageType(inputImage)
		origType = self.getITKImageType(origImage)
		sliceType = eval("itk.Image.%s3"%imageType[0])
		orgSliceType = eval("itk.Image.%s3"%origType[0])
		lm = itk.LabelMap._3
		
		for labelSlice, origSlice in self.slices:
			labelStatistics = itk.LabelImageToStatisticsLabelMapFilter[sliceType,orgSliceType,lm].New()
			labelStatistics.SetInput1(labelSlice)
			labelStatistics.SetInput2(origSlice)
			labelStatistics.Update()
			labelMap = labelStatistics.GetOutput()
			try:
				labelObj = labelMap.GetLabelObject(labelMap.GetLabels()[-1])
				if self.parameters["Method"] == COM:
					centerOfGravity = labelObj.GetCenterOfGravity()
					com = (centerOfGravity[0], centerOfGravity[1])
				else:
					centroid = labelObj.GetCentroid()
					com = (centroid[0], centroid[1])
			except:
				com = None
			self.coms.append(com)

		print "Coms =",self.coms
		# Translate
		translation = itk.TranslationTransform.D3.New()
		fixedSlice = self.parameters["FixedSlice"] - 1
		resample = itk.ResampleImageFilter[orgSliceType,orgSliceType].New()
		interpolator = itk.NearestNeighborInterpolateImageFunction.IUC3D.New()
		resample.SetInterpolator(interpolator)
		for sliceIndex, slices in enumerate(self.slices):
			if self.coms[sliceIndex] is None:
				translatedImage = origSlice
			else:
				labelSlice, origSlice = slices
				translation.SetParameters((self.coms[sliceIndex][0] - self.coms[fixedSlice][0], self.coms[fixedSlice][1] - self.coms[sliceIndex][1], 0))
				resample.SetTransform(translation)
				resample.SetInput(origSlice)
				resample.SetSize(origSlice.GetLargestPossibleRegion().GetSize())
				resample.SetOutputSpacing(origSlice.GetSpacing())
				resample.SetOutputOrigin(origSlice.GetOrigin())
				resample.SetDefaultPixelValue(bgValue)
				translatedImage = resample.GetOutput()
				translatedImage.Update()
				translatedImage.DisconnectPipeline()
				
			# Paste slice to volume
			origImage = self.pasteITKImageSlice(origImage, translatedImage, sliceIndex)

		self.slices = None
		return origImage
