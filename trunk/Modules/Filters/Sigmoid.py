# -*- coding: iso-8859-1 -*-
"""
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
import itk
import lib.FilterTypes
import scripting
import types

class SigmoidFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
    A class for mapping an image data thru sigmoid image filter
	"""		
	name = "Sigmoid" 
	category = lib.FilterTypes.MISCFILTERING
	level = scripting.COLOR_EXPERIENCED
	
	def __init__(self, inputs = (1, 1)):
		"""
		Initialization
		"""		   
		lib.ProcessingFilter.ProcessingFilter.__init__(self, inputs)
		self.itkFlag = 1
		self.descs = {"Minimum": "Minimum output value", "Maximum": "Maximum output value", \
						"Alpha": "Alpha", "Beta": "Beta"}
		self.itkFilter = None
		self.filterDesc = "Computes sigmoid function pixel-wise\nInput: Grayscale image\nOutput: Grayscale image"
		
	def getParameterLevel(self, parameter):
		"""
		Return the level of the given parameter
		"""
		if parameter in ["Minimum", "Maximum"]:
			return scripting.COLOR_BEGINNER
		return scripting.COLOR_EXPERIENCED				   
		
	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""			   
		return [["Data range", ("Minimum", "Maximum")], ["", ("Alpha","Beta")]]

	def getDefaultValue(self, parameter):
		"""
		Return the default value of a parameter
		"""	   
		if parameter == "Minimum":
			return 0.0
		if parameter == "Maximum":
			return 1.0
		if parameter == "Alpha":
			return -0.5
		if parameter == "Beta":
			return 3
		return 0
		
	def getType(self, parameter):
		"""
		Return the type of the parameter
		"""	   
		return types.FloatType

	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute the filter with given inputs and return the output
		"""					   
		if not lib.ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None

		image = self.getInput(1)
		image = self.convertVTKtoITK(image, cast = types.FloatType)
		dim = image.GetLargestPossibleRegion().GetImageDimension()
		
		self.itkFilter = eval("itk.SigmoidImageFilter.IF%dIF%d.New()"%(dim,dim))
		self.itkFilter.SetOutputMinimum(self.parameters["Minimum"])
		self.itkFilter.SetOutputMaximum(self.parameters["Maximum"])
		self.itkFilter.SetAlpha(self.parameters["Alpha"])
		self.itkFilter.SetBeta(self.parameters["Beta"])

		try:
			self.itkFilter.SetInput(image)
		except:
			image = self.castITKImage(image,eval("itk.Image.F%d"%dim))
			self.itkFilter.SetInput(image)
		
		self.setImageType("F%d"%dim)
		data = self.itkFilter.GetOutput()
		if update:
			data.Update()

		return data
