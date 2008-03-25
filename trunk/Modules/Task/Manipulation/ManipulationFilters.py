#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: ManipulationFilters
 Project: BioImageXD
 Created: 13.04.2006, KP
 Description:

 A module containing classes representing the filters available in ManipulationPanelC
							
 Copyright (C) 2005	 BioImageXD Project
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
import GUI.GUIBuilder as GUIBuilder
import lib.ImageOperations
try:
	import itk
except:
	pass
import lib.messenger
from lib import ProcessingFilter
import types
import vtk
import vtkbxd
import wx

# getFilterlist() searches through these Modules for Filter classes
import MathFilters
import SegmentationFilters
import MorphologicalFilters
import TrackingFilters
try:
	import RegistrationFilters
except:
	pass

from lib.FilterTypes import *

class IntensityMeasurementList(wx.ListCtrl):
	def __init__(self, parent, log):

		wx.ListCtrl.__init__(self, parent, -1, size = (450, 250), \
							style = wx.LC_REPORT | wx.LC_VIRTUAL | wx.LC_HRULES | wx.LC_VRULES,)

		self.measurements = []
		self.InsertColumn(0, "ROI")
		self.InsertColumn(1, "Voxel #")
		self.InsertColumn(2, "Sum")

		self.InsertColumn(3, "Min")
		self.InsertColumn(4, "Max")
		self.InsertColumn(5, u"Mean\u00B1std.dev.")
	 
		#self.InsertColumn(2, "")
		self.SetColumnWidth(0, 70)
		self.SetColumnWidth(1, 60)
		self.SetColumnWidth(2, 60)
		self.SetColumnWidth(3, 50)
		self.SetColumnWidth(4, 50)
		self.SetColumnWidth(5, 100)

		self.SetItemCount(1000)

		self.attr1 = wx.ListItemAttr()
		self.attr1.SetBackgroundColour("white")

		self.attr2 = wx.ListItemAttr()
		self.attr2.SetBackgroundColour("light blue")
		
		self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected)

	def setMeasurements(self, measurements):
		self.measurements = measurements
		
	def OnItemSelected(self, event):
		self.currentItem = event.m_itemIndex

	def getColumnText(self, index, col):
		item = self.GetItem(index, col)
		return item.GetText()

	def OnGetItemText(self, item, col):
		
		
		if item >= len(self.measurements):
			return ""
		m = self.measurements[item]
		#values.append((mask.getName(),n,totint,avgint, minval, maxval, mean, sigma))
		
		if col == 0:
			return "%s" % m[0]
		elif col in [3]:
			return "%.2f" % m[3]
		elif col == 5:
			return u"%.2f\u00B1%.2f" % (m[5], m[6])
		return "%d" % m[col]

	def OnGetItemImage(self, item):
		return - 1

	def OnGetItemAttr(self, item):
		if item % 2 == 1:
			return self.attr1
		elif item % 2 == 0:
			return self.attr2
		else:
			return None

def getFilters():
	"""
	This function returns all the filter-classes in this module and is used by ManipulationFilters.getFilterList()
	"""
	return [GaussianSmoothFilter, 
			ROIIntensityFilter, GradientFilter, GradientMagnitudeFilter,
			ITKAnisotropicDiffusionFilter, ITKGradientMagnitudeFilter,
			ITKSigmoidFilter, ITKLocalMaximumFilter]

# fixed getFilterList() so that unnecessary wildcard imports could be removed, 10.8.2007 SS
def getFilterList():
	"""
	Modified: 10.8.2007, SS
	This function returns the filter-classes from all filter-modules
	"""
	filterlist = getFilters()
	filterlist += MathFilters.getFilters()
	filterlist += SegmentationFilters.getFilters()
	filterlist += MorphologicalFilters.getFilters()
	filterlist += TrackingFilters.getFilters()
	try:
		filterlist += RegistrationFilters.getFilters()
	except:
		pass
	return filterlist




