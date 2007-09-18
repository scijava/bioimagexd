#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: ManipulationFilters
 Project: BioImageXD
 Created: 13.04.2006, KP
 Description:

 A module containing classes representing the filters available in ManipulationPanelC
							
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
import RegistrationFilters

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
#        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
		#self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnItemDeselected)

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
    Created: 10.8.2007, SS
    Description: This function returns all the filter-classes in this module and is used by ManipulationFilters.getFilterList()
    """
    return [AnisotropicDiffusionFilter, SolitaryFilter, GaussianSmoothFilter,
            ShiftScaleFilter, ExtractComponentFilter, TimepointCorrelationFilter,
            ROIIntensityFilter, CutDataFilter, GradientFilter, GradientMagnitudeFilter,
            ITKAnisotropicDiffusionFilter, ITKGradientMagnitudeFilter,
            ITKCannyEdgeFilter, ITKSigmoidFilter, ITKLocalMaximumFilter]

# fixed getFilterList() so that unnecessary wildcard imports could be removed, 10.8.2007 SS
def getFilterList():
    """
    Created: KP
    Modified: 10.8.2007, SS
    Description: This function returns the filter-classes from all filter-modules
    """
    filterlist = getFilters()
    filterlist += MathFilters.getFilters()
    filterlist += SegmentationFilters.getFilters()
    filterlist += MorphologicalFilters.getFilters()
    filterlist += TrackingFilters.getFilters()
    filterlist += RegistrationFilters.getFilters()
    return filterlist


MATH = "Image arithmetic"
SEGMENTATION = "Segmentation"
FILTERING = "Filtering"
ITK = "ITK"
LOGIC = "Logical operations"
MEASUREMENT = "Measurements"
REGION_GROWING = "Region growing"
FEATUREDETECTION = "Feature detection"
TRACKING = "Tracking"
REGISTRATION = "Registration"

class AnisotropicDiffusionFilter(ProcessingFilter.ProcessingFilter):
	"""
	Class: Anisotropic diffusion
	Created: 13.04.2006, KP
	Description: An edge preserving smoothing filter
	"""     
	name = "Anisotropic diffusion 3D"
	category = FILTERING
	
	def __init__(self):
		"""
		Created: 13.04.2006, KP
		Description: Initialization
		"""        
		ProcessingFilter.ProcessingFilter.__init__(self, (1, 1))
		self.vtkfilter = vtk.vtkImageAnisotropicDiffusion3D()
		self.descs = {"Faces": "Faces", "Corners": "Corners", "Edges": "Edges",
			"CentralDiff": "Central difference", "Gradient": "Gradient to neighbor",
				"DiffThreshold": "Diffusion threshold:", "DiffFactor": "Diffusion factor:"}
	
	def getParameters(self):
		"""
		Created: 15.04.2006, KP
		Description: Return the list of parameters needed for configuring this GUI
		"""            
		return [ 
		"Neighborhood:", ["", ( ("Faces", "Corners", "Edges"), )],
		"Threshold:", ["Gradient measure", ( ("CentralDiff", "Gradient"), ("cols", 2)) ],
		["", ("DiffThreshold", "DiffFactor")]
		]
		
	def getDesc(self, parameter):
		"""
		Created: 15.04.2006, KP
		Description: Return the description of the parameter
		"""    
		return self.descs[parameter]
		
	def getLongDesc(self, parameter):
		"""
		Created: 15.04.2006, KP
		Description: Return a long description of the parameter
		"""     
		if parameter == "Faces":
			return "Toggle whether the 6 voxels adjoined by faces are included in the neighborhood."
		elif parameter == "Corners":
			return "Toggle whether the 8 corner connected voxels are included in the neighborhood."
		elif parameter == "Edges":
			return "Toggle whether the 12 edge connected voxels are included in the neighborhood."
		return ""
		
	def getType(self, parameter):
		"""
		Created: 15.04.2006, KP
		Description: Return the type of the parameter
		"""    
		if parameter in ["Faces", "Edges", "Corners"]:
			return types.BooleanType
		elif parameter in ["CentralDiff", "Gradient"]:
			return GUIBuilder.RADIO_CHOICE
		return types.FloatType
		
	def getDefaultValue(self, parameter):
		"""
		Created: 15.04.2006, KP
		Description: Return the default value of a parameter
		"""     
		if parameter in ["Faces", "Edges", "Corners"]:
			return 1
		elif parameter == "DiffThreshold":
			return 5.0
		elif parameter == "DiffFactor":
			return 1.0
		return 2
		

	def execute(self, inputs, update = 0, last = 0):
		"""
		Created: 15.04.2006, KP
		Description: Execute the filter with given inputs and return the output
		"""            
		if not ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None
		
		image = self.getInput(1)
		self.vtkfilter.SetInput(image)
		
		self.vtkfilter.SetDiffusionThreshold(self.parameters["DiffThreshold"])
		self.vtkfilter.SetDiffusionFactor(self.parameters["DiffFactor"])
		self.vtkfilter.SetFaces(self.parameters["Faces"])
		self.vtkfilter.SetEdges(self.parameters["Edges"])
		self.vtkfilter.SetCorners(self.parameters["Corners"])
		self.vtkfilter.SetGradientMagnitudeThreshold(self.parameters["CentralDiff"])
		
		if update:
			self.vtkfilter.Update()
		return self.vtkfilter.GetOutput()      

class SolitaryFilter(ProcessingFilter.ProcessingFilter):
	"""
	Created: 13.04.2006, KP
	Description: A filter for removing solitary noise pixels
	"""     
	name = "Solitary filter"
	category = FILTERING
	
	def __init__(self):
		"""
		Created: 13.04.2006, KP
		Description: Initialization
		"""        
		ProcessingFilter.ProcessingFilter.__init__(self, (1, 1))
		self.vtkfilter = vtkbxd.vtkImageSolitaryFilter()
		self.descs = {"HorizontalThreshold": "X:", "VerticalThreshold": "Y:", \
						"ProcessingThreshold": "Processing threshold:"}
	
	def getParameters(self):
		"""
		Created: 15.04.2006, KP
		Description: Return the list of parameters needed for configuring this GUI
		"""            
		return [ "Thresholds:", ["", ("HorizontalThreshold", "VerticalThreshold", "ProcessingThreshold")]]
		
	def getDesc(self, parameter):
		"""
		Created: 15.04.2006, KP
		Description: Return the description of the parameter
		"""    
		return self.descs[parameter]
		
	def getLongDesc(self, parameter):
		"""
		Created: 15.04.2006, KP
		Description: Return a long description of the parameter
		""" 
		Xhelp = "Threshold that a pixel's horizontal neighbor needs to be over so that the pixel is not removed."
		Yhelp = "Threshold that a pixel's vertical neighbor needs to be over so that the pixel is not removed."
		Thresholdhelp = "Threshold that a pixel needs to be over to get processed by solitary filter."
		
		if parameter == "HorizontalThreshold":
			return Xhelp
		elif parameter == "VerticalThreshold":
			return Yhelp
		elif parameter == "ProcessingThreshold":
			return Thresholdhelp
		return ""
		
		
	def getType(self, parameter):
		"""
		Created: 15.04.2006, KP
		Description: Return the type of the parameter
		"""    
		if parameter in ["HorizontalThreshold", "VerticalThreshold", "ProcessingThreshold"]:
			return types.IntType
		
	def getDefaultValue(self, parameter):
		"""
		Created: 15.04.2006, KP
		Description: Return the default value of a parameter
		"""     
		return 0
		

	def execute(self, inputs, update = 0, last = 0):
		"""
		Created: 15.04.2006, KP
		Description: Execute the filter with given inputs and return the output
		"""            
		if not ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None
		
		image = self.getInput(1)
		self.vtkfilter.SetInput(image)
		
		self.vtkfilter.SetFilteringThreshold(self.parameters["ProcessingThreshold"])
		self.vtkfilter.SetHorizontalThreshold(self.parameters["HorizontalThreshold"])
		self.vtkfilter.SetVerticalThreshold(self.parameters["VerticalThreshold"])
		
		if update:
			self.vtkfilter.Update()
		return self.vtkfilter.GetOutput()      

class GaussianSmoothFilter(ProcessingFilter.ProcessingFilter):
	"""
	Created: 15.11.2006, KP
	Description: A gaussian smoothing filter
	"""     
	name = "Gaussian smooth"
	category = FILTERING
	
	def __init__(self):
		"""
		Created: 15.11.2006, KP
		Description: Initialization
		"""        
		ProcessingFilter.ProcessingFilter.__init__(self, (1, 1))
		self.vtkfilter = vtk.vtkImageGaussianSmooth()
		self.descs = {"RadiusX": "Radius factor X:", "RadiusY": "Radius factor Y:", "RadiusZ": "Radius factor Z:",
			"Dimensionality": "Dimensionality"}
	
	def getParameters(self):
		"""
		Created: 15.11.2006, KP
		Description: Return the list of parameters needed for configuring this GUI
		"""            
		return [ "Radius factor:", ["", ("RadiusX", "RadiusY", "RadiusZ")],
		["", ("Dimensionality", )]
		]
		
	def getDesc(self, parameter):
		"""
		Created: 15.11.2006, KP
		Description: Return the description of the parameter
		"""    
		return self.descs[parameter]
 
		
		
	def getType(self, parameter):
		"""
		Created: 15.11.2006, KP
		Description: Return the type of the parameter
		"""    
		if parameter in ["RadiusX", "RadiusY", "RadiusZ"]:
			return types.FloatType
		return GUIBuilder.SPINCTRL
		
	def getDefaultValue(self, parameter):
		"""
		Created: 15.11.2006, KP
		Description: Return the default value of a parameter
		"""     
		if parameter == "Dimensionality":
			return 3
		return 1.5
		
	def getRange(self, parameter):
		"""
		Created: 15.11.2006, KP
		Description: return the range of the parameter
		"""
		return 1, 3

	def execute(self, inputs, update = 0, last = 0):
		"""
		Created: 15.11.2006, KP
		Description: Execute the filter with given inputs and return the output
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
		
