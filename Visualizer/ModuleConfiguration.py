# -*- coding: iso-8859-1 -*-

"""
 Unit: ModuleConfiguration
 Project: BioImageXD
 Created: 30.04.2005, KP
 Description:

 A module containing the configuration dialogs for various rendering 
 modules.
 
 Copyright (C) 2005  BioImageXD Project
 See CREDITS.txt for details

 This program is free software; you can redistribute it and / or modify
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
import lib.messenger

class ModuleConfigurationPanel(wx.ScrolledWindow):
	"""
	Created: 23.05.2005, KP
	Description: A base class for module configuration dialogs
	"""    
	def __init__(self, parent, visualizer, name, **kws):
		"""
		Created: 28.04.2005, KP
		Description: Initialization
		"""
		#scrolled.ScrolledPanel.__init__(self,parent.parent,-1)
		if "mode" in kws:
			self.mode = kws["mode"]
			del kws["mode"]
		wx.ScrolledWindow.__init__(self, parent, -1, **kws)
		self.sizer = wx.GridBagSizer()
		self.visualizer = visualizer
		self.parent = parent
		self.name = name
		
		self.buttonBox = wx.BoxSizer(wx.HORIZONTAL)
		self.applyButton = wx.Button(self, -1, "Apply")
		
		self.applyButton.Bind(wx.EVT_BUTTON, self.onApply)
		self.buttonBox.Add(self.applyButton)
		
		self.contentSizer = wx.GridBagSizer()
		self.sizer.Add(self.contentSizer, (0, 0))
		
		self.toggleBtn = wx.ToggleButton(self, -1, "Advanced >>")
		self.toggleBtn.SetValue(0)
		self.toggleBtn.Bind(wx.EVT_TOGGLEBUTTON, self.onMaterial)
		self.sizer.Add(self.toggleBtn, (1, 0))
		
		self.lightBox = wx.StaticBox(self, -1, "Lighting")
		self.lightBoxSizer = wx.StaticBoxSizer(self.lightBox, wx.VERTICAL)
		self.lightPanel = wx.Panel(self, -1)
		self.lightSizer = wx.GridBagSizer()
		self.lightBoxSizer.Add(self.lightPanel)
		self.ambientLbl = wx.StaticText(self.lightPanel, -1, "Ambient lighting:")
		self.diffuseLbl = wx.StaticText(self.lightPanel, -1, "Diffuse lighting:")
		self.specularLbl = wx.StaticText(self.lightPanel, -1, "Specular lighting:")
		self.specularPowerLbl = wx.StaticText(self.lightPanel, -1, "Specular power:")
			
		self.ambientEdit = wx.TextCtrl(self.lightPanel, -1, "0.1")
		self.diffuseEdit = wx.TextCtrl(self.lightPanel, -1, "0.7")
		self.specularEdit = wx.TextCtrl(self.lightPanel, -1, "0.2")
		self.specularPowerEdit = wx.TextCtrl(self.lightPanel, -1, "10.0")
		
		self.lightSizer.Add(self.ambientLbl, (0, 0))
		self.lightSizer.Add(self.ambientEdit, (0, 1))
		self.lightSizer.Add(self.diffuseLbl, (1, 0))
		self.lightSizer.Add(self.diffuseEdit, (1, 1))
		self.lightSizer.Add(self.specularLbl, (2, 0))
		self.lightSizer.Add(self.specularEdit, (2, 1))
		self.lightSizer.Add(self.specularPowerLbl, (3, 0))
		self.lightSizer.Add(self.specularPowerEdit, (3, 1))
		self.lightPanel.SetSizer(self.lightSizer)
		self.lightSizer.Fit(self.lightPanel)
		
		#self.sizer.Add(self.lightPanel,(2,0))
		self.sizer.Add(self.lightBoxSizer, (2, 0))
		
		self.line = wx.StaticLine(self, -1)
		self.sizer.Add(self.line, (3, 0), flag = wx.EXPAND|wx.LEFT|wx.RIGHT)
		self.sizer.Add(self.buttonBox, (4, 0))
		
		self.sizer.Show(self.lightBoxSizer, 0)
		
		self.initializeGUI()
		self.findModule()
		
		self.SetSizer(self.sizer)
		self.SetAutoLayout(1)
		self.sizer.Fit(self)
		
		lib.messenger.connect(None, "update_module_settings", self.updateModuleSettings)

	def updateModuleSettings(self, obj, evt, *args):
		"""
		Created: 02.08.2005, KP
		Description: Signal for updating the module settings
		"""
		if self.module:
			self.setModule(self.module)

	def onMaterial(self, event):
		"""
		Created: 23.05.2005, KP
		Description: Toggle material configuration
		"""		
		val = self.toggleBtn.GetValue()
		
		self.sizer.Show(self.lightBoxSizer, val)
		self.Layout()
		self.parent.Layout()
		self.parent.FitInside()
		#self.parent.SetupScrolling()
		
	def onApply(self, event):
		"""
		Created: 16.05.2005, KP
		Description: Apply the changes
		"""		
		try:
			ambient = float(self.ambientEdit.GetValue())
			diffuse = float(self.diffuseEdit.GetValue())
			specular = float(self.specularEdit.GetValue())
			specularpwr = float(self.specularPowerEdit.GetValue())
		except:
			return
		self.module.setProperties(ambient, diffuse, specular, specularpwr)
		
	def findModule(self):
		"""
		Created: 28.04.2005, KP
		Description: Refresh the modules affected by this configuration
		"""
		modules = self.visualizer.getCurrentMode().getModules()
		for module in modules:
			if module.getName() == self.name:
				self.setModule(module)
				return

	def setModule(self, module):
		"""
		Created: 28.04.2005, KP
		Description: Set the module to be configured
		"""  
		self.module = module
