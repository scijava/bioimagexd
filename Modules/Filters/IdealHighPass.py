#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: IdealHighPass.py
 Project: BioImageXD
 Created: 23.09.2009, LP
 Description:

 A module that contains ideal high pass filter in fourier domain for the
 processing task.
 
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
__author__ = "BioImageXD Project <http://www.bioimagexd.net/>"
__version__ = "$Revision$"
__date__ = "$Date$"

import lib.FilterTypes
import vtk
import scripting
import Modules

loader = Modules.DynamicLoader.getPluginLoader()
FourierFilters = loader.getPluginItem("Task","Process",2).FourierFilters

class IdealHighPassFilter(FourierFilters.FourierFilter):
	"""
	An ideal high pass filter in fourier domain
	"""
	name = "Ideal high pass"
	category = lib.FilterTypes.FOURIER
	level = scripting.COLOR_INTERMEDIATE

	def __init__(self, inputs = (1,1)):
		"""
		Initialization
		"""
		FourierFilters.FourierFilter.__init__(self, inputs)
		self.filter = vtk.vtkImageIdealHighPass()
