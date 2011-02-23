#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: BinaryThinning.py
 Project: BioImageXD
 Description:

 A module that contains thinning filter for the processing task. Uses different
 thinning algorithms for 2D and 3D data.
 
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

class BinaryThinningFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	A binary thinning filter. Uses different itk algorithms for 2D and 3D data
	"""
	name = "Binary thinning"
	category = lib.FilterTypes.MORPHOLOGICAL
	level = scripting.COLOR_BEGINNER

	def __init__(self, inputs = (1,1)):
		"""
		Initialization
		"""
		lib.ProcessingFilter.ProcessingFilter.__init__(self,(1,1))
		self.itkFlag = 1
		self.filter = None
		self.pc = itk.PyCommand.New()
		self.pc.SetCommandCallable(self.updateProgress)
		self.filterDesc = "Performs skeletonization for binary image\nInput: Binary image\nOutput: Binary image"

	def updateProgress(self):
		"""
		Update progress event handler
		"""
		lib.ProcessingFilter.ProcessingFilter.updateProgress(self,self.filter,"ProgressEvent")

	def execute(self, inputs = (1,1), update = 0, last = 0):
		"""
		Execute filter in input image and return output image
		"""
		if not lib.ProcessingFilter.ProcessingFilter.execute(self,inputs):
			return None

		self.eventDesc = "Binary thinning image"
		inputImage = self.getInput(1)
		inputImage = self.convertVTKtoITK(inputImage)

		largestRegion = inputImage.GetLargestPossibleRegion()
		dim = largestRegion.GetImageDimension()

		if dim == 3 and largestRegion.GetSize().GetElement(2) == 1:
			dim = 2
			extracted = 1
			
			itkType = self.getITKImageType(inputImage)[0]
			extractFilter = eval("itk.ExtractImageFilter.I%s3I%s2.New()"%(type,type))
			
			region = itk.ImageRegion._3()
			size = itk.Size._3()
			index = itk.Index._3()
			for i in range(2):
				size.SetElement(i, largestRegion.GetSize().GetElement(i))
				index.SetElement(i, largestRegion.GetIndex().GetElement(i))
			size.SetElement(2,0)
			index.SetElement(2,0)
			region.SetSize(size)
			region.SetIndex(index)
			
			extractFilter.SetExtractionRegion(region)
			extractFilter.SetInput(inputImage)
			input = extractFilter.GetOutput()
			input.Update()
		else:
			extracted = 0
			input = inputImage

		if dim == 2:
			self.filter = itk.BinaryThinningImageFilter[input,input].New()
		else:
			self.filter = itk.BinaryThinning3DImageFilter[input,input].New()
		
		self.filter.AddObserver(itk.ProgressEvent(),self.pc.GetPointer())
		self.filter.SetInput(input)

		outputImage = self.filter.GetOutput()
		outputImage.Update()

		return outputImage
