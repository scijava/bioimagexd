#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: AnalyzeTracks
 Project: BioImageXD
 Description:

 A filter for analyzing the tracking results
 
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

import GUI.CSVListView

class AnalyzeTracksFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	A filter for analyzing the results of tracking
	"""
	name = "Analyze tracks"
	category = lib.FilterTypes.TRACKING

	def __init__(self):
		"""
		Initialization
		"""
		self.tracks = []
		self.track = None
		self.tracker = None
		self.trackListBox = None
		self.fileUpdated = 0
		lib.ProcessingFilter.ProcessingFilter.__init__(self, (1, 1))

		self.descs = {"ResultsFile": "Tracking results file:"}
		self.numberOfPoints = None
		self.particleFile = ""

	def setParameter(self, parameter, value):
		"""
		Set a value for the parameter
		"""
		lib.ProcessingFilter.ProcessingFilter.setParameter(self, parameter, value)

		if parameter == "ResultsFile" and os.path.exists(value) and self.trackListBox:
			self.fileUpdated = 1

	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""
		return [["Tracking Results", (("ResultsFile", "Select track file that contains the results", "*.csv"), )]]

	def getLongDesc(self, parameter):
		"""
		Return a long description of the parameter
		"""
		return ""

	def getType(self, parameter):
		"""
		Return the type of the parameter
		"""
		return GUI.GUIBuilder.FILENAME

	def getRange(self, parameter):
		"""
		Return the range of given parameter
		"""
		return 0, 0

	def getDefaultValue(self, parameter):
		"""
		Return the default value of a parameter
		"""

		if parameter == "ResultsFile":
			return "track_results.csv"

	def getGUI(self, parent, taskPanel):
		"""
		Return the GUI for this filter
		"""
		gui = lib.ProcessingFilter.ProcessingFilter.getGUI(self, parent, taskPanel)

		if not self.trackListBox:
			self.trackListBox = GUI.CSVListView.CSVListView(self.gui)
			sizer = wx.BoxSizer(wx.VERTICAL)

			sizer.Add(self.trackListBox, 1)
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
		self.tracks = self.track.getTracks(0)
		self.showTracks(self.tracks)

	def showTracks(self, tracks):
		"""
		show the given tracks in the track grid
		"""
#		track length
#		Directional persistance = path length / distance to starting point
#		speed
#		angle (avg of changes)

		rows = [["Length", "Avg. speed", "Directional persistence", "Avg. angle"]]
		globalmin = 9999999999
		globalmax = 0
		for i, track in enumerate(tracks):
			length = track.getNumberOfTimepoints()
			speed = track.getSpeed()
			dp = track.getDirectionalPersistence()
			avgang = track.getAverageAngle()
			row = [length, speed, dp, avgang]
			mintp, maxtp = track.getTimeRange()
			if mintp < globalmin:
				globalmin = mintp
			if maxtp > globalmax:
				globalmax = maxtp
			for tp in range(0, maxtp + 1):
				if tp < mintp:
					row.append("")
					continue
				val, pos = track.getObjectAtTime(tp)
				print "    value at tp ", tp, "(pos ", pos, ") is ", val
				# Set the value at row i, column tp+1 (because there is the column for enabling
				# this track)
				row.append(pos)
			rows.append(row)

		for i in range(0, globalmax):
			rows[0].append("T%d" % i)

		self.trackListBox.setContents(rows)
