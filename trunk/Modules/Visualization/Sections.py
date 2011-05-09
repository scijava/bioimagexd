# -*- coding: iso-8859-1 -*-

"""
 Unit: Sections
 Project: BioImageXD
 Description:

 A visualization mode for Visualizer that shows the xy- xz, and yz- planes
 of the data.
 
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

import scripting
from GUI.PreviewFrame.SectionsPanel import SectionsPanel
from Visualizer.VisualizationMode import VisualizationMode

def getName():
	"""
	Description:Return the name of this visualization mode (used to identify mode internally)
	"""
	return "sections"

def isDefaultMode():
	"""
	Return a boolean indicating whether this mode should be used as the default visualization mode
	"""
	return 0    

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

def getToolbarPos():
	return 3

def getIcon():
	"""
	return the icon name for this visualization mode
	"""
	return "Vis_Ortho.png"

def getShortDesc():
	"""
	return a short description (used as menu items etc.) of this visualization mode
	"""
	return "Orthogonal mode"

def getDesc():
	"""
	return a description (used as tooltips etc.) of this visualization mode
	"""
	return "Display three orthogonal sections of the dataset"    

def getClass():
	"""
	return the class that is instantiated as the actual visualization mode
	"""
	return SectionsMode

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
	return 500

def showZoomToolbar():
	"""
	return a boolean indicating whether the visualizer toolbars (zoom, annotation) should be visible 
	"""
	return True    
		
class SectionsMode(VisualizationMode):

	def __init__(self, parent, visualizer):
		"""
		Initialization
		"""
		VisualizationMode.__init__(self, parent, visualizer)
		self.iactivePanel = None
		
	def updateRendering(self):
		"""
		Update the rendering
		"""      
		if self.iactivePanel:
			self.iactivePanel.setTimepoint(self.timepoint)
			self.iactivePanel.updatePreview()
			self.iactivePanel.Refresh()
		
	def showSliceSlider(self):
		"""
		Method that is queried to determine whether
					 to show the zslider
		"""
		return True
		
	def showSideBar(self):
		"""
		Method that is queried to determine whether
					 to show the sidebar
		"""
		return False
	
	def setDataUnit(self, dataUnit):
		"""
		Set the dataunit to be visualized
		"""
		self.iactivePanel.setDataUnit(dataUnit, 0)
		
	def activate(self, sidebarwin):
		"""
		Set the mode of visualization
		"""
		scripting.wantWholeDataset = 1

		if not self.iactivePanel:
			x, y = self.visualizer.visWin.GetSize()
			self.iactivePanel = SectionsPanel(self.parent, self.visualizer, size = (x, y))
		return self.iactivePanel
