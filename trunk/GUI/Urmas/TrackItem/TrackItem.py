# -*- coding: iso-8859-1 -*-

"""
 Unit: TrackItem
 Project: BioImageXD
 Created: 19.03.2005, KP
 Description:

 URM/AS - The Unified Rendering Manager / Animator for Selli
 
 Urmas is a timeline based GUI for controlling the rendering of datasets. The GUI allows users
 to specify a path for the camera to follow (using Heikki Uuksulainen's MayaVi animator code)
 and also allows them to produce videos of the rendering using ffmpeg.

 The items placed on the track are implemented in this module
 
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

import wx

#import os.path
#import sys
#import math, random

import lib.ImageOperations
#from Urmas import UrmasControl
import Logging        
DRAG_OFFSET = 15
		
class TrackItem:
	"""
	Class: TrackItem
	Created: 10.02.2005, KP
	Description: A class representing one item on a track
	"""       

	def __init__(self, parent, text, size, **kws):
		#wx.Panel.__init__(self,parent,-1)#,style=wx.SIMPLE_BORDER)
		self.text = text
		self.parent = parent
		self.minSize = 5
		self.position = (0, 0)
		self.pos = (0, 0)
		self.dc = 0
		self.buffer = 0
		self.destroyed = 0
		self.getting = 0
		self.thumbnailbmp = 0
		self.dragMode = 0
		self.labelheight = 15
		self.volume = None
		self.thumbtimepoint = -1
		self.timepoint = kws.get("timepoint", -1)
		self.editable = kws.get("editable", 1)
		self.dataUnit = kws.get("dataunit", None)
		
		if kws.has_key("thumbnail"):
			self.thumbtimepoint = kws["thumbnail"]
			#self.setThumbnailDataunit(self.dataUnit)
		self.color = (255, 255, 255)
		self.headercolor = (127, 127, 127)
		
		self.width, self.height = size
		self.setWidth(self.width)
		self.beginX = 0
		
	def SetPosition(self, pos):
		self.pos = pos
		TrackItem.updateItem(self)
		
	def GetPosition(self):
		return self.pos
		
	def GetSize(self):
		return self.width, self.height
		
	def getTimepoint(self):
		"""
		Created: 19.04.2005, KP
		Description: Return the timepoint of this item
		"""       
		return self.timepoint
		
	def setItemNumber(self, n):
		"""
		Created: 14.04.2005, KP
		Description: Set the item number of this item
		"""       
		self.itemnum = n
		
	def setText(self, s):
		"""
		Created: 14.04.2005, KP
		Description: Set the text number of this item
		"""       
		self.text = s

	def OnDragOver(self, x, y):
		"""
		Created: 12.04.2005, KP
		Description: A method called when something is being dragged over this item
		"""       
		w, h = self.GetSize()
		ix, iy = self.GetPosition()
		d = abs(ix - x)
		if d > w / 2:
			hilight = w - 3
		else:
			hilight = 2
		self.drawItem(hilight)
		#self.Refresh()
		self.parent.paintTrack()
		self.parent.Refresh()
		
	def setThumbnailDataunit(self, dataunit):
		"""
		Created: 06.05.2005, KP
		Description: Sets the setting for thumbnail generation
		"""       
		self.dataUnit = dataunit
		self.thumbtimepoint = self.timepoint
		#print "self.timepoint=",self.timepoint
		#self.volume = self.dataUnit.getTimepoint(self.thumbtimepoint)
		#print "release data=",self.volume.GetReleaseDataFlag()
		
	def __set_pure_state__(self, state):
		"""
		Created: 11.04.2005, KP
		Description: Update the item
		"""       
		start, end = state.position
		# don't update itemnum, since it should accurately represent the 
		# number of spline points, and that is guaranteed by the track
		# object that creates this item
		#self.itemnum = state.itemnum
		
		
		start = self.parent.getPixels(start)
		end = self.parent.getPixels(end)
		
		start += self.parent.getLabelWidth()
		end += self.parent.getLabelWidth()
		
		
		self.SetPosition((start, 0))
		w = (end - start)
		self.setWidth(w)
		self.drawItem()
 #       self.parent.paintTrack()
 #       self.parent.Refresh()
		
	def setColor(self, col, headercolor):
		"""
		Created: 10.02.2005, KP
		Description: Set the color and header color for this item
		"""       
		self.color = col
		self.headercolor = headercolor
		self.drawItem()

	def drawHeader(self, hilight = -1):
		"""
		Created: 19.03.2005, KP
		Description: A method that draws the header of this item
		"""       
		# Set the color to header color
		r, g, b = self.headercolor
		if hilight != -1:
			r -= 32
			g -= 32
			b -= 32
			if r < 0:r = 0
			if g < 0:g = 0
			if b < 0:b = 0
		col = wx.Colour(r, g, b)
		
		# And draw the header block
		self.dc.SetBrush(wx.Brush(col))
		self.dc.SetPen(wx.Pen((0, 0, 0)))
		self.dc.SetBackground(wx.Brush(col))
		self.dc.DrawRectangle(0, 0, self.width, self.labelheight)

		# Draw the text inside the header
		if self.text != "":
			self.dc.SetTextForeground((0, 0, 0))
			self.dc.SetFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.NORMAL))
			self.dc.DrawText(self.text, 5, 2)            
		
	def drawItem(self, hilight = -1):
		"""
		Created: 10.02.2005, KP
		Description: A method that draws this track item
		"""
		#self.dc = wx.BufferedDC(wx.ClientDC(self),self.buffer)
		self.dc = wx.MemoryDC()
		self.dc.SelectObject(self.buffer)

		self.dc.BeginDrawing()
		r, g, b = 0, 0, 0
		if hilight != -1:
			r = 32
			g = 32
			b = 32
		brush = wx.Brush(wx.Colour(r, g, b))
		self.dc.SetBackground(brush)
		self.dc.Clear()

		self.dc.SetPen(wx.Pen((0, 0, 0)))

		# draw the body
		#r,g,b=self.color
		#col=wx.Colour(r,g,b)
		#self.dc.SetBrush(wx.Brush(wx.BLACK))
		#self.dc.DrawRectangle(0,0,self.width,self.height)        
		
		self.drawHeader(hilight)
		if hilight != -1:
			self.hilight(hilight)
		if self.thumbtimepoint >= 0:
			self.drawThumbnail()
		r, g, b = self.headercolor

		self.dc.SetPen(wx.Pen(wx.Colour(r, g, b), 2))
		self.dc.DrawLine(self.width - 1, 0, self.width - 1, self.height)
		self.dc.EndDrawing()
		self.dc.SelectObject(wx.NullBitmap)
		self.dc = None

	def hilight(self, h):
		"""
		Created: 12.04.2005, KP
		Description: A method to highlight the spot where a drop would occur
		""" 
		self.dc.SetPen(wx.Pen(wx.Colour(0, 0, 0), 2))
		self.dc.DrawLine(h, 0, h, self.height)
		
	def drawThumbnail(self):
		"""
		Created: 10.02.2005, KP
		Description: A method that draws a thumbnail on an item. If no thumbnail exists,
					 this will create one
		"""   
		if not self.thumbnailbmp:
			if not self.volume:
				self.volume = self.dataUnit.getTimepoint(self.thumbtimepoint)
			#self.volume.Update()
			vx, vy, vz = self.volume.GetDimensions()
			ctf = self.dataUnit.getSettings().get("ColorTransferFunction")
			#print self.volume.GetUpdateExtent()
			self.thumbnailbmp = lib.ImageOperations.vtkImageDataToPreviewBitmap(self.dataUnit, self.thumbtimepoint, ctf, 0, self.height - self.labelheight)
			
		iw, ih = self.thumbnailbmp.GetSize()
		#print "image size=",iw,ih
		wdiff = (self.width - iw) / 2
		if wdiff < 0:wdiff = 0
		self.dc.DrawBitmap(self.thumbnailbmp, wdiff, self.labelheight)
		
	def setMinimumWidth(self, w):
		"""
		Created: 10.02.2005, KP
		Description: Set the minimum width for this item, below which it cannot
					 be resized
		"""       
		self.minSize = w
		
	def setWidth(self, w):
		"""
		Created: 10.02.2005, KP
		Description: Set the width of this item. Will allocate buffer for
					 drawing self.
		"""       
		self.width = w
#        self.SetSize((w,self.height))
		self.oldbuffer = self.buffer
		self.buffer = wx.EmptyBitmap(self.width, self.height)
		del self.dc
		self.drawItem()
		
	def onDown(self, event):
		"""
		Created: 10.02.2005, KP
		Description: Event handler for when the mouse is pressed down over
					 this item. Will store the position in order to enable
					 dragging.
		"""       
		x, y = event.GetPosition()
		ex, ey = event.GetPosition()
		#print "onDow()",x,y
		self.dragMode = 0
		w, h = self.GetSize()
		posx, posy = self.GetPosition()
		x -= posx
		Logging.info("Item number #%d selected" % self.itemnum, kw = "animator")
		if self.itemnum == 0 and x < DRAG_OFFSET:
			# Drag mode where first item is dragged, this affects the
			# empty space at the front
			self.dragMode = 2
		elif x < DRAG_OFFSET:
			# drag mode where an item is dragged from the front
			self.dragMode = 3
			self.beginX = ex
		elif abs(x - w) < DRAG_OFFSET:
			# drag mode where an item is dragged from behind
			self.dragMode = 1
			self.beginX = ex
		return
			
	def canDrag(self, event):
		"""
		Created: 16.7.2005, KP
		Description: A method that tells whether a track item can be dragged
		"""       
		x, y = event.GetPosition()
		w, h = self.GetSize()
		posx, posy = self.GetPosition()
		w = int(w)
		posx = int(posx)
		if x in range(posx - DRAG_OFFSET, posx + DRAG_OFFSET):
			return 1
		if x in range(posx + w - DRAG_OFFSET, posx + w + DRAG_OFFSET):
			return 1
		return 0
		
	def onUp(self, event):
		"""
		Created: 10.02.2005, KP
		Description: Event handler for when mouse is released over this item.
					 Will store the position in order to enable dragging.
		"""    
		x, y = event.GetPosition()
		self.beginX = x
		self.updateItem()
		self.dragMode = 0

	def updateItem(self):
		"""
		Created: 06.04.2005, KP
		Description: A method called when the item has been resized
		"""       
		posx, posy = self.GetPosition()
		posx -= self.parent.getLabelWidth()
		start = self.parent.getDuration(posx)
		w, h = self.GetSize()
		end = self.parent.getDuration(posx + w)
		self.position = (start, end)
		
	def getPosition(self):
		"""
		Created: 11.04.2005, KP
		Description: Return the starting and ending position of this item
		"""       
		return self.position
		
	def onDrag(self, event):
		"""
		Created: 10.02.2005, KP
		Description: Event handler for when the mouse is dragged on the item.
					 Will resize the item accordingly.
		"""
		if self.canDrag(event):
			self.parent.SetCursor(wx.StockCursor(wx.CURSOR_SIZEWE))
		else:
			self.parent.SetCursor(wx.STANDARD_CURSOR)
		if not event.Dragging():
			return
		if not self.dragMode:
			#print "Click closer to the edge"
			return
		self.parent.onDragItem(self, event)
		
		
	def __getstate__(self):
		"""
		Created: 11.04.2005, KP
		Description: Return the dict that is to be pickled to disk
		"""      
		odict = {}
		keys = [""]
		for key in ["position", "pos", "itemnum"]:
			odict[key] = self.__dict__[key]
		if self.timepoint != -1:
			odict["timepoint"] = self.timepoint
		return odict    

	def __str__(self):
		"""
		Created: 05.04.2005, KP
		Description: Return string representation of self
		"""  
		if self.timepoint != -1:
			desc = "T%d" % self.timepoint
		else:
			desc = "I"
		start, end = self.position
		return "[%s %ds:%ds]" % (desc, start, end)
		


class EmptyItem(TrackItem):
	"""
	Class: EmptyItem
	Created: 16.04.2005, KP
	Description: An item representing empty space
	"""       
	def __init__(self, parent, size, **kws):
		"""
		Created: 16.04.2005, KP
		Description: Initialize
		"""       
		TrackItem.__init__(self, parent, "", size, **kws)
		
	def drawItem(self, hilight = -1):
		"""
		Created: 13.04.2005, KP
		Description: A method that draws the item.
		"""
		self.dc = wx.MemoryDC()
		self.dc.SelectObject(self.buffer)

		#self.dc = wx.BufferedDC(wx.ClientDC(self),self.buffer)
		self.dc.Clear()
		self.dc.BeginDrawing()
		col = self.parent.GetBackgroundColour()
		r, g, b = col.Red(), col.Green(), col.Blue()
		col = wx.Colour(r, g, b)
		self.dc.SetBrush(wx.Brush(col))
		self.dc.DrawRectangle(0, 0, self.width, self.height)        
		self.dc.EndDrawing()
		self.dc.SelectObject(wx.NullBitmap)
		
	def __str__(self):
		"""
		Created: 13.04.2005, KP
		Description: Return string representation of self
		"""  
		start, end = self.position
		return "[E %ds:%ds]" % (start, end)      
		
class StopItem(TrackItem):
	"""
	Class: StopItem
	Created: 24.06.2005, KP
	Description: An item representing stop in a camera movement
	"""       
	def __init__(self, parent, size, **kws):
		"""
		Created: 24.06.2005, KP
		Description: Initialize
		"""       
		self.itemnum = -1
		self.stopitem = 1
		TrackItem.__init__(self, parent, "Stop", size, **kws)
		
	def isStopped(self):return 1
		
	def drawItem(self, hilight = -1):
		"""
		Created: 24.06.2005, KP
		Description: A method that draws the item.
		"""
		#self.dc = wx.BufferedDC(wx.ClientDC(self),self.buffer)
		self.dc = wx.MemoryDC()
		self.dc.SelectObject(self.buffer)

		self.dc.Clear()
		self.dc.BeginDrawing()
		self.dc.SetPen(wx.Pen((0, 0, 0)))

		# draw the body
		r, g, b = self.color
		col = wx.Colour(r, g, b)
		self.dc.SetBrush(wx.Brush(col))
		#self.dc.SetBackground(wx.Brush(wx.BLACK))
		self.dc.DrawRectangle(0, 0, self.width, self.height)        

		TrackItem.drawHeader(self)
		
		r, g, b = self.headercolor
		self.dc.SetPen(wx.Pen(wx.Colour(r, g, b), 2))
		self.dc.DrawLine(self.width - 1, 0, self.width - 1, self.height)


		self.dc.SetTextForeground((0, 0, 0))
		self.dc.SetFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.NORMAL))
		s = self.parent.getDuration(self.GetSize()[0])

		text = u"Motionless camera"
		text2 = u"Duration: %.2fs" % (s)
		
		self.dc.DrawText(text, 5, self.labelheight + 5)
		self.dc.DrawText(text2, 5, 10 + self.labelheight + 5)

		if hilight != -1:
			self.hilight(hilight)

		self.dc.EndDrawing()
		self.dc.SelectObject(wx.NullBitmap)
		self.dc = None
		
	def __str__(self):
		"""
		Created: 13.04.2005, KP
		Description: Return string representation of self
		"""  
		start, end = self.position
		return "[STOP %ds:%ds]" % (start, end)    
		
	def __getstate__(self):
		"""
		Created: 11.04.2005, KP
		Description: Return the dict that is to be pickled to disk
		"""      
		odict = {}
		keys = [""]
		for key in ["position", "itemnum"]:
			odict[key] = self.__dict__[key]
		odict["stopitem"] = 1
		return odict    
		
	def __set_pure_state__(self, state):
		"""
		Created: 17.07.2005, KP
		Description: Set the pure state of this item
		"""      
		TrackItem.__set_pure_state__(self, state)
		self.stopitem = state.stopitem
