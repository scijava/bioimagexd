#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

"""
 Unit: CameraView
 Project: BioImageXD
 Created: 12.12.2005, KP
 Description:

 URM/AS - The Unified Rendering Manager / Animator for Selli
 
 This is a panel for viewing a camera's settings for debug purposes.
  
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

import lib.messenger
import types
import wx

FIELDS = ["ClippingRange", "DirectionOfProjection", "Distance", "EyeAngle",
"FocalDisk", "FocalPoint", "Orientation", "ParallelProjection",
"ParallelScale", "Position", "Roll", "ViewAngle", "ViewPlaneNormal", "ViewShear",
"ViewUp", "WindowCenter"]

class CameraView(wx.StaticText):
	"""
	Created: 12.12.2005, KP
	Description: A class for viewing a vtkCamera
	"""    
	def __init__(self, parent, id):
		wx.StaticText.__init__(self, parent, id)
		self.str = ""
		lst = []
		for i in FIELDS:
			self.str += ("%s: %%s\n" % i)
			lst.append("n/a")
		self.SetLabel(self.str % tuple(lst))
		
		lib.messenger.connect(None, "view_camera", self.viewCamera)
	
	def getAsStr(self, val):
		if type(val) in [types.ListType, types.TupleType]:
			return map(self.getAsStr, val)
		if type(val) == types.StringType:
			return val
		elif type(val) == types.FloatType:
			return "%.4f" % val
		return str(val)
	
	def viewCamera(self, obj, evt, args):
		"""
		Method: viewCamera
		Created: 12.12.2005, KP
		Description: A method to update the displayed vtkCamera
		"""  
		cam = args
		lst = []
		for i in FIELDS:
			val = eval("cam.Get%s()" % i)
			val = self.getAsStr(val)
			lst.append(val)
				
		self.SetLabel(self.str % tuple(lst))
		
		
