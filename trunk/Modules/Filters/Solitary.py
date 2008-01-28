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
		Created: 13.04.2006, KP
		Description: Initialization
		"""		   
		lib.ProcessingFilter.ProcessingFilter.__init__(self, (1, 1))
		self.vtkfilter = vtkbxd.vtkImageSolitaryFilter()
		self.vtkfilter.AddObserver("ProgressEvent", self.updateProgress)
		self.descs = {"HorizontalThreshold": "X:", "VerticalThreshold": "Y:", \
						"ProcessingThreshold": "Processing threshold:"}
	
	def getParameters(self):
		"""
		Created: 15.04.2006, KP
		Description: Return the list of parameters needed for configuring this GUI
		"""			   
		return [ "Thresholds:", ["", ("HorizontalThreshold", "VerticalThreshold", "ProcessingThreshold")]]
		
	def getXMLDescription(self):
		"""
		Created: 26.01.2008, KP
		Description: return XMl describing this filter's GUI
		"""
		return """
<Filter name="Solitary filter">
	<Parameters>
		<Param id="HorizontalThreshold" type="Integer" defaultValue="0" />
		<Param id="VerticalThreshold" type="Integer" defaultValue="0"  />
		<Param id="ProcessingThreshold" type="Integer"  defaultValue="0" />
	</Parameters>
	<UserInterface>
		<Grouping label="Thresholds">
			<Input id="HorizontalThreshold" label="X:"/>
			<Input id="VerticalThreshold" label="Y:"/>
			<Input id="ProcessingThreshold" label="Processing threshold:" />
		</Grouping>
	</UserInterface>
	<Descriptions>
		<LongDesc id="HorizontalThreshold">
			Threshold that a pixel's horizontal neighbor needs to be over so that the pixel is not removed.
		</LongDesc>
		<LongDesc id="VerticalThreshold">
			Threshold that a pixel's vertical neighbor needs to be over so that the pixel is not removed.
		</LongDesc>
		<LongDesc id="ProcessingThreshold">
			Threshold that a pixel needs to be over to get processed by solitary filter.
		</LongDesc>
	</Descriptions>
</Filter>
"""
		
	def getDesc(self, parameter):
		"""
		Created: 15.04.2006, KP
		Description: Return the description of the parameter
		"""	   
		return self.descs[parameter]
		
	def getLongDesc(self, parameter):
		"""
		Created: 15.04.2006, KP
		Description: Return a long description of the parameter
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
		Created: 15.04.2006, KP
		Description: Return the type of the parameter
		"""	   
		if parameter in ["HorizontalThreshold", "VerticalThreshold", "ProcessingThreshold"]:
			return types.IntType
		
	def getDefaultValue(self, parameter):
		"""
		Created: 15.04.2006, KP
		Description: Return the default value of a parameter
		"""		
		return 0
		
	def execute(self, inputs, update = 0, last = 0):
		"""
		Created: 15.04.2006, KP
		Description: Execute the filter with given inputs and return the output
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