class ShiftScaleFilter(ProcessingFilter.ProcessingFilter):
	"""
	Created: 13.04.2006, KP
	Description: A filter for shifting the values of dataset by constant and scaling by a constant
	"""     
	name = "Shift and Scale"
	category = MATH
	
	def __init__(self):
		"""
		Created: 13.04.2006, KP
		Description: Initialization
		"""        
		ProcessingFilter.ProcessingFilter.__init__(self, (1, 1))
		self.vtkfilter = vtk.vtkImageShiftScale()
		self.descs = {"Shift": "Shift:", "Scale": "Scale:", "AutoScale": "Scale to range 0-255"}
	
	def getParameters(self):
		"""
		Created: 15.04.2006, KP
		Description: Return the list of parameters needed for configuring this GUI
		"""            
		return [["", ("Shift", "Scale", "AutoScale")]]
		
	def getDesc(self, parameter):
		"""
		Created: 15.04.2006, KP
		Description: Return the description of the parameter
		"""    
		return self.descs[parameter]
		
	def getLongDesc(self, parameter):
		"""
		Created: 15.04.2006, KP
		Description: Return a long description of the parameter
		""" 
		return ""
		
		
	def getType(self, parameter):
		"""
		Created: 15.04.2006, KP
		Description: Return the type of the parameter
		"""    
		if parameter in ["Shift", "Scale"]:
			return types.FloatType
		elif parameter == "AutoScale":
			return types.BooleanType
		
	def getDefaultValue(self, parameter):
		"""
		Created: 15.04.2006, KP
		Description: Return the default value of a parameter
		"""     
		if parameter in ["Shift", "Scale"]:
			return 0
		return 1
		

	def execute(self, inputs, update = 0, last = 0):
		"""
		Created: 15.04.2006, KP
		Description: Execute the filter with given inputs and return the output
		"""            
		if not ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None
		
		image = self.getInput(1)
		#print "Using ",image
		self.vtkfilter.SetInput(image)
		if self.parameters["AutoScale"]:
			x, y = image.GetScalarRange()
			print "image type=", image.GetScalarTypeAsString()
			print "Range of data=", x, y
			self.vtkfilter.SetOutputScalarTypeToUnsignedChar()
			if not y:
				lib.messenger.send(None, "show_error", "Bad scalar range", "Data has scalar range of %d -%d" % (x, y))
				return vtk.vtkImageData()
			scale = 255.0 / y
			print "Scale=", scale
			self.vtkfilter.SetShift(0)
			self.vtkfilter.SetScale(scale)
		else:
			self.vtkfilter.SetShift(self.parameters["Shift"])
			self.vtkfilter.SetScale(self.parameters["Scale"])
		
		if update:
			self.vtkfilter.Update()
		return self.vtkfilter.GetOutput()    
		
		
		
