# -*- coding: iso-8859-1 -*-
"""
 Unit: Gallery
 Project: BioImageXD
 Created: 28.04.2005, KP
 Description:

 A gallery view for Visualizer
		  
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

from GUI.PreviewFrame.GalleryPanel import GalleryPanel
import Logging
import wx.lib.scrolledpanel as scrolled
from Visualizer.VisualizationMode import VisualizationMode
import wx
import scripting

def getName():
	"""
	Description:Return the name of this visualization mode (used to identify mode internally)
	"""
	return "gallery"

def isDefaultMode():
	"""
	Return a boolean indicating whether this mode should be used as the default visualization mode
	"""
	return 0

def getShortDesc():
	"""
	return a short description (used as menu items etc.) of this visualization mode
	"""
	return "Gallery mode"

def getDesc():
	"""
	return a description (used as tooltips etc.) of this visualization mode
	"""
	return "Show the dataset as a gallery of slices"

def getIcon():
	"""
	return the icon name for this visualization mode
	"""
	return "Vis_Gallery.png"

def getToolbarPos():
	return 1

def showInfoWindow():
	"""
	Return a boolean indicating whether the info window should be kept visible when this mode is loaded
	"""
	return 1

def showFileTree():
	"""
	Return a boolean indicating whether the file tree should be kept visible when this mode is loaded
	"""
	return 1 

def showSeparator():
	"""
	return two boolean values indicating whether to place toolbar separator before or after this icon
	"""
	return (0, 0) 

def getClass():
	"""
	return the class that is instantiated as the actual visualization mode
	"""
	return GalleryMode

def getImmediateRendering():
	"""
	Return a boolean indicating whether this mode should in general update it's 
				 rendering after each and every change to a configuration affecting the rendering
	"""
	return False

def getConfigPanel():
	"""
	return the class that is instantiated as the configuration panel for the mode
	"""
	return None

def getRenderingDelay():
	"""
	return a value in milliseconds that is the minimum delay between two rendering events being sent
				 to this visualization mode. In general, the smaller the value, the faster the rendering should be
	"""
	return 2000

def showZoomToolbar():
	"""
	return a boolean indicating whether the visualizer toolbars (zoom, annotation) should be visible 
	"""
	return True
	
class GalleryConfigurationPanel(scrolled.ScrolledPanel):
	"""
	A configuration panel for the gallery view
	"""
	def __init__(self, parent, visualizer, mode, **kws):
		"""
		Initialization
		"""
		scrolled.ScrolledPanel.__init__(self, parent, -1, size = (100, 500))
		self.visualizer = visualizer
		self.mode = mode	

		self.sizer = wx.GridBagSizer()
		self.radiobox = wx.RadioBox(self, -1, "View in gallery", \
									choices = ["Slices", "Timepoints"], \
									majorDimension = 1, \
									style = wx.RA_SPECIFY_COLS)

		self.okbutton = wx.Button(self, -1, "Update")
		self.okbutton.Bind(wx.EVT_BUTTON, self.onSetViewMode)
		self.sizer.Add(self.radiobox, (0, 0))
		self.sizer.Add(self.okbutton, (2, 0))
		
		self.SetSizer(self.sizer)
		self.SetAutoLayout(1)
		self.SetupScrolling()

		
	def setDataUnit(self, dataUnit):
		"""
		Set the dataunit
		"""
		x, y, z = dataUnit.getDimensions()
		
	def onSetViewMode(self, event):
		"""
		Configure whether to show timepoints or slices
		"""
		pos = self.radiobox.GetSelection()
		if pos == 0:
			val = self.visualizer.zslider.GetValue()
		else:
			val = self.visualizer.getTimepoint()
		self.mode.galleryPanel.setShowTimepoints(pos, val)

		
class GalleryMode(VisualizationMode):

	def __init__(self, parent, visualizer):
		"""
		Initialization
		"""
		VisualizationMode.__init__(self, parent, visualizer)
		self.galleryPanel = None
		self.configPanel = None
		
	def updateRendering(self):
		"""
		Update the rendering
		"""
		if not self.enabled:
			Logging.info("Visualizer is disabled, won't update gallery", kw = "visualizer")
			return
		Logging.info("Updating gallery", kw = "visualizer")

		self.galleryPanel.forceUpdate()

	def showSliceSlider(self):
		"""
		Method that is queried to determine whether to show the zslider
		"""
		return True
		
	def showSideBar(self):
		"""
		Method that is queried to determine whether
					 to show the sidebar
		"""
		return True

	def getSidebarWinOrigSize(self):
		"""
		Return default size of sidebar win
		"""
		return (100,500)

	def activate(self, sidebarwin):
		"""
		Set the mode of visualization
		"""
		scripting.wantWholeDataset = 0
		self.sidebarWin = sidebarwin

		x, y = self.visualizer.visWin.GetSize()
		if not self.galleryPanel:
			self.galleryPanel = GalleryPanel(self.parent, self.visualizer, size = (x, y))
			self.iactivePanel = self.galleryPanel

		if not self.configPanel:
			# When we embed the sidebar in a sashlayoutwindow, the size
			# is set correctly
			self.container = wx.SashLayoutWindow(self.sidebarWin)

			self.configPanel = GalleryConfigurationPanel(self.container, self.visualizer, self, size = (x, y))
			if self.dataUnit:
				self.configPanel.setDataUnit(self.dataUnit)
			self.configPanel.Show()
		else:
			self.configPanel.Show()
			self.container.Show()

		return self.galleryPanel
		

	def setDataUnit(self, dataUnit):
		"""
		Set the dataunit to be visualized
		"""
		VisualizationMode.setDataUnit(self, dataUnit)
		if self.configPanel:
			self.configPanel.setDataUnit(dataUnit)
		
	def deactivate(self, newmode = None):
		"""
		Unset the mode of visualization
		"""
		self.container.Show(0)
		self.configPanel.Show(0)
		VisualizationMode.deactivate(self, newmode)
		self.configPanel.Destroy()
