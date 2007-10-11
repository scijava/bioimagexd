#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

"""
 Unit: UrmasWindow
 Project: BioImageXD
 Created: 10.02.2005, KP
 Description:

 URM/AS - The Unified Rendering Manager / Animator for Selli
 
 This is a timeline based GUI for controlling the rendering of datasets. The GUI allows users
 to specify a path for the camera to follow (using Heikki Uuksulainen's MayaVi animator code)
 and also allows them to produce videos of the rendering using ffmpeg.
 
 This is the window that contains the Urmas.
 
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
t.
"""
__author__ = "BioImageXD Project"
__version__ = "$Revision: 1.22 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import wx
import GUI.Urmas.Timeline
import TimelinePanel
import Logging
import UrmasControl
import VideoGeneration
import wx.lib.scrolledpanel
import GUI.Dialogs
import UrmasPalette
import PlaybackControl
from GUI import MenuManager
import lib.messenger
import time
import scripting

class UrmasWindow(wx.lib.scrolledpanel.ScrolledPanel):
	"""
	Created: 10.02.2005, KP
	Description: A window for controlling the rendering/animation/movie generation.
				 The window has a notebook with different pages for rendering and
				 animation modes, and a page for configuring the movie generation.
	"""
	def __init__(self, parent, menumanager, taskwin, visualizer):
		self.scrolled = 1
		self.frozen = 0
		wx.lib.scrolledpanel.ScrolledPanel.__init__(self, parent, -1)
		self.parent = parent
		self.taskWin = taskwin
		self.videoGenerationPanel = None
		self.visualizer = visualizer
		self.Unbind(wx.EVT_CHILD_FOCUS)
		self.menuManager = menumanager
		scripting.mainWindow.Enable(0)
		self.createMenu(menumanager)
		self.lastFrameTime = 0
		self.delayed = 0
		scripting.animator = self
		self.control = UrmasControl.UrmasControl(self, visualizer)

		self.sizer = wx.BoxSizer(wx.VERTICAL)
		self.palette = UrmasPalette.UrmasPalette(self, self.control)
		self.sizer.Add(self.palette, 0, flag = wx.EXPAND)

		self.splitter = TimelinePanel.SplitPanel(self, -1)
		w = self.GetSize()[0]
		self.timeline = GUI.Urmas.Timeline.Timeline(self.splitter, self.control, size = (768, 50))
		self.timelinePanel = TimelinePanel.TimelinePanel(self.splitter, self.control, size = (1024, 500), p = self.parent)
		self.timelinePanel.timeline = self.timeline
		self.splitter.SplitHorizontally(self.timeline, self.timelinePanel, -300)
		
		self.control.setTimelinePanel(self.timelinePanel)
		
		self.sizer.Add(self.splitter, 1, flag = wx.EXPAND)

		self.control.setAnimationMode(1)

		self.visualizer.sliderPanel.Show(0)
		n = self.control.getDuration()
	
		self.controlpanel = PlaybackControl.PlaybackControl(self.visualizer.sliderWin, n * 10)
		self.controlpanel.bindTimeslider(self.onShowFrame, all = 1)
		s = self.visualizer.sliderWin.GetSize()
		self.visualizer.setCurrentSliderPanel(self.controlpanel)
		self.controlpanel.SetSize(s)
		
		lib.messenger.connect(None, "video_generation_close", self.onVideoGenerationClose)
		
		self.SetSizer(self.sizer)
		self.SetAutoLayout(1)
		if self.scrolled:
			self.SetupScrolling()
		
		self.splitter.UpdateSize()
		wx.CallAfter(self.updateRenderWindow)
		
		
	def enable(self, flag):
		"""
		Created: 26.04.2006, KP
		Description: Enable / Disable rendering of this window	  
		"""
		if flag and self.frozen:
			self.frozen = 0
			self.Thaw()
		elif not flag:
			self.frozen = 1
			self.Freeze()
		
	def enableRendering(self, flag):
		"""
		Created: KP
		Description: Enable or disable the rendering in the preview window
		"""
		if flag:
			self.timelinePanel.splineEditor.iren.Enable()
		else:
			self.timelinePanel.splineEditor.iren.Disable()
			
	def updateRenderWindow(self, *args):
		"""
		Created: 15.12.2005, KP
		Description: Updates the render window camera settings
					 after all initialization is done. For some
					 reason, it has to be done here to take effect.					   
		"""
		Logging.info("Setting view of render window", kw = "animator")
		scripting.mainWindow.Enable(1)
		self.timelinePanel.wxrenwin.setView((1, 1, 1, 0, 0, 1))
		
	def onShowFrame(self, evt = None):
		"""
		Created: 15.08.2005, KP
		Description: Sets the frame to be shown
		"""
		t = time.time()
		if t - self.lastFrameTime < 0.2:
			return
		self.lastFrameTime = t
		frame = self.controlpanel.timeslider.GetValue()
		
		spf = self.control.getSecondsPerFrame()
		tp = int(frame * spf)
		lib.messenger.send(None, "show_time_pos", tp)
		lib.messenger.send(None, "render_time_pos", tp)
		self.timelinePanel.timeline.Refresh()
		
	def cleanMenu(self):
		"""
		Created: 06.04.2005, KP
		Description: Removes the menu items from menu
		"""
		mgr = self.menuManager
		
		mgr.remove(MenuManager.ID_PREFERENCES)
		mgr.remove(MenuManager.ID_ADD_SPLINE)
		mgr.remove(MenuManager.ID_ADD_TIMEPOINT)
		mgr.remove(MenuManager.ID_ADD_TRACK)
		mgr.remove(MenuManager.ID_ANIMATE)

		mgr.remove(MenuManager.ID_FIT_TRACK)
	
		mgr.remove(MenuManager.ID_MIN_TRACK)
		mgr.remove(MenuManager.ID_OPEN_PROJECT)
		mgr.remove(MenuManager.ID_RENDER_PROJECT)
		mgr.remove(MenuManager.ID_RENDER_PREVIEW)
