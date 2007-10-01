# -*- coding: iso-8859-1 -*-
"""
 Unit: BioradDataSource
 Project: BioImageXD
 Created: 29.03.2006, KP
 Description: A datasource for reading Biorad .PIC files

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

try:
	import itk
except ImportError:
	pass
import os.path
from lib.DataSource.DataSource import DataSource
from lib.DataUnit.DataUnit import DataUnit
import re
import vtk

def getExtensions():
	return ["pic"]

def getFileType():
	return "BioRad PIC datasets (*.pic)"

def getClass():
	return BioradDataSource	   

class BioradDataSource(DataSource):
	"""
	Created: 12.04.2005, KP
	Description: BioRad .PIC files datasource
	"""
	def __init__(self, filename = ""):
		"""
		Created: 12.04.2005, KP
		Description: Constructor
		"""	   
		DataSource.__init__(self)
		self.setPath(filename)
		dataSetName = os.path.basename(filename)
		dataSetName = dataSetName.split(".")
		dataSetName = ".".join(dataSetName[:-1])
		self.dataSetName = dataSetName
		self.io = itk.BioRadImageIO.New()
		self.reader = itk.ImageFileReader[itk.Image.UC3].New()
		self.reader.SetImageIO(self.io.GetPointer())
		self.ctf = None
		self.filename = filename
		self.filepattern = None
		self.dimensions = None
		self.voxelsize = (1, 1, 1)
		self.spacing = None
		self.itkToVtk = None
		self.color = None
		self.shift = None
		self.tps = -1
		if filename:
			self.path = os.path.dirname(filename)
			self.getDataSetCount()
		
	def getDataSetCount(self):
		"""
		Created: 12.04.2005, KP
		Description: Returns the number of individual DataSets (=time points)
		managed by this DataSource
		"""
		# This seems to rely on the fact that tps is set to -1 in the constructor
		if self.tps < 0:
			#f = self.filename[:]
			#r = re.compile("(\d+)....$")
			
			#m = r.search(f)
			#d = m.groups(0)
			#print d
			#f = f.replace(d[0], "%d")
			#n = 1
			#self.filepattern = f
			#for i in range(1, 99999):
			#	if os.path.exists(f%i):
			#		n = i
			#print "Dataset has", n, "timepoints"
			#self.tps = n
			filename = self.filename
			numberBeforeExtensionRe = re.compile("(\d+)....$")
			numberBeforeExtensionMatch = numberBeforeExtensionRe.search(filename)
			numberBeforeExtension = numberBeforeExtensionMatch.group(1)
			self.filepattern = filename.replace(numberBeforeExtension, "%d")
			timePoints = 1
# Try various filenames and see if they exist to determine amount of timepoint
# this DataSource manages.
# The filenames don't have zeroes in them? bxd00005.pic for example.
# Shouldn't we break if a timepoint file doesn't exist.
# TODO: Are we sure that 99999 is high enough?
			for i in range(1, 99999):
				if os.path.exists(self.filepattern % i):
					timePoints = i
			print "Dataset has", timePoints, "timepoints"
			self.tps = timePoints
		return self.tps

	def getFileName(self):
		"""
		Created: 21.07.2005
		Description: Return the file name
		"""
		return self.filename

	def getDataSet(self, i, raw = 0):
		"""
		Created: 12.04.2005, KP
		Description: Returns the DataSet at the specified index
		Parameters:	  i		  The index
		"""
		data = self.getTimepoint(i)
		data = self.getResampledData(data, i)
		if not self.shift:
			self.shift = vtk.vtkImageShiftScale()
			self.shift.SetOutputScalarTypeToUnsignedChar()
		self.shift.SetInput(data)

		x0, x1 = data.GetScalarRange()
		print "Scalar range=", x0, x1
		if not x1:
			x1 = 1
		scale = 255.0/x1

		if scale:
			self.shift.SetScale(scale)
		self.shift.Update()
		data = self.shift.GetOutput()
		data.ReleaseDataFlagOff()
		return data

	def getTimepoint(self, requestedTimePoint, onlyDims = 0):
		"""
		Created: 16.02.2006, KP
		Description: Return the nth timepoint
		"""		   
		print "Switching to dataset ", self.filepattern % (requestedTimePoint + 1)
		self.reader.SetFileName(self.filepattern % (requestedTimePoint + 1))
		self.reader.Update()
		
		if not self.itkToVtk:
			self.itkToVtk = itk.ImageToVTKImageFilter.IUC3.New()
		data = self.reader.GetOutput()
		
		if not self.voxelsize:
			size = data.GetSpacing()
			x, y, z = [size.GetElement(i) for i in range(0, 3)]
			self.voxelsize = (x, y, z)
			print "Read voxel size", self.voxelsize
		if not self.dimensions:
			reg = data.GetLargestPossibleRegion()
			size = reg.GetSize()
			x, y, z = [size.GetElement(i) for i in range(0, 3)]
			self.dimensions = (x, y, z)
			print "Read dimensions", self.dimensions
		if onlyDims:
			return
		self.itkToVtk.SetInput(data)
		self.itkToVtk.Update()
		return self.itkToVtk.GetOutput()
		
	def internalGetDimensions(self):
		"""
		Created: 12.04.2005, KP
		Description: Returns the (x, y, z) dimensions of the datasets this 
					 dataunit contains
		""" 
		self.getVoxelSize()
		return self.dimensions

		
	def getSpacing(self):
		"""
		Created: 12.04.2005, KP
		Description: Returns the spacing of the datasets this 
					 dataunit contains
		"""
		if not self.spacing:
			a, b, c = self.getVoxelSize()
			self.spacing = [1, b/a, c/a]
		return self.spacing
		
	def getVoxelSize(self):
		"""
		Created: 12.04.2005, KP
		Description: Returns the voxel size of the datasets this 
					 dataunit contains
		"""
		if not self.voxelsize:
			self.getTimepoint(0, onlyDims = 1)
		return self.voxelsize

	@staticmethod
	def loadFromFile(filename):
		"""
		Created: 12.04.2005, KP
		Description: Loads the specified .oif-file and imports data from it.
		Parameters:	  filename	The .oif-file to be loaded
		"""
		dataunit = DataUnit()
		datasource = BioradDataSource(filename)
		dataunit.setDataSource(datasource)
		return [dataunit]
		

	def getDataSetName(self):
		"""
		Created: 18.11.2005, KP
		Description: Returns the name of the dataset series which this datasource
					 operates on
		"""
		return self.dataSetName

		
	def getColorTransferFunction(self):
		"""
		Created: 26.04.2005, KP
		Description: Returns the ctf of the dataset series which this datasource
					 operates on
		"""
		if not self.ctf:
			self.ctf = vtk.vtkColorTransferFunction()
			self.ctf.AddRGBPoint(0, 0, 0, 0)
			self.ctf.AddRGBPoint(255, 0, 1, 0)
		return self.ctf 
