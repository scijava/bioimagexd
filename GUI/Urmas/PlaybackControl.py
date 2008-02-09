"""
 Unit: PlaybackControl
 Project: BioImageXD
 Created: 25.02.2006, KP
 Description:

 URM/AS - The Unified Rendering Manager / Animator for Selli
 
 This is a timeline based GUI for controlling the rendering of datasets. The GUI allows users
 to specify a path for the camera to follow (using Heikki Uuksulainen's MayaVi animator code)
 and also allows them to produce videos of the rendering using ffmpeg.
 
 This is the playback control panel for Urmas
 
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
t.
"""
__author__ = "BioImageXD Project"
__version__ = "$Revision: 1.22 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import wx
import lib.messenger
import os
import time
import scripting
import wx.lib.buttons as buttons
import platform

class PlaybackControl(wx.Panel):
	"""
	A panel that contains a slider and stop and play/pause buttons 
	"""
	def __init__(self, parent, n):    
		"""
		Method that initializes the class
		"""        
		wx.Panel.__init__(self, parent, -1, size = (1024, 34))
		#wx.SashLayoutWind#ow.__init__(self,parent,-1)
		self.sizer = wx.BoxSizer(wx.HORIZONTAL)
		#self.SetBackgroundColour((255,0,0))
		iconpath = scripting.get_icon_dir()
		self.rangeMax = n
		self.buttonPanel = wx.Panel(self, -1, size = (48, -1), style = wx.RAISED_BORDER)
		self.buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
		self.buttonPanel.SetSizer(self.buttonSizer)
		self.buttonPanel.SetAutoLayout(1)
		
		self.nextIcon = wx.Image(os.path.join(iconpath, "next.gif"), wx.BITMAP_TYPE_GIF).ConvertToBitmap()
		self.prevIcon = wx.Image(os.path.join(iconpath, "previous.gif"), wx.BITMAP_TYPE_GIF).ConvertToBitmap()
		
		self.playIcon = wx.Image(os.path.join(iconpath, "player_play.gif"), wx.BITMAP_TYPE_GIF).ConvertToBitmap()
		self.pauseIcon = wx.Image(os.path.join(iconpath, "player_pause.gif"), wx.BITMAP_TYPE_GIF).ConvertToBitmap()
		#self.stopicon = wx.Image(os.path.join(iconpath,"stop.gif"),wx.BITMAP_TYPE_GIF).ConvertToBitmap()
		self.beginIcon =  wx.Image(os.path.join(iconpath, "player_start.gif"), wx.BITMAP_TYPE_GIF).ConvertToBitmap()
		self.endIcon =  wx.Image(os.path.join(iconpath, "player_end.gif"), wx.BITMAP_TYPE_GIF).ConvertToBitmap()
		
		#self.playpause=buttons.GenBitmapButton(self,-1,self.playicon)
		#self.stop = buttons.GenBitmapButton(self,-1,self.stopicon)
		
		self.beginButton = buttons.GenBitmapButton(self.buttonPanel, -1, self.beginIcon, style = wx.BORDER_NONE)
		self.prevButton = buttons.GenBitmapButton(self.buttonPanel, -1, self.prevIcon, style = wx.BORDER_NONE)
		self.playButton = buttons.GenBitmapButton(self.buttonPanel, -1, self.playIcon, style = wx.BORDER_NONE)
		self.pauseButton = buttons.GenBitmapButton(self.buttonPanel, -1, self.pauseIcon, style = wx.BORDER_NONE)
		self.nextButton = buttons.GenBitmapButton(self.buttonPanel, -1, self.nextIcon, style = wx.BORDER_NONE)
		self.endButton = buttons.GenBitmapButton(self.buttonPanel, -1, self.endIcon, style = wx.BORDER_NONE)
		
		self.nextButton.Bind(wx.EVT_BUTTON, self.onNextFrame)
		self.prevButton.Bind(wx.EVT_BUTTON, self.onPrevFrame)
		self.beginButton.Bind(wx.EVT_BUTTON, self.onFirstFrame)
		self.endButton.Bind(wx.EVT_BUTTON, self.onLastFrame)
		self.playButton.Bind(wx.EVT_BUTTON, self.onPlay)
		self.pauseButton.Bind(wx.EVT_BUTTON, self.onPause)
		
		self.timeslider = wx.Slider(self, size = (32, -1), value = 1, minValue = 1, maxValue = n,
		style = wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS)
		
		#self.sizer.Add(self.playpause,)
		#self.sizer.Add(self.stop)
		
		for btn in [self.beginButton, self.prevButton, self.playButton, self.pauseButton, 
					self.nextButton, self.endButton]:
			btn.SetBestSize((24, 24))
			self.buttonSizer.Add(btn)
		self.buttonSizer.Fit(self.buttonPanel)
		
		
		self.sizer.Add(self.buttonPanel, 0, flag = wx.ALIGN_CENTER_VERTICAL)
		self.sizer.Add(self.timeslider, 1, flag = wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
		
		self.callback = None
		self.changing = 0
		
		#self.playpause.Bind(wx.EVT_BUTTON,self.onPlayPause)
		#self.stop.Bind(wx.EVT_BUTTON,self.onStop)
		#self.stop.Enable(0)
		self.pauseButton.Enable(0)
		
		self.SetSizer(self.sizer)
		self.SetAutoLayout(1)
		self.sizer.Fit(self)
		
		lib.messenger.connect(None, "set_timeslider_value", self.onSetTimeslider)
		lib.messenger.connect(None, "set_frames", self.onSetFrames)
		lib.messenger.connect(None, "timepoint_changed", self.onSetTimepoint)        
		lib.messenger.connect(None, "set_play_mode", self.onSetPlay)
		
		
	def onSetPlay(self, obj, evt, *args):
		"""
		A callback for setting the control panel to play mode
		"""     
		self.onPlay(None, no_events = 1)
	
		
	def bindTimeslider(self, method, all = 0):
		"""
		Bind the timeslider to a method
		"""     
		if not all and platform.system() in ["Windows", "Darwin"]:
			self.timeslider.Unbind(wx.EVT_SCROLL_ENDSCROLL)
			#self.timeslider.Unbind(wx.EVT_SCROLL_THUMBRELEASE)
			self.timeslider.Bind(wx.EVT_SCROLL_ENDSCROLL, method)
			#self.timeslider.Bind(wx.EVT_SCROLL_THUMBRELEASE,method)
		else:
			self.timesliderMethod = method
			self.timeslider.Unbind(wx.EVT_SCROLL)
			self.timeslider.Bind(wx.EVT_SCROLL, self.delayedTimesliderEvent)        
		
	def delayedTimesliderEvent(self, event):
		"""
		Set the timepoint to be shown
		"""
		self.changing = time.time()
		wx.FutureCall(200, lambda e = event, s = self:s.timesliderMethod(e))        
			   
	def onFirstFrame(self, evt):
		"""
		Go to the first frames
		"""
		self.timeslider.SetValue(0)
		if self.timesliderMethod:
			self.timesliderMethod()
		
	def onLastFrame(self, evt):
		"""
		Go to the first frames
		"""
		self.timeslider.SetValue(self.rangeMax)    
		if self.timesliderMethod:
			self.timesliderMethod()
			
	def onNextFrame(self, evt):
		"""
		Go to the next frame
		"""
		n = self.timeslider.GetValue()
		if n + 1 <= self.rangeMax:
			self.timeslider.SetValue(n + 1)
			if self.timesliderMethod:
				self.timesliderMethod()
		
	def onPrevFrame(self, evt):
		"""
		Go to the prev frame
		"""
		n = self.timeslider.GetValue()
		if n > 0:        
			self.timeslider.SetValue(n - 1)
			if self.timesliderMethod:
				self.timesliderMethod()
		
	def onPlay(self, evt, no_events = 0):
		"""
		Callback for when the play icon is pressed
		"""
		self.pauseButton.Enable(1)
		self.playButton.Enable(0)
		if not no_events:
			lib.messenger.send(None, "playback_play")
	
	def onPause(self, evt, no_events = 0):
		"""
		Callback for when the pause icon is pressed
		"""
		self.playButton.Enable(1)
		self.pauseButton.Enable(0)
		lib.messenger.send(None, "playback_pause")
			
			
	def onSetTimeslider(self, obj, event, tp):
		"""
		Update the timeslider according to an event
		"""
		self.timeslider.SetValue(tp) 
		
	def onSetFrames(self, obj, event, r1):
		"""
		Set the range that the time slider shows based on the number of frames
		"""        
		self.rangeMax = r1
		self.timeslider.SetRange(0, r1)
		self.timeslider.Refresh()        


	def onSetTimepoint(self, obj, event, timepoint):
		"""
		Update the timepoint according to an event
		"""
		curr = self.timeslider.GetValue()
		if curr - 1 != timepoint:
			self.timeslider.SetValue(timepoint + 1)
