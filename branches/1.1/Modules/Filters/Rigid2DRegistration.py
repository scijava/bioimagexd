#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: Rigid2DRegistration.py
 Project: BioImageXD
 Description:

 A module containing the rigid 2d registration filter for the processing
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
import types
import time
import GUI.GUIBuilder
import vtk
import itk
import Logging

CENTEROFMASS = 1
loader = Modules.DynamicLoader.getPluginLoader()
RegistrationFilters = loader.getPluginItem("Task","Process",2).RegistrationFilters

class Rigid2DRegistrationFilter(RegistrationFilters.RegistrationFilter):
	"""
	Rigid2dRegistrationFilter class
	"""
	name = "Rigid registration 2D"
	category = lib.FilterTypes.REGISTRATION
	level = scripting.COLOR_EXPERIENCED

	def __init__(self, inputs = (1,1)):
		"""
		Initializes Rigid 2D Registration object
		"""
		RegistrationFilters.RegistrationFilter.__init__(self,inputs)
		self.descs["RotateAround"] = "Rotate around"
		del self.descs["UsePreviousAsFixed"]
		self.totalTransform = itk.Array.D()
		self.totalTransform.SetSize(5)
		for i in range(5):
			self.totalTransform.SetElement(i,0)
		self.filterDesc = "Performs 2D rigid registration (translation + rotation) between images in time series data\nInput: Grayscale/Binary image\nOutput: Grayscale/Binary image"

	def updateProgress(self):
		"""
		Updates progress of the registration process.
		"""
		currentParameter = self.transform.GetParameters()
		print "M: %f A: %f C: (%f,%f) T: (%f,%f)" %(self.optimizer.GetValue(),currentParameter.GetElement(0),currentParameter.GetElement(1),currentParameter.GetElement(2),currentParameter.GetElement(3),currentParameter.GetElement(4))
		RegistrationFilters.RegistrationFilter.updateProgress(self)

	def getParameterLevel(self, parameter):
		"""
		Return the level of the given parameter
		"""
		if parameter == "RotateAround":
			return scripting.COLOR_BEGINNER
		return RegistrationFilters.RegistrationFilter.getParameterLevel(self,parameter)

	def getDefaultValue(self, parameter):
		"""
		Return the default value of a parameter
		"""
		if parameter == "RotateAround":
			return CENTEROFMASS
		if parameter == "MinimumStepLength":
			return 0.02
		if parameter == "MaximumStepLength":
			return 5.0
		return RegistrationFilters.RegistrationFilter.getDefaultValue(self,parameter)

	def getType(self,parameter):
		"""
		Return the type of the parameter
		"""
		if parameter == "RotateAround":
			return GUI.GUIBuilder.CHOICE
		return RegistrationFilters.RegistrationFilter.getType(self,parameter)

	def getRange(self,parameter):
		"""
		Return the range for a given parameter
		"""
		if parameter == "RotateAround":
			return ("Geometrical center","Center of mass")
		return RegistrationFilters.RegistrationFilter.getRange(self,parameter)

	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""
		return [["Fixed image", ("FixedTimepoint",)], ["", ("BackgroundPixelValue",)], ["Accuracy and speed settings", ("MaxIterations","MaxStepLength","MinStepLength")], ["", ("RotateAround",)]]

	def execute(self, inputs, update = 0, last = 0):
		"""
		Initializes and executes the registration process. Does
		the result transform to the input image and returns transformed image.
		"""
		if not lib.ProcessingFilter.ProcessingFilter.execute(self,inputs):
			return None

		backgroundValue = self.parameters["BackgroundPixelValue"]
		minStepLength = self.parameters["MinStepLength"]
		maxStepLength = self.parameters["MaxStepLength"]
		maxIterations = self.parameters["MaxIterations"]
		useMoments = self.parameters["RotateAround"]
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
		vtkToItk.Update()
		movingImage = vtkToItk.GetOutput()

		fixedImage = self.dataUnit.getSourceDataUnits()[0].getTimepoint(fixedtp)
		fixedImage.SetUpdateExtent(fixedImage.GetWholeExtent())
		fixedImage.Update()
		#fixedImage = self.convertVTKtoITK(fixedImage, cast = types.FloatType)
		vtkToItk2 = itk.VTKImageToImageFilter.IF3.New()
		icast2 = vtk.vtkImageCast()
		icast2.SetOutputScalarTypeToFloat()
		icast2.SetInput(fixedImage)
		vtkToItk2.SetInput(icast2.GetOutput())
		vtkToItk2.Update()
		fixedImage = vtkToItk2.GetOutput()

		# Take only first slice of the data
		fixedRegion = fixedImage.GetLargestPossibleRegion()
		fixedSize = fixedRegion.GetSize()
		movingRegion = movingImage.GetLargestPossibleRegion()
		movingSize = movingRegion.GetSize()

		extractFilter = itk.ExtractImageFilter.IF3IF2.New()
		extractRegion = itk.ImageRegion._3()
		extractSize = itk.Size._3()
		extractIndex = itk.Index._3()
		for i in range(0,3):
			extractIndex.SetElement(i,0)
		extractRegion.SetIndex(extractIndex)
		for i in range(0,2):
			extractSize.SetElement(i, fixedSize.GetElement(i))
		extractRegion.SetSize(extractSize)
		extractFilter.SetExtractionRegion(extractRegion)
		extractFilter.SetInput(fixedImage)
		fixedImage = extractFilter.GetOutput()
		fixedImage.Update()

		extractFilter2 = itk.ExtractImageFilter.IF3IF2.New()
		for i in range(0,2):
			extractSize.SetElement(i, movingSize.GetElement(i))
		extractRegion.SetSize(extractSize)
		extractFilter2.SetExtractionRegion(extractRegion)
		extractFilter2.SetInput(movingImage)
		movingImage = extractFilter2.GetOutput()
		movingImage.Update()

		# Create registration framework's components
		self.registration = itk.ImageRegistrationMethod.IF2IF2.New()
		self.optimizer = itk.RegularStepGradientDescentOptimizer.New()
		self.metric = itk.MeanSquaresImageToImageMetric.IF2IF2.New()
		self.interpolator = itk.LinearInterpolateImageFunction.IF2D.New()
		self.transform = itk.CenteredRigid2DTransform.D.New()

		# Initialize registration framework's components
		self.registration.SetOptimizer(self.optimizer.GetPointer())
		self.registration.SetTransform(self.transform.GetPointer())
		self.registration.SetInterpolator(self.interpolator.GetPointer())
		self.registration.SetMetric(self.metric.GetPointer())
		self.registration.SetFixedImage(fixedImage)
		self.registration.SetMovingImage(movingImage)
		self.registration.SetFixedImageRegion(fixedImage.GetBufferedRegion())
		self.optimizer.SetMaximumStepLength(maxStepLength)
		self.optimizer.SetMinimumStepLength(minStepLength)
		self.optimizer.SetNumberOfIterations(maxIterations)

		# Set optimizer scales
		scales = itk.Array.D()
		scales.SetSize(5)
		translationScale = 1.0/5000.0
		scales.SetElement(0, 1.0)
		for i in range (1,5):
			scales.SetElement(i,translationScale)
		self.optimizer.SetScales(scales)

		# Initialize transform
		initializer = itk.CenteredTransformInitializer[self.transform, fixedImage, movingImage].New()
		initializer.SetTransform(self.transform)
		initializer.SetFixedImage(fixedImage)
		initializer.SetMovingImage(movingImage)
		if useMoments == CENTEROFMASS:
			initializer.MomentsOn()
		else:
			initializer.GeometryOn()
		initializer.InitializeTransform()
			
		self.registration.SetInitialTransformParameters(self.transform.GetParameters())

		iterationCommand = itk.PyCommand.New()
		iterationCommand.SetCommandCallable(self.updateProgress)
		self.optimizer.AddObserver(itk.IterationEvent(),iterationCommand.GetPointer())

		Logging.info("Starting registration")
		startTime = time.time()
		self.registration.StartRegistration()
		finalParameters = self.registration.GetLastTransformParameters()
		Logging.info("Registration took %s seconds"%(time.time() - startTime))
		Logging.info("Final registration parameters")
		Logging.info("Center of rotation = (%f,%f)"%(finalParameters.GetElement(1),finalParameters.GetElement(2)))
		Logging.info("Angle = %f"%(finalParameters.GetElement(0)))
		Logging.info("Translation X = %f"%(finalParameters.GetElement(3)))
		Logging.info("Translation Y = %f"%(finalParameters.GetElement(4)))

		self.resampler = itk.ResampleImageFilter.IF2IF2.New()
		resampleInterpolator = itk.NearestNeighborInterpolateImageFunction.IF2D.New()
		self.transform.SetParameters(finalParameters)
		self.resampler.SetTransform(self.transform.GetPointer())
		self.resampler.SetInput(movingImage)
		self.resampler.SetSize(movingImage.GetLargestPossibleRegion().GetSize())
		self.resampler.SetOutputSpacing(movingImage.GetSpacing())
		self.resampler.SetOutputOrigin(movingImage.GetOrigin())
		self.resampler.SetDefaultPixelValue(backgroundValue)
		self.resampler.SetInterpolator(resampleInterpolator.GetPointer())
		data = self.resampler.GetOutput()
		data.Update()

		data = self.convertITKtoVTK(data, cast = "UC3")
		return data
	
