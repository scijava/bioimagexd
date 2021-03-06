#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: MorphologicalFilters
 Project: BioImageXD
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
import itk
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
			SobelFilter, MedianFilter]#, OpeningByReconstruction]


class ErodeFilter(MorphologicalFilter):
	"""
	Description: An erosion filter
	"""     
	name = "Erode"
	category = lib.FilterTypes.MORPHOLOGICAL
	
	def __init__(self):
		"""
		Initialization
		"""        
		MorphologicalFilter.__init__(self)
		self.vtkfilter = vtk.vtkImageContinuousErode3D()
		self.vtkfilter.AddObserver('ProgressEvent', lib.messenger.send)
		lib.messenger.connect(self.vtkfilter, "ProgressEvent", self.updateProgress)
		self.filterDesc = "Replaces each pixel/voxel with minimum value inside kernel\nInput: Grayscale/Binary image\nOutput: Grayscale/Binary image"
		
class VarianceFilter(MorphologicalFilter):
	"""
	Variance filter
	"""
	name = "Variance"
	category = lib.FilterTypes.MORPHOLOGICAL
	
	def __init__(self):
		"""
		Initialization
		"""        
		MorphologicalFilter.__init__(self)
		self.vtkfilter = vtk.vtkImageVariance3D()        
		self.vtkfilter.AddObserver('ProgressEvent', lib.messenger.send)
		lib.messenger.connect(self.vtkfilter, "ProgressEvent", self.updateProgress)
		self.filterDesc = "Replaces each pixel/voxel with variance inside kernel\nInput: Grayscale image\nOutput: Grayscale image"
		
class DilateFilter(MorphologicalFilter):
	"""
	A 3D dilation filter
	"""      
	name = "Dilate"
	category = lib.FilterTypes.MORPHOLOGICAL
	
	def __init__(self):
		"""
		Initialization
		"""        
		MorphologicalFilter.__init__(self)
		self.vtkfilter = vtk.vtkImageContinuousDilate3D()  
		self.vtkfilter.AddObserver('ProgressEvent', lib.messenger.send)
		lib.messenger.connect(self.vtkfilter, "ProgressEvent", self.updateProgress)
		self.filterDesc = "Replaces each pixel/voxel with maximum value inside kernel\nInput: Grayscale/Binary image\nOutput: Grayscale/Binary image"
		
class RangeFilter(MorphologicalFilter):
	"""
	A filter that sets the value of the neighborhood to be the max-min of that nbh
	"""     
	name = "Range"
	category = lib.FilterTypes.MORPHOLOGICAL
	
	def __init__(self):
		"""
		Initialization
		"""        
		MorphologicalFilter.__init__(self)
		self.vtkfilter = vtk.vtkImageRange3D()     
		self.vtkfilter.AddObserver('ProgressEvent', lib.messenger.send)
		lib.messenger.connect(self.vtkfilter, "ProgressEvent", self.updateProgress)
		self.filterDesc = "Replaces each pixel/voxel with maximum minus minimum value inside kernel\nInput: Grayscale image\nOutput: Grayscale image"
		
class SobelFilter(MorphologicalFilter):
	"""
	A sobel filter in 3D
	"""     
	name = "Sobel"
	category = lib.FilterTypes.FEATUREDETECTION
	
	def __init__(self):
		"""
		Initialization
		"""        
		MorphologicalFilter.__init__(self)
		self.vtkfilter = vtk.vtkImageSobel3D()          
		self.vtkfilter.AddObserver('ProgressEvent', lib.messenger.send)
		lib.messenger.connect(self.vtkfilter, "ProgressEvent", self.updateProgress)
		self.filterDesc = "Applies Sobel operator for each pixel/voxel\nInput: Grayscale image\nOutput: Vector image"
		
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
	name = "Median"
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
		self.filterDesc = "Replaces each pixel/voxel with median value inside kernel\nInput: Grayscale/Binary image\nOutput: Grayscale/Binary image"

"""
class OpeningByReconstruction(MorphologicalFilter):
	\"""
	OpeningByReconstructionFilter
	OpeningByReconstruction(f) = DilationByReconstruction(f,Erosion(f))
	\"""
	name = "Opening by reconstruction"
	category = lib.FilterTypes.MORPHOLOGICAL
	level = scripting.COLOR_INTERMEDIATE

	def __init__(self):
		\"""
		Initialization
		\"""
		MorphologicalFilter.__init__(self)
		self.itkFlag = 1
		self.filter = None
		self.pc = itk.PyCommand.New()
		self.pc.SetCommandCallable(self.updateProgress)

	def updateProgress(self):
		\"""
		Update progress event handler
		\"""
		lib.ProcessingFilter.ProcessingFilter.updateProgress(self,self.filter,"ProgressEvent")

	def execute(self, inputs, update = 0, last = 0):
		\"""
		Execute the filter with given inputs and return the output
		\"""
		if not lib.ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None
		image = self.getInput(1)
		image = self.convertVTKtoITK(image)

		kernelX = self.parameters["KernelX"]
		kernelY = self.parameters["KernelY"]
		kernelZ = self.parameters["KernelZ"]
		region = image.GetLargestPossibleRegion()
		size = region.GetSize()
		dim = region.GetImageDimension()
		strel = itk.strel(dim)

		if kernelX > size.GetElement(0):
			kernelX = size.GetElement(0)
		if kernelY > size.GetElement(1):
			kernelY = size.GetElement(1)
		if dim == 3 and kernelZ > size.GetElement(2):
			kernelZ = size.GetElement(2)

		if dim == 3:
			radius = (kernelX,kernelY,kernelZ)
		else:
			radius = (kernelX,kernelY)
		strel.SetRadius(radius)

		self.filter = itk.OpeningByReconstructionImageFilter[image,image,strel].New()
		self.filter.AddObserver(itk.ProgressEvent(),self.pc.GetPointer())
		self.filter.SetKernel(strel)
		self.filter.SetInput(image)

		output = self.filter.GetOutput()
		output.Update()

		return output
"""		
