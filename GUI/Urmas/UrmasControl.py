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
		self.duration = 60 # seconds
		self.frames = 12 * self.duration # frames
		self.animationMode = 0
		self.viewMode = 0
		self.frameSize = (512, 512)
		self.visualizer = visualizer
		self.renderer = UrmasRenderer.UrmasRenderer(self)

	def setFrameSize(self, x, y):
		"""
		Method: setFrameSize
		Created: 19.12.2005, KP
		Description: Set the frame size of the rendered images
		"""
		self.frameSize = (x, y)
		
	def getFrameSize(self):
		"""
		Created: 19.12.2005, KP
		Description: Get the frame size of the rendered images
		"""	   
		return self.frameSize
		
	def writeToDisk(self, filename):
		"""
		Created: 06.04.2005, KP
		Description: Writes the whole control datastructures to disk by way of
					 pickling
		"""
		p = UrmasPersist.UrmasPersist(self)
		p.persist(filename)
	
	def getViewMode(self):return self.viewMode	  
	def setViewMode(self, mode):
		"""
		Created: 17.08.2005, KP
		Description: Set the view mode of spline editor
		"""	   
		self.viewMode = mode


	def resetAnimator(self):
		"""
		Created: 24.06.2005, KP
		Description: Reset the animator
		"""	   
		self.clearGUI()
		self.updateLayouts()

	def readFromDisk(self, filename):
		"""
		Created: 06.04.2005, KP
		Description: Read the whole control datastructures from disk by way of
					 pickling
		"""	   
		self.clearGUI()
		p = UrmasPersist.UrmasPersist(self)
		p.depersist(filename)
		self.updateLayouts()

		
	def clearGUI(self):
		"""
		Created: 06.04.2005, KP
		Description: Clear the GUI
		"""	   
		self.timeline.clearTracks()
		
	def updateGUI(self):
		"""
		Created: 06.04.2005, KP
		Description: Update the GUI to match the data structures
		"""	   
		self.__set_pure_state__(self)
		self.updateLayouts()
		
	def __set_pure_state__(self, state):
		"""
		Created: 11.04.2005, KP
		Description: Update the GUI to match the data structures
		"""	   
		Logging.info("Setting pure state of control...", kw = "animator")
		self.setAnimationMode(state.animationMode)
		self.timelineConfig.setFrames(state.frames)
		self.timelineConfig.setDuration(state.duration)
		self.configureTimeline(state.duration, state.frames)
		
	def getFrames(self):
		"""
		Created: 04.04.2005, KP
		Description: Return the number of frames
		"""	   
		return self.frames
		
	def getFramesPerSecond(self):
		"""
		Creted: 09.10.2006, KP
		Description: Return the frames per second
		"""
		return self.frames / float(self.duration)
		
	def getSecondsPerFrame(self):
		"""
		Creted: 09.10.2006, KP
		Description: Return the seconds per frame
		"""
		return float(self.duration) / self.frames
		
	def getDuration(self):
		"""
		Created: 20.03.2005, KP
		Description: Return the duration of the timeline
		"""	   
		return self.duration
		
	def getPixelsPerSecond(self):
		"""
		Created: 20.03.2005, KP
		Description: Return how many pixels there are per second on the timescale
		"""	   
		return self.timeline.timeScale.getPixelsPerSecond()

	def setAnimator(self, animator):
		"""
		Created: 20.03.2005, KP
		Description: Sets the animator controlled by this
		"""	   
		self.animator = animator

	def setTimelinePanel(self, timelinepanel):
		"""
		Created: 20.03.2005, KP
		Description: Sets the timeline panel controlled by this
		"""	   
		self.timelinePanel = timelinepanel


	def renderProject(self, preview, **kws):
		"""
		Created: 19.04.2005, KP
		Description: Render this project
		"""			   
		return self.renderer.render(self, preview, **kws)
		
	def getDataUnit(self):
		"""
		Created: 20.03.2005, KP
		Description: Returns the dataunit
		"""			   
		return self.dataUnit
		
	def setDataUnit(self, dataunit):
		"""
		Created: 20.03.2005, KP
		Description: Sets the dataunit used as a source of data
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
		Created: 12.09.2007, KP
		Description: initialize the spline editor
		"""
		data = self.renderingInterface.getCurrentData()
		ctf = self.renderingInterface.getColorTransferFunction()
		self.splineEditor.updateData(data, ctf)
		self.splineEditor.initCamera()
		self.splineEditor.render()
		
	def updateLayouts(self):
		"""
		Created: 20.03.2005, KP
		Description: Update various parts of the window as the layout changes
		"""	   
		if self.timeline:
			self.timeline.Layout()

		if self.timelinePanel:
			self.timelinePanel.Layout()
		if self.window:
			self.window.Layout()
		
	def getSplineEditor(self):
		"""
		Created: 14.04.2005, KP
		Description: Return the spline editor instance
		"""		   
		return self.splineEditor
		
	def setAnimationMode(self, mode):
		"""
		Created: 12.03.2005, KP
		Description: Method used to either show or hide the animator
		"""		   
		self.animationMode = mode
		self.timeline.setAnimationMode(mode)
		self.timeline.reconfigureTimeline()
		self.updateLayouts()
		
	def setTimeline(self, timeline):
		"""
		Created: 20.03.2005, KP
		Description: Sets the timeline controlled by this
		"""	   
		self.timeline = timeline
		self.getSelectedTrack = timeline.getSelectedTrack
		
		
	def setTimelineConfig(self, config):
		"""
		Created: 20.03.2005, KP
		Description: Sets the timeline config panel controlled by this
		"""	   
	
		self.timelineConfig = config
		
	def setSplineInteractionCallback(self, cb):
		"""
		Created: 19.03.2005, KP
		Description: Method to set a callback that is called when interaction
					 with the spline editor ends
		"""		   
		self.splineEditor.setInteractionCallback(cb)
	
		
	def configureTimeline(self, seconds, frames):
		"""
		Created: 20.03.2005, KP
		Description: Set the duration and frames of the movie
		"""	   
		#print "Calling timeline.configureTimeline(",seconds,",",frames,")"
		self.duration = seconds
		self.frames = frames
		self.timeline.configureTimeline(seconds, frames)
		self.updateLayouts()

	def setSplineEditor(self, spe):
		"""
		Created: 19.03.2005, KP
		Description: Method used to set the spline editor
		"""		   
		self.splineEditor = spe
		
	def __str__(self):
		"""
		Created: 05.04.2005, KP
		Description: Return string representation of self
		"""		   
		s = "Urmas rendering\nDuration: %.2fs\nFrames: %d\n" % (self.duration, self.frames)
		s += str(self.timeline)
		return s
		
	def __getstate__(self):
		"""
		Created: 06.04.2005, KP
		Description: Return the dict that is to be pickled to disk
		"""		 
		odict = {}
		for key in ["duration", "frames", "timeline", "animationMode"]:
			odict[key] = self.__dict__[key]
		return odict
		
