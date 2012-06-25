# -*- coding: iso-8859-1 -*-
"""
 Unit: MRCDataSource.py
 Project: BioImageXD
 Created: 2008/04/09, LP
 Description: Class for managing 3D MRC data located on disk

 Copyright (C) 2005	BioImageXD Project
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
__version__ = "$Revision$"
__date__ = "$Date$"

from lib.DataSource.DataSource import DataSource
from lib.DataUnit.DataUnit import DataUnit
import lib.messenger
import vtkbxd
import vtk
import Logging

def getExtensions(): return ["mrc","st"]
def getFileType(): return "MRC file format (*.mrc, *.st)"
def getClass(): return MRCDataSource

class MRCDataSource(DataSource):
	"""
	Datasource for managing 3D EM data stored in a MRC-file.
	"""
	def __init__(self, filename = ""):
		"""
		Constructor of MRCDataSource
		"""
		DataSource.__init__(self)
		self.filename = filename
		self.setPath(filename)

		self.bitDepth = 0
		self.spacing = None
		self.voxelSize = None

		# Create vtkMRCReader for reading MRC files
		self.reader = vtkbxd.vtkMRCReader()
		self.reader.AddObserver('ProgressEvent', lib.messenger.send)
		lib.messenger.connect(self.reader, 'ProgressEvent', self.updateProgress)

		if self.filename:
			self.reader.SetFileName(self.convertFileName(self.filename))
			if self.reader.OpenFile():
				if self.reader.ReadHeader():
					self.setOriginalScalarRange()
				else:
					Logging.error("Failed to read the header of the MRC file correctly",
					"Error in MRCDataSource.py in __init.py__, failed to read the header of the MRC file: %s" %(self.filename))
					return
			else:
				Logging.error("Failed to open file",
							  "Error in MRCDataSource.py in __init__, failed to open file: %s" %(self.filename))
				return

	def getDataSetCount(self):
		"""
		Returns the count of time points.
		@return Count of time points
		"""
		return 1

	def getBitDepth(self):
		"""
		Return bit depth of dataset
		@return Integer bit depth
		"""
		mode = self.reader.GetMode()
		if mode == 0:
			self.bitdepth = 8
		elif mode == 1:
			self.bitdepth = 16
		elif mode == 2:
			self.bitdepth = 32

		return self.bitdepth

	def getFileName(self):
		"""
		Returns the file name associated with datasource
		@return Filename
		"""
		return self.filename

	def getDataSet(self, i, raw = 0):
		"""
		Returns image data of datasource
		@param i Not used, here only for interface reasons
		@param raw A flag indicating that the data is not to be processed in any way
		@return vtkImageData
		"""
		data = self.reader.GetOutput()
		if raw:
			return data

		data = self.getResampledData(data, i)
		if self.explicitScale or (data.GetScalarType() != 3):
			data = self.getIntensityScaledData(data)
			
		return data

	def getName(self):
		"""
		Returns the name of the dataset handled by this DataSource
		@return Dataset name
		"""
		return "MRC Image"

	def loadFromFile(self, filename):
		"""
		Loads image from MRC-file and generates own DataSource
		@param filename Path to MRC-file
		@return List of tuples of datasets in file (only one)
		"""
		self.filename = filename
		dataUnits = []
		imageName = self.getShortName()
		dataSource = MRCDataSource(filename)
		dataUnit = DataUnit()
		dataUnit.setDataSource(dataSource)
		dataUnits.append((imageName,dataUnit))

		return dataUnits

	def getVoxelSize(self):
		"""
		Return size of voxel in X,Y and Z dimensions.
		@return list of floats meaning voxel size in meters.
		"""
		if not self.voxelSize:
			voxelSizeAngstrom = self.reader.GetVoxelSize()
			voxelSize = map(lambda x: x*(10**-10),voxelSizeAngstrom)
			self.voxelSize = voxelSize

		return self.voxelSize

	def getSpacing(self):
		"""
		Return spacing of the dataset
		@return List of floats as spacing
		"""
		if not self.spacing:
			voxelSize = self.getVoxelSize()
			spacing = [1.0,1.0,1.0]
			spacing[1] = voxelSize[1] / voxelSize[0]
			spacing[2] = voxelSize[2] / voxelSize[0]
			self.spacing = spacing
			
		return self.spacing

	def internalGetDimensions(self):
		"""
		Return dimensions of the dataset
		@return list of integers
		"""
		dims = self.reader.GetImageDims()
		dimList = list(dims)
		dimList.append(1)
		return tuple(dimList)

	def setOriginalScalarRange(self):
		"""
		Set original range of scalar values of data
		"""
		mode = self.reader.GetMode()
		min = 0
		max = 255

		if mode == 1:
			min = int(self.reader.GetMin())
			max = int(self.reader.GetMax())
		elif mode == 2:
			min = self.reader.GetMin()
			max = self.reader.GetMax()

		self.originalScalarRange = (min,max)

	def getScalarRange(self):
		"""
		Return scalar range of data
		@return Tuple of scalar range
		"""
		if not self.scalarRange:
			self.scalarRange = self.getOriginalScalarRange()

		if self.explicitScale and self.intensityScale != 1:
			x0,x1 = self.scalarRange
			x0 += self.getIntensityShift()
			x0 *= self.getIntensityScale()
			x1 += self.getIntensityShift()
			x1 *= self.getIntensityScale()
			print "Returning scaled",x0,x1,self.scalarRange
			return (x0,x1)

		return self.scalarRange
	
	def getColorTransferFunction(self):
		"""
		Returns color transfer function of dataset
		@return Color transfer function
		"""
		if not self.ctf:
			ctf = vtk.vtkColorTransferFunction()
			minval,maxval = self.getScalarRange()
			ctf.AddRGBPoint(minval,0,0,0)
			ctf.AddRGBPoint(maxval,1,1,1)
			self.ctf = ctf

		return self.ctf

