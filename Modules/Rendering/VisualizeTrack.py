# -*- coding: iso-8859-1 -*-

"""
 Unit: VisualizeTrack
 Project: BioImageXD
 Created: 29.05.2006, KP
 Description:

 A VisualizeTrack rendering module
		   
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

import scripting as bxd
from GUI import GUIBuilder
import lib.messenger
import types
from Visualizer.VisualizationModules import VisualizationModule
from Visualizer.ModuleConfiguration import ModuleConfigurationPanel
import vtk

def getClass():
	return VisualizeTrackModule

def getConfigPanel():
	return VisualizeTrackConfigurationPanel

def getName():
	return "Visualize tracks"

class VisualizeTrackModule(VisualizationModule):
	"""
	Created: 24.06.2005, KP
	Description: A module for clipping the dataset
	"""    
	def __init__(self, parent, visualizer, **kws):
		"""
		Created: 03.05.2005, KP
		Description: Initialization
		"""     
		VisualizationModule.__init__(self, parent, visualizer, **kws)   

		self.descs = {"TrackFile": "Select the track file", "AllTracks": "Show all tracks", \
					"Track": "Select the track to visualize", "MinLength": "Minimum length of track", \
					"ShowObject": "Show object using surface rendering"}
		
		self.showTracks = []
			
		self.lineMapper = vtk.vtkPolyDataMapper()
		self.sphereMapper = vtk.vtkPolyDataMapper()
		self.firstMapper = vtk.vtkPolyDataMapper()
		self.lastMapper = vtk.vtkPolyDataMapper()
		self.currentMapper = vtk.vtkPolyDataMapper()
		self.actors = []
		self.renderer = self.parent.getRenderer()

        #iactor = self.wxrenwin.GetRenderWindow().GetInteractor()
		lib.messenger.connect(None, "visualize_tracks", self.onVisualizeTracks)
		
	def onVisualizeTracks(self, obj, evt, tracks):
		"""
		Created: 15.04.2007, KP
		Description: visualize the tracks given as argument
		"""
		self.showTracks = tracks
		print "Got tracks=", tracks
		self.updateRendering()

	def setParameter(self, parameter, value):
		"""
		Created: 13.04.2006, KP
		Description: Set a value for the parameter
		"""    
		VisualizationModule.setParameter(self, parameter, value)
  
		
	def getParameters(self):
		"""
		Created: 31.05.2006, KP
		Description: Return the list of parameters needed for configuring this GUI
		"""            
		return [  ]
		
	def getDefaultValue(self, parameter):
		"""
		Created: 13.04.2006, KP
		Description: Return the default value of a parameter
		"""           
		if parameter == "TrackFile":
			return "tracks.csv"
		if parameter == "Track":
			return 0
		if parameter == "MinLength":
			return 3
		if parameter == "AllTracks":
			return False
		if parameter == "ShowObject":
			return False
			
	def getRange(self, parameter):
		"""
		Created: 31.05.2006, KP
		Description: If a parameter has a certain range of valid values, the values can be queried with this function
		"""     
		if parameter == "Track":
			#TODO: self.track does not exist
			if self.track:
				minlength = self.parameters["MinLength"]
				return 0, self.track.getNumberOfTracks(minlength)
				
			else:
				return 0, 5
		elif parameter == "MinLength":
			if self.track:
				return 1, self.track.getMaximumTrackLength()
			else:
				return 1, 100
		return 1, 1
		
	def getType(self, parameter):
		"""
		Created: 13.04.2006, KP
		Description: Return the type of the parameter
		"""    

		if parameter == "TrackFile":
			return GUIBuilder.FILENAME
		if parameter == "Track":
			return GUIBuilder.SLICE
		if parameter == "MinLength":
			return GUIBuilder.SLICE
		if parameter == "AllTracks":
			return types.BooleanType

	def __getstate__(self):
		"""
		Created: 02.08.2005, KP
		Description: A getstate method that saves the lights
		"""            
		odict = VisualizationModule.__getstate__(self)
		#print "Saving Slice =" ,self.parameters["Slice"]
		#print "Returning",odict
		odict["parameters"] = self.parameters
		return odict
		
	def __set_pure_state__(self, state):
		"""
		Created: 02.08.2005, KP
		Description: Set the state of the light
		"""        
		VisualizationModule.__set_pure_state__(self, state)
		self.parameters = state.parameters
		self.sendUpdateGUI()
				
	def setDataUnit(self, dataunit):
		"""
		Created: 28.04.2005, KP
		Description: Sets the dataunit this module uses for visualization
		"""       
		VisualizationModule.setDataUnit(self, dataunit)

	def showTimepoint(self, value):
		"""
		Created: 28.04.2005, KP
		Description: Set the timepoint to be displayed
		"""          
		self.renew = 1
		VisualizationModule.showTimepoint(self, value)

	def getPoints(self, tracks):
		"""
		Created: 15.04.2007, KP
		Description: adapt the track objects to straightforward point lists
		"""
		ret = []
		xc, yc, zc = self.data.GetSpacing()
		for track in tracks:
			mintp, maxtp = track.getTimeRange() 
			currtrack = []
			for t in range(mintp, maxtp + 1):
				val, (x, y, z) = track.getObjectAtTime(t)
				if x >= 0 and y >= 0 and z >= 0:
					currtrack.append((x * xc, y * yc, z * zc))
				else:
					break
			ret.append(currtrack)
		return ret
		
	def updateRendering(self):
		"""
		Created: 03.05.2005, KP
		Description: Update the Rendering of this module
		"""             
		#data = self.data
		#self.mapper.SetInput(data)
		for actor in self.actors:
			self.renderer.RemoveActor(actor)
		if self.showTracks:
			edges = vtk.vtkCellArray()

			tracks = self.getPoints(self.showTracks)
			appendLines  = vtk.vtkAppendPolyData()
			appendSpheres = vtk.vtkAppendPolyData()
			appendFirst = vtk.vtkAppendPolyData()
			appendLast = vtk.vtkAppendPolyData()
			appendCurrent = vtk.vtkAppendPolyData()
			
			lineactor = vtk.vtkActor()
			lineactor.SetMapper(self.lineMapper)
			lineactor.GetProperty().SetDiffuseColor(1, 1, 1)
			spheresActor = vtk.vtkActor()
			spheresActor.SetMapper(self.sphereMapper)
			spheresActor.GetProperty().SetDiffuseColor(0, 1, 1)
			
			firstActor = vtk.vtkActor()
			firstActor.SetMapper(self.firstMapper)
			firstActor.GetProperty().SetDiffuseColor(0, 1, 0)
			
			lastActor = vtk.vtkActor()
			lastActor.SetMapper(self.lastMapper)
			lastActor.GetProperty().SetDiffuseColor(1, 0, 0)
			
			currentActor = vtk.vtkActor()
			currentActor.SetMapper(self.currentMapper)
			currentActor.GetProperty().SetDiffuseColor(0, 0, 1)
			
			self.actors.append(lineactor)
			self.actors.append(spheresActor)
			self.actors.append(firstActor)
			self.actors.append(lastActor)
			self.actors.append(currentActor)
			for actor in self.actors:
				self.renderer.AddActor(actor)

			for track in tracks:
				for i, (x, y, z) in enumerate(track[:-1]):
				
					linesource = vtk.vtkLineSource()
					linesource.SetPoint1(x, y, z)
					linesource.SetPoint2(*track[i + 1])
					tubeFilter = vtk.vtkTubeFilter()
					tubeFilter.SetRadius(1.5)
					tubeFilter.SetNumberOfSides(10)
			
					tubeFilter.SetInput(linesource.GetOutput())
					appendLines.AddInput(tubeFilter.GetOutput())
					
					
					sph = vtk.vtkSphereSource()
					sph.SetPhiResolution(20)
					sph.SetThetaResolution(20)
					sph.SetCenter(x, y, z)

					sph.SetRadius(3)            

					if i == 0:
						appendFirst.AddInput(sph.GetOutput())
					elif i == bxd.visualizer.getTimepoint():
						appendCurrent.AddInput(sph.GetOutput())
					else:
						appendSpheres.AddInput(sph.GetOutput())
										
				sph = vtk.vtkSphereSource()
				sph.SetPhiResolution(20)
				sph.SetThetaResolution(20)
				sph.SetCenter(*track[-1])
				sph.SetRadius(3)         
				appendLast.AddInput(sph.GetOutput())
				#self.lastMapper.SetInput(sph.getOutput())                
				
			
			self.currentMapper.SetInput(appendCurrent.GetOutput())
			self.sphereMapper.SetInput(appendSpheres.GetOutput())
			self.lineMapper.SetInput(appendLines.GetOutput())
			self.firstMapper.SetInput(appendFirst.GetOutput())
			self.lastMapper.SetInput(appendLast.GetOutput())

			#self.mapper.SetInput(append.GetOutput())
	
			self.currentMapper.Update()
			self.lineMapper.Update()
			self.sphereMapper.Update()
			self.firstMapper.Update()
			self.lastMapper.Update()
			VisualizationModule.updateRendering(self)
			self.parent.Render()    

		
	def setProperties(self, ambient, diffuse, specular, specularpower):
		"""
		Created: 16.05.2005, KP
		Description: Set the ambient, diffuse and specular lighting of this module
		"""         
		pass
	def setShading(self, shading):
		"""
		Created: 16.05.2005, KP
		Description: Set shading on / off
		"""          
		pass

class VisualizeTrackConfigurationPanel(ModuleConfigurationPanel):

	def __init__(self, parent, visualizer, name = "VisualizeTrack", **kws):
		"""
		Created: 29.05.2006, KP
		Description: Initialization
		"""     
		ModuleConfigurationPanel.__init__(self, parent, visualizer, name, **kws)
	
	def initializeGUI(self):
		"""
		Created: 28.04.2005, KP
		Description: Initialization
		"""          
		pass
		
	def setModule(self, module):
		"""
		Created: 28.04.2005, KP
		Description: Set the module to be configured
		"""  
		ModuleConfigurationPanel.setModule(self, module)
		self.module = module
		self.gui = GUIBuilder.GUIBuilder(self, self.module)
		self.module.sendUpdateGUI()
		self.contentSizer.Add(self.gui, (0, 0))

	def onApply(self, event):
		"""
		Created: 28.04.2005, KP
		Description: Apply the changes
		"""     
		self.module.updateRendering()
