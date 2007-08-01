# -*- coding: iso-8859-1 -*-

"""
 Unit: VisualizationFrame
 Project: BioImageXD
 Created: 28.04.2005, KP
 Description:

 A framework for embedding different visualization modes to BioImageXD
 
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
__version__ = "$Revision: 1.9 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import wx
import time
import platform
import vtk
from vtk.wx.wxVTKRenderWindowInteractor import wxVTKRenderWindowInteractor
import Dialogs
import  wx.lib.colourselect as  csel
import wx.lib.scrolledpanel as scrolled

from lib.persistence import state_pickler

from VisualizationModules import *
from ModuleConfiguration import *
from VisualizerWindow import *
	
class RendererConfiguration(wx.MiniFrame):
	"""
	Created: 16.05.2005, KP
	Description: A frame for configuring the renderer
	"""    
	def __init__(self, parent, visualizer):
		"""
		Created: 28.04.2005, KP
		Description: Initialization
		"""     
		wx.MiniFrame.__init__(self, parent, -1, "Configure Render Window")
		self.panel = wx.Panel(self, -1)
		self.s = wx.BoxSizer(wx.VERTICAL)
		
		self.sizer = wx.GridBagSizer()
		self.parent = parent
		self.visualizer = visualizer
		self.mode = self.visualizer.currMode
		
		self.buttonBox = wx.BoxSizer(wx.HORIZONTAL)
		self.okButton = wx.Button(self.panel, -1, "Ok")
		self.applyButton = wx.Button(self.panel, -1, "Apply")
		self.cancelButton = wx.Button(self.panel, -1, "Cancel")
		
		self.okButton.Bind(wx.EVT_BUTTON, self.onOk)
		self.applyButton.Bind(wx.EVT_BUTTON, self.onApply)
		self.cancelButton.Bind(wx.EVT_BUTTON, self.onCancel)
		
		
		self.buttonBox.Add(self.okButton)
		self.buttonBox.Add(self.applyButton)
		self.buttonBox.Add(self.cancelButton)
		
		self.contentSizer = wx.GridBagSizer()
		self.sizer.Add(self.contentSizer, (0, 0))
		
		self.line = wx.StaticLine(self.panel, -1)
		self.sizer.Add(self.line, (2, 0), flag = wx.EXPAND | wx.LEFT | wx.RIGHT)
		self.sizer.Add(self.buttonBox, (3, 0))
		
		self.initializeGUI()
		
		self.panel.SetSizer(self.sizer)
		self.panel.SetAutoLayout(1)
		self.sizer.Fit(self.panel)
		self.SetSize(self.panel.GetSize())
		
		self.s.Add(self.panel)
		self.SetSizer(self.s)        
		self.SetAutoLayout(1)
		self.s.Fit(self)
		
	def initializeGUI(self):
		"""
		Created: 16.05.2005, KPself.mode
		Description: Build up the configuration GUI
		"""             
		self.colorLbl = wx.StaticText(self.panel, -1, "Background color:")
		self.colorBtn = csel.ColourSelect(self.panel, -1)
		self.Bind(csel.EVT_COLOURSELECT, self.onSelectColor, id = self.colorBtn.GetId())

		self.sizeLbl = wx.StaticText(self.panel, -1, "Window size:")
		self.sizeEdit = wx.TextCtrl(self.panel, -1, "512x512")

		self.stereoLbl = wx.StaticText(self.panel, -1, "Stereo rendering:")
		self.modes = [None, "RedBlue", "CrystalEyes", "Dresden", "Interlaced", "Left", "Right"]
		stereomodes = ["No stereo", "Red-Blue", "Crystal Eyes", "Dresden", "Interlaced", "Left", "Right"]
		self.stereoChoice = wx.Choice(self.panel, -1, choices = stereomodes)
		
		self.stereoChoice.Bind(wx.EVT_CHOICE, self.onSetStereoMode)
		
		self.contentSizer.Add(self.colorLbl, (0, 0))
		self.contentSizer.Add(self.colorBtn, (0, 1))
		self.contentSizer.Add(self.sizeLbl, (1, 0))
		self.contentSizer.Add(self.sizeEdit, (1, 1))
		self.contentSizer.Add(self.stereoLbl, (2, 0))
		self.contentSizer.Add(self.stereoChoice, (2, 1))
		self.color = None
		self.stereoMode = None
		
	def onApply(self, event):
		"""
		Created: 16.05.2005, KP
		Description: Apply the changes
		"""           
		if self.color:
			r, g, b = self.color
			print "Setting renderwindow background to ", r, g, b
			self.visualizer.setBackground(r, g, b)
		print "Setting stero mode to", self.stereoMode
		self.mode.setStereoMode(self.stereoMode)
		try:
			x, y = map(int, self.sizeEdit.GetValue().split("x"))
			print "Setting render window size to ", x, y
			self.visualizer.setRenderWindowSize((x, y))
		except:
			pass
		self.visualizer.Render()

		
	def onCancel(self, event):
		"""
		Created: 28.04.2005, KP
		Description: Close this dialog
		"""     
		self.Close()
		
	def onOk(self, event):
		"""
		Created: 28.04.2005, KP
		Description: Apply changes and close
		""" 
		self.onApply(None)
		self.Close()
		
	def onSelectColor(self, event):
		"""
		Created: 16.05.2005, KP
		Description: Select the background color for render window
		"""             
		color = event.GetValue()
		self.color = (color.Red(), color.Green(), color.Blue())
		
	def onSetStereoMode(self, event):
		"""
		Created: 16.05.2005, KP
		Description: Set the stereo mode
		"""             
		index = event.GetSelection()
		mode = self.modes[index]
	
		self.stereoMode = mode
			
	

class ConfigurationPanel(scrolled.ScrolledPanel):
	"""
	Created: 28.04.2005, KP
	Description: A panel that can be used to configure the rendering
	"""
	def __init__(self, parent, visualizer, mode, **kws):
		"""
		Created: 28.04.2005, KP
		Description: Initialization
		"""
		#wx.Panel.__init__(self,parent,-1,style=wx.RAISED_BORDER)
		#wx.ScrolledWindow.__init__(self,parent,-1)
		size = kws.get("size", (200, -1))
		scrolled.ScrolledPanel.__init__(self, parent, -1, size = size)
		
		self.tmpSizer = wx.GridBagSizer(5, 5)
		
		self.sizer = wx.GridBagSizer(5, 5) 
		# Unbind to not get annoying behaviour of scrolling
		# when clicking on the panel
		self.Unbind(wx.EVT_CHILD_FOCUS)

		self.parent = parent
		self.visualizer = visualizer
		self.mode = mode
		self.currentConf = None
		self.count = {}
		self.currentConfMode = ""
		
		self.visSbox = wx.StaticBox(self, -1, "3D mode")
		self.visSizer = wx.StaticBoxSizer(self.visSbox)
		self.tmpSizer.Add(self.sizer, (0, 0))
		self.visSizer.Add(self.tmpSizer)
		
		self.moduleLbl = wx.StaticText(self, -1, "3D rendering modules")
		
#        self.moduleBox = wx.StaticBox(self,-1,"Modules for 3D scene")
#        self.moduleSizer = wx.StaticBoxSizer(self.moduleBox, wx.VERTICAL)
		modules = self.mode.mapping.keys()
		modules.sort()

		self.moduleChoice = wx.Choice(self, -1, choices = modules)
		self.moduleChoice.SetSelection(0)
		
		
		self.moduleListbox = wx.CheckListBox(self, -1, size = (250, 80))
		
		font = self.moduleListbox.GetFont()
		if platform.system() != "Windows":
			font.SetPointSize(font.GetPointSize() - 2)
		else:
			font.SetPointSize(font.GetPointSize() - 1)

		self.moduleListbox.SetFont(font)

		
		
		self.moduleListbox.Bind(wx.EVT_CHECKLISTBOX, self.onCheckItem)
		self.moduleListbox.Bind(wx.EVT_LISTBOX, self.onSelectItem)
		
		self.moduleLoad = wx.Button(self, -1, "Load")
		self.moduleLoad.Bind(wx.EVT_BUTTON, self.onLoadModule)
		
		self.moduleRemove = wx.Button(self, -1, "Remove")
		self.moduleRemove.Bind(wx.EVT_BUTTON, self.onRemoveModule)        
		n = 0
#        self.sizer.Add(self.namePanel,(n,0),flag=wx.EXPAND|wx.LEFT|wx.RIGHT)
#        n+=1
		self.sizer.Add(self.moduleLbl, (n, 0))
		n += 1
		self.sizer.Add(self.moduleChoice, (n, 0))
		n += 1
		self.sizer.Add(self.moduleListbox, (n, 0))
		n += 1
	 
		box = wx.BoxSizer(wx.HORIZONTAL)
		box.Add(self.moduleLoad)
		box.Add(self.moduleRemove)
		self.sizer.Add(box, (n, 0))
		self.selected = -1
		self.confPanel = None
		
		self.SetSizer(self.visSizer)
		self.SetAutoLayout(1)
		self.SetupScrolling()
		
	def onConfigureRenderwindow(self, event):
		"""
		Created: 15.05.2005, KP
		Description: Configure the render window
		"""
		conf = RendererConfiguration(self, self.visualizer)
		conf.Show()
		
		
	def onSelectItem(self, event):
		"""
		Created: 15.05.2005, KP
		Description: Select a module
		"""
		self.selected = event.GetSelection()
		self.showConfiguration(self.selected)
		
	def showConfiguration(self, n):
		"""
		Created: 23.05.2005, KP
		Description: showConfiguration
		"""
		if self.currentConf:
			self.sizer.Detach(self.currentConf)
			#self.confSizer.Detach(self.currentConf)

			#del self.currentConf
			self.currentConf.Show(0)
		lbl = self.moduleListbox.GetString(n)
		self.currentConfLbl = lbl
		modname = lbl.split("#")[0].strip()
		panel = self.mode.getConfigurationPanel(modname)
		
		w, h = self.moduleListbox.GetSize()
		
#        if not self.confPanel:
#            self.confPanel = wx.StaticBox(self,-1,"Configure %s"%lbl)
#            self.confSizer = wx.StaticBoxSizer(self.confPanel,wx.VERTICAL)
#            self.confPanel = NamePanel(self,"Configure %s"%lbl,None,size=(200,25))
#            self.sizer.Add(self.confSizer,(5,0),flag=wx.EXPAND|wx.LEFT|wx.RIGHT)
#        self.confPanel.SetLabel("Configure %s"%lbl)
		#self.confPanel.setColor((0,0,0),(180,255,180))
		
		self.currentConf = panel(self, self.visualizer, lbl)#,mode=self.mode)
	 
		#self.confSizer.Add(self.currentConf)
		self.sizer.Add(self.currentConf, (5, 0))
		#self.currentConf.Layout()
		#self.Layout()
		#self.parent.Layout()
		
		self.SetupScrolling()
				
	def onCheckItem(self, event):
		"""
		Created: 15.05.2005, KP
		Description: Enable / Disable a module
		"""
		index = event.GetSelection()
		lbl = self.moduleListbox.GetString(index)
		status = self.moduleListbox.IsChecked(index)
		#print "Setting rendering of %s to %s"%(lbl,status)
		self.mode.setRenderingStatus(lbl, status)

	def onConfigureLights(self, event):
		"""
		Created: 29.04.2005, KP
		Description: Configure the lights
		"""
		lm = self.mode.lightsManager
		lm.config()


	def onLoadModule(self, event):
		"""
		Created: 28.04.2005, KP
		Description: Load the selected module
		"""
		lbl = self.moduleChoice.GetStringSelection()
		if not lbl in self.count:
			self.count[lbl] = 0
		n = self.count[lbl]
		nlbl = lbl
		if n > 0:
			nlbl = "%s #%d" % (lbl, n + 1)
		self.count[lbl] += 1
			
		self.mode.loadModule(lbl, nlbl)
		self.appendModuleToList(nlbl)
		
	def appendModuleToList(self, module):
		"""
		Created: 16.05.2005, KP
		Description: Append a module to the list
		"""
		n = self.moduleListbox.GetCount()
		self.moduleListbox.InsertItems([module], n)
		self.moduleListbox.Check(n)

	def onRemoveModule(self, event):
		"""
		Created: 03.05.2005, KP
		Description: Remove the selected module
		"""
		if self.selected == -1:
			if self.moduleListbox.GetCount() == 1:
				self.selected = 0
		if self.selected == -1:
			Dialogs.showerror(self, "You have to select a module to be removed", "No module selected")
			return
		lbl = self.moduleListbox.GetString(self.selected)
		self.mode.removeModule(lbl)
		self.moduleListbox.Delete(self.selected)
		self.selected = -1
		
		if self.currentConf and self.currentConfLbl == lbl:
			self.sizer.Detach(self.currentConf)
			#self.confSizer.Detach(self.currentConf)
			self.currentConf.Show(0)
			del self.currentConf
			self.currentConf = None
			self.SetupScrolling()

	def onOpenScene(self, event):
		"""
		Created: 02.08.2005, KP
		Description: Load a scene from file
		"""    
		wc = "3D view scene (*.3xd)|*.3xd"
		filename = Dialogs.askOpenFileName(self, "Open 3D view scene", wc, 0)
		if filename:        
			state = state_pickler.load_state(open(filename[0], "r"))
			#state_pickler.set_state(self.mode,state)
			self.moduleListbox.Clear()
			self.mode.__set_pure_state__(state)
			
			messenger.send(None, "update_module_settings")
	
	def onSaveScene(self, event):
		"""
		Created: 02.08.2005, KP
		Description: Save a scene to file
		"""    
		wc = "3D view scene (*.3xd)|*.3xd"
		filename = None
		dlg = wx.FileDialog(self, "Save 3D view scene as...", defaultFile = "scene.3xd", wildcard = wc, style = wx.SAVE)
		if dlg.ShowModal() == wx.ID_OK:
			filename = dlg.GetPath()        
		if filename:
			p = state_pickler.dump(self.mode, open(filename, "w"))        
		
class VisualizationFrame(wx.Frame):
	"""
	Created: 28.04.2005, KP
	Description: A window for showing 3D visualizations
	"""
	def __init__(self, parent, **kws):
		"""
		Created: 28.04.2005, KP
		Description: Initialization
		"""
		wx.Frame.__init__(self, parent, -1, "BioImageXD Visualization", **kws)

