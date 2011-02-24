#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Copyright (C) 2009  BioImageXD Project
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
__author__ = "BioImageXD Project <http://www.bioimagexd.net/>"
__version__ = "$Revision$"
__date__ = "$Date$"

import lib.ProcessingFilter
import lib.FilterTypes
import scripting
import GUI.GUIBuilder
import wx
import itk
import types
import math
import FRAPAnalysisList

class FRAPAnalysisFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	Description: Filter for doing FRAP analysis
	"""
	name = "FRAP Analysis"
	category = lib.FilterTypes.VOXELANALYSE
	level = scripting.COLOR_EXPERIENCED
	
	def __init__(self):
		"""
		Initialization
		"""
		lib.ProcessingFilter.ProcessingFilter.__init__(self, (1, 2))
		self.descs = {"ROI": "Use ROI as FRAP ROI",
					  "SecondInput": "Use second input as FRAP ROI"}
		self.itkFlag = 1
		self.timePointMeasurements = []
		self.frapMeasurements = {}
		
		self.timePointGUI = None
		self.frapGUI = None
		self.filterDesc = "Quantitatively analyzes FRAP (Fluorescence Recovery After Photobleaching) data\nInput: Grayscale image\nOutput: Grayscale image"

	def getInputName(self, n):
		"""
		Return the name of the input n
		"""
		if n == 2:
			return "ROI mask"
		return "Source dataset"
		
	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""			   
		return [["Select ROI to use", ("ROI", "SecondInput")]]
				
	def getType(self, parameter):
		"""
		Return the type of the parameter
		"""	   
		if parameter == "ROI":
			return GUI.GUIBuilder.ROISELECTION
		return types.BooleanType

	def getDefaultValue(self, parameter):
		"""
		"""
		if parameter == "SecondInput":
			return False
		if parameter == "ROI":
			n = scripting.visualizer.getRegionsOfInterest()
			if n:
				return 0, n[0]
			return 0, None
		return 0

	def getGUI(self, parent, taskPanel):
		"""
		Return the GUI ofr this filter
		"""
		gui = lib.ProcessingFilter.ProcessingFilter.getGUI(self, parent, taskPanel)
		if not self.timePointGUI:
			self.timePointGUI = FRAPAnalysisList.FRAPIntensityMeasurementList(self.gui, -1)
			if self.timePointMeasurements:
				self.timePointGUI.SetItemCount(len(self.timePointMeasurements))
				self.timePointGUI.setMeasurements(self.timePointMeasurements)

			self.frapGUI = FRAPAnalysisList.FRAPAnalysisList(self.gui, -1)

			self.exportBtn = wx.Button(self.gui, -1, "Export statistics")
			self.exportBtn.Bind(wx.EVT_BUTTON, self.onExportStatistics)

			sizer = wx.BoxSizer(wx.VERTICAL)
			sizer.Add(self.timePointGUI, 1, wx.EXPAND)
			sizer.AddSpacer((5,5))
			sizer.Add(self.frapGUI, 1)
			sizer.AddSpacer((5,5))
			sizer.Add(self.exportBtn)
			sizer.AddSpacer((5,5))
			gui.sizer.Add(sizer, (1,0), flag = wx.EXPAND | wx.ALL)

		return gui

	def onExportStatistics(self, evt):
		"""
		Export statistics button event handler
		"""
		pass
		
	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute the filter with given inputs and return the output
		"""
		if not lib.ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None

		timePoints = self.dataUnit.getNumberOfTimepoints()
		if timePoints:
			self.timePointGUI.SetItemCount(timePoints)

		if not self.parameters["SecondInput"]:
			roi = self.parameters["ROI"][1]
		else:
			roi = self.getInput(2)

		image = self.getInput(1)
		if not roi:
			return image

		dx, dy, dz = self.dataUnit.getDimensions()
		radius = 0.0
		timeStamps = self.dataUnit.getSettings().get("TimeStamps")
		for tp in range(timePoints):
			image = self.dataUnit.getSourceDataUnits()[0].getTimepoint(tp)
			itkImage = self.convertVTKtoITK(image)

			maskValue = 255
			if self.parameters["SecondInput"]:
				itkMask = self.convertVTKtoITK(mask)
				min, maskValue = mask.GetScalarRange()
			else:
				n, mask = lib.ImageOperations.getMaskFromROIs([roi], dx, dy, dz)
				itkMask = self.convertVTKtoITK(mask)
				min, maskValue = mask.GetScalarRange()

			maskValue = int(maskValue)
			labelStats = itk.LabelStatisticsImageFilter[itkImage, itkMask].New()
			labelStats.SetInput(0, itkImage)
			labelStats.SetLabelInput(itkMask)
			labelStats.Update()

			numPixels = labelStats.GetCount(maskValue)
			totInt = labelStats.GetSum(maskValue)
			maxInt = labelStats.GetMaximum(maskValue)
			minInt = labelStats.GetMinimum(maskValue)
			meanInt = labelStats.GetMean(maskValue)
			sigma = labelStats.GetSigma(maskValue)
			self.timePointMeasurements.append({"NumPixels": numPixels,
											   "TotInt": totInt,
											   "MaxInt": maxInt,
											   "MinInt": minInt,
											   "MeanInt": meanInt,
											   "Sigma": sigma})
			if radius <= 0.0:
				radius = math.sqrt(numPixels / math.pi)

		if self.timePointGUI:
			self.timePointGUI.setStats(self.timePointMeasurements)
			self.timePointGUI.Refresh()

		# Calculate FRAP statistics
		lowestIntTP = 0
		lowestInt = self.timePointMeasurements[0]["MeanInt"]
		for n, tpStat in enumerate(self.timePointMeasurements):
			if lowestInt > tpStat["MeanInt"]:
				lowestIntTP = n
				lowestInt = tpStat["MeanInt"]				
		self.frapMeasurements["LowestInt"] = lowestInt
		
		highestIntBeforeTP = 0
		highestIntBefore = self.timePointMeasurements[0]["MeanInt"]
		for n, tpStat in enumerate(self.timePointMeasurements[:lowestIntTP-1]):
			if highestIntBefore < tpStat["MeanInt"]:
				highestIntBeforeTP = n
				highestIntBefore = tpStat["MeanInt"]
		self.frapMeasurements["BaselineInt"] = highestIntBefore

		highestIntAfterTP = len(self.timePointMeasurements) - 1
		highestIntAfter = self.timePointMeasurements[-1]["MeanInt"]
		for n, tpStat in enumerate(self.timePointMeasurements[lowestIntTP:]):
			if highestIntAfter < tpStat["MeanInt"]:
				highestIntAfterTP = n
				highestIntAfter = tpStat["MeanInt"]
		self.frapMeasurements["AfterRecoveryInt"] = highestIntAfter

		self.frapMeasurements["RecoveryPercentage"] = (highestIntAfter - lowestInt) / (highestIntBefore - lowestInt) * 100

		halfRecInt = highestIntBefore / 2
		halfRecIntTP = lowestIntTP
		diffInt = 0.0
		for n, tpStat in enumerate(self.timePointMeasurements[lowestIntTP:highestIntAfterTP]):
			if tpStat["MeanInt"] > halfRecInt:
				halfRecIntTP = n + lowestIntTP
				break

		recTime = timeStamps[halfRecIntTP] - timeStamps[lowestIntTP]
		self.frapMeasurements["HalfRecoveryTime"] = recTime

		self.frapMeasurements["DiffusionConstant"] = 2 * radius**2 / (4 * recTime)

		# Add results to frapGUI
		for key, value in self.frapMeasurements.iteritems():
			eval("self.frapGUI.set%s(value)"%key)
		self.frapGUI.Refresh()
		
		return image
