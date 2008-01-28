# -*- coding: iso-8859-1 -*-
"""
 Unit: ChannelListBox
 Project: BioImageXD
 Created: 26.07.2005, KP
 Description:

 A HTML listbox that shows information about each dataset and allows
 the user to select one.

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
__author__ = "BioImageXD Project <http://www.bioimagexd.org>"
__version__ = "$Revision: 1.21 $"
__date__ = "$Date: 2005/01/13 14:36:20 $"

#import os.path

import wx
import lib.messenger
import MenuManager

class CommandHistory(wx.Frame):
	"""
	Class: CommandHistory
	Created: 13.02.2006, KP
	Description: A class for viewing the command history
	""" 
	def __init__(self, parent, mgr):
		self.parent = parent
		wx.Frame.__init__(self, parent, -1, "Command history", size = (300, 400))
		self.sizer = wx.GridBagSizer()
		
		self.menuManager = mgr
		
		self.undobox = UndoListBox(self, mgr, size = (300, 300))
		self.update = self.undobox.update
		
		self.doBtn = wx.Button(self, -1, "Run")
		self.undoBtn = wx.Button(self, -1, "Undo")
		
		self.doBtn.Bind(wx.EVT_BUTTON, self.onRunCommand)
		self.undoBtn.Bind(wx.EVT_BUTTON, self.onUndoCommand)
		
		
		self.btnSizer = wx.BoxSizer(wx.HORIZONTAL)
		self.btnSizer.Add(self.doBtn)
		self.btnSizer.Add(self.undoBtn)
		
		self.sizer.Add(self.undobox, (0, 0))
		self.sizer.Add(self.btnSizer, (1, 0))
		
		self.SetSizer(self.sizer)
		self.SetAutoLayout(1)
		self.sizer.Fit(self)
		
	def onRunCommand(self, evt):
		"""
		Method: onRunCommand
		Run the selected command
		"""            
		cmd = self.undobox.getCommand()
		self.menuManager.enable(MenuManager.ID_REDO)
		self.menuManager.disable(MenuManager.ID_REDO)        
		print "cmd=", cmd
		if cmd:
			print "running..."
			cmd.run()
			self.undobox.Update()
		
	def onUndoCommand(self, evt):
		"""
		Method: onRunCommand
		Undo the selected command
		"""            
		cmd = self.undobox.getCommand()
		if cmd:
			cmd.undo()
			self.menuManager.setUndoedCommand(cmd)
			self.menuManager.enable(MenuManager.ID_REDO)
			self.menuManager.disable(MenuManager.ID_UNDO)
		
	def enableUndo(self, flag):
		"""
		Method: enableUndo(flag)
		Enable / Disable the undo button
		"""    
		self.undoBtn.Enable(flag)
		
class UndoListBox(wx.HtmlListBox):
	def __init__(self, parent, mgr, **kws):
		"""
		Method: __init__(parent,kws)
		Initialization
		"""
		self.parent = parent
		wx.HtmlListBox.__init__(self, parent, -1, **kws)
		self.Bind(wx.EVT_LISTBOX, self.onSelectItem)
		self.dataUnit = None
		self.menuManager = mgr
		self.previews = {}
		self.SetItemCount(0)
		self.units = []
		self.selectedCmd = None
		lib.messenger.connect(None, "execute_command", self.update)
		
	def getCommand(self):
		"""
		Method: getCommand
		Return the selected command
		"""        
		return self.selectedCmd
		
	def update(self, *args):
		"""
		Method: upate
		Update the item count of this listbox
		"""    
		self.commands = self.menuManager.getCommands()
		self.SetItemCount(len(self.commands))
		
	def onSelectItem(self, event):
		"""
		Method: onSelectItem
		Callback called when a user selects a channel in this listbox
		"""
		item = self.GetSelection()
		command = self.commands[item]
		self.selectedCmd = command
		flag = command.canUndo()
		self.parent.enableUndo(flag)
		
		
	def OnGetItem(self, n):
		"""
		Method: OnGetItem
		Return the HTML code for given item
		"""      
		
		if len(self.commands) < n:
			return ""
		cmd = self.commands[n]
		desc = cmd.getDesc()
		category = cmd.getCategory()
		color = "#000000"
		if cmd.isUndoed():
			color = "#ff0000"
		
		return """<table>
<tr><td valign="top">
<td valign="top"><font color="%s"><b>%s</font></b><br>
<font color="#808080">%s</font></td></tr>
</table>
""" % (color, category, desc)
