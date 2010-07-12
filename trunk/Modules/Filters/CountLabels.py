#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: CountLabels.py
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
import vtkbxd
import math
import codecs
import csv
import lib.Math

class CountLabelsFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	A filter for analyzing polydata
	"""
	name = "Object colocalization"
	category = lib.FilterTypes.COLOCALIZATION
	level = scripting.COLOR_INTERMEDIATE

	def __init__(self, inputs = (2,2)):
		"""
		Initialization
		"""
		self.defaultObjectsFile = u"statistics.csv"
		self.objectsBox = None
		self.timepointData = {}
		self.polyDataSource = None
		self.segmentedSource = None
		self.delayedData = None
		self.oldTimepoint = -1
		lib.ProcessingFilter.ProcessingFilter.__init__(self, inputs)
		self.descs = {}
		self.items = {}
		self.aggregateData = []
		self.centersOfMassList = []
		self.objects = None
		self.countCounts = {}
		self.tracksFile = None
		self.resultVariables = {"ObjectCount":"Number of background objects","ColocCount":"Number of colocalizing (foreground) objects",
								"FgToBgColoc":"Percent of colocalizing objects that are colocalized","BgToFgColoc":"Percent of background objects that are colocalized",
								"PercentOfObjectVoxelsColocalized":"Percentage of voxels in foreground objects that are colocalized with background"}
		self.headers = ["Background object","# of objects inside", "% of voxels colocalized"]
		self.aggregateHeaders = ["Bg#","Fg#","Coloc % of fg voxels","Coloc % (bg)","Coloc % (fg)",u"Mean \u00B1 SD (fg objs in bg)", "Mode (fg objs in bg)"]
		
	def getParameters(self):
		"""
		Returns the parameters for GUI.
		"""
		return [
			]

	def getType(self, parameter):
		"""
		Returns the types of parameters for GUI.
		"""
		if parameter in ["DistanceToSurface","InsideSurface"]:
			return types.BooleanType
			
			
	def getDefaultValue(self, parameter):
		"""
		Description:
		"""
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
		if len(self.centersOfMassList) > item:
			print "Showing center of mass=",self.centersOfMassList[item]
			centerofmass = self.centersOfMassList[item]
			x, y, z = centerofmass
			lib.messenger.send(None, "show_centerofmass", item, centerofmass)
			lib.messenger.send(None, "zslice_changed", int(z))
			lib.messenger.send(None, "update_helpers", 1)

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
				self.objectsBox.setContents(self.delayedData)
				self.aggregateBox.setContents(self.delayedAggregates)
				self.delayedData = None
			else:
				self.aggregateBox.setContents([self.aggregateHeaders])
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
		filename = GUI.Dialogs.askSaveAsFileName(self.taskPanel, "Save object colocalization statistics as", \
													"%s.csv" % name, "CSV File (*.csv)|*.csv")
													
		self.writeStatistics(filename)
		
	def writeStatistics(self, filename):
		"""
		Write the statistics to the given file
		"""
		f = codecs.open(filename, "ab", "utf-8")
		w = csv.writer(f, dialect = "excel", delimiter = ";")
		sources = self.dataUnit.getSourceDataUnits()
		
		names = [x.getName() for x in sources]
		w.writerow(["Object colocalization statistics",self.dataUnit.getName(), "source channels:"]+names+[ "timepoint",self.getCurrentTimepoint()])
		w.writerow([])
		

		w.writerow(["# of background objects","# of foreground objects","% of background objects colocalized","% of foreground objects colocalized", "Mean # of fg objects per bg object","Std.dev","Mode"])
		w.writerow(self.aggregateData)
		w.writerow([])
		self.objectsBox.writeOut(w, [self.headers])
		w.writerow([])
		w.writerow(["Histogram"])
		keys = self.countCounts.keys()
		keys.sort()
		for key in keys:
			w.writerow([key, self.countCounts[key]])

	def setDataUnit(self, dataUnit):
		"""
		a method to set the dataunit used by this filter
		"""
		lib.ProcessingFilter.ProcessingFilter.setDataUnit(self, dataUnit)
		self.dataUnit = dataUnit
		sourceUnits = dataUnit.getSourceDataUnits()

	def getRange(self, param):
		"""
		Description:
		"""
		return 0,999
		
	def getInputName(self, n):
		"""
		Return the name of the input #n
		"""			 
		if n == 2: return "Counted objects"
		return "Background objects" 
		
	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute filter in input image and return output image
		"""
		if not lib.ProcessingFilter.ProcessingFilter.execute(self,inputs):
			return None

		bgImage = self.getInput(1)
		bgDataUnit = self.getInputDataUnit(1)
		tracksFile = bgDataUnit.getSettings().get("StatisticsFile")
		if tracksFile:
			self.tracksFile = tracksFile
			self.reader = lib.ParticleReader.ParticleReader(tracksFile, 0)
		else:
			self.reader = None
			
		fgImage = self.getInput(2)
		
		labelcount = vtkbxd.vtkImageLabelCount()
		labelcount.AddInput(bgImage)
		labelcount.AddInput(fgImage)
		
		labelcount.Update()

		if not self.objects and self.reader:
			self.objects = self.reader.read()
			
		timepoint = self.getCurrentTimepoint()
		self.centersOfMassList = []
		if  self.objects and self.oldTimepoint != timepoint:
			for obj in self.objects[timepoint]:
				x, y,z  = obj.getCenterOfMass()
				self.centersOfMassList.append((x,y,z))
			self.oldTimepoint = timepoint
		
		data = [self.headers[:]]
		countArray = labelcount.GetBackgroundToObjectCountArray()
		fgToBgArray = labelcount.GetForegroundToBackgroundArray()
		bgObjSizeArray = labelcount.GetBackgroundObjectSizeArray()
		fgObjSizeArray = labelcount.GetObjectSizeArray()
		bgOverlapArray = labelcount.GetBackgroundOverlapArray()
		overlapArray = labelcount.GetObjectOverlapArray()

		fgCount = fgToBgArray.GetSize()
		bgCount = countArray.GetSize()
		
		aggregateData = [self.aggregateHeaders[:]]

		totalCount = 0
		bgColocCount = 0
		fgColocCount = 0
		for i in range(0, fgCount+1):
			bgObj = fgToBgArray.GetValue(i)
			if bgObj:
				fgColocCount+=1
			else:
				print "Object %d not in any bg object"%i
		fgObjCounts = []
		self.countCounts = {}
		
		for i in range(1, bgCount):
			entry = []
			entry.append("#%d"%i)
			bgSize = bgObjSizeArray.GetValue(i)
			bgOverlap = bgOverlapArray.GetValue(i)
			objcount = countArray.GetValue(i)
			self.countCounts[objcount] = self.countCounts.get(objcount,0)+1
			fgObjCounts.append(objcount)
			if objcount:
				bgColocCount+=1
			entry.append("%d objects"%objcount)
			entry.append("%.2f%%"%(100*bgOverlap/float(bgSize)))
			totalCount += objcount
			data.append(entry)
			dataentry = [i, objcount, bgOverlap/float(bgSize)]
			self.items[i] = dataentry
			
		fgColocVoxCount = 0
		fgTotalVoxCount = 0
		for i in range(1, fgCount):
			fgOverlap = overlapArray.GetValue(i)
			fgSize = fgObjSizeArray.GetValue(i)
			fgColocVoxCount += fgOverlap
			fgTotalVoxCount += fgSize
		fgVoxColoc = fgColocVoxCount/float(fgTotalVoxCount)
			
		print "Total nuber of voxels=", fgTotalVoxCount
		print "Number of voxels that overlap background=", fgColocVoxCount
		print "Percent of coloc=", 100*fgColocVoxCount /float(fgTotalVoxCount)
		
		
		agg = []
		agg.append(bgCount)
		agg.append(fgCount)
		agg.append("%.2f%%"%(100*fgVoxColoc))
		agg.append("%.2f%%"%((float(bgColocCount) / bgCount)*100))
		agg.append("%.2f%%"%((float(fgColocCount) / fgCount)*100))
		mean, sd = lib.Math.meanstdev(fgObjCounts)
		largest = 0
		for count in self.countCounts.keys():
			if self.countCounts[count] > largest:
				largest = count
		agg.append(u"%.2f \u00B1 %.2f"%(mean,sd))
		agg.append("%d"%largest)
		self.setResultVariable("ObjectCount", bgCount)
		self.setResultVariable("ColocCount", fgCount)
		self.setResultVariable("FgToBgColoc", float(bgColocCount) / bgCount)
		self.setResultVariable("BgToFgColoc", float(fgColocCount)/fgCount)
		self.setResultVariable("PercentOfObjectVoxelsColocalized", fgVoxColoc)
		self.aggregateData = [bgCount, fgCount, fgVoxColoc, float(bgColocCount) / bgCount, float(fgColocCount) / fgCount, mean, sd, largest]

		aggregateData.append(agg)
		if self.objectsBox:
			self.objectsBox.setContents(data)
			self.aggregateBox.setContents(aggregateData)
		else:
			self.delayedData = data
			self.delayedAggregates = aggregateData
			
		return bgImage
