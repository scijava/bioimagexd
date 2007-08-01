# -*- coding: iso-8859-1 -*-

"""
 Unit: Info
 Project: BioImageXD
 Created: 05.0.2005, KP
 Description:

 A info mode for Visualizer
		   
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

from GUI.InfoWidget import InfoWidget
from GUI.TreeWidget import TreeWidget

def getName():
	return "info"

# Return None as the icon name to indicate we don't wish to appear in the toolbar
def getIcon():
	return None

def getDesc():
	return None

def getShortDesc():
	return "Dataset Info"

def getToolbarPos():
	return - 9999

def getClass():
	return InfoMode

def getConfigPanel():
	return None

def getImmediateRendering():
	return False

def getRenderingDelay():
	return 10000

def showZoomToolbar():
	return False
		
class InfoMode:

	def __init__(self, parent, visualizer):
		"""
		Method: __init__
		Created: 24.05.2005, KP
		Description: Initialization
		"""
		self.parent = parent
		self.menuManager = visualizer.menuManager
		self.visualizer = visualizer
		
		self.dataUnit = None
		self.modules = []
		
		self.infowidget = None
		self.tree = None
		
	def showSideBar(self):
		"""
		Method: showSideBar()
		Created: 24.05.2005, KP
		Description: Method that is queried to determine whether
					 to show the sidebar
		"""
		return True
		
	def activate(self, sidebarwin):
		"""
		Method: activate()
		Created: 24.05.2005, KP
		Description: Set the mode of visualization
		"""
		self.sidebarWin = sidebarwin
		
		
		if not self.infowidget:
			self.infowidget = InfoWidget(self.parent, size = (512, 512))
		

		if not self.tree:
			self.tree = TreeWidget(self.sidebarWin)
			#self.tree.SetSize(self.sidebarWin.GetSize())
			self.infowidget.setTree(self.tree)
			self.tree.Show()
		else:
			self.tree.Show()
			
		return self.infowidget
		
	def Render(self):
		"""
		Method: Render()
		Created: 24.05.2005, KP
		Description: Update the rendering
		"""      
		pass        
		
	def setBackground(self, r, g, b):
		"""
		Method: setBackground(r,g,b)
		Created: 24.05.2005, KP
		Description: Set the background color
		"""        
		pass
		
	def updateRendering(self):
		"""
		Method: updateRendering
		Created: 26.05.2005, KP
		Description: Update the rendering
		"""      
		pass
		
	def deactivate(self, newmode = None):
		"""
		Method: deactivate()
		Created: 24.05.2005, KP
		Description: Unset the mode of visualization
		"""
		self.infowidget.Show(0)       
		self.tree.Show(0)
		
	def setDataUnit(self, dataUnit):
		"""
		Method: setDataUnit
		Created: 25.05.2005, KP
		Description: Set the dataunit to be visualized
		"""
		
	def setTimepoint(self, tp):
		"""
		Method: setTimepoint
		Created: 25.05.2005, KP
		Description: Set the timepoint to be visualized
		"""
		#TODO: makes no sense, 19.7.2007 SS
		self.infowidget.preview.setTimepoint(tp)

	def saveSnapshot(self, filename):
		"""
		Method: saveSnapshot(filename)
		Created: 05.06.2005, KP
		Description: Save a snapshot of the scene
		"""      
		#TODO: makes no sense, 19.7.2007 SS
		self.infowidget.preview.saveSnapshot(filename)
