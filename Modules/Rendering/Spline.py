# -*- coding: iso-8859-1 -*-

"""
 Unit: Spline
 Project: BioImageXD
 Created: 15.08.2005, KP
 Description:

 A module containing the Spline widget module for the visualizer
		   
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
import wx

def getClass():
	return SplineModule

def getConfigPanel():
	return SplineConfigurationPanel

def getName():
	return "Camera path"

class SplineModule(VisualizationModule):
	"""
	Class: SplinePlaneModule
	A module for slicing the dataset
	"""    
	def __init__(self, parent, visualizer, **kws):
		"""
		Method: __init__(parent)
		Initialization
		"""     
		self.x, self.y, self.z = -1, -1, -1
		VisualizationModule.__init__(self, parent, visualizer, **kws)   
		self.on = 0
		self.renew = 1
		self.mapper = vtk.vtkPolyDataMapper()
		self.eventDesc = "Rendering Camera Path"
		

		self.spline = spline = vtk.vtkSplineWidget()
		self.spline.GetLineProperty().SetColor(1, 0, 0)
		self.spline.GetHandleProperty().SetColor(0, 1, 0)
		self.spline.SetResolution(1000)

		#TODO: endInteraction is in GUI.Urmas.SplineEditor
		self.spline.AddObserver("EndInteractionEvent", self.endInteraction)
		self.spline.AddObserver("InteractionEvent", self.endInteraction)

		#TODO: iren is in GUI.Urmas.SplineEditor
		self.spline.SetInteractor(self.iren)
		#self.spline.On()
		
		#self.spline.SetEnabled(1)        
		self.renderer = self.parent.getRenderer()
		
#        iactor = self.wxrenwin.GetRenderWindow().GetInteractor()
		
		#self.updateRendering()
		
	   
	def __getstate__(self):
		"""
		Method: __getstate__
		A getstate method that saves the lights
		"""            
		odict = VisualizationModule.__getstate__(self)
		odict.update({"spline":self.getVTKState(self.spline)})
		odict.update({"renderer":self.getVTKState(self.renderer)})
		odict.update({"camera":self.getVTKState(self.renderer.GetActiveCamera())})
		return odict
		
	def __set_pure_state__(self, state):
		"""
		Method: __set_pure_state__()
		Set the state of the light
		"""        
		
		self.setVTKState(self.spline, state.spline)
		
		self.setVTKState(self.renderer, state.renderer)
		self.setVTKState(self.renderer.GetActiveCamera(), state.camera)
		VisualizationModule.__set_pure_state__(self, state)
		 
		
	def setDataUnit(self, dataunit):
		"""
		Method: setDataUnit(self)
		Sets the dataunit this module uses for visualization
		"""       
		VisualizationModule.setDataUnit(self, dataunit)
		if self.visualizer.getProcessedMode():
			data = self.dataUnit.getSourceDataUnits()[0].getTimepoint(0)
		else:
			data = self.dataUnit.getTimepoint(0)


		ctf = self.dataUnit.getColorTransferFunction()
	def showTimepoint(self, value):
		"""
		Method: showTimepoint(tp)
		Set the timepoint to be displayed
		"""          
		self.renew = 1
		VisualizationModule.showTimepoint(self, value)
		
		
	def updateRendering(self):
		"""
		Method: updateRendering()
		Update the Rendering of this module
		"""             
		if self.renew:
			self.spline.SetInput(self.data)
		
		if not self.on:
			self.spline.On()
			self.on = 1
		
		#self.mapper.Update()
		VisualizationModule.updateRendering(self, input)
		self.parent.Render()    

	def disableRendering(self):
		"""
		Method: disableRendering()
		Disable the Rendering of this module
		"""          
		self.spline.Off()
		self.wxrenwin.Render()
		
	def enableRendering(self):
		"""
		Method: enableRendering()
		Enable the Rendering of this module
		"""          
		self.spline.On()
		self.wxrenwin.Render()
		
	def setProperties(self, ambient, diffuse, specular, specularpower):
		"""
		Method: setProperties(ambient,diffuse,specular,specularpower)
		Set the ambient, diffuse and specular lighting of this module
		"""         
		for widget in [self.spline]:
			property = widget.GetProperty()
			property.SetAmbient(ambient)
			property.SetDiffuse(diffuse)
			property.SetSpecular(specular)
			property.SetSpecularPower(specularpower)
		
	def setShading(self, shading):
		"""
		Method: setShading(shading)
		Set shading on / off
		"""          
		pass
		
class SplineConfigurationPanel(ModuleConfigurationPanel):

	def __init__(self, parent, visualizer, name = "Camera Path", **kws):
		"""
		Method: __init__(parent)
		Initialization
		"""     
		ModuleConfigurationPanel.__init__(self, parent, visualizer, name, **kws)
	
	def initializeGUI(self):
		"""
		Method: initializeGUI()
		Initialization
		"""  
		
		self.shadingBtn = wx.CheckBox(self.lightPanel, -1, "Use shading")
		self.shadingBtn.SetValue(1)
		self.shading = 1
		self.shadingBtn.Bind(wx.EVT_CHECKBOX, self.onCheckShading)
		
		self.lightSizer.Add(self.shadingBtn, (4, 0))
		
	def onCheckShading(self, event):
		"""
		Method: onCheckShading
		Toggle use of shading
		"""  
		self.shading = event.IsChecked()        
		
	def setModule(self, module):
		"""
		Method: setModule(module)
		Set the module to be configured
		"""  
		ModuleConfigurationPanel.setModule(self, module)

		
	def onApply(self, event):
		"""
		Method: onApply()
		Apply the changes
		"""     
		ModuleConfigurationPanel.onApply(self, event)
		self.module.updateData()
		self.module.updateRendering()

"""
foo 
"""
