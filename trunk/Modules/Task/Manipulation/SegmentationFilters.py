# -*- coding: iso-8859-1 -*-
"""
 Unit: SegmentationFilters
 Project: BioImageXD
 Created: 07.06.2006, KP
 Description:

 A module containing the segmentation filters for the processing task.
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


import traceback
import scripting
import codecs
import csv
import GUI.GUIBuilder as GUIBuilder
import GUI.Dialogs
try:
	import itk
except:
	pass
import lib.ImageOperations
import lib.messenger
import Logging
import os.path
from lib import ProcessingFilter
import time
import types
import vtk
import vtkbxd
import wx

from lib.FilterTypes import *


def getFilters():
	"""
	This function returns all the filter-classes in this module and is used by ManipulationFilters.getFilterList()
	"""
	return [MaskFilter,
			MaximumObjectsFilter, ITKRelabelImageFilter, ITKInvertIntensityFilter,
			ITKConfidenceConnectedFilter, ITKConnectedThresholdFilter,
			ITKNeighborhoodConnectedThresholdFilter]


class MaskFilter(ProcessingFilter.ProcessingFilter):
	"""
	Created: 13.04.2006, KP
	Description: A base class for image mathematics filters
	"""		
	name = "Mask"
	category = MASK
	level = scripting.COLOR_BEGINNER
	def __init__(self, inputs = (2, 2)):
		"""
		Initialization
		"""		   
		ProcessingFilter.ProcessingFilter.__init__(self, inputs)
		self.vtkfilter = vtk.vtkImageMask()
		self.cast = None
		
		self.descs = {"OutputValue": "Masked output value"}
			
			
	def getInputName(self, n):
		"""
		Return the name of the input #n
		"""			 
		if n == 1:
			return "Source dataset %d" % n	  
		return "Mask dataset"
		
	def getDefaultValue(self, parameter):
		"""
		Return the default value of a parameter
		"""	   
		return 0
		
	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""			   
		return [["", ("OutputValue", )]]

	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute the filter with given inputs and return the output
		"""					   
		if not ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None
		self.vtkfilter.SetInput1(self.getInput(1))
		
		maskDataset = self.getInput(2)
		print "maskDataset=",maskDataset.GetScalarType()
		# If scalar type is not unsigned char, then cast the data
		if maskDataset.GetScalarType() != 3:
			# if the data is unsigned long, check that if there's no 0
			# intensity, then use 1 as the background intensity
			if maskDataset.GetScalarType() == 9:
				histogram = lib.ImageOperations.get_histogram(maskDataset)
				print "histogram = ",histogram[0:10]
			if not self.cast:
				self.cast = vtk.vtkImageCast()
			print "Casting data"
			self.cast.RemoveAllInputs()
			self.cast.SetInput(maskDataset)
			self.cast.SetOutputScalarType(3)
			self.cast.SetClampOverflow(1)
			maskDataset = self.cast.GetOutput()
		
		self.vtkfilter.SetInput2(maskDataset)
		self.vtkfilter.SetMaskedOutputValue(self.parameters["OutputValue"])
		
		if update:
			self.vtkfilter.Update()
		return self.vtkfilter.GetOutput()


