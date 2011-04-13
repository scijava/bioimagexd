#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: MultiResolutionRegistration.py
 Project: BioImageXD
 Description:

 A module containing the translation registration filter in multi resolution.
							
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
import GUI.GUIBuilder

loader = Modules.DynamicLoader.getPluginLoader()
RegistrationFilters = loader.getPluginItem("Task","Process",2).RegistrationFilters

class MultiResolutionRegistrationFilter(RegistrationFilters.RegistrationFilter):
	"""
	MultiResolutionRegistrationFilter class
	"""
	name = "Multi resolution translation registration"
	category = lib.FilterTypes.REGISTRATION
	level = scripting.COLOR_EXPERIENCED

	def __init__(self, inputs = (1,1)):
		"""
		Initializes new object
		"""
		RegistrationFilters.RegistrationFilter.__init__(self,inputs)
		self.descs = {"FixedTimepoint": "Timepoint for fixed image", "BackgroundPixelValue": "Set background pixel value as", "UsePreviousAsFixed": "Use previous time point as fixed image", "X": "X direction", "Y": "Y direction", "Z": "Z direction",\
					"MaxStepLength0": "Maximum step length", "MinStepLength0": "Minimum step length", "MaxIterations0": "Maximum iterations", "LevelX0": "Level X", "LevelY0": "Level Y", "LevelZ0": "Level Z",\
					"MaxStepLength1": "Maximum step length", "MinStepLength1": "Minimum step length", "MaxIterations1": "Maximum iterations", "LevelX1": "Level X", "LevelY1": "Level Y", "LevelZ1": "Level Z",\
					"MaxStepLength2": "Maximum step length", "MinStepLength2": "Minimum step length", "MaxIterations2": "Maximum iterations", "LevelX2": "Level X", "LevelY2": "Level Y", "LevelZ2": "Level Z",\
					"MaxStepLength3": "Maximum step length", "MinStepLength3": "Minimum step length", "MaxIterations3": "Maximum iterations", "LevelX3": "Level X", "LevelY3": "Level Y", "LevelZ3": "Level Z"}
		self.totalTranslation = itk.Array.D()
		self.totalTranslation.SetSize(3)
		for i in range(3):
			self.totalTranslation.SetElement(i,0)
		self.filterDesc = "Performs multi resolution translation registration between images in time series data\nInput: Grayscale/Binary image\nOutput: Grayscale/Binary image"

	def updateProgress(self):
		"""
		Updates progress of registration
		"""
		currentParameter = self.transform.GetParameters()
		print "M: %f  T: %f %f %f" %(self.optimizer.GetValue(),currentParameter.GetElement(0),currentParameter.GetElement(1),currentParameter.GetElement(2))
		RegistrationFilters.RegistrationFilter.updateProgress(self)
	
	def updateParameters(self):
		"""
		Updates registration parameters during when resolution is changed
		"""
		level = self.registration.GetCurrentLevel()
		self.optimizer.SetMaximumStepLength(self.maxSteps[level])
		self.optimizer.SetMinimumStepLength(self.minSteps[level])
		self.optimizer.SetNumberOfIterations(self.maxIters[level])
		print "Changed optimizer settings, Max step length: %f, Min step length: %f, Max iterations: %d"%(self.maxSteps[level],self.minSteps[level],self.maxIters[level])

	def getParameterLevel(self, parameter):
		"""
		Return the level of the given parameter
		"""
		if parameter in ["FixedTimepoint","BackgroundPixelValue","UsePreviousAsFixed","X","Y","Z"]:
			return scripting.COLOR_BEGINNER
		return scripting.COLOR_EXPERIENCED
			
	def getDefaultValue(self, parameter):
		"""
		Return the default value of a parameter
		"""    
		if parameter == "FixedTimepoint":
			return 1
		if parameter == "MaxStepLength2":
			return 10.0
		if parameter == "MaxStepLength3":
			return 1.0
		if parameter == "MinStepLength2":
			return 0.1
		if parameter == "MinStepLength3":
			return 0.01
		if parameter == "MaxIterations2" or parameter == "MaxIterations3":
			return 30
		if parameter == "BackgroundPixelValue":
			return 0
		if parameter == "UsePreviousAsFixed":
			return False
		if parameter in ["X", "Y", "Z"]:
			return True
		if parameter in ["LevelX3", "LevelY3", "LevelZ3"]:
			return 1
		if parameter in ["LevelX2", "LevelY2", "LevelZ2"]:
			return 2
		
		return ""
	
	def getType(self, parameter):
		"""
		Return the type of the parameter
		"""
		if parameter == "FixedTimepoint" or parameter == "BackgroundPixelValue":
			return GUI.GUIBuilder.SLICE
		if "MaxStepLength" in parameter or "MinStepLength" in parameter:
			return types.FloatType
		if parameter == "UsePreviousAsFixed" or parameter == "X" or parameter == "Y" or parameter == "Z":
			return types.BooleanType
		
		return types.IntType
			 
	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""            
		return [["Fixed image", ("UsePreviousAsFixed","FixedTimepoint")],
			["", ("BackgroundPixelValue",)],
			["Use result to translate in", ("X","Y","Z")],
			["Level 3", ("LevelX3","LevelY3","LevelZ3","MaxIterations3","MaxStepLength3","MinStepLength3")],
			["Level 2", ("LevelX2","LevelY2","LevelZ2","MaxIterations2","MaxStepLength2","MinStepLength2")],
			["Level 1", ("LevelX1","LevelY1","LevelZ1","MaxIterations1","MaxStepLength1","MinStepLength1")],
			["Level 0", ("LevelX0","LevelY0","LevelZ0","MaxIterations0","MaxStepLength0","MinStepLength0")]]

	def execute(self, inputs, update = 0, last = 0):
		"""
		Initializes and executes the registration process. Does
		the result translation to input image and returns translated image.
		"""
		if not lib.ProcessingFilter.ProcessingFilter.execute(self,inputs):
			return None
		
		backgroundValue = self.parameters["BackgroundPixelValue"]
		usePrevious = self.parameters["UsePreviousAsFixed"]
		transX = self.parameters["X"]
		transY = self.parameters["Y"]
		transZ = self.parameters["Z"]
		
		self.minSteps = []
		self.maxSteps = []
		self.maxIters = []
		levelsX = []
		levelsY = []
		levelsZ = []
		for i in range(4):
			minStepLength = eval("self.parameters['MinStepLength%d']"%i)
			maxStepLength = eval("self.parameters['MaxStepLength%d']"%i)
			maxIterations = eval("self.parameters['MaxIterations%d']"%i)
			x = eval("self.parameters['LevelX%d']"%i)
			y = eval("self.parameters['LevelY%d']"%i)
			z = eval("self.parameters['LevelZ%d']"%i)
			if minStepLength and maxStepLength and maxIterations and x and y and z:
				self.minSteps.append(minStepLength)
				self.maxSteps.append(maxStepLength)
				self.maxIters.append(maxIterations)
				levelsX.append(x)
				levelsY.append(y)
				levelsZ.append(z)
		usedLevels = len(self.minSteps)

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
		if self.transform and not usePrevious and False:
			initialParameters = self.transform.GetParameters()
		else:
			initialParameters = None

		# Create registration framework's components
		fixedPyramid = itk.MultiResolutionPyramidImageFilter.IF3IF3.New()
		movingPyramid = itk.MultiResolutionPyramidImageFilter.IF3IF3.New()
		self.registration = itk.MultiResolutionImageRegistrationMethod.IF3IF3.New()
		self.metric = itk.MeanSquaresImageToImageMetric.IF3IF3.New()
		self.transform = itk.TranslationTransform.D3.New()
		self.interpolator = itk.LinearInterpolateImageFunction.IF3D.New()
		self.optimizer = itk.RegularStepGradientDescentOptimizer.New()

		# Initialize registration framework's components
		self.registration.SetOptimizer(self.optimizer)
		self.registration.SetTransform(self.transform)
		self.registration.SetInterpolator(self.interpolator)
		self.registration.SetMetric(self.metric)
		self.registration.SetFixedImagePyramid(fixedPyramid)
		self.registration.SetMovingImagePyramid(movingPyramid)
		self.registration.SetFixedImage(fixedImage)
		self.registration.SetMovingImage(movingImage)
		self.registration.SetFixedImageRegion(fixedImage.GetLargestPossibleRegion())
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

		# Set schedules
		fixedMatr = itk.vnl_matrix.UI(usedLevels,3)
		movingMatr = itk.vnl_matrix.UI(usedLevels,3)
		for i in range(usedLevels):
			fixedMatr.put(i,0,levelsX[i])
			fixedMatr.put(i,1,levelsY[i])
			fixedMatr.put(i,2,levelsZ[i])
			movingMatr.put(i,0,levelsX[i])
			movingMatr.put(i,1,levelsY[i])
			movingMatr.put(i,2,levelsZ[i])

		fixedArray = itk.Array2D.UI(fixedMatr)
		movingArray = itk.Array2D.UI(movingMatr)
		self.registration.SetSchedules(fixedArray,movingArray)

		# Use last transform parameters as initialization to this registration
		if initialParameters is None:
			self.transform.SetIdentity()
			initialParameters = self.transform.GetParameters()
		
		self.registration.SetInitialTransformParameters(tuple([initialParameters[i] for i in range(3)]))
		self.optimizer.SetMaximumStepLength(self.maxSteps[usedLevels-1])
		self.optimizer.SetMinimumStepLength(self.minSteps[usedLevels-1])
		self.optimizer.SetNumberOfIterations(self.maxIters[usedLevels-1])
		
		iterationCommand = itk.PyCommand.New()
		iterationCommand.SetCommandCallable(self.updateProgress)
		self.optimizer.AddObserver(itk.IterationEvent(),iterationCommand)
		levelCommand = itk.PyCommand.New()
		levelCommand.SetCommandCallable(self.updateParameters)
		self.registration.AddObserver(itk.IterationEvent(),levelCommand)

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

		if not self.parameters["X"]:
			finalParameters.SetElement(0,0.0)
		if not self.parameters["Y"]:
			finalParameters.SetElement(1,0.0)
		if not self.parameters["Z"]:
			finalParameters.SetElement(2,0.0)
		
		# del filters to free memory
		#del self.metric
		#del self.optimizer
		#del self.interpolator
		#del self.registration
		
		Logging.info("Use transform parameters")
		Logging.info("Translation X = %f"%(finalParameters.GetElement(0)))
		Logging.info("Translation Y = %f"%(finalParameters.GetElement(1)))
		Logging.info("Translation Z = %f"%(finalParameters.GetElement(2)))

		# Translate input image using results from the registration
		resampler = itk.ResampleImageFilter.IF3IF3.New()
		self.transform.SetParameters(finalParameters)
		resampler.SetTransform(self.transform)
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