class ExtractComponentFilter(ProcessingFilter.ProcessingFilter):
	"""
	Created: 21.01.2007, KP
	Description: A filter for extracting component or components from a dataset
	"""     
	name = "Extract components"
	category = FILTERING
	
	def __init__(self):
		"""
		Created: 21.01.2007, KP
		Description: Initialization
		"""        
		ProcessingFilter.ProcessingFilter.__init__(self, (1, 1))
		self.vtkfilter = vtk.vtkImageExtractComponents()
		self.descs = {"Component1": "Component #1", "Component2": "Component #2", "Component3": "Component #3"}
	
	def getParameters(self):
		"""
		Created: 21.01.2007, KP
		Description: Return the list of parameters needed for configuring this GUI
		"""            
		return [["", ("Component1", "Component2", "Component3")]]
		
	def getDesc(self, parameter):
		"""
		Created: 21.01.2007, KP
		Description: Return the description of the parameter
		"""    
		return self.descs[parameter]
		
	def getLongDesc(self, parameter):
		"""
		Created: 21.01.2007, KP
		Description: Return a long description of the parameter
		""" 
		return ""
		
	def getRange(self, parameter):
		"""
		Created: 21.01.2007, KP
		Description: return the range of values for given parameter
		"""
		return ["No output", "R (component 1)", "G (component 2)", "B (component 3)"]
		
	def getType(self, parameter):
		"""
		Created: 21.01.2007, KP
		Description: Return the type of the parameter
		"""    
		if parameter in ["Component1", "Component2", "Component3"]:
			return GUIBuilder.CHOICE
		
	def getDefaultValue(self, parameter):
		"""
		Created: 21.01.2007, KP
		Description: Return the default value of a parameter
		"""     
		if parameter == "Component1":
			return 1
		if parameter == "Component2":
			return 2
		if parameter == "Component3":
			return 3
		

	def execute(self, inputs, update = 0, last = 0):
		"""
		Created: 15.04.2006, KP
		Description: Execute the filter with given inputs and return the output
		"""            
		if not ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None
		
		image = self.getInput(1)
		#print "Using ",image
		self.vtkfilter.SetInput(image)
		
		cmps = []
		cmps.append(self.parameters["Component1"])
		cmps.append(self.parameters["Component2"])
		cmps.append(self.parameters["Component3"])
		while 0 in cmps:
			cmps.remove(0)
		cmps = [x - 1 for x in cmps]
		t = tuple(cmps)
		print "Extracting components", t
		self.vtkfilter.SetComponents(*t)            
		
		if update:
			self.vtkfilter.Update()
		return self.vtkfilter.GetOutput()    
		
		
		
		
