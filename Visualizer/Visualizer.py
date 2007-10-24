# -*- coding: iso-8859-1 -*-

"""
 Unit: Visualizer
 Project: BioImageXD
 Created: 28.04.2005, KP
 Description:

 A visualization framework for the BioImageXD software

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
__author__ = "BioImageXD Project"
__version__ = "$Revision: 1.9 $"
__date__ = "$Date: 2005 / 01 / 13 13: 42: 03 $"

import wx
import time
import lib.messenger
import os
import GUI.Dialogs
import Logging
import GUI.MenuManager
import GUI.Histogram
import GUI.AnnotationToolbar
import platform
import os.path
import sys
import lib.Command
import Modules
import Configuration
import scripting
import GUI.Toolbar
import GUI.UIElements

visualizerInstance = None

def getVisualizer():
	global visualizerInstance
	return visualizerInstance

class Visualizer:
	"""
	Created: 05.04.2005, KP
	Description: A class that is the controller for the visualization
	"""
	def __init__(self, parent, menuManager, mainwin, **kws):
		"""
		Created: 28.04.2005, KP
		Description: Initialization
		"""
		global visualizerInstance
		visualizerInstance = self
		self.masks = []
		self.setLater = 0
		self.currentMask = None
		self.currSliderPanel = None
		self.delayed = 0
		self.immediateRender = 1
		self.oldEnabled = 1
		self.noRender = 0
		self.oldClientSize = 0
		self.updateFactor = 0.001
		self.depthT = 0
		self.zoomToFitFlag = 1

		self.conf = Configuration.getConfiguration()
		self.zoomFactor = 1.0
		scripting.zoomFactor = self.zoomFactor

		self.tb = None
		self.z = 0
		self.viewCombo = None
		self.histogramIsShowing = 0
		self.blockTpUpdate = 0
		self.histogramDataUnit = None
		self.histograms = []
		self.changing = 0
		self.mainwin = mainwin
		self.menuManager = menuManager
		self.renderingTime = 0
		self.lastWinSaveTime = 0
		self.firstLoad = {}
		self.in_vtk = 0
		self.parent = parent
		lib.messenger.connect(None, "timepoint_changed", self.onSetTimepoint)

		lib.messenger.connect(None, "data_changed", self.updateRendering)
		lib.messenger.connect(None, "itf_update", self.updateRendering)
		self.closed = 0
		self.initialized = 0
		self.renderer = None
		self.dataUnit = None
		self.enabled = 1
		self.timepoint = 0
		self.preload = 0
		self.processedMode = 0
		self.maxTimepoint = 0
		self.modes = Modules.DynamicLoader.getVisualizationModes()
		self.instances = {}
		for key in self.modes.keys():
			self.instances[key] = None

		lib.messenger.connect(None, "show", self.onSetVisibility)
		lib.messenger.connect(None, "hide", self.onSetVisibility)

		self.sizes = {}

		self.parent.Bind(
			wx.EVT_SASH_DRAGGED_RANGE, self.onSashDrag,
			id = GUI.MenuManager.ID_TOOL_WIN, id2 = GUI.MenuManager.ID_HISTOGRAM_WIN,
		)

		self.sidebarWin = wx.SashLayoutWindow(self.parent, \
											GUI.MenuManager.ID_VISTREE_WIN, \
											style = wx.RAISED_BORDER | wx.SW_3D)
		self.sidebarWin.SetOrientation(wx.LAYOUT_VERTICAL)
		self.sidebarWin.SetAlignment(wx.LAYOUT_LEFT)
		self.sidebarWin.SetSashVisible(wx.SASH_RIGHT, True)
		self.sidebarWin.SetSashBorder(wx.SASH_RIGHT, True)
		self.sidebarWin.SetDefaultSize((200, 768))
		self.sidebarWin.origSize = (200, 768)

		self.toolWin = wx.SashLayoutWindow(self.parent, GUI.MenuManager.ID_TOOL_WIN, style = wx.NO_BORDER)
		self.toolWin.SetOrientation(wx.LAYOUT_HORIZONTAL)
		self.toolWin.SetAlignment(wx.LAYOUT_TOP)
		self.toolWin.SetSashVisible(wx.SASH_BOTTOM, False)
		self.toolWin.SetDefaultSize((500, 44))
		self.toolWin.origSize = (500, 44)

		self.annotateBarWin = wx.SashLayoutWindow(self.parent, \
												GUI.MenuManager.ID_ANNOTATION_WIN, \
												style = wx.NO_BORDER)
		self.annotateBarWin.SetOrientation(wx.LAYOUT_VERTICAL)
		self.annotateBarWin.SetAlignment(wx.LAYOUT_RIGHT)

		self.annotateBarWin.SetDefaultSize((70, 768))
		self.annotateBarWin.origSize = (70, 768)

		self.annotateBar = GUI.AnnotationToolbar.AnnotationToolbar(self.annotateBarWin, self)
		self.histogramWin = wx.SashLayoutWindow(self.parent, \
												GUI.MenuManager.ID_HISTOGRAM_WIN, \
												style = wx.NO_BORDER)
		self.histogramWin.SetOrientation(wx.LAYOUT_HORIZONTAL)
		self.histogramWin.SetAlignment(wx.LAYOUT_TOP)
		self.histogramWin.SetDefaultSize((500, 0))

		self.histogramPanel = wx.Panel(self.histogramWin)
		self.histogramBox = wx.BoxSizer(wx.HORIZONTAL)

		self.histogramPanel.SetSizer(self.histogramBox)
		self.histogramPanel.SetAutoLayout(1)
		self.histogramBox.Fit(self.histogramPanel)

		self.visWin = wx.SashLayoutWindow(self.parent, \
											GUI.MenuManager.ID_VISAREA_WIN, \
											style = wx.NO_BORDER | wx.SW_3D)
		self.visWin.SetOrientation(wx.LAYOUT_VERTICAL)
		self.visWin.SetAlignment(wx.LAYOUT_LEFT)
		self.visWin.SetSashVisible(wx.SASH_RIGHT, False)
		self.visWin.SetSashVisible(wx.SASH_LEFT, False)
		self.visWin.SetDefaultSize((512, 768))

		self.sliderWin = wx.SashLayoutWindow(self.parent, \
											GUI.MenuManager.ID_VISSLIDER_WIN, \
											style = wx.NO_BORDER)
		self.sliderWin.SetOrientation(wx.LAYOUT_HORIZONTAL)
		self.sliderWin.SetAlignment(wx.LAYOUT_BOTTOM)
		self.sliderWin.SetSashVisible(wx.SASH_TOP, False)
		self.sliderWin.SetDefaultSize((500, 64))
		self.sliderWin.origSize = (500, 64)

		self.zsliderWin = wx.SashLayoutWindow(self.parent, \
												GUI.MenuManager.ID_ZSLIDER_WIN, \
												style = wx.NO_BORDER | wx.SW_3D)
		self.zsliderWin.SetOrientation(wx.LAYOUT_VERTICAL)
		self.zsliderWin.SetAlignment(wx.LAYOUT_RIGHT)
		self.zsliderWin.SetSashVisible(wx.SASH_RIGHT, False)
		self.zsliderWin.SetSashVisible(wx.SASH_LEFT, False)
		self.zsliderWin.SetDefaultSize((64, 768))
		window = 64
		if platform.system() == 'Darwin':
			window = 44
		self.zsliderWin.origSize = (window, 768)

		self.sliderbox = None
		self.zsliderPanel = None
		self.sliderPanel = None
		self.timeslider = None
		self.timesliderMethod = None
		self.upbtn = None
		self.downbtn = None
		self.next = None
		self.zslider = None
		self.zsliderSizer = None
		self.prev = None
		self.sliderbox = None

		self.createSliders()

		self.currMode = None
		self.currModeModule = None
		self.currentWindow = None
		self.galleryPanel = None
		self.preview = None
		self.sectionsPanel = None
		self.mode = None

		self.parent.Bind(wx.EVT_SIZE, self.OnSize)
		self.dimInfo = None
		self.yaw = None
		self.elevation = None
		self.zoomCombo = None
		self.roll = None
		self.pitch = None
		self.zoomLevels = None
		self.maxWidth = None
		self.origBtn = None

		self.createToolbar()

	def getMasks(self):
		"""
		Created: 20.06.2006, KP
		Description: Get all the masks
		"""
		return self.masks

	def setMask(self, mask):
		"""
		Created: 20.06.2006, KP
		Description: Set the current mask
		"""
		self.masks.insert(0, mask)
		self.currentMask = mask
		self.dataUnit.setMask(mask)

	def createSliders(self):
		"""
		Created: 1.08.2005, KP
		Description: Method that creates the sliders
		"""
		self.sliderPanel = wx.Panel(self.sliderWin, -1)
		self.setCurrentSliderPanel(self.sliderPanel)
		iconpath = scripting.get_icon_dir()
		leftarrow = wx.Image(os.path.join(iconpath, "leftarrow.gif"), wx.BITMAP_TYPE_GIF).ConvertToBitmap()
		rightarrow = wx.Image(os.path.join(iconpath, "rightarrow.gif"), wx.BITMAP_TYPE_GIF).ConvertToBitmap()
		uparrow = wx.Image(os.path.join(iconpath, "uparrow.gif"), wx.BITMAP_TYPE_GIF).ConvertToBitmap()
		downarrow = wx.Image(os.path.join(iconpath, "downarrow.gif"), wx.BITMAP_TYPE_GIF).ConvertToBitmap()

		self.prev = wx.BitmapButton(self.sliderPanel, -1, leftarrow)
		self.prev.SetSize((64, 64))
		self.next = wx.BitmapButton(self.sliderPanel, -1, rightarrow)
		self.next.SetSize((64, 64))

		self.sliderbox = wx.BoxSizer(wx.HORIZONTAL)
		self.prev.Bind(wx.EVT_BUTTON, self.onPrevTimepoint)
		self.next.Bind(wx.EVT_BUTTON, self.onNextTimepoint)

		self.timeslider = wx.Slider(self.sliderPanel, value = 1, minValue = 0, maxValue = 1,
		style = wx.SL_HORIZONTAL | wx.SL_LABELS)
		self.timeslider.SetHelpText("Use this slider to select the displayed timepoint.")
		self.bindTimeslider(self.onUpdateTimepoint)

		self.zsliderPanel = wx.Panel(self.zsliderWin)
		boxsizer = wx.BoxSizer(wx.VERTICAL)
		self.zslider = wx.Slider(self.zsliderPanel, value = 1, minValue = 0, maxValue = 1,
		style = wx.SL_VERTICAL | wx.SL_LABELS | wx.SL_AUTOTICKS)

		self.upbtn = wx.BitmapButton(self.zsliderPanel, -1, uparrow)
		self.downbtn = wx.BitmapButton(self.zsliderPanel, -1, downarrow)

		self.downbtn.Bind(wx.EVT_BUTTON, self.onSliceDown)
		self.upbtn.Bind(wx.EVT_BUTTON, self.onSliceUp)
		boxsizer.Add(self.upbtn)
		boxsizer.Add(self.zslider, 1)
		boxsizer.Add(self.downbtn)

		self.zsliderPanel.SetSizer(boxsizer)
		self.zsliderPanel.SetAutoLayout(1)
		self.zsliderSizer = boxsizer
		self.zsliderSizer.Fit(self.zsliderPanel)

		self.zslider.SetHelpText("Use this slider to select the displayed optical slice.")
		self.zslider.Bind(wx.EVT_SCROLL, self.onChangeZSlice)
		self.zslider.Bind(wx.EVT_SCROLL_PAGEDOWN, self.onZPageDown)
		self.zslider.Bind(wx.EVT_SCROLL_PAGEUP, self.onZPageUp)
		lib.messenger.connect(None, "zslice_changed", self.onChangeZSlice)

		self.sliderbox.Add(self.prev, flag = wx.ALIGN_CENTER_VERTICAL)
		self.sliderbox.Add(self.timeslider, 1)
		self.sliderbox.Add(self.next, flag = wx.ALIGN_CENTER_VERTICAL)
		self.sliderPanel.SetSizer(self.sliderbox)
		self.sliderPanel.SetAutoLayout(1)
		self.sliderbox.Fit(self.sliderPanel)

	def onSliceUp(self, evt = None):
		"""
		Created: 15.11.2006, KP
		Description: Move one slice up
		"""
		newZSliderValue = self.zslider.GetValue() - 1
		if newZSliderValue >= self.zslider.GetMin():
			self.zslider.SetValue(newZSliderValue)
			self.onChangeZSlice(None)

	def onSliceDown(self, evt = None):
		"""
		Created: 15.11.2006, KP
		Description: Move one slice down
		"""
		newZSliderValue = self.zslider.GetValue() + 1
		if newZSliderValue <= self.zslider.GetMax():
			self.zslider.SetValue(newZSliderValue)
			self.onChangeZSlice(None)

	def bindTimeslider(self, method, all = 0):
		"""
		Created: 15.08.2005, KP
		Description: Bind the timeslider to a method
		"""
		if not all and platform.system() == "Windows":
			self.timeslider.Unbind(wx.EVT_SCROLL_ENDSCROLL)
			self.timeslider.Bind(wx.EVT_SCROLL_ENDSCROLL, method)
		elif not all and platform.system() == "Darwin":
			self.timeslider.Bind(wx.EVT_SCROLL_THUMBRELEASE, method)
		else:
			self.timesliderMethod = method
			self.timeslider.Unbind(wx.EVT_SCROLL)
			self.timeslider.Bind(wx.EVT_SCROLL, self.delayedTimesliderEvent)

	def onSetVisibility(self, obj, evt, arg):
		"""
		Created: 12.07.2005, KP
		Description: Set an object's visibility
		"""
		obj = None
		if arg == "toolbar":
			obj = self.toolWin
		elif arg == "zslider":
			obj = self.zsliderWin
		elif arg == "histogram":
			obj = self.histogramWin
			width, height = 0, 0
			for i in self.histograms:
				width2, height2 = i[0].GetSize()
				width = width2
				if height < height2:
					height = height2
			Logging.info("Got ", width, height, "for histogram size", kw = "visualizer")
			if not height:
				height = 200
			self.sizes["histogram"] = width, height
		elif arg == "config": obj = self.sidebarWin
		if evt == "hide":
			Logging.info("Hiding ", arg, " = ", obj, kw = "visualizer")
			if arg not in self.sizes:
				width, height = obj.GetSize()
				self.sizes[arg] = (width, height)
			obj.SetDefaultSize((0, 0))
		else:
			Logging.info("Showing ", arg)
			if arg in self.sizes:
				obj.SetDefaultSize(self.sizes[arg])
			del self.sizes[arg]
		if evt == "show" and arg == "histogram":
			if not self.histogramIsShowing:
				self.createHistogram()
			self.histogramPanel.Layout()
			for histogram, sbox, sboxsizer in self.histograms:
				sboxsizer.Fit(histogram)
			self.histogramIsShowing = 1
		elif evt == "hide" and arg == "histogram":
			self.histogramIsShowing = 0

		self.OnSize(None)

	def getDataUnit(self):
		"""
		Created: 09.07.2005, KP
		Description: Return the dataunit that is currently shown
		"""
		return self.dataUnit

	def nextTimepoint(self):
		"""
		Created: 18.07.2005, KP
		Description: Go to next timepoint
		"""
		if self.timepoint < self.maxTimepoint:
			Logging.info("Setting timepoint to ", self.timepoint + 1, kw = "visualizer")
			self.setTimepoint(self.timepoint + 1)
			self.blockTpUpdate = 1
			lib.messenger.send(None, "timepoint_changed", self.timepoint)
			self.blockTpUpdate = 0

	def getTimepoint(self):
		"""
		Created: 06.09.2006, KP
		Description: return the current timepoint
		"""
		return self.timepoint

	def getNumberOfTimepoints(self):
		"""
		Created: 18.07.2006, KP
		Description: Return the number of timepoints
		"""
		return self.maxTimepoint

	def onNextTimepoint(self, evt):
		"""
		Created: 26.06.2005, KP
		Description: Go to next timepoint
		"""
		undo_cmd = "scripting.visualizer.prevTimepoint()"
		do_cmd = "scripting.visualizer.nextTimepoint()"
		cmd = lib.Command.Command(lib.Command.GUI_CMD, None, None, do_cmd, undo_cmd, desc = "Switch to next timepoint")
		cmd.run()

	def onPrevTimepoint(self, evt):
		"""
		Created: 26.06.2005, KP
		Description: Go to previous timepoint
		"""
		undo_cmd = "scripting.visualizer.nextTimepoint()"
		do_cmd = "scripting.visualizer.prevTimepoint()"
		cmd = lib.Command.Command(lib.Command.GUI_CMD, None, None, do_cmd, undo_cmd, desc = "Switch to previous timepoint")
		cmd.run()

	def prevTimepoint(self):
		"""
		Created: 18.07.2006, KP
		Description: Switch to previous timepoint
		"""
		if self.timepoint >= 1:
			self.setTimepoint(self.timepoint - 1)
			self.blockTpUpdate = 1
			lib.messenger.send(None, "timepoint_changed", self.timepoint)
			self.blockTpUpdate = 0

	def createHistogram(self):
		"""
		Created: 28.05.2005, KP
		Description: Method to create histograms of the dataunit
		"""
		if self.dataUnit != self.histogramDataUnit:
			self.histogramDataUnit = self.dataUnit
		for histogram, sbox, sboxsizer in self.histograms:

			self.histogramBox.Detach(sboxsizer)
			sboxsizer.Detach(histogram)
			sboxsizer.Destroy()
			sbox.Destroy()
			histogram.Destroy()
		self.histograms = []
		units = []
		if self.processedMode:
			units = self.dataUnit.getSourceDataUnits()
		else:
			units = [self.dataUnit]
		for unit in units:
			ds = unit.getDataSource()
			minval,maxval = ds.getOriginalScalarRange()
			scale = maxval / 255.0
			histogram = GUI.Histogram.Histogram(self.histogramPanel, scale = scale, lowerThreshold = minval, upperThreshold = maxval)
			dataUnitName = unit.getName()
			sbox = wx.StaticBox(self.histogramPanel, -1, "Channel %s" % dataUnitName)
			sboxsizer = wx.StaticBoxSizer(sbox, wx.VERTICAL)
			sboxsizer.Add(histogram)
			self.histogramBox.Add(sboxsizer, 1, border = 10, flag = wx.BOTTOM)
			histogram.setDataUnit(unit)
			self.histograms.append((histogram, sbox, sboxsizer))
		self.histogramPanel.Layout()
		self.OnSize(None)

	def createToolbar(self):
		"""
		Created: 28.05.2005, KP
		Description: Method to create a toolbar for the window
		"""
		icondir = scripting.get_icon_dir()
		if self.tb:
			return
		self.tb = GUI.Toolbar.Toolbar(self.toolWin, -1, style = wx.TB_HORIZONTAL)
		self.tb.SetToolBitmapSize((32, 32))

		self.maxWidth = self.parent.GetSize()[0]

		#toolSize = self.tb.GetToolSize()[0]

		self.viewCombo = wx.ComboBox(self.tb,
									GUI.MenuManager.ID_SET_VIEW,
									"Isometric",
									choices = ["+X", "-X", "+Y", "-Y", "+Z", "-Z", "Isometric"],
									size = (130, -1),
									style = wx.CB_DROPDOWN)
		self.viewCombo.SetSelection(6)
		self.viewCombo.SetHelpText("This controls the view angle of 3D view mode.")
		self.tb.AddControl(self.viewCombo)

		wx.EVT_COMBOBOX(self.parent, GUI.MenuManager.ID_SET_VIEW, self.onSetView)
		self.tb.AddSimpleTool(GUI.MenuManager.ID_ZOOM_OUT,
							wx.Image(os.path.join(icondir, "zoom-out.gif"),
									wx.BITMAP_TYPE_GIF).ConvertToBitmap(),
							"Zoom out",
							"Zoom out on the optical slice")


		self.zoomLevels = [0.1, 0.125, 0.25, 0.3333, 0.5, 0.6667, 0.75, 
		1.0, 1.25, 1.5, 2.0, 3.0, 4.0,  6.0,  8.0, -1]
		choices = ["10%", "12.5%", "25%", "33.33%", "50%", "66.67%", "75%", "100%", "125%",
					"150%", "200%",  "300%", "400%", "600%", "800%", "Zoom to fit"]

		self.zoomCombo = wx.ComboBox(self.tb,
									GUI.MenuManager.ID_ZOOM_COMBO,
									"Zoom to fit",
									choices = choices,
									size = (120, -1),
									style = wx.CB_DROPDOWN)
		self.zoomCombo.SetSelection(len(choices)-1)
		self.zoomCombo.SetHelpText("This controls the zoom level of visualization views.")
		self.tb.AddControl(self.zoomCombo)

		self.tb.AddSimpleTool(GUI.MenuManager.ID_ZOOM_IN, \
								wx.Image(os.path.join(icondir, "zoom-in.gif"), \
										wx.BITMAP_TYPE_GIF).ConvertToBitmap(), \
								"Zoom in", \
								"Zoom in on the slice")

		self.tb.AddSimpleTool(GUI.MenuManager.ID_ZOOM_TO_FIT, \
								wx.Image(os.path.join(icondir, "zoom-to-fit.gif"), \
											wx.BITMAP_TYPE_GIF).ConvertToBitmap(), \
								"Zoom to Fit", \
								"Zoom the slice so that it fits in the window")

		self.tb.AddSimpleTool(GUI.MenuManager.ID_ZOOM_OBJECT, \
								wx.Image(os.path.join(icondir, "zoom-object.gif"), \
											wx.BITMAP_TYPE_GIF).ConvertToBitmap(), \
								"Zoom object", \
								"Zoom user selected portion of the slice")



		icon = wx.Image(os.path.join(icondir, "original.gif"), wx.BITMAP_TYPE_GIF).ConvertToBitmap()
		self.tb.AddSeparator()
		self.origBtn = wx.BitmapButton(self.tb, GUI.MenuManager.ORIG_BUTTON, icon)

		self.origBtn.SetHelpText("Use this button to show how the unprocessed dataset looks like.")
		self.origBtn.Bind(wx.EVT_LEFT_DOWN, lambda x: self.onShowOriginal(x, 1))
		self.origBtn.Bind(wx.EVT_LEFT_UP, lambda x: self.onShowOriginal(x, 0))

		self.tb.AddControl(self.origBtn)
		iconpath = scripting.get_icon_dir()

		self.pitch = wx.SpinButton(self.tb, GUI.MenuManager.PITCH, style = wx.SP_VERTICAL, size = (-1, 22))
		self.tb.AddControl(self.pitch)
		self.yaw = wx.SpinButton(self.tb, GUI.MenuManager.YAW, style = wx.SP_VERTICAL, size = (-1, 22))
		self.tb.AddControl(self.yaw)
		self.roll = wx.SpinButton(self.tb, GUI.MenuManager.ROLL, style = wx.SP_VERTICAL, size = (-1, 22))
		self.tb.AddControl(self.roll)
		self.elevation = wx.SpinButton(self.tb, -1, style = wx.SP_VERTICAL, size = (-1, 22))
		self.tb.AddControl(self.elevation)

		self.dimInfo = GUI.UIElements.DimensionInfo(self.tb, -1, size = (160, 50))
		self.tb.AddControl(self.dimInfo)

		wx.EVT_TOOL(self.parent, GUI.MenuManager.ID_ZOOM_IN, self.zoomIn)
		wx.EVT_TOOL(self.parent, GUI.MenuManager.ID_ZOOM_OUT, self.zoomOut)
		wx.EVT_TOOL(self.parent, GUI.MenuManager.ID_ZOOM_TO_FIT, self.zoomToFit)
		wx.EVT_TOOL(self.parent, GUI.MenuManager.ID_ZOOM_OBJECT, self.zoomObject)

		self.zoomCombo.Bind(wx.EVT_COMBOBOX, self.zoomToComboSelection)
		self.tb.Realize()

		self.viewCombo.Enable(0)

	def onPerspectiveRendering(self, evt):
		"""
		Created: 08.11.2006, KP
		Description: Toggle perspective rendering on or off
		"""
		flag = not evt.IsChecked()
		if hasattr(self.currentWindow, "getRenderer"):
			cam = self.currentWindow.getRenderer().GetActiveCamera()
			cam.SetParallelProjection(flag)
			self.currentWindow.Render()

	def getRegionsOfInterest(self):
		"""
		Created: 04.08.2006, KP
		Description: Return all the regions of interest
		"""
		if hasattr(self.currentWindow, "getRegionsOfInterest"):
			return self.currentWindow.getRegionsOfInterest()
		return []

	def onShowOriginal(self, evt, flag = 1):
		"""
		Created: 27.07.2005, KP
		Description: Show the original datasets instead of processed ones
		"""

		if evt == "hide":
			flag = 0
		if self.dataUnit:
			self.dataUnit.getSettings().set("ShowOriginal", flag)
		self.updateRendering()
		evt.Skip()

	def onSetView(self, evt):
		"""
		Created: 22.07.2005, KP
		Description: Set view mode
		"""
		item = evt.GetString()
		viewmapping = {" + X": (1, 0, 0, 0, 0, 1), " - X": (-1, 0, 0, 0, 0, 1),
					 " + Y": (0, 1, 0, 1, 0, 0), " - Y": (0, -1, 0, 1, 0, 0),
					 " + Z": (0, 0, 1, 0, 1, 0), " - Z": (0, 0, -1, 0, 1, 0),
					 "Isometric": (1, 1, 1, 0, 0, 1)}

		if hasattr(self.currMode, "wxrenwin"):
			self.currMode.wxrenwin.setView(viewmapping[item])
			self.currMode.wxrenwin.Render()

	def zoomObject(self, evt):
		"""
		Created: 19.03.2005, KP
		Description: Lets the user select the part of the object that is zoomed
		"""
		self.zoomToFitFlag = 0
		self.currMode.zoomObject()

	def zoomOut(self, evt):
		"""
		Created: 19.03.2005, KP
		Description: Makes the zoom factor smaller
		"""
		zoomFactor = self.currMode.getZoomFactor()
		numberOfZoomLevels = len(self.zoomLevels)
		for i in range(numberOfZoomLevels - 1, 0, -1):
			if self.zoomLevels[i] > 0 and self.zoomLevels[i] < zoomFactor:
				level = self.zoomLevels[i]
				Logging.info("Current zoom factor = ", zoomFactor, "setting to", level, kw = "visualizer")
				self.setComboBoxToFactor(level)
				break
		return self.zoomComboDirection(0)

	def zoomToComboSelection(self, evt):
		"""
		Created: 19.03.2005, KP
		Description: Sets the zoom according to the combo selection
		"""
		return self.zoomComboDirection(0)
		
	def getPositionForFactor(self, factor):
		"""
		Created: 01.09.2007, KP
		Description: search the correct combobox position for the given zoom factor
		"""
		pos = 6
		for i, zoomFactor in enumerate(self.zoomLevels):
			if zoomFactor == factor:
				pos = i
				break
		return pos
				
	def setComboBoxToFactor(self, factor):
		"""
		Created: 01.08.2005, KP
		Description: Set the value of the combobox to the correct zoom factor
		"""
		pos = self.getPositionForFactor(factor)
		self.zoomCombo.SetSelection(pos)
		self.currMode.setZoomFactor(self.zoomLevels[pos])
		self.zoomFactor = self.currMode.getZoomFactor()
		scripting.zoomFactor = self.zoomFactor

	def zoomComboDirection(self, dir):
		"""
		Created: 21.02.2005, KP
		Description: Makes the zoom factor larger / smaller based on values in the zoom combobox
		"""
		pos = self.zoomCombo.GetSelection()
		#pos = self.getPositionForFactor(self.zoomFactor)
		if dir > 0 and pos >= self.zoomCombo.GetCount():
			return
		if dir < 0 and pos == 0:
			return
		pos += dir
		factor = self.zoomLevels[pos]
		self.zoomCombo.SetSelection(pos)

		if factor == -1:
			self.zoomToFitFlag = 1
			self.currMode.zoomToFit()
		else:
			self.zoomToFitFlag = 0
			self.currMode.setZoomFactor(factor)
		self.zoomFactor = self.currMode.getZoomFactor()
		scripting.zoomFactor = self.zoomFactor

		self.currMode.Render()

	def zoomIn(self, evt, factor = -1):
		"""
		Created: 21.02.2005, KP0
		Description: Makes the zoom factor larger
		"""
		zoomFactor = self.currMode.getZoomFactor()
		numberOfZoomLevels = len(self.zoomLevels)
		for i in range(0, numberOfZoomLevels):
			if self.zoomLevels[i] > zoomFactor:
				level = self.zoomLevels[i]
				self.setComboBoxToFactor(level)
				break
		return self.zoomComboDirection(0)

	def zoomToFit(self, evt = None):
		"""
		Created: 21.02.2005, KP
		Description: Sets the zoom factor to fit the image into the preview window
		"""
		self.zoomToFitFlag = 1
		self.currMode.zoomToFit()
		self.zoomCombo.SetStringSelection("Zoom to fit")
		self.currMode.Render()

	def onSashDrag(self, event = None):
		"""
		Created: 24.5.2005, KP
		Description: A method for laying out the window
		"""

		if event and event.GetDragStatus() == wx.SASH_STATUS_OUT_OF_RANGE:
			Logging.info("Out of range", kw = "visualizer")
			return
		width, height = self.sidebarWin.GetSize()
		if event:
			eID = event.GetId()
			newsize = (event.GetDragRect().width, height)
		else:
			eID = GUI.MenuManager.ID_VISTREE_WIN
			newsize = self.sidebarWin.origSize

		if eID == GUI.MenuManager.ID_VISTREE_WIN:
			Logging.info("Sidebar window size = %d, %d" % newsize, kw = "visualizer")
			self.sidebarWin.SetDefaultSize(newsize)

			self.sidebarWin.origSize = newsize

		self.OnSize(None)

	def OnSize(self, event = None):
		"""
		Created: 23.05.2005, KP
		Description: Handle size events
		"""
		wx.LayoutAlgorithm().LayoutWindow(self.parent, self.visWin)
		x, y = self.zsliderWin.GetSize()
		self.zsliderPanel.SetSize((x, y))

		visSize = self.visWin.GetClientSize()
		self.annotateBar.Layout()
		newsize = visSize[0]

		if self.currentWindow:
			self.currentWindow.SetSize(visSize)
			self.currMode.relayout()
			if self.currMode.layoutTwice() and event:
				wx.CallAfter(self.OnSize)

		self.oldClientSize = newsize
		if self.currSliderPanel:
			self.currSliderPanel.SetSize(self.sliderWin.GetSize())
		if time.time() - self.lastWinSaveTime > 5:
			self.saveWindowSizes()

	def restoreWindowSizesFromSettings(self):
		"""
		Created: 13.04.2006, KP
		Description: Restore the window sizes from settings
		"""

		item = "%s_SidebarSize" % self.mode
		ssize = self.conf.getConfigItem(item, "Sizes")
		if not ssize:
			return 0
		ssize = eval(ssize)
		self.sidebarWin.SetDefaultSize(ssize)

		if self.dataUnit and self.dataUnit.isProcessed():
			currentTask = self.mainwin.getCurrentTaskName()
			ssize = self.conf.getConfigItem("%s_TaskPanelSize"%currentTask, "Sizes")
			if ssize:
				x,y = [int(x) for x in ssize[1:-1].split(",")]
				
				self.mainwin.taskWin.SetDefaultSize((x,y))
		
		return 1

	def saveWindowSizes(self):
		"""
		Created: 13.04.2006, KP
		Description: Save window sizes to the settings
		"""
		if self.mode:
			ssize = self.sidebarWin.GetSize()
			if 0 not in ssize:
				ssize = str(ssize)
				self.conf.setConfigItem("%s_SidebarSize" % self.mode, "Sizes", ssize)
		if self.dataUnit and self.dataUnit.isProcessed():
			currentTask = self.mainwin.getCurrentTaskName()
			ssize = self.mainwin.taskWin.GetSize()
			if 0 not in ssize:
				self.conf.setConfigItem("%s_TaskPanelSize"%currentTask, "Sizes", str(ssize))

	def setCurrentSliderPanel(self, panel):
		"""
		Created: 26.01.2006, KP
		Description: Set the currently visible timeslider panel
		"""
		self.currSliderPanel = panel

	def __del__(self):
		global visualizerInstance
		visualizerInstance = None



	def setProcessedMode(self, mode):
		"""
		Created: 25.05.2005, KP
		Description: Set the visualizer to processed / unprocessed mode
		"""
		self.processedMode = mode

	def getProcessedMode(self):
		"""
		Created: 25.05.2005, KP
		Description: Return whether visualizer is in processed / unprocessed mode
		"""
		return self.processedMode

	def getCurrentWindow(self):
		"""
		Created: 23.11.2006, KP
		Description: return the current visualizer window
		"""
		return self.currentWindow

	def getCurrentMode(self):
		"""
		Created: 20.06.2005, KP
		Description: Return the current visualization mode
		"""
		return self.currMode

	def getCurrentModeName(self):
		"""
		Created: 20.06.2005, KP
		Description: Return the current visualization mode
		"""
		return self.mode

	def closeVisualizer(self):
		"""
		Created: 12.08.2005, KP
		Description: Close the visualizer
		"""
		if self.currMode:
#			self.currentWindow.enable(0)
#			self.currMode.setDataUnit(None)
#			self.currentWindow.enable(1)
#			self.Render()
			self.currentWindow.Show(0)
			self.currMode.deactivate()
			del self.currentWindow
		self.currMode = None
		self.currentWindow = None
		self.mode = None

		self.currModeModule = None
		self.dataUnit = None
		self.sidebarWin.SetDefaultSize((0, 1024))
		self.zslider.SetRange(1, 2)
		self.zslider.SetValue(1)
		wx.LayoutAlgorithm().LayoutWindow(self.parent, self.visWin)
		del self.dataUnit
		self.dataUnit = None

	def setVisualizationMode(self, mode, reload = 0):
		"""
		Created: 23.05.2005, KP
		Description: Set the mode of visualization
		"""
		if self.mode == mode:
			Logging.info("Mode %s already selected" % mode, kw = "visualizer")
			if self.dataUnit and self.currMode.dataUnit != self.dataUnit:
				Logging.info("Re - setting dataunit", kw = "visualizer")
				self.currMode.setDataUnit(self.dataUnit)
				return
		self.mode = mode

		if self.currMode:
			self.zoomFactor = self.currMode.getZoomFactor()
			scripting.zoomFactor = self.zoomFactor
			self.currentWindow.Show(0)

			self.currMode.deactivate(self.mode)
			if hasattr(self.currentWindow, "enable"):
				self.currentWindow.enable(0)

		modeclass, settingclass, module = self.modes[mode]
		modeinst = self.instances[mode]
		if reload:
			del self.instances[mode]
			modeinst = None

		if not modeinst:
			modeinst = modeclass(self.visWin, self)
			self.instances[mode] = modeinst
			self.currMode = modeinst

		if not module.showZoomToolbar():
			self.toolWin.SetDefaultSize((500, 0))
			self.annotateBarWin.SetDefaultSize((0, -1))

		else:
			self.toolWin.SetDefaultSize((500, 44))
			self.annotateBarWin.SetDefaultSize((70, -1))

		# dataunit might have been changed so set it every time a
		# mode is loaded

		self.currMode = modeinst
		self.currModeModule = module

		# Most visualization methods don't want alpha channel
		# The ones that do, can change the flag from activate()
		scripting.wantAlphaChannel = 0
		scripting.preferRGB = 1
		scripting.wantWholedataset = 1

		self.currentWindow = modeinst.activate(self.sidebarWin)

		self.sidebarWin.SetDefaultSize((0, 1024))
		wx.LayoutAlgorithm().LayoutWindow(self.parent, self.visWin)
		if not modeinst.showSliceSlider():
			print "Won't show zslider in ",modeinst
			if self.zsliderWin.GetSize()[0]:
				self.zsliderWin.SetDefaultSize((0, 1024))
		else:
			print "showing zslider"
			if self.zsliderWin.GetSize() != self.zsliderWin.origSize:
				self.zsliderWin.SetDefaultSize(self.zsliderWin.origSize)

		if modeinst.showViewAngleCombo():
			self.viewCombo.Enable(1)
		else:
			self.viewCombo.Enable(0)
		if self.zoomToFitFlag:
			self.currMode.zoomToFit()
		else:
			self.currMode.setZoomFactor(self.zoomFactor)
			scripting.zoomFactor = self.zoomFactor

		if not self.zoomToFitFlag and hasattr(self.currMode, "getZoomFactor"):
			self.setComboBoxToFactor(self.currMode.getZoomFactor())

		if not modeinst.showSideBar():
			if self.sidebarWin.GetSize()[0]:
				self.sidebarWin.SetDefaultSize((0, 1024))
		else:
			if self.sidebarWin.GetSize() != self.sidebarWin.origSize:
				flag = 0
				# If this is the first time we're loading a visualization mode, then restore the
				# size from settings
				if not self.mode in self.firstLoad:
					flag = self.restoreWindowSizesFromSettings()
					self.firstLoad[self.mode] = 1
				if not flag:
					# If restoring the size from settings failed or this is not the first time, then
					# use the sidebarWin.origSize
					self.sidebarWin.SetDefaultSize(self.sidebarWin.origSize)
		wx.LayoutAlgorithm().LayoutWindow(self.parent, self.visWin)

		self.currentWindow.enable(0)
		if self.dataUnit and modeinst.dataUnit != self.dataUnit:
			Logging.info("Re - setting dataunit", kw = "visualizer")
			modeinst.setDataUnit(self.dataUnit)

		modeinst.setTimepoint(self.timepoint)
		self.currentWindow.Show()
		if hasattr(self.currentWindow, "enable"):
			self.currentWindow.enable(self.enabled)
		lib.messenger.send(None, "visualizer_mode_loading", modeinst)

	def showItemToolbar(self, flag):
		"""
		Created: 01.06.2005, KP
		Description: Show / hide item toolbar
		"""
		pass

	def enable(self, flag, **kws):
		"""
		Created: 23.05.2005, KP
		Description: Enable / Disable updates
		"""
		self.preload = 0
		if kws.has_key("preload"):
			self.preload = kws["preload"]

		if self.noRender:
			self.oldEnabled = flag
			return
		self.enabled = flag
		if self.currentWindow:
			Logging.info("Setting enabled status of current window to %s" % (not not flag), kw = "visualizer")
			self.currentWindow.enable(flag)
		if self.setLater:
			self.setupMode()
			self.setLater = 0
		if flag:
			wx.LayoutAlgorithm().LayoutWindow(self.parent, self.visWin)
			Logging.info("Setting visualizer window to ", self.visWin.GetSize(), kw = "visualizer")
			self.currentWindow.SetSize(self.visWin.GetClientSize())

	def setBackground(self, r, g, b):
		"""
		Created: 16.05.2005, KP
		Description: Set the background color
		"""
		self.currMode.setBackground(r, g, b)

	def onClose(self, event):
		"""
		Created: 28.04.2005, KP
		Description: Called when this window is closed
		"""
		self.closed = 1

	def isClosed(self):
		"""
		Created: 28.04.2005, KP
		Description: Returns flag indicating the closure of this window
		"""
		return self.closed

	def toggleTimeSlider(self, flag):
		"""
		Created: 23.07.2006, KP
		Description: Toggle the time slider on or off
		"""
		if not flag:
			self.sliderWin.SetDefaultSize((0, 0))
		else:
			self.sliderWin.SetDefaultSize(self.sliderWin.origSize)

	def setDataUnit(self, dataunit):
		"""
		Created: 28.04.2005, KP
		Description: Sets the dataunit this module uses for visualization
		"""
		self.dataUnit = dataunit
		count = dataunit.getNumberOfTimepoints()

		self.maxTimepoint = count - 1
		if count == 1:
			Logging.info("Hiding time slider, because only one timepoint", kw="visualizer")
			self.toggleTimeSlider(0)
		else:
			Logging.info("Setting time range to %d" % count, kw = "visualizer")
			self.toggleTimeSlider(1)
			self.timeslider.SetRange(1, count)
			
		currT = modT = self.timeslider.GetValue()
		currT = max(1,currT)
		currT = min(count, currT)
		
		if currT != modT and count > 1:
			Logging.info("Setting time slider value to %d"%currT, kw="visualizer")
			oldBlock = self.blockTpUpdate
			self.blockTpUpdate = 1
			self.timeslider.SetValue(currT)
			self.blockTpUpdate = oldBlock
			

		x, y, z = dataunit.getDimensions()

		#currz = self.zslider.GetValue()
		self.zslider.SetRange(1, z)
		if self.timepoint > count:
			Logging.info("Setting timepoint to %d"%count,kw="visualizer")
			self.setTimepoint(count)

		Logging.info("Setting zslider value",kw="visualizer")
		if z < self.z:
			self.zslider.SetValue(1)
			self.onChangeZSlice(None)
		else:
			self.zslider.SetValue(self.z+1)
		if z <= 1:
			self.zsliderWin.SetDefaultSize((0, 768))
		elif self.currMode.showSliceSlider():
			self.zsliderWin.SetDefaultSize(self.zsliderWin.origSize)
		showItems = 0

		if self.processedMode:
			numberOfDataUnits = len(dataunit.getSourceDataUnits())
			if numberOfDataUnits > 1:
				showItems = 1
		self.showItemToolbar(showItems)

		if self.enabled and self.currMode:
			Logging.info("Setting up current mode", kw="visualizer")
			self.setupMode()
		else:
			Logging.info("Will set up mode later", kw="visualizer")
			self.setLater = 1
			
		if self.histogramIsShowing:
			Logging.info("Updating histogram",kw="visualizer")
			self.createHistogram()
		self.OnSize(None)

	def setupMode(self):
		"""
		Created: 09.03.2007, KP
		Description: Setup the current mode
		"""
		Logging.info("Setting dataunit to current mode", kw = "visualizer")
		self.currMode.setDataUnit(self.dataUnit)
		lib.messenger.send(None, "zslice_changed", self.z)
		self.currMode.setTimepoint(self.timepoint)
		if self.zoomToFitFlag:
			Logging.info("Will zoom to fit", kw="visualizer")
			self.currMode.zoomToFit()
		else:
			self.currMode.setZoomFactor(self.zoomFactor)
			scripting.zoomFactor = self.zoomFactor
		self.currMode.Render()
		
	def setZoomFactor(self, factor):
		"""
		Created: 01.09.2007, KP
		Description: set the zoom factor to given factor
		"""
		if self.currMode:
			if factor < 0.05:
				factor = 0.05
			if factor > 10:
				factor = 10
			self.zoomFactor = factor
			self.currMode.setZoomFactor(factor)
			scripting.zoomFactor = factor
			self.zoomCombo.SetValue("%.2f%%"%(factor*100))
			
		
	def setImmediateRender(self, flag):
		"""
		Created: 14.02.2006, KP
		Description: Toggle immediate rendering on or off
		"""
		self.immediateRender = flag

	def setNoRendering(self, flag):
		"""
		Created: 14.02.2006, KP
		Description: Toggle rendering on or off
		"""
		if not flag:
			self.noRender = flag
			self.enable(self.oldEnabled)
		else:
			self.oldEnabled = self.enabled
			self.enable(0)
			self.noRender = flag

	def isEnabled(self):
		return self.enabled

	def updateRendering(self, event = None, object = None, delay = 0):
		"""
		Created: 25.05.2005, KP
		Description: Update the rendering
		"""
		if not self.enabled:
			Logging.info("Disabled, will not update rendering", kw = "visualizer")
			return

		if not self.immediateRender and delay >= 0:
			Logging.info("Will not update rendering on other than apply button", kw = "visualizer")
			return

		Logging.info("Updating rendering", kw = "visualizer")
		imm = 1
		# If the visualization mode doesn't want immediate rendering
		# then we will delay a bit with this
		# If the delay is negative, then rendering will be immediate
		if delay >= 0:
			imm = self.currModeModule.getImmediateRendering()
		delay = self.currModeModule.getRenderingDelay()
		Logging.info("Immediate rendering = ", imm, "delay = ", delay, kw = "visualizer")
		if not imm:
			t = time.time()
			delay /= 1000.0
			if not self.renderingTime:
				self.renderingTime = t - (delay * 2)
			diff = t - self.renderingTime
			Logging.info("diff in renderTime = ", diff, kw = "visualizer")
			if diff < delay and not self.delayed:
				diff = 200 + int(1000 * diff)
				Logging.info("Delaying, delay = %f, diff = %d" % (delay, diff), kw = "visualizer")
				self.delayed = 1
				wx.FutureCall(diff, self.updateRendering)
				return
		Logging.info("Updating rendering", kw = "visualizer")
		self.renderingTime = time.time()
		self.currMode.updateRendering()
		self.delayed = 0

	def Render(self, evt = None):
		"""
		Created: 28.04.2005, KP
		Description: Render the scene
		"""
		if self.enabled:
			self.currMode.Render()


	def onZPageDown(self, evt):
		"""
		Created: 26.10.2006, KP
		Description: Callback for when the z slider is "paged down"
		"""
		newpos = self.zslider.GetValue() - 1
		newpos += 10
		if newpos<0:newpos=0
		self.zslider.SetValue(newpos)

	def onZPageUp(self, evt):
		"""
		Created: 26.10.2006, KP
		Description: Callback for when the z slider is "paged up"
		"""
		newpos = self.zslider.GetValue() - 1
		newpos -= 10
		self.zslider.SetValue(newpos)

	def onChangeZSlice(self, obj, event = None, arg = None):
		"""
		Created: 1.08.2005, KP
		Description: Set the z slice to be shown
		"""
		timeValue = time.time()
		if abs(self.depthT - timeValue) < self.updateFactor:
			return
		self.depthT = time.time()

		if arg:
			newz = arg
			self.zslider.SetValue(arg + 1)
		elif (not event and not arg) and obj:
			newz = obj.GetPosition() - 1
		else:
			newz = self.zslider.GetValue() - 1

		if self.z != newz:
			self.z = newz
			lib.messenger.send(None, "zslice_changed", newz)
			
	def getZSliderValue(self):
		"""
		Created: 17.08.2007, KP
		Description: return the z slider value
		"""
		return self.zslider.GetValue()

	def onSnapshot(self, event):
		"""
		Created: 05.06.2005, KP
		Description: Save a snapshot of current visualization
		"""
		if self.currMode and self.dataUnit:
			wildCardDict = {"png": "Portable Network Graphics Image (*.png)", "jpeg": "JPEG Image (*.jpeg)",
			"tiff": "TIFF Image (*.tiff)", "bmp": "Bitmap Image (*.bmp)"}

			defaultExt = self.conf.getConfigItem("ImageFormat", "Output")
			if defaultExt == "jpg":
				defaultExt = "jpeg"
			if defaultExt == "tif":
				defaultExt = "tiff"
			initFile = "%s.%s" % (self.dataUnit.getName(), defaultExt)
			if defaultExt not in wildCardDict:
				defaultExt = "png"
			wildCard = wildCardDict[defaultExt] + "|*.%s" % defaultExt
			del wildCardDict[defaultExt]

			for key in wildCardDict.keys():
				wildCard += "|%s|*.%s" % (wildCardDict[key], key)
			filename = GUI.Dialogs.askSaveAsFileName(self.parent,
													"Save snapshot of rendered scene",
													initFile,
													wildCard,
													"snapshotImage")
			if filename:
				do_cmd = "scripting.visualizer.saveSnapshot(ur'%s')" % filename
				cmd = lib.Command.Command(lib.Command.GUI_CMD, None, None, do_cmd, "", desc = "Save a snapshot of the visualizer")
				cmd.run()

	def saveSnapshot(self, filename):
		"""
		Created: 14.06.2007, KP
		Description save a snapshot with the given name
		"""
		if filename:
			self.currMode.saveSnapshot(filename)

	def restoreWindowSizes(self):
		"""
		Created: 15.08.2005, KP
		Description: Restores the window sizes that may be changed by setRenderWindowSize
		"""
		self.visWin.SetDefaultSize(self.visWin.origSize)
		self.sidebarWin.SetDefaultSize(self.sidebarWin.origSize)
		self.sliderWin.SetDefaultSize(self.sliderWin.origSize)
		self.toolWin.SetDefaultSize(self.toolWin.origSize)
		self.OnSize(None)

	def setRenderWindowSize(self, size, taskwin):
		"""
		Created: 28.04.2005, KP
		Description: Set the render window size by modifying the size of the surrounding panels
		"""
		x, y = size
		currx, curry = self.visWin.GetSize()
		self.visWin.origSize = (currx, curry)
		Logging.info("Current window size = ", currx, curry)
		diffx = currx - x
		diffy = curry - y
		Logging.info("Need to modify renderwindow size by ", diffx, ", ", diffy)#, kw = "visualizer")
		sx, sy = self.sidebarWin.GetSize()
		self.sidebarWin.origSize = (sx, sy)
		sx2, sy2 = taskwin.GetSize()
		d2 = sx2 - sx
		if sx2 < abs(diffx / 2):
			diffx -= sx
			sx2 = 0
		else:
			d = diffx / 2
			d -= (d2 / 2)
			sx2 += d
			diffx += -d
		taskwin.SetDefaultSize((sx2, sy2))
		taskwin.parent.OnSize(None)

		if sx:
			sx += diffx
			self.sidebarWin.SetDefaultSize((sx, sy))
			Logging.info("Size of siderbar window after modification = ", sx, sy)
		slx, sly = self.sliderWin.GetSize()
		self.sliderWin.origSize = (slx, sly)

		if diffy < 0 and abs(diffy) > abs(sly):
			Logging.info("Hiding toolbar to get more space in y - direction")#, kw = "visualizer")
			tx, ty = self.toolWin.GetSize()
			self.toolWin.origSize = (tx, ty)
			self.toolWin.SetDefaultSize((0, 0))
			diffy += ty
		if diffy:
			Logging.info("I'm told to set renderwindow size to %d, \
							%d with a %d modification of y - size." \
							%(x, y, diffy))#, kw = "visualizer")

			if diffy < 0 and sly < diffy:
				Logging.info("Giving %d more to y - size is the best I can do" % sy)#, kw = "visualizer")
				sly = 0
			else:
				sly += diffy
				Logging.info("Size of slider win after modification = ", sx, sy)

			self.sliderWin.SetDefaultSize((slx, sly))

		self.OnSize(None)
		self.parent.Layout()
		self.parent.Refresh()
		self.currentWindow.Update()
		self.Render()

	def setTimepoint(self, timepoint):
		"""
		Created: 28.04.2005, KP
		Description: Set the timepoint to be shown
		"""
		if self.blockTpUpdate:
			return
		Logging.info("setTimepoint(%d)" % timepoint, kw = "visualizer")
		# The timeslider has values that start from 1 whereas the internal time point values 
		# start from 0
		curr = self.timeslider.GetValue()
		# if the timeslider is not already at the current value, then set it to the given value
		if curr - 1 != timepoint:
			self.timeslider.SetValue(timepoint + 1)
		self.timepoint = timepoint
		if hasattr(self.currentWindow, "setTimepoint"):
			self.currentWindow.setTimepoint(self.timepoint)
		self.currMode.setTimepoint(self.timepoint)

	def onUpdateTimepoint(self, evt = None):
		"""
		Created: 31.07.2005, KP
		Description: An event handler for events caused by the time slider
		"""
		# if this call is not from a user caused event, and there has been a request
		# to change the timepoint 1/100 of a second ago, then wait a bit
		if not evt:
			diff = abs(time.time() - self.changing)
			if diff < 0.01:
				Logging.info("delay too small: ", diff, kw = "visualizer")
				wx.FutureCall(200, self.onUpdateTimepoint)
				self.changing = time.time()
				return
		if self.in_vtk:
			Logging.info("In vtk, delaying", kw = "visualizer")
			wx.FutureCall(50, lambda e = evt: self.onUpdateTimepoint(evt))
			return
		timepoint = self.timeslider.GetValue()-1
		if self.timepoint != timepoint:
			Logging.info("Sending timepoint change event (timepoint = %d)" % timepoint, kw = "visualizer")
			self.blockTpUpdate = 1
			lib.messenger.send(None, "timepoint_changed", timepoint)
			self.blockTpUpdate = 0

			do_cmd = "scripting.visualizer.setTimepoint(%d)" % timepoint
			undo_cmd = "scripting.visualizer.setTimepoint(%d)" % self.timepoint
			cmd = lib.Command.Command(lib.Command.GUI_CMD, \
									None, \
									None, \
									do_cmd, \
									undo_cmd, \
									desc = "Switch to timepoint %d" % timepoint)
			cmd.run()
			
	def onSetTimeRange(self, obj, event, r1, r2):
		"""
		Created: 15.08.2005, KP
		Description: Set the range that the time slider shows
		"""
		self.timeslider.SetRange(r1, r2)
		self.timeslider.Refresh()

	def onSetTimepoint(self, obj, event, timepoint):
		"""
		Created: 21.06.2005, KP
		Description: Update the timepoint according to an event
		"""
		self.setTimepoint(timepoint)

	def onSetTimeslider(self, obj, event, timepoint):
		"""
		Created: 21.08.2005, KP
		Description: Update the timeslider according to an event
		"""
		self.timeslider.SetValue(timepoint)

	def delayedTimesliderEvent(self, event):
		"""
		Created: 28.04.2005, KP
		Description: Set the timepoint to be shown
		"""
		self.changing = time.time()
		wx.FutureCall(200, lambda e = event, s = self: s.timesliderMethod(e))
