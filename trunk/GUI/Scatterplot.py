#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
Unit: Scatterplot
Project: BioImageXD
Created: 25.03.2005, KP
Description:

A module that displays a scatterplot and allows the user
select the colocalization threshold based on the plot. Uses the vtkImageAccumulate
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

#class Scatterplot(InteractivePanel.InteractivePanel):
class Scatterplot(wx.Panel):
	"""
	A panel showing the scattergram
	"""
	def __init__(self, parent, **kws):
		"""
		Initialization
		"""
		self.parent = parent
		self.slice = None
		# Empty space is the space between the legends and the scatterplot
		self.emptySpace = 4
		self.timepoint = 0
		self.scatterHeight = 255
		self.scatterBitmap = None
		self.drawLegend = kws.get("drawLegend")
		# Legend width is the width / height of the scalar colorbar
		self.legendWidth = 24
		self.slope, self.intercept = None, None
		self.horizontalLegend = None
		self.verticalLegend = None
		self.scatterLegend = None
		
		self.plotCache = {}
		self.size = (256,256)
		if self.drawLegend:
			self.xoffset = self.legendWidth + self.emptySpace
			w, h = self.size
			h += self.legendWidth + self.emptySpace
			w += self.legendWidth * 2 + self.emptySpace * 4 + 10+self.xoffset
			self.size = (w, h)
			size = (w, h)
			
		self.xoffset = 0

			
		self.scatterCTF = None
		self.mode = (1, 2)
		
		self.userDrawnThresholds=None
			
		self.lower1, self.upper1, self.lower2, self.upper2 = 127,255,127,255
		
		self.middlestart = [0, 0]
		self.action = 5
		self.countVoxels = 1
		self.renew = 1
		self.wholeVolume = 1
		self.logarithmic = 1
		self.scatter = None
		self.scatterplot = None
		self.scalarMax = 255
		self.dataUnit = None
		#InteractivePanel.InteractivePanel.__init__(self, parent, size = size, **kws)
		wx.Panel.__init__(self, parent, size = size)

		self.Bind(wx.EVT_PAINT, self.OnPaint)

		self.Bind(wx.EVT_RIGHT_DOWN, self.onRightClick)
		self.ID_COUNTVOXELS = wx.NewId()
		self.ID_WHOLEVOLUME = wx.NewId()
		self.ID_LOGARITHMIC = wx.NewId()
		self.ID_SAVE_AS = wx.NewId()
		self.ID_SAVE_WITH_LEGEND = wx.NewId()
		self.ID_SAVE_CSV = wx.NewId()
		self.menu = wx.Menu()
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
		self.Bind(wx.EVT_MOTION, self.updateUserDrawnThresholds)
		self.Bind(wx.EVT_LEFT_UP, self.setThreshold)
		self.actionstart = None
		self.actionend = None
		self.buffer = wx.EmptyBitmap(*self.size)
		
		lib.messenger.connect(None, "timepoint_changed", self.onUpdateScatterplot)
	
	def getSlope(self):
		"""
		@return the slope of the correlation line
		"""
		return self.slope
		
	def setSlopeAndIntercept(self, slope, intercept):
		"""
		Set the slope and intercept
		"""
		self.setSlope(slope)
		self.setIntercept(intercept)
		self.updatePreview()
		
	def setSlope(self, slope):
		"""
		Set the slope coefficient
		"""
		self.slope = slope

	def getIntercept(self):
		"""
		@return the intercept of the correlation line
		"""
		return self.intercept
		
	def setIntercept(self, intercept):
		"""
		Set the slope coefficient
		"""
		self.intercept = intercept
	
	
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
		
	def onRightClick(self, event):
		"""
		Method that is called when the right mouse button is
					 pressed down on this item
		""" 
		self.PopupMenu(self.menu, event.GetPosition())
		
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
		
		x = min(x, 255)
		y = min(y, 255)
		x = max(x, 0)
		y = max(y, 0)
		
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
		
	def getThresholds(self):
		"""
		@return the thresholds this scatterplot is set to
		"""
		return (self.lower1, self.upper1), (self.lower2, self.upper2)
		
	def setCh1LowerThreshold(self, threshold):
		"""
		Set the lower threshold of ch1
		"""
		self.lower1 = threshold
		self.paintPreview()
		
	def setCh1UpperThreshold(self, threshold):
		"""
		Set the upper threshold of ch1
		"""
		self.upper1 = threshold
		self.paintPreview()
		
	def setCh2LowerThreshold(self, threshold):
		"""
		Set the lower threshold of ch1
		"""
		self.lower2 = threshold
		self.paintPreview()
		
	def setCh2UpperThreshold(self, threshold):
		"""
		Set the upper threshold of ch1
		"""
		self.upper2 = threshold
		self.paintPreview()
		
	def setThresholds(self, ch1lower, ch1upper, ch2lower, ch2upper):
		"""
		Set the thresholds this scatteplot is set to
		"""
		Logging.info("\nScatterplot thresholds set to (%d-%d) (%d-%d)"%(ch1lower,ch1upper,ch2lower,ch2upper))
		self.lower1, self.upper1, self.lower2, self.upper2 = ch1lower, ch1upper, ch2lower, ch2upper
		self.paintPreview()
		
	def updateUserDrawnThresholds(self, event):
		"""
		Draws the rubber band to current mouse pos
		"""
		if not event.LeftIsDown():
			return
			
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
	
		(greenLower, greenUpper), (redLower, redUpper) = self.getThresholds()
		
		if self.mode[0] == 1:
			greenLower = x1
			if greenLower > greenUpper:
				greenUpper, greenLower = greenLower, greenUpper
			self.lower1 = greenLower
		if self.mode[0] == 3:
			greenUpper = x2
			if greenLower > greenUpper:
				greenUpper, greenLower = greenLower, greenUpper
			self.upper1 = x2
			
		if self.mode[1] == 2:
			redLower = y1
			if redLower > redUpper:
				redUpper, redLower = redLower, redUpper
			self.lower2 = y1
		elif self.mode[1] == 4:
			redUpper = y2
			if redLower > redUpper:
				redUpper, redLower = redLower, redUpper
			self.upper2 = y2

		self.userDrawnThresholds = (greenLower, greenUpper), (redLower, redUpper)

		self.updatePreview()
			
		
	def setDataUnit(self, dataUnit):
		"""
		Sets the data unit that is displayed
		"""
		self.sources = dataUnit.getSourceDataUnits()
		self.dataUnit = dataUnit
