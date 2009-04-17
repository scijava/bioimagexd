#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
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
import lib.FilterTypes
import scripting
import itk
import types
import time
import Logging

class MorphologicalWatershedFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	A filter for performing the ITK morphological watershed segmentation
	"""
	name = "Morphological watershed segmentation"
	category = lib.FilterTypes.WATERSHED
	level = scripting.COLOR_BEGINNER
	
	def __init__(self, inputs = (1, 1)):
		"""
		Initialization
		"""   
		lib.ProcessingFilter.ProcessingFilter.__init__(self, inputs, requireWholeDataset = 1)
		self.descs = {"Level": "Segmentation Level", "MarkWatershedLine": "Mark the watershed line",
		"Threshold": "Remove objects with less voxels than:"}
		self.itkFlag = 1
		self.origCtf = None
		self.n = 0
		self.ignoreObjects = 2
		self.relabelFilter	= None
		self.itkfilter = None
		self.data = None

	def getParameterLevel(self, parameter):
		"""
		Return the level of the given parameter
		"""
		if parameter in ["Threshold", "Level"]:
			return scripting.COLOR_INTERMEDIATE
		
		return scripting.COLOR_BEGINNER
			
	def getDefaultValue(self, parameter):
		"""
		Return the default value of a parameter
		"""	   
		if parameter == "Level":
			return 5
		return 0
		
	def getType(self, parameter):
		"""
		Return the type of the parameter
		"""	   
		if parameter == "MarkWatershedLine":
			return types.BooleanType
		return types.FloatType
			 
		
	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""			   
		return [["", ("Level", "MarkWatershedLine")], ["Minimum object size (in pixels)", ("Threshold", )]]

	def onRemove(self):
		"""
		Callback for when filter is removed
		"""
		self.restoreCtf()
		if self.itkfilter:
			del self.itkfilter
		if self.relabelFilter:
			del self.relabelFilter
		if self.vtkToItk:
			del self.vtkToItk

	def onDisable(self):
		"""
		Callback for when filter is disabled
		"""
		self.restoreCtf()

	def restoreCtf(self):
		"""
		Restore palette to the state before using this module
		"""
		if self.origCtf:
			self.dataUnit.getSettings().set("ColorTransferFunction", self.origCtf)
		self.origCtf = None		
	
	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute the filter with given inputs and return the output
		"""
		if not lib.ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None
			
		image = self.getInput(1)
		image = self.convertVTKtoITK(image)
		dim = image.GetLargestPossibleRegion().GetImageDimension()
		if not self.itkfilter:
			try:
				typestr = "itk.Image.UL%d"%dim
				ul = eval(typestr)
				self.itkfilter = itk.MorphologicalWatershedImageFilter[image, ul].New()
			except:
				Logging.info("Failed to get MorphologicalWatershedImageFilter, trying watershed module")
				Logging.traceback.print_exc()
				import watershed
				self.itkfilter = watershed.MorphologicalWatershedImageFilter[image, ul].New()
		
		markWatershedLine = self.parameters["MarkWatershedLine"]
		self.itkfilter.SetMarkWatershedLine(markWatershedLine)

		t = time.time()
		self.eventDesc = "Performing morphological watershed segmentation"
		self.itkfilter.SetInput(image)
		Logging.info("Using watershed level %.3f"%self.parameters["Level"])
		self.itkfilter.SetLevel(self.parameters["Level"])
		
		self.setImageType("UL%d"%dim)
		self.itkfilter.Update()
		print "Morphological watershed took", time.time() - t, "seconds"
		t = time.time()
		data = self.itkfilter.GetOutput()

		self.eventDesc = "Relabeling segmented image"
		
		if not self.relabelFilter:
			self.relabelFilter = itk.RelabelComponentImageFilter[data, data].New()

		self.relabelFilter.SetInput(data)

		th = self.parameters["Threshold"]
		self.relabelFilter.SetMinimumObjectSize(th)
	
		data = self.relabelFilter.GetOutput()
		data.Update()

		print "Relabeling took", time.time()-t
		t = time.time()
		n = self.relabelFilter.GetNumberOfObjects()
		settings = self.dataUnit.getSettings()
		ncolors = settings.get("PaletteColors")
		
		if not self.origCtf or not ncolors or ncolors != n or not self.data or self.data != data:
			self.data = data
			ctf = lib.ImageOperations.watershedPalette(2, n)
			if markWatershedLine:
				ctf.AddRGBPoint(0, 1.0, 1.0, 1.0)
			if not self.origCtf:
				self.origCtf = self.dataUnit.getColorTransferFunction()
			settings.set("ColorTransferFunction", ctf)
			val = [0, 0, 0]
			ctf.GetColor(1, val)
			print "ctf value at 1 =", val, "n colors =", n
			settings.set("PaletteColors", n)

		print "Creating palette took",time.time()-t,"seconds"

		return data