class MaximumObjectsFilter(ProcessingFilter.ProcessingFilter):
	"""
	A filter for labeling all separate objects in an image
	"""		
	name = "Threshold for maximum object number"
	category = THRESHOLDING
	
	def __init__(self, inputs = (1, 1)):
		"""
		Initialization
		"""		   
		ProcessingFilter.ProcessingFilter.__init__(self, inputs)		
		self.descs = {"MinSize": "Minimum object size in pixels"}
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
		if parameter == "MinSize":
			return 15
		return 0
		
	def getType(self, parameter):
		"""
		Return the type of the parameter
		"""	   
		return types.IntType
		
	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""
		return [["", ("MinSize", )]]
		
	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute the filter with given inputs and return the output
		"""
		if not ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None
			
		image = self.getInput(1)
		image = self.convertVTKtoITK(image)
		if not self.itkfilter:
			self.itkfilter = itk.ThresholdMaximumConnectedComponentsImageFilter[image].New()

		self.itkfilter.SetOutsideValue(0)
		self.itkfilter.SetInsideValue(255)
		self.itkfilter.SetInput(image)
		self.itkfilter.SetMinimumObjectSizeInPixels(self.parameters["MinSize"])
				
		self.setImageType("UL3")
		self.itkfilter.Update()
		print "\n\n", self.itkfilter.GetThresholdValue()
		data = self.itkfilter.GetOutput()
		return data

		
class ITKRelabelImageFilter(ProcessingFilter.ProcessingFilter):
	"""
	Created: 13.04.2006, KP
	Description: Re-label an image produced by watershed segmentation
	"""		
	name = "Re-label image"
	category = OBJECT
	level = scripting.COLOR_BEGINNER
	def __init__(self, inputs = (1, 1)):
		"""
		Initialization
		"""		   
		ProcessingFilter.ProcessingFilter.__init__(self, inputs)
		self.descs = {"Threshold": "Remove objects with less voxels than:"}
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
		return 0
		
	def getType(self, parameter):
		"""
		Return the type of the parameter
		"""	   
		return types.IntType
		
	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""			   
		return [["Minimum object size (in pixels)", ("Threshold", )]]

	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute the filter with given inputs and return the output
		"""
		if not ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None
			
		image = self.getInput(1)
		image = self.convertVTKtoITK(image)
		if not self.itkfilter:
			print "Image=", image
			self.itkfilter = itk.RelabelComponentImageFilter[image, image].New()
		self.itkfilter.SetInput(image)
		th = self.parameters["Threshold"]
		self.itkfilter.SetMinimumObjectSize(th)

		data = self.itkfilter.GetOutput()
				
		self.itkfilter.Update()

		return data


class ITKInvertIntensityFilter(ProcessingFilter.ProcessingFilter):
	"""
	Created: 05.07.2006, KP
	Description: Invert the intensity of the image
	"""		
	name = "Invert intensity"
	category = MISCFILTERING
	
	def __init__(self, inputs = (1, 1)):
		"""
		Initialization
		"""		   
		ProcessingFilter.ProcessingFilter.__init__(self, inputs)
				
		self.descs = {}
		self.itkFlag = 1
		self.itkfilter = None
			
	def getDefaultValue(self, parameter):
		"""
		Return the default value of a parameter
		"""
		return 0
		
	def getType(self, parameter):
		"""
		Return the type of the parameter
		"""	   
		return types.IntType
		
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
			self.itkfilter = itk.InvertIntensityImageFilter[image, image].New()
			
		self.itkfilter.SetInput(image)
		
		#self.setImageType("UL3")

		data = self.itkfilter.GetOutput()			 
				
		self.itkfilter.Update()
		
		return data

		
