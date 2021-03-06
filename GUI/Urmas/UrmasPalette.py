#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

"""
 Unit: UrmasPalette
 Project: BioImageXD
 Created: 12.04.2005, KP
 Description:

 URM/AS - The Unified Rendering Manager / Animator for Selli
 
 This is a timeline based GUI for controlling the rendering of datasets. The GUI allows users
 to specify a path for the camera to follow (using Heikki Uuksulainen's MayaVi animator code)
 and also allows them to produce videos of the rendering using ffmpeg.
 
 This is a palette containing different items that can be dragged to the timeline.
 
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

import wx
import GUI.Dialogs
import GUI.MenuManager
import os.path
import lib.messenger
import scripting

from wx.lib.statbmp  import GenStaticBitmap as StaticBitmap

class UrmasDropTarget(wx.PyDropTarget):
	"""
	Description: A drop target for dragging from the palette to timeline
	"""
	def __init__(self, tgt, datatype):
		"""
		Initialization
		"""
		wx.PyDropTarget.__init__(self)
		self.target = tgt
		self.dataformat = wx.CustomDataFormat(datatype)
		self.data = wx.CustomDataObject(self.dataformat)
		self.SetDataObject(self.data)

	def OnLeave(self):
		"""
		Track mouse movement for reporting to target
		"""
		
		self.target.OnDragLeave()
		
	def OnDrop(self, x, y):
		"""
		Return true to accept drop
		"""
		
		self.target.OnDragLeave()
		return 1
		
	def OnDragOver(self, x, y, d):
		"""
		
		"""
		
		self.target.OnDragOver(x, y, d)
		return wx.DragCopy
		
	def OnData(self, x, y, d):
		"""
		Get the dropped data
		"""
		
		if self.GetData():
			data = self.data.GetData()
			#print "Got at %d,%d: %s"%(x,y,data)
			self.target.AcceptDrop(x, y, data)

		return d

class UrmasPalette(wx.Panel):
	"""
	Description: A palette from which items can be dragged to the timeline
	"""
	def __init__(self, parent, control):
		"""
		Initialization
		Parameters:
			control     UrmasControl object
		"""
		self.parent = parent
		self.control = control
		self.dropsource = None
		self.icons = {}
		self.panels = {}
		self.sbmps = {}

		wx.Panel.__init__(self, parent, style = wx.RAISED_BORDER, size = (750, 32))
		self.sizer = wx.BoxSizer(wx.HORIZONTAL)
		
		self.iconpath = scripting.get_icon_dir()
		
		self.ID_NEWTIMEPOINTTRACK = wx.NewId()
		toolTip = wx.ToolTip("Click to add a track for controlling animated timepoints.")
		self.addNormalItem(self.ID_NEWTIMEPOINTTRACK,
		"Animator_TrackTimepoint.png", self.onToolNewTimepointTrack, toolTip)        
		
		self.ID_NEWSPLINETRACK = wx.NewId()
		toolTip = wx.ToolTip("Click to add a track for controlling the camera movement using a spline curve.")
		self.addNormalItem(self.ID_NEWSPLINETRACK,
		"Animator_TrackCameraPath.png", self.onToolNewSplineTrack, toolTip)        

		
		self.ID_NEWKEYFRAMETRACK = wx.NewId()
		toolTip = wx.ToolTip("Click to the timeline to add a track for controlling the camera movement by creating keyframes.")
		self.addNormalItem(self.ID_NEWKEYFRAMETRACK,
		"Animator_TrackKeyframe.png", self.onToolNewKeyframeTrack, toolTip)        
		
		p = wx.Panel(self, -1, size = (50, 1))
		self.sizer.Add(p, flag = wx.RIGHT, border = 2)
		
		self.ID_NEWTIMEPOINT = wx.NewId()
		toolTip = wx.ToolTip("Drag this on to a timepoint track to select visualized timepoints.")
		self.addDragDropItem(self.ID_NEWTIMEPOINT,
		"Animator_Timepoint.png", self.onToolNewTimepoint, toolTip)        

		self.ID_NEWSPLINE = wx.NewId()                
		toolTip = wx.ToolTip("Drag this on to a camera path track to add a random camera path.")
		self.addDragDropItem(self.ID_NEWSPLINE,
		"Animator_CameraPath.png", self.onToolNewSpline, toolTip)        
		
		self.ID_NEWCIRCULAR = wx.NewId()
		toolTip = wx.ToolTip("Drag this on to a camera path track to make camera rotate around X axis.")
		self.addDragDropItem(self.ID_NEWCIRCULAR,
		"Animator_CameraPathX.png", self.onToolNewCircular, toolTip)        
		
		self.ID_NEWPERPENDICULAR = wx.NewId()
		toolTip = wx.ToolTip("Drag this on to a camera path track to make camera rotate around Y axis.")
		self.addDragDropItem(self.ID_NEWPERPENDICULAR,
		"Animator_CameraPathY.png", self.onToolNewPerpendicular, toolTip)        
		
		self.ID_STOP_CAMERA = wx.NewId()        
		toolTip = wx.ToolTip("Drag this on to a camera path to add a pause in camera movement.")
		self.addDragDropItem(self.ID_STOP_CAMERA,
		"Animator_Pause.png", self.onToolNewStop, toolTip)        
		
		
		self.ID_ADD_KEYFRAME = wx.NewId()
		toolTip = wx.ToolTip("Drag this on to a keyframe track to add a keyframe at the current camera position.")        
		self.addDragDropItem(self.ID_ADD_KEYFRAME,
		"Animator_Keyframe.png", self.onToolNewKeyframe, toolTip)     
		
		self.zoomLevels = [0.25, 0.3333, 0.5, 0.6667, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 4.0, 6.0]
		self.zoomCombo = wx.ComboBox(self, GUI.MenuManager.ID_ANIM_ZOOM_COMBO,
						  choices = ["25%", "33.33%", "50%", "66.67%", "75%", "100%", "125%", "150%", "200%", "300%", "400%", "600%"], size = (100, -1), style = wx.CB_DROPDOWN)
		self.zoomCombo.SetSelection(5)
		self.zoomCombo.SetHelpText("This controls the zoom level of animator tracks.")        
		self.zoomCombo.Bind(wx.EVT_COMBOBOX, self.zoomToComboSelection)
		
		self.sizer.Add(self.zoomCombo, flag = wx.RIGHT, border = 2)
		
		self.ID_RENDER = wx.NewId()
		toolTip = wx.ToolTip("Click to render the project.")
		self.addNormalItem(self.ID_RENDER,
		"Animator_Render.png", self.parent.onMenuRender, toolTip)         
		
		self.SetSizer(self.sizer)
		self.SetAutoLayout(1)
		self.sizer.Fit(self)
		
	def zoomToComboSelection(self, event):
		"""
		Set the zoom level of the tracks
		"""        
		pos = self.zoomCombo.GetSelection()
		lvl = self.zoomLevels[pos]
		lib.messenger.send(None, "set_animator_zoom", lvl)
		
		
	def addDragDropItem(self, newid, icon, dragCallback, toolTip):        
		"""
		Add an item to the toolbar
		"""
		bmp = wx.Image(os.path.join(self.iconpath, icon), wx.BITMAP_TYPE_ANY).ConvertToBitmap()
		bmp2 = wx.EmptyBitmap(38, 32)
		dc = wx.MemoryDC()
		dc.SelectObject(bmp2)
		
		#dc.SetPen(wx.Pen(self.GetBackgroundColour(),1))
		#dc.SetBrush(wx.Brush(self.GetBackgroundColour()))
		dc.SetPen(wx.Pen(wx.Colour(0, 0, 0), 1))
		dc.SetBrush(wx.Brush(wx.Colour(0, 0, 0)))
		dc.DrawRectangle(0, 0, 38, 32)
		
		x = 1
		y = 0
		dc.DrawBitmap(bmp, 7, 0)
		for i in range(0, 10):
			dc.SetPen(wx.Pen(wx.Colour(135, 135, 135), 1))
			dc.DrawLine(x, y, x + 6, y)           
			y += 1
			dc.SetPen(wx.Pen(wx.Colour(100, 100, 100), 1))
			dc.DrawLine(x, y, x + 6, y)
			y += 1
			y += 2
		
		dc.SelectObject(wx.NullBitmap)
		self.icons[newid] = bmp2
		sbmp = StaticBitmap(self, newid, bmp, style = wx.RAISED_BORDER, size = (40, 40))
		self.sbmps[newid] = sbmp
		sbmp.Bind(wx.EVT_MOTION, dragCallback)        
		#p.Bind(wx.EVT_MOTION,dragCallback)        
		#self.sizer.Add(p,flag=wx.RIGHT,border=2)
		#p.Bind(               wx.EVT_LEFT_UP,self.onToolClick)
		self.sizer.Add(sbmp, flag = wx.RIGHT, border = 2)
		
		sbmp.Bind(wx.EVT_LEFT_UP, self.onToolClick)
		
		sbmp.SetHelpText(toolTip.GetTip())
		sbmp.SetToolTip(toolTip)        
		#p.SetToolTip(toolTip)      
	  
	def addNormalItem(self, newid, icon, callback, toolTip):        
		"""
		Add an item to the toolbar
		"""
		bmp = wx.Image(os.path.join(self.iconpath, icon), wx.BITMAP_TYPE_ANY).ConvertToBitmap()
		self.icons[newid] = bmp
		#sbmp=StaticBitmap(self,newid,bmp,style=wx.RAISED_BORDER)
		#self.sbmps[newid]=sbmp
		btn = wx.BitmapButton(self, newid, bmp)
		#sbmp.Bind(wx.EVT_MOTION,dragCallback)        
		btn.Bind(wx.EVT_BUTTON, callback)
		#p.Bind(wx.EVT_MOTION,callback)        
		#self.sizer.Add(p,flag=wx.RIGHT,border=2)
		#p.Bind(               wx.EVT_LEFT_UP,self.onToolClick)
		self.sizer.Add(btn, flag = wx.RIGHT, border = 2)
		
		btn.SetHelpText(toolTip.GetTip())
		btn.SetToolTip(toolTip)   
		
	def onToolClick(self, event):
		"""
		A method that displays instructions if the user clicks on the palette
		"""
		GUI.Dialogs.showwarning(None, "You need to drag and drop this item on to a track.", "Drag item instead of clicking")
		
	def onToolNewPerpendicular(self, event):
		"""
		A method for dragging a spline from palette
		"""
		if event.Dragging():
			self.dropItem("Spline", "Perpendicular")
		event.Skip()

	def onToolNewKeyframe(self, event):
		"""
		A method for dragging a spline from palette
		"""
		if event.Dragging():
			self.dropItem("Keyframe", "Keyframe")
		event.Skip()
		
	def onToolNewKeyframeTrack(self, event):
		"""
		A method for dragging a keyframe track from palette
		"""
		self.control.timeline.addKeyframeTrack("")
		
	def onToolNewSplineTrack(self, event):
		"""
		A method for dragging a spline track from palette
		"""
		self.control.timeline.addSplinepointTrack("")
		
	def onToolNewTimepointTrack(self, event):
		"""
		A method for dragging a timepoint track from palette
		"""
		self.control.timeline.addTrack("")
		

		
	def onToolNewStop(self, event):
		"""
		A method for dragging a spline from palette
		"""
		if event.Dragging():
			self.dropItem("Spline", "Stop")
		event.Skip()

	def onToolNewCircular(self, event):
		"""
		A method for dragging a spline from palette
		"""
		if event.Dragging():
			self.dropItem("Spline", "Circular")
		event.Skip()
		
	def onToolNewSpline(self, event):
		"""
		A method for dragging a spline from palette
		"""
		
		if event.Dragging():
			self.dropItem("Spline")
		event.Skip()
		
	def onToolNewTimepoint(self, event):
		"""
		A method for dragging a spline from palette
		"""
		if event.Dragging():
			self.dropItem("Timepoint")
		event.Skip()        
			
		
	def dropItem(self, datatype, indata = "Hello, World!"):
		"""
		A method that creates a DnD of specified type
		"""
		
		data = wx.CustomDataObject(wx.CustomDataFormat(datatype))
		data.SetData(indata)
		
		self.dropsource = wx.DropSource(self)
		self.dropsource.SetData(data)
		
		res = self.dropsource.DoDragDrop(wx.Drag_AllowMove)
		
		return res

