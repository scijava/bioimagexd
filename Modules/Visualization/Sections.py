# -*- coding: iso-8859-1 -*-

"""
 Unit: Sections
 Project: BioImageXD
 Created: 28.04.2005, KP
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
	return "sections"

def isDefaultMode():
	return 0    

def showInfoWindow():
	return 1

def showFileTree():
	return 1

def showSeparator():
	return (0, 0)

def getToolbarPos():
	return 3

def getIcon():
	return "view_sections.jpg"

def getShortDesc():
	return "Orthographic view"

def getDesc():
	return "Display three orthographic sections of the dataset"    

def getClass():
	return SectionsMode

def getImmediateRendering():
	return False

def getConfigPanel():
	return None

def getRenderingDelay():
	return 500

def showZoomToolbar():
	return True    
		
class SectionsMode(VisualizationMode):

	def __init__(self, parent, visualizer):
		"""
		Created: 24.05.2005, KP
		Description: Initialization
		"""
		VisualizationMode.__init__(self, parent, visualizer)
		self.sectionsPanel = None
		
	def updateRendering(self):
		"""
		Created: 26.05.2005, KP
		Description: Update the rendering
		"""      
		self.sectionsPanel.setTimepoint(self.timepoint)
		self.sectionsPanel.updatePreview()
		self.sectionsPanel.Refresh()
		
	def showSliceSlider(self):
		"""
		Created: 07.08.2005, KP
		Description: Method that is queried to determine whether
					 to show the zslider
		"""
		return True
		
	def showSideBar(self):
		"""
		Created: 24.05.2005, KP
		Description: Method that is queried to determine whether
					 to show the sidebar
		"""
		return False
  
	def activate(self, sidebarwin):
		"""
		Created: 24.05.2005, KP
		Description: Set the mode of visualization
		"""
		scripting.wantWholeDataset = 1

		if not self.sectionsPanel:
			x, y = self.visualizer.visWin.GetSize()
			self.sectionsPanel = SectionsPanel(self.parent, self.visualizer, size = (x, y))
			self.iactivePanel = self.sectionsPanel
		return self.sectionsPanel
