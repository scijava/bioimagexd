#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: GUIBuilder
 Project: BioImageXD
 Created: 15.04.2006, KP
 Description:

 A module containing the classes for building a GUI for all the manipulation filters
							
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
__author__ = "BioImageXD Project <http://www.bioimagexd.org/>"
__version__ = "$Revision: 1.42 $"
__date__ = "$Date: 2005/01/13 14:52:39 $"

import scripting
import ColorTransferEditor
from wx.lib.filebrowsebutton import FileBrowseButton
import Histogram
import lib.messenger
import Logging
import types
import wx
import traceback
import lib.Command
import os

RADIO_CHOICE = "RADIO_CHOICE"
THRESHOLD = "THRESHOLD"
CTF = "CTF"
PIXEL = "PIXEL"
PIXELS = "PIXELS"
SLICE = "SLICE"
FILENAME = "FILENAME"
CHOICE = "CHOICE"
SPINCTRL = "SPINCTRL"
NOBR = "NOBR"
BR = "BR"
ROISELECTION = "ROISELECTION"

SPECIAL_ELEMENTS = [RADIO_CHOICE, THRESHOLD, CTF, PIXEL, PIXELS, SLICE, FILENAME, CHOICE, ROISELECTION]

class GUIBuilderBase:
	"""
	Created: 31.05.2006, KP
	Description: A base class for modules that intend to use GUI builder
	""" 
	name = "GUIBuilderBase"
	def __init__(self, changeCallback):
		"""
		Created: 13.04.2006, KP
		Description: Initialization
		"""
		self.initialization = True
		self.numberOfInputs = (1,1) 
		self.descs = {}
		self.dataUnit = None 
		self.initDone = 0
		self.parameters = {}
		self.inputMapping = {}
		self.sourceUnits = []
		self.inputs = []
		self.inputIndex = 0
		self.gui = None
		self.modCallback = changeCallback
		self.updateDefaultValues()
		
	def setInitialization(self, flag):
		"""
		Created: 07.12.2007, KP
		Description: toggle a flag indicating, whether the filter should be re-initialized
		"""
		self.initialization = flag
			
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

	def recordParameterChange(self, parameter, value, modpath): #svn-1037, 18.7.07, MB
		"""
		Created: 14.06.2007, KP
		Description: record the change of a parameter along with information for how to undo it
		"""
		oldval = self.parameters.get(parameter, None)
		if oldval == value:
			return
		if self.getType(parameter) == ROISELECTION:
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

	def setParameter(self, parameter, value):
		"""
		Created: 13.04.2006, KP
		Description: Set a value for the parameter
		"""	   
		self.parameters[parameter] = value
		if self.modCallback:
			self.modCallback(self)
#
	def getParameter(self, parameter):
		"""
		Created: 29.05.2006, KP
		Description: Get a value for the parameter
		"""	   
		return self.parameters.get(parameter, None)
		
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

