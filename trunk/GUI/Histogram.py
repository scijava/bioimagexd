# -*- coding: iso-8859-1 -*-
"""
 Unit: Histogram
 Project: BioImageXD
 Created: 30.10.2004, KP
 Description:

 A widget used to view a histogram
 
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
__version__ = "$Revision: 1.28 $"
__date__ = "$Date: 2005/01/13 14:52:39 $"

import lib.ImageOperations
import Logging
import wx
import lib.messenger

myEVT_SET_THRESHOLD = wx.NewEventType()
EVT_SET_THRESHOLD = wx.PyEventBinder(myEVT_SET_THRESHOLD, 1)

class ThresholdEvent(wx.PyCommandEvent):

	def __init__(self, eventType, eid):
		wx.PyCommandEvent.__init__(self, eventType, eid)
		self.lowerThreshold = 0
		self.upperThreshold = 255
		
	def setThresholds(self, x, y):
		self.lowerThreshold = x
		self.upperThreshold = y
		
	   
	def getThresholds(self):
		return self.lowerThreshold, self.upperThreshold

class Histogram(wx.Panel):
	"""
	A widget that can paint a histogram
	"""
	def __init__(self, parent, **kws):
		"""
		Method: __init__(parent)
		Initialization
		"""
		self.scale = kws.get("scale", 1)
		self.lowerThreshold = kws.get("lowerThreshold", 0)
		self.upperThreshold = kws.get("upperThreshold", 255)

		if "scale" in kws:
			del kws["scale"]
		if "lowerThreshold" in kws:
			del kws["lowerThreshold"]
		if "upperThreshold" in kws:
			del kws["upperThreshold"]
		kws["size"] = (270, 200)
		wx.Panel.__init__(self, parent, -1, **kws)
		self.parent = parent
		self.size = (270, 200)
		self.timePoint = 0
		self.buffer = wx.EmptyBitmap(256, 200)
		self.backGround = None
		self.Bind(wx.EVT_PAINT, self.OnPaint)
		lib.messenger.connect(None, "timepoint_changed", self.onSetTimepoint)
		lib.messenger.connect(None, "threshold_changed", self.updatePreview)
		self.Bind(wx.EVT_RIGHT_DOWN, self.onRightClick)

		self.ID_LOGARITHMIC = wx.NewId()
		self.ID_IGNORE_BORDER = wx.NewId()
		self.logarithmic = 1
		self.ignoreBorder = 0
		self.histogram = None
		self.noupdate = 0
		self.data = None
		self.replaceCTF = None
		self.thresholdMode = 0
		self.middleStart = 0
		
		self.xoffset = 0 
		
		self.renew = 1
		self.menu = wx.Menu()
		self.mode = "lower"
		item = wx.MenuItem(self.menu, self.ID_LOGARITHMIC, "Logarithmic scale", kind = wx.ITEM_CHECK)
		self.Bind(wx.EVT_MENU, self.onSetLogarithmic, id = self.ID_LOGARITHMIC)
		self.menu.AppendItem(item)
		self.menu.Check(self.ID_LOGARITHMIC, 1)

		item = wx.MenuItem(self.menu, self.ID_IGNORE_BORDER, "Ignore border bin", kind = wx.ITEM_CHECK)
		self.Bind(wx.EVT_MENU, self.onSetIgnoreBorder, id = self.ID_IGNORE_BORDER)
		self.menu.AppendItem(item)
		
		self.actionstart = None
		self.Bind(wx.EVT_LEFT_DOWN, self.markActionStart)
		self.Bind(wx.EVT_MOTION, self.updateActionEnd)
		self.Bind(wx.EVT_LEFT_UP, self.setThreshold)
	   
	def setReplacementCTF(self, colorTransferFunction):
		"""
		Set a CTF that will replace the original CTF
		"""
		self.replaceCTF = colorTransferFunction
		self.colorTransferFunction = colorTransferFunction
		
	def setLowerThreshold(self, lowerThreshhold):
		"""
		Set the lower threshold showin with this widget
		"""
		self.lowerThreshold = lowerThreshhold
		self.actionstart = None
		self.updatePreview(renew = 1)
		self.Refresh()

	def setUpperThreshold(self, upperThreshhold):
		"""
		Set the upper threshold showin with this widget
		"""
		self.upperThreshold = upperThreshhold
		self.actionstart = None
		self.updatePreview(renew = 1)
		self.Refresh()

	def getLowerThreshold(self):
		"""
		Return the lower threshold selected with this widget
		"""			   
		return self.lowerThreshold
		
	def getUpperThreshold(self):
		"""
		Return the upper threshold selected with this widget
		"""					
		return self.upperThreshold
		
	def setThresholdMode(self, flag):
		"""
		Sets the flag indicating that the threshold selectors need to be
					 activated even if the dataset is not colocalization dataset
		"""	   

		self.thresholdMode = flag
		self.actionstart = (self.lowerThreshold, 0)

	def markActionStart(self, event):
		"""
		Sets the starting position of rubber band for zooming
		"""
		position = event.GetPosition()
		x, y = position
		print "pos=",position
		x -= self.xoffset
		y = 255 - y
		if x > 255:
			x = 255
		if y > 255:
			y = 255
		if x < 0:
			x = 0
		if y < 0:
			y = 0
		
		if not self.thresholdMode:
			get = self.dataUnit.getSettings().get
			lower = get("ColocalizationLowerThreshold")
			if lower == None:
				return
		
		self.actionstart = (x, y)
		#upper = get("ColocalizationUpperThreshold")
		
		print "lower threshold = ",self.lowerThreshold
		print "upper threshold=",self.upperThreshold
		print "scale=",self.scale

		lowerDifference = abs(x - self.lowerThreshold/self.scale)
		upperDifference = abs(x - self.upperThreshold/self.scale)
		# x is in range 0-255, thresholds can be larger

		if lowerDifference > 30 and upperDifference > 30:
			self.mode = "middle"
			self.middleStart = x
		else:
			self.mode = "upper"
			if lowerDifference < upperDifference:
				self.mode = "lower"
			if int(self.scale * x) < self.lowerThreshold:
				self.mode = "lower"
			if int(self.scale * x) > self.upperThreshold:
				self.mode = "upper"
		self.updatePreview()
			
	def updateActionEnd(self, event):
		"""
		Draws the rubber band to current mouse pos
		"""
		if event.LeftIsDown():
			x, y = event.GetPosition()
			x -= self.xoffset
			y = 255 - y
			if x > 255:
				x = 255
			if y > 255:
				y = 255
			if x < 0:
				x = 0
			if y < 0:
				y = 0
			self.actionstart = (x, y)
			self.updatePreview()
			
	def setThreshold(self, event = None):
		"""
		Sets the thresholds based on user's selection
		"""
		if not self.actionstart:
			return
		xorg, y1 = self.actionstart
		x1 = int(xorg * self.scale)
		
		set = self.dataUnit.getSettings().set
		get = self.dataUnit.getSettings().get
		
		lower = get("ColocalizationLowerThreshold")
		colocMode = (lower is not None)
		if colocMode:
			upper = get("ColocalizationUpperThreshold")
		else:
			lower = self.lowerThreshold
			upper = self.upperThreshold
			
		if self.mode == "upper":
			if colocMode:
				set("ColocalizationUpperThreshold", x1)
			self.upperThreshold = x1
		elif self.mode == "lower":
			if colocMode:
				set("ColocalizationLowerThreshold", x1)
			self.lowerThreshold = x1
		elif self.mode == "middle":
			difference = x1 - int(self.scale * self.middleStart)
			if self.lowerThreshold + difference < 0:
				difference = - self.lowerThreshold
			if self.upperThreshold + difference > int(self.scale * 255):
				difference = int(self.scale * 255) - self.upperThreshold
			self.lowerThreshold += difference
			self.upperThreshold += difference
			self.middleStart = xorg
			if colocMode:
				set("ColocalizationUpperThreshold", self.upperThreshold)
				set("ColocalizationLowerThreshold", self.lowerThreshold)
				
			
		if self.thresholdMode:
			lib.messenger.send(self, "threshold_changed", int(self.lowerThreshold / self.scale), int(self.upperThreshold / self.scale))
			# Also send out wx style event. This is mainly for the benefit of
			# the manipulation task
			event = ThresholdEvent(myEVT_SET_THRESHOLD, self.GetId())
			event.setThresholds(self.lowerThreshold, self.upperThreshold)
			self.GetEventHandler().ProcessEvent(event)
			
			
		if colocMode:
			lib.messenger.send(None, "threshold_changed") 
		self.actionstart = None
		
		 
		
	def onRightClick(self, event):
		"""
		Method that is called when the right mouse button is
					 pressed down on this item
		"""		 
		self.PopupMenu(self.menu, event.GetPosition())

	def onSetLogarithmic(self, event):
		"""
		Set the scale to logarithmic
		"""
		self.logarithmic = not self.logarithmic
		self.menu.Check(self.ID_LOGARITHMIC, self.logarithmic)
		self.renew = 1
		self.updatePreview()
		self.Refresh()

	def onSetIgnoreBorder(self, event):
		"""
		Method: onSetLogarithmic
		Set the scale to logarithmic
		"""
		self.ignoreBorder = not self.ignoreBorder
		self.menu.Check(self.ID_IGNORE_BORDER, self.ignoreBorder)
		self.renew = 1
		self.updatePreview()
		
	def onSetTimepoint(self, obj, event, timepoint):
		"""
		Set the timepoint to be shown
		"""
		self.timePoint = timepoint
		self.renew = 1
		self.updatePreview()
		
	def setDataUnit(self, dataUnit, noupdate = 0):
		"""
		Set the dataunit from which the histogram is drawn
		"""
		self.dataUnit = dataUnit

		self.renew = 1
		self.noupdate = noupdate
		self.scalarMax = dataUnit.getScalarRange()[1]
		self.lowerThreshold = self.scalarMax / 2
		self.upperThreshold = self.scalarMax
		self.scale = self.scalarMax / 255.0
		self.updatePreview()

	def updatePreview(self, *args, **kws):
		"""
		Update the histogram
		"""
		get = self.dataUnit.getSettings().get
		if not self.thresholdMode and get("ColocalizationLowerThreshold"):
			lower = get("ColocalizationLowerThreshold")
			upper = get("ColocalizationUpperThreshold")
		else:
			lower = self.lowerThreshold
			upper = self.upperThreshold

		self.renew = kws.get("renew", self.renew)
		if self.renew:
			if not self.noupdate or not self.data:
				self.data = self.dataUnit.getTimepoint(self.timePoint)
				self.data.Update()
			self.colorTransferFunction = self.dataUnit.getSettings().get("ColorTransferFunction")

			if not self.colorTransferFunction:
				self.colorTransferFunction = self.dataUnit.getColorTransferFunction()
				#Logging.info("No colorTransferFunction!")
			if self.replaceCTF:
				self.colorTransferFunction = self.replaceCTF
			self.backGround = self.parent.GetBackgroundColour()

			histogram, self.percent, self.values, xoffset = lib.ImageOperations.histogram(self.data, \
																bg = self.backGround, \
																colorTransferFunction = self.colorTransferFunction, \
																logarithmic = self.logarithmic, \
																ignore_border = self.ignoreBorder, \
																lower = lower * self.scale, \
																upper = upper * self.scale, \
																maxval = 255 * self.scale)
			self.xoffset = xoffset
			self.histogram = histogram
			width = self.histogram.GetWidth()
			height = self.histogram.GetHeight()
			#self.buffer = wx.EmptyBitmap(width, height)
			self.buffer = wx.EmptyBitmap(270, 200)
			if self.size != (width, height):
				Logging.info("Setting size to", width, height, kw = "imageop")
				self.SetSize((width, height))
				self.parent.Layout()
				self.size = (width,height)
			self.renew = 0

		self.paintPreview()

		
	def paintPreview(self):
		"""
		Paints the scatterplot
		"""
		dc = wx.BufferedDC(wx.ClientDC(self), self.buffer)
		dc.BeginDrawing()
		dc.DrawBitmap(self.histogram, 0, 0, 1)
		get = self.dataUnit.getSettings().get
		set = self.dataUnit.getSettings().set
		colorTransferFunction = self.dataUnit.getColorTransferFunction()
		val = [0, 0, 0]

		r1, r2 = colorTransferFunction.GetRange()
		colorTransferFunction.GetColor(r2, val)

		if not self.thresholdMode and get("ColocalizationLowerThreshold") == None:
			return
		colocMode = get("ColocalizationLowerThreshold") != None
		if colocMode:
			lower1 = int(get("ColocalizationLowerThreshold"))
			upper1 = int(get("ColocalizationUpperThreshold"))
		else:
			lower1 = self.lowerThreshold
			upper1 = self.upperThreshold

		if self.actionstart or colocMode:
			
			if self.actionstart:
				xorg, y1 = self.actionstart
				x1 = int(self.scale * xorg)

				if self.mode == "upper":
					upper1 = x1
					self.upperThreshold = x1
				elif self.mode == "lower":
					lower1 = x1
					self.lowerThreshold = x1
				elif self.mode == "middle":
					difference = x1 - int(self.scale * self.middleStart)
					if self.lowerThreshold + difference < 0:
						difference = - self.lowerThreshold
					if self.upperThreshold + difference > int(self.scale * 255):
						difference = int(self.scale * 255) - self.upperThreshold
					
					self.middleStart = xorg
					self.lowerThreshold += difference
					self.upperThreshold += difference
					lower1 = self.lowerThreshold
					upper1 = self.upperThreshold
					if colocMode:
						set("ColocalizationLowerThreshold", lower1)
						set("ColocalizationUpperThreshold", upper1)

				if self.mode == "upper" and upper1 < lower1:
					self.mode = "lower"
					upper1, lower1 = lower1, upper1
					if colocMode:
						set("ColocalizationLowerThreshold", lower1)
						set("ColocalizationUpperThreshold", upper1)
					self.lowerThreshold = lower1
					self.upperThreshold = upper1
					
				elif self.mode == "lower" and upper1 < lower1:
					self.mode = "upper"
					upper1, lower1 = lower1, upper1
					if colocMode:
						set("ColocalizationLowerThreshold", lower1)
						set("ColocalizationUpperThreshold", upper1)
					self.lowerThreshold = lower1
					self.upperThreshold = upper1
				
		r, g, b = val
		r *= 255
		g *= 255
		b *= 255
		r = int(r)
		g = int(g)
		b = int(b)

		overlayWidth = int((upper1 - lower1) / self.scale)
		borders = lib.ImageOperations.getOverlayBorders(overlayWidth, 150, (r, g, b), 80)
		borders = borders.ConvertToBitmap()
		dc.DrawBitmap(borders, self.xoffset + int(lower1 / self.scale), 0, 1)
		
		overlay = lib.ImageOperations.getOverlay(overlayWidth, 150, (r, g, b), 32)
		overlay = overlay.ConvertToBitmap()
		dc.DrawBitmap(overlay, self.xoffset + int(lower1 / self.scale), 0, 1)

		if self.values:
			tot = 0
			totth = 0
			for i, val in enumerate(self.values):
				tot += val
				if i >= lower1 and i <= upper1:
					totth += val
			self.percent = totth / float(tot)

		if not self.percent:
			self.percent = 0.00
		dc.SetFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.NORMAL))
		dc.DrawText("%.2f%% of data selected (range %d-%d)" \
					% (100 * self.percent, self.lowerThreshold, \
					self.upperThreshold), 10, 182)
		dc.EndDrawing()
		dc = None


		
	def OnPaint(self, event):
		"""
		Does the actual blitting of the bitmap
		"""
		dc = wx.BufferedPaintDC(self, self.buffer)#, self.buffer)
		

