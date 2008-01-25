#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: RegistrationFilters
 Project: BioImageXD
 Created: 14.03.2007, KP
 Description:

 A module containing the registration filters for the processing task.
							
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
__author__ = "BioImageXD Project <http://www.bioimagexd.net/>"
__version__ = "$Revision$"
__date__ = "$Date$"

import lib.ProcessingFilter
import types
import GUI.GUIBuilder as GUIBuilder
import scripting

SEGMENTATION = "Segmentation"
MEASUREMENT = "Measurements"
WATERSHED = "Watershed segmentation"
REGIONGROWING = "Region growing"
REGISTRATION = "Registration"


class RegistrationFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	Created: 14.03.2007, KP
	Description: A filter for doing registration
	"""     
	name = "Versor Rigid 3D Registration"
	category = REGISTRATION
	level = scripting.COLOR_EXPERIENCED
	
	def __init__(self, inputs = (1, 1)):
		"""
		Created: 14.03.2007, KP
		Description: Initialization
		"""        
		lib.ProcessingFilter.ProcessingFilter.__init__(self, inputs)
		
		self.descs = {"FixedTimepoint": "Timepoint for fixed image", "MaxStepLength": "Maximum step length", "MinStepLength": "Minimum step length", "MaxIterations": "Maximum iterations", "BackgroundPixelValue": "Set background pixel value as", "UsePreviousAsFixed": "Use previous time point as fixed image"}
		self.itkFlag = 1
		self.registration = None
		self.metric = None
		self.transform = None
		self.interpolator = None
		self.optimizer = None
		self.resampler = None
		self.lastTransform = None

	def updateProgress(self):
		"""
		Created: 20.12.2007, LP
		Description: Updates progress of the registration
		"""
		# ImageRegistrationMethod doesn't update progress so we need to do it
		self.registration.SetProgress(self.optimizer.GetCurrentIteration().__float__()/self.optimizer.GetNumberOfIterations().__float__())
		lib.ProcessingFilter.ProcessingFilter.updateProgress(self,self.registration,"ProgressEvent")
		
	def getParameterLevel(self, parameter):
		"""
		Created: 14.03.2007, KP
		Description: Return the level of the given parameter
		"""
		if parameter in ["FixedTimepoint","BackgroundPixelValue","MaxIterations","UsePreviousAsFixed"]:
			return scripting.COLOR_INTERMEDIATE
		if parameter in ["MaxStepLength","MinStepLength"]:
			return scripting.COLOR_EXPERIENCED
		
		return scripting.COLOR_BEGINNER                    
			
	def getDefaultValue(self, parameter):
		"""
		Created: 14.03.2007, KP
		Description: Return the default value of a parameter
		"""    
		if parameter == "FixedTimepoint":
			return 1
		if parameter == "MaxStepLength":
			return 10.0
		if parameter == "MinStepLength":
			return 0.1
		if parameter == "MaxIterations":
			return 30
		if parameter == "BackgroundPixelValue":
			return 0
		if parameter == "UsePreviousAsFixed":
			return False
		
		return 0
		
	def getRange(self, parameter):
		"""
		Created: 14.03.2007, KP
		Description: Return the range for a given parameter
		"""
		if parameter == "FixedTimepoint":
			return (1, self.dataUnit.getNumberOfTimepoints())
		if parameter == "BackgroundPixelValue":
			return (0, self.dataUnit.getSourceDataUnits()[0].getDataSource().getScalarRange()[1])

	def getType(self, parameter):
		"""
		Created: 14.03.2007, KP
		Description: Return the type of the parameter
		"""
		if parameter == "FixedTimepoint":
			return GUIBuilder.SLICE
		if parameter == "BackgroundPixelValue":
			return GUIBuilder.SLICE
		if parameter == "MaxStepLength":
			return types.FloatType
		if parameter == "MinStepLength":
			return types.FloatType
		if parameter == "UsePreviousAsFixed":
			return types.BooleanType
		
		return types.IntType
			 
	def getParameters(self):
		"""
		Created: 14.03.2007, KP
		Description: Return the list of parameters needed for configuring this GUI
		"""            
		return [["Fixed image", ("UsePreviousAsFixed","FixedTimepoint")], ["", ("BackgroundPixelValue",)], ["Accuracy and speed settings", ("MaxIterations","MaxStepLength","MinStepLength")]]

	def setParameter(self, parameter, value):
		"""
		Created: 23.1.2008, LP
		Description: Set value of parameter
		"""
		lib.ProcessingFilter.ProcessingFilter.setParameter(self,parameter,value)
		if parameter == "UsePreviousAsFixed" and self.gui:
			item = self.gui.items["FixedTimepoint"]
			if self.getParameter(parameter):
				for c in item.GetChildren():
					c.Show(False)
			else:
				for c in item.GetChildren():
					c.Show(True)
			self.gui.sizer.Layout()


def getFilters():
    """
    Created: 10.8.2007, SS
    Description: This function returns all the filter-classes in this module and is used by ManipulationFilters.getFilterList()
    """
    return []
