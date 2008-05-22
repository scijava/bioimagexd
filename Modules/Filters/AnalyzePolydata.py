#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: AnalyzePolydata
 Project: BioImageXD
 Description:

 A module for the imagedata to polydata conversion filter
 
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
import scripting
import types
import GUI.GUIBuilder
import itk
import os
import lib.Particle
import lib.FilterTypes
import GUI.CSVListView
import wx
import vtk
import codecs
import csv
import vtkbxd

class AnalyzePolydataFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	A filter for analyzing polydata
	"""
	name = "Analyze polydata"
	category = lib.FilterTypes.POLYDATA
	level = scripting.COLOR_INTERMEDIATE

	def __init__(self):
		"""
		Initialization
		"""
		self.defaultObjectsFile = u"statistics.csv"
		self.objectsBox = None
		self.timepointData = {}
		self.polyDataSource = None
		self.segmentedSource = None
		self.delayedData = None
		lib.ProcessingFilter.ProcessingFilter.__init__(self,(2,2))
		for i in range(1, 3):
			self.setInputChannel(i, i)
		self.descs = {"PolyDataFile":"Surface file", "ObjectsFile":"Segmented objects file",
			"DistanceToSurface":"Measure distance to surface","InsideSurface":"Analyze whether object is inside the surface"}
			
		self.resultVariables = {"DistanceList":"List of object distances to surface"}
		self.headers = ["Object","Position","Distance to surface (COM)","Distance to surface (All)","Inside surface"]
	def getParameters(self):
		"""
		Returns the parameters for GUI.
		"""
		return [
			["Polydata",( ("PolyDataFile","Select the polydata file to analyze", "*.vtp"),)],
			["Segmented objects",( ("ObjectsFile","Select the objects file to analyze", "*.csv"),)],
			["Analyses",("DistanceToSurface","InsideSurface")],
			
			]

	def getType(self, parameter):
		"""
		Returns the types of parameters for GUI.
		"""
		if parameter in ["PolyDataFile","ObjectsFile"]:
			return GUI.GUIBuilder.FILENAME
		if parameter in ["DistanceToSurface","InsideSurface"]:
			return types.BooleanType
			
			
	def getDefaultValue(self, parameter):
		"""
		Description:
		"""
		if parameter == "PolyDataFile":
			return "surface.pol"
		if parameter == "ObjectsFile":
			return self.defaultObjectsFile
		if parameter in ["DistanceToSurface","InsideSurface"]:
			return True
		return 0

	def getParameterLevel(self, param):
		"""
		Description:
		"""
		return scripting.COLOR_BEGINNER
		
	def onActivateItem(self, listctrl, event, item):
		"""
		An event handler for item activation
		"""
		lib.messenger.send(None,"highlight_object", item+1)
			
	def getGUI(self, parent, taskPanel):
		"""
		Return the GUI for this filter
		"""
		gui = lib.ProcessingFilter.ProcessingFilter.getGUI(self, parent, taskPanel)

		if not self.objectsBox:
			self.objectsBox = GUI.CSVListView.CSVListView(self.gui)
			lib.messenger.connect(self.objectsBox, "item_activated", self.onActivateItem)
			if self.delayedData:
				self.objectsBox.setContents(self.delayedData)
				self.delayedData = None
			else:
				self.objectsBox.setContents([self.headers])
			sizer = wx.BoxSizer(wx.VERTICAL)

			sizer.Add(self.objectsBox, 1)
			box = wx.BoxSizer(wx.HORIZONTAL)

			sizer.Add(box)
			pos = (0, 0)
			item = gui.sizer.FindItemAtPosition(pos)
			if item.IsWindow():
				win = item.GetWindow()
			elif item.IsSizer():
				win = item.GetSizer()
			elif item.IsSpacer():
				win = item.GetSpacer()

			gui.sizer.Detach(win)
			gui.sizer.Add(sizer, (0, 0), flag = wx.EXPAND | wx.ALL)
			gui.sizer.Add(win, (1, 0), flag = wx.EXPAND | wx.ALL)
			self.exportBtn = wx.Button(self.gui, -1, "Export statistics")
			self.exportBtn.Bind(wx.EVT_BUTTON, self.onExportStatistics)
			sizer.AddSpacer((5,5))
			sizer.Add(self.exportBtn)

		return gui

	def onExportStatistics(self, evt):
		"""
		Export the statistics
		"""
		name = self.dataUnit.getName()
		filename = GUI.Dialogs.askSaveAsFileName(self.taskPanel, "Save polydata statistics as", \
													"%s.csv" % name, "CSV File (*.csv)|*.csv")
													
		self.writeStatistics(filename)
		
	def writeStatistics(self, filename):
		"""
		Write the statistics to the given file
		"""
		f = codecs.open(filename, "awb", "utf-8")
		w = csv.writer(f, dialect = "excel", delimiter = ";")
		sources = self.dataUnit.getSourceDataUnits()
		
		names = [x.getName() for x in sources]
		w.writerow(["Surface data analysis for",self.dataUnit.getName(), "source channels:"]+names+[ "timepoint",self.getCurrentTimepoint()])
		w.writerow([])
		

		self.objectsBox.writeOut(w, [self.headers])
		f.close()
		
	def setDataUnit(self, dataUnit):
		"""
		a method to set the dataunit used by this filter
		"""
		lib.ProcessingFilter.ProcessingFilter.setDataUnit(self, dataUnit)
		sourceUnits = dataUnit.getSourceDataUnits()
		tracksFile = None
		for unit in sourceUnits:
			print "Checking",unit
			tracksFileTmp = unit.getSettings().get("StatisticsFile")
			print "Tracksf ile=",tracksFileTmp
		
			if unit.getPolyDataAtTimepoint(0) != None:
				print "Poly data unit=",unit
				self.polyDataSource = unit
			elif tracksFileTmp:
				self.segmentedSource = unit
				print "Segmented source = ",unit
				tracksFile = tracksFileTmp
				
		if tracksFile and os.path.exists(tracksFile):
			self.set("ObjectsFile", tracksFile)
			self.defaultObjectsFile = tracksFile

	def getRange(self, param):
		"""
		Description:
		"""
		return 0,999
		
	def calculateDistancesToSurface(self, timepoint, objects):
		"""
		Calculate the distance to surface for the given set of objects
		"""
	
		if not self.polyDataSource:
			return []
		polydata = self.polyDataSource.getPolyDataAtTimepoint(timepoint)
		imgdata = self.polyDataSource.getTimepoint(timepoint)
		if not polydata:
			return []
		locator = vtk.vtkPointLocator()
		locator.SetDataSet(polydata)
		locator.BuildLocator()
		distances = []
		for object in objects:
			x, y,z  = object.getCenterOfMass()
			xs, ys, zs = imgdata.GetSpacing()
			x*=xs
			y*=ys
			z*=zs
			dist = 0 
			objid = locator.FindClosestPoint(x,y,z)
			x2,y2,z2 = polydata.GetPoint(objid)
			dist = object.distance3D(x,y,z,x2,y2,z2)
			distances.append(dist)
		return distances

	def calculateAverageDistancesToSurface(self, timepoint, objects):
		"""
		Calculate the distance to surface for the given set of objects
		"""
	
		if not self.polyDataSource:
			return []
		polydata = self.polyDataSource.getPolyDataAtTimepoint(timepoint)
		imgdata = self.segmentedSource.getTimepoint(timepoint)
		print "Getting imgdata from",self.segmentedSource
		if not polydata:
			return []
		voxelSizes = self.segmentedSource.getVoxelSize()
		voxelSizes = [x*10000000 for x in voxelSizes]
		print "Setting voxel sizes",voxelSizes
		distanceCalc = vtkbxd.vtkImageLabelDistanceToSurface()
		distanceCalc.SetVoxelSize(voxelSizes)
		distanceCalc.SetInputConnection(0, imgdata.GetProducerPort())
		distanceCalc.SetInputConnection(1, polydata.GetProducerPort())
		print "Calculating average distances"

		distanceCalc.Update()
		distArray = distanceCalc.GetAverageDistanceToSurfaceArray();
		distances = []
		for i in range(1, distArray.GetSize()):
			value = distArray.GetValue(i)
			distances.append(value)
		return distances
		
	def calculateIsInside(self, timepoint, objects):
		"""
		Calculate whether the objects are on the inside of the surface
		"""
	
		if not self.polyDataSource:
			return []
		polydata = self.polyDataSource.getPolyDataAtTimepoint(timepoint)
		imgdata = self.polyDataSource.getTimepoint(timepoint)
		if not polydata:
			return []
		locator = vtk.vtkOBBTree()
		locator.SetDataSet(polydata)
		locator.BuildLocator()
		distances = []
		for object in objects:
			x, y,z  = object.getCenterOfMass()
			x, y,z  = object.getCenterOfMass()
			xs, ys, zs = imgdata.GetSpacing()
			x*=xs
			y*=ys
			z*=zs
			inside = locator.InsideOrOutside([x,y,z])
			if inside == -1:
				distances.append("Yes")
			elif inside == 1:
				distances.append("No")
			else:
				distances.append("n/a")
	
		return distances		
	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute filter in input image and return output image
		"""
		if not lib.ProcessingFilter.ProcessingFilter.execute(self,inputs):
			return None

		inputImage = self.getInput(1)
		
		reader = lib.Particle.ParticleReader(self.parameters["ObjectsFile"], 0)
		objects = reader.read()
		
		timepoint = self.getCurrentTimepoint()
		distances = []
		insides = []
		if self.parameters["DistanceToSurface"]:
			distances = self.calculateDistancesToSurface(timepoint, objects[timepoint])
			avgDistances = self.calculateAverageDistancesToSurface(timepoint, objects[timepoint])
		if self.parameters["InsideSurface"]:
			insides = self.calculateIsInside(timepoint, objects[timepoint])
			
		data = [self.headers]
		self.setResultVariable("DistanceList", distances)
		if timepoint not in self.timepointData:
			for i, object in enumerate(objects[timepoint]):
				x,y,z = object.getCenterOfMass()
				entry = []
				entry.append("#%d"%object.objectNumber())
				entry.append("%d,%d,%d"%(int(x),int(y),int(z)))
				if distances:
					entry.append("%.2f"%distances[i])
				else:
					entry.append("")
				if avgDistances:
					entry.append("%.2f"%avgDistances[i])
				else:
					entry.append("")
				if insides:
					entry.append(insides[i])
				else:
					entry.append("")
				data.append(entry)
			self.timepointData[timepoint] = data
		else:
			data = self.timepointData[timepoint]
		if self.objectsBox:
			self.objectsBox.setContents(data)
		else:
			self.delayedData = data
			
		return inputImage