class GaussianSmoothFilter(ProcessingFilter.ProcessingFilter):
	"""
	A gaussian smoothing filter
	"""		
	name = "Gaussian smooth"
	category = FILTERING
	
	def __init__(self):
		"""
		Initialization
		"""		   
		ProcessingFilter.ProcessingFilter.__init__(self, (1, 1))
		self.vtkfilter = vtk.vtkImageGaussianSmooth()
		self.eventDesc = "Performing gaussian smoothing"
		self.vtkfilter.AddObserver("ProgressEvent", lib.messenger.send)
		lib.messenger.connect(self.vtkfilter, 'ProgressEvent', self.updateProgress)
		self.descs = {"RadiusX": "Radius factor X:", "RadiusY": "Radius factor Y:", "RadiusZ": "Radius factor Z:",
			"Dimensionality": "Dimensionality"}
	
	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""			   
		return [ "Radius factor:", ["", ("RadiusX", "RadiusY", "RadiusZ")],
		["", ("Dimensionality", )]
		]
		
 
	def getType(self, parameter):
		"""
		Return the type of the parameter
		"""	   
		if parameter in ["RadiusX", "RadiusY", "RadiusZ"]:
			return types.FloatType
		return GUIBuilder.SPINCTRL
		
	def getDefaultValue(self, parameter):
		"""
		Return the default value of a parameter
		"""		
		if parameter == "Dimensionality":
			return 3
		return 1.5
		
	def getRange(self, parameter):
		"""
		return the range of the parameter
		"""
		return 1, 3

	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute the filter with given inputs and return the output
		"""			   
		if not ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None
		
		image = self.getInput(1)
		self.vtkfilter.SetInput(image)
		
		x, y, z = self.parameters["RadiusX"], self.parameters["RadiusY"], self.parameters["RadiusZ"]
		dims = self.parameters["Dimensionality"]
		self.vtkfilter.SetRadiusFactors(x, y, z)
		self.vtkfilter.SetDimensionality(dims)
		
		if update:
			self.vtkfilter.Update()
		return self.vtkfilter.GetOutput()			   

		

		
class ROIIntensityFilter(ProcessingFilter.ProcessingFilter):
	"""
	Created: 04.08.2006, KP
	Description: A filter for calculating the volume, total and average intensity of a ROI
	"""		
	name = "Analyze ROIs"
	category = MEASUREMENT
	
	def __init__(self):
		"""
		Initialization
		"""		   
		ProcessingFilter.ProcessingFilter.__init__(self, (1, 2))
	  
		self.reportGUI = None
		self.measurements = []
		self.descs = {"ROI": "Region of Interest", "AllROIs": "Measure all ROIs",
					"SecondInput":"Use second input as ROI"}
		self.itkFlag = 1
		
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
		gui = ProcessingFilter.ProcessingFilter.getGUI(self, parent, taskPanel)
		if not self.reportGUI:
			self.reportGUI = IntensityMeasurementList(self.gui, -1)
			if self.measurements:
				self.reportGUI.setMeasurements(self.measurements)
				
			gui.sizer.Add(self.reportGUI, (1, 0), flag = wx.EXPAND | wx.ALL)
			
		return gui
		
	def getType(self, parameter):
		"""
		Return the type of the parameter
		"""	   
		if parameter == "ROI":
			return GUIBuilder.ROISELECTION
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
			return 0
		return 0
		
	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute the filter with given inputs and return the output
		"""			   
		if not ProcessingFilter.ProcessingFilter.execute(self, inputs):
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
			labelStats.SetInput(1, itkLabel)
			labelStats.Update()
			for statval in statValues:
		
				n = labelStats.GetCount(statval)
	
				totint = labelStats.GetSum(statval)
				maxval = labelStats.GetMaximum(statval)
				minval = labelStats.GetMinimum(statval)
	#			 median = labelStats.GetMedian(255)
	#			 variance = labelStats.GetVariance(255)
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


