# -*- coding: iso-8859-1 -*-
"""
 Unit: Simple
 Project: BioImageXD
 Created: 28.04.2005, KP
 Description:

 A view for Visualizer that shows a simple preview of the data
		  
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

import Logging
from Visualizer.VisualizationMode import VisualizationMode
from GUI.PreviewFrame.PreviewFrame import PreviewFrame
import scripting

def getName():
	return "MIP"

def isDefaultMode():
	return 0

def showInfoWindow():
	return 1

def showFileTree():
	return 1

def showSeparator():
	return (0, 0)

def getToolbarPos():
	return 5

def getIcon():
	return "view_rendering.jpg"

def getShortDesc():
	return "Maximum Intensity Projection"

def getDesc():
	return "Create a Maximum Intensity Projection of the dataset"

def getClass():
	return SimpleMode

def getImmediateRendering():
	return False

def getConfigPanel():
	return None

def getRenderingDelay():
	return 1500

def showZoomToolbar():
	return True
	
class SimpleMode(VisualizationMode):

	def __init__(self, parent, visualizer):
		"""
		Created: 24.05.2005, KP
		Description: Initialization
		"""
		VisualizationMode.__init__(self, parent, visualizer)        
		self.parent = parent
		self.visualizer = visualizer
		self.iactivePanel = None
		self.init = 1
		self.dataUnit = None
		
	def showSideBar(self):
		"""
		Created: 24.05.2005, KP
		Description: Method that is queried to determine whether
					 to show the sidebar
		"""
		return False
		
	def Render(self):
		"""
		Created: 24.05.2005, KP
		Description: Update the rendering
		"""      
		self.iactivePanel.updatePreview(0)
		
	def updateRendering(self):
		"""
		Created: 26.05.2005, KP
		Description: Update the rendering
		"""
		Logging.info("Updating rendering", kw = "preview")
		self.iactivePanel.updatePreview(1)
		
	def setBackground(self, r, g, b):
		"""
		Created: 24.05.2005, KP
		Description: Set the background color
		"""      
		if self.iactivePanel:
			self.iactivePanel.setBackgroundColor((r, g, b))

	def activate(self, sidebarwin):
		"""
		Created: 24.05.2005, KP
		Description: Set the mode of visualization
		"""
		scripting.wantWholeDataset = 1

		if not self.iactivePanel:
			Logging.info("Generating preview", kw = "visualizer")
			self.iactivePanel = PreviewFrame(self.parent)
			self.iactivePanel.setPreviewType("MIP")
		return self.iactivePanel
		
	def setDataUnit(self, dataUnit):
		"""
		Created: 25.05.2005, KP
		Description: Set the dataunit to be visualized
		"""
		Logging.info("setDataUnit(", dataUnit, ")", kw = "visualizer")
		if dataUnit == self.dataUnit:
			Logging.info("Same dataunit, not changing", kw = "visualizer")
			return
		if self.init:
			self.iactivePanel.setPreviewType("")
			self.init = 0
			
		self.iactivePanel.setDataUnit(dataUnit, 0)
		
	def setTimepoint(self, tp):
		"""
		Created: 25.05.2005, KP
		Description: Set the timepoint to be visualized
		"""
		Logging.info("Setting timepoint to ", tp, kw = "visualizer")
		self.iactivePanel.setTimepoint(tp)
		
	def deactivate(self, newmode = None):
		"""
		Created: 24.05.2005, KP
		Description: Unset the mode of visualization
		"""
		self.iactivePanel.Show(0)
		self.iactivePanel.onDeactivate()        
		del self.iactivePanel
		self.iactivePanel = None
		
	def saveSnapshot(self, filename):
		"""
		Created: 05.06.2005, KP
		Description: Save a snapshot of the scene
		"""      
		self.iactivePanel.saveSnapshot(filename)
		
		
