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
import lib.FilterTypes
import scripting

class ExtractSubsetFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	Created: 04.08.2006, KP
	Description: A filter for cutting the data to a smaller size
	"""     
	name = "Extract a subset"
	category = lib.FilterTypes.FILTERING
	
	def __init__(self):
		"""
		Created: 10.08.2006, KP
		Description: Initialization
		"""        
		lib.ProcessingFilter.ProcessingFilter.__init__(self, (1, 1))
		self.reportGUI = None
		self.measurements = []
		self.vtkfilter = vtk.vtkExtractVOI()
		self.vtkfilter.AddObserver("ProgressEvent", self.updateProgress)
		
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
		return (1, z)
		
		
	def getType(self, parameter):
		"""
		Created: 31.07.2006, KP
		Description: Return the type of the parameter
		"""    
		if parameter == "ROI":
			return GUI.GUIBuilder.ROISELECTION
		if parameter == "UseROI":
			return types.BooleanType
		return GUI.GUIBuilder.SLICE
		
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
		print "VOI=", minx, maxx, miny, maxy, minz, maxz
		imagedata = self.getInput(1)
		#imagedata.SetUpdateExtent(minx,maxx,miny,maxy,minz,maxz)
		imagedata.SetUpdateExtent(imagedata.GetWholeExtent())
		imagedata.Update()
		self.vtkfilter.SetInput(imagedata)
		self.vtkfilter.SetVOI(minx, maxx, miny, maxy, minz, maxz)
		data = self.vtkfilter.GetOutput()

		if minz > 0:
			translate = vtk.vtkImageTranslateExtent()
			translate.SetTranslation((0,0,-minz))
			translate.SetInput(data)
			data = translate.GetOutput()
		
		return  data
