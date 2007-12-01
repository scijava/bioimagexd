# -*- coding: iso-8859-1 -*-
"""
 Unit: FileListDataSource
 Project: BioImageXD
 Created: 29.03.2006, KP
 Description: A datasource for a list of given files as a time series,
				dependent on the given number of slices in a stack

 Copyright (C) 2005  BioImageXD Project
 See CREDITS.txt for details

 This program is free software; you can redistribute it and / or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program; if not, write to the Free Software
 Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111 - 1307  USA
"""

__author__ = "BioImageXD Project < http://www.bioimagexd.org/>"
__version__ = "$Revision: 1.37 $"
__date__ = "$Date: 2005 / 01 / 13 13:42:03 $"

from lib.DataSource.DataSource import DataSource
import Image
import TiffImagePlugin
import Logging
import os.path
import vtk
import vtkbxd

def getExtensions(): 
	return []

def getFileType(): 
	return "filelist"

def getClass(): 
	return FileListDataSource	 
	

class FileListDataSource(DataSource):
	"""
	Created: 12.04.2005, KP
	Description: File list datasource for reading a dataset from a given set of files
	"""
	def __init__(self, filenames = [], callback = None):
		"""
		Created: 12.04.2005, KP
		Description: Constructor
		"""    
		DataSource.__init__(self)
		self.name = "Import"
		self.extMapping = {"tif": "TIFF", "tiff": "TIFF", "png": "PNG", "jpg": "JPEG", "jpeg": "JPEG", \
							"pnm": "PNM", "vti": "XMLImageData", "vtk": "DataSet", "bmp": "BMP"}
		self.dimMapping = {"bmp":2, "tif":2, "tiff":2, "png":2, "jpg":2, "jpeg":2, "pnm":2, "vti":3, "vtk":3}
		
		self.callback = callback
		self.dimensions = None
		self.voxelsize = (1, 1, 1)
		self.spacing = (1, 1, 1)
		self.color = None
		self.shift = None
		self.isRGB = 0
		self.numberOfComponents = 1
		self.tps = -1
		# Store results of checking dimensions of given filenames in a dictionary
		self.dimensionCheck = {}
		if filenames:
			self.numberOfImages = len(filenames)
			self.getDataSetCount()
		
		self.imageDims = {}
		
		self.numberOfImages = 0
		self.readers = []
		self.slicesPerTimepoint = 1
		self.is3D = 0
		
	def getNumberOfScalarComponents(self):
		"""
		Created: 24.10.2007, KP
		Description: return the number of scalar components
		"""
		return self.numberOfComponents
	
	def setColorTransferFunction(self, ctf):
		"""
		Created: 04.06.2007, KP
		Description: Set the color transfer function
		"""
		self.ctf = ctf
		
	def is3DImage(self):
		"""
		Created: 08.05.2007, KP
		Description: Return a flag indicating whether the images are 2D or 3D images
		"""
		return self.is3D
				
	def setFilenames(self, filenames):
		"""
		Created: 07.05.2007, KP
		Description: set the filenames that will be read
		"""
		if not self.dimensions:
			self.retrieveImageInfo(filenames[0])
		self.filenames = filenames
		self.numberOfImages = len(filenames)
		if not self.checkImageDimensions(filenames):
			raise Logging.GUIError("Image dimensions do not match", \
									"Some of the selected files have differing dimensions, \
									and cannot be imported into the same dataset.")		 
		self.getReadersFromFilenames()
				
		
		
	def checkImageDimensions(self, filenames):
		"""
		Created: 16.05.2007, KP
		Description: check that each image in the list has the same dimensions
		"""
		s = None
		hashStr = filenames[:]
		hashStr.sort()
		hashStr = str(hashStr)
		# check to see if there's already a result of the check for these filenames in the cache
		if hashStr in self.dimensionCheck:
			Logging.info("Using cached result for dimensions check: %s"%(str(self.dimensionCheck[hashStr])))
			return self.dimensionCheck[hashStr]
			
		for file in filenames:
			if file not in self.imageDims:
				try:
					i = Image.open(file)
				except IOError, ex:
					raise Logging.GUIError("Cannot open image file", "Cannot open image file %s" % file)
				fSize = i.size
				self.imageDims[file] = i.size
			else:
				fSize = self.imageDims[file]
			if s and fSize != s:
				x0, y0 = s
				x1, y1 = fSize
				self.dimensionCheck[hashStr] = False
				return 0
			s = fSize 
			fn = file
		self.dimensionCheck[hashStr] = True
		return 1
		
	def getReaderByExtension(self, ext, isRGB = 0):
		"""
		Created: 08.05.2007, KP
		Description: return a VTK image reader based on file extension
		"""
		assert ext in self.extMapping, "Extension not recognized: %s" % ext
		mpr = self.extMapping[ext]
		prefix="vtk"
		# If it's a tiff file, we use our own, extended TIFF reader
		if self.extMapping[ext] == "TIFF" and not isRGB:
			mpr = "ExtTIFF"
			prefix="vtkbxd"
		self.rdrstr = "%s.vtk%sReader()" % (prefix, mpr)
		rdr = eval(self.rdrstr)
		if ext == "bmp":
			rdr.Allow8BitBMPOn()
		if mpr == "ExtTIFF" and not isRGB:
			rdr.RawModeOn()
		
		return rdr

	def getReadersFromFilenames(self):
		"""
		Created: 07.05.2007, KP
		Description: create the reader list from a given set of file names and parameters
		"""		   
