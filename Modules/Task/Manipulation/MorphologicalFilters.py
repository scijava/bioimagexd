#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: MorphologicalFilters
 Project: BioImageXD
 Created: 07.06.2006, KP
 Description:

 A module containing the morphological filters for the processing task.
							
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
import types
import lib.messenger
import scripting
import vtk
import lib.FilterTypes


class MorphologicalFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	A base class for morphological operations
	"""     
	name = "Morphological filter"
	category = lib.FilterTypes.MORPHOLOGICAL
	
	def __init__(self):
		"""
		Initialization
		"""        
		lib.ProcessingFilter.ProcessingFilter.__init__(self, (1, 1))
	
		self.descs = {"KernelX": "X", "KernelY": "Y", "KernelZ": "Z"}
	
	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""            
		return [ ["Kernel size", ("KernelX", "KernelY", "KernelZ")] ]
		
	def getDesc(self, parameter):
		"""
		Return the description of the parameter
		"""    
		return self.descs[parameter]
		
	def getType(self, parameter):
		"""
		Return the type of the parameter
		"""    
		return types.IntType
		
	def getDefaultValue(self, parameter):
		"""
		Return the default value of a parameter
		"""           
		return 2
		

	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute the filter with given inputs and return the output
		"""            
		if not lib.ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None
		
		x, y, z = self.parameters["KernelX"], self.parameters["KernelY"], self.parameters["KernelZ"]
		self.vtkfilter.SetKernelSize(x, y, z)
		
		image = self.getInput(1)
		  
		self.vtkfilter.SetInput(image)
		if update:
			self.vtkfilter.Update()
		return self.vtkfilter.GetOutput()                


def getFilters():
    """
    This function returns all the filter-classes in this module and is used by ManipulationFilters.getFilterList()
    """
    return [DilateFilter, ErodeFilter, VarianceFilter, RangeFilter,
            SobelFilter, MedianFilter]


class ErodeFilter(MorphologicalFilter):
	"""
	Description: An erosion filter
	"""     
	name = "Erode 3D"
	category = lib.FilterTypes.MORPHOLOGICAL
	
	def __init__(self):
		"""
		Initialization
		"""        
		MorphologicalFilter.__init__(self)
		self.vtkfilter = vtk.vtkImageContinuousErode3D()
		self.vtkfilter.AddObserver('ProgressEvent', lib.messenger.send)
		lib.messenger.connect(self.vtkfilter, "ProgressEvent", self.updateProgress)
		
class VarianceFilter(MorphologicalFilter):
	"""
	Variance filter
	"""     
	name = "Variance 3D"
	category = lib.FilterTypes.MORPHOLOGICAL
	
	def __init__(self):
		"""
		Initialization
		"""        
		MorphologicalFilter.__init__(self)
		self.vtkfilter = vtk.vtkImageVariance3D()        
		self.vtkfilter.AddObserver('ProgressEvent', lib.messenger.send)
		lib.messenger.connect(self.vtkfilter, "ProgressEvent", self.updateProgress)
		
class DilateFilter(MorphologicalFilter):
	"""
	A 3D dilation filter
	"""      
	name = "Dilate 3D"
	category = lib.FilterTypes.MORPHOLOGICAL
	
	def __init__(self):
		"""
		Initialization
		"""        
		MorphologicalFilter.__init__(self)
		self.vtkfilter = vtk.vtkImageContinuousDilate3D()  
		self.vtkfilter.AddObserver('ProgressEvent', lib.messenger.send)
		lib.messenger.connect(self.vtkfilter, "ProgressEvent", self.updateProgress)
  
class RangeFilter(MorphologicalFilter):
	"""
	A filter that sets the value of the neighborhood to be the max-min of that nbh
	"""     
	name = "Range 3D"
	category = lib.FilterTypes.MORPHOLOGICAL
	
	def __init__(self):
		"""
		Initialization
		"""        
		MorphologicalFilter.__init__(self)
		self.vtkfilter = vtk.vtkImageRange3D()     
		self.vtkfilter.AddObserver('ProgressEvent', lib.messenger.send)
		lib.messenger.connect(self.vtkfilter, "ProgressEvent", self.updateProgress)
		
class SobelFilter(MorphologicalFilter):
	"""
	A sobel filter in 3D
	"""     
	name = "Sobel 3D"
	category = lib.FilterTypes.FEATUREDETECTION
	
	def __init__(self):
		"""
		Initialization
		"""        
		MorphologicalFilter.__init__(self)
		self.vtkfilter = vtk.vtkImageSobel3D()          
		self.vtkfilter.AddObserver('ProgressEvent', lib.messenger.send)
		lib.messenger.connect(self.vtkfilter, "ProgressEvent", self.updateProgress)
		
	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""  
		return []
		
	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute the filter with given inputs and return the output
		"""            
		if not lib.ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None        
		image = self.getInput(1)
		self.vtkfilter.SetInput(image)
		if update:
			self.vtkfilter.Update()
		return self.vtkfilter.GetOutput()
		

		
		
class MedianFilter(MorphologicalFilter):
	"""
	A median filter
	"""     
	name = "Median 3D"
	category = lib.FilterTypes.FILTERING
	level = scripting.COLOR_BEGINNER
	
	def __init__(self):
		"""
		Initialization
		"""        
		MorphologicalFilter.__init__(self)
		self.vtkfilter = vtk.vtkImageMedian3D()     
		self.vtkfilter.AddObserver('ProgressEvent', lib.messenger.send)
		lib.messenger.connect(self.vtkfilter, "ProgressEvent", self.updateProgress)
