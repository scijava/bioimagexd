#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: FilterObjects.py
 Project: BioImageXD
 Created: 10.12.2009, LP
 Description:

 A module that is used to filter objects from labeled image using different
 parameters.
 
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
import itk
import lib.FilterTypes

class FilterObjectsFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	Label image filtering filter
	"""
	name = "Filter objects"
	category = lib.FilterTypes.OBJECT
	level = scripting.COLOR_BEGINNER

	def __init__(self, inputs = (1,1)):
		"""
		Initialization
		"""
		lib.ProcessingFilter.ProcessingFilter.__init__(self,(1,1))
		self.itkFlag = 1
		self.labelMap = None
		self.descs = {"FilterSize": "Filter by size",
					  "MinSize": "Minimum size in voxels",
					  "MaxSize": "Maximum size in voxels",
					  "FilterBorder": "Filter objects touching border",
					  "FilterRoundness": "Filter by roundness",
					  "MinRoundness": "Minimum roundness",
					  "MaxRoundness": "Maximum roundness"}

	def getParameters(self):
		"""
		Returns the parameters for GUI.
		"""
		return [["Filter by size", ("FilterSize", "MinSize", "MaxSize")],
				["Filter objects touching border", ("FilterBorder",)],
				["Filter by roundness", ("FilterRoundness", "MinRoundness", "MaxRoundness")]]

	def getType(self, param):
		"""
		Returns the types of parameters for GUI.
		@param param Parameter name
		"""
		if param in ["FilterSize","FilterBorder","FilterRoundness"]:
			return types.BooleanType
		if param in ["MinRoundness","MaxRoundness"]:
			return types.FloatType
		
		return types.IntType

	def getDefaultValue(self, param):
		"""
		Returns the default value of the parameter
		@param param Parameter name
		"""
		if param == "MinSize":
			return 0
		if param == "MaxSize":
			return 1000000
		if param == "FilterSize":
			return True
		if param == "FilterBorder":
			return False
		if param == "FilterRoundness":
			return False
		if param == "MinRoundness":
			return 0.0
		if param == "MaxRoundness":
			return 1.0

	def getParameterLevel(self, param):
		"""
		Returns the level of knowledge for using parameter
		@param param Parameter name
		"""
		return scripting.COLOR_BEGINNER

	def execute(self, inputs = (1,1), update = 0, last = 0):
		"""
		Execute filter in input image and return output image
		"""
		if not lib.ProcessingFilter.ProcessingFilter.execute(self,inputs):
			return None

		self.eventDesc = "Filtering objects"
		inputImage = self.getInput(1)
		inputImage = self.convertVTKtoITK(inputImage)
		region = inputImage.GetLargestPossibleRegion()
		dim = region.GetImageDimension()

		shapeFilter = eval("itk.LabelImageToShapeLabelMapFilter.IUL%dLM%d.New()"%(dim,dim))
		if self.parameters["FilterRoundness"]:
			shapeFilter.ComputePerimeterOn()
		shapeFilter.SetInput(inputImage)
		self.labelMap = shapeFilter.GetOutput()
		self.labelMap.Update()

		if self.parameters["FilterSize"]:
			minSize = self.parameters["MinSize"]
			maxSize = self.parameters["MaxSize"]
			shapeOpeningMinSize = eval("itk.ShapeOpeningLabelMapFilter.LM%d.New()"%dim)
			shapeOpeningMinSize.InPlaceOn()
			shapeOpeningMinSize.SetAttribute('Size')
			shapeOpeningMinSize.SetInput(self.labelMap)
			shapeOpeningMinSize.SetLambda(minSize)
			shapeOpeningMinSize.Update()

			shapeOpeningMaxSize = eval("itk.ShapeOpeningLabelMapFilter.LM%d.New()"%dim)
			shapeOpeningMaxSize.InPlaceOn()
			shapeOpeningMaxSize.SetAttribute('Size')
			shapeOpeningMaxSize.SetInput(shapeOpeningMinSize.GetOutput())
			shapeOpeningMaxSize.SetReverseOrdering(True)
			shapeOpeningMaxSize.SetLambda(maxSize)
			shapeOpeningMaxSize.Update()
			self.labelMap = shapeOpeningMaxSize.GetOutput()

		if self.parameters["FilterBorder"]:
			shapeOpeningBorder = eval("itk.ShapeOpeningLabelMapFilter.LM%d.New()"%dim)
			shapeOpeningBorder.InPlaceOn()
			shapeOpeningBorder.SetAttribute('SizeOnBorder')
			shapeOpeningBorder.SetInput(self.labelMap)
			shapeOpeningBorder.SetReverseOrdering(True)
			shapeOpeningBorder.SetLambda(1)
			shapeOpeningBorder.Update()
			self.labelMap = shapeOpeningBorder.GetOutput()

		if self.parameters["FilterRoundness"]:
			shapeOpeningMinRoundness = eval("itk.ShapeOpeningLabelMapFilter.LM%d.New()"%dim)
			shapeOpeningMinRoundness.InPlaceOn()
			shapeOpeningMinRoundness.SetAttribute('Roundness')
			shapeOpeningMinRoundness.SetInput(self.labelMap)
			shapeOpeningMinRoundness.SetLambda(self.parameters["MinRoundness"])
			shapeOpeningMinRoundness.Update()
			self.labelMap = shapeOpeningMinRoundness.GetOutput()

			shapeOpeningMaxRoundness = eval("itk.ShapeOpeningLabelMapFilter.LM%d.New()"%dim)
			shapeOpeningMaxRoundness.InPlaceOn()
			shapeOpeningMaxRoundness.SetAttribute('Roundness')
			shapeOpeningMaxRoundness.SetInput(self.labelMap)
			shapeOpeningMaxRoundness.SetReverseOrdering(True)
			shapeOpeningMaxRoundness.SetLambda(self.parameters["MaxRoundness"])
			shapeOpeningMaxRoundness.Update()
			self.labelMap = shapeOpeningMaxRoundness.GetOutput()

		relabelSize = eval("itk.ShapeRelabelLabelMapFilter.LM%d.New()"%dim)
		relabelSize.SetInput(self.labelMap)
		relabelSize.SetAttribute('Size')
		relabelSize.Update()
		self.labelMap = relabelSize.GetOutput()

		shapeToImage = eval("itk.LabelMapToLabelImageFilter.LM%dIUL%d.New()"%(dim,dim))
		shapeToImage.SetInput(self.labelMap)
		outputImage = shapeToImage.GetOutput()
		outputImage.Update()
		return outputImage
