# -*- coding: iso-8859-1 -*-
"""
 Unit: DataSource.py
 Project: BioImageXD
 Created: 03.11.2004, JM
 Description: Classes for managing 4D data located on disk

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

import vtk
import os.path
import Configuration
import Logging
import scripting
import lib.messenger
import platform
import sys

class DataWriter:
	"""
	 base class for different kinds of DataWriters
	"""
	def __init__(self):
		"""
		Constructor
		"""    
		pass
		
	def sync(self):
		"""
		Write pending imagedata to disk
		"""    
		raise "Abstract method sync() called"
	
	def write(self):
		"""
		Write the data to disk
		"""    
		raise "Abstract method write() called"	  
		
	def addImageData(self, imageData):
		"""
		Add a vtkImageData object to be written to the disk.
		"""    
		raise "Abstract method addImageData"

	def addImageDataObjects(self, imageDataList):		
		"""
		Method: addImageDataObjects(imageDataList)
		Adds a list of vtkImageData objects to be written to the
					  disk. Uses addVtiObject to do all the dirty work
		"""
		raise "Abstract method addImageDataObjects called"
		
class DataSource:
	"""
	Created: 03.11.2004, JM
	Description: A base class for different kinds of DataSources
	"""
	def __init__(self):
		"""
		Initialization
		"""
		self.system = platform.system()
		
		self.ctf = None
		self.bitdepth = 0
		self.resampleFilter = None
		self.mask = None
		self.maskImageFilter = None
		self.mipData = None
		self.resampleDims = None
		self.singleBitDepth = 8
		self.resampledTimepoint = -1
		self.intensityScale = 0
		self.intensityShift = 0
		self.currentTimepoint = 0
		self.scalarRange = None
		self.explicitScale = 0
		self.originalScalarRange = (0, 255)
		self.shift = None
		self.originalDimensions = None
		self.resampleFactors = None
		self.resampledVoxelSize = None
		self.timestamps = []
		self.absoluteTimestamps = []
		
		self.resampling = False

		conf = Configuration.getConfiguration()
		self.autoResampleLimitDimensions = None
		self.autoResampleTargetDimensions = None
		self.filePath = ""
		self.reader = None
		self.vtkFilters = []
		val = None
		try:
			val = eval(conf.getConfigItem("DoResample", "Performance"))
		except:
			pass
		if val:
			self.autoResampleLimitDimensions = eval(conf.getConfigItem("ResampleDims", "Performance"))
			self.autoResampleTargetDimensions = eval(conf.getConfigItem("ResampleTo", "Performance"))
			self.setResampling(True)
			
	def getParser(self):
		return None
		
	def getCurrentTimepoint(self):
		"""
		@return the timepoint that this datasource is reading
		"""
		return self.currentTimepoint
		
	def setCurrentTimepoint(self, timepoint):
		"""
		Set the timepoint that this datasource is reading
		"""
		self.currentTimepoint = timepoint
		
	def setResampling(self, status):
		"""
		enable / disable resampling
		"""
		self.resampling = status
			
	def destroy(self):
		"""
		destroy self
		"""
		del self.reader
		for i in self.vtkFilters:
			del i
		self.vtkFilters = []
			
	def setPath(self, path):
		"""
		Set the path this datasource was created from
		"""   
		self.filePath = path

	def getPath(self):
		"""
		Return the path this datasource was created from
		"""   
		return self.filePath
		
	def setMask(self, mask):
		"""
		Set the mask applied to this dataunit
		"""   
		self.mask = mask
		
	def setResampleDimensions(self, dims):
		"""
		Set the resample dimensions
		"""
		Logging.info("Setting dimensions of resampled image to ",dims,kw="datasource")
		self.resampleDims = [int(dimension) for dimension in dims]
		lib.messenger.send(None, "set_resample_dims", dims, self.originalDimensions)

	def getOriginalScalarRange(self):
		"""
		Return the original scalar range for this dataset
		"""
		return self.originalScalarRange
		
	def getOriginalDimensions(self):
		"""
		Return the original scalar range for this dataset
		"""
		return self.originalDimensions
		
	def getResampleFactors(self):
		"""
		Return the factors for the resampling
		"""
		if not self.resampleFactors and self.resampleDims:		  
			if not self.originalDimensions:
				rd = self.resampleDims
				self.resampleDims = None
				self.resampleDims = rd
			x, y, z = self.originalDimensions
			rx, ry, rz = self.resampleDims
			xf = rx / float(x)
			yf = ry / float(y)
			zf = rz / float(z)
			self.resampleFactors = (xf, yf, zf)
		return self.resampleFactors
		
	def getResampledVoxelSize(self):
		"""
		Return the voxel size for the data after resampling has taken place
		"""
		if not self.resampleDims:
			return None
		if not self.resampledVoxelSize:
			vx, vy, vz = self.getVoxelSize()
			rx, ry, rz = self.getResampleFactors()		  
			self.resampledVoxelSize = (vx / rx, vy / ry, vz / rz)
		return self.resampledVoxelSize
		
	def getResampleDimensions(self):
		"""
		Get the resample dimensions
		"""
		if self.autoResampleLimitDimensions and not self.resampleDims:
			dims = self.getDimensions()
			if dims[0] * dims[1] > self.autoResampleLimitDimensions[0] * self.autoResampleLimitDimensions[1]:
				x, y = self.autoResampleTargetDimensions
				self.resampleDims = (int(x), int(y), int(dims[2]))
		return self.resampleDims

	@staticmethod
	def getCacheKey(datafilename, chName, purpose):
		"""
		Return a unique name based on a filename and channel name that can be used as 
					 a filename for the MIP
		"""
		filename = datafilename.replace("\\", "_")
		filename = filename.replace("/", "_")
		filename = filename.replace(":", "_")
		return filename + "_" + chName + "_" + purpose
		
	def getFromCache(self, datafilename, chName, purpose):
		"""
		Retrieve a MIP image from cache
		"""
		key = self.getCacheKey(datafilename, chName, purpose)
		directory = scripting.get_preview_dir()
		filename = "%s.png" % key
		filepath = os.path.join(directory, filename)
		if not os.path.exists(filepath):
			return None
		reader = vtk.vtkPNGReader()
		reader.SetFileName(filepath)
		reader.Update()
		return reader.GetOutput()
		
	def storeToCache(self, imagedata, datafilename, chName, purpose):
		"""
		Store an image to a cache
		"""
		if imagedata.GetScalarType() not in [3, 5]:
			return
		key = self.getCacheKey(datafilename, chName, purpose)
		writer = vtk.vtkPNGWriter()
		writer.SetInputConnection(imagedata.GetProducerPort())
		directory = scripting.get_preview_dir()
		filename = "%s.png" % key
		filepath = os.path.join(directory, filename)
		#print "Storing to cache", filepath
		writer.SetFileName(filepath)
		writer.Write()
		
	def getMIPdata(self, n):
		"""
		Return a small resampled dataset of which a small
					 MIP can be created.
		"""
		return self.getDataSet(n)
		if not self.mipData:
			x, y, z = self.getDimensions()
			self.mipData = self.getResampledData(self.getDataSet(n, raw = 1), n, resampleToDimensions = (128, 128, z))
		return self.mipData
		
	def getIntensityScale(self):
		"""
		@return the scaling applied to the intensity vaues in the data
		"""
		if self.intensityScale:
			return self.intensityScale
		else:
			minval, maxval = self.originalScalarRange
			scale = 255.0 / maxval
			return scale

	def getIntensityShift(self):
		"""
		@return the shift applied to the intensity values in the data
		"""
		return self.intensityShift
		
	def setIntensityScale(self, shift, scale):
		"""
		Set the factors for scaling and shifting the intensity of
					 the data. Used for emphasizing certain range of intensities
					 in > 8-bit data.
		"""
		self.explicitScale = 1
		self.intensityScale = scale
		self.intensityShift = shift
		
	
	def getIntensityScaledData(self, data):
		"""
		Return the data shifted and scaled to appropriate intensity range
		"""
		if not self.explicitScale:
			return data
		if self.intensityScale == -1:
			return data
		if not self.shift:
			self.shift = vtk.vtkImageShiftScale()
			self.shift.SetOutputScalarTypeToUnsignedChar()
			self.shift.SetClampOverflow(1)
		
		self.shift.SetInputConnection(data.GetProducerPort())
		# Need to call this or it will remember the whole extent it got from resampling
		self.shift.UpdateWholeExtent()

		if self.intensityScale:
			self.shift.SetScale(self.intensityScale)
			currScale = self.intensityScale
		else:
			minval, maxval = self.originalScalarRange
			scale = 255.0 / maxval
			self.shift.SetScale(scale)
			currScale = scale
		
		self.shift.SetShift(self.intensityShift)
		
		Logging.info("Intensity shift = %d, scale = %f"%(self.intensityShift, currScale), kw="datasource")
		
		return self.shift.GetOutput()
	
	def getResampledData(self, data, n, resampleToDimensions = None):
		"""
		Return the data resampled to given dimensions
		"""
		if self.resampling and not scripting.resamplingDisabled:
			currentResamplingDimensions = self.getResampleDimensions()
			# If we're given dimensions to resample to, then we use those
			if resampleToDimensions:
				currentResamplingDimensions = resampleToDimensions
			
			# If the resampling dimensions are not defined (even though resampling is requested)
			# then don't resample the data
			if not currentResamplingDimensions:
				return data
				
			if n == self.resampledTimepoint and self.resampleFilter and not currentResamplingDimensions:
				data = self.resampleFilter.GetOutput()
			else:
				Logging.info("Resampling data to ", self.resampleDims, kw = "datasource")
				if not self.resampleFilter:
					self.resampleFilter = vtk.vtkImageResample()
					x, y, z = self.originalDimensions
					
					rx, ry, rz = currentResamplingDimensions
					xf = rx / float(x)
					yf = ry / float(y)
					zf = rz / float(z)
					self.resampleFilter.SetAxisMagnificationFactor(0, xf)
					self.resampleFilter.SetAxisMagnificationFactor(1, yf)
					self.resampleFilter.SetAxisMagnificationFactor(2, zf)
				else:
					self.resampleFilter.RemoveAllInputs()
				self.resampleFilter.SetInputConnection(data.GetProducerPort())

				data = self.resampleFilter.GetOutput()
		if self.mask:
			if not self.maskImageFilter:
				self.maskImageFilter = vtk.vtkImageMask()
				self.maskImageFilter.SetMaskedOutputValue(0)
			else:
				self.maskImageFilter.RemoveAllInputs()
			self.maskImageFilter.SetImageInput(data)
			self.maskImageFilter.SetMaskInput(self.mask.getMaskImage())
			
			data = self.maskImageFilter.GetOutput()
			
		return data

	def setTimeStamps(self, timestamps):
		"""
		Set the timestamps
		"""
		self.timestamps = timestamps
		
	def setAbsoluteTimeStamps(self, timestamps):
		"""
		Set the absolute timestamps
		"""
		self.absoluteTimestamps = timestamps
		
	def getTimeStamp(self, timepoint):
		"""
		@return the timestamp for given timepoint
		"""
		if len(self.timestamps) > timepoint:
			return self.timestamps[timepoint]
		return timepoint
		
	def getAbsoluteTimeStamp(self, timepoint):
		"""
		Returns a timestamp that is not relative to the beginning of the time series, but
		some absolute time moment before that. This can be used for example, to put several
		different dataunits into a single timeline, provided that their measurement of the
		absolute timestamp begin from the same moment. This could be, for example, the moment
		the microscope was turned on.
		"""
		if len(self.absoluteTimestamps) >= timepoint:
			return self.absoluteTimestamps[timepoint]
		return timepoint

	def getEmissionWavelength(self):
		"""
		Returns the emission wavelength used to image this channel
		managed by this DataSource
		"""
		return 0
			
	def getExcitationWavelength(self):
		"""
		Returns the excitation wavelength used to image this channel
		managed by this DataSource
		"""
		return 0
		
	def getNumericalAperture(self):
		"""
		Returns the numerical aperture used to image this channel
		managed by this DataSource
		"""
		return 0
		
	def getDataSetCount(self):
		"""
		Returns the number of individual DataSets ( = time points)
		managed by this DataSource
		"""
		raise "Abstract method getDataSetCount() in DataSource called"

	def getShortName(self):
		"""
		@return the base filename
		"""
		return os.path.basename(self.getFileName())
		
	def getFileName(self):
		"""
		Return the file name
		"""    
		raise "Abstract method getFileName() called in DataSource"

	def getDataSet(self, i, raw = 0):
		"""
		Returns the DataSet at the specified index
		Parameters:   i		  The index
		"""
		raise "Abstract method getDataSet() in DataSource called"

	def getName(self):
		"""
		Returns the name of the dataset series which this datasource
					 operates on
		"""
		raise "Abstract method getName() in DataSource called"
		
		
	def convertFileName(self, filename):
		"""
		convert the filename to proper encoding
		"""
		if self.system == "Windows": return filename.encode('mbcs')
		return filename.encode(sys.getfilesystemencoding())
		
	def getDimensions(self):
		"""
		Returns the (x, y, z) dimensions of the datasets this 
					 dataunit contains
		"""
		if self.resampleDims and not scripting.resamplingDisabled:
			return self.resampleDims
		if not self.dimensions or sum(self.dimensions)==0:
			self.dimensions = self.internalGetDimensions()
		return self.dimensions[0:3]
		
	def getScalarRange(self):
		"""
		Return the bit depth of data
		"""
		self.getBitDepth()
		return self.scalarRange
		
	def getBitDepth(self):
		"""
		Return the bit depth of data
		"""
		if not self.bitdepth:
			data = self.getDataSet(0, raw = 1)
			data.UpdateInformation()
			self.scalarRange = data.GetScalarRange()
			scalartype = data.GetScalarType()

			if scalartype == 4:
				self.bitdepth = 16
			elif scalartype == 5:
				self.bitdepth = 16
				if max(self.scalarRange) > 4096:
					self.bitdepth = 16
				else:
					self.bitdepth = 12
			elif scalartype == 3:
				self.bitdepth = 8
			elif scalartype == 7:
				self.bitdepth = 16
			elif scalartype == 11:
				self.bitdepth = 16
			else:
				raise "Bad LSM bit depth, %d, %s" % (scalartype, data.GetScalarTypeAsString())
			self.singleBitDepth = self.bitdepth
			self.bitdepth *= data.GetNumberOfScalarComponents()
		return self.bitdepth
	
	def getSingleComponentBitDepth(self):
		"""
		return the bit depth of single component of data
		"""
		if not self.singleBitDepth:
			self.getBitDepth()
		return self.singleBitDepth
		
	def uniqueId(self):
		"""
		return a string identifying the dataset
		"""
		return self.getFileName()
		
	def updateProgress(self, obj, evt):
		"""
		Sends progress update event
		"""
		if not obj:
			progress = 1.0
		else:
			progress = obj.GetProgress()
		notinvtk = 0
		currentTimepoint = self.getCurrentTimepoint()
		timestamp = self.getTimeStamp(currentTimepoint)
		msg = "Reading channel %s of %s"%(self.getName(), self.getShortName())
		
		if currentTimepoint >=0 and self.getDataSetCount()>1:
			msg += " (timepoint %d / %d" % (currentTimepoint+1, self.getDataSetCount())
			msg+=", %.1fs)"%timestamp
		if progress >= 1.0:
			notinvtk = 1
		scripting.inIO = (progress < 1.0)
		if scripting.mainWindow:
			scripting.mainWindow.updateProgressBar(obj, evt, progress,msg, notinvtk)
