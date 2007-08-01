# -*- coding: iso-8859-1 -*-
"""
 Unit: Histogram
 Project: BioImageXD
 Created: 30.10.2004, KP
 Description:

 A widget used to view a histogram
 
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
__version__ = "$Revision: 1.28 $"
__date__ = "$Date: 2005/01/13 14:52:39 $"

import ImageOperations
import Logging
import wx
#from enthought.tvtk import messenger
import messenger

myEVT_SET_THRESHOLD = wx.NewEventType()
EVT_SET_THRESHOLD = wx.PyEventBinder(myEVT_SET_THRESHOLD, 1)

class ThresholdEvent(wx.PyCommandEvent):
	def __init__(self, evtType, eid):
		wx.PyCommandEvent.__init__(self, evtType, eid)
		self.lowerThreshold = 0
		self.upperThreshold = 255
		
	def setThresholds(self, x, y):
		self.lowerThreshold = x
		self.upperThreshold = y
		
	   
	def getThresholds(self):
		return self.lowerThreshold, self.upperThreshold

class Histogram(wx.Panel):
	"""
	Class: Histogram
	Created: 11.07.2005, KP
	Description: A widget that can paint a histogram
	"""
	def __init__(self, parent, **kws):
		"""
		Method: __init__(parent)
		Created: 24.03.2005, KP
		Description: Initialization
		"""    
		self.scale = kws.get("scale", 1)
		if "scale" in kws:del kws["scale"]
		
		wx.Panel.__init__(self, parent, -1, **kws)
		self.parent = parent
		self.timePoint = 0
		self.buffer = wx.EmptyBitmap(256, 150)
		self.bg = None
		self.Bind(wx.EVT_PAINT, self.OnPaint)
		messenger.connect(None, "timepoint_changed", self.onSetTimepoint)
		messenger.connect(None, "threshold_changed", self.updatePreview)
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
		self.lowerThreshold = 0
		self.upperThreshold = 255
		
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
	   
	def setReplacementCTF(self, ctf):
		"""
		Method: setReplacementCTF
		Created: 15.04.2006, KP
		Description: Set a CTF that will replace the original CTF
		"""            
		self.replaceCTF = ctf
		self.ctf = ctf
		
	def setLowerThreshold(self, lth):
		"""
		Method: setLowerThreshold
		Created: 06.06.2006, KP
		Description: Set the lower threshold showin with this widget
		"""                    
		self.lowerThreshold = lth
		#self.actionstart=(self.lowerThreshold,0)
		#self.setThreshold(None)
		self.actionstart = None
		self.updatePreview(renew = 1)
		self.Refresh()
	def setUpperThreshold(self, uth):
		"""
		Method: setUpperThreshold
		Created: 06.06.2006, KP
		Description: Set the upper threshold showin with this widget
		"""                    
		self.upperThreshold = uth
		#self.actionstart=(self.upperThreshold,0)
		self.actionstart = None
		#self.setThreshold(None)
		self.updatePreview(renew = 1)
		self.Refresh()
	def getLowerThreshold(self):
		"""
		Method: getLowerThreshold
		Created: 12.04.2006, KP
		Description: Return the lower threshold selected with this widget
		"""            
		return self.lowerThreshold
		
	def getUpperThreshold(self):
		"""
		Created: 12.04.2006, KP
		Description: Return the upper threshold selected with this widget
		"""                 
		return self.upperThreshold
		
	def setThresholdMode(self, flag):
		"""
		Created: 12.04.2006, KP
		Description: Sets the flag indicating that the threshold selectors need to be
					 activated even if the dataset is not colocalization dataset
		"""    

		self.thresholdMode = flag
		self.actionstart = (self.lowerThreshold, 0)

	def markActionStart(self, event):
		"""
		Created: 12.07.2005, KP
		Description: Sets the starting position of rubber band for zooming
		"""    
		pos = event.GetPosition()
		x, y = pos
		x -= self.xoffset
		y = 255 - y
		if x > 255:x = 255
		if y > 255:y = 255
		if x < 0:x = 0
		if y < 0:y = 0
		
		if not self.thresholdMode:
			get = self.dataUnit.getSettings().get
			lower = get("ColocalizationLowerThreshold")
			if lower == None:
				return
		
		self.actionstart = (x, y)
		#upper=get("ColocalizationUpperThreshold")
		
		ldiff = abs(x - self.lowerThreshold)
		udiff = abs(x - self.upperThreshold)
		if ldiff > 30 and udiff > 30:
			self.mode = "middle"
			self.middleStart = x
		else:            
			self.mode = "upper"
			if ldiff < udiff: self.mode = "lower"
			if x < self.lowerThreshold: self.mode = "lower"
			if x > self.upperThreshold: self.mode = "upper"
		self.updatePreview()
			
	def updateActionEnd(self, event):
		"""
		Created: 12.07.2005, KP
		Description: Draws the rubber band to current mouse pos       
		"""
		if event.LeftIsDown():
			x, y = event.GetPosition()
			x -= self.xoffset
			y = 255 - y
			if x > 255:x = 255
			if y > 255:y = 255
			if x < 0:x = 0
			if y < 0:y = 0            
			self.actionstart = (x, y)
			self.updatePreview()
			
	def setThreshold(self, event = None):
		"""
		Created: 24.03.2005, KP
		Description: Sets the thresholds based on user's selection
		"""
		
		if not self.actionstart:return
		x1, y1 = self.actionstart
		
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
			diff = x1 - self.middleStart
			if self.lowerThreshold + diff < 0:
				diff = -self.lowerThreshold
			if self.upperThreshold + diff > 255:
				diff = 255 - self.upperThreshold
			self.lowerThreshold += diff
			self.upperThreshold += diff
			self.middleStart = x1
			if colocMode:
				set("ColocalizationUpperThreshold", self.upperThreshold)
				set("ColocalizationLowerThreshold", self.lowerThreshold)
				
			
		if self.thresholdMode:
			messenger.send(self, "threshold_changed", self.lowerThreshold, self.upperThreshold)
			# Also send out wx style event. This is mainly for the benefit of
			# the manipulation task
			evt = ThresholdEvent(myEVT_SET_THRESHOLD, self.GetId())
			evt.setThresholds(self.lowerThreshold, self.upperThreshold)
			self.GetEventHandler().ProcessEvent(evt)
			
			
		if colocMode:
			messenger.send(None, "threshold_changed") 
		self.actionstart = None
		
		 
		
	def onRightClick(self, event):
		"""
		Created: 02.04.2005, KP
		Description: Method that is called when the right mouse button is
					 pressed down on this item
		"""      
		self.PopupMenu(self.menu, event.GetPosition())

	def onSetLogarithmic(self, evt):
		"""
		Created: 12.07.2005, KP
		Description: Set the scale to logarithmic
		"""
		self.logarithmic = not self.logarithmic
		self.menu.Check(self.ID_LOGARITHMIC, self.logarithmic)
		self.renew = 1
		self.updatePreview()
		self.Refresh()

	def onSetIgnoreBorder(self, evt):
		"""
		Method: onSetLogarithmic
		Created: 12.07.2005, KP
		Description: Set the scale to logarithmic
		"""
		self.ignoreBorder = not self.ignoreBorder
		self.menu.Check(self.ID_IGNORE_BORDER, self.ignoreBorder)
		self.renew = 1
		self.updatePreview()
		
	def onSetTimepoint(self, obj, evt, timepoint):
		"""
		Created: 12.07.2005, KP
		Description: Set the timepoint to be shown
		"""
		self.timePoint = timepoint
		self.renew = 1
		self.updatePreview()
		
	def setDataUnit(self, dataUnit, noupdate = 0):
		"""
		Created: 28.04.2005, KP
		Description: Does the actual blitting of the bitmap
		Parameters:
			noupdate  Setting this flag to 1 will force the histogram       
					  to never update it's source data
		"""
		self.dataUnit = dataUnit
		self.renew = 1
		self.noupdate = noupdate
		self.updatePreview()
		
		
	def updatePreview(self, *args, **kws):
		"""
		Created: 12.07.2005, KP
		Description: Update the histogram
		"""
		get = self.dataUnit.getSettings().get
		if not self.thresholdMode:
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
			self.ctf = self.dataUnit.getSettings().get("ColorTransferFunction")
			if not self.ctf:Logging.info("No ctf!")
			if self.replaceCTF:
				self.ctf = self.replaceCTF
			self.bg = self.parent.GetBackgroundColour()
			
			histogram, self.percent, self.values, xoffset = ImageOperations.histogram(self.data, bg = self.bg, ctf = self.ctf,
							 logarithmic = self.logarithmic,
							ignore_border = self.ignoreBorder,
							lower = lower,
							upper = upper, maxval = 255 * self.scale)
			self.xoffset = xoffset
			self.histogram = histogram
			w, h = self.histogram.GetWidth(), self.histogram.GetHeight()
			self.buffer = wx.EmptyBitmap(w, h)
			Logging.info("Setting size to", w, h, kw = "imageop")
			self.SetSize((w, h))
			self.parent.Layout()
			self.renew = 0
			
		
		self.paintPreview()
		
		# Commented because in windows looks bad and not needed
		#self.Refresh()
		
	def paintPreview(self):
		"""
		Created: 12.07.2005, KP
		Description: Paints the scatterplot
		"""
		
		dc = wx.BufferedDC(wx.ClientDC(self), self.buffer)
		dc.BeginDrawing()
		dc.DrawBitmap(self.histogram, 0, 0, 1)
		get = self.dataUnit.getSettings().get
		set = self.dataUnit.getSettings().set
		ctf = self.dataUnit.getColorTransferFunction()
		val = [0, 0, 0]
		r1, r2 = ctf.GetRange()
		ctf.GetColor(r2, val)
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
				x1, y1 = self.actionstart
				if self.mode == "upper":
					upper1 = x1
					self.upperThreshold = x1
				elif self.mode == "lower":
					lower1 = x1
					self.lowerThreshold = x1
				elif self.mode == "middle":
					diff = x1 - self.middleStart
					if self.lowerThreshold + diff < 0:
						diff = -self.lowerThreshold
					if self.upperThreshold + diff > 255:
						diff = 255 - self.upperThreshold
					
					self.middleStart = x1
					self.lowerThreshold += diff
					self.upperThreshold += diff
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
	
		#borders = ImageOperations.getOverlayBorders(upper1-lower1+1,150,(r,g,b),128)
		borders = ImageOperations.getOverlayBorders(upper1 - lower1 + 1, 150, (r, g, b), 80)
		borders = borders.ConvertToBitmap()
		dc.DrawBitmap(borders, self.xoffset + lower1, 0, 1)
		
		overlay = ImageOperations.getOverlay(upper1 - lower1, 150, (r, g, b), 32)
		overlay = overlay.ConvertToBitmap()
		dc.DrawBitmap(overlay, self.xoffset + lower1, 0, 1)
		if self.values:
			tot = 0
			totth = 0
			for i, val in enumerate(self.values):
				tot += val
				if i >= lower1 and i <= upper1:totth += val
			self.percent = totth / float(tot)
		
		if self.percent:
			dc.SetFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.NORMAL))
			dc.DrawText("%.2f%% of data selected (range %d-%d)" % (100 * self.percent, self.scale * self.lowerThreshold, self.scale * self.upperThreshold), 10, 182)
				
		
		dc.EndDrawing()
		dc = None


		
	def OnPaint(self, event):
		"""
		Created: 28.04.2005, KP
		Description: Does the actual blitting of the bitmap
		"""
		dc = wx.BufferedPaintDC(self, self.buffer)#,self.buffer)
		

