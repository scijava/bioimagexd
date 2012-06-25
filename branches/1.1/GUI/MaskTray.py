# -*- coding: iso-8859-1 -*-
"""
 Unit: MaskTray
 Project: BioImageXD
 Created: 20.06.2006, KP
 Description:

 A panel that shows all the masks created in the software
 
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

import wx.lib.buttons  as  buttons
import bxdexceptions
import lib.ImageOperations
import wx.lib.scrolledpanel as scrolled
import vtk
import wx
import lib.messenger

masks = []

class Mask:
	"""
	Created: 20.06.2006, KP
	Description: A mask class
	"""
	def __init__(self, name, size, image):
		"""
		Initialization
		"""
		self.name = name
		self.size = size
		self.image = image
		self.ctf = vtk.vtkColorTransferFunction()
		self.ctf.AddRGBPoint(0, 0, 0, 0)
		self.ctf.AddRGBPoint(255, 1.0, 1.0, 1.0)
		
	def getMaskImage(self):
		"""
		Return the mask image
		"""   
		return self.image
		
	def getAsBitmap(self, bg = wx.Colour(255, 255, 255)):
		"""
		Return a preview bitmap of the mask
		"""           
		preview = lib.ImageOperations.getMIP(self.image, self.ctf)
		preview = lib.ImageOperations.vtkImageDataToWxImage(preview)
		preview.Rescale(80, 80)
		preview = preview.ConvertToBitmap()
		
		bmp = wx.EmptyBitmap(100, 120, -1)
		dc = wx.MemoryDC()
		dc.SelectObject(bmp)
		dc.BeginDrawing()
		dc.SetBackground(wx.Brush(bg))
		dc.Clear()
		dc.DrawBitmap(preview, 10, 10)
		
		dc.SetFont(wx.Font(9, wx.SWISS, wx.NORMAL, wx.BOLD))
		dc.DrawText(self.name, 10, 90)
		
		dc.SetTextForeground(wx.Colour(40, 40, 40))
		dc.SetFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.NORMAL))
		x, y, z = self.size
		dc.DrawText("%d x %d x %d" % (x, y, z), 10, 105)
						
		dc.EndDrawing()
		dc.SelectObject(wx.NullBitmap)
		dc = None    
		return bmp
		


class MaskTray(wx.MiniFrame):
	"""
	Created: 20.06.2006, KP
	Description: A frame used to let the user select from the different masks
	"""
	def __init__(self, parent, **kws):
		"""
		Initialization
		"""
		wx.MiniFrame.__init__(self, parent, -1, "Mask selection", size = (410, 210), style = wx.DEFAULT_FRAME_STYLE)
				
		self.panel = wx.Panel(self, -1)
		self.sizer = wx.GridBagSizer()
		self.panel.SetSizer(self.sizer)
		self.panel.SetAutoLayout(1)
		
		self.masks = []
		self.buttons = []
		self.selectedMask = None
		
		self.scrollSizer = wx.GridBagSizer()
		self.scrollSizer.SetEmptyCellSize((0,0))
		self.scroll = scrolled.ScrolledPanel(self.panel, -1, size = (410, 150))
		self.scroll.SetSizer(self.scrollSizer)
		self.scroll.SetAutoLayout(1)
		self.scroll.SetupScrolling()
		
		self.sizer.Add(self.scroll, (0, 0), flag = wx.EXPAND | wx.ALL)
		
		self.buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
		self.okButton = wx.Button(self.panel, -1, "Select")
		self.nomaskButton = wx.Button(self.panel, -1, "No mask")
		self.cancelButton = wx.Button(self.panel, -1, "Cancel")
		self.removeButton = wx.Button(self.panel, -1, "Remove")
		
		self.okButton.Bind(wx.EVT_BUTTON, self.onSelectMask)
		self.nomaskButton.Bind(wx.EVT_BUTTON, self.onSetNoMask)
		self.cancelButton.Bind(wx.EVT_BUTTON, self.onCancel)
		self.removeButton.Bind(wx.EVT_BUTTON, self.onRemoveMask)
		
		self.buttonSizer.Add(self.cancelButton, 0, wx.ALIGN_RIGHT)
		self.buttonSizer.Add((20, 20), 0, wx.EXPAND)
		self.buttonSizer.Add(self.nomaskButton, 0, wx.ALIGN_RIGHT)
		self.buttonSizer.Add((20, 20), 0, wx.EXPAND)
		self.buttonSizer.Add(self.okButton, 0, wx.ALIGN_RIGHT)
		self.buttonSizer.Add((20, 20), 0, wx.EXPAND)
		self.buttonSizer.Add(self.removeButton, 0, wx.ALIGN_RIGHT)
		
		self.sizer.Add(self.buttonSizer, (1, 0), flag = wx.EXPAND | wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER)
		
		self.panel.Fit()
		
	def onSetNoMask(self, evt):
		"""
		Disable the use of masks
		"""   
		self.dataUnit.setMask(None)
		lib.messenger.send(None,"mask_changed")
		self.Close(True)
		
	def addMask(self, mask = None, name = "Mask", imagedata = None):
		"""
		Add a mask to the tray
		"""   
#		if not mask and (name and imagedata):
#			m = Mask(name, imagedata.GetDimensions(), imagedata)
#		elif mask:
#			m = mask
#		else:
#			raise bxdexceptions.MissingParameterException("No mask given")
#		self.masks.append(m)

		if not mask:
			raise bxdexceptions.MissingParameterException("No mask given")
		elif name and imagedata:
			mask = Mask(name, imagedata.GetDimensions(), imagedata)

		self.masks.append(mask)
		maskBitmap = mask.getAsBitmap(self.GetBackgroundColour())

		genericToggleButton = buttons.GenBitmapToggleButton(self.scroll, -1, maskBitmap)
		self.Bind(wx.EVT_BUTTON, self.onToggleButton, genericToggleButton)
		self.buttons.append(genericToggleButton)
		maskAmount = len(self.masks)

		self.scrollSizer.Add(genericToggleButton, (0, maskAmount - 1))
		self.scroll.SetupScrolling()
		self.Layout()
		
	def onToggleButton(self, evt):
		"""
		A callback for when the user toggles a button
		"""
		for i, btn in enumerate(self.buttons):
			if btn.GetId() != evt.GetId():
				btn.SetValue(0)
			else:
				self.selectedMask = self.masks[i]
				
	def setDataUnit(self, dataUnit):
		"""
		Set the dataunit to which the selected mask will be applied
		"""   
		self.dataUnit = dataUnit
		
	def onSelectMask(self, evt):
		"""
		A callback for when the user has selected a mask
		"""
		if self.selectedMask:
			self.dataUnit.setMask(self.selectedMask)
			lib.messenger.send(None,"mask_changed")
		self.Close(True)
		
	def onCancel(self, evt):
		"""
		A callback for when the user wishes to cancel the selection
		"""   
		self.Close(True)

	def onRemoveMask(self, evt):
		"""
		A callback for removing a mask
		"""
		if self.selectedMask:
			for i,m in enumerate(self.masks):
				if m == self.selectedMask:
					self.masks.pop(i)
					button = self.buttons.pop(i)
					self.Unbind(wx.EVT_BUTTON, button)
					button.Destroy()
					self.selectedMask = None
					lib.messenger.send(None, "remove_mask", i)
					self.scroll.SetupScrolling()
					self.Layout()
