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

import bxdexceptions
import lib.messenger
import wx
import scripting

class ModuleConfigurationPanel(wx.ScrolledWindow):
	"""
	Created: 23.05.2005, KP
	Description: A base class for module configuration dialogs
	"""    
	def __init__(self, parent, visualizer, name, **kws):
		"""
		Initialization
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
		self.sizer.Add(self.buttonBox, (2, 0))

		self.advancedBoxSizer = None
		
		self.initializeGUI()
		self.findModule()
		
		self.SetSizer(self.sizer)
		self.SetAutoLayout(1)
		self.sizer.Fit(self)
		
		lib.messenger.connect(None, "update_module_settings", self.updateModuleSettings)

	def initializeGUI(self):
		raise bxdexceptions.AbstractMethodCalled()

	def updateModuleSettings(self, obj, evt, *args):
		"""
		Signal for updating the module settings
		"""
		if self.module:
			self.setModule(self.module)

	def onApply(self, event):
		"""
		Apply the changes
		"""
		try:
			visualizationFrame = scripting.visualizer.getCurrentMode().getSidebarWindow()
			ambient = float(visualizationFrame.ambientEdit.GetValue())
			diffuse = float(visualizationFrame.diffuseEdit.GetValue())
			specular = float(visualizationFrame.specularEdit.GetValue())
			specularpwr = float(visualizationFrame.specularPowerEdit.GetValue())
			viewangle = int(visualizationFrame.angleEdit.GetValue())
		except:
			return

		self.module.setProperties(ambient, diffuse, specular, specularpwr, viewangle)
		
	def findModule(self):
		"""
		Refresh the modules affected by this configuration
		"""
		modules = self.visualizer.getCurrentMode().getModules()
		for module in modules:
			if module.getName() == self.name:
				self.setModule(module)
				return

	def setModule(self, module):
		"""
		Set the module to be configured
		"""  
		self.module = module
