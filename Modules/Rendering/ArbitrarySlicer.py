# -*- coding: iso-8859-1 -*-

"""
 Unit: ArbitrarySlicer
 Project: BioImageXD
 Created: 28.04.2005, KP
 Description:

 A module containing the arbitrary slices module for the visualization
		  
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
__version__ = "$Revision: 1.9 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

from Visualizer.ModuleConfiguration import ModuleConfigurationPanel
from Visualizer.VisualizationModules import VisualizationModule
import vtk
import wx

def getClass():
	return ArbitrarySliceModule

def getConfigPanel():
	return ArbitrarySliceConfigurationPanel

def getName():
	return "Arbitrary slices"

class ArbitrarySliceModule(VisualizationModule):
	"""
	Class: ArbitrarySliceModule
	Created: 03.05.2005, KP
	Description: A module for slicing the dataset
	"""    
	def __init__(self, parent, visualizer, **kws):
		"""
		Method: __init__(parent)
		Created: 03.05.2005, KP
		Description: Initialization
		"""     
		self.x, self.y, self.z = -1, -1, -1
		VisualizationModule.__init__(self, parent, visualizer, **kws)   
		#self.name = "Arbitrary Slices"
		self.on = 0
		self.renew = 1
		self.mapper = vtk.vtkPolyDataMapper()
		
		self.outline = vtk.vtkOutlineFilter()
		self.outlineMapper = vtk.vtkPolyDataMapper()
		self.outlineActor = vtk.vtkActor()
		self.outlineActor.SetMapper(self.outlineMapper)
		
		self.picker = vtk.vtkCellPicker()
		self.picker.SetTolerance(0.5)
		
		self.planes = []
		self.renderer = self.parent.getRenderer()
		self.renderer.AddActor(self.outlineActor)
		
		self.ctf = None
		self.origin = None
		self.spacing = None
		self.extent = None
		
		
		#self.updateRendering()
		
	def addPlane(self):
		"""
		Method: addPlane()
		Created: 16.05.2005, KP
		Description: Add a plane
		"""       
		print "Adding plane"
		plw = vtk.vtkImagePlaneWidget()
		#self.planeWidget.DisplayTextOn()
		
		plw.SetPicker(self.picker)
		
		plw.SetResliceInterpolateToCubic()
		
		iactor = self.wxrenwin.GetRenderWindow().GetInteractor()
		plw.SetInteractor(iactor)
		self.planes.append(plw)
		if self.ctf:
			plw.GetColorMap().SetLookupTable(self.ctf)
		self.renew = 1

		
	def setDataUnit(self, dataunit):
		"""
		Method: setDataUnit(self)
		Created: 28.04.2005, KP
		Description: Sets the dataunit this module uses for visualization
		"""       
		VisualizationModule.setDataUnit(self, dataunit)
		print "got dataunit", dataunit
		data = self.dataUnit.getTimepoint(0)
		self.origin = data.GetOrigin()
		self.spacing = data.GetSpacing()
		self.extent = data.GetWholeExtent()

		x = self.extent[1] / 2
		y = self.extent[3] / 2
		z = self.extent[5] / 2
		self.setDisplaySlice(x, y, z)

		ctf = self.dataUnit.getColorTransferFunction()
		self.ctf = ctf
		for planeWidget in self.planes:
			planeWidget.GetColorMap().SetLookupTable(ctf)
#        self.planeWidget.maxDim = x
		
	
	def setDisplaySlice(self, x, y, z):
		"""
		Method: setDisplaySlice
		Created: 04.05.2005, KP
		Description: Set the slices to display
		"""           
		self.x, self.y, self.z = x, y, z
		#self.parent.getRenderer().ResetCameraClippingRange()
		#self.wxrenwin.GetRenderWindow().Render()
		print "Showing slices ", self.x, self.y, self.z

	def showTimepoint(self, value):
		"""
		Method: showTimepoint(tp)
		Created: 28.04.2005, KP
		Description: Set the timepoint to be displayed
		"""          
		self.renew = 1
		VisualizationModule.showTimepoint(self, value)
		
		
	def updateRendering(self):
		"""
		Method: updateRendering()
		Created: 03.05.2005, KP
		Description: Update the Rendering of this module
		"""             
		self.outline.SetInput(self.data)
		self.outlineMapper.SetInput(self.outline.GetOutput())
		
		self.outlineMapper.Update()

		if self.renew:
			for planeWidget in self.planes:
				planeWidget.SetInput(self.data)
			self.renew = 0
		#self.planeWidget.SetSliceIndex(self.x)
		
		if not self.on:
			for planeWidget in self.planes:
				planeWidget.On()
			self.on = 1
		
		#self.mapper.Update()
		VisualizationModule.updateRendering(self, input)
		self.parent.Render()    

	def disableRendering(self):
		"""
		Method: disableRendering()
		Created: 15.05.2005, KP
		Description: Disable the Rendering of this module
		"""          
		self.renderer.RemoveActor(self.outlineActor)
		for planeWidget in self.planes:
			planeWidget.Off()
		self.wxrenwin.Render()
		
	def enableRendering(self):
		"""
		Method: enableRendering()
		Created: 15.05.2005, KP
		Description: Enable the Rendering of this module
		"""          
		self.renderer.AddActor(self.outlineActor)
		for planeWidget in self.planes:
			planeWidget.On()
		self.wxrenwin.Render()
		
	def setProperties(self, ambient, diffuse, specular, specularpower):
		"""
		Method: setProperties(ambient,diffuse,specular,specularpower)
		Created: 16.05.2005, KP
		Description: Set the ambient, diffuse and specular lighting of this module
		"""         
		for widget in self.planes:
			property = widget.GetTexturePlaneProperty()
			property.SetAmbient(ambient)
			property.SetDiffuse(diffuse)
			property.SetSpecular(specular)
			property.SetSpecularPower(specularpower)
		
	def setShading(self, shading):
		"""
		Method: setShading(shading)
		Created: 16.05.2005, KP
		Description: Set shading on / off
		"""          
		for widget in self.planes:
			property = widget.GetTexturePlaneProperty()
			if shading:
				property.ShadeOn()
			else:
				property.ShadeOff()        

class ArbitrarySliceConfigurationPanel(ModuleConfigurationPanel):

	def __init__(self, parent, visualizer, name = "Arbitrary Slices", **kws):
		"""
		Method: __init__(parent)
		Created: 04.05.2005, KP
		Description: Initialization
		"""     
		ModuleConfigurationPanel.__init__(self, parent, visualizer, name, **kws)
	
	def initializeGUI(self):
		"""
		Method: initializeGUI()
		Created: 28.04.2005, KP
		Description: Initialization
		"""  
		self.addButton = wx.Button(self, -1, "Add plane")
		self.addButton.Bind(wx.EVT_BUTTON, self.onAddPlane)
		self.contentSizer.Add(self.addButton, (0, 0), flag = wx.EXPAND | wx.LEFT | wx.RIGHT)
		
		self.shadingBtn = wx.CheckBox(self, -1, "Use shading")
		self.shadingBtn.SetValue(1)
		self.shading = 1
		self.shadingBtn.Bind(wx.EVT_CHECKBOX, self.onCheckShading)
		
		self.lightSizer.Add(self.shadingBtn, (4, 0))
  
	def onAddPlane(self, event):
		"""
		Method: onAddPLane
		Created: 16.05.2005, KP
		Description: Add a plane
		"""  
		print "self.module=", self.module
		self.module.addPlane()
		self.module.updateRendering()
		
	def onCheckShading(self, event):
		"""
		Method: onCheckShading
		Created: 16.05.2005, KP
		Description: Toggle use of shading
		"""  
		self.shading = event.IsChecked()

	def setModule(self, module):
		"""
		Method: setModule(module)
		Created: 28.04.2005, KP
		Description: Set the module to be configured
		"""  
		ModuleConfigurationPanel.setModule(self, module)
		print "Setting module to ", module
