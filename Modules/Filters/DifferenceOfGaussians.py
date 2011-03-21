# -*- coding: iso-8859-1 -*-
"""
 Unit: DifferenceOfGaussians.py
 Project: BioImageXD
 Description:

 A module that contains DoG filter for the processing task.
 
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

import lib.ProcessingFilter
import scripting
import lib.FilterTypes
import types
import vtk
import vtkbxd

class DifferenceOfGaussiansFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	Difference of Gaussians filter
	"""
	name = "Difference of Gaussians"
	category = lib.FilterTypes.FEATUREDETECTION
	level = scripting.COLOR_BEGINNER

	def __init__(self, inputs = (1,1)):
		"""
		Initialization
		"""
		lib.ProcessingFilter.ProcessingFilter.__init__(self,(1,1))
		self.descs = {"StdDevX1": "X:", "StdDevY1": "Y", "StdDevZ1": "Z",
					  "StdDevX2": "X", "StdDevY2": "Y", "StdDevZ2": "Z"}
		self.filterDesc = "Computes Difference of Gaussians of input image\nInput: Grayscale image\n:Output: Grayscale image"

	def getParameters(self):
		"""
		Returns the parameters for GUI.
		"""
		return [["Standard deviation for thinner",("StdDevX1","StdDevY1","StdDevZ1")],
				["Standard deviation for wider",("StdDevX2","StdDevY2","StdDevZ2")]]

	def getType(self, param):
		"""
		Returns the types of parameters for GUI.
		@param param Parameter name
		"""
		return types.FloatType

	def getDefaultValue(self, param):
		"""
		Returns the default value of the parameter
		@param param Parameter name
		"""
		if param in ["StdDevX1","StdDevY1"]:
			return 1.0
		if param == "StdDevZ1":
			return 0.25
		if param in ["StdDevX2","StdDevY2"]:
			return 5.0
		if param == "StdDevZ2":
			return 1.25
		return 1.0

	def getParameterLevel(self,param):
		"""
		Returns the level of knowledge for using parameter.
		@param param Parameter name
		"""
		return scripting.COLOR_BEGINNER

	def execute(self, inputs = (1,1), update = 0, last = 0):
		"""
		Execute filter in input image and return output image.
		"""
		if not lib.ProcessingFilter.ProcessingFilter.execute(self,inputs):
			return None

		image = self.getInput(1)
		dim = image.GetDimensions()[2]
		if dim > 0:
			dim = 3
		else:
			dim = 2
		
		radius1 = int(round(2 * self.parameters["StdDevX1"])), int(round(2 * self.parameters["StdDevY1"])), int(round(2 * self.parameters["StdDevZ1"]))
		radius2 = int(round(2 * self.parameters["StdDevX2"])), int(round(2 * self.parameters["StdDevY2"])), int(round(2 * self.parameters["StdDevZ2"]))

		gaussian = vtk.vtkImageGaussianSmooth()
		gaussian.SetInput(image)
		gaussian.SetDimensionality(dim)

		gaussian.SetStandardDeviations(self.parameters["StdDevX1"],self.parameters["StdDevY1"],self.parameters["StdDevZ1"])
		gaussian.SetRadiusFactors(radius1)
		gaussian.Update()
		gaussian1 = vtk.vtkImageData()
		gaussian1.DeepCopy(gaussian.GetOutput())

		gaussian.SetStandardDeviations(self.parameters["StdDevX2"],self.parameters["StdDevY2"],self.parameters["StdDevZ2"])
		gaussian.SetRadiusFactors(radius2)
		gaussian.Update()
		gaussian2 = gaussian.GetOutput()

		imageMath = vtkbxd.vtkImageMathematicsClamp()
		imageMath.SetOperationToSubtract()
		imageMath.SetInput1(gaussian1)
		imageMath.SetInput2(gaussian2)
		imageMath.SetClampOverflow(True)
		data = imageMath.GetOutput()
		
		if update:
			data.Update()
		
		return data
