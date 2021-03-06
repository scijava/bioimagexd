# -*- coding: iso-8859-1 -*-

"""
 Unit: Toolbar
 Project: BioImageXD
 Created: 03.02.2005, KP
 Description:

 A resizing toolbar

 Copyright (C) 2006	 BioImageXD Project
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
__version__ = "$Revision: 1.21 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

from wx.lib.buttons import GenBitmapButton
from wx.lib.buttons import GenBitmapToggleButton
import platform
import wx

class ToolCommandEvent(wx.PyCommandEvent):
	def __init__(self, eventType, eid, isdown):
		wx.PyCommandEvent.__init__(self, eventType, eid)
		self.isdown = isdown
		
	def IsChecked(self):
		return self.isdown

class Toolbar(wx.Panel):
	"""
	A toolbar that can change it's amount of tool rows based on it's size
	"""
	def __init__(self, parent, wid, pos = wx.DefaultPosition, size = wx.DefaultSize,
			style = wx.TB_HORIZONTAL | wx.NO_BORDER, name = ""):
		"""
		Initialize the toolbar
		"""
		wx.Panel.__init__(self, parent, wid, pos, size, style)
		#self.SetBackgroundColour((255,255,0))
		self.toolSize = (32, 32)
		self.parent = parent
		self.x = 0
		self.ctrlToRow = {}
		self.toolSeparation = 5
		self.totSizer = wx.BoxSizer(wx.VERTICAL)
		self.sizer = wx.GridBagSizer(self.toolSeparation, self.toolSeparation)
		self.totSizer.AddSpacer((0, 10))
		self.totSizer.Add(self.sizer)
		self.sizes = []
		self.rowsizers = []
		self.oldLayout = []
		self.nondarwin = platform.system() != "Darwin"
		self.ctrls = []
		self.idToTool = {}
		self.minSize = 999999
		self.SetSizer(self.totSizer)
		self.SetAutoLayout(1)
		self.Bind(wx.EVT_SIZE, self.OnSize)
		
	def OnSize(self, evt):
		"""
		Event handler for size events
		"""
		size = evt.GetSize()
		if size[0] == 0:
			return
		layout = self.getLayout(size[0])
		if layout != self.oldLayout:
			self.createRows(layout)
			self.ReOrderItems(layout, size[0])
			self.oldLayout = layout
			
			x = self.GetSize()[0]
			if self.nondarwin:
				#TODO Magic numbers 44 and 50
				y = 44 * len(layout)
			else:
				y = 50 * len(layout)
			self.parent.SetDefaultSize((x, y))
			self.Layout()
			self.sizer.Fit(self)
			self.parent.Layout()
			
	def ReOrderItems(self, layout, width):
		"""
		Re-order the items based on a given layout
		"""
		for sizer in self.rowsizers:
			try:
				while sizer.GetItem(0):
					sizer.Detach(0)
			except:
				pass
		ms = 0
		for y, row in enumerate(layout):
			self.x = 0
			for i, ctrl in enumerate(row):
				self.rowsizers[y].Add(ctrl)
				self.rowsizers[y].AddSpacer((self.toolSeparation, 0))
				self.ctrlToRow[ctrl] = self.rowsizers[y]
				ms += self.sizes[i] + self.toolSeparation
		self.minSize = ms
		
	def getLayout(self, width):
		"""
		Get the optimal layout for current controls and given width
		"""
		ctrls = []
		curr = []
		ms = 0
		
		for i, ctrl in enumerate(self.ctrls):
			if ms + self.toolSeparation + self.sizes[i] > width:
				ctrls.append(curr)
				curr = []
				ms = 0
			curr.append(ctrl)
			ms += self.sizes[i] + self.toolSeparation
		if curr not in ctrls:
			ctrls.append(curr)
		n = 0
		for i in ctrls:
			n += len(i)
		return ctrls
		
		
	def EnableTool(self, toolid, flag):
		"""
		Enable / Disable a tool
		"""
		self.idToTool[toolid].Enable(flag)
		
	def createRows(self, layout):
		"""
		Create enough rows to fit a given layout
		"""
		for y in range(len(layout)):
			if len(self.rowsizers) <= y:
				rowsizer = wx.BoxSizer(wx.HORIZONTAL)
				self.rowsizers.append(rowsizer)
				self.sizer.Add(rowsizer, (y, 0), flag = wx.EXPAND | wx.LEFT | wx.RIGHT)
		
	def Realize(self):
		"""
		Render the toolbar
		"""
		w = self.GetSize()[0]
		if not w:
			return
		layout = self.getLayout(w)
		self.createRows(layout)
		self.ReOrderItems(layout, w)
	
		self.Layout()
		self.Refresh()
		
	def DeleteTool(self, toolid):
		"""
		Delete a tool
		"""
		ctrl = self.idToTool[toolid]
		self.ctrls.remove(ctrl)
		del self.idToTool[toolid]
		if ctrl in self.ctrlToRow:
			sizer = self.ctrlToRow[ctrl]
			sizer.Detach(ctrl)
			ctrl.Show(0)
			sizer.Remove(ctrl)
			
		w = self.GetSize()[0]
		layout = self.getLayout(w)
		self.ReOrderItems(layout, w)
				
		
	def AddControl(self, ctrl):
		"""
		Add a control to the toolbar
		"""
		self.ctrls.append(ctrl)
		self.idToTool[ctrl.GetId()] = ctrl
		self.sizes.append(ctrl.GetSize()[0])
		#self.sizer.Add(ctrl,(self.y,self.x))
		self.x += 1
		
	def onToolButton(self, evt):
		"""
		A method for passing the events forward in event chain
		"""
		nevt = ToolCommandEvent(wx.EVT_TOOL.evtType[0], evt.GetId(), evt.GetIsDown())
		self.GetEventHandler().ProcessEvent(nevt)
		
	def AddSimpleTool(self, wid, bitmap, shortHelpString = '', longHelpString = '', isToggle = 0):
		"""
		A method for adding a tool to the toolbar
		"""
		if not isToggle:
			#btn = wx.BitmapButton(self,id,bitmap,size=self.toolSize)
			btn = GenBitmapButton(self, wid, bitmap, style = wx.BORDER_NONE, size = self.toolSize)
		else:
			btn = GenBitmapToggleButton(self, wid, bitmap, size = (-1, self.toolSize[1]))
		
		btn.Bind(wx.EVT_BUTTON, self.onToolButton)
		btn.SetToolTipString(longHelpString)
		#self.sizer.Add(btn,(self.y,self.x))
		self.ctrls.append(btn)
		self.idToTool[wid] = btn
		self.sizes.append(btn.GetSize()[0])
		self.x += 1
		
	def ToggleTool(self, toolid, flag):
		"""
		A method for toggling a togglebutton on or off
		"""
		ctrl = self.idToTool[toolid]
		ctrl.SetToggle(flag)
		
	def DoAddTool(self, wid, label, bitmap, bmpDisabled = None,
		kind = wx.ITEM_NORMAL, shortHelp = '', longHelp = '', clientData = None):
		"""
		A method for adding a tool to the toolbar
		"""
		self.AddSimpleTool(wid, bitmap, shortHelp, longHelp, (kind == wx.ITEM_CHECK))
		
	def AddSeparator(self):
		"""
		A method for adding a separator to the toolbar
		"""
		sep = wx.Panel(self, -1, size = (2, 32), style = wx.SUNKEN_BORDER)
		#self.sizer.Add(sep, (self.y,self.x))
		self.x += 1
		self.ctrls.append(sep)
		self.idToTool[sep.GetId()] = sep
		self.sizes.append(sep.GetSize()[0])

	def GetToolSeparation(self):
		"""
		Return the width between tools
		"""
		return self.toolSeparation
		
	def GetToolSize(self):
		"""
		Return the size of a toolbar item
		"""
		return self.toolSize
		
	def SetToolBitmapSize(self, size):
		"""
		Set the bitmap size of the toolbar
		"""
		self.toolSize = size
