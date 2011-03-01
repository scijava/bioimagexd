#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: GUIBuilder
 Project: BioImageXD
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
import GUI.Scatterplot
import Configuration

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
COLOC_THRESHOLD = "COLOCTHRESHOLD"
SCATTERPLOT = "SCATTERPLOT"

SPECIAL_ELEMENTS = [RADIO_CHOICE, THRESHOLD, CTF, PIXEL, PIXELS, SLICE, FILENAME, CHOICE, ROISELECTION, COLOC_THRESHOLD, SCATTERPLOT]

def getGUIBuilderForFilter(obj):
	return GUIBuilder
		
class GUIBuilder(wx.Panel):
	"""
	A GUI builder for the manipulation filters
	""" 
	def __init__(self, parent, myfilter):
		"""
		Initialization
		""" 
		wx.Panel.__init__(self, parent, -1)
		self.filter = myfilter
		self.sizer = wx.GridBagSizer()
		# store the histograms so that the filters can access them if they need
		# to
		self.histograms = []
		self.currentBackground = None
		self.currentBackgroundSizer = None
		self.items = {}
		self.buildGUI(myfilter)
		self.SetSizer(self.sizer)
		self.SetAutoLayout(1)
		self.Bind(wx.EVT_CHILD_FOCUS, self.onFocus)
		
		
	def getSizerPosition(self):
		"""
		Return the position in the sizer where the user can add more stuff
		""" 
		return (1, 0)
		
	def isSpecialElement(self, item, itemType):
		"""
		determine whether the given item is an item that requires special method to create the GUI element for
		"""
		if (type(item) == types.TupleType): return True
		if itemType in SPECIAL_ELEMENTS: return True
		return False

	def buildGUI(self, currentFilter):
		"""
		Build the GUI for a given filter
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

		# If filter description available, add to filter GUI
		filterDesc = self.currentFilter.getFilterDesc()
		if filterDesc != "":
			filterDescSizer = self.createFilterDesc(filterDesc)
			sizer.Add(filterDescSizer, (gy, 0), span = (1,2))
			gy += 2
		
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
							#skipNextNItems = 2
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
						elif itemType == COLOC_THRESHOLD:
							self.currentRow += self.createColocalizationThresholdSelection(n, items, currentFilter)
						elif itemType == SCATTERPLOT:
							self.currentRow += self.createColocalizationThresholdSelection(n, items, currentFilter, paintScalars = 0, useBitDepth = 0)
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
		create a GUI element that allows the editing of a color transfer function
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
		self.items[itemName] = background
		setColorTransferFunction = lambda obj, event, arg, panel = colorPanel, i = item, \
								   s = self: s.onSetCtf(panel, i, arg)
	  
	  	lib.messenger.connect(currentFilter, "set_%s_ctf" % item, setColorTransferFunction)
		setotf = lambda obj, event, arg, panel = colorPanel, i = item, s = self: s.onSetOtf(panel, i, arg)
		lib.messenger.connect(currentFilter, "set_%s_otf" % item, setotf)
		
		return 0
			
	def createThresholdSelection(self, n, items, currentFilter):
		"""
		create a histogram GUI element that can be used to select a lower and upper threshold
		"""
		item = items[n]
		itemName = item[0]
		background = wx.Window(self, -1)
		level = currentFilter.getParameterLevel(itemName)
		if level:
			#background.SetBackgroundColour(level)
			background.SetForegroundColour(level)
		
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
		
		print "Setting dataUnit"
		histogram.setDataUnit(dataUnit, noupdate = 1)
		print "done"
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
		self.items[itemName] = background

		return 0

	def createColocalizationThresholdSelection(self, n, items, currentFilter, paintScalars = 1, useBitDepth = 1):
		"""
		create a scatterplot GUI element that can be used to select a lower and upper threshold
		for two channels for colocalization
		"""
		item = items[n]
		itemName = item[0]
		background = wx.Window(self, -1)
		level = currentFilter.getParameterLevel(itemName)
		if level:
			#background.SetBackgroundColour(level)
			background.SetForegroundColour(level)
		
		scatterPlot = GUI.Scatterplot.Scatterplot(background, drawLegend = 1, paintScalars = paintScalars, useBitDepth = useBitDepth)
		dataUnit = self.filter.getDataUnit()
		
		scatterPlot.setDataUnit(dataUnit)
		
		flo1 = lambda obj, event, arg, scatterPlot = scatterPlot, i = item[0], s = self: \
					s.onSetScatterplotValues(scatterPlot, i, arg, valuetype = "Lower", ch="Ch1")
		lib.messenger.connect(currentFilter, "set_%s" % item[0], flo1)
		fhi1 = lambda obj, event, arg, scatterPlot = scatterPlot, i = item[1], s = self: \
					s.onSetScatterplotValues(scatterPlot, i, arg, valuetype = "Upper", ch="Ch1")
		lib.messenger.connect(currentFilter, "set_%s" % item[1], fhi1)
		
		flo2 = lambda obj, event, arg, scatterPlot = scatterPlot, i = item[2], s = self: \
					s.onSetScatterplotValues(scatterPlot, i, arg, valuetype = "Lower", ch="Ch2")
		lib.messenger.connect(currentFilter, "set_%s" % item[2], flo2)
		fhi2 = lambda obj, event, arg, scatterPlot = scatterPlot, i = item[3], s = self: \
					s.onSetScatterplotValues(scatterPlot, i, arg, valuetype = "Upper", ch="Ch2")
		lib.messenger.connect(currentFilter, "set_%s" % item[3], fhi2)
		
		setDataunitFunc = lambda obj, event, dataunit, h = scatterPlot: h.setDataUnit(dataunit)
		
		lib.messenger.connect(currentFilter,"set_%s_dataunit"%item[0],setDataunitFunc)
		lib.messenger.connect(currentFilter,"set_%s_dataunit"%item[1],setDataunitFunc)
		lib.messenger.connect(currentFilter,"set_%s_dataunit"%item[2],setDataunitFunc)
		lib.messenger.connect(currentFilter,"set_%s_dataunit"%item[3],setDataunitFunc)
		
		setSlopeIntercept = lambda obj, event, slope, intercept, scatterPlot = scatterPlot: scatterPlot.setSlopeAndIntercept(slope, intercept)
		lib.messenger.connect(currentFilter, "set_slope_intercept", setSlopeIntercept)
		
		self.itemSizer.Add(background, (0, 0), flag=wx.EXPAND)
		
		bgsizer = wx.GridBagSizer()
		bgsizer.Add(scatterPlot, (0,0), span=(1,2))
				
		ch1lowerLbl = wx.StaticText(background, -1,"Ch1 lower:")
		ch1upperLbl = wx.StaticText(background,-1,"Ch1 upper:")
		#ch1lower = self.createNumberInput(background, currentFilter, item[0], types.IntType, 0, "", self.updateThresholdHistogram)
		#ch1upper = self.createNumberInput(background, currentFilter, item[1], types.IntType, 255, "", self.updateThresholdHistogram)
		ch2lowerLbl = wx.StaticText(background, -1,"Ch2 lower:")
		ch2upperLbl = wx.StaticText(background,-1,"Ch2 upper:")
		#ch2lower = self.createNumberInput(background, currentFilter, item[2], types.IntType, 0, "", self.updateThresholdHistogram)
		#ch2upper = self.createNumberInput(background, currentFilter, item[3], types.IntType, 255, "", self.updateThresholdHistogram)


		ch1lower = self.createSlider(currentFilter, item[0],item[0], background)
		ch1upper = self.createSlider(currentFilter, item[1],item[1], background)
		ch2lower = self.createSlider(currentFilter, item[2],item[2], background)
		ch2upper = self.createSlider(currentFilter, item[3],item[3], background)

		inputs = [ch1lower, ch1upper, ch2lower, ch2upper]
		setScatterplotFunc = lambda obj, event, th1, th2, f = currentFilter, inputs = inputs, item = item: self.setScatterplotThresholds(obj, event, th1, th2, f, item, inputs)
		lib.messenger.connect(scatterPlot, "scatterplot_thresholds", setScatterplotFunc)

		bgsizer.Add(ch1lowerLbl,(1,0))
		bgsizer.Add(ch1lower,(1,1))
		bgsizer.Add(ch1upperLbl,(2,0))
		bgsizer.Add(ch1upper,(2,1))
		bgsizer.Add(ch2lowerLbl,(3,0))
		bgsizer.Add(ch2lower,(3,1))
		bgsizer.Add(ch2upperLbl,(4,0))
		bgsizer.Add(ch2upper,(4,1))
		background.SetSizer(bgsizer)
		background.SetAutoLayout(1)
		background.Layout()
		self.items[itemName] = background
		
		return 0

	def setScatterplotThresholds(self, scatterplot, event, ch1thresholds, ch2thresholds, currentFilter, item, inputs):
		"""
		Set the filter thresholds from scatterplot
		"""
		lower1, upper1 = ch1thresholds
		lower2, upper2 = ch2thresholds
		inputs[0].SetValue(lower1)
		inputs[1].SetValue(upper1)
		inputs[2].SetValue(lower2)
		inputs[3].SetValue(upper2)
		currentFilter.set("LowerThresholdCh1",lower1)
		currentFilter.set("UpperThresholdCh1",upper1)
		currentFilter.set("LowerThresholdCh2",lower2)
		currentFilter.set("UpperThresholdCh2",upper2)

	def updateThresholdHistogram(self, event, input, parameter, itemType, currentFilter):
		"""
		Update the threshold histogram
		"""
		currentFilter.sendUpdateGUI([parameter])
		
	def createMultiPixelSelection(self, n, items, currentFilter):
		"""
		create a GUI element that allows the user to select (and remove selection of) multiple pixels
		"""
		pixelsizer = wx.GridBagSizer()
		background = wx.Window(self, -1)
		itemName = items[n]
		level = currentFilter.getParameterLevel(itemName)
		if level:
			#background.SetBackgroundColour(level)
			background.SetForegroundColour(level)
		
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
		self.items[itemName] = background

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
		create a GUI element for selecting a pixel from the preview
		"""
		background = wx.Window(self, -1)
		itemName = items[n]
		level = currentFilter.getParameterLevel(itemName)
		if level:
			#background.SetBackgroundColour(level)
			background.SetForegroundColour(level)

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
		self.items[itemName] = background
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
		create a dropdown menu to select a ROI
		"""
		box = wx.BoxSizer(wx.VERTICAL)
		itemName = items[n]
		item = items[n]
		text = currentFilter.getDesc(itemName)
		val = 0
		
		label = wx.StaticText(self, -1, text)
		box.Add(label)
		regionsOfInterest = scripting.visualizer.getRegionsOfInterest()
		choices = []
		for roi in regionsOfInterest:
			if roi.getName() not in choices:
				choices.append(roi.getName())
		
		def updateROIs(currentFilter, itemName, choice):
			regionsOfInterest = scripting.visualizer.getRegionsOfInterest()
			choices = []
			for roi in regionsOfInterest:
				if roi.getName() not in choices:
					choices.append(roi.getName())
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
		self.items[itemName] = box

		return 1

	def createChoice(self, n, items, currentFilter):
		"""
		create a choice (a dropdown menu) gui element
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
				#label.SetBackgroundColour(level)
				label.SetForegroundColour(level)
			#background.SetBackgroundColour(level)
			background.SetForegroundColour(level)
		choice.Bind(wx.EVT_CHOICE, updateChoiceFunc)

		longDesc = currentFilter.getLongDesc(itemName)
		if longDesc:
			choice.SetToolTip(wx.ToolTip(s))

		setChoiceFunc = lambda obj, event, arg, c = choice, i = itemName, s = self: \
								s.onSetChoiceFromFilter(c, i, arg)
		lib.messenger.connect(currentFilter, "set_%s" % itemName, setChoiceFunc) 

		box.Add(background, 1)
		self.itemSizer.Add(box, (self.currentRow, 0), flag = wx.EXPAND | wx.HORIZONTAL)
		self.items[itemName] = box
		#for item in choices:

		return 1

	def createRadioChoice(self, n, items, currentFilter):
		"""
		create a radio choice GUI element
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
			level = currentFilter.getParameterLevel(i)
			filterDescription = currentFilter.getDesc(i)
			itemToDesc[i] = filterDescription
			choices.append(filterDescription)
			setRadioFunc = lambda obj, event, arg, box, s = self: s.onSetRadioBox(box, event.split("_")[1], arg)
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
		self.items[itemName] = box

		spec="rows"
		if majordim == wx.RA_SPECIFY_COLS:
			spec = "columns"

		return 0
		
	def createSliceSelection(self, n, items, currentFilter, parent = None):
		"""
		create a slice selection slider GUI element
		"""
		itemName = items[n]
		item = items[n]
		level = currentFilter.getParameterLevel(itemName)
		
		if not parent:
			parent = self
		text = currentFilter.getDesc(itemName)
		box = wx.BoxSizer(wx.VERTICAL)
		if text:
			label = wx.StaticText(self, -1, text)
			box.Add(label)
		background = wx.Window(parent, -1)
		
		slider = self.createSlider(currentFilter, itemName, item, background)
		if level:
			#background.SetBackgroundColour(level)
			background.SetForegroundColour(level)
			if text:
				#label.SetBackgroundColour(level)
				label.SetForegroundColour(level)
		
		box.Add(background, 1)
		self.itemSizer.Add(box, (self.currentRow, 0), flag = wx.EXPAND | wx.HORIZONTAL)
		self.items[itemName] = box

		return 1
		
	def createSlider(self, currentFilter, itemName, item, parent):
		"""
		Create a slider
		"""
		defValue = currentFilter.getDefaultValue(itemName)
		minval, maxval = currentFilter.getRange(itemName)
		#x = max(200, maxval)
		x = 256
		
		slider = wx.Slider(parent, -1, value = defValue, minValue = minval, maxValue = maxval,
		style = wx.SL_HORIZONTAL | wx.SL_LABELS | wx.SL_AUTOTICKS, size = (x, -1))
		
		longDesc = currentFilter.getLongDesc(itemName)
		if longDesc:
			slider.SetToolTip(wx.ToolTip(s))
		
				
		onSliderScroll = lambda event, its = item, f = currentFilter: \
								self.onSetSliderValue(event, its, f, final = False)
		onSliderScrollFinal = lambda event, its = item, f = currentFilter: \
								self.onSetSliderValue(event, its, f, final = True)
								
		slider.Bind(wx.EVT_SCROLL, onSliderScroll)
		slider.Bind(wx.EVT_SCROLL_THUMBRELEASE, onSliderScrollFinal)
		slider.Bind(wx.EVT_SCROLL_CHANGED, onSliderScrollFinal)
		setSliderFunc = lambda obj, event, arg, slider = slider, i = itemName, s = self: \
								s.onSetSlice(slider, i, arg)
			
		lib.messenger.connect(currentFilter, "set_%s" % itemName, setSliderFunc)

		
		updateSliderFunc = lambda obj, event, slider = slider, i = itemName, \
					fi = currentFilter, s = self: s.updateRange(fi, i, slider)
		lib.messenger.connect(currentFilter, "update_%s" % itemName, updateSliderFunc)
		return slider
		
	def updateRange(self, currentFilter, itemName, slider):
		"""
		Update the range of a slider or a spin box
		"""
		minval, maxval = currentFilter.getRange(itemName)
		slider.SetRange(minval, maxval)
		
	def createFileSelection(self, n, items, currentFilter):
		"""
		create a file selection GUI element that shows the filename and has a button to select a file
		"""
		itemName = items[n][0]

		box = wx.BoxSizer(wx.VERTICAL)
		text = currentFilter.getDesc(itemName)
		defValue = currentFilter.getDefaultValue(itemName)
		ftype = defValue.split(".")[-1]
		conf = Configuration.getConfiguration()
		remember = conf.getConfigItem("RememberPath", "Paths")
		lastPath = ""
		if remember:
			lastPath = conf.getConfigItem("LastPath_%s"%ftype, "Paths")
			if not lastPath:
				lastPath = "."

		updateFilenameFunc = lambda event, its = items[n], f = currentFilter, i = itemName, \
						s = self: s.onSetFileName(f, i, event)

		browse = FileBrowseButton(self, -1, size = (400, -1), labelText = text, 
		fileMask = items[n][2], dialogTitle = items[n][1], startDirectory = lastPath, changeCallback = updateFilenameFunc)

		browse.SetValue(defValue)
		setFilenameFunc = lambda obj, event, arg, b = browse, i = itemName, s = self: \
									s.onSetFileNameFromFilter(b, i, arg)
		lib.messenger.connect(currentFilter, "set_%s" % itemName, setFilenameFunc) 
									
		longDesc = currentFilter.getLongDesc(itemName)
		if longDesc:
			browse.SetToolTip(wx.ToolTip(s))

		box.Add(browse, 1)
		self.itemSizer.Add(box, (self.currentRow, 0), flag = wx.EXPAND | wx.HORIZONTAL)
		self.items[itemName] = box

		return 1
							
	def buildChannelSelection(self):
		"""
		Build a GUI for selecting the source channels
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
		Set the parameter to the value of the choice widget
		"""			  
		value = event.GetSelection()
		filter.setParameter(item, value)		
		
	def onSetROI(self, regionsOfInterest, filter, item, event):
		"""
		Set the parameter to the ROI corresponding to the value of the choice widget
		"""			  
		value = event.GetSelection()
		regionsOfInterest = scripting.visualizer.getRegionsOfInterest()
		filter.setParameter(item, (value, regionsOfInterest[value]))
				
		
	def onSetFileName(self, filter, item, event):
		"""
		Set the file name
		"""			  
		filename = event.GetString()
		filter.setParameter(item, filename)
		if filename == filter.getDefaultValue(item):
			return
		
		conf = Configuration.getConfiguration()
		remember = conf.getConfigItem("RememberPath", "Paths")
		ftype = filename.split(".")[-1]
		if remember:
			conf.setConfigItem("LastPath_%s"%ftype, "Paths", os.path.dirname(filename))
		
	def onSetChoiceFromFilter(self, cc, itemName, value):
		"""
		Set the file name
		"""			  
		cc.SetSelection(value)
	
	def onSetFileNameFromFilter(self, browseButton, itemName, value):
		"""
		Set the file name
		"""
		browseButton.SetValue(value)
		
	def onSetRadioBox(self, box, item, value):
		"""
		Set the value for the GUI item 
		"""
		selectionValue = box.itemToDesc[item]
		if value:
			box.SetStringSelection(selectionValue)
		
	def onSetSlice(self, slider, item, value):
		"""
		Set the value for the GUI item 
		"""
		slider.SetValue(value)

	def onSetSpinFromFilter(self, spin, item, value):
		"""
		Set the value for the GUI item 
		"""							
		spin.SetValue(value)

	def onSetInputChannel(self, currentFilter, inputNum, event):
		"""
		Set the input channel number #inputNum
		"""				 
		n = event.GetSelection()
		self.currentFilter.setInputChannel(inputNum, n)
		
	def createGUIElement(self, currentFilter, itemSizer, item, x, y, useOld = 0):
		"""
		Build the GUI related to one specific item
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
			updatef = lambda obj, event, arg, label = label, i = item, s = self: label.SetLabel(arg)

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
			#label.SetBackgroundColour(level)
			label.SetForegroundColour(level)
		
		if level:		   
			#background.SetBackgroundColour(level)
			background.SetForegroundColour(level)
		
		if itemType in [types.IntType, types.FloatType]:
			input = self.createNumberInput(background, currentFilter, item, itemType, defaultValue, desc)
			inputtype="Integer"
			if itemType==types.FloatType:inputtype="Float"
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
		self.items[item] = background
		
		if useOther:
			self.currentBackgroundSizer	 = self.newItemSizer
		return (x, y)
						
	def createNumberInput(self, parent, currentFilter, item, itemType, defaultValue, label = "", chainFunction = None):
		"""
		Return the input for int type
		"""
		input = wx.TextCtrl(parent, -1, str(defaultValue), style = wx.TE_PROCESS_ENTER)
		valid = lambda event, f = currentFilter, p = item, t = itemType, \
							i = input:self.validateAndPassOn(event, i, p, itemType, f, chainFunction)
		input.Bind(wx.EVT_TEXT_ENTER, valid)
		input.Bind(wx.EVT_KILL_FOCUS, valid)
		input.Bind(wx.EVT_TEXT, valid)
		
		f = lambda obj, event, arg, input = input, it = item, s = self: s.onSetNumber(input, it, arg)
		lib.messenger.connect(currentFilter, "set_%s" % item, f)
		return input
		
	def createSpinInput(self, parent, currentFilter, itemName, itemType, defaultValue, label = ""):
		"""
		Return the input for int type
		"""
		minval, maxval = currentFilter.getRange(itemName)
		
		spin = wx.SpinCtrl(parent, -1, style = wx.SP_VERTICAL)
		spin.SetRange(minval,maxval)
		func = lambda event, its = itemName, sp = spin, f = currentFilter:self.onSetSpinValue(event, sp, its, f)
		spin.Bind(wx.EVT_SPINCTRL, func)
		spin.Bind(wx.EVT_TEXT, func)
		
		f = lambda obj, event, arg, spin = spin, i = itemName, s = self: s.onSetSpinFromFilter(spin, i, arg)
			
		lib.messenger.connect(currentFilter, "set_%s" % itemName, f)

		f = lambda obj, event, spin = spin, i = itemName, fi = currentFilter, s = self: s.updateRange(fi, i, spin)
		lib.messenger.connect(currentFilter, "update_%s" % itemName, f)
		
		return spin

	def createFilterDesc(self, filterDesc = ""):
		"""
		Create filter description
		"""
		fdWin = wx.Window(self, -1)
		fdSizer = wx.BoxSizer(wx.HORIZONTAL)
		fdWin.SetSizer(fdSizer)
		fdWin.SetAutoLayout(1)
		filterDescText = wx.StaticText(fdWin, -1, filterDesc)
		fdSizer.Add(filterDescText)
		filterDescText.SetBackgroundColour((213,213,237))
		fdWin.SetBackgroundColour((213,213,237))
		filterDescText.Wrap(330)
		fdWin.Layout()

		#descBox = wx.StaticBox(self, -1, "Description")
		#descBoxSizer = wx.StaticBoxSizer(descBox, wx.VERTICAL)
		#descBoxSizer.Add(fdWin)
		return fdWin


	def updateLabel(self, obj, label):
		"""
		update the label of an object
		"""
		obj.SetLabel(label)
	

	def onSetNumber(self, input, item, value):
		"""
		Set the value for the GUI item
		"""
		input.ChangeValue(str(value))

	def onSetBool(self, input, item, value):
		"""
		Set the value for the GUI item
		"""				
		input.SetValue(value)
	
	def createBooleanInput(self, parent, currentFilter, item, itemType, defaultValue, label = ""):
		"""
		Return the input for boolean type
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
		Remove a seed from filter
		"""			
		item = listbox.itemName
		n = listbox.GetSelection()
		if n != wx.NOT_FOUND:
			s = listbox.GetString(n)
			seedPoint = eval(s)
			listbox.Delete(n)
			
		seeds = currFilter.getParameter(item)   
		seeds.remove(seedPoint)
		currFilter.setParameter(item, seeds)

	def onAddPixel(self, obj, event, rx, ry, rz, r, g, b, alpha, \
					colorTransferFunction, item, currFilter, listbox):
		"""
		Add a value to the pixel listbox
		"""
		if listbox.selectPixel:
			seeds = currFilter.getParameter('Seed') # item[0])
			seeds.append((rx, ry, rz))
			currFilter.setParameter('Seed',seeds) # item[0], seeds)
			listbox.Append("(%d, %d, %d)" % (rx, ry, rz))
			listbox.selectPixel = 0

			
	def onSetPixel(self, obj, event, rx, ry, rz, r, g, b, alpha, \
					colorTransferFunction, item, currFilter, valueLabel):
		"""
		Set the value of the pixel label
		"""				
		if valueLabel.selectPixel:
			currFilter.setParameter(item[0], (rx, ry, rz))
			valueLabel.SetLabel("(%d, %d, %d)" % (rx, ry, rz))
			valueLabel.selectPixel = 0
			
	def onSetPixelFromFilter(self, label, item, value):
		"""
		Set the value of the pixel label from a variable
		"""				
		rx, ry, rz = value
		label.SetLabel("(%d, %d, %d)" % (rx, ry, rz))

	def onSetPixelsFromFilter(self, listbox, item, value):
		"""
		Set the value of the pixel label from a variable
		"""
		listbox.Clear()
		for rx, ry, rz in value:
			listbox.Append("(%d, %d, %d)" % (rx, ry, rz))			 

	def onSetHistogramValues(self, histogram, item, value, valuetype = "Lower"):
		"""
		Set the lower and upper threshold for histogram
		"""
		eval("histogram.set%sThreshold(value)" % valuetype)
		
	def onSetScatterplotValues(self, scatterplot, item, value, valuetype = "Lower", ch="Ch1"):
		eval("scatterplot.set%s%sThreshold(value)"%(ch,valuetype))
		scatterplot.updatePreview()

	def onSetCtf(self, colorPanel, item, value):
		"""
		Set the color transfer function editor colorTransferFunction
		"""
		colorPanel.setColorTransferFunction(value)
		
	def onSetOtf(self, colorPanel, item, value):
		"""
		Set the color transfer function editor otf
		"""
		colorPanel.setOpacityTransferFunction(value)
			
	def onSetThreshold(self, event, items, currentFilter):
		"""
		Process an event from the histogram
		"""
		thresholds = event.getThresholds()
		for i, item in enumerate(items):
			currentFilter.setParameter(item, thresholds[i])
		currentFilter.sendUpdateGUI(items)
			
	def onSetSliderValue(self, event, items, currentFilter, final = False):
		"""
		Set the slider value
		"""
		value = event.GetPosition()
		if final:
			currentFilter.setParameter(items, value)
		else:
			currentFilter.set(items, value)
			
	def onSetSpinValue(self, event, spinbox, itemName, currentFilter):
		"""
		Set the spin value
		"""		 
		value = spinbox.GetValue()
		value = int(value)
		currentFilter.setParameter(itemName, value)
			
	def onSelectRadioBox(self, event, items, currentFilter):
		"""
		Process an event from a radio box
		"""
		selection = event.GetSelection()
		
		for i, item in enumerate(items):
			flag = (i == selection)
			currentFilter.setParameter(item, flag)
		
	def validateAndPassOn(self, event, input, parameter, itemType, currentFilter, chain = None):
		"""
		Build the GUI for a given filter
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
		
	def onFocus(self, event):
		"""
		Pass focus event to prevent jumping around in scrolled panel
		"""
		pass
	
