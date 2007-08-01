# -*- coding: iso-8859-1 -*-

"""
 Unit: Track
 Project: BioImageXD
 Created: 05.02.2005, KP
 Description:

 URM/AS - The Unified Rendering Manager / Animator for Selli
 
 Urmas is a timeline based GUI for controlling the rendering of datasets. The GUI allows users
 to specify a path for the camera to follow (using Heikki Uuksulainen's MayaVi animator code)
 and also allows them to produce videos of the rendering using ffmpeg.
 
 The widgets that implement the Tracks of the timeline are implemented in this module.

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

#import Dialogs
#import ImageOperations
#import Logging
#import math
#import messenger
#import os.path
#import random
#import sys

from GUI.Urmas.TrackItem.TrackItem import TrackItem
from GUI.Urmas.UrmasPalette import UrmasDropTarget
from GUI.TimepointSelection import TimepointSelection
from Track import Track
import wx
 
class TimepointTrack(Track):
	"""
	Class: TimepointTrack
	Created: 13.04.2005, KP
	Description: A class representing a timepoint track in the timeline
	"""       
	def __init__(self, name, parent, **kws):
		self.nameColor = (128, 195, 155)
		self.fg = (0, 0, 0)
		self.bg = self.nameColor
		# A flag that indicates that keyframe track is similiar to
		# camera path track in that it defines the camera movement
		self.trackType = "DEFINE_TIMEPOINT"        
		Track.__init__(self, name, parent, **kws)
		
		self.itemClass = kws.get("item", TrackItem)

		self.paintOverlay = 1
		self.overlayColor = ((255, 255, 255), 25)                
	
		dt = UrmasDropTarget(self, "Timepoint")
		self.SetDropTarget(dt)
		self.thumbnail = 1

		# added this because was commented out in Track
		self.sizer = wx.GridBagSizer()
	
	def AcceptDrop(self, x, y, data):
		"""
		Method: AcceptDrop
		Created: 12.04.2005, KP
		Description: Method called to indicate that a user is no longer dragging
					 something to this track
		"""
		oldlen = len(self.items)
		timepoints = TimepointSelection(self.parent)
		timepoints.setDataUnit(self.control.getDataUnit())
		if timepoints.ShowModal() == wx.ID_OK:
			tps = timepoints.getSelectedTimepoints()
			self.insertTimepoints(tps)
		if not oldlen:
			self.expandToMax()
			
	def showThumbnail(self, flag):
		"""
		Method: showThumbnail
		Created: 04.02.2005, KP
		Description: A method to set a flag indicating, whether to show a
					 thumbnail on the items in this track
		"""           
		self.thumbnail = flag
		for item in self.items:
			#print "Setting thumbnail on",item
			item.setThumbnailDataunit(self.dataUnit)
	
	def insertTimepoints(self, timepoints):
		"""
		Method: insertTimepoints(tps)
		Created: 13.04.2005, KP
		Description: Insert the given timepoints to the track
		"""              
		pos = self.dragEndPosition
		for tp in timepoints:
			self.addTimepoint(pos, tp, 0)
			pos += 1
			self.paintTrack()
#        self.Refresh()
#        self.Layout()
		#self.sizer.Fit(self)
			

	def addTimepoint(self, position, timepoint, update = 1):
		"""
		Method: addTimepoint
		Created: 04.02.2005, KP
		Description: A method to add a new item to this track
		"""              
		h = self.height
		kws = {"editable":self.editable}
		kws["dataunit"] = self.dataUnit
		kws["thumbnail"] = timepoint
		kws["timepoint"] = timepoint
		text = "%d" % timepoint
		item = self.itemClass(self, text, (20, h), **kws)
		if self.color:
			item.setColor(self.color, self.headercolor)
		self.items.insert(position, item)
		# +1 accounts for the empty item
		
		for i, trackitem in enumerate(self.items):
			trackitem.setItemNumber(i)
			
		if update:
			self.Layout()
			self.sizer.Fit(self)
		item.updateItem()
		self.updatePositions()
		return item
		
			
	def setItemAmount(self, n):
		"""
		Method: setItemAmount
		Created: 20.04.2005, KP
		Description: A method to set the amount of items in this track
		"""               
		self.remove()
		self.initTrack()
		for i in range(n):
			self.addTimepoint(i, i, 0)
			
	def __set_pure_state__(self, state):
		"""
		Method: __set_pure_state__()
		Created: 11.04.2005, KP
		Description: Method called by UrmasPersist to allow the object
					 to refresh before it's items are created
		""" 
		Track.__set_pure_state__(self, state)
		for i, item in enumerate(state.items):
			tp = self.addTimepoint(i, item.timepoint, 0)
			tp.__set_pure_state__(item)
		#self.updatePositions()
		self.paintTrack()
