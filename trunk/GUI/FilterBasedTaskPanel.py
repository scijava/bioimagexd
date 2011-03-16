#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: FilterBasedTaskPanel
 Project: BioImageXD
 Description:

 A base class for task panels that is based on using a chain of filters to process the data
							
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
__version__ = "$Revision: 1.42 $"
__date__ = "$Date: 2005/01/13 14:52:39 $"


import TaskPanel
import types
import lib.FilterBasedModule

class FilterBasedTaskPanel(TaskPanel.TaskPanel):
	"""
	A window for restoring a single dataunit
	"""
	def __init__(self, parent, tb, wantNotebook = 1):
		"""
		Initialization
		@param parent    Is the parent widget of this window
		"""
		self.filterEditor = None
		TaskPanel.TaskPanel.__init__(self, parent, tb, wantNotebook = wantNotebook)

		self.filterList = lib.FilterBasedModule.FilterList(self.filtersModule)
		self.currentSelected = -1

	def filterModified(self, filter):
		"""
		A callback for when filter parameters change
		"""
		if self.filterEditor:
			self.filterEditor.setModified(1)
		  
	def updateSettings(self, force = 0):
		"""
		A method used to set the GUI widgets to their proper values
		"""
		self.filterList = self.settings.get("FilterList")
		
		if self.filterList:
			if self.cacheParser:
				parser = self.cacheParser
				cached = 1
			else:
				parser = self.settings.parser

			self.filterList.setDataUnit(self.dataUnit)
			self.filterList.readValuesFrom(parser)
			self.parser = None
			self.filterEditor.setFilterList(self.filterList)
			self.filterEditor.updateFromFilterList()
				
	def updateFilterData(self):
		"""
		A method used to set the right values in dataset
					 from filter GUI widgets
		"""
		self.dataUnit.getSettings().set("FilterList", self.filterList)
		
	def doProcessingCallback(self, *args):
		"""
		A callback for the button "Manipulation Dataset Series"
		"""
		self.updateFilterData()
		TaskPanel.TaskPanel.doOperation(self)

	def doPreviewCallback(self, event = None, *args):
		"""
		A callback for the button "Preview" and other events
					 that wish to update the preview
		"""
		self.updateFilterData()
		TaskPanel.TaskPanel.doPreviewCallback(self, event)

	def removeFilters(self):
		"""
		Remove filters from settings
		"""
		filtNum = len(self.filterList.getFilters())
		for i in range(filtNum-1,-1,-1):
			self.filterList.removeFilter(i)

