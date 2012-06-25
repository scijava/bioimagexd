# -*- coding: iso-8859-1 -*-
"""
 Unit: Merging
 Project: BioImageXD
 Description:

 Merges two (or more) 8-bit datasets to one 24-bit using classes in the VTK
 library.

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
__version__ = "$Revision: 1.18 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"


import scripting
import lib.messenger
import Logging
from lib.Module import Module
import time
import vtkbxd
import vtk
import lib.ImageOperations

class Merging(Module):
	"""
	Merges two or more datasets to one
	"""
	def __init__(self, **kws):
		"""
		Initialization
		"""
		Module.__init__(self, **kws)
		self.doAlpha = 1
		self.extent = []
		self.thresholds = []
		self.merge = None
		self.running = False
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

		self.infos = []
		self.intensityTransferFunctions = []
		self.ctfs = []
		
		self.alphaMode = [0, 0]
		self.n = -1
		self.merge = None
		
	def addInput(self, dataunit, data):
		"""
		Adds an input for the color merging filter
		"""
		settings = dataunit.getSettings()
		if not settings.get("PreviewChannel"):
			Logging.info("Not including ", dataunit, "in merging", kw = "processing")
			return
		
		Module.addInput(self, dataunit, data)

		self.n += 1
					
		ctf = settings.get("ColorTransferFunction")
		
#		Logging.info("ctf=",ctf,kw="processing")
		
		self.ctfs.append(ctf)
		
		self.alphaTF = settings.get("AlphaTransferFunction")
		self.alphaMode = settings.get("AlphaMode")
		#print "n=",self.n,"self.settings=",self.settings
		#itf=self.settings.getCounted("IntensityTransferFunction",self.n)
		
		itf = settings.get("IntensityTransferFunction")
		
		if not itf:
			Logging.info("Didn't get iTF", kw = "processing")
		self.intensityTransferFunctions.append(itf)


	def getPreview(self, z):
		"""
		Does a preview calculation for the x-y plane at depth z
		"""
		if z != -1:
			self.doAlpha = 0
		else: # If the whole volume is requested, then we will also do alpha
			#Logging.info("Will create alpha channel, because whole volume requested",kw="processing")
			self.doAlpha = 1
		if not scripting.wantAlphaChannel:
			self.doAlpha = 0
		if self.settings.get("ShowOriginal"):
			ret = self.doOperation()      
			self.doAlpha = 1
			return ret
		if not self.preview:
			self.preview = self.doOperation()
		self.doAlpha = 1
		return self.preview

	def doOperation(self):
		"""
		Does color merging for the dataset
		"""
		t1 = time.time()
		datasets = []
		alphas = []
		
		processed = []
		imagelen = len(self.images)
		if not imagelen:
			return None
		self.shift = 0
		self.scale = 0.333
		self.scale /= imagelen
		
		luminance = 0
		self.shift = 0
		self.scale = 1
		self.merge = vtkbxd.vtkImageColorMerge()
		self.merge.AddObserver("ProgressEvent", lib.messenger.send)
		lib.messenger.connect(self.merge, 'ProgressEvent', self.updateProgress)

		if self.doAlpha:
			self.merge.BuildAlphaOn()
			if self.alphaMode[0] == 0:
				Logging.info("Alpha mode = maximum", kw = "processing")
				self.merge.MaximumModeOn()                
			elif self.alphaMode[0] == 1:
				Logging.info("Alpha mode = average, threshold = ", self.alphaMode[1], kw = "processing")
				self.merge.AverageModeOn()
				self.merge.SetAverageThreshold(self.alphaMode[1])
			elif self.alphaMode[0] == 2:
				self.merge.LuminanceModeOn()
				Logging.info("Alpha mode = luminance", kw = "processing")
			else:
				self.merge.BuildAlphaOff()
		else:
			self.merge.BuildAlphaOff()
		

		images = lib.ImageOperations.castImagesToLargestDataType(self.images)
		for i, image in enumerate(images):
			self.merge.AddInput(image)
			self.merge.AddLookupTable(self.ctfs[i])
			self.merge.AddIntensityTransferFunction(self.intensityTransferFunctions[i])

		#data = self.getLimitedOutput(self.merge)

		data = self.merge.GetOutput()

		t3 = time.time()
		Logging.info("Merging took %.4f seconds" % (t3 - t1), kw = "processing")
		#lib.messenger.send(None, "update_progress", 100, "Done.")
		
		#data.GlobalReleaseDataFlagOn()
		return data

