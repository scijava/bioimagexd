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
import Logging
from lib.DataUnit import DataUnit
import vtkbxd
import vtk
def getExtensions(): return ["lif"]
def getFileType(): return "Leica Image File Format (*.lif)"
def getClass(): return LIFDataSource

class LIFDataSource(DataSource):
	"""
	Created: 19.07.2007, LP
	Description: Manages 4D data stored in a LIF-file.
	"""

	def __init__(self, filename = "", imageNum = -1, channelNum = -1):
		"""
		Created: 19.07.2007, LP
		Description: Constructor of LIF DataSource
		"""
		DataSource.__init__(self)
		self.filename = filename
		# LIF file can contain multiple images with multiple channels.
		# Define which image and channel is associated to this DataSource
		self.imageNum = imageNum
		self.channelNum = channelNum
		self.bitDepth = 0
		
		self.spacing = None
		self.voxelSize = None
		self.dimensions = None
		self.ctf = None
		
		# Use vtkLIFReader
		self.reader = vtkbxd.vtkLIFReader()

		# Open file if defined
		if self.filename:
			self.reader.SetFileName(self.filename)
			if self.reader.OpenFile():
				if self.reader.ReadLIFHeader():
					self.reader.SetCurrentImage(self.imageNum)
					self.reader.SetCurrentChannel(self.channelNum)
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
		Created: 24.07.2007, LP
		Description: Returns the count of time points of the data set
		"""
		if not self.dimensions:
			self.getDimensions()
		return self.dimensions[3]

	def getFileName(self):
		"""
		Created: 23.07.2007, LP
		Description: Returns the file name
		"""
		return self.filename;

	def getDataSet(self, i, raw = 0):
		"""
		Created 24.07.2007, LP
		Description: Returns the defined timepoint of current image and channel
		Parameters: i	 The timepoint of data to return
					raw	 A flag indicating that the data is not to be processed
						 in any way
		"""
		if self.imageNum < 0 or self.channelNum < 0:
			Logging.error("No image or channel number specified",
						  "Error in LIFDataSource.py in getDataSet, no image or channel number specified.")
			return None
		
		if i < 0 or (i > 0 and i >= self.getDataSetCount()):
			Logging.error("Given time point is out of bounds",
						  "Time point %d that is out of bounds requested from getDataSet"%i)
			return None

		self.reader.SetCurrentImageAndChannel(self.imageNum, self.channelNum)
		self.reader.SetCurrentTimePoint(i)
		data = self.reader.GetOutput()

		if raw:
			return data

#        data = self.getIntensityScaledData(data)
		return data	

	def getName(self):
		"""
		Created: 20.07.2007, LP
		Description: Returns the name of the dataset handled by this DataSource
		"""
		if self.imageNum < 0 or self.channelNum < 0:
			Logging.error("Image or channel number not specified",
						  "Error in LIFDataSource.py in getName, no image or channel specified.")
			return ""
		return "Ch-%d"%(self.channelNum + 1)

	def getDimensions(self):
		"""
		Created 20.07.2007, LP
		Description: Returns the (x,y,z) dimensions of the dataset this
					 dataunit contains
		"""
		if not self.dimensions:
#			 self.dimensions = self.reader.GetImageDimensions(self.imageNum)
			self.reader.SetImageDimensions(self.imageNum)
			self.dimensions = self.reader.GetDims()
		return self.dimensions[0:3]

	def loadFromFile(self, filename):
		"""
		Created: 20.07.2007, LP
		Description: Loads images from LIF-file and generates own DataSource
					 for each image in file. Returns list of tuples which
					 includes image name and DataUnit.
		Parameters:	 filename: path to file where images should be loaded
		"""
		self.filename = filename
		dataUnits = []
		self.reader.SetFileName(self.filename)

		if self.reader.OpenFile():
			if self.reader.ReadLIFHeader():
				imageCount = self.reader.GetImageCount()
				for i in range(imageCount):
					imageName = self.reader.GetImageName(i)
					imageChannels = self.reader.GetChannelCount(i)
					for c in range(imageChannels):
						dataSource = LIFDataSource(filename,i,c)
						dataUnit = DataUnit.DataUnit()
						dataUnit.setDataSource(dataSource)
#						 dataUnits.append(dataUnit)
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
		Created: 20.07.2007, LP
		Description: Returns normalized spacing between voxels
		"""
		if not self.spacing:
#			 x,y,z = self.reader.GetImageVoxelSizes(self.imageNum)
			x, y, z = self.getVoxelSize()
			self.spacing = [1, y / x, z / x]
		return self.spacing

	def getVoxelSize(self):
		"""
		Created: 20.07.2007, LP
		Description: Returns size of voxel as 3-tuple
		"""
		if not self.voxelSize:
#			 self.voxelSize = self.reader.GetImagesVoxelSizes(self.imageNum)
			self.reader.SetImageVoxelSizes(self.imageNum)
			self.voxelSize = self.reader.GetVoxelss()
		return self.voxelSize

	def getColorTransferFunction(self):
		"""
		Created: 24.07.2007, LP
		Description:
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
			else:
				b = 1
			
			ctf.AddRGBPoint(minval,0,0,0)
			ctf.AddRGBPoint(maxval,r,g,b)
			self.ctf = ctf
			
		return self.ctf

	def resetColorTransferFunction(self):
		"""
		Created: 03.08.2007, LP
		Description: Resets the CTF of the data source.
		"""
		self.ctf = None
		return self.getColorTransferFunction()

	def getBitDepth(self):
		"""
		Created: 24.07.2007, LP
		Description: Returns resolution of the current image's current channel.
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
		Created: 24.07.2007, LP
		Description: Returns pair that contains range of data values
		"""
		if not self.scalarRange:
			bitDepth = self.getBitDepth()
			self.scalarRange = (0,2**bitDepth-1)
		return self.scalarRange

	def uniqueID(self):
		"""
		Created: 01.08.2007, LP
		Description: Returns a string identifying the dataset
		"""
		imageName = self.reader.GetImageName(self.imageNum)
		return imageName + "|" + self.getName()

	def __str__(self):
		"""
		Created: 03.08.2007, LP
		Description: Returns the basic info of this instance as a string
		"""
		return "LIF DataSource (%s, image %d, channel %d)"%(self.filename,self.imageNum,self.channelNum)

