# -*- coding: iso-8859-1 -*-
"""
 Unit: OlympusDataSource
 Project: BioImageXD
 Created: 16.02.2006, KP
 Description: A datasource for reading Olympus OIF files

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

import codecs
import ConfigParser
from lib.DataSource.DataSource import DataSource
from lib.DataUnit.DataUnit import DataUnit
import lib.messenger
import Logging
import math
import os
import os.path
import struct
import vtk
import vtkbxd
import scripting

def getExtensions(): 
	return ["oif"]

def getFileType(): 
	return "Olympus Image Format datasets (*.oif)"		  

def getClass(): 
	return OlympusDataSource
	
class OlympusDataSource(DataSource):
	"""
	Olympus OIF files datasource
	"""
	def __init__(self, filename = "", channel = -1, \
					name = ""):
		"""
		Constructor
		"""
		DataSource.__init__(self)
		self.channel = channel
		
		if not name:
			name = "Ch%d" % channel
		self.bitdepth = 12
		self.name = name

		self.timepoint = 0
		self.timepoints = 0
		self.filename = filename
		self.parser = ConfigParser.RawConfigParser()
		if filename:
			filepointer = codecs.open(filename, "r", "utf-16")
			self.parser.readfp(filepointer)
			dataName = self.parser.get("File Info","DataName")
			if dataName[0] == '"':
				dataName = dataName[1:]
			if dataName[-1] == '"':
				dataName = dataName[:-1]
			directoryName, self.lutFileName = self.getLUTPath(self.channel)
			newLut = os.path.join(directoryName, self.lutFileName)
			newLut = os.path.join(os.path.dirname(self.filename), newLut)
			if not os.path.exists(newLut):
				self.path = "%s.files"%self.filename
				print self.lutFileName
			else:
				self.path = os.path.join(os.path.dirname(filename), "%s.files"%dataName)
			
			# when lutFileName is e.g. bro28_par3_07-04-18_LUT1.lut, we take the 
			# bro28_par3_07-04-18 and ignore the LUT1.lut, and use that as the basis of the filenames
			# for the tiff files
			self.fileNameBase = "_".join(self.lutFileName.split("_")[:-1])
			#self.fileNameBase = dataName
			
		self.reader = None
		self.originalScalarRange = (0, 4095)
		self.scalarRange = 0, 2 ** self.bitdepth - 1
		self.dimensions = (0,0,0)
		self.voxelsize = (1,1,1)
		self.spacing = None
		self.emission = 0
		self.excitation = 0
		self.color = None
		self.shift = None
		self.noZ = 0
		self.reverseSlices = True

		if channel >= 0:
			self.ctf = self.readLUT()
		self.setPath(filename)
		
		# nm = nanometer, um = micrometer, mm = millimeter
		self.unit_coeffs = {"nm":1e-9, "um":1e-6, "mm":0.001,"ms":0.001}
		self.shortname = None
			
	def setBitDepth(self, bitdepth):
		"""
		Set the bit depth of  images in this dataunit
		"""
		self.bitdepth = bitdepth
		
	def setReverseSlices(self, reverseFlag):
		"""
		Set a flag indicating whether the slices should be returned in reverse order
		"""
		self.reverseSlices = reverseFlag
		
	def setEmissionWavelength(self, emission):
		"""
		Set the emission wavelength
		"""
		self.emission = emission
		
	def setExcitationWavelength(self, excitation):
		"""
		Set the emission wavelength
		"""
		self.excitation = excitation
			
	def setTimepoints(self, timepoints):
		"""
		Set the number of timepoints in the dataset
		"""
		self.timepoints = timepoints
		
	def setDimensions(self, dimensions):
		"""
		Set the dimensions of the data read by this reader
		"""
		self.dimensions = dimensions
		
	def setVoxelSize(self, voxelSize):
		"""
		Set the voxel size of a single voxel in this dataset
		"""
		self.voxelsize = voxelSize
	
	def getDataSetCount(self):
		"""
		Returns the number of individual DataSets (=time points)
		managed by this DataSource
		"""
		if not self.timepoints:
			return 1
		return self.timepoints
		
	def getEmissionWavelength(self):
		"""
		Returns the emission wavelength used to image this channel
		managed by this DataSource
		"""
		return self.emission
			
	def getExcitationWavelength(self):
		"""
		Returns the excitation wavelength used to image the channel
		managed by this DataSource
		"""
		return self.excitation

	def getFileName(self):
		"""
		Return the file name
		"""	   
		return self.filename
	
	def getDataSet(self, i, raw = 0):
		"""
		Returns the image data for timepoint i
		"""
		self.setCurrentTimepoint(i)
		data = self.getTimepoint(i)
		if raw:
			return data
		
		if not self.originalScalarRange:
			self.originalScalarRange = 0, (2 ** self.getBitDepth()) - 1
		
		data = self.getResampledData(data, i)
		data = self.getIntensityScaledData(data)
		
		return data
		
	def getTimepoint(self, timepointIndex):
		"""
		Return the timepointIndexth timepoint
		"""		   
		self.timepoint = timepointIndex
		path = self.path[:]
		if not self.reader:
			self.reader = vtkbxd.vtkExtTIFFReader()
			self.reader.AddObserver("ProgressEvent", lib.messenger.send)
			lib.messenger.connect(self.reader, 'ProgressEvent', self.updateProgress)
			xDimension, yDimension, zDimension = self.dimensions
			self.reader.SetDataExtent(0, xDimension - 1, 0, yDimension - 1, 0, zDimension - 1)
			
			spacing = self.getSpacing()
			self.reader.SetDataSpacing(*spacing)
		
		zpat = ""
		tpat = ""
		cpat = os.path.sep + "%s_C%.3d" % (self.fileNameBase, self.channel)
		path += cpat

		if self.dimensions[2] > 1:
			zpat = "Z%.3d"
		if self.timepoints > 1:
			tpat = "T%.3d"%(timepointIndex+1)
		pat = path + zpat + tpat + ".tif"
		
		self.reader.SetFilePattern(pat)

		if self.reverseSlices and 0:
			#print "offset=",self.dimensions[2]
			self.reader.SetFileNameSliceOffset(self.dimensions[2])
			self.reader.SetFileNameSliceSpacing(-1)
		else:
			self.reader.SetFileNameSliceOffset(1)

		self.reader.UpdateInformation()

		return self.reader.GetOutput()
		
	def internalGetDimensions(self):
		"""
		get the dimensions for this dataset, used by the getDimensions()
		"""
		return self.dimensions

	def readLUT(self): 
		"""
		Read the LUT for this dataset
		"""
		lutFile = os.path.join(self.path, self.lutFileName)

		file = codecs.open(lutFile, "r", "utf-16")
		while 1:
			line = file.readline()
			if "ColorLUTData" in line:
				break
		
		file.close()
		file = open(lutFile, "rb")
		file.seek(-4 * 65536, 2)
		data = file.read()
		
		format = "i" * 65536
		values = struct.unpack(format, data)
		ctf = vtk.vtkColorTransferFunction()
		vals = [( ((x >> 16) & 0xff), ((x >> 8) & 0xff), (x & 0xff)) for x in values]
		
		i = 0
		coeff = 16.0
		
		if self.explicitScale == 1:
			minval, maxval = self.originalScalarRange
			if self.intensityShift:
				maxval += self.intensityShift
			scale = self.intensityScale
			if not scale:
				scale = 255.0 / maxval
			maxval *= scale
			
			self.scalarRange = (0, maxval)
			self.bitdepth = int(math.log(maxval + 1, 2))
			self.explicitScale = 2
		else:
			minval, maxval = self.scalarRange
		coeff = 65536.0 / (maxval + 1)

		red0, green0, blue0 = -1, -1, -1
		for i in range(0, maxval + 1):
			red, green, blue = vals[int(i * coeff)]
			if i in [0, maxval] or (red != red0 or green != green0 or blue != blue0):
				ctf.AddRGBPoint(i, red / 255.0, green / 255.0, blue / 255.0)
				red0, green0, blue0 = red, green, blue
		
		return ctf

	
	def getSpacing(self):
		"""
		Returns the spacing of the datasets this 
					 dataunit contains
		"""
		if not self.spacing:
			aDimension, bDimension, cDimension = self.getVoxelSize()
			self.spacing = [1, bDimension / aDimension, cDimension / aDimension]
		return self.spacing
		
	def getVoxelSize(self):
		"""
		Returns the voxel size of the datasets this 
					 dataunit contains
		"""
		if not self.voxelsize:
			xDimension, yDimension, zDimension, timepoint, channel, \
			voxelXDimension, voxelYDimension, voxelZDimension = self.getAllDimensions(self.parser)
						 
			self.voxelsize = (voxelXDimension, voxelYDimension, voxelZDimension)

			#print "Got voxel size=",self.voxelsize
		return self.voxelsize
	
	def getAllDimensions(self, parser):
		"""
		Read the number of timepoints, channels and XYZ from the OIF file
		"""	   
		timepoints = 0
		channels = 0
		xDimension = 0
		yDimension = 0
		zDimension = 1
		timeStep = 1
		for i in range(0, 7):
			sect = "Axis %d Parameters Common" % i
			key = "AxisCode"
			data = parser.get(sect, key)
			# If Axis i is the time axis
			n = int(parser.get(sect, "MaxSize"))
			unit = parser.get(sect, "UnitName")
			unit = unit.replace('"', "")
			startPosition = parser.get(sect, "StartPosition")
			endPosition = parser.get(sect, "EndPosition")
			startPosition = startPosition.replace('"', '')
			endPosition = endPosition.replace('"', '')
			
			startpos = float(startPosition)
			endpos = float(endPosition)
			
			if endpos < startpos:
				self.reverseSlices = 1
			
			diff = abs(endpos - startpos)
			if unit in self.unit_coeffs:
				coeff = self.unit_coeffs[unit]
			
			diff *= coeff
			if data == '"T"':
				if n == 0:
					timepoints = 1
					timeStep = 0.0
				else:
					timepoints = n
					timeStep = diff/n
			elif data == '"C"':
				channels = n
			elif data == '"X"':
				xDimension = n
				voxelXDimension = diff
			elif data == '"Y"':
				yDimension = n
				voxelYDimension = diff
			elif data == '"Z"':
				zDimension = n
				voxelZDimension = diff
		
		if zDimension == 0:
			zDimension = 1
			self.noZ = 1
		voxelXDimension /= float(xDimension)
		voxelYDimension /= float(yDimension)
		if zDimension > 1:
			voxelZDimension /= float(zDimension - 1)
		self.originalDimensions = (xDimension, yDimension, zDimension)
		return xDimension, yDimension, zDimension, timepoints, channels, \
				voxelXDimension, voxelYDimension, voxelZDimension, timeStep
				
	def getLUTPath(self, channel):
		"""
		Read the path and filename for the LUT file of given channel which can also be used
					 for the paths of the TIFF files
		"""
		path = self.parser.get("ProfileSaveInfo", "LutFileName%d"%(channel-1))
		lutPath, lutFileName = path.split("\\")
		if lutPath[0]=='"':
			lutPath = lutPath[1:]
		if lutFileName[0]=='"':
			lutFileName = lutFileName[1:]
		if lutFileName[-1]=='"':
			lutFileName = lutFileName[:-1]
		return lutPath, lutFileName
		
	def getDyes(self, parser, numberOfChannels):
		"""
		Read the dye names for numberOfChannels channels
		""" 
		names = []
		exs = []
		ems = []
		for i in range(1, numberOfChannels + 1):
			sect = "Channel %d Parameters" % i
			data = parser.get(sect, "DyeName")
			data = data.replace('"', "")
			emission = int(parser.get(sect, "EmissionWavelength"))
			excitation = int(parser.get(sect, "ExcitationWavelength"))
			names.append(data)
			exs.append(excitation)
			ems.append(emission)
		return names, (exs, ems)
			
	def loadFromFile(self, filename):
		"""
		Loads the specified .oif-file and imports data from it.
		Parameters:	  filename	The .oif-file to be loaded
		"""
		self.filename = filename
		self.path = os.path.dirname(filename)
		
		try:
			file = open(filename)
			file.close()
		except IOError, ex:
			Logging.error("Failed to open Olympus OIF File",
			"Failed to open file %s for reading: %s" % (filename, str(ex)))		   

		filepointer = codecs.open(filename, "r", "utf-16")
		self.parser.readfp(filepointer)
		xDimension, yDimension, zDimension, timepoints, \
		channels, voxelXDimension, voxelYDimension, voxelZDimension, timeStep = self.getAllDimensions(self.parser)
		
		voxsiz = (voxelXDimension, voxelYDimension, voxelZDimension)
		names, (excitations, emissions) = self.getDyes(self.parser, channels)
		
		self.bitdepth = int(self.parser.get("Reference Image Parameter", "ValidBitCounts"))
		
		dataunits = []
		for channel in range(1, channels + 1):
			name = names[channel - 1]	 
			excitation = excitations[channel - 1]
			emission = emissions[channel - 1]
			datasource = OlympusDataSource(filename, channel, name = name)
			datasource.setDimensions((xDimension, yDimension, zDimension))
			datasource.setTimepoints(timepoints)
			stamps = []
			for i in range(0, timepoints):
				stamps.append(i*timeStep)
			datasource.setTimeStamps(stamps)
			datasource.setAbsoluteTimeStamps(stamps)
			datasource.setVoxelSize(voxsiz)
			datasource.setReverseSlices(self.reverseSlices)
			datasource.setEmissionWavelength(emission)
			datasource.setExcitationWavelength(excitation)
			datasource.setBitDepth(self.bitdepth)
			datasource.originalDimensions = (xDimension, yDimension, zDimension)
			dataunit = DataUnit()
			dataunit.setDataSource(datasource)
			dataunits.append(dataunit)
			
		return dataunits

	def getName(self):
		"""
		Returns the name of the dataset series which this datasource
					 operates on
		"""
		return self.name
		
	def uniqueId(self):
		"""
		return a string identifying the dataset
		"""
		return self.getFileName() + "|" + str(self.channel) 

	def getBitDepth(self):
		"""
		return the bit depth of the images returned by this datasource
		"""
		return self.bitdepth
	
	def getSingleComponentBitDepth(self):
		"""
		return the bit depth of a single component of the image returned by this datasource
		"""
		return self.getBitDepth()
	
	def getColorTransferFunction(self):
		"""
		Returns the ctf of the dataset series which this datasource
					 operates on
		"""
		if not self.ctf:
			self.ctf = self.readLUT()
		return self.ctf		   