class ITKConfidenceConnectedFilter(ProcessingFilter.ProcessingFilter):
	"""
	Created: 29.05.2006, KP
	Description: A class for doing confidence connected segmentation
	"""		
	name = "Confidence connected threshold"
	category = REGIONGROWING
	
	def __init__(self, inputs = (1, 1)):
		"""
		Initialization
		"""
		ProcessingFilter.ProcessingFilter.__init__(self, inputs)
		
		
		self.descs = {"Seed": "Seed voxel", "Neighborhood": "Initial neighborhood size",
			"Multiplier": "Range relaxation", "Iterations": "Iterations"}
		self.itkFlag = 1
		self.itkfilter = None

	def getParameterLevel(self, parameter):
		"""
		Return the level of the given parameter
		"""
		if parameter in ["Multiplier", "Iterations"]:
			return scripting.COLOR_EXPERIENCED
		if parameter == "Neighborhood":
			return scripting.COLOR_INTERMEDIATE
		
		return scripting.COLOR_BEGINNER			   
			
	def getDefaultValue(self, parameter):
		"""
		Return the default value of a parameter
		"""	   
		if parameter == "Seed":
			return []
		elif parameter == "Multiplier":
			return 2.5
		elif parameter == "Iterations":
			return 5
		elif parameter == "Neighborhood":
			return 2
			
	def getType(self, parameter):
		"""
		Return the type of the parameter
		"""	   
		if parameter == "Seed":
			return GUIBuilder.PIXELS
		elif parameter == "Multiplier":
			return types.FloatType
		elif parameter == "Iterations":
			return types.IntType
		elif parameter == "Neighborhood":
			return types.IntType
			
	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""			   
		return [["Seed", ("Seed", )],
		["Segmentation", ("Neighborhood", "Multiplier", "Iterations")]]

	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute the filter with given inputs and return the output
		"""					   
		if not ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None
			
		image = self.getInput(1)
		image = self.convertVTKtoITK(image)
		uc3 = itk.Image.UC3
		self.itkfilter = itk.ConfidenceConnectedImageFilter.IUC3IUC3.New()
		self.itkfilter.SetInput(image)
		
		pixelidx = itk.Index[3]()
		for (x, y, z) in self.parameters["Seed"]:
			pixelidx.SetElement(0, x)
			pixelidx.SetElement(1, y)
			pixelidx.SetElement(2, z)
			self.itkfilter.AddSeed(pixelidx)	
			
		iters = self.parameters["Iterations"]
		self.itkfilter.SetNumberOfIterations(iters)
		
		mult = self.parameters["Multiplier"]
		print "mult=", mult
		self.itkfilter.SetMultiplier(mult)
		rad = self.parameters["Neighborhood"]
		self.itkfilter.SetInitialNeighborhoodRadius(rad)
		
		self.itkfilter.SetReplaceValue(255)
		if update:
			self.itkfilter.Update()
			
		data = self.itkfilter.GetOutput()

		return data			   


class ITKConnectedThresholdFilter(ProcessingFilter.ProcessingFilter):
	"""
	Created: 26.05.2006, KP
	Description: A class for doing confidence connected segmentation
	"""		
	name = "Connected threshold"
	category = REGIONGROWING
	level = scripting.COLOR_BEGINNER
	def __init__(self, inputs = (1, 1)):
		"""
		Initialization
		"""		   
		ProcessingFilter.ProcessingFilter.__init__(self, inputs)		
		
		self.descs = {"Seed": "Seed voxel", "Upper": "Upper threshold", "Lower": "Lower threshold"}
		self.itkFlag = 1
		self.setImageType("UC3")
		self.itkfilter = None

	def getDefaultValue(self, parameter):
		"""
		Return the default value of a parameter
		"""	   
		if parameter == "Seed":
			return []
		elif parameter == "Upper":
			return 255
		elif parameter == "Lower":
			return 128
		
	def getType(self, parameter):
		"""
		Return the type of the parameter
		"""	   
		if parameter in ["Lower", "Upper"]:
			return GUIBuilder.THRESHOLD
		return GUIBuilder.PIXELS
				
	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""			   
		return [["Seed", ("Seed", )],
		["Threshold", (("Lower", "Upper"), )]]

	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute the filter with given inputs and return the output
		"""					   
		if not ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None
		image = self.getInput(1)
