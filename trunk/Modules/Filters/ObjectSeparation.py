#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: ObjectSeparation.py
 Project: BioImageXD
 Description:

A module that uses morphological watershed segmentation to separate touching
objects.
 
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

import lib.ProcessingFilter
import lib.FilterTypes
import scripting
import types
import itk
import time
import os.path

class ObjectSeparationFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	"""
	name = "Object separation"
	category = lib.FilterTypes.OBJECT
	level = scripting.COLOR_BEGINNER

	def __init__(self, inputs = (1,1)):
		"""
		"""
		lib.ProcessingFilter.ProcessingFilter.__init__(self, inputs)
		self.descs = {"Level": "Segmentation level", "ImageSpacing": "Use image spacing", "Threshold": "Remove objects with less voxels than:"}
		self.itkFlag = 1

		self.origCtf = None
		self.data = None
		self.ignoreObjects = 1

	def getDefaultValue(self, parameter):
		"""
		"""
		if parameter == "Level":
			return 1
		if parameter == "ImageSpacing":
			return True
		return 0

	def getType(self, parameter):
		"""
		"""
		if parameter == "Threshold":
			return types.IntType
		if parameter == "ImageSpacing":
			return types.BooleanType
		return types.FloatType

	def getParameters(self):
		"""
		"""
		return [["", ("Level",)], ["", ("ImageSpacing",)], ["Minimum object size (in voxels)", ("Threshold",)]]

	def onRemove(self):
		"""
		Callback for when filter is removed
		"""
		self.restoreCtf()

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
		Execute filter using the input and return the output
		"""
		if not lib.ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None

		image = self.getInput(1)
		image = self.convertVTKtoITK(image)
		dim = image.GetLargestPossibleRegion().GetImageDimension()
		typestr = "itk.Image.UL%d"%dim
		ul = eval(typestr)
		self.eventDesc = "Performing object separation procedure"

		starttime = time.time()
		# Create new filters
		invert = itk.InvertIntensityImageFilter[image,image].New()
		distance = itk.DanielssonDistanceMapImageFilter[image,image].New()
		invdistance = itk.InvertIntensityImageFilter[image,image].New()

		# Setup pipeline
		invert.SetInput(image)
		distance.SetInput(invert.GetOutput())
		distance.SetUseImageSpacing(self.parameters["ImageSpacing"])
		invdistance.SetInput(distance.GetOutput())
		# Take inverted distance result and remove earlier filter for saving
		# some memory
		data = invdistance.GetOutput()
		data.Update()
		del invert
		del distance
		del invdistance

		mws = itk.MorphologicalWatershedImageFilter[data,ul].New()
		mws.SetLevel(int(self.parameters["Level"]))
		mws.SetInput(data)
		data = mws.GetOutput()

		# Execute object separation
		data.Update()
		endtime = time.time()
		print "Object separation took", endtime - starttime, "seconds"
		del mws

		# Mask and relabel objects
		self.eventDesc = "Relabeling objects"
		mask = itk.MaskImageFilter[data,image,data].New()
		relabel = itk.RelabelComponentImageFilter[data,data].New()
		relabel.SetMinimumObjectSize(self.parameters["Threshold"])

		mask.SetInput1(data)
		mask.SetInput2(image)
		relabel.SetInput(mask.GetOutput())
		data = relabel.GetOutput()
		data.Update()

		# Create ctf for objects
		self.eventDesc = "Create CTF for objects"
		n = relabel.GetNumberOfObjects()
		print "Number of objects",n
		settings = self.dataUnit.getSettings()
		ncolors = settings.get("PaletteColors")
		if not self.origCtf or not ncolors or ncolors < n:
			ctf = lib.ImageOperations.watershedPalette(1, n, ignoreColors = 1)
			if not self.origCtf:
				self.origCtf = self.dataUnit.getColorTransferFunction()
			self.data = data
			settings.set("ColorTransferFunction", ctf)
			settings.set("PaletteColors", n)

		return data
