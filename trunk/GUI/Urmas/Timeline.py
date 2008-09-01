# -*- coding: iso-8859-1 -*-
"""
 Unit: Timeline
 Project: BioImageXD
 Created: 04.02.2005, KP
 Description:

 URM/AS - The Unified Rendering Manager / Animator for Selli
 
 This is a timeline based GUI for controlling the rendering of datasets. The GUI allows users
 to specify a path for the camera to follow (using Heikki Uuksulainen's MayaVi animator code)
 and also allows them to produce videos of the rendering using ffmpeg.
 
 The timeline widget and the timescale are implemented in this module.
 
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
__author__ = "BioImageXD Project"
__version__ = "$Revision: 1.22 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"


import GUI.Dialogs
import GUI.Urmas.UrmasPalette
from Track.KeyframeTrack import KeyframeTrack
import lib.messenger    
import Logging
import wx.lib.scrolledpanel as scrolled
from Track.SplineTrack import SplineTrack
from Track.TimepointTrack import TimepointTrack
from TimeScale import TimeScale
import wx

class Timeline(scrolled.ScrolledPanel):
	"""
	Description: Class representing the timeline with different tracks
	"""    
	def __init__(self, parent, control, **kws):
		"""
		Initialize
		"""
		size = (750, 600)
		
		if kws.has_key("size"):
			size = kws["size"]
		print "Using size", size
		scrolled.ScrolledPanel.__init__(self, parent, -1, size = size)
		
		self.oldBgCol = self.GetBackgroundColour()
		self.control = control
		self.parent = parent
		self.frames = 0
		self.selectedTrack = None
		control.setTimeline(self)
		self.sizer = wx.GridBagSizer(5, 1)
		self.sizer.AddGrowableCol(0)
		self.timepointSizer = wx.GridBagSizer(2, 1)
		self.splineSizer = wx.GridBagSizer(2, 1)
		self.keyframeSizer = wx.GridBagSizer(2, 1)
		
		
		self.timeScale = TimeScale(self)
		self.timeScale.setDuration(self.control.getDuration())

		self.sizer.Add(self.timeScale, (0, 0), flag = wx.EXPAND | wx.LEFT | wx.RIGHT)
		self.sizer.Add(self.timepointSizer, (1, 0), flag = wx.EXPAND | wx.LEFT | wx.RIGHT)
		self.sizer.Add(self.splineSizer, (2, 0), flag = wx.EXPAND | wx.LEFT | wx.RIGHT)
		self.sizer.Add(self.keyframeSizer, (3, 0), flag = wx.EXPAND | wx.LEFT | wx.RIGHT)
		
		self.Unbind(wx.EVT_CHILD_FOCUS)
		
		self.haveTp = 1
		self.haveSp = 1
		self.haveKf = 1
   
		self.timepointTracks = []
		self.splinepointTracks = []
		self.keyframeTracks = []
		self.timepointTrackAmnt = 0
		self.splinepointTrackAmnt = 0
		self.keyframeTrackAmnt = 0
		self.trackOffset = 1
		
		w, h = self.GetSize()
		w2, h = self.timeScale.GetSize()
		self.timeScale.SetSize((w, h))
		dt = GUI.Urmas.UrmasPalette.UrmasDropTarget(self, "Track")
		self.SetDropTarget(dt)
			
		self.SetSizer(self.sizer)
		self.SetAutoLayout(1)
		
		
		#self.sizer.Fit(self)
		lib.messenger.connect(None, "set_timeline_size", self.setupScrolling)
		lib.messenger.connect(None, "set_duration", self.onSetDuration)
		lib.messenger.connect(None, "set_frames", self.onSetFrames)
		lib.messenger.connect(None, "update_timeline", self.onUpdateTimeline)
		
	def onUpdateTimeline(self, obj, evt, *args):
		"""
		Method to refresh the whole timeline
		"""
		for tracks, sizer in [(self.timepointTracks, self.timepointSizer),
							  (self.splinepointTracks, self.splineSizer),
							  (self.keyframeTracks, self.keyframeSizer)]:
			#t=None
			for i in tracks:
				if i:
					#t=i
					i.updateItemSizes()
					i.setDuration(self.seconds, self.frames)
					print i.GetSize()

		
	def AcceptDrop(self, x, y, data):
		"""
		Method called to indicate that a user is no longer dragging
					 something to this track
		"""     
		#print "AcceptDrop",x,y,data
		if data == "Spline":
			self.addSplinepointTrack("")
		elif data == "Keyframe":
			self.addKeyframeTrack("")
		else:
			self.addTrack("")
			
	def OnDragLeave(self):
		"""
		Method called to indicate that a user is no longer dragging
					 something to this track
		"""     
		#print "OnDragLeave"
		#print "old bg color=",self.oldBgCol
		self.SetBackgroundColour(self.oldBgCol)
		self.Refresh()
			
	def OnDragOver(self, x, y, d):
		"""
		Method called to indicate that a user is dragging
					 something to this track
		""" 
		self.SetBackgroundColour((192, 192, 192))
		self.Refresh()
		
	def setupScrolling(self, obj = None, evt = None, arg = None):
		"""
		Set the scrollbars
		"""         
		self.SetupScrolling()
		
	def getSplineTracks(self):
		"""
		Return the camera path tracks
		""" 
		return self.splinepointTracks
		
	def getTimepointTracks(self):
		"""
		Return the timepoint tracks
		""" 
		return self.timepointTracks
		
	def getKeyframeTracks(self):
		"""
		Return the keyframe tracks
		""" 
		return self.keyframeTracks
		
	def getSelectedTrack(self):
		"""
		Return the track that is currently selected
		""" 
		return self.selectedTrack
		
	def setSelectedTrack(self, track):
		"""
		Set the track that is currently selected
		""" 
		if self.selectedTrack and track != self.selectedTrack:
			self.selectedTrack.setSelected(None)
		self.selectedTrack = track
		self.control.window.updateMenus()
		
		
	def setBeginningToPrevious(self, track):
		"""
		Set the given track to start at the position where
					 the previous track ends
		""" 
		i = self.splinepointTracks.index(track)
		if i < 1:
			GUI.Dialogs.showwarning(self, "First track has no preceeding tracks", "Cannot set beginning of track")
			return
		p = self.splinepointTracks[i - 1].items[-1].getPoint()
		self.splinepointTracks[i].items[0].setPoint(p)
		#print "Setting track %d to begin at %s"%(i,str(p))
		self.splinepointTracks[i].showSpline()
		
	def setEndToNext(self, track):
		"""
		Set the given track to end at the position where
					 the next track begins
		""" 
		i = self.splinepointTracks.index(track)
		
		if i == len(self.splinepointTracks) - 1:
			GUI.Dialogs.showwarning(self, "Last track has no following tracks", "Cannot set end of track")
			return
		p = self.splinepointTracks[i + 1].items[0].getPoint()
		self.splinepointTracks[i].items[-1].setPoint(p)
		#print "Setting track %d to end at %s"%(i,str(p))
		self.splinepointTracks[i].showSpline()
		
			
		
	def __set_pure_state__(self, state):
		"""
		Method called by UrmasPersist to allow the object
					 to refresh before it's items are created
		""" 
		Logging.info("Setting pure state of timeline", kw = "animator")
		# We add these tracks so that when the tracks are depersisted, they will simply overwrite these
		# since URPO doesn't know how to create the tracks, just how to load the contents
#        spamnt = self.splinepointTrackAmnt
#        tpamnt = self.timepointTrackAmnt

		#for tptrack in state.timepointTracks:
		for tptrack in state.timepointTracks:
			t = self.addTrack(tptrack.label)
			t.__set_pure_state__(tptrack)
		for sptrack in state.splinepointTracks:
			t = self.addSplinepointTrack(sptrack.label)
			t.__set_pure_state__(sptrack)
		for kftrack in state.keyframeTracks:
			t = self.addKeyframeTrack(kftrack.label)
			t.__set_pure_state__(kftrack)
			

#        for n in range(tpamnt-len(self.timepointTracks)):
#            print "Adding timepoint track"
#            self.addTrack("Timepoints %d"%n,n)
#        for n in range(spamnt-len(self.splinepointTracks)):
#            print "Adding splinepoint track"
#            self.addSplinepointTrack("Camera Path %d"%n)
#        print "splinepointtracks now=",self.splinepointTracks
			
	def moveTracks(self, sizer, moveFrom, moveTo, howMany):
		"""
		Moves the tracks placed on a sizer
		Parameters:
			moveFrom    Start moving the tracks from here
			moveTo      Move them here
			howMany     How many tracks there are to move
		""" 
		replace = []
		for i in range(howMany):
			#item=self.sizer.FindItemAtPosition((self.trackOffset+moveFrom+i,0))
			item = sizer.FindItemAtPosition((moveFrom + i, 0))
			item = item.GetWindow()
			#print "Got item =",item
#            print "Detaching %d at (%d,0)"%(i,moveFrom+i)
			sizer.Show(item, 0)
			sizer.Detach(item)
			replace.append(item)
		
		for i in range(0, len(replace)):
			item = replace[i]
			#print "Placing %d to (%d,0)"%(i,moveTo+i)
			#self.sizer.Add(item,(self.trackOffset+moveTo+i,0),flag=wx.EXPAND|wx.ALL)
			sizer.Add(item, (moveTo + i, 0), flag = wx.EXPAND | wx.ALL)
			item.SetSize((item.width, item.height))
			sizer.Show(item, 1)
			
			
	def addTrack(self, label, n = 0):
		"""
		Adds a track to the timeline
		"""    
		if label == "":
			label = "Timepoints %d" % len(self.timepointTracks)
		if not self.haveTp:
			# Add the sizers to which the tracks will be added
			# this way we don't need to for example shuffle
			# spline and keyframe tracks if timepoint tracks need
			# to be changed
			self.sizer.Add(self.timepointSizer, (1, 0), flag = wx.EXPAND | wx.ALL)
			self.haveTp = 1
		tr = TimepointTrack(label, self, number = 1, timescale = self.timeScale, \
							control = self.control, height = 55)
		
		self.timeScale.setOffset(tr.getLabelWidth())
		self.splinepointTrackAmnt = len(self.splinepointTracks)
		self.timepointTrackAmnt = len(self.timepointTracks)
		self.keyframeTrackAmnt = len(self.keyframeTracks)
		# Move the splinepoints down by one step

		self.timepointSizer.Add(tr, (self.timepointTrackAmnt, 0), flag = wx.EXPAND | wx.ALL)
		tr.setColor((56, 196, 248))
		if self.dataUnit:
			#print "Setting dataunit",self.dataUnit
			tr.setDataUnit(self.dataUnit)
		
		if n:
			tr.setItemAmount(n)        
		
		self.FitInside()
		self.Layout()            
		
		self.timepointTracks.append(tr)
		self.control.window.updateMenus()
		#print "almost done"
		if self.dataUnit:
			tr.showThumbnail(True)
		return tr
			
	def addSplinepointTrack(self, label):
		"""
		Description:
		"""
		if not self.haveSp:
			# Add the sizers to which the tracks will be added
			# this way we don't need to for example shuffle
			# spline and keyframe tracks if timepoint tracks need
			# to be changed
			self.sizer.Add(self.splineSizer, (2, 0), flag = wx.EXPAND | wx.ALL)
			self.havedSp = 1
			
		if label == "":
			label = "Camera Path %d" % len(self.splinepointTracks)
		tr = SplineTrack(label, self, number = 1, timescale = self.timeScale, control = self.control, height = 55)
		self.timeScale.setOffset(tr.getLabelWidth())
		tr.setColor((56, 196, 248))
		self.splinepointTrackAmnt = len(self.splinepointTracks)
		self.timepointTrackAmnt = len(self.timepointTracks)
		self.keyframeTrackAmnt = len(self.keyframeTracks)

		self.splineSizer.Add(tr, (self.splinepointTrackAmnt, 0), flag = wx.EXPAND | wx.ALL)
		
		self.FitInside()
		self.Layout()
		#self.SetupScrolling()
		self.splinepointTracks.append(tr)    
		self.control.window.updateMenus()
		return tr

	def addKeyframeTrack(self, label):
		"""
		Description:
		"""
		if not self.haveKf:
			# Add the sizers to which the tracks will be added
			# this way we don't need to for example shuffle
			# spline and keyframe tracks if timepoint tracks need
			# to be changed
			self.sizer.Add(self.keyframeSizer, (3, 0), flag = wx.EXPAND | wx.ALL)
			self.haveKf = 1

		if label == "":
			label = "Keyframe %d" % len(self.keyframeTracks)
		tr = KeyframeTrack(label, self, number = 1, timescale = self.timeScale, \
							control = self.control, height = 55)
		self.timeScale.setOffset(tr.getLabelWidth())
		self.keyframeTrackAmnt = len(self.keyframeTracks)
		self.timepointTrackAmnt = len(self.timepointTracks)
		self.splinepointTrackAmnt = len(self.splinepointTracks)
		self.keyframeSizer.Add(tr, (self.keyframeTrackAmnt, 0), flag = wx.EXPAND | wx.ALL)
		
		self.FitInside()
		self.Layout()
		self.keyframeTracks.append(tr)    
		self.control.window.updateMenus()
		
		return tr        
		
	def getLargestTrackLength(self, cmptrack):
		"""
		Return the length of the largest track that is the
					 same type as the argument, but not the same
		"""
		tracks = []
		tracks.extend(self.timepointTracks)
		tracks.extend(self.splinepointTracks)
		tracks.extend(self.keyframeTracks)
		ret = 0
		for track in tracks:
			if track != cmptrack and track.trackType == cmptrack.trackType and len(track.items):
				item = track.items[-1]
				x, y = item.GetPosition()
				w, h = item.GetSize()
				curr = x + w - track.getLabelWidth()
				if ret < curr:
					ret = curr
		return ret
			
	def setDisabled(self, flag):
		"""
		Disables / Enables this timeline
		"""
		self.timeScale.setDisabled(flag)

	def setAnimationMode(self, flag):
		"""
		Sets animation mode on or off. This affects the spline points
					 track.
		"""
		self.setDisabled(not flag)
		if len(self.splinepointTracks):
			for track in self.splinepointTracks:
				track.setEnabled(flag)
		 
		self.Refresh()
		#self.Layout()
		#self.sizer.Fit(self)#self.SetScrollbars(20,0,tx/20,0)
	
	def clearTracks(self):
		"""
		Remove all tracks
		"""    
		self.control.setSplineInteractionCallback(None)
		for track in self.timepointTracks:
			self.removeTrack(track)
		for track in self.splinepointTracks:
			self.removeTrack(track)
		for track in self.keyframeTracks:
			self.removeTrack(track)
		self.splinepointTracks = []
		self.timepointTracks = []
		self.keyframeTracks = []
		
	def removeTrack(self, track, reorder = 0):
		"""
		Remove a track from the GUI
		"""    
		if track in self.timepointTracks:
			sizer = self.timepointSizer
			lst = self.timepointTracks
			amnt = self.timepointTrackAmnt
		elif track in self.splinepointTracks:
			sizer = self.splineSizer
			lst = self.splinepointTracks            
			amnt = self.splinepointTrackAmnt
		else:
			sizer = self.keyframeSizer
			lst = self.keyframeTracks
			amnt = self.keyframeTrackAmnt
		sizer.Show(track, 0)
		sizer.Detach(track)
		track.remove()
		if reorder:
			pos = lst.index(track)
			self.moveTracks(sizer, pos + 1, pos, len(lst[pos + 1:]))
			amnt -= 1
			self.timepointTrackAmnt -= 1                    
			lst.remove(track)
			self.Layout()

	def setDataUnit(self, dataUnit):
		"""
		Sets the dataunit on this timeline
		"""
		self.dataUnit = dataUnit
		for track in self.timepointTracks:
			track.setDataUnit(dataUnit)
			track.showThumbnail(True)
		
	def onSetDuration(self, obj, evt, duration):
		"""
		Method to set the timeline duration
		"""
		if self.seconds != duration:
			self.seconds = duration
			self.configureTimeline(duration, self.frames)
		
	def onSetFrames(self, obj, evt, frames):
		"""
		Method to set the timeline duration
		"""
		self.frames = frames
		
	def reconfigureTimeline(self):
		"""
		Method to reconfigure items on timeline with
					 the same duration and frame amount
		"""    
		self.configureTimeline(self.control.getDuration(), self.control.getFrames())
	
		
	def configureTimeline(self, seconds, frames):
		"""
		Method that sets the duration of the timeline to
					 given amount of seconds, and the frame amount to
					 given amount of frames
		"""
		self.seconds = seconds
		self.frames = frames
		self.timeScale.setDuration(seconds)
		tx, ty = self.timeScale.GetSize()
		print "configureTimeline(", seconds,",",frames,")"
		for i in self.timepointTracks + self.splinepointTracks + self.keyframeTracks:
			if i:
				i.setDuration(seconds, frames)
#		for sizer in [self.timepointSizer, self.splineSizer, self.keyframeSizer]:
#			print "Size=", sizer.GetSize()

#		self.Layout()
#		self.Refresh()

	def __str__(self):
		"""
		Return string representation of self
		"""        
		s = "Timepoint tracks: {"
		s += ", ".join(map(str, self.timepointTracks))
		s += "}\n"
		s += "Splinepoint tracks: {"
		s += ", ".join(map(str, self.splinepointTracks))
		s += "}\n"
		s += "Keyframe tracks: {"
		s += ", ".join(map(str, self.keyframeTracks))
		s += "}\n"
		return s
	
	def __getstate__(self):
		"""
		Return the dict that is to be pickled to disk
		"""      
		odict = {}
		keys = [""]
		self.timepointTrackAmnt = len(self.timepointTracks)
		self.splinepointTrackAmnt = len(self.splinepointTracks)
		self.keyframeTrackAmnt = len(self.keyframeTracks)
		for key in ["timepointTracks", "splinepointTracks", "splinepointTrackAmnt", \
					"timepointTrackAmnt", "keyframeTracks", "keyframeTrackAmnt"]:
			odict[key] = self.__dict__[key]
		return odict        
 
