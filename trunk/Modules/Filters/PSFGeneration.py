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
import lib.ImageOperations
import scripting
import types
import random
import math
import vtk
import os
import Logging
import csv

class PSFGenerationFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	A filter for generating test data
	"""		
	name = "PSF generation"
	category = lib.FilterTypes.DECONVOLUTION
	level = scripting.COLOR_EXPERIENCED
	
	def __init__(self):
		"""
		Initialization
		"""
		lib.ProcessingFilter.ProcessingFilter.__init__(self, (1, 1))
		self.imageCache = {}
		self.vtkfilter = vtkbxd.vtkImageDiffractionPSF3D()
		self.origCtf = None
		for i in range(1, 2):
			self.setInputChannel(i, i)
		self.descs = {"RefractionIndex":"Index of refraction of the media",
					  "NumericalAperture":"Numerical aperture",
					  "Wavelength":"Wavelength (nm)",
					  "SphericalAberration":"Longitudinal Spherical Aberration (nm)",
					  "VoxelSpacing":"Voxel spacing (nm)",
					  "SliceSpacing":"Slice spacing (nm)",
					  "X":"PSF width (px)",
					  "Y":"PSF height (px)",
					  "Z":"PSF depth (slices)",
					  "Normalization":"Normalization"}
		self.filterDesc = "Generates computational model of PSF to be used for deconvolution\nInput: None\nOutput: Grayscale image"
	
	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""			   
		return [ ["Imaging parameters (0 = read from file)",("RefractionIndex","NumericalAperture","Wavelength","SphericalAberration")],
				["PSF output",("X","Y","Z","VoxelSpacing","SliceSpacing","Normalization")]
		]
				
	def setParameter(self, parameter, value):
		"""
		An overriden method for setting the parameter value, used to catch and set the number
		of timepoints
		"""
		if self.parameters.get(parameter)!=value:
			self.modified = 1
		lib.ProcessingFilter.ProcessingFilter.setParameter(self, parameter, value)
		if parameter in ["X","Y","Z"]:
			if self.dataUnit:
				print (self.parameters["X"], self.parameters["Y"], self.parameters["Z"])
				#self.dataUnit.setNumberOfTimepoints(1)
				self.dataUnit.setModifiedDimensions((self.parameters["X"], self.parameters["Y"], self.parameters["Z"]))
				lib.messenger.send(None, "update_dataset_info")

	def getParameterLevel(self, parameter):
		"""
		Returns parameter level
		"""
		if parameter in ["SphericalAberration", "Normalization"]:
			return scripting.COLOR_EXPERIENCED
		return scripting.COLOR_BEGINNER
	
	def onRemove(self):
		"""
		A callback for stuff to do when this filter is being removed.
		"""
		if self.origCtf:
			self.dataUnit.getSettings().set("ColorTransferFunction",self.origCtf)
			self.origCtf = None
		if self.dataUnit:
			self.dataUnit.setModifiedDimensions(None)
				
	def getRange(self, parameter):
		"""
		Return the range of options for the parameter
		"""
		if parameter == "Normalization":
			return ["Peak = 1", "Peak = 255", "Sum of pixels = 1"]
		
	def getType(self, parameter):
		"""
		Return the type of the parameter
		"""	   
		if parameter in ["RefractionIndex","NumericalAperture"]:
			return types.FloatType
		if parameter == "Normalization": return GUI.GUIBuilder.CHOICE;
			
		return types.IntType
		
	def getDefaultValue(self, parameter):
		"""
		Return the default value of a parameter
		"""		
		if parameter == "Normalization": return 2
		if parameter == "RefractionIndex": return 1.3
		if parameter in ["X","Y"]: return 100
		if parameter == "Z": return 11
		if self.dataUnit:
			dataUnit = self.getInputDataUnit(1)
			vx, vy, vz = dataUnit.getVoxelSize()
			if parameter == "SliceSpacing":
				return vz*1000000000 # scale to nanometers
			elif parameter == "VoxelSpacing":
				return vx*1000000000
			elif parameter == "NumericalAperture":

				return dataUnit.getNumericalAperture()
				
			elif parameter == "Wavelength":
				return dataUnit.getExcitationWavelength()
		return 0

	def canSelectChannels(self):
		"""
		No channel selection for PSF generation filter
		"""
		return 0
		
	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute the filter with given inputs and return the output
		"""			   
		if not lib.ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None

		lib.messenger.send(None, "update_dataset_info")
		scripting.wantWholeDataset = 1
		
		dataUnit = self.getInputDataUnit(1)
#		dataSource = dataUnit.getDataSource()
		self.vtkfilter.SetRefractionIndex(self.parameters["RefractionIndex"])
		numericalAperture = self.parameters["NumericalAperture"]
		print "Using numerical aperture=", numericalAperture
		self.vtkfilter.SetNumericalAperture(numericalAperture)
		
		wavelength = self.parameters["Wavelength"]
		print "Using wavelenght", wavelength
		self.vtkfilter.SetWavelength(wavelength)
		
		self.vtkfilter.SetSphericalAberration(self.parameters["SphericalAberration"])
		print "Using normalization = %d"%self.parameters["Normalization"]
		self.vtkfilter.SetNormalization(self.parameters["Normalization"])
		
		w, h, d = self.parameters["X"], self.parameters["Y"], self.parameters["Z"]
		self.vtkfilter.SetDimensions([w,h,d])
		
		vx = self.parameters["VoxelSpacing"]
		vz = self.parameters["SliceSpacing"]
		
		print "Using spacing",vx,vx,vz
		self.vtkfilter.SetPixelSpacing(vx)
		self.vtkfilter.SetSliceSpacing(vz)
		
		self.vtkfilter.Update()
		psf = self.vtkfilter.GetOutput()
		psf.SetUpdateExtent(psf.GetWholeExtent())
		print psf.GetScalarRange()
		minval, maxval = psf.GetScalarRange()

#		ctf = vtk.vtkColorTransferFunction()
		#ctf.AddRGBPoint(0, 0,0,0)
		#ctf.AddRGBPoint(maxval, 0,255,0)

		if not self.origCtf:
			origCtf = self.dataUnit.getSettings().get("ColorTransferFunction")
			self.origCtf = origCtf
		ctf = lib.ImageOperations.fire(0, maxval)
		self.dataUnit.getSettings().set("ColorTransferFunction", ctf)
		return psf
