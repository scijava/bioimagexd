# -*- coding: iso-8859-1 -*-
"""
 Unit: OMETIFFDataSource.py
 Project: BioImageXD
 Description: OME-TIFF file data source

 Copyright (C) 2012 BioImageXD Project
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

__author__ = "BioImageXD Project <http://www.bioimagexd.net/>"
__version__ = "$Revision$"
__date__ = "$Date$"

from lib.DataSource.DataSource import DataSource
from lib.DataUnit import DataUnit
import Logging
import vtk
import vtkbxd

def getExtensions():
	return ["ome.tif", "ome.tiff"]

def getFileType():
	return "OME-TIFF datasets (*.ome.tif)"

def getClass():
	return OMETIFFDataSource

class OMETIFFDataSource(DataSource):
	"""
	OMETIFFDataSource class
	"""
	def __init__(self, filename = "", imageNum = 0, channelNum = 0):
		"""
		Constructor
		"""
		DataSource.__init__(self)
		self.filename = filename
		self.numImages = 1
		self.numChannels = 1
		self.currentImage = imageNum
		self.currentChannel = channelNum
		self.currentTimePoint = 0
		self.imageName = ""
		self.reader = vtkbxd.vtkOMETIFFReader()

		self.ctf = None
		
		if self.filename:
			self.reader.SetFileName(self.convertFileName(self.filename))
			if not self.reader.ReadOMEHeader():
				Logging.error("Failed to open OME-TIFF file",
							"Failed to open file %s for reading: %s"%(filename, str(ex)))
				return
			
			self.numImages = self.reader.GetNumberOfImages()
			if self.currentImage < self.numImages:
				self.reader.SetCurrentImage(self.currentImage)
			self.numChannels = self.reader.GetNumberOfChannels()
			if self.currentChannel < self.numChannels:
				self.reader.SetCurrentChannel(self.currentChannel)
			self.imageName = self.reader.GetImageName()
			if self.imageName == "":
				self.imageName = "Image-%d"%(self.currentImage+1)

	def getDataSetCount(self):
		"""
		Returns the count of time points of the selected OME image
		"""
		return self.reader.GetNumberOfTimePoints()
		
	def getFileName(self):
		"""
		Returns the file name with image name
		"""
		return self.filename + "_" + self.imageName

	def getDataSet(self, i, raw = 0):
		"""
		Returns the defined timepoint of current image and channel
		@param i The timepoint of data to return
		@param raw A flag indicating that the data is not to be processed in any way
		"""
		if i < 0 or i >= self.getDataSetCount():
			Logging.error("Given time point is out of bounds",
						  "Time point %d requested is out of bounds"%i)
			return None

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
		Returns the name of the dataset
		"""
		channelName = self.reader.GetChannelName()
		if channelName == "":
			return "Ch-%d"%(self.currentChannel + 1)
		return channelName

	def getExcitationWavelength(self):
		"""
		Returns excitation wavelength of this channel
		"""
		return self.reader.GetExcitationWavelength()

	def getEmissionWavelength(self):
		"""
		Returns emission wavelength of this channel
		"""
		return self.reader.GetEmissionWavelength()
		
	def internalGetDimensions(self):
		"""
		Returns the (x,y,z,t) dimensions of the dataset this dataunit contains
		@return 4-tuple of dimensions of the dataset
		"""
		dim = self.reader.GetImageDimensions()
		dim = list(dim)
		dim.append(self.reader.GetNumberOfTimePoints())
		for i in range(4):
			if  dim[i] <= 0:
				dim[i] = 1
		
		dim = tuple(dim)
		return dim

	def loadFromFile(self, filename):
		"""
		Loads images from OME-TIFF file and generates own DataSource
		for each image in file.
		Returns list of tuples that include image name and DataUnit.
		@parameter filename Path to file from where images should be loaded
		"""
		self.filename = filename
		dataUnits = []
		self.reader.SetFileName(self.convertFileName(self.filename))

		if self.reader.ReadOMEHeader():
			imageNum = self.reader.GetNumberOfImages()
			imageNames = []
			for i in range(imageNum):
				imageName = self.reader.GetImageName()
				if imageName == "":
					imageName = "Image-%d"%(i+1)
				if imageName in imageNames:
					imageName = imageName + "-%d"%(i+1)
				imageNames.append(imageName)
			
			for i,imageName in enumerate(imageNames):
				self.reader.SetCurrentImage(i)
				channelNum = self.reader.GetNumberOfChannels()
				for c in range(channelNum):
					datasource = OMETIFFDataSource(filename,i,c)
					dataunit = DataUnit.DataUnit()
					dataunit.setDataSource(datasource)
					dataunit.updateSettings()
					dataUnits.append((imageName,dataunit))
		else:
			Logging.error("Failed to read OME header",
						  "Error in OMETIFFDataSource.py in loadFromFile, failed to read OME header from file: %s"%self.filename)

		return dataUnits

	def getSpacing(self):
		"""
		Returns normalized spacing between voxels
		"""
		voxelSize = self.getVoxelSize()
		if voxelSize[0] == 0.0:
			return (1.0, 1.0, 1.0)
		return (1.0, voxelSize[1] / voxelSize[0], voxelSize[2] / voxelSize[0])

	def getVoxelSize(self):
		"""
		Returns physical size of voxels as micrometers
		"""
		voxelSize = self.reader.GetVoxelSize()
		voxelSize = list(voxelSize)
		for i in range(3):
			voxelSize[i] = voxelSize[i] * 10**-6
		return tuple(voxelSize)

	def getColorTransferFunction(self):
		"""
		Creates color transfer function for channel
		"""
		if not self.ctf:
			ctf = vtk.vtkColorTransferFunction()
			minval,maxval = self.getScalarRange()
			ctf.AddRGBPoint(minval,0,0,0)
			ctf.AddRGBPoint(maxval,1,1,1)
			self.ctf = ctf
		
		return self.ctf

	def getBitDepth(self):
		"""
		Return the bit depth of data
		"""
		if not self.bitdepth:
			scalartype = self.reader.GetPixelType()
			self.scalarRange = (0,0)

			if scalartype in [2,3]:
				self.bitdepth = 8
				self.scalarRange = (0,255)
			elif scalartype in [4,5]:
				self.bitdepth = 16
			elif scalartype in [6,7,10]:
				self.bitdepth = 32
			elif scalartype == 11:
				self.bitdepth = 64

			if self.scalarRange == (0,0):
				data = self.getDataSet(0, raw = 1)
				data.Update()
				self.scalarRange = data.GetScalarRange()
				if self.scalarRange[0] >= 0 and self.scalarRange[1] <= 4095:
					self.bitdepth = 12
					self.scalarRange = (0,4095)
			self.singleBitDepth = self.bitdepth

		return self.bitdepth

	def uniqueID(self):
		"""
		Return a unique string identifying the dataset
		"""
		return self.imageName + "|" + self.getName()

	def __str__(self):
		"""
		Returns the basic info of this instance
		"""
		return "OMETIFF DataSource (%s, image %d, channel %d)"%(self.filename, self.currentImage, self.currentChannel)
	
