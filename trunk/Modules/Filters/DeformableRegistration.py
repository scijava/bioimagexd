#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: DeformableRegistration.py
 Project: BioImageXD
 Description:

 A module containing the deformable registration filter for the processing
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
import lib.FilterTypes
import lib.ProcessingFilter
import types
import time
import vtk
import itk
import Logging
import math

loader = Modules.DynamicLoader.getPluginLoader()
RegistrationFilters = loader.getPluginItem("Task","Process",2).RegistrationFilters

class DeformableRegistrationFilter(RegistrationFilters.RegistrationFilter):
	"""
	DeformableRegistrationFilter class
	"""
	name = "Deformable Registration"
	category = lib.FilterTypes.REGISTRATION
	level = scripting.COLOR_EXPERIENCED

	def __init__(self, inputs = (1,1)):
		"""
		Initializes Rigid 2D Registration object
		"""
		RegistrationFilters.RegistrationFilter.__init__(self,inputs)
		del self.descs["UsePreviousAsFixed"]
		self.descs["UseCaching"] = "Use caching of BSpline weights"
		self.descs["GridSizeX"] = "X:"
		self.descs["GridSizeY"] = "Y:"
		self.descs["GridSizeZ"] = "Z:"

	def updateProgress(self):
		"""
		Updates progress of the registration process.
		"""
		RegistrationFilters.RegistrationFilter.updateProgress(self)

	def getParameterLevel(self, parameter):
		"""
		Return the level of the given parameter
		"""
		if parameter in ["UseCaching", "GridSizeX", "GridSizeY", "GridSizeZ"]:
			return scripting.COLOR_INTERMEDIATE
		return RegistrationFilters.RegistrationFilter.getParameterLevel(self,parameter)

	def getDefaultValue(self, parameter):
		"""
		Return the default value of a parameter
		"""
		if parameter in ["GridSizeX", "GridSizeY"]:
			return 5
		if parameter in ["GridSizeZ"]:
			return 5
		if parameter == "MinimumStepLength":
			return 0.02
		if parameter == "MaximumStepLength":
			return 5.0
		return RegistrationFilters.RegistrationFilter.getDefaultValue(self,parameter)

	def getType(self,parameter):
		"""
		Return the type of the parameter
		"""
		if parameter == "UseCaching":
			return types.BooleanType
		if parameter in ["GridSizeX", "GridSizeY", "GridSizeZ"]:
			return types.IntType
		return RegistrationFilters.RegistrationFilter.getType(self,parameter)

	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""
		return [["Fixed image", ("FixedTimepoint",)], ["Background intensity", ("BackgroundPixelValue",)], ["Caching", ("UseCaching",)], ["Grid size", ("GridSizeX","GridSizeY","GridSizeZ")], ["Accuracy and speed settings", ("MaxIterations","MaxStepLength","MinStepLength")]]

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
		caching = self.parameters["UseCaching"]
		gridSizeX = self.parameters["GridSizeX"]
		gridSizeY = self.parameters["GridSizeY"]
		gridSizeZ = self.parameters["GridSizeZ"]
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

		fixedRegion = fixedImage.GetLargestPossibleRegion()
		fixedSize = fixedRegion.GetSize()
		dim = fixedRegion.GetImageDimension()
		if dim == 3 and fixedSize.GetElement(2) < 2:
			dim = 2
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
			extractFilter2.SetExtractionRegion(extractRegion)
			extractFilter2.SetInput(movingImage)
			movingImage = extractFilter2.GetOutput()
			movingImage.Update()			

		# Create registration framework's components
		self.registration = eval("itk.ImageRegistrationMethod.IF%dIF%d.New()"%(dim,dim))
		self.optimizer = itk.RegularStepGradientDescentOptimizer.New()
		#self.optimizer = itk.LBFGSBOptimizer.New()
		self.metric = eval("itk.MeanSquaresImageToImageMetric.IF%dIF%d.New()"%(dim,dim))
		self.interpolator = eval("itk.LinearInterpolateImageFunction.IF%dD.New()"%dim)
		self.transform = eval("itk.BSplineDeformableTransform.D%d%d.New()"%(dim,dim))

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
		self.metric.SetUseCachingOfBSplineWeights(caching)

		# Initialize transform
		gridRegion = eval("itk.ImageRegion._%d()"%dim)
		gridSizeOnImage = eval("itk.Size._%d()"%dim)
		gridBorderSize = eval("itk.Size._%d()"%dim)
		totalGridSize = eval("itk.Size._%d()"%dim)

		gridSizeOnImage.SetElement(0,gridSizeX)
		gridSizeOnImage.SetElement(1,gridSizeY)
		if dim == 3:
			gridSizeOnImage.SetElement(2,gridSizeZ)
		gridBorderSize.Fill(3)
		
		for i in range(dim):
			totalGridSize.SetElement(i,gridSizeOnImage.GetElement(i) + gridBorderSize.GetElement(i))
		gridRegion.SetSize(totalGridSize)

		gridSpacing = fixedImage.GetSpacing()
		gridOrigin = fixedImage.GetOrigin()
		fixedSize = fixedRegion.GetSize()

		for i in range(dim):
			spacingElement = gridSpacing.GetElement(i)
			spacingElement *= int(math.floor(float(fixedSize.GetElement(i)-1) / float(gridSizeOnImage.GetElement(i)-1)))
			originElement = gridOrigin.GetElement(i)
			originElement -= spacingElement
			gridSpacing.SetElement(i,spacingElement)
			gridOrigin.SetElement(i,originElement)

		self.transform.SetGridSpacing(gridSpacing)
		self.transform.SetGridOrigin(gridOrigin)
		self.transform.SetGridRegion(gridRegion)
		self.transform.SetGridDirection(fixedImage.GetDirection())
		numOfParameters = self.transform.GetNumberOfParameters()
		parameters = itk.Array.D(numOfParameters)
		parameters.Fill(0.0)
		self.transform.SetParameters(parameters)
		self.registration.SetInitialTransformParameters(self.transform.GetParameters())

		#boundSelect = itk.Array.SL(numOfParameters)
		#upperBound = itk.Array.D(numOfParameters)
		#lowerBound = itk.Array.D(numOfParameters)
		#boundSelect.Fill(0)
		#upperBound.Fill(0.0)
		#lowerBound.Fill(0.0)
		#self.optimizer.SetBoundSelection(boundSelect)
		#self.optimizer.SetUpperBound(upperBound)
		#self.optimizer.SetLowerBound(lowerBound)
		#self.optimizer.SetCostFunctionConvergenceFactor(10**12)
		#self.optimizer.SetProjectedGradientTolerance(1.0)
		#self.optimizer.SetMaximumNumberOfIterations(500)
		#self.optimizer.SetMaximumNumberOfEvaluations(500)
		#self.optimizer.SetMaximumNumberOfCorrections(5)		

		iterationCommand = itk.PyCommand.New()
		iterationCommand.SetCommandCallable(self.updateProgress)
		self.optimizer.AddObserver(itk.IterationEvent(),iterationCommand.GetPointer())

		Logging.info("Starting registration")
		startTime = time.time()
		self.registration.StartRegistration()
		finalParameters = self.registration.GetLastTransformParameters()
		self.transform.SetParameters(finalParameters)
		Logging.info("Registration took %s seconds"%(time.time() - startTime))

		self.resampler = eval("itk.ResampleImageFilter.IF%dIF%d.New()"%(dim,dim))
		resampleInterpolator = eval("itk.NearestNeighborInterpolateImageFunction.IF%dD.New()"%dim)
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
	