class TimepointCorrelationFilter(ProcessingFilter.ProcessingFilter):
	"""
	Created: 31.07.2006, KP
	Description: A filter for calculating the correlation between two timepoints
	"""     
	name = "Timepoint correlation"
	category = MEASUREMENT
	
	def __init__(self):
		"""
		Created: 31.07.2006, KP
		Description: Initialization
		"""        
		ProcessingFilter.ProcessingFilter.__init__(self, (1, 1))
		
		self.box = None
		self.descs = {"Timepoint1": "First timepoint:", "Timepoint2": "Second timepoint:"}
	
	def getParameters(self):
		"""
		Created: 31.07.2006, KP
		Description: Return the list of parameters needed for configuring this GUI
		"""            
		return [["", ("Timepoint1", "Timepoint2")]]
		
	def getGUI(self, parent, taskPanel):
		"""
		Created: 31.07.2006, KP
		Description: Return the GUI for this filter
		"""              
		gui = ProcessingFilter.ProcessingFilter.getGUI(self, parent, taskPanel)
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
		Created: 31.07.2006, KP
		Description: Return the type of the parameter
		"""    
		return GUIBuilder.SLICE
		
	def getDefaultValue(self, parameter):
		"""
		Created: 31.07.2006, KP
		Description: Return the default value of a parameter
		"""     
		if parameter == "Timepoint1":
			return 0
		return 1
		
		
	def getRange(self, parameter):
		"""
		Created: 31.07.2006, KP
		Description: Return the range for the parameter
		"""             
		return (0, self.dataUnit.getNumberOfTimepoints())

	def execute(self, inputs, update = 0, last = 0):
		"""
		Created: 31.07.2006, KP
		Description: Execute the filter with given inputs and return the output
		"""            
		if not ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None
		tp1 = self.parameters["Timepoint1"]
		tp2 = self.parameters["Timepoint2"]
		self.vtkfilter = vtkbxd.vtkImageAutoThresholdColocalization()
		units = self.dataUnit.getSourceDataUnits()
		data1 = units[0].getTimepoint(tp1)
		# We need to prepare a copy of the data since
		# when we get the next timepoint, the data we got earlier will reference the
		# new data
		tp = vtk.vtkImageData()
		tp.DeepCopy(data1)
		data2 = units[0].getTimepoint(tp2)
		data1 = tp
		
		self.vtkfilter.AddInput(data1)
		self.vtkfilter.AddInput(data2)
		# Set the thresholds so they won't be calculated
		self.vtkfilter.SetLowerThresholdCh1(0)
		self.vtkfilter.SetLowerThresholdCh2(0)
		self.vtkfilter.SetUpperThresholdCh1(255)
		self.vtkfilter.SetUpperThresholdCh2(255)
	   
		#print "Using ",image
		

		self.vtkfilter.Update()
		self.corrLbl2.SetLabel("%.5f" % self.vtkfilter.GetPearsonWholeImage())
		return self.getInput(1)
		
class ROIIntensityFilter(ProcessingFilter.ProcessingFilter):
	"""
	Created: 04.08.2006, KP
	Description: A filter for calculating the volume, total and average intensity of a ROI
	"""     
	name = "Analyze ROIs"
	category = MEASUREMENT
	
	def __init__(self):
		"""
		Created: 31.07.2006, KP
		Description: Initialization
		"""        
		ProcessingFilter.ProcessingFilter.__init__(self, (1, 1))
	  
		self.reportGUI = None
		self.measurements = []
		self.descs = {"ROI": "Region of Interest", "AllROIs": "Measure all ROIs"}
		self.itkFlag = 1

	def getParameters(self):
		"""
		Created: 31.07.2006, KP
		Description: Return the list of parameters needed for configuring this GUI
		"""            
		return [["", ("ROI", "AllROIs")]]
		
		
	def getGUI(self, parent, taskPanel):
		"""
		Created: 31.07.2006, KP
		Description: Return the GUI for this filter
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
		Created: 31.07.2006, KP
		Description: Return the type of the parameter
		"""    
		if parameter == "ROI":
			return GUIBuilder.ROISELECTION
		return types.BooleanType
		
	def getDefaultValue(self, parameter):
		"""
		Created: 31.07.2006, KP
		Description: Return the default value of a parameter
		"""     
		if parameter == "ROI":
			n = scripting.visualizer.getRegionsOfInterest()
			if n:
				return (0, n[0])
			return 0
		return 0
		
	def execute(self, inputs, update = 0, last = 0):
		"""
		Created: 31.07.2006, KP
		Description: Execute the filter with given inputs and return the output
		"""            
		if not ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None
		
		if not self.parameters["AllROIs"]:
			rois = [self.parameters["ROI"][1]]
			print "rois =", rois
		else:
			rois = scripting.visualizer.getRegionsOfInterest()
		imagedata =  self.getInput(1)
		
		mx, my, mz = self.dataUnit.getDimensions()
		values = []
		for mask in rois:
			if not mask:
				print "No mask"
				return imagedata
			print "Processing mask=", mask
			n, maskImage = lib.ImageOperations.getMaskFromROIs([mask], mx, my, mz)

			itkLabel =  self.convertVTKtoITK(maskImage)
			itkOrig = self.convertVTKtoITK(imagedata)

			labelStats = itk.LabelStatisticsImageFilter[itkOrig, itkLabel].New()
			
			labelStats.SetInput(0, itkOrig)
			labelStats.SetInput(1, itkLabel)
			labelStats.Update()
		
			n = labelStats.GetCount(255)

			totint = labelStats.GetSum(255)
			maxval = labelStats.GetMaximum(255)
			minval = labelStats.GetMinimum(255)
#            median = labelStats.GetMedian(255)
#            variance = labelStats.GetVariance(255)
			mean = labelStats.GetMean(255)
			sigma = labelStats.GetSigma(255)
			values.append((mask.getName(), n, totint, minval, maxval, mean, sigma))
		if self.reportGUI:
			self.reportGUI.setMeasurements(values)
			self.reportGUI.Refresh()
		self.measurements = values
		return imagedata



class CutDataFilter(ProcessingFilter.ProcessingFilter):
	"""
	Created: 04.08.2006, KP
	Description: A filter for cutting the data to a smaller size
	"""     
	name = "Extract a subset"
	category = FILTERING
	
	def __init__(self):
		"""
		Created: 10.08.2006, KP
		Description: Initialization
		"""        
		ProcessingFilter.ProcessingFilter.__init__(self, (1, 1))
		self.reportGUI = None
		self.measurements = []
		self.descs = {"UseROI": "Use Region of Interest to define resulting region", \
						"ROI": "Region of Interest Used in Cutting", \
						"FirstSlice": "First Slice in Resulting Stack", \
						"LastSlice": "Last Slice in Resulting Stack"}
	
	def getParameters(self):
		"""
		Created: 31.07.2006, KP
		Description: Return the list of parameters needed for configuring this GUI
		"""            
		return [["Region of Interest", ("UseROI", "ROI")], ["Slices", ("FirstSlice", "LastSlice")]]
		

	def getRange(self, parameter):
		"""
		Created: 31.07.2006, KP
		Description: Return the range for the parameter
		"""       
		if self.dataUnit:
			x, y, z = self.dataUnit.getDimensions()
		else:
			z = 0
		return (1, z + 1)
		
		
	def getType(self, parameter):
		"""
		Created: 31.07.2006, KP
		Description: Return the type of the parameter
		"""    
		if parameter == "ROI":
			return GUIBuilder.ROISELECTION
		if parameter == "UseROI":
			return types.BooleanType
		return GUIBuilder.SLICE
		
	def getDefaultValue(self, parameter):
		"""
		Created: 31.07.2006, KP
		Description: Return the default value of a parameter
		"""     
		if parameter == "UseROI":
			return 0
		if parameter == "ROI":
			n = scripting.visualizer.getRegionsOfInterest()
			if n:
				return (0, n[0])
			return 0
		if parameter == "LastSlice":
			if self.dataUnit:
				x, y, z = self.dataUnit.getDimensions()
			else:
				z = 1
			return z
			
		return 1
		
	def execute(self, inputs, update = 0, last = 0):
		"""
		Created: 31.07.2006, KP
		Description: Execute the filter with given inputs and return the output
		"""            
		if not ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None

		maxx, maxy, maxz = self.dataUnit.getDimensions()
		minx = 0
		miny = 0
		minz = 0
		if self.parameters["UseROI"]:
			minx, maxx = 99999, 0
			miny, maxy = 99999, 0            
			roi = self.parameters["ROI"][1]
			pts = roi.getCoveredPoints()
			for (x, y) in pts:
				if minx > x:
					minx = x
				if x > maxx:
					maxx = x
				if miny > y:
					miny = y
				if y > maxy:
					maxy = y
  
		minz = self.parameters["FirstSlice"]
		maxz = self.parameters["LastSlice"]
		minz -= 1
		maxz -= 1
		
		print "VOI=", minx, maxx, miny, maxy, minz, maxz
		voi = vtk.vtkExtractVOI()
		imagedata =  self.getInput(1)
		imagedata.SetUpdateExtent(minx,maxx,miny,maxy,minz,maxz)
		voi.SetInput(imagedata)
		voi.SetVOI(minx, maxx, miny, maxy, minz, maxz)
		voi.Update()
		data = voi.GetOutput()
		data.SetWholeExtent(0, (maxx - minx) - 1, 0, (maxy - miny) - 1, 0, (maxz - minz) - 1)
		data.SetExtent(0, (maxx - minx) - 1, 0, (maxy - miny) - 1, 0, (maxz - minz) - 1)
		data.SetUpdateExtent(data.GetExtent())
		return  data


class GradientFilter(ProcessingFilter.ProcessingFilter):
	"""
	Created: 13.04.2006, KP
	Description: A class for calculating the gradient of the image
	"""     
	name = "Gradient"
	category = MATH
	
	def __init__(self, inputs = (1, 1)):
		"""
		Created: 13.04.2006, KP
		Description: Initialization
		"""        
		ProcessingFilter.ProcessingFilter.__init__(self, inputs)
		self.vtkfilter = vtk.vtkImageGradient()
		self.vtkfilter.SetDimensionality(3)
	
	def getParameters(self):
		"""
		Created: 15.04.2006, KP
		Description: Return the list of parameters needed for configuring this GUI
		"""            
		return []

	def execute(self, inputs, update = 0, last = 0):
		"""
		Created: 15.04.2006, KP
		Description: Execute the filter with given inputs and return the output
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
		Created: 13.04.2006, KP
		Description: Initialization
		"""        
		ProcessingFilter.ProcessingFilter.__init__(self, inputs)
		self.vtkfilter = vtk.vtkImageGradientMagnitude()
		self.vtkfilter.SetDimensionality(3)
	
	def getParameters(self):
		"""
		Created: 15.04.2006, KP
		Description: Return the list of parameters needed for configuring this GUI
		"""            
		return []

	def execute(self, inputs, update = 0, last = 0):
		"""
		Created: 15.04.2006, KP
		Description: Execute the filter with given inputs and return the output
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
		Created: 13.04.2006, KP
		Description: Initialization
		"""        
		ProcessingFilter.ProcessingFilter.__init__(self, inputs)
		
		
		self.descs = {"TimeStep": "Time step for iterations", "Conductance": "Conductance parameter",
			"Iterations": "Number of iterations"}
		self.itkFlag = 1
		self.itkfilter = None

	def getParameterLevel(self, parameter):
		"""
		Created: 9.11.2006, KP
		Description: Return the level of the given parameter
		"""
		return scripting.COLOR_INTERMEDIATE
			
	def getDefaultValue(self, parameter):
		"""
		Created: 15.04.2006, KP
		Description: Return the default value of a parameter
		"""    
		if parameter == "TimeStep":
			return 0.0630
		if parameter == "Conductance":
			return 9.0
		if parameter == "Iterations":
			return 5
		return 0
		
	def getType(self, parameter):
		"""
		Created: 13.04.2006, KP
		Description: Return the type of the parameter
		"""    
		if parameter in ["TimeStep", "Conductance"]:
			return types.FloatType
		return types.IntType
		
		
	def getParameters(self):
		"""
		Created: 15.04.2006, KP
		Description: Return the list of parameters needed for configuring this GUI
		"""            
		return [["", ("TimeStep", "Conductance", "Iterations")]]


	def execute(self, inputs, update = 0, last = 0):
		"""
		Created: 15.04.2006, KP
		Description: Execute the filter with given inputs and return the output
		"""                    
		if not ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None
			
		image = self.getInput(1)
		image = self.convertVTKtoITK(image, cast = types.FloatType)
		
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
		Created: 13.04.2006, KP
		Description: Initialization
		"""        
		ProcessingFilter.ProcessingFilter.__init__(self, inputs)
		self.itkFlag = 1
		self.itkfilter = None
		
		
	def getParameters(self):
		"""
		Created: 15.04.2006, KP
		Description: Return the list of parameters needed for configuring this GUI
		"""            
		return []        

	def execute(self, inputs, update = 0, last = 0):
		"""
		Created: 15.04.2006, KP
		Description: Execute the filter with given inputs and return the output
		"""                    
		if not ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None
			
		image = self.getInput(1)
		image = self.convertVTKtoITK(image)
		if not self.itkfilter:
			self.itkfilter = itk.GradientMagnitudeImageFilter[image, image].New()

		self.itkfilter.SetInput(image)
		
		#self.setImageType("F3")
		
		if update:
			self.itkfilter.Update()
		data = self.itkfilter.GetOutput()
		#if last or self.nextFilter and not self.nextFilter.getITK():            
		#    print "Converting to VTK"
		#    data=self.convertITKtoVTK(data,imagetype="F3")
		#    print "data=",data
		return data            

