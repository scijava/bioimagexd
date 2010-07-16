#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: LipidAnalysis.py
 Project: BioImageXD
 Description:

 A module that contains lipid analysis for the processing task.
 
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
import GUI.GUIBuilder as GUIBuilder
import vtkbxd
import itk

class LipidAnalysisFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	A lipid analysis filter
	"""
	name = "Lipid analysis"
	category = lib.FilterTypes.VOXELANALYSE
	level = scripting.COLOR_INTERMEDIATE

	def __init__(self, inputs = (2,2)):
		"""
		Initialization
		"""
		lib.ProcessingFilter.ProcessingFilter.__init__(self, inputs)
		self.itkFlag = 1
		self.descs = {"Seed": "Seed voxel",
					  "InternalDistance": "Initial distance to seed",
					  "InternalPropagation": "Propagation scaling",
					  "InternalCurvature": "Curvature scaling",
					  "InternalAdvection": "Advection scaling",
					  "InternalMaxRMSError": "Max RMS error",
					  "InternalIterations": "Max iterations",
					  "ExternalDistance": "Initial distance to seed",
					  "ExternalPropagation": "Propagation scaling",
					  "ExternalCurvature": "Curvature scaling",
					  "ExternalAdvection": "Advection scaling",
					  "ExternalMaxRMSError": "Max RMS error",
					  "ExternalIterations": "Max iterations"
					  }

	#def updateProgress(self):
	#	"""
	#	Update progress event handler
	#	"""
	#	lib.ProcessingFilter.ProcessingFilter.updateProgress(self,self.filter,"ProgressEvent")

	def getParameters(self):
		"""
		Returns the parameters for GUI.
		"""
		return [["Seed", ("Seed", )],
				["Internal contour", ("InternalDistance", "InternalPropagation", "InternalCurvature", "InternalAdvection", "InternalMaxRMSError", "InternalIterations")],
				["External contour", ("ExternalDistance", "ExternalPropagation", "ExternalCurvature", "ExternalAdvection", "ExternalMaxRMSError", "ExternalIterations")]]

	def getType(self, param):
		"""
		Returns the types of parameters for GUI.
		@param param Parameter name
		"""
		if param == "Seed":
			return GUIBuilder.PIXELS
		if param in ["InternalDistance", "InternalIterations", "ExternalDistance", "ExternalIterations"]:
			return types.IntType
		return types.FloatType

	def getDefaultValue(self, param):
		"""
		Returns the default value of the parameter
		@param param Parameter name
		"""
		if param == "Seed":
			return []
		if param in ["InternalCurvature", "ExternalCurvature"]:
			return 0.75
		if param in ["InternalAdvection", "ExternalAdvection"]:
			return 1.0
		if param in ["InternalIterations", "ExternalIterations"]:
			return 500
		if param in ["InternalMaxRMSError", "ExternalMaxRMSError"]:
			return 0.05
		if param == "InternalPropagation":
			return 1.5
		if param == "ExternalPropagation":
			return -1.5
		if param == "InternalDistance":
			return 100
		if param == "ExternalDistance":
			return 300

	def getParameterLevel(self, param):
		"""
		Returns the level of knowledge for using parameter
		@param param Parameter name
		"""
		return scripting.COLOR_BEGINNER

	def execute(self, inputs = (2,2), update = 0, last = 0):
		"""
		Execute filter in input image and return output image
		"""
		if not lib.ProcessingFilter.ProcessingFilter.execute(self,inputs):
			return None

		self.eventDesc = "Lipid analysis"
		inputChannel1 = self.getInput(1)
		inputChannel2 = self.getInput(2)
		combinedChannels = self.combineChannels(inputChannel1, inputChannel2)

		# Convert to ITK
		combinedITK = self.convertVTKtoITK(combinedChannels, cast = types.FloatType)
		combinedITK.DisconnectPipeline()
		region = combinedITK.GetLargestPossibleRegion()
		size = region.GetSize()
		index = region.GetIndex()
		#inputITK1 = self.convertVTKtoITK(inputChannel1, cast = types.FloatType)
		#inputITK1.DisconnectPipeline()
		#inputITK2 = self.convertVTKtoITK(inputChannel2, cast = types.FloatType)
		#inputITK2.DisconnectPipeline()
		#self.writeInterResult(combinedITK, "combined", combinedChannels.GetScalarRange())
		"""
		paste = itk.PasteImageFilter[combinedITK].New()
		padImage = itk.Image.F3.New()
		padIndex = itk.Index._3()
		padSize = itk.Size._3()
		padRegion = itk.ImageRegion._3()
		pasteIndex = itk.Index._3()
		for i in range(3):
			padIndex[i] = 0
			padSize[i] = size[i]
			pasteIndex[i] = 0
		
		padSize[2] = 5
		padRegion.SetSize(padSize)
		padRegion.SetIndex(padIndex)
		padImage.SetRegions(padRegion)
		padImage.SetSpacing(combinedITK.GetSpacing())
		padImage.SetOrigin(combinedITK.GetOrigin())
		padImage.Allocate()

		resImage = itk.Image.F3.New()
		resIndex = itk.Index._3()
		resIndex = itk.Index._3()
		resSize = itk.Size._3()
		resRegion = itk.ImageRegion._3()
		for i in range(3):
			resIndex[i] = 0
			resSize[i] = size[i]
		
		resSize[2] += 10
		resRegion.SetSize(resSize)
		resRegion.SetIndex(resIndex)
		resImage.SetRegions(resRegion)
		resImage.SetSpacing(combinedITK.GetSpacing())
		resImage.SetOrigin(combinedITK.GetOrigin())
		resImage.Allocate()
		
		paste.SetSourceImage(padImage)
		paste.SetDestinationImage(resImage)
		paste.SetDestinationIndex(pasteIndex)
		paste.SetSourceRegion(padImage.GetLargestPossibleRegion())
		paste.Update()
		paste.SetSourceImage(combinedITK)
		paste.SetDestinationImage(resImage)
		pasteIndex[2] += 5
		paste.SetDestinationIndex(pasteIndex)
		paste.Update()
		paste.SetSourceImage(padImage)
		paste.SetDestinationImage(resImage)
		pasteIndex[2] += size[2]
		paste.SetDestinationIndex(pasteIndex)
		paste.SetSourceRegion(padImage.GetLargestPossibleRegion())
		paste.Update()

		combinedITK = resImage
		"""
		print "Gradient anisotropic diffusion image filter ... "
		diffusion = itk.GradientAnisotropicDiffusionImageFilter.IF3IF3.New()
		diffusion.SetNumberOfIterations(5)
		diffusion.SetTimeStep(0.0625)
		diffusion.SetConductanceParameter(3.0)
		diffusion.SetInput(combinedITK)

		print "Gradient magnitude recursive Gaussian image filter ..."
		gradient = itk.GradientMagnitudeRecursiveGaussianImageFilter.IF3IF3.New()
		gradient.SetInput(diffusion.GetOutput())
		gradient.SetSigma(1.0)

		print "Sigmoid filter ..."
		sigmoid = itk.SigmoidImageFilter.IF3IF3.New()
		sigmoid.SetOutputMinimum(0.0)
		sigmoid.SetOutputMaximum(1.0)
		sigmoid.SetAlpha(-0.5)
		sigmoid.SetBeta(3.0)
		sigmoid.SetInput(gradient.GetOutput())

		size = combinedITK.GetLargestPossibleRegion().GetSize()
		seeds = self.parameters["Seed"]
		internalDistance = self.parameters["InternalDistance"]
		internalPropagation = self.parameters["InternalPropagation"]
		internalCurvature = self.parameters["InternalCurvature"]
		internalAdvection = self.parameters["InternalAdvection"]
		internalMaxRMSError = self.parameters["InternalMaxRMSError"]
		internalIterations = self.parameters["InternalIterations"]
		externalDistance = self.parameters["ExternalDistance"]
		externalPropagation = self.parameters["ExternalPropagation"]
		externalCurvature = self.parameters["ExternalCurvature"]
		externalAdvection = self.parameters["ExternalAdvection"]
		externalMaxRMSError = self.parameters["ExternalMaxRMSError"]
		externalIterations = self.parameters["ExternalIterations"]

		# Internal contour
		print "Internal contour..."
		internalInitialContour = self.createInitialContour(seeds[0], internalDistance, size)
		internalInitialContour.DisconnectPipeline()

		filter = itk.GeodesicActiveContourLevelSetImageFilter.IF3IF3F.New()
		filter.SetPropagationScaling(internalPropagation)
		filter.SetCurvatureScaling(internalCurvature)
		filter.SetAdvectionScaling(internalAdvection)
		filter.SetMaximumRMSError(internalMaxRMSError)
		filter.SetNumberOfIterations(internalIterations)
		filter.SetInitialImage(internalInitialContour)
		filter.SetFeatureImage(sigmoid.GetOutput())
		filter.Update()
		#zeroCrossing = itk.ZeroCrossingImageFilter.IF3IF3.New()
		#zeroCrossing.SetBackgroundValue(0)
		#zeroCrossing.SetForegroundValue(255)
		#zeroCrossing.SetInput(filter.GetOutput())
		#data = zeroCrossing.GetOutput()
		internalContour = filter.GetOutput()
		internalContour.DisconnectPipeline()

		# External contour
		print "External contour..."
		externalInitialContour = self.createInitialContour(seeds[0], externalDistance, size)
		externalInitialContour.DisconnectPipeline()
		
		filter.SetPropagationScaling(externalPropagation)
		filter.SetCurvatureScaling(externalCurvature)
		filter.SetAdvectionScaling(externalAdvection)
		filter.SetMaximumRMSError(externalMaxRMSError)
		filter.SetNumberOfIterations(externalIterations)
		filter.SetInitialImage(externalInitialContour)
		filter.Update()
		#zeroCrossing = itk.ZeroCrossingImageFilter.IF3IF3.New()
		#zeroCrossing.SetBackgroundValue(0)
		#zeroCrossing.SetForegroundValue(255)
		#zeroCrossing.SetInput(filter.GetOutput())
		#data = zeroCrossing.GetOutput()
		#data.Update()
		externalContour = filter.GetOutput()
		externalContour.DisconnectPipeline()

		# Threshold and cast results
		print "Thresholding results..."
		threshold = itk.BinaryThresholdImageFilter[internalContour,internalContour].New()
		cast = itk.CastImageFilter[internalContour, itk.Image.UC3].New()
		threshold.SetInput(internalContour)
		threshold.SetUpperThreshold(0.0)
		threshold.SetInsideValue(255)
		threshold.SetOutsideValue(0)
		cast.SetInput(threshold.GetOutput())
		thresInsideContour = cast.GetOutput()
		thresInsideContour.Update()
		thresInsideContour.DisconnectPipeline()

		threshold.SetInput(externalContour)
		thresOutsideContour = cast.GetOutput()
		thresOutsideContour.Update()
		thresOutsideContour.DisconnectPipeline()

		# Subtract contours from each other
		print "Subtract filtering..."
		subFilter = itk.SubtractImageFilter[thresOutsideContour, thresInsideContour, thresOutsideContour].New()
		subFilter.SetInput1(thresOutsideContour)
		subFilter.SetInput2(thresInsideContour)
		resultData = subFilter.GetOutput()
		resultData.Update()
		
		return resultData

	def combineChannels(self, vtkChannel1, vtkChannel2):
		"""
		"""
		print "Combining channels ..."
		vtkImageMathClamp = vtkbxd.vtkImageMathematicsClamp()
		vtkImageMathClamp.SetOperationToAdd()
		vtkImageMathClamp.SetInput1(vtkChannel1)
		vtkImageMathClamp.SetInput2(vtkChannel2)
		vtkImageMathClamp.SetClampOverflow(1)
		vtkImageMathClamp.Update()
		return vtkImageMathClamp.GetOutput()

	def createInitialContour(self, com, distance, size):
		"""
		"""
		seed = itk.VectorContainer.UILSNF3.New()
		seed.Initialize()
		seedValue = -distance
		seedPos = itk.Index._3()
		seedPos.SetElement(0, com[0])
		seedPos.SetElement(1, com[1])
		seedPos.SetElement(2, com[2])
		node = itk.LevelSetNode.F3()
		node.SetValue(seedValue)
		node.SetIndex(seedPos)
		seed.InsertElement(0, node)

		fastMarch = itk.FastMarchingImageFilter.IF3IF3.New()
		fastMarch.SetTrialPoints(seed)
		fastMarch.SetSpeedConstant(1.0)
		fastMarch.SetOutputSize(size)
		fastMarch.Update()

		return fastMarch.GetOutput()
	
	def writeInterResult(self, image, name, rangeVal):
		"""
		"""
		region = image.GetLargestPossibleRegion()
		size = region.GetSize()
		index = region.GetIndex()

		shift = -rangeVal[0]
		scale = 255 / (rangeVal[1] - rangeVal[0])

		shiftscale = itk.ShiftScaleImageFilter[image,image].New()
		shiftscale.SetShift(shift)
		shiftscale.SetScale(scale)
		shiftscale.SetInput(image)
		ucimage = itk.Image.UC3
		cast = itk.CastImageFilter[image,ucimage].New()
		cast.SetInput(shiftscale.GetOutput())
		writer = itk.ImageSeriesWriter.IUC3IUC2.New()
		nameGenerator = itk.NumericSeriesFileNames.New()
		nameGenerator.SetSeriesFormat("/media/hdd2/Downloads/LipidData/test/"+name+"%03d.tiff")
		nameGenerator.SetStartIndex(index[2])
		nameGenerator.SetEndIndex(index[2] + size[2] - 1)
		nameGenerator.SetIncrementIndex(1)
		writer.SetFileNames(nameGenerator.GetFileNames())
		writer.SetInput(cast.GetOutput())
		writer.Update()
		
