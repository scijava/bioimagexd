# -*- coding: iso-8859-1 -*-
"""
 Unit: BXCDataSource
 Project: BioImageXD
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

import ConfigParser
from lib.DataSource.DataSource import DataSource
from lib.DataSource.RGBComponentDataSource import RGBComponentDataSource
from lib.DataUnit.DataUnit import DataUnit
from lib.DataUnit.DataUnitSetting import DataUnitSettings
import lib.messenger
import os.path
import Logging
import scripting
import vtk


def getExtensions():
	return ["bxc"]

def getFileType():
	return "BioImageXD dataset channel (*.bxc)"

def getClass():
	return BXCDataSource

class BXCDataSource(DataSource):
	"""
	Manages 4D data stored in du- and vti-files
	"""
	def __init__(self, filename = ""):
		"""
		Constructor
		"""
		DataSource.__init__(self)
		# list of references to individual datasets (= timepoints) stored in 
		# vti-files
		self.polydataReader = None
		self.dataSets = []
		self.polyTimepoint = -1
		self.polyDataFiles = []
		# filename of the .du-file
		self.filename = filename
		self.baseFilename = ""
		self.setPath(filename)
		# path to the .du-file and .vti-file(s)
		self.path = ""
		self.reader = None
		# Number of datasets added to this datasource
		self.counter = 0
		self.parser = None
		self.ctf = None
		# TODO: what is this?
		# self.dataUnitSettings = {}
		self.settings = None
		self.dimensions = None
		self.spacing = None
		self.voxelsizes = None
		
	def getFileName(self):
		"""
		Return the file name
		"""
		if not self.baseFilename:
			return self.filename
		return self.baseFilename
		
	def setBaseFileName(self, filename):
		"""
		set the base filename. This interface is mainly for BXD reader to utilize
		"""
		self.baseFilename = filename
		
	def getParser(self):
		"""
		Returns the parser that is used to read the .du file
		"""
		return self.parser
		
	def getDataSetCount(self):
		"""
		Returns the number of individual DataSets (= time points)
		managed by this DataSource
		"""
		return len(self.dataSets)

	def getPolyData(self, timepoint):
		"""
		Return the polygonal dataset associated with given timepoint
		"""
		if not self.polydataReader or self.polyTimepoint != timepoint:
			if len(self.polyDataFiles) <= timepoint:
				return None
			self.polyTimepoint = timepoint
			filename = self.polyDataFiles[timepoint]
			self.polydataReader = vtk.vtkXMLPolyDataReader()
			self.polydataReader.AddObserver("ProgressEvent", lib.messenger.send)
			lib.messenger.connect(self.polydataReader, 'ProgressEvent', self.updateProgress)
			filepath = os.path.join(self.path, filename)
			if not self.polydataReader.CanReadFile(filepath):
				Logging.error("Cannot read file",
				"Cannot read vtkPolyData File %s"%filename)
			self.polydataReader.SetFileName(filepath)
			self.polydataReader.Update()
			self.updateProgress(None, None)
			self.polydataReader.Update()
		return self.polydataReader.GetOutput()
		
	def getDataSet(self, i, raw = 0):
		"""
		Returns the DataSet at the specified index
		@param i  The index
		"""
		# Check boundaries
		if i < 0:
			i = 0
		elif i >= len(self.dataSets):
			i = len(self.dataSets) - 1

		self.setCurrentTimepoint(i)
		data = self.loadVti(self.dataSets[i])
		if not self.originalScalarRange:
			self.originalScalarRange = 0, (2**self.getBitDepth()) - 1
		#self.scalarRange = data.GetScalarRange()
		if raw:
			return data
		
		data = self.getResampledData(data, i)
		
		if data.GetScalarType() != 3 and not raw and self.settings.getType() != "Process":
			data = self.getIntensityScaledData(data)
		
		return data

	def readInfo(self, data):
		"""
		Read various bits of info from the dataset
		"""
		self.dimensions = data.GetDimensions()
		self.spacing = data.GetSpacing()
		#self.bitdepth = 8*data.GetNumberOfScalarComponents()

	def internalGetDimensions(self):
		"""
		Returns the (x, y, z) dimensions of the datasets this 
					 dataunit contains
		"""
		return eval(self.settings.get("Dimensions"))
		
	def getSpacing(self):
		"""
		Returns the spacing of the datasets this 
					 dataunit contains
		"""
		if not self.spacing:
			#data = self.getDataSet(0)
			#self.readInfo(data)
			self.spacing = eval(self.settings.get("Spacing"))
		return self.spacing
		
	def getVoxelSize(self):
		"""
		Returns the spacing of the datasets this 
					 dataunit contains
		"""
		try:
			vsiz = self.parser.get("VoxelSize", "VoxelSize")
		except ConfigParser.NoOptionError:
			vsiz = self.parser.get("VoxelSize", "voxelsize")
		if type(vsiz) == type(""):			
			return eval(vsiz)
		return vsiz
	
	def loadVti(self, filename):
		"""
		Loads the specified DataSet from disk and returns
					 it as vtkImageData
		@param filename	The file where Dataset is loaded from
		"""
		if not self.reader or self.filename != filename:
			self.filename = filename
			self.reader = vtk.vtkXMLImageDataReader()
			self.reader.AddObserver("ProgressEvent", lib.messenger.send)
			lib.messenger.connect(self.reader, 'ProgressEvent', self.updateProgress)
			filepath = os.path.join(self.path, filename)
			if not self.reader.CanReadFile(filepath):
				Logging.error("Cannot read file",
				"Cannot read XML Image Data File %s"%filename)
			self.reader.SetFileName(filepath)
			self.updateProgress(None, None)
		data = self.reader.GetOutput()
		return data

	def loadBxdFile(self, filename):
		"""
		Loads the specified .bxc-file, the checks the format
					 of the loaded dataunit and returns it

		Parameters:   filename	The .du-file to be loaded
		"""
		self.filename = filename
		self.path = os.path.dirname(filename)
		Logging.info("Trying to open %s"%filename, kw = "datasource")
		try:
			# A SafeConfigParser is used to parse the .du-file
			self.parser = scripting.MyConfigParser()
			self.parser.read([filename])
			dataUnitFormat = ""
			if self.parser.has_option("Type","Type"):
				dataUnitFormat = self.parser.get("Type","Type")
			if dataUnitFormat == "":
				dataUnitFormat = "NOOP"
		except ConfigParser.ParsingError, ex:
			#Logging.error("Failed to open file for reading",
			#"BXCDataSource failed to open %s for reading. Reason: %s"%(filename, str(ex)))
			#return [None]
			return "NOOP"
		return dataUnitFormat

	def loadFromFile(self, filename):
		"""
		Loads the specified .bxc-file and imports data from it.
					 Also returns a DataUnit of the type stored in the loaded
					 .bxc-file or None if something goes wrong. The dataunit is
					 returned in a list with one item for interoperability with
					 LSM data source
		"""
		if not self.baseFilename:
			self.baseFilename = filename
		self.shortname = os.path.basename(filename)
		dataUnitFormat = self.loadBxdFile(filename)
		Logging.info("format of unit = ", dataUnitFormat, kw = "datasource")

		if (not dataUnitFormat) or (not self.parser):
			Logging.info("No dataUnitFormat or parser: %s and %s"%(dataUnitFormat, self.parser), kw = "datasource")
			return None

		# Then, the number of datasets/timepoints that belong to this dataset
		# series
		try:
			count = self.parser.get("ImageData", "numberOfFiles")
		except ConfigParser.NoOptionError:
			count = self.parser.get("ImageData", "numberoffiles")
		Logging.info("format = ", dataUnitFormat, "count = ", count, kw = "datasource")

		# Then read the .vti-filenames and store them in the dataSets-list:
		filedir = os.path.dirname(filename)
		
		hasPolydata = self.parser.has_section("PolyData")
		for i in range(int(count)):
			currentFile = "file_%d"%i
			filename = self.parser.get("ImageData", currentFile)
			
			if hasPolydata:
				print "GOT polydata"
				polyFileName = self.parser.get("PolyData", currentFile)
				self.polyDataFiles.append(polyFileName)
				
			reader = vtk.vtkXMLImageDataReader()
			filepath = os.path.join(filedir, filename)
			if not reader.CanReadFile(filepath):
				Logging.error("Cannot read file",
				"Cannot read source XML Image Data File %s"%filename)
				return

			self.dataSets.append(filename)

		# If everything went well, we create a new DataUnit-instance of the
		# correct subclass, so that the DataUnit-instance can take over and
		# resume data processing. First, we return the DataUnit to the caller,
		# so it can set a reference to it:
		dataunit = DataUnit()
		settings = DataUnitSettings()
		settings.setType("")
		settings = settings.readFrom(self.parser)
		self.originalDimensions = eval(settings.get("Dimensions"))
		self.settings = settings
		dataunit.setDataSource(self)
		dataunit.setSettings(settings)
		data = dataunit.getTimepoint(0)
		dataunits = [dataunit]
	   
		if data.GetNumberOfScalarComponents() == 3:
			for i in range(0, 3) :
				dataSource = RGBComponentDataSource(self, i)
				dataunit = DataUnit()
				dataunit.setDataSource(dataSource)
				settings = DataUnitSettings()
				settings = settings.readFrom(self.parser)
				dataunit.setSettings(settings)
				dataunits.append(dataunit)
		return dataunits

	def getName(self):
		"""
		Returns the name of the dataset series which this datasource
					 operates on
		"""
		return self.settings.get("Name")

	def getColorTransferFunction(self):
		"""
		Returns the ctf of the dataset series which this datasource
					 operates on
		"""
		Logging.info("Getting colortransferfunction from settings", kw = "ctf")
		
		if not self.ctf:
			ctf = self.settings.get("ColorTransferFunction")
			#Logging.info("settings.ctf = ", ctf, kw = "ctf")
			try:
				#ctf = self.parser.get("ColorTransferFunction", "ColorTransferFunction")
				ctf = self.settings.get("ColorTransferFunction")				  
				if not ctf:
					ctf = self.settings.get("ColocalizationColorTransferFunction")
			except:
				return None
			if not ctf:
				Logging.info("Will return no CTF", kw = "ctf")
				ctf = vtk.vtkColorTransferFunction()
				ctf.AddRGBPoint(0, 0, 0, 0)
				ctf.AddRGBPoint(255, 1, 1, 1)				  
			else:
				#Logging.info("Using CTF read from dataset", ctf, kw = "ctf")
				pass
			self.ctf = ctf
		return self.ctf

	def getScalarRange(self):
		"""
		Returns pair that contains range of data values
		"""
		if not self.scalarRange:
			self.getBitDepth()
			if self.singleBitDepth == 8 or self.singleBitDepth == 12 or len(self.dataSets) == 1:
				min = 0
				max = 2**self.singleBitDepth - 1
				self.scalarRange = (int(min),int(max))
			else:
				data = self.getDataSet(0, raw = 1)
				data.Update()
				self.scalarRange = data.GetScalarRange()
		
		return self.scalarRange

	def getBitDepth(self):
		"""
		Return the bit depth of data
		"""
		if not self.bitdepth:
			self.bitdepth = int(self.settings.get("BitDepth"))
			data = self.getDataSet(0, raw = 1)
			data.UpdateInformation()
			self.singleBitDepth = self.bitdepth / data.GetNumberOfScalarComponents()
		return self.bitdepth
		
	def getTimeStamp(self, timepoint):
		"""
		@return the timestamp for given timepoint
		"""
		if len(self.timestamps) == 0:
			self.createTimeStamps()
		if len(self.timestamps) > timepoint:
			return self.timestamps[timepoint]
		return timepoint	

	def getAbsoluteTimeStamp(self, timepoint):
		"""
		@return the absolute timestamp for given timepoint
		"""
		if len(self.absoluteTimestamps) == 0:
			self.createTimeStamps()
		if len(self.absoluteTimestamps) >= timepoint:
			return self.absoluteTimestamps[timepoint]
		return timepoint

	def getTimeStamps(self):
		"""
		@return all the timestamps
		"""
		if len(self.timestamps) == 0:
			self.createTimeStamps()
		return self.timestamps

	def getAbsoluteTimeStamps(self):
		"""
		@return all the absolute timestamps
		"""
		if len(self.absoluteTimestamps) == 0:
			self.createTimeStamps()
		return self.absoluteTimestamps

	def createTimeStamps(self):
		"""
		Creates time stamps for setTimeStamps and setAbsoluteTimeStamps methods
		"""
		timestamps = self.settings.get("TimeStamps")
		if not timestamps:
			timestamps = []
		absoluteTimestamps = self.settings.get("AbsoluteTimeStamps")
		if not absoluteTimestamps:
			absoluteTimestamps = []
		
		if len(absoluteTimestamps) > len(timestamps):
			timestamps = [0.0]
			firstTS = absoluteTimestamps[0]
			for ts in range(1,len(absoluteTimestamps)):
				timestamps.append(absoluteTimestamps[ts] - firstTS)
		
		self.setTimeStamps(timestamps)
		self.setAbsoluteTimeStamps(absoluteTimestamps)

	def getExcitationWavelength(self):
		"""
		Return excitation wavelength
		"""
		try:
			excitation = self.settings.get("ExcitationWavelength")
			excitation = float(excitation)
		except:
			excitation = 0
		
		return excitation

	def getEmissionWavelength(self):
		"""
		Return emission wavelength
		"""
		try:
			emission = self.settings.get("EmissionWavelength")
			emission = float(emission)
		except:
			emission = 0

		return emission
