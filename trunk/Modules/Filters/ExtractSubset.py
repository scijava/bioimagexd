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
import types
import GUI.GUIBuilder
import lib.messenger
import lib.FilterTypes
import scripting
import bxdevents

class ExtractSubsetFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	A filter for cutting the data to a smaller size
	"""     
	name = "Extract a subset"
	category = lib.FilterTypes.FILTERING
	
	def __init__(self):
		"""
		Initialization
		"""        
		lib.ProcessingFilter.ProcessingFilter.__init__(self, (1, 1))
		self.reportGUI = None
		self.measurements = []
		self.vtkfilter = vtk.vtkExtractVOI()
		self.vtkfilter.AddObserver("ProgressEvent", lib.messenger.send)
		lib.messenger.connect(self.vtkfilter, 'ProgressEvent', self.updateProgress)
		self.translation = []
		self.descs = {"UseROI": "Use Region of Interest to define resulting region", \
						"ROI": "Region of Interest Used in Cutting", \
						"FirstSlice": "First Slice in Resulting Stack", \
						"LastSlice": "Last Slice in Resulting Stack"}
	
	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""            
		return [["Region of Interest", ("UseROI", "ROI")], ["Slices", ("FirstSlice", "LastSlice")]]
		

	def getRange(self, parameter):
		"""
		Return the range for the parameter
		"""       
		if self.dataUnit:
			x, y, z = self.dataUnit.getDimensions()
		else:
			z = 0
		return (1, z)
		
		
	def getType(self, parameter):
		"""
		Return the type of the parameter
		"""    
		if parameter == "ROI":
			return GUI.GUIBuilder.ROISELECTION
		if parameter == "UseROI":
			return types.BooleanType
		return GUI.GUIBuilder.SLICE
		
	def getDefaultValue(self, parameter):
		"""
		Return the default value of a parameter
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
		
	def onRemove(self):
		"""
		A method called when this filter is removed
		"""
		if self.translation:
			lib.messenger.send(None, bxdevents.TRANSLATE_DATA, (-self.translation[0], -self.translation[1], -self.translation[2]))
		
	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute the filter with given inputs and return the output
		"""            
		if not lib.ProcessingFilter.ProcessingFilter.execute(self, inputs):
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
		maxx -= 1
		maxy -= 1
		scripting.wantWholeDataset=1
		imagedata = self.getInput(1)
		imagedata.SetUpdateExtent(imagedata.GetWholeExtent())
		imagedata.Update()

		# Mask original image
		if self.parameters["UseROI"]:
			mask = lib.ImageOperations.getMaskFromPoints(pts, maxx+1, maxy+1, maxz+1)
			maskFilter = vtk.vtkImageMask()
			maskFilter.SetImageInput(imagedata)
			maskFilter.SetMaskInput(mask)
			imagedata = maskFilter.GetOutput()
			imagedata.Update()
		
		# Extract VOI of original data
		self.vtkfilter.SetInput(imagedata)
		self.vtkfilter.SetVOI(minx, maxx, miny, maxy, minz, maxz)
		data = self.vtkfilter.GetOutput()
		translate = vtk.vtkImageTranslateExtent()
		translate.SetInput(data)
		#print "input data=",data
		translation = [0,0,0]
		if minz > 0:
			translation[2] = -minz
		if minx > 0:
			translation[0] = -minx
		if miny > 0:
			translation[1] = -miny
		newTranslation = translation[:]
		#if self.translation:
		#	dx = self.translation[0]-minx
		#	dy = self.translation[1]-miny
		#	dz = self.translation[2]-minz
		#	newTranslation = [dx,dy,dz]
		self.translation = newTranslation
		
		#lib.messenger.send(None, bxdevents.TRANSLATE_DATA, tuple(self.translation))
		if translation != [0,0,0]:
			translate.SetTranslation(tuple(translation))
			#translate.SetOutputOrigin(0,0,0)
			data = translate.GetOutput()
			data.Update()
			
		reslice = vtk.vtkImageChangeInformation()
		reslice.SetOutputOrigin(0,0,0)
		reslice.SetInput(data)
		data = reslice.GetOutput()
		print "Returning data",data
		return  data
