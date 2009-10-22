#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: ImageCast.py
 Project: BioImageXD
 Created: 10.12.2007, LP
 Description:

 A module for casting the intensity of dataset
 
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
import vtkbxd

class ImageCastFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	A filter for casting the image to a different datatype
	"""		
	name = "Convert data type"
	category = lib.FilterTypes.CONVERSION
	
	def __init__(self):
		"""
		Initialization
		"""		   
		lib.ProcessingFilter.ProcessingFilter.__init__(self, (1, 1))
		self.vtkfilter = vtk.vtkImageCast()
		self.vtkfilter.AddObserver("ProgressEvent", lib.messenger.send)
		lib.messenger.connect(self.vtkfilter, 'ProgressEvent', self.updateProgress)
		self.eventDesc = "Casting the image to datatype"
		self.descs = {"ClampOverflow":"Clamp overflow","Float":"Float", "Double":"Double",
		"Int":"Int","UnsignedInt":"Unsigned int", "Long":"Long", "UnsignedLong":"Unsigned long",
		"Short":"Short","UnsignedShort":"Unsigned short","UnsignedChar":"Unsigned char","Char":"Char"}
	
	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""			   
		return [["", ("ClampOverflow",)],
		["Target datatype",(("Float","Double","Int","UnsignedInt","Long","UnsignedLong","Short","UnsignedShort","Char","UnsignedChar"),("cols",4))]]
		
		
	def getLongDesc(self, parameter):
		"""
		Return a long description of the parameter
		""" 
		return ""
		
	def getType(self, parameter):
		"""
		Return the type of the parameter
		"""	   
		if parameter in ["Float","Double","Int","UnsignedInt","Long","UnsignedLong","Short","UnsignedShort","Char","UnsignedChar"]:
			return GUI.GUIBuilder.RADIO_CHOICE
		elif parameter == "ClampOverflow":
			return types.BooleanType
		
	def getDefaultValue(self, parameter):
		"""
		Return the default value of a parameter
		"""		
		if parameter == "ClampOverflow":
			return True
		if parameter == "UnsignedChar":
			return 1
		return 0
		
	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute the filter with given inputs and return the output
		"""			   
		if not lib.ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None

		bitDepth = 8
		min = 0.0
		max = 255.0
		image = self.getInput(1)
		self.vtkfilter.SetInput(image)
		self.vtkfilter.SetClampOverflow(self.parameters["ClampOverflow"])
		output = self.vtkfilter.GetOutput()

		for param in ["Float","Double","Int","UnsignedInt","Long","UnsignedLong","Short","UnsignedShort","Char","UnsignedChar"]:
			if self.parameters[param]:
				eval("self.vtkfilter.SetOutputScalarTypeTo%s()"%param)
				output.Update()
				min,max = output.GetScalarRange()
				
				self.eventDesc = "Casting the image to datatype %s"%param
				if param in ["Short", "UnsignedShort"]:
					bitDepth = 16
				if param in ["Int", "UnsignedInt", "Float"]:
					bitDepth = 32
				if param in ["Double", "Long", "UnsignedLong"]:
					bitDepth = 64

		settings = self.dataUnit.getSettings()
		settings.set("BitDepth", bitDepth)
		ctf = settings.get("ColorTransferFunction")
		scaledCtf = vtk.vtkColorTransferFunction()
		handleCtf = vtkbxd.vtkHandleColorTransferFunction()
		handleCtf.ScaleColorTransferFunction(ctf,scaledCtf,min,max)
		settings.set("ColorTransferFunction",scaledCtf)

		if update:
			self.vtkfilter.Update()
		return self.vtkfilter.GetOutput()
		
