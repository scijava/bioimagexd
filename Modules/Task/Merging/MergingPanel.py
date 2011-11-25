#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: MergingPanel
 Project: BioImageXD
 Description:

 A wxPython Dialog window that is used to control the settings for the
 colocalization module. Expects to be handed a ColorCombinationDataUnit() 
 containing the datasets from which the color combination is generated.
 Uses the PreviewFrame for previewingge.

 Copyright (C) 2005  BioImageXD Project
 See CREDITS.txt for details

 This program is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.

 This program is direstributed in the hope that it will be useful,
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

from GUI.IntensityTransferEditor import IntensityTransferEditor
import lib.messenger
import Logging
from GUI import TaskPanel
from GUI import ColorTransferEditor
import vtkbxd
import wx
import scripting
import types

class MergingPanel(TaskPanel.TaskPanel):
	"""
	Description: A window for controlling the settings of the color
				 combination module
	"""
	def __init__(self, parent, tb):
		"""
		Initialization
		Parameters:
				parent    Is the parent widget of this window
		"""
		self.alphaTF = vtkbxd.vtkIntensityTransferFunction()
		self.operationName = "Merge"
		self.createItemSelection = 1
		TaskPanel.TaskPanel.__init__(self, parent, tb)

		self.oldBg = self.GetBackgroundColour()
		
		self.mainsizer.Layout()
		self.mainsizer.Fit(self)

	def createButtonBox(self):
		"""
		Creates a button box containing the buttons Render,
					 Preview and Close
		"""
		TaskPanel.TaskPanel.createButtonBox(self)
		lib.messenger.connect(None, "process_dataset", self.doColorMergingCallback)        

		
	def createOptionsFrame(self):
		"""
		Creates a frame that contains the various widgets
					 used to control the colocalization settings
		"""
		TaskPanel.TaskPanel.createOptionsFrame(self)

		self.paletteLbl = wx.StaticText(self, -1, "Channel palette:")
		self.commonSettingsSizer.Add(self.paletteLbl, (1, 0))
		self.colorBtn = ColorTransferEditor.CTFButton(self)
		self.commonSettingsSizer.Add(self.colorBtn, (2, 0))

		self.editIntensityPanel = wx.Panel(self.settingsNotebook, -1)
		self.editIntensitySizer = wx.GridBagSizer()
		
		self.intensityTransferEditor = IntensityTransferEditor(self.editIntensityPanel)
		self.editIntensitySizer.Add(self.intensityTransferEditor, (0, 0), span = (1, 2))        

		self.box = wx.BoxSizer(wx.HORIZONTAL)
		self.editIntensitySizer.Add(self.box, (2, 0))
		
		self.restoreBtn = wx.Button(self.editIntensityPanel, -1, "Reset")
		self.restoreBtn.Bind(wx.EVT_BUTTON, self.intensityTransferEditor.restoreDefaults)
		self.box.Add(self.restoreBtn)        
		
		# The alpha function doesn't need to be edited
		# Code left if futher need shows ups
		
		#self.editAlphaPanel = wx.Panel(self.settingsNotebook,-1)
		self.editAlphaPanel = wx.Panel(self.editIntensityPanel, -1)
		self.editAlphaSizer = wx.GridBagSizer()

		self.alphaModeBox = wx.RadioBox(self.editAlphaPanel, -1, "Alpha channel construction",
		choices = ["Maximum Mode", "Average Mode", "Image Luminance", "No alpha"], \
					majorDimension = 2, style = wx.RA_SPECIFY_COLS)
		
		self.alphaModeBox.SetForegroundColour(scripting.COLOR_EXPERIENCED)
		self.alphaModeBox.Bind(wx.EVT_RADIOBOX, self.modeSelect)
		
		self.averageLbl = wx.StaticText(self.editAlphaPanel, -1, "Average Threshold:")
		self.averageLbl.SetForegroundColour(scripting.COLOR_EXPERIENCED)
		self.averageEdit = wx.TextCtrl(self.editAlphaPanel, -1, "", size = (150, -1))
		self.averageEdit.Enable(0)
		self.averageEdit.SetForegroundColour(scripting.COLOR_EXPERIENCED)
		self.averageEdit.Bind(wx.EVT_TEXT_ENTER, self.onAverageEdit)
		self.averageEdit.Bind(wx.EVT_KILL_FOCUS, self.onAverageEdit)
		
		box = wx.BoxSizer(wx.HORIZONTAL)
		box.Add(self.averageLbl)
		box.Add(self.averageEdit)
		self.editAlphaSizer.Add(self.alphaModeBox, (0, 0))
		self.editAlphaSizer.Add(box, (2, 0))
		
		self.editAlphaPanel.SetSizer(self.editAlphaSizer)
		self.editAlphaSizer.Fit(self.editAlphaPanel)
		self.editIntensitySizer.Add(self.editAlphaPanel, (4, 0))

		self.editIntensityPanel.SetSizer(self.editIntensitySizer)
		self.editIntensityPanel.SetAutoLayout(1)
		
		self.editIntensityPanel.Layout()
		self.editIntensitySizer.Fit(self.editIntensityPanel)        
		self.settingsNotebook.AddPage(self.editIntensityPanel, "Intensity")
		#self.settingsNotebook.AddPage(self.editAlphaPanel,"Alpha Channel")
		
