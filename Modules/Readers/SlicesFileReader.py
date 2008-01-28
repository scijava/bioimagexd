# -*- coding: iso-8859-1 -*-
"""
 Unit: SlicesFileReader
 Project: BioImageXD
 Created: 09.01.2008, KP
 Description: A datasource for reading a directory of normal image formats. This assumes
 			  that all files of a given type in a directory belong to a single channel

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

from lib.DataSource.DataSource import DataSource
import FileListDataSource
from lib.DataUnit.DataUnit import DataUnit
import os.path
import glob
import vtk


def getExtensions(): 
	return ["tif","jpg","bmp","png"]

def getFileType(): 
	return "Image files (*.tif, *.jpg, *.bmp, *.png)"

def getClass(): 
	return SlicesDataSource


class SlicesDataSource(DataSource):
	"""
	A datasource for reading a directory of image slices
	"""
	def __init__(self, filename = ""):

		DataSource.__init__(self)


	def getTimeStamp(self, timepoint):
		"""
		return the timestamp for given timepoint
		"""
		return timepoint

	def getDataSetCount(self):
		"""
		Returns the number of individual DataSets (=time points)
		managed by this DataSource
		"""
		return 0
  
	def getBitDepth(self):
		"""
		Return the bit depth of data
		"""
		return 8
		
	def getScalarRange(self):
		"""
		Return the bit depth of data
		"""
		return 0,255

	def internalGetDimensions(self):
		"""
		Return the original dimensions of the dataset
		"""
		return (0,0,0)

	def getSpacing(self):
		return [1,1,1]

		
	def getVoxelSize(self):
		return [1,1,1]
		
	def getFileName(self):
		"""
		Return the file name
		"""
		return ""
		
	def loadFromFile(self, filename):
		"""
		Loads a directory of slices
		"""
		self.filename = filename
		filebase, ext = os.path.splitext(filename)
		directoryname = os.path.abspath(os.path.dirname(filename))
		
		ext = ext[1:]
		files = glob.glob(os.path.join(directoryname, "*.%s"%ext))
		print "Loading files", files
		
		datasource = FileListDataSource.FileListDataSource()
		datasource.setSlicesPerTimepoint(len(files))
		datasource.setFilenames(files)
		dataunit = DataUnit()
		dataunit.setDataSource(datasource)
		settings = dataunit.getSettings()

		dims = datasource.getDimensions()
		settings.set("Dimensions", dims)
		settings.set("Name", os.path.basename(os.path.dirname(filename)))
		
		return [dataunit]
	def getColorTransferFunction(self):
		"""
		Returns the ctf of the dataset series which this datasource
					 operates on
		"""
		return None
		
		
	def getName(self):
		"""
		Returns the name of the dataset series which this datasource
					 operates on
		"""
		return os.path.basename(os.path.dirname(self.filename))

	def uniqueId(self):
		"""
		return a string identifying the dataset
		"""
		return self.filename

   
