#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

"""
 Unit: RenderingConfigPanel
 Project: BioImageXD
 Created: 19.12.2005, KP
 Description:

 URM/AS - The Unified Rendering Manager / Animator for Selli
 
 This is a timeline based GUI for controlling the rendering of datasets. The GUI allows users
 to specify a path for the camera to follow (using Heikki Uuksulainen's MayaVi animator code)
 and also allows them to produce videos of the rendering using ffmpeg.
 
 The configuration panel for the rendering is implemented in this module.
 
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

#import Animator
#import CameraView
#import wx.lib.masked as masked
#import operator
#import os.path
#import PreviewFrame
#import SplineEditor
#import sys
#import Timeline
#import Track
#from Visualizer import VisualizerWindow
#from vtk.wx.wxVTKRenderWindowInteractor import wxVTKRenderWindowInteractor


import lib.messenger
from wx.lib.masked import TimeCtrl
import types
import wx

#class RenderingConfigPanel(wx.Panel):
class RenderingConfigPanel:
	"""
	Created: 04.02.2005, KP
	Description: Contains configuration options for the timeline
	"""	   
	def __init__(self, parent, control):
		self.control = control
		self.parent = parent
		#wx.Panel.__init__(self,parent,-1)#,style=wx.SUNKEN_BORDER)
		#wx.wizard.WizardPageSimple.__init__(self,parent)
		self.control.setTimelineConfig(self)
		self.sizer = wx.GridBagSizer(5, 5)
		self.fps = 12.00
		self.secs = 60
		self.parent = parent
		self.updated = 0
		self.in_fps = 0
		self.in_framecount = 0
		self.outputsizer = wx.GridBagSizer(5, 5)
		box = wx.StaticBox(self.parent, wx.HORIZONTAL, "Rendering parameters")
		self.outputstaticbox = wx.StaticBoxSizer(box, wx.HORIZONTAL)
		self.outputstaticbox.Add(self.outputsizer)
		
		self.totalFramesLabel = wx.StaticText(self.parent, -1, "Frames:")
		self.durationLabel = wx.StaticText(self.parent, -1, "Duration:")
		#self.fpsLabel=wx.StaticText(self,-1,"12 / second")

		self.totalFrames = wx.TextCtrl(self.parent, -1, "720", size = (50, -1), style = wx.TE_PROCESS_ENTER)
		self.spin = wx.SpinButton( self.parent, -1, style = wx.SP_VERTICAL , size = (-1, 25))
		self.duration = TimeCtrl(self.parent, -1, "00:01:00", fmt24hr = True, size = (50, 25), style = wx.TE_PROCESS_ENTER, spinButton = self.spin)
		
		
		self.totalFrames.Bind(wx.EVT_TEXT, self.updateFrameCount)
		self.duration.Bind(wx.EVT_TEXT, self.updateDuration)

		self.followAspect = wx.CheckBox(self.parent, -1, "Don't resize preview, only use aspect ratio.")
		toolTip = wx.ToolTip("""If this box is checked, the rendering preview window
