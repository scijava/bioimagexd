# -*- coding: iso-8859-1 -*-

"""
 Unit: Animator
 Project: BioImageXD
 Created: 19.06.2005, KP
 Description:

 An animator mode for Visualizer
		  
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
__author__ = "BioImageXD Project <http://www.bioimagexd.org/>"
__version__ = "$Revision: 1.9 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import GUI.Urmas.UrmasWindow
import Logging
from GUI import MenuManager
from Visualizer.VisualizationMode import VisualizationMode
import wx

def getName():
	"""
	Description:Return the name of this visualization mode (used to identify mode internally)
	"""
	return "animator"

def getDesc():
	"""
	return a description (used as tooltips etc.) of this visualization mode
	"""
	return "Create an animation showing the dataset with the Animator"

def getShortDesc():
	"""
	return a short description (used as menu items etc.) of this visualization mode
	"""
	return "Animator"

def getIcon():
	"""
	return the icon name for this visualization mode
	"""
	return "task_animator.jpg"

def isDefaultMode():
	"""
	Return a boolean indicating whether this mode should be used as the default visualization mode
	"""
	return 0

def showInfoWindow():
	"""
	Return a boolean indicating whether the info window should be kept visible when this mode is loaded
	"""
	return 0

def showFileTree():
	"""
	Return a boolean indicating whether the file tree should be kept visible when this mode is loaded
	"""
	return 0    

def showSeparator():
	"""
	return two boolean values indicating whether to place toolbar separator before or after this icon
	"""
	return (1, 0)
	
# We want to be in the far right
def getToolbarPos():
	return 999
	
def getClass():
	"""
	return the class that is instantiated as the actual visualization mode
	"""
	return AnimatorMode

def getConfigPanel():
	"""
	return the class that is instantiated as the configuration panel for the mode
	"""
	return None

def getImmediateRendering():
	"""
	Return a boolean indicating whether this mode should in general update it's 
				 rendering after each and every change to a configuration affecting the rendering
	"""

	return False

def getRenderingDelay():
	"""
	return a value in milliseconds that is the minimum delay between two rendering events being sent
				 to this visualization mode. In general, the smaller the value, the faster the rendering should be
	"""
	return 10000

def showZoomToolbar():
	"""
	return a boolean indicating whether the visualizer toolbars (zoom, annotation) should be visible 
	"""
	return False

class AnimatorMode(VisualizationMode):

	def __init__(self, parent, visualizer):
		"""
		Method: __init__
		Initialization
		"""
		VisualizationMode.__init__(self, parent, visualizer)
		self.parent = parent
		self.menuManager = visualizer.menuManager
		self.visualizer = visualizer
		
		self.dataUnit = None
		
		self.urmaswin = None
		self.doLockSliderPanel = 0
		
	def layoutTwice(self):
		"""
		Method that is queried for whether the mode needs to
					 be laid out twice
		"""
		return True
		
	def closeOnReload(self):

		return True
		
	def showSideBar(self):
		"""
		Method that is queried to determine whether
					 to show the sidebar
		"""
		return False
		
	def relayout(self):
		"""
		Method called when the size of the window changes
		"""    
		#self.urmaswin.Layout()
		#wx.CallAfter(self.urmaswin.Layout)
		#wx.CallAfter(self.visualizer.OnSize)
		
	def activate(self, sidebarwin):
		"""
		Set the mode of visualization
		"""
		self.sidebarWin = sidebarwin
		Logging.info("Disabling tasks in menu", kw = "visualizer")
		self.menuManager.mainToolbar.EnableTool(MenuManager.ID_ADJUST, 0)
		self.menuManager.mainToolbar.EnableTool(MenuManager.ID_RESTORE, 0)
		self.menuManager.mainToolbar.EnableTool(MenuManager.ID_COLOCALIZATION, 0)
		self.menuManager.mainToolbar.EnableTool(MenuManager.ID_COLORMERGING, 0)
		self.visualizer.sliderPanel.Show(0)
		self.origSliderWinSize = self.visualizer.sliderWin.GetSize()
		self.visualizer.sliderWin.SetDefaultSize((-1, 64))
		
		if not self.urmaswin:
			self.urmaswin = GUI.Urmas.UrmasWindow.UrmasWindow(self.parent, \
																self.visualizer.menuManager, \
																self.visualizer.mainwin.taskWin, \
																self.visualizer)
			
		else:
			print "Restoring",self.urmaswin
			self.urmaswin.Show(1)
			self.parent.Show(1)
			self.urmaswin.enableRendering(1)
			self.urmaswin.controlpanel.Show(1)
			wx.CallAfter(self.urmaswin.updateRenderWindow)
			
		return self.urmaswin
		
	def Render(self):
		"""
		Update the rendering
		"""      
		pass        
		
	def setBackground(self, r, g, b):
		"""
		Set the background color
		"""        
		pass
		
	def updateRendering(self):
		"""
		Update the rendering
		"""      
		pass
		
	def lockSliderPanel(self, flag):
		"""
		Set a flag indicating whether the sliderpanel 
					 should be switched back to normal when switching
					 from animator
		"""     
		self.doLockSliderPanel = flag
		
	def deactivate(self, newmode = None):
		"""
		Unset the mode of visualization
		"""
		self.urmaswin.Show(0) 
		self.urmaswin.enableRendering(0)   
		self.urmaswin.controlpanel.Show(0)
		self.visualizer.sliderWin.SetDefaultSize(self.origSliderWinSize)

		if not self.doLockSliderPanel and newmode != "3d":
			print "\n\n*** DEACTIVATING ANIMATOR\n"
			self.visualizer.setCurrentSliderPanel(self.visualizer.sliderPanel)        
			self.visualizer.sliderPanel.Show(1)
		if newmode != "3d":
			self.menuManager.mainToolbar.EnableTool(MenuManager.ID_ADJUST, 1)
			self.menuManager.mainToolbar.EnableTool(MenuManager.ID_RESTORE, 1)
			self.menuManager.mainToolbar.EnableTool(MenuManager.ID_COLOCALIZATION, 1)
			self.menuManager.mainToolbar.EnableTool(MenuManager.ID_COLORMERGING, 1)        
		
	def setDataUnit(self, dataUnit):
		"""
		Set the dataunit to be visualized
		"""
		self.urmaswin.setDataUnit(dataUnit)
		
	def setTimepoint(self, tp):
		"""
		Set the timepoint to be visualized
		"""
		pass

	def saveSnapshot(self, filename):
		"""
		Save a snapshot of the scene
		"""      
		pass
		
	def reloadMode(self):
		"""
		Method called when the user tries to reload the mode
		"""    
		pass
