#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: MenuManager
 Project: BioImageXD
 Created: 29.05.2005, KP
 Description:

 A module for managing the menus

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
__version__ = "$Revision: 1.71 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import wx

# We preface all ids with 31 so they won't overlap with ids returned by wx.NewId() 
ID_OPEN					= 31100
ID_QUIT					= 31101
ID_ABOUT				= 31102
ID_COLOCALIZATION		= 31103
ID_COLORMERGING			= 31104
ID_VSIA					= 31105
ID_ADJUST				= 31106
ID_VIS_ANIMATOR			= 31107
ID_REEDIT				= 31108
ID_TREE					= 31109
ID_IMPORT				= 31110
ID_EXPORT				= 31111
ID_EXPORT_VTIFILES		= 31112
ID_EXPORT_IMAGES		= 31113
ID_IMPORT_VTIFILES		= 31114
ID_IMPORT_IMAGES		= 31115
ID_HELP					= 31116
ID_SETTINGS				= 31117
ID_PREFERENCES			= 31118
ID_RESLICE				= 31119
ID_MAYAVI				= 31120
ID_VIS_SECTIONS			= 31121
ID_VIS_SLICES			= 31122
ID_VIS_3D				= 31123
ID_INFO					= 31124
ID_SHOW_TREE			= 31125
ID_VIS_GALLERY			= 31126
ID_LIGHTS				= 31127
ID_RENDERWIN			= 31128
ID_RELOAD				= 31129

ID_TREE_WIN				= 31130
ID_VIS_WIN				= 31131
ID_TASK_WIN				= 31132
ID_OPEN_SETTINGS		= 31133
ID_SAVE_SETTINGS		= 31134

ID_RESTORE				= 31135
ID_SAVE_SNAPSHOT		= 31136

ID_CAPTURE				= 31137
ID_ZOOM_OUT				= 31138
ID_ZOOM_IN				= 31139
ID_ZOOM_TO_FIT			= 31140
ID_ZOOM_OBJECT			= 31141

ID_PREFERENCES			= 31142
ID_ADD_SPLINE			= 31143
ID_ADD_TIMEPOINT		= 31144
ID_ADD_TRACK			= 31145
ID_ANIMATE				= 31146
ID_FIT_TRACK			= 31147
ID_MIN_TRACK			= 31148
ID_OPEN_PROJECT			= 31149
ID_RENDER_PROJECT		= 31150
ID_RENDER_PREVIEW		= 31151
ID_SAVE_PROJECT			= 31152
ID_SET_TRACK			= 31153
ID_SPLINE_CLOSED		= 31154
ID_SPLINE_SET_BEGIN		= 31155
ID_SPLINE_SET_END		= 31156
ID_SET_TRACK_TOTAL		= 31157
ID_CLOSE_PROJECT		= 31158
ID_MAINTAIN_UP			= 31159
ID_SET_TRACK_RELATIVE	= 31160
ID_ADD_SCALE			= 31161
ID_DRAG_ANNOTATION		= 31162
ID_ROI_CIRCLE			= 31163
ID_ROI_RECTANGLE		= 31164
ID_ROI_POLYGON			= 31165

ID_VIEW_CONFIG			= 31166
ID_VIEW_TASKPANEL		= 31167
ID_VIEW_TOOLBAR			= 31168
ID_VIEW_HISTOGRAM		= 31169
ID_CLOSE_TASKWIN		= 31170

ID_DELETE_TRACK			= 31171
ID_VIS_SIMPLE			= 31172

ID_SET_VIEW				= 31173
ID_VIEW_TOOL_NAMES		= 31174

ID_VIEW_SHELL			= 31175
ID_SHELL_WIN			= 31176
ID_INFO_WIN				= 31177
ID_VIEW_INFO			= 31178
ID_LOAD_SCENE			= 31179
ID_SAVE_SCENE			= 31180
ID_SEPARATOR			= 31181