class GUIBuilder(wx.Panel):
	"""
	Created: 13.04.2006, KP
	Description: A GUI builder for the manipulation filters
	""" 
	def __init__(self, parent, myfilter):
		"""
		Created: 13.04.2006, KP
		Description: Initialization
		""" 
		wx.Panel.__init__(self, parent, -1)
		self.filter = myfilter
		self.sizer = wx.GridBagSizer()
		# store the histograms so that the filters can access them if they need
		# to
		self.histograms = []
		self.currentBackground = None
		self.currentBackgroundSizer = None
		
		self.buildGUI(myfilter)
		self.SetSizer(self.sizer)
		self.SetAutoLayout(1)
		
	def getSizerPosition(self):
		"""
		Created: 07.06.2006, KP
		Description: Return the position in the sizer where the user can add more stuff
		""" 
		return (1, 0)
		
	def isSpecialElement(self, item, itemType):
		"""
		Created: 12.09.2007, KP
		Description: determine whether the given item is an item that requires special method to create the GUI element for
		"""
		if (type(item) == types.TupleType): return True
		if itemType in SPECIAL_ELEMENTS: return True
		return False

	def buildGUI(self, currentFilter):
		"""
		Created: 13.04.2006, KP
		Description: Build the GUI for a given filter
		""" 
		self.currentFilter = currentFilter
		parameters = currentFilter.getParameters()
		gy = 0
		staticBox = wx.StaticBox(self, -1, currentFilter.getName())
		staticBoxSizer = wx.StaticBoxSizer(staticBox, wx.VERTICAL)
		staticBox.Lower()
		
		self.sizer.Add(staticBoxSizer, (0, 0))
		sizer = wx.GridBagSizer()
		staticBoxSizer.Add(sizer)
		
		# If necessary, create the channel selection GUI
		if currentFilter.canSelectChannels():
			channelSelection = self.buildChannelSelection()
			sizer.Add(channelSelection, (gy, 0), span = (1, 2))
		
			gy += 1
		keepOnSameRow = 0
		cx = 0
		# Loop through all the parameters we need to create GUI elements for
		for param in parameters:
			# If the parameter is just a header, then create a label to show it
			if type(param) == types.StringType:
				label = wx.StaticText(self, -1, param)
				sizer.Add(label, (gy, 0))		
			# If it's a list with header name and items
			elif type(param) == types.ListType:
				self.staticBoxName, items = param
				self.itemSizer = wx.GridBagSizer()
				self.currentRow = -1
				positionOnSameRow = 0
				skipNextNItems = 0
				
				# Loop through all the items on this section
				for n, item in enumerate(items):
					if item == NOBR:
						keepOnSameRow = 1
						continue
					if skipNextNItems:
						skipNextNItems -= 1
						continue
						
					itemName = item
					isTuple = type(item) == types.TupleType

					if isTuple:
						itemType = currentFilter.getType(item[0])
						itemName = item[0]
					else:
						itemType = currentFilter.getType(item)
					if not self.isSpecialElement(item, itemType):
						# The GUI for the parameter is created using the regular createGUIElement method
						if not keepOnSameRow:
							self.currentRow += 1
							cx = 0
						else:
							keepOnSameRow = 0
							cx += 1
							positionOnSameRow = 1
						oldRow = self.currentRow
						cx, self.currentRow = self.createGUIElement(currentFilter, self.itemSizer, item, x = cx, y = self.currentRow, useOld = positionOnSameRow)
						# If there are more than one item specified on this parameter block, then we check if
						# the previous item was an element instructing us to not switch to the next row, but
						# keep adding items to the current row, and if so, act accordingly
						if n > 0:
							if items[n - 1] == NOBR and self.currentRow != oldRow:
								self.currentRow -= 1
							else:
								positionOnSameRow = 0
					else: # Items that are contained in a tuple can be "special" items, for which some of the tuple items are
						  # parameters.
						if not keepOnSameRow:
							self.currentRow += 1
						if itemType == RADIO_CHOICE:
							# Indicate that we need to skip next item, since radio choice is as follows
							# ( ("NearestNeighbor", "Linear"), ("cols", 2)),
							# where the following element specifies parameters for the item
							skipNextNItems = 1
							self.currentRow += self.createRadioChoice(n, items, currentFilter)
						elif itemType == SLICE:
							self.currentRow += self.createSliceSelection(n, items, currentFilter)
						elif itemType == FILENAME:
							skipNextNItems = 2
							self.currentRow += self.createFileSelection(n, items, currentFilter)
						elif itemType == CHOICE:
							self.currentRow += self.createChoice(n, items, currentFilter)
						elif itemType == ROISELECTION:
							self.currentRow += self.createROISelection(n, items, currentFilter)
						elif itemType == PIXEL:
							self.currentRow += self.createPixelSelection(n, items, currentFilter)
						elif itemType == PIXELS:
							self.currentRow += self.createMultiPixelSelection(n, items, currentFilter)
						elif itemType == THRESHOLD:
							self.currentRow += self.createThresholdSelection(n, items, currentFilter)
						elif itemType == CTF:
							self.currentRow += self.createColorTransferFunctionEditor(n, items, currentFilter)
						else:
							# If the item was not a "special" parameter, then we just group the parameters on this tuple
							groupsizer = wx.GridBagSizer()
							x = 0
							for it in item:
								self.createGUIElement(currentFilter, groupsizer, it, x = x, y = 0)
								x += 1
							span = (1, x)
							self.itemSizer.Add(groupsizer, (self.currentRow, 0), span = span)
							# If the name is an empty string, don't create a static box around
				
				# If the parameter requires a static box to show the name of the GUI block, then
				# create the staticbox
				if self.staticBoxName:
					staticBox = wx.StaticBox(self, -1, self.staticBoxName)
					staticBoxSizer = wx.StaticBoxSizer(staticBox, wx.VERTICAL)
					staticBox.Lower()
				
					sizer.Add(staticBoxSizer, (gy, 0), flag = wx.EXPAND)
					staticBoxSizer.Add(self.itemSizer)
				else:
					# otherwise we can just add the created sizer to the main sizer
					sizer.Add(self.itemSizer, (gy, 0), flag = wx.EXPAND)

			# The next item goes to the next row
			gy += 1
			
	def createColorTransferFunctionEditor(self, n, items, currentFilter):
		"""
		Created: 12.09.2007, KP
		Description: create a GUI element that allows the editing of a color transfer function
		"""
		itemName = items[n]
		item = items[n]
		background = wx.Window(self, -1)
		backgroundSizer = wx.BoxSizer(wx.VERTICAL)
		background.SetSizer(backgroundSizer)
		background.SetAutoLayout(1)
		level = currentFilter.getParameterLevel(itemName)

		wantAlpha = items[n][1]
		text = currentFilter.getDesc(itemName)
		if text:
			colorLbl = wx.StaticText(background, -1, text)
			backgroundSizer.Add(colorLbl)

		colorPanel = ColorTransferEditor.ColorTransferEditor(background, alpha = wantAlpha)
		backgroundSizer.Add(colorPanel)
		self.itemSizer.Add(background, (0, 0))
		setColorTransferFunction = lambda obj, event, arg, panel = colorPanel, i = item, \
											s = self: s.onSetCtf(panel, i, arg)
	  
	  	print
		lib.messenger.connect(currentFilter, "set_%s_ctf" % item, setColorTransferFunction)
		setotf = lambda obj, event, arg, panel = colorPanel, i = item, s = self: s.onSetOtf(panel, i, arg)
		lib.messenger.connect(currentFilter, "set_%s_otf" % item, setotf)
		return 0
			
	def createThresholdSelection(self, n, items, currentFilter):
		"""
		Created: 12.09.2007, KP
		Description: create a histogram GUI element that can be used to select a lower and upper threshold
		"""
		item = items[n]
		itemName = item[0]
		background = wx.Window(self, -1)
		level = currentFilter.getParameterLevel(itemName)
		if level:
			background.SetBackgroundColour(level)
		
		histogram = Histogram.Histogram(background)
		
		
		self.histograms.append(histogram)
		func = lambda event, its = item, f = currentFilter:self.onSetThreshold(event, its, f)
		histogram.Bind(Histogram.EVT_SET_THRESHOLD, func)
		
		histogram.setThresholdMode(1)
		dataUnit = self.filter.getDataUnit().getSourceDataUnits()[0]
		flo = lambda obj, event, arg, histogram = histogram, i = item[0], s = self: \
					s.onSetHistogramValues(histogram, i, arg, valuetype = "Lower")
		lib.messenger.connect(currentFilter, "set_%s" % item[0], flo)
		fhi = lambda obj, event, arg, histogram = histogram, i = item[1], s = self: \
					s.onSetHistogramValues(histogram, i, arg, valuetype = "Upper")
		lib.messenger.connect(currentFilter, "set_%s" % item[1], fhi)
		
		setDataunitFunc = lambda obj, event, dataunit, h = histogram: h.setDataUnit(dataunit)
		
		lib.messenger.connect(currentFilter,"set_%s_dataunit"%item[0],setDataunitFunc)
		lib.messenger.connect(currentFilter,"set_%s_dataunit"%item[1],setDataunitFunc)
		
		histogram.setDataUnit(dataUnit, noupdate = 1)
		
		self.itemSizer.Add(background, (0, 0), flag=wx.EXPAND)
		
		bgsizer = wx.GridBagSizer()
		bgsizer.Add(histogram, (0,0), span=(1,2))
				
		lowerLbl = wx.StaticText(background, -1,"Lower threshold:")
		upperLbl = wx.StaticText(background,-1,"Upper threshold:")
		
		lower = self.createNumberInput(background, currentFilter, item[0], types.IntType, 0, "", self.updateThresholdHistogram)
		upper = self.createNumberInput(background, currentFilter, item[1], types.IntType, 255, "", self.updateThresholdHistogram)

		bgsizer.Add(lowerLbl,(1,0))
		bgsizer.Add(lower,(1,1))
		bgsizer.Add(upperLbl,(2,0))
		bgsizer.Add(upper,(2,1))
		background.SetSizer(bgsizer)
		background.SetAutoLayout(1)
		background.Layout()
		
		return 0
		

	def updateThresholdHistogram(self, event, input, parameter, itemType, currentFilter):
		"""
		Created: 06.11.2007, KP
		Description: 
		"""
		currentFilter.sendUpdateGUI([parameter])

		
	def createMultiPixelSelection(self, n, items, currentFilter):
		"""
		Created: 12.09.2007, KP
		Description: create a GUI element that allows the user to select (and remove selection of) multiple pixels
		"""
		pixelsizer = wx.GridBagSizer()
		background = wx.Window(self, -1)
		itemName = items[n]
		level = currentFilter.getParameterLevel(itemName)
		if level:
			background.SetBackgroundColour(level)
		
		seedbox = wx.ListBox(background, -1, size = (150, 150))
		pixelsizer.Add(seedbox, (0, 0), span = (2, 1))
		
		addButton = wx.Button(background, -1, "Add seed")
		def markListBox(listBox):
			listBox.selectPixel = 1
		addPixelFunc = lambda event, l = seedbox:markListBox(l)
		addButton.Bind(wx.EVT_BUTTON, addPixelFunc)
		pixelsizer.Add(addButton, (0, 1))
		rmButton = wx.Button(background, -1, "Remove")
		seedbox.itemName = itemName
		removeSeedFunc = lambda event, its = items, f = currentFilter:self.removeSeed(seedbox, f)
		rmButton.Bind(wx.EVT_BUTTON, removeSeedFunc)
		pixelsizer.Add(rmButton, (1, 1))
		
		background.SetSizer(pixelsizer)
		background.SetAutoLayout(1)
		background.Layout()
		
		#obj, event, x, y, z, scalar, rval, gval, bval, r, g, b, a, colorTransferFunction)
		getVoxelSeedFunc = lambda obj, event, rx, ry, rz, scalar, rval, gval, bval, \
							r, g, b, alpha, currentCt, its = items, \
							f = currentFilter:self.onAddPixel(obj, event, rx, ry, rz, r, g, b, \
																alpha, currentCt, its, f, seedbox)
		lib.messenger.connect(None, "get_voxel_at", getVoxelSeedFunc)
		self.itemSizer.Add(background, (0, 0))							   
		onSetPixelsFunc = lambda obj, event, arg, seedbox = seedbox, i = itemName, \
				s = self: s.onSetPixelsFromFilter(seedbox, i, arg)
		lib.messenger.connect(currentFilter, "set_%s" % itemName, onSetPixelsFunc)
		return 0

	def createPixelSelection(self, n, items, currentFilter):
		"""
		Created: 12.09.2007, KP
		Description: create a GUI element for selecting a pixel from the preview
		"""
		background = wx.Window(self, -1)
		itemName = items[n]
		level = currentFilter.getParameterLevel(itemName)
		if level:
			background.SetBackgroundColour(level)
			
		label = wx.StaticText(background, -1, "(%d, %d, %d)" % (0, 0, 0), size = (80, -1))
		button = wx.Button(background, -1, "Set seed")
		def markAsSelected(listBox): 
			listBox.selectPixel = 1
		addPixelFunc = lambda event, l = label: markAsSelected(l)
		
		button.Bind(wx.EVT_BUTTON, addPixelFunc)
		box = wx.BoxSizer(wx.HORIZONTAL)
		box.Add(label)
		box.Add(button)
		background.SetSizer(box)
		background.SetAutoLayout(1)
		background.Layout()
		self.itemSizer.Add(background, (0, 0))
		getVoxelFunc = lambda obj, event, rx, ry, rz, scalar, rval, gval, bval, \
						r, g, b, alpha, currentCt, its = item, \
						f = currentFilter:self.onSetPixel(obj, event, rx, ry, rz, r, g, b, \
															alpha, currentCt, its, f, label)
		lib.messenger.connect(None, "get_voxel_at", getVoxelFunc)

		onSetPixelFunc = lambda obj, event, arg, label = label, i = itemName, \
					s = self: s.onSetPixelFromFilter(label, i, arg)
		lib.messenger.connect(currentFilter, "set_%s" % itemName, onSetPixelFunc)
		return 0

	def createROISelection(self, n, items, currentFilter):
		"""
		Created: 12.09.2007, KP
		Description: create a dropdown menu to select a ROI
		"""
		box = wx.BoxSizer(wx.VERTICAL)
		itemName = items[n]
		item = items[n]
		text = currentFilter.getDesc(itemName)
		val = 0
		
		label = wx.StaticText(self, -1, text)
		box.Add(label)
		regionsOfInterest = scripting.visualizer.getRegionsOfInterest()
		choices = [x.getName() for x in regionsOfInterest]
		
		def updateROIs(currentFilter, itemName, choice):
			regionsOfInterest = scripting.visualizer.getRegionsOfInterest()
			choices = [x.getName() for x in regionsOfInterest]		
			choice.Clear()
			choice.AppendItems(choices)
			
		longDesc = currentFilter.getLongDesc(itemName)
		if longDesc:
			choice.SetToolTip(wx.ToolTip(s))

		setRoiFunc = lambda event, its = item, f = currentFilter, i = itemName, \
						r = regionsOfInterest, s = self: s.onSetROI(r, f, i, event)
		choice = wx.Choice(self, -1, choices = choices)
		
		choice.SetSelection(val)
		choice.Bind(wx.EVT_CHOICE, setRoiFunc)
		
		updateRoiFunc = lambda obj, event, choice = choice, i = itemName, \
			fi = currentFilter, s = self: updateROIs(fi, i, choice)
		lib.messenger.connect(currentFilter, "update_%s" % itemName, updateRoiFunc) 
		lib.messenger.connect(None, "update_annotations", updateRoiFunc)
		
		box.Add(choice, 1)
		# was (y, 0)
		self.itemSizer.Add(box, (self.currentRow, 0), flag = wx.EXPAND | wx.HORIZONTAL)
		return 1

	def createChoice(self, n, items, currentFilter):
		"""
		Created: 12.09.2007, KP
		Description: create a choice (a dropdown menu) gui element
		"""
		itemName = items[n]
		item = items[n]
		box = wx.BoxSizer(wx.VERTICAL)
		text = currentFilter.getDesc(itemName)
		defValue = currentFilter.getDefaultValue(itemName)
		level = currentFilter.getParameterLevel(itemName)

		if text:
			label = wx.StaticText(self, -1, text)
			box.Add(label)
		
		background = wx.Window(self, -1)
		choices = currentFilter.getRange(itemName)
		updateChoiceFunc = lambda event, its = item, f = currentFilter, i = itemName, s = self: \
									s.onSetChoice(f, i, event)
		choice = wx.Choice(background, -1, choices = choices)
		
		choice.SetSelection(defValue)
		if level:
			if text: 
				label.SetBackgroundColour(level)
			background.SetBackgroundColour(level)
		choice.Bind(wx.EVT_CHOICE, updateChoiceFunc)

		longDesc = currentFilter.getLongDesc(itemName)
		if longDesc:
			choice.SetToolTip(wx.ToolTip(s))

		setChoiceFunc = lambda obj, event, arg, c = choice, i = itemName, s = self: \
								s.onSetChoiceFromFilter(c, i, arg)
		lib.messenger.connect(currentFilter, "set_%s" % itemName, setChoiceFunc) 

		box.Add(background, 1)
		self.itemSizer.Add(box, (self.currentRow, 0), flag = wx.EXPAND | wx.HORIZONTAL)
		return 1

	def createRadioChoice(self, n, items, currentFilter):
		"""
		Created: 12.09.2007, KP
		Description: create a radio choice GUI element
		"""
		itemName = items[n]

		if items[n + 1][0] == "cols":
			majordim = wx.RA_SPECIFY_COLS
		else:
			majordim = wx.RA_SPECIFY_ROWS
		
		item = items[n]
		choices = []
		itemToDesc = {}
		funcs = []
		for i in item:
			filterDescription = currentFilter.getDesc(i)
			itemToDesc[i] = filterDescription
			choices.append(filterDescription)
			setRadioFunc = lambda obj, event, arg, box, i = i, s = self: s.onSetRadioBox(box, i, arg)
			funcs.append(("set_%s" % i, setRadioFunc))
			longDesc = currentFilter.getLongDesc(i)
		
		box = wx.RadioBox(self, -1, self.staticBoxName, choices = choices,
		majorDimension = items[n + 1][1], style = majordim)
		if longDesc:
			box.SetToolTip(wx.ToolTip(s))

		for funcname, f in funcs:
			radioBoxF = lambda obj, event, arg, box = box: f(obj, event, arg, box)
			lib.messenger.connect(currentFilter, funcname, radioBoxF)
		box.itemToDesc = itemToDesc
		onSelectRadioBox = lambda event, its = item, f = currentFilter: self.onSelectRadioBox(event, its, f)
			
		box.Bind(wx.EVT_RADIOBOX, onSelectRadioBox)
		self.staticBoxName = ""
		self.itemSizer.Add(box, (0, 0))
		return 0
		
	def createSliceSelection(self, n, items, currentFilter):
		"""
		Created: 12.09.2007, KP
		Description: create a slice selection slider GUI element
		"""
		itemName = items[n]
		item = items[n]
		
		text = currentFilter.getDesc(itemName)
		box = wx.BoxSizer(wx.VERTICAL)
		if text:
			label = wx.StaticText(self, -1, text)
			box.Add(label)
		
		defValue = currentFilter.getDefaultValue(itemName)
		level = currentFilter.getParameterLevel(itemName)
		minval, maxval = currentFilter.getRange(itemName)
		x = 200
		
		background = wx.Window(self, -1)
		slider = wx.Slider(background, -1, value = defValue, minValue = minval, maxValue = maxval,
		style = wx.SL_HORIZONTAL | wx.SL_LABELS | wx.SL_AUTOTICKS, size = (x, -1))
		
		longDesc = currentFilter.getLongDesc(itemName)
		if longDesc:
			slider.SetToolTip(wx.ToolTip(s))
		
		if level:
			background.SetBackgroundColour(level)
			if text:
				label.SetBackgroundColour(level)
				
		onSliderScroll = lambda event, its = item, f = currentFilter: \
								self.onSetSliderValue(event, its, f)
		slider.Bind(wx.EVT_SCROLL, onSliderScroll)
		setSliderFunc = lambda obj, event, arg, slider = slider, i = itemName, s = self: \
								s.onSetSlice(slider, i, arg)
			
		lib.messenger.connect(currentFilter, "set_%s" % itemName, setSliderFunc)

		def updateRange(currentFilter, itemName, slider):
			minval, maxval = currentFilter.getRange(itemName)
			slider.SetRange(minval, maxval)
		
		updateSliderFunc = lambda obj, event, slider = slider, i = itemName, \
					fi = currentFilter, s = self: updateRange(fi, i, slider)
		lib.messenger.connect(currentFilter, "update_%s" % itemName, updateSliderFunc)
		
		box.Add(background, 1)
		self.itemSizer.Add(box, (self.currentRow, 0), flag = wx.EXPAND | wx.HORIZONTAL)
		return 1
		
	def createFileSelection(self, n, items, currentFilter):
		"""
		Created: 12.09.2007, KP
		Description: create a file selection GUI element that shows the filename and has a button to select a file
		"""
		itemName = items[n][0]

		box = wx.BoxSizer(wx.VERTICAL)
		text = currentFilter.getDesc(itemName)
		defValue = currentFilter.getDefaultValue(itemName)

		updateFilenameFunc = lambda event, its = items[n], f = currentFilter, i = itemName, \
						s = self: s.onSetFileName(f, i, event)

		browse = FileBrowseButton(self, -1, size = (400, -1), labelText = text, 
		fileMask = items[n][2], dialogTitle = items[n][1], changeCallback = updateFilenameFunc)

		browse.SetValue(defValue)
		setFilenameFunc = lambda obj, event, arg, b = browse, i = itemName, s = self: \
									s.onSetFileNameFromFilter(b, i, arg)
		lib.messenger.connect(currentFilter, "set_%s" % itemName, setFilenameFunc) 
									
		longDesc = currentFilter.getLongDesc(itemName)
		if longDesc:
			browse.SetToolTip(wx.ToolTip(s))

		box.Add(browse, 1)
		self.itemSizer.Add(box, (self.currentRow, 0), flag = wx.EXPAND | wx.HORIZONTAL)
		return 1
							
	def buildChannelSelection(self):
		"""
		Created: 17.04.2006, KP
		Description: Build a GUI for selecting the source channels
		"""
		sizer = wx.GridBagSizer()
		y = 0
		chmin, chmax = self.currentFilter.getNumberOfInputs()

		choices = self.currentFilter.getInputChannelNames()
		
		for i in range(1, chmax + 1):
			label = wx.StaticText(self, -1, self.currentFilter.getInputName(i))
			sizer.Add(label, (y, 0))
			chlChoice = wx.Choice(self, -1, choices = choices)
			sizer.Add(chlChoice, (y, 1))
			#chlChoice.SetSelection(i - 1)
			#self.currentFilter.setInputChannel(i, i - 1)
			chlChoice.SetSelection(self.currentFilter.getInputChannel(i))
			func = lambda event, f = self.currentFilter, n = i: self.onSetInputChannel(f, n, event)
			chlChoice.Bind(wx.EVT_CHOICE, func)

			y += 1
		return sizer
		
	def onSetChoice(self, filter, item, event):
		"""
		Created: 20.07.2006, KP
		Description: Set the parameter to the value of the choice widget
		"""			  
		value = event.GetSelection()
		filter.setParameter(item, value)		
		
	def onSetROI(self, regionsOfInterest, filter, item, event):
		"""
		Created: 20.07.2006, KP
		Description: Set the parameter to the ROI corresponding to the value of the choice widget
		"""			  
		value = event.GetSelection()
		regionsOfInterest = scripting.visualizer.getRegionsOfInterest()
		filter.setParameter(item, (value, regionsOfInterest[value]))		  
				
		
	def onSetFileName(self, filter, item, event):
		"""
		Created: 12.07.2006, KP
		Description: Set the file name
		"""			  
		filename = event.GetString()
		filter.setParameter(item, filename)
		
	def onSetChoiceFromFilter(self, cc, itemName, value):
		"""
		Created: 12.07.2006, KP
		Description: Set the file name
		"""			  
		cc.SetSelection(value)
	
	def onSetFileNameFromFilter(self, browseButton, itemName, value):
		"""
		Created: 12.07.2006, KP
		Description: Set the file name
		"""			  
		browseButton.SetValue(value)
		
	def onSetRadioBox(self, box, item, value):
		"""
		Created: 05.06.2006, KP
		Description: Set the value for the GUI item 
		"""			
		selectionValue = box.itemToDesc[item]
		if value:
			box.SetStringSelection(selectionValue)
		
	def onSetSlice(self, slider, item, value):
		"""
		Created: 05.06.2006, KP
		Description: Set the value for the GUI item 
		"""					
		
		slider.SetValue(value)

	def onSetSpinFromFilter(self, spin, item, value):
		"""
		Created: 21.06.2006, KP
		Description: Set the value for the GUI item 
		"""							
		spin.SetValue(value)

	def onSetInputChannel(self, currentFilter, inputNum, event):
		"""
		Created: 17.04.2006, KP
		Description: Set the input channel number #inputNum
		"""				 
		n = event.GetSelection()
		self.currentFilter.setInputChannel(inputNum, n)
		
	def createGUIElement(self, currentFilter, itemSizer, item, x, y, useOld = 0):
		"""
		Created: 15.04.2006, KP
		Description: Build the GUI related to one specific item
		"""
		desc = currentFilter.getDesc(item)
		if not useOld:
			background = wx.Window(self, -1)
		else:
			background = self.currentBackground
		
		itemType = currentFilter.getType(item)
		br = 0		  
		if desc and desc[ -1] == '\n':
			desc = desc[:-1]
			br = 1
		if not useOld:
			if br:
				backgroundSizer = wx.BoxSizer(wx.VERTICAL)
			else:
				backgroundSizer = wx.BoxSizer(wx.HORIZONTAL)
			background.SetSizer(backgroundSizer)
			background.SetAutoLayout(1)
				
		else:
			backgroundSizer = self.currentBackgroundSizer
			
		self.currentBackgroundSizer = backgroundSizer
		self.currentBackground = background
		
		if	desc and itemType not in [types.BooleanType]:
			label = wx.StaticText(background, -1, desc)
			updatef = lambda obj, event, arg, label = label, i = item, s = self: s.SetLabel(label, arg)
										
			lib.messenger.connect(currentFilter, "update_%s_label" % item, updatef)
			backgroundSizer.Add(label)
		else:
			label = None
			
		useOther = 0
		if br and not useOld:
			useOther = 1
			newsizer = wx.BoxSizer(wx.HORIZONTAL)
			self.newItemSizer = newsizer
			
			
		defaultValue = currentFilter.getDefaultValue(item)
		
		level = currentFilter.getParameterLevel(item)
		if label and level:
			label.SetBackgroundColour(level)
		
		if level:		   
			background.SetBackgroundColour(level)
		
		if itemType in [types.IntType, types.FloatType]:
			input = self.createNumberInput(background, currentFilter, item, itemType, defaultValue, desc)
		elif itemType == types.BooleanType:
			input = self.createBooleanInput(background, currentFilter, item, itemType, defaultValue, desc)
		elif itemType == SPINCTRL:
			input  = self.createSpinInput(background, currentFilter, item, itemType, defaultValue, desc)
		else:
			raise "Unrecognized input type: %s" % (str(itemType))
	   
		txt = currentFilter.getLongDesc(item)
		if txt:
			input.SetHelpText(txt)
			
		if not useOther:
			backgroundSizer.Add(input)
		else:
			self.newItemSizer.Add(input)
			backgroundSizer.Add(self.newItemSizer)


		if not useOld:
			itemSizer.Add(background, (y, x))
		background.Layout()

		if useOther:
			self.currentBackgroundSizer	 = self.newItemSizer
		return (x, y)
						
	def createNumberInput(self, parent, currentFilter, item, itemType, defaultValue, label = "", chainFunction = None):
		"""
		Created: 15.04.2006, KP
		Description: Return the input for int type
		"""		   
		input = wx.TextCtrl(parent, -1, str(defaultValue), style = wx.TE_PROCESS_ENTER)
		valid = lambda event, f = currentFilter, p = item, t = itemType, \
							i = input:self.validateAndPassOn(event, i, p, itemType, f, chainFunction)
		input.Bind(wx.EVT_TEXT_ENTER, valid)
		input.Bind(wx.EVT_KILL_FOCUS, valid)
		
		f = lambda obj, event, arg, input = input, it = item, s = self: s.onSetNumber(input, it, arg)
		lib.messenger.connect(currentFilter, "set_%s" % item, f)
		return input
		
	def createSpinInput(self, parent, currentFilter, itemName, itemType, defaultValue, label = ""):
		"""
		Created: 15.04.2006, KP
		Description: Return the input for int type
		"""		   
		minval, maxval = currentFilter.getRange(itemName)
		
		spin = wx.SpinCtrl(parent, -1, style = wx.SP_VERTICAL)
		func = lambda event, its = itemName, sp = spin, f = currentFilter:self.onSetSpinValue(event, sp, its, f)
		spin.Bind(wx.EVT_SPINCTRL, func)
		spin.Bind(wx.EVT_TEXT, func)
		
		f = lambda obj, event, arg, spin = spin, i = itemName, s = self: s.onSetSpinFromFilter(spin, i, arg)
			
		lib.messenger.connect(currentFilter, "set_%s" % itemName, f)

		def updateRange(currentFilter, itemName, spin):
			minval, maxval = currentFilter.getRange(itemName)
			
			spin.SetRange(minval, maxval)
		
		f = lambda obj, event, spin = spin, i = itemName, fi = currentFilter, s = self: updateRange(fi, i, spin)
		lib.messenger.connect(currentFilter, "update_%s" % itemName, f)
		
		return spin
	

	def updateLabel(self, obj, label):
		"""
		Created: 14.06.2007, KP
		Description: update the label of an object
		"""
		obj.SetLabel(label)
	

	def onSetNumber(self, input, item, value):
		"""
		Created: 05.06.2006, KP
		Description: Set the value for the GUI item
		"""				
		input.SetValue(str(value))

	def onSetBool(self, input, item, value):
		"""
		Created: 05.06.2006, KP
		Description: Set the value for the GUI item
		"""				
		input.SetValue(value)
	
	def createBooleanInput(self, parent, currentFilter, item, itemType, defaultValue, label = ""):
		"""
		Created: 15.04.2006, KP
		Description: Return the input for boolean type
		"""		   
		input = wx.CheckBox(parent, -1, label)
		input.SetValue(defaultValue)
		valid = lambda event, f = currentFilter, p = item, t = itemType, i = input:\
						self.validateAndPassOn(event, i, p, itemType, f)
		input.Bind(wx.EVT_CHECKBOX, valid)
		f = lambda obj, event, arg, input = input, i = item, s = self: s.onSetBool(input, i, arg)
		lib.messenger.connect(currentFilter, "set_%s" % item, f)	   
		return input
		
	def removeSeed(self, listbox, currFilter):
		"""
		Created: 29.05.2006, KP
		Description: Remove a seed from filter
		"""			
		item = listbox.itemName
		n = listbox.GetSelection()
		if n != wx.NOT_FOUND:
			s = listbox.GetString(n)
			seedPoint = eval(s)
			listbox.Delete(n)
			
		seeds = currFilter.getParameter(item[0])   
		seeds.remove(seedPoint)
		currFilter.setParameter(item[0], seeds)

	def onAddPixel(self, obj, event, rx, ry, rz, r, g, b, alpha, \
					colorTransferFunction, item, currFilter, listbox):
		"""
		Created: 29.05.2006, KP
		Description: Add a value to the pixel listbox
		"""				
		if listbox.selectPixel:
			seeds = currFilter.getParameter(item[0])
			seeds.append((rx, ry, rz))
			currFilter.setParameter(item[0], seeds)
			listbox.Append("(%d, %d, %d)" % (rx, ry, rz))			   
			listbox.selectPixel = 0

			
	def onSetPixel(self, obj, event, rx, ry, rz, r, g, b, alpha, \
					colorTransferFunction, item, currFilter, valueLabel):
		"""
		Created: 26.05.2006, KP
		Description: Set the value of the pixel label
		"""				
		if valueLabel.selectPixel:
			currFilter.setParameter(item[0], (rx, ry, rz))
			valueLabel.SetLabel("(%d, %d, %d)" % (rx, ry, rz))
			valueLabel.selectPixel = 0
			
	def onSetPixelFromFilter(self, label, item, value):
		"""
		Created: 06.06.2006, KP
		Description: Set the value of the pixel label from a variable
		"""				
		rx, ry, rz = value
		label.SetLabel("(%d, %d, %d)" % (rx, ry, rz))

	def onSetPixelsFromFilter(self, listbox, item, value):
		"""
		Created: 06.06.2006, KP
		Description: Set the value of the pixel label from a variable
		"""		
		listbox.Clear()
		for rx, ry, rz in value:
			listbox.Append("(%d, %d, %d)" % (rx, ry, rz))			 

	def onSetHistogramValues(self, histogram, item, value, valuetype = "Lower"):
		"""
		Created: 06.06.2006, KP
		Description: Set the lower and upper threshold for histogram
		"""
		eval("histogram.set%sThreshold(value)" % valuetype)

	def onSetCtf(self, colorPanel, item, value):
		"""
		Created: 12.03.2007, KP
		Description: Set the color transfer function editor colorTransferFunction
		"""
		colorPanel.setColorTransferFunction(value)
		
	def onSetOtf(self, colorPanel, item, value):
		"""
		Created: 12.03.2007, KP
		Description: Set the color transfer function editor otf
		"""
		colorPanel.setOpacityTransferFunction(value)
			
	def onSetThreshold(self, event, items, currentFilter):
		"""
		Created: 15.04.2006, KP
		Description: Process an event from the histogram
		"""
		thresholds = event.getThresholds()
		for i, item in enumerate(items):
			currentFilter.setParameter(item, thresholds[i])
		currentFilter.sendUpdateGUI(items)
			
	def onSetSliderValue(self, event, items, currentFilter):
		"""
		Created: 31.05.2006, KP
		Description: Set the slider value
		"""		 
		value = event.GetPosition()
		currentFilter.setParameter(items, value)

	def onSetSpinValue(self, event, spinbox, itemName, currentFilter):
		"""
		Created: 31.05.2006, KP
		Description: Set the spin value
		"""		 
		value = spinbox.GetValue()
		value = int(value)
		currentFilter.setParameter(itemName, value)
			
	def onSelectRadioBox(self, event, items, currentFilter):
		"""
		Created: 15.04.2006, KP
		Description: Process an event from a radio box
		"""		 
		selection = event.GetSelection()
		
		for i, item in enumerate(items):
			flag = (i == selection)
			currentFilter.setParameter(item, flag)
		
	def validateAndPassOn(self, event, input, parameter, itemType, currentFilter, chain = None):
		"""
		Created: 13.04.2006, KP
		Description: Build the GUI for a given filter
		"""
		if itemType == types.IntType:
			convert = int
		elif itemType == types.FloatType:
			convert = float
		elif itemType == types.BooleanType:
			convert = bool
		try:
			value = convert(input.GetValue())
		except:
			return
		currentFilter.setParameter(parameter, value)
		if chain:
			chain(event, input, parameter, itemType, currentFilter)
		
