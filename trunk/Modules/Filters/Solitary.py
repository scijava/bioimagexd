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
import vtkbxd
import GUI.GUIBuilder
import lib.FilterTypes
import scripting
import types

class SolitaryFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	Created: 13.04.2006, KP
	Description: A filter for removing solitary noise pixels
	"""		
	name = "Solitary filter"
	category = lib.FilterTypes.FILTERING
	
	def __init__(self):
		"""
		Initialization
		"""		   
		lib.ProcessingFilter.ProcessingFilter.__init__(self, (1, 1))
		self.vtkfilter = vtkbxd.vtkImageSolitaryFilter()
		self.vtkfilter.AddObserver("ProgressEvent", self.updateProgress)
		self.descs = {"HorizontalThreshold": "X:", "VerticalThreshold": "Y:", \
						"ProcessingThreshold": "Processing threshold:"}
	
	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""			   
		return [ "Thresholds:", ["", ("HorizontalThreshold", "VerticalThreshold", "ProcessingThreshold")]]
		

		
	def getLongDesc(self, parameter):
		"""
		Return a long description of the parameter
		""" 
		Xhelp = "Threshold that a pixel's horizontal neighbor needs to be over so that the pixel is not removed."
		Yhelp = "Threshold that a pixel's vertical neighbor needs to be over so that the pixel is not removed."
		Thresholdhelp = "Threshold that a pixel needs to be over to get processed by solitary filter."
		
		if parameter == "HorizontalThreshold":
			return Xhelp
		elif parameter == "VerticalThreshold":
			return Yhelp
		elif parameter == "ProcessingThreshold":
			return Thresholdhelp
		return ""
		
	def getType(self, parameter):
		"""
		Return the type of the parameter
		"""	   
		if parameter in ["HorizontalThreshold", "VerticalThreshold", "ProcessingThreshold"]:
			return types.IntType
		
	def getDefaultValue(self, parameter):
		"""
		Return the default value of a parameter
		"""		
		return 0
		
	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute the filter with given inputs and return the output
		"""			   
		if not lib.ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None
		
		image = self.getInput(1)
		self.vtkfilter.SetInput(image)
		
		self.vtkfilter.SetFilteringThreshold(self.parameters["ProcessingThreshold"])
		self.vtkfilter.SetHorizontalThreshold(self.parameters["HorizontalThreshold"])
		self.vtkfilter.SetVerticalThreshold(self.parameters["VerticalThreshold"])
		
		if update:
			self.vtkfilter.Update()
		return self.vtkfilter.GetOutput()	   