class GradientFilter(ProcessingFilter.ProcessingFilter):
	"""
	Created: 13.04.2006, KP
	Description: A class for calculating the gradient of the image
	"""		
	name = "Gradient"
	category = MATH
	
	def __init__(self, inputs = (1, 1)):
		"""
		Initialization
		"""		   
		ProcessingFilter.ProcessingFilter.__init__(self, inputs)
		self.vtkfilter = vtk.vtkImageGradient()
		self.vtkfilter.SetDimensionality(3)
		self.vtkfilter.AddObserver("ProgressEvent", lib.messenger.send)
		lib.messenger.connect(self.vtkfilter, 'ProgressEvent', self.updateProgress)
	
	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""			   
		return []

	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute the filter with given inputs and return the output
		"""			   
		if not ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None
		
		self.vtkfilter.SetInput(self.getInput(1))
			
		if update:
			self.vtkfilter.Update()
		return self.vtkfilter.GetOutput()			 


class GradientMagnitudeFilter(ProcessingFilter.ProcessingFilter):
	"""
	Created: 13.04.2006, KP
	Description: A class for calculating the gradient magnitude of the image
	"""		
	name = "Gradient magnitude"
	category = FEATUREDETECTION
	level = scripting.COLOR_BEGINNER

	def __init__(self, inputs = (1, 1)):
		"""
		Initialization
		"""		   
		ProcessingFilter.ProcessingFilter.__init__(self, inputs)
		self.vtkfilter = vtk.vtkImageGradientMagnitude()
		self.vtkfilter.SetDimensionality(3)
		self.vtkfilter.AddObserver("ProgressEvent", lib.messenger.send)
		lib.messenger.connect(self.vtkfilter, 'ProgressEvent', self.updateProgress)
		self.eventDesc = "Performing edge detection (gradient magnitude)"
	
	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""			   
		return []

	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute the filter with given inputs and return the output
		"""			   
		if not ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None
		
		self.vtkfilter.SetInput(self.getInput(1))
			
		if update:
			self.vtkfilter.Update()
		return self.vtkfilter.GetOutput()			 

		
class ITKAnisotropicDiffusionFilter(ProcessingFilter.ProcessingFilter):
	"""
	Created: 13.04.2006, KP
	Description: A class for doing anisotropic diffusion on ITK
	"""		
	name = "Gradient anisotropic diffusion (ITK)"
	category = FILTERING
	
	def __init__(self, inputs = (1, 1)):
		"""
		Initialization
		"""		   
		ProcessingFilter.ProcessingFilter.__init__(self, inputs)
		
		self.eventDesc = "Performing edge preserving smoothing (gradient anisotropic diffusion)"
		self.descs = {"TimeStep": "Time step for iterations", "Conductance": "Conductance parameter",
			"Iterations": "Number of iterations"}
		self.itkFlag = 1
		self.itkfilter = None

	def getParameterLevel(self, parameter):
		"""
		Return the level of the given parameter
		"""
		return scripting.COLOR_INTERMEDIATE
			
	def getDefaultValue(self, parameter):
		"""
		Return the default value of a parameter
		"""	   
		if parameter == "TimeStep":
			return 0.0625
		if parameter == "Conductance":
			return 9.0
		if parameter == "Iterations":
			return 5
		return 0
		
	def getType(self, parameter):
		"""
		Return the type of the parameter
		"""	   
		if parameter in ["TimeStep", "Conductance"]:
			return types.FloatType
		return types.IntType
		
	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""			   
		return [["", ("TimeStep", "Conductance", "Iterations")]]

	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute the filter with given inputs and return the output
		"""					   
		if not ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None
			
		image = self.getInput(1)
		image = self.convertVTKtoITK(image, cast = types.FloatType)
		f3 = itk.Image.F3
		
		self.itkfilter = itk.GradientAnisotropicDiffusionImageFilter[f3, f3].New()

		self.itkfilter.SetInput(image)
		self.itkfilter.SetTimeStep(self.parameters["TimeStep"])
		self.itkfilter.SetConductanceParameter(self.parameters["Conductance"])
		self.itkfilter.SetNumberOfIterations(self.parameters["Iterations"])
		
		if update:
			self.itkfilter.Update()
		return self.itkfilter.GetOutput()			 


class ITKGradientMagnitudeFilter(ProcessingFilter.ProcessingFilter):
	"""
	Created: 13.04.2006, KP
	Description: A class for calculating gradient magnitude on ITK
	"""		
	name = "Gradient magnitude (ITK)"
	category = FEATUREDETECTION
	
	def __init__(self, inputs = (1, 1)):
		"""
		Initialization
		"""		   
		ProcessingFilter.ProcessingFilter.__init__(self, inputs)
		self.eventDesc = "Performing edge detection (gradient magnitude)"
		self.itkFlag = 1
		self.itkfilter = None
		
	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""			   
		return []		 

	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute the filter with given inputs and return the output
		"""					   
		if not ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None
			
		image = self.getInput(1)
		image = self.convertVTKtoITK(image)
		if not self.itkfilter:
			self.itkfilter = itk.GradientMagnitudeImageFilter[image, image].New()

		self.itkfilter.SetInput(image)
		
		if update:
			self.itkfilter.Update()
		data = self.itkfilter.GetOutput()
		return data			   


   


