#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: ProcessingFilter
 Project: BioImageXD
 Created: 13.04.2006, KP
 Description:

 A module that contains the base class for various data processing filters used in the Process
 task and other task modules.

 Copyright (C) 2005	 BioImageXD Project
 See CREDITS.txt for details

 This program is free software; you can redistribute it and / or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program; if not, write to the Free Software
 Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111 - 1307	 USA

"""
__author__ = "BioImageXD Project < http://www.bioimagexd.org/>"
__version__ = "$Revision: 1.42 $"
__date__ = "$Date: 2005 / 01 / 13 14:52:39 $"

# import ImageOperations
# import wx

import types
import vtk
import lib.Command
import sys

MATH = "Image arithmetic"
SEGMENTATION = "Segmentation"
FILTERING = "Filtering"
ITK = "ITK"
LOGIC = "Logical operations"
MEASUREMENT = "Measurements"
REGION_GROWING = "Region growing"
FEATUREDETECTION = "Feature detection"
TRACKING = "Tracking"
REGISTRATION = "Registration"

try:
	import itk
except ImportError:
	print "Could not import ITK, terminating."
	sys.exit()
import lib.messenger
import scripting
import GUI.GUIBuilder as GUIBuilder

class ProcessingFilter(GUIBuilder.GUIBuilderBase):
	"""
	Created: 13.04.2006, KP
	Description: A base class for manipulation filters
	"""
	category = "No category"
	name = "Generic Filter"
	level = scripting.COLOR_EXPERIENCED
	def __init__(self, numberOfInputs = (1, 1)):
		"""
		Created: 13.04.2006, KP
		Description: Initialization
		"""
		self.taskPanel = None
		self.dataUnit = None
		self.processInputText = "Input from procedure list"

		GUIBuilder.GUIBuilderBase.__init__(self, changeCallback = self.notifyTaskPanel)

		self.numberOfInputs = numberOfInputs
		self.noop = 0
		self.parameters = {}
		self.gui = None

		self.ignoreObjects = 0
		self.inputIndex = 0
		self.inputs = []
		self.nextFilter = None
		self.prevFilter = None
		self.itkToVtk = None
		self.enabled = 1
		self.itkFlag = 0
		self.imageType = "UC3"
		for item in self.getPlainParameters():
			self.setParameter(item, self.getDefaultValue(item))

		self.vtkToItk = None
		self.itkToVtk = None
		#self.G = "UC3"

	def onRemove(self):
		"""
		Created: 25.1.2007, KP
		Description: Callback for when the filter is removed
		"""
		pass

	def set(self, parameter, value):
		"""
		Created: 21.07.2006, KP
		Description: Set the given parameter to given value
		"""
		GUIBuilder.GUIBuilderBase.setParameter(self, parameter, value)
		# Send a message that will update the GUI
		lib.messenger.send(self, "set_%s" % parameter, value)

	def setParameter(self, parameter, value):
		"""
		Created: 13.04.2006, KP
		Description: Set a value for the parameter
		"""
		if self.taskPanel:
			listOfFilters = self.taskPanel.getFilters(self.name)
			print "Got filters",listOfFilters
			filterIndex = listOfFilters.index(self)
			if len(listOfFilters) == 1:
				func = "getFilter('%s')" % self.name
			else:
				func = "getFilter('%s', %d)" % (self.name, filterIndex)
			n = scripting.mainWindow.currentTaskWindowName
			method="scripting.mainWindow.tasks['%s'].%s"%(n,func)
			self.recordParameterChange(parameter, value, method)

		#print "\n\nSetting ",parameter,"to",value
		GUIBuilder.GUIBuilderBase.setParameter(self, parameter, value)

	def writeOutput(self, dataUnit, timePoint):
		"""
		Created: 09.07.2006, KP
		Description: Optionally write the output of this module during the processing
		"""
		pass

	def notifyTaskPanel(self, module):
		"""
		Created: 31.05.2006, KP
		Description: Notify the task panel that filter has changed
		"""
		if self.taskPanel:				# TODO: Is this method used at all? The parameter 'module' is not used.
			self.taskPanel.filterModified(self)

	def setImageType(self, imageType):
		"""
		Created: 15.05.2006, KP
		Description: Set the image type of the ITK image
		"""
		self.imageType = imageType

	def getImageType(self):
		"""
		Created: 15.05.2006, KP
		Description: Get the image type of the ITK image
		"""
		return self.imageType

	def setTaskPanel(self, taskPanel):
		"""
		Created: 14.05.2006, KP
		Description: Set the task panel that controls this filter
		"""
		self.taskPanel = taskPanel

	def convertVTKtoITK(self, image, cast = None):
		"""
		Created: 18.04.2006, KP
		Description: Convert the image data to ITK image
		"""
		if "itkImage" in str(image.__class__):
			return image
		if not self.itkFlag:
			lib.messenger.send(None, "show_error", "Non-ITK filter tries to convert to ITK",
				"A non-ITK filter %s tried to convert data to ITK image data" % self.name)
			return image

		#if not self.vtkToItk:
		ImageType = itk.VTKImageToImageFilter.IUC3

		if cast == types.FloatType:
			ImageType = itk.VTKImageToImageFilter.IF3
		elif not cast:
			scalarType = image.GetScalarTypeAsString()

			if scalarType == "unsigned char":
				ImageType = itk.VTKImageToImageFilter.IUC3
			elif scalarType == "unsigned int":
				conv = vtk.vtkImageCast()
				conv.SetInput(image)
				ImageType = itk.VTKImageToImageFilter.IUL3
				conv.SetOutputScalarTypeToUnsignedLong ()
				image = conv.GetOutput()
			elif scalarType == "unsigned short":
				ImageType = itk.VTKImageToImageFilter.IUS3

		self.vtkToItk = ImageType.New()

		#if self.prevFilter and self.prevFilter.getITK():
		#	 return image
		if cast:
			icast = vtk.vtkImageCast()
			if cast == types.FloatType:
				icast.SetOutputScalarTypeToFloat()
			icast.SetInput(image)
			image = icast.GetOutput()
		self.vtkToItk.SetInput(image)
		self.vtkToItk.Update()
		return self.vtkToItk.GetOutput()

	#def convertITKtoVTK(self, image, cast = None, imagetype = "UC3", force = 0):
	def convertITKtoVTK(self, image, imagetype = "UC3", force = 0):
		"""
		Created: 18.04.2006, KP
		Description: Convert the image data to ITK image
		"""
		# For non-ITK images, do nothing
		if image.__class__ == vtk.vtkImageData:
#		if not force and self.prevFilter and not self.prevFilter.getITK() and not self.getITK():
			return image
		#if not self.itkToVtk:
		#	 c=eval("itk.Image.%s"%imagetype)
		#	 self.itkToVtk = itk.ImageToVTKImageFilter[c].New()
		del self.itkToVtk
		self.itkToVtk = itk.ImageToVTKImageFilter[image].New()
		# If the next filter is also an ITK filter, then won't
		# convert
		if not force and self.nextFilter and self.nextFilter.getITK():
			print "NEXT FILTER IS ITK"
			return image
		self.itkToVtk.SetInput(image)
		self.itkToVtk.Update()
		return self.itkToVtk.GetOutput()
	def setNextFilter(self, nfilter):
		"""
		Created: 18.04.2006, KP
		Description: Set the next filter in the chain
		"""
		self.nextFilter = nfilter

	def setPrevFilter(self, pfilter):
		"""
		Created: 18.04.2006, KP
		Description: Set the previous filter in the chain
		"""
		self.prevFilter = pfilter

	def getITK(self):
		"""
		Created: 18.04.2006, KP
		Description: Return whether this filter is working on ITK side of the pipeline
		"""
		return self.itkFlag

	def getEnabled(self):
		"""
		Created: 13.04.2006, KP
		Description: Return whether this filter is enabled or not
		"""
		return self.enabled

	def setDataUnit(self, dataUnit):
		"""
		Created: 15.04.2006, KP
		Description: Set the dataunit that is the input of this filter
		"""
		self.dataUnit = dataUnit

	def getDataUnit(self):
		"""
		Created: 15.04.2006, KP
		Description: return the dataunit
		"""
		return self.dataUnit

	def setEnabled(self, flag):
		"""
		Created: 13.04.2006, KP
		Description: Set whether this filter is enabled or not
		"""
		print "Setting ", self, "to enabled = ", flag
		self.enabled = flag

	def getGUI(self, parent, taskPanel):
		"""
		Created: 13.04.2006, KP
		Description: Return the GUI for this filter
		"""
		self.taskPanel = taskPanel
		if not self.gui:
			self.gui = GUIBuilder.GUIBuilder(parent, self)
		return self.gui

	@classmethod
	def getName(cls):
		"""
		Created: 13.04.2006, KP
		Description: Return the name of the filter
		"""
		return cls.name

	@classmethod
	def getCategory(cls):
		"""
		Created: 13.04.2006, KP
		Description: Return the category this filter should be classified to
		"""
		return cls.category

	def execute(self, inputs):
		"""
		Created: 13.04.2006, KP
		Description: Execute the filter with given inputs and return the output
		"""
		self.inputs = inputs
		return 1
