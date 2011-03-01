#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: ProcessingFilter
 Project: BioImageXD
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
import itk
import lib.Command
import sys
import Logging
import lib.messenger
import scripting
import traceback

import GUI.GUIBuilder

class ProcessingFilter:
	"""
	A base class for manipulation filters
	"""
	category = "No category"
	name = "Generic Filter"
	level = scripting.COLOR_EXPERIENCED

	def __init__(self, numberOfInputs = (1, 1), changeCallback = None, requireWholeDataset = False):
		"""
		Initialization
		"""
		self.taskPanel = None
		self.dataUnit = None
		self.processInputText = "Input from procedure list"
		self.requireWholeDataset = requireWholeDataset
		self.initialization = True
		self.numberOfInputs = numberOfInputs
		self.descs = {}
		self.initDone = 0
		self.recordedParameters = {} # We keep another dictionary for recorded values
									 # so we can determine if we need to record a change or not
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

		self.itkToVtk = None
		self.vtkToItk = None
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
		self.executive = None
		self.eventDesc = ""
		self.replacementColorTransferFunction = None
		self.filterDesc = ""
		
		self.polyOutput = None
		self.polyInput = None
		
	def setPolyDataInput(self, polydata):
		"""
		Set the polydata input of this filter
		"""
		self.polyInput = polydata
		
	def setPolyDataOutput(self, polydata):
		"""
		Set the polydata output of this filter
		"""
		self.polyOutput = polydata
		
	def getPolyDataOutput(self):
		"""
		@return the polydata output
		"""
		return self.polyOutput
		
	def resetFilters(self):
		"""
		reset the filter instances
		"""
		self.itkfilter = None
		self.relabelFilter = None

	def setInitialization(self, flag):
		"""
		toggle a flag indicating, whether the filter should be re-initialized
		"""
		self.initialization = flag
		
	def getColorTransferFunction(self):
		"""
		return a color transfer function that is modified by this filter, or
					 None, if the ctf doesn't need to be modified
		"""
		return self.replacementColorTransferFunction
		
	def getResultVariables(self):
		"""
		@return the result variables of this filter
		"""
		return self.resultVariables.keys()
		
	def getResultVariableDict(self, tp = None):
		"""
		@return the result varible dictionar
		"""
		if tp is None:
			tp = self.getCurrentTimepoint()
		return self.resultVar.get(tp, None)
		
	def setResultVariable(self, variable, value, tp = None):
		"""
		set a result variable to a value
		"""
		if variable not in self.getResultVariables():
			raise Exception("No such result variable '%s'"%(variable))
		if tp is None:
			tp = self.getCurrentTimepoint()
		if not self.resultVar.has_key(tp):
			self.resultVar[tp] = {}
		
		self.resultVar[tp][variable] = value
		
	def getResultVariable(self, variable, tp = None):
		"""
		return a value of a result variable
		"""
		if tp is None:
			tp = self.getCurrentTimepoint()
		try:
			return self.resultVar.get(tp).get(variable, None)
		except:
			return None
		
	def getResultVariableDesc(self, variable):
		"""
		return the description of a result variable
		"""
		return self.resultVariables.get(variable,"")
		
	def getEventDesc(self):
		"""
		return a string describing the event being currently executed
		"""
		if self.eventDesc:
			return self.eventDesc
		return "Performing %s"%self.name
		
	def setExecutive(self, executive):
		"""
		set the object controlling the execution of this filter
		"""
		self.executive = executive

	def onRemove(self):
		"""
		Callback for when the filter is removed
		"""
		pass

	def onEnable(self):
		"""
		Callback for when the filter is set enabled
		"""
		pass

	def onDisable(self):
		"""
		Callback for when the filter is disabled
		"""
		pass

	def updateProgress(self, obj, evt):
		"""
		Sends progress update event
		"""
		if self.executive:
			if self.itkFlag:
				self.executive.updateITKProgress(obj.GetNameOfClass(), obj.GetProgress())
			else:
				self.executive.updateProgress(obj, evt)

	def set(self, parameter, value):
		"""
		Set the given parameter to given value
		"""
		self.parameters[parameter] = value
		if self.modCallback:
			self.modCallback(self)
		# Send a message that will update the GUI
		lib.messenger.send(self, "set_%s" % parameter, value)

	def setParameter(self, parameter, value):
		"""
		Set a value for the parameter
		"""
		if self.taskPanel:
			listOfFilters = self.taskPanel.filterEditor.getFilters(self.name)
			try:
				filterIndex = listOfFilters.index(self)
			except:
				print "Could not find myself in list",self
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
		Get a value for the parameter
		"""	   
		return self.parameters.get(parameter, None)

			
	def writeOutput(self, dataUnit, timePoint):
		"""
		Optionally write the output of this module during the processing
		"""
		pass

	def notifyTaskPanel(self, module):
		"""
		Notify the task panel that filter has changed
		"""
		if self.taskPanel:
			self.taskPanel.filterModified(self)

	def setImageType(self, imageType):
		"""
		Set the image type of the ITK image
		"""
		self.imageType = imageType

	def getImageType(self):
		"""
		Get the image type of the ITK image
		"""
		return self.imageType

	def setTaskPanel(self, taskPanel):
		"""
		Set the task panel that controls this filter
		"""
		self.taskPanel = taskPanel

	def convertVTKtoITK(self, image, cast = None):
		"""
		Convert the image data to ITK image
		"""
		if "itkImage" in str(image.__class__):
			return image
		
		if not self.itkFlag:
			lib.messenger.send(None, "show_error", "Non-ITK filter tries to convert to ITK",
				"A non-ITK filter %s tried to convert data to ITK image data" % self.name)
			return image

		extent = image.GetWholeExtent()
		if extent[5] - extent[4] == 0:
			dim = 2
		else:
			dim = 3

		if cast == types.FloatType:
			typestr = "itk.VTKImageToImageFilter.IF%d"%dim
			ImageType = eval(typestr)
			scalarType = "float"
		elif not cast:
			scalarType = image.GetScalarTypeAsString()

			if scalarType in ["unsigned int", "unsigned long", "unsigned long long"]:
				conv = vtk.vtkImageCast()
				conv.SetInput(image)
				typestr = "itk.VTKImageToImageFilter.IUL%d"%dim
				ImageType = eval(typestr)
				conv.SetOutputScalarTypeToUnsignedLong()
				image = conv.GetOutput()
			elif scalarType == "unsigned short":
				typestr = "itk.VTKImageToImageFilter.IUS%d"%dim
				ImageType = eval(typestr)
			elif scalarType == "float":
				typestr = "itk.VTKImageToImageFilter.IF%d"%dim
				ImageType = eval(typestr)
			else:
				typestr = "itk.VTKImageToImageFilter.IUC%d"%dim	
				ImageType = eval(typestr)
		else:
			typestr = "itk.VTKImageToImageFilter.IUC%d"%dim	
			ImageType = eval(typestr)

		Logging.info("Scalar type = %s"%scalarType)
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
		output = self.vtkToItk.GetOutput()
		output.Update()
			
		return output

	def convertITKtoVTK(self, image, cast = None, force = 0):
		"""
		Convert the ITK image data to VTK image
		"""
		# For non-ITK images, do nothing
		if image.__class__ == vtk.vtkImageData:
			return image

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
		Set the next filter in the chain
		"""
		self.nextFilter = nfilter

	def setPrevFilter(self, pfilter):
		"""
		Set the previous filter in the chain
		"""
		self.prevFilter = pfilter

	def getITK(self):
		"""
		Return whether this filter is working on ITK side of the pipeline
		"""
		return self.itkFlag

	def getEnabled(self):
		"""
		Return whether this filter is enabled or not
		"""
		return self.enabled

	def setDataUnit(self, dataUnit):
		"""
		Set the dataunit that is the input of this filter
		"""
		self.dataUnit = dataUnit
		self.sourceUnits = []
		self.resetFilters()
		self.updateDefaultValues()

	def getDataUnit(self):
		"""
		return the dataunit
		"""
		return self.dataUnit

	def setEnabled(self, flag):
		"""
		Set whether this filter is enabled or not
		"""
		self.enabled = flag

	def getGUI(self, parent, taskPanel):
		"""
		Return the GUI for this filter
		"""
		self.taskPanel = taskPanel
		if not self.gui:
			GUIBuilder = GUI.GUIBuilder.getGUIBuilderForFilter(self)
			self.gui = GUIBuilder(parent, self)
		return self.gui

	@classmethod
	def getName(cls):
		"""
		Return the name of the filter
		"""
		return cls.name

	@classmethod
	def getCategory(cls):
		"""
		Return the category this filter should be classified to
		"""
		return cls.category

	def execute(self, inputs):
		"""
		Execute the filter with given inputs and return the output
		"""
		self.inputs = inputs
		return 1

	def getSelectedInputChannelNames(self):
		"""
		return the names of the selected input channels
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
		return the names of the input channels
		"""
		if fromStack:
			choices = [self.processInputText]
		else:
			choices = []
		print "Choices=",self.dataUnit
		# If the input is a processed dataunit, i.e. output from a task,
		# then we offer both the task output and the individual channels
		if self.dataUnit.isProcessed():
			print self.dataUnit.getSourceDataUnits()
			for i, dataunit in enumerate(self.dataUnit.getSourceDataUnits()):
				choices.append(dataunit.getName())
		else:
			# If we have a non - processed dataunit (i.e. a single channel)
			# as input, then we only offer that
			choices = [self.dataUnit.getName()]
		return choices
		
	def getInputChannel(self, mapIndex):
		"""
		return the index of the channel tht corresponds to given input number
		"""
		if mapIndex not in self.inputMapping:
			self.setInputChannel(mapIndex, mapIndex-1)
		return self.inputMapping[mapIndex]
		
	def getInput(self, mapIndex):
		"""
		Return the input imagedata #n
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

	def getPolyDataInput(self, mapIndex):
		"""
		Return the input imagedata #n
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
				image = self.polyInput
			except:
				traceback.print_exc()
				Logging.info("No input with number %d" %self.inputIndex, self.inputs, kw = "processing")
		else:
			# If input from stack is not requested, or the dataunit is not processed, then just return 
			# the image data from the corresponding channel
			Logging.info("Using input from channel %d as input %d" % (self.inputMapping[mapIndex] - 1, mapIndex), \
							kw = "processing")
			
			image = self.getPolyDataInputFromChannel(self.inputMapping[mapIndex] - 1)
		return image
		
		
	def getInputDataUnit(self, mapIndex):
		"""
		Return the input dataunit for input #n
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
		return the current timepoint 
		"""
		if scripting.processingTimepoint != -1:
			timePoint = scripting.processingTimepoint
		else:
			timePoint = scripting.visualizer.getTimepoint()
		return timePoint
		
	def getNumberOfInputSourceUnits(self):
		"""
		Return the number of input source units
		"""
		return len(self.sourceUnits)
		
	def getInputFromChannel(self, unitIndex, timepoint = -1, dataUnit = 0):
		"""
		Return an imagedata object that is the current timepoint for channel #n
		"""
		if self.dataUnit.isProcessed():
			if not self.sourceUnits:
				self.sourceUnits = self.dataUnit.getSourceDataUnits()
		else:
			self.sourceUnits = [self.dataUnit]
				
		if scripting.processingTimepoint != -1:
			currentTimePoint = scripting.processingTimepoint
		else:
			currentTimePoint = scripting.visualizer.getTimepoint()

		if timepoint != -1:
			currentTimePoint = timepoint
		if dataUnit:
			return self.sourceUnits[unitIndex]

		return self.sourceUnits[unitIndex].getTimepoint(currentTimePoint)
		
	def getPolyDataInputFromChannel(self, unitIndex, timepoint = -1, dataUnit = 0):
		"""
		Return an imagedata object that is the current timepoint for channel #n
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

		return self.sourceUnits[unitIndex].getPolyDataAtTimepoint(currentTimePoint)
		
	def updateDefaultValues(self):
		"""
		update the default values
		"""
		if not self.initialization:
			return
		self.initDone = 0
		for item in self.getPlainParameters():
			defaultValue = self.getDefaultValue(item)
			self.setParameter(item,defaultValue)
		self.initDone = 1
		
	def getNumberOfInputs(self):
		"""
		Return the number of inputs required for this filter
		"""
		return self.numberOfInputs
		
	def setInputChannel(self, inputNumber, channel):
		"""
		Set the input channel for input #inputNum
		"""
		self.inputMapping[inputNumber] = channel
		
	def getInputName(self, n):
		"""
		Return the name of the input #n
		"""
		return "Source dataset %d" % n
		
	def getParameterLevel(self, parameter):
		"""
		Return the level of the given parameter. This is used to color code the GUI options
		"""
		return scripting.COLOR_BEGINNER
			
	def sendUpdateGUI(self, parameters = []):
		"""
		Method to update the GUI elements that correspond to the parameters
					 If a list of parameters is defined, then only those gui entries are updated.
		"""
		if not parameters:
			parameters = self.getPlainParameters()
		for item in parameters:
			value = self.getParameter(item)
			lib.messenger.send(self, "set_%s" % item, value)
			
			
	def canSelectChannels(self):
		"""
		Should it be possible to select the channel
		"""
		return 1
	
	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""	 
		return []
		
	def getPrecedingResultVariable(self, variable):
		"""
		@return the given result variable from any filter before this one
		@param variable The result variable to retrieve
		"""
		currentFilter = self.prevFilter
		while currentFilter:
			# Only retrieve variables from enabled filters
			if currentFilter.getEnabled():
				value = currentFilter.getResultVariable(variable)
				if value is not None:
					return value
			currentFilter = currentFilter.prevFilter
		return None
			
	def getPlainParameters(self):
		"""
		Return whether this filter is enabled or not
		"""
		returnList = []
		for item in self.getParameters():
			# If it's a label, then ignore it
			if type(item) == types.StringType:
				continue
			# if it's a list type, then add each parameter in the list to the list of plain parameters
			elif type(item) == types.ListType:
				title, items = item
				for curritem in items:
					toadd = curritem
					if type(curritem) == types.TupleType:
						returnList.extend(curritem)
					else:
						returnList.extend([curritem])
		return returnList
		
	def recordParameterChange(self, parameter, value, modpath):
		"""
		record the change of a parameter along with information for how to undo it
		"""
		oldval = self.recordedParameters.get(parameter, None)
		if oldval == value:
			return
		self.recordedParameters[parameter] = value
		if self.getType(parameter) == GUI.GUIBuilder.ROISELECTION:
			i, roi = value
			rois = scripting.visualizer.getRegionsOfInterest()
			if oldval in rois:
				n = rois.index(oldval)
				setoldval = "scripting.visualizer.getRegionsOfInterest()[%d]" % n
			else:
				setoldval = ""
			if len(rois) > i:
				setval = "scripting.visualizer.getRegionsOfInterest()[%d]" % i
			else:
				setval = ""
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
		Return the description of the parameter
		"""	   
		return self.descs.get(parameter,"")
		
	def getLongDesc(self, parameter):
		"""
		Return the long description of the parameter
		"""	   
		return ""
		
	def getType(self, parameter):
		"""
		Return the type of the parameter
		"""	   
		return types.IntType
		
	def getRange(self, parameter):
		"""
		If a parameter has a certain range of valid values, the values can be queried with this function
		"""
		return -1, -1
		
	def getDefaultValue(self, parameter):
		"""
		Return the default value of a parameter
		"""
		return 0

	def castITKImage(self, img, type):
		"""
		Casts ITK image to different type
		@parameter img Original image to be casted
		@parameter type itk.Image type of result image
		"""
		cast = itk.CastImageFilter[img,type].New()
		cast.SetInput(img)
		data = cast.GetOutput()
		data.Update()
		return data
	
	def getITKImageType(self, img):
		"""
		Return tuple of ITK image type in form (type,dim)
		"""
		dim = img.GetLargestPossibleRegion().GetImageDimension()
		type = ""
		imgClass = str(img.__class__)
		if "itkImageUC" in imgClass:
			type = "UC"
		elif "itkImageUS" in imgClass:
			type = "US"
		elif "itkImageUL" in imgClass:
			type = "UL"
		elif "itkImageF" in imgClass:
			type = "F"
		elif "itkImageD" in imgClass:
			type = "D"

		return (type,dim)

	def splitITKImageIntoSlices(self, image = None, true2D = False):
		"""
		Split ITK image to slices and return as list of slices
		"""
		if image is None:
			return None
		
		imageType = self.getITKImageType(image)
		size = image.GetLargestPossibleRegion().GetSize()
		extractRegion = itk.ImageRegion._3()
		extractSize = itk.Size._3()
		extractIndex = itk.Index._3()
		for i in range(3):
			extractSize[i] = size[i]
			extractIndex[i] = 0
		if true2D:
			extractSize[2] = 0
			dim = 2
		else:
			extractSize[2] = 1
			dim = 3

		sliceType = eval("itk.Image.%s%d"%(imageType[0],dim))
		slices = []
		for z in range(0, size[2]):
			extractRegion.SetSize(extractSize)
			extractIndex[2] = z
			extractRegion.SetIndex(extractIndex)
			if dim == 3:
				crop = itk.RegionOfInterestImageFilter[sliceType,sliceType].New()
				crop.SetRegionOfInterest(extractRegion)
			else:
				crop = itk.ExtractImageFilter[image,sliceType].New()
				crop.SetExtractionRegion(extractRegion)
			crop.SetInput(image)
			crop.Update()
			imgSlice = crop.GetOutput()
			imgSlice.DisconnectPipeline()
			slices.append(imgSlice)

		return slices

	def pasteITKImageSlice(self, origImage, translatedImage, sliceIndex):
		"""
		Paste single slice into ITK 3D image stack
		"""
		destIndex = itk.Index._3()
		destIndex[0] = 0
		destIndex[1] = 0
		destIndex[2] = sliceIndex
		paste = itk.PasteImageFilter[origImage].New()
		paste.SetDestinationImage(origImage)
		paste.SetSourceImage(translatedImage)
		paste.SetSourceRegion(translatedImage.GetLargestPossibleRegion())
		paste.SetDestinationIndex(destIndex)
		paste.Update()
		origImage = paste.GetOutput()
		origImage.DisconnectPipeline()
		return origImage

	def getFilterDesc(self):
		"""
		Return description of the filter
		"""
		return self.filterDesc
