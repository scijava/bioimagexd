# -*- coding: iso-8859-1 -*-
"""
 Unit: OlympusDataSource
 Project: BioImageXD
 Created: 16.02.2006, KP
 Description: A datasource for reading Olympus OIF files

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

#import lib.messenger

import codecs
import ConfigParser
from lib.DataSource.DataSource import DataSource
from lib.DataUnit.DataUnit import DataUnit
import Logging
import math
import os
import os.path
import struct
import vtk
import vtkbxd
		
def getExtensions(): 
	return ["oif"]

def getFileType(): 
	return "Olympus Image Format datasets (*.oif)"        

def getClass(): 
	return OlympusDataSource
	
class OlympusDataSource(DataSource):
	"""
	Created: 12.04.2005, KP
	Description: Olympus OIF files datasource
	"""
	def __init__(self, filename = "", channel = -1, basename = "", lutname = "", \
					name = "", dimensions = (0, 0, 0), time = 0, voxelsize = (1, 1, 1), \
					reverse = 0, emission = 0, excitation = 0, bitdepth = 12):
		"""
		Created: 12.04.2005, KP
		Description: Constructor
		"""    
		DataSource.__init__(self)
		if not name:
			name = "Ch%d" % channel
		self.bitdepth = bitdepth
		self.name = name
		self.basename = basename
		self.lutname = lutname
		self.timepoint = 0
		self.timepoints = time
		self.filename = filename
		self.parser = ConfigParser.RawConfigParser()
		self.reader = None
		self.originalScalarRange = (0, 4095)
		self.scalarRange = 0, 2 ** self.bitdepth - 1
		self.channel = channel
		self.dimensions = dimensions
		self.voxelsize = voxelsize
		self.spacing = None
		self.emission = emission
		self.excitation = excitation
		self.color = None
		self.shift = None
		self.noZ = 0
		self.reverseSlices = reverse
		if filename:
			self.path = os.path.dirname(filename)
		if channel >= 0:
			self.ctf = self.readLUT()
		self.setPath(filename)
		
		# nm = nanometer, um = micrometer, mm = millimeter
		self.unit_coeffs = {"nm":1e-9, "um":1e-6, "mm":0.001}
		self.shortname = None
		
	def getDataSetCount(self):
		"""
		Created: 12.04.2005, KP
		Description: Returns the number of individual DataSets (=time points)
		managed by this DataSource
		"""
		if not self.timepoints:
			return 1
		return self.timepoints
		
	def getEmissionWavelength(self):
		"""
		Created: 07.04.2006, KP
		Description: Returns the emission wavelength used to image this channel
		managed by this DataSource
		"""
		return self.emission
			
	def getExcitationWavelength(self):
		"""
		Created: 07.04.2006, KP
		Description: Returns the excitation wavelength used to image the channel
		managed by this DataSource
		"""
		return self.excitation

	def getFileName(self):
		"""
		Created: 21.07.2005
		Description: Return the file name
		"""    
		return self.filename
	
	def getDataSet(self, i, raw = 0):
		"""
		Created: 12.04.2005, KP
		Description: Returns the image data for timepoint i
		"""
		data = self.getTimepoint(i)        
		if raw:
			return data
		
		#self.originalScalarRange=data.GetScalarRange()
		#print "Setting original scalar range to ",2**self.getBitDepth()-1
		
		if not self.originalScalarRange:
			self.originalScalarRange = 0, (2 ** self.getBitDepth()) - 1
		
		data = self.getResampledData(data, i)
		data = self.getIntensityScaledData(data)
		
		#data.ReleaseDataFlagOff()
		return data
		
	def updateProgress(self, object, event):
		"""
		Created: 12.11.2006, KP
		Description: Sends progress update event
		"""        
		if not object:
			progress = 1.0
		else:
			progress = object.GetProgress()
		if self.channel >= 0:
			txt = object.GetProgressText()
			if not txt:
				txt = ""

			msg = "Reading channel %d of %s" % (self.channel, self.basename)
			if self.timepoint >= 0:

				msg += " (timepoint %d / %d, %s)" % (self.timepoint + 1, self.timepoints + 1, txt)
		else:
			msg = "Reading %s..." % self.shortname
		notinvtk = 0
		
		if progress == 1.0:
			notinvtk = 1
			
		#print progress,msg
		#lib.messenger.send(None,"update_progress",progress,msg,notinvtk)
		
	def getTimepoint(self, timepointIndex):
		"""
		Created: 16.02.2006, KP
		Description: Return the timepointIndexth timepoint
		"""        
		self.timepoint = timepointIndex
		path = os.path.join(self.path, "%s.oif.files" % self.basename)
		if not self.reader:
			self.reader = vtkbxd.vtkExtTIFFReader()
			self.reader.AddObserver("ProgressEvent", self.updateProgress)
			xDimension, yDimension, zDimension = self.dimensions
			self.reader.SetDataExtent(0, xDimension - 1, 0, yDimension - 1, 0, zDimension - 1)
			
			spacing = self.getSpacing()
			self.reader.SetDataSpacing(*spacing)
		
		zpat = ""
		tpat = ""
		cpat = os.path.sep + "%s_C%.3d" % (self.lutname, self.channel)
		path += cpat
		
		if self.dimensions[2] > 1:
			zpat = "Z%.3d"
		if self.timepoints > 0:
			tpat = "T%.3d"
		pat = path + zpat + tpat + ".tif"
		
		self.reader.SetFilePattern(pat)
		if self.reverseSlices and 0:
			#print "offset=",self.dimensions[2]
			self.reader.SetFileNameSliceOffset(self.dimensions[2])
			self.reader.SetFileNameSliceSpacing(-1)
		else:
			self.reader.SetFileNameSliceOffset(1)

		self.reader.UpdateInformation()
#        print "pattern='"+self.reader.GetFilePattern()+"'"
		#self.reader.Update()
		#print self.reader
#        print vtk,self.reader
#        print "Scalar range for data=",self.reader.GetOutput().GetScalarRange()
		return self.reader.GetOutput()
		
	def getDimensions(self):
		"""
		Created: 12.04.2005, KP
		Description: Returns the (x,y,z) dimensions of the datasets this 
					 dataunit contains
		"""
		if self.resampleDims:
			
			return self.resampleDims
		if not self.dimensions:
			raise "No dimensions given for ", str(self)
			#print "Got dimensions=",self.dimensions
		return self.dimensions

	def readLUT(self): 
		"""
		Created: 16.02.2006, KP
		Description: Read the LUT for this dataset
		"""
		lutpath = os.path.join(self.path, "%s.oif.files" % self.basename, "%s_LUT%d.lut" \
								% (self.lutname, self.channel))
		file = codecs.open(lutpath, "r", "utf-16")
		#print "Reading lut from %s..."%lutpath
		while 1:
			line = file.readline()
			if "ColorLUTData" in line:
				break
		
		#pos = file.tell()
		file.close()
		file = open(lutpath, "rb")
		file.seek(-4 * 65536, 2)
		data = file.read()
		#print "Got ",len(data),"bytes"
		
		format = "i" * 65536
		values = struct.unpack(format, data)
		ctf = vtk.vtkColorTransferFunction()
		#print values
		vals = [( ((x >> 16) & 0xff), ((x >> 8) & 0xff), (x & 0xff)) for x in values]
		
		#def f(x):( (x>>16)&0xff
		i = 0
		#red2, green2, blue2 = -1, -1, -1
		coeff = 16.0
		
		#print "CUrrent minval,maxval=",minval,maxval
		if self.explicitScale == 1:
			minval, maxval = self.originalScalarRange
			#shift = self.intensityShift
			if self.intensityShift:
				maxval += self.intensityShift
				#print "Maximum value after being shifted=",maxval
			scale = self.intensityScale
			if not scale:
				scale = 255.0 / maxval
			maxval *= scale
			
			self.scalarRange = (0, maxval)
			#print "GOT MAXVAL=",0,maxval
			self.bitdepth = int(math.log(maxval + 1, 2))
			#print "Set bitdepth to ",self.bitdepth
			#print "Maximum value after being scaled=",maxval
			self.explicitScale = 2
		else:
			minval, maxval = self.scalarRange
		coeff = 65536.0 / (maxval + 1)
		#coeff=int(coeff)
		#print "coeff=",coeff
#        print "Largest value=",len(vals)/coeff
		red0, green0, blue0 = -1, -1, -1
		for i in range(0, maxval + 1):
			red, green, blue = vals[int(i * coeff)]
			if i in [0, maxval] or (red != red0 or green != green0 or blue != blue0):
				ctf.AddRGBPoint(i, red / 255.0, green / 255.0, blue / 255.0)
				red0, green0, blue0 = red, green, blue
			if i == maxval:
				print "-->", i, maxval, "maps to", red, green, blue
		
		return ctf
	
	def getTimeStamp(self, timepoint):
		"""
		Created: 02.07.2007, KP
		Description: return the timestamp for given timepoint
		"""
		pass

	
	def getSpacing(self):
		"""
		Created: 12.04.2005, KP
		Description: Returns the spacing of the datasets this 
					 dataunit contains
		"""
		if not self.spacing:
			aDimension, bDimension, cDimension = self.getVoxelSize()
			self.spacing = [1, bDimension / aDimension, cDimension / aDimension]
		return self.spacing
		
	def getVoxelSize(self):
		"""
		Created: 12.04.2005, KP
		Description: Returns the voxel size of the datasets this 
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
		Created: 16.02.2006, KP
		Description: Read the number of timepoints, channels and XYZ from the OIF file
		"""    
		timepoints = 0
		channels = 0
		xDimension = 0
		yDimension = 0
		zDimension = 1
		for i in range(0, 7):
			sect = "Axis %d Parameters Common" % i
			key = "AxisCode"
			data = parser.get(sect, key)
			# If Axis i is the time axis
			n = timepoints = int(parser.get(sect, "MaxSize")) #TODO: why n = timepoints = .... ??
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
				timepoints = n
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
		#print "\n\n\n *** SETTING ORIGINAL DIMS TO ",( xDimension, yDimension, zDimension)
		self.originalDimensions = (xDimension, yDimension, zDimension)
		return xDimension, yDimension, zDimension, timepoints, channels, \
				voxelXDimension, voxelYDimension, voxelZDimension
				
	def getLUTPath(self, parser):
		"""
		Created: 05.09.2006, KP
		Description: Read the base name for the LUT file which can also be used
					 for the paths of the TIFF files
		"""
		path = parser.get("ProfileSaveInfo", "LutFileName0")
		path = os.path.basename(path)
		path = path.split("\\")[-1]
		parts = path.split("_")
		path = "_".join(parts[:-1])
		return path
				
	def getDyes(self, parser, numberOfChannels):
		"""
		Created: 16.02.2006, KP
		Description: Read the dye names for numberOfChannels channels
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
		Created: 12.04.2005, KP
		Description: Loads the specified .oif-file and imports data from it.
		Parameters:   filename  The .oif-file to be loaded
		"""
		self.filename = filename
		self.path = os.path.dirname(filename)
		
		basefile = os.path.basename(filename)
		basefile = basefile.replace(".oif", "")
		
		try:
			file = open(filename)
			file.close()
		except IOError, ex:
			Logging.error("Failed to open Olympus OIF File",
			"Failed to open file %s for reading: %s" % (filename, str(ex)))        

		filepointer = codecs.open(filename, "r", "utf-16")
		self.parser.readfp(filepointer)
		xDimension, yDimension, zDimension, timepoints, \
		channels, voxelXDimension, voxelYDimension, voxelZDimension = self.getAllDimensions(self.parser)
		
		voxsiz = (voxelXDimension, voxelYDimension, voxelZDimension)
		names, (excitations, emissions) = self.getDyes(self.parser, channels)
		
		self.bitdepth = eval(self.parser.get("Reference Image Parameter", "ValidBitCounts"))
		lutpath = self.getLUTPath(self.parser)
		
		dataunits = []
		for channel in range(1, channels + 1):
			name = names[channel - 1]    
			excitation = excitations[channel - 1]
			emission = emissions[channel - 1]
			datasource = OlympusDataSource(filename, channel, name = name, basename = basefile,
										lutname = lutpath,
										dimensions = (xDimension, yDimension, zDimension), 
										time = timepoints, voxelsize = voxsiz,
										reverse = self.reverseSlices,
										emission = emission,
										excitation = excitation, bitdepth = self.bitdepth)
			#datasource.bitdepth = self.bitdepth
			datasource.originalDimensions = (xDimension, yDimension, zDimension)
			dataunit = DataUnit()
			dataunit.setDataSource(datasource)
			dataunits.append(dataunit)
			
		return dataunits

	def getName(self):
		"""
		Created: 18.11.2005, KP
		Description: Returns the name of the dataset series which this datasource
					 operates on
		"""
		return self.name
		
	def uniqueId(self):
		"""
		Created: 07.02.2007, KP
		Description: return a string identifying the dataset
		"""
		return self.getFileName() + "|" + str(self.channel) 

	def resetColorTransferFunction(self):
		"""
		Created: 12.10.2006, KP
		Description: A method that will reset the CTF from the datasource.
					 This is useful e.g. when scaling the intensities of the    
					 dataset
		"""
		self.ctf = None
		return self.getColorTransferFunction()
	
	def getColorTransferFunction(self):
		"""
		Created: 26.04.2005, KP
		Description: Returns the ctf of the dataset series which this datasource
					 operates on
		"""
		if not self.ctf:
			self.ctf = self.readLUT()
		return self.ctf        
