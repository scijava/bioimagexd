#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: TranslationRegistration2D.py
 Project: BioImageXD
 Description:

 A module containing the translation registration 2D filter for the processing
 task.
							
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

import Modules
import scripting
import lib
import itk
import Logging
import types
import time

loader = Modules.DynamicLoader.getPluginLoader()
RegistrationFilters = loader.getPluginItem("Task","Process",2).RegistrationFilters

class TranslationRegistration2DFilter(RegistrationFilters.RegistrationFilter):
	"""
	TranslationRegistration2DFilter class
	"""
	name = "Translation Registration 2D"
	category = lib.FilterTypes.REGISTRATION
	level = scripting.COLOR_EXPERIENCED

	def __init__(self, inputs = (1,1)):
		"""
		Initializes new object
		"""
		RegistrationFilters.RegistrationFilter.__init__(self,inputs)
		self.totalTranslation = itk.Array.D()
		self.totalTranslation.SetSize(2)
		for i in range(2):
			self.totalTranslation[i] = 0
		self.descs["UsePreviousAsFixed"] = "Use previous slice as fixed image"
		self.descs["FixedTimepoint"] = "Slice for fixed image"

	def updateProgress(self):
		"""
		Updates progress of registration
		"""
		currentParameter = self.transform.GetParameters()
		#print "M: %f  T: %f %f" %(self.optimizer.GetValue(),currentParameter[0],currentParameter[1])
		RegistrationFilters.RegistrationFilter.updateProgress(self)

	def getRange(self, param):
		"""
		Return the range for a given parameter
		"""
		if param == "FixedTimepoint":
			return (1, self.dataUnit.getDimensions()[2])
		else:
			return RegistrationFilters.RegistrationFilter.getRange(self,param)

	def execute(self, inputs, update = 0, last = 0):
		"""
		Initializes and executes the registration process. Does
		the result translation to input image and returns translated image.
		"""
		if not lib.ProcessingFilter.ProcessingFilter.execute(self,inputs):
			return None

		backgroundValue = self.parameters["BackgroundPixelValue"]
		minStepLength = self.parameters["MinStepLength"]
		maxStepLength = self.parameters["MaxStepLength"]
		maxIterations = self.parameters["MaxIterations"]
		usePrevious = self.parameters["UsePreviousAsFixed"]
		fixedSlice = self.parameters["FixedTimepoint"]

		inputImage = self.getInput(1)
		inputITK = self.convertVTKtoITK(inputImage, cast = types.FloatType)
		itkSlices = self.splitITKImageIntoSlices(inputITK)
		regSlices = self.splitITKImageIntoSlices(inputITK, true2D = True)

		# Create registration framework's components
		self.registration = itk.ImageRegistrationMethod.IF2IF2.New()
		self.metric = itk.MeanSquaresImageToImageMetric.IF2IF2.New()
		self.interpolator = itk.LinearInterpolateImageFunction.IF2D.New()
		self.optimizer = itk.RegularStepGradientDescentOptimizer.New()
		self.transform = None
		resampler = itk.ResampleImageFilter.IF3IF3.New()

		for index, movingImage in enumerate(regSlices):
			if usePrevious and index-1 >= 0:
				fixedImage = regSlices[index-1]
			elif usePrevious:
				fixedImage = movingImage
			else:
				fixedImage = regSlices[fixedSlice-1]
			
			# Use last transform parameters as initialization to registration
			#if self.transform is not None and not usePrevious:
			#	initialParameters = self.transform.GetParameters()
			#else:
			#	initialParameters = None

			initialParameters = None
			# Initialize registration framework's components
			if self.transform is None:
				self.transform = itk.TranslationTransform.D2.New()

			# Use last transform parameters as initialization to registration
			if initialParameters is None:
				self.transform.SetIdentity()
				initialParameters = self.transform.GetParameters()

			self.registration.SetOptimizer(self.optimizer)
			self.registration.SetTransform(self.transform)
			self.registration.SetInterpolator(self.interpolator)
			self.registration.SetMetric(self.metric)
			self.registration.SetFixedImage(fixedImage)
			self.registration.SetMovingImage(movingImage)
			self.registration.SetFixedImageRegion(fixedImage.GetBufferedRegion())
			self.registration.SetInitialTransformParameters(initialParameters)
			self.optimizer.SetMaximumStepLength(maxStepLength)
			self.optimizer.SetMinimumStepLength(minStepLength)
			self.optimizer.SetNumberOfIterations(maxIterations)
				
			iterationCommand = itk.PyCommand.New()
			iterationCommand.SetCommandCallable(self.updateProgress)
			self.optimizer.AddObserver(itk.IterationEvent(),iterationCommand)
			# Execute registration
			Logging.info("Starting registration")
			startTime = time.time()
			self.registration.StartRegistration()
			finalParameters = self.registration.GetLastTransformParameters()
			Logging.info("Registration took %s seconds"%(time.time() - startTime))
			Logging.info("Final Registration parameters")
			Logging.info("Translation X = %f"%(finalParameters[0]))
			Logging.info("Translation Y = %f"%(finalParameters[1]))

			if usePrevious:
				for i in range(2):
					self.totalTranslation[i] = self.totalTranslation[i] + finalParameters[i]
				finalParameters = self.totalTranslation

			Logging.info("Use transform parameters")
			Logging.info("Translation X = %f"%(finalParameters[0]))
			Logging.info("Translation Y = %f"%(finalParameters[1]))

			# Translate input image using results from the registration
			resampleTranslation = itk.Array.D()
			resampleTranslation.SetSize(3)
			for i in range(2):
				resampleTranslation[i] = finalParameters[i]
			resampleTranslation[2] = 0
			resampleTransform = itk.TranslationTransform.D3.New()
			resampleTransform.SetParameters(resampleTranslation)
			resampler.SetTransform(resampleTransform)
			
			resampler.SetInput(itkSlices[index])
			region = itkSlices[index].GetLargestPossibleRegion()
			resampler.SetSize(region.GetSize())
			resampler.SetOutputSpacing(itkSlices[index].GetSpacing())
			resampler.SetOutputOrigin(itkSlices[index].GetOrigin())
			resampler.SetDefaultPixelValue(backgroundValue)
			data = resampler.GetOutput()
			data.Update()

			# Paste resampler slice to original data
			inputITK = self.pasteITKImageSlice(inputITK, data, index)

		return inputITK
