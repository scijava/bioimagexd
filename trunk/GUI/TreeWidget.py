# -*- coding: iso-8859-1 -*-
"""
 Unit: TreeWidget
 Project: BioImageXD
 Description:

 A widget for displaying a hierarchical tree of datasets

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
__version__ = "$Revision: 1.21 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import wx
import Logging
import types
import lib.messenger
import platform
import Configuration
import Modules.DynamicLoader

class OrderedDict(dict):
	def __init__(self):
		dict.__init__(self)
		self._keyList = []
		
	def __setitem__(self, key, value):
		if key not in self._keyList:
			self._keyList.append(key)
		return dict.__setitem__(self, key, value)
		
	def items(self):
		return [(x, self[x]) for x in self._keyList]
	def keys(self):
		return self._keyList

class TreeWidget(wx.SashLayoutWindow):
	"""
	A panel containing the tree
	"""
	def __init__(self, parent):
		"""
		Initialization
		"""        
		wx.SashLayoutWindow.__init__(self, parent, -1)
		self.treeId = wx.NewId()
		self.parent = parent
		self.tree = wx.TreeCtrl(self, self.treeId, style = wx.TR_HAS_BUTTONS | wx.TR_MULTIPLE)
		self.multiSelect = 0
		self.programmatic = 0
		self.lastobj = None
		self.ignore = 0
		self.tree.Bind(wx.EVT_TREE_SEL_CHANGED, self.onSelectionChanged, id = self.tree.GetId())    
		self.tree.Bind(wx.EVT_TREE_SEL_CHANGING, self.onSelectionChanging, id = self.tree.GetId())
		self.tree.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.onActivateItem, id = self.tree.GetId())
		self.tree.Bind(wx.EVT_KEY_DOWN, self.onKeyDown, id = self.tree.GetId())
		self.items = OrderedDict()
		self.greenitems = []
		self.yellowitems = []
		self.dataUnitToPath = {}
		self.selectedItem = None
		
		isz = (16, 16)
		il = wx.ImageList(isz[0], isz[1])
		fldridx     = il.Add(wx.ArtProvider_GetBitmap(wx.ART_FOLDER,      wx.ART_OTHER, isz))
		fldropenidx = il.Add(wx.ArtProvider_GetBitmap(wx.ART_FILE_OPEN,   wx.ART_OTHER, isz))
		fileidx     = il.Add(wx.ArtProvider_GetBitmap(wx.ART_REPORT_VIEW, wx.ART_OTHER, isz))
		
		self.tree.SetImageList(il)
		self.il = il
	
		self.root = self.tree.AddRoot("Datasets")
		self.tree.SetPyData(self.root, "1")
		self.tree.SetItemImage(self.root, fldridx, which = wx.TreeItemIcon_Normal)
		self.tree.SetItemImage(self.root, fldropenidx, which = wx.TreeItemIcon_Expanded)

		self.lsmfiles = None
		self.leicafiles = None
		self.bxdfiles = None
		self.oiffiles = None
		self.bioradfiles = None
		self.interfilefiles = None
		self.liffiles = None
		self.mrcfiles = None
		self.lastSelection = None
		
		self.dataUnitItems = []
		self.groupedDataUnit = None
		self.groupedItems = []
		self.removeParents = []
		
		self.itemColor = (0, 0, 0)
		
		
		self.tree.Bind(wx.EVT_RIGHT_DOWN, self.onRightClick)
		self.Bind(wx.EVT_RIGHT_DOWN, self.onRightClick)
		self.ID_CLOSE_DATAUNIT = wx.NewId()
		self.ID_GROUP_DATAUNIT = wx.NewId()
		self.ID_UNGROUP = wx.NewId()
		self.menu = wx.Menu()
		self.tree.SetHelpText("Files that you open appear in this tree.")        
	   
		item = wx.MenuItem(self.menu, self.ID_CLOSE_DATAUNIT, "Close dataset")
		self.tree.Bind(wx.EVT_MENU, self.onCloseDataset, id = self.ID_CLOSE_DATAUNIT)
		self.Bind(wx.EVT_MENU, self.onCloseDataset, id = self.ID_CLOSE_DATAUNIT)
		self.menu.AppendItem(item)
		item = wx.MenuItem(self.menu, self.ID_GROUP_DATAUNIT, "Group dataset")
		self.tree.Bind(wx.EVT_MENU, self.onCloseDataset, id = self.ID_GROUP_DATAUNIT)
		self.Bind(wx.EVT_MENU, self.onGroupDataset, id = self.ID_GROUP_DATAUNIT)
		self.menu.AppendItem(item)
		item = wx.MenuItem(self.menu, self.ID_UNGROUP, "Ungroup")
		self.tree.Bind(wx.EVT_MENU, self.onUngroup, id = self.ID_UNGROUP)
		self.Bind(wx.EVT_MENU, self.onUngroup, id = self.ID_UNGROUP)
		self.menu.AppendItem(item)
		
	def onUngroup(self, evt):
		"""
		Ungroup all dataunits
		"""
		self.groupedDataUnit = None
		self.unmarkItems(self.groupedItems, "}")
		self.groupedItems = []

	def onGroupDataset(self, event):
		"""
		Add the selected dataunit into a grouping
		"""
		selections = self.tree.GetSelections()
		if not selections and self.selectedItem:
			selections = [self.selectedItem]
		if not self.groupedDataUnit:
			pluginLoader = Modules.DynamicLoader.getPluginLoader()
			taskMod = pluginLoader.getPluginModule("Task", "Process")
			unitType = taskMod.getDataUnit()
			moduleType = pluginLoader.getPluginClass("Task","Process")
			self.groupedDataUnit = unitType()
			module = moduleType()
			self.groupedDataUnit.setModule(module)
		
		for item in selections:
			if item in self.groupedItems: continue
			self.groupedItems.append(item)
			self.markBlue([item], "}")
			obj = self.tree.GetPyData(item)
			print "Adding source dataunit",obj
			self.groupedDataUnit.addSourceDataUnit(obj)
		setting = self.groupedDataUnit.getSettings()
		setting.set("FilterList",[])
		
		print "Now=",self.groupedDataUnit.getSourceDataUnits()
			
	def onRightClick(self, event):
		"""
		Method that is called when the right mouse button is
					 pressed down on this item
		"""      
		pt = event.GetPosition()
		item, flags = self.tree.HitTest(pt)
		if not item:
			Logging.info("No item to select", kw = "ui")
			return
		self.tree.SelectItem(item)
		self.selectedItem = item
		self.PopupMenu(self.menu, event.GetPosition())   
 
	def closeItem(self, item, obj):
		"""
		close on item from the tree
		"""
		unit = self.dataUnitToPath[obj]
		self.items[unit] -= 1
		
		if obj in self.dataUnitToPath:
			del self.dataUnitToPath[obj]

		if self.items[unit] <= 0:
			conf = Configuration.getConfiguration()
			lst = self.items.keys()
			lst.remove(unit)
			conf.setConfigItem("FileList", "General", lst)
			conf.writeSettings()
			del self.items[unit]
			parent = self.tree.GetItemParent(item)
			#self.tree.Delete(parent)
			if parent not in self.removeParents:
				self.removeParents.append(parent)
			wx.CallAfter(self.removeEmptyParents)

		lib.messenger.send(None, "delete_dataset", obj)
		obj.destroySelf()   
		del obj 
		
	def removeEmptyParents(self):
		"""
		remove empty parent items from the tree after their children have been removed
		"""
		removeParents = []
		for i in self.removeParents:
			# Remove pointer to item in this class if item is directory of some
			# kind of file type
			if i == self.lsmfiles:
				self.lsmfiles = None
			elif i == self.leicafiles:
				self.leicafiles = None
			elif i == self.bxdfiles:
				self.bxdfiles = None
			elif i == self.oiffiles:
				self.oiffiles = None
			elif i == self.bioradfiles:
				self.bioradfiles = None
			elif i == self.interfilefiles:
				self.interfilefiles = None
			elif i == self.liffiles:
				self.liffiles = None
			elif i == self.mrcfiles:
				self.mrcfiles = None

			parent = self.tree.GetItemParent(i)
			self.tree.Delete(i)
			if parent and parent not in removeParents and self.tree.GetChildrenCount(parent) <= 0 and parent != self.tree.GetRootItem():
				removeParents.append(parent)
		if removeParents:
			self.removeParents = removeParents
			wx.CallAfter(self.removeEmptyParents)
		else:
			self.removeParents = []
					
	def onCloseDataset(self, event):
		"""
		Method to close a dataset
		"""
		selections = self.tree.GetSelections()
		if not selections and self.selectedItem:
			selections = [self.selectedItem]
		for item in self.tree.GetSelections():
			obj = self.tree.GetPyData(item)
			print "OnCloseItem",obj
				
			if obj in self.dataUnitToPath:
				self.closeItem(item, obj)
			elif obj == "2":
				citem, cookie = self.tree.GetFirstChild(item)
				while citem.IsOk():
					nitem = self.tree.GetNextSibling(citem)
					cobj = self.tree.GetPyData(citem)
					self.closeItem(citem, cobj)
					citem = nitem
					del cobj					
				
			if obj != "1":
				lib.messenger.send(None, "delete_dataset", obj)
				self.tree.Delete(item)
				del obj
			else:
				Logging.info("Cannot delete top-level entry", kw = "ui")
			
	def onSize(self, event):
		"""
		Callback that modifies the tree size according to
					 own changes in size
		"""                
		w, h = self.GetClientSizeTuple()
		self.tree.SetDimensions(0, 0, w, h)
		
	def getSelectionContainer(self):
		"""
		Return the dataset that contains a channel
		"""         
		selections = self.tree.GetSelections()
		dataunits = []
		items = []
		for i in selections:
			parent = self.tree.GetItemParent(i)
			data = self.tree.GetPyData(parent)
			if data == "2":
				item, cookie = self.tree.GetFirstChild(parent)
			else:
				item, cookie = self.tree.GetFirstChild(parent)
			while item.IsOk():
				data = self.tree.GetPyData(item)
				if data not in dataunits:
					dataunits.append(data)
					items.append(item)
				item = self.tree.GetNextSibling(item)
		
		return dataunits, items
		
		
	def markGreen(self, items):
		"""
		Mark given items green and set the old green item to default color
		"""                    
		if self.greenitems:
			for item in self.greenitems:
				self.tree.SetItemBold(item, 0)
			pass
		self.greenitems = items    
		for item in items:
			self.tree.SetItemBold(item, 1)
			
	def markYellow(self, items):
		"""
		Mark given items yellow and set the old yellow item to default color
		"""        
		if self.yellowitems:
			for item in self.yellowitems:
				self.tree.SetItemBackgroundColour(item, (255, 255, 255))
			pass
		self.yellowitems = items    
		for item in items:
			#self.itemColor=self.tree.GetItemTextColour(item)
			self.tree.SetItemBackgroundColour(item, (255, 255, 0))    
		
	def markRed(self, items, appendchar = ""):
		"""
		Mark given items red
		"""                
		for item in items:
			if appendchar != "":
				txt = self.tree.GetItemText(item)
				if txt[-len(appendchar):] != appendchar:
					self.tree.SetItemText(item, txt + appendchar)
			self.tree.SetItemTextColour(item, (255, 0, 0))
			
	def unmarkItems(self, items, appendchar = ""):	
		"""
		Unmark the given items
		"""
		for item in items:
			if appendchar != "":
				txt = self.tree.GetItemText(item)
				if txt[-len(appendchar):] == appendchar:
					newtext = txt[:-len(appendchar)]
					self.tree.SetItemText(item, newtext)
			self.tree.SetItemTextColour(item, self.itemColor)
			
	def markBlue(self, items, appendchar = ""):
		"""
		Mark given items blue
		"""                
		for item in items:
			if appendchar != "":
				txt = self.tree.GetItemText(item)
				if txt[-len(appendchar):] != appendchar:
					self.tree.SetItemText(item, txt + appendchar)
			self.tree.SetItemTextColour(item, (0, 0, 255))

		
	def hasItem(self, path):
		"""
		Returns whether the tree has a specified item
		"""            
		return (path in self.items and self.items[path])
		
	def getItemNames(self):
		"""
		Return the names of the dataunits in the tree
		"""
		return self.items.keys()
	
	def addToTree(self, name, path, objtype, objs):
		"""
		Add item to the tree
		Parameters:
			name        Name of the item
			path        Path of the item
			objtype     Type of the object (lsm, bxd)
			objs        objects to add
		"""
		item = None
		imageSize = (16, 16)
		il = wx.ImageList(imageSize[0], imageSize[1])
		folderIndex = il.Add(wx.ArtProvider_GetBitmap(wx.ART_FOLDER, wx.ART_OTHER, imageSize))
		folderOpenIndex = il.Add(wx.ArtProvider_GetBitmap(wx.ART_FILE_OPEN, wx.ART_OTHER, imageSize))
		fileIndex = il.Add(wx.ArtProvider_GetBitmap(wx.ART_REPORT_VIEW, wx.ART_OTHER, imageSize))

		if objtype in ["lif", "lei", "txt"]:
			path = path + name
		
		for i in range(0, len(objs)):
			if not path in self.items:
				self.items[path] = 1
			else:
				self.items[path] += 1
		
		for i in objs:
			self.dataUnitToPath[i] = path

		if objtype == "lsm":
			if not self.lsmfiles:
				self.lsmfiles = self.tree.AppendItem(self.root, "LSM files")
				self.tree.SetPyData(self.lsmfiles, "1")
				self.tree.SetItemImage(self.lsmfiles, folderIndex, which = wx.TreeItemIcon_Normal)
				self.tree.SetItemImage(self.lsmfiles, folderOpenIndex, which = wx.TreeItemIcon_Expanded)
			item = self.lsmfiles
			self.tree.Expand(item)
			item = self.tree.AppendItem(item, name)
			self.tree.Expand(item)
			self.tree.SetPyData(item, "2")        
			self.tree.SetItemImage(item, folderOpenIndex, which = wx.TreeItemIcon_Expanded)
		
		elif objtype in ["txt","lei"]:
			if not self.leicafiles:
				self.leicafiles = self.tree.AppendItem(self.root, "Leica files")
				self.tree.SetPyData(self.leicafiles, "1")
				self.tree.SetItemImage(self.leicafiles, folderIndex, which = wx.TreeItemIcon_Normal)
				self.tree.SetItemImage(self.leicafiles, folderOpenIndex, which = wx.TreeItemIcon_Expanded)        

			item = self.leicafiles
			self.tree.Expand(item)
			item = self.tree.AppendItem(item, name)
			self.tree.Expand(item)
			
			self.tree.SetPyData(item, "2")
			self.tree.SetItemImage(item, folderOpenIndex, which = wx.TreeItemIcon_Expanded)
			
		elif objtype == "oif":
			if not self.oiffiles:
				self.oiffiles = self.tree.AppendItem(self.root, "Olympus files")
				self.tree.SetPyData(self.oiffiles, "1")
				self.tree.SetItemImage(self.oiffiles, folderIndex, which = wx.TreeItemIcon_Normal)
				self.tree.SetItemImage(self.oiffiles, folderOpenIndex, which = wx.TreeItemIcon_Expanded)
			item = self.oiffiles
			self.tree.Expand(item)
			item = self.tree.AppendItem(item, name)
			self.tree.Expand(item)
			self.tree.SetPyData(item, "2")
			self.tree.SetItemImage(item, folderOpenIndex, which = wx.TreeItemIcon_Expanded)
			
		elif objtype == "pic":
			if not self.bioradfiles:
				self.bioradfiles = self.tree.AppendItem(self.root, "BioRad files")
				self.tree.SetPyData(self.bioradfiles, "1")
				self.tree.SetItemImage(self.bioradfiles, folderIndex, which = wx.TreeItemIcon_Normal)
				self.tree.SetItemImage(self.bioradfiles, folderOpenIndex, which = wx.TreeItemIcon_Expanded)
			item = self.bioradfiles
			self.tree.Expand(item)
		
		elif objtype == "hdr":
			if not self.interfilefiles:
				self.interfilefiles = self.tree.AppendItem(self.root, "Interfile files")
				self.tree.SetPyData(self.interfilefiles, "1")
				self.tree.SetItemImage(self.interfilefiles, folderIndex, which = wx.TreeItemIcon_Normal)
				self.tree.SetItemImage(self.interfilefiles, folderOpenIndex, which = wx.TreeItemIcon_Expanded)
			item = self.interfilefiles
			self.tree.Expand(item)
			
		elif objtype == "bxd":
			if not self.bxdfiles:
				self.bxdfiles = self.tree.AppendItem(self.root, "BioImageXD files")
				self.tree.SetPyData(self.bxdfiles, "1")        
				self.tree.SetItemImage(self.bxdfiles, folderIndex, which = wx.TreeItemIcon_Normal)
				self.tree.SetItemImage(self.bxdfiles, folderOpenIndex, which = wx.TreeItemIcon_Expanded)

			item = self.bxdfiles
			self.tree.Expand(item)            
			item = self.tree.AppendItem(item, name)
			self.tree.Expand(item)

			self.tree.SetPyData(item, "2")        
			self.tree.SetItemImage(item, folderOpenIndex, which = wx.TreeItemIcon_Expanded)

		elif objtype == "bxc":
			if not self.bxdfiles:
				self.bxdfiles = self.tree.AppendItem(self.root, "BioImageXD files")
				self.tree.SetPyData(self.bxdfiles, "1")        
				self.tree.SetItemImage(self.bxdfiles, folderIndex, which = wx.TreeItemIcon_Normal)
				self.tree.SetItemImage(self.bxdfiles, folderOpenIndex, which = wx.TreeItemIcon_Expanded)

			item = self.bxdfiles
			self.tree.Expand(item)
			
		elif objtype == "lif":
			if not self.liffiles:
				self.liffiles = self.tree.AppendItem(self.root, "LIF files")
				self.tree.SetPyData(self.liffiles, "1")
				self.tree.SetItemImage(self.liffiles, folderIndex, which = wx.TreeItemIcon_Normal)
				self.tree.SetItemImage(self.liffiles, folderOpenIndex, which = wx.TreeItemIcon_Expanded)

			item = self.liffiles
			self.tree.Expand(item)
			item = self.tree.AppendItem(item, name)
			self.tree.Expand(item)
			self.tree.SetPyData(item, "2")
			self.tree.SetItemImage(item, folderOpenIndex, which = wx.TreeItemIcon_Expanded)
			
		elif objtype in ["mrc","st"]:
			if not self.mrcfiles:
				self.mrcfiles = self.tree.AppendItem(self.root, "MRC files")
				self.tree.SetPyData(self.mrcfiles, "1")
				self.tree.SetItemImage(self.mrcfiles, folderIndex, which = wx.TreeItemIcon_Normal)
				self.tree.SetItemImage(self.mrcfiles, folderOpenIndex, which = wx.TreeItemIcon_Expanded)

			item = self.mrcfiles
			self.tree.Expand(item)
			item = self.tree.AppendItem(item, name)
			self.tree.Expand(item)
			self.tree.SetPyData(item, "2")
			self.tree.SetItemImage(item, folderOpenIndex, which = wx.TreeItemIcon_Expanded)

		self.tree.Expand(item)
		selected = 0
		for obj in objs:
			added = self.tree.AppendItem(item, obj.getName())
				
			resampledims = obj.dataSource.getResampleDimensions()
			if resampledims and resampledims != (0, 0, 0):
				self.markRed([added], "*")
			self.tree.SetPyData(added, obj)        
			self.tree.SetItemImage(added, fileIndex, which = wx.TreeItemIcon_Normal)
			#self.tree.SetItemImage(added,folderOpenIndex,which=wx.TreeItemIcon_Expanded)
			self.tree.EnsureVisible(added)
			self.dataUnitItems.append(added)
			
			if len(self.items.keys()) == 1 and not selected:
				self.tree.UnselectAll()
				self.tree.SelectItem(added, 1)
				selected = 1
				lib.messenger.send(None, "tree_selection_changed", obj)
			
		self.tree.Expand(self.root)
		conf = Configuration.getConfiguration()
		lst = self.items.keys()
		conf.setConfigItem("FileList", "General", lst)
		conf.writeSettings()

	def getSelectedDataUnits(self):
		"""
		Returns the selected dataunits
		"""
		if self.groupedDataUnit:
			return [self.groupedDataUnit]
		items = self.tree.GetSelections()
		objs = [self.tree.GetPyData(x) for x in items]
		objs = filter(lambda x:type(x) != types.StringType, objs)
		return objs
		
	def getSelectedPaths(self):
		"""
		Return the paths of the selected dataunits
		"""
		
		objs = self.getSelectedDataUnits()
		return [self.dataUnitToPath[x] for x in objs]
		

	def onActivateItem(self, event = None):
		"""
		A event handler called when user double clicks an item
		"""
		item = event.GetItem()
		if not item.IsOk():
			return
		obj = self.tree.GetPyData(item)
		if obj == "1":
			return
		self.item = item
		lib.messenger.send(None, "tree_selection_changed", obj)
		self.markGreen([item])
		
		event.Skip()
		
	def onSelectionChanging(self, event):
		"""
		An event handler called before the selection changes
		"""
		if self.ignore:
			event.Skip()
			return
		if not self.multiSelect and not self.programmatic:
		    if platform.system() not in ["Darwin", "Linux"]: 
			    self.tree.UnselectAll()
		item = event.GetItem()
		if not item.IsOk():
			Logging.info("Item %s is not ok" % str(item), kw = "io")
			return
				
		obj = self.tree.GetPyData(item)
		if obj == "1":
			#self.tree.UnselectItem(item)
			event.Veto()
			return
		elif obj == "2":
			# Select it's children
			self.ignore = 1
			self.tree.UnselectItem(item)
			citem, cookie = self.tree.GetFirstChild(item)
			while citem.IsOk():
				if not self.tree.IsSelected(citem):
					self.tree.ToggleItemSelection(citem)
				citem = self.tree.GetNextSibling(citem)                                
			event.Veto()
			self.ignore = 0
		
	def onKeyDown(self, event):
		"""
		Akey event handler
		"""
		keyevent = event
		if keyevent.ControlDown() or keyevent.ShiftDown():
			self.multiSelect = 1
		else:
			self.multiSelect = 0
		event.Skip()
		
	def onSelectionChanged(self, event = None):
		"""
		A event handler called when user selects an item.
		"""
		if self.ignore:
			event.Skip()
			return
		item = event.GetItem()
		self.lastSelection = item
		if not item.IsOk():
			return
		
		if item not in self.tree.GetSelections(): # Make selection work on 64-bit Win7
			self.tree.SelectItem(item)
		
		obj = self.tree.GetPyData(item)
		if obj == "1":
			return
		self.item = item
		if obj and type(obj) != types.StringType:
			if self.lastobj != obj:
				Logging.info("Switching to ", obj)
				lib.messenger.send(None, "clear_cache_dataunits")
				lib.messenger.send(None, "tree_selection_changed", obj)
				self.markGreen([item])
				self.lastobj = obj
		self.multiSelect = 0
		
	def unselectAll(self):
		"""
		Unselect everything in the tree
		"""
		self.tree.UnselectAll()
		
	def getChannelsByName(self, unit, channels):
		"""
		Return items in the tree by their names
		"""   
		return self.selectChannelsByName(unit, channels, dontSelect = 1)
		
	def selectChannelsByNumber(self, unit, numbers, dontSelect = 0):
		"""
		Select channels with the given numhers
		"""
		n = -1
		ret = []
		self.programmatic = 1
		for item in self.dataUnitItems:
			obj = self.tree.GetPyData(item)
			if unit == self.dataUnitToPath[obj]:
				
				n += 1
				if n in numbers:                    
					ret.append(obj)
					if not dontSelect and not self.tree.IsSelected(item):                    
						self.tree.ToggleItemSelection(item)                    
		self.programmatic = 0    
		return ret

	def selectChannelsByName(self, unit, channels, dontSelect = 0):
		"""
		Select items in the tree by their names
		"""
		ret = []
		self.programmatic = 1        
		for item in self.dataUnitItems:
			obj = self.tree.GetPyData(item)
			if obj.getName() in channels and unit == self.dataUnitToPath[obj]:
				if not dontSelect and not self.tree.IsSelected(item):
					self.tree.ToggleItemSelection(item)
				ret.append(obj)
		self.programmatic = 0        
		return ret

	def closeAll(self):
		"""
		Close all open datasets
		"""
		self.ignore = 1
		self.selectAll(self.tree.GetRootItem())
		self.ignore = 0
		self.onCloseDataset("")
	
	def selectAll(self,parent):
		"""
		Selects all items from the tree
		"""
		if parent.IsOk() and self.tree.ItemHasChildren(parent):
			child, cookie = self.tree.GetFirstChild(parent)
			while child:
				obj = self.tree.GetPyData(child)
				select = obj != "1" and obj != "2"
				if child not in self.tree.GetSelections() and select:
					self.tree.SelectItem(child)
				if self.tree.ItemHasChildren(child):
					self.selectAll(child)
				child = self.tree.GetNextSibling(child)


	def onSelectAll(self, event):
		"""
		Select all event handler
		"""
		self.ignore = 1
		self.selectAll(self.tree.GetRootItem())
		self.ignore = 0
