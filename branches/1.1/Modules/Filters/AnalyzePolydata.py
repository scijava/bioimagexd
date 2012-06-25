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
import lib.ParticleReader
import lib.FilterTypes
import GUI.CSVListView
import wx
import vtk
import codecs
import csv
import vtkbxd
import Logging

class AnalyzePolydataFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	A filter for analyzing polydata
	"""
	name = "Analyze polydata"
	category = lib.FilterTypes.SEGMENTATIONANALYSE
	level = scripting.COLOR_EXPERIENCED

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
		self.objectData = None
		self.aggrData = None
		lib.ProcessingFilter.ProcessingFilter.__init__(self,(2,2))
		for i in range(1, 3):
			self.setInputChannel(i, i)
		self.itkFlag = 1
		self.descs = {"PolyDataFile":"Surface file", "ObjectsFile":"Segmented objects file", "ResultsFile":"Results file",
			"DistanceToSurface":"Measure distance to surface","InsideSurface":"Analyze whether object is inside the surface"}
			
		self.resultVariables = {"NumObjsOutside":"Number of objects whose center of mass is outside the surface",
		"NumObjsInside":"Number of objects whose center of mass is inside the surface",
		"AvgDistanceCOMtoSurface":"Average distance from all objects' center of mass to surface",
		"AvgDistanceCOMtoSurfaceStdErr":"Std. error of average distance from all objects' center of masses to surface",
		"AvgDistanceCOMtoCellCOM":"Average distance from all objects' center of mass to cell center of mass",
		"AvgDistanceCOMtoCellCOMStdErr":"Std. error of average distance from all objects' center of mass to cell center of mass",
		"NumVoxelsInside":"Number of voxels inside the surface",
		"NumVoxelsOutside":"Number of voxels outside the surface",
		"PercentageVoxelsInside":"Avg. percentage of voxels inside the surface",
		"PercentageVoxelsInsideStdErr":"Std. error of average percentage of voxels inside the surface",
		"AvgDistanceToSurface":"Average distance to surface from each voxel in the objects",
		"AvgDistanceToSurfaceStdErr":"Std. error of average distance to surface from each voxel in the objects",
		"AvgDistanceToCellCOM":"Average distance to cell COM from each voxel in the objects",
		"AvgDistanceToCellCOMStdErr":"Std. error of average distance to cell COM from each voxel in the objects"}

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
		self.writeHeaders = ["Obj#","COM X", "COM Y", "COM Z", "Dist.(COM-surface)", "Avg.Dist.(voxels-surface)", "Avg.Dist.(voxels-surface) Std.Err.", "Dist.(Obj COM-Cell COM)", "Avg.Dist.(Voxels-Cell COM)", "Avg.Dist.(Voxels-Cell COM) Std.Err.", "Vox.count(inside)", "Vox.count(outside)","COM inside surface"]

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
		self.filterDesc = "Analyzes location of segmented objects in respect of polydata surface, to quantify for instance cellular internalization\nInputs: Polydata image and label image\nOutput: Results (polydata input for pipeline)"
		
	def getParameters(self):
		"""
		Returns the parameters for GUI.
		"""
		return [
#			["Polydata",(("PolyDataFile","Select the polydata file to analyze", "*.vtp"),)],
#			["Segmented objects",(("ObjectsFile","Select the objects file to analyze", "*.csv"),)],
			["Settings",("DistanceToSurface","InsideSurface")],
			["Results", (("ResultsFile","File to write results to", "*.csv"),)]
			]

	def getType(self, parameter):
		"""
		Returns the types of parameters for GUI.
		"""
		if parameter in ["PolyDataFile","ObjectsFile"]:
			return GUI.GUIBuilder.FILENAME
		if parameter == "ResultsFile":
			return GUI.GUIBuilder.SAVEFILE
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
		if parameter == "ResultsFile":
			return "Polydata.csv"
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
				aggrData = [["Quantity", "Value"],
							[self.aggregateHeaders[0], "0"],
							[self.aggregateHeaders[1], "0"],
							[self.aggregateHeaders[2], u"0.000\u00B10.000 \u03BCm"],
							[self.aggregateHeaders[3], u"0.000\u00B10.000 \u03BCm"],
							[self.aggregateHeaders[4], "0"],
							[self.aggregateHeaders[5], "0"],
							[self.aggregateHeaders[6], u"0.00\u00B10.00 %"],
							[self.aggregateHeaders[7], u"0.000\u00B10.000 \u03BCm"],
							[self.aggregateHeaders[8], u"0.000\u00B10.000 \u03BCm"]]
				self.aggregateBox.setContents(aggrData)
				self.aggregateBox.SetColumnWidth(0, 150)
				self.aggregateBox.SetColumnWidth(1, 200)

			self.exportBtn = wx.Button(self.gui, -1, "Export statistics")
			self.exportBtn.Bind(wx.EVT_BUTTON, self.onExportStatistics)
			sizer = wx.BoxSizer(wx.VERTICAL)
			sizer.Add(self.objectsBox, 1)
			sizer.Add(self.aggregateBox, 1)
			box = wx.BoxSizer(wx.HORIZONTAL)
			sizer.Add(box)
			sizer.AddSpacer((5,5))
			sizer.Add(self.exportBtn)
			
			pos = (0, 0)
			item = gui.sizer.FindItemAtPosition(pos)
			if item.IsWindow():
				win = item.GetWindow()  
			elif item.IsSizer():
				win = item.GetSizer()
			elif item.IsSpacer():
				win = item.GetSpacer()

			resultSizer = win.GetItem(0).GetSizer().FindItemAtPosition((4,0)).GetSizer()
			resultSizer.Add(sizer)

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
		self.writeToFile(filename, self.dataUnit)
		#f = codecs.open(filename, "ab", "utf-8")
		#w = csv.writer(f, dialect = "excel", delimiter = ";")
		#sources = self.dataUnit.getSourceDataUnits()
		
		#names = [x.getName() for x in sources]
		#w.writerow(["Surface data analysis for",self.dataUnit.getName(), "source channels:"]+names+[ "timepoint",self.getCurrentTimepoint()])
		#w.writerow([])
		
		#self.objectsBox.writeOut(w, [self.headers])
		#f.close()

	def writeOutput(self, dataUnit, timepoint):
		"""
		Write the output of this module during the processing
		"""
		fileroot = self.parameters["ResultsFile"]
		if not self.parameters["ResultsFile"]:
			fileroot = "polydata.csv"
		fileroot = fileroot.split(".")
		fileroot = ".".join(fileroot[:-1])
		dircomp = os.path.dirname(fileroot)
		if not dircomp:
			bxddir = dataUnit.getOutputDirectory()
			fileroot = os.path.join(bxddir, fileroot)
		filename = "%s.csv" % fileroot
		self.writeToFile(filename, dataUnit, timepoint)

	def writeToFile(self, filename, dataUnit, timepoint = -1):
		"""
		write the objects from a given timepoint to file
		"""
		f = codecs.open(filename, "ab", "latin1")
		Logging.info("Saving polydata statistics to file %s"%filename, kw="processing")
		
		w = csv.writer(f, dialect = "excel", delimiter = ";")

		if timepoint >= 0:
			w.writerow(["Timepoint %d" % timepoint])
		
		for row in self.objectData:
			w.writerow(row)
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

	def calculateDistancesToSurface(self, polydata, imgdata, objects, surfaceCOM):
		"""
		Calculate the distance to surface for the given set of objects
		"""	
		if not polydata:
			print "Failed to read polydata"
			return [], []
		locator = vtk.vtkPointLocator()
		locator.SetDataSet(polydata)
		locator.BuildLocator()
		distances = []
		comDistances = []
		cx, cy, cz = surfaceCOM
		objVoxelSizes = self.segmentedSource.getVoxelSize()
		objVoxelSizes = [x*1000000 for x in objVoxelSizes]
		surfVoxelSizes = self.polyDataSource.getVoxelSize()
		surfVoxelSizes = [x*1000000 for x in surfVoxelSizes]
		cxReal = cx * surfVoxelSizes[0]
		cyReal = cy * surfVoxelSizes[1]
		czReal = cz * surfVoxelSizes[2]
		xs, ys, zs = imgdata.GetSpacing()

		for obj in objects:
			x, y, z  = obj.getCenterOfMass()

			xReal = x * objVoxelSizes[0]
			yReal = y * objVoxelSizes[1]
			zReal = z * objVoxelSizes[2]
			comDistances.append(obj.distance3D(xReal,yReal,zReal,cxReal,cyReal,czReal))
			xPoint = x * xs
			yPoint = y * ys
			zPoint = z * zs
			dist = 0 
			objid = locator.FindClosestPoint((xPoint, yPoint, zPoint))
			x2,y2,z2 = polydata.GetPoint(objid)
			x2 /= xs
			y2 /= ys
			z2 /= zs
			pos1 = x,y,z
			pos2 = x2,y2,z2
			x, y, z = [pos1[i] * objVoxelSizes[i] for i in range(0,3)]
			x2, y2, z2 = [pos2[i] * surfVoxelSizes[i] for i in range(0,3)]
			
			dist = obj.distance3D(x,y,z,x2,y2,z2)
			distances.append(dist)
			
		return distances, comDistances

	def calculateAverageDistancesToSurface(self, polydata, imgdata, objects, centerOfMass):
		"""
		Calculate the distance to surface for the given set of objects
		"""
		if not polydata:
			return [], []
		locator = vtk.vtkOBBTree()
		locator.SetDataSet(polydata)
		locator.BuildLocator()
		voxelSizes = self.segmentedSource.getVoxelSize()
		voxelSizes = [x*1000000 for x in voxelSizes]
		print "Setting voxel sizes",voxelSizes
		distanceCalc = vtkbxd.vtkImageLabelDistanceToSurface()
		distanceCalc.SetVoxelSize(voxelSizes)
		distanceCalc.SetMeasurePoint(centerOfMass)
		distanceCalc.SetInputConnection(0, imgdata.GetProducerPort())
		distanceCalc.SetInputConnection(1, polydata.GetProducerPort())
		distanceCalc.SetSurfaceLocator(locator)
		print "Calculating average distances"

		distanceCalc.Update()
		distArray = distanceCalc.GetAverageDistanceToSurfaceArray()
		distStdErrArray = distanceCalc.GetAverageDistanceToSurfaceStdErrArray()
		distances = []
		distancesStdErr = []
		comDistances = []
		comDistancesStdErr = []
		inOut = []
		for i in range(1, distArray.GetSize()):
			value = distArray.GetValue(i)
			distances.append(value)
			value = distStdErrArray.GetValue(i)
			distancesStdErr.append(value)

		distArray = distanceCalc.GetAverageDistanceToPointArray()
		distStdErrArray = distanceCalc.GetAverageDistanceToPointStdErrArray()
		insideArray = distanceCalc.GetInsideCountArray()
		outsideArray = distanceCalc.GetOutsideCountArray()

		for i in range(1, distArray.GetSize()):
			value = distArray.GetValue(i)
			comDistances.append(value)
			value = distStdErrArray.GetValue(i)
			comDistancesStdErr.append(value)
			inOut.append((insideArray.GetValue(i), outsideArray.GetValue(i)))
			
		return comDistances, distances, inOut, comDistancesStdErr, distancesStdErr
		
	def calculateIsInside(self, polydata, imgdata, objects):
		"""
		Calculate whether the objects are on the inside of the surface
		"""
		if not polydata:
			return []
		
		locator = vtk.vtkOBBTree()
		locator.SetDataSet(polydata)
		locator.BuildLocator()
		distances = []
		xs, ys, zs = imgdata.GetSpacing()

		for object in objects:
			x, y, z  = object.getCenterOfMass()
			x *= xs
			y *= ys
			z *= zs

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
		
		timepoint = self.getCurrentTimepoint()
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

		# Read objects first from users input file, then from objects
		# StatisticsFile, then from object csv found in file's directory,
		# and finally create again from file

		#particleFile = ""
		#objectsFile = self.parameters["ObjectsFile"]
		#if os.path.exists(objectsFile):
		#	particleFile = objectsFile
		#else:
		particleFile = os.path.basename(self.segmentedSource.getSettings().get("StatisticsFile"))

		#if not os.path.exists(particleFile):
		path = self.segmentedSource.getDataSource().path
		#for fileName in os.listdir(path):
			#if ".csv" in fileName:
				#particleFile = os.path.join(path,fileName)
		particleFile = os.path.join(path, particleFile)

		if os.path.exists(particleFile):
			reader = lib.ParticleReader.ParticleReader(particleFile, 0)
			objects = reader.read()
		else: # Do AnalyzeObjects
			pass
		
		distances = []
		insides = []
		if self.parameters["DistanceToSurface"]:
			objComDistToSurf, objComDistToSurfCom = self.calculateDistancesToSurface(polydata, imgdata, objects[timepoint], centerOfMass)
			avgDistToCom, avgDistToSurf, objInsideCount, avgDistToComStdErr, avgDistToSurfStdErr = self.calculateAverageDistancesToSurface(polydata, self.segmentedSource.getTimepoint(timepoint), objects[timepoint], centerOfMass)
		else:
			objComDistToSurf = []
			objComDistToSurfCom = []
			avgDistToSurf = []
			avgDistToSurfStdErr = []
			avgDistToCom = []
			avgDistToComStdErr = []
			objInsideCount = []
			for i in range(len(objects[timepoint])):
				objComDistToSurf.append(0.0)
				objComDistToSurfCom.append(0.0)
				avgDistToSurf.append(0.0)
				avgDistToSurfStdErr.append(0.0)
				avgDistToCom.append(0.0)
				avgDistToComStdErr.append(0.0)
				objInsideCount.append((0,0))

		if self.parameters["InsideSurface"]:
			insides = self.calculateIsInside(polydata, imgdata, objects[timepoint])
			
		#print "# of objs=", len(objects[timepoint])
		#print "# of dists=",len(objComDistToSurf), len(avgDistToSurf), len(objComDistToSurfCom), len(avgDistToCom)
		data = [self.headers]
		writeData = [self.writeHeaders]
		aggrData = [["Quantity", "Value"]]
		insideCount = 0
		outsideCount = 0
		insideCountVox = 0
		outsideCountVox = 0
		percInsideList = []

		if timepoint not in self.timepointData or True: # Fixed to work in BBA
			for i, object in enumerate(objects[timepoint]):
				x,y,z = object.getCenterOfMass()
				entry = []
				writeEntry = []
				entry.append("#%d"%object.objectNumber()) # 1
				entry.append("%d,%d,%d"%(int(round(x)),int(round(y)),int(round(z)))) # 2
				entry.append(u"%.3f \u03BCm"%objComDistToSurf[i]) # 3
				entry.append(u"%.3f\u00B1%.3f \u03BCm"%(avgDistToSurf[i],avgDistToSurfStdErr[i])) # 4
				entry.append(u"%.3f \u03BCm"%objComDistToSurfCom[i]) # 5
				entry.append(u"%.3f\u00B1%.3f \u03BCm"%(avgDistToCom[i],avgDistToComStdErr[i])) # 6
				entry.append("%d"%objInsideCount[i][0])
				entry.append("%d"%objInsideCount[i][1])

				writeEntry.append("%d"%object.objectNumber()) # 1
				writeEntry.append("%d"%int(round(x))) # 2
				writeEntry.append("%d"%int(round(y))) # 2
				writeEntry.append("%d"%int(round(z))) # 2
				writeEntry.append("%.3f"%objComDistToSurf[i]) # 3
				writeEntry.append("%.3f"%avgDistToSurf[i]) # 4
				writeEntry.append("%.3f"%avgDistToSurfStdErr[i]) # 4
				writeEntry.append("%.3f"%objComDistToSurfCom[i]) # 5
				writeEntry.append("%.3f"%avgDistToCom[i]) # 6
				writeEntry.append("%.3f"%avgDistToComStdErr[i]) # 6
				writeEntry.append("%d"%objInsideCount[i][0])
				writeEntry.append("%d"%objInsideCount[i][1])
				objCount = float(objInsideCount[i][0]+objInsideCount[i][1])
				if objCount != 0.0:
					percInsideList.append(objInsideCount[i][0]/objCount)
				else:
					percInsideList.append(0.0)
				
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
					writeEntry.append(isIn)
				else:
					entry.append("")
					writeEntry.append("")
				data.append(entry)
				writeData.append(writeEntry)
			
			percInside, percInsideStd, percInsideStdErr = lib.Math.meanstdeverr(percInsideList)
			entry = []
			avgDistComToSurf, avgDistComToSurfStd, avgDistComToSurfStdErr = lib.Math.meanstdeverr(objComDistToSurf)
			avgDistComToCOM, avgDistComToCOMStd, avgDistComToCOMStdErr = lib.Math.meanstdeverr(objComDistToSurfCom)
			avgDistToSurface, avgDistToSurfaceStd, avgDistToSurfaceStdErr = lib.Math.meanstdeverr(avgDistToSurf)
			avgDistToCellCOM, avgDistToCellCOMStd, avgDistToCellCOMStdErr = lib.Math.meanstdeverr(avgDistToCom)
			entry.append("%d"%outsideCount)
			entry.append("%d"%insideCount)
			entry.append(u"%.3f\u00B1%.3f \u03BCm"%(avgDistComToSurf,avgDistComToSurfStdErr))
			entry.append(u"%.3f\u00B1%.3f \u03BCm"%(avgDistComToCOM, avgDistComToCOMStdErr))
			entry.append("%d"%insideCountVox)
			entry.append("%d"%outsideCountVox)
			entry.append(u"%.2f\u00B1%.2f "%(percInside*100, percInsideStdErr*100) + "%")
			entry.append(u"%.3f\u00B1%.3f \u03BCm"%(avgDistToSurface, avgDistToSurfaceStdErr))
			entry.append(u"%.3f\u00B1%.3f \u03BCm"%(avgDistToCellCOM, avgDistToCellCOMStdErr))

			for i in range(len(entry)):
				aggrData += [[self.aggregateHeaders[i], entry[i]]]
			
			self.setResultVariable("NumObjsOutside", outsideCount)
			self.setResultVariable("NumObjsInside", insideCount)
			self.setResultVariable("AvgDistanceCOMtoSurface", avgDistComToSurf)
			self.setResultVariable("AvgDistanceCOMtoSurfaceStdErr", avgDistComToSurfStdErr)
			self.setResultVariable("AvgDistanceCOMtoCellCOM", avgDistComToCOM)
			self.setResultVariable("AvgDistanceCOMtoCellCOMStdErr", avgDistComToCOMStdErr)
			self.setResultVariable("NumVoxelsInside", insideCountVox)
			self.setResultVariable("NumVoxelsOutside", outsideCountVox)
			self.setResultVariable("PercentageVoxelsInside", percInside)
			self.setResultVariable("PercentageVoxelsInsideStdErr", percInsideStdErr)
			self.setResultVariable("AvgDistanceToSurface", avgDistToSurface)
			self.setResultVariable("AvgDistanceToSurfaceStdErr", avgDistToSurfaceStdErr)
			self.setResultVariable("AvgDistanceToCellCOM", avgDistToCellCOM)
			self.setResultVariable("AvgDistanceToCellCOMStdErr", avgDistToCellCOMStdErr)
			self.timepointData[timepoint] = data, aggrData
			
		else:
			data, aggrData = self.timepointData[timepoint]

		self.objectData = writeData
		self.aggrData = aggrData
		
		if self.objectsBox:
			self.objectsBox.setContents(data)
			self.aggregateBox.setContents(aggrData)
			self.aggregateBox.SetColumnWidth(0, 150)
			self.aggregateBox.SetColumnWidth(1, 200)
		else:
			self.delayedData = data, aggrData
			
		return inputImage
