# -*- coding: iso-8859-1 -*-

"""
 Unit: VisualizeTrack
 Project: BioImageXD
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

import scripting
from GUI import GUIBuilder
import lib.messenger
import types
from Visualizer.VisualizationModules import VisualizationModule
from Visualizer.ModuleConfiguration import ModuleConfigurationPanel
import vtk
import wx
import os.path
import lib.Track
import Modules.DynamicLoader

def getClass():
	return VisualizeTrackModule

def getConfigPanel():
	return VisualizeTrackConfigurationPanel

def getName():
	return "Visualize motion tracks"

class VisualizeTrackModule(VisualizationModule):
	"""
	A module for clipping the dataset
	"""    
	def __init__(self, parent, visualizer, **kws):
		"""
		Initialization
		"""     
		VisualizationModule.__init__(self, parent, visualizer, **kws)   

		self.descs = {"TrackFile": "Tracks file", #"AllTracks": "Show all tracks", \
					"MinLength": "Min. length of track (# of timepoints)",
					"SphereRadius": "Sphere radius",
					"TubeRadius": "Tube radius"}
					#"SameStartingPoint":"Tracks start at same point"}
		
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
		visualize the tracks given as argument
		"""
		self.setTracks(tracks)
		self.updateRendering()

	def setTracks(self, tracks):
		"""
		Set tracks to visualize
		"""
		self.showTracks = tracks

	def setParameter(self, parameter, value):
		"""
		Set a value for the parameter
		"""
		#if parameter == "AllTracks":
		#	lib.messenger.send(None, "visualize_all_tracks", value)
		VisualizationModule.setParameter(self, parameter, value)
  
	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""
		return [["Read tracks", (("TrackFile", "Select track file to visualize", "*.csv"),)], ["Show tracks",()], ["Settings",("MinLength","SphereRadius","TubeRadius")]]

	def getParameterLevel(self, parameter):
		"""
		Return level of parameter
		"""
		if parameter in ["SphereRadius", "TubeRadius"]:
			return scripting.COLOR_EXPERIENCED
		return scripting.COLOR_BEGINNER
		
	def getDefaultValue(self, parameter):
		"""
		Return the default value of a parameter
		"""           
		if parameter == "TrackFile":
			return "tracks.csv"
		if parameter == "MinLength":
			return 3
		if parameter == "AllTracks":
			return False
		if parameter == "SphereRadius":
			return 2.5
		if parameter == "TubeRadius":
			return 1.0
		return False
		
	def getRange(self, parameter):
		"""
		If a parameter has a certain range of valid values, the values can be queried with this function
		"""
		if parameter == "MinLength":
			return 1, 1000
		return 1, 1
		
	def getType(self, parameter):
		"""
		Return the type of the parameter
		"""
		if parameter == "TrackFile":
			return GUIBuilder.FILENAME
		if parameter == "MinLength":
			return GUIBuilder.SPINCTRL
		if parameter in ["AllTracks","SameStartingPoint"]:
			return types.BooleanType
		if parameter in ["SphereRadius","TubeRadius"]:
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
		VisualizationModule.setDataUnit(self, dataunit)

	def showTimepoint(self, value):
		"""
		Set the timepoint to be displayed
		"""          
		self.renew = 1
		VisualizationModule.showTimepoint(self, value)

	def getPoints(self, tracks):
		"""
		adapt the track objects to straightforward point lists
		"""
		ret = []
		xc, yc, zc = self.data.GetSpacing()
		for track in tracks:
			mintp, maxtp = track.getTimeRange() 
			currtrack = []
			for t in range(mintp, maxtp + 1):
				val, (x, y, z) = track.getObjectAtTime(t)
				if x >= 0 and y >= 0 and z >= 0:
					currtrack.append((t, (x * xc, y * yc, z * zc)))
				else:
					break
			ret.append(currtrack)
		return ret
		
	def updateRendering(self):
		"""
		Update the Rendering of this module
		"""
		for actor in self.actors:
			self.renderer.RemoveActor(actor)
		self.actors = []
		if self.showTracks:
			edges = vtk.vtkCellArray()
			inputUnit = self.getInputDataUnit(1)
			timepoint = scripting.visualizer.getTimepoint()
			timepoints = scripting.visualizer.getNumberOfTimepoints()

			tubeRadius = self.parameters["TubeRadius"]
			sphereRadius = self.parameters["SphereRadius"]

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
			
			#dataw, datay, dataz = inputUnit.getDimensions()
			for track in tracks:
				#dx, dy, dz = 0,0,0
				#if self.parameters["SameStartingPoint"]:
				#	dx = -track[0][0]
				#	dy = -track[0][1]
				#	dz = -track[0][2]
				#	dx+=dataw/2
				#	dy+=datay/2
				#	dz+=dataz/2

				for i, (t,(x, y, z)) in enumerate(track[:-1]):
				#	x+=dx
				#	y+=dy
				#	z+=dz
					t2, (x2,y2,z2) = track[i + 1]
				#	x2+=dx
				#	y2+=dy
				#	z2+=dz

					if x != x2 or y != y2 or z != z2:
						linesource = vtk.vtkLineSource()
						linesource.SetPoint1(x, y, z)
						linesource.SetPoint2(x2, y2, z2)
						tubeFilter = vtk.vtkTubeFilter()
						tubeFilter.SetRadius(tubeRadius)
						tubeFilter.SetNumberOfSides(10)
						tubeFilter.SetInput(linesource.GetOutput())
						appendLines.AddInput(tubeFilter.GetOutput())
					
					sph = vtk.vtkSphereSource()
					sph.SetPhiResolution(20)
					sph.SetThetaResolution(20)
					sph.SetCenter(x, y, z)

					sph.SetRadius(sphereRadius)
					if t == timepoint:
						appendCurrent.AddInput(sph.GetOutput())
					elif i != 0:
						appendSpheres.AddInput(sph.GetOutput())

				if timepoint != track[0][0]:
					sph = vtk.vtkSphereSource()
					sph.SetPhiResolution(20)
					sph.SetThetaResolution(20)
					sph.SetCenter(track[0][1])
					sph.SetRadius(sphereRadius)
					appendFirst.AddInput(sph.GetOutput())

				if timepoint != track[-1][0]:
					sph = vtk.vtkSphereSource()
					sph.SetPhiResolution(20)
					sph.SetThetaResolution(20)
					sph.SetCenter(track[-1][1])
					sph.SetRadius(sphereRadius)         
					appendLast.AddInput(sph.GetOutput())
				else:
					sph = vtk.vtkSphereSource()
					sph.SetPhiResolution(20)
					sph.SetThetaResolution(20)
					sph.SetCenter(track[-1][1])
					sph.SetRadius(sphereRadius)         
					appendCurrent.AddInput(sph.GetOutput())

			self.currentMapper.SetInput(appendCurrent.GetOutput())
			self.sphereMapper.SetInput(appendSpheres.GetOutput())
			self.lineMapper.SetInput(appendLines.GetOutput())
			self.firstMapper.SetInput(appendFirst.GetOutput())
			self.lastMapper.SetInput(appendLast.GetOutput())

			#self.mapper.SetInput(append.GetOutput())
			if appendCurrent.GetNumberOfInputConnections(0) > 0:
				self.currentMapper.Update()
				self.actors.append(currentActor)
			if appendLines.GetNumberOfInputConnections(0) > 0:
				self.lineMapper.Update()
				self.actors.append(lineactor)
			if appendSpheres.GetNumberOfInputConnections(0) > 0:
				self.sphereMapper.Update()
				self.actors.append(spheresActor)
			if appendFirst.GetNumberOfInputConnections(0) > 0:
				self.firstMapper.Update()
				self.actors.append(firstActor)
			if appendLast.GetNumberOfInputConnections(0) > 0:
				self.lastMapper.Update()
				self.actors.append(lastActor)
			
			for actor in self.actors:
				self.renderer.AddActor(actor)
			
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

	def disableRendering(self):
		"""
		Disable the rendering of this module
		"""
		for actor in self.actors:
			self.renderer.RemoveActor(actor)
		self.actors = []
		self.wxrenwin.Render()
		

