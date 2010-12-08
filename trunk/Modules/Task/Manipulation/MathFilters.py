#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: MathFilters
 Project: BioImageXD
 Created: 07.06.2006, KP
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
		self.descs = {"ClampOverflow": "Clamp overflow"}
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
	Created: 15.04.2006, KP
	Description: A filter for calculating logical and
	"""     
	name = "And"
   
	def __init__(self):
		"""
		Initialization
		"""        
		LogicFilter.__init__(self)
		self.operation = "And"    
		
class OrFilter(LogicFilter):
	"""
	Created: 15.04.2006, KP
	Description: A filter for calculating logical or
	"""     
	name = "Or"
   
	def __init__(self):
		"""
		Initialization
		"""        
		LogicFilter.__init__(self)
		self.operation = "Or"

class XorFilter(LogicFilter):
	"""
	Created: 15.04.2006, KP
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
	   
class NotFilter(LogicFilter):
	"""
	Created: 15.04.2006, KP
	Description: A filter for calculating logical not
	"""     
	name = "Not"
				
	def __init__(self):
		"""
		Initialization
		"""        
		LogicFilter.__init__(self, inputs = (1, 1))
		self.operation = "Not"       
		
class NorFilter(LogicFilter):
	"""
	Created: 15.04.2006, KP
	Description: A filter for calculating logical nor
	"""     
	name = "Nor"
   
	def __init__(self):
		"""
		Initialization
		"""        
		LogicFilter.__init__(self)
		self.operation = "Nor"    
		
class NandFilter(LogicFilter):
	"""
	Created: 15.04.2006, KP
	Description: A filter for calculating logical nand
	"""     
	name = "Nand"
   
	def __init__(self):
		"""
		Initialization
		"""        
		LogicFilter.__init__(self)
		self.operation = "Nand"          
		
class SubtractFilter(MathFilter):
	"""
	Created: 15.04.2006, KP
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

class ExpFilter(MathFilter):
	"""
	Class: ExpFilter
	Created: 15.04.2006, KP
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
		
class LogFilter(MathFilter):
	"""
	Class: LogFilter
	Created: 15.04.2006, KP
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
   
class SQRTFilter(MathFilter):
	"""
	Class: SQRTFilter
	Created: 15.04.2006, KP
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
			
