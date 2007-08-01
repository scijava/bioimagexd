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

#import vtk

import Logging
import lib.ImageOperations
import weakref
import DataUnitSetting

class DataUnit:
	"""
	Created: 03.11.2004, JM
	Description: A class representing a timeseries of 3D data
	"""

	def __init__(self, dataUnitName = ""):
		"""
		Created: 03.11.2004, JM
		Description: Constructor
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
		
	def setCacheKey(self,key):
		"""
		Created: 23.10.2006, KP
		Description: Set the key under which this dataunit is stored in the cache
		"""
		self.cacheKey = key

	def getCacheKey(self):
		"""
		Created: 23.10.2006, KP
		Description: Get the key under which this dataunit is stored in the cache
		"""
		return self.cacheKey

	def destroySelf(self):
		"""
		Created: 27.1.2007, KP
		Description: finalize self
		"""
		self.dataSource.destroy()
		del self.dataSource
		del self.settings
		self.dataSource = None
		self.settings = None
		self.destroyed = 1

	def resetSettings(self):
		"""
		Created: 23.10.2006, KP
		Description: Reset the settings of this dataunit. This is done for example after a task
					 has been closed to reset the dataunit back to it's original state
		"""
		self.settings.resetSettings()
		self.settings = DataUnitSetting.DataUnitSettings()
		
	def setMask(self, mask):
		"""
		Created: 20.06.2006, KP
		Description: Set the mask applied to this dataunit
		"""   
		self.dataSource.setMask(mask)

	def isProcessed(self):
		"""
		Created: 31.05.2005, KP
		Description: A method for querying whether this dataset is a processed one
		"""    
		return 0


	def getDataSource(self):
		"""
		Created: 12.04.2006, KP
		Description: Returns the data source of this dataset
		"""		   
		return self.dataSource
		
	def getMIP(self, mipTimepoint, color, small = 0, noColor = 0):
		"""
		Created: 01.09.2005, KP
		Description: Returns MIP of the given timepoint
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
					print "Getting MIP with color", color
					self.mip = lib.ImageOperations.getMIP(imagedata, color)
					print "Got mip, storing to cache", self.mip
				
					self.dataSource.storeToCache(self.mip, self.getFileName(), self.getName(), "MIP")
				else:
					self.mip = cached
					
			return self.mip
	
	def storeToCache(self, imagedata, timepoint, purpose):
		"""
		Created: 14.11.2006, KP
		Description: Store any image data along with it's timepoint and purpose to the cached
		"""
		self.dataSource.storeToCache(imagedata, self.getFileName(), self.getName(), 
			"%s_tp%d" % (purpose, timepoint))

	def getFromCache(self, timepoint, purpose):
		"""
		Created: 14.11.2006, KP
		Description: Retrieve from cache any image data by it's purpose and timepoint
		"""
		return self.dataSource.getFromCache(self.getFileName(), self.getName(), "%s_tp%d" % (purpose, timepoint))
		
		
	def resetColorTransferFunction(self):
		"""
		Created: 12.10.2006, KP
		Description: A method that will reset the CTF from the datasource.
					 This is useful e.g. when scaling the intensities of the	
					 dataset
		"""
		self.ctf = None
		self.dataSource.resetColorTransferFunction()
		ctf = self.getColorTransferFunction()
		self.settings.set("ColorTransferFunction", ctf)

	def getColorTransferFunction(self):
		"""
		Created: 26.04.2005, KP
		Description: Returns the ctf of this object
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
		Created: 27.03.2005, KP
		Description: Sets the settings object of this dataunit
		"""
		self.settings = settings
		self.updateSettings()
	
	def updateSettings(self):
		"""
		Created: 28.03.2005, KP
		Description: Sets the settings of this object based on the datasource
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
			
	def getSettings(self):
		"""
		Created: 27.03.2005, KP
		Description: Returns the settings object of this dataunit
		"""
		return self.settings
		
	def getName(self):
		"""
		Created: 03.11.2004, JM
		Description: Returns the name of this DataUnit
		"""
		return self.dataUnitName

	def setName(self, dataUnitName):
		"""
		Created: 8.12.2004, JM
		Description: Sets the name of this dataunit
		"""
		self.dataUnitName = dataUnitName
		if self.settings:
			self.settings.set("Name", dataUnitName)
 
	def getTimepoint(self, timepoint):
		"""
		Created: 17.11.2004, KP
		Description: Returns the requested time point
		Parameters:
				n		The timepoint we need to return
		"""
		if self.destroyed:
			print "I have been destroyed!"
			print "There are ", weakref.getweakrefcount(self), "references to me"
		if not self.dataSource:
			print self, self.dataUnitName
			Logging.error("No datasource specified",
			"No datasource specified for DataUnit, unable to get timepoint!")
			return None
		return self.dataSource.getDataSet(timepoint)
		

	def getNumberOfTimepoints(self):
		"""
		Created: 10.11.2004, JM
		Description: Returns the length of this DataUnit
		"""
		return self.length

	def setDataSource(self, dataSource):
		"""
		Created: 09.11.2004, JM
		Description: Sets a DataSource for this SourceDataUnit
		Parameters: dataSource	A DataSource to manage actual
								image data located on disk
		"""
		# Then load the settings specific to SourceDataUnit:
		self.dataSource = dataSource
		self.dataUnitName = dataSource.getName()
		self.length = dataSource.getDataSetCount()
		
		self.getDimensions = dataSource.getDimensions
		self.getSpacing = dataSource.getSpacing
		self.getVoxelSize = dataSource.getVoxelSize
		self.getResampledVoxelSize = dataSource.getResampledVoxelSize
		self.getBitDepth = dataSource.getBitDepth
		self.getSingleComponentBitDepth = dataSource.getSingleComponentBitDepth
		self.getTimeStamp = dataSource.getTimeStamp
		self.getScalarRange = dataSource.getScalarRange
		self.getEmissionWavelength = dataSource.getEmissionWavelength
		self.getExcitationWavelength = dataSource.getExcitationWavelength
		self.getNumericalAperture = dataSource.getNumericalAperture
#		 Logging.info("Dataunit ", repr(self), "got datasource", repr(self.dataSource), kw = "datasource")
		
		#self.updateSettings()
   

	def getFileName(self):
		"""
		Created: 21.03.2006, KP
		Description: Return the path to the file this dataunit represents
		"""
		return self.dataSource.getFileName()
		
		
