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
import lib.ImageOperations
import scripting
import vtk
import GUI.GUIBuilder
import types

class MaskROIFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	A filter for masking with ROI
	"""
	name = "Use ROI mask"
	category = lib.FilterTypes.ROI
	level = scripting.COLOR_BEGINNER
	def __init__(self):
		"""
		Initialization
		"""
		lib.ProcessingFilter.ProcessingFilter.__init__(self, (2, 2))
		self.descs = {"ROI": "Region of Interest used as mask",
					  "OutputValue":"Outside mask value",
					  "UseImageROI": "Use image input as ROI"}
		self.filterDesc = "Uses a Region of Interest (ROI) as a mask\nInput: Grayscale/Binary/Label image and optional Binary image\nOutput: Grayscale/Binary/Label image"

	def getInputName(self, n):
		"""
		Return the name of the input #n
		"""			 
		if n == 1:
			return "Source dataset %d" % n	  
		return "Optional ROI image"
	
	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""
		return [["Region of Interest", ("ROI",)], ["", ("UseImageROI", "OutputValue")]]
	
	def getType(self, parameter):
		"""
		Return the type of the parameter
		"""    
		if parameter == "ROI":
			return GUI.GUIBuilder.ROISELECTION
		if parameter == "OutputValue":
			return types.FloatType
		if parameter == "UseImageROI":
			return types.BooleanType
		
	def getDefaultValue(self, parameter):
		"""
		Return the default value of a parameter
		"""     
		if parameter == "ROI":
			n = scripting.visualizer.getRegionsOfInterest()
			if n:
				return (0, n[0])
			return 0
		return 0
		
	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute the filter with given inputs and return the output
		"""            
		if not lib.ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None

		if self.parameters["UseImageROI"]:
			maskImage = self.getInput(2)
			# If scalar type is not unsigned char, then cast the data
			cast = vtk.vtkImageCast()
			cast.SetInput(maskImage)
			cast.SetOutputScalarType(3)
			cast.SetClampOverflow(1)
			maskImage = cast.GetOutput()
		else:
			maxx, maxy, maxz = self.dataUnit.getDimensions()
			roi = self.parameters["ROI"][1]
			n, maskImage = lib.ImageOperations.getMaskFromROIs([roi], maxx, maxy, maxz)

		scripting.wantWholeDataset=1
		imagedata = self.getInput(1)
		imagedata.SetUpdateExtent(imagedata.GetWholeExtent())
		imagedata.Update()

		maskFilter = vtk.vtkImageMask()
		maskFilter.SetImageInput(imagedata)
		maskFilter.SetMaskInput(maskImage)
		maskFilter.SetMaskedOutputValue(self.parameters["OutputValue"])
		
		return maskFilter.GetOutput()
