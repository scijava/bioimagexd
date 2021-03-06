# -*- coding: iso-8859-1 -*-

"""
 Unit: NewSurface.py
 Project: BioImageXD
 Description:

 A module containing the surface rendering modules for the visualization
		   
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
	return SurfaceModule

def getConfigPanel():
	return SurfaceConfigurationPanel

def getName():
	return "Surface rendering"

def getQuickKeyCombo(): 
	return "Shift-Ctrl-S"

class SurfaceModule(VisualizationModule):
	"""
	A surface Rendering module
	"""    
	def __init__(self, parent, visualizer, **kws):
		"""
		Initialization
		"""     
		VisualizationModule.__init__(self, parent, visualizer, **kws)   
		#self.name = "Surface Rendering"
		#for i in range(1, 3):
		#	self.setInputChannel(i, i)
		self.normals = vtk.vtkPolyDataNormals()
		self.smooth = None
		self.volumeModule = None
		self.scalarRange = (0, 255)
		
		self.eventDesc = "Rendering iso-surface"
		self.decimate = vtk.vtkDecimatePro()
		self.setMethod(1)
		self.init = 0
		self.mapper = vtk.vtkPolyDataMapper()
		
		self.descs = {"Method": "Surface rendering method", "Gaussian": "Smooth surface with gaussian smoothing",
			"Normals": "Smooth surface with normals", "FeatureAngle": "Feature angle of normals\n",
			"Simplify": "Simplify surface", "PreserveTopology": "Preserve topology",
			"IsoValue": "Iso value", "SurfaceRangeBegin": "Generate surfaces in range:\n",
			"SurfaceAmnt": "Number of surfaces", "Transparency": "Surface transparency",
			"MultipleSurfaces": "Visualize multiple surfaces","SolidColor":"Color surface with max. intensity"}
		
		self.actor = self.lodActor = vtk.vtkLODActor()
		self.lodActor.SetMapper(self.mapper)
		self.lodActor.SetNumberOfCloudPoints(10000)
		self.renderer = self.parent.getRenderer()
		self.renderer.AddActor(self.lodActor)
		#self.updateRendering()
		self.filterDesc = "Create and visualize iso-surface"
		
	def getParameterLevel(self, parameter):
		"""
		Return the level of the given parameter
		"""
		if parameter in ["IsoValue", "SolidColor", "Gaussian", "Normals"]:
			return scripting.COLOR_BEGINNER
		return scripting.COLOR_EXPERIENCED
	
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
		return [["", ("Method", )], \
				["Smoothing options", \
					("Gaussian", "Normals", "FeatureAngle", "Simplify", "PreserveTopology") ], \
	   			["Iso-Surface", ("IsoValue", "SolidColor")], \
				["Surface transparency", ("Transparency",)],
				["Multiple Surfaces", \
					("MultipleSurfaces", "SurfaceRangeBegin", GUI.GUIBuilder.NOBR, \
					"SurfaceRangeEnd", "SurfaceAmnt")],
		]
		
	def getRange(self, parameter):
		"""
		If a parameter has a certain range of valid values, the values can be queried with this function
		"""     
		if parameter == "Method":
			return ["Contour Filter", "Marching Cubes", "Discrete Marching Cubes", "Iso-Surface Volume Rendering"]
		if parameter in ["Simplify", "Transparency"]:
			return 0, 100
		if parameter == "FeatureAngle":
			return 0, 180
		if parameter in ["IsoValue", "SurfaceAmnt", "SurfaceRangeBegin", "SurfaceRangeEnd"]:
			return self.scalarRange
		
		return - 1, -1
		
	def getDefaultValue(self, parameter):
		"""
		Return the default value of a parameter
		"""           
		if parameter == "SolidColor":
			return 0
		if parameter == "Method":
			return 1
		if parameter == "Gaussian": 
			return 1
		if parameter == "Normals": 
			return 1
		if parameter == "FeatureAngle": 
			return 45   
		if parameter == "Simplify": 
			return 0
		if parameter == "PreserveTopology": 
			return 1
		if parameter == "IsoValue":
			#if self.scalarRange[1] - self.scalarRange[0] <= 256:
			return 128
			#else:
			#	return int(0.75 * self.scalarRange[1])
		
		if parameter == "Transparency": 
			return 0
		if parameter == "SurfaceRangeBegin": 
			return 1
		if parameter == "SurfaceRangeEnd": 
			return 255
		if parameter == "SurfaceAmnt": 
			return 1
		if parameter == "MultipleSurfaces": 
			return 0
			
	def getType(self, parameter):
		"""
		Return the type of the parameter
		"""   
		if parameter == "Method":
			return GUI.GUIBuilder.CHOICE
		if parameter in ["Gaussian", "Normals", "PreserveTopology", "MultipleSurfaces","SolidColor"]: 
			return types.BooleanType
		if parameter in ["Simplify", "IsoValue", "Transparency"]: 
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
		minVal, maxVal = self.data.GetScalarRange()
		#if (min,max) != self.scalarRange:
		self.setScalarRange(minVal, maxVal)

	def setMethod(self, method):
		"""
		Set the Rendering method used
		"""             
		self.method = method
		if method < 3:
			#Ray Casting, RGBA Ray Casting, Texture Mapping, MIP
			filters = [vtk.vtkContourFilter, vtk.vtkMarchingCubes, vtk.vtkDiscreteMarchingCubes]
			Logging.info("Using ", filters[method], "as  contourer", kw = "visualizer")
			self.contour = filters[method]()
			if self.volumeModule:
				self.volumeModule.disableRendering()
				self.volumeModule = None
				self.enableRendering()
		else:
			Logging.info("Using volume rendering for isosurface")
			self.disableRendering()
			if not self.volumeModule:
				self.volumeModule = Volume.VolumeModule(self.parent, self.visualizer, \
														moduleName = "Volume", label = "Volume")
				#self.volumeModule.setMethod(Volume.ISOSURFACE) #TODO: no such method
				self.volumeModule.setDataUnit(self.dataUnit)
			self.volumeModule.showTimepoint(self.timepoint)

	def updateRendering(self):
		"""
		Update the Rendering of this module
		"""
		method = self.parameters["Method"]
		self.setMethod(method)

		if self.volumeModule:
			self.volumeModule.function = vtk.vtkVolumeRayCastIsosurfaceFunction()
			self.volumeModule.function.SetIsoValue(self.parameters["IsoValue"])
			self.volumeModule.showTimepoint(self.timepoint)
			return
		
		if not self.init:
			self.init = 1
			self.mapper.ColorByArrayComponent(0, 0)
		self.mapper.AddObserver("ProgressEvent", lib.messenger.send)
		lib.messenger.connect(self.mapper, 'ProgressEvent', self.updateProgress)
		dataUnit = self.getInputDataUnit(1)
		if not dataUnit:
			dataUnit = self.dataUnit
		dataCtf = dataUnit.getColorTransferFunction()
		if self.parameters["SolidColor"]:
			minval, maxval = dataCtf.GetRange()
			ctf = vtk.vtkColorTransferFunction()
			ctf.AddRGBPoint(int(minval), 0,0,0)
			r,g,b = dataCtf.GetColor(maxval)
			ctf.AddRGBPoint(int(minval) + 1, r,g,b)
			ctf.AddRGBPoint(maxval, r,g,b)
		else:
			ctf = dataCtf
		self.mapper.SetLookupTable(ctf)
		self.mapper.ScalarVisibilityOn()
		
		minVal, maxVal = self.data.GetScalarRange()
		self.setScalarRange(minVal, maxVal)
		
		self.mapper.SetScalarRange(minVal, maxVal)
		self.mapper.SetColorModeToMapScalars()
		
		opacity = self.parameters["Transparency"]
		opacity = (100 - opacity) / 100.0
		Logging.info("Using opacity ",  opacity, kw = "visualizer")
		if opacity != 1:
			cullers = self.parent.getRenderer().GetCullers()
			cullers.InitTraversal()
			culler = cullers.GetNextItem()
			culler.SetSortingStyleToBackToFront()
			#print cullers, culler
			#self.parent.getRenderer().GetRenderWindow().SetAlphaBitPlanes(1)
			#self.parent.getRenderer().GetRenderWindow().SetMultiSamples(0)
			#self.parent.getRenderer().SetUseDepthPeeling(1)
			#self.parent.getRenderer().SetMaximumNumberOfPeels(100)
			#self.parent.getRenderer().SetOcclusionRatio(1.0)
			#print self.parent.getRenderer().GetLastRenderingUsedDepthPeeling()
		
		self.actor.GetProperty().SetOpacity(opacity)
		
		polyinput = self.getPolyDataInput(1)
		if polyinput:
			Logging.info("Using polydata input", kw="visualizer")
			self.mapper.SetInput(polyinput)
			VisualizationModule.updateRendering(self, polyinput)
			self.parent.Render() 
			return

		x, y, z = self.dataUnit.getDimensions()
		input = self.getInput(1)
		input = optimize.optimize(image = input, updateExtent = (0, x - 1, 0, y - 1, 0, z - 1))
		
		if self.parameters["Gaussian"]:
			Logging.info("Doing gaussian smoothing", kw = "visualizer")
			if not self.smooth:
				self.smooth = vtk.vtkImageGaussianSmooth()
			self.smooth.SetInput(input)
			input = self.smooth.GetOutput()
		
		self.contour.SetInput(input)
		input = self.contour.GetOutput()
		
		multi = self.parameters["MultipleSurfaces"]

		
		if not multi:
			Logging.info("Using single isovalue=%d" % int(self.parameters["IsoValue"]), kw = "visualizer")
			self.contour.SetValue(0, self.parameters["IsoValue"])
		else:
			begin = self.parameters["SurfaceRangeBegin"]
			end = self.parameters["SurfaceRangeEnd"]
			n = self.parameters["SurfaceAmnt"]
			Logging.info("Generating %d values in range %d-%d" % (n, begin, end), kw = "visualizer")            
			self.contour.GenerateValues(n, begin, end)
			n = self.contour.GetNumberOfContours()
			for i in range(0, n):
				self.contour.SetValue(i, int(self.contour.GetValue(i)))
			#print self.contour

		#TODO: should decimateLevel and preserveTopology be instance variables?
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
			self.decimate.SetInput(input)
			input = self.decimate.GetOutput()
		
		if self.parameters["Normals"]:
			angle = self.parameters["FeatureAngle"]
			Logging.info("Generating normals at angle", angle, kw = "visualizer")
			self.normals.SetFeatureAngle(angle)
			self.normals.SetInput(input)
			input = self.normals.GetOutput()

		self.mapper.SetInput(input)
		VisualizationModule.updateRendering(self, input)
		self.parent.Render()


class SurfaceConfigurationPanel(ModuleConfigurationPanel):
	def __init__(self, parent, visualizer, name = "Surface rendering", **kws):
		"""
		Initialization
		"""     
		ModuleConfigurationPanel.__init__(self, parent, visualizer, name, **kws)
		self.method = 0
		
#	def setModule(self, module): #TODO: why two modules named setModule() ?
#		"""
#		Set the module to be configured
#		"""  
#		ModuleConfigurationPanel.setModule(self, module)
#		self.module.sendUpdateGUI()
		
	def onApply(self, event):
		"""
		Apply the changes
		"""     
		ModuleConfigurationPanel.onApply(self, event)
			
		self.module.updateData()
		self.module.updateRendering()
		
	def onSelectMethod(self, event):
		"""
		Select the surface rendering method
		"""  
		self.method = self.moduleChoice.GetSelection() #TODO: no variable moduleChoice
		flag = (self.method != 3)

		#self.isoRangeBegin.Enable(flag)
		#self.isoRangeEnd.Enable(flag)
		#self.isoRangeSurfaces.Enable(flag)

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
