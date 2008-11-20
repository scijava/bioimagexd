#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: ViewTracks
 Project: BioImageXD
 Description:

 A filter for viewing results of tracking
 
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
import scripting
import os.path
import types
import wx
import Modules.DynamicLoader
import Modules

class ViewTracksFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	A filter for controlling the visualization of the tracking results
	"""     
	name = "View tracks"
	category = lib.FilterTypes.TRACKING
	
	def __init__(self):
		"""
		Initialization
		"""        
		self.tracks = []
		self.track = None
		self.tracker = None
		self.trackGrid = None
		self.fileUpdated = 0
		pluginLoader = Modules.DynamicLoader.getPluginLoader()
		analyzeObjectsMod = pluginLoader.getPluginModule("Filters", "CreateTracksFilter")
		self.trackingGUI = analyzeObjectsMod.getUserInterfaceModule()
		
		lib.ProcessingFilter.ProcessingFilter.__init__(self, (1, 1))
		
		self.descs = {"MinLength": "Min. length of track (# of timepoints)",
			"ResultsFile": "Tracking results file:",
			"Track": "Track to visualize",
			"AllTracks":"Visualize all tracks"}
	
		self.numberOfPoints = None
		lib.messenger.connect(None, "set_shown_tracks", self.updateSelectedTracks)
		
		self.particleFile = ""
		
	def setParameter(self, parameter, value):
		"""
		Set a value for the parameter
		"""    
		lib.ProcessingFilter.ProcessingFilter.setParameter(self, parameter, value)

		if parameter == "ResultsFile" and os.path.exists(value) and self.trackGrid:
			self.fileUpdated = 1
		 
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
		if parameter == "MinLength":
			lib.messenger.send(self, "update_Track")
		
		if parameter == "AllTracks":
			if self.tracks and value:
				lib.messenger.send(None, "visualize_tracks", self.tracks)
				lib.messenger.send(None, "update_helpers", 1)
			if not value:
				lib.messenger.send(None, "visualize_tracks", [])
				lib.messenger.send(None, "update_helpers", 1)
		  
	def updateSelectedTracks(self, obj, evt, tracks):
		"""
		show the given tracks
		"""
		if self.tracks:
			showtracks = []
			for i in tracks:
				showtracks.append(self.tracks[i])
			lib.messenger.send(None, "visualize_tracks", showtracks)            
			lib.messenger.send(None, "update_helpers", 1)
	
	
	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""            
		return [["Tracking", ("MinLength", )],        
		["Tracking Results", (("ResultsFile", "Select track file that contains the results", "*.csv"), )],
		["Visualization", ("Track", "AllTracks")]]

		
	def getLongDesc(self, parameter):
		"""
		Return a long description of the parameter
		""" 
		return ""
		
		
	def getType(self, parameter):
		"""
		Return the type of the parameter
		"""    
		if parameter in ["MinLength"]:
			return GUI.GUIBuilder.SPINCTRL
		if parameter == "Track":
			return GUI.GUIBuilder.SLICE            
		if parameter == "AllTracks":
			return types.BooleanType
		return GUI.GUIBuilder.FILENAME
		
	def getRange(self, parameter):
		"""
		Return the range of given parameter
		"""
		print "Get range", parameter
		if parameter == "Track":
			if self.track:
				minlength = self.parameters["MinLength"]
				return 0, self.track.getNumberOfTracks(minlength)            
			else:
				return 0, 1
		if parameter == "MinLength":
			if self.numberOfPoints:
				return 0, self.numberOfPoints
			return 0, 1
				
	def getDefaultValue(self, parameter):
		"""
		Return the default value of a parameter
		"""
		if parameter == "Track":
			return 0    
		if parameter == "MinLength":
			return 3
		if parameter == "ResultsFile":
			return "track_results.csv"
		if parameter == "AllTracks":
			return False
		return "statistics.csv"
		
		
	def getGUI(self, parent, taskPanel):
		"""
		Return the GUI for this filter
		"""              
		gui = lib.ProcessingFilter.ProcessingFilter.getGUI(self, parent, taskPanel)
		
		if not self.trackGrid:
			self.trackGrid = self.trackingGUI.TrackTableGrid(self.gui, self.dataUnit, self, canEnable = 1)
			sizer = wx.BoxSizer(wx.VERTICAL)
			
			sizer.Add(self.trackGrid, 1)
			box = wx.BoxSizer(wx.HORIZONTAL)
			
			self.readTracksBtn = wx.Button(self.gui, -1, "Read tracks")
			box.Add(self.readTracksBtn)
			
			self.readTracksBtn.Bind(wx.EVT_BUTTON, self.onReadTracks)
			
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
			
		if self.prevFilter:
			filename = self.prevFilter.getParameter("ResultsFile")
			if filename and os.path.exists(filename):
				self.setParameter("ResultsFile", filename)
				self.onReadTracks(event = None)
		return gui
		
		
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
				# Set the value at row i, column tp+1 (because there is the column for enabling
				# this track)
				table.SetValue(i, tp + 1, pos, override = 1)
		self.trackGrid.SetTable(table)
		self.trackGrid.ForceRefresh()