#		self.scalarMax = max([sourceUnit.getScalarRange()[1] for sourceUnit in self.sources])
		self.scalarMax = max([(2**sourceUnit.getSingleComponentBitDepth())-1 for sourceUnit in self.sources])
		
		self.buffer = wx.EmptyBitmap(*self.size)
		self.updatePreview()
		
	def setVoxelCount(self, event):
		"""
		Method to set on / off the voxel counting mode of scattergram
		"""
		self.countVoxels = event.Checked()
		self.renew = True
		self.updatePreview()
		
			
	def setWholeVolume(self, event):
		"""
		Method to set on / off the construction of scattergram from 
					 the whole volume
		"""
		self.wholeVolume = event.Checked()
		self.renew = True
		self.updatePreview()
		
	def setThreshold(self, event = None):
		"""
		Sets the thresholds based on user's selection
		"""
		if not self.userDrawnThresholds:
			return
		(greenLower, greenUpper), (redLower, redUpper) = self.userDrawnThresholds
		Logging.info("Getting from user drawn thresholds %d,%d, %d,%d"%(greenLower, greenUpper, redLower, redUpper))
		self.lower1, self.upper1 = min(greenLower, greenUpper), max(greenLower, greenUpper)
		self.lower2, self.upper2 = min(redLower, redUpper), max(redLower, redUpper)
		
		lib.messenger.send(self, "scatterplot_thresholds", (greenLower, greenUpper), (redLower, redUpper))

		self.updatePreview()

		self.actionstart, self.actionend = None, None
		self.userDrawnThresholds = None
		self.mode = (0, 0)
		
	def setTimepoint(self, tp):
		"""
		Sets the timepoint to be shown
		"""
		if tp != self.timepoint:
			self.renew = True
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
		
	def generateScatterplot(self, imagedata1, imagedata2):
		"""
		Create the scatterplot from the given imagedata objects
		"""
		cvx = self.countVoxels	# Flag indicating whether we should count voxels, or just show the intensities
		log = self.logarithmic	# Flag indicating whether we should draw a logarithmic scatterplot
		wv = self.wholeVolume	# Flag indicating whether we should use the whole volume
		scatter, ctf, scatterImage = lib.ImageOperations.scatterPlot( imagedata1, imagedata2, z = -1,
			countVoxels = cvx,  logarithmic = log, wholeVolume = wv)
