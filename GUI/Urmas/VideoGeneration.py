#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

"""
 Unit: VideoGeneration
 Project: BioImageXD
 Created: 10.02.2005, KP
 Description:

 URM/AS - The Unified Rendering Manager / Animator for Selli
 
 This module contains a panel that can be used to control the creation of a movie
 out of a set of rendered images.
 
 Copyright (C) 2005  BioImageXD Project
 See CREDITS.txt for details

 This program is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
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

#import Visualizer

import Configuration
import GUI.Dialogs
import lib.messenger
import lib.RenderingInterface
import Logging
import math
import platform
import os
import scripting
import sys
import wx

class VideoGeneration(wx.Panel):
	"""
	Created: 05.05.2005, KP
	Description: A page for controlling video generation
	"""
	def __init__(self, parent, control, visualizer):
		"""
		Created: 05.05.2005, KP
		Description: Initialization
		"""
		wx.Panel.__init__(self, parent, -1)
		self.control = control
		self.visualizer = visualizer
		self.frameList = None
			
		# The slider panel will be unlocked by UrmasWindow, not 
		# VideoGeneration
		self.visualizer.getCurrentMode().lockSliderPanel(1)
		
		
		self.oldSelection = 0
		self.rendering = 0
		self.oldformat = None
		self.abort = 0
		self.parent = parent
		self.size = self.control.getFrameSize()
		self.frames = self.control.getFrames()
		self.fps = self.control.getFrames() / float(self.control.getDuration())
		self.dur = self.control.getDuration()

		self.outputExts = [["png", "bmp", "jpg", "tif", "pnm"], ["mpg", "mpg", "avi", "wmv", "avi", "avi", "mov"]]
		self.outputFormats = [["PNG", "BMP", "JPEG", "TIFF", "PNM"],
							 ["MPEG1", "MPEG2", "WMV1",
							  "WMV2", "MS MPEG4", "MS MPEG4 v2",
							  "QuickTime MPEG4", "AVI MPEG4"]]
		self.outputCodecs = [("mpeg1video", "mpg"), ("mpeg2video", "mpg"), \
							("wmv1", "wmv"), ("wmv2", "wmv"), ("msmpeg4", "avi"), \
							("msmpeg4v2", "avi"), ("mpeg4", "mov"), ("mpeg4", "avi")]
		self.padding = [1, 1, 0, 0, 0, 0]
		self.presets = [(0, 0, 0), ((720, 576), (25), 6000), ((720, 480), (29.97), 6000)]
		self.targets = ["", "pal-dvd", "ntsc-dvd"]
		self.needpad = 0
		self.mainsizer = wx.GridBagSizer()
		self.generateGUI()

			
		# Produce quicktime MPEG4 by default but MS MPEG4 v2 on windows
		sel = 6
		if platform.system() == "Windows":
			sel = 5
		self.outputFormat.SetSelection(sel)
		
		self.buttonBox = wx.BoxSizer(wx.HORIZONTAL)
		self.okButton = wx.Button(self, -1, "Ok")
		self.cancelButton = wx.Button(self, -1, "Cancel")
		
		self.okButton.Bind(wx.EVT_BUTTON, self.onOk)
		self.cancelButton.Bind(wx.EVT_BUTTON, self.onCancel)
		
		
		self.buttonBox.Add(self.okButton)
		self.buttonBox.Add(self.cancelButton)
		

		self.mainsizer.Add(self.buttonBox, (5, 0), flag = wx.EXPAND | wx.RIGHT | wx.LEFT)

		self.SetSizer(self.mainsizer)
		self.SetAutoLayout(True)
		self.mainsizer.Fit(self)

	def onCancel(self, *args):
		"""
		Created: 15.12.2005, KP
		Description: Close the video generation window
		"""        
		if self.rendering:
			lib.messenger.send(None, "stop_rendering")
			self.abort = 1
#        self.visualizer.getCurrentMode().lockSliderPanel(0)            
		lib.messenger.send(None, "video_generation_close")
		
		
	def onOk(self, event):
		"""
		Created: 26.04.2005, KP
		Description: Render the whole damn thing
		"""
		self.okButton.Enable(0)
		lib.messenger.send(None, "set_play_mode")
		lib.messenger.connect(None, "playback_stop", self.onCancel)
		
		self.abort = 0
		if self.visualizer.getCurrentModeName() != "3d":
			self.visualizer.setVisualizationMode("3d")
		path = self.rendir.GetValue()
		file = self.videofile.GetValue()
		dn = os.path.dirname(path)
		while not os.path.exists(dn):
			os.mkdir(dn)
			dn = os.path.dirname(dn)
		codec = self.outputFormat.GetSelection()    
		vcodec, ext = self.outputCodecs[codec]
		file_coms = file.split(".")
		file_coms[-1] = ext
		file = ".".join(file_coms)
		
		conf = Configuration.getConfiguration()
		conf.setConfigItem("FramePath", "Paths", path)
		conf.setConfigItem("VideoPath", "Paths", file)
		conf.writeSettings()
		
		renderingInterface = lib.RenderingInterface.getRenderingInterface(1)
		renderingInterface.setVisualizer(self.visualizer)
		# if we produce images, then set the correct file type
		if self.formatMenu.GetSelection() == 0:
			formatNum = self.outputFormat.GetSelection()
			imageExt = self.outputExts[0][formatNum]
			Logging.info("Setting output image format to ", imageExt, kw = "animator")
			renderingInterface.setType(imageExt)
		
		Logging.info("Setting duration to ", self.dur, "and frames to", self.frames, kw = "animator")
		self.control.configureTimeline(self.dur, self.frames)

		Logging.info("Will produce %s, rendered frames go to %s" % (file, path), kw = "animator")
		size = self.size
		x, y = size
		self.file = file
		self.size = size
		self.path = path
		
		
		sel = self.preset.GetSelection()
		if sel != 0:
			(x, y), fps, br = self.presets[sel]
		
		Logging.info("Will set render window to ", size, kw = "animator")
		self.visualizer.setRenderWindowSize((x, y), self.parent)
		self.rendering = 1
		lib.messenger.connect(None, "rendering_done", self.cleanUp)
		flag = self.control.renderProject(0, renderpath = path)
		
		self.rendering = 0
		if flag == -1:
			return
			
	def cleanUp(self, *args):
		"""
		Created: 30.1.2006, KP
		Description: Method to clean up after rendering is done
		""" 
		renderingInterface = lib.RenderingInterface.getRenderingInterface()        
		self.frameList = renderingInterface.getFrameList()
		# if the rendering wasn't aborted, then restore the animator
		if not self.abort:
			self.visualizer.restoreWindowSizes()
			self.parent.SetDefaultSize(self.parent.origSize)
			self.parent.parent.OnSize(None)
					
		if self.formatMenu.GetSelection() == 1:

			Logging.info("Will produce video", kw = "animator")
			self.encodeVideo(self.path, self.file, self.size)
			
		# clear the flags so that urmaswindow will destroy as cleanly
		
		self.abort = 0
		self.rendering = 0
		
		
		lib.messenger.send(None, "video_generation_close")
#        self.Close()
		lib.messenger.disconnect(None, "rendering_done")

	def encodeVideo(self, path, file, size):
		"""
		Created: 27.04.2005, KP
		Description: Encode video from the frames produced
		""" 
		renderingInterface = lib.RenderingInterface.getRenderingInterface()
		
		pattern = renderingInterface.getFilenamePattern()
		framename = renderingInterface.getFrameName()
		
		# FFMPEG uses %3d instead of %.3d for files numbered 000 - 999
		pattern = pattern.replace("%.", "%")
		pattern = pattern.split(os.path.sep)[-1]
		pattern = pattern.replace("%s", framename)
		pattern = os.path.join(path, pattern)
		Logging.info("Pattern for files = ", pattern, kw = "animator")
		
		#frameRate = int(self.frameRate.GetValue())
		#frameRate=float(self.frameRate.GetValue())
		frameRate = self.fps
		codec = self.outputFormat.GetSelection()    
		vcodec, ext = self.outputCodecs[codec]        
#        if self.needpad and frameRate not in [12.5,25]:
#            scodec=self.outputFormats[1][codec]
#            #if frameRate<12.5:frameRate=12
#            #else:frameRate=24
#            frameRate=25
#            GUI.Dialogs.showmessage(self, \
#										"For the code you've selected (%s), \
#										the target frame rate must be either 12.5 or 25. %d will be used." \
#										% (scodec,frameRate), \
#										"Bad framerate")

		x, y = size
		ffmpegs = {"linux": "bin/ffmpeg", "win32": "bin\\ffmpeg.exe", "darwin": "bin/ffmpeg.osx"}
		ffmpeg = "ffmpeg"
		quality = self.qualitySlider.GetValue()
		quality = 11 - quality
		quality = math.ceil(1 + (3.333333 * (quality - 1)))
		
		
		target = ""
		sel = self.preset.GetSelection()
		if sel != 0:
			target = self.targets[sel]
			(x, y), fps, br = self.presets[sel]
		for i in ffmpegs.keys():
			if i == sys.platform:
				ffmpeg = ffmpegs[i]
				break
				
		bindir = scripting.get_main_dir()
		ffmpeg = os.path.join(bindir, ffmpeg)
		if not target:
			commandLine = "%s -qscale %d -b 8192 -r %.2f -s %dx%d -i \"%s\" -vcodec %s \"%s\"" \
							% (ffmpeg, quality, frameRate, x, y, pattern, vcodec, file)
		else:
			
			commandLine = "%s -qscale %d -s %dx%d -i \"%s\" -target %s \"%s\"" % (ffmpeg, quality, x, y, pattern, target, file)
		Logging.info("Command line for ffmpeg=", commandLine, kw = "animator")
		os.system(commandLine)
		if os.path.exists(file):
			GUI.Dialogs.showmessage(self, "Encoding was successful!", "Encoding done")
			if self.delFramesBox.GetValue():
				for file in self.frameList:
					print "Removing", file
					os.unlink(file)
		else:
			GUI.Dialogs.showmessage(self, "Encoding failed: File %s does not exist!" % file, "Encoding failed")
		
		
	def onUpdateFormat(self, event):
		"""
		Created: 26.04.2005, KP
		Description: Update the gui based on the selected output format
		""" 
		sel = self.formatMenu.GetSelection()
		
		if sel:
			self.outputFormatLbl.SetLabel("Video Codec:")
			
		else:
			self.outputFormatLbl.SetLabel("Image Format:")
		self.delFramesBox.Enable(sel)
		self.qualitySlider.Enable(sel)
		self.videofile.Enable(sel)            
		
		self.videofileBtn.Enable(sel)
		
		currentSelection = self.outputFormat.GetSelection()        
		self.outputFormat.Clear()
		for i in self.outputFormats[sel]:
			self.outputFormat.Append(i)
		self.outputFormat.SetSelection(self.oldSelection)        
		self.oldSelection = currentSelection
		
	
	def onUpdateCodec(self, event):
		"""
		Created: 26.04.2005, KP
		Description: Update the gui based on the selected output codec
		""" 
		sel = self.formatMenu.GetSelection()
		if sel == 1:
			codec = self.outputFormat.GetSelection()
			
	def onUpdatePreset(self, event):
		"""
		Created: 07.02.2006, KP
		Description: Update the GUI based on the selected preset
		""" 
		sel = self.preset.GetSelection()
		flag = (sel == 0)
		self.formatMenu.Enable(flag)
		self.outputFormat.Enable(flag)
		
		if not flag:
			(x, y), fps, br = self.presets[sel]
			oldformat1 = self.formatMenu.GetStringSelection()
			oldformat2 = self.outputFormat.GetStringSelection()
			self.oldformat = (oldformat1, oldformat2)
			self.formatMenu.SetStringSelection("Video")
			self.outputFormat.SetStringSelection("MPEG2")
			self.frameRate.SetLabel("%.2f" % fps)
			self.frameSize.SetLabel("%d x %d" % (x, y))
		else:
			if self.oldformat:
				oldformat1, oldformat2 = self.oldformat
				self.formatMenu.SetStringSelection(oldformat1)
				self.outputFormat.SetStringSelection(oldformat2)
				self.frameRate.SetLabel("%.2f" % self.fps)
				self.frameSize.SetLabel("%d x %d" % self.size)
			
			
	def generateGUI(self):
		"""
		Created: 26.04.2005, KP
		Description: Generate the GUI
		""" 
		self.outputsizer = wx.GridBagSizer(0, 5)
		box = wx.StaticBox(self, wx.HORIZONTAL, "Rendering")
		self.outputstaticbox = wx.StaticBoxSizer(box, wx.HORIZONTAL)
		self.outputstaticbox.Add(self.outputsizer)

		self.formatLabel = wx.StaticText(self, -1, "Output Format")
		self.formatMenu = wx.Choice(self, -1, choices = ["Images", "Video"])
		self.formatMenu.SetSelection(1)
		self.formatMenu.Bind(wx.EVT_CHOICE, self.onUpdateFormat)
		
		
		self.totalFramesLabel = wx.StaticText(self, -1, "Frames:")
		self.durationLabel = wx.StaticText(self, -1, "Duration:")

		self.totalFrames = wx.StaticText(self, -1, "%d" % self.frames, size = (50, -1))
		
		t = self.dur
		h = t / 3600
		m = t / 60
		s = t % 60
		t = "%.2d:%.2d:%.2d" % (h, m, s)
		self.duration = wx.StaticText(self, -1, t, size = (100, -1))

		self.outputFormatLbl = wx.StaticText(self, -1, "Video codec:")
		self.outputFormat = wx.Choice(self, -1, choices = self.outputFormats[1])
		self.outputFormat.Bind(wx.EVT_CHOICE, self.onUpdateCodec)
		self.outputFormat.SetSelection(2)
		
		self.frameSizeLbl = wx.StaticText(self, -1, "Frame size:")
		#self.frameSize = wx.Choice(self,-1,choices=["320 x 240","512 x 512","640 x 480","800 x 600"])
		#self.frameSize.SetSelection(1)
		self.frameSize = wx.StaticText(self, -1, "%d x %d" % self.size)

		self.frameRateLbl = wx.StaticText(self, -1, "Frame rate:")
		self.frameRate = wx.StaticText(self, -1, "%.2f" % self.fps)
		
		self.qualityLbl = wx.StaticText(self, -1, "Encoding quality (1 = worst, 10 = best)")
		self.qualitySlider = wx.Slider(self, -1, value = 10, minValue = 1, maxValue = 10, \
										style = wx.SL_HORIZONTAL | wx.SL_LABELS | wx.SL_AUTOTICKS, size = (250, -1))
		
		self.presetLbl = wx.StaticText(self, -1, "Preset encoding targets:")
		self.preset = wx.Choice(self, -1, choices = ["Use settings below", "PAL-DVD", "NTSC-DVD"])
		self.preset.Bind(wx.EVT_CHOICE, self.onUpdatePreset)
		self.preset.SetSelection(0)
		n = 0
		self.outputsizer.Add(self.presetLbl, (n, 0))
		n += 1
		self.outputsizer.Add(self.preset, (n, 0))
		
		n += 1
		self.outputsizer.Add(self.formatLabel, (n, 0))
		self.outputsizer.Add(self.formatMenu, (n, 1))
		n += 1
		self.outputsizer.Add(self.outputFormatLbl, (n, 0))
		self.outputsizer.Add(self.outputFormat, (n, 1))
		n += 1
		self.outputsizer.Add(self.frameSizeLbl, (n, 0))
		self.outputsizer.Add(self.frameSize, (n, 1))
		n += 1
		self.outputsizer.Add(self.frameRateLbl, (n, 0))
		self.outputsizer.Add(self.frameRate, (n, 1))
		n += 1
		self.outputsizer.Add(self.durationLabel, (n, 0))
		self.outputsizer.Add(self.duration, (n, 1))        
		n += 1
		self.outputsizer.Add(self.totalFramesLabel, (n, 0))
		self.outputsizer.Add(self.totalFrames, (n, 1))
		n += 1
		self.outputsizer.Add(self.qualityLbl, (n, 0), span = (1, 2))
		n += 1
		self.outputsizer.Add(self.qualitySlider, (n, 0), span = (1, 2))
		
		self.mainsizer.Add(self.outputstaticbox, (0, 0))
	
		conf = Configuration.getConfiguration()
		path = conf.getConfigItem("FramePath", "Paths")
		video = conf.getConfigItem("VideoPath", "Paths")
		if not path:
			path = os.path.expanduser("~")
		if not video:
			video = os.path.join(path, "video.avi")
		self.rendir = wx.TextCtrl(self, -1, path, size = (150, -1))#,size=(350,-1))
		self.rendirLbl = wx.StaticText(self,
		-1, "Save frames in directory:")
		
		self.delFramesBox = wx.CheckBox(self, -1, "Delete frames after encoding is ready")
		self.delFramesBox.SetValue(1)
		
		self.dirBtn = wx.Button(self, -1, "...")
		self.dirBtn.Bind(wx.EVT_BUTTON, self.onSelectDirectory)
		
		self.renderingsizer = wx.GridBagSizer(5, 5)

		
		self.renderingsizer.Add(self.rendirLbl, (0, 0), flag = wx.EXPAND | wx.LEFT | wx.RIGHT)
		self.renderingsizer.Add(self.rendir, (1, 0), flag = wx.EXPAND | wx.LEFT | wx.RIGHT)
		self.renderingsizer.Add(self.dirBtn, (1, 1))
		self.renderingsizer.Add(self.delFramesBox, (2, 0))
		
		self.videofile = wx.TextCtrl(self, -1, video, size = (150, -1))
		self.videofileLbl = wx.StaticText(self, -1, "Output file name:")
		self.videofileBtn = wx.Button(self, -1, "...")
		self.videofileBtn.Bind(wx.EVT_BUTTON, self.onSelectOutputFile)
		
		self.renderingsizer.Add(self.videofileLbl, (3, 0), flag = wx.EXPAND | wx.ALL)
		self.renderingsizer.Add(self.videofile, (4, 0), flag = wx.EXPAND | wx.ALL)
		self.renderingsizer.Add(self.videofileBtn, (4, 1), flag = wx.EXPAND | wx.ALL)
			self.mainsizer.Add(self.renderingsizer, (1, 0), flag = wx.EXPAND | wx.ALL)

	def onSelectDirectory(self, event = None):
		"""
		Created: 10.11.2004, KP
		Description: A callback that is used to select the directory where
					 the rendered frames are stored
		"""
		dirname = GUI.Dialogs.askDirectory(self, "Directory for rendered frames", ".")
		self.rendir.SetValue(dirname)
		
	def onSelectOutputFile(self, event = None):
		"""
		Created: 26.04.2005, KP
		Description: A callback that is used to select the video file 
					 that is produced.
		"""
		sel = self.formatMenu.GetSelection()
		codec = self.outputFormat.GetSelection()
		codecname = self.outputFormats[sel][codec]
		ext = self.outputExts[sel][codec]
		wc = "%s File (*.%s)|*.%s" % (codecname, ext, ext)
		filename = GUI.Dialogs.askSaveAsFileName(self, "Select output filename", "movie.%s" % ext, wc)
		if filename:
			self.videofile.SetValue(filename)

		

