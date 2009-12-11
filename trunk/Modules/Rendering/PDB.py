# -*- coding: iso-8859-1 -*-

"""
 Unit: PDB
 Project: BioImageXD
 Created: 29.05.2006, KP
 Description:

 A PDB rendering module
		   
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

import scripting
import GUI.GUIBuilder
import types
from Visualizer.VisualizationModules import VisualizationModule
from Visualizer.ModuleConfiguration import ModuleConfigurationPanel
import vtk
import os

def getClass():
	return PDBModule

def getConfigPanel():
	return PDBConfigurationPanel

def getName():
	return "Protein Data Bank"

class PDBModule(VisualizationModule):
	"""
	A module for clipping the dataset
	"""    
	def __init__(self, parent, visualizer, **kws):
		"""
		Initialization
		"""
		self.actorsInitialized = False
		VisualizationModule.__init__(self, parent, visualizer, **kws)   

		self.descs = {"FileName": "PDB File Name",
					  "SphereRadius": "Sphere radius",
					  "TubeRadius": "Tube radius"}
		self.mapper = vtk.vtkPolyDataMapper()
		self.mapper.UseLookupTableScalarRangeOff()
		self.mapper.SetScalarVisibility(1)
		self.mapper.SetScalarModeToDefault()
		
		#make the actor from the mapper
		self.actor = vtk.vtkLODActor()
		self.actor.GetProperty().SetRepresentationToSurface()
		self.actor.GetProperty().SetInterpolationToGouraud()
		self.actor.GetProperty().SetColor(1,1,1)
		self.actor.GetProperty().SetAmbient(0.15)
		self.actor.GetProperty().SetDiffuse(0.85)
		self.actor.GetProperty().SetSpecular(0.1)
		self.actor.GetProperty().SetSpecularPower(100)
		self.actor.GetProperty().SetSpecularColor(1,1,1)
		self.actor.GetProperty().SetColor(1,1,1)		
		self.actor.SetNumberOfCloudPoints(30000)
		
		self.actor.SetMapper(self.mapper)
		self.reader = vtk.vtkPDBReader()
		self.renderer = self.parent.getRenderer()
		
		self.tubeFilter = vtk.vtkTubeFilter()
		self.tubeFilter.SetNumberOfSides(8)
		self.tubeFilter.SetCapping(0)
		self.tubeFilter.SetRadius(0.2)
		self.tubeFilter.SetVaryRadius(0)
		self.tubeFilter.SetRadiusFactor(10)
		
		self.mapper2 = vtk.vtkPolyDataMapper()
		self.mapper2.UseLookupTableScalarRangeOff()
		self.mapper2.SetScalarVisibility(1)
		self.mapper2.SetScalarModeToDefault()
		
		self.tubeActor = vtk.vtkLODActor()
		self.tubeActor.SetMapper(self.mapper2)
		self.tubeActor.GetProperty().SetRepresentationToSurface()
		self.tubeActor.GetProperty().SetInterpolationToGouraud()
		self.tubeActor.GetProperty().SetColor(1,1,1)
		self.tubeActor.GetProperty().SetAmbient(0.15)
		self.tubeActor.GetProperty().SetDiffuse(0.85)
		self.tubeActor.GetProperty().SetSpecular(0.1)
		self.tubeActor.GetProperty().SetSpecularPower(100)
		self.tubeActor.GetProperty().SetSpecularColor(1,1,1)
		self.tubeActor.SetNumberOfCloudPoints(30000)
		
		self.sphereSource = vtk.vtkSphereSource()
		self.sphereSource.SetCenter(0,0,0)
		self.sphereSource.SetRadius(1)
		self.sphereSource.SetThetaResolution(8)
		self.sphereSource.SetStartTheta(0)
		self.sphereSource.SetEndTheta(360)
		self.sphereSource.SetPhiResolution(8)
		self.sphereSource.SetStartPhi(0)
		self.sphereSource.SetEndPhi(180)
		
		self.glyph3D = vtk.vtkGlyph3D()
		self.glyph3D.SetOrient(1)
		self.glyph3D.SetColorMode(1)
		self.glyph3D.SetScaleMode(2)
		self.glyph3D.SetScaleFactor(.25)
		self.glyph3D.SetSource(self.sphereSource.GetOutput())


	def getParameterLevel(self, parameter):
		"""
		Return the level of the given parameter
		"""
		return scripting.COLOR_INTERMEDIATE
		
	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""            
		
		return [["Input", (("FileName", "Select the PDB file to visualize", "*.pdb"), )], ["Settings", ("SphereRadius", "TubeRadius")]]

		
	def getDefaultValue(self, parameter):
		"""
		Return the default value of a parameter
		"""           
		if parameter == "FileName":
			return "protein.pdb"
		if parameter == "TubeRadius":
			return 0.2
		if parameter == "SphereRadius":
			return 1.0
		
		
	def getType(self, parameter):
		"""
		Return the type of the parameter
		"""    
		if parameter == "FileName":
			return GUI.GUIBuilder.FILENAME
		return types.FloatType
		
	def __getstate__(self):
		"""
		A getstate method that saves the lights
		"""            
		odict = VisualizationModule.__getstate__(self)
		#print "Saving Slice =" ,self.parameters["Slice"]
		#print "Returning",odict
		odict["parameters"] = self.parameters
		return odict
		
	def __set_pure_state__(self, state):
		"""
		Set the state of the light
		"""        
		VisualizationModule.__set_pure_state__(self, state)
		self.parameters = state.parameters
		self.sendUpdateGUI()
				
	def setDataUnit(self, dataunit):
		"""
		Sets the dataunit this module uses for visualization
		"""
		if dataunit == None:
			return
		VisualizationModule.setDataUnit(self, dataunit)

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
		filename = self.parameters["FileName"]
		if not os.path.exists(filename):
			return

		self.reader.SetFileName(filename)
		self.reader.SetHBScale(1.0)
		self.reader.SetBScale(1.0)

		self.sphereSource.SetRadius(self.parameters['SphereRadius'])
		self.tubeFilter.SetRadius(self.parameters['TubeRadius'])
		
		self.glyph3D.SetInputConnection(self.reader.GetOutputPort())
		self.mapper.SetInputConnection(self.glyph3D.GetOutputPort())
		self.tubeFilter.SetInputConnection(self.reader.GetOutputPort())
		self.mapper2.SetInputConnection(self.tubeFilter.GetOutputPort())
		
		if not self.actorsInitialized:
			self.renderer.AddActor(self.tubeActor)
			self.renderer.AddActor(self.actor)
			self.actorsInitialized = True

		self.mapper.Update()
		VisualizationModule.updateRendering(self)
		self.parent.Render()

		
	def setProperties(self, ambient, diffuse, specular, specularpower):
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
		Set channel selection off
		"""
		return 0

class PDBConfigurationPanel(ModuleConfigurationPanel):

	def __init__(self, parent, visualizer, name = "PDB", **kws):
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
		self.contentSizer.Add(self.gui, (0, 0))

	def onApply(self, event):
		"""
		Apply the changes
		"""     
		self.module.updateRendering()
