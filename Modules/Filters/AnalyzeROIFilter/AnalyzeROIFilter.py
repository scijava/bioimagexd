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

import lib.ProcessingFilter
import lib.FilterTypes
import GUI.GUIBuilder
import types
import scripting
import IntensityMeasurementsList
import wx
import itk

class AnalyzeROIFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	A filter for calculating the volume, total and average intensity of a ROI
	"""		
	name = "Analyze ROI"
	category = lib.FilterTypes.VOXELANALYSE
	level = scripting.COLOR_BEGINNER
	
	def __init__(self):
		"""
		Initialization
		"""		   
		lib.ProcessingFilter.ProcessingFilter.__init__(self, (1, 2))
	  
		self.reportGUI = None
		self.measurements = []
		self.descs = {"ROI": "Region of Interest", "AllROIs": "Measure all ROIs",
					"SecondInput":"Use second input as ROI"}
		self.itkFlag = 1
		self.filterDesc = "Quantitatively analyzes a ROI (Region Of Interest) or several\nInput: Grayscale image\nOutput: Grayscale image"
		
	def getInputName(self, n):
		"""
		Return the name of the input #n
		"""			 
		if n == 2: return "ROI image"
		return "Source dataset" 

	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""			   
		return [["", ("ROI", "AllROIs","SecondInput")]]
		
	def getGUI(self, parent, taskPanel):
		"""
		Return the GUI for this filter
		"""
		gui = lib.ProcessingFilter.ProcessingFilter.getGUI(self, parent, taskPanel)
		if not self.reportGUI:
			self.reportGUI = IntensityMeasurementsList.IntensityMeasurementsList(self.gui, -1)
			if self.measurements:
				self.reportGUI.setMeasurements(self.measurements)
				
			gui.sizer.Add(self.reportGUI, (1, 0), flag = wx.EXPAND | wx.ALL)
			
		return gui
		
	def getType(self, parameter):
		"""
		Return the type of the parameter
		"""	   
		if parameter == "ROI":
			return GUI.GUIBuilder.ROISELECTION
		return types.BooleanType
		
	def getDefaultValue(self, parameter):
		"""
		Return the default value of a parameter
		"""		
		if parameter == "SecondInput": return False
		if parameter == "ROI":
			n = scripting.visualizer.getRegionsOfInterest()
			if n:
				return (0, n[0])
			return 0, None
		return 0
		
	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute the filter with given inputs and return the output
		"""			   
		if not lib.ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None
		
		if not self.parameters["SecondInput"]:
			if not self.parameters["AllROIs"]:
				rois = [self.parameters["ROI"][1]]
				print "rois =", rois
			else:
				rois = scripting.visualizer.getRegionsOfInterest()
		else:
			rois = [self.getInput(2)]

		imagedata =	 self.getInput(1)
		
		mx, my, mz = self.dataUnit.getDimensions()
		values = []

		itkOrig = self.convertVTKtoITK(imagedata)
		for mask in rois:
			if not mask:
				return imagedata
			if self.parameters["SecondInput"]:
				itkLabel = self.convertVTKtoITK(mask)

				roiName = None
				if mask.GetScalarType() == 9:
					a, b = mask.GetScalarRange()
					statValues = range(int(a), int(b))
				else:
					statValues = [255]
			else:
				n, maskImage = lib.ImageOperations.getMaskFromROIs([mask], mx, my, mz)

				itkLabel =	self.convertVTKtoITK(maskImage)
				statValues = [255]
				roiName = mask.getName()

			labelStats = itk.LabelStatisticsImageFilter[itkOrig, itkLabel].New()
			
			labelStats.SetInput(0, itkOrig)
			labelStats.SetLabelInput(itkLabel)
			labelStats.Update()
			for statval in statValues:
		
				n = labelStats.GetCount(statval)
	
				totint = labelStats.GetSum(statval)
				maxval = labelStats.GetMaximum(statval)
				minval = labelStats.GetMinimum(statval)
				mean = labelStats.GetMean(statval)
				sigma = labelStats.GetSigma(statval)
				if not roiName:
					name = "%d"%statval
				else:
					name = roiName
				values.append((name, n, totint, minval, maxval, mean, sigma))
		if self.reportGUI:
			self.reportGUI.setMeasurements(values)
			self.reportGUI.Refresh()
		self.measurements = values
		return imagedata