#		 print "Using as input",image
		image = self.convertVTKtoITK(image)

		self.itkfilter = itk.ConnectedThresholdImageFilter.IUC3IUC3.New()
		self.itkfilter.SetInput(image)
		self.itkfilter.SetLower(self.parameters["Lower"])
		self.itkfilter.SetUpper(self.parameters["Upper"])
		
		pixelidx = itk.Index[3]()
		for (x, y, z) in self.parameters["Seed"]:
			pixelidx.SetElement(0, x)
			pixelidx.SetElement(1, y)
			pixelidx.SetElement(2, z)
			print "Using as seed", x, y, z, pixelidx
			self.itkfilter.AddSeed(pixelidx)	
		print "Threshold=", self.parameters["Lower"], self.parameters["Upper"]
		
		
		self.itkfilter.SetReplaceValue(255)
		if update:
			self.itkfilter.Update()
			
		data = self.itkfilter.GetOutput()
		#if last:
		#	 return self.convertITKtoVTK(data,cast="UC3")
			
		return data		 

		
class ITKNeighborhoodConnectedThresholdFilter(ProcessingFilter.ProcessingFilter):
	"""
	Created: 29.05.2006, KP
	Description: A class for doing connected threshold segmentation 
	"""		
	name = "Neighborhood connected threshold"
	category = REGIONGROWING
	
	def __init__(self, inputs = (1, 1)):
		"""
		Initialization
		"""		   
		ProcessingFilter.ProcessingFilter.__init__(self, inputs)
		self.setImageType("UC3")
		
		self.descs = {"Seed": "Seed voxel", "Upper": "Upper threshold", "Lower": "Lower threshold",
			"RadiusX": "X neighborhood size",
			"RadiusY": "Y neighborhood size",
			"RadiusZ": "Z neighborhood size"}
		self.itkFlag = 1
		self.itkfilter = None

	def getParameterLevel(self, parameter):
		"""
		Return the level of the given parameter
		"""
		if parameter in ["RadiusX", "RadiusY", "RadiusZ"]:
			return scripting.COLOR_INTERMEDIATE
		
		return scripting.COLOR_BEGINNER						   
		
	def getDefaultValue(self, parameter):
		"""
		Return the default value of a parameter
		"""	   
		if parameter == "Seed":
			return []
		elif parameter == "Upper":
			return 255
		elif parameter == "Lower":
			return 128
		elif parameter in ["RadiusX", "RadiusY"]:
			return 2
		return 1
		
	def getType(self, parameter):
		"""
		Return the type of the parameter
		"""	   
		if parameter in ["Lower", "Upper"]:
			return GUIBuilder.THRESHOLD
		elif "Radius" in parameter:
			return types.IntType
		return GUIBuilder.PIXELS
				
	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""			   
		return [["Seed", ("Seed", )],
		["Threshold", (("Lower", "Upper"), )],
		["Neighborhood", ("RadiusX", "RadiusY", "RadiusZ")]]

	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute the filter with given inputs and return the output
		"""					   
		if not ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None
			
		image = self.getInput(1)
#		 print "Using as input",image
		image = self.convertVTKtoITK(image)
		self.itkfilter = itk.NeighborhoodConnectedImageFilter.IUC3IUC3.New()
		self.itkfilter.SetInput(image)
		self.itkfilter.SetLower(self.parameters["Lower"])
		self.itkfilter.SetUpper(self.parameters["Upper"])
		
		pixelidx = itk.Index[3]()
		for (x, y, z) in self.parameters["Seed"]:
			pixelidx.SetElement(0, x)
			pixelidx.SetElement(1, y)
			pixelidx.SetElement(2, z)
			self.itkfilter.AddSeed(pixelidx)	
		
		rx, ry, rz = self.parameters["RadiusX"], self.parameters["RadiusY"], self.parameters["RadiusZ"]
		
		size = itk.Size[3]()
		size.SetElement(0, rx)
		size.SetElement(0, ry)
		size.SetElement(0, rz)
		self.itkfilter.SetRadius(size)
		self.itkfilter.SetReplaceValue(255)
		if update:
			self.itkfilter.Update()
			
		data = self.itkfilter.GetOutput()
		#if last:
		#	 return self.convertITKtoVTK(data,imagetype="UC3")
			
		return data			   
