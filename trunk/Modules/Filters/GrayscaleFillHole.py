#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: GrayscaleFillHole.py
 Project: BioImageXD
 Created: 07.12.2009, LP
 Description:

 A module that contains grayscale fill hole filter for the processing task.
 
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
import types
import lib.FilterTypes
import scripting
import itk

class GrayscaleFillHoleFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	GrayscaleFillHole removes local minima not connected to the boundary of the
	image
	"""
	name = "Grayscale fill hole"
	category = lib.FilterTypes.MORPHOLOGICAL
	level = scripting.COLOR_BEGINNER

	def __init__(self, inputs = (1,1)):
		"""
		Initialization
		"""
		lib.ProcessingFilter.ProcessingFilter.__init__(self, inputs)
		self.descs = {"2D": "Do for each 2D slice separately"}
		self.itkFlag = 1
		self.filter = None
		self.pc = itk.PyCommand.New()
		self.pc.SetCommandCallable(self.updateProgress)

	def updateProgress(self):
		"""
		Update progress event handler
		"""
		lib.ProcessingFilter.ProcessingFilter.updateProgress(self,self.filter,"ProgressEvent")

	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""
		return [["Parameters", ("2D",)],]

	def getDefaultValue(self, param):
		"""
		Return default value of parameter
		"""
		return False

	def getType(self, param):
		"""
		Return type of parameter
		"""
		return types.BooleanType

	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute the filter with given inputs and return the output
		"""
		if not lib.ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None

		image = self.getInput(1)
		image = self.convertVTKtoITK(image)

		if self.parameters["2D"]:
			type,dim = self.getITKImageType(image)
			self.filter = itk.SliceBySliceImageFilter[image,image].New()
			fillHoles = eval("itk.GrayscaleFillholeImageFilter.I%s2I%s2.New()"%(type,type))
			self.filter.SetFilter(fillHoles.GetPointer())
			self.filter.SetInput(image)
		else:
			self.filter = itk.GrayscaleFillholeImageFilter[image,image].New()
			self.filter.AddObserver(itk.ProgressEvent(),self.pc.GetPointer())
			self.filter.SetInput(image)

		output = self.filter.GetOutput()
		output.Update()

		return output
