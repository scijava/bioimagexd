# -*- coding: iso-8859-1 -*-

"""
 Unit: Surface
 Project: BioImageXD
 Created: 28.04.2005, KP
 Description:

 A module for rendering the polygonal datasets 
		   
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
import lib.messenger
import Logging
import optimize
import scripting
import types
from Visualizer.VisualizationModules import VisualizationModule
from Visualizer.ModuleConfiguration import ModuleConfigurationPanel
import Volume
import vtk

def getClass():
	return PolydataVisualization

def getConfigPanel():
	return PolydataVisualizationPanel

def getName():
	return "Surface measurements"

def getQuickKeyCombo(): 
	return "Shift-Ctrl-S"

class PolydataVisualization(VisualizationModule):
	"""
	A surface Rendering module
	"""    
	def __init__(self, parent, visualizer, **kws):
		"""
		Initialization
		"""     
		self.init = False
		VisualizationModule.__init__(self, parent, visualizer, numberOfInputs = (2,2), **kws)   
		#self.name = "Surface Rendering"
		self.normals = vtk.vtkPolyDataNormals()
		self.smooth = None
		self.volumeModule = None
		self.scalarRange = (0, 255)
		for i in range(1, 3):
			self.setInputChannel(i, i)
			
		self.eventDesc = "Rendering iso-surface"
		self.decimate = vtk.vtkDecimatePro()
		self.mapper = vtk.vtkPolyDataMapper()
		self.mapper2 = vtk.vtkPolyDataMapper()
		
		self.contour = vtk.vtkMarchingCubes()
		self.contour2 = vtk.vtkDiscreteMarchingCubes()
		
		self.descs = {
			"Normals": "Smooth surface with normals", "FeatureAngle": "Feature angle of normals\n",
			"Simplify": "Simplify surface", "PreserveTopology": "Preserve topology",
			"Transparency": "Surface transparency","Distance":"Distance to consider inside",
			"MarkColor":"Mark in/outside objects with colors"
			}
		
		self.actor = self.lodActor = vtk.vtkLODActor()
		self.lodActor.SetMapper(self.mapper)
		self.lodActor.SetNumberOfCloudPoints(10000)
		
		self.actor2 = vtk.vtkLODActor()
		self.actor2.SetMapper(self.mapper2)
		self.actor2.SetNumberOfCloudPoints(10000)
		self.renderer = self.parent.getRenderer()
		self.renderer.AddActor(self.lodActor)
		self.renderer.AddActor(self.actor2)
		
		lib.messenger.connect(None, "highlight_object", self.onHighlightObject)

	def setParameter(self, parameter, value):
		"""
		Set a value for the parameter
		"""    
		lib.ProcessingFilter.ProcessingFilter.setParameter(self, parameter, value)
		if parameter == "Distance":
			if self.init:
				self.setLookupTableBasedOnDistance(value)
				self.parent.Render()    
		elif parameter == "Transparency":
			if self.init:
				self.updateOpacity()
				self.parent.Render()
			
			
	def onHighlightObject(self, senderObj, event, value):
		"""
		Highlight the given object
		"""
		ctf = vtk.vtkColorTransferFunction()
		ctf.AddRGBPoint(0, 0,0,1.0)
		ctf.AddRGBPoint(value-1, 0,0,1.0)
		ctf.AddRGBPoint(value, 0, 1.0, 0)
		ctf.AddRGBPoint(value+1, 0, 0, 1.0)
		ctf.AddRGBPoint(3000, 0, 0, 1.0)
		self.mapper2.SetLookupTable(ctf)
		
	def getParameterLevel(self, parameter):
		"""
		Return the level of the given parameter
		"""
		if parameter in ["FeatureAngle", "Normals"]:
			return scripting.COLOR_EXPERIENCED
		if parameter == "PreserveTopology":
			return scripting.COLOR_INTERMEDIATE
		
		
		return scripting.COLOR_BEGINNER            
		

	def setScalarRange(self, min, max):
		"""
		Set the scalar range of this module
		"""   
		self.scalarRange = (min, max)
		lib.messenger.send(self, "update_SurfaceRangeBegin")
		lib.messenger.send(self, "update_SurfaceRangeEnd")
		lib.messenger.send(self, "update_SurfaceAmnt")
		lib.messenger.send(self, "update_IsoValue")
		print "Scalar range of data=", min, max
		
	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""            
		return [
				["Smoothing options", \
					( "Normals", "FeatureAngle", "Simplify", "PreserveTopology") ], \
				["Multiple Surfaces", ( "Transparency",)],
				["Measurements",("Distance","MarkColor")]
		]
		
	def getRange(self, parameter):
		"""
		If a parameter has a certain range of valid values, the values can be queried with this function
		"""     
		if parameter in ["Simplify", "Transparency"]:
			return 0, 100
		if parameter == "FeatureAngle":
			return 0, 180
		if parameter in ["Distance"]:
			return 0,200
		return - 1, -1
		
	def getDefaultValue(self, parameter):
		"""
		Return the default value of a parameter
		"""           
		if parameter == "Distance":
			return 10
		if parameter == "Normals": 
			return 1
		if parameter == "FeatureAngle": 
			return 45   
		if parameter == "Simplify": 
			return 0
		if parameter == "PreserveTopology": 
			return 1
		if parameter == "Transparency": 
			return 0
		return 1
			
	def getType(self, parameter):
		"""
		Return the type of the parameter
		"""   

		if parameter in ["Gaussian", "Normals", "PreserveTopology", "MultipleSurfaces", "SavePolyData","MarkColor"]: 
			return types.BooleanType
		if parameter in ["Simplify", "IsoValue", "Transparency","Distance"]: 
			return GUI.GUIBuilder.SLICE
		if parameter in ["SurfaceRangeBegin", "SurfaceRangeEnd", "SurfaceAmnt", "FeatureAngle"]: 
			return GUI.GUIBuilder.SPINCTRL

		
	def setDataUnit(self, dataunit):
		"""
		Sets the dataunit this module uses for visualization
		"""       
		VisualizationModule.setDataUnit(self, dataunit)
#        self.data=self.dataUnit.getTimepoint(0)
		
	def showTimepoint(self, value, update = 1):
		"""
		Show the given timepoint
		"""
		VisualizationModule.showTimepoint(self, value, update)
		min, max = self.data.GetScalarRange()
		#if (min,max) != self.scalarRange:
		self.setScalarRange(min, max)
				
				
	def setLookupTableBasedOnDistance(self, distance):
		"""
		Set the color lookup table of channel 2  to be based on the given distance
		"""
		inputDataUnit2 = self.getInputDataUnit(2)
		print "inputDataUnit2=",inputDataUnit2
		if not inputDataUnit2:
			return
		input2 = self.getInput(2)
		minval, maxval = input2.GetScalarRange()
		settings = inputDataUnit2.getSettings()
		filterList = settings.get("FilterList")
		distanceList = filterList.getResultVariable("DistanceList")
		if not distanceList:
			return
		ctf = vtk.vtkColorTransferFunction()
		for i in range(1, maxval):
			d = distanceList[i]
			r,g,b = (0,1.0,0)
			if d > self.parameters["Distance"]:
				r,g,b = (0,0,1.0)
			ctf.AddRGBPoint(i, r,g,b)
		self.mapper2.SetLookupTable(ctf)
		self.parent.Render()

	def updateOpacity(self):
		opacity = self.parameters["Transparency"]
		opacity = (100 - opacity) / 100.0
		Logging.info("Using opacity ",  opacity, kw = "visualizer")
		if opacity != 1:
			cullers = self.parent.getRenderer().GetCullers()
			cullers.InitTraversal()
			culler = cullers.GetNextItem()
			culler.SetSortingStyleToBackToFront()
		
		self.actor.GetProperty().SetOpacity(opacity)

	def updateRendering(self):
		"""
		Update the Rendering of this module
		"""           
		self.mapper.AddObserver("ProgressEvent", lib.messenger.send)
		lib.messenger.connect(self.mapper, 'ProgressEvent', self.updateProgress)
		dataUnit = self.getInputDataUnit(1)
		inputDataUnit2 = self.getInputDataUnit(2)
	
		settings = inputDataUnit2.getSettings()
		filterList = settings.get("FilterList")
	
		if not dataUnit:
			dataUnit = self.dataUnit
		self.mapper.SetLookupTable(dataUnit.getColorTransferFunction())
		self.mapper.ScalarVisibilityOn()
		
		min, max = self.data.GetScalarRange()
		
		#if (min,max) != self.scalarRange:
		self.setScalarRange(min, max)
		
		dataUnit = self.getInputDataUnit(1)
		self.mapper.ColorByArrayComponent(0, 0)
		self.mapper.SetScalarRange(min, max)
		self.mapper.SetColorModeToMapScalars()
		self.mapper.SetLookupTable(dataUnit.getColorTransferFunction())
		self.mapper.ScalarVisibilityOn()
		
		self.updateOpacity()
		#self.actor2.GetProperty().SetOpacity(opacity)
		
		polyinput = self.getPolyDataInput(1)
		if polyinput:
			Logging.info("Using polydata input", kw="visualizer")
			VisualizationModule.updateRendering(self, polyinput)
		else:
			input = self.getInput(1)
		
			x, y, z = self.dataUnit.getDimensions()
			input = optimize.optimize(image = input, updateExtent = (0, x - 1, 0, y - 1, 0, z - 1))
			self.contour.SetInput(input)
			polyinput = self.contour.GetOutput()
		
		
		input2 = self.getInput(2)
		minval, maxval = input2.GetScalarRange()
		
		input2.Update()
		self.contour2.SetInput(input2)
		print "Generating",maxval-1,"values in range",1,maxval
		self.contour2.GenerateValues(maxval-1, 1, maxval)
		n = self.contour2.GetNumberOfContours()
		for i in range(0, n):
			self.contour2.SetValue(i, int(self.contour2.GetValue(i)))

		self.mapper2.ColorByArrayComponent(0, 0)
		self.mapper2.SetScalarRange(min, max)
		
		if not self.parameters["MarkColor"]:
			self.mapper2.SetLookupTable(inputDataUnit2.getColorTransferFunction())
		else:
			self.setLookupTableBasedOnDistance(self.parameters["Distance"])

		print "\n\n\n*** INPUT DATAUNIT2=",inputDataUnit2
		self.mapper2.SetColorModeToMapScalars()
		self.mapper2.ScalarVisibilityOn()
			
		polyinput2 = self.contour2.GetOutput()

		decimateLevel = self.parameters["Simplify"] 
		preserveTopology = self.parameters["PreserveTopology"] 
		if decimateLevel != 0:            
			self.decimate.SetPreserveTopology(preserveTopology)
			if not preserveTopology:
				self.decimate.SplittingOn()
				self.decimate.BoundaryVertexDeletionOn()
			else:
				self.decimate.SplittingOff()
				self.decimate.BoundaryVertexDeletionOff()
			self.decimate.SetTargetReduction(decimateLevel / 100.0)
			
			Logging.info("Decimating %.2f%%, preserve topology: %s" \
						% (decimateLevel, preserveTopology), kw = "visualizer")
			self.decimate.SetInput(polyinput)
			polyinput = self.decimate.GetOutput()
		
		
		if self.parameters["Normals"]:
			angle = self.parameters["FeatureAngle"]
			Logging.info("Generating normals at angle", angle, kw = "visualizer")
			self.normals.SetFeatureAngle(angle)
			self.normals.SetInput(polyinput)
			polyinput = self.normals.GetOutput()
		
		self.mapper.SetInput(polyinput)
		self.mapper2.SetInput(polyinput2)
		self.init = True
		VisualizationModule.updateRendering(self, polyinput)
		self.parent.Render()    

class PolydataVisualizationPanel(ModuleConfigurationPanel):
	def __init__(self, parent, visualizer, name = "Polydata measurements", **kws):
		"""
		Initialization
		"""     
		ModuleConfigurationPanel.__init__(self, parent, visualizer, name, **kws)
		self.method = 0
		
	def onApply(self, event):
		"""
		Apply the changes
		"""     
		ModuleConfigurationPanel.onApply(self, event)
			
		self.module.updateData()
		self.module.updateRendering()

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
		#print "module=",module
		self.module = module
		self.gui = GUI.GUIBuilder.GUIBuilder(self, self.module)
		
		self.contentSizer.Add(self.gui, (0, 0))
		
		self.module.setScalarRange(*self.module.scalarRange)
		self.module.sendUpdateGUI()
