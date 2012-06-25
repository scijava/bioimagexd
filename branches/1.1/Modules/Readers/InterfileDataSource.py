# -*- coding: iso-8859-1 -*-
"""
 Unit: InterfileDataSource
 Project: BioImageXD
 Description: A datasource for reading Interfile .hdr files

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
from lib.DataUnit.DataUnit import DataUnit
import os.path
import re
import vtk
import lib.messenger


def getExtensions(): 
	return ["hdr"]

def getFileType(): 
	return "Interfile files (*.hdr)"

def getClass(): 
	return InterfileDataSource    	

class InterfileDataSource(DataSource):
	"""
	Interfile datasource
	"""
	def __init__(self, filename = ""):
		"""
		Constructor
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
		self.numberOfImages = 0
		self.dataFileName = ""
		self.bytesPerPixel = 0
		self.duration = 0.0
		
		if filename:
			self.path = os.path.dirname(filename)
			self.getDataSetCount()            
			f = open(filename, "r")
			self.readInfo(f)
			f.close()
			self.createTimeStamps()
		
	def readInfo(self, file):
		"""
		Read the header info from file
		"""
		lines = file.readlines()
		dimre = re.compile("matrix size.*\[(\d)\].*:=\s*(\d+)")
		spacere = re.compile("scaling factor.*\[(\d)\].*:=(.*)")
		formatre = re.compile("!number format.*:=\s*(.*)\s*")
		numberre = re.compile("!total number of images.*:=\s*(\d+)")
		datare = re.compile("!name of data file.*:=(.*)")
		bytesre = re.compile("!number of bytes per pixel.*:=\s*(\d+)")
		timere = re.compile("image duration.*:=\s*(.*)")
		self.dimensions = [0, 0, 0]
		self.voxelsize = [0, 0, 0]
		self.spacing = [0, 0, 0]
		
		for line in lines:
			line = line.strip()
			
			if line.find("byte order") != -1:
				if line.find("LITTLEENDIAN") != -1:
					self.endianness = "LittleEndian"
				else:
					self.endianness = "BigEndian"
				print "Endianness:",self.endianness
			m = dimre.search(line)
			if m:
				n, x = m.groups()
				print "Dimension", n, "=", x
				self.dimensions[int(n) - 1] = int(x)
			m = spacere.search(line)
			if m:
				n, x = m.groups()
				x = x.strip()
				print "Spacing", n, "=", x
				self.voxelsize[int(n) - 1] = float(x) / 1000
			m = formatre.search(line)
			if m:
				if line.find("short float") != -1:
					self.datatype = "Float"
				elif line.find("long float") != -1:
					self.datatype = "Double"
				elif line.find("unsigned integer") != -1:
					self.datatype = "UnsignedShort"
				print "Data type:",self.datatype
			m = numberre.search(line)
			if m:
				n, = m.groups()
				self.numberOfImages = int(n)
				print "Number of images:",self.numberOfImages
			m = datare.search(line)
			if m:
				file, = m.groups()
				file = file.strip()
				self.dataFileName = self.path + "/" + file
				print "Data filename:",self.dataFileName
			m = bytesre.search(line)
			if m:
				bytes, = m.groups()
				bytes = bytes.strip()
				self.bytesPerPixel = int(bytes)
				print "Bytes per pixel:",self.bytesPerPixel
			m = timere.search(line)
			if m:
				time, = m.groups()
				time = time.strip()
				self.duration = float(time)
				print "Duration:",self.duration
				
		print "Dims =", self.dimensions
		x = self.voxelsize[0]
		self.originalDimensions = self.dimensions
		self.spacing = [1, self.voxelsize[1] / x, self.voxelsize[2] / x]
		if self.dimensions[2] > 0:
			self.tps = self.numberOfImages / self.dimensions[2]
		else:
			self.tps = self.numberOfImages
			self.dimensions[2] = 1
			self.spacing[2] = 1.0

	def getDataSetCount(self):
		"""
		Returns the number of individual DataSets (=time points)
		managed by this DataSource
		"""
		#if self.tps < 0:
			#f = self.filename[:]
			#f = f.replace(".hdr", ".img")
			#f = f.replace(".HDR", ".IMG")
			
			#r = re.compile("(\d+)....$")
			
			#m = r.search(f)
			#if m:
			#	d = m.groups(0)
			#	print d
			#	f = f.replace(d[0], "%d")
			#	n = 0
			#	self.filepattern = f
			#	for i in range(1, 99999):
			#		if os.path.exists(f % i):
			#			n += 1
			#			if n == 1:
			#				self.imgfile = self.filepattern % i
			#	self.tps = n
			#else:
			#	self.tps = 1
			#	self.imgfile = f
				
		return self.tps
		
	def getFileName(self):
		"""
		Return the file name
		"""    
		return self.filename
			
	def getDataSet(self, i, raw = 0):
		"""
		Returns the DataSet at the specified index
		Parameters:   i       The index
		"""
		self.setCurrentTimepoint(i)
		data = self.getTimepoint(i)
		data = self.getResampledData(data, i)
		"""
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
		data = self.shift.GetOutput()
		"""
		data.Update()
		data.ReleaseDataFlagOff()
		return data
		
	def getTimepoint(self, n, onlyDims = 0):
		"""
		Return the nth timepoint
		"""
		if not self.reader:
			self.reader = vtk.vtkImageReader2()
			self.reader.AddObserver('ProgressEvent', lib.messenger.send)
			lib.messenger.connect(self.reader, 'ProgressEvent', self.updateProgress)
			eval("self.reader.SetDataScalarTypeTo%s()" % self.datatype)
			x, y, z = self.dimensions
			if z == 0:
				z += 1
			self.reader.SetDataExtent(0, x - 1, 0, y - 1, 0, z - 1)
			self.reader.SetFileDimensionality(3)
			self.reader.SetDataSpacing(self.spacing)
			eval("self.reader.SetDataByteOrderTo%s()" % self.endianness)
			
		#if self.tps == 1:
		#	self.reader.SetFileName(self.imgfile)
		#else:
		#	print "Switching to dataset ", self.filepattern % (n + 1)
		#	self.reader.SetFileName(self.filepattern % (n + 1))
		self.reader.SetFileName(self.dataFileName)
		skip = n
		for i in self.dimensions:
			skip *= i
		skip *= self.bytesPerPixel
		self.reader.SetHeaderSize(skip)
		self.reader.Update()
		print self.reader.GetOutput()
		
		return self.reader.GetOutput()
		
	def internalGetDimensions(self):
		"""
		Returns the (x,y,z) dimensions of the datasets this 
					 dataunit contains
		"""
		return self.dimensions

		
	def getSpacing(self):
		"""
		Returns the spacing of the datasets this 
					 dataunit contains
		"""
		return self.spacing
		
	def getVoxelSize(self):
		"""
		Returns the voxel size of the datasets this 
					 dataunit contains
		"""
		return self.voxelsize
			
	def loadFromFile(self, filename):
		"""
		Loads the specified .oif-file and imports data from it.
		Parameters:   filename  The .oif-file to be loaded
		"""
		dataunit = DataUnit()
		datasource = InterfileDataSource(filename)
		dataunit.setDataSource(datasource)
		return [dataunit]
		

	def getName(self):
		"""
		Returns the name of the dataset series which this datasource operates on
		"""
		return self.name

		
	def getColorTransferFunction(self):
		"""
		Returns the ctf of the dataset series which this datasource operates on
		"""
		if not self.ctf:
			self.ctf = vtk.vtkColorTransferFunction()
			minval,maxval = self.getScalarRange()
			self.ctf.AddRGBPoint(minval, 0, 0, 0)
			self.ctf.AddRGBPoint(maxval, 0, 1, 0)
		return self.ctf

	def createTimeStamps(self):
		"""
		Creates time stamps for setTimeStamps and setAbsoluteTimeStamps methods
		"""
		absoluteTimeStamps = []
		relativeTimeStamps = []
		if self.tps > 0:
			for i in xrange(self.tps):
				absoluteTimeStamps.append(i * self.duration)
				relativeTimeStamps.append(i * self.duration)

		self.setTimeStamps(relativeTimeStamps)
		self.setAbsoluteTimeStamps(absoluteTimeStamps)
		
	def getBitDepth(self):
		"""
		Return the bit depth of data
		"""
		if not self.bitdepth:
			data = self.getDataSet(0, raw = 1)
			data.UpdateInformation()
			self.scalarRange = data.GetScalarRange()
			self.bitdepth = self.bytesPerPixel * 8

		return self.bitdepth
