# -*- coding: iso-8859-1 -*-
"""
 Unit: SegmentationFilters
 Project: BioImageXD
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
import itk
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
	return [MaximumObjectsFilter, ITKRelabelImageFilter, ITKInvertIntensityFilter,
			ITKConfidenceConnectedFilter, ITKConnectedThresholdFilter,
			ITKNeighborhoodConnectedThresholdFilter]


class MaximumObjectsFilter(ProcessingFilter.ProcessingFilter):
	"""
	A filter for labeling all separate objects in an image
	"""		
	name = "Threshold for maximum object number"
	category = THRESHOLDING
	level = scripting.COLOR_BEGINNER
	
	def __init__(self, inputs = (1, 1)):
		"""
		Initialization
		"""		   
		ProcessingFilter.ProcessingFilter.__init__(self, inputs)		
		self.descs = {"MinSize": "Minimum object size in pixels"}
		self.itkFlag = 1
		self.itkfilter = None
		self.filterDesc = "Computes the threshold value that maximizes the number of objects in the image\nInput: Grayscale image\nOutput: Binary image"

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
	Re-label an image produced by watershed segmentation
	"""		
	name = "Re-label image"
	category = OBJECT
	level = scripting.COLOR_EXPERIENCED
	
	def __init__(self, inputs = (1, 1)):
		"""
		Initialization
		"""		   
		ProcessingFilter.ProcessingFilter.__init__(self, inputs)
		self.descs = {"Threshold": "Remove objects with less voxels than:"}
		self.itkFlag = 1
		self.itkfilter = None
		self.filterDesc = "Remaps labels in label image, order by size\nInput: Label image\nOutput: Label image"
		
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
	Invert the intensity of the image
	"""		
	name = "Invert"
	category = MATH
	level = scripting.COLOR_BEGINNER
	
	def __init__(self, inputs = (1, 1)):
		"""
		Initialization
		"""		   
		ProcessingFilter.ProcessingFilter.__init__(self, inputs)
				
		self.descs = {}
		self.itkFlag = 1
		self.itkfilter = None
		self.filterDesc = "Inverts the intensities of an image for every pixel/voxel\nInput: Grayscale/Binary image\nOutput: Grayscale/Binary image"

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

		data = self.itkfilter.GetOutput()			 
		self.itkfilter.Update()
		
		return data

		
class ITKConfidenceConnectedFilter(ProcessingFilter.ProcessingFilter):
	"""
	A class for doing confidence connected segmentation
	"""		
	name = "Confidence connected threshold"
	category = REGIONGROWING
	level = scripting.COLOR_EXPERIENCED
	
	def __init__(self, inputs = (1, 1)):
		"""
		Initialization
		"""
		ProcessingFilter.ProcessingFilter.__init__(self, inputs)
		
		
		self.descs = {"Seed": "Seed voxel", "Neighborhood": "Initial neighborhood size",
			"Multiplier": "Range relaxation", "Iterations": "Iterations"}
		self.itkFlag = 1
		self.itkfilter = None
		self.filterDesc = "Iteratively grows/changes initial neighborhood using pixels/voxels inside specified confidence range of neighborhood mean and variance\nInput: Grayscale image\nOutput: Binary image"

	def getParameterLevel(self, parameter):
		"""
		Return the level of the given parameter
		"""
		if parameter in ["Multiplier", "Iterations"]:
			return scripting.COLOR_EXPERIENCED
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
		self.itkfilter = itk.ConfidenceConnectedImageFilter[image,image].New()
		self.itkfilter.SetInput(image)
		dim = image.GetLargestPossibleRegion().GetImageDimension()
		
		pixelidx = eval("itk.Index[%d]()"%dim)
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
	A class for doing confidence connected segmentation
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
		self.filterDesc = "Includes all pixels/voxels in result that are connected to seed and inside defined thresholds\nInput: Grayscale image\nOutput: Binary image"

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

		self.itkfilter = itk.ConnectedThresholdImageFilter[image,image].New()
		self.itkfilter.SetInput(image)
		self.itkfilter.SetLower(self.parameters["Lower"])
		self.itkfilter.SetUpper(self.parameters["Upper"])
		dim = image.GetLargestPossibleRegion().GetImageDimension()
		
		pixelidx = eval("itk.Index[%d]()"%dim)
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
		return data		 

		
class ITKNeighborhoodConnectedThresholdFilter(ProcessingFilter.ProcessingFilter):
	"""
	A class for doing connected threshold segmentation 
	"""		
	name = "Neighborhood connected threshold"
	category = REGIONGROWING
	level = scripting.COLOR_EXPERIENCED
	
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
		self.filterDesc = "Includes all pixels/voxels in result that are connected to seed and whose all neighbors are inside defined thresholds\nInput: Grayscale image\nOutput: Binary image"

	def getParameterLevel(self, parameter):
		"""
		Return the level of the given parameter
		"""
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
		image = self.convertVTKtoITK(image)
		self.itkfilter = itk.NeighborhoodConnectedImageFilter[image,image].New()
		self.itkfilter.SetInput(image)
		self.itkfilter.SetLower(self.parameters["Lower"])
		self.itkfilter.SetUpper(self.parameters["Upper"])
		dim = image.GetLargestPossibleRegion().GetImageDimension()
		
		pixelidx = eval("itk.Index[%d]()"%dim)
		for (x, y, z) in self.parameters["Seed"]:
			pixelidx.SetElement(0, x)
			pixelidx.SetElement(1, y)
			pixelidx.SetElement(2, z)
			self.itkfilter.AddSeed(pixelidx)	
		
		rx, ry, rz = self.parameters["RadiusX"], self.parameters["RadiusY"], self.parameters["RadiusZ"]
		
		size = eval("itk.Size[%d]()"%dim)
		size.SetElement(0, rx)
		size.SetElement(0, ry)
		if dim == 3:
			size.SetElement(0, rz)
		self.itkfilter.SetRadius(size)
		self.itkfilter.SetReplaceValue(255)
		if update:
			self.itkfilter.Update()
			
		data = self.itkfilter.GetOutput()
		return data			   
