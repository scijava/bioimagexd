# -*- coding: iso-8859-1 -*-

"""
 Unit: VisualizationModules
 Project: BioImageXD
 Created: 28.04.2005, KP
 Description:

 A module containing the various Rendering modules for the visualization

 Copyright (C) 2005	 BioImageXD Project
 See CREDITS.txt for details

 This program is free software; you can redistribute it and / or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program; if not, write to the Free Software
 Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111 - 1307	 USA
"""
__author__ = "BioImageXD Project"
__version__ = "$Revision: 1.9 $"
__date__ = "$Date: 2005 / 01 / 13 13: 42: 03 $"

import Logging
import lib.messenger
import GUI.Urmas.UrmasPersist
import lib.ProcessingFilter
import scripting

class VisualizationModule(lib.ProcessingFilter.ProcessingFilter):
	name = "VisualizationModule"
	"""
	Created: 28.04.2005, KP
	Description: A class representing a visualization module
	"""
	def __init__(self, parent, visualizer, **kws):
		"""
		Initialization
		"""
		self.processInputText = "Task output"
		self.name = kws["label"]

		self.moduleName = kws["moduleName"]
		self.numberOfInputs = (1, 1)
		self.timepoint = -1
		self.parent = parent
		self.shading = 0
		self.visualizer = visualizer
		self.wxrenwin = parent.wxrenwin
		self.renWin = self.wxrenwin.GetRenderWindow()
		self.renderer = self.parent.getRenderer()
		self.eventDesc = "Rendering"
		self.view = None
		self.setVTKState = GUI.Urmas.UrmasPersist.setVTKState
		self.getVTKState = GUI.Urmas.UrmasPersist.getVTKState
		

		self.inputs = []
		self.dataUnit = None
		self.inputIndex = 0
		self.data = None
		self.vtkObjects = []
		lib.ProcessingFilter.ProcessingFilter.__init__(self, changeCallback = self.parameterChanged)

	def set(self, parameter, value):
		"""
		Set the given parameter to given value
		"""
		lib.ProcessingFilter.ProcessingFilter.setParameter(self, parameter, value)
		# Send a message that will update the GUI
		lib.messenger.send(self, "set_%s" % parameter, value)

	def setParameter(self, parameter, value):
		"""
		Set a value for the parameter
		"""
		if self.initDone:
			method = "visualizer.getCurrentWindow().getModule('%s')" % self.name
			self.recordParameterChange(parameter, value, method)
		lib.ProcessingFilter.ProcessingFilter.setParameter(self, parameter, value)

	def parameterChanged(self, module):
		"""
		Callback for notifying when parameter ha changed
		"""
		pass

	def canSelectChannels(self):
		"""
		Should it be possible to select the channel
		"""
		return 1

	def setView(self, view):
		"""
		Set the view that is to be set for the render window before
					 first render.
		"""
		self.view = view

	def updateProgress(self, obj, event):
		"""
		Update the progress information
		"""
		progress = obj.GetProgress()
		txt = obj.GetProgressText()
		if not txt:
			txt = self.eventDesc
		lib.messenger.send(None, "update_progress", progress, txt)

	def getName(self):
		"""
		Return the name of this module
		"""
		return self.name

	def setDataUnit(self, dataunit):
		"""
		Sets the dataunit this module uses for visualization
		"""
		self.dataUnit = dataunit
		VisualizationModule.showTimepoint(self, self.visualizer.getTimepoint(), update = 0)

	def getDataUnit(self):
		"""
		Returns the dataunit this module uses for visualization
		"""
		return self.dataUnit

	def updateData(self):
		"""
		"OK Update the data that is displayed
		"""
		self.showTimepoint(self.timepoint)

	def showTimepoint(self, value, update = 1):
		"""
		Set the timepoint to be displayed
		"""
		self.timepoint = value
		if not self.dataUnit:
			return
		if self.visualizer.getProcessedMode():
			Logging.info("Will render processed data instead", kw = "rendering")
			self.data = self.dataUnit.doPreview(scripting.WHOLE_DATASET, 1, self.timepoint)
		else:
			Logging.info("Using timepoint data for tp", value, kw = "rendering")
			self.data = self.dataUnit.getTimepoint(value)

		# We set this for the new style modules that are based on the GUI builder
		self.inputs = [self.data]
		self.inputIndex = 0

		if update:
			self.updateRendering()

	def updateRendering(self, input = None):
		"""
		Update the Rendering of this module
		"""
		if self.view:
			self.wxrenwin.setView(self.view)
			self.view = None

	def disableRendering(self):
		"""
		Disable the Rendering of this module
		"""
		self.renderer.RemoveActor(self.actor)
		self.wxrenwin.Render()

	def enableRendering(self):
		"""
		Enable the Rendering of this module
		"""
		self.renderer.AddActor(self.actor)
		self.wxrenwin.Render()

	def setProperties(self, ambient, diffuse, specular, specularpower):
		"""
		Set the ambient, diffuse and specular lighting of this module
		"""
		property = self.actor.GetProperty()
		property.SetAmbient(ambient)
		property.SetDiffuse(diffuse)
		property.SetSpecular(specular)
		property.SetSpecularPower(specularpower)

	def setShading(self, shading):
		"""
		Set shading on / off
		"""
		self.shading = shading
		property = self.actor.GetProperty()
		if hasattr(property, "ShadeOn"):
			property.SetShade(shading)
		elif hasattr(property, "ShadingOn"):
			property.SetShading(shading)

	def __getstate__(self):
		"""
		A getstate method that saves the lights
		"""
		params = {}
		for key, val in self.parameters.items():
			if hasattr(val, "GetClassName") and "vtk" in val.GetClassName():
				params[key] = self.getVTKState(val)
			else:
				params[key] = val
		odict = {
			"timepoint": self.timepoint,
			"name": self.name,
			"moduleName": self.moduleName,
			"shading": self.shading,
			"parameters": params,
			"vtkobjects": self.vtkObjects
		}
		for vtkobj in self.vtkObjects:
			odict[vtkobj] = self.getVTKState(self.__dict__[vtkobj])

		if hasattr(self, "actor"):
			odict.update({"actorProperty": self.getVTKState(self.actor.GetProperty())})
		return odict

	def __set_pure_state__(self, state):
		"""
		Set the state of the light
		"""
		self.name = state.name
		self.moduleName = state.moduleName
		self.showTimepoint(state.timepoint)
		if hasattr(self, "actor"):
			self.setVTKState(self.actor.GetProperty(), state.actorProperty)
		self.setShading(state.shading)
