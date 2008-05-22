#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

"""
 Unit: UrmasControl
 Project: BioImageXD
 Created: 22.02.2005, KP
 Description:

 URM/AS - The Unified Rendering Manager / Animator for Selli
 
 This is a timeline based GUI for controlling the rendering of datasets. The GUI allows users
 to specify a path for the camera to follow (using Heikki Uuksulainen's MayaVi animator code)
 and also allows them to produce videos of the rendering using ffmpeg.
 
 This module contains the UrmasControl that is controlling the whole 
 Urmas experience as well as representations of the tracks and items of
 the timeline that can be written out or sent to the renderer that produces
 the final movie.
 
 Copyright (C) 2005	 BioImageXD Project
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
__author__ = "BioImageXD Project"
__version__ = "$Revision: 1.22 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import lib.RenderingInterface
import Logging

import UrmasPersist
import UrmasRenderer


class UrmasControl:
	"""
	Created: 22.02.2005, KP
	Description: A class that controls Urmas
	"""
	def __init__(self, window, visualizer):
		self.window = window
		self.timeline = None
		self.timelinePanel = None
		self.timescale = None
		self.splineEditor = None
		self.splinePointAmount = 5
		self.duration = 10 # seconds
		self.frames = 15 * self.duration # frames
		self.animationMode = 0
		self.viewMode = 0
		self.frameSize = (512, 512)
		self.visualizer = visualizer
		self.renderer = UrmasRenderer.UrmasRenderer(self)

	def setFrameSize(self, x, y):
		"""
		Method: setFrameSize
		Set the frame size of the rendered images
		"""
		self.frameSize = (x, y)
		
	def getFrameSize(self):
		"""
		Get the frame size of the rendered images
		"""	   
		return self.frameSize
		
	def writeToDisk(self, filename):
		"""
		Writes the whole control datastructures to disk by way of
					 pickling
		"""
		p = UrmasPersist.UrmasPersist(self)
		p.persist(filename)
	
	def getViewMode(self):return self.viewMode	  
	def setViewMode(self, mode):
		"""
		Set the view mode of spline editor
		"""	   
		self.viewMode = mode


	def resetAnimator(self):
		"""
		Reset the animator
		"""	   
		self.clearGUI()
		self.updateLayouts()

	def readFromDisk(self, filename):
		"""
		Read the whole control datastructures from disk by way of
					 pickling
		"""	   
		self.clearGUI()
		p = UrmasPersist.UrmasPersist(self)
		p.depersist(filename)
		self.updateLayouts()

		
	def clearGUI(self):
		"""
		Clear the GUI
		"""	   
		self.timeline.clearTracks()
		
	def updateGUI(self):
		"""
		Update the GUI to match the data structures
		"""	   
		self.__set_pure_state__(self)
		self.updateLayouts()
		
	def __set_pure_state__(self, state):
		"""
		Update the GUI to match the data structures
		"""	   
		Logging.info("Setting pure state of control...", kw = "animator")
		self.setAnimationMode(state.animationMode)
		self.timelineConfig.setFrames(state.frames)
		self.timelineConfig.setDuration(state.duration)
		self.configureTimeline(state.duration, state.frames)
		
	def getFrames(self):
		"""
		Return the number of frames
		"""	   
		return self.frames
		
	def getFramesPerSecond(self):
		"""
		Creted: 09.10.2006, KP
		Return the frames per second
		"""
		return self.frames / float(self.duration)
		
	def getSecondsPerFrame(self):
		"""
		Creted: 09.10.2006, KP
		Return the seconds per frame
		"""
		return float(self.duration) / self.frames
		
	def getDuration(self):
		"""
		Return the duration of the timeline
		"""	   
		return self.duration
		
	def getPixelsPerSecond(self):
		"""
		Return how many pixels there are per second on the timescale
		"""	   
		return self.timeline.timeScale.getPixelsPerSecond()

	def setAnimator(self, animator):
		"""
		Sets the animator controlled by this
		"""	   
		self.animator = animator

	def setTimelinePanel(self, timelinepanel):
		"""
		Sets the timeline panel controlled by this
		"""	   
		self.timelinePanel = timelinepanel


	def renderProject(self, preview, **kws):
		"""
		Render this project
		"""			   
		return self.renderer.render(self, preview, **kws)
		
	def getDataUnit(self):
		"""
		Returns the dataunit
		"""			   
		return self.dataUnit
		
	def setDataUnit(self, dataunit):
		"""
		Sets the dataunit used as a source of data
		"""	   
		self.dataUnit = dataunit
		self.renderingInterface = lib.RenderingInterface.getRenderingInterface(1)
		self.renderingInterface.setDataUnit(dataunit)
		self.renderingInterface.setVisualizer(self.visualizer)
		self.timelinePanel.setDataUnit(dataunit)

		self.configureTimeline(self.duration, self.frames)
		self.updateGUI()
		self.updateLayouts()
		
		self.initializeSplineEditor()
		
	def initializeSplineEditor(self):
		"""
		initialize the spline editor
		"""
		data = self.renderingInterface.getCurrentData()
		ctf = self.renderingInterface.getColorTransferFunction()
		self.splineEditor.updateData(data, ctf)
		self.splineEditor.initCamera()
		self.splineEditor.render()
		
	def updateLayouts(self):
		"""
		Update various parts of the window as the layout changes
		"""	   
		if self.timeline:
			self.timeline.Layout()

		if self.timelinePanel:
			self.timelinePanel.Layout()
		if self.window:
			self.window.Layout()
		
	def getSplineEditor(self):
		"""
		Return the spline editor instance
		"""		   
		return self.splineEditor
		
	def setAnimationMode(self, mode):
		"""
		Method used to either show or hide the animator
		"""		   
		self.animationMode = mode
		self.timeline.setAnimationMode(mode)
		self.timeline.reconfigureTimeline()
		self.updateLayouts()
		
	def setTimeline(self, timeline):
		"""
		Sets the timeline controlled by this
		"""	   
		self.timeline = timeline
		self.getSelectedTrack = timeline.getSelectedTrack
		
		
	def setTimelineConfig(self, config):
		"""
		Sets the timeline config panel controlled by this
		"""	   
	
		self.timelineConfig = config
		
	def setSplineInteractionCallback(self, cb):
		"""
		Method to set a callback that is called when interaction
					 with the spline editor ends
		"""		   
		self.splineEditor.setInteractionCallback(cb)
	
		
	def configureTimeline(self, seconds, frames):
		"""
		Set the duration and frames of the movie
		"""	   
		#print "Calling timeline.configureTimeline(",seconds,",",frames,")"
		self.duration = seconds
		self.frames = frames
		self.timeline.configureTimeline(seconds, frames)
		self.updateLayouts()

	def setSplineEditor(self, spe):
		"""
		Method used to set the spline editor
		"""		   
		self.splineEditor = spe
		
	def __str__(self):
		"""
		Return string representation of self
		"""		   
		s = "Urmas rendering\nDuration: %.2fs\nFrames: %d\n" % (self.duration, self.frames)
		s += str(self.timeline)
		return s
		
	def __getstate__(self):
		"""
		Return the dict that is to be pickled to disk
		"""		 
		odict = {}
		for key in ["duration", "frames", "timeline", "animationMode"]:
			odict[key] = self.__dict__[key]
		return odict
		
