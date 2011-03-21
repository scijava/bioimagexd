# -*- coding: iso-8859-1 -*-

"""
 Unit: ClippingPlane
 Project: BioImageXD
 Description:

 A module containing a clipping plane module
		   
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

import GUI.GUIBuilder
import types
from Visualizer.ModuleConfiguration import ModuleConfigurationPanel
from Visualizer.VisualizationModules import VisualizationModule
import vtk

def getClass():
	return ClippingPlaneModule

def getConfigPanel():
	return ClippingPlaneConfigurationPanel

def getName():
	return "Clipping plane"

class ClippingPlaneModule(VisualizationModule):
	"""
	A module for clipping the dataset
	"""    
	def __init__(self, parent, visualizer, **kws):
		"""
		Initialization
		"""
		self.x, self.y, self.z = -1, -1, -1
		#self.name = "Clipping Plane"
		self.parent = parent        
		self.on = 0
		self.renew = 1
		self.currentPlane = None
		self.clipped = 0
		self.clippedModules = []
		self.planeWidget = vtk.vtkPlaneWidget()
		self.planeWidget.AddObserver("InteractionEvent", self.clipVolumeRendering)
		self.planeWidget.SetResolution(20)
		self.planeWidget.SetRepresentationToOutline()
		self.planeWidget.NormalToXAxisOn()
		self.renderer = self.parent.getRenderer()
		self.plane = vtk.vtkPlane()

		iactor = parent.wxrenwin.GetRenderWindow().GetInteractor()
		self.planeWidget.SetInteractor(iactor)
		VisualizationModule.__init__(self, parent, visualizer, **kws)
		
		self.descs = {"ShowControl": "Show controls",
					  "AllModules": "Clip all modules",
					  "ClippedModule": "Module to clip"}
		self.filterDesc = "Clip rendering using a plane"
		
	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""
		return [["", ("ClippedModule", "AllModules", "ShowControl")]]

	def getDefaultValue(self, parameter):
		"""
		Return the default value of a parameter
		"""           
		if parameter == "ShowControl":
			return True

		if parameter == "AllModules":
			return False

		if parameter == "ClippedModule":
			return 0
		
	def setParameter(self, parameter, value):
		"""
		set the value of a parameter to value
		"""
		VisualizationModule.setParameter(self, parameter, value)
		if parameter == "ShowControl":
			self.showPlane(value)
		if parameter in ["AllModules", "ClippedModule"]:
			self.clipWithCurrentPlane()

	def getType(self, parameter):
		"""
		Return the type of the parameter
		"""    
		if parameter in ["ShowControl", "AllModules"]:
			return types.BooleanType
		if parameter == "ClippedModule":
			return GUI.GUIBuilder.CHOICE        

	def getRange(self, parameter):
		"""
		If a parameter has a certain range of valid values, the values can be queried with this function
		"""     
		names = [module.getName() for module in self.parent.getModules()]
		names.remove(self.getName())
		return names
		
	def __getstate__(self):
		"""
		A getstate method that saves the lights
		"""            
		odict = VisualizationModule.__getstate__(self)
		odict.update({"planeWidget":self.getVTKState(self.planeWidget)})
		odict.update({"currentPlane":self.getVTKState(self.currentPlane)})
		odict.update({"renderer":self.getVTKState(self.renderer)})
		odict.update({"camera":self.getVTKState(self.renderer.GetActiveCamera())})
		odict.update({"clipped":self.clipped})
		return odict
		
	def __set_pure_state__(self, state):
		"""
		Set the state of the light
		"""        
		self.setVTKState(self.planeWidget, state.planeWidget)
		self.setVTKState(self.currentPlane, state.currentPlane)
		self.setVTKState(self.renderer, state.renderer)
		self.setVTKState(self.renderer.GetActiveCamera(), state.camera)

		self.clipped = state.clipped
		if self.clipped:
			self.clipVolumeRendering(self.planeWidget, None)
		VisualizationModule.__set_pure_state__(self, state)
				
		
	def removeClippingPlane(self, plane):
		"""
		Remove a clipping plane
		"""       
		for module in self.clippedModules:
			if hasattr(module, "mapper") and hasattr(module.mapper, "RemoveClippingPlane") and module.mapper.GetClippingPlanes():
				module.mapper.RemoveClippingPlane(plane)
				self.clipped = 0
		
	def getModulesToClip(self):
		"""
		return all the visualizer modules that are to be clipped based on user choices
		"""
		if not self.parameters.get("AllModules", 0):
			modname = self.parent.getModules()[self.parameters["ClippedModule"]].getName()
			modules = filter(lambda x, n = modname:x.getName() == n, self.parent.getModules())
		else:
			modules = self.parent.getModules()
		return modules
		
	def clipVolumeRendering(self, object, event):
		"""
		Called when the plane is interacted with
		"""
		if self.currentPlane:
			self.removeClippingPlane(self.currentPlane)
			self.currentPlane = None
		object.GetPlane(self.plane)
		self.clipWithCurrentPlane()
		
	def clipWithCurrentPlane(self):
		"""
		clip the selected mappers with the current clipping plane
		"""
		if self.currentPlane:
			self.removeClippingPlane(self.currentPlane)
		
		modules = self.getModulesToClip()
		self.clippedModules = modules
		for module in modules:
			if hasattr(module, "mapper") and hasattr(module.mapper, "AddClippingPlane"):
				module.mapper.AddClippingPlane(self.plane)
				self.currentPlane = self.plane
				self.clipped = 1
		
	def setDataUnit(self, dataunit):
		"""
		Sets the dataunit this module uses for visualization
		"""
		VisualizationModule.setDataUnit(self, dataunit)	
		data = self.getInput(1)

		self.origin = data.GetOrigin()
		self.spacing = data.GetSpacing()
		self.extent = data.GetWholeExtent()
		
		y = self.extent[3]
		x = self.extent[1]
		
		self.planeWidget.SetInput(data)
		self.planeWidget.SetOrigin(-32, -32, -32)
		self.planeWidget.SetPoint1(0, y + 32, 0)
		self.planeWidget.SetPoint2(x + 32, 0, 0)
		self.planeWidget.PlaceWidget()

	def showTimepoint(self, value):
		"""
		Set the timepoint to be displayed
		"""          
		self.renew = 1
		VisualizationModule.showTimepoint(self, value)
		
	def updateRendering(self):
		"""
		Update the Rendering of this module
		"""
		#self.outline.SetInput(self.data)
		#self.outlineMapper.SetInput(self.outline.GetOutput())
		
		#self.outlineMapper.Update()

		if self.renew:
			data = self.getInput(1)
			self.planeWidget.SetInput(data)
			self.renew = 0
		
		if not self.on:
			self.planeWidget.On()
			self.on = 1
		
		#self.mapper.Update()
		VisualizationModule.updateRendering(self, input)
		self.parent.Render()    

	def disableRendering(self):
		"""
		Disable the Rendering of this module
		"""
		if self.currentPlane:
			self.removeClippingPlane(self.currentPlane)        
		self.planeWidget.Off()
		self.wxrenwin.Render()
		
	def showPlane(self, flag):
		"""
		Show / hide the plane controls
		"""
		if flag:
			self.planeWidget.On()
		else:
			self.planeWidget.Off()
		
	def enableRendering(self):
		"""
		Enable the Rendering of this module
		"""
		self.planeWidget.On()
		self.wxrenwin.Render()
		
	def setProperties(self, ambient, diffuse, specular, specularpower, viewangle):
		"""
		Set the ambient, diffuse and specular lighting of this module
		"""         
		pass

	def setShading(self, shading):
		"""
		Set shading on / off
		"""
		pass

	def canSelectChannels(self):
		"""
		No channel selection
		"""
		return 0

class ClippingPlaneConfigurationPanel(ModuleConfigurationPanel):

	def __init__(self, parent, visualizer, name = "Clipping plane", **kws):
		"""
		Initialization
		"""     
		ModuleConfigurationPanel.__init__(self, parent, visualizer, name, **kws)
		self.gui = None
	
	def initializeGUI(self):
		"""
		Initialization
		"""  
		pass
		
	def setModule(self, module):
		"""
		Set the module to be configured
		"""  
		ModuleConfigurationPanel.setModule(self, module)
		self.module = module
		self.gui = GUI.GUIBuilder.GUIBuilder(self, self.module)
		self.module.sendUpdateGUI()
		self.contentSizer.Add(self.gui, (0, 0))
		
	def onApply(self, event):
		"""
		Apply the changes
		"""     
		self.module.updateRendering()
