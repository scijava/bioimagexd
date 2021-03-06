# -*- coding: iso-8859-1 -*-

"""
 Unit: InteractivePanel
 Project: BioImageXD
 Description:

 A panel that can select regions of interest, draw annotations, etc.
		 
 Copyright (C) 2005	 BioImageXD Project
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
import lib.ImageOperations
import lib.messenger
import Logging
import math
import MaskTray
import wx.lib.ogl as ogl
import platform
import wx
import bxdevents
from AnnotationSettings import AnnotationSettings

import GUI.PainterHelpers
import GUI.OGLAnnotations
import GUI.MaskTray

ZOOM_TO_BAND = 1
MANAGE_ANNOTATION = 2
ADD_ANNOTATION = 3
ADD_ROI = 4
SET_THRESHOLD = 5

INTERPOLATION_VARY =- 1
INTERPOLATION_NONE = 0
INTERPOLATION_LINEAR = 1
INTERPOLATION_CUBIC = 2

class InteractivePanel(ogl.ShapeCanvas):
	"""
	A panel that can be used to select regions of interest, draw
				 annotations on etc.
	"""
	def __init__(self, parent, **kws):
		"""
		Initialization
		"""
		ogl.OGLInitialize()
		# boolean for indicating whether or not the annotations are enabled on this interactivepanel
		self.annotationsEnabled = False
		self.parent = parent
		# Some variables for quickly determining the platform 
		self.is_windows = platform.system() == "Windows"
		self.is_mac = platform.system() == "Darwin"
		self.enabled = True
		
		# A counter for wheel rotations so that we can react to a given number of rotations
		# since a single rotation of wheel produces quite many events
		self.wheelCounter = 0
		self.xoffset = 0
		self.yoffset = 0		
		self.currentSketch = None
		# The number of pixels a single scroll unit will scroll
		self.scrollStepSize = 1
		# A variable to indicate the current position of a mouse drag for calculating
		# how much to scroll or zoom 
		self.scrollPos = None
		# a variable to indicate the current position of a mouse drag for calculating
		# in which direction to change the z slice
		self.zoomDragPos = None
		self.maxClientSizeX = 512
		self.maxClientSizeY = 512
		self.painterHelpers = []
		size = kws.get("size", (512, 512))
		self.zoomToFitFlag = False
		
		self.dataUnit = None
		self.dataDimX = self.dataDimY = self.dataDimZ = 0
		self.listeners = {}
		self.annotationClass = None
		self.threeDMode = False
		self.voxelSize = (1, 1, 1)
		self.bgColor = kws.get("bgColor", (0, 0, 0))
		self.action = 0
		self.imagedata = None
		self.bmp = None

		self.preventScrolling = False
		self.annotationColor = wx.Colour(0, 255, 0)
		self.actionstart = (0, 0)
		self.actionend = (0, 0)
		self.prevPolyEnd = None
		self.measurementPoints = []
		x, y = size
		self.buffer = wx.EmptyBitmap(x, y)
		ogl.ShapeCanvas.__init__(self, parent, -1, size = size)
		
		self.diagram = ogl.Diagram()
		self.SetDiagram(self.diagram)
		self.diagram.SetCanvas(self)
		
		self.size = size
	
		self.lines = []
		
        # Annotations that have been converted to masks by right-clicking.
		self.roiToMaskRC = []
		self.subtractROI = None
		self.rubberbandAllowed = 0
		
		self.ID_VARY = wx.NewId()
		self.ID_NONE = wx.NewId()
		self.ID_LINEAR = wx.NewId()
		self.ID_CUBIC = wx.NewId()
		self.interpolation = INTERPOLATION_VARY
		self.renew = 1
		self.menu = wx.Menu()
		
		item = wx.MenuItem(self.menu, self.ID_VARY, "Interpolation depends on size", kind = wx.ITEM_RADIO)
		self.menu.AppendItem(item)
		self.menu.Check(self.ID_VARY, 1)
		item = wx.MenuItem(self.menu, self.ID_NONE, "Nearest neighbor interpolation", kind = wx.ITEM_RADIO)
		self.menu.AppendItem(item)
		item = wx.MenuItem(self.menu, self.ID_LINEAR, "Linear interpolation", kind = wx.ITEM_RADIO)
		self.menu.AppendItem(item)
		item = wx.MenuItem(self.menu, self.ID_CUBIC, "Cubic interpolation", kind = wx.ITEM_RADIO)
		self.menu.AppendItem(item)
		
		self.subbgMenu = wx.Menu()
		self.ID_SUB_BG = wx.NewId()
		item = wx.MenuItem(self.subbgMenu, self.ID_SUB_BG, "Subtract background")
		self.subbgMenu.AppendItem(item)

		self.ID_ZERO_BG = wx.NewId()
		item = wx.MenuItem(self.subbgMenu, self.ID_ZERO_BG, "Set background to zero")
		self.subbgMenu.AppendItem(item)

		self.ID_CONV_SG_ROI_TO_MASK = wx.NewId()
		item = wx.MenuItem(self.subbgMenu, self.ID_CONV_SG_ROI_TO_MASK, "Convert to mask")
		self.subbgMenu.AppendItem(item)
		
		self.Bind(wx.EVT_MENU, self.onSetInterpolation, id = self.ID_VARY)
		self.Bind(wx.EVT_MENU, self.onSetInterpolation, id = self.ID_NONE)
		self.Bind(wx.EVT_MENU, self.onSetInterpolation, id = self.ID_LINEAR)
		self.Bind(wx.EVT_MENU, self.onSetInterpolation, id = self.ID_CUBIC)
		self.Bind(wx.EVT_MENU, self.onSubtractBackground, id = self.ID_SUB_BG)
		self.Bind(wx.EVT_MENU, self.onSetBackgroundToZero, id = self.ID_ZERO_BG)
		self.Bind(wx.EVT_MENU, self.onConvertSingleROIToMask, id = self.ID_CONV_SG_ROI_TO_MASK)
		
		GUI.PainterHelpers.registerHelpers(self)

		self.zoomFactor = 1
		self.addListener(wx.EVT_RIGHT_DOWN, self.onFinishPolygon)
		self.addListener(wx.EVT_RIGHT_DOWN, self.onRightClickROI)
		self.paintPreview()
		
		self.Unbind(wx.EVT_PAINT)
		self.Bind(wx.EVT_PAINT, self.OnPaint)
		

		self.Bind(wx.EVT_LEFT_DOWN, self.onLeftDown)
		self.Bind(wx.EVT_MOTION, self.onMouseMotion)
		self.Bind(wx.EVT_RIGHT_DOWN, self.onRightDown)
		self.Bind(wx.EVT_LEFT_UP, self.executeAction)
		self.Bind(wx.EVT_SIZE, self.OnSize)
		self.Bind(wx.EVT_MOUSEWHEEL, self.onMouseWheel)
		self.Bind(wx.EVT_KEY_UP, self.onKeyUp)
		lib.messenger.connect(None, "update_helpers", self.onUpdateHelpers)
		lib.messenger.connect(None, bxdevents.DATA_DIMENSIONS_CHANGED, self.onUpdateDataDimensions)
		lib.messenger.connect(None, "mask_changed", self.onMaskSelectionChanged)
		lib.messenger.connect(None, bxdevents.TRANSLATE_DATA, self.onApplyTranslation)
			

	def deregister(self):
		"""
		Delete all known references because this view mode is to be removed
		"""
		try:
			lib.messenger.disconnect(None, "update_helpers", self.onUpdateHelpers)
			lib.messenger.disconnect(None, bxdevents.DATA_DIMENSIONS_CHANGED, self.onUpdateDataDimensions)
			lib.messenger.disconnect(None, "mask_changed", self.onMaskSelectionChanged)
			lib.messenger.disconnect(None, bxdevents.TRANSLATE_DATA, self.onApplyTranslation)
		except:
			pass

	def onKeyUp(self,event):
		"""
		An event handler of keyboard key release
		"""
		keyCode = event.GetKeyCode()
		if keyCode in [wx.WXK_DELETE, wx.WXK_NUMPAD_DELETE, wx.WXK_BACK]:
			ctrl = event.ControlDown()
			self.deleteAnnotation(ctrl)
		elif keyCode in [wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER]:
			if len(self.measurementPoints)>1:
				totalDistance=0
				for i, pt in enumerate(self.measurementPoints[1:]):
					x0,y0 = self.measurementPoints[i]
					x1,y1 = pt
					d = math.sqrt((x1-x0)*(x1-x0)+(y1-y0)*(y1-y0))
					d /= self.zoomFactor
					totalDistance += d
				lib.messenger.send(None, "show_measured_distance", totalDistance)
			self.measurementPoints = []
			self.paintPreview()
			self.Refresh()

		
	def onUpdateDataDimensions(self, *args):
		"""
		update the preview because data dimensions may have changed
		"""
		x, y, z = self.dataUnit.getDimensions()
		self.dataDimX, self.dataDimY, self.dataDimZ = x, y, z
		if self.zoomToFitFlag:
			self.zoomToFit()
		self.calculateBuffer()
		
		value = scripting.visualizer.zslider.GetValue()
		if value > z: value = z
		# This message works differently (index wise, 0-(z-1)) compared to zslider's range (1-z)
		lib.messenger.send(None, "zslice_changed", value-1)
		scripting.visualizer.zslider.SetRange(1, z)
		self.updatePreview()
		scripting.visualizer.zslider.SetValue(value)
		
		
	def disableAnnotations(self):
		"""
		disable the annotations
		"""
		self.annotationsEnabled = 0


	def onConvertSingleROIToMask(self, event):
		"""
		Converts selected (single) ROI to mask
		"""
		masks, names = self.getMasksAndNames([self.subtractROI])
		for i in range(len(masks)):
			#duplicate = False
			#for item in self.roiToMaskRC:
			#	if names[i] in item:
			#		duplicate = True
			#		break
			#if not duplicate:
			self.roiToMaskRC.append((masks[i], names[i]))
		if hasattr(scripting.visualizer.currentWindow, "getRightClickedConvertedMasks"):
			masksAndNames = scripting.visualizer.currentWindow.getRightClickedConvertedMasks()
			dims = scripting.visualizer.dataUnit.getDimensions()
			masks = []
			for i in range(len(masksAndNames)):
				masks.append(MaskTray.Mask(masksAndNames[i][1], dims, masksAndNames[i][0]))
			scripting.visualizer.setMask(masks)


	def getRightClickedConvertedMasks(self):
		"""
		Returns right-clicked converted masks along with their names
		"""
		return self.roiToMaskRC
	
	def onSubtractBackground(self, event):
		"""
		subtract a background using the given ROI
		"""
		if not self.subtractROI: return
		mx, my, mz = self.dataUnit.getDimensions()
		rois = [self.subtractROI]
		n, maskImage = lib.ImageOperations.getMaskFromROIs(rois, mx, my, mz)
		
		tp = scripting.visualizer.getTimepoint()
		if self.dataUnit.isProcessed():
			origImage = self.dataUnit.doPreview(z, renew, tp)
		else:
			origImage = self.dataUnit.getTimepoint(tp)
			
		import itk
		scalarType = origImage.GetScalarTypeAsString()
		if scalarType == "unsigned char":
			ImageType = itk.VTKImageToImageFilter.IUC3
		elif scalarType == "unsigned short":
			ImageType = itk.VTKImageToImageFilter.IUS3
		
		vtkToItk = ImageType.New()
		vtkToItk.SetInput(origImage)
		vtkToItk.Update()
		
		itkOrig = vtkToItk.GetOutput()
		
		vtkToItk2 = itk.VTKImageToImageFilter.IUC3.New()
		vtkToItk2.SetInput(maskImage)
		vtkToItk2.Update()
		itkLabel = vtkToItk2.GetOutput()

		labelStats = itk.LabelStatisticsImageFilter[itkOrig, itkLabel].New()
		labelStats.SetInput(0, itkOrig)
		labelStats.SetInput(1, itkLabel)
		labelStats.Update()
		
		avgint = labelStats.GetMean(255)   
		ds = self.dataUnit.getDataSource()
		shift = ds.getIntensityShift()
		scale = ds.getIntensityScale()
		if shift:
			shift -= int(round(avgint))
		else:
			shift = -int(round(avgint))
		if not scale:
			scale = 1
		ds.setIntensityScale(shift, scale)
		self.updatePreview(1)
 
		
	def onSetInterpolation(self, event):
		"""
		Set the inteprolation method
		"""
		eID = event.GetId()
		flags = (1, 0, 0, 0)
		interpolation = INTERPOLATION_VARY
		if eID == self.ID_NONE:
			flags = (0, 1, 0, 0)
			interpolation = INTERPOLATION_NONE
		elif eID == self.ID_LINEAR:
			flags = (0, 0, 1, 0)
			interpolation = INTERPOLATION_LINEAR
		elif eID == self.ID_CUBIC:
			flags = (0, 0, 0, 1)
			interpolation = INTERPOLATION_CUBIC
		
		self.menu.Check(self.ID_VARY, flags[0])
		self.menu.Check(self.ID_NONE, flags[1])
		self.menu.Check(self.ID_LINEAR, flags[2])
		self.menu.Check(self.ID_CUBIC, flags[3])
		if self.interpolation != interpolation:
			self.interpolation = interpolation
			self.updatePreview()
	
	def onApplyTranslation(self, obj, event, translation):
		"""
		Apply a translation to the annotations
		"""
		dx,dy,dz = translation
		print "\nApplying a translation of ",dx,dy
		shapelist = self.diagram.GetShapeList()
		for shape in shapelist:
			sx, sy = shape.GetX(), shape.GetY()
			shape.SetX(sx+dx)
			shape.SetY(sy+dy)
		self.repaintHelpers()
	
	def setOffset(self, x, y):
		"""
		Set the offset of this interactive panel. The offset is variable
					 based on the size of the screen vs. the dataset size.
		"""

		shapelist = self.diagram.GetShapeList()
		for shape in shapelist:
			if not hasattr(shape, "getOffset"):
				continue
			sx, sy = shape.GetX(), shape.GetY()
			ox, oy = shape.getOffset()
			xdiff = x - ox
			ydiff = y - oy
			shape._offset = (x, y)
			#shape.Move(x+xdiff,y+ydiff, display=False)
			shape.SetX(sx + xdiff)
			shape.SetY(sy + ydiff)

		self.xoffset, self.yoffset = x, y
		self.repaintHelpers()
			   
		
	def unOffset(self, *args):
		"""
		Return a coordinate from which the offsets have been subtracted
		"""
		if type(args[0]) == types.TupleType:
			return (args[0][0] - self.xoffset, args[0][1] - self.yoffset)
		else:
			return (args[0] - self.xoffset, args[1] - self.yoffset)
		
	def getOffset(self):
		"""
		Return the offset
		"""
		return self.xoffset, self.yoffset
		
	def addListener(self, evt, func):
		"""
		Add a listener to an event
		"""
		if not self.listeners.has_key(evt):
			self.listeners [evt] = [func]
		else:
			self.listeners [evt].append(func)

		
	def registerPainter(self, painter):
		"""
		Add a painter helper that will be used to paint on the DC after everything else
		"""
		self.painterHelpers.append(painter)
	  
	def onUpdateHelpers(self, obj, evt, update):
		"""
		a callback for updating the helpers based on messenger messages
		"""
		self.repaintHelpers(update)
		if update:
			self.Refresh()
			
	def repaintHelpers(self, update = 1):
		"""
		Repaint the helpers but nothing else
		"""
		
		w, h = self.buffer.GetWidth(), self.buffer.GetHeight()
		self.buffer = wx.EmptyBitmap(w, h)
		memdc = wx.MemoryDC()
		memdc.SelectObject(self.buffer)
		
		x0, y0, x1, y1 = self.GetClientRect()
		memdc.DrawBitmap(self.bgbuffer, x0, y0, False)
		
		for helper in self.painterHelpers:
			helper.paintOnDC(memdc)
		memdc.SelectObject(wx.NullBitmap)		 
		if update:
			self.Update()
		
			
	def getRegionsOfInterest(self):
		"""
		Return all the regions of interest draw in this panel	  
		"""
		shapelist = self.diagram.GetShapeList()
		rois = []
		for shape in shapelist:
			if isinstance(shape, GUI.OGLAnnotations.OGLAnnotation) and shape.isROI():
				rois.append(shape)
		return rois
		
	def roiToMask(self):
		"""
		Convert the selected ROI to mask
		"""
		return self.getMasksAndNames(self.getRegionsOfInterest())

	def getMasksAndNames(self, rois):
		"""
		Returns the masks and names of the given ROIs
		"""
		mx, my, mz = self.dataUnit.getDimensions()
		names = []
		#names = [roi.getName() for roi in rois]
		for roi in rois:
			if roi.parent == None:
				names.append(roi.getName())
			elif roi.getName() not in names:
				names.append(roi.getName())
		
		# This is a bit tricky. If the ROI is a 3D one, then we need
		# to create one mask for every slice and then merge them
		# together. We need to group the 3D ROIs together based on their
		# parent.
		parents = []
		shapeAnnotations = filter(lambda x:isinstance(x, GUI.OGLAnnotations.ShapeAnnotation), rois)
		for shapeAnnotation in shapeAnnotations:
			if shapeAnnotation.parent not in parents and shapeAnnotation.parent != None:
				parents.append(shapeAnnotation.parent)

		# Create 3D masks based off of the 3D annotations.
		masks = []
		for parent in parents:
			annotations = parent.GetAnnotations()
			maskFromROIs = []
			# All children of a parent form one mask volume.
			for annotation in annotations:
				maskFromROIs.append(lib.ImageOperations.getMaskFromROIs([annotation], mx, my, 1)[1])
			if maskFromROIs != []:
				masks.append(lib.ImageOperations.CreateVolumeFromSlices(maskFromROIs, self.dataUnit.getSpacing()))

        # Create 2D masks based off of the 2D annotations.
		rois2D = []
		for roi in rois:
			if roi.parent == None:
				rois2D.append(roi)
		if rois2D != []:
			masks.append(lib.ImageOperations.getMaskFromROIs(rois2D, mx, my, mz)[1])
						
		# Return all the masks and names.
		return masks, names

	def create3DCircle(self, x, ex, y, ey, scaleFactor, nrOfCircles):
		my3DCircle = GUI.OGLAnnotations.My3DCircle()
		for i in range(0, nrOfCircles):
		    circle = self.createCircle(x, ex, y, ey, scaleFactor)
		    my3DCircle.AddAnnotation(circle)
		return my3DCircle

	def createCircle(self, x, ex, y, ey, scaleFactor):
		diff = max(abs(x - ex), abs(y - ey))
		if diff < 2:diff = 2
		shape = GUI.OGLAnnotations.MyCircle(2 * diff, zoomFactor = scaleFactor)
		shape._offset = (self.xoffset, self.yoffset)
		shape.SetCentreResize(0)
		shape.SetX( ex )
		shape.SetY( ey )
		return shape

	def create3DRectangle(self, x, ex, y, ey, scaleFactor, nrOfRectangles):
		my3DRectangle = GUI.OGLAnnotations.My3DRectangle()
		for i in range(0, nrOfRectangles):
			rectangle = self.createRectangle(x, ex, y, ey, scaleFactor)
			my3DRectangle.AddAnnotation(rectangle)
		return my3DRectangle

	def createRectangle(self, x, ex, y, ey, scaleFactor):
		dx = abs(x - ex)
		dy = abs(y - ey)
		shape = GUI.OGLAnnotations.MyRectangle(dx, dy, zoomFactor = scaleFactor)
		shape._offset = (self.xoffset, self.yoffset)
		shape.SetCentreResize(0)
		shape.SetX( ex + (x - ex) / 2 )
		shape.SetY( ey + (y - ey) / 2 )
		return shape

	def create3DPolygon(self, points, zoomFactor = -1, nrOfPolygons = 0):
		"""
		Create a 3D polygon
		"""
		my3DPolygon = GUI.OGLAnnotations.My3DPolygon()
		for i in range(0, nrOfPolygons):
			polygon = self.createPolygon(points, zoomFactor)
			my3DPolygon.AddAnnotation(polygon)
		return my3DPolygon

	def createPolygon(self, points, zoomFactor):
		shape = GUI.OGLAnnotations.MyPolygon(zoomFactor = self.zoomFactor)
		shape._offset = (self.xoffset, self.yoffset)
		pts = []
		mx, my = shape.polyCenter(points)
		for x, y in points:
			pts.append((((x - mx)), ((y - my))))
		shape.Create(pts)
		shape.SetX(mx)
		shape.SetY(my)
		self.addNewShape(shape)
		return shape

	def initPolygon(self, points, zoomFactor = -1):
		"""
		Create a polygon
		"""
		if zoomFactor == -1:
			zoomFactor = self.zoomFactor

		if self.threeDMode:
			self.create3DPolygon(points, zoomFactor, self.dataUnit.getDimensions()[2])
		else:
			self.createPolygon(points, zoomFactor)
		self.paintPreview()
		
	def OnSize(self, evt):
		"""
		The size evet
		"""
		self.maxClientSizeX, self.maxClientSizeY = self.GetClientSize()
		evt.Skip()
		
	def setBackgroundColor(self, bg):
		"""
		Sets the background color
		"""	   
		self.bgColor = bg
		
	def getDrawableRectangles(self):
		"""
		Return the rectangles can be drawn on as four-tuples
		"""	   
		a, b, c, d = self.GetClientRect()
		return [(a, c, b, d)]
		

	def onRightClickROI(self, event):
		"""
		a method that checks whether a right click event happens on a ROI
					 and acts upon it
		"""
		x, y = event.GetPosition()
		obj, attach = self.FindShape(x, y)
		if obj and obj.isROI():
			self.subtractROI = obj
			self.PopupMenu(self.subbgMenu, event.GetPosition())
	
	def onMouseWheel(self, event):
		"""
		react to a mouse wheel rotation, where three consecutive rotations
					 in the same direction will trigger a change in zoom level
		"""
		if not event.GetWheelRotation():
			return
		direction = event.GetWheelRotation() / abs(event.GetWheelRotation())
		self.wheelCounter += direction
		if abs(self.wheelCounter) == 3:
			if self.wheelCounter < 0:
				scripting.visualizer.onSliceDown()
			else:
				scripting.visualizer.onSliceUp()
			self.wheelCounter = 0
			
	def onRightDown(self, event):
		"""
		An event handler for when the right button is clicked down
		"""
		if wx.EVT_RIGHT_DOWN in self.listeners:
			for method in self.listeners[wx.EVT_RIGHT_DOWN]:
				method(event)
				flag = event.GetSkipped()
				if not flag:
					return
		event.Skip()
		if event.ShiftDown():
			self.PopupMenu(self.menu, event.GetPosition())
		else:
			self.zoomDragPos = event.GetPosition()[1]

	def onFinishPolygon(self, event):
		"""
		Turn the sketch polygon into a real polygon
		"""
		if self.currentSketch:
			pts = self.currentSketch.getPoints()
			self.currentSketch.Delete()
			self.RemoveShape(self.currentSketch)
			del self.currentSketch
			self.currentSketch = None
			self.initPolygon(pts)
			self.repaintHelpers()
			self.Refresh()
			self.action = 0
			self.actionstart = (0, 0)
			self.actionend = (0, 0)
			self.saveAnnotations()
		else:
			event.Skip()
		return 1
		
	def markMeasurementPoint(self, pt):
		"""
		Mark a measurement point
		"""
		self.measurementPoints.append(pt)
		self.paintPreview()
		self.Refresh()
		
	def onLeftDown(self, event):
		"""
		Sets the starting position of rubber band for zooming
		"""
		self.SetFocus()
		event.Skip()
		pos = event.GetPosition()
		x, y = pos

		foundDrawable = 0
		for x0, x1, y0, y1 in self.getDrawableRectangles():
			if x >= x0 and x <= x1 and y >= y0 and y <= y1:
				foundDrawable = 1 
				break
		if event.AltDown() and foundDrawable:
			self.markMeasurementPoint((x,y))
		if not foundDrawable:
			Logging.info("Attempt to draw in non-drawable area: %d,%d" % (x, y), kw = "iactivepanel")
			# we zero the action so nothing further will be done by onMouseMotion
			self.action = 0
			return 1
			
		if self.currentSketch:
			self.currentSketch.AddPoint(pos)
		self.actionstart = pos
		self.rubberbandAllowed = 1
		return 1
		
	def onMouseMotion(self, event):
		"""
		Update the mouse position and the rendering according to user action,
					 e.g. draw a rubber band when zooming to selected region
		"""
		if not event.Dragging():
			self.scrollPos = None
			self.zoomDragPos = None
		if (event.LeftIsDown() or event.MiddleIsDown()) and event.Dragging():
			# Here we check if we want to prevent scrolling, because
			# we might only want to move an annotation. The key
			# is to select an annotation, and then drag it.
			# The preventScrolling variable is updated in OGLAnnotations'
			# onDragLeft.
			annotations = AnnotationSettings.getInstance().getAnnotations()
			keys = annotations.keys()
			annotationSelected = False
			for key in keys:
				if annotations[key].Selected():
					annotationSelected = True
					break
			if not self.preventScrolling and not annotationSelected and self.scrollPos and self.action != ZOOM_TO_BAND and self.action != ADD_ANNOTATION and self.action != ADD_ROI:
				self.changeScrollByDifference(self.scrollPos, event.GetPosition())
			self.scrollPos = event.GetPosition()
		if event.RightIsDown():
			yPos = event.GetPosition()[1]
			if self.zoomDragPos:
				dy = yPos - self.zoomDragPos
				f = self.getZoomFactor()
				if dy > 0:
					f-=0.1
				elif dy < 0:
					f+=0.1
				scripting.visualizer.setZoomFactor(f)
				scripting.visualizer.Render()
			if event.Dragging():
				self.zoomDragPos = yPos
			
		if event.LeftIsDown():
			self.actionend = event.GetPosition()
			if self.action == ZOOM_TO_BAND or self.action == ADD_ANNOTATION or self.action == ADD_ROI:
				self.paintPreview()
				self.Refresh()
				
		pos = event.GetPosition()

		if self.currentSketch:
			self.actionend = pos
			x0, y0, w, h = self.GetClientRect()
			
			self.currentSketch.setTentativePoint((pos))
			dc = wx.ClientDC(self)
			self.PrepareDC(dc)
			
			self.paintPreview()
			self.Refresh()
			 
			self.currentSketch.Draw(dc)
			
			dc.EndDrawing()
		event.Skip()
		
		
	def getInterpolationForSize(self, x, y,  factor):
		"""
		return the proper interpolation for INTERPOLATION_VARY for the given width and height
		"""
		pixels = (x * factor) * (y * factor)
		if pixels <= 1024 * 1024:
			interpolation = INTERPOLATION_CUBIC
		elif pixels <= 2048 * 2048:
			interpolation = INTERPOLATION_LINEAR
		else:
			interpolation = INTERPOLATION_NONE
		return interpolation
		
	def zoomImageWithInterpolation(self, image, zoomFactor, interpolation, z, ctf = None):
		"""
		zoom an image with the given zoomFactor using the given interpolation
		"""
		if interpolation == INTERPOLATION_VARY:
			#x, y, z = image.GetDimensions()
			x,y = self.dataDimX, self.dataDimY
			pixels = (x * zoomFactor) * (y * zoomFactor)
			if pixels <= 1024 * 1024:
				interpolation = INTERPOLATION_CUBIC
				Logging.info("Using cubic interpolation",kw="preview")
			elif pixels <= 2048 * 2048:
				interpolation = INTERPOLATION_LINEAR
				Logging.info("Using linear interpolation",kw="preview")
			else:
				Logging.info("Using no interpolation", kw = "preview")
				interpolation = INTERPOLATION_NONE
				return None
		img = lib.ImageOperations.scaleImage(image, zoomFactor, z, interpolation)
		return lib.ImageOperations.vtkImageDataToWxImage(img, ctf = ctf)
		
	def changeScrollByDifference(self, start, end):
		"""
		scroll by the difference of the starting and ending coordinates
		"""
#		Logging.info("Scrolling by difference of %s and %s"%(str(start),str(end)), kw="preview")
		x, y = self.CalcUnscrolledPosition(0,0)
		
		dx = end[0]-start[0]
		dy = end[1]-start[1]
#		Logging.info("Currents scroll = %d, %d, adding %d and %d"%(x,y,dx,dy), kw="preview")
		x -= dx
		y -= dy
		sx = int(x / self.scrollStepSize)
		sy = int(y / self.scrollStepSize)
		
		self.Scroll(sx, sy)
		
	def onDeactivate(self):
		"""
		event handler called when the visualization mode is about to be deactivated
		"""
		if not self.dataUnit:
			return
		if self.dataUnit and self.dataUnit.getDataSource(): 
			settings = self.dataUnit.getSettings()
			if self.annotationsEnabled:
				self.saveAnnotations()
				print "\n\n*** Saving annotations"
				scripting.storeSettingsToCache(self.dataUnit.getFileName() + "_" + self.dataUnit.getName() + "_annotations", [settings])
				self.dataUnit.getSettings().set("Annotations", [])
					   
	def getDuplicateDC(self, dc):
		"""
		return a duplicate of the current client dc as a buffer
		"""
		x0, y0, w, h = self.GetClientRect()
		retbuf = wx.EmptyBitmap(w, h)
		memdc = wx.MemoryDC()
		memdc.SelectObject(retbuf)
		memdc.Blit(0, 0, w, h, dc, x0, y0)
		return memdc
		
	def actionEnd(self, event):
		"""
		Unconditionally end the current action
		"""	   
		
		self.action = 0
		self.annotationClass = None

		self.actionstart = (0, 0)
		self.actionend = (0, 0)
		
		event.Skip()
		
	def executeAction(self, event):
		"""
		Call the right callback depending on what we're doing
		"""
		self.rubberbandAllowed = 0
		if self.action == ZOOM_TO_BAND:
			self.zoomToRubberband(event)
		elif self.action == ADD_ANNOTATION:
			self.paintPreview()
			x, y = event.GetPosition()
			ex, ey = self.actionstart
			self.addNewAnnotation(self.annotationClass, x, y, ex, ey)
		
			if self.annotationClass == "POLYGON":
				self.actionstart = self.actionend
				self.prevPolyEnd = self.actionend
			else:
				self.action = None
				self.actionstart = (0, 0)
				self.actionend = (0, 0)
				self.prevPolyEnd = None
				return 1
		elif self.action == SET_THRESHOLD:
			self.setThreshold()

		self.action = 0
		self.actionstart = (0, 0)
		self.actionend = (0, 0)
		self.annotationClass = None
		event.Skip()

	def addNewAnnotation(self, annotationClass, x, y, ex, ey, noUpdate = 0, scaleFactor = -1):
		"""
		add an annotaiton of given type
		"""
		if scaleFactor == -1:
			scaleFactor = self.zoomFactor

		x,y = self.getScrolledXY(x, y)
		x,y = int(scaleFactor * x), int(scaleFactor * y)
		ex,ey = self.getScrolledXY(ex, ey)
		ex,ey = int(scaleFactor * ex), int(scaleFactor * ey)

		self.threeDMode = ("3D" in annotationClass)

		if "CIRCLE" in annotationClass:
			if self.threeDMode:
				shape = self.create3DCircle(x, ex, y, ey, scaleFactor, self.dataUnit.getDimensions()[2])
			else:
				shape = self.createCircle(x, ex, y, ey, scaleFactor)

		elif "RECTANGLE" in annotationClass:
			if self.threeDMode:
				shape = self.create3DRectangle(x, ex, y, ey, scaleFactor, self.dataUnit.getDimensions()[2])
			else:
				shape = self.createRectangle(x, ex, y, ey, scaleFactor)

		elif annotationClass == "FINISHED_POLYGON":
			shape = GUI.OGLAnnotations.MyPolygon(zoomFactor = scaleFactor)
			
		elif annotationClass == "POLYGON" or annotationClass == "3D_POLYGON":
			if not self.currentSketch:
				shape = GUI.OGLAnnotations.MyPolygonSketch(zoomFactor = scaleFactor)
				shape.SetCentreResize(0)
				shape.SetX( ex + (x - ex) / 2 )
				shape.SetY( ey + (y - ey) / 2 )
				if self.actionstart != (0, 0):
					shape.AddPoint(self.actionstart)					
				self.currentSketch = shape
			else:
				shape = None
			if self.actionend != (0, 0):					
				self.currentSketch.AddPoint(self.actionend)		 

		elif annotationClass == "SCALEBAR":
			dx = abs(x - ex)
			dy = abs(y - ey)
			shape = GUI.OGLAnnotations.MyScalebar(dx, dy, voxelsize = self.voxelSize, zoomFactor = scaleFactor, color = self.annotationColor)
			shape.SetCentreResize(0)  
			shape.SetX( ex + (x - ex) / 2 )
			shape.SetY( ey + (y - ey) / 2 )

		elif annotationClass == "TEXT":
			dx = abs(x - ex)
			dy = abs(y - ey)
			shape = GUI.OGLAnnotations.MyText(dx, dy, zoomFactor = scaleFactor)
			shape.SetCentreResize(0)  
			shape.SetX( ex + (x - ex) / 2 )
			shape.SetY( ey + (y - ey) / 2 )
		
		if shape:
			# The reason for this is that polygons are handled differently
			# than the other annotations.
			if self.threeDMode and annotationClass != "3D_POLYGON":
				annotations = shape.GetAnnotations()
				for annotation in annotations:
					self.addNewShape(annotation, noUpdate = noUpdate)
			else:
				shape._offset = (self.xoffset, self.yoffset)
				self.addNewShape(shape, noUpdate = noUpdate)

		self.saveAnnotations()
		if not noUpdate:
			lib.messenger.send(None, "update_annotations")
		return shape
		
	def saveAnnotations(self):
		"""
		Save the annotations to the settings
		"""
		annotations = self.diagram.GetShapeList()

		annotations = filter(lambda x:isinstance(x, GUI.OGLAnnotations.OGLAnnotation), annotations)
		annotations = filter(lambda x:not isinstance(x, GUI.OGLAnnotations.MyPolygonSketch), annotations)

		if self.dataUnit:
			for annotation in annotations:
				AnnotationSettings.getInstance().addAnnotation(annotation)
	
	def addNewShape(self, shape, noUpdate = 0):
		"""
		Add a new shape to the canvas
		"""
		evthandler = GUI.OGLAnnotations.MyEvtHandler(self)
		evthandler.SetShape(shape)
		evthandler.SetPreviousHandler(shape.GetEventHandler())
		shape.SetEventHandler(evthandler)
		shape.SetDraggable(True, True)
		shape.SetCanvas(self)
		shape.SetBrush(wx.TRANSPARENT_BRUSH)
		shape.SetPen(wx.Pen(self.annotationColor, 1))

		# Change color for annotation name
		# Unfortunately needs to be done in this not so handy way
		AnnotationSettings.getInstance().addColor(shape.getName(), self.annotationColor)
		shape.SetTextColour(shape.getName())
		
		self.AddShape( shape )
		
		if not noUpdate:
			self.diagram.ShowAll(1)
			self.repaintHelpers()
			self.Refresh()		  
		
	def updateAnnotations(self):
		"""
		Update all the annotations
		"""
		for i in self.diagram.GetShapeList():
			if hasattr(i, "setScaleFactor"):
				i.setScaleFactor(self.zoomFactor)
		
	def markROI(self, roitype):
		"""
		Add a ROI to the panel
		"""
		Logging.info("Adding a %s region of interest" % roitype, kw = "iactivepanel")
		self.action = ADD_ROI
		
	def startRubberband(self):
		"""
		Start rubber band
		"""
		self.action = ZOOM_TO_BAND
		
	def deleteAnnotation(self, ctrl = False):
		"""
		Delete annotations on the scene
		"""
		shapeList = self.diagram.GetShapeList()
		for shape in shapeList:
			if shape.Selected():
				if shape.parent != None:
					parent = shape.parent
					if not ctrl:
						annotations = parent.GetAnnotations()
						for annotation in annotations:
							self.RemoveShape(annotation)
					parent.RemoveAnnotation(shape)
					self.RemoveShape(shape)
					shape.Delete()
					if not ctrl:
						del parent
				else:
					self.RemoveShape(shape)
					shape.Delete()

				AnnotationSettings.getInstance().removeAnnotation(shape)
				self.saveAnnotations()
				self.paintPreview()
				self.Refresh()
			
	def addAnnotation(self, annClass, **kws):
		"""
		Add an annotation to the scene
		"""
		self.action = ADD_ANNOTATION
		self.annotationClass = annClass
		self.annotationColor = kws.get('color', self.annotationColor)
		
	def zoomToRubberband(self, event):
		"""
		Zooms to the rubberband
		"""
		x1, y1 = self.actionstart
		x2, y2 = self.actionend
		Logging.info("Zooming to rubberband defined by (%d,%d),(%d,%d)" % (x1, y1, x2, y2), kw = "iactivepanel")
		
		self.actionstart = (0, 0)
		self.actionend = (0, 0)
		x1, x2 = min(x1, x2), max(x1, x2)
		y1, y2 = min(y1, y2), max(y1, y2)
		
		x1, y1 = self.getScrolledXY(x1, y1)
		x2, y2 = self.getScrolledXY(x2, y2)

		self.setZoomFactor(min(16.0,lib.ImageOperations.getZoomFactor((x2 - x1), (y2 - y1), self.maxClientSizeX, self.maxClientSizeY)))

		scrollX = x1 * self.zoomx
		if x1 > x2 / 2.0:
			scrollX *= self.zoomFactor
		scrollY = y1 * self.zoomy
		if y1 > y2 / 2.0:
			scrollY *= self.zoomFactor
		self.scrollTo = (scrollX, scrollY)
		scripting.visualizer.zoomCombo.SetValue(str(self.zoomFactor*100)+"%")
		self.updatePreview()
		
	def getZoomFactor(self):
		"""
		Return the zoom factor
		"""		   
		return self.zoomFactor
		
	def getScrolledXY(self, x, y):
		"""
		Returns the x and y coordinates moved by the 
					 x and y scroll offset
		"""
		tpl = self.CalcUnscrolledPosition(x, y)
		if self.zoomFactor == 1:
			return tpl
		else:
			return [int(float(x) / self.zoomFactor) for x in tpl]	   
		
	def resetScroll(self):
		"""
		Sets the scrollbars to their initial values
		"""	   
		self.Scroll(0, 0)
		
	def setDataUnit(self, dataUnit):
		"""
		Sets the data unit that is displayed
		"""
		self.dataUnit = dataUnit
		if dataUnit:
			self.voxelSize = dataUnit.getVoxelSize()
			x, y, z = self.dataUnit.getDimensions()
			self.dataDimX, self.dataDimY, self.dataDimZ = x,y,z
		if dataUnit and self.enabled:
			self.buffer = wx.EmptyBitmap(x, y)
			wx.CallAfter(self.readAnnotationsFromCache)

	def enable(self, flag):
		"""
		Enable/Disable updates
		"""
		self.enabled = flag
		
	def readAnnotationsFromCache(self):
		"""
		a method that will read cached annotations and show them after the panel has bee initialized
		"""
		if not self.annotationsEnabled:
			return
		if not self.dataUnit.getDataSource():
			return
		print "Reading annotations from dataunit",self.dataUnit
		cachedSettings, cacheParser = scripting.getSettingsFromCache(self.dataUnit.getFileName() + "_" + self.dataUnit.getName() + "_annotations")

		if cachedSettings:
			self.restoreAnnotations(cachedSettings[0])

	def restoreAnnotations(self, settings):
		"""
		restore annotations from cache
		"""
		annotations = AnnotationSettings.getInstance().getAnnotations()
		keys = annotations.keys()

		for key in keys:
			annotation = annotations[key]
			name, pen, text = annotation.getName(), annotation.GetPen(), annotation.GetTextColour()
			annotation.SetEventHandler(annotation)
			self.addNewShape(annotation, noUpdate = 1)
			annotation.SetCanvas(self)
			annotation.setName(name)
			annotation.SetPen(pen)
			annotation.SetTextColour(text)
			AnnotationSettings.getInstance().updateAnnotation(annotation, annotation)

		self.setOffset(self.xoffset, self.yoffset)
		self.updateAnnotations()

		self.diagram.ShowAll(1)
		self.repaintHelpers()

		self.Refresh()
		
	def OnPaint(self, event):
		"""
		Does the actual blitting of the bitmap
		"""
		scrolledWinDC = 0
		if 1 or self.is_windows or self.is_mac:
			x, y = self.GetViewStart()
			if x or y:
				scrolledWinDC = 1
				dc = wx.PaintDC(self)
				
				self.PrepareDC(dc)
				dc.BeginDrawing()
				x,y, w, h = self.GetClientRect()
				dc.DrawBitmap(self.buffer, x,y, False)

		if not scrolledWinDC:
			
			dc = wx.BufferedPaintDC(self, self.buffer)#,self.buffer)
			
		if scrolledWinDC:
			dc.EndDrawing()
					

	def paintPreview(self, dc):
		"""
		Paints the image to a DC
		"""
		if self.measurementPoints:
			dc.SetPen(wx.Pen(wx.Colour(255,0,0), 1))
			dc.SetBrush(wx.TRANSPARENT_BRUSH)
			for i, (x,y) in enumerate(self.measurementPoints):
				dc.DrawCircle(x,y,4)
				if i>0:
					x0,y0 = self.measurementPoints[i-1]
					dc.DrawLine(x0,y0,x,y)
			
		if self.rubberbandAllowed and (self.action == ZOOM_TO_BAND or self.action == ADD_ANNOTATION):
			xr,yr,wr,hr = self.GetClientRect()
			if self.actionstart and self.actionend:
				x1, y1 = self.actionstart
				x2, y2 = self.actionend
				x1, x2 = min(x1, x2), max(x1, x2)
				y1, y2 = min(y1, y2), max(y1, y2)
				d1, d2 = (x2 - x1, y2 - y1)
	
				if self.zoomFactor != 1:
					f = self.zoomFactor
					x1, y1 = self.getScrolledXY(x1, y1)
					x1, y1 = int(f * x1), int(f * y1)

				dc.SetPen(wx.Pen(wx.Colour(255, 255, 255), 1, wx.DOT))
				dc.SetBrush(wx.TRANSPARENT_BRUSH)

				if self.action == ZOOM_TO_BAND or self.annotationClass == "RECTANGLE" or self.annotationClass == "SCALEBAR":
					dc.DrawRectangle(x1+xr, y1+yr, d1, d2)

				elif self.annotationClass == "CIRCLE":
					rad = max(d1,d2)
					dc.DrawCircle(x1+xr,y1+yr,rad)
		
	def setScrollbars(self, xdim, ydim):
		"""
		Configures scroll bar behavior depending on the
					 size of the dataset, which is given as parameters.
		"""
		Logging.info("Requested size = %d, %d, client size = %d, %d" % (self.maxClientSizeX, self.maxClientSizeY, xdim, ydim), kw = "iactivepanel")

		newx = min(self.maxClientSizeX, xdim)
		newy = min(self.maxClientSizeY, ydim)

		if newx <= self.dataDimX and self.dataDimX <= self.maxClientSizeX:
			newx = self.dataDimX
		if newy <= self.dataDimY and self.dataDimY <= self.maxClientSizeY:
			newy = self.dataDimY
			
		xrate, yrate = 0, 0
		# if the requested size is larger than client size, then we need scrollbars
		if xdim > self.maxClientSizeX:
			xrate = self.scrollStepSize
		if ydim > self.maxClientSizeY:
			yrate = self.scrollStepSize
		self.SetScrollRate(xrate, yrate)
		
		Logging.info("Setting size of preview to ", newx, newy, "virtual size to ", xdim, ydim, kw = "iactivepanel")
		self.SetVirtualSize((xdim, ydim))

	def makeBackgroundBuffer(self, dc):
		"""
		Copy the current buffer to a background buffer that is used 
					 among other things to restore the background after painting
					 over the image (e.g. annotations)
		"""
		w, h = self.buffer.GetWidth(), self.buffer.GetHeight()
		self.bgbuffer = wx.EmptyBitmap(w, h)
		memdc = wx.MemoryDC()
		memdc.SelectObject(self.bgbuffer)
		memdc.Blit(0, 0, w, h, dc, 0, 0)
		memdc.SelectObject(wx.NullBitmap)

	def saveSnapshot(self, filename):
		"""
		Save a snapshot of the scene
		"""
		ext = filename.split(".")[-1].lower()
		if ext == "jpg":
			ext = "jpeg"
		if ext == "tif":
			ext = "tiff"
		mime = "image/%s" % ext
		img = self.buffer.ConvertToImage()
		img.SaveMimeFile(filename, mime)

	def onSetBackgroundToZero(self, event):
		"""
		Set background pixels of ROI to zero
		"""
		if not self.subtractROI: return

		mx, my, mz = self.dataUnit.getDimensions()
		rois = [self.subtractROI]
		n, maskImage = lib.ImageOperations.getMaskFromROIs(rois, mx, my, mz)
		name = self.subtractROI.getName()
		mask = GUI.MaskTray.Mask(name, (mx,my,mz), maskImage)
		scripting.visualizer.setMask(mask)
		self.dataUnit.setMask(mask)
		
		self.updatePreview(1)

	def onMaskSelectionChanged(self, obj, event):
		"""
		Update preview after selecting a mask
		"""
		self.updatePreview(1)
		
