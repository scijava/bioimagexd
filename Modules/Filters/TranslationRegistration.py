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

import Modules
import scripting
import lib
import itk
import Logging
import types
import time
import vtk

loader = Modules.DynamicLoader.getPluginLoader()
RegistrationFilters = loader.getPluginItem("Task","Process",2).RegistrationFilters

class TranslationRegistrationFilter(RegistrationFilters.RegistrationFilter):
	"""
	TranslationRegistrationFilter class
	"""
	name = "Translation registration"
	category = lib.FilterTypes.REGISTRATION
	level = scripting.COLOR_EXPERIENCED

	def __init__(self, inputs = (1,1)):
		"""
		Initializes new object
		"""
		RegistrationFilters.RegistrationFilter.__init__(self,inputs)
		self.totalTranslation = itk.Array.D()
		self.totalTranslation.SetSize(3)
		for i in range(3):
			self.totalTranslation.SetElement(i,0)

	def updateProgress(self):
		"""
		Updates progress of registration
		"""
		currentParameter = self.transform.GetParameters()
		print "M: %f  T: %f %f %f" %(self.optimizer.GetValue(),currentParameter.GetElement(0),currentParameter.GetElement(1),currentParameter.GetElement(2))
		RegistrationFilters.RegistrationFilter.updateProgress(self)

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

		if usePrevious:
			if scripting.processingTimepoint > 0:
				fixedtp = scripting.processingTimepoint - 1
			else:
				fixedtp = 0
		else:
			fixedtp = self.parameters["FixedTimepoint"] - 1

		movingImage = self.getInput(1)
		movingImage.SetUpdateExtent(movingImage.GetWholeExtent())
		movingImage.Update()

		# Create copy of data, otherwise movingImage will point to same image
		# as fixedImage
		mi = vtk.vtkImageData()
		mi.DeepCopy(movingImage)
		movingImage = mi
		movingImage.Update()
		#movingImage = self.convertVTKtoITK(movingImage, cast = types.FloatType)
		# Following is dirty but currently has to be done this way since
		# convertVTKtoITK doesn't work with two dataset unless
		# itkConfig.ProgressCallback is set and that eats all memory.
		vtkToItk = itk.VTKImageToImageFilter.IF3.New()
		icast = vtk.vtkImageCast()
		icast.SetOutputScalarTypeToFloat()
		icast.SetInput(movingImage)
		vtkToItk.SetInput(icast.GetOutput())
		movingImage = vtkToItk.GetOutput()
		movingImage.Update()

		fixedImage = self.dataUnit.getSourceDataUnits()[0].getTimepoint(fixedtp)
		fixedImage.SetUpdateExtent(fixedImage.GetWholeExtent())
		fixedImage.Update()
			
		#fixedImage = self.convertVTKtoITK(fixedImage, cast = types.FloatType)
		vtkToItk2 = itk.VTKImageToImageFilter.IF3.New()
		icast2 = vtk.vtkImageCast()
		icast2.SetOutputScalarTypeToFloat()
		icast2.SetInput(fixedImage)
		vtkToItk2.SetInput(icast2.GetOutput())
		fixedImage = vtkToItk2.GetOutput()
		fixedImage.Update()

		# Use last transform parameters as initialization to this registration
		if self.transform and not usePrevious:
			initialParameters = self.transform.GetParameters()
		else:
			initialParameters = None

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
		#fixedSize = fixedImage.GetLargestPossibleRegion().GetSize()
		#region = itk.ImageRegion._3()
		#size = itk.Size._3()
		#index = itk.Index._3()
		#index.SetElement(0, -fixedSize.GetElement(0))
		#index.SetElement(1, -fixedSize.GetElement(1))
		#index.SetElement(2, -fixedSize.GetElement(2))
		#size.SetElement(0, 3*fixedSize.GetElement(0))
		#size.SetElement(1, 3*fixedSize.GetElement(1))
		#size.SetElement(2, 3*fixedSize.GetElement(2))
		#region.SetIndex(index)
		#region.SetSize(size)
		
		self.registration.SetFixedImageRegion(fixedImage.GetBufferedRegion())
		#self.registration.SetFixedImageRegion(region)

		# Use last transform parameters as initialization to this registration
		if not initialParameters:
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

		if usePrevious:
			for i in range(3):
				self.totalTranslation.SetElement(i,self.totalTranslation.GetElement(i) + finalParameters.GetElement(i))
			finalParameters = self.totalTranslation

		# del filters to free memory
		del self.metric
		del self.optimizer
		del self.interpolator
		del self.registration
		
		Logging.info("Use transform parameters")
		Logging.info("Translation X = %f"%(finalParameters.GetElement(0)))
		Logging.info("Translation Y = %f"%(finalParameters.GetElement(1)))
		Logging.info("Translation Z = %f"%(finalParameters.GetElement(2)))
		# Translate input image using results from the registration
		resampler = itk.ResampleImageFilter.IF3IF3.New()
		self.transform.SetParameters(finalParameters)
		resampler.SetTransform(self.transform.GetPointer())
		resampler.SetInput(movingImage)
		region = movingImage.GetLargestPossibleRegion()
		resampler.SetSize(region.GetSize())
		resampler.SetOutputSpacing(movingImage.GetSpacing())
		resampler.SetOutputOrigin(movingImage.GetOrigin())
		resampler.SetDefaultPixelValue(backgroundValue)
		data = resampler.GetOutput()
		data.Update()

		data = self.convertITKtoVTK(data, cast = "UC3")
		return data

