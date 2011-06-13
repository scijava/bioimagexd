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
import vtkbxd
import GUI.GUIBuilder
import lib.FilterTypes
import scripting
import types
import vtk

class DeconvolutionFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	Iterative Deconvolution 3D
	"""		
	name = "Iterative Deconvolution"
	category = lib.FilterTypes.DECONVOLUTION
	
	def __init__(self):
		"""
		Initialization
		"""		   
		scripting.wantWholeDataset=1
		lib.ProcessingFilter.ProcessingFilter.__init__(self, (2,2))
		self.vtkfilter = vtkbxd.vtkImageIterativeDeconvolution3D()
		self.vtkfilter.AddObserver("ProgressEvent", lib.messenger.send)
		lib.messenger.connect(self.vtkfilter, 'ProgressEvent', self.updateProgress)
		self.descs = {"Iterations":"Max. number of iterations","Gamma":"Wiener filter gamma (0 = off, 0.0001-0.1)",
					 "FilterX":"Low-pass filter X & Y","FilterZ":"Low-pass filter Z",
					 "ChangeThresholdPercent":"Terminate iteration if mean delta < x%",
					 "Normalize":"Normalize PSF",
					 "AntiRing":"Perform anti-ringing step",
					 "DetectDivergence":"Detect divergence"
					  }
		self.filterDesc = "Performs iterative deconvolution for input image using provided PSF image\nInputs: Grayscale images\nOutput: Grayscale image"
			
	def getInputName(self, n):
		"""
		Return the name of the input #n
		"""			 
		if n == 1: return "Image to deconvolve"
		return "PSF image" 
	
	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""			   
		return [ ["Filtering", ("FilterX","FilterZ")],
				 ["Options",("Normalize","AntiRing","DetectDivergence")],
				 ["Deconvolution",("Iterations","Gamma","ChangeThresholdPercent")],
		]

	def getParameterLevel(self, parameter):
		"""
		Return parameter level
		"""
		if parameter in ["FilterX", "FilterZ", "Iterations"]:
			return scripting.COLOR_BEGINNER
		return scripting.COLOR_EXPERIENCED
		
	def getType(self, parameter):
		"""
		Return the type of the parameter
		"""	   
		if parameter in ["Normalize","DetectDivergence","AntiRing", "FilterX","FilterZ"]:
			return types.BooleanType
		if parameter in ["ChangeThresholdPercent","Gamma"]:
			return types.FloatType
		if parameter == "Iterations": return types.IntType
		
		
	def getDefaultValue(self, parameter):
		"""
		Return the default value of a parameter
		"""		
		if parameter == "Iterations": return 100
		if parameter == "Normalize": return False
		if parameter == "AntiRing": return True 
		if parameter == "DetectDivergence": return True
		if parameter == "FilterX": return True
		if parameter == "FilterZ": return True
		if parameter == "ChangeThresholdPercent": return 0.01
		return 0
		
	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute the filter with given inputs and return the output
		"""
		if not lib.ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None

		import pdb
		pdb.set_trace()
		image = self.getInput(1)
		origType = image.GetScalarType()
		origMin, origMax = image.GetScalarRange()
		if image.GetScalarType() != 10:
			cast = vtk.vtkImageCast()
			cast.SetInput(image)
			cast.SetOutputScalarTypeToFloat()
			image = cast.GetOutput()

		image.Update()
		
		psf = self.getInput(2)
		#psf.SetUpdateExtent(psf.GetWholeExtent())
		#image.SetUpdateExtent(image.GetWholeExtent())
		if psf.GetScalarType() != 10:
			cast = vtk.vtkImageCast()
			cast.SetInput(psf)
			cast.SetOutputScalarTypeToFloat()
			psf = cast.GetOutput()

		psf.Update()
		print "image dims=",image.GetDimensions()
		print "psf dims=",psf.GetDimensions()
		self.vtkfilter.SetInputConnection(0, image.GetProducerPort())
		self.vtkfilter.SetInputConnection(1, psf.GetProducerPort())
		
		print "Setting antiring to",self.parameters["AntiRing"]
		print "anti ring =",self.getParameter("AntiRing")
		self.vtkfilter.SetAntiRing(self.parameters["AntiRing"])
		self.vtkfilter.SetDetectDivergence(self.parameters["DetectDivergence"])
		self.vtkfilter.SetFilterX(self.parameters["FilterX"])
		self.vtkfilter.SetFilterY(self.parameters["FilterX"])
		self.vtkfilter.SetFilterZ(self.parameters["FilterZ"])
		self.vtkfilter.SetChangeThresholdPercent(self.parameters["ChangeThresholdPercent"])
		self.vtkfilter.SetNumberOfIterations(self.parameters["Iterations"])
		self.vtkfilter.SetNormalize(self.parameters["Normalize"])
		self.vtkfilter.SetGamma(self.parameters["Gamma"])
		
		print self.vtkfilter
		self.vtkfilter.Update()
		#minval, maxval = self.vtkfilter.GetOutput().GetScalarRange()
		
		#shiftscale = vtk.vtkImageShiftScale()
		#shift = -(minval - origMin)
		#scale = origMax/(maxval+shift)
		#shiftscale.SetShift(shift)
		#shiftscale.SetScale(scale)
		#print "Shifting by",shift,"scaling by",scale,"new maxval =",scale*(maxval+shift),"new minval =",scale*(minval+shift)
		#shiftscale.SetInput(self.vtkfilter.GetOutput())

		cast = vtk.vtkImageCast()
		cast.SetInputConnection(self.vtkfilter.GetOutputPort())
		#cast.SetInputConnection(shiftscale.GetOutputPort())
		cast.SetOutputScalarType(origType)
		cast.ClampOverflowOn()
		cast.Update()

		# Set original ctf if needed
		if self.prevFilter and 'PSF' in self.prevFilter.getName():
			self.dataUnit.getSettings().set("ColorTransferFunction",self.prevFilter.origCtf)

		return cast.GetOutput()