class ITKSigmoidFilter(ProcessingFilter.ProcessingFilter):
	"""
	Created: 29.05.2006, KP
	Description: A class for mapping an image data thru sigmoid image filter
	"""		
	name = "Sigmoid filter (ITK)" 
	category = FILTERING
	
	def __init__(self, inputs = (1, 1)):
		"""
		Initialization
		"""		   
		ProcessingFilter.ProcessingFilter.__init__(self, inputs)
		self.itkFlag = 1
		self.descs = {"Minimum": "Minimum output value", "Maximum": "Maximum Output Value", \
						"Alpha": "Alpha", "Beta": "Beta"}
		
	def getParameterLevel(self, parameter):
		"""
		Return the level of the given parameter
		"""
		return scripting.COLOR_EXPERIENCED				   
		
	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""			   
		return [["Data range", ("Minimum", "Maximum")],
		]		 

	def getDefaultValue(self, parameter):
		"""
		Return the default value of a parameter
		"""	   
		if parameter == "Minimum":
			return 0.0
		if parameter == "Maximum":
			return 1.0
		if parameter == "Alpha":
			return 
		return 0
		
	def getType(self, parameter):
		"""
		Return the type of the parameter
		"""	   
		return types.FloatType

	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute the filter with given inputs and return the output
		"""					   
		if not ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None
			
		image = self.getInput(1)
		image = self.convertVTKtoITK(image, cast = types.FloatType)
		if not self.itkfilter:
			f3 = itk.Image.F3
			self.itkfilter = itk.SigmoidImageFilter[f3, f3].New()
		self.itkfilter.SetInput(image)
		
		self.setImageType("F3")
		data = self.itkfilter.GetOutput()
		if update:
			data.Update()

		return data			   


class ITKLocalMaximumFilter(ProcessingFilter.ProcessingFilter):
	"""
	Created: 29.05.2006, KP
	Description: A class for finding the local maxima in an image
	"""		
	name = "Find local maxima"
	category = FEATUREDETECTION
	
	def __init__(self, inputs = (1, 1)):
		"""
		Initialization
		"""
		ProcessingFilter.ProcessingFilter.__init__(self, inputs)
		self.descs = {"Connectivity": "Use 8 neighbors for connectivity"}
		self.itkFlag = 1
				
	def getDefaultValue(self, parameter):
		"""
		Return the default value of a parameter
		"""	  
		if parameter == "Connectivity":
			return 1
		return 0

	def getType(self, parameter):
		"""
		Return the type of the parameter
		"""	   
		if parameter in ["Connectivity"]:
			return types.BooleanType
				
	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""			   
		return [["", ("Connectivity", )]]

	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute the filter with given inputs and return the output
		"""					   
		if not ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None
			
		image = self.getInput(1)
#		 print "Using as input",image
		image = self.convertVTKtoITK(image)
		uc3 = itk.Image.UC3
		shift = itk.ShiftScaleImageFilter[uc3, uc3].New()
		recons = itk.ReconstructionByDilationImageFilter[uc3, uc3].New()
		subst = itk.SubtractImageFilter[uc3, uc3, uc3].New()
		shift.SetInput(image)
		shift.SetShift(-1)
		recons.SetMaskImage(image)
		recons.SetMarkerImage(shift.GetOutput())
		recons.SetFullyConnected(self.parameters["Connectivity"])
		subst.SetInput1(image)
		subst.SetInput2(recons.GetOutput())
		
		if 1 or update:
			subst.Update()
			
		data = subst.GetOutput()

		return data			   

