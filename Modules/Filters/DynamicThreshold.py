#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: DynamicThreshold.py
 Project: BioImageXD
 Description:

 A module that contains dynamic threshold 3D filter for the processing task.
 
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
import types
import GUI.GUIBuilder
import itk
import lib.FilterTypes
MEAN = 0
MEDIAN = 1

class DynamicThresholdFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	A dynamic threshold filter. Uses itkBXD DynamicThreshold3DImageFilter.
	"""
	name = "Dynamic threshold"
	category = lib.FilterTypes.THRESHOLDING
	level = scripting.COLOR_BEGINNER

	def __init__(self, inputs = (1,1)):
		"""
		Initialization
		"""
		self.statisticsType = MEAN
		self.radius = (2,2,2)
		self.insideValue = 255
		self.outsideValue = 0
		
		lib.ProcessingFilter.ProcessingFilter.__init__(self,(1,1))
		self.itkFlag = 1
		self.descs = {"X": "X:", "Y": "Y:", "Z": "Z", "StatisticsType": "Statistics type:", "Threshold": "Threshold over statistics", "UseImageSpacing": "Use image spacing"}
		self.filter = None
		self.filterDesc = "Separates the image pixels/voxels into two classes, foreground and background, using locally calculated threshold\nInput: Grayscale image\nOutput: Binary image"

		self.pc = itk.PyCommand.New()
		self.pc.SetCommandCallable(self.updateProgress)
	

	def updateProgress(self):
		"""
		Update progress event handler
		"""
		lib.ProcessingFilter.ProcessingFilter.updateProgress(self,self.filter,"ProgressEvent")

	def getParameters(self):
		"""
		Returns the parameters for GUI.
		"""
		return [["",("StatisticsType",)],["Radius",("X","Y","Z")],["",("Threshold",)],["",("UseImageSpacing",)]]

	def getType(self, param):
		"""
		Returns the types of parameters for GUI.
		@param param Parameter name
		"""
		if param == "StatisticsType":
			return GUI.GUIBuilder.CHOICE
		if param == "UseImageSpacing":
			return types.BooleanType
		return types.IntType

	def getDefaultValue(self, param):
		"""
		Returns the default value of the parameter
		@param param Parameter name
		"""
		if param == "StatisticsType":
			return self.statisticsType
		elif param == "X":
			return self.radius[0]
		elif param == "Y":
			return self.radius[1]
		elif param == "Z":
			return self.radius[2]
		elif param == "Threshold":
			return 0
		elif param == "UseImageSpacing":
			return True

	def getParameterLevel(self, param):
		"""
		Returns the level of knowledge for using parameter
		@param param Parameter name
		"""
		return scripting.COLOR_BEGINNER

	def getRange(self, param):
		"""
		Returns range of list parameter
		@param param Parameter name
		"""
		if param == "StatisticsType":
			return ("Mean","Median")
		
	def execute(self, inputs = (1,1), update = 0, last = 0):
		"""
		Execute filter in input image and return output image
		"""
		if not lib.ProcessingFilter.ProcessingFilter.execute(self,inputs):
			return None

		self.eventDesc = "Dynamic thresholding image"
		inputImage = self.getInput(1)
		inputImage = self.convertVTKtoITK(inputImage)

		dynamicThresholdFilter = itk.DynamicThreshold3DImageFilter[inputImage,inputImage].New()
		self.filter = dynamicThresholdFilter

		dynamicThresholdFilter.AddObserver(itk.ProgressEvent(),self.pc)
		dynamicThresholdFilter.SetRadius(self.parameters["X"],self.parameters["Y"],self.parameters["Z"])
		dynamicThresholdFilter.SetThreshold(self.parameters["Threshold"])
		if self.parameters["StatisticsType"] == MEAN:
			dynamicThresholdFilter.SetStatisticsTypeMean()
		else:
			dynamicThresholdFilter.SetStatisticsTypeMedian()
		
		if self.parameters["UseImageSpacing"]:
			dynamicThresholdFilter.SetUseImageSpacingOn()
		else:
			dynamicThresholdFilter.SetUseImageSpacingOff()

		dynamicThresholdFilter.SetInput(inputImage)
		outputImage = dynamicThresholdFilter.GetOutput()
		if update:
			outputImage.Update()

		return outputImage
