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

class DataWriter:
	"""
	Created: 26.03.2005
	Description: A base class for different kinds of DataWriters
	"""
	def __init__(self):
		"""
		Created: 26.03.2005
		Description: Constructor
		"""    
		pass
		
	def sync(self):
		"""
		Created: 26.03.2005
		Description: Write pending imagedata to disk
		"""    
		raise "Abstract method sync() called"
	
	def write(self):
		"""
		Created: 26.03.2005
		Description: Write the data to disk
		"""    
		raise "Abstract method write() called"	  
		
	def addImageData(self, imageData):
		"""
		Created: 26.03.2005, KP
		Description: Add a vtkImageData object to be written to the disk.
		"""    
		raise "Abstract method addImageData"

	def addImageDataObjects(self, imageDataList):		
		"""
		Method: addImageDataObjects(imageDataList)
		Created: 26.03.2005, KP
		Description: Adds a list of vtkImageData objects to be written to the
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
		Created: 17.11.2004, KP
		Description: Initialization
		"""
		self.ctf = None
		self.bitdepth = 0
		self.resample = None
		self.mask = None
		self.maskImg = None
		self.mipData = None
		self.resampleDims = None
		self.singleBitDepth = 8
		self.resampleTp = -1
		self.intensityScale = 0
		self.intensityShift = 0
		self.scalarRange = None
		self.explicitScale = 0
		self.originalScalarRange = (0, 255)
		self.shift = None
		self.originalDimensions = None
		self.resampleFactors = None
		self.resampledVoxelSize = None

		conf = Configuration.getConfiguration()
		self.limitDims = None
		self.toDims = None
		self.filePath = ""
		self.reader = None
		self.vtkFilters = []
		val = None
		try:
			val = eval(conf.getConfigItem("DoResample", "Performance"))
		except:
			pass
		if val:
			self.limitDims = eval(conf.getConfigItem("ResampleDims", "Performance"))
			self.toDims = eval(conf.getConfigItem("ResampleTo", "Performance"))

	def getParser(self):
		return None
			
	def destroy(self):
		"""
		Created: 27.1.2007, KP
		Description: destroy self
		"""
		del self.reader
		for i in self.vtkFilters:
			del i
		self.vtkFilters = []
			
	def setPath(self, path):
		"""
		Created: 17.07.2006, KP
		Description: Set the path this datasource was created from
		"""   
		self.filePath = path

	def getPath(self):
		"""
		Created: 17.07.2006, KP
		Description: Return the path this datasource was created from
		"""   
		return self.filePath
		
	def setMask(self, mask):
		"""
		Created: 20.06.2006, KP
		Description: Set the mask applied to this dataunit
		"""   
		self.mask = mask
		
	def setResampleDimensions(self, dims):
		"""
		Created: 1.09.2005, KP
		Description: Set the resample dimensions
		"""
		Logging.info("Setting dimensions of resampled image to ",dims,kw="datasource")
		#self.resampleDims = map(int, dims)
		self.resampleDims = [int(dimension) for dimension in dims]
		lib.messenger.send(None, "set_resample_dims", dims, self.originalDimensions)

	def getOriginalScalarRange(self):
		"""
		Created: 12.04.2006, KP
		Description: Return the original scalar range for this dataset
		"""				   
		return self.originalScalarRange
		
	def getOriginalDimensions(self):
		"""
		Created: 12.04.2006, KP
		Description: Return the original scalar range for this dataset
		"""				
		return self.originalDimensions
		
	def getResampleFactors(self):
		"""
		Created: 07.04.2006, KP
		Description: Return the factors for the resampling
		"""		   
		if not self.resampleFactors and self.resampleDims:		  
			if not self.originalDimensions:
				rd = self.resampleDims
				self.resampleDims = None
				self.resampleDims = rd
			#print "Original dimensions = ", self.originalDimensions
			x, y, z = self.originalDimensions
			rx, ry, rz = self.resampleDims
			#print "Reasmple dimensions = ", self.resampleDims
			xf = rx / float(x)
			yf = ry / float(y)
			zf = rz / float(z)
			self.resampleFactors = (xf, yf, zf)
			#print "Resample factors = ", self.resampleFactors
		return self.resampleFactors
		
	def getResampledVoxelSize(self):
		"""
		Created: KP
		Description: Return the voxel size for the data after resampling has taken place
		"""
		if not self.resampleDims:
			return None
		if not self.resampledVoxelSize:
			vx, vy, vz = self.getVoxelSize()
			rx, ry, rz = self.getResampleFactors()		  
			#print "\n\n****resample factors = ", rx, ry, rz
			self.resampledVoxelSize = (vx / rx, vy / ry, vz / rz)
		return self.resampledVoxelSize
		
	def getResampleDimensions(self):
		"""
		Created: 11.09.2005, KP
		Description: Get the resample dimensions
		"""
		if self.limitDims and not self.resampleDims:
			dims = self.getDimensions()
			if dims[0] * dims[1] > self.limitDims[0] * self.limitDims[1]:
				x, y = self.toDims
				self.resampleDims = (int(x), int(y), int(dims[2]))
		return self.resampleDims

	@staticmethod
	def getCacheKey(datafilename, chName, purpose):
		"""
		Created: 07.11.2006, KP
		Description: Return a unique name based on a filename and channel name that can be used as 
					 a filename for the MIP
		"""
		filename = datafilename.replace("\\", "_")
		filename = filename.replace("/", "_")
		filename = filename.replace(":", "_")
		return filename + "_" + chName + "_" + purpose
		
	def getFromCache(self, datafilename, chName, purpose):
		"""
		Created: 07.11.2006, KP
		Description: Retrieve a MIP image from cache
		"""
		key = self.getCacheKey(datafilename, chName, purpose)
		#print "KEY = ", key
		directory = scripting.get_preview_dir()
		#print "\n\nPREWVIEW DIR = ", directory
		filename = "%s.png" % key
		filepath = os.path.join(directory, filename)
		if not os.path.exists(filepath):
			#print "File ", filename, "ch", chName, "not in cache"
			return None
		#print "File ", filepath, "ch", chName, "IS in cache"
		reader = vtk.vtkPNGReader()
		reader.SetFileName(filepath)
		reader.Update()
		return reader.GetOutput()
		
	def storeToCache(self, imagedata, datafilename, chName, purpose):
		"""
		Created: 07.11.2006, KP
		Description: Store an image to a cache
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
		print "Wrote ", purpose
		Logging.backtrace()
		
	def getMIPdata(self, n):
		"""
		Created: 05.06.2006, KP
		Description: Return a small resampled dataset of which a small
					 MIP can be created.
		"""				  
		return self.getDataSet(n)
		if not self.mipData:
			x, y, z = self.getDimensions()
			self.mipData = self.getResampledData(self.getDataSet(n, raw = 1), n, tmpDims = (128, 128, z))
		return self.mipData
		
	def getIntensityScale(self):
		"""
		Created: 27.04.2007, KP
		Description: return the shift and scale applied to the data as tuple
		"""
		return self.intensityShift, self.intensityScale
		
	def setIntensityScale(self, shift, scale):
		"""
		Created: 12.04.2006, KP
		Description: Set the factors for scaling and shifting the intensity of
					 the data. Used for emphasizing certain range of intensities
					 in > 8-bit data.
		"""					   
		self.explicitScale = 1
		self.intensityScale = scale
		self.intensityShift = shift
		
	
	def getIntensityScaledData(self, data):
		"""
		Created: 12.04.2006, KP
		Description: Return the data shifted and scaled to appropriate intensity range
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
			#x0, x1 = data.GetScalarRange()
			#if x1 == 0:
			#	 scale = 1.0
			#else:
			#	 scale = 255.0/x1
			minval, maxval = self.originalScalarRange
			#print "Calculating intensity scale based on bitdepth = ", self.bitdepth
			scale = 255.0 / maxval
			self.shift.SetScale(scale)
			currScale = scale
		
		self.shift.SetShift(self.intensityShift)
		
		Logging.info("Intensity shift = %d, scale = %f"%(self.intensityShift, currScale), kw="datasource")
		
		return self.shift.GetOutput()
	
	def getResampledData(self, data, n, tmpDims = None):
		"""
		Created: 1.09.2005, KP
		Description: Return the data resampled to given dimensions
		"""
		if not scripting.resamplingDisabled and not (not tmpDims and not self.resampleDims and not self.limitDims):
			
			useDims = self.getResampleDimensions()
			if tmpDims:
				useDims = tmpDims
			if not useDims:
				return data
			if n == self.resampleTp and self.resample and not useDims:
				data = self.resample.GetOutput()
			else:
				Logging.info("Resampling data to ", self.resampleDims, kw = "dataunit")
				self.resample = vtk.vtkImageResample()
				self.resample.SetInputConnection(data.GetProducerPort())
				# Release the memory used by source data
				#print "data = ", data
				
				#x, y, z = data.GetDimensions()
				#print "got dims = ", x, y, z
				#self.originalDimensions = (x, y, z)
				x, y, z = self.originalDimensions
				
				rx, ry, rz = useDims
				xf = rx / float(x)
				yf = ry / float(y)
				zf = rz / float(z)
				#print "origi dims = ", x, y, z
				#print "dism to resample to ", rx, ry, rz
				
				self.resample.SetAxisMagnificationFactor(0, xf)
				self.resample.SetAxisMagnificationFactor(1, yf)
				self.resample.SetAxisMagnificationFactor(2, zf)
				#self.resample.Update()				   
				#newdata = scripting.execute_limited(self.resample)
				#data.ReleaseData()
				#data = newdata
				data = self.resample.GetOutput()		   
		if self.mask:
			if not self.maskImg:
				self.maskImg = vtk.vtkImageMask()
				self.maskImg.SetMaskedOutputValue(0)
			else:
				self.maskImg.RemoveAllInputs()
			self.maskImg.SetImageInput(data)
			self.maskImg.SetMaskInput(self.mask.getMaskImage())
			
			#self.maskImg.Update()
			#newdata = scripting.execute_limited(self.maskImg)

			#data.ReleaseData()
			data = self.maskImg.GetOutput()
			
		return data

	def getTimeStamp(self, timepoint):
		"""
		Created: 02.07.2007, KP
		Description: return the timestamp for given timepoint
		"""
		return timepoint

	def getEmissionWavelength(self):
		"""
		Created: 07.04.2006, KP
		Description: Returns the emission wavelength used to image this channel
		managed by this DataSource
		"""
		return 0
			
	def getExcitationWavelength(self):
		"""
		Created: 07.04.2006, KP
		Description: Returns the excitation wavelength used to image this channel
		managed by this DataSource
		"""
		return 0
		
	def getNumericalAperture(self):
		"""
		Created: 07.04.2006, KP
		Description: Returns the numerical aperture used to image this channel
		managed by this DataSource
		"""
		return 0
		
	def getDataSetCount(self):
		"""
		Created: 03.11.2004, JM
		Description: Returns the number of individual DataSets ( = time points)
		managed by this DataSource
		"""
		raise "Abstract method getDataSetCount() in DataSource called"

	def getFileName(self):
		"""
		Created: 21.07.2005
		Description: Return the file name
		"""    
		raise "Abstract method getFileName() called in DataSource"

	def getDataSet(self, i, raw = 0):
		"""
		Created: 03.11.2004, JM
		Description: Returns the DataSet at the specified index
		Parameters:   i		  The index
		"""
		raise "Abstract method getDataSet() in DataSource called"

	def getName(self):
		"""
		Created: 18.11.2004, KP
		Description: Returns the name of the dataset series which this datasource
					 operates on
		"""
		raise "Abstract method getName() in DataSource called"
		
	def getDimensions(self):
		"""
		Created: 14.12.2004, KP
		Description: Returns the (x, y, z) dimensions of the datasets this 
					 dataunit contains
		"""
		raise "Abstract method getDimensions() in DataSource called"

	def getScalarRange(self):
		"""
		Created: 28.05.2005, KP
		Description: Return the bit depth of data
		"""
		self.getBitDepth()
		return self.scalarRange
		
	def getBitDepth(self):
		"""
		Created: 28.05.2005, KP
		Description: Return the bit depth of data
		"""
		if not self.bitdepth:
			
			data = self.getDataSet(0, raw = 1)
			data.UpdateInformation()
			self.scalarRange = data.GetScalarRange()
			#print "Scalar range of data", self.scalarRange
			scalartype = data.GetScalarType()
			#print "Scalar type", scalartype, data.GetScalarTypeAsString()
			#print "Number of scalar components", data.GetNumberOfScalarComponents()
		
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
		Created: 13.06.2007, KP
		Description: return the bit depth of single component of data
		"""
		if not self.singleBitDepth:
			self.getBitDepth()
		return self.singleBitDepth
		
	def uniqueId(self):
		"""
		Created: 07.02.2007, KP
		Description: return a string identifying the dataset
		"""
		return self.getFileName()
