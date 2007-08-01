# -*- coding: iso-8859-1 -*-
"""
 Unit: RGBComponentDataSource.py
 Project: BioImageXD
 Created: 06.2.2006, KP
 Description: A datasource for extracting an rgb component from an input datasource
 
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


#import ConfigParser
#import os.path
#import Configuration
#import Logging
#import lib.DataUnit
#import scripting
#import messenger

from lib.DataSource.DataSource import DataSource
import vtk

class RGBComponentDataSource(DataSource):
	"""
	Created: 06.02.2007, KP
	Description: A datasource that extracts a single RGB component from a source datasource
	"""
	def __init__(self, source, component):
		"""
		Created: 06.02.2007, KP
		Description: Initialization
		"""
		DataSource.__init__(self)
		self.source = source
		self.component = component
		self.extract = vtk.vtkImageExtractComponents()
		self.extract.SetComponents(self.component)
		self.setPath = source.setPath
		self.getPath = source.getPath
		self.setMask = source.setMask
		self.getSpacing = source.getSpacing
		self.getVoxelSize = source.getVoxelSize
		self.setResampleDimensions = source.setResampleDimensions
		self.getOriginalScalarRange = source.getOriginalScalarRange
		self.getOriginalDimensions = source.getOriginalDimensions
		self.getResampleFactors = source.getResampleFactors
		self.getResampledVoxelSize = source.getResampledVoxelSize
		self.getResampleDimensions = source.getResampleDimensions
		self.setIntensityScale = source.setIntensityScale
		self.getIntensityScaledData = source.getIntensityScaledData
		self.getResampledData = source.getResampledData
		self.getEmissionWavelength = source.getEmissionWavelength
		self.getExcitationWavelength = source.getExcitationWavelength
		self.getNumericalAperture = source.getNumericalAperture
		self.getDataSetCount = source.getDataSetCount
		self.getFileName = source.getFileName
		self.getDimensions = source.getDimensions
		self.getScalarRange = source.getScalarRange
		self.ctf = None
		
		
	def getColorTransferFunction(self):
		"""
		Created: 06.02.2007, KP
		Description: return the color transfer function for this dataset
		"""
		if not self.ctf:
			col = [0, 0, 0]
			col[self.component] = 1.0
			col = tuple(col)
			self.ctf = vtk.vtkColorTransferFunction()
			self.ctf.AddRGBPoint(0, 0, 0, 0)
			self.ctf.AddRGBPoint(255, *col)
		return self.ctf

	def getName(self): 
		return self.source.getName() + "(" + "RGB"[self.component] + ")"

	def getCacheKey(self, datafilename, chName, purpose):
		"""
		Created: 07.11.2006, KP
		Description: Return a unique name based on a filename and channel name that can be used as 
					 a filename for the MIP
		"""
		
		filename = datafilename.replace("\\", "_")
		filename = filename.replace("/", "_")
		filename = filename.replace(":", "_")
		
		rgbcomponent = "RGB"[self.component]
		return filename + "_" + chName + "_" + rgbcomponent + "_" + "_" + purpose
		
	def getDataSet(self, i, raw = 0):
		"""
		Created: 06.02.2007, KP
		Description: Returns the DataSet at the specified index
		Parameters:   i		  The index
		"""		   
		data = self.source.getDataSet(i, raw)
		print "\n\nExtracting component", self.component

		self.extract.SetInput(data)
		return self.extract.GetOutput()
		
		
	def getBitDepth(self):
		"""
		Created: 06.02.2007, KP
		Description: Return the bit depth of data
		"""
		if not self.bitdepth:
			
			data = self.getDataSet(0, raw = 1)
			
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
		return self.bitdepth