#        self.optionssizer.Add(self.intensityTransferEditor,(3,0))

	def modeSelect(self, event):
		"""
		A method that is called when the selection of alpha mode is chan ged
		"""
		mode = event.GetInt()
		try:
			value = int(self.averageEdit.GetValue())
		except:
			value = 0
		self.settings.set("AlphaMode", [mode, value])
		if mode == 1:
			self.averageEdit.Enable(1)
		else:
			self.averageEdit.Enable(0)

	def onAverageEdit(self, evt):
		"""
		Method to update settings of current average value
		"""
		try:
			value = int(self.averageEdit.GetValue())
		except:
			value = 0
		mode = self.settings.get("AlphaMode")
		mode[1] = value
		self.settings.set("AlphaMode", mode)

	def resetTransferFunctions(self, event = None):
		"""
		A method to reset all the intensity transfer functions
		"""
		dataunits = self.dataUnit.getSourceDataUnits()
		for unit in dataunits:
			setting = unit.getSettings()
			minval, maxval = unit.getScalarRange()
			ctf = unit.getColorTransferFunction()
			ctfmin, ctfmax = ctf.GetRange()
			print "CTF range=",ctfmax
			bitmax = (2**unit.getSingleComponentBitDepth()-1)
			print "bitmax=",bitmax
			maxval = max(ctfmax, maxval,bitmax)
			itf = vtkbxd.vtkIntensityTransferFunction()
			itf.SetRangeMax(maxval)
			self.alphaTF.SetRangeMax(maxval)
			setting.set("IntensityTransferFunction", itf)


	def updateSettings(self, force = 0):
		"""
		A method used to set the GUI widgets to their proper values
					 based on the selected channel, the settings of which are 
					 stored in the instance variable self.configSetting
		"""
		if self.dataUnit and self.settings:
			ctf = self.settings.get("ColorTransferFunction")
			if ctf and self.colorBtn:
				Logging.info("Setting ctf of color button", kw = "ctf")
				self.colorBtn.setColorTransferFunction(ctf)
				self.colorBtn.Refresh()
	
			#Logging.info("settings=",self.settings,kw="task")
			tf = self.settings.get("IntensityTransferFunction")
			self.intensityTransferEditor.setIntensityTransferFunction(tf)
			try:
				mode = self.settings.get("AlphaMode")
				if types.StringType == type(mode):
					mode = eval(mode)
				self.alphaModeBox.SetSelection(mode[0])
				if mode[0] == 1:
					self.averageEdit.Enable(1)
				else:
					self.averageEdit.Enable(0)
				self.averageEdit.SetValue(str(mode[1]))
			except:
				pass

	def doColorMergingCallback(self, *args):
		"""
		A callback for the processing button
		"""
		#print "\n\n\n\n\nDO COLOR MERGING"
		method = self.alphaModeBox.GetSelection()
		val = 0
		if method == 1:
			val = int(self.averageEdit.GetValue())
		lst = [method, val]
		Logging.info("Setting alpha mode to ", lst, kw = "task")
		#self.dataUnit.setAlphaMode(lst)
		self.settings.set("AlphaMode", lst)

		TaskPanel.TaskPanel.doOperation(self)

	def setCombinedDataUnit(self, dataUnit):
		"""
		Sets the combined dataunit that is to be processed.
					 It is then used to get the names of all the source 
					 data units and they are added to the menu.
		"""
		TaskPanel.TaskPanel.setCombinedDataUnit(self, dataUnit)
		# We add entry "Alpha Channel" to the list of channels to allow
		# the user to edit the alpha channel for the 24-bit color merging
		#self.dataUnit.setOpacityTransfer(self.alphaTF)
		self.settings.set("AlphaTransferFunction", self.alphaTF)
		ctf = self.settings.get("ColorTransferFunction")
		
		sources =  dataUnit.getSourceDataUnits()
		totmax = 0
		
		for i in sources:
			minval, maxval = i.getScalarRange()
			ctf = i.getColorTransferFunction()
			ctfmin, ctfmax = ctf.GetRange()
			bitmax = (2**i.getSingleComponentBitDepth()-1)
			maxval = max(ctfmax, maxval,bitmax)
			if maxval > totmax:
				totmax = maxval

		self.alphaTF.SetRangeMax(int(totmax))
		
		for i in range(len(sources)):
			tf = vtkbxd.vtkIntensityTransferFunction()
			tf.SetRangeMax(int(totmax))
			#self.settings.setCounted("IntensityTransferFunction",i,tf,0)
			sources[i].getSettings().set("IntensityTransferFunction", tf)

		tf = sources[0].getSettings().get("IntensityTransferFunction")
		#print "\n\nSETTING ITF EDITOR FUNCTION"
		self.intensityTransferEditor.setIntensityTransferFunction(tf)

		for i in range(len(sources)):
			self.dataUnit.setOutputChannel(i, 1)
		if self.colorBtn:
			#Logging.info("Setting ctf of colorbutton to ",ctf,kw="ctf")
			self.colorBtn.setColorTransferFunction(ctf)
		else:
			Logging.info("No color button to set ctf to ", kw = "ctf")
		self.restoreFromCache()
