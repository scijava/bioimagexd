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
import wx

class ColocalizationFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	A filter for calculating a colocalization map and various colocalization statistics
	"""		
	name = "Colocalization"
	category = lib.FilterTypes.COLOCALIZATION
	level = scripting.COLOR_BEGINNER
	
	def __init__(self):
		"""
		Initialization
		"""
		self.defaultLower = 128
		self.defaultUpper = 255
		self.colocRange = 255
		self.numericalAperture = 1.4
		self.listctrl = None
		self.emissionWavelength = 520
		self.oldThresholds = None
		lib.ProcessingFilter.ProcessingFilter.__init__(self, (2,2), requireWholeDataset = 1)
		for i in range(1, 3):
			self.setInputChannel(i, i)


		self.colocFilter = vtkbxd.vtkImageColocalizationFilter()
		self.colocFilter.AddObserver('ProgressEvent', lib.messenger.send)
		lib.messenger.connect(self.colocFilter, "ProgressEvent", self.updateProgress)

		self.colocAutoThreshold = vtkbxd.vtkImageAutoThresholdColocalization()
		self.colocAutoThreshold.SetCalculateThreshold(0)
		self.colocAutoThreshold.GetOutput().ReleaseDataFlagOn()
		self.colocAutoThreshold.AddObserver('ProgressEvent', lib.messenger.send)
		lib.messenger.connect(self.colocAutoThreshold, "ProgressEvent", self.updateProgress)
		self.descs = {"LowerThresholdCh1": "Lower Threshold (Ch1)", "UpperThresholdCh1": "Upper threshold (Ch1)",
		"LowerThresholdCh2": "Lower Threshold (Ch2)", "UpperThresholdCh2": "Upper threshold (Ch2)",
		"PValue":"Calculate P-value","None":"None", "Costes":"Costes", "Fay":"Fay",
		"Steensel":"van Steensel","Iterations":"Iterations","PSF":"PSF radius (px)","Lambda":u"Ch2 \u03BB (nm)",
		"NA":"Numerical aperture", "Palette":"","OneBit":"Use single value for colocalization","ColocValue":"Coloc. value"
		}
		self.resultVariables = {
							"Ch1ThresholdMax":		"Ch1 Upper Threshold",
							"Ch2ThresholdMax":		"Ch2 Upper Threshold",
							"PearsonImageAbove":	"Correlation (voxels > threshold)",
							"PearsonImageBelow":	"Correlation (voxels < threshold)",
							"PearsonWholeImage":	"Correlation",
							"M1":					"M1",
							"M2":					"M2",
							"K1":					"K1",
							"K2":					"K2",
							"DiffStainIntCh1":		"Diff.stain ch1/h2 (intensity)",
							"DiffStainIntCh2":		"Diff.stain ch2/ch1 (intensity)",
							"DiffStainVoxelsCh1":	"Diff.stain of ch1/ch2 (# of voxels)",
							"DiffStainVoxelsCh2":	"Diff.stain of ch2/ch1 (# of voxels)",
							"ThresholdM1":			"M1 (colocalized voxels)",
							"ThresholdM2":			"M2 (colocalized voxels)",
							"ColocAmount":			"# of coloc. voxels",
							"ColocPercent":			"% of colocalization",
							"PercentageVolumeCh1":	"% of ch1 coloc. (voxels)",
							"PercentageTotalCh1":	"% of ch1 coloc. (tot.intensity)",
							"PercentageTotalCh2":	"% of ch2 coloc. (tot.intensity)",
							"PercentageVolumeCh2":	"% of ch2 coloc. (voxels)",
							"PercentageMaterialCh1":"% of ch1 coloc. (intensity)",
							"PercentageMaterialCh2":"% of ch2 coloc. (intensity)",
							"SumOverThresholdCh1":	"Sum of ch1 (over threshold)",
							"SumOverThresholdCh2":	"Sum of ch2 (over threshold)",
							"SumCh1":				"Sum of ch1 (total)",
							"SumCh2":				"Sum of ch2 (total)",
							"NonZeroCh1":			"# of non-zero voxels (Ch1)",
							"NonZeroCh2":			"# of non-zero voxels (Ch2)",
							"OverThresholdCh2":		"# of voxels > threshold (Ch2)",
							"OverThresholdCh1":		"# of voxels > threshold (Ch1)",
							"Slope":				"Slope",
							"Intercept":			"Intercept",
							"PValue":				"P-Value",
							"RObserved":			"R(obs)",
							"RRandMean":			"R(rand) mean",
							"RRandSD":				"R(rand) sd",
							"NumIterations":		"Iterations",
							"Method":				"Method",
							"ColocCount":			"Amount of coloc",
							"LowerThresholdCh1":"",
							"UpperThresholdCh1":"",
							"LowerThresholdCh2":"",
							"UpperThresholdCh2":""
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
		oldval = self.recordedParameters.get(parameter, None)
		lib.ProcessingFilter.ProcessingFilter.setParameter(self, parameter, value)
		if parameter in ["LowerThresholdCh1","LowerThresholdCh2","UpperThresholdCh1","UpperThresholdCh2"] and self.initDone and self.gui and value != oldval:
			lib.messenger.send(None, "data_changed", 0)
		
	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""
		return [  ["Thresholds", (("LowerThresholdCh1", "UpperThresholdCh1","LowerThresholdCh2", "UpperThresholdCh2"),)],
		 		 ["Calculate P-value", ( ("None","Costes","Fay","Steensel"), ("cols", 2)) ],
		 		 ["Costes parameters", ("Iterations","PSF","NA","Lambda")],
		 		 ["Colocalization output",("OneBit","ColocValue")]
			]
				
	def getLongDesc(self, parameter):
		"""
		Return a long description of the parameter
		""" 
		return ""
		
	def getType(self, parameter):
		"""
		Return the type of the parameter
		"""	   
		if parameter in ["LowerThresholdCh1", "UpperThresholdCh1","LowerThresholdCh2","UpperThresholdCh2"]:
			return GUI.GUIBuilder.COLOC_THRESHOLD
		elif parameter in ["PValue","OneBit"]:
			return types.BooleanType
		elif parameter in ["None","Costes","Fay","Steensel"]:
			return GUI.GUIBuilder.RADIO_CHOICE
		elif parameter == "Iterations": 
			return GUI.GUIBuilder.SPINCTRL
		if parameter in ["NA", "PSF"]:
			return types.FloatType
		
		return types.IntType
	
	def getRange(self, parameter):
		"""
		@return the range of the given parameter
		"""
		if parameter == "Iterations":
			return 0,999
		elif parameter in ["LowerThresholdCh1","LowerThresholdCh2","UpperThresholdCh1","UpperThresholdCh2"]:
			return 0, self.colocRange
		
	def getDefaultValue(self, parameter):
		"""
		Return the default value of a parameter
		"""
		if parameter in ["None","Costes","Fay","Steensel"]: return 0
		if parameter == "Iterations": return 100
		if parameter == "NA":return self.numericalAperture
		if parameter == "Lambda": return self.emissionWavelength
		if parameter in ["LowerThresholdCh1","LowerThresholdCh2"]:
			return self.defaultLower
		if parameter in ["UpperThresholdCh1","UpperThresholdCh2"]:
			return self.defaultUpper
		return 0
		
	def setDataUnit(self,dataUnit):
		"""
		set the dataunit used as input for this filter
		"""
		if dataUnit:
			sourceDataUnits = dataUnit.getSourceDataUnits()
			if sourceDataUnits:
				self.defaultUpper = sourceDataUnits[0].getScalarRange()[1]
				self.defaultLower = self.defaultUpper / 2
				na = sourceDataUnits[1].getNumericalAperture()
				if na:
					self.numericalAperture = na
				emissionWavelength = sourceDataUnits[1].getEmissionWavelength()
				if emissionWavelength:
					self.emissionWavelength = emissionWavelength
		lib.ProcessingFilter.ProcessingFilter.setDataUnit(self, dataUnit)
		

			
	def setInputChannel(self, inputNum,n):
		lib.ProcessingFilter.ProcessingFilter.setInputChannel(self, inputNum, n)
		
		if self.dataUnit:
			dataUnit = self.getInputDataUnit(inputNum)
			if dataUnit:
				lib.messenger.send(self, "set_UpperThreshold_dataunit", dataUnit)
				
				
	def getGUI(self, parent, taskPanel):
		"""
		Return the GUI for this filter
		"""
		gui = lib.ProcessingFilter.ProcessingFilter.getGUI(self, parent, taskPanel)
		
		if not self.listctrl:
			self.listctrl = GUI.ColocListView.ColocListView(self.gui, -1, size = (350, 300))
			
			sizer = wx.BoxSizer(wx.VERTICAL)
			sizer.Add(self.listctrl, 1)
			gui.sizer.Add(sizer, (1, 0), flag = wx.EXPAND | wx.ALL)
		return gui

	def calculatePValue(self, images):
		"""
		Calculate the P-value
		"""
		coloctest = vtkbxd.vtkImageColocalizationTest()
		self.eventDesc = "Calculating P-Value"
		method = 2
		if self.parameters["Costes"]: method = 1
		if self.parameters["Fay"]: method = 0
		coloctest.SetMethod(method)
		Logging.info("Calculating P-value, method = %d"%method)

		
		if self.parameters["PSF"]:
			Logging.info("Using manual PSF size %d"%int(self.parameters["PSF"]))
			coloctest.SetManualPSFSize(int(self.parameters["PSF"]))

		coloctest.SetNumIterations(self.parameters["Iterations"])
		images[0].SetUpdateExtent(images[0].GetWholeExtent())
		images[1].SetUpdateExtent(images[1].GetWholeExtent())
		images[0].Update()
		images[1].Update()
		
		for data in images:
			coloctest.AddInput(data)
		coloctest.AddObserver('ProgressEvent', lib.messenger.send)
		lib.messenger.connect(coloctest, "ProgressEvent", self.updateProgress)
		
		coloctest.Update()
		for i in ["PValue", "RObserved", "RRandMean", "RRandSD",
				  "NumIterations", "ColocCount", "Method"]:
			val = eval("coloctest.Get%s()" % i)
			self.setResultVariable(i, val)

		lib.messenger.send(None, "update_progress", 100, "Done.")
		
	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute the filter with given inputs and return the output
		"""
		if not lib.ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None
		images = [self.getInput(x) for x in range(1,3)]
		self.eventDesc="Calculating colocalization"
		self.colocFilter.RemoveAllInputs()
		self.colocAutoThreshold.RemoveAllInputs()
		depth = 8
		if self.parameters["OneBit"]:
			depth = 1
		self.colocFilter.SetOutputDepth(depth)

		ch1thresmax = self.getPrecedingResultVariable("Ch1ThresholdMax")
		ch2thresmax = self.getPrecedingResultVariable("Ch2ThresholdMax")
		
		Logging.info("result vars ch1, ch2=",ch1thresmax, ch2thresmax)
		if ch1thresmax != None and ch2thresmax != None:
			slope = self.getPrecedingResultVariable("Slope")
			intercept = self.getPrecedingResultVariable("Intercept")
			print "Got slope, intercept", slope, intercept
			lib.messenger.send(self, "set_slope_intercept", slope, intercept)
			self.set("LowerThresholdCh1", ch1thresmax)
			self.set("LowerThresholdCh2", ch2thresmax)
		maxval = int(max([x.GetScalarRange()[1] for x in images]))
		self.colocRange = maxval
		lib.messenger.send(self, "update_LowerThresholdCh1")
		lib.messenger.send(self, "update_LowerThresholdCh2")
		lib.messenger.send(self, "update_UpperThresholdCh1")
		lib.messenger.send(self, "update_UpperThresholdCh2")
		Logging.info("Maximum value = %d"%maxval, kw="processing") 
		ch1Lower, ch1Upper, ch2Lower, ch2Upper = self.parameters["LowerThresholdCh1"], self.parameters["UpperThresholdCh1"], self.parameters["LowerThresholdCh2"], self.parameters["UpperThresholdCh2"]
		
		self.colocAutoThreshold.AddInput(images[0])
		self.colocAutoThreshold.AddInput(images[1])
		
		# When we set the lower thresholds, then the given thresholds will be used
		self.colocAutoThreshold.SetLowerThresholdCh1(self.parameters["LowerThresholdCh1"])
		self.colocAutoThreshold.SetLowerThresholdCh2(self.parameters["LowerThresholdCh2"])
		self.colocAutoThreshold.SetUpperThresholdCh1(self.parameters["UpperThresholdCh1"])
		self.colocAutoThreshold.SetUpperThresholdCh2(self.parameters["UpperThresholdCh2"])
	
		#if self.oldThresholds != (ch1Lower, ch1Upper, ch2Lower, ch2Upper):
		#	Logging.info("Calculating statistics")
		#	self.colocAutoThreshold.Update()

		#	for variable in self.resultVariables.keys():
		#		if hasattr(self.colocAutoThreshold, "Get%s"%variable):
		#			self.setResultVariable(variable, eval("self.colocAutoThreshold.Get%s()"%variable))


		#	self.oldThresholds = self.parameters["LowerThresholdCh1"], self.parameters["UpperThresholdCh1"], self.parameters["LowerThresholdCh2"], self.parameters["UpperThresholdCh2"]
		
		# This is used if one bit colocalization is selected
		self.colocFilter.SetOutputScalarValue(self.parameters["ColocValue"])

		for i in range(len(images)):
			self.colocFilter.AddInput(images[i])
			self.colocFilter.SetColocalizationLowerThreshold(i, self.parameters["LowerThresholdCh%d"%(i+1)])
			self.colocFilter.SetColocalizationUpperThreshold(i, self.parameters["UpperThresholdCh%d"%(i+1)])
			
		data = self.colocFilter.GetOutput()
		for key in ["LowerThresholdCh1","LowerThresholdCh2","UpperThresholdCh1","UpperThresholdCh2"]:
			self.setResultVariable(key, self.parameters[key])
		
		if self.parameters["Costes"] or self.parameters["Fay"] or self.parameters["Steensel"]:
			self.calculatePValue(images)
		if self.listctrl:
			self.listctrl.updateListCtrl(self.getResultVariableDict())
	
		return data
