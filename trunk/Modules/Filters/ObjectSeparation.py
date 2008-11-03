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
import time
import types
import itk

class ObjectSeparationFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	"""
	name = "Object separation"
	category = lib.FilterTypes.WATERSHED
	level = scripting.COLOR_BEGINNER

	def __init__(self, inputs = (1,1)):
		"""
		"""
		lib.ProcessingFilter.ProcessingFilter.__init__(self, inputs)
		self.descs = {"Level": "Segmentation Level", "Threshold": "Remove objects with less voxels than:"}
		self.itkFlag = 1

		self.ctf = None
		self.origCTF = None
		self.distance = None
		self.mws = None
		self.mask = None
		self.relabel = None
		self.ignoreObjects = 1

	def getDefaultValue(self, parameter):
		"""
		"""
		if parameter == "Level":
			return 1
		return 0

	def getType(self, parameter):
		"""
		"""
		if parameter == "Threshold":
			return types.IntType
		return types.FloatType

	def getParameters(self):
		"""
		"""
		return [["", ("Level",)], ["Minimum object size (in voxels)", ("Threshold",)]]

	def onRemove(self):
		"""
		"""
		if self.origCTF:
			self.dataUnit.getSettings().set("ColorTransferFunction", self.origCTF)
			self.ctf = None

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

		# Create new filters
		invert = itk.InvertIntensityImageFilter[image,image].New()
		distance = itk.DanielssonDistanceMapImageFilter[image,image].New()
		#self.distance = itk.DanielssonDistanceMapImageFilter[image,image].New()
		invdistance = itk.InvertIntensityImageFilter[image,image].New()
		mws = itk.MorphologicalWatershedImageFilter[image,ul].New()
		#self.mws = itk.MorphologicalWatershedImageFilter[image,ul].New()

		# Set parameters
		mws.SetLevel(self.parameters["Level"])
		#self.mws.SetLevel(self.parameters["Level"])

		# Setup pipeline
		invert.SetInput(image)
		#self.distance.SetInput(invert.GetOutput())
		distance.SetInput(invert.GetOutput())
		#invdistance.SetInput(self.distance.GetOutput())
		invdistance.SetInput(distance.GetOutput())
		mws.SetInput(invdistance.GetOutput())
		#self.mws.SetInput(invdistance.GetOutput())
		data = mws.GetOutput()
		#data = self.mws.GetOutput()

		# Execute object separation
		starttime = time.time()
		data.Update()
		endtime = time.time()
		print "Object separation took", endtime - starttime, "seconds"

		# Mask and relabel objects
		self.eventDesc = "Relabeling objects"
		mask = itk.MaskImageFilter[data,image,data].New()
		relabel = itk.RelabelComponentImageFilter[data,data].New()
		relabel.SetMinimumObjectSize(self.parameters["Threshold"])
		
		mask.SetInput1(data)
		mask.SetInput2(image)
		relabel.SetInput(mask.GetOutput())
		data = relabel.GetOutput()
		#self.mask = itk.MaskImageFilter[data,image,data].New()
		#self.relabel = itk.RelabelComponentImageFilter[data,data].New()
		#self.relabel.SetMinimumObjectSize(self.parameters["Threshold"])
		
		#self.mask.SetInput1(data)
		#self.mask.SetInput2(image)
		#self.relabel.SetInput(self.mask.GetOutput())
		#data = self.relabel.GetOutput()		
		data.Update()

		# Create ctf for objects
		self.eventDesc = "Create CTF for objects"
		n = relabel.GetNumberOfObjects()
		#n = self.relabel.GetNumberOfObjects()
		settings = self.dataUnit.getSettings()
		ncolors = settings.get("PaletteColors")
		if not self.ctf or not ncolors or ncolors < n:
			self.ctf = lib.ImageOperations.watershedPalette(1, n)
			
		self.origCTF = self.dataUnit.getColorTransferFunction()
		settings.set("ColorTransferFunction", self.ctf)
		settings.set("PaletteColors", n)

		return data
