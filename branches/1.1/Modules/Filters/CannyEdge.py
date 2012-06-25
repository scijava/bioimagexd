#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: CannyEdge
 Project: BioImageXD
 Description:

 A module that contains Canny edge detection method
 
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

class CannyEdgeFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	A class that uses the ITK canny edge detection filter
	"""		
	name = "Canny edge detection"
	category = lib.FilterTypes.FEATUREDETECTION
	level = scripting.COLOR_EXPERIENCED
	
	def __init__(self, inputs = (1, 1)):
		"""
		Initialization
		"""
		lib.ProcessingFilter.ProcessingFilter.__init__(self, inputs)
		self.itkFlag = 1
		self.itkfilter = None
		self.eventDesc = "Performing edge detection (canny edge)"
		self.descs = {"LowerThreshold":"Lower threshold", "UpperThreshold":"Upper threshold","VarianceX":"X","VarianceY":"Y","VarianceZ":"Z",
		"MaxErrorX":"X", "MaxErrorY":"Y", "MaxErrorZ":"Z",
		"Rescale":"Rescale data to unsigned char (0-255)"}
		self.filterDesc = "Performs Canny edge detection method\nInput: Grayscale image\nOutput: Grayscale image"
		
	def getParameterLevel(self, parameter):
		"""
		Return the level of the given parameter
		"""
		if parameter == "Rescale":
			return scripting.COLOR_BEGINNER
		return scripting.COLOR_EXPERIENCED

	def getType(self, parameter):
		"""
		Returns the types of parameters for GUI.
		"""
		if parameter in [ "LowerThreshold", "UpperThreshold","VarianceX", "VarianceY","VarianceZ","MaxErrorX","MaxErrorY","MaxErrorZ"]:
			return types.FloatType
		if parameter == "Rescale":
			return types.BooleanType
		

	def getDefaultValue(self, parameter):
		"""
		Returns the default value for a parameter
		"""
		if parameter == "LowerThreshold":
			return 0.5
		if parameter == "UpperThreshold":
			return 2
		if parameter in ["VarianceX","VarianceY","VarianceZ"]:
			return 0
		if parameter == "Rescale": return True
		return 0.01
			
	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""			   
		return [["Threshold",("LowerThreshold","UpperThreshold")],["Output", ("Rescale",)],["Variance",("VarianceX","VarianceY","VarianceZ")],["Maximum Error",("MaxErrorX","MaxErrorY","MaxErrorZ")]]
	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute the filter with given inputs and return the output
		"""
		if not lib.ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None
		
		image = self.getInput(1)
		image = self.convertVTKtoITK(image, types.FloatType)
		if not self.itkfilter:
			self.itkfilter = itk.CannyEdgeDetectionImageFilter[image, image].New()

		self.itkfilter.SetInput(image)
		self.itkfilter.SetVariance((self.parameters["VarianceX"],self.parameters["VarianceY"],self.parameters["VarianceZ"]))
		self.itkfilter.SetMaximumError((self.parameters["MaxErrorX"],self.parameters["MaxErrorY"],self.parameters["MaxErrorZ"]))
		self.itkfilter.SetLowerThreshold(self.parameters["LowerThreshold"])
		self.itkfilter.SetUpperThreshold(self.parameters["UpperThreshold"])

		data = self.itkfilter.GetOutput()
		if self.parameters["Rescale"]:
			# Output data is 0.0 or 1.0, rescale this
			rescale = itk.RescaleIntensityImageFilter.IF3IUC3.New()
			rescale.SetOutputMinimum(0)
			rescale.SetOutputMaximum(255)
			rescale.SetInput(self.itkfilter.GetOutput())
			data = rescale.GetOutput()
		# Update filter everytime
		data.Update()
		
		return data
