# -*- coding: iso-8859-1 -*-

"""
 Unit: Distance
 Project: BioImageXD
 Description:

 A module containing a distance widget
		   
 Copyright (C) 2006	 BioImageXD Project
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
import vtkbxd

def getClass():
	return DistanceModule

def getConfigPanel():
	return DistanceConfigurationPanel

def getName():
	return "Distance measurement"


class DistanceModule(VisualizationModule):
	"""
	A module for measuring the distance between two points
	"""	   
	def __init__(self, parent, visualizer, **kws):
		"""
		Initialization
		"""		
		self.x, self.y, self.z = -1, -1, -1
		VisualizationModule.__init__(self, parent, visualizer, **kws)	

		self.on = 0
		self.renew = 1
	
		self.distanceWidget = vtk.vtkDistanceWidget()
		self.obsTag = self.distanceWidget.AddObserver("EndInteractionEvent", self.onPlacePoint)
		self.representation = vtkbxd.vtkDistanceRepresentationScaled2D()
		self.representation.SetScaleX(1.0)
		self.representation.SetScaleZ(1.0)
		self.distanceWidget.SetRepresentation(self.representation)
		self.renderer = self.parent.getRenderer()
		iactor = self.wxrenwin.GetRenderWindow().GetInteractor()
		self.distanceWidget.SetInteractor(iactor)
		self.picker = vtk.vtkCellPicker()
		self.currentPlane = None

		#self.picker.SetTolerance(0.05)
		#self.updateRendering()
		self.filterDesc = "Measure distance in 3D view"
	  
	def onPlacePoint(self, obj, event):
		"""
		onPlacePoint
		"""		   
		p1 = [0, 0, 0]
		p2 = [0, 0, 0]
		pos1 = None
		pos2 = None
		
		self.representation.GetPoint1DisplayPosition(p1)
		self.representation.GetPoint2DisplayPosition(p2)
		if self.picker.Pick(p1, self.renderer):
			pos1 = self.picker.GetPickPosition()
			print "Got point", pos1, "by picking", p1
			selPt = self.picker.GetSelectionPoint()
			pos12 = selPt[0:2]
			self.representation.GetPoint1Representation().SetWorldPosition(pos1)
			self.representation.GetAxis().GetPoint1Coordinate().SetValue(pos1)
		if self.picker.Pick(p2, self.renderer):
			pos2 = self.picker.GetPickPosition()
			print "Got point", pos1, "by picking", p1
			selPt = self.picker.GetSelectionPoint()
			pos22 = selPt[0:2]
			self.representation.GetPoint2Representation().SetWorldPosition(pos2)
			self.representation.GetAxis().GetPoint2Coordinate().SetValue(pos2)
		self.representation.BuildRepresentation()
		self.distanceWidget.RemoveObserver(self.obsTag)
		
	def __getstate__(self):
		"""
		A getstate method that saves the lights
		"""			   
		odict = VisualizationModule.__getstate__(self)
		odict.update({"distanceWidget":self.getVTKState(self.distanceWidget)})
		
		odict.update({"renderer":self.getVTKState(self.renderer)})
		odict.update({"camera":self.getVTKState(self.renderer.GetActiveCamera())})
		return odict
		
	def __set_pure_state__(self, state):
		"""
		Set the state of the light
		"""		   
		self.setVTKState(self.distanceWidget, state.distanceWidget)
		self.setVTKState(self.currentPlane, state.currentPlane)
		self.setVTKState(self.renderer, state.renderer)
		self.setVTKState(self.renderer.GetActiveCamera(), state.camera)
		VisualizationModule.__set_pure_state__(self, state)
				
	def setDataUnit(self, dataunit):
		"""
		Sets the dataunit this module uses for visualization
		"""		  
		VisualizationModule.setDataUnit(self, dataunit)
		if self.visualizer.getProcessedMode():
			data = self.dataUnit.getSourceDataUnits()[0].getTimepoint(0)
		else:
			data = self.dataUnit.getTimepoint(0)
		self.data = data
		sx, sy, sz = data.GetSpacing()
		
		vx, vy, vz = self.dataUnit.getVoxelSize()
		scale = vx
		scale = 1000000
		self.representation.SetLabelFormat("%.2fum")
		self.representation.SetScaleX(vx)
		self.representation.SetScaleZ(vz)


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
		if self.renew:
#			 self.distanceWidget.SetInput(self.data)
			self.renew = 0
		
		if not self.on:
			self.distanceWidget.On()
			self.on = 1
		
		#self.mapper.Update()
		VisualizationModule.updateRendering(self, input)
		self.parent.Render()	

	def disableRendering(self):
		"""
		Disable the Rendering of this module
		"""			 
		self.distanceWidget.Off()
		self.wxrenwin.Render()
		
	def showPlane(self, flag):
		"""
		Show / hide the plane controls
		"""			 
		if flag:
			self.distanceWidget.On()
		else:
			self.distanceWidget.Off()
		
		
	def enableRendering(self):
		"""
		Enable the Rendering of this module
		"""			 
		self.distanceWidget.On()
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

class DistanceConfigurationPanel(ModuleConfigurationPanel):

	def __init__(self, parent, visualizer, name = "Distance", **kws):
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
		print "module=", module
		self.module = module
		
	def onApply(self, event):
		"""
		Apply the changes
		"""		
		pass
