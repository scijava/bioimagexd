# -*- coding: iso-8859-1 -*-
"""
 Unit: BXDDataSource
 Project: BioImageXD
 Created: 03.11.2004, JM
 Description: A class that reprensets the .bxd files that list 
			the individual .bxc files that belong to a given dataset

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
__version__ = "$Revision: 1.37 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import BXCDataSource
from lib.DataSource.DataSource import DataSource
import os.path
import Logging

def getExtensions(): 
	return ["bxd"]

def getFileType(): 
	return "BioImageXD dataset (*.bxd)"

def getClass(): 
	return BXDDataSource

class BXDDataSource(DataSource):
	"""
	Created: 08.02.2007, KP
	Description: Manages .bxd files that list each individual .bxc channel. This datasource is a kind of a pseudo
				 datasource in that it will return BXC datasources, and cannot in and of itself read anything
	"""
	def __init__(self, filename = ""):
		"""
		Created: 08.2.2007, KP
		Description: Constructor
		"""
		DataSource.__init__(self)
		self.sourceUnits = []  
   

	def loadFromFile(self, filename):
		"""
		Created: 08.02.2007, KP
		Description: Loads the specified .bxc-file and imports data from it.
					 Also returns a DataUnit of the type stored in the loaded
					 .bxc-file or None if something goes wrong. The dataunit is
					 returned in a list with one item for interoperability with
					 LSM data source
		"""
		
		
		try:
			f = open(filename, "r")
		except IOError, ex:
			Logging.error("Failed to open BXD File",
			"Failed to open file %s for reading: %s" % (filename, str(ex)))
		
		filepath = os.path.dirname(filename)
		lines = f.readlines()
		f.close()
		
		dataunits = []
		
		for i, line in enumerate(lines):
			# We create a datasource with specific channel number that
			#  we can associate with the dataunit
			bxcfile = os.path.join(filepath, line.strip())
			Logging.info("Reading file %s" % bxcfile, kw = "lsmreader")
			datasource = BXCDataSource.BXCDataSource()
			bxcdataunits = datasource.loadFromFile(bxcfile)
#            dataunit=DataUnit.DataUnit()
#            dataunit.setDataSource(datasource)
			dataunits.extend(bxcdataunits)
			
		return dataunits
