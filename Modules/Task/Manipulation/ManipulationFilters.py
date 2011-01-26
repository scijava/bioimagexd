#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: ManipulationFilters
 Project: BioImageXD
 Created: 13.04.2006, KP
 Description:

 A module containing classes representing the filters available in ManipulationPanelC
							
 Copyright (C) 2005	 BioImageXD Project
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

import scripting
import GUI.GUIBuilder as GUIBuilder
import lib.ImageOperations
try:
	import itk
except:
	pass
import lib.messenger
from lib import ProcessingFilter
import types
import vtk
import vtkbxd
import wx

# getFilterlist() searches through these Modules for Filter classes
import MathFilters
import SegmentationFilters
import MorphologicalFilters
import RegistrationFilters
import FourierFilters

from lib.FilterTypes import *


def getFilters():
	"""
	This function returns all the filter-classes in this module and is used by ManipulationFilters.getFilterList()
	"""
	return [GaussianSmoothFilter, 
			#GradientFilter,
			GradientMagnitudeFilter,
			ITKAnisotropicDiffusionFilter, 
			ITKLocalMaximumFilter]

# fixed getFilterList() so that unnecessary wildcard imports could be removed, 10.8.2007 SS
def getFilterList():
	"""
	Modified: 10.8.2007, SS
	This function returns the filter-classes from all filter-modules
	"""
	filterlist = getFilters()
	filterlist += MathFilters.getFilters()
	filterlist += SegmentationFilters.getFilters()
	filterlist += MorphologicalFilters.getFilters()
	filterlist += RegistrationFilters.getFilters()
	filterlist += FourierFilters.getFilters()
	
	return filterlist


class GaussianSmoothFilter(ProcessingFilter.ProcessingFilter):
	"""
	A gaussian smoothing filter
	"""		
	name = "Gaussian smooth"
	category = FILTERING
	
	def __init__(self):
		"""
		Initialization
		"""		   
		ProcessingFilter.ProcessingFilter.__init__(self, (1, 1))
		self.vtkfilter = vtk.vtkImageGaussianSmooth()
		self.eventDesc = "Performing gaussian smoothing"
		self.vtkfilter.AddObserver("ProgressEvent", lib.messenger.send)
		lib.messenger.connect(self.vtkfilter, 'ProgressEvent', self.updateProgress)
		self.descs = {"RadiusX": "Radius factor X:", "RadiusY": "Radius factor Y:", "RadiusZ": "Radius factor Z:",
			"Dimensionality": "Dimensionality"}
	
	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""			   
		return [ "Radius factor:", ["", ("RadiusX", "RadiusY", "RadiusZ")],
		["", ("Dimensionality", )]
		]
		
 
	def getType(self, parameter):
		"""
		Return the type of the parameter
		"""	   
		if parameter in ["RadiusX", "RadiusY", "RadiusZ"]:
			return types.FloatType
		return GUIBuilder.SPINCTRL
		
	def getDefaultValue(self, parameter):
		"""
		Return the default value of a parameter
		"""		
		if parameter == "Dimensionality":
			return 3
		return 1.5
		
	def getRange(self, parameter):
		"""
		return the range of the parameter
		"""
		return 1, 3

	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute the filter with given inputs and return the output
		"""			   
		if not ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None
		
		image = self.getInput(1)
		self.vtkfilter.SetInput(image)
		
		x, y, z = self.parameters["RadiusX"], self.parameters["RadiusY"], self.parameters["RadiusZ"]
		dims = self.parameters["Dimensionality"]
		self.vtkfilter.SetRadiusFactors(x, y, z)
		self.vtkfilter.SetStandardDeviations(x,y,z)
		self.vtkfilter.SetDimensionality(dims)
		self.vtkfilter.SetNumberOfThreads(1)
		if update:
			self.vtkfilter.Update()
		
		return self.vtkfilter.GetOutput()


#class GradientFilter(ProcessingFilter.ProcessingFilter):
#	"""
#	Description: A class for calculating the gradient of the image
#	"""		
#	name = "Gradient"
#	category = MATH
#	
#	def __init__(self, inputs = (1, 1)):
#		"""
#		Initialization
#		"""		   
#		ProcessingFilter.ProcessingFilter.__init__(self, inputs)
#		self.vtkfilter = vtk.vtkImageGradient()
#		self.vtkfilter.SetDimensionality(3)
#		self.vtkfilter.AddObserver("ProgressEvent", lib.messenger.send)
#		lib.messenger.connect(self.vtkfilter, 'ProgressEvent', self.updateProgress)
#	
#	def getParameters(self):
#		"""
#		Return the list of parameters needed for configuring this GUI
#		"""			   
#		return []
#
#	def execute(self, inputs, update = 0, last = 0):
#		"""
#		Execute the filter with given inputs and return the output
#		"""			   
#		if not ProcessingFilter.ProcessingFilter.execute(self, inputs):
#			return None
#		
#		self.vtkfilter.SetInput(self.getInput(1))
#			
#		if update:
#			self.vtkfilter.Update()
#		return self.vtkfilter.GetOutput()			 


