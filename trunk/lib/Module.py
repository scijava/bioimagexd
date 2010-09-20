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
__author__ = "Selli Project <http://sovellusprojektit.it.jyu.fi/selli/>"
__version__ = "$Revision: 1.19 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import Logging
import scripting

class Module:
	"""
	A Base class for all data processing modules
	"""
	def __init__(self, **kws):
		"""
		Initialization
		"""
		self.images = []
		self.dataunits = []
		self.doRGB = 0
		self.xSize, self.ySize, self.zSize = 0, 0, 0
		self.extent = None
		self.zoomFactor = 1
		self.settings = None
		self.scale = 1
		self.shift = 0
		self.timepoint = -1

		self.eventDesc = "Processing data"
		self.controlUnit = None
		# If we enable this, then ITK starts eating memory like crazy
		#import itkConfig
		#itkConfig.ProgressCallback = self.updateITKProgress

	def getPolyDataOutput(self):
		"""
		Return the polygonal data output of this module, or None if no polydata output exists.
		"""
		return None
		
	def getEventDesc(self):
		"""
		Get the event description. More complex modules can overwrite this for
					 more dynamic descriptions
		"""
		return self.eventDesc
		
	def updateITKProgress(self, name, itkprogress):
		"""
		update the progress from the itk side
		"""
		progress = self.shift + itkprogress * self.scale
		scripting.mainWindow.updateProgressBar(None, "ProgressEvent", progress, self.getEventDesc(), 0)
		
	def setControlDataUnit(self, dataunit):
		"""
		Set the dataunit that is controlling the execution of this module
		"""
		self.controlUnit = dataunit
		
	def getControlDataUnit(self):
		"""
		Set the dataunit that is controlling the execution of this module
		"""
		return self.controlUnit

	def updateProgress(self, obj, evt):
		"""
		Sends progress update event
		"""		   
		# The shift and scale variables allow the processing method to affect the reported progress
		# since it may combine several different VTK classes that will each report progress from 
		# 0% to 100%
		progress = self.shift + obj.GetProgress() * self.scale
		txt = obj.GetProgressText()
		if not txt:
			txt = self.getEventDesc()
		scripting.mainWindow.updateProgressBar(obj, evt, progress, txt, 0)
		
	def setTimepoint(self, timePoint):
		"""
		Sets the timepoint this module is processing
		"""
		self.timepoint = timePoint
		
	def setSettings(self, settings):
		"""
		Sets the settings object of this module
		"""
		self.settings = settings

	def reset(self):
		"""
		Resets the module to initial state
		"""
		self.images = []
		self.dataunits = []

		self.extent = None
		self.xSize, self.ySize, self.zSize = 0, 0, 0
		self.shift = 0
		self.scale = 1

	def addInput(self, dataunit, imageData):
		"""
		 Adds an input a vtkImageData object and the corresponding dataunit
		"""
		#imageData.SetScalarTypeToUnsignedChar()
		newxSize, newySize, newzSize = imageData.GetDimensions()

		if not (newxSize or newySize or newzSize):
			imageData.UpdateInformation()
			newxSize, newySize, newzSize = imageData.GetDimensions()
		if self.xSize and self.ySize and self.zSize:
			#if newxSize != self.xSize or newySize != self.ySize or newzSize != self.zSize:
			#	raise ("ERROR: Dimensions do not match: currently (%d,%d,%d), "
			#	"new dimensions (%d,%d,%d)"%(self.xSize, self.ySize, self.zSize, newxSize, newySize, newzSize))
			pass
		else:			 
			self.xSize, self.ySize, self.zSize = imageData.GetDimensions()
			#Logging.info("Dataset dimensions =(%d,%d,%d)"%(newxSize,newySize,newzSize),kw="dataunit")
		extent = imageData.GetExtent()


		#if self.extent:
		#	if self.extent != extent:
		#		Logging.error("Extents do not match","Extents do not match: %s and %s" % (self.extent, extent))
		#else:
		#	self.extent = extent
		self.images.append(imageData)
		self.dataunits.append(dataunit)

	def getPreview(self, zDepth):	#does the same as processData and doOperation (below)
		"""
		Does a preview calculation for the x-y plane at depth z
		"""
		return self.images[0]

	def processData(self, zDepth, newData, toZ = None):	#does the same as processPreview and doOperation (above and below)
		"""
		Processes the input data
		Parameters: z		 The z coordinate of the plane to be processed
					newData  The output vtkImageData object
					toZ		 Optional parameter defining the z coordinate
							 where the colocalization data is written
		"""
		return self.images[0]

	def doOperation(self):	#does the same as processPreview and processData (look above)
		"""
		Does the operation for the specified datasets.
		"""
		return self.images[0]

	def getNumberOfOutputs(self):
		"""
		Returns number of output datas
		"""
		return 1
	
