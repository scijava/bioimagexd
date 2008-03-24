# -*- coding: iso-8859-1 -*-
"""
 Unit: DataSource.py
 Project: BioImageXD
 Created: 03.11.2004, JM
 Description: Classes for managing 4D data located on disk

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
__version__ = "$Revision: 1.37 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

from lib.DataSource.DataSource import DataSource
from lib.DataUnit.DataUnit import DataUnit
import lib.messenger
import Logging
import os.path
import scripting
import vtk
import vtkbxd
import struct
import time

def getExtensions(): 
	return ["lsm"]

def getFileType(): 
	return "Zeiss LSM 510 datasets (*.lsm)"

def getClass(): 
	return LsmDataSource

class LsmDataSource(DataSource):
	"""
	Manages 4D data stored in an lsm-file
	"""
	def __init__(self, filename = "", channelNum = -1):
		"""
		Constructor
		"""
		DataSource.__init__(self)
		# Name and path of the lsm-file:
		self.filename = filename
		self.timepoint = -1
		self.shortname = os.path.basename(filename)
		self.path = ""
		# An lsm-file may contain multiple channels. However, LsmDataSource only
		# handles one channel. The following attribute indicates, which channel
		# within the lsm-file is hadled by this LsmDataSource instance.
		self.channelNum = channelNum
		self.setPath(filename)
		self.dataUnitSettings = {}
		# TODO: what is this?
		self.count = 0

		self.dimensions = None
		self.spacing = None
		self.origin = None
		self.voxelsize = None
		# vtkLSMReader is used to do the actual reading:
		self.reader = vtkbxd.vtkLSMReader()
		#self.reader.DebugOn()
		self.reader.AddObserver("ProgressEvent", lib.messenger.send)
		lib.messenger.connect(self.reader, 'ProgressEvent', self.updateProgress)
		# If a filename was specified, the file is loaded
		if self.filename:
			self.path = os.path.dirname(filename)
			Logging.info("LsmDataSource created with file %s and channelNum=%d"%\
			(self.filename, channelNum), kw = "lsmreader")
			try:
				f = open(filename)
				f.close()
			except IOError, ex:
				Logging.error("Failed to open LSM File",
				"Failed to open file %s for reading: %s" % (filename, str(ex)))
				return
				
			self.reader.SetFileName(self.convertFileName(self.filename))
			self.reader.SetUpdateChannel(channelNum)
			self.reader.UpdateInformation()
			self.originalScalarRange = None
			self.getBitDepth()
			self.originalDimensions = self.reader.GetDimensions()[0:3]
			self.readTimeStamps()
			


	def readTimeStamps(self):
		"""
		return the timestamp for given timepoint
		"""
		if not self.reader:
			return
		timestamps = self.reader.GetTimeStampInformation()
		stamps = []
		absStamps = []
		if not timestamps.GetSize():
			timeInterval = self.reader.GetTimeInterval()
			if timeInterval != 0:
				for i in range(0, self.getDataSetCount()):
					stamps.append(i*timeInterval)
					absStamps.append(i*timeInterval)
			else:
				return
		else:
			v0 = timestamps.GetValue(0)
			for timepoint in range(0, self.getDataSetCount()):
				v = timestamps.GetValue(timepoint)
				stamps.append(v-v0)
				absStamps.append(v)
		self.setTimeStamps(stamps)
		self.setAbsoluteTimeStamps(absStamps)

	def getDataSetCount(self):
		"""
		Returns the number of individual DataSets (=time points)
		managed by this DataSource
		"""
		if not self.dimensions:
			self.getDimensions()
		return self.dimensions[3]
  
	def getBitDepth(self):
		"""
		Return the bit depth of data
		"""
		if not self.bitdepth:
			d = self.reader.GetOutput().GetScalarType()
			if d == 3:
				self.bitdepth = 8
				if not self.originalScalarRange:
					self.originalScalarRange = (0, 255)
			if d == 5:
				self.bitdepth = 12
				if not self.originalScalarRange:
					self.originalScalarRange = (0, 4095)
		return self.bitdepth
		
	def getScalarRange(self):
		"""
		Return the bit depth of data
		"""
		if not self.scalarRange:
			#data=self.getDataSet(0,raw=1)
			#self.scalarRange=data.GetScalarRange()
			self.scalarRange = (0, 2 ** self.bitdepth - 1)
		if self.explicitScale and self.intensityScale != -1:
			x0, x1  = self.scalarRange
			x0 += self.getIntensityShift()
			x0 *= self.getIntensityScale()
			x1 += self.getIntensityShift()
			x1 *= self.getIntensityScale()
			print "Returning scaled",x0,x1,self.scalarRange
			return (x0,x1)
		return self.scalarRange

	def internalGetDimensions(self):
		"""
		Return the original dimensions of the dataset
		"""
		return self.reader.GetDimensions()

	def getSpacing(self):
		
		if not self.spacing:
			a, b, c = self.reader.GetVoxelSizes()
			Logging.info("Voxel sizes = ", a, b, c, kw = "lsmreader")
			self.spacing = [1, b / a, c / a]
		return self.spacing
		
		
	def getVoxelSize(self):
		if not self.voxelsize:
			self.voxelsize = self.reader.GetVoxelSizes()
		return self.voxelsize
			
		
	def getDataSet(self, i, raw = 0):
		"""
		Returns the timepoint at the specified index
		Parameters:	  i		  The timepoint to retrieve
					  raw	  A flag indicating that the data is not to be processed in any way
		"""
		# No timepoint can be returned, if this LsmDataSource instance does not
		# know what channel it is supposed to handle within the lsm-file.
		self.setCurrentTimepoint(i)
		if self.channelNum == -1:
			Logging.error("No channel number specified",
			"LSM Data Source got a request for dataset from timepoint "
			"%d, but no channel number has been specified" % (i))
			return None
	
		self.timepoint = i
		self.reader.SetUpdateChannel(self.channelNum)
		self.reader.SetUpdateTimePoint(i)
		data = self.reader.GetOutput()

		if raw:
			return data
		if self.resampling:
			data = self.getResampledData(data, i)
		if self.explicitScale or (data.GetScalarType() != 3 and not raw):
			data = self.getIntensityScaledData(data)
		return data
		
	def getFileName(self):
		"""
		Return the file name
		"""
		return self.filename
		
	def loadFromFile(self, filename):
		"""
		Loads all channels from a specified LSM file to DataUnit-
					 instances and returns them as a list.
		Parameters:	  filename	The .lsm-file to be loaded
		"""
		try:
			f = open(filename,"r")
			f.close()
		except IOError, ex:
			Logging.error("Failed to open LSM File",
			"Failed to open file %s for reading: %s" % (filename, str(ex)))

		self.filename = filename
		self.shortname = os.path.basename(filename)
		self.path = os.path.dirname(filename)

		self.reader.SetFileName(self.convertFileName(filename))


		#self.reader.Update()
		self.reader.UpdateInformation()

		dataunits = []
		channelNum = self.reader.GetNumberOfChannels()
		self.timepointAmnt = channelNum
		Logging.info("There are %d channels" % channelNum, kw = "lsmreader")
		for i in range(channelNum):
			# We create a datasource with specific channel number that
			#  we can associate with the dataunit
			datasource = LsmDataSource(filename, i)
			datasource.setPath(filename)
			dataunit = DataUnit()
			dataunit.setDataSource(datasource)
			dataunits.append(dataunit)
			
		return dataunits


	def getColorTransferFunction(self):
		"""
		Returns the ctf of the dataset series which this datasource
					 operates on
		"""
		if not self.ctf:
			Logging.info("Using ctf based on LSM Color", kw = "lsmreader")
			ctf = vtk.vtkColorTransferFunction()
			r = self.reader.GetChannelColorComponent(self.channelNum, 0)
			g = self.reader.GetChannelColorComponent(self.channelNum, 1)
			b = self.reader.GetChannelColorComponent(self.channelNum, 2)
			#print "Got color components=",r,g,b
			r /= 255.0
			g /= 255.0
			b /= 255.0
			minval, maxval = self.getScalarRange()
			
			if self.explicitScale:
				shift = self.intensityShift
				if self.intensityShift:
					maxval += self.intensityShift
					#print "Maximum value after being shifted=",maxval
				scale = self.intensityScale
				if not scale:
					scale = 255.0 / maxval
				maxval *= scale
				#print "Maximum value after being scaled=",maxval
			ctf.AddRGBPoint(0, 0, 0, 0)
			ctf.AddRGBPoint(maxval, r, g, b)
			self.ctf = ctf
		return self.ctf
		
	def resetColorTransferFunction(self):
		"""
		A method that will reset the CTF from the datasource.
					 This is useful e.g. when scaling the intensities of the
					 dataset
		"""
		self.scalarRange = None
		self.ctf = None
		return self.getColorTransferFunction()
		
		
	def getName(self):
		"""
		Returns the name of the dataset series which this datasource
					 operates on
		"""
		if self.channelNum < 0:
			Logging.error("No channel number specified",
			"LSM Data Source got a request for the name of the channel, "
			"but no channel number has been specified")
			return ""
		return self.reader.GetChannelName(self.channelNum)

	def uniqueId(self):
		"""
		return a string identifying the dataset
		"""
		return self.getFileName() + "|" + str(self.channelNum)

	def __str__(self):
		"""
		Returns the basic information of this instance as a string
		"""
		return "LSM DataSource (%s, channel %d)" % (self.filename, self.channelNum)

