# -*- coding: iso-8859-1 -*-
"""
 Unit: CombineDiffIntensityRangeImages.py
 Project: BioImageXD
 Created: 19.8.2009, LP
 Description:

 A module that combines two datasets with adjacent intensity ranges. For
 instance first image which is under exposed to be in intensity range 0-100 and
 other image from the same data which is over exposed to be in intensity range
 30-255.
							
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

import lib
import lib.ProcessingFilter
import GUI
import vtk

MEAN = 0

class CombineDiffIntensityRangeImagesFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	A class for combining datasets into one
	"""
	name = "Combine diff. inten. range images"
	category = lib.FilterTypes.CONVERSION
	
	def __init__(self, inputs = (2, 2)):
		"""
		Initialization
		"""
		self.method = MEAN
		lib.ProcessingFilter.ProcessingFilter.__init__(self, inputs)
		self.descs = {"Method": "Method used in combination"}

	def getInputName(self, n):
		"""
		Return the name of the input #n
		"""
		if n == 1:
			return "First input"
		return "Second input"

	def getDefaultValue(self, parameter):
		"""
		Return the default value of a parameter
		"""
		return self.method
		
	def getType(self, parameter):
		"""
		Return the type of the parameter
		"""
		return GUI.GUIBuilder.CHOICE
	
	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""
		return [["", ("Method",)]]

	def getRange(self, param):
		"""
		Return the selection list
		"""
		if param == "Method":
			return ("Mean",)

	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute the filter with given inputs and return the output
		"""
		if not lib.ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None
			
		input1 = self.getInput(1)
		input1.UpdateInformation()
		input1.SetUpdateExtent(input1.GetWholeExtent())
		input1.Update()
		resultImage = input1
		
		input2 = self.getInput(2)
		input2.UpdateInformation()
		input2.SetUpdateExtent(input2.GetWholeExtent())
		input2.Update()

		if self.parameters["Method"] == MEAN:
			maxInput1 = input1.GetScalarTypeMax()
			minInput1 = input1.GetScalarTypeMin()
			maxInput2 = input2.GetScalarTypeMax()
			minInput2 = input2.GetScalarTypeMin()
			if maxInput1 > maxInput2:
				max = maxInput1
			else:
				max = maxInput2
			if minInput1 < minInput2:
				min = minInput1
			else:
				min = minInput2

			# Select result type to be a combination of original types
			scalarType1 = input1.GetScalarType()
			scalarType2 = input2.GetScalarType()
			unsigned = ""
			if scalarType1 == 11 or scalarType2 == 11: # If either is double
				type = "Double"
			elif scalarType1 == 10 or scalarType2 == 10: # If either is float
				type = "Float"
			else:
				unsigned = "Unsigned"
				type = ""
				if min < 0:
					unsigned = ""
				if max > 2**32-1:
					type = "Long"
				elif max > 2**16-1:
					type = "Int"
					if max > 2**31-1 and not unsigned:
						type = "Long"
				elif max > 2**8-1:
					type = "Short"
					if max > 2**15-1 and not unsigned:
						type = "Int"
				elif max > 2**7-1 and not unsigned:
					type = "Short"
				else:
					type = "Char"
				
			# Cast input images to float
			castFilter = vtk.vtkImageCast()
			castFilter.SetOutputScalarTypeToFloat()
			castFilter.SetInput(input1)
			input1 = castFilter.GetOutput()
			input1.Update()
			castFilter = vtk.vtkImageCast()
			castFilter.SetInput(input2)
			input2 = castFilter.GetOutput()
			input2.Update()

			# Calculate mean
			mathFilter = vtk.vtkImageMathematics()
			mathFilter.SetOperationToAdd()
			mathFilter.SetInput1(input1)
			mathFilter.SetInput2(input2)
			addOutput = mathFilter.GetOutput()

			# Divide by 2
			mathFilter = vtk.vtkImageMathematics()
			mathFilter.SetConstantK(0.5)
			mathFilter.SetOperationToMultiplyByK()
			mathFilter.SetInput1(addOutput)
			meanImage = mathFilter.GetOutput()

			# Cast to original data type
			castFilter = vtk.vtkImageCast()
			outputType = "castFilter.SetOutputScalarTypeTo%s%s()"%(unsigned, type)
			eval(outputType)
			castFilter.SetInput(meanImage)
			resultImage = castFilter.GetOutput()

		return resultImage
	