class GradientMagnitudeFilter(ProcessingFilter.ProcessingFilter):
	"""
	A class for calculating the gradient magnitude of the image
	"""		
	name = "Gradient magnitude"
	category = FEATUREDETECTION
	level = scripting.COLOR_BEGINNER

	def __init__(self, inputs = (1, 1)):
		"""
		Initialization
		"""		   
		ProcessingFilter.ProcessingFilter.__init__(self, inputs)
		self.vtkfilter = vtk.vtkImageGradientMagnitude()
		self.vtkfilter.SetDimensionality(3)
		self.vtkfilter.AddObserver("ProgressEvent", lib.messenger.send)
		lib.messenger.connect(self.vtkfilter, 'ProgressEvent', self.updateProgress)
		self.eventDesc = "Performing edge detection (gradient magnitude)"
	
	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""			   
		return []

	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute the filter with given inputs and return the output
		"""			   
		if not ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None
		
		self.vtkfilter.SetInput(self.getInput(1))
			
		if update:
			self.vtkfilter.Update()
		return self.vtkfilter.GetOutput()

		
class ITKAnisotropicDiffusionFilter(ProcessingFilter.ProcessingFilter):
	"""
	Description: A class for doing anisotropic diffusion on ITK
	"""		
	name = "Gradient anisotropic diffusion"
	category = FILTERING
	
	def __init__(self, inputs = (1, 1)):
		"""
		Initialization
		"""		   
		ProcessingFilter.ProcessingFilter.__init__(self, inputs)
		
		self.eventDesc = "Performing edge preserving smoothing (gradient anisotropic diffusion)"
		self.descs = {"TimeStep": "Time step for iterations", "Conductance": "Conductance parameter",
			"Iterations": "Number of iterations"}
		self.itkFlag = 1
		self.itkfilter = None

	def getParameterLevel(self, parameter):
		"""
		Return the level of the given parameter
		"""
		return scripting.COLOR_INTERMEDIATE
			
	def getDefaultValue(self, parameter):
		"""
		Return the default value of a parameter
		"""	   
		if parameter == "TimeStep":
			return 0.0625
		if parameter == "Conductance":
			return 9.0
		if parameter == "Iterations":
			return 5
		return 0
		
	def getType(self, parameter):
		"""
		Return the type of the parameter
		"""	   
		if parameter in ["TimeStep", "Conductance"]:
			return types.FloatType
		return types.IntType
		
	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""			   
		return [["", ("TimeStep", "Conductance", "Iterations")]]

	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute the filter with given inputs and return the output
		"""					   
		if not ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None
			
		image = self.getInput(1)
		image = self.convertVTKtoITK(image, cast = types.FloatType)
		
		self.itkfilter = itk.GradientAnisotropicDiffusionImageFilter[image, image].New()
		self.itkfilter.SetInput(image)
		self.itkfilter.SetTimeStep(self.parameters["TimeStep"])
		self.itkfilter.SetConductanceParameter(self.parameters["Conductance"])
		self.itkfilter.SetNumberOfIterations(self.parameters["Iterations"])
		
		if update:
			self.itkfilter.Update()
		return self.itkfilter.GetOutput()			 


class ITKLocalMaximumFilter(ProcessingFilter.ProcessingFilter):
	"""
	Created: 29.05.2006, KP
	Description: A class for finding the local maxima in an image
	"""		
	name = "Find local maxima"
	category = FEATUREDETECTION
	
	def __init__(self, inputs = (1, 1)):
		"""
		Initialization
		"""
		ProcessingFilter.ProcessingFilter.__init__(self, inputs)
		self.descs = {"Connectivity": "Use 8 neighbors for connectivity"}
		self.itkFlag = 1
				
	def getDefaultValue(self, parameter):
		"""
		Return the default value of a parameter
		"""	  
		if parameter == "Connectivity":
			return 1
		return 0

	def getType(self, parameter):
		"""
		Return the type of the parameter
		"""	   
		if parameter in ["Connectivity"]:
			return types.BooleanType
				
	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""			   
		return [["", ("Connectivity", )]]

	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute the filter with given inputs and return the output
		"""					   
		if not ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None
			
		image = self.getInput(1)
#		 print "Using as input",image
		image = self.convertVTKtoITK(image)
		shift = itk.ShiftScaleImageFilter[image, image].New()
		recons = itk.ReconstructionByDilationImageFilter[image, image].New()
		subst = itk.SubtractImageFilter[image, image, image].New()
		shift.SetInput(image)
		shift.SetShift(-1)
		recons.SetMaskImage(image)
		recons.SetMarkerImage(shift.GetOutput())
		recons.SetFullyConnected(self.parameters["Connectivity"])
		subst.SetInput1(image)
		subst.SetInput2(recons.GetOutput())
		
		if 1 or update:
			subst.Update()
			
		data = subst.GetOutput()

		return data			   

