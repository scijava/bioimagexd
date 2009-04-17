# -*- coding: iso-8859-1 -*-

"""
 Unit: FilterBasedTaskSettings
 Project: BioImageXD
 Created: 26.03.2005, KP
 Description:

 This is a base class for all tasks that are based on the notion of a list of filters

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
__version__ = "$Revision: 1.21 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

from DataUnitSetting import DataUnitSettings
import lib.FilterBasedModule

class FilterBasedTaskSettings(DataUnitSettings):
	"""
	Created: 27.03.2005, KP
	Description: Stores settings related to single unit Manipulationing
	"""
	def __init__(self, n = -1):
		"""
		Constructor
		"""
		DataUnitSettings.__init__(self, n)
		self.set("Type", "No Type Set")
		
		self.registerPrivate("ColorTransferFunction", 1)
		self.registerCounted("Source")
		self.register("FilterList", serialize = 1)
		self.register("VoxelSize")
		self.register("Spacing")
		#self.register("Origin")
		self.register("Dimensions")
		self.register("Type")
		self.register("Name")
		self.register("BitDepth")
		
	def initialize(self, dataunit, channels, timepoints):
		"""
		Method: initialize(dataunit, channels, timepoints)
		Set initial values for settings based on 
					 number of channels and timepoints
		"""
		DataUnitSettings.initialize(self, dataunit, channels, timepoints)
		
	def writeTo(self, parser):
		"""
		Attempt to write all keys to a parser
		"""
		DataUnitSettings.writeTo(self, parser)
		filterList = self.get("FilterList")
		if filterList:
			filterList.writeOut(parser)
	
	def deserialize(self, name, value):
		"""
		Returns the value of a given key
		"""
		if name == "FilterList":
			filterList = lib.FilterBasedModule.FilterList()
			filterNames = eval(value)
			filterList.populate(filterNames)
			return filterList
				
		else:
			return DataUnitSettings.deserialize(name, value)
		
		
	def serialize(self, name, value):
		"""
		Returns the value of a given key in a format
					 that can be written to disk.
		"""
		if name == "FilterList":
			if value:
				return str(value.getFilterNames())
			else:
				return "[]"
		else:
			return DataUnitSettings.serialize( name, value)
