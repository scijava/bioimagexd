#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: InverseFFT.py
 Project: BioImageXD
 Description:

 A module that contains inverse fast fourier transform for the processing task.
 
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
import lib.FilterTypes
import vtk
import types
import scripting

class InverseFFTFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	A inverse fourier transform filter.
	"""
	name = "Inverse FFT"
	category = lib.FilterTypes.FOURIER
	level = scripting.COLOR_EXPERIENCED

	def __init__(self, inputs = (1,1)):
		"""
		Initialization
		"""
		lib.ProcessingFilter.ProcessingFilter.__init__(self,(1,1))
		self.descs = {}
		self.filter = None
		self.filterDesc = "Transforms image from frequency domain to spatial domain\nInput: Complex image\nOutput: Grayscale image"

	def updateProgress(self):
		"""
		Update progress event handler
		"""
		lib.ProcessingFilter.ProcessingFilter.updateProgress(self,self.filter,"ProgressEvent")

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

		self.eventDesc = "Calculating inverse FFT"
		inputImage = self.getInput(1)

		self.filter = vtk.vtkImageRFFT()
		extract = vtk.vtkImageExtractComponents()
		extract.SetComponents(0)

		self.filter.SetInput(inputImage)
		extract.SetInputConnection(self.filter.GetOutputPort())
		outputImage = extract.GetOutput()
		
		if update:
			outputImage.Update()

		return outputImage
