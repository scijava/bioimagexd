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
import Logging
import os.path
import scripting
import vtk
import vtkbxd
import struct

def getExtensions(): 
	return ["lsm"]

def getFileType(): 
	return "Zeiss LSM 510 datasets (*.lsm)"

def getClass(): 
	return LsmDataSource

class LsmDataSource(DataSource):
	"""
	Created: 18.11.2004, KP
	Description: Manages 4D data stored in an lsm-file
	"""
	def __init__(self, filename = "", channelNum = -1):
		"""
		Created: 18.11.2004, KP
		Description: Constructor
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
		self.timestamps = None

		self.dimensions = None
		self.spacing = None
		self.origin = None
		self.voxelsize = None
		# vtkLSMReader is used to do the actual reading:
		self.reader = vtkbxd.vtkLSMReader()
		#self.reader.DebugOn()
		self.reader.AddObserver("ProgressEvent", self.updateProgress)
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
			#print "Update information..."
			self.reader.UpdateInformation()
			#print "done"
			self.originalScalarRange = None
			self.getBitDepth()
			self.originalDimensions = self.reader.GetDimensions()[0:3]

			self.updateProgress(None, None)
			
	def updateProgress(self, obj, evt):
		"""
		Created: 13.07.2004, KP
		Description: Sends progress update event
		"""
		if not obj:
			progress = 1.0
		else:
			progress = obj.GetProgress()
		if self.channelNum >= 0:
			msg = "Reading channel %d of %s" % (self.channelNum + 1, self.shortname)
			if self.timepoint >= 0 and self.getDataSetCount()>1:
				msg += " (timepoint %d / %d)" % (self.timepoint + 1, self.dimensions[3])
		else:
			msg = "Reading %s..." % self.shortname
		notinvtk = 0
		
		if progress >= 1.0:
			notinvtk = 1
		scripting.inIO = (progress < 1.0)
		if scripting.mainWindow:
			scripting.mainWindow.updateProgressBar(obj, evt, progress,msg, notinvtk)

	def getTimeStamp(self, timepoint):
		"""
		Created: 02.07.2007, KP
		Description: return the timestamp for given timepoint
		"""
		if not self.reader:
			return timepoint
		if not self.timestamps:
			self.timestamps = self.reader.GetTimeStampInformation()
		if timepoint > self.timestamps.GetSize():
			return 0
		v = self.timestamps.GetValue(timepoint)
		v0 = self.timestamps.GetValue(0)
		return (v - v0)


	def getDataSetCount(self):
		"""
		Created: 03.11.2004, JM
		Description: Returns the number of individual DataSets (=time points)
		managed by this DataSource
		"""
		if not self.dimensions:
			self.getDimensions()
		return self.dimensions[3]
  
	def getBitDepth(self):
		"""
		Created: 07.08.2006, KP
		Description: Return the bit depth of data
		"""
		if not self.bitdepth:
			#self.reader.DebugOn()
			#self.reader.Update()
			d = self.reader.GetOutput().GetScalarType()
			#self.reader.ExecuteInformation()
						
			#self.reader.DebugOff()
			#print "\n\n\n**** Datatype=",d
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
		Created: 28.05.2005, KP
		Description: Return the bit depth of data
		"""
		if not self.scalarRange:
			#data=self.getDataSet(0,raw=1)
			#self.scalarRange=data.GetScalarRange()
			self.scalarRange = (0, 2 ** self.bitdepth - 1)
		return self.scalarRange

	def internalGetDimensions(self):
		"""
		Created: 14.12.2004, KP
		Description: Return the original dimensions of the dataset
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
		Created: 18.11.2004, KP
		Description: Returns the timepoint at the specified index
		Parameters:	  i		  The timepoint to retrieve
					  raw	  A flag indicating that the data is not to be processed in any way
		"""
		# No timepoint can be returned, if this LsmDataSource instance does not
		# know what channel it is supposed to handle within the lsm-file.
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
		Created: 21.07.2005
		Description: Return the file name
		"""
		return self.filename
		
	def loadFromFile(self, filename):
		"""
		Created: 18.11.2004, KP
		Description: Loads all channels from a specified LSM file to DataUnit-
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
		print type(filename)


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
		Created: 26.04.2005, KP
		Description: Returns the ctf of the dataset series which this datasource
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
		Created: 12.10.2006, KP
		Description: A method that will reset the CTF from the datasource.
					 This is useful e.g. when scaling the intensities of the
					 dataset
		"""
		self.scalarRange = None
		self.ctf = None
		return self.getColorTransferFunction()
		
		
	def getName(self):
		"""
		Created: 18.11.2004, KP
		Description: Returns the name of the dataset series which this datasource
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
		Created: 07.02.2007, KP
		Description: return a string identifying the dataset
		"""
		return self.getFileName() + "|" + str(self.channelNum)

	def __str__(self):
		"""
		Created: 18.11.2004, KP
		Description: Returns the basic information of this instance as a string
		"""
		return "LSM DataSource (%s, channel %d)" % (self.filename, self.channelNum)