class VisualizeTrackConfigurationPanel(ModuleConfigurationPanel):

	def __init__(self, parent, visualizer, name = "VisualizeTrack", **kws):
		"""
		Initialization
		"""
		pluginLoader = Modules.DynamicLoader.getPluginLoader()
		createTrackMod = pluginLoader.getPluginModule("Filters", "CreateTracksFilter")
		self.trackingGUI = createTrackMod.getUserInterfaceModule()
		ModuleConfigurationPanel.__init__(self, parent, visualizer, name, **kws)
		lib.messenger.connect(None, "set_shown_tracks", self.updateSelectedTracks)
		lib.messenger.connect(None, "visualize_all_tracks", self.visualizeAllTracks)
	
	def initializeGUI(self):
		"""
		Initialization
		"""
		if not hasattr(self,"gui"):
			return

		box = wx.BoxSizer(wx.HORIZONTAL)
		self.readButton = wx.Button(self.gui, -1, "Read tracks")
		box.Add(self.readButton)
		self.readButton.Bind(wx.EVT_BUTTON, self.onReadTracks)

		# Terrible hack!!!
		sizer = self.gui.sizer.FindItemAtPosition((0,0)).GetSizer().GetItem(0).GetSizer().FindItemAtPosition((1,0)).GetSizer().GetItem(0).GetSizer()
		sizer.Add(box, (1,0))

		self.trackGrid = self.trackingGUI.TrackTableGrid(self.gui, self.module.dataUnit, self, canEnable = 1)
		gridSizer = wx.BoxSizer(wx.HORIZONTAL)
		gridSizer.Add(self.trackGrid, 1)

		self.selectAllBtn = wx.Button(self.gui, -1, "Select all")
		self.selectAllBtn.Bind(wx.EVT_BUTTON, self.onSelectAll)
		self.deselectAllBtn = wx.Button(self.gui, -1, "Deselect all")
		self.deselectAllBtn.Bind(wx.EVT_BUTTON, self.onDeselectAll)
		btnBox = wx.BoxSizer(wx.HORIZONTAL)
		btnBox.Add(self.selectAllBtn)
		btnBox.Add(self.deselectAllBtn)
		
		# Terrible hack!!!
		sizer = self.gui.sizer.FindItemAtPosition((0,0)).GetSizer().GetItem(0).GetSizer().FindItemAtPosition((2,0)).GetSizer().GetItem(0).GetSizer()
		sizer.Add(btnBox, (0,0))
		sizer.Add(gridSizer, (1,0))
		
	def setModule(self, module):
		"""
		Set the module to be configured
		"""
		ModuleConfigurationPanel.setModule(self, module)
		self.module = module
		self.gui = GUIBuilder.GUIBuilder(self, self.module)
		self.module.sendUpdateGUI()
		self.contentSizer.Add(self.gui, (0, 0))
		self.initializeGUI()
		#self.module.sendUpdateGUI()

	def onApply(self, event):
		"""
		Apply the changes
		"""     
		self.module.updateRendering()

	def onReadTracks(self, evt):
		"""
		Read tracks
		"""
		filename = self.module.parameters["TrackFile"]
		if not os.path.exists(filename):
			return

		self.trackReader = lib.Track.TrackReader()
		self.trackReader.readFromFile(filename)
		self.tracks = self.trackReader.getTracks(self.module.parameters["MinLength"])
		n = len(self.tracks)

		table = self.trackGrid.getTable()
		table.Clear()
		table.AppendRows(n)
		for i, track in enumerate(self.tracks):
			mintp, maxtp = track.getTimeRange()
			for tp in range(mintp, maxtp + 1):
				val, pos = track.getObjectAtTime(tp)
				table.SetValue(i, tp + 1, pos, override = 1)
		self.trackGrid.SetTable(table)
		self.trackGrid.ForceRefresh()

	def onSelectAll(self, evt):
		"""
		View all tracks
		"""
		self.visualizeAllTracks(None, evt, 1)

	def onDeselectAll(self, evt):
		"""
		View no tracks
		"""
		self.visualizeAllTracks(None, evt, 0)
		
	def updateSelectedTracks(self, obj, evt, tracks):
		"""
		Show selected tracks
		"""
		showTracks = []
		for i in tracks:
			showTracks.append(self.tracks[i])
		self.module.setTracks(showTracks)

	def visualizeAllTracks(self, obj, evt, value):
		"""
		Handle visualize all tracks selection
		"""
		if value:
			for i in range(0,self.trackGrid.GetNumberRows()):
				self.trackGrid.table.setEnabled(i,1)
		else:
			for i in range(0,self.trackGrid.GetNumberRows()):
				self.trackGrid.table.setEnabled(i,0)

		self.trackGrid.ForceRefresh()
		if value:
			lib.messenger.send(None, "visualize_tracks", self.tracks)
		else:
			lib.messenger.send(None, "visualize_tracks", [])
			
