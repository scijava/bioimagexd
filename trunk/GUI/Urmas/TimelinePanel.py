#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

"""
 Unit: TimelinePanel
 Project: BioImageXD
 Created: 04.02.2005, KP
 Description:

 URM/AS - The Unified Rendering Manager / Animator for Selli
 
 This is a timeline based GUI for controlling the rendering of datasets. The GUI allows users
 to specify a path for the camera to follow (using Heikki Uuksulainen's MayaVi animator code)
 and also allows them to produce videos of the rendering using ffmpeg.

 The timeline widget and it's configuration is implemented in this module.
 
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


import SplineEditor
import lib.messenger
import RenderingConfigPanel
from Timeline import Timeline
import Visualizer.VisualizerWindow
import wx

class SplitPanel(wx.SplitterWindow):
	"""
	Created: 25.01.2006, KP
	Description: A splitterwindow containing the timeline and it's configuration
	"""    
	def __init__(self, parent, ID):
		wx.SplitterWindow.__init__(self, parent, ID,
								   )        
class TimelinePanel(wx.Panel):
	"""
	Created: 04.02.2005, KP
	Description: Contains the timescale and the different "tracks"
	"""    
	def __init__(self, parent, control, size = (750, 300), p = None):

		wx.Panel.__init__(self, parent, -1, style = wx.RAISED_BORDER, size = size)
		self.parent = parent
		self.control = control
		self.sizer = wx.GridBagSizer()        
		w = size[0]
		self.wxrenwin = None
		# added this because "timeline" is used on lines 202-209
		self.timeline = Timeline

		self.confSizer = wx.GridBagSizer()

		self.timelineConfig = RenderingConfigPanel.RenderingConfigPanel(self, control)

		# The timelineConfig is not actually a panel, just an object that contains
		# the sizer we want to add to the layout. This is done to thin the hierarchy of
		# panels because MacOS X doesn't like many nested panels. That's why we just
		# add the sizer
		self.confSizer.Add(self.timelineConfig.sizer, (0, 0), flag = wx.EXPAND | wx.ALL)

		#sbox=wx.StaticBox(self,-1,"Animator configuration")
		#sboxsizer=wx.StaticBoxSizer(sbox,wx.HORIZONTAL)
		#sboxsizer.Add(self.confSizer)

		sboxsizer = self.confSizer

		self.useButton = wx.Button(self, -1, "Use settings")

		self.useButton.Bind(wx.EVT_BUTTON, self.useSettings)

		self.confSizer.Add(self.useButton, (1, 0))
		self.wxrenwin = Visualizer.VisualizerWindow.VisualizerWindow(self, size = (300, 300))
		self.splineEditor = SplineEditor.SplineEditor(self, self.wxrenwin)
		self.control.setSplineEditor(self.splineEditor)   
		
		self.sizer.Add(sboxsizer, (0, 0), flag = wx.EXPAND | wx.ALL)
		self.sizer.Add(self.wxrenwin, (0,1))
		self.SetSizer(self.sizer)
		self.SetAutoLayout(1)
		self.sizer.Fit(self)

		
		self.Refresh()
		
		self.wxrenwin.initializeVTK()
		self.splineEditor.initializeVTK()
		self.wxrenwin.Render()
		
		n = self.timelineConfig.getFrameAmount()
		
		lib.messenger.send(None, "set_frames", n)
		lib.messenger.connect(None, "set_frame_size", self.onSetFrameSize)
		lib.messenger.connect(None, "set_keyframe_mode", self.onSetKeyframeMode)
		
		#wx.CallAfter(self.initializeVTK)


	def initializeVTK(self):
		"""
		Created: 12.09.2007, KP
		Description: initialize the vtk window
		"""

		
     

		#self.sboxsizer.Add(self.wxrenwin)
		#self.sizer.Add(self.sboxsizer,(0,1))
		#self.Layout()
		
		#self.wxrenwin.Raise()

	def onSetFrameSize(self, obj, evt, size, onlyAspect):
		"""
		Created: 19.12.2005, KP
		Description: Event to change the size of the rendering preview
					 based on the size of the actual rendered frames
		"""
		if not self.wxrenwin:
			return
		x, y = size
		xtoy = float(x) / y
		if onlyAspect:
			y = 300
			x = xtoy * y
		
		self.wxrenwin.SetSize((x, y))
		self.wxrenwin.SetMinSize((x, y))
		print "Setting size of renderwindow to ", (x, y)
		
		self.wxrenwin.Update()
		self.wxrenwin.Render()
		

	def onSetKeyframeMode(self, obj, evt, arg):
		"""
		Created: 18.08.2005, KP
		Description: Toggles the keyframe mode on / off
		"""            
		pass
		
	def useSettings(self, evt):
		"""
		Created: 16.08.2005, KP
		Description: Use the configured settings
		"""    
		self.timelineConfig.useSettings(evt)
		n = self.timelineConfig.getFrameAmount()
		lib.messenger.send(None, "set_frames", n)
		cam = self.splineEditor.getCamera()


	def useTimeline(self, flag):
		print "useTimeline called!"
		if not flag:
			self.timeline.setDisabled(1)
		else:
			self.timeline.setDisabled(0)
		
	def setDataUnit(self, dataUnit):
		print "setDataUnit called!"
		self.dataUnit = dataUnit
		self.timeline.setDataUnit(dataUnit)
		
		
