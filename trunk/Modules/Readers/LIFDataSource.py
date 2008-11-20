# -*- coding: iso-8859-1 -*-
"""
 Unit: LIFDataSource.py
 Project: BioImageXD
 Created: 2007/07/19, LP
 Description: Class for managing 4D LIF data located on disk

 Copyright (C) 2005	BioImageXD Project
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
__version__ = "$Revision$"
__date__ = "$Date$"

from lib.DataSource.DataSource import DataSource
from lib.DataUnit import DataUnit
import Logging
import scripting
import vtkbxd
import vtk
import lib.messenger

def getExtensions(): return ["lif"]
def getFileType(): return "Leica Image File Format (*.lif)"
def getClass(): return LIFDataSource

class LIFDataSource(DataSource):
	"""
	Manages 4D data stored in a LIF-file.
	"""

	def __init__(self, filename = "", imageNum = -1, channelNum = -1, reader = None):
		"""
		Constructor of LIF DataSource
		"""
		DataSource.__init__(self)
		self.filename = filename
		self.imageName = ""
		self.setPath(filename);
		# LIF file can contain multiple images with multiple channels.
		# Define which image and channel is associated to this DataSource
		self.imageNum = imageNum
		self.channelNum = channelNum
		self.bitDepth = 0
		
		self.spacing = None
		self.voxelSize = None
		self.ctf = None

		# Use vtkLIFReader
		self.reader = vtkbxd.vtkLIFReader()
		self.reader.AddObserver('ProgressEvent', lib.messenger.send)
		lib.messenger.connect(self.reader, 'ProgressEvent', self.updateProgress)

		# Open file if defined
		if self.filename:
			self.reader.SetFileName(self.convertFileName(self.filename))
			if self.reader.OpenFile():
				if reader:
					self.reader.CopyHeaderInfo(reader)
				if self.reader.ReadLIFHeader():
					self.reader.SetCurrentImage(self.imageNum)
					self.reader.SetCurrentChannel(self.channelNum)
					self.imageName = self.reader.GetImageName(self.imageNum)
					self.createTimeStamps()
				else:
					Logging.error("Failed to read the header of the LIF file correctly",
								  "Error in LIFDataSource.py in __init__, failed to read the header of the LIF file: %s" %(self.filename))
					return
			else:
				Logging.error("Failed to open file",
							  "Error in LIFDataSource.py in __init__, failed to open file: %s" %(self.filename))
				return

	def getDataSetCount(self):
		"""
		Returns the count of time points of the data set
		"""
		if not self.dimensions:
			self.dimensions = self.internalGetDimensions()
		return self.dimensions[3]

	def getFileName(self):
		"""
		Returns the file name with image name
		"""
		return self.filename + "_" + self.imageName;

	def getDataSet(self, i, raw = 0):
		"""
		Returns the defined timepoint of current image and channel
		@param i The timepoint of data to return
		@param raw A flag indicating that the data is not to be processed in any way
		"""
		if self.imageNum < 0 or self.channelNum < 0:
			Logging.error("No image or channel number specified",
						  "Error in LIFDataSource.py in getDataSet, no image or channel number specified.")
			return None
		
		if i < 0 or i >= self.getDataSetCount():
			Logging.error("Given time point is out of bounds",
						  "Time point %d that is out of bounds requested from getDataSet"%i)
			return None

		self.setCurrentTimepoint(i)
		self.reader.SetCurrentImageAndChannel(self.imageNum, self.channelNum)
		self.reader.SetCurrentTimePoint(i)
		data = self.reader.GetOutput()
		if raw:
			return data

		data = self.getResampledData(data, i)
		if self.explicitScale or (data.GetScalarType() != 3):
			data = self.getIntensityScaledData(data)

		return data

	def getName(self):
		"""
		Returns the name of the dataset handled by this DataSource
		"""
		if self.imageNum < 0 or self.channelNum < 0:
			Logging.error("Image or channel number not specified",
						  "Error in LIFDataSource.py in getName, no image or channel specified.")
			return ""
		return "Ch-%d"%(self.channelNum + 1)

	def internalGetDimensions(self):
		"""
		Returns the (x,y,z,t) dimensions of the dataset this dataunit contains
		@return 4-tuple of dimensions of the dataset	
		"""
		dimensions = self.reader.GetImageDims()
		# Make sure that every dimension is at least 1. This prevents
		# software from crashing with weird datasets like xt-series.
		dimensions = list(dimensions)
		
		if dimensions[0] <= 0:
			dimensions[0] = 1
		if dimensions[1] <= 0:
			dimensions[1] = 1
		if dimensions[2] <= 0:
			dimensions[2] = 1
		if dimensions[3] <= 0:
			dimensions[3] = 1

		dimensions = tuple(dimensions)

		return dimensions

	def loadFromFile(self, filename):
		"""
		Loads images from LIF-file and generates own DataSource
					 for each image in file. Returns list of tuples which
					 includes image name and DataUnit.
		@parameter filename Path to file where images should be loaded
		"""
		self.filename = filename
		dataUnits = []
		self.reader.SetFileName(self.convertFileName(self.filename))

		if self.reader.OpenFile():
			if self.reader.ReadLIFHeader():
				imageCount = self.reader.GetImageCount()
				for i in range(imageCount):
					imageName = self.reader.GetImageName(i)
					imageChannels = self.reader.GetChannelCount(i)
					for c in range(imageChannels):
						dataSource = LIFDataSource(filename,i,c,self.reader)
						dataUnit = DataUnit.DataUnit()
						dataUnit.setDataSource(dataSource)
						dataUnits.append((imageName,dataUnit))
			else:
				Logging.error("Failed to read the LIF header",
							  "Error in LIFDataSource.py in loadFromFile, failed to read the LIF header from file: %s"%(self.filename))
		else:
			Logging.error("Failed to open the LIF file",
						  "Error in LIFDataSource.py in loadFromFile, failed to open the LIF file: %s"%(self.filename))

		return dataUnits

	def getSpacing(self):
		"""
		Returns normalized spacing between voxels
		"""
		if not self.spacing:
			x, y, z = self.getVoxelSize()
			if x != 0:
				self.spacing = [1.0, y / x, z / x]
			else:
				self.spacing = [0,0,0]
		return self.spacing

	def getVoxelSize(self):
		"""
		Returns size of voxel as 3-tuple
		@return Size of voxel as 3-tuple
		"""
		if not self.voxelSize:
			self.voxelSize = self.reader.GetImageVoxels()
		return self.voxelSize

	def getColorTransferFunction(self):
		"""
		Creates color transfer function for channel
		@return Color transfer function of channel
		"""
		if not self.ctf:
			ctf = vtk.vtkColorTransferFunction()
			minval,maxval = self.getScalarRange()
			LUTName = self.reader.GetImageChannelLUTName(self.imageNum,self.channelNum)
			LUTName = LUTName.lower()
			r,g,b = (0,0,0)
			if LUTName == "red":
				r = 1
			elif LUTName == "green":
				g = 1
			elif LUTName == "blue":
				b = 1
			elif LUTName == "cyan":
				g = 1
				b = 1
			elif LUTName == "yellow":
				r = 1
				g = 1
			else:
				r = 1
				g = 1
				b = 1
			
			ctf.AddRGBPoint(minval,0,0,0)
			ctf.AddRGBPoint(maxval,r,g,b)
			self.ctf = ctf
			
		return self.ctf

	def getBitDepth(self):
		"""
		Returns resolution of the current image's current channel.
		"""
		if not self.bitDepth:
			if self.imageNum < 0 or self.channelNum < 0:
				Logging.error("No image or channel number specified",
							  "Error in LIFDataSource.py in getBitDepth, image or channel number not specified.")
				return 0
			self.bitDepth = self.reader.GetImageChannelResolution(self.imageNum, self.channelNum)
		return self.bitDepth

	def getScalarRange(self):
		"""
		Returns pair that contains range of data values
		"""
		if not self.scalarRange:
			minScalar = self.reader.GetImageChannelMin(self.imageNum,self.channelNum)
			maxScalar = self.reader.GetImageChannelMax(self.imageNum,self.channelNum)
			self.scalarRange = (int(minScalar),int(maxScalar))
		return self.scalarRange

	def createTimeStamps(self):
		"""
		Creates time stamps for setTimeStamps and setAbsoluteTimeStamps methods
		"""
		timeStamps = self.reader.GetTimeStamps(self.imageNum)
		absoluteTimeStamps = []
		relativeTimeStamps = [0.00]
		if timeStamps.GetSize() > 0:
			absoluteTimeStamps = [timeStamps.GetValue(0)]

		timePoints = self.getDataSetCount()
		framesPerTimePoint = self.reader.GetFramesPerTimePoint(self.imageNum)
		if timePoints * framesPerTimePoint > timeStamps.GetSize():
			timePoints = timeStamps.GetSize() / framesPerTimePoint

		for i in range(1,timePoints):
			timeStamp = timeStamps.GetValue(framesPerTimePoint * i)
			earlierTS = timeStamps.GetValue(framesPerTimePoint * (i-1))
			absoluteTimeStamps.append(timeStamp)
			relativeTimeStamps.append((timeStamp - earlierTS)/1000.0 + relativeTimeStamps[i-1])

		self.setTimeStamps(relativeTimeStamps)
		self.setAbsoluteTimeStamps(absoluteTimeStamps)		

	def uniqueID(self):
		"""
		Returns a string identifying the dataset
		"""
		return self.imageName + "|" + self.getName()

	def __str__(self):
		"""
		Returns the basic info of this instance as a string
		"""
		return "LIF DataSource (%s, image %d, channel %d)"%(self.filename,self.imageNum,self.channelNum)