ID_TOOL_WIN				= 31182
ID_VISAREA_WIN			= 31183
ID_VISTREE_WIN			= 31184
ID_VISSLIDER_WIN		= 31185
ID_ZSLIDER_WIN			= 31186
ID_HISTOGRAM_WIN		= 31187

ID_DEL_ANNOTATION		= 31188

ID_ADD_KEYFRAME			= 31189
ID_RESAMPLE				= 31190
ID_TOOL_WIN2			= 31191
ID_ZOOM_COMBO			= 31192
ORIG_BUTTON				= 31193
CONTEXT_HELP			= 31194

PITCH					= 31195
YAW						= 31196
ROLL					= 31197

ID_HIDE_INFO			= 31198
ID_ANIM_ZOOM_COMBO		= 31131
ID_ITEM_SIZES			= 31200
ID_ITEM_ORDER			= 31201
ID_ITEM_ROTATE_CW		= 31202
ID_ITEM_ROTATE_CCW		= 31203
ID_FIT_TRACK_RATIO		= 31204
ID_DELETE_ITEM			= 31205

ID_VIEW_SCRIPTEDIT		= 31206
ID_RECORD_SCRIPT		= 31207
ID_STOP_RECORD			= 31208
ID_RUN_SCRIPT			= 31209

ID_UNDO					= 31210
ID_REDO					= 31211
ID_COMMAND_HISTORY		= 31212

ID_SAVE_SCRIPT			= 31213
ID_LOAD_SCRIPT			= 31214
ID_CLOSE_SCRIPTEDITOR	= 31215

ID_IMMEDIATE_RENDER		= 31216

ID_MANIPULATE			= 31217
ID_SAVE_DATASET			= 31218

ID_VIEW_MASKSEL			= 31219
ID_ROI_TO_MASK			= 31220
ID_RESCALE				= 31221
ID_RESAMPLING			= 31222

ID_ANNOTATION_WIN		= 31223
ID_ANNOTATION_FONT		= 31224
ID_ANNOTATION_TEXT		= 31225

ID_VIEW_TREE			= 31226

ID_NO_RENDER			= 31227

ID_TOOLBAR_HELP			= 31228
ID_CONTEXT_HELP			= 31229

ID_PERSPECTIVE			= 31230
ID_RESAMPLE_TO_FIT		= 31231

ID_RECORD_EVENTS		= 31232
ID_PLAY_EVENTS			= 31233
ID_STOP_EVENTS			= 31234
ID_REWIND_EVENTS		= 31235

ID_REPORT_BUG			= 31236

ID_BATCHPROCESSOR		= 31237

ID_LOAD_ANALYSIS		= 31238
ID_SAVE_ANALYSIS		= 31239

ID_CLOSE_BATCHPROCESSOR	= 31240
ID_CLOSE_ALL            = 31241
ID_FILE_VIEW_TREE       = 31242

ID_MENU_ROI_CIRCLE      = 31243
ID_MENU_ROI_RECTANGLE   = 31244
ID_MENU_ROI_POLYGON     = 31245
ID_MENU_ADD_SCALE       = 31246
ID_MENU_DEL_ANNOTATION  = 31247
ID_MENU_CHANGE_COLOR    = 31248
ID_MENU_ROI_TO_MASK     = 31249

ID_SELECT_ALL           = 31250
ID_VIEW_ANNOPANEL       = 31251
ID_VIEW_MAIN_TOOLBAR    = 31252
ID_MAIN_TOOLBAR         = 31253
ID_MENU_RESAMPLING      = 31254

ID_ROI_THREE_D_POLYGON	    = 31255
ID_ROI_THREE_D_CIRCLE	    = 31256
ID_ROI_THREE_D_RECTANGLE    = 31257

