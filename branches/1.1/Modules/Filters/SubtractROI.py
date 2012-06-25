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
__author__ = "BioImageXD Project <http://www.bioimagexd.net/>"
__version__ = "$Revision$"
__date__ = "$Date$"

import lib.ProcessingFilter
import itk
import scripting
import lib.ImageOperations
import GUI.GUIBuilder
import vtk

class SubtractROIFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	A filter to subtract ROI from the image data
	"""
	name = "Subtract ROI"
	category = lib.FilterTypes.ROI
	
	def __init__(self):
		"""
		Initialization
		"""        
		lib.ProcessingFilter.ProcessingFilter.__init__(self, (1, 1))
		self.descs = {"ROI": "Region of Interest used in subtraction"}
		self.itkFlag = 1
		self.filterDesc = "Subtracts the average intensity of a ROI from every pixel/voxel of the image.\nInput: Grayscale image\nOutput: Grayscale image"
	
	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""
		return [["Region of Interest", ("ROI",)]]
		
	def getType(self, parameter):
		"""
		Return the type of the parameter
		"""    
		if parameter == "ROI":
			return GUI.GUIBuilder.ROISELECTION
		
	def getDefaultValue(self, parameter):
		"""
		Return the default value of a parameter
		"""     
		if parameter == "ROI":
			n = scripting.visualizer.getRegionsOfInterest()
			if n:
				return (0, n[0])
			return 0
		
	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute the filter with given inputs and return the output
		"""
		if not lib.ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None

		roi = self.parameters["ROI"][1]
		scripting.wantWholeDataset = 1
		imagedata = self.getInput(1)
		imagedata.SetUpdateExtent(imagedata.GetWholeExtent())
		imagedata.Update()

		itkOrig = self.convertVTKtoITK(imagedata)
		itkOrig.DisconnectPipeline()

		mx, my, mz = self.dataUnit.getDimensions()
		n, maskImage = lib.ImageOperations.getMaskFromROIs([roi], mx, my, mz)
		itkLabel = self.convertVTKtoITK(maskImage)
		itkLabel = self.castITKImage(itkLabel, itkOrig)
		#vtkToItk2 = itk.VTKImageToImageFilter.IUC3.New()
		#vtkToItk2.SetInput(maskImage)
		#itkLabel = vtkToItk2.GetOutput()
		#itkLabel.Update()

		labelStats = itk.LabelStatisticsImageFilter[itkOrig, itkLabel].New()
		labelStats.SetInput(0, itkOrig)
		labelStats.SetInput(1, itkLabel)
		labelStats.Update()
		
		avgint = labelStats.GetMean(255)
		print "Subtract from image:",avgint

		shift = vtk.vtkImageShiftScale()
		shift.SetInput(imagedata)
		shift.SetClampOverflow(1)
		shift.SetScale(1)
		shift.SetShift(-avgint)
		
		return shift.GetOutput()