will always be sized so that it fits into the screen and
uses the aspect ratio of the final rendered frame. If 
this is unchecked, the preview window will be resized to
be the same size as the final frame.""")
		self.followAspect.SetToolTip(toolTip)
		self.followAspect.SetValue(1)
		box = wx.BoxSizer(wx.HORIZONTAL)
		box.Add(self.duration)
		box.Add(self.spin)
		
		self.frameSizeLbl = wx.StaticText(self.parent, -1, "Frame size:")
		self.resLst = [(0, 0), (320, 240), (512, 512), (640, 480), (720, 576), (800, 600)]
		self.frameSize = wx.Choice(self.parent, -1,
		choices = ["Custom", "320 x 240", "512 x 512", "640 x 480", "720x576 (PAL)", "800 x 600"])
		self.frameSize.SetSelection(1)		  
		self.frameSize.Bind(wx.EVT_CHOICE, self.onUpdateFrameSize)
		self.outputsizer.Add(self.durationLabel, (0, 0))
		#self.outputsizer.Add(self.duration,(0,1))	 
		self.outputsizer.Add(box, (0, 1))	
		
		self.outputsizer.Add(self.totalFramesLabel, (1, 0))
		self.outputsizer.Add(self.totalFrames, (1, 1))
				
		#self.outputsizer.Add(self.fpsLabel,(2,1))
		self.frameRateLbl = wx.StaticText(self.parent, -1, "Frame rate:")
		self.frameRate = wx.TextCtrl(self.parent, -1, "%.2f" % 12, style = wx.TE_PROCESS_ENTER)
		self.frameRate.Bind(wx.EVT_TEXT, self.updateFPS)
		
		
		self.outputsizer.Add(self.frameRateLbl, (2, 0))
		self.outputsizer.Add(self.frameRate, (2, 1))
		
		self.custLbl = wx.StaticText(self.parent, -1, "Custom size:")
		self.custXLbl = wx.StaticText(self.parent, -1, "x")
		self.custX = wx.TextCtrl(self.parent, -1, "512", size = (48, -1))
		self.custY = wx.TextCtrl(self.parent, -1, "512", size = (48, -1))
		self.custX.Enable(0)
		self.custY.Enable(0)
		box = wx.BoxSizer(wx.HORIZONTAL)
		box.Add(self.custX)
		box.Add(self.custXLbl)
		box.Add(self.custY)
		
		self.outputsizer.Add(self.frameSizeLbl, (3, 0))
		self.outputsizer.Add(self.frameSize, (3, 1))
		self.outputsizer.Add(self.custLbl, (4, 0))
		self.outputsizer.Add(box, (4, 1))
		self.outputsizer.Add(self.followAspect, (5, 0))
				
		self.sizer.Add(self.outputstaticbox, (0, 0), flag = wx.EXPAND | wx.ALL)
		#self.sizer.Add(self.animationstaticbox,(0,1),flag=wx.EXPAND|wx.ALL)
		
		#self.sline=wx.StaticLine(self)
		#self.sizer.Add(self.sline,(4,0),flag=wx.EXPAND|wx.RIGHT|wx.LEFT)
		#self.sizer.Add(self.useButton,(5,0))
		
		#self.SetSizer(self.sizer)
		#self.SetAutoLayout(1)
		#self.sizer.Fit(self)
		#self.updateFormat()
		self.useSettings()
		
	def onUpdateFrameSize(self, evt):
		"""
		A callback for when the user changes the frame size
		"""		
		sel = evt.GetSelection()
		flag = (sel == 0)
		self.custX.Enable(flag)
		self.custY.Enable(flag)
		evt.Skip()
	def getFrameAmount(self):
		"""
		Return the number of frames selected
		"""		
		try:
			n = int(self.totalFrames.GetValue())
			return n
		except:
			return 0

	def setFrames(self, n):
		"""
		Set the number of frames in the GUI
		"""		   
		self.totalFrames.SetValue(str(n))
		self.useSettings()
		
	def setDuration(self, t):
		"""
		Set the duration in the GUI
		"""			   
		if type(t) != types.StringType:
			h = t / 3600
			m = t / 60
			s = t % 60
			t = "%.2d:%.2d:%.2d" % (h, m, s)
		self.duration.SetValue(t)
		self.useSettings()
	
	def useSettings(self, event = None):
		"""
		Use the GUI settings
		"""		   
		duration = -1
		frameCount = -1
		try:
			# We get a string, but pylint doesn't know that (it thinks we get a wxDateTime)
			# so we cast this to str although it is already an str
			duration = str(self.duration.GetValue())
			hh, mm, ss = map(int, duration.split(":"))
			print hh, mm, ss
			secs = hh * 3600 + mm * 60 + ss
			lib.messenger.send(None, "set_duration", secs)
		except:
			pass
		try:
			frameCount = self.totalFrames.GetValue()
			frameCount = int(frameCount)
			lib.messenger.send(None, "set_frames", frameCount)
		except:
			pass
		if duration != -1 and frameCount != -1:
			self.control.configureTimeline(secs, frameCount)

		x = -1
		y = -1
		try:
			sel = self.frameSize.GetSelection()
			if sel != 0:
				x, y = self.resLst[sel]
			else:
				try:
					x = int(self.custX.GetValue())
					y = int(self.custY.GetValue())
				except:
					return
			#x,y=size.split("x")
			#x=int(x)
			#y=int(y)
			keepAspect = self.followAspect.GetValue()
		except:
			pass			
		if x != -1 and y != -1:
			self.control.setFrameSize(x, y)
			lib.messenger.send(None, "set_frame_size", (x, y), keepAspect)
			
			
			#self.control.configureTimeline(secs,frameCount)

		#self.parent.sizer.Fit(self.parent)
		
	def getDurationInSeconds(self):
		"""
		return the duration of the movie in seconds
		"""
		
		if not self.updated:
			return self.secs

		duration = str(self.duration.GetValue())
		try:
			hh, mm, ss = map(int, duration.split(":"))
			
		except:
			return 0
		secs = hh * 3600.0 + mm * 60.0 + ss
		self.secs = secs
		self.updated = 0
		return secs
		
	def updateFPS(self, event):
		"""
		update the amount of frames based on the Frames Per Second variable
		"""
		if self.in_framecount:
			return
		self.in_fps = 1
		secs = self.getDurationInSeconds()
		try:
			fps = float(self.frameRate.GetValue())
		except:
			self.in_fps = 0
			return
		newframes = secs * fps
		
		self.totalFrames.SetValue("%d" % newframes)
		
		self.in_fps = 0
		
	def updateDuration(self, event):
		"""
		update the amount of frames based on the duration of the movie
		"""
		self.updated = 1
		secs = self.getDurationInSeconds()
		if secs == 0:
			return
		newframes = self.fps * secs
		self.totalFrames.SetValue("%d" % newframes)
		#self.fpsLabel.SetLabel("%.2f / second"%newfps)
		
	def updateFrameCount(self, event):
		"""
		Update the frame rate based on the duration
		"""
		if self.in_fps:
			return
		self.in_framecount = 1
		try:
			frameCount = int(self.totalFrames.GetValue())
		except:
			self.in_framecount = 0
			return
		if frameCount == 0:
			self.in_framecount = 0
			return
		secs = self.getDurationInSeconds()
		
		self.fps = frameCount / float(secs)
		self.frameRate.SetValue("%.2f" % self.fps)
		#self.fpsLabel.SetLabel("%.2f / second"%newfps)
		self.in_framecount = 0
		
		