class ITKCannyEdgeFilter(ProcessingFilter.ProcessingFilter):
	"""
	Created: 13.04.2006, KP
	Description: A class that uses the ITK canny edge detection filter
	"""     
	name = "Canny edge detection"
	category = FEATUREDETECTION
	
	def __init__(self, inputs = (1, 1)):
		"""
		Created: 13.04.2006, KP
		Description: Initialization
		"""        
		ProcessingFilter.ProcessingFilter.__init__(self, inputs)
		self.itkFlag = 1
		self.itkfilter = None
		
	def getParameterLevel(self, parameter):
		"""
		Created: 1.11.2006, KP
		Description: Return the level of the given parameter
		"""
		return scripting.COLOR_EXPERIENCED
		
	def getParameters(self):
		"""
		Created: 15.04.2006, KP
		Description: Return the list of parameters needed for configuring this GUI
		"""            
		return []        

	def execute(self, inputs, update = 0, last = 0):
		"""
		Created: 15.04.2006, KP
		Description: Execute the filter with given inputs and return the output
		"""                    
		if not ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None
			
		image = self.getInput(1)
		image = self.convertVTKtoITK(image)
		if not self.itkfilter:
			self.itkfilter = itk.CannyEdgeDetectionImageFilter[image, image].New()

		self.itkfilter.SetInput(image)
		
		#self.setImageType("F3")
		
		if update:
			self.itkfilter.Update()
		data = self.itkfilter.GetOutput()
		#if last or self.nextFilter and not self.nextFilter.getITK():            
		#    print "Converting to VTK"
		#    data=self.convertITKtoVTK(data,imagetype="F3")
		#    print "data=",data
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
		Created: 13.04.2006, KP
		Description: Initialization
		"""        
		ProcessingFilter.ProcessingFilter.__init__(self, inputs)
		self.itkFlag = 1
		self.descs = {"Minimum": "Minimum output value", "Maximum": "Maximum Output Value", \
						"Alpha": "Alpha", "Beta": "Beta"}
		f3 = itk.Image.F3
		self.itkfilter = itk.SigmoidImageFilter[f3, f3].New()
		
	def getParameterLevel(self, parameter):
		"""
		Created: 9.11.2006, KP
		Description: Return the level of the given parameter
		"""
		return scripting.COLOR_EXPERIENCED                 
		
	def getParameters(self):
		"""
		Created: 15.04.2006, KP
		Description: Return the list of parameters needed for configuring this GUI
		"""            
		return [["Data range", ("Minimum", "Maximum")],
		]        
	def getDefaultValue(self, parameter):
		"""
		Created: 15.04.2006, KP
		Description: Return the default value of a parameter
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
		Created: 13.04.2006, KP
		Description: Return the type of the parameter
		"""    
		return types.FloatType


	def execute(self, inputs, update = 0, last = 0):
		"""
		Created: 15.04.2006, KP
		Description: Execute the filter with given inputs and return the output
		"""                    
		if not ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None
			
		image = self.getInput(1)
		image = self.convertVTKtoITK(image, cast = types.FloatType)
		self.itkfilter.SetInput(image)
		
		self.setImageType("F3")
		
		if update:
			self.itkfilter.Update()
		data = self.itkfilter.GetOutput()
		#if last or self.nextFilter and not self.nextFilter.getITK():            
		#    print "Converting to VTK"
		#    data=self.convertITKtoVTK(data,imagetype="F3")
		#    print "data=",data
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
		Created: 26.05.2006, KP
		Description: Initialization
		"""        
		ProcessingFilter.ProcessingFilter.__init__(self, inputs)
		
		
		self.descs = {"Connectivity": "Use 8 neighbors for connectivity"}
		self.itkFlag = 1
		
			
	def getDefaultValue(self, parameter):
		"""
		Created: 26.05.2006, KP
		Description: Return the default value of a parameter
		"""   
		if parameter == "Connectivity":
			return 1
		return 0
	def getType(self, parameter):
		"""
		Created: 26.05.2006, KP
		Description: Return the type of the parameter
		"""    
		if parameter in ["Connectivity"]:
			return types.BooleanType
				
	def getParameters(self):
		"""
		Created: 15.04.2006, KP
		Description: Return the list of parameters needed for configuring this GUI
		"""            
		return [["", ("Connectivity", )]]

	def execute(self, inputs, update = 0, last = 0):
		"""
		Created: 15.04.2006, KP
		Description: Execute the filter with given inputs and return the output
		"""                    
		if not ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None
			
		image = self.getInput(1)
#        print "Using as input",image
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
		
		if update:
			subst.Update()
			
		data = subst.GetOutput()
#        if last:
#            return self.convertITKtoVTK(data,imagetype="UC3")
			
		return data            

