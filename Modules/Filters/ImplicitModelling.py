#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: ImplicitModelling
 Project: BioImageXD
 Description:

 A module for the implicit modelling of a polydata object
 
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
import lib.ImageOperations
import os
import wx
import vtk

class ImplicitModellingFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	A filter for analyzing polydata
	"""
	name = "Implicit modelling"
	category = lib.FilterTypes.POLYDATA
	level = scripting.COLOR_INTERMEDIATE

	def __init__(self):
		"""
		Initialization
		"""
		self.defaultObjectsFile = u"statistics.csv"
		self.objectsBox = None
		self.timepointData = {}
		self.polyDataSource = None
		self.segmentedSource = None
		self.delayedData = None
		self.vtkfilter = vtk.vtkImplicitModeller()
		self.vtkfilter.SetProcessModeToPerVoxel()
		self.vtkfilter.SetNumberOfThreads(2)
		lib.ProcessingFilter.ProcessingFilter.__init__(self,(1,1))
		for i in range(1, 2):
			self.setInputChannel(i, i)
		self.descs = {"MaximumDistance":"Max. distance","Capping":"Mark outer boundary","CapValue":"Boundary value", "ScaleToMax":"Scale output values to max."}
			
	def getParameters(self):
		"""
		Returns the parameters for GUI.
		"""
		return [
			["Implicit modelling",("MaximumDistance","Capping","CapValue","ScaleToMax")],
			
			]

	def getType(self, parameter):
		"""
		Returns the types of parameters for GUI.
		"""

		if parameter in ["Capping", "ScaleToMax"]:
			return types.BooleanType
		return types.FloatType
			
	def getDefaultValue(self, parameter):
		"""
		Description:
		"""
		if parameter == "Capping": return True
		if parameter == "MaximumDistance": return 0.1
		if parameter == "CapValue": return 255
		if parameter == "ScaleToMax": return True
	def getParameterLevel(self, param):
		"""
		Description:
		"""
		return scripting.COLOR_BEGINNER
		

	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute filter in input image and return output image
		"""
		if not lib.ProcessingFilter.ProcessingFilter.execute(self,inputs):
			return None

		inputImage = self.getPolyDataInput(1)
		self.vtkfilter.RemoveAllInputs()
		self.vtkfilter.SetInput(inputImage)
		dataUnit = self.getInputDataUnit(1)
#		scripting.wantWholeDataset = True
		dims = dataUnit.getDimensions()
		self.vtkfilter.SetSampleDimensions(dims)
		self.vtkfilter.SetCapping(self.parameters["Capping"])
		self.vtkfilter.SetOutputScalarTypeToUnsignedChar()
		self.vtkfilter.SetMaximumDistance(self.parameters["MaximumDistance"])
		self.vtkfilter.SetScaleToMaximumDistance(self.parameters["ScaleToMax"])
		self.vtkfilter.SetCapValue(self.parameters["CapValue"])
		self.vtkfilter.SetModelBounds(-5,5,-5,5,-5,5)
		self.vtkfilter.Update()
			
		print self.vtkfilter
		x0, x1 = self.vtkfilter.GetOutput().GetScalarRange()
		print self.vtkfilter.GetOutput()
		print "scalar range=",x0,x1
#		print "Setting palette to",x0,x1
#		ctf = lib.ImageOperations.fire(x0,x1)
#		self.dataUnit.getSettings().set("ColorTransferFunction", ctf)
		return self.vtkfilter.GetOutput()
