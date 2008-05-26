#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: CreatePolydata
 Project: BioImageXD
 Description:

 A module for the imagedata to polydata conversion filter
 
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
import lib.FilterTypes
import vtk
import Logging

import optimize

class CreatePolydataFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	A filter for converting imagedata to polydata
	"""
	name = "Convert to polygonal data"
	category = lib.FilterTypes.POLYDATA
	level = scripting.COLOR_INTERMEDIATE

	def __init__(self, inputs = (1,1)):
		"""
		Initialization
		"""
		self.scalarRange = 0,255
		lib.ProcessingFilter.ProcessingFilter.__init__(self,(1,1))
		self.contour = vtk.vtkMarchingCubes()
		self.decimate = vtk.vtkDecimatePro()
		self.descs = {"Simplify": "Simplify surface", "IsoValue":"Iso-surface value", 
		"PreserveTopology":"PreserveTopology"}
	
	def getParameters(self):
		"""
		Returns the parameters for GUI.
		"""
		return [
				["Smoothing",("Simplify","PreserveTopology")],["Surface generation",("IsoValue",)]
		]

	def getType(self, param):
		"""
		Returns the types of parameters for GUI.
		"""
		if param in ["Simplify", "IsoValue"]:
			return GUI.GUIBuilder.SLICE
		if param in ["PreserveTopology"]:
			return types.BooleanType
		if paramet in ["PolyDataFile"]:
			return GUI.GUIBuilder.FILENAME
		
		return types.IntType

	def getDefaultValue(self, param):
		"""
		Description:
		"""
		if param == "IsoValue":return 255
		if param == "Simplify": return 65
		if param == "PreserveTopology": return True
		if param == "PolyDataFile": return "surface.pol"
		return 0

	def getParameterLevel(self, param):
		"""
		Description:
		"""
		return scripting.COLOR_BEGINNER

	def getRange(self, param):
		"""
		Description:
		"""
		if param == "Simplify": return (0,100)
		if param == "IsoValue": return self.scalarRange

		return (0,999)
		
	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute filter in input image and return output image
		"""
		if not lib.ProcessingFilter.ProcessingFilter.execute(self,inputs):
			return None

		self.eventDesc = "Converting image data to polygonal data"
		inputImage = self.getInput(1)
		inputImage.Update()
		self.scalarRange = inputImage.GetScalarRange()
		lib.messenger.send(self, "update_IsoValue")
		
		x, y, z = self.dataUnit.getDimensions()
		input = optimize.optimize(image = inputImage, updateExtent = (0, x - 1, 0, y - 1, 0, z - 1))
		self.contour.SetInput(input)
		
		self.contour.SetValue(0, self.parameters["IsoValue"])

		polyOutput = self.contour.GetOutput()

		#TODO: should decimateLevel and preserveTopology be instance variables?
		decimateLevel = self.parameters["Simplify"] 
		preserveTopology = self.parameters["PreserveTopology"] 
		if decimateLevel != 0:            
			self.decimate.SetPreserveTopology(preserveTopology)
			if not preserveTopology:
				self.decimate.SplittingOn()
				self.decimate.BoundaryVertexDeletionOn()
			else:
				self.decimate.SplittingOff()
				self.decimate.BoundaryVertexDeletionOff()
			self.decimate.SetTargetReduction(decimateLevel / 100.0)
			
			Logging.info("Decimating %.2f%%, preserve topology: %s" \
						% (decimateLevel, preserveTopology), kw = "visualizer")
			self.decimate.SetInput(polyOutput)
			polyOutput = self.decimate.GetOutput()
		
		polyOutput.Update()
		self.setPolyDataOutput(polyOutput)
		return inputImage
