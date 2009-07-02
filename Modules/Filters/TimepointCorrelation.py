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
import vtk
import vtkbxd
import types
import GUI.GUIBuilder
import lib.FilterTypes
import scripting
import wx

class TimepointCorrelationFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	A filter for calculating the correlation between two timepoints
	"""		
	name = "Timepoint correlation"
	category = lib.FilterTypes.VOXELANALYSE
	
	def __init__(self):
		"""
		Initialization
		"""		   
		lib.ProcessingFilter.ProcessingFilter.__init__(self, (1, 1))
		
		self.box = None
		self.descs = {"Timepoint1": "First timepoint:", "Timepoint2": "Second timepoint:"}
		self.resultVariables = {"Correlation": "Correlation between timepoints", 
		"Timepoint1": "First timepoint", "Timepoint2":"Second timepoint"}
	
	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""			   
		return [["", ("Timepoint1", "Timepoint2")]]
		
	def getGUI(self, parent, taskPanel):
		"""
		Return the GUI for this filter
		"""				 
		gui = lib.ProcessingFilter.ProcessingFilter.getGUI(self, parent, taskPanel)
		if not self.box:
			self.corrLbl = wx.StaticText(gui, -1, "Correlation:")
			self.corrLbl2 = wx.StaticText(gui, -1, "0.0")
			box = wx.BoxSizer(wx.HORIZONTAL)
			box.Add(self.corrLbl)
			box.Add(self.corrLbl2)
			self.box = box
			gui.sizer.Add(box, (1, 0), flag = wx.EXPAND | wx.LEFT | wx.RIGHT)

		return gui
		
	def getType(self, parameter):
		"""
		Return the type of the parameter
		"""	   
		return GUI.GUIBuilder.SLICE
		
	def getDefaultValue(self, parameter):
		"""
		Return the default value of a parameter
		"""		
		if parameter == "Timepoint1":
			return 0
		return 1
		
	def getRange(self, parameter):
		"""
		Return the range for the parameter
		"""				
		return (1, self.dataUnit.getNumberOfTimepoints())

	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute the filter with given inputs and return the output
		"""			   
		if not lib.ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None

		tp1 = self.parameters["Timepoint1"] - 1
		tp2 = self.parameters["Timepoint2"] - 1
		self.vtkfilter = vtkbxd.vtkImageAutoThresholdColocalization()
		units = self.dataUnit.getSourceDataUnits()
		data1 = units[0].getTimepoint(tp1)
		# We need to prepare a copy of the data since when we get the next
		# timepoint, the data we got earlier will reference the new data
		tp = vtk.vtkImageData()
		data1.SetUpdateExtent(data1.GetWholeExtent())
		data1.Update()
		tp.DeepCopy(data1)
		data1 = tp
		data2 = units[0].getTimepoint(tp2)
		data2.SetUpdateExtent(data2.GetWholeExtent())
		data2.Update()
		
		self.vtkfilter.AddInput(data1)
		self.vtkfilter.AddInput(data2)

		# Set the thresholds so they won't be calculated
		self.vtkfilter.SetLowerThresholdCh1(0)
		self.vtkfilter.SetLowerThresholdCh2(0)
		self.vtkfilter.SetUpperThresholdCh1(255)
		self.vtkfilter.SetUpperThresholdCh2(255)
		self.vtkfilter.Update()
		correlation = self.vtkfilter.GetPearsonWholeImage()
		self.setResultVariable("Timepoint1",tp1)
		self.setResultVariable("Timepoint2",tp2)
		self.setResultVariable("Correlation",correlation)
		
		self.corrLbl2.SetLabel("%.5f" % correlation)
		return self.getInput(1)