#		self.z = int(self.slicesPerTimepoint)


		for i in self.readers:
			del i
		self.readers = []
		

		if not self.filenames:
			raise Logging.GUIError("No files could be found", \
									"For some reason, no files were listed to be imported.")		 
					
		files = self.filenames
		print "Determining readers from ", self.filenames
		
		isRGB = 1
		ext = files[0].split(".")[-1].lower()
		
		if ext in ["tif", "tiff"]:
			tiffimg = Image.open(files[0])
			if tiffimg.mode == "RGB":
				print "MODE IS RGB, IS AN RGB IMAGE"
			else:
				print "MODE ISN'T RGB, THEREFOR NOT RGB"
				isRGB = 0
		self.isRGB = isRGB
				
		dirName = os.path.dirname(files[0])
		print "THERE ARE ", self.slicesPerTimepoint, "SLICES PER TIMEPOINT"
		ext = files[0].split(".")[-1].lower()

		dim = self.dimMapping[ext]
		self.is3D = (dim == 3)
		self.readers = []
		
		if dim == 3:
			totalFiles = len(files)
			for i, file in enumerate(files):
				rdr = self.getReaderByExtension(ext, isRGB)
				rdr.SetFileName(file)
				self.readers.append(rdr)
			return
			
		totalFiles = len(files) / self.slicesPerTimepoint

		imgAmnt = len(files)
		if totalFiles == 1:
			rdr = self.getReaderByExtension(ext, isRGB)
			arr = vtk.vtkStringArray()
			for fileName in files:
				arr.InsertNextValue(os.path.join(dirName, fileName))
			rdr.SetFileNames(arr)
			self.readers.append(rdr)
			return
			
		if imgAmnt > 1:
			# If the pattern doesn't have %, then we just use
			# the given filenames and allocate them to timepoints
			# using  slicesPerTimepoint slices per timepoint
			ntps = len(files) / self.slicesPerTimepoint
			filelst = files[:]
			# dirn #TODO: what was this?
			for tp in range(0, ntps):
				rdr = self.getReaderByExtension(ext, isRGB)
				arr = vtk.vtkStringArray()
				for i in range(0, self.slicesPerTimepoint):
					arr.InsertNextValue(filelst[0])
					filelst = filelst[1:]
				
				rdr.SetFileNames(arr)
				rdr.SetDataExtent(0, self.x - 1, 0, self.y - 1, 0, self.slicesPerTimepoint - 1)
				rdr.SetDataSpacing(self.spacing)
				rdr.SetDataOrigin(0, 0, 0)
				self.readers.append(rdr)

			return
		elif imgAmnt == 1:
			# If only one file
			rdr = self.getReaderByExtension(ext, isRGB)
			rdr.SetDataExtent(0, self.x - 1, 0, self.y - 1, 0, self.slicesPerTimepoint - 1)
			rdr.SetDataSpacing(self.spacing)
			rdr.SetDataOrigin(0, 0, 0)
			
			rdr.SetFileName(files[0])

			Logging.info("Reader = ", rdr, kw = "io")
			self.readers.append(rdr)
			

	def getSlicesPerTimepoint(self):
		"""
		Created: 24.10.2007, KP
		Description: return the number of slices per timepoint
		"""
		return self.slicesPerTimepoint

	def setSlicesPerTimepoint(self, n):
		"""
		Created: 07.05.2007, KP
		Description: Set the number of slices that belong to a given timepoint
		"""
		assert n > 0, "Slices per timepoint needs to be greater than 0"
		print "Setting slices per timepoint to ", n
		self.slicesPerTimepoint = n
		self.z = n
		self.readers = []
		
	def getDataSetCount(self):
		"""
		Created: 12.04.2005, KP
		Description: Returns the number of individual DataSets (=time points)
		managed by this DataSource
		"""
		return int(self.numberOfImages / self.slicesPerTimepoint)
		
	def getDataSet(self, i, raw = 0):
		"""
		Created: 12.04.2005, KP
		Description: Returns the DataSet at the specified index
		Parameters:   i		  The index
		"""
		data = self.getTimepoint(i)
		if self.isRGB and self.numberOfComponents == 4:
			extract = vtk.vtkImageExtractComponents()
			extract.SetComponents(0, 1, 2)
			extract.SetInput(data)
			data = extract.GetOutput()
		return data
		
	def retrieveImageInfo(self, filename):
		"""
		Created: 21.04.2005, KP
		Description: A method that reads information from an image
		"""		   
		assert filename, "Filename must be defined"
		assert os.path.exists(filename), "File that we're retrieving information \
										from (%s) needs to exist, but doesn't." % filename
		ext  = filename.split(".")[-1].lower()
		rdr = self.getReaderByExtension(ext)
		
		if ext == "bmp":
			rdr.Allow8BitBMPOn()
		
		rdr.SetFileName(filename)
		rdr.Update()
		data = rdr.GetOutput()
		self.numberOfComponents = data.GetNumberOfScalarComponents()
		
		self.x, self.y, z = data.GetDimensions()
		self.dimensions = (self.x, self.y, self.slicesPerTimepoint)
		if z > 1:
			self.slicesPerTimepoint = z
			self.z = z
			self.dimensions = (self.x, self.y, self.slicesPerTimepoint)
			lib.messenger.send(self, "update_dimensions")
				
	def getTimepoint(self, n, onlyDims = 0):
		"""
		Created: 16.02.2006, KP
		Description: Return the nth timepoint
		"""		   
		if not self.readers:
			self.getReadersFromFilenames()
			
		if n >= len(self.readers):
			raise Logging.GUIError("Attempt to read bad timepoint", \
									"Timepoint %d is not defined by the given filenames" % n)
			n = 0
			
		self.reader = self.readers[n]
		data = self.reader.GetOutput()
		if not self.voxelsize:
			size = data.GetSpacing()
			x, y, z = [size.GetElement(x) for x in range(0, 3)]
			self.voxelsize = (x, y, z)
			print "Read voxel size", self.voxelsize

		if onlyDims:
			return 
		return data		   
	

	def getDimensions(self):
		"""
		Created: 12.04.2005, KP
		Description: Returns the (x,y,z) dimensions of the datasets this
		dataunit contains
		"""
		return (self.x, self.y, self.slicesPerTimepoint)

	def getSpacing(self):
		"""
		Created: 12.04.2005, KP
		Description: Returns the spacing of the datasets this 
					 dataunit contains
		"""
		if not self.spacing:
			a, b, c = self.getVoxelSize()
			self.spacing = [1, b / a, c / a]
		return self.spacing
		
	def getVoxelSize(self):
		"""
		Created: 12.04.2005, KP
		Description: Returns the voxel size of the datasets this 
					 dataunit contains
		"""
		return self.voxelsize
  
	def setVoxelSize(self, vxs):
		"""
		Created: 08.05.2007, KP
		Description: set the voxel sizes of the images that are read
		"""
		self.voxelsize = vxs
		a, b, c = vxs
		self.spacing = [1, b / a, c / a]		
			
			
	def loadFromFile(self, filename):
		"""
		Created: 12.04.2005, KP
		Description: Loads the specified .oif - file and imports data from it.
		"""
		return []
		

	def getName(self):
		"""
		Created: 18.11.2005, KP
		Description: Returns the name of the dataset series which this datasource
					 operates on
		"""
		return self.name

		
	def getColorTransferFunction(self):
		"""
		Created: 26.04.2005, KP
		Description: Returns the ctf of the dataset series which this datasource
					 operates on
		"""
		return self.ctf
