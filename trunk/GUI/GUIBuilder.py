#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: GUIBuilder
 Project: BioImageXD
 Created: 15.04.2006, KP
 Description:

 A module containing the classes for building a GUI for all the manipulation filters
							
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

#import wx.lib.buttons as buttons
#import UIElements

import scripting
import ColorTransferEditor
from wx.lib.filebrowsebutton import FileBrowseButton
import Histogram
import lib.messenger
import Logging
import types
import wx
import traceback		#svn-1037, 18.7.07, MB
import lib.Command		#svn-1037, 18.7.07, MB

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

class GUIBuilderBase:
	"""
	Created: 31.05.2006, KP
	Description: A base class for modules that intend to use GUI builder
	""" 
	def __init__(self, changeCallback):
		"""
		Created: 13.04.2006, KP
		Description: Initialization
		"""
		self.parameters = {}
		self.inputMapping = {}
		self.sourceUnits = []
		self.inputs = []
		self.inputIndex = 0
		self.gui = None
		self.modCallback = changeCallback
		self.initDone = 0
		for item in self.getPlainParameters():
			self.setParameter(item, self.getDefaultValue(item))
		self.initDone = 1

		self.numberOfInputs = None #added this because variable didnt exist on line 150, SS
		self.descs = {} #added this because variable didnt exist on line 240, SS
		self.dataUnit = None #added this because variable didnt exist on line 92, SS
		self.name = None #added this because variable didnt exist on line 263, SS
		
	def getInput(self, mapIndex):
		"""
		Created: 17.04.2006, KP
		Description: Return the input imagedata #n
		"""				
		if mapIndex not in self.inputMapping:
			self.inputMapping[mapIndex] = mapIndex - 1
		if self.inputMapping[mapIndex] == 0 and self.dataUnit.isProcessed():
			print self.inputs
			Logging.info("Using input %d from stack as input %d" % (mapIndex - 1, mapIndex), kw = "processing")
			try:
				image = self.inputs[self.inputIndex]
			except:
				traceback.print_exc()
				Logging.info("No input with number %d" %self.inputIndex, self.inputs, kw = "processing")
			self.inputIndex += 1
		else:
			Logging.info("\nUsing input from channel %d as input %d" % (self.inputMapping[mapIndex] - 1, mapIndex), \
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
		if self.inputMapping[mapIndex] == 0 and self.dataUnit.isProcessed():		   
			return self.dataUnit
		else:
			image = self.getInputFromChannel(self.inputMapping[mapIndex] - 1, dataUnit = 1)
		return image
		
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
		#print "RETURNING TIMEPOINT %d from SOURCEUNITS %d AS SOURCE" %(tp, unitIndex)
		#print "SOURCE UNIT IS = ", self.sourceUnits[unitIndex]
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
		Description: Return the level of the given parameter
		"""
		return scripting.COLOR_BEGINNER			 
			
	def sendUpdateGUI(self):
		"""
		Created: 05.06.2006, KP
		Description: Method to update the GUI for this filter
		"""			 
		for item in self.getPlainParameters():
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
			# If it's a label
			if type(item) == types.StringType:
				continue
			elif type(item) == types.ListType:
				title, items = item
				if type(items[0]) == types.TupleType:
					items = items[0]
				returnList.extend(items)
		return returnList


	def recordParameterChange(self, parameter, value, modpath):	#svn-1037, 18.7.07, MB
		#Heres probably some stuff to cleanup
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
			# First record the proper value
			value = roi
		else:
			if type(value) in [types.StringType, types.UnicodeType]:

				setval = "'%s'" % value
				setoldval = "'%s'" % oldval
			else:
				#print "Not string"
				setval = str(value)
				setoldval = str(oldval)
			#print "setval = ", setval, "oldval = ", oldval
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
#		 assert self.checkRange(parameter, value), \
#								"Value %s of parameter %s doesn't fit within the range %s - %s" %()
		self.parameters[parameter] = value
		if self.modCallback:
			self.modCallback(self)
#
	def getParameter(self, parameter):
		"""
		Created: 29.05.2006, KP
		Description: Get a value for the parameter
		"""    
		if parameter in self.parameters:
			return self.parameters[parameter]
		return None
		
	def getDesc(self, parameter):
		"""
		Created: 13.04.2006, KP
		Description: Return the description of the parameter
		"""    
		try:
			return self.descs[parameter]
		except:			   
			return ""
		
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
		
	def buildGUI(self, currentFilter):
		"""
		Created: 13.04.2006, KP
		Description: Build the GUI for a given filter
		""" 
		self.currentFilter = currentFilter
		parameters = currentFilter.getParameters()
		gy = 0
			
		# XXX: CHANGED TO MAKE MAC WORK
		staticBox = wx.StaticBox(self, -1, currentFilter.getName())
		staticBoxSizer = wx.StaticBoxSizer(staticBox, wx.VERTICAL)
		staticBox.Lower()
		
		
		self.sizer.Add(staticBoxSizer, (0, 0))
		sizer = wx.GridBagSizer()
		staticBoxSizer.Add(sizer)
		
		if currentFilter.canSelectChannels():
			channelSelection = self.buildChannelSelection()
		
			sizer.Add(channelSelection, (gy, 0), span = (1, 2))
		
			gy += 1
		nobr = 0
		cx = 0
		for param in parameters:

			# If it's a list with header name and items
			if type(param) == types.ListType:
				staticBoxName, items = param
				itemsizer = wx.GridBagSizer()

				y = -1
				useOld = 0
				skip = 0
				for n, item in enumerate(items):
					if item == NOBR:
						nobr = 1
						continue

					if skip:
						skip -= 1
						continue
					itemName = item
					isTuple = 0
					if type(item) == types.TupleType:
						itemType = currentFilter.getType(item[0])
						itemName = item[0]
						isTuple = 1
					else:
						itemType = currentFilter.getType(item)
					#print "item = ", item, "param = ", param
					#print "itemType = ", itemType, "isTuple = ", isTuple
					
					#print "items = ", items
					
					if not (isTuple and itemType == types.BooleanType) \
						and itemType not in [RADIO_CHOICE, SLICE, PIXEL, PIXELS, THRESHOLD, \
											FILENAME, CHOICE, ROISELECTION, CTF]:
						#print "NOBR = ", nobr, "processing item", item
						if not nobr:
							y += 1
							cx = 0
						else:
							nobr = 0
							cx += 1
							useOld = 1
						#print "x = ", cx, "y = ", y
						oldy = y
						cx, y = self.processItem(currentFilter, itemsizer, item, x = cx, y = y, useOld = useOld)
						if n > 0:
							if items[n - 1] == NOBR and y != oldy:
								y -= 1
								
							else:
								useOld = 0
						#print "ndxt y = ", y
					else: # Items that are contained in a tuple ask to be grouped
						  # together
						if not nobr:
							y += 1
						#print "cx = ", cx, "y = ", y
						if itemType == RADIO_CHOICE:

							# Indicate that we need to skip next item
							skip = 1
							#print item
							#print "Creating radio choice"
							if items[n + 1][0] == "cols":
								majordim = wx.RA_SPECIFY_COLS
							else:
								majordim = wx.RA_SPECIFY_ROWS
							
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
								

							
							box = wx.RadioBox(self, -1, staticBoxName, choices = choices,
							majorDimension = items[n + 1][1], style = majordim)
							if longDesc:
								box.SetToolTip(wx.ToolTip(s))

							for funcname, f in funcs:
								radioBoxF = lambda obj, event, arg, box = box: f(obj, event, arg, box)
								lib.messenger.connect(currentFilter, funcname, radioBoxF)
							box.itemToDesc = itemToDesc
							onSelectRadioBox = lambda event, its = item, f = currentFilter: self.onSelectRadioBox(event, its, f)
								
								
							box.Bind(wx.EVT_RADIOBOX, onSelectRadioBox)
							staticBoxName = ""
							itemsizer.Add(box, (0, 0))
						elif itemType == SLICE:
							text = currentFilter.getDesc(itemName)
							box = wx.BoxSizer(wx.VERTICAL)
							if text:
								label = wx.StaticText(self, -1, text)
								box.Add(label)
							
							defValue = currentFilter.getDefaultValue(itemName)
							level = currentFilter.getParameterLevel(itemName)
							minval, maxval = currentFilter.getRange(itemName)
							#print "Value for ", itemName, " = ", defValue, "range = ", minval, maxval
							x = 200
							
							background = wx.Window(self, -1)
							slider = wx.Slider(background, -1, value = defValue, minValue = minval, maxValue = maxval,
							style = wx.SL_HORIZONTAL | wx.SL_LABELS | wx.SL_AUTOTICKS,
							size = (x, -1))
							
							longDesc = currentFilter.getLongDesc(itemName)
							if longDesc:
								slider.SetToolTip(wx.ToolTip(s))

							
							#slider.SetBackgroundColour(level)
							if level:
								if text:
									label.SetBackgroundColour(level)
								background.SetBackgroundColour(level)
							onSliderScroll = lambda event, its = item, f = currentFilter: \
													self.onSetSliderValue(event, its, f)
							slider.Bind(wx.EVT_SCROLL, onSliderScroll)
							setSliderFunc = lambda obj, event, arg, slider = slider, i = itemName, s = self: \
													s.onSetSlice(slider, i, arg)
								

							lib.messenger.connect(currentFilter, "set_%s" % itemName, setSliderFunc)

							def updateRange(currentFilter, itemName, slider):
								print currentFilter, itemName, slider
								minval, maxval = currentFilter.getRange(itemName)
								slider.SetRange(minval, maxval)

							
							updateSliderFunc = lambda obj, event, slider = slider, i = itemName, \
										fi = currentFilter, s = self: updateRange(fi, i, slider)
							lib.messenger.connect(currentFilter, "update_%s" % itemName, updateSliderFunc)
							
							box.Add(background, 1)
							#print "Adding box to ", y, 0
							itemsizer.Add(box, (y, 0), flag = wx.EXPAND | wx.HORIZONTAL)
							y += 1
						elif itemType == FILENAME:
							# Indicate that we need to skip next item
							skip = 2
						
							box = wx.BoxSizer(wx.VERTICAL)
							text = currentFilter.getDesc(itemName)
							defValue = currentFilter.getDefaultValue(itemName)
					
							updateFilenameFunc = lambda event, its = item, f = currentFilter, i = itemName, \
											s = self: s.onSetFileName(f, i, event)

							browse = FileBrowseButton(self, -1, size = (400, -1),
							labelText = text, fileMask = items[n][2],
							dialogTitle = items[n][1],
							changeCallback = updateFilenameFunc)
							browse.SetValue(defValue)
							setFilenameFunc = lambda obj, event, arg, b = browse, i = itemName, s = self: \
														s.onSetFileNameFromFilter(b, i, arg)
							lib.messenger.connect(currentFilter, "set_%s" % itemName, setFilenameFunc) 
														
							longDesc = currentFilter.getLongDesc(itemName)
							if longDesc:
								# changed following so that makes sense, 20.7.2007 SS
								# filebrowse.SetToolTip(wx.ToolTip(s))
								browse.SetToolTip(wx.ToolTip(s))

							box.Add(browse, 1)							 
							itemsizer.Add(box, (y, 0), flag = wx.EXPAND | wx.HORIZONTAL)
							y += 1
						elif itemType == CHOICE:
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
								#choice.SetBackgroundColour(level)
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
							itemsizer.Add(box, (y, 0), flag = wx.EXPAND | wx.HORIZONTAL)
							y += 1

						
						elif itemType == ROISELECTION:
							box = wx.BoxSizer(wx.VERTICAL)
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
							
							#f = lambda obj, event, arg, c = choice, i = itemName, s = self: s.onSetROIFromFilter(c, i, arg)
							#lib.messenger.connect(currentFilter, "set_%s" %itemName, f) 
							
							
							box.Add(choice, 1)
							itemsizer.Add(box, (y, 0), flag = wx.EXPAND | wx.HORIZONTAL)
							y += 1
							
						elif itemType == PIXEL:
							#print "Creating pixel selection"
							background = wx.Window(self, -1)
							level = currentFilter.getParameterLevel(itemName)
							if level:
								background.SetBackgroundColour(level)
								
							label = wx.StaticText(background, -1, "(%d, %d, %d)" % (0, 0, 0), size = (80, -1))
							button = wx.Button(background, -1, "Set seed")
							def f(listBox):	#"listBox" used to be "l", shouldn't "l" 2 rows below also be changed?!
								listBox.selectPixel = 1
							addPixelFunc = lambda event, l = label:f(l)
							button.Bind(wx.EVT_BUTTON, addPixelFunc)
							box = wx.BoxSizer(wx.HORIZONTAL)
							box.Add(label)
							box.Add(button)
							background.SetSizer(box)
							background.SetAutoLayout(1)
							background.Layout()
							itemsizer.Add(background, (0, 0))
							getVoxelFunc = lambda obj, event, rx, ry, rz, scalar, rval, gval, bval, \
											r, g, b, alpha, currentCt, its = item, \
											f = currentFilter:self.onSetPixel(obj, event, rx, ry, rz, r, g, b, \
																				alpha, currentCt, its, f, label)
							lib.messenger.connect(None, "get_voxel_at", getVoxelFunc)

							onSetPixelFunc = lambda obj, event, arg, label = label, i = itemName, \
										s = self: s.onSetPixelFromFilter(label, i, arg)
							lib.messenger.connect(currentFilter, "set_%s" % itemName, onSetPixelFunc)

							
						elif itemType == PIXELS:
							#print "Creating multiple pixels selection"
							pixelsizer = wx.GridBagSizer()
							background = wx.Window(self, -1)
							
							level = currentFilter.getParameterLevel(itemName)
							if level:
								background.SetBackgroundColour(level)
							
							seedbox = wx.ListBox(background, -1, size = (150, 150))
							pixelsizer.Add(seedbox, (0, 0), span = (2, 1))
							
							addButton = wx.Button(background, -1, "Add seed")
							def markListBox(listBox):
								listBox.selectPixel = 1
							func = lambda event, l = seedbox:markListBox(l)
							addButton.Bind(wx.EVT_BUTTON, addPixelFunc)
							pixelsizer.Add(addButton, (0, 1))
							#print "ITEM = ", item
							rmButton = wx.Button(background, -1, "Remove")
							seedbox.itemName = item
							removeSeedFunc = lambda event, its = item, f = currentFilter:self.removeSeed(seedbox, f)
							rmButton.Bind(wx.EVT_BUTTON, removeSeedFunc)
							pixelsizer.Add(rmButton, (1, 1))
							
							background.SetSizer(pixelsizer)
							background.SetAutoLayout(1)
							background.Layout()
							
							#obj, event, x, y, z, scalar, rval, gval, bval, r, g, b, a, colorTransferFunction)
							getVoxelSeedFunc = lambda obj, event, rx, ry, rz, scalar, rval, gval, bval, \
												r, g, b, alpha, currentCt, its = item, \
												f = currentFilter:self.onAddPixel(obj, event, rx, ry, rz, r, g, b, \
																					alpha, currentCt, its, f, seedbox)
							lib.messenger.connect(None, "get_voxel_at", getVoxelSeedFunc)
							itemsizer.Add(background, (0, 0))							   
							onSetPixelsFunc = lambda obj, event, arg, seedbox = seedbox, i = itemName, \
									s = self: s.onSetPixelsFromFilter(seedbox, i, arg)
							lib.messenger.connect(currentFilter, "set_%s" % itemName, onSetPixelsFunc)														
							
						elif itemType == THRESHOLD:
							background = wx.Window(self, -1)
							level = currentFilter.getParameterLevel(itemName)
							if level:
								background.SetBackgroundColour(level)
							#print "Creating threshold selection"
							histogram = Histogram.Histogram(background)
							self.histograms.append(histogram)
							func = lambda event, its = item, f = currentFilter:self.onSetThreshold(event, its, f)
							histogram.Bind(Histogram.EVT_SET_THRESHOLD, func)
							
							histogram.setThresholdMode(1)
							dataUnit = self.filter.getDataUnit().getSourceDataUnits()[0]
							#print "Connecting", item[0], item[1]
							flo = lambda obj, event, arg, histogram = histogram, i = item[0], s = self: \
										s.onSetHistogramValues(histogram, i, arg, valuetype = "Lower")
							lib.messenger.connect(currentFilter, "set_%s" % item[0], flo)
							fhi = lambda obj, event, arg, histogram = histogram, i = item[1], s = self: \
										s.onSetHistogramValues(histogram, i, arg, valuetype = "Upper")
							lib.messenger.connect(currentFilter, "set_%s" % item[1], fhi)
							
							histogram.setDataUnit(dataUnit, noupdate = 1)
							itemsizer.Add(background, (0, 0))
						elif itemType == CTF:
							background = wx.Window(self, -1)
							backgroundSizer = wx.BoxSizer(wx.VERTICAL)
							background.SetSizer(backgroundSizer)
							background.SetAutoLayout(1)
							level = currentFilter.getParameterLevel(itemName)
 #							 if level:
 #								 background.SetBackgroundColour(level)
							wantAlpha = items[n][1]
							text = currentFilter.getDesc(itemName)
							if text:
								colorLbl = wx.StaticText(background, -1, text)
								backgroundSizer.Add(colorLbl)
	
							colorPanel = ColorTransferEditor.ColorTransferEditor(background, alpha = wantAlpha)
							backgroundSizer.Add(colorPanel)
							itemsizer.Add(background, (0, 0))
							setColorTransferFunction = lambda obj, event, arg, panel = colorPanel, i = item, \
																s = self: s.onSetCtf(panel, i, arg)
						  
							lib.messenger.connect(currentFilter, "set_%s_colorTransferFunction" % item, setColorTransferFunction)
							setotf = lambda obj, event, arg, panel = colorPanel, i = item, s = self: s.onSetOtf(panel, i, arg)
							lib.messenger.connect(currentFilter, "set_%s_otf" % item, setotf)
							
						else:
							groupsizer = wx.GridBagSizer()
							x = 0
							for it in item:
								self.processItem(currentFilter, groupsizer, it, x = x, y = 0)
								x += 1
							span = (1, x)
							itemsizer.Add(groupsizer, (y, 0), span = span)
							# If the name is an empty string, don't create a static box around
				
				# the items
				if staticBoxName:
					staticBox = wx.StaticBox(self, -1, staticBoxName)
					staticBoxSizer = wx.StaticBoxSizer(staticBox, wx.VERTICAL)
					staticBox.Lower()
#					 staticBox = wx.Panel(self, -1, style = wx.SUNKEN_BORDER)
#					 staticBoxSizer = wx.BoxSizer(wx.VERTICAL)
#					 staticBox.SetSizer(staticBoxSizer)
#					 staticBox.SetAutoLayout(1)
					
				
					sizer.Add(staticBoxSizer, (gy, 0), flag = wx.EXPAND)
					staticBoxSizer.Add(itemsizer)
				else:
					sizer.Add(itemsizer, (gy, 0), flag = wx.EXPAND)			  
			# If it's just a header name
			elif type(param) == types.StringType:
				label = wx.StaticText(self, -1, param)
				sizer.Add(label, (gy, 0))
			gy += 1

			
		
	def buildChannelSelection(self):
		"""
		Created: 17.04.2006, KP
		Description: Build a GUI for selecting the source channels
		"""						
		chmin, chmax = self.currentFilter.getNumberOfInputs()
		sizer = wx.GridBagSizer()
		y = 0
		choices = [self.currentFilter.processInputText]
		# If the input is a processed dataunit, i.e. output from a task,
		# then we offer both the task output and the individual channels
		if self.currentFilter.dataUnit.isProcessed():
			for i, dataunit in enumerate(self.currentFilter.dataUnit.getSourceDataUnits()):
				choices.append(dataunit.getName())
		else:
			# If we have a non - processed dataunit (i.e. a single channel)
			# as input, then we only offer that
			choices = [self.currentFilter.dataUnit.getName()]		  
		
		print "There are ", chmax, "channels"
		for i in range(1, chmax + 1):
			label = wx.StaticText(self, -1, self.currentFilter.getInputName(i))
			sizer.Add(label, (y, 0))
			chlChoice = wx.Choice(self, -1, choices = choices)
			sizer.Add(chlChoice, (y, 1))
			chlChoice.SetSelection(i - 1)
			print "Setting input channel", i, "to ", i - 1
			self.currentFilter.setInputChannel(i, i - 1)
			
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
		#print "Setting parameter", item, "to", value
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
		#print "Setting parameter", item, "to", filename
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
		#print "Setting value of filebrowse to", value
		
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
		
	def processItem(self, currentFilter, itemsizer, item, x, y, useOld = 0):
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
		#input.SetBackgroundColour(level)
	   
		txt = currentFilter.getLongDesc(item)
		if txt:
			input.SetHelpText(txt)
			
		if not useOther:
			backgroundSizer.Add(input)
		else:
			self.newItemSizer.Add(input)
			backgroundSizer.Add(self.newItemSizer)
		#backgroundSizer.Fit(background)
		
		#x2 = x

		if not useOld:
		#	itemsizer.Add(background, (y, x2))  #(19.6.07 SS)
			itemsizer.Add(background, (y, x))
		background.Layout()

		if useOther:
			self.currentBackgroundSizer  = self.newItemSizer
		return (x, y)
						
	def createNumberInput(self, parent, currentFilter, item, itemType, defaultValue, label = ""):
		"""
		Created: 15.04.2006, KP
		Description: Return the input for int type
		"""		   
		
		input = wx.TextCtrl(parent, -1, str(defaultValue))
		valid = lambda event, f = currentFilter, p = item, t = itemType, \
							i = input:self.validateAndPassOn(event, i, p, itemType, f)
		input.Bind(wx.EVT_TEXT, valid)
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
		#print input, item, value
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
		#print "item in removeSeed = ", item
		n = listbox.GetSelection()
		if n != wx.NOT_FOUND:
			s = listbox.GetString(n)
			seedPoint = eval(s)
			listbox.Delete(n)
			
		#print "Getting parameter", item[0]
		seeds = currFilter.getParameter(item[0])   
		#print "Removing ", seedPoint, "from ", seeds
		seeds.remove(seedPoint)
		currFilter.setParameter(item[0], seeds)

	def onAddPixel(self, obj, event, rx, ry, rz, r, g, b, alpha, \
					colorTransferFunction, item, currFilter, listbox):
		"""
		Created: 29.05.2006, KP
		Description: Add a value to the pixel listbox
		"""				
		#print "Set pixel", obj, event, rx, ry, rz, r, g, b, alpha, item, currFilter
		#print "item = ", item
		if listbox.selectPixel:
			seeds = currFilter.getParameter(item[0])
			seeds.append((rx, ry, rz))
			#print "Setting parameter", item, "to", seeds			 
			
			currFilter.setParameter(item[0], seeds)
			listbox.Append("(%d, %d, %d)" % (rx, ry, rz))			   
			listbox.selectPixel = 0

			
	def onSetPixel(self, obj, event, rx, ry, rz, r, g, b, alpha, \
					colorTransferFunction, item, currFilter, valueLabel):
		"""
		Created: 26.05.2006, KP
		Description: Set the value of the pixel label
		"""				
		#print "Set pixel", obj, event, rx, ry, rz, r, g, b, alpha, item, currFilter
		if valueLabel.selectPixel:
			#print "Settng parameter", item, "to", rx, ry, rz
			
			currFilter.setParameter(item[0], (rx, ry, rz))
			valueLabel.SetLabel("(%d, %d, %d)" % (rx, ry, rz))
			valueLabel.selectPixel = 0
			
	def onSetPixelFromFilter(self, label, item, value):
		"""
		Created: 06.06.2006, KP
		Description: Set the value of the pixel label from a variable
		"""				
		rx, ry, rz = value
		#print "Set pixel", obj, event, rx, ry, rz, r, g, b, alpha, item, currFilter
		label.SetLabel("(%d, %d, %d)" % (rx, ry, rz))

	def onSetPixelsFromFilter(self, listbox, item, value):
		"""
		Created: 06.06.2006, KP
		Description: Set the value of the pixel label from a variable
		"""		
		listbox.Clear()
		#print value
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
		Description: Process an event from a radio box
		"""		 
		thresholds = event.getThresholds()
		for i, item in enumerate(items):
			currentFilter.setParameter(item, thresholds[i])			  
			
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
		
	def validateAndPassOn(self, event, input, parameter, itemType, currentFilter):
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
