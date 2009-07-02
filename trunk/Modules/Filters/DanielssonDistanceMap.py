# -*- coding: iso-8859-1 -*-
"""
 Unit: DanielssonDistanceMap.py
 Project: BioImageXD
 Created: 10.09.2008, LP
 Description:

 A module that contains Danielsson distance map filter for the processing task.
 
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
import itk

class DanielssonDistanceMapFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	Danielsson distance map filter
	"""
	name = "Danielsson distance map"
	category = lib.FilterTypes.FEATUREDETECTION
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
		self.descs = {"Squared": "Squared distance", "ImageSpacing": "Use image spacing"}

	def updateProgress(self):
		"""
		Update progress event handler
		"""
		lib.ProcessingFilter.ProcessingFilter.updateProgress(self,self.filter,"ProgressEvent")

	def getParameters(self):
		"""
		Returns the parameters for GUI.
		"""
		return [["Options",("Squared","ImageSpacing")]]

	def getType(self, param):
		"""
		Returns the types of parameters for GUI.
		@param param Parameter name
		"""
		return types.BooleanType

	def getDefaultValue(self, param):
		"""
		Returns the default value of the parameter
		@param param Parameter name
		"""
		if param == "ImageSpacing":
			return True
		return False

	def getParameterLevel(self,param):
		"""
		Returns the level of knowledge for using parameter.
		@param param Parameter name
		"""
		return scripting.COLOR_INTERMEDIATE

	def execute(self, inputs = (1,1), update = 0, last = 0):
		"""
		Execute filter in input image and return output image.
		"""
		if not lib.ProcessingFilter.ProcessingFilter.execute(self,inputs):
			return None

		image = self.getInput(1)
		image = self.convertVTKtoITK(image)

		squared = self.parameters["Squared"]
		imageSpacing = self.parameters["ImageSpacing"]

		danielsson = itk.DanielssonDistanceMapImageFilter[image,image].New()
		self.filter = danielsson
		self.filter.AddObserver(itk.ProgressEvent(),self.pc.GetPointer())
		self.filter.SetInput(image)
		self.filter.SetSquaredDistance(squared)
		self.filter.SetUseImageSpacing(imageSpacing)

		outputImage = self.filter.GetOutput()
		outputImage.Update()

		return outputImage