class MenuManager:
	"""
	Created: 29.05.2005, KP
	Description: A class for managing the menu
	"""
	instance = None
	mainwin = None
	mapping = {}

	def __init__(self, mainwin, **kws):
		"""
		Method: __init__(parent,id,app)
		Initialization
		"""
		self.text = 1
		self.separators = {}
		if kws.has_key("text"):
			self.text = kws["text"]
		self.mainwin = mainwin
		# This is the menubar object that holds all the menus
		self.mapping = {}
		self.menus = {}
		self.visualizer = None
		self.itemBar = None
		self.mainToolbar = None
		self.toolIds = []
		self.tools = {}
		self.channelIds = []
		self.commands = []
		self.showToolNames = 0
		
	def getCommands(self):
		"""
		Return the list of commands
		"""
		return self.commands
				
	def addCommand(self, cmd):
		"""
		Method: addCommand
		Add a command to the list of executed commands
		"""
		if cmd not in self.commands:
			self.commands.append(cmd)
		
	def getLastCommand(self):
		"""
		Method: getLastCommand
		Return the last executed command
		"""
		if (len(self.commands) == 0): 		#	There is nothing to undo
			return False					#   Thus return False
		return self.commands[-1]
			
	def setUndoedCommand(self, cmd):
		"""
		Method: setUndoedCommand
		Set the last command that was undoed
		"""
		self.undoCmd = cmd
	
	def getUndoedCommand(self):
		"""
		Method: getUndoedCommand
		Return the last undoed command
		"""
		return self.undoCmd
		
		
	def setMenuBar(self, menubar):
		"""
		Method: setMenuBar
		Set the menubar
		"""
		self.menubar = menubar

	def setMainToolbar(self, bar):
		"""
		Method: setMenuBar
		Set the menubar
		"""
		self.mainToolbar = bar

	def removeSeparator(self, sepid):
		"""
		Method: removeSeparator
		delete a separator
		"""
		menu = self.menus[self.mapping[sepid]]
		menu.RemoveItem(self.separators[sepid])
		
	def addSeparator(self, menuname, sepid = None, before = None):
		"""
		Method: addSeparator(menuname)
		add a separator
		"""
		if not before:
			if not sepid:
				self.menus[menuname].AppendSeparator()
			else:
				
				item = wx.MenuItem(self.menus[menuname], wx.ID_SEPARATOR, kind = wx.ITEM_SEPARATOR)
				self.separators[sepid] = item
				self.menus[menuname].Append(item)
				self.mapping[sepid] = menuname
		else:
			menu = self.menus[menuname]
			# Find the position where the item belongs
			k = 0
			for i in range(0, 319):
				if menu.FindItemByPosition(i).GetId() == before:
					k = i
					break
			if not sepid:
				menu.InsertSeparator(k)
			else:
				item = wx.MenuItem(self.menus[menuname], wx.ID_SEPARATOR, kind = wx.ITEM_SEPARATOR)
				self.separators[sepid] = item
				
				self.menus[menuname].InsertItem(k, item)
				self.mapping[sepid] = menuname

	def check(self, itemid, flag):
		"""
		Check / uncheck a menu item
		"""
		menu = self.mapping[itemid]
		self.menus[menu].Check(itemid, flag)
		
	def isChecked(self, itemid):
		"""
		Method: isChecked(itemid)
		Return whether an item is checked
		"""
		menu = self.mapping[itemid]
		self.menus[menu].IsChecked(itemid)
		
	def addSubMenu(self, menuname, submenuname, title, menuid):
		"""
		Method: addSubMenu(menuname,submenuname,title,menuid)
		make a menu a submenu of another
		"""
		self.menus[menuname].AppendMenu(menuid, title, self.menus[submenuname])
		
	def createMenu(self, menuname, menutitle, place = 1, before = None):
		"""
		Create a menu with a given id and title
		"""
		ret = self.menus[menuname] = wx.Menu()
		if not place:
			return
		if not before:
			self.menubar.Append(self.menus[menuname], menutitle)
		else:
			menu = self.menus[before]
			print "Searching for menu ", menu, menu.GetTitle()
			for i in range(0, self.menubar.GetMenuCount()):
				gmenu = self.menubar.GetMenu(i)
				if gmenu == menu:
					pos = i
					break
			#pos= self.menubar.FindMenu(menu.GetTitle())
			
			self.menubar.Insert(pos, self.menus[menuname], menutitle)
		return ret
			
	def setVisualizer(self, visualizer):
		"""
		Set the visualizer instance managed by this class
		"""
		self.visualizer = visualizer
		
	def clearItemsBar(self):
		"""
		Clear items bar
		"""
		self.visualizer.annotateToolbar.clearChannelItems()
		#if not self.itemBar:return
		#for i in self.toolIds:
		#	self.itemBar.DeleteTool(i)
		#self.toolIds=[]
		#self.itemBar.Realize()
		

	def addChannelItem(self, name, bitmap, toolid, func):
		"""
		Add a toolbar item
		"""
		self.channelIds.append(toolid)

		#self.itemBar= self.visualizer.tb
		#self.visualizer.tb.Bind(wx.EVT_TOOL,func,id=toolid)
	
		#self.tools[toolid]=(name,bitmap,func)
		#self.itemBar.DoAddTool(toolid,name,bitmap,kind=wx.ITEM_CHECK)
		
		#self.itemBar.Realize()
		self.visualizer.annotateToolbar.addChannelItem(name, bitmap, toolid, func)
		
	
	def toggleTool(self, toolid, flag):
		"""
		Toggle a toolbar item
		"""
		if toolid in self.channelIds:
			self.visualizer.annotateToolbar.toggleChannelItem(toolid, flag)
			return
		self.visualizer.tb.ToggleTool(toolid, flag)

	def addMenuItem(self, menu, menuid, name, hlp = None, callback = None, \
					before = None, check = 0, checked = 1):
		"""
		Method: addMenuItem
		Add a menu item
		"""
		if not callback:
			if hlp and type(hlp) != type(""):
				callback = hlp
				hlp = None
		self.mapping[menuid] = menu
		menu = self.menus[menu]
		if check:
			method = menu.AppendCheckItem
		else:
			method = menu.Append
		if not before:
			if not hlp:
				method(menuid, name)            # Find the position where the item belongs
			else:
				method(menuid, name, hlp)
		else:
			if check:
				method = menu.Insert
			else:
				method = menu.InsertCheckItem
			# Find the position where the item belongs
			k = 0
			for i in range(0, 999):
				if menu.FindItemByPosition(i).GetId() == before:
					k = i
					break
			if not hlp:
				menu.Insert(k, menuid, name)
			else:
				menu.Insert(k, menuid, name, hlp)
			
			
		if callback:
			wx.EVT_MENU(self.mainwin, menuid, callback)
		if check and checked:
			self.check(menuid, 1)

	def disable(self, itemid):
		"""
		Disable a menu item
		"""
		self.menus[self.mapping[itemid]].Enable(itemid, 0)
		
	def enable(self, itemid, callback = None):
		"""
		Enable a menu item
		"""
		self.menus[self.mapping[itemid]].Enable(itemid, 1)
		if callback:
			wx.EVT_MENU(self.mainwin, itemid, callback)
			
	def removeMenu(self, menuname):
		"""
		Method: removeMenu(menuname)
		Remove a menu
		"""
		title = self.menus[menuname].GetTitle()
		for i in range(self.menubar.GetMenuCount()):
			menu = self.menubar.GetMenu(i)
			if menu.GetTitle() == title:
				self.menubar.Remove(i)
				break
		
	def remove(self, itemid):
		"""
		Method: remove(itemid)
		Remove a menu item
		"""
		menu = self.menus[self.mapping[itemid]]
		menu.Delete(itemid)
		self.mapping[itemid] = None
