# -*- coding: iso-8859-1 -*-
"""
 Unit: GeodesicActiveContourLevelSet.py
 Project: BioImageXD
 Description:

 A module that contains dynamic threshold filter for the processing task.
 
 Copyright (C) 2005	 BioImageXD Project
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

import lib
import scripting
import types
import itk
import time
import GUI.GUIBuilder
import lib.Progress

class GeodesicActiveContourLevelSetFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	"""
	name = "Geodesic active contour level set"
	category = lib.FilterTypes.ACTIVECONTOUR
	level = scripting.COLOR_EXPERIENCED

	def __init__(self, inputs = (2,2)):
		"""
		"""
		lib.ProcessingFilter.ProcessingFilter.__init__(self,inputs)
		self.itkFlag = 1

		self.descs = {"PropagationScaling" : "Propagation scaling",
					  "CurvatureScaling" : "Curvature scaling",
					  "AdvectionScaling" : "Advection scaling",
					  "MaxRMSError" : "Max RMS error",
					  "Iterations" : "Max iterations",
					  "Seed": "Seed voxel",
					  "InitialDistance": "Initial distance to seed",
					  "Alpha": "Sigmoid alpha",
					  "Beta": "Sigmoid beta"}

		self.propagationScaling = 0.0
		self.curvatureScaling = 0.0
		self.advectionScaling = 0.0
		self.maxRMSError = 0.0
		self.iterations = 0

		self.filter = None
		self.smooth = None
		self.gradient = None
		self.sigmoid = None
		self.progressObj = lib.Progress.Progress()

	def getParameters(self):
		"""
		Returns the parameters for GUI
		"""
		return [["Seed", ("Seed", "InitialDistance")],
				["Scaling parameters", ("PropagationScaling","CurvatureScaling","AdvectionScaling")],
				["Speed and accuracy parameters",("MaxRMSError","Iterations")],
				["Settings",("Alpha","Beta")]]

	def getType(self, param):
		"""
		Returns the type of parameter
		@param param Parameter name
		"""
		if param in ["Iterations","InitialDistance"]:
			return types.IntType
		if param == "Seed":
			return GUI.GUIBuilder.PIXELS
		return types.FloatType

	def getDefaultValue(self, param):
		"""
		Returns the default value of parameter
		@param param Parameter name
		"""
		if param == "PropagationScaling":
			return -1.0
		if param == "CurvatureScaling":
			return 0.75
		if param == "AdvectionScaling":
			return 1.0
		if param == "MaxRMSError":
			return 0.05
		if param == "Iterations":
			return 300
		if param == "Seed":
			return []
		if param == "InitialDistance":
			return 100
		if param == "Alpha":
			return -0.5
		if param == "Beta":
			return 3.0

	def getParameterLevel(self, param):
		"""
		Returns the level of knowledge for using the parameter
		@param param Parameter name
		"""
		if param == "Iterations" or param == "MaxRMSError":
			return scripting.COLOR_INTERMEDIATE
		return scripting.COLOR_EXPERIENCED

	def updateProgress(self):
		"""
		Progress event handle
		"""
		i = self.filter.GetElapsedIterations()
		self.progressObj.setProgress(i / float(self.parameters["Iterations"]))
		lib.ProcessingFilter.ProcessingFilter.updateProgress(self, None, "ProgressEvent")

	def execute(self, inputs = (2,2), update = 0, last = 0):
		"""
		Execute filter using speed image and feature image
		@return Returns result active contour and result level set from which
		the active contour is extracted from
		"""
		if not lib.ProcessingFilter.ProcessingFilter.execute(self,inputs):
			return None

		self.progressObj.setProgress(0.0)
		lib.ProcessingFilter.ProcessingFilter.updateProgress(self, None, "ProgressEvent")
		initialModel = self.getInput(1)
		featureImage = self.getInput(2)

		initialModel = self.convertVTKtoITK(initialModel, cast = types.FloatType)
		featureImage = self.convertVTKtoITK(featureImage, cast = types.FloatType)
		dim = featureImage.GetLargestPossibleRegion().GetImageDimension()
		imagetype = eval("itk.Image.F%d"%dim)
		if "itkImageF" not in str(initialModel.__class__):
			initialModel = self.castITKImage(initialModel,imagetype)
		if "itkImageF" not in str(featureImage.__class__):
			featureImage = self.castITKImage(featureImage,imagetype)
		
		self.propagationScaling = self.parameters["PropagationScaling"]
		self.curvatureScaling = self.parameters["CurvatureScaling"]
		self.advectionScaling = self.parameters["AdvectionScaling"]
		self.maxRMSError = self.parameters["MaxRMSError"]
		self.iterations = self.parameters["Iterations"]
		
		self.smooth = itk.CurvatureAnisotropicDiffusionImageFilter[imagetype,imagetype].New()
		self.smooth.SetTimeStep(0.0625)
		self.smooth.SetNumberOfIterations(8)
		self.smooth.SetConductanceParameter(0.5)
		self.smooth.SetInput(featureImage)
		
		self.gradient = itk.GradientMagnitudeRecursiveGaussianImageFilter[imagetype,imagetype].New()
		self.gradient.SetSigma(1.0)
		self.gradient.SetInput(self.smooth.GetOutput())

		self.sigmoid = itk.SigmoidImageFilter[imagetype,imagetype].New()
		self.sigmoid.SetOutputMinimum(0.0)
		self.sigmoid.SetOutputMaximum(1.0)
		self.sigmoid.SetAlpha(self.parameters["Alpha"])
		self.sigmoid.SetBeta(self.parameters["Beta"])
		self.sigmoid.SetInput(self.gradient.GetOutput())

		cast = eval("itk.RescaleIntensityImageFilter.IF%dIUC%d.New()"%(dim,dim))
		cast.SetInput(self.sigmoid.GetOutput())
		cast.SetOutputMinimum(0)
		cast.SetOutputMaximum(255)

		seedPoints = self.parameters["Seed"]
		seeds = eval("itk.VectorContainer.UILSNF%d.New()"%dim)
		seeds.Initialize()
		initDist = self.parameters["InitialDistance"]
		seedValue = -initDist
		for i,seed in enumerate(seedPoints):
			seedPos = eval("itk.Index._%d()"%dim)
			seedPos[0] = seed[0]
			seedPos[1] = seed[1]
			if dim == 3:
				seedPos[2] = seed[2]
			node = eval("itk.LevelSetNode.F%d()"%dim)
			node.SetValue(seedValue)
			node.SetIndex(seedPos)
			seeds.InsertElement(i, node)

		fastMarch = itk.FastMarchingImageFilter[imagetype,imagetype].New()
		fastMarch.SetTrialPoints(seeds)
		fastMarch.SetSpeedConstant(1.0)
		fastMarch.SetOutputSize(initialModel.GetLargestPossibleRegion().GetSize())
		fastMarch.SetOutputSpacing(initialModel.GetSpacing())
		fastMarch.SetOutputOrigin(initialModel.GetOrigin())

		pc = itk.PyCommand.New()
		pc.SetCommandCallable(self.updateProgress)

		self.filter = eval("itk.GeodesicActiveContourLevelSetImageFilter.IF%dIF%dF.New()"%(dim,dim))
		self.filter.SetPropagationScaling(self.propagationScaling)
		self.filter.SetCurvatureScaling(self.curvatureScaling)
		self.filter.SetAdvectionScaling(self.advectionScaling)
		self.filter.SetMaximumRMSError(self.maxRMSError)

		self.filter.SetInput(fastMarch.GetOutput())
		self.filter.SetFeatureImage(self.sigmoid.GetOutput())
		self.filter.SetNumberOfIterations(self.iterations)
		self.filter.AddObserver(itk.ProgressEvent(),pc)
		
		start = time.clock()
		self.filter.Update()
		end = time.clock()
		duration = end - start
		print "Geodesic Active Contour Level Set filter took %.2f s"%(duration)
		print "Max. no. iterations: %d"%(self.filter.GetNumberOfIterations())
		print "Max. RMS error: %.3f"%(self.filter.GetMaximumRMSError())
		print "No. elapsed iterations: %d"%(self.filter.GetElapsedIterations())
		print "RMS change: %.3f"%(self.filter.GetRMSChange())

		self.zeroCrossing = itk.ZeroCrossingImageFilter[imagetype,imagetype].New()
		self.zeroCrossing.SetBackgroundValue(0)
		self.zeroCrossing.SetForegroundValue(255)
		self.zeroCrossing.SetInput(self.filter.GetOutput())
		data = self.zeroCrossing.GetOutput()
		data.Update()

		#self.dataUnit.getSettings().set("BitDepth", 32)
		self.dataUnit.getSettings().set("BitDepth", 8)
		data = self.castITKImage(data, eval("itk.Image.UC%d"%dim))
		
		self.progressObj.setProgress(1.0)
		lib.ProcessingFilter.ProcessingFilter.updateProgress(self, None, "ProgressEvent")
		
		return data
