#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
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
__version__ = "$Revision: 1.42 $"
__date__ = "$Date: 2005/01/13 14:52:39 $"

import scripting
import lib.ProcessingFilter
import lib.FilterTypes
import lib.messenger
import GUI.GUIBuilder
import vtk
import vtkbxd
import types
import Logging

class AutoThresholdColocalizationFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	A filter for calculating a colocalization map and various colocalization statistics
	"""		
	name = "Auto threshold colocalization"
	category = lib.FilterTypes.FILTERING
	level = scripting.COLOR_BEGINNER
	
	def __init__(self):
		"""
		Initialization
		"""
		lib.ProcessingFilter.ProcessingFilter.__init__(self, (2,2), requireWholeDataset = 1)
		for i in range(1, 3):
			self.setInputChannel(i, i)
		self.colocAutoThreshold = vtkbxd.vtkImageAutoThresholdColocalization()
		self.done = False
		self.colocAutoThreshold.GetOutput().ReleaseDataFlagOn()
		self.colocAutoThreshold.AddObserver('ProgressEvent', lib.messenger.send)
		lib.messenger.connect(self.colocAutoThreshold, "ProgressEvent", self.updateProgress)
		self.resultVariables = {
							"Ch1ThresholdMax":	"Ch1 Automatic Threshold",
							"Ch2ThresholdMax":	"Ch2 Automatic Threshold",
							"Slope":			"Correlation slope",
							"Intercept":		"Correlation intercept"
							}
					
	def getParameterLevel(self, parameter):
		"""
		Return the level of the given parameter
		"""
		return scripting.COLOR_BEGINNER
	
	def setParameter(self, parameter, value):
		"""
		Set a value for the parameter
		"""
		oldval = self.parameters.get(parameter, "ThisIsABadValueThatNoOneWillEverUse")
		lib.ProcessingFilter.ProcessingFilter.setParameter(self, parameter, value)
		if self.initDone and self.gui and value != oldval:
			lib.messenger.send(None, "data_changed", 0)
		
	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""
		return [ ]
				
	def getLongDesc(self, parameter):
		"""
		Return a long description of the parameter
		""" 
		return ""

	def setDataUnit(self, dataUnit):
		"""
		Set the dataunit that is the input of this filter
		"""
		self.done = False
		lib.ProcessingFilter.ProcessingFilter.setDataUnit(self, dataUnit)
		
	def getType(self, parameter):
		"""
		Return the type of the parameter
		"""	   
		
		return types.IntType
		
	def getDefaultValue(self, parameter):
		"""
		Return the default value of a parameter
		"""
		return 0
		
	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute the filter with given inputs and return the output
		"""
		
		if not lib.ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None
		images = [self.getInput(x) for x in range(1,3)]
		self.eventDesc="Calculating colocalization thresholds"

		if not self.done:
			self.done = True
			images[0].SetUpdateExtent(images[0].GetWholeExtent())
			images[1].SetUpdateExtent(images[1].GetWholeExtent())
			images[0].Update()
			images[1].Update()
			maxval = int(max([x.GetScalarRange()[1] for x in images]))
			Logging.info("Maximum value = %d"%maxval, kw="processing") 
		
			self.colocAutoThreshold.AddInput(images[0])
			self.colocAutoThreshold.AddInput(images[1])
			
				
			self.colocAutoThreshold.SetUpperThresholdCh1(maxval)
			self.colocAutoThreshold.SetUpperThresholdCh2(maxval)
			self.colocAutoThreshold.Update()
			slope = self.colocAutoThreshold.GetSlope()
			intercept = self.colocAutoThreshold.GetIntercept()
			ch1th = self.colocAutoThreshold.GetCh1ThresholdMax()
			ch2th = self.colocAutoThreshold.GetCh2ThresholdMax()
			self.setResultVariable("Slope", slope)
			self.setResultVariable("Intercept", intercept)
			self.setResultVariable("Ch1ThresholdMax", int(ch1th))
			self.setResultVariable("Ch2ThresholdMax", int(ch2th))
		else:
			Logging.info("Automated threshold already calculated")
			
		Logging.info("Auto threshold ch1 = %d, ch2 = %d"%(self.getResultVariable("Ch1ThresholdMax"),self.getResultVariable("Ch2ThresholdMax")))
		return self.getInput(1)