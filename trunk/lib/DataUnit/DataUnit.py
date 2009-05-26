# -*- coding: iso-8859-1 -*-
"""
 Unit: DataUnit.py
 Project: BioImageXD
 Created: 03.11.2004, JM
 Description: Classes for 4D DataUnits
		   
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
__version__ = "$Revision: 1.93 $"
__date__ = "$Date: 2005/01/13 14:09:15 $"

import bxdexceptions
import DataUnitSetting
import lib.ImageOperations
import Logging
import os

class DataUnit:
	"""
	Description: A class representing a timeseries of 3D data
	"""
	def __init__(self, dataUnitName = "", initToNone = 1):
		"""
		Constructor
		Parameters: dataUnitName, Name for the DataUnit, default to ""
		"""
		self.dataUnitName = dataUnitName
		self.length = 0
		self.dataSource = None

		self.color = None
		self.ctf = None
		self.randomCTF = None
		self.cacheKey = None
		self.settings = DataUnitSetting.DataUnitSettings()
		self.mip = None
		self.mipTimepoint = -1
		self.destroyed = 0

		if initToNone:
			self.getResampledVoxelSize = None 
			self.getVoxelSize = None
			self.getScalarRange = None
			self.getDimensions = None
			self.getSpacing = None
			self.getSingleComponentBitDepth = None
			self.getNumericalAperture = None
			self.getBitDepth = None
			self.getExcitationWavelength = None
			self.getEmissionWavelength = None
			
	def setNumberOfTimepoints(self, timepoints):
		"""
		Set the number of timepoits
		"""
		self.length = timepoints

	def getDimensions(self):
		"""
		@since: 27.07.2007
		@author: SG
		Abstract method for getting the dimensions of this DataUnit
		"""
		raise bxdexceptions.AbstractMethodCalled()

	def setCacheKey(self, key):
		"""
		Set the key under which this dataunit is stored in the cache
		"""
		self.cacheKey = key

	def getCacheKey(self):
		"""
		Get the key under which this dataunit is stored in the cache
		"""
		return self.cacheKey

	def destroySelf(self):
		"""
		finalize self
		"""
		self.dataSource.destroy()
		del self.dataSource
		del self.settings
		self.dataSource = None
		self.settings = None
		self.destroyed = 1

	def resetSettings(self):
		"""
		Reset the settings of this dataunit. This is done for example after a task
					 has been closed to reset the dataunit back to it's original state
		"""
		self.settings.resetSettings()
		self.settings = DataUnitSetting.DataUnitSettings()
		
	def setMask(self, mask):
		"""
		Set the mask applied to this dataunit
		"""   
		self.dataSource.setMask(mask)

	def isProcessed(self):
		"""
		A method for querying whether this dataset is a processed one
		"""    
		return 0


	def getDataSource(self):
		"""
		Returns the data source of this dataset
		"""		   
		return self.dataSource
		
	def getMIP(self, mipTimepoint, color, small = 0, noColor = 0):
		"""
		Returns MIP of the given timepoint
		"""		   
		if self.mip and self.mipTimepoint == mipTimepoint:
			#Logging.info("Using existing MIP")
			return self.mip
		else:
			#Logging.info("Generating MIP of timepoint = ", mitTimepoint)
			if not small:
				imagedata = self.getTimepoint(mipTimepoint)
			else:
				cached = self.dataSource.getFromCache(self.getFileName(), self.getName(), "MIP")
				if not cached:
					imagedata = self.dataSource.getMIPdata(mipTimepoint)
					imagedata.Update()
		
					if not color and not noColor:
						color = self.getColorTransferFunction()
					self.mip = lib.ImageOperations.getMIP(imagedata, color)
					
					self.dataSource.storeToCache(self.mip, self.getFileName(), self.getName(), "MIP")
				else:
					self.mip = cached
					
			return self.mip
	
	def storeToCache(self, imagedata, timepoint, purpose):
		"""
		Store any image data along with it's timepoint and purpose to the cached
		"""
		self.dataSource.storeToCache(imagedata, self.getFileName(), self.getName(), 
			"%s_tp%d" % (purpose, timepoint))

	def getFromCache(self, timepoint, purpose):
		"""
		Retrieve from cache any image data by it's purpose and timepoint
		"""
		return self.dataSource.getFromCache(self.getFileName(), self.getName(), "%s_tp%d" % (purpose, timepoint))
		
		
	def resetColorTransferFunction(self):
		"""
		A method that will reset the CTF from the datasource.
					 This is useful e.g. when scaling the intensities of the	
					 dataset
		"""
		self.ctf = None
		if self.dataSource:
			self.dataSource.resetColorTransferFunction()
		ctf = self.getColorTransferFunction()
		self.settings.set("ColorTransferFunction", ctf)

	def getColorTransferFunction(self):
		"""
		Returns the ctf of this object
		"""
		
		if not self.dataSource and not self.ctf:
			Logging.backtrace()
			Logging.info("Using no ctf because datasource = ", self.dataSource, kw = "ctf")
			return None
		if not self.ctf:
			self.ctf = self.dataSource.getColorTransferFunction()
			#Logging.info("Ctf from datasource = ", self.ctf, kw = "ctf")
		return self.ctf
	
	
	def setSettings(self, settings):
		"""
		Sets the settings object of this dataunit
		"""
		self.settings = settings
		self.updateSettings()
	
	def updateSettings(self):
		"""
		Sets the settings of this object based on the datasource
		"""
		if not self.settings:
			Logging.info("No settings present, won't update", kw = "dataunit")
			return
		if not (self.settings and self.settings.get("ColorTransferFunction")):
			ctf = self.getColorTransferFunction()
			# Watch out not to overwrite the palette
			#self.ctf = self.settings.get("ColorTransferFunction")
			#ctf = self.ctf
			self.settings.set("ColorTransferFunction", ctf)
			#if ctf and self.settings.get("Type") == "ColorMergingSettings":
			#	 self.settings.set("MergingColorTransferFunction", ctf)
		
		if self.dataSource:
			self.settings.set("VoxelSize", self.dataSource.getVoxelSize())
			self.settings.set("Spacing", self.dataSource.getSpacing())
			self.settings.set("Dimensions", self.dataSource.getDimensions())
			self.settings.set("BitDepth", self.dataSource.getBitDepth())
			self.settings.set("EmissionWavelength", self.dataSource.getEmissionWavelength())
			self.settings.set("ExcitationWavelength", self.dataSource.getExcitationWavelength())
			self.settings.set("NumericalAperture", self.dataSource.getNumericalAperture())
			self.settings.set("TimeStamps", self.dataSource.getTimeStamps())
			self.settings.set("AbsoluteTimeStamps", self.dataSource.getAbsoluteTimeStamps())
			
	def getSettings(self):
		"""
		Returns the settings object of this dataunit
		"""
		return self.settings
		
	def getName(self):
		"""
		Returns the name of this DataUnit
		"""
		return self.dataUnitName

	def setName(self, dataUnitName):
		"""
		Sets the name of this dataunit
		"""
		self.dataUnitName = dataUnitName
		if self.settings:
			self.settings.set("Name", dataUnitName)
 
	def getTimepoint(self, timepoint):
		"""
		Returns the requested time point
		@param timepoint	The timepoint to read
		"""
		if not self.dataSource:
			Logging.error("No datasource specified",
			"No datasource specified for DataUnit, unable to get timepoint!")
			return None
		return self.dataSource.getDataSet(timepoint)

	def getPolyDataAtTimepoint(self, timepoint):
		"""
		@return the vtkPolyData object representing the dataset at given timepoint
		"""
		if not self.dataSource:
			Logging.error("No datasource specified",
			"No datasource specified for DataUnit, unable to get timepoint!")
			return None
		return self.dataSource.getPolyData(timepoint)

	def getNumberOfTimepoints(self):
		"""
		Returns the length of this DataUnit
		"""
		return self.length

	def setDataSource(self, dataSource):
		"""
		Sets a DataSource for this SourceDataUnit
		Parameters: dataSource	A DataSource to manage actual
								image data located on disk
		"""
		# Then load the settings specific to SourceDataUnit:
		self.dataSource = dataSource
		self.dataUnitName = dataSource.getName()
		self.length = dataSource.getDataSetCount()
		self.getTimeStamp = dataSource.getTimeStamp
		self.getAbsoluteTimeStamp = dataSource.getAbsoluteTimeStamp
		self.getDimensions = dataSource.getDimensions
		self.getSpacing = dataSource.getSpacing
		self.getVoxelSize = dataSource.getVoxelSize
		self.getResampledVoxelSize = dataSource.getResampledVoxelSize
		self.getBitDepth = dataSource.getBitDepth
		self.getSingleComponentBitDepth = dataSource.getSingleComponentBitDepth
		self.getScalarRange = dataSource.getScalarRange
		self.getEmissionWavelength = dataSource.getEmissionWavelength
		self.getExcitationWavelength = dataSource.getExcitationWavelength
		self.getNumericalAperture = dataSource.getNumericalAperture
	
	def getFileName(self):
		"""
		Return the path to the file this dataunit represents
		"""
		if self.dataSource:
			return self.dataSource.getFileName()
		return "unnamed"

	def getDataUnitCount(self):
		"""
		Return count of dataunits
		"""
		return 1
	
	def __str__(self):
		return "<DataUnit:"+ os.path.basename(self.getFileName())+":"+self.getName()+">"
	
	def __repr__(self):
		return str(self)
