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
import vtk
import GUI.GUIBuilder
import lib.FilterTypes
import scripting
import types

class CityBlockDistanceFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	A distance transform filter - Manhattan or city block distance from VTK
	"""		
	name = "City block distance"
	category = lib.FilterTypes.FEATUREDETECTION
	
	def __init__(self):
		"""
		Initialization
		"""		   
		lib.ProcessingFilter.ProcessingFilter.__init__(self, (1, 1))
		self.vtkfilter = vtk.vtkImageCityBlockDistance()
		self.vtkfilter.AddObserver("ProgressEvent", lib.messenger.send)
		lib.messenger.connect(self.vtkfilter, 'ProgressEvent', self.updateProgress)
		self.descs = {"CastToOriginal":"Cast output to same datatype as input"}
	
	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""			   
		return [  ["CityBlock distance", ("CastToOriginal",)]]
		
		
	def getType(self, parameter):
		"""
		Return the type of the parameter
		"""	   
		if parameter == "CastToOriginal":
			return types.BooleanType

	def getDefaultValue(self, parameter):
		"""
		Return the default value of a parameter
		"""		
		if parameter == "CastToOriginal":
			return True
		
	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute the filter with given inputs and return the output
		"""			   
		if not lib.ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None
		
		image = self.getInput(1)
		origType = image.GetScalarType()
		cast1 = vtk.vtkImageCast()
		cast1.SetInput(image)
		cast1.SetOutputScalarTypeToShort()
		# vtkImageCityBlockDistance requires short input
		self.vtkfilter.SetInput(cast1.GetOutput())
		
		data = self.vtkfilter.GetOutput()
		if self.parameters["CastToOriginal"]:
			cast = vtk.vtkImageCast()
			cast.SetInput(self.vtkfilter.GetOutput())
			cast.SetOutputScalarType(origType)
			cast.SetClampOverflow(1)
			data = cast.GetOutput()
		if update:
			self.vtkfilter.Update()
		return data  
