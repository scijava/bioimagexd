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

class EuclideanDistanceFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	A distance transform filter
	"""		
	name = "Euclidean distance"
	category = lib.FilterTypes.FEATUREDETECTION
	
	def __init__(self):
		"""
		Initialization
		"""		   
		lib.ProcessingFilter.ProcessingFilter.__init__(self, (1, 1))
		self.vtkfilter = vtk.vtkImageEuclideanDistance()
		self.vtkfilter.AddObserver("ProgressEvent", lib.messenger.send)
		lib.messenger.connect(self.vtkfilter, 'ProgressEvent', self.updateProgress)
		self.descs = {"Algorithm":"Calculation algorithm","ConsiderAnisotropy":"Consider anisotropy","CastToUnsignedChar":"Cast to unsigned char"}
	
	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""			   
		return [  ["Euclidean distance", ("Algorithm","ConsiderAnisotropy","CastToUnsignedChar")]]
		
		
	def getType(self, parameter):
		"""
		Return the type of the parameter
		"""	   
		if parameter == "Algorithm":
			return GUI.GUIBuilder.CHOICE
		return types.BooleanType
		
	def getRange(self, parameter):
		"""
		Return the range of values available for parameter
		"""
		if parameter == "Algorithm":
			return ["Saito with caching for 2^n square images", "Saito"]

	def getDefaultValue(self, parameter):
		"""
		Return the default value of a parameter
		"""		
		if parameter == "Algorithm":
			return 0
		return True
		
	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute the filter with given inputs and return the output
		"""			   
		if not lib.ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None
		
		image = self.getInput(1)
		self.vtkfilter.SetInput(image)
		
		self.vtkfilter.SetConsiderAnisotropy(self.parameters["ConsiderAnisotropy"])
		self.vtkfilter.SetAlgorithm(self.parameters["Algorithm"])
		data = self.vtkfilter.GetOutput()
		if self.parameters["CastToUnsignedChar"]:
			cast = vtk.vtkImageCast()
			cast.SetInput(self.vtkfilter.GetOutput())
			cast.SetOutputScalarTypeToUnsignedChar()
			cast.SetClampOverflow(1)
			data = cast.GetOutput()
		if update:
			self.vtkfilter.Update()
		return data  
