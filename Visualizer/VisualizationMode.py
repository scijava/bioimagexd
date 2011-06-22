# -*- coding: iso-8859-1 -*-

"""
 Unit: VisualizationMode
 Project: BioImageXD
 Description:

 A module that contains the base class for various view modes
		  
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
 Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111 - 1307  USA
"""
__author__ = "BioImageXD Project"
__version__ = "$Revision: 1.9 $"
__date__ = "$Date: 2005 / 01 / 13 13: 42: 03 $"

import lib.DataUnit.DataUnitSetting


class VisualizationMode:
	"""
	A class representing a visualization mode
	"""
	def __init__(self, parent, visualizer, **kws):
		"""
		Initialization
		"""    
		self.parent = parent
		self.dataUnit = None
		self.enabled = 1
		self.iactivePanel = None
		self.timepoint = 0

		self.visualizer = visualizer
		
	def getRenderWindow(self):
		"""
		return a render window, if this mode uses one
		"""
		return None
   
	def layoutTwice(self):
		"""
		Method that is queried for whether the mode needs to
					 be laid out twice
		"""
		return False
		
	def annotate(self, annclass, **kws):
		"""
		Add an annotation to the scene
		"""
		if self.iactivePanel:
			self.iactivePanel.addAnnotation(annclass, **kws)
		
	def manageAnnotation(self):
		"""
		Manage annotations on the scene
		"""
		if self.iactivePanel:
			self.iactivePanel.manageAnnotation()

	def deleteAnnotation(self):
		"""
		Delete annotations on the scene
		"""
		if self.iactivePanel:
			self.iactivePanel.deleteAnnotation()
			
	def zoomObject(self):
		"""
		Zoom to a user selected portion of the image
		"""
		if self.iactivePanel:
			self.iactivePanel.startRubberband()
			
		
	def zoomToFit(self):
		"""
		Zoom the dataset to fit the available screen space
		"""
		if self.iactivePanel:
			self.iactivePanel.zoomToFit()
			
	
	def setZoomFactor(self, factor):
		"""
		Set the factor by which the image is zoomed
		"""
		if self.iactivePanel:
			self.iactivePanel.setZoomFactor(factor)  
			
	def getZoomFactor(self):
		"""
		Get the zoom factor
		"""
		if self.iactivePanel:
			return self.iactivePanel.getZoomFactor()   
		return 1.0
			
	def showSideBar(self):
		"""
		Method that is queried to determine whether
					 to show the sidebar
		"""
		return False

	def getSidebarWinOrigSize(self):
		"""
		Return default size of sidebar win
		"""
		return (200,500)
		
	def showSliceSlider(self):
		"""
		Method that is queried to determine whether
					 to show the zslider
		"""
		return False

	def showTimeSlider(self):
		"""
		Method that is queried to determine whether to show time slider
		"""
		return True
   
	def showViewAngleCombo(self):
		"""
		Method that is queried to determine whether
					 to show the view angle combo box in the toolbar
		"""
		return False  
		
	def closeOnReload(self):
		"""
		Method to determine whether the visualization mode
					 should be closed if the user clicks it again.
		"""    
		return False
  
	def setBackground(self, red, green, blue):
		"""
		Set the background color
		"""		   
		self.iactivePanel.setBackground(red, green, blue)

	def setDataUnit(self, dataunit):
		"""
		Sets the dataunit this module uses for visualization
		"""			   
		self.dataUnit = dataunit
		if dataunit and not dataunit.getSettings():
			settings = lib.DataUnit.DataUnitSetting.DataUnitSettings()
			dataunit.setSettings(settings)		  
		if self.iactivePanel:
			self.iactivePanel.setDataUnit(dataunit)
		
	def getDataUnit(self):
		"""
		Returns the dataunit this module uses for visualization
		"""		
		return self.dataUnit
		
	def setTimepoint(self, timepoint):
		"""
		Set the timepoint to be visualized
		"""
		self.timepoint = timepoint
		self.iactivePanel.setTimepoint(timepoint)

	def saveSnapshot(self, filename):
		"""
		Save a snapshot of the scene
		@param filename  The name of the image file to be written
		"""
		self.iactivePanel.saveSnapshot(filename)
		
	def deactivate(self, newmode = None):
		"""
		De-activate the visualization mode, hiding it's contents
		"""
		self.iactivePanel.Show(0)
		if hasattr(self.iactivePanel, "onDeactivate"):
			self.iactivePanel.onDeactivate() 
		self.iactivePanel.Destroy()
		del self.iactivePanel
		self.iactivePanel = None
	def relayout(self):
		"""
		Method called when the size of the window changes
		"""    
		pass
		
	def reloadMode(self):
		"""
		Method called when the user tries to reload the mode
		"""    
		pass
