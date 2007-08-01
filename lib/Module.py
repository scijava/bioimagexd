# -*- coding: iso-8859-1 -*-
"""
 Unit: Module.py
 Project: BioImageXD
 Created: 03.11.2004, KP
 Description:

 A Base Class for all data processing modules.
						   
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
__version__ = "$Revision: 1.22 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import vtk
import ImageOperations
import Logging
#from enthought.tvtk import messenger
import messenger
import scripting

class Module:
	"""
	Created: 03.11.2004, KP
	Description: A Base class for all data processing modules
	"""
	def __init__(self, **kws):
		"""
		Created: 03.11.2004, KP
		Description: Initialization
		"""
		self.images = []
		self.shift = 0
		self.scale = 1
		self.dataunits = []
		self.x, self.y, self.z = 0, 0, 0
		self.extent = None
		self.settings = None
		self.timepoint = -1

		self.eventDesc = "Processing data"
		self.controlUnit = None
	 
	def setControlDataUnit(self, dataunit):
		"""
		Created: 10.07.2006, KP
		Description: Set the dataunit that is controlling the execution of this module
		"""
		self.controlUnit = dataunit
		
	def getControlDataUnit(self):
		"""
		Created: 10.07.2006, KP
		Description: Set the dataunit that is controlling the execution of this module
		"""
		return self.controlUnit
	
	def updateProgress(self, obj, evt):
		"""
		Created: 13.07.2004, KP
		Description: This listens to progress update events from VTK side, and sends them forward using the messenger
		"""        
		progress = obj.GetProgress()
		# The shift and scale variables allow the processing method to affect the reported progress
		# since it may combine several different VTK classes that will each report progress from 
		# 0% to 100%
		progress = self.shift + progress * self.scale
		txt = obj.GetProgressText()
		if not txt:txt = self.eventDesc
		messenger.send(None, "update_progress", progress, txt, 0)        
		
	def setTimepoint(self, tp):
		"""
		Created: 21.06.2005, KP
		Description: Sets the timepoint this module is processing
		"""
		self.timepoint = tp
		
	def setSettings(self, settings):
		"""
		Created: 27.03.2005, KP
		Description: Sets the settings object of this module
		"""
		self.settings = settings

	def reset(self):
		"""
		Created: 04.11.2004, KP
		Description: Resets the module to initial state
		"""
		self.images = []
		self.extent = None
		self.x, self.y, self.z = 0, 0, 0
		self.shift = 0
		self.scale = 1

	def addInput(self, dataunit, imageData):
		"""
		 Created: 03.11.2004, KP
		 Description: Adds an input a vtkImageData object and the corresponding dataunit
		"""
		#imageData.SetScalarTypeToUnsignedChar()
		x, y, z = imageData.GetDimensions()
		if not (x or y or z):
			imageData.UpdateInformation()
			x, y, z = imageData.GetDimensions()
		# If the dimensions of the input images do not match, then raise an exception
		if self.x and self.y and self.z:
			if x != self.x or y != self.y or z != self.z:
				Logging.error("Dimensions do not match", "ERROR: Dimensions do not match: currently (%d,%d,%d), "
				"new dimensions (%d,%d,%d)" % (self.x, self.y, self.z, x, y, z))
		else:            
			self.x, self.y, self.z = imageData.GetDimensions()
			#Logging.info("Dataset dimensions =(%d,%d,%d)"%(x,y,z),kw="dataunit")
		extent = imageData.GetExtent()
		if self.extent:
			if self.extent != extent:
				Logging.error("Extents do not match", "Extents do not match: %s and %s" % (self.extent, extent))
				#raise Loggin"ERROR: Extents do not match"
		else:
			self.extent = extent
		self.images.append(imageData)
		self.dataunits.append(dataunit)

	def getPreview(self, z):
		"""
		Created: 03.11.2004, KP
		Description: Does a preview calculation for the x-y plane at depth z
		"""
		return self.images[0]

	def doOperation(self):
		"""
		Created: 01.12.2004, KP
		Description: Does the operation for the specified datasets.
		"""
		return self.images[0]


