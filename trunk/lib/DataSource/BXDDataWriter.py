
# -*- coding: iso-8859-1 -*-
"""
 Unit: BXDDataWriter
 Project: BioImageXD
 Created: 22.02.2005, KP
 Description:

 A writer of BioImageXD .bxd files
 
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
__version__ = "$Revision: 1.40 $"
__date__ = "$Date: 2005/01/13 14:52:39 $"


#from ConfigParser import *
from DataSource import DataWriter 
#import vtk
import os.path

import Logging
#import DataUnit
		
class BXDDataWriter(DataWriter):
	"""
	Created: 26.03.2005, KP
	Description: A writer of BioImageXD data (.bxd) files
	"""

	def __init__(self, filename):
		"""
		Constructor
		"""
		DataWriter.__init__(self)
		# list of references to individual channels (.bxc files)
		self.writers = []
		
		# path to the .du-file and .vti-file(s)
		self.path = os.path.dirname(filename)
		bxdfile = os.path.basename(filename)
		if bxdfile[-4:].lower() != ".bxd":
			newdirname = bxdfile
			bxdfile = bxdfile + ".bxd"
		else:
			lst = bxdfile.split(".")
			newdirname = ".".join(lst[:-1])
		self.filedir = os.path.join(self.path, newdirname)
		if not os.path.exists(self.filedir):
			os.mkdir(self.filedir)
		elif not os.path.isdir(self.filedir):
			Logging.error("Not a directory", "The selected path, %s exists and is not directory. Cannot write files" %(self.filedir))
		self.filename = os.path.join(self.filedir, bxdfile)
		
	
		
	def getBXCFileName(self, bxdFile):
		"""
		return a corresponding .bxc filename when given a bxd file name
		"""
		bxdFile = os.path.basename(bxdFile)
		if bxdFile[-4:].lower() != ".bxd":
			bxcFile = bxdFile + ".bxc"
		else:
			bxcFile = bxdFile[:-4] + ".bxc"
		return os.path.join(self.getPath(), bxcFile)
		
	def getPath(self):
		"""
		Return the actual (created) path where the files should be written
		"""
		return self.filedir
		
	def getFilename(self):
		"""
		Return the filename
		"""
		return self.filename
		
	def write(self):
		"""
		Writes the given datasets and their information to a du file
		"""
		try:
			fp = open(self.filename, "w")
		except IOError, ex:
			Logging.error("Failed to write settings",
			"BXDDataSource Failed to open .bxd file %s for writing settings (%s)" %(self.filename, str(ex)))
			return
		for writer in self.writers:
			filename = os.path.basename(writer.getFilename())
			fp.write("%s\n" %filename)
	   
		fp.close()

	def addChannelWriter(self, writer):
		"""
		Add a vtkImageData object to be written to the disk.
		"""
		self.writers.append(writer)
