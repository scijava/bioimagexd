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


import types
import vtk
import lib.Command
import sys
import Logging
import lib.messenger
import scripting

import GUI.GUIBuilder

class ProcessingFilter:
	"""
	Created: 13.04.2006, KP
	Description: A base class for manipulation filters
	"""
	category = "No category"
	name = "Generic Filter"
	level = scripting.COLOR_EXPERIENCED

	def __init__(self, numberOfInputs = (1, 1), changeCallback = None):
		"""
		Created: 13.04.2006, KP
		Description: Initialization
		"""
		self.taskPanel = None
		self.dataUnit = None
		self.processInputText = "Input from procedure list"

		self.initialization = True
		self.numberOfInputs = numberOfInputs
		self.descs = {}
		self.dataUnit = None 
		self.initDone = 0
		self.parameters = {}
		self.inputMapping = {}
		self.sourceUnits = []
		self.inputs = []
		self.inputIndex = 0
		self.gui = None
		if not changeCallback:
			self.modCallback = self.notifyTaskPanel
		else:
			self.modCallback = changeCallback
		self.updateDefaultValues()

		self.noop = 0
		self.parameters = {}
		self.gui = None
		self.resultVar = {}
		self.resultVariables = {}
		self.ignoreObjects = 0
		self.inputIndex = 0
		self.inputs = []
		self.nextFilter = None
		self.prevFilter = None
		self.enabled = 1
		self.itkFlag = 0
		self.imageType = "UC3"
		for item in self.getPlainParameters():
			self.setParameter(item, self.getDefaultValue(item))
		chmin, chmax = numberOfInputs
		for i in range(1, chmax+1):
			self.setInputChannel(i, i-1)
		self.vtkToItk = None
		self.itkToVtk = None
		self.executive = None
		self.eventDesc = ""
		self.replacementColorTransferFunction = None
		
		# self.itk = 0
		
	def resetFilters(self):
		"""
		Created: 08.01.2008, KP
		Description: reset the filter instances
		"""
		self.itkfilter = None
		self.relabelFilter = None

	def setInitialization(self, flag):
		"""
		Created: 07.12.2007, KP
		Description: toggle a flag indicating, whether the filter should be re-initialized
		"""
		self.initialization = flag
		
	def getColorTransferFunction(self):
		"""
		Created: 08.12.2007, KP
		Description: return a color transfer function that is modified by this filter, or
					 None, if the ctf doesn't need to be modified
		"""
		return self.replacementColorTransferFunction
		
	def getResultVariables(self):
		"""
		Created: 20.11.2007, KP
		Description: return the result variables of this filter
		"""
		return self.resultVariables.keys()
		
	def setResultVariable(self, variable, value):
		"""
		Created: 20.11.2007, KP
		Description: set a result variable to a value
		"""
		if variable not in self.getResultVariables():
			raise Exception("No such result variable '%s'"%(variable))
		self.resultVar[variable] = value
		
	def getResultVariable(self, variable):
		"""
		Created: 20.11.2007, KP
		Description: return a value of a result variable
		"""
		return self.resultVar.get(variable, None)
		
	def getResultVariableDesc(self, variable):
		"""
		Created: 27.11.2007, KP
		Description: return the description of a result variable
		"""
		return self.resultVariables.get(variable,"")
		
	def getEventDesc(self):
		"""
		Created: 08.11.2007, KP
		Description: return a string describing the event being currently executed
		"""
		if self.eventDesc:
			return self.eventDesc
		return "Performing %s"%self.name
		
	def setExecutive(self, executive):
		"""
		Created: 08.11.2007, KP
		Description: set the object controlling the execution of this filter
		"""
		self.executive = executive

	def onRemove(self):
		"""
		Created: 25.1.2007, KP
		Description: Callback for when the filter is removed
		"""
		pass

	def updateProgress(self, obj, evt):
		"""
		Created: 13.07.2004, KP
		Description: Sends progress update event
		"""
		if self.executive:
			if self.itkFlag:
				self.executive.updateITKProgress(obj.GetNameOfClass(), obj.GetProgress())
			else:
				self.executive.updateProgress(obj, evt)

	def set(self, parameter, value):
		"""
		Created: 21.07.2006, KP
		Description: Set the given parameter to given value
		"""
		self.parameters[parameter] = value
		if self.modCallback:
			self.modCallback(self)
		# Send a message that will update the GUI
		lib.messenger.send(self, "set_%s" % parameter, value)

	def setParameter(self, parameter, value):
		"""
		Created: 13.04.2006, KP
		Description: Set a value for the parameter
		"""
		if self.taskPanel:
			listOfFilters = self.taskPanel.filterEditor.getFilters(self.name)
			filterIndex = listOfFilters.index(self)
			if len(listOfFilters) == 1:
				func = "getFilter('%s')" % self.name
			else:
				func = "getFilter('%s', %d)" % (self.name, filterIndex)
			n = scripting.mainWindow.currentTaskWindowName
			method="scripting.mainWindow.tasks['%s'].filterEditor.%s"%(n,func)
			self.recordParameterChange(parameter, value, method)
		self.parameters[parameter] = value
		if self.modCallback:
			self.modCallback(self)
			
	def getParameter(self, parameter):
		"""
		Created: 29.05.2006, KP
		Description: Get a value for the parameter
		"""	   
		return self.parameters.get(parameter, None)

			
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
		if self.taskPanel:
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
		try:
			import itk
		except ImportError:
			print "Could not import ITK, terminating."
			sys.exit()
		# self.itk = 1
		
		if "itkImage" in str(image.__class__):
			return image
		if not self.itkFlag:
			lib.messenger.send(None, "show_error", "Non-ITK filter tries to convert to ITK",
				"A non-ITK filter %s tried to convert data to ITK image data" % self.name)
			return image

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
				conv.SetOutputScalarTypeToUnsignedLong()
				image = conv.GetOutput()
			elif scalarType == "unsigned short":
				ImageType = itk.VTKImageToImageFilter.IUS3
			else:
				ImageType = itk.VTKImageToImageFilter.IUC3

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

	def convertITKtoVTK(self, image, cast = None, force = 0):
		"""
		Created: 18.04.2006, KP
		Description: Convert the ITK image data to VTK image
		"""
		# For non-ITK images, do nothing
		if image.__class__ == vtk.vtkImageData:
			return image

		del self.itkToVtk
		
		try:
			import itk
		except ImportError:
			print "Could not import ITK, terminating."
			sys.exit()
			
		self.itkToVtk = itk.ImageToVTKImageFilter[image].New()
		# If the next filter is also an ITK filter, then won't
		# convert
		if not force and self.nextFilter and self.nextFilter.getITK():
			return image
		self.itkToVtk.SetInput(image)
		self.itkToVtk.Update()

		if cast:
			icast = vtk.vtkImageCast()
			if cast == "UC3":
				icast.SetOutputScalarTypeToUnsignedChar()
			elif cast == "US3":
				icast.SetOutputScalarTypeToUnsignedShort()
			icast.SetInput(self.itkToVtk.GetOutput())
			icast.Update()
			return icast.GetOutput()

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
		self.sourceUnits = []
		self.resetFilters()
		self.updateDefaultValues()
			
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
			GUIBuilder = GUI.GUIBuilder.getGUIBuilderForFilter(self)
			self.gui = GUIBuilder(parent, self)
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

	def getSelectedInputChannelNames(self):
		"""
		Created: 07.12.2007, KP
		Description: return the names of the selected input channels
		"""
		oldText = self.processInputText
		self.processInputText = "output"
		inputChannels = self.getInputChannelNames()
		keys = self.inputMapping.keys()
		returnNames = []
		
		for chIndex in self.inputMapping.values():
			returnNames.append(inputChannels[chIndex])
			
		self.processInputText = oldText
		return returnNames
		
		
	def getInputChannelNames(self, fromStack = 1):
		"""
		Created: 07.12.2007, KP
		Description: return the names of the input channels
		"""
		if fromStack:
			choices = [self.processInputText]
		else:
			choices = []
		# If the input is a processed dataunit, i.e. output from a task,
		# then we offer both the task output and the individual channels
		if self.dataUnit.isProcessed():
			for i, dataunit in enumerate(self.dataUnit.getSourceDataUnits()):
				choices.append(dataunit.getName())
		else:
			# If we have a non - processed dataunit (i.e. a single channel)
			# as input, then we only offer that
			choices = [self.dataUnit.getName()]
		return choices
		
	def getInputChannel(self, mapIndex):
		"""
		Created: 07.12.2007, KP
		Description: return the index of the channel tht corresponds to given input number
		"""
		if mapIndex not in self.inputMapping:
			self.setInputChannel(mapIndex, mapIndex-1)
		return self.inputMapping[mapIndex]
		
	def getInput(self, mapIndex):
		"""
		Created: 17.04.2006, KP
		Description: Return the input imagedata #n
		"""
		if not self.dataUnit:
			self.dataUnit = scripting.combinedDataUnit
		# By default, asking for say, input number 1 gives you 
		# the first (0th actually) input mapping
		# these can be thought of as being specified in the GUI where you have as many 
		# selections of input data as the filter defines (with the variable numberOfInputs)
		if mapIndex not in self.inputMapping:
			self.setInputChannel(mapIndex, mapIndex-1)
			
		# Input mapping 0 means to return the input from the filter stack above
		
		if self.inputMapping[mapIndex] == 0 and self.dataUnit and self.dataUnit.isProcessed():
			try:
				image = self.inputs[self.inputIndex]
			except:
				traceback.print_exc()
				Logging.info("No input with number %d" %self.inputIndex, self.inputs, kw = "processing")
		else:
			# If input from stack is not requested, or the dataunit is not processed, then just return 
			# the image data from the corresponding channel
			Logging.info("Using input from channel %d as input %d" % (self.inputMapping[mapIndex] - 1, mapIndex), \
							kw = "processing")
			
			image = self.getInputFromChannel(self.inputMapping[mapIndex] - 1)
		return image
		
	def getInputDataUnit(self, mapIndex):
		"""
		Created: 12.03.2007, KP
		Description: Return the input dataunit for input #n
		"""	  
		if mapIndex not in self.inputMapping:
			return None
		if self.inputMapping[mapIndex] == 0 and self.dataUnit and self.dataUnit.isProcessed():
			return self.dataUnit
		else:
			dataunit = self.getInputFromChannel(self.inputMapping[mapIndex] - 1, dataUnit = 1)
		return dataunit
		
	def getCurrentTimepoint(self):
		"""
		Created: 14.03.2007, KP
		Description: return the current timepoint 
		"""
		timePoint = scripting.visualizer.getTimepoint()
		if scripting.processingTimepoint != -1:
			timePoint = scripting.processingTimepoint
		return timePoint
		
	def getInputFromChannel(self, unitIndex, timepoint = -1, dataUnit = 0):
		"""
		Created: 17.04.2006, KP
		Description: Return an imagedata object that is the current timepoint for channel #n
		"""
		if self.dataUnit.isProcessed():
			if not self.sourceUnits:
				self.sourceUnits = self.dataUnit.getSourceDataUnits()
		else:
			self.sourceUnits = [self.dataUnit]
				
		currentTimePoint = scripting.visualizer.getTimepoint()
		if scripting.processingTimepoint != -1:
			currentTimePoint = scripting.processingTimepoint
		if timepoint != -1:
			currentTimePoint = timepoint
		if dataUnit:
			return self.sourceUnits[unitIndex]

		return self.sourceUnits[unitIndex].getTimepoint(currentTimePoint)
		
	def updateDefaultValues(self):
		"""
		Created: 08.11.2007, KP
		Description: update the default values
		"""
		if not self.initialization:
			return
		self.initDone = 0
		for item in self.getPlainParameters():
			self.setParameter(item, self.getDefaultValue(item))
		self.initDone = 1
		
	def getNumberOfInputs(self):
		"""
		Created: 17.04.2006, KP
		Description: Return the number of inputs required for this filter
		"""
		return self.numberOfInputs
		
	def setInputChannel(self, inputNumber, channel):
		"""
		Created: 17.04.2006, KP
		Description: Set the input channel for input #inputNum
		"""

		self.inputMapping[inputNumber] = channel
		
	def getInputName(self, n):
		"""
		Created: 17.04.2006, KP
		Description: Return the name of the input #n
		"""
		return "Source dataset %d" % n
		
	def getParameterLevel(self, parameter):
		"""
		Created: 1.11.2006, KP
		Description: Return the level of the given parameter. This is used to color code the GUI options
		"""
		return scripting.COLOR_BEGINNER
			
	def sendUpdateGUI(self, parameters = []):
		"""
		Created: 05.06.2006, KP
		Description: Method to update the GUI elements that correspond to the parameters
					 If a list of parameters is defined, then only those gui entries are updated.
		"""
		if not parameters:
			parameters = self.getPlainParameters()
		for item in parameters:
			value = self.getParameter(item)
			lib.messenger.send(self, "set_%s" % item, value)
			
			
	def canSelectChannels(self):
		"""
		Created: 31.05.2006, KP
		Description: Should it be possible to select the channel
		"""
		return 1
	
	def getParameters(self):
		"""
		Created: 13.04.2006, KP
		Description: Return the list of parameters needed for configuring this GUI
		"""	 
		return []
	
	def getPlainParameters(self):
		"""
		Created: 15.04.2006, KP
		Description: Return whether this filter is enabled or not
		"""
		returnList = []
		for item in self.getParameters():
			# If it's a label, then ignore it
			if type(item) == types.StringType:
				continue
			# if it's a list type, then add each parameter in the list to the list of plain parameters
			elif type(item) == types.ListType:
				title, items = item
				if type(items[0]) == types.TupleType:
					items = items[0]
				returnList.extend(items)
		return returnList
		
	def recordParameterChange(self, parameter, value, modpath):
		"""
		Created: 14.06.2007, KP
		Description: record the change of a parameter along with information for how to undo it
		"""
		oldval = self.parameters.get(parameter, None)
		if oldval == value:
			return
		if self.getType(parameter) == GUI.GUIBuilder.ROISELECTION:
			i, roi = value
			setval = "scripting.visualizer.getRegionsOfInterest()[%d]" % i
			rois = scripting.visualizer.getRegionsOfInterest()
			if oldval in rois:
				n = rois.index(oldval)
				setoldval = "scripting.visualizer.getRegionsOfInterest()[%d]" % n
			else:
				setoldval = ""
			value = roi
		else:
			if type(value) in [types.StringType, types.UnicodeType]:
	
				setval = "'%s'" % value
				setoldval = "'%s'" % oldval
			else:
				setval = str(value)
				setoldval = str(oldval)
		n = scripting.mainWindow.currentTaskWindowName
		do_cmd = "%s.set('%s', %s)" % (modpath, parameter, setval)
		if oldval and setoldval:
			undo_cmd = "%s.set('%s', %s)" % (modpath, parameter, setoldval)
		else:
			undo_cmd = ""
		cmd = lib.Command.Command(lib.Command.PARAM_CMD, None, None, do_cmd, undo_cmd, \
									desc = "Change parameter '%s' of filter '%s'" % (parameter, self.name))
		cmd.run(recordOnly = 1)
		
	def getDesc(self, parameter):
		"""
		Created: 13.04.2006, KP
		Description: Return the description of the parameter
		"""	   
		return self.descs.get(parameter,"")
		
	def getLongDesc(self, parameter):
		"""
		Created: 13.04.2006, KP
		Description: Return the long description of the parameter
		"""	   
		return ""
		
	def getType(self, parameter):
		"""
		Created: 13.04.2006, KP
		Description: Return the type of the parameter
		"""	   
		return types.IntType
		
	def getRange(self, parameter):
		"""
		Created: 31.05.2006, KP
		Description: If a parameter has a certain range of valid values, the values can be queried with this function
		"""
		return -1, -1
		
	def getDefaultValue(self, parameter):
		"""
		Created: 13.04.2006, KP
		Description: Return the default value of a parameter
		"""
		return 0
