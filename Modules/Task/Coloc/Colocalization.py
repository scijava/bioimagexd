# -*- coding: iso-8859-1 -*-
"""
 Unit: Colocalization.py
 Project: BioImageXD
 Created: 16.11.2004, KP
 Description:

 Calculates the colocalization between two channels
 
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
__version__ = "$Revision: 1.24 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

STATISTICS_ONLY = 2
THRESHOLDS_ONLY = 1
import vtk
import time
#from enthought.tvtk import messenger
import messenger
import lib.Module
from lib.Module import *

class Colocalization(Module):
	"""
	Created: 03.11.2004, KP
	Description: Creates a colocalization map
	"""
	def __init__(self, **kws):
		"""
		Created: 03.11.2004, KP
		Description: Initialization
		"""
		Module.__init__(self, **kws)
		self.running = 0
		self.depth = 8
		self.reset()

	def reset(self):
		"""
		Created: 04.11.2004, KP
		Description: Resets the module to initial state. This method is
					 used mainly when doing previews, when the parameters
					 that control the colocalization are changed and the
					 preview data becomes invalid.
		"""
		Module.reset(self)
		self.colocFilter = vtk.vtkImageColocalizationFilter()
		self.colocFilter.AddObserver("ProgressEvent", self.updateProgress)

		#self.colocFilter.GetOutput().ReleaseDataFlagOn()
		self.colocFilter.AddObserver("ProgressEvent", self.updateProgress)
		self.colocAutoThreshold = vtk.vtkImageAutoThresholdColocalization()
		self.colocAutoThreshold.GetOutput().ReleaseDataFlagOn()
		self.colocAutoThreshold.AddObserver("ProgressEvent", self.updateProgress)
		self.thresholds = []
		self.settingsLst = []
		self.preview = None
		self.n = -1

	def addInput(self, dataunit, data):
		"""
		Created: 03.11.2004, KP
		Description: Adds an input for the colocalization filter
		"""

		Module.addInput(self, dataunit, data)
		settings = dataunit.getSettings()
		self.settingsLst.append(settings)
		th0 = settings.get("ColocalizationLowerThreshold")
		th1 = settings.get("ColocalizationUpperThreshold")
		self.thresholds.append((th0, th1))
		self.depth = self.settings.get("ColocalizationDepth")


	def getPreview(self, z):
		"""
		Created: 03.11.2004, KP
		Description: Does a preview calculation for the x-y plane at depth z
		"""
		if not self.preview:
			self.preview = self.doOperation()
		return self.preview

	def doOperation(self):
		"""
		Created: 10.11.2004, KP
		Description: Calculates the colocalization map and optionally the thresholds used
		"""

		Logging.info("Doing ", self.depth, "-bit colocalization", kw = "processing")
#        self.colocFilter=vtk.vtkImageColocalizationFilter()
#        self.colocFilter.AddObserver("ProgressEvent",self.updateProgress)
		self.colocFilter.SetOutputDepth(self.depth)

		maxval = 0
		for i in self.images:
			maxval = max(i.GetScalarRange()[1], maxval)
		maxval = int(maxval)

		settings = self.settingsLst[0]
		calcVal = settings.get("CalculateThresholds")
		if calcVal:
			self.eventDesc = "Calculating thresholds"
			Logging.info("Calculating thresholds, calcval=%d" % calcVal, kw = "processing")

			self.colocAutoThreshold.AddInput(self.images[0])
			self.colocAutoThreshold.AddInput(self.images[1])
			if calcVal == STATISTICS_ONLY:
				Logging.info("CALCULATING ONLY STATISTICS", kw = "processing")
				# When we set the lower thresholds, then the given thresholds will be used
				Logging.info("Setting lower thresholds ", int(self.thresholds[0][0]), int(self.thresholds[1][0]), "for statistics")
				self.colocAutoThreshold.SetLowerThresholdCh1(int(self.thresholds[0][0]))
				self.colocAutoThreshold.SetLowerThresholdCh2(int(self.thresholds[1][0]))

				print "Setting upper thresholds", self.thresholds[0][1], self.thresholds[1][1]            
				self.colocAutoThreshold.SetUpperThresholdCh1(int(self.thresholds[0][1]))
				self.colocAutoThreshold.SetUpperThresholdCh2(int(self.thresholds[1][1]))               
			elif calcVal == THRESHOLDS_ONLY:
				Logging.info("CALCULATING ONLY THRESHOLD", kw = "processing")
				Logging.info("Calculated thresholds, using %d as max" % maxval, kw = "processing")
				self.colocAutoThreshold.SetUpperThresholdCh1(maxval)
				self.colocAutoThreshold.SetUpperThresholdCh2(maxval)

				
			self.colocAutoThreshold.Update()
			
			if calcVal == THRESHOLDS_ONLY:
				self.settings.set("Ch1ThresholdMax", self.colocAutoThreshold.GetCh1ThresholdMax())
				self.settings.set("Ch2ThresholdMax", self.colocAutoThreshold.GetCh2ThresholdMax())
				self.settings.set("Slope", self.colocAutoThreshold.GetSlope())
				self.settings.set("Intercept", self.colocAutoThreshold.GetIntercept())            
			Logging.info("Done!", kw = "processing")
			
			t1 = settings.get("Ch1ThresholdMax")
			t2 = settings.get("Ch2ThresholdMax")
			if t1 == None:t1 = 0
			if t2 == None:t2 = 0
			Logging.info("Got thresholds", t1, t2, kw = "processing")
			l = [(t1, maxval), (t2, maxval)]
			self.settings.set("CalculateThresholds", 0)

			
			# if CalculateThresholds == 1, then set the calculated thresholds
			# if it's 2 then only the statistics need to be calculated
			
			if calcVal == THRESHOLDS_ONLY:
				for i in range(0, 2):
					self.settingsLst[i].set("ColocalizationLowerThreshold", l[i][0])
					self.settingsLst[i].set("ColocalizationUpperThreshold", l[i][1])
				Logging.info("Threshold for Ch1 =", t1, " and Ch2 =", t2, kw = "processing")
				self.thresholds = [(t1, maxval), (t2, maxval)]
			else:
				for i in ["Ch1ThresholdMax", "Ch2ThresholdMax", "PearsonImageAbove",
						  "PearsonImageBelow", "PearsonWholeImage", "M1", "M2",
						  "K1", "K2", "DiffStainIntCh1", "DiffStainIntCh2",
						  "DiffStainVoxelsCh1", "DiffStainVoxelsCh2",
						  "ThresholdM1", "ThresholdM2",
						  "ColocAmount", "ColocPercent", "PercentageVolumeCh1",
						  "PercentageTotalCh1", "PercentageTotalCh2",
						  "PercentageVolumeCh2", "PercentageMaterialCh1", "PercentageMaterialCh2",
						  "SumOverThresholdCh1", "SumOverThresholdCh2", "SumCh1", "SumCh2",
						  "NonZeroCh1", "NonZeroCh2", "OverThresholdCh2", "OverThresholdCh1"]:
					method = "self.colocAutoThreshold.Get%s()" % i
	
					val = eval(method)
	#                if "DiffStain" in i:
	#                    print i,val
					settings.set(i, val)            
			#settings.set("ColocalizationScatterplot",self.colocFilter.GetOutput(1))
		self.eventDesc = "Calculating colocalization..."
		outScalar = self.settings.get("OutputScalar")
		Logging.info("Using ", outScalar, " as output scalar")#,kw="processing")
		self.colocFilter.SetOutputScalarValue(outScalar)

		for i in range(len(self.images)):
			print self.thresholds[i]
			Logging.info("Using %d as lower and %d as upper threshold" % self.thresholds[i], kw = "processing")

#            print "Adding input %d"%i
			self.colocFilter.AddInput(self.images[i])

			self.colocFilter.SetColocalizationLowerThreshold(i, int(self.thresholds[i][0]))
			self.colocFilter.SetColocalizationUpperThreshold(i, int(self.thresholds[i][1]))

#        data = self.getLimitedOutput(self.colocFilter)        
#        self.colocFilter.Update()
		data = self.colocFilter.GetOutput()
		messenger.send(None, "update_progress", 100, "Done.")
		
		return data
