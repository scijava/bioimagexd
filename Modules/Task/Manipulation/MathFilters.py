#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: MathFilters
 Project: BioImageXD
 Description:

 A module containing the math filters for the processing task.
							
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
import vtkbxd
import types
from lib.FilterTypes import *


class MathFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	Created: 13.04.2006, KP
	Description: A base class for image mathematics filters
	"""     
	name = "Math filter"
	category = MATH
	
	def __init__(self, inputs = (2, 2)):
		"""
		Initialization
		"""        
		lib.ProcessingFilter.ProcessingFilter.__init__(self, inputs)
		self.descs = {"ClampOverflow": "Prevent over/underflow"}
		self.vtkfilter = vtkbxd.vtkImageMathematicsClamp()
	
	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""            
		return [["", ("ClampOverflow",)],]

	def getType(self, param):
		"""
		Return the type of param
		"""
		return types.BooleanType

	def getDefaultValue(self, param):
		"""
		Return the default value of the param
		"""
		return True

	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute the filter with given inputs and return the output
		"""
		lib.ProcessingFilter.ProcessingFilter.execute(self, inputs)
		image = self.getInput(1)
		self.vtkfilter.SetClampOverflow(self.parameters["ClampOverflow"])
	
		if self.numberOfInputs[0] > 1:
			self.vtkfilter.SetInput1(image)
			self.vtkfilter.SetInput2(self.getInput(2))
		else:
			self.vtkfilter.SetInput1(image)
			self.vtkfilter.SetInput2(image)
			self.vtkfilter.SetInput(image)    
		f = "self.vtkfilter.SetOperationTo%s()" % self.operation
		eval(f)
		
		if update:
			self.vtkfilter.Update()
		return self.vtkfilter.GetOutput() 


def getFilters():
    """
    This function returns all the filter-classes in this module and is used by ManipulationFilters.getFilterList()
    """
    return [AndFilter, OrFilter, XorFilter, NotFilter,
            NorFilter, NandFilter, SubtractFilter, AddFilter,
            DivideFilter, MultiplyFilter, SinFilter,
            CosFilter, ExpFilter, LogFilter, SQRTFilter]


class LogicFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	A base class for logic filters
	"""     
	name = "Logic filter"
	category = LOGIC
	
	def __init__(self, inputs = (2, 2)):
		"""
		Initialization
		"""        
		lib.ProcessingFilter.ProcessingFilter.__init__(self, inputs)
		self.vtkfilter = vtk.vtkImageLogic()
		self.vtkfilter.SetOutputTrueValue(255)

	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""
		return []

	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute the filter with given inputs and return the output
		"""
		lib.ProcessingFilter.ProcessingFilter.execute(self, inputs)
		image = self.getInput(1)
	
		if self.numberOfInputs[0] > 1:
			self.vtkfilter.SetInput1(image)
			self.vtkfilter.SetInput2(self.getInput(2))
		else:
			self.vtkfilter.SetInput1(image)
			self.vtkfilter.SetInput2(image)
			self.vtkfilter.SetInput(image)    
		f = "self.vtkfilter.SetOperationTo%s()" % self.operation
		eval(f)
		
		if update:
			self.vtkfilter.Update()
		return self.vtkfilter.GetOutput() 

		
class AndFilter(LogicFilter):
	"""
	Description: A filter for calculating logical and
	"""     
	name = "And"
   
	def __init__(self):
		"""
		Initialization
		"""        
		LogicFilter.__init__(self)
		self.operation = "And"
		self.filterDesc = "Calculates logical \"and\" between input images\nInputs: Binary/Grayscale images\nOutput: Binary image"
		
class OrFilter(LogicFilter):
	"""
	Description: A filter for calculating logical or
	"""     
	name = "Or"
   
	def __init__(self):
		"""
		Initialization
		"""        
		LogicFilter.__init__(self)
		self.operation = "Or"
		self.filterDesc = "Calculates logical \"or\" between input images\nInputs: Binary/Grayscale images\nOutput: Binary image"

class XorFilter(LogicFilter):
	"""
	Description: A filter for calculating logical xor
	"""
	name = "Xor"
   
	def __init__(self):
		"""
		Method: __init__()
		Initialization
		"""        
		LogicFilter.__init__(self)
		self.operation = "Xor"
		self.filterDesc = "Calculates logical \"xor\" between input images\nInputs: Binary/Grayscale images\nOutput: Binary image"
	   
class NotFilter(LogicFilter):
	"""
	Description: A filter for calculating logical not
	"""
	name = "Not"
				
	def __init__(self):
		"""
		Initialization
		"""        
		LogicFilter.__init__(self, inputs = (1, 1))
		self.operation = "Not"
		self.filterDesc = "Calculates logical \"negate\" of input image\nInput: Binary/Grayscale image\nOutput: Binary image"

class NorFilter(LogicFilter):
	"""
	Description: A filter for calculating logical nor
	"""     
	name = "Nor"
   
	def __init__(self):
		"""
		Initialization
		"""        
		LogicFilter.__init__(self)
		self.operation = "Nor"
		self.filterDesc = "Calculates logical \"nor\" between input images\nInputs: Binary/Grayscale images\nOutput: Binary image"
		
