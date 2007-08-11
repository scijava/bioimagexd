# -*- coding: iso-8859-1 -*-
"""
 Unit: FilterBasedModule
 Project: BioImageXD
 Created: 04.04.2006, KP
 
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


import vtk
import Logging
import lib.Module

import optimize

class FilterBasedModule(lib.Module.Module):
	"""
	Created: 04.04.2006, KP
	Description: Applies a stack of processing filters to a given input dataset
	"""

	def __init__(self, **kws):
		"""
		Created: 25.11.2004, KP
		Description: Initialization
		"""
		lib.Module.Module.__init__(self, **kws)

		self.cached = None
		self.cachedTimepoint = -1
		self.depth = 8
		self.extent = None
		self.images = []
		self.modified = 0
		self.preview = None
		self.running = 0
		self.settings = None
		self.reset()
		
	def setModified(self, flag):
		"""
		Created: 14.05.2006
		Description: Set a flag indicating whether filter parameters have changed
		"""
		Logging.info("Setting modified to %s"%str(not not flag), kw="dataunit")
		self.modified = flag

	def reset(self):
		"""
		Created: 25.11.2004, KP
		Description: Resets the module to initial state. This method is
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
		Created: 04.04.2006, KP
		Description: Adds an input for the single dataunit Manipulationing filter
		"""
		lib.Module.Module.addInput(self, dataunit, data)
		self.settings = dataunit.getSettings()


	def getPreview(self, depth):
		"""
		Created: 04.04.2006, KP
		Description: Does a preview calculation for the x-y plane at depth depth
		"""
		if self.settings.get("ShowOriginal"):
			Logging.info("Returning original data", kw="dataunit")
			return self.images[0] 
		if not self.preview or self.modified:
			dims = self.images[0].GetDimensions()
			if depth >= 0:
				self.extent = (0, dims[0]-1, 0, dims[1]-1, depth, depth)
			else:
				self.extent = None
			Logging.info("Creating preview...", kw="dataunit")
			self.preview = self.doOperation(preview=1)
			self.extent = None
		else:
			Logging.info("Modified = %s so returning old preview"%str(not not self.modified), kw="dataunit")
		return self.preview


	def doOperation(self, preview=0):	#TODO:test
		"""
		Created: 04.04.2006, KP
		Description: Manipulationes the dataset in specified ways
		"""
		if preview and not self.modified and self.cached and self.timepoint == self.cachedTimepoint:
			Logging.info("--> Returning cached data, timepoint=%d, cached timepoint=%d" % 
				(self.timepoint, self.cachedTimepoint), kw = "pipeline")
			return self.cached
		else:
			del self.cached
			self.cached = None
		filterlist = self.settings.get("FilterList")
		Logging.info("Creating preview, filters = %s"%str(filterlist), kw="pipeline")
		if type(filterlist) == type(""):
			filterlist = []
		self.settings.set("FilterList", filterlist)
		data = self.images
		if not filterlist:
			return self.images[0]
		try:
			# enabledFilters = filter(lambda x:x.getEnabled(), filterlist)
			enabledFilters = [filterModule for filterModule in filterlist if filterModule.getEnabled()]	 
		except AttributeError:
			enabledFilters = []
		highestFilterIndex = len(enabledFilters)-1
		
		lastfilter = None
		#lasttype = "UC3"
		for i, currfilter in enumerate(enabledFilters):
			flag = (i == highestFilterIndex)
			if i > 0:
				print enabledFilters[i-1], "->", currfilter
				currfilter.setPrevFilter(enabledFilters[i-1])
			else:
				print "-> ", currfilter
				currfilter.setPrevFilter(None)
			if not flag:
				currfilter.setNextFilter(enabledFilters[i+1])
				print currfilter, "->", enabledFilters[i+1]
			else:
				currfilter.setNextFilter(None)
				print currfilter, "->|"
			#data = currfilter.execute(data,update=flag,last=flag)
			data = currfilter.execute(data, update=0, last=flag)
			
			if not flag:
				nextfilter = enabledFilters[i+1]
				if not currfilter.itkFlag and nextfilter.itkFlag:
					Logging.info("Executing VTK side before switching to ITK", kw="pipeline")
					data = optimize.optimize(image = data, releaseData = 1)
					data.Update()
				
			
			lastfilter = currfilter
			
			if not preview:
				currfilter.writeOutput(self.controlUnit, self.timepoint)
			#lasttype = currfilter.getImageType()
			
			
			data = [data]
			if not data:
				self.cached = None
				return None
	
		data = data[0]
		if data.__class__ != vtk.vtkImageData:
			
			data = lastfilter.convertITKtoVTK(data)#,imagetype=lasttype)

		data.ReleaseDataFlagOff()

		self.modified = 0
		return data
