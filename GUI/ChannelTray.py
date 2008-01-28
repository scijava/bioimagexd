# -*- coding: iso-8859-1 -*-
"""
 Unit: ChannelTray
 Project: BioImageXD
 Created: 20.06.2006, KP
 Description:

 A panel that lets the user select from given channels
 
 Copyright (C) 2006  BioImageXD Project
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

#import ImageOperations
#import vtk

import  wx.lib.buttons  as  buttons
import lib.messenger
import os.path
import  wx.lib.scrolledpanel as scrolled
import wx

class ChannelTray(wx.Panel):
	"""
	Created: 20.06.2006, KP
	Description: A frame used to let the user select from the different masks
	"""
	def __init__(self, parent, **kws):
		"""
		Initialization
		"""          
		wx.Panel.__init__(self, parent, -1)
				
		self.sizer = wx.GridBagSizer()
		self.SetSizer(self.sizer)
		self.SetAutoLayout(1)
		
		self.channels = []
		self.buttons = []
		self.previews = []
		self.selectedChannel = None
		
		self.scrollSizer = wx.GridBagSizer()
		self.scroll = scrolled.ScrolledPanel(self, -1, size = (400, 90))
		self.scroll.SetSizer(self.scrollSizer)
		self.scroll.SetAutoLayout(1)
		self.scroll.SetupScrolling()
		
		self.sizer.Add(self.scroll, (0, 0), flag = wx.EXPAND | wx.ALL)
		
	def addChannel(self, name, color, filename, dims, bmp):
		"""
		Add a channel to the tray
		"""                 
		b = buttons.GenBitmapToggleButton(self.scroll, -1, bmp)
		self.Bind(wx.EVT_BUTTON, self.onToggleButton, b)
		self.buttons.append(b)
		self.units.append((name, filename, color, dims))
		n = len(self.units)
		
		self.scrollSizer.Add(b, (0, n - 1))        
		self.scroll.SetupScrolling()
		self.Layout()

	def clear(self):
		"""
		clear the items bar
		"""
		for btn in self.buttons:
			btn.Show(0)
			self.scrollSizer.Detach(btn)
		self.buttons = []
		self.channels = []
		self.buttons = []
		self.previews = []
		self.scroll.SetupScrolling()
		self.Layout()
		
	def setPreview(self, i, bmp):
		"""
		set the bitmap for this channel
		"""
		name, filename, color, dims = self.units[i]
		bmp = self.getPreviewBitmap(bmp, name, dims, color)
		self.buttons[i].SetBitmapLabel(bmp)
		self.buttons[i].Refresh()
		self.previews[i] = bmp
		
	def onToggleButton(self, evt):
		"""
		A callback for when the user toggles a button
		"""   
		for i, btn in enumerate(self.buttons):
			if btn.GetId() != evt.GetId():
				btn.SetValue(0)
			else:
				self.selectedChannel = i
				lib.messenger.send(None, "channel_selected", self.selectedChannel)
	def SetSelection(self, n):
		"""
		select a given channel
		"""
		for i, btn in enumerate(self.buttons):
			btn.SetValue(i == n)
		self.selectedChannel = n
		lib.messenger.send(None, "channel_selected", self.selectedChannel)
		
	def getPreviewBitmap(self, preview, name, size, color):
		"""
		return an image of a channel with relevant info like channel name coupled to it's preview bitmap
		"""        
		bmp = wx.EmptyBitmap(60, 80, -1)
		dc = wx.MemoryDC()
		dc.SelectObject(bmp)
		dc.BeginDrawing()
		#dc.SetBackground(wx.Brush(color))
		dc.Clear()
		r, g, b = color
		dc.SetBrush(wx.Brush(wx.Colour(r, g, b)))
		dc.DrawRectangle(0, 0, 56, 56)

		dc.DrawBitmap(preview, 3, 3)
		dc.SetFont(wx.Font(9, wx.SWISS, wx.NORMAL, wx.BOLD))
		dc.DrawText(name, 3, 56)
		
		dc.SetTextForeground(wx.Colour(40, 40, 40))
		dc.SetFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.NORMAL))
		x, y, z = size
		dc.DrawText("%d x %d x %d" % (x, y, z), 3, 66)
		
						
		dc.EndDrawing()
		dc.SelectObject(wx.NullBitmap)
		dc = None    
		return bmp

	def setDataUnit(self, dataunit, toolImage = (32, 32)):
		"""
		Set the dataunit to be listed
		"""
		w, h = toolImage
		self.imageW, self.imageH = w, h
		self.dataUnit = dataunit
		try:
			units = self.dataUnit.getSourceDataUnits()
		except:
			units = [self.dataUnit]
		self.units = []
		for i, unit in enumerate(units):
			self.previews.append(wx.EmptyBitmap(60, 80))
			name = unit.getName()
			filename = "(no file)"
			if hasattr(unit, "dataSource"):
				filename = unit.dataSource.getFileName()
				filename = os.path.basename(filename)
			x, y, z = unit.getDimensions()
			ctf = unit.getColorTransferFunction()
			if ctf:
				val = [0, 0, 0]
				ctf.GetColor(255, val)
				r, g, b = val
				r *= 255
				g *= 255
				b *= 255
			else:
				r, g, b = 255, 255, 255
			self.addChannel(name,  (r, g, b), filename, (x, y, z), self.previews[i])
			self.dataUnit = dataunit
		
		
  
