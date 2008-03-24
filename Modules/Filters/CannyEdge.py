#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: CannyEdge
 Project: BioImageXD
 Created: 10.12.2007, LP
 Description:

 A module that contains dynamic threshold filter for the processing task.
 
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
import scripting
import types
import GUI.GUIBuilder
import itk
import lib.FilterTypes

class CannyEdgeFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	A class that uses the ITK canny edge detection filter
	"""		
	name = "Canny edge detection"
	category = lib.FilterTypes.FEATUREDETECTION
	
	def __init__(self, inputs = (1, 1)):
		"""
		Initialization
		"""
		lib.ProcessingFilter.ProcessingFilter.__init__(self, inputs)
		self.itkFlag = 1
		self.itkfilter = None
		self.eventDesc = "Performing edge detection (canny edge)"
		
	def getParameterLevel(self, parameter):
		"""
		Return the level of the given parameter
		"""
		return scripting.COLOR_EXPERIENCED
		
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
		image = self.convertVTKtoITK(image,types.FloatType)
		if not self.itkfilter:
			self.itkfilter = itk.CannyEdgeDetectionImageFilter[image, image].New()

		self.itkfilter.SetInput(image)

		# Output data is 0.0 or 1.0, rescale this
		rescale = itk.RescaleIntensityImageFilter.IF3IUC3.New()
		rescale.SetOutputMinimum(0)
		rescale.SetOutputMaximum(255)
		rescale.SetInput(self.itkfilter.GetOutput())
		data = rescale.GetOutput()
		# Update filter everytime
		data.Update()
		print "Got data=",data

		
		return data