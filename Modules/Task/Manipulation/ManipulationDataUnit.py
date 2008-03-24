# -*- coding: iso-8859-1 -*-
"""
 Unit: ManipulationDataUnit
 Project: BioImageXD
 Created: 01.01.2004, KP
 Description: A dataunit class that represents a data unit Manipulated through filters

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

__author__ = "BioImageXD Project <http://www.bioimagexd.org/>"
__version__ = "$Revision: 1.93 $"
__date__ = "$Date: 2005/01/13 14:09:15 $"

from lib.DataUnit.CombinedDataUnit import CombinedDataUnit
import ManipulationSettings
import vtk

class ManipulationDataUnit(CombinedDataUnit):
	"""
	A class representing a dataunit manipulated with the process task
	"""

	def __init__(self, name = ""):
		"""
		Constructor
		"""
		CombinedDataUnit.__init__(self, name)
		self.original = None
		self.initialized = 0
		self.checkDimensions = False
		self.modifiedDimensions = None
		
	def setModifiedDimensions(self, dims):
		"""
		Set the dimensions reported by this combined dataunit
		"""
		self.modifiedDimensions = dims
		
	def getDimensions(self):
		"""
		An method for getting the dataunit dimensions that can be overriden 
		"""
		if not self.modifiedDimensions:
			return CombinedDataUnit.getDimensions(self)
		else:
			return self.modifiedDimensions
		
		
	def setOriginal(self, datasource):
		"""
		Sets the original DataUnit for this ManipulationedSourceDataUnit
		Parameters: dataUnit  The original unmodified DataUnit
		"""
		self.original = datasource
		self.length = datasource.getNumberOfTimepoints()
		

	def getColorTransferFunction(self):
		"""
		Returns the ctf of the source dataunit
		"""
		sources = self.getSourceDataUnits()
		if not self.initialized:
			self.initialized = 1
			if len(sources) == 1:        
				ctf = sources[0].getSettings().get("ColorTransferFunction")
				self.settings.set("ColorTransferFunction", ctf)
				return ctf
			else:
				ctf = sources[0].getSettings().get("ColorTransferFunction")           
				start, end = ctf.GetRange()
				ctf = vtk.vtkColorTransferFunction()
				ctf.AddRGBPoint(0, 0, 0, 0)
				ctf.AddRGBPoint(end, 1.0, 1.0, 1.0)
				self.settings.set("ColorTransferFunction", ctf)
				return ctf
		return self.settings.get("ColorTransferFunction")
	   
	def addSourceDataUnit(self, dataUnit, **args):
		"""
		Adds a source data unit to this dataunit
		"""
		self.setOriginal(dataUnit)    
		CombinedDataUnit.addSourceDataUnit(self, dataUnit, **args)
		self.name = "Manipulated %s" % dataUnit.getName()
		self.updateSettings()
		#print self.settings.get("ColorTransferFunction")
  

	def getSettingsClass(self):
		"""
		Return the class that represents settings for this dataunit
		"""
		return ManipulationSettings.ManipulationSettings

	def switchDatasets(self):
		"""
		Initialize Manipulation dataunit again when dataset is switched
		"""
		self.initialized = 0
		
