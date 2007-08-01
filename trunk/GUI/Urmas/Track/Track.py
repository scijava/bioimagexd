# -*- coding: iso-8859-1 -*-

"""
 Unit: Track
 Project: BioImageXD
 Created: 05.02.2005, KP
 Description:

 URM/AS - The Unified Rendering Manager / Animator for Selli
 
 Urmas is a timeline based GUI for controlling the rendering of datasets. The GUI allows users
 to specify a path for the camera to follow (using Heikki Uuksulainen's MayaVi animator code)
 and also allows them to produce videos of the rendering using ffmpeg.
 
 The widgets that implement the Tracks of the timeline are implemented in this module.

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
import Logging
#import os.path
#import sys
#import math, random
#import threading

#from Urmas.TrackItem import *
#from GUI.Urmas import UrmasPalette
import lib.ImageOperations
#import GUI.Dialogs
#import GUI.TimepointSelection
import lib.messenger

class Track(wx.Panel):
	"""
	Created: 04.02.2005, KP
	Description: A class representing a track in the timeline
	"""
	def __init__(self, name, parent, **kws):
		wx.Panel.__init__(self, parent, -1, style = wx.SIMPLE_BORDER)
		self.paintOverlay = 0
		self.number = 0
		self.duration = 0
		self.frames = 0
		self.closed = 0
		self.bold = 0
		self.height = 80
		self.startOfTrack = 0
		self.editable = 1
		self.selectedItem = None
		self.dragItem = None
		self.SetBackgroundColour((255, 255, 255))
		self.control = kws["control"]
		self.splineEditor = self.control.getSplineEditor()
		self.label = name
		self.previtem = None
		if kws.has_key("height"):
			#print "Setting height to ",kws["height"]
			self.height = kws["height"]
		if kws.has_key("editable"):
			self.editable = kws["editable"]
		self.timescale = kws["timescale"]
		if kws.has_key("number"):
			self.number = kws["number"]
			
		self.overlayPosInPixels = 0
		self.overlayPosInPixelsEnd = 0
		self.overlayPos = -1
		self.overlayItem = None              
		
		#self.sizer=wx.GridBagSizer()
		self.color = None
		self.parent = parent

		self.enabled = 1
		w, h = self.parent.GetSize()
		d = self.control.getDuration()
		self.width = d * self.timescale.getPixelsPerSecond() + self.getLabelWidth()

		self.buffer = wx.EmptyBitmap(self.width, self.height)
		self.SetSize((self.width, self.height))
		self.dragEndPosition = 0
				
		self.items = []
		self.itemAmount = 0
		self.oldNamePanelColor = 0
	
		self.initTrack()
		self.timePos = -1
		self.timePosItem = None
		self.timePosInPixels = 0
		self.timePosInPixelsEnd = 0
		
		self.Bind(wx.EVT_MOTION, self.onDrag)
		self.Bind(wx.EVT_LEFT_DOWN, self.onDown)
		self.Bind(wx.EVT_LEFT_UP, self.onUp)
		
		self.Bind(wx.EVT_PAINT, self.onPaint)
		
		self.renew = 0
		s = self.control.getFrames()
		#print "duration=",d,"frames=",s
		self.setDuration(d, s)
		self.paintTrack()
		lib.messenger.connect(None, "show_time_pos", self.onShowTimePosition)

	def getStartOfTrack(self):
		"""
		Created: 15.11.2006, KP
		Description: return the starting position of track, in pixels
		"""
		return self.startOfTrack
		
	def onShowTimePosition(self, obj, evt, arg):
		"""
		Created: 15.08.2005, KP
		Description: Show the frame position
		"""     
		#print "showtimePos",obj,evt,arg
		self.timePos = arg
		# When renew=2 it means that only the time position needs to be re-drawn
		self.renew = 2
		
	def onPaint(self, event):
		"""
		Created: 17.07.2005, KP
		Description: Blit the buffer
		""" 
		if self.renew:
			try:
				self.paintTrack()
			except Exception, e:
				print "Failed to paint track:", e
				event.Skip()
			self.renew = 0
		dc = wx.BufferedPaintDC(self, self.buffer)#,self.buffer)
		
	def paintTrack(self):
		"""
		Created: 17.07.2005, KP
		Description: Paint the track
		""" 
		#print "Painting track",self.buffer.GetWidth(),self.buffer.GetHeight()
		self.dc = wx.BufferedDC(wx.ClientDC(self), self.buffer)
		if self.renew != 2:
			self.dc.Clear()
			self.dc.SetBrush(wx.Brush(self.bg))
			#self.dc.SetPen(wx.Pen(self.fg,1))
			self.dc.BeginDrawing()
			self.dc.DrawRectangle(0, 0, self.getLabelWidth(), self.height)
			
			self.dc.SetTextForeground(self.fg)
			weight = wx.NORMAL
			if self.bold:
				weight = wx.BOLD
			self.dc.SetFont(wx.Font(9, wx.SWISS, wx.NORMAL, weight))
			self.dc.DrawText(self.label, 2, 1)
			
			if self.closed:
				self.dc.SetFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.NORMAL))
				self.dc.DrawText("Closed track", 2, 15)
			# IF CIRCULAR; DRAW TEXT
		
			x = self.startOfTrack + self.getLabelWidth()
			for item in self.items:
				self.dc.DrawBitmap(item.buffer, x, 0)
				item.SetPosition((x, 0))
		
				w, h = item.GetSize()
				x += w

			#self.stored=self.buffer.GetSubBitmap((0,0,self.buffer.GetWidth(),self.buffer.GetHeight()))
			w, h = self.buffer.GetWidth(), self.buffer.GetHeight()
			self.stored = wx.EmptyBitmap(w, h)
			mdc = wx.MemoryDC()
			mdc.SelectObject(self.stored)
			mdc.BeginDrawing()
			mdc.Blit(0, 0, w, h, self.dc, 0, 0)
			self.mdc = mdc  
		elif self.timePosInPixels:
			self.dc.Blit(self.timePosInPixels - 1, 0, self.timePosInPixelsEnd, self.height, self.mdc, self.timePosInPixels - 1, 0)
		pps = self.timescale.getPixelsPerSecond() 

		if hasattr(self, "onPaintTrack"):
			self.onPaintTrack()
			
		if self.paintOverlay == 1:
			self.onPaintOverlay()
		
		if self.timePos != -1:
			pos = self.getLabelWidth() + self.timePos * pps        
			self.dc.SetPen(wx.Pen((255, 255, 255), 2))
			self.dc.DrawLine(pos, 0, pos, self.height)
			self.timePosInPixels = pos
			self.timePosInPixelsEnd = pos + 5
		
		self.dc.EndDrawing()
		self.dc = None

	def onPaintOverlay(self):
		"""
		Created: 22.08.2005, KP
		Description: Called by Track so that track types can do their own painting
		"""
		if self.renew != 2 and self.overlayPosInPixels:
			self.dc.Blit(self.overlayPosInPixels - 1, 0, self.overlayPosInPixelsEnd, self.height, self.mdc, self.overlayPosInPixels - 1, 0)                    
		
		#print "overlayPos=",self.overlayPos,"overlayItem=",self.overlayItem
		if self.overlayPos != -1:
			if not self.overlayItem or (self.overlayPos != self.overlayItem.getPosition()[0]):
				curr = None
				for item in self.items:
					start, end = item.getPosition()
					if start <= self.overlayPos and end >= self.overlayPos:
						curr = item
						break
				self.overlayItem = curr
				self.overlayPos = start

			# It is possible that the overlay item is not found e.g.
			# if the user has dragged the item
			# in that case, just don't paint it
			if not self.overlayItem:
				return
			start, end = self.overlayItem.getPosition()
			pps = self.timescale.getPixelsPerSecond() 
			w = (end - start) * pps
			h = self.height
			#print "Painting overlay at ",self.overlayPos*pps
			try:
				color, percentage = self.overlayColor
				overlay = lib.ImageOperations.getOverlay(int(w), int(h), color, percentage)
			except Exception, e:
				print "Failed to create overlay:", e
				#sys.stdin.readline()
			overlay = overlay.ConvertToBitmap()
			overlaydc = wx.MemoryDC()
			overlaydc.SelectObject(overlay)
			pen = wx.Pen(wx.Colour(255, 255, 255), 2)
			overlaydc.SetPen(pen)
			overlaydc.SetBrush(wx.TRANSPARENT_BRUSH)
			overlaydc.DrawRectangle(1, 1, w - 3, h - 3)
			overlaydc.SelectObject(wx.NullBitmap)
			
			
			pos = self.getLabelWidth() + self.overlayPos * pps
			self.overlayPosInPixelsEnd = pos + w + 1
			self.overlayPosInPixels = pos
			self.dc.DrawBitmap(overlay, pos, 0, 1)            
	   
	def updateItemSizes(self):
		"""
		Created: 15.12.2005, KP
		Description: Update each item's width based on it's position
		"""       
		pps = self.timescale.getPixelsPerSecond()
		for item in self.items:
			x, y = item.getPosition()
			item.setWidth(abs(x - y) * pps)
		
	def updatePositions(self):
		"""
		Created: 17.07.2005, KP
		Description: Update each item with new position
		"""
		x = self.startOfTrack + self.getLabelWidth()
		for item in self.items:
			item.SetPosition((x, 0))
			w, h = item.GetSize()
			x += w
		 
		
	def onEvent(self, etype, event):
		"""
		Created: 17.07.2005, KP
		Description: Item is dragged
		"""    
		ex, ey = event.GetPosition()
		for item in self.items:
			x, y = item.GetPosition()
			w, h = item.GetSize()
			if ex >= x and ex <= x + w:
				eval("item.on%s(event)" % etype)
				self.selectedItem = item
				return 1
		return 0
				
	def onDrag(self, event):
		"""
		Created: 17.07.2005, KP
		Description: Item is clicked
		"""
		if self.dragItem and self.dragItem.dragMode:
			self.dragItem.onDrag(event)
			return
		self.onEvent("Drag", event)
		self.dragItem = self.selectedItem
						
				
	def onDown(self, event):
		"""
		Created: 17.07.2005, KP
		Description: Item is clicked
		"""
		ret = self.onEvent("Down", event)
		#print "ret=",ret,"selectedItem=",self.selectedItem
		if ret:
			item = self.selectedItem
			#print "dragmode=",self.selectedItem.dragMode
		else:
			item = None
			
		if self.selectedItem and self.selectedItem.dragMode:
			return ret
		self.selectedItem = None
		if item:
			#print "Setting overlay item"
			#self.timePosItem=self.selectedItem
			start, end = item.getPosition()
			self.overlayItem = item
			self.overlayPos = start
			return ret
		else:
			self.overlayPos = -1
			self.overlayItem = None          
		
		return ret

	def removeActiveItem(self):
		"""
		Created: 31.01.2006, KP
		Description: Remove the currently selected item
		"""        
		if self.selectedItem:
			self.items.remove(self.selectedItem)
			self.overlayPosInPixels = 0
			self.overlayPosInPixelsEnd = 0
			self.overlayPos = -1
			self.overlayItem = None    
			self.paintTrack()
		   
			
			
	def onUp(self, event):
		"""
		Created: 17.07.2005, KP
		Description: Item is clicked
		"""
		if self.selectedItem:
			self.selectedItem.onUp(event)
		#if not self.onEvent("Up",event):
		self.setSelected(event)
		
				
	def getItems(self):
		"""
		Created: 19.04.2005, KP
		Description: Return items in this track
		""" 
		return self.items
		
	def setSelected(self, event):
		"""
		Created: 14.04.2005, KP
		Description: Selects this track
		"""
		#print "setSelected(",event,")"
		if event:
			self.bold = 1
			self.parent.setSelectedTrack(self)
		else:
			print "\n\n*** IM NOT SELECTE#D ANYMORE"
			self.SetWindowStyle(wx.SIMPLE_BORDER)
			self.bold = 0
			# Reset also the overlay
			self.overlayPosInPixels = 0
			self.overlayPosInPixelsEnd = 0
			self.overlayPos = -1
			self.overlayItem = None              
			
		self.paintTrack()
			
	def setEnabled(self, flag):
		"""
		Created: 14.04.2005, KP
		Description: Enables / disables this track
		""" 
		self.enabled = flag
		if not flag:
			self.oldNamePanelColor = col
			r = g = b = 200
			#print "Setting background to ",r,g,b
			self.fg = (128, 128, 128)
			self.bg = (r, g, b)
		else:
			self.fg = (0, 0, 0)
			self.bg = self.nameColor

		
	def OnDragOver(self, x, y, d):
		"""
		Created: 12.04.2005, KP
		Description: Method called to indicate that a user is dragging
					 something to this track
		""" 
		#print "OnDragOver(%d,%d,%s)"%(x,y,d)
		if not self.oldNamePanelColor:
			col = self.bg
			#r,g,b=col.Red(),col.Green(),col.Blue()
			r, g, b = col
			self.oldNamePanelColor = col
			r = int(r * 0.8)
			g = int(g * 0.8)
			b = int(b * 0.8)
			self.fg = (255, 255, 255)
			self.bg = (r, g, b)
			self.paintTrack()
			self.Refresh()
		curritem = None
		n = 0
		for item in self.items:
			ix, iy = item.GetPosition()
			w, h = item.GetSize()
			#print "ix,iy=",ix,iy
			if ix <= x:
				n += 1
			if ix <= x and ix + w >= x:
				#print "Found item",item
				curritem = item
				self.dragEndPosition = self.items.index(item) + 1
				d = abs(ix - x)
				if d < w / 2:
					self.dragEndPosition -= 1
			if self.previtem and self.previtem != curritem:
				self.previtem.drawItem()
				#self.previtem.Refresh()
		if curritem:
			curritem.OnDragOver(x, y)
			self.previtem = curritem
		else:
			if n == 0:
				self.dragEndPosition = 0
			else:
				self.dragEndPosition = -1
		
	def OnDragLeave(self):
		"""
		Created: 12.04.2005, KP
		Description: Method called to indicate that a user is no longer dragging
					 something to this track
		"""     
		self.oldNamePanelColor = None
		self.fg = (0, 0, 0)
		self.bg = self.nameColor
		self.paintTrack()
		self.Refresh()

	def __set_pure_state__(self, state):
		"""
		Created: 11.04.2005, KP
		Description: Method called by UrmasPersist to allow the object
					 to refresh before it's items are created
		""" 
		print "Setting pure state of track"
		Logging.info("Set pure state of track", state.label, kw = "animator")
		self.label = state.label
		self.startOfTrack = state.startOfTrack
		self.color = state.color
		self.nameColor = state.nameColor
		#self.namePanel.setLabel(self.label)
		
	def updateLabels(self):
		"""
		Created: 19.03.2005, KP
		Description: A method that updates all the items in this track
		"""           
		#print "Updating labels"
		for item in self.items:
			item.updateItem()
			item.drawItem()
			#item.Refresh()
		self.paintTrack()
		self.Refresh()
#        self.Layout()

	def getMinItemSize(self):
		"""
		Created: 15.11.2006, KP
		Description: Return a minimal item size in pixels based on duration and amount of frames
		"""
		
		spf = self.control.getSecondsPerFrame()
		pps = self.control.getPixelsPerSecond()
		print "MINIMUM ITEM SIZE=", spf, "(IN PIXELS=", spf * pps, ")"
		return spf * pps
		
	def onDragItem(self, trackitem, event):
		"""
		Created: 16.07.2005, KP
		Description: Execute dragging of item
		"""         
		x, y = event.GetPosition()
		#print "onDragItem",trackitem.dragMode,x,y
		
		if trackitem.dragMode == 2:
			x -= self.getLabelWidth()
			#print "Setting empty space to ",x
			self.setEmptySpace(x)
			self.paintTrack()
			self.Refresh()
			return
		
		posx, posy = trackitem.GetPosition()    
		minItemSize = self.getMinItemSize()        
		
		# Dragged from the beginning
		if trackitem.dragMode == 3:
			diff = x - trackitem.beginX
			# we actually need to drag the previous item
			pos = self.items.index(trackitem)
			pos -= 1
			item = self.items[pos]
			if diff >= 0:
				itemdiff = diff
				#trackitemdiff=-diff
				trackitemdiff = 0
			elif diff < 0:
				itemdiff = diff
				#trackitemdiff=abs(diff)
				trackitemdiff = 0
			#print "diff=",diff,"itemdiff=",itemdiff,"trackdiff=",trackitemdiff

				
			
			itemNewWidth = item.width + itemdiff
			print "item new width=", itemNewWidth, "minItemSize=", minItemSize
			if itemNewWidth < item.minSize:
				return
			if itemNewWidth < minItemSize:
				itemNewWidth = minItemSize
				
			
			trackItemNewWidth = trackitem.width + trackitemdiff
			#print "Trackitem New width=",trackItemNewWidth
			
			if trackItemNewWidth < trackitem.minSize:
				return
			if trackItemNewWidth < minItemSize:
				trackItemNewWidth = minItemSize
				
			item.setWidth(itemNewWidth)
			trackitem.setWidth(trackItemNewWidth)
			trackitem.beginX = x
	
		elif trackitem.dragMode == 1:
			diff = x - trackitem.beginX
			#print "beginX=",trackitem.beginX,"x=",x,"diff=",diff
			newTrackItemWidth = trackitem.width + diff
			if newTrackItemWidth < trackitem.minSize:
				return
			if newTrackItemWidth < minItemSize:
				newTrackItemWidth = minItemSize
				
			if diff > 0 and not self.itemCanResize(trackitem.width, trackitem.width + diff):
				print "Would go over the timescale"
				return
			trackitem.beginX = x
			trackitem.setWidth(newTrackItemWidth)
		#self.updatePositions()
		self.paintTrack()
		self.Refresh()
#        self.updateLayout()
		
	def remove(self):
		"""
		Created: 06.04.2005, KP
		Description: Remove all items from self
		"""               
		for i in range(len(self.items) - 1, 0, -1):
			self.removeItem(i)
		
	def removeItem(self, position):
		"""
		Created: 14.04.2005, KP
		Description: Remove an item from this track
		"""              
		print "Removing item ", position
		item = self.items[position]
		self.items.remove(item)
		
	def setDataUnit(self, dataUnit):
		"""
		Created: 04.02.2005, KP
		Description: A method to set the dataunit this track contains
		"""           
		self.dataUnit = dataUnit
		
	def getNumberOfTimepoints(self):
		"""
		Created: 04.02.2005, KP
		Description: Return the number of items in this track
		"""               
		return len(self.items)
		
	  
	def itemCanResize(self, fromWidth, toWidth):
		"""
		Created: 04.02.2005, KP
		Description: A method that tells whether an item can change its size
					 from the specified size to a new size
		"""               
		return 1
		diff = toWidth - fromWidth
		w += diff
		
		#print "w=",w,"duration=",self.duration,"pps=",self.timescale.getPixelsPerSecond()
		if w > self.duration * self.timescale.getPixelsPerSecond():
			return 0
		return 1
		
	def initTrack(self):
		"""
		Created: 11.04.2005, KP
		Description: Initialize the GUI portion of this track
		"""
		self.items = []
   
		
	def setDuration(self, seconds, frames, **kws):
		"""
		Created: 04.02.2005, KP
		Description: A method to set the length of this track, affecting
					 size of its items
		"""              
		self.duration = seconds
		self.frames = frames
		
		
		w = self.duration * self.timescale.getPixelsPerSecond()
		self.width = w + self.getLabelWidth()
		print "Set duration of ", self, " to ", seconds, "new width=", self.width
		self.buffer = wx.EmptyBitmap(self.width, self.height)
		self.SetSize((self.width, self.height))
		self.renew = 0
		self.paintTrack()

	def expandToMax(self, keep_ratio = 0):
		"""
		Created: 19.04.2005, KP
		Description: Expand this track to it's maximum size
		"""              
		n = len(self.items)
		if not n:
			return
		
		w = float(self.duration) / float(n)
		w *= self.timescale.getPixelsPerSecond()
		lastpos = self.items[-1].getPosition()[1]
		coeff = self.timescale.getDuration() / float(lastpos)
		#print "coeff=",coeff
		tot = 0
		last = 0
		for i in self.items:
			if keep_ratio:
				neww = i.width * coeff
			else:
				neww = w
			i.setWidth(neww)
			tot += w
			last = i
	   
		diff = self.duration * self.timescale.getPixelsPerSecond() - tot
		if diff > 1:
			#print "diff=",diff
			last.setWidth(w + diff)
		self.updateLayout()
		
	def setToSizeTotal(self, size):
		"""
		Created: 19.04.2005, KP
		Description: Set duration of all items in this track
		"""              
		n = float(size) / len(self.items)
		self.setToSize(n)

	def setToSize(self, size = 8):
		"""
		Created: 19.04.2005, KP
		Description: Set each item on this track to given size
		"""              
		n = len(self.items)
		if not n:
			return
		
		tot = 0
		last = 0
		for i in self.items:
			i.setWidth(size)
			tot += size
			last = i
	   
		self.updateLayout()

	def setEmptySpace(self, space):
		"""
		Created: 15.04.2005, KP
		Description: Sets the empty space at the beginning of a track
		"""        
		maxempty = self.parent.getLargestTrackLength(self)
		if space < 0:
			space = 0
		if 0 and space > maxempty:
			Logging.info("Won't grow beyond ", maxempty, kw = "animator")
			space = maxempty
		#self.positionItem.setWidth(space)
		self.startOfTrack = space
		
		self.buffer = wx.EmptyBitmap(self.width + space, self.height)
		self.paintTrack()
#        self.positionItem.SetSize((space,-1))
		#self.Layout()
		self.Refresh()
		#self.updateLayout()
		#print "setting positionItem size",space

	def GetSize(self):
		return (self.width + self.startOfTrack, self.height)
		
	def getLabelWidth(self):
		"""
		Created: 04.02.2005, KP
		Description: A method that returns the width of the name panel
		"""               
		return self.timescale.getLabelWidth()

	def setColor(self, col):
		"""
		Created: 04.02.2005, KP
		Description: A method that sets the color of this track's items
		"""               
		self.color = col
		self.headercolor = (127, 127, 127)
		for item in self.items:
			item.setColor(col, self.headercolor)
			#item.Layout()
			
	def updateLayout(self):
		"""
		Created: 04.02.2005, KP
		Description: A method that updates the layout of this track
		"""               
		#self.Layout()
		#self.parent.Layout()
		for item in self.items:
			item.updateItem()
		self.paintTrack()
		self.Refresh()

	def shiftItems(self, direction):
		"""
		Created: 15.12.2005, KP
		Description: Shift items in the given direction
		"""      
		print "Shifting items ", direction
		nitems = []
		n = len(self.items)
		nitems = [self.items[i % n] for i in range(direction, n + direction)]
		for i, item in enumerate(nitems):
			item.setItemNumber(i)
		self.items = nitems
		print "shifted items: ", self.items
		self.paintTrack()
		self.Refresh()
		
	def getDuration(self, pixels):
		"""
		Created: 20.03.2005, KP
		Description: A method that returns the time the camera takes to travel
					 given part of the spline
		""" 
		return float(pixels) / self.control.getPixelsPerSecond()
		
	def getPixels(self, duration):
		"""
		Created: 11.04.2005, KP
		Description: A method that returns the amount of pixels a given
					 number of seconds streches on the timeline
		""" 
		return float(duration) * self.control.getPixelsPerSecond()
		
	def __str__(self):
		"""
		Created: 05.04.2005, KP
		Description: Return string representation of self
		"""        
		s = "%s [\n" % self.label
		s += ", ".join(map(str, self.items))
		s += "]\n"
		return s
		
	def __getstate__(self):
		"""
		Created: 11.04.2005, KP
		Description: Return the dict that is to be pickled to disk
		"""      
		odict = {}
		keys = [""]
		self.itemAmount = len(self.items)
		for key in ["label", "items", "color", "nameColor", "number", "itemAmount", "startOfTrack"]:
			odict[key] = self.__dict__[key]
		return odict        
	
		
			

		
#import KeyframeTrack
		
