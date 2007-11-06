#-*- coding: iso-8859-1 -*-
"""
 Unit: TaskPanel
 Project: BioImageXD
 Created: 23.11.2004, KP
 Description:

 A panel that is a base class for all the task panels that are 
 used to control the settings for the various modules. Expects to be handed a 
 CombinedDataUnit() containing the datasets that the module processes
 Uses the Visualizer for previewing.

 Copyright (C) 2005	 BioImageXD Project
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

import scripting
import ChannelTray
import lib.ImageOperations
import lib.messenger
import Logging
import os.path
import ProcessingManager
from wx.lib.scrolledpanel import ScrolledPanel
import vtk
import vtkbxd
import wx

TOOL_W = 50
TOOL_H = 50

class TaskPanel(ScrolledPanel):
	"""
	Created: 23.11.2004, KP
	Description: A baseclass for a panel for controlling the settings of the 
				 various task modules
	"""
	def __init__(self, root, tb, wantNotebook = 1):
		"""
		Created: 03.11.2004, KP
		Description: Initialization
		Parameters:
				root	Is the parent widget of this window
		"""
		ScrolledPanel.__init__(self, root, -1, size = (200, -1))
		#wx.Panel.__init__(self, root, -1,size=(200,-1))
		self.toolMgr = tb
		self.itemBitmaps = []
		self.cacheParser = None
		self.wantNotebook = wantNotebook
		# Unbind to not get annoying behaviour of scrolling
		# when clicking on the panel
		self.Unbind(wx.EVT_CHILD_FOCUS)
		self.buttonPanel = wx.Panel(self, -1)
		self.root = root
		self.preview = None
		self.onByDefault = 1
		self.cacheKey = None

	
		self.mainsizer = wx.GridBagSizer()
		if not hasattr(self, "createItemSelection"):
			self.createItemSelection = 0

		n = 0
		self.channelBox = None
		if self.createItemSelection:
			self.channelBox = ChannelTray.ChannelTray(self, size = (250, 72), style = wx.BORDER_SUNKEN)
			self.mainsizer.Add(self.channelBox, (n, 0))
			n += 1
		self.settingsSizer = wx.GridBagSizer()
		#self.mainsizer.Add(self.settingsSizer,(0,1),flag=wx.EXPAND|wx.ALL)
		
		self.commonSettingsSizer = wx.GridBagSizer()
		self.mainsizer.Add(self.commonSettingsSizer, (n, 0), flag = wx.EXPAND | wx.ALL)
		n += 1
		self.mainsizer.Add(self.settingsSizer, (n, 0), flag = wx.EXPAND | wx.ALL)
		n += 1
		if wantNotebook:
			self.settingsNotebook = wx.Notebook(self, -1, style = wx.NB_MULTILINE)
			
			font = self.settingsNotebook.GetFont()
			font.SetPointSize(font.GetPointSize() - 1)
			self.settingsNotebook.SetFont(font)

		#self.staticLine=wx.StaticLine(self)
		#self.mainsizer.Add(self.staticLine,(2,0),span=(1,1),flag=wx.EXPAND)
		self.mainsizer.Add(self.buttonPanel, (n, 0), span = (1, 1), flag = wx.EXPAND)
		
		self.buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
		self.buttonPanel.SetSizer(self.buttonSizer)
		self.buttonPanel.SetAutoLayout(1)

		n += 1
		self.filePath = None
		self.dataUnit = None
		self.settings = None
		self.settingsIndex = -1

		self.createButtonBox()
		self.createOptionsFrame()

		self.SetSizer(self.mainsizer)
		self.SetAutoLayout(True)
		
		self.SetupScrolling()
		
		#lib.messenger.connect(None,"itf_update",self.doPreviewCallback)
		lib.messenger.connect(None, "channel_selected", self.selectItem)
		lib.messenger.connect(None, "switch_datasets", self.onSwitchDatasets)
		lib.messenger.connect(None, "update_settings_gui", self.onUpdateGUI)
  
		
	def setCacheKey(self, key):
		"""
		Created: 30.10.2006, KP
		Description: Set the cached settings for this task, so that they can be restored later on
		"""
		self.cacheKey = key
		
		
	def onUpdateGUI(self, *arg):
		"""
		Created: 07.02.2006, KP
		Description: A callback for updating the GUI when settings have been changed
		"""			
		self.updateSettings(1)
		
	def restoreFromCache(self, cachedSettings = None):
		"""
		Created: 30.10.2006, KP
		Description: Restore settings for the dataunit and source dataunits from a cache entry
		"""
		# Load the cached settings
		
		if not cachedSettings:
			if self.cacheKey:
				cachedSettings, cacheParser = scripting.getSettingsFromCache(self.cacheKey)
			
		if not cachedSettings:
			Logging.info("No settings found in cache", kw = "caching")
			return
		Logging.info("Restoring settings with key %s from cache" % (str(self.cacheKey)), kw = "caching")
		combined = cachedSettings[0]
		self.dataUnit.setSettings(combined)
		sources = self.dataUnit.getSourceDataUnits()
		for i, setting in enumerate(cachedSettings[1:]):
			#print "Setting settings of source %d"%i
			#DataUnitSetting.DataUnitSettings.initialize(setting,sources[i],len(sources),sources[i].getNumberOfTimepoints())
			sources[i].setSettings(setting)
			#tf=setting.get("IntensityTransferFunction")
			#print setting,tf
			#print "\n\nSetting itf ",i,"= itf with 0=",tf.GetValue(0),"and 255=",tf.GetValue(255)
		self.settings = sources[self.settingsIndex].getSettings()
		self.cacheParser = cacheParser
		self.updateSettings(force = True)
		
	def cacheSettings(self):
		"""
		Created: 23.10.2006, KP
		Description: Store the settings of the dataunit in a cache from which they can be
					 later retrieved at will
		"""
		# It is possible we do not have dataunit if the task was closed for example, because of
		# different dimensions of the dataunits
		if not self.dataUnit:
			return
		sources = self.dataUnit.getSourceDataUnits()
		#print "SOURCES=",sources
		settings = [x.getSettings() for x in sources]
		settings.insert(0, self.dataUnit.getSettings())
		Logging.info("Storing to cache with key %s" % str(self.dataUnit.getCacheKey()), kw = "caching")
		#for i,settingx in enumerate(settings[1:]):
		#	 
		#	 tf=settingx.get("IntensityTransferFunction")
		scripting.storeSettingsToCache(self.dataUnit.getCacheKey(), settings)
		for i in sources:
			i.resetSettings()
		
	def onSwitchDatasets(self, obj, evt, args):
		"""
		Created: 11.08.2005, KP
		Description: Switch the used source datasets
		"""
		try:
			self.dataUnit.switchSourceDataUnits(args)
		except Logging.GUIError, err:
			err.show()			  
		if self.channelBox:
			self.channelBox.clear()
			self.channelBox.setDataUnit(self.dataUnit, toolImage = (TOOL_W, TOOL_H))
		self.createItemToolbar()
		self.doPreviewCallback()

			
	def getChannelItemBitmap(self, chbmp, color = (255, 255, 255)):
		"""
		Created: 7.11.2006, KP
		Description: Draw a bitmap that can be used as a label for the channel selection buttonsSizer
		"""
		if chbmp.GetWidth() != TOOL_W or chbmp.GetHeight() != TOOL_H:
			chbmp = chbmp.ConvertToImage()
			chbmp = chbmp.Rescale(TOOL_W, TOOL_H).ConvertToBitmap()
		dc = wx.MemoryDC()
		bmp2 = wx.EmptyBitmap(60, 60)
		dc.SelectObject(bmp2)
		dc.BeginDrawing()
		val = [0, 0, 0]
		#dc.SetBrush(wx.TRANSPARENT_BRUSH)
		if isinstance(color, vtk.vtkColorTransferFunction):
			color.GetColor(255, val)
			r, g, b = val
			r *= 255
			g *= 255
			b *= 255
		else:
			r, g, b = color
		dc.SetPen(wx.Pen(wx.Colour(r, g, b), 6))
		dc.SetBrush(wx.Brush(wx.Colour(r, g, b)))
		dc.DrawRectangle(0, 0, 60, 60)
		dc.DrawBitmap(chbmp, 5, 5)
		dc.EndDrawing()
		dc.SelectObject(wx.NullBitmap)
		return bmp2
		
	def createItemToolbar(self, force = 0):
		"""
		Created: 31.03.2005, KP
		Description: Method to create a toolbar for the window that allows use to select processed channel
		"""
		self.toolMgr.clearItemsBar()
		n = 0

		self.toolIds = []
		sourceUnits = self.dataUnit.getSourceDataUnits()
		if not force and len(sourceUnits) == 1:
			return
		merge = vtkbxd.vtkImageColorMerge()
		self.itemMips = []
		for i, dataunit in enumerate(sourceUnits):
			#color = dataunit.getColor()
			ctf = dataunit.getColorTransferFunction()
			name = dataunit.getName()
			dc = wx.MemoryDC()
			
			bmp, vtkimg = lib.ImageOperations.vtkImageDataToPreviewBitmap(dataunit, 0, None, TOOL_W, TOOL_H, getvtkImage = 1)
			self.itemMips.append(vtkimg)
			if self.channelBox:
				self.channelBox.setPreview(i, bmp)
			bmp2 = self.getChannelItemBitmap(bmp, ctf)
			toolid = wx.NewId()
			self.toolIds.append(toolid)
			self.toolMgr.addChannelItem(name, bmp2, toolid, lambda e, x = n, s = self:s.setPreviewedData(e, x))
			self.toolMgr.toggleTool(toolid, self.onByDefault)
			self.dataUnit.setOutputChannel(i, self.onByDefault)
			n = n + 1
		
		if self.channelBox:
			self.channelBox.SetSelection(0)
		return n

	def createButtonBox(self):
		"""
		Created: KP
		Description: create the buttons on the bottom of the	 panel
		"""
		self.buttonsSizer2 = wx.BoxSizer(wx.HORIZONTAL)

		self.previewButton = wx.Button(self.buttonPanel, -1, "Apply")
		self.previewButton.Bind(wx.EVT_BUTTON, self.doPreviewCallback)
		self.buttonsSizer2.AddSpacer((5,5))
		self.buttonsSizer2.Add(self.previewButton, 1, wx.RIGHT | wx.TOP | wx.ALIGN_CENTER, 10)
		self.buttonsSizer2.AddSpacer((5,5))

	def onHelp(self, evt):
		"""
		Created: 03.11.2004, KP
		Description: Shows a help for this task panel
		"""
		lib.messenger.send(None, "view_help", self.operationName)
		
	def createOptionsFrame(self):
		"""
		Created: 03.11.2004, KP
		Description: Creates a frame that contains the various widgets
					 used to control the colocalization settings
		"""

		if self.wantNotebook:
			self.settingsSizer.Add(self.settingsNotebook, (1, 0), flag = wx.EXPAND | wx.ALL)


	def setPreviewedData(self, event, index = -1):
		"""
		Created: 22.07.2005, KP
		Description: A callback function for marking channels to be rendered
					 in the preview.
		"""
		flag0, flag1 = 0, 0
		try:
			flag0 = event.IsChecked()
		except:
			pass
		try:
			flag1 = event.GetIsDown()
		except:
			flag1 = 0
		flag = flag0 or flag1
		self.dataUnit.setOutputChannel(index, flag)
		self.doPreviewCallback(None)
		
	def selectItem(self, obj, event, index = -1):
		"""
		Created: 03.11.2004, KP
		Description: A callback function called when a channel is selected in
					 the menu
		"""
		Logging.info("Select item %d" % index, kw = "dataunit")
		if index == -1:		  
			Logging.error("No index given", "No index for selected dataunit given")
		sunit = self.dataUnit.getSourceDataUnits()[index]
		self.settings = sunit.getSettings()
		self.settingsIndex = index
		
		self.updateSettings()

	def updateSettings(self, force = 0):
		"""
		Created: 03.11.2004, KP
		Description: A method used to set the GUI widgets to their proper values
					 based on the selected channel, the settings of which are
					 stored in the instance variable self.settings
		"""
		raise "Abstract method updateSetting() called from base class"

	def doOperation(self):
		"""
		Created: 03.2.2005, KP
		Description: A method that executes the operation on the selected
					 dataset
		"""		   
		mgr = ProcessingManager.ProcessingManager(self, self.operationName)
		scripting.processingManager = mgr
		mgr.setDataUnit(self.dataUnit)
		self.grayOut()

		if scripting.modal:
			mgr.ShowModal()
			mgr.Destroy()
		   
			scripting.processingManager = None			  
		else:
			mgr.Show()
		self.grayOut(1)			   

	def grayOut(self, enable = 0):
		"""
		Created: 16.11.2004, KP
		Description: Grays out the widget while doing colocalization
		Parameters:
			enable		If the enable parameter is defined, the effect of the
						function is reversed and the widgets are set to normal
						state

		"""
		self.Enable(enable)

	def doPreviewCallback(self, *args):
		"""
		Created: 03.11.2004, KP
		Description: A callback for the button "Preview" and other events
					 that wish to update the preview
		"""
		Logging.info("Sending preview update event", kw = "event")
		lib.messenger.send(None, "data_changed", -1)

	def saveSettingsCallback(self, event):
		"""
		Created: 30.11.2004, KP
		Description: A callback to save the settings for this operation to a 
					 du file
		"""
		wc = "Dataset settings (*.bxd)|*.bxd"
		dlg = wx.FileDialog(self, "Save dataset settings to file", wildcard = wc, style = wx.SAVE)
		filename = None
		if dlg.ShowModal() == wx.ID_OK:
			filename = dlg.GetPath()
		
		dlg.Destroy()

		if not filename:
			return
		if filename[-3:].lower() != ".bxd":
			filename += ".bxd"

		Logging.info("Saving to ", filename, kw = "processing")

		self.updateSettings()
		self.dataUnit.doProcessing(filename, settings_only = True)

	def setCombinedDataUnit(self, dataUnit):
		"""
		Created: 23.11.2004, KP
		Description: Sets the combined dataunit that is to be processed.
					 It is then used to get the names of all the source data
					 units and they are added to the menu.
		"""
		lib.messenger.send(None, "current_task", self.operationName)
				
		self.dataUnit = dataUnit
		name = dataUnit.getName()
		Logging.info("Name of dataunit is ", name, kw = "dataunit")
		#self.taskName.SetValue(name)
		try:
			#self.preview.setDataUnit(dataUnit)
			units = self.dataUnit.getSourceDataUnits()
			
		except Logging.GUIError, ex:
			ex.show()
		fileNames = []
		for unit in units:
			ds = unit.dataSource.getFileName()
			ds = os.path.basename(ds)
			if ds not in fileNames:
				fileNames.append(ds)
		if self.channelBox:
			self.channelBox.setDataUnit(dataUnit, toolImage = (TOOL_W, TOOL_H))
		lib.messenger.send(None, "current_file", ", ".join(fileNames))		   
		
		self.selectItem(None, None, 0)
		# Delay the call, maybe it will make it work on mac
		wx.FutureCall(100, self.createItemToolbar)
