# -*- coding: iso-8859-1 -*-

"""
 Unit: Axes
 Project: BioImageXD
 Description:

 A module containing axes for visualization
 
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

from Visualizer.VisualizationModules import VisualizationModule
from Visualizer.ModuleConfiguration import ModuleConfigurationPanel
import vtk
import scripting
import types
import GUI.GUIBuilder
import math

def getClass():
	return AxesModule

def getConfigPanel():
	return AxesConfigurationPanel

def getName():
	return "Axes"

class AxesModule(VisualizationModule):
	"""
	A module for showing a scale bar
	"""    
	def __init__(self, parent, visualizer, **kws):
		"""
		Initialization
		"""
		self.x, self.y, self.z = -1, -1, -1
		self.renew = 1
		self.mapper = vtk.vtkPolyDataMapper()
		self.axes = None
		VisualizationModule.__init__(self, parent, visualizer, **kws)
		iactor = self.wxrenwin.GetRenderWindow().GetInteractor()

		self.descs = {"X": "X axis", "Y": "Y axis", "Z": "Z axis"}
		self.axes = axes = vtk.vtkAxesActor()
		axes.SetShaftTypeToCylinder()
		axes.SetXAxisLabelText("X")
		axes.SetYAxisLabelText("Y")
		axes.SetZAxisLabelText("Z")
		axes.SetTotalLength(2.0, 2.0, 2.0)
		self.length = math.sqrt(2.0**2 + 2.0**2 + 2.0**2)
		
		tprop = vtk.vtkTextProperty()
		tprop.ItalicOn()
		tprop.ShadowOn()
		tprop.SetFontFamilyToTimes()
		axes.GetXAxisCaptionActor2D().SetCaptionTextProperty(tprop)
		tprop2 = vtk.vtkTextProperty()
		tprop2.ShallowCopy(tprop)
		axes.GetYAxisCaptionActor2D().SetCaptionTextProperty(tprop2)
		tprop3 = vtk.vtkTextProperty()
		tprop3.ShallowCopy(tprop)
		axes.GetZAxisCaptionActor2D().SetCaptionTextProperty(tprop3)  
		self.renderer = self.parent.getRenderer()
		self.actor = self.axes
		self.marker = vtk.vtkOrientationMarkerWidget()
		self.marker.SetOutlineColor(0.93, 0.57, 0.13)
		self.marker.SetOrientationMarker(axes)
		self.marker.SetViewport(0.0, 0.0, 0.2, 0.2)
		
		self.marker.SetInteractor(iactor)
		self.marker.SetEnabled(1)
		self.marker.InteractiveOff()
		self.filterDesc = "Add axes in 3D view"
		
	def setDataUnit(self, dataunit):
		"""
		Sets the dataunit this module uses for visualization
		"""       
		VisualizationModule.setDataUnit(self, dataunit)

	def setParameter(self, parameter, value):
		"""
		Set parameter and update axes
		"""
		VisualizationModule.setParameter(self, parameter, value)
		if self.axes:
			x,y,z = self.parameters["X"], self.parameters["Y"], self.parameters["Z"]
			self.axes.SetTotalLength(x,y,z)
			length = math.sqrt(x**2 + y**2 + z**2) / self.length
			self.marker.SetViewport(0.0, 0.0, 0.2 * length, 0.2 * length)
		
	def getParameterLevel(self, parameter):
		"""
		Return parameter level
		"""
		return scripting.COLOR_BEGINNER

	def getParameters(self):
		"""
		Return parameters for GUI
		"""
		return [["Axes length", ("X", "Y", "Z")]]

	def getDefaultValue(self, parameter):
		"""
		Return default value of parameter
		"""
		return 2.0

	def getType(self, parameter):
		"""
		Return type of parameter
		"""
		return types.FloatType
		
	def showTimepoint(self, value):
		"""
		Set the timepoint to be displayed
		"""          
		self.updateRendering()
		
	def updateRendering(self, e1 = None, e2 = None):
		"""
		Update the Rendering of this module
		"""             
		#self.mapper.Update()
		VisualizationModule.updateRendering(self, input)
		self.wxrenwin.Render()    

	def disableRendering(self):
		"""
		Disable the Rendering of this module
		"""          
		#self.renderer.RemoveActor(self.actor)
		self.marker.Off()
		self.wxrenwin.Render()
		
	def enableRendering(self):
		"""
		Enable the Rendering of this module
		"""          
		#self.renderer.AddActor(self.actor)
		self.marker.On()
		self.wxrenwin.Render()
		
	def setProperties(self, ambient, diffuse, specular, specularpower, viewangle):
		"""
		A dummy method that captures the call for setting the
					 different properties
		"""
		pass

	def canSelectChannels(self):
		"""
		"""
		return 0
		
class AxesConfigurationPanel(ModuleConfigurationPanel):

	def __init__(self, parent, visualizer, name = "Axes", **kws):
		"""
		Initialization
		"""     
		ModuleConfigurationPanel.__init__(self, parent, visualizer, name, **kws)
	
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
		self.contentSizer.Add(self.gui, (0,0))
		
	def onApply(self, event):
		"""
		"""
		self.module.updateRendering()
		
