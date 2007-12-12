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
import scripting
import vtk

MORPHOLOGICAL = "Morphological operations"
FEATUREDETECTION = "Feature detection"
FILTERING = "Filtering"

class MorphologicalFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	Created: 13.04.2006, KP
	Description: A base class for manipulation filters
	"""     
	name = "Morphological filter"
	category = MORPHOLOGICAL
	
	def __init__(self):
		"""
		Method: __init__()
		Created: 13.04.2006, KP
		Description: Initialization
		"""        
		lib.ProcessingFilter.ProcessingFilter.__init__(self, (1, 1))
	
		self.descs = {"KernelX": "X", "KernelY": "Y", "KernelZ": "Z"}
	
	def getParameters(self):
		"""
		Method: getParameters
		Created: 13.04.2006, KP
		Description: Return the list of parameters needed for configuring this GUI
		"""            
		return [ ["Convolution kernel", ("KernelX", "KernelY", "KernelZ")] ]
		
	def getDesc(self, parameter):
		"""
		Method: getDesc
		Created: 13.04.2006, KP
		Description: Return the description of the parameter
		"""    
		return self.descs[parameter]
		
	def getType(self, parameter):
		"""
		Method: getType
		Created: 13.04.2006, KP
		Description: Return the type of the parameter
		"""    
		return types.IntType
		
	def getDefaultValue(self, parameter):
		"""
		Method: getDefaultValue
		Created: 13.04.2006, KP
		Description: Return the default value of a parameter
		"""           
		return 2
		

	def execute(self, inputs, update = 0, last = 0):
		"""
		Method: execute
		Created: 13.04.2006, KP
		Description: Execute the filter with given inputs and return the output
		"""            
		if not lib.ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None
		
		x, y, z = self.parameters["KernelX"], self.parameters["KernelY"], self.parameters["KernelZ"]
		self.vtkfilter.SetKernelSize(x, y, z)
		
		image = self.getInput(1)
		  
		#print "Setting input=",image  
		self.vtkfilter.SetInput(image)
		if update:
			self.vtkfilter.Update()
		return self.vtkfilter.GetOutput()                


def getFilters():
    """
    Created: 10.8.2007, SS
    Description: This function returns all the filter-classes in this module and is used by ManipulationFilters.getFilterList()
    """
    return [DilateFilter, ErodeFilter, VarianceFilter, RangeFilter,
            SobelFilter, HybridMedianFilter, MedianFilter]


class ErodeFilter(MorphologicalFilter):
	"""
	Created: 13.04.2006, KP
	Description: An erosion filter
	"""     
	name = "Erode 3D"
	category = MORPHOLOGICAL
	
	def __init__(self):
		"""
		Method: __init__()
		Created: 13.04.2006, KP
		Description: Initialization
		"""        
		MorphologicalFilter.__init__(self)
		self.vtkfilter = vtk.vtkImageContinuousErode3D()
		self.vtkfilter.AddObserver("ProgressEvent", self.updateProgress)
		
class VarianceFilter(MorphologicalFilter):
	"""
	Created: 13.04.2006, KP
	Description: Variance filter
	"""     
	name = "Variance 3D"
	category = MORPHOLOGICAL
	
	def __init__(self):
		"""
		Method: __init__()
		Created: 13.04.2006, KP
		Description: Initialization
		"""        
		MorphologicalFilter.__init__(self)
		self.vtkfilter = vtk.vtkImageVariance3D()        
		self.vtkfilter.AddObserver("ProgressEvent", self.updateProgress)
		
class DilateFilter(MorphologicalFilter):
	"""
	Created: 13.04.2006, KP
	Description: A dilation filter
	"""      
	name = "Dilate 3D"
	category = MORPHOLOGICAL
	
	def __init__(self):
		"""
		Method: __init__()
		Created: 13.04.2006, KP
		Description: Initialization
		"""        
		MorphologicalFilter.__init__(self)
		self.vtkfilter = vtk.vtkImageContinuousDilate3D()  
		self.vtkfilter.AddObserver("ProgressEvent", self.updateProgress)
  
class RangeFilter(MorphologicalFilter):
	"""
	Created: 13.04.2006, KP
	Description: A filter that sets the value of the neighborhood to be the max-min of that nbh
	"""     
	name = "Range 3D"
	category = MORPHOLOGICAL
	
	def __init__(self):
		"""
		Created: 13.04.2006, KP
		Description: Initialization
		"""        
		MorphologicalFilter.__init__(self)
		self.vtkfilter = vtk.vtkImageRange3D()     
		self.vtkfilter.AddObserver("ProgressEvent", self.updateProgress)
		
class SobelFilter(MorphologicalFilter):
	"""
	Created: 13.04.2006, KP
	Description: A sobel filter in 3D
	"""     
	name = "Sobel 3D"
	category = FEATUREDETECTION
	
	def __init__(self):
		"""
		Created: 13.04.2006, KP
		Description: Initialization
		"""        
		MorphologicalFilter.__init__(self)
		self.vtkfilter = vtk.vtkImageSobel3D()          
		self.vtkfilter.AddObserver("ProgressEvent", self.updateProgress)
		
	def getParameters(self):
		"""
		Created: 13.04.2006, KP
		Description: Return the list of parameters needed for configuring this GUI
		"""  
		return []
		
	def execute(self, inputs, update = 0, last = 0):
		"""
		Created: 13.04.2006, KP
		Description: Execute the filter with given inputs and return the output
		"""            
		if not lib.ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None        
		image = self.getInput(1)
		self.vtkfilter.SetInput(image)
		if update:
			self.vtkfilter.Update()
		return self.vtkfilter.GetOutput()         
		
class HybridMedianFilter(MorphologicalFilter):
	"""
	Created: 13.04.2006, KP
	Description: A 2D median filter that preserves edges and corners
	"""     
	name = "Hybrid median 2D"
	category = FILTERING
	level = scripting.COLOR_BEGINNER
	
	def __init__(self):
		"""
		Created: 13.04.2006, KP
		Description: Initialization
		"""        
		MorphologicalFilter.__init__(self)
		self.vtkfilter = vtk.vtkImageHybridMedian2D()        
		self.vtkfilter.AddObserver("ProgressEvent", self.updateProgress)
		self.eventDesc = "Performing hybrid median filtering"
		
	def getParameters(self):
		"""
		Created: 13.04.2006, KP
		Description: Return the list of parameters needed for configuring this GUI
		"""  
		return []
		
	def execute(self, inputs, update = 0, last = 0):
		"""
		Created: 13.04.2006, KP
		Description: Execute the filter with given inputs and return the output
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
	Created: 13.04.2006, KP
	Description: A median filter
	"""     
	name = "Median 3D"
	category = FILTERING
	level = scripting.COLOR_BEGINNER
	
	def __init__(self):
		"""
		Method: __init__()
		Created: 13.04.2006, KP
		Description: Initialization
		"""        
		MorphologicalFilter.__init__(self)
		self.vtkfilter = vtk.vtkImageMedian3D()        
		self.vtkfilter.AddObserver("ProgressEvent", self.updateProgress)
