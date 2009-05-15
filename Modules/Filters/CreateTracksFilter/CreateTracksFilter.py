#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: CreateTracks
 Project: BioImageXD
 Description:

 A filter for doing tracking of objects
 
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
import lib.FilterTypes
import GUI.GUIBuilder
import lib.Particle
import lib.ParticleTracker
import lib.ParticleReader
import lib.Track

import Modules.DynamicLoader
import TrackingFilterGUI
import scripting
import os.path
import types
import wx
import vtk

class CreateTracksFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	A filter for tracking objects in a segmented image
	"""     
	name = "Create motion tracks"
	category = lib.FilterTypes.TRACKING
	
	def __init__(self):
		"""
		Initialization
		"""        
		self.tracks = []
		self.track = None
		self.tracker = None
		self.trackGrid = None
		self.objectsReader = None
		self.delayReading = 0
		self.ctf = None
		self.particleFile = ""

		lib.ProcessingFilter.ProcessingFilter.__init__(self, (1, 1))
		
		pluginLoader = Modules.DynamicLoader.getPluginLoader()
		analyzeObjectsMod = pluginLoader.getPluginModule("Filters", "AnalyzeObjectsFilter")
		self.watershedStats = analyzeObjectsMod.getUserInterfaceModule()
		
		self.descs = {
			"MaxVelocity": "Max. speed (in um)",
			"MinVelocity": "Min. speed (in um)",
			"VelocityDeviation":"Deviation from max/min (in %)",
			"MaxSizeChange": "Max. size change (% of old size)",
			"MaxDirectionChange": "Direction (angle of the allowed sector in degrees)",
			"MaxIntensityChange": "Max. change of average intensity (% of old intensity)",
			"MinLength": "Min. length of track (# of timepoints)",
			"MinSize": "Min. size of tracked objects",
			"TrackFile": "Object statistics file:",
			"SizeWeight": "Weight (0-100%):", "DirectionWeight": "Weight (0-100%):",
			"IntensityWeight": "Weight (0-100%):",
			"VelocityWeight": "Weight (0-100%):",
			"ResultsFile": "File to store the results:",
			"Track": "Track to visualize",
			"UseROI": "Select seed objects using ROI:", "ROI": "ROI for tracking:"}
			
		lib.messenger.connect(None, "selected_objects", self.onSetSelectedObjects)
	
		self.numberOfPoints = None
		self.selectedTimepoint = 0
		lib.messenger.connect(None, "timepoint_changed", self.onSetTimepoint)
		

	def onRemove(self):
		"""
		Remove event listeners
		"""
		lib.messenger.disconnect(None, "selected_objects", self.onSetSelectedObjects)
		lib.messenger.disconnect(None, "timepoint_changed", self.onSetTimepoint)
			
	def onSetTimepoint(self, obj, event, timepoint):
		"""
		Update the column that can be edited based on the timepoint
		"""
		self.selectedTimepoint = timepoint
		self.updateObjects()
		
	def onSetSelectedObjects(self, obj, event, objects, isROI = 0):
		"""
		An event handler for highlighting selected objects
		"""
		if not self.ctf:
			self.ctf = self.dataUnit.getColorTransferFunction()
		if not objects:
			self.dataUnit.getSettings().set("ColorTransferFunction", self.ctf)
			lib.messenger.send(None, "data_changed", 0)
			return

		if not isROI:
			# Since these object id's come from the list indices, instead of being the actual
			# intensity values, we need to add 1 to each object value to account for the
			# objects produced by the segmentation results
			objects = [x + 1 for x in objects]
		self.selections = objects
		self.setSelectedObjects()

	def setSelectedObjects(self):
		"""
		Highlight selected objects
		"""
		ctf = vtk.vtkColorTransferFunction()
		minval, maxval = self.ctf.GetRange()
		hv = 0.4
		ctf.AddRGBPoint(0, 0, 0, 0)
		#ctf.AddRGBPoint(1, 0, 0, 0)
		ctf.AddRGBPoint(1, hv, hv, hv)
		ctf.AddRGBPoint(maxval, hv, hv, hv)
		for obj in self.selections:
			if obj - 1 not in self.selections and obj - 1 > 0:
				ctf.AddRGBPoint(obj - 1, hv, hv, hv)
			ctf.AddRGBPoint(obj, 0.0, 1.0, 0.0)
			if obj + 1 not in self.selections and obj + 1 <= maxval:
				ctf.AddRGBPoint(obj + 1, hv, hv, hv)
		print "Setting CTF where highlighted=", self.selections
		self.dataUnit.getSettings().set("ColorTransferFunction", ctf)
		lib.messenger.send(None, "data_changed", 0)
		
		
	def setParameter(self, parameter, value):
		"""
		Set a value for the parameter
		"""    
		lib.ProcessingFilter.ProcessingFilter.setParameter(self, parameter, value)
		if parameter == "TrackFile":
			self.particleFile = value
		elif parameter == "ResultsFile" and os.path.exists(value):
			pass
#            self.track = lib.Track.Track(value)
#            self.tracks = self.track.getTracks(self.parameters["MinLength"])
#            print "Read %d tracks"%(len(self.tracks))
#            lib.messenger.send(self,"update_Track")
			#if self.parameters.has_key("Track") and self.tracks:
			#    lib.messenger.send(None,"visualize_tracks",[self.tracks[self.parameters["Track"]]])
			#    lib.messenger.send(None,"update_helpers",1)
		elif parameter == "Track":
			if self.tracks:
				lib.messenger.send(None, "visualize_tracks", [self.tracks[self.parameters["Track"]]])            
				lib.messenger.send(None, "update_helpers", 1)
		elif parameter == "ROI":
			index, roi = self.parameters["ROI"]
			if roi and self.parameters["UseROI"]:
				print "roi=",roi,index
				selections = self.getObjectsForROI(roi)
				# The last boolean is a flag indicating that this selection
				# comes from a ROI
				lib.messenger.send(None, "selected_objects", selections, True)
				
		if parameter == "MinLength":
			lib.messenger.send(self, "update_Track")
	
	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""            
		return [
		["Change between consecutive objects",
		("MaxVelocity", "MinVelocity","VelocityWeight","VelocityDeviation",
		"MaxSizeChange", "SizeWeight",
		"MaxIntensityChange", "IntensityWeight",
		"MaxDirectionChange", "DirectionWeight")],
		["Region of Interest", ("UseROI", "ROI")],
		["Tracking", ("MinLength", "MinSize")],
		["Load object info", (("TrackFile", "Select file with object statistics to load", "*.csv"), )],
		["Tracking Results", (("ResultsFile", "Select track file that contains the results", "*.csv"), )],
		]
		
	def getLongDesc(self, parameter):
		"""
		Return a long description of the parameter
		""" 
		return ""
		
		
	def getType(self, parameter):
		"""
		Return the type of the parameter
		"""    
		if parameter == "UseSize":
			return types.BooleanType
		elif parameter in ["MaxVelocity", "MinVelocity","MaxSizeChange", "MinLength", "MinSize","VelocityDeviation"]:
			return GUI.GUIBuilder.SPINCTRL
		elif parameter in ["SizeWeight", "DirectionWeight", "IntensityWeight", "MaxDirectionChange", \
							"MaxIntensityChange", "MaxSizeChange", "VelocityWeight"]:
			return GUI.GUIBuilder.SPINCTRL
		if parameter == "Track":
			return GUI.GUIBuilder.SLICE     
		if parameter == "ROI":
			return GUI.GUIBuilder.ROISELECTION
		if parameter == "UseROI":
			return types.BooleanType
		return GUI.GUIBuilder.FILENAME
		
	def getRange(self, parameter):
		"""
		Return the range of given parameter
		"""             
		if parameter in ["MaxVelocity", "MinSize","MinVelocity","VelocityDeviation","MaxSizeChange","MaxIntensityChange"]:
			return (0, 999)
		if parameter == "Track":
			if self.track:
				minlength = self.parameters["MinLength"]
				return 0, self.track.getNumberOfTracks(minlength)
		if parameter == "MinLength":
			if self.numberOfPoints:
				return 0, self.numberOfPoints
			return 0, 1000
		if parameter == "MaxDirectionChange":
			return (0, 180)
		return (0, 100)
				
	def getDefaultValue(self, parameter):
		"""
		Return the default value of a parameter
		"""     
		if parameter == "UseSize":
			return 1
		if parameter == "MinSize":
			return 6
		if parameter == "MaxVelocity":
			return 18
		if parameter == "MinVelocity":
			return 5
		if parameter == "MaxSizeChange":
			return 35
		if parameter == "MinLength":
			return 3
		if parameter == "VelocityDeviation": 
			return 30
		if parameter in ["IntensityWeight", "SizeWeight", "DirectionWeight", "VelocityWeight"]:
			return 25
		if parameter == "MaxDirectionChange":
			return 45
		if parameter == "MaxIntensityChange":
			return 40
		if parameter == "MaxSizeChange":
			return 25
		#if parameter=="Track":return 0            
		if parameter == "ResultsFile":
			return "track_results.csv"
		if parameter == "UseROI":
			return 0
		if parameter == "ROI":
			n = scripting.visualizer.getRegionsOfInterest()
			if n:
				return (0, n[0])
			return 0,None
		if parameter == "TrackFile":
			if self.particleFile:
				return self.particleFile
		return "statistics.csv"
		
	def setDataUnit(self, dataUnit):
		"""
		a method to set the dataunit used by this filter
		"""
		lib.ProcessingFilter.ProcessingFilter.setDataUnit(self, dataUnit)
		tracksFile = dataUnit.getSettings().get("StatisticsFile")
		print "Tracks file=",tracksFile
		if tracksFile and os.path.exists(tracksFile):
			print "Got tracks file",tracksFile
			self.parameters["TrackFile"] = tracksFile
			self.particleFile = tracksFile
			self.delayReading = 1
			
	def getGUI(self, parent, taskPanel):
		"""
		Return the GUI for this filter
		"""              
		gui = lib.ProcessingFilter.ProcessingFilter.getGUI(self, parent, taskPanel)
		
		if not self.trackGrid:
			self.trackGrid = TrackingFilterGUI.TrackTableGrid(self.gui, self.dataUnit, self)
			self.reportGUI = self.watershedStats.WatershedObjectList(self.gui, -1, (350, 100))
			sizer = wx.BoxSizer(wx.VERTICAL)
			sizer.Add(self.trackGrid, 1)
						
			box = wx.BoxSizer(wx.HORIZONTAL)
			
			self.readBtn = wx.Button(self.gui, -1, "Read objects")
			self.readTracksBtn = wx.Button(self.gui, -1, "Read tracks")
			self.newTrackBtn = wx.Button(self.gui, -1, "New track")
			self.calcTrackBtn = wx.Button(self.gui, -1, "Calculate tracks")
			box.Add(self.readBtn)
			box.Add(self.readTracksBtn)
			box.Add(self.newTrackBtn)
			box.Add(self.calcTrackBtn)
			
			#self.newTrackBtn.Enable(0)
			self.calcTrackBtn.Enable(0)
			
			self.readTracksBtn.Bind(wx.EVT_BUTTON, self.onReadTracks)
			self.readBtn.Bind(wx.EVT_BUTTON, self.onReadObjects)
			self.newTrackBtn.Bind(wx.EVT_BUTTON, self.trackGrid.onNewTrack)
			self.calcTrackBtn.Bind(wx.EVT_BUTTON, self.onDoTracking)
			
			sizer.Add(box)
			
			self.toggleBtn = wx.ToggleButton(self.gui, -1, "Show seed objects>>")
			self.toggleBtn.SetValue(0)
			self.toggleBtn.Bind(wx.EVT_TOGGLEBUTTON, self.onShowObjectList)
			sizer.Add(self.toggleBtn)            
			sizer.Add(self.reportGUI, 1)
			sizer.Show(self.reportGUI, 0)
			
			self.guisizer = sizer
			self.useSelectedBtn = wx.Button(self.gui, -1, "Use selected as seeds")
			self.useSelectedBtn.Bind(wx.EVT_BUTTON, self.onUseSelectedSeeds)
			sizer.Add(self.useSelectedBtn)
			
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
			self.gui = gui
			
		if self.delayReading:
			self.onReadObjects(None)
			self.delayReading = 0
		return gui
		
	def getObjectsForROI(self, roi):
		"""
		return the intensity values of objects in a given roi
		"""
		imagedata = self.getInputFromChannel(0)
		mx, my, mz = self.dataUnit.getDimensions()
		n, maskImage = lib.ImageOperations.getMaskFromROIs([roi], mx, my, mz)
		maskFilter = vtk.vtkImageMask()
		maskFilter.SetMaskedOutputValue(0)
		maskFilter.SetMaskInput(maskImage)
		maskFilter.SetImageInput(imagedata)
		maskFilter.Update()
		data = maskFilter.GetOutput()
		histogram = lib.ImageOperations.get_histogram(data)
		ret = []
		for i in range(2, len(histogram)):
			if histogram[i]:
				ret.append(i)
		return ret
		
	def onUseSelectedSeeds(self, event):
		"""
		use the selected seed list
		"""
		if self.parameters["UseROI"]:
			index, roi = self.parameters["ROI"]
			selections = []
			if roi:
				selections = self.getObjectsForROI(roi)
		else:
			selections = self.selections[:]
		
		if self.ctf:
			self.dataUnit.getSettings().set("ColorTransferFunction", self.ctf)
			self.ctf = None
			lib.messenger.send(None, "data_changed", 0)

		n = self.trackGrid.getTable().GetNumberRows()
		n2 = len(selections)
		if n2 > n:
			self.trackGrid.AppendRows(n2 - n)
			self.trackGrid.SetTable(self.trackGrid.getTable())
		
		currTp = self.trackGrid.getTimepoint()
		particles = self.tracker.getParticles(currTp, selections)
		for i, obj in enumerate(particles):
			self.trackGrid.getTable().SetValue(i, currTp, obj.getCenterOfMass())
		self.trackGrid.ForceRefresh()
		
	def onShowObjectList(self, event):
		"""
		show a list of objects that can be used as seeds for trakcing
		"""
		val = self.toggleBtn.GetValue()
		if not val:
			self.toggleBtn.SetLabel("Show seed objects >>")
		else:
			self.toggleBtn.SetLabel("<< Hide seed objects")
		self.guisizer.Show(self.reportGUI, val)
		self.gui.Layout()

	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute the filter with given inputs and return the output
		"""            
		if not lib.ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None
		image = self.getInputFromChannel(0)
		return image
	
	def onReadTracks(self, event):
		"""
		Read tracks from a file instead of calculating them
		"""
		filename = self.parameters["ResultsFile"]
		if not os.path.exists(filename):
			return
		self.track = lib.Track.TrackReader()
		self.track.readFromFile(filename)
		
		self.tracks = self.track.getTracks(self.parameters["MinLength"])
		n = len(self.tracks)
		lib.messenger.send(self, "update_Track")
		print "Read %d tracks" % (n)
		print self.tracks
		self.showTracks(self.tracks)
		
	def showTracks(self, tracks):
		"""
		show the given tracks in the track grid
		"""
		table = self.trackGrid.getTable()
		table.Clear()
		table.AppendRows(len(tracks))
		for i, track in enumerate(tracks):
			mintp, maxtp = track.getTimeRange()
			print "Track", i, "has time range", mintp, maxtp
			for tp in range(mintp, maxtp + 1):
				val, pos = track.getObjectAtTime(tp)
				print "    value at tp ", tp, "(pos ", pos, ") is ", val
				if val:
					table.SetValue(i, tp, pos, override = 1)
		self.trackGrid.SetTable(table)
		self.trackGrid.ForceRefresh()
		
		
	def onReadObjects(self, event):
		"""
		Read the object statistics from the given file
		"""
		if not self.particleFile:
			return
		if not self.tracker:
			self.tracker = lib.Particle.ParticleTracker()

		image = self.getInputFromChannel(0)
		spacing = image.GetSpacing()
		try:
			datasource = self.dataUnit.sourceunits[0].getDataSource()
			timeInterval = datasource.getTimeStamp(1)
			if timeInterval < 0.0:
				timeInterval = 1.0
		except:
			timeInterval = 1.0
		
		
		self.tracker.setSpacing(spacing)
		self.tracker.setTimeInterval(timeInterval)
		self.tracker.setFilterObjectSize(self.parameters["MinSize"])
		if not os.path.exists(self.particleFile):
			GUI.Dialogs.showerror(None, "Could not read the selected particle file %s"%self.particleFile, "Cannot read particle file")
			return
		else:
			self.tracker.readFromFile(self.particleFile, statsTimepoint = self.selectedTimepoint)
		rdr = self.objectsReader = self.tracker.getReader()

		self.reportGUI.setVolumes(rdr.getVolumes())
		self.reportGUI.setCentersOfMass(rdr.getCentersOfMass())
		avgints,avgintsstderr = rdr.getAverageIntensities()
		self.reportGUI.setAverageIntensities(avgints,avgintsstderr)
		self.reportGUI.setAreasUm(rdr.getAreas())
		avgdists,avgdiststderr = rdr.getAverageDistances()
		self.reportGUI.setAverageDistances(avgdists,avgdiststderr)
		
		self.calcTrackBtn.Enable(1)
		
	def updateObjects(self):
		"""
		update the objects list
		"""
		if self.objectsReader and self.reportGUI:
			rdr = self.objectsReader
			rdr.read(statsTimepoint = self.selectedTimepoint)
			self.reportGUI.setVolumes(rdr.getVolumes())
			self.reportGUI.setCentersOfMass(rdr.getCentersOfMass())
			avgints, avgintsstderr = rdr.getAverageIntensities()
			self.reportGUI.setAverageIntensities(avgints,avgintsstderr)
			
	def getObjectFromCoord(self, pt, timepoint = -1):
		"""
		return an intensity value at given x,y,z
		"""
		if not pt:
			return None
		x, y, z = pt
