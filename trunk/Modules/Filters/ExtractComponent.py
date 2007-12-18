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
import vtk
import GUI.GUIBuilder
import lib.FilterTypes
import scripting

class ExtractComponentFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	Created: 21.01.2007, KP
	Description: A filter for extracting component or components from a dataset
	"""     
	name = "Extract components"
	category = lib.FilterTypes.FILTERING
	
	def __init__(self):
		"""
		Created: 21.01.2007, KP
		Description: Initialization
		"""        
		lib.ProcessingFilter.ProcessingFilter.__init__(self, (1, 1))
		self.vtkfilter = vtk.vtkImageExtractComponents()
		self.vtkfilter.AddObserver("ProgressEvent", self.updateProgress)
		
		self.descs = {"Component1": "Component #1", "Component2": "Component #2", "Component3": "Component #3"}
	
	def getParameters(self):
		"""
		Created: 21.01.2007, KP
		Description: Return the list of parameters needed for configuring this GUI
		"""            
		return [["", ("Component1", "Component2", "Component3")]]
		
	def getDesc(self, parameter):
		"""
		Created: 21.01.2007, KP
		Description: Return the description of the parameter
		"""    
		return self.descs[parameter]
		
	def getLongDesc(self, parameter):
		"""
		Created: 21.01.2007, KP
		Description: Return a long description of the parameter
		""" 
		return ""
		
	def getRange(self, parameter):
		"""
		Created: 21.01.2007, KP
		Description: return the range of values for given parameter
		"""
		return ["No output", "R (component 1)", "G (component 2)", "B (component 3)"]
		
	def getType(self, parameter):
		"""
		Created: 21.01.2007, KP
		Description: Return the type of the parameter
		"""    
		if parameter in ["Component1", "Component2", "Component3"]:
			return GUI.GUIBuilder.CHOICE
		
	def getDefaultValue(self, parameter):
		"""
		Created: 21.01.2007, KP
		Description: Return the default value of a parameter
		"""     
		if parameter == "Component1":
			return 1
		if parameter == "Component2":
			return 2
		if parameter == "Component3":
			return 3
		

	def execute(self, inputs, update = 0, last = 0):
		"""
		Created: 15.04.2006, KP
		Description: Execute the filter with given inputs and return the output
		"""            
		if not ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None
		
		image = self.getInput(1)
		#print "Using ",image
		self.vtkfilter.SetInput(image)
		
		cmps = []
		cmps.append(self.parameters["Component1"])
		cmps.append(self.parameters["Component2"])
		cmps.append(self.parameters["Component3"])
		while 0 in cmps:
			cmps.remove(0)
		cmps = [x - 1 for x in cmps]
		t = tuple(cmps)
		print "Extracting components", t
		self.vtkfilter.SetComponents(*t)            
		
		if update:
			self.vtkfilter.Update()
		return self.vtkfilter.GetOutput()    
		
		