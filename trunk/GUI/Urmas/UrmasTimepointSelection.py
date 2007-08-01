#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

"""
 Unit: UrmasTimepointSelection
 Project: BioImageXD
 Created: 12.03.2005
 Creator: KP
 Description:

 URM/AS - The Unified Rendering Manager / Animator for Selli
 
 This is a timeline based GUI for controlling the rendering of datasets. The GUI allows users
 to specify a path for the camera to follow (using Heikki Uuksulainen's MayaVi animator code)
 and also allows them to produce videos of the rendering using ffmpeg.
 
 This is the wxPanel based class implementing a timepoint selection.
 
 Modified: 12.03.2005 KP - Created the module
 
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
import wx.wizard
import GUI.TimepointSelection

class UrmasTimepointSelection(wx.wizard.PyWizardPage):
	"""
	Class: UrmasTimepointSelection
	Created: 12.03.2005, KP
	Description: Implements selection of timepoints for Urmas
	"""     
	def __init__(self, parent):
		wx.wizard.PyWizardPage.__init__(self, parent)
		self.sizer = wx.GridBagSizer()
		
		self.timepointSelection = GUI.TimepointSelection.TimepointSelectionPanel(self)
		
		self.sizer.Add(self.timepointSelection, (0, 0))
		
		self.SetSizer(self.sizer)
		self.SetAutoLayout(1)
		self.sizer.Fit(self)
		
	def GetNext(self):
		"""
		Method: GetNext()
		Created: 14.03.2005, KP
		Description: Returns the page that comes after this one
		"""          
		return self.next
		
	def GetPrev(self):
		"""
		Method: GetPrev()
		Created: 14.03.2005, KP
		Description: Returns the page that comes before this one
		"""              
		return self.prev
		
	def setDataUnit(self, du):
		"""
		Method: setDataUnit
		Created: 12.03.2005, KP
		Description: Sets the dataunit
		"""          
		self.timepointSelection.setDataUnit(du)
