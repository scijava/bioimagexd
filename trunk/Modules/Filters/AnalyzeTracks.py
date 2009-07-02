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
import types
import os
import wx
import csv
import scripting
import codecs
import Logging


class AnalyzeTracksFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	A filter for analyzing the results of tracking
	"""
	name = "Analyze motion tracks"
	category = lib.FilterTypes.SEGMENTATIONANALYSE

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

		self.descs = {"MinLength":"Minimum length of tracks","ResultsFile": "Tracking results file:", "AnalyseFile": "Analyse results file:"}
		self.numberOfPoints = None
		self.particleFile = ""

		self.lengths = []
		self.dps = []
		self.speeds = []
		self.angles = []
		self.tpCount = []
		self.globalmin = 0
		self.globalmax = 0

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
		return [["Tracking Results", (("ResultsFile", "Select track file that contains the results", "*.csv"), )],
				["Results of the analyse", (("AnalyseFile", "Select the file to export analyse results", "*.csv"), )],
				["Track parameters", ("MinLength",)]]

	def getLongDesc(self, parameter):
		"""
		Return a long description of the parameter
		"""
		return ""

	def getType(self, parameter):
		"""
		Return the type of the parameter
		"""
		if parameter == "MinLength":
			return types.IntType
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
		if parameter == "AnalyseFile":
			return "track_analyse.csv"
		if parameter == "MinLength":
			return 3

	def getGUI(self, parent, taskPanel):
		"""
		Return the GUI for this filter
		"""
		gui = lib.ProcessingFilter.ProcessingFilter.getGUI(self, parent, taskPanel)

		if not self.trackListBox:
			self.trackListBox = GUI.CSVListView.CSVListView(self.gui)
			self.aggregateBox = GUI.CSVListView.CSVListView(self.gui)
			sizer = wx.BoxSizer(wx.VERTICAL)
			sizer.Add(self.trackListBox, 1)
			sizer.Add(self.aggregateBox, 1)

			self.exportBtn = wx.Button(self.gui, -1, "Export statistics")
			self.exportBtn.Bind(wx.EVT_BUTTON, self.onExportStatistics)
			sizer.Add(self.exportBtn)
			gui.sizer.Add(sizer, (1, 0), flag = wx.EXPAND | wx.ALL)

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

		self.onReadTracks(None)

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
		self.showTracks(self.tracks)

	def showTracks(self, tracks):
		"""
		show the given tracks in the track grid
		"""
#		track length
#		Directional persistance = distance to starting point / path length
#		speed
#		angle (avg of changes)

		rows = [["Track #", "# of tps", u"Length (\u03BCm)", u"Avg. speed (\u03BCm/s)", "Directional persistence", "Avg. angle"]]
		self.globalmin = 9999999999
		self.globalmax = 0
		self.lengths = []
		self.dps = []
		self.speeds = []
		self.angles = []
		self.tpCount = []
		dpsPerTp={}
		for i, track in enumerate(tracks):
			tps = track.getNumberOfTimepoints()
			#if tps < self.parameters["MinLength"]:
			#	continue
			length = track.getLength()
			speed = track.getSpeed()
			dp = track.getDirectionalPersistence()
			if tps not in dpsPerTp:
				dpsPerTp[tps] = []
			dpsPerTp[tps].append(dp)
			self.lengths.append(length)
			self.speeds.append(speed)
			self.tpCount.append(tps)
			self.dps.append(dp)
			avgang,avgangstd,avgangstderr = track.getAverageAngle()
			self.angles.append((avgang,avgangstderr))
			row = [i+1, tps, "%.6f"%(length), "%.6f"%(speed), "%.6f"%(dp), u"%.6f\u00B1%.6f"%(avgang,avgangstderr)]
			mintp, maxtp = track.getTimeRange()
			if mintp < self.globalmin:
				self.globalmin = mintp
			if maxtp > self.globalmax:
				self.globalmax = maxtp
			for tp in range(0, maxtp + 1):
				if tp < mintp:
					row.append("")
					continue
				val, pos = track.getObjectAtTime(tp)
				# Set the value at row i, column tp+1 (because there is the column for enabling
				# this track)
				row.append(pos)
			rows.append(row)

		dpkeys = dpsPerTp.keys()
		dpkeys.sort()
		for k in dpkeys:
			print "Avg. dp for tracks of len %d = %.3f"%(k, lib.Math.averageValue(dpsPerTp[k]))
		
		for i in range(0, self.globalmax):
			rows[0].append("T%d" % i)

		self.trackListBox.setContents(rows)
		
		totalRows = [["# of tracks", "Avg. tps", u"Avg. length (\u03BCm)", u"Avg. speed (\u03BCm/s)", "Avg. DP", "Avg. angle"]]
		self.avglen = lib.Math.meanstdeverr(self.lengths)
		self.avgspeed = lib.Math.meanstdeverr(self.speeds)
		self.avgdps = lib.Math.meanstdeverr(self.dps)
		self.avgang = lib.Math.meanstdeverr([x for x,y in self.angles])
		self.avgTpCount = lib.Math.averageValue(self.tpCount)
		avgs = [len(tracks), "%.6f"%self.avgTpCount, u"%.6f\u00B1%.6f"%(self.avglen[0],self.avglen[2]), u"%.6f\u00B1%.6f"%(self.avgspeed[0],self.avgspeed[2]), u"%.6f\u00B1%.6f"%(self.avgdps[0],self.avgdps[2]), u"%.6f\u00B1%.6f"%(self.avgang[0],self.avgang[2])]
		totalRows.append(avgs)
		self.aggregateBox.setContents(totalRows)
		
	def onExportStatistics(self, evt):
		"""
		Export the statistics to csv file
		"""
		name = self.parameters["AnalyseFile"]
		filename = GUI.Dialogs.askSaveAsFileName(self.taskPanel, "Save tracking analyse results as", "%s"%name, "CSV File (*.csv)|*.csv")

		if filename and self.taskPanel:
			listOfFilters = self.taskPanel.filterList.getFilters()
			filterIndex = listOfFilters.index(self)
			func = "getFilter(%d)"%(filterIndex)
			n = scripting.mainWindow.currentTaskWindowName
			method = "scripting.mainWindow.tasks['%s'].filterList.%s"%(n,func)
			do_cmd = "%s.exportStatistics('%s')"%(method,filename)
			cmd = lib.Command.Command(lib.Command.GUI_CMD, None, None, do_cmd, "", desc = "Export analysed tracking statistics")
			cmd.run()
			
	def exportStatistics(self, filename):
		"""
		Export statistics from the current timepoint to the defined csv file
		"""
		timepoint = scripting.visualizer.getTimepoint()
		self.writeToFile(filename, self.dataUnit, timepoint)

	def writeOutput(self, dataUnit, timepoint):
		"""
		Write the output of this module during the processing
		"""
		fileroot = self.parameters["AnalyseFile"]
		if not self.parameters["AnalyseFile"]:
			fileroot = "tracking_analyse.csv"
		fileroot = fileroot.split(".")
		fileroot = ".".join(fileroot[:-1])
		dircomp = os.path.dirname(fileroot)
		if not dircomp:
			bxddir = dataUnit.getOutputDirectory()
			fileroot = os.path.join(bxddir, fileroot)
		filename = "%s.csv" % fileroot
		self.writeToFile(filename, dataUnit, timepoint)

	def writeToFile(self, filename, dataUnit, timepoint):
		"""
		Write the statistics from a given timepoint to file
		"""
		f = codecs.open(filename, "wb", "latin1")
		Logging.info("Saving statistics of tracking to file %s"%filename, kw="processing")
		w = csv.writer(f, dialect = "excel", delimiter = ";")

		headers = ["Track #", "# of timepoints", "Length (micrometers)", "Avg. speed (micrometers/second)", "Directional persistence", "Avg. angle", "Avg. angle std. error"]
		for i in range(0, self.globalmax):
			headers.append("T%d"%i)

		w.writerow(headers)
		for i,track in enumerate(self.tracks):
			tps = self.tpCount[i]
			length = self.lengths[i]
			speed = self.speeds[i]
			direction = self.dps[i]
			angle,anglestderr = self.angles[i]
			row = [str(i+1), str(tps), str(length), str(speed), str(direction), str(angle), str(anglestderr)]
			
			mintp, maxtp = track.getTimeRange()
			for tp in range(0, maxtp + 1):
				if tp < mintp:
					row.append("")
					continue
				val, pos = track.getObjectAtTime(tp)
				row.append(pos)
			w.writerow(row)

		# Write totals and averages
		w.writerow(["Totals"])
		w.writerow(["# of tracks", "Avg. timepoints", "Avg. length (micrometers)", "Avg. length std. error", "Avg. speed (micrometers/second)", "Avg. speed std. error", "Avg. directional persistence", "Avg. directional persistence std. error", "Avg. angle", "Avg. angle std. error"])
		w.writerow([len(self.tracks), self.avgTpCount, self.avglen[0], self.avglen[2], self.avgspeed[0], self.avgspeed[2], self.avgdps[0], self.avgdps[2], self.avgang[0], self.avgang[2]])