class NandFilter(LogicFilter):
	"""
	Description: A filter for calculating logical nand
	"""     
	name = "Nand"
   
	def __init__(self):
		"""
		Initialization
		"""        
		LogicFilter.__init__(self)
		self.operation = "Nand"
		self.filterDesc = "Calculates logical \"nand\" between input images\nInputs: Binary/Grayscale images\nOutput: Binary image"
		
class SubtractFilter(MathFilter):
	"""
	Description: A filter for subtracting two channels
	"""
	name = "Subtract"
	category = MATH
	
	def __init__(self):
		"""
		Initialization
		"""        
		MathFilter.__init__(self)
		self.operation = "Subtract"
		self.filterDesc = "Subtracts one image from another, by subtracting the intensities for every pixel/voxel\nInputs: Grayscale image\nOutput: Grayscale image"

class AddFilter(MathFilter):
	"""
	Created: 15.04.2006, KP
	Description: A filter for adding two channels
	"""     
	name = "Add"
	category = MATH
	
	def __init__(self):
		"""
		Method: __init__()
		Initialization
		"""        
		MathFilter.__init__(self)
		self.operation = "Add"
		self.filterDesc = "Adds two images together, by pointwise adding the intensities for every pixel/voxel\nInputs: Grayscale images\nOutput: Grayscale image"

class DivideFilter(MathFilter):
	"""
	Class: DivideFilter
	Created: 15.04.2006, KP
	Description: A filter for dividing two channels
	"""     
	name = "Divide"
	category = MATH
	
	def __init__(self):
		"""
		Method: __init__()
		Initialization
		"""        
		MathFilter.__init__(self)
		self.operation = "Divide"
		self.filterDesc = "Divides one image by another, by pointwise dividing the intensities for every pixel/voxel\nInputs: Grayscale images\nOutput: Grayscale image"
		
class MultiplyFilter(MathFilter):
	"""
	Class: MultiplyFilter
	Created: 15.04.2006, KP
	Description: A filter for multiplying two channels
	"""     
	name = "Multiply"
	category = MATH
	
	def __init__(self):
		"""
		Method: __init__()
		Initialization
		"""        
		MathFilter.__init__(self)
		self.operation = "Multiply"
		self.filterDesc = "Multiplies one image by another, by pointwise multiplying the intensities for every pixel/voxel\nInputs: Grayscale images\nOutput: Grayscale image"
		
class SinFilter(MathFilter):
	"""
	Class: SinFilter
	Created: 15.04.2006, KP
	Description: A filter for calculating sine of input
	"""     
	name = "Sin"
	category = MATH
	
	def __init__(self):
		"""
		Method: __init__()
		Initialization
		"""        
		MathFilter.__init__(self, (1, 1))
		self.operation = "Sin"
		self.filterDesc = "Calculates the sine of the intensity of each pixel/voxel\nInput: Grayscale image\nOutput: Grayscale image"

class CosFilter(MathFilter):
	"""
	Class: CosFilter
	Created: 15.04.2006, KP
	Description: A filter for calculating cosine of input
	"""     
	name = "Cos"
	category = MATH
	
	def __init__(self):
		"""
		Method: __init__()
		Initialization
		"""
		MathFilter.__init__(self, (1, 1))
		self.operation = "Cos"
		self.filterDesc = "Calculates the cosine of the intensity of each pixel/voxel\nInput: Grayscale image\nOutput: Grayscale image"

class ExpFilter(MathFilter):
	"""
	Class: ExpFilter
	Description: A filter for calculating exp of input
	"""     
	name = "Exp"
	category = MATH
	
	def __init__(self):
		"""
		Method: __init__()
		Initialization
		"""        
		MathFilter.__init__(self, (1, 1))
		self.operation = "Exp"
		self.filterDesc = "Calculates the exponent of the intensity of each pixel/voxel\nInput: Grayscale image\nOutput: Grayscale image"
		
class LogFilter(MathFilter):
	"""
	Class: LogFilter
	Description: A filter for calculating logarithm of input
	"""     
	name = "Log"
	category = MATH
	
	def __init__(self):
		"""
		Method: __init__()
		Initialization
		"""        
		MathFilter.__init__(self, (1, 1))
		self.operation = "Log"
		self.filterDesc = "Calculates the logarithm of the intensity of each pixel/voxel\nInput: Grayscale image\nOutput: Grayscale image"
		
class SQRTFilter(MathFilter):
	"""
	Class: SQRTFilter
	Description: A filter for calculating square root of input
	"""     
	name = "Sqrt"
	category = MATH
	
	def __init__(self):
		"""
		Method: __init__()
		Initialization
		"""        
		MathFilter.__init__(self, (1, 1))
		self.operation = "SquareRoot"
		self.filterDesc = "Calculates the square root of the intensity of each pixel/voxel\nInput: Grayscale image\nOutput: Grayscale image"
			
