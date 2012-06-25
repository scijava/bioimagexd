# -*- coding: iso-8859-1 -*-
"""
 Unit: OtsuMultipleThresholds.py
 Project: BioImageXD
 Created: 3.11.2008, LP
 Description:

 A module containing the Otsu multiple thresholds filter for the processing
 task.
							
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
__author__ = "BioImageXD Project <http://www.bioimagexd.net/>"
__version__ = "$Revision$"
__date__ = "$Date$"

import lib
import itk
import types
import scripting

class OtsuMultipleThresholdsFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	"""
	name = "Otsu multiple thresholds"
	category = lib.FilterTypes.THRESHOLDING
	level = scripting.COLOR_EXPERIENCED

	def __init__(self, inputs = (1,1)):
		"""
		Initialization
		"""
		lib.ProcessingFilter.ProcessingFilter.__init__(self,inputs)
		self.descs = {"NumberOfThresholds": "Number of thresholds"}
		self.itkFlag = 1
		self.itkfilter = None
		self.filterDesc = "Automatically finds thresholds that separate the image pixels/voxels into the desired number of classes by maximazing the variance between them\nInput: Grayscale image\nOutput: Label image";

	def getDefaultValue(self, parameter):
		"""
		Return default value of parameter
		"""
		if parameter == "NumberOfThresholds":
			return 2

	def getType(self, parameter):
		"""
		Return type of parameter
		"""
		if parameter == "NumberOfThresholds":
			return types.IntType

	def getParameters(self):
		"""
		Return parameters for GUI
		"""
		return [["", ("NumberOfThresholds",)]]

	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute filter
		"""
		if not lib.ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None

		image = self.getInput(1)
		image = self.convertVTKtoITK(image)

		self.itkfilter = itk.OtsuMultipleThresholdsImageFilter[image,image].New()
		self.itkfilter.SetInput(image)
		self.itkfilter.SetNumberOfThresholds(self.parameters["NumberOfThresholds"])
		data = self.itkfilter.GetOutput()
		data.Update()

		return data
