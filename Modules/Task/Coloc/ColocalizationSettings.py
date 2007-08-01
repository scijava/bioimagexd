# -*- coding: iso-8859-1 -*-

"""
 Unit: ColocalizationSettings
 Project: BioImageXD
 Created: 26.03.2005, KP
 Description:

 This is a class that holds all settings of a colocalization dataunit. A dataunit's 
 setting object is the only thing differentiating it from another
 dataunit.
 
 This code was re-written for clarity. The code produced by the
 Selli-project was used as a starting point for producing this code.
 http://sovellusprojektit.it.jyu.fi/selli/ 

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
__version__ = "$Revision: 1.21 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import vtk
from lib.DataUnit.DataUnitSetting import DataUnitSettings
		
class ColocalizationSettings(DataUnitSettings):
	"""
	Created: 26.03.2005, KP
	Description: Registers keys related to colocalization in a dataunitsetting
	"""
	def __init__(self, n = -1):
		"""
		Method: __init__
		Created: 26.03.2005, KP
		Description: Constructor
		"""
		DataUnitSettings.__init__(self, n)
		
		self.set("Type", "Colocalization")
		self.registerCounted("ColocalizationLowerThreshold", 1)
		self.registerCounted("ColocalizationUpperThreshold", 1)
		self.register("ColocalizationDepth", 1)
		self.register("CalculateThresholds")
		
		for i in ["PValue", "RObserved", "RRandMean", "RRandSD",
				  "NumIterations", "ColocCount", "Method", "PSF",
				  "Ch1ThresholdMax", "Ch2ThresholdMax", "PearsonImageAbove",
				  "PearsonImageBelow", "PearsonWholeImage", "M1", "M2",
				  "ThresholdM1", "ThresholdM2", "Slope", "Intercept",
				  "K1", "K2", "DiffStainIntCh1", "DiffStainIntCh2",
					  "DiffStainVoxelsCh1", "DiffStainVoxelsCh2",
				  "ColocAmount", "ColocPercent", "PercentageVolumeCh1",
				  "PercentageTotalCh1", "PercentageTotalCh2",
				  "PercentageVolumeCh2", "PercentageMaterialCh1", "PercentageMaterialCh2",
				  "SumOverThresholdCh1", "SumOverThresholdCh2", "SumCh1", "SumCh2",
				  "NonZeroCh1", "NonZeroCh2", "OverThresholdCh1", "OverThresholdCh2"]:
			self.register(i, 1)
		self.register("OutputScalar", 1)

		#self.register("ColocalizationColorTransferFunction",1)
		ctf = vtk.vtkColorTransferFunction()
		ctf.AddRGBPoint(0, 0, 0, 0)
		ctf.AddRGBPoint(255, 1.0, 1.0, 1.0)
		self.set("ColorTransferFunction", ctf)
		# This is used purely for remembering the ctf the user has set
		self.register("ColocalizationColorTransferFunction", 1)

	def initialize(self, dataunit, channels, timepoints):
		"""
		Created: 27.03.2005
		Description: Set initial values for settings based on 
					 number of channels and timepoints
		"""
		DataUnitSettings.initialize(self, dataunit, channels, timepoints)
		print "Initializing colocaliztion for %d channels" % channels
		self.set("ColocalizationDepth", 8)
		if hasattr(dataunit, "getScalarRange"):
			minval, maxval = dataunit.getScalarRange()
		else:
			minval, maxval = dataunit.getSourceDataUnits()[0].getScalarRange()
		print "Initializing channels, maxval=", maxval
		for i in range(channels):
			self.setCounted("ColocalizationLowerThreshold", i, maxval / 2, 0)
			self.setCounted("ColocalizationUpperThreshold", i, maxval, 0)    
			ctf = vtk.vtkColorTransferFunction()
			ctf.AddRGBPoint(0, 0, 0, 0)
			ctf.AddRGBPoint(maxval, 1.0, 1.0, 1.0)
			self.set("ColorTransferFunction", ctf)            
		self.set("OutputScalar", maxval)
