# -*- coding: iso-8859-1 -*-

"""
 Unit: Orthogonal
 Project: BioImageXD
 Description:

 A module containing the orthogonal slices module for the visualization
		   
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

import wx
import vtk
import lib.messenger
import Logging
from Visualizer.VisualizationModules import VisualizationModule
from Visualizer.ModuleConfiguration import ModuleConfigurationPanel

def getClass():
	return OrthogonalPlaneModule

def getConfigPanel():
	return OrthogonalPlaneConfigurationPanel

def getName():
	return "Orthogonal slices"

def getQuickKeyCombo():
	return "Shift-Ctrl-O"

class OrthogonalPlaneModule(VisualizationModule):
	"""
	A module for slicing the dataset
	"""    
	def __init__(self, parent, visualizer, **kws):
		"""
		Initialization
		"""     
		self.x, self.y, self.z = -1, -1, -1
		VisualizationModule.__init__(self, parent, visualizer, **kws)
		self.on = 0
		self.renew = 1
		self.mapper = vtk.vtkPolyDataMapper()
		self.eventDesc = "Rendering orthogonal slices"
		self.outline = vtk.vtkOutlineFilter()
		self.outlineMapper = vtk.vtkPolyDataMapper()
		self.outlineActor = vtk.vtkActor()
		self.outlineActor.SetMapper(self.outlineMapper)
		
		self.picker = vtk.vtkCellPicker()
		self.picker.SetTolerance(0.005)
		
		self.planeWidgetX = vtk.vtkImagePlaneWidget()
		self.planeWidgetX.DisplayTextOn()
		self.planeWidgetX.SetPicker(self.picker)
		self.planeWidgetX.SetKeyPressActivationValue("x")
		#self.planeWidgetX.UserControlledLookupTableOn()
		self.prop1 = self.planeWidgetX.GetPlaneProperty()
		#self.prop1.SetColor(1, 0, 0)
		self.planeWidgetX.SetResliceInterpolateToCubic()

		self.planeWidgetY = vtk.vtkImagePlaneWidget()
		self.planeWidgetY.DisplayTextOn()
		self.planeWidgetY.SetPicker(self.picker)
		self.planeWidgetY.SetKeyPressActivationValue("y")
		self.prop2 = self.planeWidgetY.GetPlaneProperty()
		self.planeWidgetY.SetResliceInterpolateToCubic()
		#self.planeWidgetY.UserControlledLookupTableOn()
		#self.prop2.SetColor(1, 1, 0)


		# for the z-slice, turn off texture interpolation:
		# interpolation is now nearest neighbour, to demonstrate
		# cross-hair cursor snapping to pixel centers
		self.planeWidgetZ = vtk.vtkImagePlaneWidget()
		self.planeWidgetZ.DisplayTextOn()
		self.planeWidgetZ.SetPicker(self.picker)
		self.planeWidgetZ.SetKeyPressActivationValue("z")
		self.prop3 = self.planeWidgetZ.GetPlaneProperty()
		#self.prop3.SetColor(1, 0, 1)
		#self.planeWidgetZ.UserControlledLookupTableOn()
		self.planeWidgetZ.SetResliceInterpolateToCubic()
		self.renderer = self.parent.getRenderer()
		self.renderer.AddActor(self.outlineActor)
		self.useOutline = 1
		
		iactor = self.wxrenwin.GetRenderWindow().GetInteractor()
		self.planeWidgetX.SetInteractor(iactor)
		self.planeWidgetY.SetInteractor(iactor)
		self.planeWidgetZ.SetInteractor(iactor)
		
		lib.messenger.connect(None, "zslice_changed", self.setZ)
		self.filterDesc = "View orthogonal slices"
		
	   
	def __getstate__(self):
		"""
		A getstate method that saves the lights
		"""            
		odict = VisualizationModule.__getstate__(self)
		odict.update({"planeWidgetX":self.getVTKState(self.planeWidgetX)})
		odict.update({"planeWidgetY":self.getVTKState(self.planeWidgetY)})
		odict.update({"planeWidgetZ":self.getVTKState(self.planeWidgetZ)})
		odict.update({"prop1":self.getVTKState(self.prop1)})
		odict.update({"prop2":self.getVTKState(self.prop2)})
		odict.update({"prop3":self.getVTKState(self.prop3)})        
		odict.update({"renderer":self.getVTKState(self.renderer)})
		odict.update({"camera":self.getVTKState(self.renderer.GetActiveCamera())})
		odict.update({"x":self.x})
		odict.update({"z":self.z})
		odict.update({"y":self.y})
		return odict
		
	def __set_pure_state__(self, state):
		"""
		Set the state of the light
		"""
		self.setVTKState(self.planeWidgetX, state.planeWidgetX)
		self.setVTKState(self.planeWidgetX, state.planeWidgetY)
		self.setVTKState(self.planeWidgetX, state.planeWidgetZ)
		
		self.setVTKState(self.prop1, state.prop1)
		self.setVTKState(self.prop2, state.prop2)        
		self.setVTKState(self.prop3, state.prop3)       
		
		self.setVTKState(self.renderer, state.renderer)
		self.setVTKState(self.renderer.GetActiveCamera(), state.camera)
		self.x, self.y, self.z = state.x, state.y, state.z
		VisualizationModule.__set_pure_state__(self, state)
		 
		
	def setDataUnit(self, dataunit):
		"""
		Sets the dataunit this module uses for visualization
		"""       
		VisualizationModule.setDataUnit(self, dataunit)
		if self.dataUnit.isProcessed():
			data = self.dataUnit.getSourceDataUnits()[0].getTimepoint(0)
		else:
			data = self.dataUnit.getTimepoint(0)
		self.origin = data.GetOrigin()
		self.spacing = data.GetSpacing()
		self.extent = data.GetWholeExtent()

		x = self.extent[1] / 2
		y = self.extent[3] / 2
		z = self.extent[5] / 2
		self.setDisplaySlice(x, y, z)

		ctf = self.dataUnit.getColorTransferFunction()
		self.planeWidgetX.GetColorMap().SetLookupTable(ctf)
		self.planeWidgetX.maxDim = x
		
		self.planeWidgetY.GetColorMap().SetLookupTable(ctf)
		self.planeWidgetY.maxDim = y
		
		self.planeWidgetZ.GetColorMap().SetLookupTable(ctf)
		self.planeWidgetZ.maxDim = z
	
	def setZ(self, obj, evt, arg):
		"""
		Set the slices to display
		"""         
		self.z = arg
		self.updateRendering()
		
	
	def setDisplaySlice(self, x, y, z):
		"""
		Set the slices to display
		"""           
		self.x, self.y, self.z = x, y, z
		#self.parent.getRenderer().ResetCameraClippingRange()
		#self.wxrenwin.GetRenderWindow().Render()
		Logging.info("Showing slices ", self.x, self.y, self.z, kw = "rendering")

	def showTimepoint(self, value):
		"""
		Set the timepoint to be displayed
		"""          
		self.renew = 1
		VisualizationModule.showTimepoint(self, value)
		
	def alignCamera(self, widget):
		"""
		Align the camera so that it shows a given widget
		"""          
		xMin, xMax, yMin, yMax, zMin, zMax = self.extent
		sx, sy, sz = self.spacing
		ox, oy, oz = self.origin
		slice_number = widget.maxDim / 2
		cx = ox + (0.5 * (xMax - xMin)) * sx
		cy = oy + (0.5 * (yMax - yMin)) * sy
		cz = oy + (0.5 * (zMax - zMin)) * sz
		vx, vy, vz = 0, 0, 0
		nx, ny, nz = 0, 0, 0
		iaxis = widget.GetPlaneOrientation()
		if iaxis == 0:
			vz = 1
			nx = ox + xMax * sx
			cx = ox + slice_number * sx
		  
		elif iaxis == 1:
			vz = 1
			ny = oy + yMax * sy
			cy = oy + slice_number * sy
		  
		else:
			vy = 1
			nz = oz + zMax * sz
			cz = oz + slice_number * sz
		
		px = cx + nx * 2
		py = cy + ny * 2
		d = float(xMax) / zMax
		if d < 1:
			d = 1
		pz = cz + nz * (3.0 + d)
	
		camera = self.renderer.GetActiveCamera()
		camera.SetViewUp(vx, vy, vz)
		camera.SetFocalPoint(cx, cy, cz)
		camera.SetPosition(px, py, pz)
			
		camera.OrthogonalizeViewUp()
		self.renderer.ResetCameraClippingRange()
		self.wxrenwin.Render()

		
	def updateRendering(self):
		"""
		Update the Rendering of this module
		"""
		if self.useOutline:
			self.outline.SetInput(self.data)
			self.outlineMapper.SetInput(self.outline.GetOutput())
			self.outlineMapper.Update()

		if self.renew:
			self.planeWidgetX.SetInput(self.data)
			self.planeWidgetZ.SetInput(self.data)
			self.planeWidgetY.SetInput(self.data)
			self.renew = 0
			for i in ["X", "Y", "Z"]:
				eval("self.planeWidget%s.SetPlaneOrientationTo%sAxes()" % (i, i))            
		self.planeWidgetX.SetSliceIndex(self.x)
		self.planeWidgetY.SetSliceIndex(self.y)
		self.planeWidgetZ.SetSliceIndex(self.z)
		
		if not self.on:
			self.planeWidgetX.On()
			self.planeWidgetY.On()
			self.planeWidgetZ.On()
			self.on = 1
		
		#self.mapper.Update()
		VisualizationModule.updateRendering(self, input)
		self.parent.Render()    

	def disableRendering(self):
		"""
		Disable the Rendering of this module
		"""          
		if self.useOutline:
			self.renderer.RemoveActor(self.outlineActor)
		self.planeWidgetX.Off()
		self.planeWidgetY.Off()
		self.planeWidgetZ.Off()
		self.wxrenwin.Render()
		
	def enableRendering(self):
		"""
		Enable the Rendering of this module
		"""
		if self.useOutline:
			self.renderer.AddActor(self.outlineActor)
		self.planeWidgetX.On()
		self.planeWidgetY.On()
		self.planeWidgetZ.On()
		self.wxrenwin.Render()
		
	def setProperties(self, ambient, diffuse, specular, specularpower, viewangle):
		"""
		Set the ambient, diffuse and specular lighting of this module
		"""         
		for widget in [self.planeWidgetX, self.planeWidgetY, self.planeWidgetZ]:
			property = widget.GetTexturePlaneProperty()
			property.SetAmbient(ambient)
			property.SetDiffuse(diffuse)
			property.SetSpecular(specular)
			property.SetSpecularPower(specularpower)
			self.renderer.GetActiveCamera().SetViewAngle(viewangle)
		
	def setShading(self, shading):
		"""
		Set shading on / off
		"""          
		for widget in [self.planeWidgetX, self.planeWidgetY, self.planeWidgetZ]:
			property = widget.GetTextureProperty()
			if shading:
			    property.ShadingOn()
			else:
			    property.ShadingOff()
	
	def setUseOutline(self, outline):
		"""
		Set outline on / off
		"""
		if self.useOutline == outline:
			return
			
		self.useOutline = outline
		if self.useOutline:
			self.renderer.AddActor(self.outlineActor)
		else:
			self.renderer.RemoveActor(self.outlineActor)
			

class OrthogonalPlaneConfigurationPanel(ModuleConfigurationPanel):
	def __init__(self, parent, visualizer, name = "Orthogonal Slices", **kws):
		"""
		Initialization
		"""     
		ModuleConfigurationPanel.__init__(self, parent, visualizer, name, **kws)
	
	def initializeGUI(self):
		"""
		Initialization
		"""
		sliceBox = wx.StaticBox(self, -1, "Slices")
		sliceBoxSizer = wx.StaticBoxSizer(sliceBox, wx.VERTICAL)		
		self.contentSizer.Add(sliceBoxSizer, (0, 0))
		sliceSizer = wx.GridBagSizer()
		sliceBoxSizer.Add(sliceSizer)

		self.xLbl = wx.StaticText(self, -1, "X Slice:")
		self.xSlider = wx.Slider(self, value = 0, minValue = 0, maxValue = 10,
		style = wx.HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS, size = (250, -1))
		
		self.yLbl = wx.StaticText(self, -1, "Y Slice:")
		self.ySlider = wx.Slider(self, value = 0, minValue = 0, maxValue = 10,
		style = wx.HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS, size = (250, -1))
		
		self.zLbl = wx.StaticText(self, -1, "Z Slice:")
		self.zSlider = wx.Slider(self, value = 0, minValue = 0, maxValue = 10,
		style = wx.HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS, size = (250, -1))
		
		sliceSizer.Add(self.xLbl, (0, 0), flag = wx.EXPAND | wx.LEFT | wx.RIGHT)
		sliceSizer.Add(self.xSlider, (1, 0))

		sliceSizer.Add(self.yLbl, (2, 0), flag = wx.EXPAND | wx.LEFT | wx.RIGHT)
		sliceSizer.Add(self.ySlider, (3, 0))

		sliceSizer.Add(self.zLbl, (4, 0), flag = wx.EXPAND | wx.LEFT | wx.RIGHT)
		sliceSizer.Add(self.zSlider, (5, 0))
			
		box = wx.BoxSizer(wx.HORIZONTAL)
		self.ID_X = wx.NewId()
		self.ID_Y = wx.NewId()
		self.ID_Z = wx.NewId()
		self.xBtn = wx.Button(self, self.ID_X, "X")
		self.yBtn = wx.Button(self, self.ID_Y, "Y")
		self.zBtn = wx.Button(self, self.ID_Z, "Z")
		self.xBtn.Bind(wx.EVT_BUTTON, self.alignCamera)
		self.yBtn.Bind(wx.EVT_BUTTON, self.alignCamera)
		self.zBtn.Bind(wx.EVT_BUTTON, self.alignCamera)
		
		box.Add(self.xBtn, 1)
		box.Add(self.yBtn, 1)
		box.Add(self.zBtn, 1)
		sliceSizer.Add(box, (6, 0))
		
		self.xSlider.Bind(wx.EVT_SCROLL, self.onUpdateSlice)
		self.ySlider.Bind(wx.EVT_SCROLL, self.onUpdateSlice)
		self.zSlider.Bind(wx.EVT_SCROLL, self.onUpdateSlice)
		
		#self.shadingBtn = wx.CheckBox(self, -1, "Use shading")
		#self.shadingBtn.SetValue(0)
		#self.shading = 0
		#self.shadingBtn.Bind(wx.EVT_CHECKBOX, self.onCheckShading)

		self.borderBtn = wx.CheckBox(self, -1, "Show slice borders")
		self.borderBtn.SetValue(1)
		self.border = 1
		self.borderBtn.Bind(wx.EVT_CHECKBOX, self.onCheckBorder)
		self.outlineBtn = wx.CheckBox(self, -1, "Show outline border")
		self.outlineBtn.SetValue(1)
		self.outline = 1
		self.outlineBtn.Bind(wx.EVT_CHECKBOX, self.onCheckOutline)
		
		#self.contentSizer.Add(self.shadingBtn, (7, 0))
		borderBox = wx.StaticBox(self, -1, "Show borders")
		borderBoxSizer = wx.StaticBoxSizer(borderBox, wx.VERTICAL)		
		self.contentSizer.Add(borderBoxSizer, (1, 0))
		borderSizer = wx.GridBagSizer()
		borderBoxSizer.Add(borderSizer)
		borderSizer.Add(self.borderBtn, (0,0))
		borderSizer.Add(self.outlineBtn, (1,0))
		
	def onCheckShading(self, event):
		"""
		Toggle use of shading
		"""  
		self.shading = event.IsChecked()
		self.module.setShading(self.shading)

	def onCheckBorder(self, event):
		"""
		Toggle use of borders
		"""  
		self.border = event.IsChecked()
		opacity = 0.0
		if self.border:
			opacity = 1.0

		for d in ["X","Y","Z"]:
			prop = eval("self.module.planeWidget%s.GetPlaneProperty()"%d)
			prop.SetOpacity(opacity)

	def onCheckOutline(self, event):
		"""
		Toggle use of outline
		"""  
		self.outline = event.IsChecked()
		self.module.setUseOutline(self.outline)
		
	def alignCamera(self, event):
		"""
		Align the camera to face a certain plane
		"""  
		if event.GetId() == self.ID_X:
			Logging.info("aliging to X", kw = "rendering")
			self.module.alignCamera(self.module.planeWidgetX)
		elif event.GetId() == self.ID_Y:
			Logging.info("aliging to Y", kw = "rendering")
			self.module.alignCamera(self.module.planeWidgetY)
		else:
			Logging.info("aliging to Z", kw = "rendering")
			self.module.alignCamera(self.module.planeWidgetZ)
		
	def setModule(self, module):
		"""
		Set the module to be configured
		"""  
		ModuleConfigurationPanel.setModule(self, module)
		dataUnit = module.getDataUnit()
		if dataUnit.isProcessed():
			data = dataUnit.getSourceDataUnits()[0].getTimepoint(0)
		else:
			data = dataUnit.getTimepoint(0)

#        ext=module.getDataUnit().getTimepoint(0).GetWholeExtent()
		ext = data.GetWholeExtent()
		x, y, z = ext[1], ext[3], ext[5]
		Logging.info("x=%d, y=%d, z=%d" % (x, y, z), kw = "rendering")
		self.xSlider.SetRange(0, x)
		self.xSlider.SetValue(module.x)
		
		self.ySlider.SetRange(0, y)
		self.ySlider.SetValue(module.y)
		
		self.zSlider.SetRange(0, z)
		self.zSlider.SetValue(module.z)
		self.onUpdateSlice(None)
		
	def onUpdateSlice(self, event):
		"""
		Update the slice to be displayed
		"""  
		x = self.xSlider.GetValue()
		y = self.ySlider.GetValue()
		z = self.zSlider.GetValue()
		self.module.setDisplaySlice(x, y, z)
		self.module.updateRendering()	

	def onApply(self, event):
		"""
		Apply the changes
		"""     
		ModuleConfigurationPanel.onApply(self, event)
		self.module.updateData()
		self.module.updateRendering()
