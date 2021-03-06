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

from lib import ProcessingFilter
import vtk
import types
import GUI.GUIBuilder as GUIBuilder
import lib.messenger
import scripting
import lib.FilterTypes

class AnisotropicDiffusionFilter(ProcessingFilter.ProcessingFilter):
	"""
	An edge preserving smoothing filter
	"""     
	name = "Anisotropic diffusion"
	category = lib.FilterTypes.FILTERING
	level = scripting.COLOR_EXPERIENCED
	
	def __init__(self):
		"""
		Initialization
		"""        
		ProcessingFilter.ProcessingFilter.__init__(self, (1, 1))
		self.vtkfilter = vtk.vtkImageAnisotropicDiffusion3D()
		self.eventDesc = "Performing edge preserving smoothing (anisotropic diffusion)"

		self.vtkfilter.AddObserver('ProgressEvent', lib.messenger.send)
		lib.messenger.connect(self.vtkfilter, "ProgressEvent", self.updateProgress)
		self.descs = {"Faces": "Faces", "Corners": "Corners", "Edges": "Edges",
			"CentralDiff": "Central difference", "Gradient": "Gradient to neighbor",
				"DiffThreshold": "Diffusion threshold:", "DiffFactor": "Diffusion factor:"}
		self.filterDesc = "Performs anisotropic diffusion inside the neighborhood that fulfills given parameters\nInput: Grayscale image\nOutput: Grayscale image"
	
	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""            
		return [ 
		"Neighborhood:", ["", ( ("Faces", "Corners", "Edges"), )],
		["Gradient measure", ( ("CentralDiff", "Gradient"), ("cols", 2)) ],
		["", ("DiffThreshold", "DiffFactor")]
		]

	def getParameterLevel(self, parameter):
		"""
		Return parameter level
		"""
		return scripting.COLOR_EXPERIENCED
		
	def getLongDesc(self, parameter):
		"""
		Return a long description of the parameter
		"""     
		if parameter == "Faces":
			return "Toggle whether the 6 voxels adjoined by faces are included in the neighborhood."
		elif parameter == "Corners":
			return "Toggle whether the 8 corner connected voxels are included in the neighborhood."
		elif parameter == "Edges":
			return "Toggle whether the 12 edge connected voxels are included in the neighborhood."
		return ""
		
	def getType(self, parameter):
		"""
		Return the type of the parameter
		"""    
		if parameter in ["Faces", "Edges", "Corners"]:
			return types.BooleanType
		elif parameter in ["CentralDiff", "Gradient"]:
			return GUIBuilder.RADIO_CHOICE
		return types.FloatType
		
	def getDefaultValue(self, parameter):
		"""
		Return the default value of a parameter
		"""     
		if parameter in ["Faces", "Edges", "Corners"]:
			return 1
		elif parameter == "DiffThreshold":
			return 5.0
		elif parameter == "DiffFactor":
			return 1.0
		if parameter == "CentralDiff":
			return True
		return False

	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute the filter with given inputs and return the output
		"""
		if not ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None
		
		image = self.getInput(1)
		self.vtkfilter.SetInput(image)

		self.vtkfilter.SetDiffusionThreshold(self.parameters["DiffThreshold"])
		self.vtkfilter.SetDiffusionFactor(self.parameters["DiffFactor"])
		self.vtkfilter.SetFaces(self.parameters["Faces"])
		self.vtkfilter.SetEdges(self.parameters["Edges"])
		self.vtkfilter.SetCorners(self.parameters["Corners"])
		self.vtkfilter.SetGradientMagnitudeThreshold(self.parameters["CentralDiff"])

		if update:
			self.vtkfilter.Update()
		return self.vtkfilter.GetOutput()      
