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
import lib.Math
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
		self.itkFlag = 1
		self.descs = {"PolyDataFile":"Surface file", "ObjectsFile":"Segmented objects file",
			"DistanceToSurface":"Measure distance to surface","InsideSurface":"Analyze whether object is inside the surface"}
			
		self.resultVariables = {"NumObjsOutside":"Number of objects whose center of mass is outside the surface",
		"NumObjsInside":"Number of objects whose center of mass is inside the surface",
		"AvgDistanceCOMtoSurface":"Average distance from all objects' center of mass to surface",
		"AvgDistanceCOMtoCellCOM":"Average distance from all objects' center of mass to cell center of mass",
		"NumVoxelsInside":"Number of voxels inside the surface",
		"NumVoxelsOutside":"Number of voxels outside the surface",
		"PercentageVoxelsInside":"Avg. percentage of voxels inside the surface",
		"AvgDistanceToSurface":"Average distance to surface from each voxel in the objects",
		"AvgDistanceToCellCOM":"Average distance to cell COM from each voxel in the objects"}

		self.headers = ["Object","Position","Dist.to surface (COM)","Dist.to surface (Voxels)","Dist.to Cell COM (COM)","Dist.to Cell COM (Voxels)","# of voxels inside", "# of voxels outside","COM Inside surface"]
		self.aggregateHeaders = ["COMs outside", "COMs inside","Avg.COM dist.to surface","Avg.COM dist.to Cell COM","# of voxels inside", "# of voxels outside","Avg. % of voxels inside", "Avg. of all-voxel-distance to surface","Avg. of all-voxel-distance to Cell COM"]
		
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
			
	def getInputName(self, n):
		"""
		Return the name of the input #n
		"""			 
		if n == 1: return "Polydata image"
		return "Segmented objects" 

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
			self.aggregateBox = GUI.CSVListView.CSVListView(self.gui)
			lib.messenger.connect(self.objectsBox, "item_activated", self.onActivateItem)
			if self.delayedData:
				data, aggrData = self.delayedData
				self.objectsBox.setContents(data)
				self.aggregateBox.setContents(aggrData)
				self.delayedData = None
			else:
				self.objectsBox.setContents([self.headers])
			sizer = wx.BoxSizer(wx.VERTICAL)

			sizer.Add(self.objectsBox, 1)
			sizer.Add(self.aggregateBox, 1)
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
		# Bugi BXC-tiedostosta luetuissa tiedoissa, katso vaikka seuraava
		# tulostus
		sourceUnits = self.dataUnit.getSourceDataUnits()
		for unit in sourceUnits:
			print "Checking",unit, unit.getSettings()
			tracksFileTmp = unit.getSettings().get("StatisticsFile")
			print "Tracks File=",tracksFileTmp

		#self.determineDataSources()
		
	#def determineDataSources(self):
	#	"""
	#	"""
	#	if self.polyDataSource: return

	#	sourceUnits = self.dataUnit.getSourceDataUnits()
	#	tracksFile = None
	#	for unit in sourceUnits:
	#		print "Checking",unit, unit.getSettings()
	#		tracksFileTmp = unit.getSettings().get("StatisticsFile")
	#		print "Tracks File=",tracksFileTmp
		
	#		if unit.getPolyDataAtTimepoint(0) != None:
	#			print "Poly data unit=",unit
	#			self.polyDataSource = unit
	#		elif tracksFileTmp:
	#			self.segmentedSource = unit
	#			print "Segmented source = ",unit
	#			tracksFile = tracksFileTmp

		#if tracksFile and os.path.exists(tracksFile):
		#	print "Setting objectsfile to",tracksFile
		#	self.set("ObjectsFile", tracksFile)
		#	self.defaultObjectsFile = tracksFile

	def getRange(self, param):
		"""
		Description:
		"""
		return 0,999
		
	def calculateDistancesToSurface(self, polydata, imgdata, objects, surfaceCOM):
		"""
		Calculate the distance to surface for the given set of objects
		"""	
		#if not self.polyDataSource:
		#	raise "No polydata source"
		#	return [], []
		#polydata = self.polyDataSource.getPolyDataAtTimepoint(timepoint)
		#imgdata = self.polyDataSource.getTimepoint(timepoint)
		if not polydata:
			print "Failed to read polydata"
			return [], []
		locator = vtk.vtkPointLocator()
		locator.SetDataSet(polydata)
		locator.BuildLocator()
		distances = []
		comDistances = []
		cx, cy, cz = surfaceCOM
		voxelSizes = self.segmentedSource.getVoxelSize()
		voxelSizes = [x*10000000 for x in voxelSizes]
		
		for obj in objects:
			x, y,z  = obj.getCenterOfMass()
			comDistances.append(obj.distance3D(x,y,z, cx, cy, cz))
			xs, ys, zs = imgdata.GetSpacing()
			x*=xs
			y*=ys
			z*=zs
			dist = 0 
			objid = locator.FindClosestPoint(x,y,z)
			x2,y2,z2 = polydata.GetPoint(objid)
			x/=xs
			y/=ys
			z/=zs
			x2/=xs
			y2/=ys
			z2/=zs
			pos1 = x,y,z
			pos2 = x2,y2,z2
			x, y, z = [pos1[i]*voxelSizes[i] for i in range(0,3)]
			x2, y2, z2 = [pos2[i]*voxelSizes[i] for i in range(0,3)]
			
			dist = obj.distance3D(x,y,z,x2,y2,z2)
			distances.append(dist)
			
		return distances, comDistances

	def calculateAverageDistancesToSurface(self, polydata, imgdata, objects, centerOfMass):
		"""
		Calculate the distance to surface for the given set of objects
		"""
		#if not self.polyDataSource:
		#	raise "No polydata source"
		#	return [], []

		#polydata = self.polyDataSource.getPolyDataAtTimepoint(timepoint)
		#imgdata = self.segmentedSource.getTimepoint(timepoint)
		#print "Getting imgdata from",self.segmentedSource
		if not polydata:
			return [], []
		locator = vtk.vtkOBBTree()
		locator.SetDataSet(polydata)
		locator.BuildLocator()
		voxelSizes = self.segmentedSource.getVoxelSize()
		voxelSizes = [x*10000000 for x in voxelSizes]
		print "Setting voxel sizes",voxelSizes
		distanceCalc = vtkbxd.vtkImageLabelDistanceToSurface()
		distanceCalc.SetVoxelSize(voxelSizes)
		distanceCalc.SetMeasurePoint(centerOfMass)
		distanceCalc.SetInputConnection(0, imgdata.GetProducerPort())
		distanceCalc.SetInputConnection(1, polydata.GetProducerPort())
		distanceCalc.SetSurfaceLocator(locator)
		print "Calculating average distances"

		distanceCalc.Update()
		distArray = distanceCalc.GetAverageDistanceToSurfaceArray();
		distances = []
		comDistances = []
		inOut=[]
		for i in range(1, distArray.GetSize()):
			value = distArray.GetValue(i)
			distances.append(value)
		
		distArray = distanceCalc.GetAverageDistanceToPointArray();
		insideArray = distanceCalc.GetInsideCountArray();
		outsideArray = distanceCalc.GetOutsideCountArray();
		for i in range(1, distArray.GetSize()):
			value = distArray.GetValue(i)
			comDistances.append(value)
			inOut.append((insideArray.GetValue(i), outsideArray.GetValue(i)))
			
		return comDistances, distances, inOut
		
	def calculateIsInside(self, polydata, imgdata, objects):
		"""
		Calculate whether the objects are on the inside of the surface
		"""
		#if not self.polyDataSource:
		#	return []
		#polydata = self.polyDataSource.getPolyDataAtTimepoint(timepoint)
		#imgdata = self.polyDataSource.getTimepoint(timepoint)
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
				distances.append(True)
			elif inside == 1:
				distances.append(False)
			else:
				distances.append(None)
	
		return distances
	

	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute filter in input image and return output image
		"""
		if not lib.ProcessingFilter.ProcessingFilter.execute(self,inputs):
			return None
		
		#self.determineDataSources()
		timepoint = self.getCurrentTimepoint()
		#if not self.polyDataSource or not self.segmentedSource:
		self.polyDataSource = self.getInputDataUnit(1)
		self.segmentedSource = self.getInputDataUnit(2)
		inputImage = self.getInput(1)
		print "Calculating cell COM"

		if self.polyDataSource.dataSource:
			imgdata = self.polyDataSource.getTimepoint(timepoint)
			polydata = self.polyDataSource.getPolyDataAtTimepoint(timepoint)
		else: # If from pipeline
			imgdata = inputImage
			polydata = self.getPolyDataInput(1)
		cellImage = self.convertVTKtoITK(imgdata)
		labelShape = itk.LabelShapeImageFilter[cellImage].New()
		labelShape.SetInput(cellImage)
		labelShape.Update()
		
		centerOfMassObj = labelShape.GetCenterOfGravity(255)
		centerOfMass = [centerOfMassObj.GetElement(i) for i in range(0,3)]
		print "Center of mass=",centerOfMass

		# Read objects first from users input file, then from polydata objects
		# StatisticsFile, then from csv found in polydata file's directory,
		# and finally create again from polydata
		particleFile = ""
		objectsFile = self.parameters["ObjectsFile"]
		if os.path.exists(objectsFile):
			particleFile = objectsFile
		else:
			particleFile = self.segmentedSource.getSettings().get("StatisticsFile")

		if particleFile != "":
			reader = lib.Particle.ParticleReader(particleFile, 0)
			objects = reader.read()
		else:
			pass # This need to be implemented
		
		distances = []
		insides = []
		if self.parameters["DistanceToSurface"]:
			objComDistToSurf, objComToSurfComDistances = self.calculateDistancesToSurface(polydata, imgdata, objects[timepoint], centerOfMass)
			avgDistToCom, avgDistToSurf,objInsideCount = self.calculateAverageDistancesToSurface(polydata, self.segmentedSource.getTimepoint(timepoint), objects[timepoint], centerOfMass)
		if self.parameters["InsideSurface"]:
			insides = self.calculateIsInside(polydata, imgdata, objects[timepoint])
			
		# Calculated statistics:
		# 1"Object"						The Object number
		# 2"Position"					The object COM
		# 3"Dist.to surface (COM)"		The distance from object COM to surface
		# 4"Dist.to surface (Voxels)"	The average distance from object voxels to surface
		# 5"Dist.to Cell COM (COM)"		The distance from object COM to cell surface COM
		# 6"Dist.to Cell COM (Voxels)"	The avg. distance from each voxel in the object to the cell surface COM
		# 7"# of voxels inside"			Number of voxels in obj that are inside the cell surface
		# 8"# of voxels outside"			Number of voxels in obj that are outside the cell surface
		# 9"COM Inside surface"			Yes/No the object's center of mass is inside the surface
		
		self.headers = ["Obj#","Pos", "Dist.(COM-surface)","Avg.Dist.(voxels-surface)","Dist.(Obj COM-Cell COM)", "Avg.Dist.(Voxels-Cell COM)","Vox.count(inside)", "Vox.count(outside)","COM inside surface"]

		# "COMs outside"				Number of objects with center of mass outside the surface
		# "COMs inside"					Number of objects with center of mass inside the surface
		# "Avg.COM dist.to surface"		Average distance from object COM to the surface
		# "Avg.COM dist.to Cell COM"	Average distance from object COM to Cell COM
		# "# of voxels inside"			Number of voxels inside the surface in total
		# "# of voxels outside"			Number of voxels outside the surface in total
		# "Avg. % of voxels inside"		Average of the percentages of object voxels that are inside
		# "Avg. of all-voxel-distance to surface",		Average of the average distances from each object's each voxel to the cell surface
		# "Avg. of all-voxel-distance to Cell COM"		Average of the average distances from each object's each voxel to the cell COM

		self.aggregateHeaders = ["COMs outside", "COMs inside","Avg.Dist.(COM-surface)","Avg.Dist.(COM-Cell COM)","# of voxels inside", "# of voxels outside","Avg. % of voxels inside", "Avg. of all-voxel-distance to surface","Avg. of all-voxel-distance to Cell COM"]
		
		
		print "# of objs=", len(objects[timepoint])
		print "# of dists=",len(objComDistToSurf), len(avgDistToSurf), len(objComToSurfComDistances), len(avgDistToCom)
		data = [self.headers]
		aggrData = [self.aggregateHeaders]
#		self.setResultVariable("DistanceList", distances)
		insideCount = 0
		outsideCount = 0
		insideCountVox = 0
		outsideCountVox = 0
		percInside = 0
		percInsideCount = 0
		if timepoint not in self.timepointData or True: # Fixed to work in BBA
			for i, object in enumerate(objects[timepoint]):
				x,y,z = object.getCenterOfMass()
				entry = []
				entry.append("#%d"%object.objectNumber()) # 1
				entry.append("%d,%d,%d"%(int(x),int(y),int(z))) # 2
				entry.append("%.2f"%objComDistToSurf[i]) # 3
				entry.append("%.2f"%avgDistToSurf[i]) # 4
				entry.append("%.2f"%objComToSurfComDistances[i]) # 5
				entry.append("%.2f"%avgDistToCom[i]) # 6
				entry.append("%d"%objInsideCount[i][0])
				entry.append("%d"%objInsideCount[i][1])
				
				percInside += objInsideCount[i][0]/float(objInsideCount[i][0]+objInsideCount[i][1])
				percInsideCount += 1
				
				insideCountVox += objInsideCount[i][0]
				outsideCountVox += objInsideCount[i][1]
				
				if insides:
					isIn="n/a"
					if insides[i]==True: 
						isIn="Yes"
						insideCount += 1
					elif insides[i]==False: 
						isIn="No"
						outsideCount += 1
					entry.append(isIn)
				else:
					entry.append("")
				data.append(entry)
			
			percInside /= percInsideCount
			entry = []
			avgDistanceComToSurf = lib.Math.averageValue(objComDistToSurf)
			avgDistanceComToCOM = lib.Math.averageValue(objComToSurfComDistances)
			avgDistToSurface = lib.Math.averageValue(avgDistToSurf)
			avgDistToCellCOM = lib.Math.averageValue(avgDistToCom)
			entry.append("%d"%outsideCount)
			entry.append("%d"%insideCount)
			entry.append("%.2f"%avgDistanceComToSurf)
			entry.append("%.2f"%avgDistanceComToCOM)
			entry.append("%d"%insideCountVox)
			entry.append("%d"%outsideCountVox)
			entry.append("%.2f%%"%(percInside*100))
			entry.append("%.2f"%avgDistToSurface)
			entry.append("%.2f"%avgDistToCellCOM)
			aggrData.append(entry)
			self.setResultVariable("NumObjsOutside", outsideCount)
			self.setResultVariable("NumObjsInside", insideCount)
			self.setResultVariable("AvgDistanceCOMtoSurface", avgDistanceComToSurf)
			self.setResultVariable("AvgDistanceCOMtoCellCOM", avgDistanceComToCOM)
			self.setResultVariable("NumVoxelsInside", insideCountVox)
			self.setResultVariable("NumVoxelsOutside", outsideCountVox)
			self.setResultVariable("PercentageVoxelsInside", percInside)
			self.setResultVariable("AvgDistanceToSurface", avgDistToSurface)
			self.setResultVariable("AvgDistanceToCellCOM", avgDistToCellCOM)
			self.timepointData[timepoint] = data, aggrData
			
		else:
			data, aggrData = self.timepointData[timepoint]
		if self.objectsBox:
			self.objectsBox.setContents(data)
			self.aggregateBox.setContents(aggrData)
		else:
			self.delayedData = data, aggrData
			
		return inputImage
