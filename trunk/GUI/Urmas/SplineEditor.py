# -*- coding: iso-8859-1 -*-
"""
 Unit: SplineEditor
 Project: BioImageXD
 Created: n/a
 Creator: Heikki Uuksulainen, KP
 Description:

 This module defines gui for editing the spline which defines the
 camera path.

 This code is distributed under the conditions of the BSD license.  See
 LICENSE.txt for details.

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

__author__ = "Heikki Uuksulainen and Prabhu Ramachandran"
__version__ = "$Revision: 0.1 $"
__date__ = "$Date: 2004/01/20 22:41:28 $"


import vtk
import Logging
import lib.messenger


math = vtk.vtkMath()
			
class SplineEditor:
	"""
	Created: Heikki Uuksulainen
	Description: A class for editing a spline
	"""           

	def __init__(self, parent, renwin, width = 600, height = 400):
		"""
		Initialization
		"""                  
		self.cameraHandles = {}
	   
		self.parent = parent
		self.data = None
		self.cmds = {}
		self.viewMode = 0
		self.wxrenwin = renwin
		lib.messenger.connect(None, "show_arrow", self.onShowArrow)
		lib.messenger.connect(None, "set_preview_mode", self.onSetPreviewMode)
		lib.messenger.connect(None, "show_camera", self.onShowCamera)
		self.arrow = None
		self.arrowVisibility = 0
		
	def onShowCamera(self, obj, evt, cam):
		"""
		Set the active based on an event
		"""
		self.setCamera(cam)
		self.render()
		
	def onShowArrow(self, obj, evt, arg):
		x, y, z = arg
		print "Showing arrow at ", x, y, z
		x -= 100
		self.arrowActor.SetVisibility(1)      
		self.arrowActor.SetPosition(x, y, z)
		self.arrowMapper.Update()
		self.render()        
		
	def onSetPreviewMode(self, obj, evt, flag):
		"""
		Set the preview mode. Toggles visibility of spline, frame etc.
		"""                   
		if flag:
			self.spline.Off()
		else:
			self.spline.On()
		if not flag:
			self.arrowActor.SetVisibility(self.arrowVisibility)
		else:
			self.arrowVisibility = self.arrowActor.GetVisibility()
			self.arrowActor.SetVisibility(0)
		self.outlineactor.SetVisibility((not flag))
		self.axes.SetVisibility((not flag))        

	def initializeVTK(self):
		"""
		Code to initialize VTK portions of this widget
		"""           
		
		self.renWin = self.wxrenwin.GetRenderWindow()
		
		ren = self.renderer = self.wxrenwin.getRenderer()
		
		ren.SetBackground(0, 0, 0)
		self.wxrenwin.Render()

		self.iren = iren = self.renWin.GetInteractor()
		self.iren.SetSize(self.renWin.GetSize())

		self.dataExtensionX = 50
		self.dataExtensionY = 50
		self.dataExtensionZ = 50

		self.data = None
		self.interactionCallback = None
		
		self.spline = spline = vtk.vtkSplineWidget()
		self.spline.GetLineProperty().SetColor(1, 0, 0)
		self.spline.GetHandleProperty().SetColor(0, 1, 0)
		self.spline.SetResolution(1000)
		
		self.spline.SetInteractor(self.iren)
		self.style = self.iren.GetInteractorStyle()
		
		self.spline.AddObserver("EndInteractionEvent", self.endInteraction)
		self.spline.AddObserver("InteractionEvent", self.endInteraction)
		self.style.AddObserver("EndInteractionEvent", self.endInteraction)
		self.style.AddObserver("InteractionEvent", self.endInteraction)        
		self.iren.AddObserver("EndInteractionEvent", self.endInteraction)
		self.iren.AddObserver("InteractionEvent", self.endInteraction)                

		self.spline.On()
		
		self.spline.SetEnabled(1)        
		self.style.SetEnabled(1)
		
		self.outline = vtk.vtkOutlineFilter ()
		self.outlinemapper = vtk.vtkPolyDataMapper ()
		self.outlineactor = vtk.vtkActor ()
		self.axes = vtk.vtkCubeAxesActor2D ()
		self.initCamera()
				
		self.arrow = vtk.vtkArrowSource()

		self.arrowTransform = vtk.vtkTransform()
		self.arrowTransform.RotateX(90.0)
		self.arrowTransform.Scale(80.0, 200.0, 200.0)

		self.transformFilter = vtk.vtkTransformFilter()
			
		self.transformFilter.SetTransform(self.arrowTransform)
		self.transformFilter.SetInput(self.arrow.GetOutput())
		self.arrowMapper = vtk.vtkPolyDataMapper()
		self.arrowMapper.SetInput(self.transformFilter.GetOutput())
		self.arrowActor = vtk.vtkActor()
		self.arrowActor.GetProperty().SetColor((0, 0, 1))
		self.arrowActor.SetMapper(self.arrowMapper)

		self.renderer.AddActor(self.arrowActor)    
		
		self.arrowActor.SetVisibility(0)
		
		self.wxrenwin.Render()
		
	def setMovement(self, flag):
		"""
		Enable / Disable moving the camera around
		"""
		self.style = self.iren.GetInteractorStyle()
		events = ["RightButtonPressEvent", "MiddleButtonPressEvent", "RightButtonReleaseEvent", "MiddleButtonReleaseEvent", "MouseWheelForwardEvent", "MouseWheelBackwardEvent"]
		
		for event in events:
			if not flag:
				if self.cmds.has_key(event):
					self.style.RemoveObserver(self.cmds[event])
				cmd = self.style.AddObserver(event, self.onDisableEvent)
				self.cmds[event] = cmd
			else:
				if event in self.cmds:
					self.style.RemoveObserver(self.cmds[event])
					del self.cmds[event]
				
	def onDisableEvent(self, obj, evt, *args):
		"""
		Stop the event from propagating
		"""
		return False
		
	def setClosed(self, flag):
		"""
		Sets the spline closed or open
		"""
		self.spline.SetClosed(flag)
		self.render()

	def getBounds(self):
		"""
		Returns the bounds of the dataset
		"""
		xmin, xmax, ymin, ymax, zmin, zmax = self.data.GetBounds()
		p1 = (xmin, ymin, zmin)
		p2 = (xmax, ymin, zmin)
		p3 = (xmax, ymax, zmin)
		p4 = (xmin, ymax, zmin)

		p5 = (xmin, ymin, zmax)
		p6 = (xmax, ymin, zmax)
		p7 = (xmax, ymax, zmax)
		p8 = (xmin, ymax, zmax)
		return [p1, p2, p3, p4, p5, p6, p7, p8]

	def setViewMode(self, showViewAngle):
		"""
		Sets the view mode
		"""
		
		if showViewAngle:
			Logging.info("Turning spline off", kw = "animator")
			self.spline.Off()
			self.spline.SetEnabled(0)
		else:
			Logging.info("Turning spline on", kw = "animator")
			self.spline.On()
			self.spline.SetEnabled(1)

		self.viewMode = showViewAngle    

	def findControlPoint(self, pt):
		"""
		This method returns the point that contains the given
					 spline handle
		"""           
		pps = self.getControlPoints()
		return pps[pt]
		
	def setInteractionCallback(self, cb):
		"""
		Method to set a callback that is called when an interaction
					 with the spline ends
		"""
		self.interactionCallback = cb

	def getSplineLength(self, ip0 = 0, ip1 = 0):
		"""
		Method that returns the length of the spline between
					 the given two points. If no points are given, the total
					 length of the spline is returned.
		"""
		if not (ip0 or ip1):
			return self.spline.GetSummedLength()
		points = self.getPoints()
		n = points.GetNumberOfPoints()
		pps = self.getControlPoints()

		# If the second point goes beyond the control points, then use the
		# last point in the spline
		if ip1 >= len(pps):
			p1 = points.GetPoint(n - 1)
		else:
			p1 = pps[ip1]
		if ip0 >= len(pps):
			Logging.info("Attempt to get spline length of ip0=%d,ip1=%d" % (ip0, ip1), kw = "animator")
		p0 = pps[ip0]

		pp0, pp1 = -1, -1
		d0, d1 = 2 ** 64, 2 ** 64

		for i in range(n):
			p = points.GetPoint(i)
			d = vtk.vtkMath.Distance2BetweenPoints(p, p0)
			if d < d0:
				d0, pp0 = d, i
			d = vtk.vtkMath.Distance2BetweenPoints(p, p1)
			if d < d1:
				d1, pp1 = d, i
		d = 0
		if pp0 < 0 or pp1 < 0:
			raise "Did not find point"
			
		p0 = points.GetPoint(pp0)
		p1 = points.GetPoint(pp1)
		sd = vtk.vtkMath.Distance2BetweenPoints(p0, p1)
		for x in range(pp0 + 1, pp1 + 1):
			p1 = points.GetPoint(x)
			d += vtk.vtkMath.Distance2BetweenPoints(p0, p1)
			p0 = p1
		return d
		
	def getCameraPosition(self, n, p0, percentage):
		"""
		Method that returns the camera position when it is located a given percentage
					 of the way from point p0 (the nth control point) to next spline point
		"""        
		pps = self.getControlPoints()
		cp0 = pps[n]
		nskip = 0
		for i in range(n):
			if pps[i] == cp0:
				nskip += 1
		
		points = self.getPoints()
		npts = points.GetNumberOfPoints()
		d0 = 2 ** 64
		pointindex =  -1
		pointindex2 = -1
		closest = -1
		d0 = 2 ** 64
		for i in range(npts):
			p = points.GetPoint(i)
			d = vtk.vtkMath.Distance2BetweenPoints(p, cp0)
			if d < 1:
				if nskip:nskip -= 1
				else:pointindex = i
				break
			if d < d0:
				closest = i
				d0 = d
		
		if pointindex != closest:
			if pointindex < 0 or abs(closest - pointindex) < 5:
				#print "Using closest %d instead of the one we found %d"%(closest,pointindex)
				pointindex = closest
			else:
				Logging.info("closest=", closest, "pointindex=", pointindex, "d0=", d0, kw = "animator")
				raise "Didn't get closest!"
		if n == len(pps) - 1:
			pointindex2 = npts - 1
		else:
			cp1 = pps[n + 1]
			closest = -1
			d0 = 2 ** 64
			for i in range(pointindex, npts):
				p = points.GetPoint(i)
				d = vtk.vtkMath.Distance2BetweenPoints(p, cp1)
				if d < 1:
					pointindex2 = i
					break
				if d < d0:
					closest = i
					d0 = d
			if pointindex2 != closest:
				if pointindex2 < 0 or abs(closest - pointindex2) < 5:
					pointindex2 = closest
				else:
					raise "Didn't get closest!"                    
		n = pointindex + (pointindex2 - pointindex) * percentage
		return (n, points.GetPoint(n))
					
	
		
	def updateData(self, data, ctf = None):
		"""
		Method that initializes the VTK rendering based
					 on a dataset
		"""            
		if self.data:
			del self.data
		self.data = data
		
		self.outline.SetInput(self.data)
		self.outlinemapper.SetInput (self.outline.GetOutput ())
		self.outlineactor.SetMapper (self.outlinemapper)
		self.outlineactor.GetProperty().SetColor((255, 255, 255))

		self.renderer.AddActor(self.outlineactor)

		# Create transfer mapping scalar value to opacity
		opacityTransferFunction = vtk.vtkPiecewiseFunction()
		opacityTransferFunction.AddPoint(10, 0.0)
		opacityTransferFunction.AddPoint(255, 0.2)

		colorTransferFunction = ctf
		if not colorTransferFunction:
			print "DIDN'T GET CTF!!"
			# Create transfer mapping scalar value to color
			colorTransferFunction = vtk.vtkColorTransferFunction()
			colorTransferFunction.AddRGBPoint(0.0, 0.0, 0.0, 0.0)
			colorTransferFunction.AddRGBPoint(255.0, 0.0, 1.0, 0.0)
		
		volumeProperty = vtk.vtkVolumeProperty()
		volumeProperty.SetColor(colorTransferFunction)
		volumeProperty.SetScalarOpacity(opacityTransferFunction)
		volumeProperty.ShadeOff()
		#volumeProperty.SetInterpolationTypeToLinear()

		
		#volumeMapper = vtk.vtkVolumeTextureMapper2D()
		
#        volumeMapper = vtk.vtkVolumeTextureMapper3D()
		
		data.Update()
#        ncomps=data.GetNumberOfScalarComponents()
#        if ncomps>1:
#            volumeProperty.IndependentComponentsOff()
#        else:
#            volumeProperty.IndependentComponentsOn()                    
#        volumeMapper.SetInput(self.data)

		self.volumeMapper =  vtk.vtkFixedPointVolumeRayCastMapper()
		self.volumeMapper.SetIntermixIntersectingGeometry(1)
		self.volumeMapper.SetSampleDistance(2)
		self.volumeMapper.SetBlendModeToComposite()
		#volume.SetMapper(self.volumeMapper)
		self.volumeMapper.SetInput(self.data)
		volumeMapper = self.volumeMapper

		volume = vtk.vtkVolume()
		# temporary
		self.renderer.AddVolume(volume)
		
		volume.SetMapper(volumeMapper)
		volume.SetProperty(volumeProperty)
		
		txt = ("X", "Y", "Z")
		for t in txt:
			eval ("self.axes.%sAxisVisibilityOn ()" % t)
			eval ("self.axes.Get%sAxisActor2D().SetLabelFactor(0.5)" % t)

		self.axes.GetProperty ().SetColor ((255, 255, 255))
		self.axes.SetNumberOfLabels (2)
		self.axes.SetFontFactor (1.0)
		self.axes.SetFlyModeToOuterEdges ()
		self.axes.SetCornerOffset (0.0)
		self.axes.ScalingOff ()
		self.axes.SetCamera (self.renderer.GetActiveCamera ())

		self.renderer.AddActor (self.axes)
		self.axes.SetInput (self.outline.GetOutput ())
		

		self.volume = volume
		self.volumeMapper = volumeMapper
		self.volumeProperty = volumeProperty
		self.wxrenwin.Render()
		#if not self.volumeMapper.IsRenderSupported(self.volumeProperty):
#            self.volumeMapper =  vtk.vtkFixedPointVolumeRayCastMapper()
#            self.volumeMapper.SetIntermixIntersectingGeometry(1)
#            self.volumeMapper.SetSampleDistance(2)
#            self.volumeMapper.SetBlendModeToComposite()
#            volume.SetMapper(self.volumeMapper)
#            self.volumeMapper.SetInput(self.data)
			
			
	def setCamera(self, cam):
		"""
		Set the active camera
		"""
		if self.renderer:
			self.renderer.SetActiveCamera(cam)
		
	def getCamera(self):
		"""
		If there's a currently active camera, returns it
		"""
		cam = None
		if self.renderer:
			cam = self.renderer.GetActiveCamera()
		return cam

	def getPoints(self):
		"""
		Returns the points of the polygon forming the spline
		"""
		data = vtk.vtkPolyData()
		self.spline.GetPolyData(data)
		return data
		
	def getRandomPoint(self):
		"""
		Return a random point for the spline
		"""        
		pt = (math.Random(-self.dataExtensionX, self.dataWidth() + self.dataExtensionX),
				math.Random(-self.dataExtensionY, self.dataHeight() + self.dataExtensionY),
				math.Random(-self.dataExtensionZ, self.dataDepth() + self.dataExtensionZ))
		return pt

	def initSpline(self, points):
		"""
		Creates a random spline with given amount of points
		"""        
		lst = []
		for i in range(points):
			pt = self.getRandomPoint()
			#self.spline.SetHandlePosition(i,pt)
			lst.append(pt)
		self.setSplinePoints(lst)
			
	def setSplinePoints(self, pointlist):
		"""
		Sets the handles of the spline widget to the given point list
		"""
		n = len(pointlist)
		self.spline.SetNumberOfHandles(n)
		for i in range(n):
			self.spline.SetHandlePosition(i, pointlist[i])
		self.renderer.Render()

	def setSplinePoint(self, pos, point):
		"""
		Sets the a handle of the spline widget to a given point
		"""        
		self.spline.SetHandlePosition(pos, point)
		
	def initCamera(self):
		"""
		Initializes the camera
		"""        
		cam = self.getCamera()
		if cam:
			focal = self.getCameraFocalPointCenter()
			cam.SetFocalPoint(focal)
			cam.SetPosition(self.getInitialCameraPosition())
			cam.ComputeViewPlaneNormal()

	def getInitialCameraPosition(self):
		"""
		Returns an initial position for the camera
		"""        
		if not self.data:
			return [0, 0, 0]
		dims = self.data.GetDimensions()
		return 1.5 * dims[0], 0.5 * dims[1], 100.0 * dims[2]
		
	def getCameraFocalPointCenter(self):
		"""
		Returns the center of the current dataset
		""" 
		if not self.data:
			return [0, 0, 0]
		return self.data.GetCenter()
			
			
	def getControlPoints(self):
		"""
		Returns the points for the handles of the widget
		"""        
		points = []
		for i in range(self.spline.GetNumberOfHandles()):
			points.append(self.spline.GetHandlePosition(i))
			
		return points

	def isActive(self):
		"""
		A method that tells whether the spline is enabled or not
		"""            
		return self.spline.GetEnabled()

	def dataWidth(self):
		"""
		Returns the width of the data
		"""       
		if not self.data:
			return 0
		return (self.data.GetDimensions())[0]

	def dataHeight(self):
		"""
		Returns the height of the data
		"""       
		if not self.data:
			return 0
		return (self.data.GetDimensions())[1]

	def dataDepth(self):
		"""
		Returns the depth of the data
		"""           
		if not self.data:
			return 0
		return (self.data.GetDimensions())[2]
	
	def dataDimensions(self):
		"""
		Returns the dimensions of the data
		"""           
		return self.data.GetDimensions()

	def getNumberOfPoints(self):
		"""
		Returns the number of points in the polygon that forms
					 the spline
		"""           
		data = vtk.vtkPolyData()
		self.spline.GetPolyData(data)
		return data.GetNumberPoints()        

	def quit(self):
		"""
		Destructs necessary objects upon quitting
		"""           
		pass
		
	def endInteraction(self, event = -1, e2 = -1):
		"""
		Method called when user manipulates the spline and then 
					 lets the mouse button up. Used to call a callback.
		"""
		cam = self.getCamera()
	
		if self.viewMode == 1:
			lib.messenger.send(None, "set_camera", cam)
			lib.messenger.send(None, "view_camera", cam)
		
		if self.interactionCallback:
			self.interactionCallback()

	def getAsImage(self):
		"""
		Render the scene to a vtkImageData
		"""
		filter = vtk.vtkWindowToImageFilter()
		filter.SetInput(self.renWin)
		filter.Update()
		return filter.GetOutput()
	
	def render(self):
		"""
		Render the widget
		"""
		self.wxrenwin.Render()