#		scatter.Mirror(0)
		self.scatterHeight = scatter.GetHeight()
		return scatter, ctf, scatterImage
		
	def getScatterplotForTimepoint(self, timepoint):
		"""
		Gets the scatterplot for the given timepoint
		"""
		if (self.timepoint, self.wholeVolume, self.logarithmic) not in self.plotCache:
			# Red on the vertical and green on the horizontal axis
			t1 = self.sources[1].getTimepoint(timepoint)
			t2 = self.sources[0].getTimepoint(timepoint)
			self.scatter, self.scatterCTF, self.scatterImage = self.generateScatterplot(t1, t2)
			self.scatter = self.scatter.Mirror(horizontally = False)
			self.plotCache[(self.timepoint, self.wholeVolume, self.logarithmic)] = self.scatter, self.scatterCTF, self.scatterImage
		else:
			self.scatter, self.scatterCTF, self.scatterImage = self.plotCache[(self.timepoint, self.wholeVolume, self.logarithmic)]
		
	def updatePreview(self, *args):
		"""
		A method that draws the scattergram
		"""
		self.buffer = wx.EmptyBitmap(*self.size)
		if self.renew and self.dataUnit:
			self.getScatterplotForTimepoint(self.timepoint)
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
		if not self.dataUnit:
			return
			
		# Get the official thresholds
		(lower1, upper1), (lower2, upper2) = self.getThresholds()
		
		# But if the user is drawing something, then we paint those instead
		if self.userDrawnThresholds:
			(lower1, upper1), (lower2, upper2) = self.userDrawnThresholds
		slope, intercept = self.getSlope(), self.getIntercept()

#		Logging.info("Painting scatterplot with thresholds (%d - %d) and (%d - %d)"%(lower1, upper1, lower2, upper2))
		self.paintScatterplot(lower1, upper1, lower2, upper2, slope, intercept)
		
	def paintScatterplot(self, lower1, upper1, lower2, upper2, slope, intercept):
		"""
		Paint the scatterplot showing the given thresholds and correlation
		@param lower1 The lower threshold for Ch1
		@param upper1 The upper threshold for Ch1
		@param lower2 The lower threshold for Ch2
		@param upper2 The upper threshold for Ch2
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


		c = 255.0 / self.scalarMax

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
			
		horizontalLegendWidth = verticalLegend.GetWidth() + 2 * self.emptySpace
	
		dc.DrawBitmap(verticalLegend, 0, 0)
		dc.DrawBitmap(horizontalLegend, self.xoffset + horizontalLegendWidth, bmp.GetHeight() + self.emptySpace)
		dc.DrawBitmap(bmp, self.xoffset + horizontalLegendWidth, 0, True)
		
		self.bmp = self.buffer

		dc.SetPen(wx.Pen(wx.Colour(255, 255, 255), 1))
		
		if slope and intercept:
			x = 255
			y = 255 - (255 * slope + intercept)
			dc.DrawLine(self.xoffset + horizontalLegendWidth, 255-intercept, self.xoffset + horizontalLegendWidth + x, y)
		
		ymax = 255
		# These are the threshold lines
		dc.DrawLine(self.xoffset + horizontalLegendWidth + lower1 * c, 0, self.xoffset + horizontalLegendWidth + lower1 * c, 255)
		dc.DrawLine(self.xoffset + horizontalLegendWidth, ymax - lower2 * c, self.xoffset + 255 + horizontalLegendWidth, ymax - lower2 * c)
		dc.DrawLine(self.xoffset + horizontalLegendWidth + upper1 * c, 0, self.xoffset + horizontalLegendWidth + upper1 * c, 255)
		dc.DrawLine(self.xoffset + horizontalLegendWidth, ymax - upper2 * c, self.xoffset + horizontalLegendWidth + 255, ymax - upper2 * c)
		
		if upper1 != lower1 and upper2 != lower2:
			overlay = lib.ImageOperations.getOverlay(int((upper1 - lower1) * c), int((upper2 - lower2) * c), (0, 0, 255), 64)
			overlay = overlay.ConvertToBitmap()
			borders = lib.ImageOperations.getOverlayBorders(int((upper1 - lower1) * c) + 1, int((upper2 - lower2) * c) + 1, (0, 0, 255), 90, lineWidth = 2)
			borders = borders.ConvertToBitmap()
			dc.DrawBitmap(overlay, self.xoffset + horizontalLegendWidth + lower1 * c, ymax - upper2 * c, 1)
			dc.DrawBitmap(borders, self.xoffset + horizontalLegendWidth + lower1 * c, ymax - upper2 * c, 1)
		
		if not self.scatterLegend:
			self.scatterLegend = lib.ImageOperations.paintCTFValues(self.scatterCTF, width = self.legendWidth, height = 256, paintScale = 1)

		dc.DrawBitmap(self.scatterLegend, self.xoffset + horizontalLegendWidth + 255 + 2 * self.emptySpace, 0)
		
		dc.SetTextForeground(wx.Colour(255, 255, 255))
		dc.SetFont(wx.Font(9, wx.SWISS, wx.NORMAL, wx.NORMAL))
		dc.DrawText("%d" % lower2, 3, ymax - lower2 * c)
		dc.DrawText("%d" % lower1, self.xoffset + horizontalLegendWidth + lower1 * c, 265)
		self.lower1 = lower1 * c
		self.lower2 = lower2 * c
		self.upper1 = upper1 * c
		self.upper2 = upper2 * c
		
		self.scatterLegendBitmap = self.buffer
		
		self.dc = dc
		del self.dc
		dc.EndDrawing()
		dc = None
