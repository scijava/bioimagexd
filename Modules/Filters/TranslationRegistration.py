#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: TranslationRegistration.py
 Project: BioImageXD
 Created: 14.12.2007, LP
 Description:

 A module containing the translation registration filter for the processing
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

import Modules.Task.Manipulation.RegistrationFilters as RegistrationFilters
import scripting
import lib
import itk
import Logging
import types
import time
import vtk

class TranslationRegistrationFilter(RegistrationFilters.RegistrationFilter):
	"""
	Created: 14.12.2007, LP
	Description: TranslationRegistrationFilter class
	"""
	name = "Translation 3D Registration"
	category = lib.FilterTypes.REGISTRATION
	level = scripting.COLOR_EXPERIENCED

	def __init__(self, inputs = (1,1)):
		"""
		Created: 14.12.2007, LP
		Description: Initializes new object
		"""
		RegistrationFilters.RegistrationFilter.__init__(self,inputs)

	def updateProgress(self):
		"""
		Created: 18.12.2007, LP
		Description: Updates progress of registration
		"""
		currentParameter = self.transform.GetParameters()
		print "M: %f  T: %f %f %f" %(self.optimizer.GetValue(),currentParameter.GetElement(0),currentParameter.GetElement(1),currentParameter.GetElement(2))
		RegistrationFilters.RegistrationFilter.updateProgress(self)

	def execute(self, inputs, update = 0, last = 0):
		"""
		Created: 14.12.2007, LP
		Description: Initializes and executes the registration process. Does
		the result translation to input image and returns translated image.
		"""
		if not lib.ProcessingFilter.ProcessingFilter.execute(self,inputs):
			return None

		fixedtp = self.parameters["FixedTimepoint"] - 1
		backgroundValue = self.parameters["BackgroundPixelValue"]
		minStepLength = self.parameters["MinStepLength"]
		maxStepLength = self.parameters["MaxStepLength"]
		maxIterations = self.parameters["MaxIterations"]

		movingImage = self.getInput(1)
		movingImage.SetUpdateExtent(movingImage.GetWholeExtent())
		movingImage.Update()
		# Create copy of data, otherwise movingImage will point to same image
		# as fixedImage
		mi = vtk.vtkImageData()
		mi.DeepCopy(movingImage)
		movingImage = mi
		movingImage.Update()
		
		fixedImage = self.dataUnit.getSourceDataUnits()[0].getTimepoint(fixedtp)
		fixedImage.SetUpdateExtent(fixedImage.GetWholeExtent())
		fixedImage.Update()
		movingImage = self.convertVTKtoITK(movingImage, cast = types.FloatType)
		fixedImage = self.convertVTKtoITK(fixedImage, cast = types.FloatType)

		# Create registration framework's components
		self.registration = itk.ImageRegistrationMethod.IF3IF3.New()
		self.metric = itk.MeanSquaresImageToImageMetric.IF3IF3.New()
		self.transform = itk.TranslationTransform.D3.New()
		self.interpolator = itk.LinearInterpolateImageFunction.IF3D.New()
		self.optimizer = itk.RegularStepGradientDescentOptimizer.New()

		# Initialize registration framework's components
		self.registration.SetOptimizer(self.optimizer.GetPointer())
		self.registration.SetTransform(self.transform.GetPointer())
		self.registration.SetInterpolator(self.interpolator.GetPointer())
		self.registration.SetMetric(self.metric.GetPointer())
		self.registration.SetFixedImage(fixedImage)
		self.registration.SetMovingImage(movingImage)
		self.registration.SetFixedImageRegion(fixedImage.GetBufferedRegion())
		self.transform.SetIdentity()
		initialParameters = self.transform.GetParameters()
		self.registration.SetInitialTransformParameters(initialParameters)
		self.optimizer.SetMaximumStepLength(maxStepLength)
		self.optimizer.SetMinimumStepLength(minStepLength)
		self.optimizer.SetNumberOfIterations(maxIterations)
		
		iterationCommand = itk.PyCommand.New()
		iterationCommand.SetCommandCallable(self.updateProgress)
		self.optimizer.AddObserver(itk.IterationEvent(),iterationCommand.GetPointer())
		# Execute registration
		Logging.info("Starting registration")
		startTime = time.time()
		self.registration.StartRegistration()
		finalParameters = self.registration.GetLastTransformParameters()
		Logging.info("Registration took %s seconds"%(time.time() - startTime))
		Logging.info("Final Registration parameters")
		Logging.info("Translation X = %f"%(finalParameters.GetElement(0)))
		Logging.info("Translation Y = %f"%(finalParameters.GetElement(1)))
		Logging.info("Translation Z = %f"%(finalParameters.GetElement(2)))

		# Translate input image using results from the registration
		self.resampler = itk.ResampleImageFilter.IF3IF3.New()
		self.resampler.SetTransform(self.transform.GetPointer())
		self.resampler.SetInput(movingImage)
		region = fixedImage.GetLargestPossibleRegion()
		self.resampler.SetSize(region.GetSize())
		self.resampler.SetOutputSpacing(fixedImage.GetSpacing())
		self.resampler.SetOutputOrigin(fixedImage.GetOrigin())
		self.resampler.SetDefaultPixelValue(backgroundValue)
		dataBeforeCast = self.resampler.GetOutput()
		dataBeforeCast.Update()
		
		data = self.convertITKtoVTK(dataBeforeCast, imagetype = "UC3")
		return data

