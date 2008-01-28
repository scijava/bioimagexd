#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
Unit: Scatterplot
Project: BioImageXD
Created: 25.03.2005, KP
Description:

A module that displays a scatterplot and allows the user
select the colocalization threshold based on the plot. Uses the vtkImageAcculat 
to calculate the scatterplot

BioImageXD includes the following persons:

Copyright (C) 2005	BioImageXD Project
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
__version__ = "$Revision: 1.22 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import Configuration
import Dialogs
import InteractivePanel
import lib.ImageOperations
import lib.messenger
import Logging
import wx
import csv
import scripting

class Scatterplot(InteractivePanel.InteractivePanel):
	"""
	Created: 25.03.2005, KP
	Description: A panel showing the scattergram
	"""
	def __init__(self, parent, size = (256, 256), **kws):
		"""
		Initialization
		"""
		self.parent = parent
		self.size = size
		self.slice = None
		# Empty space is the space between the legends and the scatterplot
		self.emptySpace = 4
		self.z = 0
		self.timepoint = 0
		self.scatterHeight = 255
		self.scatterBitmap = None
		self.drawLegend = kws.get("drawLegend")
		# Legend width is the width / height of the scalar colorbar
		self.legendWidth = 24
		self.horizontalLegend = None
		self.verticalLegend = None
		self.scatterLegend = None
		if self.drawLegend:
			w, h = self.size
			h += self.legendWidth + self.emptySpace
			w += self.legendWidth * 2 + self.emptySpace * 4 + 10
			self.size = (w, h)
			size = (w, h)
		self.xoffset = 0
		if self.drawLegend:
			self.xoffset = self.legendWidth + self.emptySpace
			
		self.scatterCTF = None
		self.mode = (1, 2)
		
		self.userDrawnThresholds=None
			
		self.lower1 = 127
		self.upper1 = 255
		self.lower2 = 127
		self.upper2 = 255
		
		self.middlestart = [0, 0]
		self.zoomx = 1
		self.zoomy = 1
		self.action = 5
		self.countVoxels = 1
		self.renew = 1
		self.wholeVolume = 1
		self.logarithmic = 1
		self.scatter = None
		self.scatterplot = None
		self.scalarMax = 255
		
		InteractivePanel.InteractivePanel.__init__(self, parent, size = size, **kws)

		self.action = 5
		self.Bind(wx.EVT_PAINT, self.OnPaint)

		self.Bind(wx.EVT_RIGHT_DOWN, self.onRightClick)
		self.ID_COUNTVOXELS = wx.NewId()
		self.ID_WHOLEVOLUME = wx.NewId()
		self.ID_LOGARITHMIC = wx.NewId()
		self.ID_SAVE_AS = wx.NewId()
		self.ID_SAVE_WITH_LEGEND = wx.NewId()
		self.ID_SAVE_CSV = wx.NewId()
		self.menu = wx.Menu()
		self.SetScrollbars(0, 0, 0, 0)
		lib.messenger.connect(None, "threshold_changed", self.updatePreview)
		

		item = wx.MenuItem(self.menu, self.ID_LOGARITHMIC, "Logarithmic scale", kind = wx.ITEM_CHECK)
		self.Bind(wx.EVT_MENU, self.onSetLogarithmic, id = self.ID_LOGARITHMIC)
		self.menu.AppendItem(item)
		self.menu.Check(self.ID_LOGARITHMIC, 1)
		
		self.menu.AppendSeparator()
		
		item = wx.MenuItem(self.menu, self.ID_SAVE_AS, "Save as...")
		self.menu.AppendItem(item)
		
		item = wx.MenuItem(self.menu, self.ID_SAVE_WITH_LEGEND,"Save with legend...")
		self.Bind(wx.EVT_MENU, self.onSaveScatterplot, id = self.ID_SAVE_AS)
		self.Bind(wx.EVT_MENU, self.onSaveScatterplot, id = self.ID_SAVE_WITH_LEGEND)
		self.menu.AppendItem(item)
		if not scripting.TFLag:
			item = wx.MenuItem(self.menu, self.ID_SAVE_CSV,"Save as CSV file...")
			self.menu.AppendItem(item)
			self.Bind(wx.EVT_MENU, self.onSaveCSV, id = self.ID_SAVE_CSV)
		
		self.Bind(wx.EVT_LEFT_DOWN, self.markActionStart)
		self.Bind(wx.EVT_MOTION, self.updateActionEnd)
		self.Bind(wx.EVT_LEFT_UP, self.setThreshold)
		self.actionstart = None
		self.actionend = None
		self.buffer = wx.EmptyBitmap(256, 256)
		
		lib.messenger.connect(None, "timepoint_changed", self.onUpdateScatterplot)
	
	def onSaveCSV(self, event):
		"""
		save the scatterplot as csv file
		"""
		filename = Dialogs.askSaveAsFileName(self, "Save scatterplot as CSV file", "scatterplot.csv", "Comma Separated Values file|*.csv", "scatterCSV")
		
		if not filename:
			return
			
		self.saveAsCSV(filename)
	
	def onSaveScatterplot(self, event):
		"""
		Save the scatterplot to a file
		"""
		if not self.scatterBitmap:
			return
		wcDict = {"png": "Portable Network Graphics Image (*.png)", "jpeg": "JPEG Image (*.jpeg)",
		"tiff": "TIFF Image (*.tiff)", "bmp": "Bitmap Image (*.bmp)"}
		#wc="PNG file|*.png|JPEG file|*.jpeg|TIFF file|*.tiff|BMP file|*.bmp"
	
		conf = Configuration.getConfiguration()
		defaultExt = conf.getConfigItem("ImageFormat", "Output")
		if defaultExt == "jpg":
			defaultExt = "jpeg"
		if defaultExt == "tif":
			defaultExt = "tiff"
		
		if defaultExt not in wcDict:
			defaultExt = "png"
		initFile = "scatterplot.%s" % (defaultExt)
		wc = wcDict[defaultExt] + "|*.%s" % defaultExt
		del wcDict[defaultExt]
		
		for key in wcDict.keys():
			wc += "|%s|*.%s" % (wcDict[key], key)
		filename = Dialogs.askSaveAsFileName(self, "Save scatterplot", initFile, wc, "scatterImage")
		
		if not filename:
			return
		ext = filename.split(".")[-1].lower()
		if ext == "jpg":
			ext = "jpeg"
		if ext == "tif":
			ext = "tiff"
		mime = "image/%s" % ext
		if event.GetId() == self.ID_SAVE_AS:
			img = self.scatterBitmap.ConvertToImage()
		else:
			img = self.scatterLegendBitmap.ConvertToImage()
		img.SaveMimeFile(filename, mime)
	
	def onUpdateScatterplot(self, evt, obj, *args):
		"""
		Update the scatterplot when timepoint changes
		"""
		self.renew = 1
		self.setTimepoint(args[0])
		self.updatePreview()
		
	def setScrollbars(self, xdim, ydim):
		"""
		Configures scroll bar behavior depending on the
					 size of the dataset, which is given as parameters.
		"""
		self.SetSize(self.size)
		self.SetVirtualSize(self.size)
		self.buffer = wx.EmptyBitmap(*self.size)
		
	def onRightClick(self, event):
		"""
		Method that is called when the right mouse button is
					 pressed down on this item
		""" 
		self.PopupMenu(self.menu, event.GetPosition())
		#menu.Destroy()
		
	def onSetLogarithmic(self, evt):
		"""
		Set the scale to logarithmic
		"""
		self.logarithmic = not self.logarithmic
		self.menu.Check(self.ID_LOGARITHMIC, self.logarithmic)
		self.renew = 1
		self.updatePreview()
		self.Refresh()
		
		
	def markActionStart(self, event):
		"""
		Sets the starting position of rubber band for zooming
		"""
		pos = event.GetPosition()
		x, y = pos
		y = self.scatterHeight - y
		x -= self.xoffset
		x -= (self.verticalLegend.GetWidth() + 2 * self.emptySpace)
		
		if x > 255:
			x = 255
		if y > 255:
			y = 255
		if x < 0:
			x = 0
		if y < 0:
			y = 0
		
		print "action marked at start=",(x,y)
		self.actionstart = (x, y)

		l1diff = abs(x - self.lower1)
		l2diff = abs(y - self.lower2)
		u1diff = abs(x - self.upper1)
		u2diff = abs(y - self.upper2)
		xmode = 0
		ymode = 0
		if l1diff < 45:
			xmode = 1
		if l2diff < 45:
			ymode = 2
			
		if l1diff > u1diff and u1diff < 45:
			# But if the user clicked closer to the upper threshold move that
			xmode = 3
		if l2diff > u2diff and u2diff < 45:
			# Same in y dir
			ymode = 4
		# If the user clicked "In the middle" (further than 30 pixels away from border)
		# Then just slide the thresholds
		
		if l2diff > 45 and u2diff > 45 and l1diff > 45 and l2diff > 45:
			ymode = 5
			xmode = 5
			self.middlestart[1] = y
			self.middlestart[0] = x
			
		self.mode = (xmode, ymode)
		
	def updateActionEnd(self, event):
		"""
		Draws the rubber band to current mouse pos
		"""
		if event.LeftIsDown():
			x, y = event.GetPosition()
			
			y = self.scatterHeight - y
			x -= self.xoffset
			x -= (self.verticalLegend.GetWidth() + 2 * self.emptySpace)
			x = min(x, 255)
			y = min(y, 255)
			x = max(x, 0)
			y = max(y, 0)

			self.actionend = (x, y)
			x1, y1 = self.actionstart
			x2, y2 = self.actionend
			
			if x2 < x1:
				x1, x2 = x2, x1
			if y2 < y1:
				y1, y2 = y2, y1
				
			c = self.scalarMax / 255.0
			x1 = int(c*x1)
			x2 = int(c*x2)
			y1 = int(c*y1)
			y2 = int(c*y2)
		
			reds = self.sources[0].getSettings()
			greens = self.sources[1].getSettings()
			
			gl, gu = greens.get("ColocalizationLowerThreshold"), greens.get("ColocalizationUpperThreshold")
			rl, ru = reds.get("ColocalizationLowerThreshold"), reds.get("ColocalizationUpperThreshold")
			
			if self.mode[0] == 1:
				greens.set("ColocalizationLowerThreshold", x1)
				gl = x1
				if gl > gu:
					gu, gl = gl, gu
				self.lower1 = gl
			if self.mode[0] == 3:
				greens.set("ColocalizationUpperThreshold", x2)
				gu = x2
				if gl > gu:
					gu, gl = gl, gu
				self.upper1 = x2
			if self.mode[1] == 2:
				reds.set("ColocalizationLowerThreshold", y1)
				rl = y1
				if rl > ru:
					ru, rl = rl, ru
				self.lower2 = y1
			elif self.mode[1] == 4:
				reds.set("ColocalizationUpperThreshold", y2)
				ru = y2
				if rl > ru:
					ru, rl = rl, ru
				self.upper2 = y2
			print "actionstart based on thresholds=",(gu,ru)
			#self.actionstart = (gu, ru)
			#self.actionend = (gl, rl)
			self.userDrawnThresholds = (gu, ru), (gl, rl)

			self.updatePreview()
			
		
	def setDataUnit(self, dataUnit):
		"""
		Sets the data unit that is displayed
		"""
		InteractivePanel.InteractivePanel.setDataUnit(self, dataUnit)
		self.sources = dataUnit.getSourceDataUnits()
		self.scalarMax = max([sourceUnit.getScalarRange()[1] for sourceUnit in self.sources])
		
		self.settings = self.sources[0].getSettings()
		self.buffer = wx.EmptyBitmap(256, 256)
		self.updatePreview()
		
	def setVoxelCount(self, event):
		"""
		Method to set on / off the voxel counting mode of scattergram
		"""
		self.countVoxels = event.Checked()
		self.renew = 1
		self.updatePreview()
		
			
	def setWholeVolume(self, event):
		"""
		Method to set on / off the construction of scattergram from 
					 the whole volume
		"""
		self.wholeVolume = event.Checked()
		self.renew = 1
		self.updatePreview()
		
	def setThreshold(self, event = None):
		"""
		Sets the thresholds based on user's selection
		"""
		# First get the coordinates of the user drawn box
		(x1, y1),(x2,y2) = self.userDrawnThresholds
		
		gl, gu = x1, x2
		rl, ru = y1, y2
		
		lib.messenger.send(None, "threshold_changed", (gl, gu), (rl, ru))
		
		lib.messenger.send(None, "data_changed", 1)

		self.renew = 1
		self.updatePreview()

		self.actionstart = None
		self.actionend = None
		self.userDrawnThresholds = None
		self.mode = (0, 0)
		
	def setTimepoint(self, tp):
		"""
		Sets the timepoint to be shown
		"""
		self.timepoint = tp
		
	def setZSlice(self, z):
		"""
		Sets the timepoint to be shown
		"""
		self.z = z
		
	def setScatterplot(self, plot):
		"""
		Sets the scatterplot as vtkImageData
		"""
		self.scatterplot = plot
		x0, x1 = self.scatterplot.GetScalarRange()
		Logging.info("Scalar range of scatterplot=", x0, x1, kw = "processing")
		
	def saveAsCSV(self, filename):
		"""
		save the scatterplot image as csv file
		"""
		f = open(filename, "wb")
		w = csv.writer(f, dialect = "excel", delimiter = ";")
		xt,yt,z = self.scatterImage.GetDimensions()
		data = []
		line = []
		for y in range(0,yt):
			for x in range(0,xt):
				value = self.scatterImage.GetScalarComponentAsDouble(x,y,0, 0)
				line.append("%d"%int(value))
			data.append(line)
			line=[]
				
		for line in data:
			w.writerow(line)
		f.close()
		
	def updatePreview(self, *args):
		"""
		A method that draws the scattergram
		"""
		width, height = self.size
		if self.renew and self.dataUnit:
			self.buffer = wx.EmptyBitmap(width, height)

			# Red on the vertical and green on the horizontal axis
			t1 = self.sources[1].getTimepoint(self.timepoint)
			t2 = self.sources[0].getTimepoint(self.timepoint)
			self.scatter, ctf, self.scatterImage = lib.ImageOperations.scatterPlot(t2, t1, -1, self.countVoxels,
			self.wholeVolume, dataunits = self.sources, logarithmic = self.logarithmic, timepoint = self.timepoint)
			self.scatter = self.scatter.Mirror(0)
			self.scatterHeight = self.scatter.GetHeight()
			self.scatterCTF = ctf
			
			self.renew = 0
		self.paintPreview()
		self.Refresh()

	def OnPaint(self, event):
		"""
		Does the actual blitting of the bitmap
		"""
		dc = wx.BufferedPaintDC(self, self.buffer)

	def paintPreview(self):
		"""
		Paints the scattergram
		"""
		dc = wx.MemoryDC()
		dc.SelectObject(self.buffer)
		dc.BeginDrawing()
		
		colour = self.parent.GetBackgroundColour()
		
		dc.SetBackground(wx.Brush(colour))
		dc.SetPen(wx.Pen(colour, 0))
		dc.SetBrush(wx.Brush(colour))
		dc.DrawRectangle(0, 0, self.size[0], self.size[1])
		if not self.scatter:
			dc.EndDrawing()
			dc = None
			return

		lower1 = int(self.sources[0].getSettings().get("ColocalizationLowerThreshold"))
		lower2 = int(self.sources[1].getSettings().get("ColocalizationLowerThreshold"))
		upper1 = int(self.sources[0].getSettings().get("ColocalizationUpperThreshold"))
		upper2 = int(self.sources[1].getSettings().get("ColocalizationUpperThreshold"))
		

		c = 255.0 / self.scalarMax
		if self.userDrawnThresholds:

			(x1,y1),(x2,y2) = self.userDrawnThresholds
			print "User drawn threhsolds = ",self.userDrawnThresholds
			if x2 < x1:
				x1, x2 = x2, x1
			if y2 < y1:
				y1, y2 = y2, y1
			lower1, upper1 = x1, x2
			lower2, upper2 = y1, y2

		bmp = self.scatter.ConvertToBitmap()
		
		self.scatterBitmap = bmp
		
		if not self.verticalLegend:
			verticalLegend = lib.ImageOperations.paintCTFValues(self.sources[1].getColorTransferFunction(), height = 256, width = self.legendWidth, paintScalars = 1)
			self.verticalLegend = verticalLegend
		else:
			verticalLegend = self.verticalLegend
		if not self.horizontalLegend:
			horizontalLegend = lib.ImageOperations.paintCTFValues(self.sources[0].getColorTransferFunction(), width = 256, height = self.legendWidth, paintScalars = 1)
			self.horizontalLegend = horizontalLegend
		else:
			horizontalLegend = self.horizontalLegend
		hzlw = verticalLegend.GetWidth() + 2 * self.emptySpace
	
		dc.DrawBitmap(verticalLegend, 0, 0)
		dc.DrawBitmap(horizontalLegend, self.xoffset + hzlw, bmp.GetHeight() + self.emptySpace)
		dc.DrawBitmap(bmp, self.xoffset + hzlw, 0, True)
		
		self.bmp = self.buffer

		slope = self.settings.get("Slope")
		intercept = self.settings.get("Intercept")
		dc.SetPen(wx.Pen(wx.Colour(255, 255, 255), 1))
		if slope and intercept:
			Logging.info("slope=", slope, "intercept=", intercept, kw = "dataunit")
			x = 255
			y = 255 - (255 * slope + intercept)
			
			dc.DrawLine(self.xoffset + hzlw, 255, self.xoffset + hzlw + x, y)
		
		ymax = 255
		# These are the threshold lines
		dc.DrawLine(self.xoffset + hzlw + lower1 * c, 0, self.xoffset + hzlw + lower1 * c, 255)
		dc.DrawLine(self.xoffset + hzlw, ymax - lower2 * c, self.xoffset + 255 + hzlw, ymax - lower2 * c)
		dc.DrawLine(self.xoffset + hzlw + upper1 * c, 0, self.xoffset + hzlw + upper1 * c, 255)
		dc.DrawLine(self.xoffset + hzlw, ymax - upper2 * c, self.xoffset + hzlw + 255, ymax - upper2 * c)
		
		borders = lib.ImageOperations.getOverlayBorders(int((upper1 - lower1) * c) + 1, int((upper2 - lower2) * c) + 1, (0, 0, 255), 90, lineWidth = 2)
		borders = borders.ConvertToBitmap()
		
		overlay = lib.ImageOperations.getOverlay(int((upper1 - lower1) * c), int((upper2 - lower2) * c), (0, 0, 255), 64)
		overlay = overlay.ConvertToBitmap()
		dc.DrawBitmap(overlay, self.xoffset + hzlw + lower1 * c, ymax - upper2 * c, 1)
		dc.DrawBitmap(borders, self.xoffset + hzlw + lower1 * c, ymax - upper2 * c, 1)
		
		if not self.scatterLegend:
			scatterLegend = lib.ImageOperations.paintCTFValues(self.scatterCTF, width = self.legendWidth, height = 256, paintScale = 1)
			self.scatterLegend = scatterLegend
		else:
			scatterLegend = self.scatterLegend
		dc.DrawBitmap(scatterLegend, self.xoffset + hzlw + 255 + 2 * self.emptySpace, 0)
		
		dc.SetTextForeground(wx.Colour(255, 255, 255))
		dc.SetFont(wx.Font(9, wx.SWISS, wx.NORMAL, wx.NORMAL))
		dc.DrawText("%d" % lower2, 3, ymax - lower2 * c)
		dc.DrawText("%d" % lower1, self.xoffset + hzlw + lower1 * c, 265)
		self.lower1 = lower1 * c
		self.lower2 = lower2 * c
		self.upper1 = upper1 * c
		self.upper2 = upper2 * c
		
		self.scatterLegendBitmap = self.buffer
		
		self.dc = dc
		del self.dc
		dc.EndDrawing()
		dc = None
