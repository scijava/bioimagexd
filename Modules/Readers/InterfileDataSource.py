# -*- coding: iso-8859-1 -*-
"""
 Unit: InterfileDataSource
 Project: BioImageXD
 Created: 29.03.2006, KP
 Description: A datasource for reading Interfile .PIC files

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

import ConfigParser
import struct
import re
import messenger
import re
		

import os.path
from DataSource import *
import DataUnit

import glob

def getExtensions(): return ["hdr"]
def getFileType(): return "Interfile files (*.hdr)"
def getClass(): return InterfileDataSource    
	

class InterfileDataSource(DataSource):
	"""
	Class: InterfileDataSource
	Created: 12.04.2005, KP
	Description: Interfile datasource
	"""
	def __init__(self, filename = ""):
		"""
		Method: __init__
		Created: 12.04.2005, KP
		Description: Constructor
		"""    
		
		DataSource.__init__(self)
		
		name = os.path.basename(filename)
		name = name.split(".")
		name = ".".join(name[:-1])
		self.name = name
		self.setPath(filename)
		self.filename = filename
		self.reader = None

		self.datatype = "Float"
		
		self.dimensions = None
		self.voxelsize = (1, 1, 1)
		self.spacing = None
		self.color = None
		self.shift = None
		self.tps = -1
		if filename:
			self.path = os.path.dirname(filename)
			self.getDataSetCount()            
			f = open(filename, "r")
			self.readInfo(f)
			f.close()
		
	def readInfo(self, file):
		"""
		Method: readInfo
		Created: 28.06.2006, KP
		Description: Read the header info from file
		"""   
		lines = file.readlines()
		dimre = re.compile("matrix size.*\[(\d)\].*:=(\d+)")
		spacere = re.compile("scaling factor.*\[(\d)\].*:=(\d*.\d*)")
		formatre = re.compile("!number format.*:=(.*)")
		self.dimensions = [0, 0, 0]
		self.voxelsize = [0, 0, 0]
		self.spacing = [0, 0, 0]
		
		for line in lines:
			line.strip()
			m = dimre.search(line)
			if line.find("byte order"):
				if line.find("LITTLEENDIAN"):
					self.endianness = "LittleEndian"
				else:
					self.endianness = "BigEndian"
			if m:
				n, x = m.groups()
				print "Dimension", n, "=", x
				self.dimensions[int(n) - 1] = int(x)
			m = spacere.search(line)
			if m:
				n, x = m.groups()
				print "Spacing ", n, "=", x
				self.voxelsize[int(n) - 1] = float(x)                    
			m = formatre.search(line)
			if m:
				print "Found", m.groups()
				s = m.groups()[0]
				if s == "short float":
					self.datatype = "Float"
				elif s == "long float":
					self.datatype = "Double"
				
		print "dims=", self.dimensions
		x = self.voxelsize[0]
		self.originalDimensions = self.dimensions
		self.spacing = [1, self.voxelsize[1] / x, self.voxelsize[2] / x]
	def getDataSetCount(self):
		"""
		Method: getDataSetCount
		Created: 12.04.2005, KP
		Description: Returns the number of individual DataSets (=time points)
		managed by this DataSource
		"""
		if self.tps < 0:
			f = self.filename[:]
			f = f.replace(".hdr", ".img")
			f = f.replace(".HDR", ".IMG")
			
			r = re.compile("(\d+)....$")
			
			m = r.search(f)
			if m:
				d = m.groups(0)
				print d
				f = f.replace(d[0], "%d")
				n = 1
				self.filepattern = f
				for i in range(1, 99999):
					if os.path.exists(f % i):
						n = i
				self.tps = n
				if n == 1:
					self.imgfile = self.filepattern % 1
			else:
				self.tps = 1
				self.imgfile = f
		return self.tps
		
	def getFileName(self):
		"""
		Method: getFileName()
		Created: 21.07.2005
		Description: Return the file name
		"""    
		return self.filename
			
	def getDataSet(self, i, raw = 0):
		"""
		Method: getDataSet
		Created: 12.04.2005, KP
		Description: Returns the DataSet at the specified index
		Parameters:   i       The index
		"""
		data = self.getTimepoint(i)
		data = self.getResampledData(data, i)
		if not self.shift:
			self.shift = vtk.vtkImageShiftScale()
			self.shift.SetOutputScalarTypeToUnsignedChar()
		self.shift.SetInput(data)
			
		x0, x1 = data.GetScalarRange()
		print "Scalar range=", x0, x1
		if not x1:
			x1 = 1
		scale = 255.0 / x1
		
		if scale:
			self.shift.SetScale(scale)
		self.shift.Update()
		data = self.shift.GetOutput()
		data.ReleaseDataFlagOff()
		return data
		
	def getTimepoint(self, n, onlyDims = 0):
		"""
		Method: getTimepoint
		Created: 16.02.2006, KP
		Description: Return the nth timepoint
		"""        
		if not self.reader:
			self.reader = vtk.vtkImageReader2()
			eval("self.reader.SetDataScalarTypeTo%s()" % self.datatype)
			x, y, z = self.dimensions
			self.reader.SetDataExtent(0, x - 1, 0, y - 1, 0, z - 1)
			self.reader.SetFileDimensionality(3)
			self.reader.SetDataSpacing(self.spacing)
			eval("self.reader.SetDataByteOrderTo%s()" % self.endianness)
			
		if self.tps == 1:
			self.reader.SetFileName(self.imgfile)
		else:
			print "Switching to dataset ", self.filepattern % (n + 1)
			self.reader.SetFileName(self.filepattern % (n + 1))
		
		self.reader.Update()
		print self.reader.GetOutput()
		
		return self.reader.GetOutput()
		
	def getDimensions(self):
		"""
		Method: getDimensions()
		Created: 12.04.2005, KP
		Description: Returns the (x,y,z) dimensions of the datasets this 
					 dataunit contains
		"""
		if self.resampleDims:
			return self.resampleDims
		return self.dimensions

		
	def getSpacing(self):
		"""
		Method: getSpacing()
		Created: 12.04.2005, KP
		Description: Returns the spacing of the datasets this 
					 dataunit contains
		"""
		return self.spacing
		
	def getVoxelSize(self):
		"""
		Method: getVoxelSize()
		Created: 12.04.2005, KP
		Description: Returns the voxel size of the datasets this 
					 dataunit contains
		"""
		return self.voxelsize
			
	def loadFromFile(self, filename):
		"""
		Method: loadFromFile
		Created: 12.04.2005, KP
		Description: Loads the specified .oif-file and imports data from it.
		Parameters:   filename  The .oif-file to be loaded
		"""
		dataunit = DataUnit.DataUnit()
		datasource = InterfileDataSource(filename)
		dataunit.setDataSource(datasource)
		return [dataunit]
		

	def getName(self):
		"""
		Method: getName
		Created: 18.11.2005, KP
		Description: Returns the name of the dataset series which this datasource
					 operates on
		"""
		return self.name

		
	def getColorTransferFunction(self):
		"""
		Method: getColorTransferFunction()
		Created: 26.04.2005, KP
		Description: Returns the ctf of the dataset series which this datasource
					 operates on
		"""
		if not self.ctf:
			self.ctf = vtk.vtkColorTransferFunction()
			self.ctf.AddRGBPoint(0, 0, 0, 0)
			self.ctf.AddRGBPoint(255, 0, 1, 0)
		return self.ctf        
