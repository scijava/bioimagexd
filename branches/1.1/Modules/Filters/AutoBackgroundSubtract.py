#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: AutoBackgroundSubtract
 Project: BioImageXD
 Description:

 A module for automatically subtracting the background from an image
 
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
import lib.FilterTypes
import vtk

class AutoBackgroundSubtractFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	A filter for automatically subtracting the background from an image
	"""		
	name = "Automatic background subtraction"
	category = lib.FilterTypes.SUBTRACT
	level = scripting.COLOR_BEGINNER
	
	def __init__(self):
		"""
		Initialization
		"""		   
		lib.ProcessingFilter.ProcessingFilter.__init__(self, (1, 1))
		self.vtkfilter = vtk.vtkImageShiftScale()
		self.vtkfilter.AddObserver("ProgressEvent", lib.messenger.send)
		lib.messenger.connect(self.vtkfilter, 'ProgressEvent', self.updateProgress)
		self.eventDesc = "Applying an Automatic background subtraction"
		self.descs = {"SmallestNonZeroValue":"Use smallest non-zero value as background",
		"FirstPeak":"First peak in histogram","MostCommon":"Most common value"}
		self.filterDesc = "Removes background by subtracting a certain value from the intensity of every pixel/voxel\nInput: Grayscale image\nOutput: Grayscale image"
	
	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""			   
		return [["Subtract", (("SmallestNonZeroValue","FirstPeak","MostCommon"),("rows",3))]]
		
	def getLongDesc(self, parameter):
		"""
		Return a long description of the parameter
		""" 
		return ""
		
	def getType(self, parameter):
		"""
		Return the type of the parameter
		"""	   
		if parameter in ["SmallestNonZeroValue","FirstPeak", "MostCommon"]:
			return GUI.GUIBuilder.RADIO_CHOICE
		
	def getDefaultValue(self, parameter):
		"""
		Return the default value of a parameter
		"""
		if parameter == "MostCommon":
			return 1
		return 0
		
	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute the filter with given inputs and return the output
		"""
		if not lib.ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None

		image = self.getInput(1)
		self.vtkfilter.SetInput(image)
		self.vtkfilter.SetClampOverflow(1)
		image.Update()
		print "Getting scalar & histogram info"

		bitdepth = self.getInputDataUnit(1).getSingleComponentBitDepth()
		histogram = lib.ImageOperations.get_histogram(image, maxval = 2**bitdepth - 1, maxrange = 1)

		shift = 0
		if self.parameters["SmallestNonZeroValue"]:
			for i, value in enumerate(histogram):
				if i and value:
					shift = -i
					print "Found smallest non-zero value %d at %d"%(value,i)
					break
		elif self.parameters["FirstPeak"]:
			for i, value in enumerate(histogram):
				if i and histogram[i-1] <= value and histogram[i+1] < value:
					shift = -i
					print "Found first peak %d at %d"%(value, i)
					break
		elif self.parameters["MostCommon"]:
			commonest = -1
			count = 0
			for i, value in enumerate(histogram):
				if value > count: 
					commonest = i
					count = value
			print "The most common value = %d count = %d"%(commonest, count)
			shift = -commonest

		self.vtkfilter.SetShift(shift)
		self.vtkfilter.Update()
		print "New Scalar range=", self.vtkfilter.GetOutput().GetScalarRange()
		
#		if update:
#			self.vtkfilter.Update()
		return self.vtkfilter.GetOutput()	 
		
