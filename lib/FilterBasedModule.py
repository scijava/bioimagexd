# -*- coding: iso-8859-1 -*-
"""
 Unit: FilterBasedModule
 Project: BioImageXD
 
 Description:
 A module that functions by taking a stack of filters and applying it to the input images

 Copyright (C) 2005	 BioImageXD Project
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
__version__ = "$Revision: 1.13 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import Logging
import lib.Module
import ConfigParser
import Modules.DynamicLoader
import traceback
import vtk
import scripting
import optimize
import types

class FilterList:
	"""
	Description: a model of a filter list that is manipulated by the filter list editor
	"""
	def __init__(self, filtersModule = None):
		# We load up the process task module to get access to the filters
		# in the future, when all the filters have been transformed into separate files
		# we can just use the dynamic loader directly
		pluginLoader = Modules.DynamicLoader.getPluginLoader()
		taskMod = pluginLoader.getPluginModule("Task", "Process")
		filtersMod = taskMod.getFilterModule()
		if not filtersModule:
			filtersModule = filtersMod
		self.filtersByCategory = {}
		self.filtersByName = {}
		self.clear()
		allFilters = filtersModule.getFilterList()
		addedFilters = Modules.DynamicLoader.getFilterModules()
		allFilters += [x[0] for x in addedFilters.values()]
		for currfilter in allFilters:
			self.filtersByName[currfilter.getName()] = currfilter
			self.registerFilter(currfilter.getCategory(), currfilter)
			
	def getResultVariable(self, var, nth = 0, tp = None):
		"""
		return the value of a result variable
		"""
		i = 0
		for f in self.filters:
			if var in f.getResultVariables() and i == nth:
				return f.getResultVariable(var, tp)
			elif var in f.getResultVariables():
				i += 1
			
	def clear(self):
		"""
		clear the filter list
		"""
		self.categories = []
		self.filters = []
		self.currentSelected = -1
		self.dataUnit = None
		self.modified = 0
			
	def addFilter(self, filter):
		"""
		add a filter to the list
		"""
		self.filters.append(filter)
		filter.setDataUnit(self.dataUnit)
		self.setModified(1)

	def setDataUnit(self, dataUnit, initializeFilters = 1):
		"""
		set the dataunit 
		"""
		self.dataUnit = dataUnit
		self.modified = 1
		print "filters = ",self.filters
		for f in self.filters:
			if not initializeFilters:
				f.setInitialization(0)
			f.setDataUnit(dataUnit)
			f.setInitialization(1)
			
	def populate(self, filterNames):
		"""
		populate the filter list from a string
		"""
		filterList = []
		nameToFilter = {}

		for name in filterNames:
			try:
				filterclass = self.filtersByName[name]
				addfilter = filterclass()
				addfilter.setDataUnit(self.dataUnit)
				filterList.append(addfilter)
			except Exception, ex:
				print "\n\nFAILED TO LOAD FILTER",ex
				traceback.print_exc()
		self.filters = filterList
		self.setModified(1)
		
	def writeOut(self, parser, prefix = ""):
		"""
		Write the filter list out to a configuration parser object
		"""
		if not parser.has_section("%sFilterList"%prefix):
			parser.add_section("%sFilterList"%prefix)
		
		filterNames = self.getFilterNames()
		parser.set("%sFilterList"%prefix,"FilterList",str(filterNames))
		counts = {}

		for i, filterName in enumerate(filterNames):
			currfilter = self.filters[i]
			keys = currfilter.getPlainParameters()
			sectionName = prefix + filterName
			
			if filterNames.count(filterName) > 1:
				filterIndex = counts.get(filterName, 0)
				sectionName="%s#%d"%(sectionName, filterIndex)
				counts[filterName] = filterIndex+1
				
			if not parser.has_section(sectionName):
				parser.add_section(sectionName)

			skipNextNItems = 0
			for key in keys:
				if skipNextNItems:
					skipNextNItems -= 1
					continue
				if key == 'cols' or key == 'rows': # Don't save RADIO_CHOICE GUI info
					skipNextNItems = 1
					continue
				parser.set(sectionName, key, currfilter.getParameter(key))

			parser.set(sectionName,"Enabled", str(currfilter.getEnabled()))
			parser.set(sectionName, "InputMapping", str(currfilter.inputMapping))
		
		
	def readValuesFrom(self, parser, prefix = ""):
		"""
		read the values for the parameters of the filters in this filterlist from a parser object
		"""
		self.setModified(1)
		filterNames = [x.getName() for x in self.filters]
		counts = {}
		# Loop through each of the filter instances
		# when we're restoring from presets or BBA file, the instances of the filters have already
		# been created and we now set the filters' parameters
		for currfilter in self.filters:
			name = currfilter.getName()
			sectionName = prefix+name
			# We calculate the name of the section in which the settings are stored in the file
			# If there are more than one same filter in the procedure list, then the section name
			# has an appended index behind the filter name, otherwise it's just the filter name
			if filterNames.count(name) > 1:
				filterIndex = counts.get(name, 0)
				sectionName = "%s#%d"%(sectionName, filterIndex)
				counts[name] = filterIndex+1
				
			if parser:
				# Get the items in the section. If it's empty, then just continue with the next filter
				try:
					items = parser.items(sectionName)
				except ConfigParser.NoSectionError:
					continue
				# In the item, value pair, item is the name of the parameter and value is it's value
				for item, value in items:
					try:
						newvalue = eval(value)
					except:
						newvalue = value
					currfilter.setParameter(item, newvalue)
				
				# We also restore the input mapping (meaning which dataunit is used as an input to the filter)
				# if there is one in the file
				if parser.has_option(sectionName, "InputMapping"):
					inputMapping = parser.get(sectionName, "InputMapping")
					currfilter.inputMapping = eval(inputMapping)
				# Update the GUI values
				currfilter.sendUpdateGUI()
				
	def getCount(self):
		"""
		return the number of filters in the filter list
		"""
		return len(self.filters)
			
	def getCategories(self):
		"""
		return the categories of the different filters
		"""
		return self.categories
		
	def getFiltersInCategory(self, category):
		"""
		return the filters in a given category
		"""
		return self.filtersByCategory.get(category, [])

	def getClassForName(self, name):
		"""
		return the a class corresponding to the given filter name
		"""
		return self.filtersByName.get(name, None)

	def removeFilter(self, index):
		"""
		remove the filter at the given index
		"""
		self.filters[index].onRemove()
		del self.filters[index]
		self.setModified(1)
		
	def setModified(self, status):
		"""
		set a status flag indicating whether the list has been modified
		"""
		self.modified = bool(status)
			
	def getModified(self):
		"""
		return the status of this filter list
		"""
		return self.modified

	def getFilter(self, index):
		"""
		return the filter at the given index
		"""
		return self.filters[index]
	
	def getFiltersWithName(self, name):
		"""
		return the filter with the given name
		"""
		ret = []
		for i in self.filters:
			if i.getName() == name:
				ret.append(i)
		return ret
		
	def getIndexForName(self, name):
		"""
		return the index of the filter corresponding to the given name
		"""
		index = -1
		for i, currFilter in enumerate(self.filters):
			if currFilter.getName() == name:
				index = i
				break
		return index
		

	def registerFilter(self, category, currfilter):
		"""
		Register a filter in a given category
		"""
		if category not in self.categories:
			self.categories.append(category)
		if not category in self.filtersByCategory:
			self.filtersByCategory[category] = []
		self.filtersByCategory[category].append(currfilter)
		
	def moveDown(self, index):
		"""
		move a filter down
		"""
		self.filters[index + 1], self.filters[index] = self.filters[index], self.filters[index + 1]
		self.setModified(1)
		
	def moveUp(self, index):
		"""
		move a filter at given index up in the list
		"""
		self.filters[index - 1], self.filters[index] = self.filters[index], self.filters[index - 1]
		self.setModified(1)
		
	def getEnabledFilters(self):
		"""
		return the enabled filters
		"""
		return [filterModule for filterModule in self.filters if filterModule.getEnabled()]
		
	def getFilters(self):
		"""
		get the list of filters
		"""
		return self.filters
		
	def getFilterNames(self):
		"""
		return the filter names
		"""
		return [x.getName() for x in self.filters]
		
	def setEnabled(self, index, status):
		"""
		set the status of a given filter
		"""
		if status:
			self.filters[index].onEnable()
		else:
			self.filters[index].onDisable()
		self.filters[index].setEnabled(status)
		self.setModified(1)
		
		
class FilterBasedModule(lib.Module.Module):
	"""
	Description: Applies a stack of processing filters to a given input dataset
	"""
	def __init__(self, **kws):
		"""
		Initialization
		"""
		lib.Module.Module.__init__(self, **kws)

		self.cached = None
		self.cachedTimepoint = -1
		self.depth = 8
		self.extent = None
		self.images = []
		self.preview = None
		self.running = 0
		self.settings = None
		self.reset()
		self.currentExecutingFilter = None
		self.polyDataOutput = None
		self.cacheDataUnits = {}
		self.cacheDataUnitsEnabled = True
		lib.messenger.connect(None, "clear_cache_dataunits", self.clearCacheDataUnits)
		lib.messenger.connect(None, "enable_dataunits_cache", self.enableDataUnitsCache)
		
	def setPolyDataOutput(self, polydata):
		"""
		Set the polydata output of this module
		"""
		self.polyDataOutput = polydata
		
	def getPolyDataOutput(self):
		"""
		Return the polydata output
		"""
		return self.polyDataOutput

	def getEventDesc(self):
		"""
		Get the event description. More complex modules can overwrite this for
					 more dynamic descriptions
		"""
		if self.currentExecutingFilter:
			return self.currentExecutingFilter.getEventDesc()
		else:
			return self.eventDesc
			
	def reset(self):
		"""
		Resets the module to initial state. This method is
					 used mainly when doing previews, when the parameters
					 that control the processing are changed and the
					 preview data becomes invalid.
		"""
		lib.Module.Module.reset(self)
		del self.cached
		self.cached = None 
		self.cachedTimepoint = -1

	def addInput(self, dataunit, data): #TODO: test
		"""
		Adds an input for the single dataunit Manipulationing filter
		"""
		lib.Module.Module.addInput(self, dataunit, data)
		self.settings = dataunit.getSettings()

	def getPreview(self, depth):
		"""
		Does a preview calculation for the x-y plane at depth depth
		"""
		if self.settings and self.settings.get("ShowOriginal"):
			Logging.info("Returning original data", kw="dataunit")
			return self.images[0] 
		if self.settings:
			filterlist = self.settings.get("FilterList")
			if not filterlist:
				modified = 0
			else:
				modified = filterlist.getModified()
		if self.timepoint != self.cachedTimepoint:
			modified = 1
		if not self.preview or modified:
			self.cachedTimepoint = self.timepoint
			dims = self.images[0].GetDimensions()
			if depth >= 0:
				self.extent = (0, dims[0]-1, 0, dims[1]-1, depth, depth)
			else:
				self.extent = None
			Logging.info("Creating preview with ext %s"%str(self.extent), kw="dataunit")
			self.preview = self.doOperation(preview=1)
			self.extent = None
		else:
			Logging.info("Modified = %s so returning old preview"%str(bool(modified)), kw="dataunit")
		return self.preview

	def doOperation(self, preview=0):
		"""
		Manipulationes the dataset in specified ways
		"""
		filterlist = self.settings.get("FilterList")
		if filterlist:
			modified = filterlist.getModified()
		else:
			modified = 0
		
		if preview and not modified and self.cached and self.timepoint == self.cachedTimepoint:
			Logging.info("--> Returning cached data, timepoint=%d, cached timepoint=%d" % 
				(self.timepoint, self.cachedTimepoint), kw = "pipeline")
			return self.cached
		else:
			del self.cached
			self.cached = None
	
		Logging.info("Creating preview, filters = %s"%str(filterlist), kw="pipeline")

		data = self.images
		if not filterlist or type(filterlist) == types.ListType or filterlist.getCount() == 0:
			Logging.info("No filters, returning original dat", kw="pipeline")
			return self.images[0]
		
		try:
			enabledFilters = filterlist.getEnabledFilters() 
		except AttributeError:
			enabledFilters = []
		highestFilterIndex = len(enabledFilters)-1
		
		lastfilter = None
		wantWhole = False
		polydata = None
		x = 1.0/(1+len(enabledFilters))

		# A very specific cache is needed, to prevent the "result" channel
		# being re-processed when being merged to the "original" channel(s).
		key = (self.settings.dataunit, self.timepoint)
		if key in self.cacheDataUnits and self.cacheDataUnitsEnabled:
			Logging.info("Returning cached dataunit", kw="pipeline")
			return self.cacheDataUnits[key]
		
		for i, currfilter in enumerate(enabledFilters):
			if currfilter.requireWholeDataset:
				wantWhole = True
			self.currentExecutingFilter = currfilter
			self.shift = x*(i+1)
			self.scale = x
			self.eventDesc = "Performing %s"%currfilter.name
			currfilter.setExecutive(self)
			if polydata:
				currfilter.setPolyDataInput(polydata)
			flag = (i == highestFilterIndex)
			if i > 0:
				currfilter.setPrevFilter(enabledFilters[i-1])
			else:
				currfilter.setPrevFilter(None)
			if not flag:
				currfilter.setNextFilter(enabledFilters[i+1])
			else:
				currfilter.setNextFilter(None)
			Logging.info("Executing %s"%currfilter.name,kw="pipeline")

			data = currfilter.execute(data, update=0, last=flag)
			polydata = currfilter.getPolyDataOutput()

			if not flag:
				nextfilter = enabledFilters[i+1]
				if not currfilter.itkFlag and nextfilter.itkFlag:
					Logging.info("Executing VTK side before switching to ITK", kw="pipeline")
					data = optimize.optimize(image = data, releaseData = 1)
					data.Update()
				elif currfilter.itkFlag and not nextfilter.itkFlag:
					Logging.info("Converting from ITK side back to VTK", kw="pipeline")
					data = currfilter.convertITKtoVTK(data)
			
			lastfilter = currfilter
			
			if not preview:
				currfilter.writeOutput(self.controlUnit, self.timepoint)
			data = [data]
			if not data:
				self.currentExecutingFilter = None
				self.cached = None
				return None

		self.currentExecutingFilter = None
		
		if wantWhole:
			scripting.wantWholeDataset = wantWhole
		Logging.info("Pipeline done",kw="pipeline")
		data = data[0]
		if data.__class__ != vtk.vtkImageData and type(data) != types.TupleType:
			data = lastfilter.convertITKtoVTK(data)

		filterlist.setModified(0)
		self.setPolyDataOutput(polydata)
		
		if self.cacheDataUnitsEnabled:
			print data.GetUpdateExtent()
			x0, x1, y0, y1, z0, z1 = data.GetUpdateExtent()
			if z1 >= 0:
				copy = vtk.vtkImageData()
				copy.DeepCopy(data)
				copy.Update()
				key = (self.settings.dataunit, self.timepoint)
				self.cacheDataUnits[key] = copy
				Logging.info("Caching dataunit", kw="pipeline")

		return data
		
	def clearCacheDataUnits(self, *args):
		"""
		Resets the cacheDataUnits variable.
		"""
		Logging.info("Clearing cached dataunits", kw="pipeline")
		self.cacheDataUnits = {}
        
	def enableDataUnitsCache(self, obj, event, value):
		if value == True:
			Logging.info("Enabling dataunits cache", kw="pipeline")
		elif value == False:
			Logging.info("Disabling dataunits cache", kw="pipeline")
		else:
			return
		self.cacheDataUnitsEnabled = value
