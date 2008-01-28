# -*- coding: iso-8859-1 -*-

"""
 Unit: MIPPreviewFrame.py
 Project: BioImageXD
 Created: 03.11.2004, KP
 Description:

 A prevew frame for showing MIP

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
__version__ = "$Revision: 1.63 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import scripting
from GUI.InteractivePanel import InteractivePanel as InteractivePanel
import lib.ImageOperations
import lib.messenger
import Logging
import Modules
import optimize
import sys
import time
import vtk
import vtkbxd
import wx

ZOOM_TO_FIT = -1

import PreviewFrame

class MIPPreviewFrame(PreviewFrame.PreviewFrame):
	"""
	Created: 12.09.2007, KP
	Description: A visualization mode used to show a MIP of the viewed data
	"""
	count = 0
	def __init__(self, parent, **kws):
		"""
		Initialize the panel
		"""
		self.mip = None
		PreviewFrame.PreviewFrame.__init__(self, parent, **kws)
		self.z = -1

	def getVoxelValue(self, event):
		"""
		Send an event containing the current voxel position
		"""
		self.rawImage = self.currentImage
		self.rawImages = [self.rawImage]
		PreviewFrame.PreviewFrame.getVoxelValue(self, event)


	def setPreviewedSlice(self, obj, event, newz = -1):
		"""
		Sets the preview to display the selected z slice
		"""
		self.z = -1
	def setZSlice(self, z):
		"""
		Sets the optical slice to preview
		"""
		self.z = -1
		

	def processOutputData(self, data):
		"""
		Process the data before it's send to the preview
		"""
		data.UpdateInformation()
		if not self.mip:
			self.mip = vtkbxd.vtkImageSimpleMIP()
		else:
			self.mip.RemoveAllInputs()
		self.mip.SetInput(data)
		data = self.mip.GetOutput()
		return PreviewFrame.PreviewFrame.processOutputData(self, data)