#		mgr.remove(MenuManager.ID_SAVE)		No ID_SAVE in GUI.MenuManager.py
		mgr.remove(MenuManager.ID_SET_TRACK)
		mgr.remove(MenuManager.ID_SET_TRACK_RELATIVE)
		mgr.remove(MenuManager.ID_MAINTAIN_UP)
		mgr.remove(MenuManager.ID_SPLINE_CLOSED)
		mgr.remove(MenuManager.ID_SPLINE_SET_BEGIN)
		mgr.remove(MenuManager.ID_SPLINE_SET_END)
		mgr.remove(MenuManager.ID_CLOSE_PROJECT)

		mgr.removeMenu("track")
		#mgr.removeMenu("rendering")
		#mgr.removeMenu("camera")

	def createMenu(self, mgr):
		"""
		Created: 06.04.2005, KP
		Description: Creates a menu for the window
		"""
		mgr.createMenu("track", "&Track", before = "help")
		#mgr.createMenu("rendering","&Rendering",before="help")
		#mgr.createMenu("camera","&Camera",before="help")
		
	  
		mgr.addMenuItem("file", MenuManager.ID_OPEN_PROJECT, "Open project...", "Open a BioImageXD Animator Project", self.onMenuOpenProject, before = MenuManager.ID_IMPORT_IMAGES)
		mgr.addMenuItem("file", MenuManager.ID_SAVE_PROJECT, "Save project as...", "Save current BioImageXD Animator Project", self.onMenuSaveProject, before = MenuManager.ID_IMPORT_IMAGES)
		mgr.addMenuItem("file", MenuManager.ID_CLOSE_PROJECT, "Close project", "Close this Animator Project", self.onMenuCloseProject, before = MenuManager.ID_IMPORT_IMAGES)
		mgr.addSeparator("file", before = MenuManager.ID_IMPORT_IMAGES)
		
		mgr.createMenu("addtrack", "&Add Track", place = 0)
		
		mgr.addMenuItem("addtrack", MenuManager.ID_ADD_TIMEPOINT, "Timepoint track", "Add a timepoint track to the timeline", self.onMenuAddTimepointTrack)
		mgr.addMenuItem("addtrack", MenuManager.ID_ADD_SPLINE, "Camera path track", "Add a camera path track to the timeline", self.onMenuAddSplineTrack)
		mgr.addMenuItem("addtrack", MenuManager.ID_ADD_KEYFRAME, "Keyframe track", "Add a keyframe track to the timeline", self.onMenuAddKeyframeTrack)		   
		mgr.addSubMenu("track", "addtrack", "&Add track", MenuManager.ID_ADD_TRACK)
		#mgr.addSeparator("track")
		
		mgr.createMenu("sizetrack", "&Item sizes", place = 0)
		mgr.addSubMenu("track", "sizetrack", "&Item sizes", MenuManager.ID_ITEM_SIZES)
		
		mgr.addMenuItem("sizetrack", MenuManager.ID_FIT_TRACK, "Expand to maximum", "Expand the track to encompass the whole timeline", self.onMaxTrack)
		mgr.addMenuItem("sizetrack", MenuManager.ID_FIT_TRACK_RATIO, "Expand to track length (keep ratio)", "Expand the track to encompass the whole timeline while retainining the relative sizes of each item.", self.onMaxTrackRatio)		
		mgr.addMenuItem("sizetrack", MenuManager.ID_MIN_TRACK, "Shrink to minimum", "Shrink the track to as small as possible", self.onMinTrack)
		mgr.addMenuItem("sizetrack", MenuManager.ID_SET_TRACK, "Set item size", "Set each item on this track to be of given size", self.onSetTrack)
		mgr.addMenuItem("sizetrack", MenuManager.ID_SET_TRACK_TOTAL, "Set total length", "Set total length of items on this track", self.onSetTrackTotal)
		mgr.addMenuItem("sizetrack", MenuManager.ID_SET_TRACK_RELATIVE, "Set to physical length", "Set the length of items on this track to be relative to their physical length", self.onSetTrackRelative)

		mgr.createMenu("shuffle", "&Shift items", place = 0)
		mgr.addSubMenu("track", "shuffle", "Shift items", MenuManager.ID_ITEM_ORDER)
		mgr.addMenuItem("shuffle", MenuManager.ID_ITEM_ROTATE_CW, "&Left", self.onShiftClockwise)
		mgr.addMenuItem("shuffle", MenuManager.ID_ITEM_ROTATE_CCW, "&Right", self.onShiftCounterClockwise)

		mgr.addSeparator("track")
		mgr.addMenuItem("track", MenuManager.ID_DELETE_TRACK, "&Remove track", "Remove the track from timeline", self.onMenuRemoveTrack)
		mgr.addMenuItem("track", MenuManager.ID_DELETE_ITEM, "&Remove item", "Remove the selected track item", self.onMenuRemoveTrackItem)
		
	
		mgr.addSeparator("track")	
		mgr.addMenuItem("track", MenuManager.ID_SPLINE_SET_BEGIN, "&Begin at the end of previous path", "Set this camera path to begin where the previous path ends", self.onMenuSetBegin)
		mgr.addMenuItem("track", MenuManager.ID_SPLINE_SET_END, "&End at the beginning of next path", "Set this camera path to end where the next path starts", self.onMenuSetEnd)
		mgr.addSeparator("track")
		mgr.addMenuItem("track", MenuManager.ID_SPLINE_CLOSED, "&Closed path", "Set the camera path to open / closed.", self.onMenuClosedSpline, check = 1)
		mgr.addMenuItem("track", MenuManager.ID_MAINTAIN_UP, "&Maintain up direction", self.onMenuSetMaintainUp, check = 1)
			
		mgr.disable(MenuManager.ID_SPLINE_SET_BEGIN)
		mgr.disable(MenuManager.ID_SPLINE_SET_END)
		mgr.disable(MenuManager.ID_ITEM_ROTATE_CCW)
		mgr.disable(MenuManager.ID_ITEM_ROTATE_CW)

	def updateMenus(self):
		"""
		Created: 18.04.2005, KP
		Description: A method to update the state of menu items
		"""
		spltracks = len(self.control.timeline.getSplineTracks())
		flag = (spltracks >= 2)
		#print "updateMenus()",spltracks
		self.menuManager.enable(MenuManager.ID_SPLINE_SET_BEGIN)
		self.menuManager.enable(MenuManager.ID_SPLINE_SET_END)
		active = self.control.getSelectedTrack()
		if active and hasattr(active, "maintainUpDirection"):
			self.menuManager.check(MenuManager.ID_MAINTAIN_UP, active.maintainUpDirection)
		if active and hasattr(active, "closed"):
			self.menuManager.check(MenuManager.ID_SPLINE_CLOSED, active.closed)
		
		method = None
		if active and active.getClosed():
			method = self.menuManager.enable
		elif active:
			method = self.menuManager.disable
		if method:	 
			method(MenuManager.ID_ITEM_ROTATE_CCW)
			method(MenuManager.ID_ITEM_ROTATE_CW)
 
	def onShiftClockwise(self, event):
		"""
		Created: 15.12.2005, KP
		Description: Shift items in current track one step clockwise
		"""
		active = self.control.getSelectedTrack()
		if not active:
			GUI.Dialogs.showwarning(self, "You need to select a track that you wish to perform the operation on.", "No track selected")
			return
		active.shiftItems(1)
		
	def onShiftCounterClockwise(self, event):
		"""
		Created: 15.12.2005, KP
		Description: Shift items in current track one step counter clockwise
		"""
		active = self.control.getSelectedTrack()
		if not active:
			GUI.Dialogs.showwarning(self, "You need to select a track that you wish to perform the operation on.", "No track selected")
			return
		active.shiftItems(-1)		
	
	def onMenuRender(self, event):
		"""
		Created: 19.04.2005, KP
		Description: Render this project
		"""
		if not self.videoGenerationPanel:
			w, h = self.taskWin.GetSize()
			self.taskWin.SetDefaultSize((300, h))
			self.videoGenerationPanel = VideoGeneration.VideoGeneration(self.taskWin, self.control, self.visualizer)
			self.videoGenerationPanel.SetSize((300, h))
			self.videoGenerationPanel.Show()
			self.visualizer.mainwin.OnSize(None)
			

	def onVideoGenerationClose(self, obj, evt, *args):
		"""
		Created: 15.12.2005, KP
		Description: Callback for closing the video generation
		""" 
	
		w, h = self.taskWin.GetSize()
		if self.videoGenerationPanel:
			self.taskWin.SetDefaultSize((0, h))
			scripting.videoGeneration = None
			
			self.visualizer.mainwin.OnSize(None)
			# destroy the video generation panel if the rendering wasn't aborted
			# if it was aborted, let the panel destroy itself			 
			if not (self.videoGenerationPanel.rendering and self.videoGenerationPanel.abort):
				self.videoGenerationPanel.Destroy()
				self.videoGenerationPanel = None
			else:
				self.videoGenerationPanel.Show(0)
			if self.visualizer.getCurrentModeName() != "animator":
				self.visualizer.setVisualizationMode("animator")

		self.visualizer.getCurrentMode().lockSliderPanel(0)
		self.visualizer.OnSize()
		
		
		
	def onMinTrack(self, evt):
		"""
		Created: 19.04.2005, KP
		Description: Callback function for menu item minimize track
		"""
		active = self.control.getSelectedTrack()
		if not active:
			GUI.Dialogs.showwarning(self, "You need to select a track that you wish to perform the operation on.", "No track selected")
			return
		active.setToSize()

	def onSetTrack(self, evt):
		"""
		Created: 19.04.2005, KP
		Description: Callback function for menu item minimize track
		"""

		dlg = wx.TextEntryDialog(self, "Set duration of each item (seconds):", "Set item duration")
		dlg.SetValue("5.0")
		val = 5
		if dlg.ShowModal() == wx.ID_OK:
			try:
				val = float(dlg.GetValue())
			except:
				return
		spf = self.control.getSecondsPerFrame()
		# Make it so that you cant set the item smaller than a single frame
		if val < spf:
			val = spf
					
		
		#print "Setting to size ",size,"(",val,"seconds)"
		active = self.control.getSelectedTrack()
		if not active:
			GUI.Dialogs.showwarning(self, "You need to select a track that you wish to perform the operation on.", "No track selected")
			return		  
		# Make sure you cant use a value that would make the items expand beyond duration
		n = active.getNumberOfTimepoints()
		
		pps = self.control.getPixelsPerSecond()
		#w*=pps
		startOfTrack = active.getStartOfTrack()
		startOfTrack /= float(pps)
		w = float(self.control.getDuration() - startOfTrack) / float(n)
		
	
		if val > w:
			val = w
		
		size = int(val * pps)		 
					
		active.setToSize(size)
		
	def onSetTrackRelative(self, evt):
		"""
		Created: 25.06.2005, KP
		Description: Set the length of items in a track relative to their physical size
		"""
		active = self.control.getSelectedTrack()
		if not active:
			GUI.Dialogs.showwarning(self, "You need to select a track that you wish to perform the operation on.", "No track selected")
			return
		
		startOfTrack = active.getStartOfTrack()
		pps = self.control.getPixelsPerSecond()
		startOfTrack /= float(pps)
		
		duration = self.control.getDuration()
		duration -= startOfTrack
		
		dlg = wx.TextEntryDialog(self, "Set total duration (seconds) of items in track:", "Set track duration")
		dlg.SetValue("%.2f" % duration)
		val = 5
		if dlg.ShowModal() == wx.ID_OK:
			try:
				val = float(dlg.GetValue())
			except:
				return
		size = int(val * self.control.getPixelsPerSecond())
		#print "Setting to size ",size,"(",val,"seconds)"
	
			
		active.setToRelativeSize(size)
		

	def onSetTrackTotal(self, evt):
		"""
		Created: 23.06.2005, KP
		Description: Set the total length of items in a track
		"""
		active = self.control.getSelectedTrack()
		if not active:
			GUI.Dialogs.showwarning(self, "You need to select a track that you wish to perform the operation on.", "No track selected")
			return				  

		d = self.control.getDuration()
		dlg = wx.TextEntryDialog(self, "Set total duration (seconds) of items in track:", "Set track duration")
		dlg.SetValue("%.2f" % d)
		val = 5
		if dlg.ShowModal() == wx.ID_OK:
			try:
				val = int(dlg.GetValue())
			except:
				return
		size = val * self.control.getPixelsPerSecond()
		#print "Setting to size ",size,"(",val,"seconds)"
		active.setToSizeTotal(size)


	def onMaxTrack(self, evt):
		"""
		Created: 19.04.2005, KP
		Description: Callback function for menu item minimize track
		"""
		active = self.control.getSelectedTrack()
		if not active:
			GUI.Dialogs.showwarning(self, "You need to select a track that you wish to perform the operation on.", "No track selected")
			return		  
		active.expandToMax()
	
	def onMaxTrackRatio(self, evt):
		"""
		Created: 19.04.2005, KP
		Description: Callback function for menu item minimize track
		"""
		active = self.control.getSelectedTrack()
		if not active:
			GUI.Dialogs.showwarning(self, "You need to select a track that you wish to perform the operation on.", "No track selected")
			return		  
		active.expandToMax(keep_ratio = 1)
		
	def onMenuSetBegin(self, evt):
		"""
		Created: 18.04.2005, KP
		Description: Callback function for menu item begin at end of previous
		"""
		active = self.control.getSelectedTrack()
		self.control.timeline.setBeginningToPrevious(active)
		
	def onMenuSetEnd(self, evt):
		"""
		Created: 18.04.2005, KP
		Description: Callback function for menu item end at beginning of next
		"""
		active = self.control.getSelectedTrack()
		self.control.timeline.setEndToNext(active)
		
	def onMenuSetMaintainUp(self, evt):
		"""
		Created: 18.04.2005, KP
		Description: Set the track to maintain up direction
		"""
		active = self.control.getSelectedTrack()
		if not active:
			GUI.Dialogs.showwarning(self, "You need to select a track that you wish to perform the operation on.", "No track selected")
			return		  
		if hasattr(active, "setMaintainUpDirection"):
			active.setMaintainUpDirection(evt.IsChecked())
		
	def onMenuClosedSpline(self, evt):
		"""
		Created: 14.04.2005, KP
		Description: Callback function for menu item camera path is closed
		"""
		track = self.control.getSelectedTrack()
		if hasattr(track, "setClosed"):
			track.setClosed(evt.IsChecked())
		
	def onMenuRemoveTrack(self, evt):
		"""
		Created: 18.07.2005, KP
		Description: Callback function for removing a track
		"""
		track = self.control.getSelectedTrack()
		if track:
			self.control.timeline.removeTrack(track, 1)
		

	def onMenuRemoveTrackItem(self, evt):
		"""
		Created: 31.01.2006, KP
		Description: Callback function for removing an item from a track
		"""
		track = self.control.getSelectedTrack()
		if track:
			track.removeActiveItem()
				
		
	def onMenuAddSplineTrack(self, evt):
		"""
		Created: 13.04.2005, KP
		Description: Callback function for adding camera path track
		"""
		self.control.timeline.addSplinepointTrack("")

	def onMenuAddKeyframeTrack(self, evt):
		"""
		Created: 18.04.2005, KP
		Description: Callback function for adding keyframe track
		"""
		self.control.timeline.addKeyframeTrack("")
		
	def onMenuAddTimepointTrack(self, evt):
		"""
		Created: 13.04.2005, KP
		Description: Callback function for adding timepoint track
		"""
		self.control.timeline.addTrack("")
				
	def onMenuCloseProject(self, event):
		"""
		Created: 24.06.2005, KP
		Description: Reset the animator
		"""
		self.control.resetAnimator()


	def onMenuOpenProject(self, event):
		"""
		Created: 06.04.2005, KP
		Description: Callback function for opening a project
		"""
		wc = "Rendering project (*.rxd)|*.rxd"
		name = GUI.Dialogs.askOpenFileName(self, "Open rendering project", wc, 0)
		if name:
			self.control.readFromDisk(name[0])
		
	def onMenuSaveProject(self, event):
		"""
		Created: 06.04.2005, KP
		Description: Callback function for saving a project
		"""
		wc = "Rendering Project (*.rxd)|*.rxd"
		name = None
		dlg = wx.FileDialog(self, "Save rendering project as...", defaultFile = "project.rxd", wildcard = wc, style = wx.SAVE)
		if dlg.ShowModal() == wx.ID_OK:
			name = dlg.GetPath()
		if name:
			self.control.writeToDisk(name)

	def setDataUnit(self, dataUnit):
		"""
		Created: 10.2.2005, KP
		Description: Method used to set the dataunit we're processing
		"""
		#self.timepointSelection.setDataUnit(dataUnit)
		#self.timelinePanel.setDataUnit(dataUnit)
		self.control.setDataUnit(dataUnit)
		
	