#! /usr/bin/env python
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
__author__ = "BioImageXD Project <http://www.bioimagexd.org/>"
__version__ = "$Revision: 1.42 $"
__date__ = "$Date: 2005/01/13 14:52:39 $"

import lib.ProcessingFilter
import lib.FilterTypes
import scripting
import itk
import types
import Logging

class SobelEdgeDetectionFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	A class for edge detection using the sobel operator
	"""		
	name = "Sobel edge detection"
	category = lib.FilterTypes.FEATUREDETECTION
	level = scripting.COLOR_BEGINNER
	
	def __init__(self, inputs = (1, 1)):
		"""
		Initialization
		"""		   
		lib.ProcessingFilter.ProcessingFilter.__init__(self, inputs)
		self.eventDesc = "Performing edge detection (Sobel)"
		self.itkFlag = 1
		self.itkfilter = None
		self.filterDesc = "Performs Sobel edge detection method\nInput: Grayscale image\nOutput: Grayscale image"
		
	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""			   
		return []

	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute the filter with given inputs and return the output
		"""					   
		if not lib.ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None
			
		image = self.getInput(1)
		image = self.convertVTKtoITK(image, types.FloatType)
		if not self.itkfilter:
			self.itkfilter = itk.SobelEdgeDetectionImageFilter[image, image].New()

		self.itkfilter.SetInput(image)
		
		if update:
			self.itkfilter.Update()
		data = self.itkfilter.GetOutput()
		return data
