#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

"""
 Unit: TimeScale
 Project: BioImageXD
 Created: 04.02.2005, KP
 Description:

 URM/AS - The Unified Rendering Manager / Animator for Selli
 
 This is a timeline based GUI for controlling the rendering of datasets. The GUI allows users
 to specify a path for the camera to follow (using Heikki Uuksulainen's MayaVi animator code)
 and also allows them to produce videos of the rendering using ffmpeg.
 
 The timescale widget is implemented in this module.

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
__author__ = "BioImageXD Project"
__version__ = "$Revision: 1.22 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

#import Logging

import wx
import lib.messenger

class TimeScale(wx.Panel):
	"""
	Shows a time scale of specified length
	"""
	def __init__(self, parent):
		wx.Panel.__init__(self, parent, -1, style = wx.RAISED_BORDER)
		self.perSecond = 24
		self.zoomLevel = 1
		self.xOffset = 15 + self.getLabelWidth()
		self.yOffset = 6
		self.bgcolor = (255, 255, 255)
		self.fgcolor = (0, 0, 0)

		#self.setDuration(60)
		lib.messenger.connect(None, "set_duration", self.onSetDuration)
		lib.messenger.connect(None, "set_animator_zoom", self.onSetZoomLevel)
		self.Bind(wx.EVT_PAINT, self.onPaint)

		
	def onSetZoomLevel(self, obj, evt, level):
		"""
		Method: onSetZoomLevel
		Sets the zoom level of the animator
		"""            
		self.setZoomLevel(level)
		lib.messenger.send(None, "update_timeline")
		
	def onSetDuration(self, obj, evt, duration):
		"""
		Method: onSetDuration
		Sets the duration of this timescale
		"""    
		self.setDuration(duration)
		
	def getLabelWidth(self):
		return 125

	def setDisabled(self, flag):
		"""
		Method: setDisabled(flag)
		Grays out / enables this 
		"""
		if not flag:
			self.Enable(True)
			self.fgcolor = (0, 0, 0)
			self.bgcolor = (255, 255, 255)
		else:
			self.Enable(False)
#            col=self.GetForegroundColour()
#            r,g,b=col.Red(),col.Green(),col.Blue()
#            self.fgcolor=(r,g,b)
			self.fgcolor = (127, 127, 127)
			col = self.GetBackgroundColour()
			r, g, b = col.Red(), col.Green(), col.Blue()
			self.bgcolor = (r, g, b)

	def setOffset(self, x):
		"""
		Sets the offset of the timescale, which is
					 mainly determined by the tracks' titles
		"""    
		
		self.xOffset = x
		self.paintScale()

	def setPixelsPerSecond(self, x):
		"""
		Set how many pixels the timeline will show per second
		"""    
		self.perSecond = x
		#print "pixels per second=",x

	def setZoomLevel(self, level):
		"""
		Set a zoom level affecting the pixels per second
		"""    
		if self.zoomLevel != level:
			self.zoomLevel = level
			# the easiest way to update the timescale is to
			# set the same duration as now, which will resize
			# and repaint the whole thing
			self.setDuration(self.seconds)
		
	def getPixelsPerSecond(self):
		"""
		Return the pixels per second, modified by the zoom level
		"""        
		return int(self.perSecond * self.zoomLevel)

	def setDuration(self, seconds):
		"""
		Set the length of the timescale
		"""        
		self.seconds = seconds
		
		self.width = self.getPixelsPerSecond() * seconds + 2 * self.xOffset
		self.height = 20 + self.yOffset
		self.SetSize((self.width , self.height))
		self.buffer = wx.EmptyBitmap(self.width, self.height)
		self.SetMinSize((self.width + 10, self.height))
		lib.messenger.send(None, "set_timeline_size", (self.width, self.height))
		self.paintScale()
		self.Refresh()
		
	def getDuration(self):
		"""
		Return the length of the timescale
		"""           
		return self.seconds

	def paintScale(self):
		"""
		Paint the timescale
		"""        
		dc = wx.MemoryDC()
		dc.SelectObject(self.buffer)
		#col=self.GetBackgroundColour()
		r, g, b = self.bgcolor
		col = wx.Colour(r, g, b)
		self.dc = dc
		self.dc.BeginDrawing()
		dc.SetBackground(wx.Brush(col))
		dc.Clear()
		
		cx, cy, cw, ch = self.GetClientRect()
		xoff = self.xOffset + cx
		yoff = self.yOffset + cy
		self.dc.SetFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.NORMAL))
		# and the tick marks and times
		self.dc.DrawLine(xoff, 0, self.width, 0)
		r, g, b = self.fgcolor
		self.dc.SetPen(wx.Pen((r, g, b)))
		for i in range(0, self.seconds + 1):
			x = i * self.getPixelsPerSecond() + xoff
			y = 10 + yoff
			if not i % 10:
				h = int(i / 3600)
				m = int(i / 60)
				s = int(i % 60)
				timeString = ""
				if 1 or h:
					timeString = "%.2d:" % h
				timeString += "%.2d:%.2d" % (m, s)
				tw, th = self.dc.GetTextExtent(timeString)
				self.dc.SetTextForeground((r, g, b))

				self.dc.DrawText(timeString, x - (tw / 2), self.height / 4)    
			if not i % 30:
				d = 4
			elif not i % 10:
				d = 4
			else:
				d = 2
			if d:
				self.dc.DrawLine(x, -1, x, d)
				self.dc.DrawLine(x, self.height - d - 4, x, self.height)
		self.dc.EndDrawing()
		dc.SelectObject(wx.NullBitmap)
		self.dc = None
	
	def onPaint(self, event):
		"""
		The event handler for paint events. Just blits a bmp
		"""    
		dc = wx.BufferedPaintDC(self, self.buffer)