#        print "Getting from ",x,y,z
		image = self.getInputFromChannel(0, timepoint = timepoint)
		image.SetUpdateExtent(image.GetWholeExtent())
		image.Update()
		intensity = int(image.GetScalarComponentAsDouble(x, y, z, 0))
		return intensity
		
	def onDoTracking(self, event):
		"""
		Do the actual tracking
		"""
		self.tracker.setMaxSpeed(self.parameters["MaxVelocity"])
		self.tracker.setMinSpeed(self.parameters["MinVelocity"])
		self.tracker.setSpeedDeviation(self.parameters["VelocityDeviation"]/ 100.0)

		self.tracker.setSizeChange(self.parameters["MaxSizeChange"] / 100.0)
		self.tracker.setIntensityChange(self.parameters["MaxIntensityChange"] / 100.0)
		self.tracker.setAngleChange(self.parameters["MaxDirectionChange"])
		w1 = self.parameters["VelocityWeight"]
		w2 = self.parameters["SizeWeight"]
		w3 = self.parameters["IntensityWeight"]
		w4 = self.parameters["DirectionWeight"]
		self.tracker.setWeights(w1, w2, w3, w4)
		
		objVals = []
		pts = self.trackGrid.getSeedPoints()
		print "Seed points=", pts
		for i, col in enumerate(pts):
			# Following doesn't work as center of mass can be outside object
			#f = lambda coord, tp = i: self.getObjectFromCoord(coord, timepoint = tp)
			#its = map(f, col)
			#objVals.append(its)
			its = []
			obj = 1
			for point in col:
				its.append(obj)
				obj += 1
			objVals.append(its)
		print "Objects=", objVals

		#for timepoint in objVals:
		#	while 0 in timepoint:
		#		print "Removing object 0"
		#		timepoint.remove(0)
		#while 1 in objVals:
		#	print "Removing object 1"
		#	objVals.remove(1)
		
		fromTp = self.trackGrid.getTimepoint()
		print "Tracking from timepoint", fromTp, "forward"
		self.tracker.track(fromTimepoint = fromTp, seedParticles = objVals)
		trackWriter = lib.ParticleReader.ParticleWriter()
		trackWriter.writeTracks(self.parameters["ResultsFile"], self.tracker.getTracks(), self.parameters["MinLength"])
	
		self.onReadTracks(None)

