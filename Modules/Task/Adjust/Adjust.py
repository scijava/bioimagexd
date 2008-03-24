# -*- coding: iso-8859-1 -*-
"""
 Unit: Adjust
 Project: BioImageXD
 Created: 25.11.2004, KP
 Description:
 
 A Module for adjusting a dataset by changing for example it's brightness, contrast
 or gamma

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
__version__ = "$Revision: 1.13 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import Logging
import lib.messenger
from lib.Module import Module
import time
import vtkbxd

class Adjust(Module):
	"""
	Process a dataunit using an intensity transfer funtion
	"""

	def __init__(self, **kws):
		"""
		Initialization
		"""
		Module.__init__(self, **kws)

		# TODO: remove attributes that already exist in base class!
		self.images = []
		self.x, self.y, self.z = 0, 0, 0
		self.extent = None
		self.running = 0
		self.depth = 8

		self.reset()

	def reset(self):
		"""
		Resets the module to initial state. This method is
					 used mainly when doing previews, when the parameters
					 that control the colocalization are changed and the
					 preview data becomes invalid.
		"""
		Module.reset(self)
		self.preview = None
		self.intensityTransferFunctions = []
		self.extent = None

	def addInput(self, dataunit, data):
		"""
		Adds an input for the single dataunit processing filter
		"""
		Module.addInput(self, dataunit, data)
		settings = dataunit.getSettings()
		tf = settings.getCounted("IntensityTransferFunctions", self.timepoint)
		if not tf:            
			raise ("No Intensity Transfer Function given for Single DataUnit "
			"to be processed")
		self.intensityTransferFunctions.append(tf)


	def getPreview(self, z):
		"""
		Does a preview calculation for the x-y plane at depth z
		"""
		if self.settings.get("ShowOriginal"):
			return self.images[0]        
		if not self.preview:
			dims = self.images[0].GetDimensions()
			if z >= 0:
				self.extent = (0, dims[0] - 1, 0, dims[1] - 1, z, z)
			else:
				self.extent = None
			self.preview = self.doOperation(preview = 1)
			self.extent = None
		return self.preview


	def doOperation(self, preview = 0):
		"""
		Processes the dataset in specified ways
		"""
		t1 = time.time()

		# Map scalars with intensity transfer list
		n = 0
		if len(self.images) > 1:
			settings = self.dataunits[0].getSettings()
			n = settings.get("PreviewedDataset")
			Logging.info("More than one source dataset for data processing, using %dth" % n, kw = "processing")
			
		mapdata = self.images[n]
		mapIntensities = vtkbxd.vtkImageMapToIntensities()
		#mapIntensities.GetOutput().ReleaseDataFlagOn()
		mapIntensities.AddObserver("ProgressEvent", lib.messenger.send)
		lib.messenger.connect(mapIntensities, "ProgressEvent", self.updateProgress)
		mapIntensities.SetIntensityTransferFunction(self.intensityTransferFunctions[n])
		mapIntensities.SetInput(mapdata)
		
		#data = self.getLimitedOutput(mapIntensities)        
		data = mapIntensities.GetOutput()
			
		t2 = time.time()
		#Logging.info("Processing took %.4f seconds"%(t2-t1))
		#data.ReleaseDataFlagOff()
		return data
