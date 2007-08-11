#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: FilterBasedTaskPanel
 Project: BioImageXD
 Created: 10.04.2005, KP
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

#import wx

#import os.path
#import Dialogs

#import GUI.PreviewFrame
#import Logging

#import sys
#import time

import TaskPanel
#import UIElements
#import string
#import scripting
import types
#import Command

class FilterBasedTaskPanel(TaskPanel.TaskPanel):
	"""
	Created: 14.08.2006, KP
	Description: A window for restoring a single dataunit
	"""
	def __init__(self, parent, tb, wantNotebook = 1):
		"""
		Created: 14.08.2006, KP
		Description: Initialization
		Parameters:
				root    Is the parent widget of this window
		"""
		TaskPanel.TaskPanel.__init__(self, parent, tb, wantNotebook = wantNotebook)

		self.filters = []
		self.currentSelected = -1
		

		self.filtersByCategory = {}
		self.filtersByName = {}
		self.categories = []

		for currfilter in self.filtersModule.getFilterList():
			self.filtersByName[currfilter.getName()] = currfilter
			self.registerFilter(currfilter.getCategory(), currfilter)
	  
		
	def filterModified(self, filter):
		"""
		Created: 14.05.2006, KP
		Description: A callback for when filter parameters change
		"""
		self.setModified(1)
		
	def setModified(self, flag):
		"""
		Created: 14.05.2006, KP
		Description: A callback for when filter parameters change
		"""
		self.dataUnit.module.setModified(1)

	def registerFilter(self, category, currfilter):
		"""
		Created: 14.08.2006, KP
		Description: Creates a button box containing the buttons Render,
		"""
		if category not in self.categories:
			self.categories.append(category)
		if not category in self.filtersByCategory:
			self.filtersByCategory[category] = []
		self.filtersByCategory[category].append(currfilter)
		  

	def getFilters(self, name):
		"""
		Created: 21.07.2006, KP
		Description: Retrieve the filters with the given name
		"""   
		print "FILTERS NOW=",self.filters
		print "requesting",name
		print [x.getName() for x in self.filters]
		
		func = lambda f, n = name:f.getName() == n
		return filter(func, self.filters)
		
	def getFilter(self, name, index = 0):
		"""
		Created: 21.07.2006, KP
		Description: Retrieve the filter with the given name, using optionally an index 
					 if there are more than one filter with the same name
		"""   
		return self.getFilters(name)[index]
		
 
	def setFilter(self, status, index = -1, name = ""):
		"""
		Created: 21.07.2006, KP
		Description: Set the status of a given filter by either it's index, or
					 if index is not given, it's name
		"""        
		if index == -1:
			for i in self.filters:
				if i.getName() == name:
					index = i
					break
		if index == -1:return False
		self.filters[index].setEnabled(status)
		self.setModified(1)
		
	def updateSettings(self, force = 0):
		"""
		Created: 14.08.2006, KP
		Description: A method used to set the GUI widgets to their proper values
		"""
		if not force:
			self.settings.set("FilterList", [])
			return
		if self.dataUnit:
			get = self.settings.get
			set = self.settings.set
		flist = self.settings.get("FilterList")
		
		if flist and len(flist):
			
			if type(flist[0]) == types.ClassType:
				for i in flist:
					print "Adding filter of class", i
					self.addFilter(None, i)
			for currfilter in self.filters:
				name = currfilter.getName()
				#parser = self.dataUnit.getParser()    
				parser = self.dataUnit.parser
				
				if parser:
					items = parser.items(name)
					
					for item, value in items:            
						#value=parser.get(name,item)
						print "Setting", item, "to", value
						value = eval(value)
						currfilter.setParameter(item, value)
					currfilter.sendUpdateGUI()
					self.parser = None
				
	def updateFilterData(self):
		"""
		Created: 13.12.2004, JV
		Description: A method used to set the right values in dataset
					 from filter GUI widgets
		"""
		print "Setting filterlist to", self.filters
		self.settings.set("FilterList", self.filters)
		
	def doProcessingCallback(self, *args):
		"""
		Created: 14.08.2006, KP
		Description: A callback for the button "Manipulation Dataset Series"
		"""
		self.updateFilterData()
		TaskPanel.TaskPanel.doOperation(self)

	def doPreviewCallback(self, event = None, *args):
		"""
		Created: 14.08.2006, KP
		Description: A callback for the button "Preview" and other events
					 that wish to update the preview
		"""
		self.updateFilterData()
		TaskPanel.TaskPanel.doPreviewCallback(self, event)
