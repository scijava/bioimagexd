#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: NonUniformIlluminationCorrection.py
 Project: BioImageXD
 Description:

 A module that contains non-uniform illumination correction filter for the
 processing task.
 
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
import lib.FilterTypes
import types
import itk

class NonUniformIlluminationCorrectionFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	A non-uniform illumination correction filter. Uses
	itkN3MRIBiasFieldCorrection filter from Insight Journal.
	"""
	name = "Non-uniform illumination correction"
	category = lib.FilterTypes.MISCFILTERING
	level = scripting.COLOR_BEGINNER

	def __init__(self, inputs = (1,1)):
		"""
		Initialization
		"""
		lib.ProcessingFilter.ProcessingFilter.__init__(self,(1,1))
		self.itkFlag = 1
		self.descs = {"ShrinkFactor": "Shrink factor",
					  "MaxIterations": "Maximum iterations",
					  "NumFittingLevels": "Number of fitting levels"}
		self.filter = None
		self.pc = itk.PyCommand.New()
		self.pc.SetCommandCallable(self.updateProgress)
		self.filterDesc = "Corrects non-uniform background illumination from image\nInput: Grayscale image\nOutput: Grayscale image"

	def updateProgress(self):
		"""
		Update progress event handler
		"""
		lib.ProcessingFilter.ProcessingFilter.updateProgress(self,self.filter,"ProgressEvent")

	def getParameters(self):
		"""
		Returns the parameters for GUI.
		"""
		return [["Parameters", ("ShrinkFactor", "MaxIterations", "NumFittingLevels")],]

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
		if param == "ShrinkFactor":
			return 4
		if param == "MaxIterations":
			return 100
		if param == "NumFittingLevels":
			return 4

	def getParameterLevel(self, param):
		"""
		Returns the level of knowledge for using parameter
		@param param Parameter name
		"""
		if param in ["ShrinkFactor","MaxIterations"]:
			return scripting.COLOR_BEGINNER
		return scripting.COLOR_EXPERIENCED

	def execute(self, inputs = (1,1), update = 0, last = 0):
		"""
		Execute filter in input image and return output image
		"""
		if not lib.ProcessingFilter.ProcessingFilter.execute(self,inputs):
			return None

		self.eventDesc = "Correcting illumination"
		inputImage = self.getInput(1)
		inputImage = self.convertVTKtoITK(inputImage)

		origOrigin = inputImage.GetOrigin()
		origSpacing = inputImage.GetSpacing()
		origSize = inputImage.GetLargestPossibleRegion().GetSize()
		shrinkImage = inputImage
		if self.parameters["ShrinkFactor"] > 1:
			shrinkFilter = itk.ShrinkImageFilter[inputImage,inputImage].New()
			shrinkFilter.SetInput(inputImage)
			shrinkFilter.SetShrinkFactors(self.parameters["ShrinkFactor"])
			shrinkImage = shrinkFilter.GetOutput()

		shrinkImage.Update()
		shrinkRegion = shrinkImage.GetLargestPossibleRegion()
		dim = shrinkRegion.GetImageDimension()
		maskImage = eval("itk.Image.UC%d.New()"%dim)
		maskImage.SetRegions(shrinkRegion)
		maskImage.Allocate()
		maskImage.FillBuffer(1)

		self.filter = itk.N3MRIBiasFieldCorrectionImageFilter[shrinkImage,maskImage].New()
		self.filter.SetInput(shrinkImage)
		self.filter.SetMaskImage(maskImage)
		self.filter.SetMaximumNumberOfIterations(self.parameters["MaxIterations"])
		self.filter.SetNumberOfFittingLevels(self.parameters["NumFittingLevels"])
		self.filter.AddObserver(itk.ProgressEvent(),self.pc.GetPointer())
		self.filter.Update()

		if self.parameters["ShrinkFactor"] > 1:
			biasField = self.filter.GetBiasField()

			resample = itk.ResampleImageFilter[biasField,biasField].New()
			interpolator = eval("itk.LinearInterpolateImageFunction.IF%dD.New()"%dim)
			castToFloat = itk.CastImageFilter[inputImage,biasField].New()
			divider = itk.DivideImageFilter[biasField,biasField,biasField].New()
			castToOrig = itk.CastImageFilter[biasField,inputImage].New()

			resample.SetInput(biasField)
			resample.SetDefaultPixelValue(1.0)
			resample.SetOutputOrigin(origOrigin)
			resample.SetOutputSpacing(origSpacing)
			resample.SetSize(origSize)
			resample.SetInterpolator(interpolator.GetPointer())
			
			castToFloat.SetInput(inputImage)
			divider.SetInput1(castToFloat.GetOutput())
			divider.SetInput2(resample.GetOutput())
			castToOrig.SetInput(divider.GetOutput())
			outputImage = castToOrig.GetOutput()
			outputImage.Update()
		else:
			outputImage = self.filter.GetOutput()

		return outputImage
