"""
 Unit: LeicaDataSource
 Project: BioImageXD
 Description: 

 A module for reading data produced by Leica microscopes. 
 
 Intial code by Karl Garsha <garsha@itg.uiuc.edu>. 
 Modified by Kalle Pahajoki for BioImageXD use.
 
 Copyright (C) 2005  Karl Garsha, BioImageXD Project
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
__author__ = "Karl Garsha, BioImageXD Project"
__version__ = "$Revision: 1.21 $"
__date__ = "$Date: 2005/01/13/ 13:42:03 $"

from lib.DataSource.DataSource import DataSource
from lib.DataUnit.DataUnit import DataUnit
import Logging
import math
import os
import re
import string
import vtk
import vtkbxd
import scripting
import lib.messenger


def getExtensions(): 
	return ["txt","lei"]

def getFileType(): 
	return "Leica TCS-NT datasets (*.txt)"

def getClass(): 
	return LeicaDataSource
		
class LeicaDataSource(DataSource):
	"""
	Leica format datasource
	"""
	def __init__(self, filename = "", experiment = "", channel = -1):
		"""
		Constructor
		"""    
		DataSource.__init__(self)
		self.filename = filename
		self.reader = LeicaExperiment(filename, progressCallback = self.updateProgress)
		self.shortname = os.path.basename(filename)

		self.experiment = experiment
		if experiment:
			self.originalDimensions = self.reader.GetDimensions(self.experiment)
			duration = self.reader.GetDuration(self.experiment)
			numT = self.reader.GetNumberOfTimepoints(self.experiment)
			print "Number of Timepoints = ",numT
			print "Duration=",duration
			step = duration/float(numT)
			stamps = []
			for t in range(0, numT):
				stamps.append(step*t)
			self.setTimeStamps(stamps)
			self.setAbsoluteTimeStamps(stamps)
			
		self.channel = channel
		self.dimensions = None
		self.voxelsize = None
		self.spacing = None
		self.color = None
		self.ctf = None
		self.setPath(filename)
		self.datasetCount = None
					
	def getDataSetCount(self):
		"""
		Returns the number of individual DataSets (=time points)
		managed by this DataSource
		"""
		if not self.datasetCount:
			self.datasetCount = self.reader.GetNumberOfTimepoints(self.experiment)
		return self.datasetCount
		
	def getFileName(self):
		"""
		Return the file name
		"""    
		return self.filename
	
	def getDataSet(self, i, raw = 0):
		"""
		Returns the DataSet at the specified index
		Parameters:   i       The index
		"""
		self.setCurrentTimepoint(i)
		self.timepoint = i
		data = self.reader.GetTimepoint(self.experiment, self.channel, i)
		return self.getResampledData(data, i)
		
	def internalGetDimensions(self):
		"""
		Returns the (x,y,z) dimensions of the datasets this 
					 dataunit contains
		"""
		return self.reader.GetDimensions(self.experiment)
		
	def getSpacing(self):
		"""
		Returns the spacing of the datasets this 
					 dataunit contains
		"""
		if not self.spacing:
			a, b, c = self.getVoxelSize()
			self.spacing = [1, b / a, c / a]
		return self.spacing
		
	def getVoxelSize(self):
		"""
		Returns the voxel size of the datasets this 
					 dataunit contains
		"""
		if not self.voxelsize:
			self.voxelsize = self.reader.GetVoxelSize(self.experiment)
		return self.voxelsize

	def getScalarRange(self):
		"""
		Return scalar range of data
		"""
		self.getBitDepth()
		self.scalarRange = (0, 2 ** self.bitdepth - 1)
		return self.scalarRange
	
	def loadFromFile(self, filename):
		"""
		Loads the specified .txt-file and imports data from it.
		Parameters:   filename  The .txt-file to be loaded
		"""
		exts = filename.split(".")
		if exts[-1].lower()=="lei":
			filename = ".".join(exts[:-1])
			if os.path.exists(filename+".txt"):
				filename+=".txt"
			elif os.path.exists(filename+".TXT"):
				filename+=".TXT"
			elif os.path.exists(filename+".Txt"):
				filename+=".Txt"
		self.filename = filename
		self.path = os.path.dirname(filename)
		self.reader.setFileName(filename)
		try:
			f = open(filename)
			f.close()
		except IOError, ex:
			Logging.error("Failed to open Leica File",
			"Failed to open file %s for reading: %s" % (filename, str(ex)))

		self.reader.Read()
		dataunits = []
		experiments = self.reader.GetExperiments()

		for experiment in experiments:
			if experiment in self.reader.nonExistent:
				continue
			channelNum = self.reader.GetNumberOfChannels(experiment)
			#print "There are %d channels in %s"%(channelNum,filename)
			for i in range(channelNum):
				# We create a datasource with specific channel number that
				#  we can associate with the dataunit
				datasource = LeicaDataSource(filename, experiment, i)
				dataunit = DataUnit()
				dataunit.setDataSource(datasource)
				dataunits.append((experiment, dataunit))
			
		return dataunits

	def uniqueId(self):
		"""
		Return a unique id identifying this channel
		"""
		return "%s|%s|%d"%(self.filename, self.experiment, self.channel)
	
	def getName(self):
		"""
		Returns the name of the dataset series which this datasource
					 operates on
		"""
		return "Ch%.2d" % self.channel
		
	def getColorTransferFunction(self):
		"""
		Returns the ctf of the dataset series which this datasource
					 operates on
		"""
		bd = self.getBitDepth()
		if bd == 32:
			return None
		if not self.ctf:
			lutColor = self.reader.getLutColor(self.experiment, self.channel)
			ctf = self.getColorByName(lutColor)
			self.ctf = ctf
		return self.ctf        
		
	def getColorByName(self, name):
		"""
		return a ctf based on a color name
		"""
		ctf = vtk.vtkColorTransferFunction()
		ctf.AddRGBPoint(0, 0.0, 0.0, 0.0)
		maxval = (2**self.getBitDepth())-1
		if name == "Green":
			ctf.AddRGBPoint(maxval, 0.0, 1.0, 0.0)
		elif name == "Gray":
			ctf.AddRGBPoint(maxval, 1.0, 1.0, 1.0)
		elif name == "Red":
			ctf.AddRGBPoint(maxval, 1.0, 0.0, 0.0)
		elif name == "Blue":
			ctf.AddRGBPoint(maxval, 0.0, 0.0, 1.0)
		elif name == "Yellow":
			ctf.AddRGBPoint(maxval, 1.0, 1.0, 0.0)
		elif name == "Magenta":
			ctf.AddRGBPoint(maxval, 1.0, 0.0, 1.0)
		elif name == "Cyan":
			ctf.AddRGBPoint(maxval, 0.0, 1.0, 1.0)
		else:
			ctf.AddRGBPoint(maxval, 1.0, 1.0, 1.0)
		return ctf
		
class LeicaExperiment:
	def __init__ (self, ExpPathTxt, progressCallback = None):
		self.SeriesDict = {}
		# Store snapshots in a dict of it's own, so we can give them separately 
		# if requested
		self.progressCallback = progressCallback
		self.SnapshotDict = {}
		self.nonExistent = []
		self.path = ""
		self.timepoints = {}
		self.readers = {}

		self.RE_ScanMode = re.compile(r'ScanMode.*', re.I)
		self.RE_X = re.compile(r'Format-Width.+\d+', re.I)
		self.RE_Y = re.compile(r'Format-Height.+\d+', re.I)
		self.RE_NumChan = re.compile(r'Dimension_2.*', re.I)
		self.RE_LogicalSize = re.compile(r'Logical\sSize.+\d+', re.I)
		self.RE_NumSect = re.compile(r'Dimension_3.*', re.I)
		self.RE_T = re.compile(r'Dimension_4.*', re.I)
		self.RE_SeriesName = re.compile(r'Series\sName:(.*)', re.I)
		self.RE_Width = re.compile(r'Size-Width.+\d+', re.I)
		self.RE_Height = re.compile(r'Size-Height.+\d+', re.I)
		self.RE_Depth = re.compile(r'Size-Depth.+\d+', re.I)
		self.RE_VoxelWidth = re.compile(r'Voxel-Width.+\d+', re.I)
		self.RE_VoxelHeight = re.compile(r'Voxel-Height.+\d+', re.I)
		self.RE_VoxelDepth = re.compile(r'Voxel-Depth.+\d+', re.I)
		self.RE_Bit_Depth = re.compile(r'Resolution in Bit.+\d+', re.I)
		self.RE_PixelSize = re.compile(r'Pixel Size in Byte.+\d+', re.I)
		self.RE_NonWhitespace = re.compile(r'\w+', re.I)
		self.RE_PhysLength = re.compile(r'Physical Length.*', re.I)
		self.RE_PhysOrig = re.compile(r'Physical\sOrigin.*', re.I)
#		self.RE_TimeStamp = re.compile(r'Stamp_(\d+).*(\d+):

		self.setFileName(ExpPathTxt)
		self.TP_CH_VolDataList = {}
	
	def getLutColor(self, experiment, channel):
		"""
		return the name of the color that the lut of the given experiment represents
		"""
		return self.SeriesDict[experiment]['LutColor_c%d'%channel]
	
	def isRaw(self, experiment):
		"""
		return a boolean indicating whether a given experiment is raw or not
		"""
		return self.SeriesDict[experiment]['RawMode']
				
	def setFileName(self, filename):
		"""
		Sets the file name to be opened
		"""
		self.filename = filename
		if filename:
			self.path = os.path.dirname(filename)
			self.Read()
	
	def Read(self):
		"""
		Read the given file
		"""    
		self.CreateExpDataStruct(self.filename)
		
	def GetExperiments(self):
		"""
		Return the number of channels this dataset contains
		"""    
		return self.SeriesDict.keys()

	def GetNumberOfChannels(self, experiment):
		"""
		Return the number of channels an experiment contains
		"""    
		return self.SeriesDict[experiment]["NumChan"]
		
	def GetDuration(self, experiment):
		"""
		Return the duration of the experiment
		"""
		return self.SeriesDict[experiment].get("Seconds",0)

	def GetNumberOfTimepoints(self, experiment):
		"""
		Return the number of channels an experiment contains
		"""        
		return self.SeriesDict[experiment]["Num_T"]
		
	def GetDimensions(self, experiment):
		"""
		Return dimensions of an experiment
		"""    
		x = self.SeriesDict[experiment]["Resolution_X"]   
		y = self.SeriesDict[experiment]["Resolution_Y"]   
		z = self.SeriesDict[experiment]["Number_Sections"]   
		return (x, y, z)
		
	def GetTimepoint(self, experiment, channel, timepoint):
		"""
		Return the data for a given timepoint
		"""    
		if (experiment,channel) not in self.timepoints or self.timepoints[(experiment, channel)] != timepoint:
			self.timepoints[(experiment,channel)] = timepoint
			self.readers[(experiment,channel)] = self.getChannelReader(experiment, channel, timepoint) 
			
		return self.readers[(experiment, channel)].GetOutput()
		
	def GetVoxelSize(self, experiment):
		"""
		Return voxel size of an experiment
		"""    
		x = self.SeriesDict[experiment]["Voxel_Width_X"]   
		y = self.SeriesDict[experiment]["Voxel_Height_Y"]   
		z = self.SeriesDict[experiment]["Voxel_Depth_Z"]   
		# They are now in microm, scale to meters as LSM reader does
		x /= 1000000.0
		y /= 1000000.0
		z /= 1000000.0
		return (x, y, z)

	def Sep_Series(self, ExpPathTxt):
		InfoFile = open(ExpPathTxt)#If the actual file is returned with the open dialog, we can skip this.
		InfoFile_AsString = InfoFile.read()
		SplitString = re.compile(r'\*+\sNEXT\sIMAGE\s\*+', re.I) 
		ImageList = SplitString.split(InfoFile_AsString)
		self.Series_Data_List = []
		for stringa in ImageList:
			#self.Series_Data_List.append=cStringIO(ImageList[stringCounter])
			self.Series_Data_List.append(stringa)
			ExpPathPair = os.path.split(ExpPathTxt)
			self.ExpPath = ExpPathPair[0]
			
			PreExpName = ExpPathPair[1]
			PreExpNameLst = string.split(PreExpName, '.')
			self.ExpName = PreExpNameLst[0] #this gets rid of the file extension
			
	def GetScanMode(self, Series_Data):
		"""
		Return the scan mode from given data
		"""        
		SeriesScanModeLine = self.RE_ScanMode.search(Series_Data)
		if not SeriesScanModeLine:
			return None
		SeriesScanModeSplit = SeriesScanModeLine.group(0).split()
		SeriesScanMode = SeriesScanModeSplit[1].strip()
		return SeriesScanMode

	def GetSeriesName(self, Series_Data):
		"""
		Return the series name from given data
		"""               
		SeriesNameString = self.RE_SeriesName.search(Series_Data)
		SeriesNameLine = SeriesNameString.group(1)
		SeriesNameLine = SeriesNameLine.strip()
		SeriesNameLine = SeriesNameLine.replace(chr(0), "")
		return SeriesNameLine
		
		
	def GetNumChan(self, Series_Data):
		"""
		Return the number of channels from given data
		"""              
		SeriesDataSplit = self.RE_NumChan.split(Series_Data)
		NumChan_String = SeriesDataSplit[1]
		NumChanMatch = self.RE_LogicalSize.search(NumChan_String)
		NumChanLine = NumChanMatch.group(0)
		WordsNumChan = NumChanLine.split()
		WordsNumChan.reverse()
		NumChan = int(WordsNumChan[0].strip())
		return NumChan        
		
	def GetZDimension(self, Series_Data):
		"""
		Return the z dimension from given data
		"""              
		#Get the z-dimension value
		if not self.RE_NumSect.search(Series_Data):
			return 1
		SeriesDataSplit = self.RE_NumSect.split(Series_Data)
		
		NumSect_String = SeriesDataSplit[1]
		NumSectMatch = self.RE_LogicalSize.search(NumSect_String)
		NumSectLine = NumSectMatch.group(0)
		WordsZ_Res = NumSectLine.split()
		WordsZ_Res.reverse()
		Z_Res = int(WordsZ_Res[0].strip())
		return Z_Res
		
	def GetTimeDimension(self, Series_Data):
		"""
		Return the time dimension from given data
		"""          
		SeriesDataSplit = self.RE_T.split(Series_Data)
		T_String = SeriesDataSplit[1]
		T_Match = self.RE_LogicalSize.search(T_String)
		T_Line = T_Match.group(0)
		T_Line = T_Line.replace(chr(0), " ")
		WordsNumT = T_Line.split()
		#WordsNumT.reverse()
		NumT = int(WordsNumT[-1].strip())
		
		PhysLengthMatch = self.RE_PhysLength.search(T_String)
		PhysLengthLine = PhysLengthMatch.group(0)
		PhysLengthLine = PhysLengthLine.replace(chr(0), " ")
		WordsPhysLength = PhysLengthLine.split()
		Seconds = float(WordsPhysLength[-2].strip())
		
		return NumT, Seconds
		
	def GetWidth(self, Series_Data):
		"""
		Return the width from given data
		"""                  
		SeriesWidthString = self.RE_Width.search(Series_Data)
		SeriesWidthLine = SeriesWidthString.group(0)
		SeriesWidthSplit = SeriesWidthLine.split()
		SeriesWidthSplit.reverse()
		SeriesWidth = float(SeriesWidthSplit[0])
		return SeriesWidth
		
	def GetHeight(self, Series_Data):
		"""
		Return the height from given data
		"""                   
		SeriesHeightString = self.RE_Height.search(Series_Data)
		SeriesHeightLine = SeriesHeightString.group(0)
		SeriesHeightSplit = SeriesHeightLine.split()
		SeriesHeightSplit.reverse()
		SeriesHeight = float(SeriesHeightSplit[0].strip())
		return SeriesHeight
		
	def GetDepth(self, Series_Data):
		"""
		Return the depth from given data
		""" 
		SeriesDepthString = self.RE_Depth.search(Series_Data)
		SeriesDepthLine = SeriesDepthString.group(0)
		
		SeriesDepthSplit = SeriesDepthLine.split()
		SeriesDepthSplit.reverse()
		
		SeriesDepth = float(SeriesDepthSplit[0].strip())
		return SeriesDepth
		
	def GetVoxelWidth(self, Series_Data):
		"""
		Return the voxel width from given data
		""" 
		SeriesVoxelWidthString = self.RE_VoxelWidth.search(Series_Data)
		SeriesVoxelWidthLine = SeriesVoxelWidthString.group(0)
		SeriesVoxelWidthSplit = SeriesVoxelWidthLine.split()
		SeriesVoxelWidthSplit.reverse()
		SeriesVoxelWidth = float(SeriesVoxelWidthSplit[0].strip())
		return SeriesVoxelWidth
		
	def GetVoxelHeight(self, Series_Data):
		"""
		Return the voxel height from given data
		"""             
		SeriesVoxelHeightString = self.RE_VoxelHeight.search(Series_Data)
		SeriesVoxelHeightLine = SeriesVoxelHeightString.group(0)
		SeriesVoxelHeightSplit = SeriesVoxelHeightLine.split()
		SeriesVoxelHeightSplit.reverse()
		SeriesVoxelHeight = float(SeriesVoxelHeightSplit[0].strip())
		return SeriesVoxelHeight
		
	def GetVoxelDepth(self, Series_Data):
		"""
		Return the voxel depth from given data
		"""                
		SeriesVoxelDepthString = self.RE_VoxelDepth.search(Series_Data)
		SeriesVoxelDepthLine = SeriesVoxelDepthString.group(0)
		SeriesVoxelDepthSplit = SeriesVoxelDepthLine.split()
		SeriesVoxelDepthSplit.reverse()
		SeriesVoxelDepth = float(SeriesVoxelDepthSplit[0].strip())
		return SeriesVoxelDepth
		
	def GetBitDepth(self, Series_Data):
		"""
		Return the bit depth from given data
		"""             
		SeriesBitDepthString = self.RE_Bit_Depth.search(Series_Data)
		SeriesBitDepthLine = SeriesBitDepthString.group(0)
		SeriesBitDepthSplit = SeriesBitDepthLine.split()
		SeriesBitDepthSplit.reverse()
		SeriesBitDepth = float(SeriesBitDepthSplit[0].strip())
		return SeriesBitDepth

	def GetNumberOfComponents(self, Series_Data):
		"""
		Return the number of components per pixel
		"""             
		SeriesPixelSizeString = self.RE_PixelSize.search(Series_Data)
		if not SeriesPixelSizeString:
			return 1
		SeriesPixelSizeLine = SeriesPixelSizeString.group(0)
		SeriesPixelSizeSplit = SeriesPixelSizeLine.split()
		SeriesPixelSizeSplit.reverse()
		SeriesPixelSize = float(SeriesPixelSizeSplit[0].strip())
		return SeriesPixelSize
		
		
	def GetResolutionX(self, Series_Data):
		"""
		Return the x resolution from given data
		"""                                    
		SeriesResXString = self.RE_X.search(Series_Data)
		SeriesResXLine = SeriesResXString.group(0)
		SeriesResXSplit = SeriesResXLine.split()
		SeriesResXSplit.reverse()
		SeriesResX = int(SeriesResXSplit[0].strip())
		return SeriesResX
				
	def GetResolutionY(self, Series_Data):
		"""
		Method: GetResolutionY(data)
		Return the x resolution from given data
		"""                                            
		SeriesResYString = self.RE_Y.search(Series_Data)
		SeriesResYLine = SeriesResYString.group(0)
		SeriesResYSplit = SeriesResYLine.split()
		SeriesResYSplit.reverse()
		SeriesResY = int(SeriesResYSplit[0].strip())
		return SeriesResY

	def Extract_Series_Info(self):
		"""
		Method: Extract_Series_Info
		Extract the info about the series
		"""        
		self.SeriesDict = {}
		
		for string in self.Series_Data_List:
			Series_Data = string
			Series_Info = {}
 
			seriesname = self.GetSeriesName(Series_Data)
			lines = string.split("\n")
			lutNameLine="Name:	Green"
			channelLUTNames = []
			for i,line in enumerate(lines):
				if "LUT_" in line:
					lutNameLine = lines[i+1]
					channelLUTNames.append(lutNameLine)

			if not channelLUTNames:
				channelLUTNames.append(lutNameLine)
			
			# strip the last two characters, which are \x00 and \r
			for i,name in enumerate(channelLUTNames):
				name = name.split("\t")[1].strip()
				name = name.replace("\x00","")
				Series_Info['LutColor_c%d'%i] = name
				
			SeriesScanMode = self.GetScanMode(Series_Data)
			
			Series_Info['Pixel_Size'] = self.GetNumberOfComponents(Series_Data)                
			Series_Info['Bit_Depth'] = self.GetBitDepth(Series_Data)
			Series_Info['Series_Name'] = seriesname
			if not SeriesScanMode:
				if "snapshot" in seriesname.lower():
					# TODO: This is a snapshot, handle it as such
					print "Do not know how to handle snapshot %s, continuing" % seriesname
					continue
				else:
					print "Unrecognized entity without scanmode:", seriesname
			else:
				Series_Info['Scan_Mode'] = SeriesScanMode
			
			if SeriesScanMode in ['xyz', 'xyzt']:
				Logging.info("Scan mode is ", SeriesScanMode, kw = "io")
				#print Series_Data
				Series_Info['NumChan'] = self.GetNumChan(Series_Data)
				#print "Number of channels=",Series_Info['NumChan']
				SeriesDataSplit = self.RE_NumChan.split(Series_Data)
				Series_Data = SeriesDataSplit[1] #Breaks data text into progressively smaller pieces
		  
				z = self.GetZDimension(Series_Data)
				Series_Info['Number_Sections'] = z
				if z != 1:
					SeriesDataSplit = self.RE_NumSect.split(Series_Data)
					Series_Data = SeriesDataSplit[1] #Breaks data text into progressively smaller pieces
				
				#Check for Time dimension--if so, get time data
				if self.RE_T.search(Series_Data):
					t, seconds = self.GetTimeDimension(Series_Data)
					
					Series_Info['Num_T'] = t
					Series_Info['Seconds'] = seconds
					SeriesDataSplit = self.RE_T.split(Series_Data)
					Series_Data = SeriesDataSplit[1]
				else:
					#raise "No timepoints found"
					Series_Info['Num_T'] = 1
				Series_Info['Width_X'] = self.GetWidth(Series_Data)
				Series_Info['Height_Y'] = self.GetHeight(Series_Data)
				Series_Info['Depth_Z'] = self.GetDepth(Series_Data)
				Series_Info['Voxel_Width_X'] = self.GetVoxelWidth(Series_Data)
				Series_Info['Voxel_Height_Y'] = self.GetVoxelHeight(Series_Data)
				Series_Info['Voxel_Depth_Z'] = self.GetVoxelDepth(Series_Data)


				Series_Info['Resolution_X'] = self.GetResolutionX(Series_Data)
				Series_Info['Resolution_Y'] = self.GetResolutionY(Series_Data)
				
				#make a dictionary containing each series info dictionary (dictionary of dictionaries)
				SeriesName = Series_Info['Series_Name']
				self.SeriesDict[SeriesName] = Series_Info

	def Create_Tiff_Lists(self):
		for key, value in self.SeriesDict.items():
			Series_Info = value
			Series_Name = key
			Num_T_Points = (Series_Info['Num_T'])
			
			notFound = 0
			TimePoints = []
			for a in xrange(Num_T_Points): #starts at 0 and counts up to (but not including) Num_T_Points.
				n = int(math.log(Num_T_Points))
				if n == 1:
					n = 2
				TP_pat = "_t%%.%dd" % n
				TP_Name = TP_pat % a
				#TP_Name='_t'+str((a%10000)//1000)+str((a%1000)//100)+str((a%100)//10)+str((a%10)//1)
				
				Num_Chan = Series_Info['NumChan']
				Channels = []
				rawMode = 0
				
				for b in xrange(Num_Chan):
					File_List = []
					if 1 or Num_Chan > 1:
						CH_Name = ('_ch' + str((b % 100) // 10) + str((b % 10) // 1))
					else:
						print "Since only one channel, no _chXXX"
						CH_Name = ("")
					Num_Z_Sec = Series_Info['Number_Sections']
					for c in xrange(Num_Z_Sec):
						#if Num_Z_Sec!=1:
						Z_Name = str('_z' + str((c % 1000) // 100) + str((c % 100) // 10) + str((c % 10) // 1))
						
						if Num_T_Points > 1:
							Slice_Name_With_Z = self.ExpName + '_' + Series_Name + TP_Name + Z_Name + CH_Name + '.tif'
							Slice_Name_No_Z = self.ExpName + '_' + Series_Name + TP_Name + CH_Name + '.tif'
						else:
							Slice_Name_With_Z = self.ExpName + '_' + Series_Name + Z_Name + CH_Name + '.tif'
							Slice_Name_No_Z = self.ExpName + '_' + Series_Name  + CH_Name + '.tif'

						withZName = os.path.join(self.path, Slice_Name_With_Z)
						noZName = os.path.join(self.path, Slice_Name_No_Z)
						
						withZNameRaw = withZName.replace(".tif",".raw")
						noZNameRaw = noZName.replace(".tif",".raw")
						
						if os.path.exists(withZNameRaw):
							File_List.append(Slice_Name_With_Z.replace(".tif",".raw"))
							rawMode = 1
						if os.path.exists(noZNameRaw):
							File_List.append(Slice_Name_No_Z.replace(".tif",".raw"))
							rawMode = 1
						if os.path.exists(withZName):
							File_List.append(Slice_Name_With_Z)
							#print "Using with Z"
						elif os.path.exists(noZName):
							#print "Using no z"
							File_List.append(Slice_Name_No_Z)
						
					Channels.append(File_List)
					if not File_List:
						notFound = 1
				TimePoints.append(Channels)
			if notFound:
				self.nonExistent.append(Series_Name)
			else:
				Series_Info['TiffList'] = TimePoints         
				Series_Info['RawMode'] = rawMode
				self.SeriesDict[Series_Name] = Series_Info #puts modified Series_Info dictionary back into SeriesDict

	def CreateExpDataStruct(self, ExpPathTxt):
		self.Sep_Series(ExpPathTxt)
		self.Extract_Series_Info()
		self.Create_Tiff_Lists()
			
	def getTIFFReader(self, Series_Info, Channel):
		"""
		create a tiff reader that reads then given channel of the given series
		"""
		XYDim = Series_Info['Resolution_X'] - 1
		NumSect = Series_Info['Number_Sections'] - 1
		XSpace = Series_Info['Voxel_Width_X']
		YSpace = Series_Info['Voxel_Height_Y']
		ZSpace = Series_Info['Voxel_Depth_Z']
		TIFFReader = vtkbxd.vtkExtTIFFReader()
		if self.progressCallback:
			TIFFReader.AddObserver("ProgressEvent", lib.messenger.send)
			lib.messenger.connect(TIFFReader, 'ProgressEvent', self.progressCallback)
		if Series_Info['Pixel_Size'] != 3:
			TIFFReader.RawModeOn()
		
		arr = vtk.vtkStringArray()
		for i in Channel:
			arr.InsertNextValue(os.path.join(self.path, i))
		TIFFReader.SetFileNames(arr)
		#First read the images for a particular channel
		# Check to see whether the image name contains either
		# channels or z slices at all. If not, then we can just you
		# the filename and skip a whole bunch of processing
	
		if Series_Info['Bit_Depth'] == 8:
			TIFFReader.SetDataScalarTypeToUnsignedChar()
		else:
			raise "Only 8-bit data supported"

		spacingX,spacingY,spacingZ = 1.0,1.0,1.0
		if XSpace != 0.0 and YSpace != 0.0:
			spacingY = YSpace / XSpace
		if XSpace != 0.0 and ZSpace != 0.0:
			spacingZ = ZSpace / XSpace
		
		TIFFReader.FileLowerLeftOff()
		TIFFReader.SetDataExtent(0, XYDim, 0, XYDim, 0, NumSect)
		TIFFReader.SetDataSpacing(spacingX, spacingY, spacingZ)
		TIFFReader.Update()
		return TIFFReader
		
	def getRAWReader(self, Series_Info, Channel):
		"""
		create a tiff reader that reads then given channel of the given series
		"""
		XYDim = Series_Info['Resolution_X'] - 1
		NumSect = Series_Info['Number_Sections'] - 1
		XSpace = Series_Info['Voxel_Width_X']
		YSpace = Series_Info['Voxel_Height_Y']
		ZSpace = Series_Info['Voxel_Depth_Z']
		
		RAWReader = vtk.vtkImageReader2()
		if self.progressCallback:
			RAWReader.AddObserver("ProgressEvent", lib.messenger.send)
			lib.messenger.connect(RAWReader, 'ProgressEvent', self.progressCallback)
		arr = vtk.vtkStringArray()
		for i in Channel:
			arr.InsertNextValue(os.path.join(self.path, i))
		RAWReader.SetFileNames(arr)
	
		if Series_Info['Bit_Depth'] == 8:
			RAWReader.SetDataScalarTypeToUnsignedChar()
		elif Series_Info['Bit_Depth'] == 12:
			RAWReader.SetDataScalarTypeToUnsignedShort()
		RAWReader.FileLowerLeftOff()

		spacingX,spacingY,spacingZ = 1.0,1.0,1.0
		if XSpace != 0.0 and YSpace != 0.0:
			spacingY = YSpace / XSpace
		if XSpace != 0.0 and ZSpace != 0.0:
			spacingZ = ZSpace / XSpace
		
		RAWReader.SetDataExtent(0, XYDim, 0, XYDim, 0, NumSect)
		RAWReader.SetDataSpacing(spacingX, spacingY, spacingZ)
		RAWReader.Update()
		return RAWReader

	def getChannelReader(self, Series_Name, channel = 0, timepoint = 0):
		Series_Info = self.SeriesDict[Series_Name]
		FileList = Series_Info['TiffList']

		rawMode = Series_Info['RawMode']
		#print "Reading leica volume",Series_Name
		self.TP_CH_VolDataList = [] #contains the vol data for each timepoint, each channel
		#for TimePoint in FileList:
		
		ChnlVolDataLst = [] #contains the volumetric datasets for each channel w/in each timepoint
#		for Channel in FileList[timepoint]:
		Channel = FileList[timepoint][channel]
		if not rawMode:
			imageReader = self.getTIFFReader(Series_Info, Channel)
		else:
			imageReader = self.getRAWReader(Series_Info, Channel)
		return imageReader
