#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: VersorRigid3DRegistration.py
 Project: BioImageXD
 Description:

 A module containing the versor rigid 3d registration filter for the processing
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

class VersorRigid3DRegistrationFilter(RegistrationFilters.RegistrationFilter):
	"""
	VersorRigid3dRegistrationFilter class
	"""
	name = "Versor Rigid Registration 3D"
	category = lib.FilterTypes.REGISTRATION
	level = scripting.COLOR_EXPERIENCED

	def __init__(self, inputs = (1,1)):
		"""
		Initializes Versor Rigid 3d Registration object
		"""
		RegistrationFilters.RegistrationFilter.__init__(self,inputs)
		self.descs["RotateAround"] = "Rotate around"
		self.totalTransform = itk.Array.D()
		self.totalTransform.SetSize(6)
		for i in range(6):
			self.totalTransform.SetElement(i,0)

	def updateProgress(self):
		"""
		Updates progress of the registration process.
		"""
		currentParameter = self.transform.GetParameters()
		print "M: %f T: %f %f %f V: %f %f %f" %(self.optimizer.GetValue(),currentParameter.GetElement(3),currentParameter.GetElement(4),currentParameter.GetElement(5),currentParameter.GetElement(0),currentParameter.GetElement(1),currentParameter.GetElement(2))
		RegistrationFilters.RegistrationFilter.updateProgress(self)

	def getParameterLevel(self, parameter):
		"""
		Return the level of the given parameter
		"""
		if parameter == "RotateAround":
			return scripting.COLOR_INTERMEDIATE
		return RegistrationFilters.RegistrationFilter.getParameterLevel(self,parameter)

	def getDefaultValue(self, parameter):
		"""
		Return the default value of a parameter
		"""
		if parameter == "RotateAround":
			return 0
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
		params = RegistrationFilters.RegistrationFilter.getParameters(self)
		addParams = ["", ("RotateAround",)]
		params.append(addParams)
		return params

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
		useMoments = self.parameters["RotateAround"]
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

		# Use last transform parameters as initialization to this registration
		if self.transform and not usePrevious:
			initialParameters = self.transform.GetParameters()
		else:
			initialParameters = None

		# Create registration framework's components
		self.registration = itk.ImageRegistrationMethod.IF3IF3.New()
		try:
			self.optimizer = itk.VersorRigid3DTransformOptimizer.New()
		except:
			Logging.error("Versor Rigid 3D Registration failed","VersorRigid3DTransformOptimizer couldn't be found.")
			return self.convertITKtoVTK(movingImage, cast = "UC3")

		self.metric = itk.MeanSquaresImageToImageMetric.IF3IF3.New()
		self.interpolator = itk.LinearInterpolateImageFunction.IF3D.New()
		self.transform = itk.VersorRigid3DTransform.D.New()

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

		if initialParameters:
			self.transform.SetParameters(initialParameters)
		else:
			rotation = itk.Versor.D()
			translation = itk.Vector.D3()
			rotation.SetRotationAroundX(0)
			rotation.SetRotationAroundY(0)
			rotation.SetRotationAroundZ(0)
			#axis = itk.Vector.D3()
			#axis.SetElement(0,0)
			#axis.SetElement(1,0)
			#axis.SetElement(2,1)
			#rotation.Set(axis,0)
			self.transform.SetRotation(rotation)
			self.transform.SetTranslation(translation)
			
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
		Logging.info("Translation X = %f"%(finalParameters.GetElement(3)))
		Logging.info("Translation Y = %f"%(finalParameters.GetElement(4)))
		Logging.info("Translation Z = %f"%(finalParameters.GetElement(5)))
		Logging.info("Versor = (%f,%f,%f)"%(finalParameters.GetElement(0),finalParameters.GetElement(1),finalParameters.GetElement(2)))

		if usePrevious:
			for i in range(6):
				self.totalTransform.SetElement(i,self.totalTransform.GetElement(i) + finalParameters.GetElement(i))
				finalParameters = self.totalTransform

		self.resampler = itk.ResampleImageFilter.IF3IF3.New()
		self.transform.SetParameters(finalParameters)
		self.resampler.SetTransform(self.transform.GetPointer())
		self.resampler.SetInput(movingImage)
		region = movingImage.GetLargestPossibleRegion()
		self.resampler.SetSize(region.GetSize())
		self.resampler.SetOutputSpacing(movingImage.GetSpacing())
		self.resampler.SetOutputOrigin(movingImage.GetOrigin())
		self.resampler.SetDefaultPixelValue(backgroundValue)
		data = self.resampler.GetOutput()
		data.Update()

		data = self.convertITKtoVTK(data, cast = "UC3")
		return data
	
