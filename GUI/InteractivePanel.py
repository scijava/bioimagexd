# -*- coding: iso-8859-1 -*-

"""
 Unit: InteractivePanel
 Project: BioImageXD
 Created: 24.03.2005, KP
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
import wx.lib.ogl as ogl
import platform
import wx	 

ZOOM_TO_BAND = 1
MANAGE_ANNOTATION = 2
ADD_ANNOTATION = 3
ADD_ROI = 4
SET_THRESHOLD = 5
DELETE_ANNOTATION = 6


class PainterHelper:
	"""
	Created: 06.10.2006, KP
	Description: A base class for adding behaviour to the painting of the previews
				 in a standard way, that can be used for example to implement different
				 kinds of highlighting, annotations etc.
	"""
	def __init__(self, parent):		   
		self.parent = parent
		
		
	def setParent(self, parent):
		"""
		Created: 02.07.2007, KP
		Description: set the parent
		"""		   
		self.parent = parent
	def paintOnDC(self, dc):
		"""
		Created: 06.10.2006, KP
		Description: A method that is used to paint whatever this helper wishes to paint
					 on the DC
		"""
		pass
		
class VisualizeTracksHelper(PainterHelper):
	"""
	Created: 21.11.2006, KP
	Description: A helper for painting the tracks
	"""
	def __init__(self, parent):
		"""
		Created: 21.11.2006, KP
		Description: Initialize the helper
		"""
		PainterHelper.__init__(self, parent)
		self.selectedTracks = []
		lib.messenger.connect(None, "visualize_tracks", self.onShowTracks)		  
		
	def onShowTracks(self, obj, evt, tracks):
		"""
		Created: 25.09.2006, KP
		Description: Show the selected tracks
		"""
		if not tracks:
			return
		self.selectedTracks = tracks
		
				
	def paintOnDC(self, dc):			   
		"""
		Created: 21.11.2006, KP
		Description: Paint the selected tracks to the DC
		"""
		if self.selectedTracks:
			xc, yc, wc, hc = self.parent.GetClientRect()
			dc.SetPen(wx.Pen((255, 255, 255), 1))
			dc.SetBrush(wx.TRANSPARENT_BRUSH)
			for track in self.selectedTracks:
				mintp, maxtp = track.getTimeRange() 
				val = -1
				while val == -1 and mintp <= maxtp:
					val, (x0, y0, z0) = track.getObjectAtTime(mintp)
					x0 *= self.parent.zoomFactor
					y0 *= self.parent.zoomFactor
					x0 += self.parent.xoffset
					y0 += self.parent.yoffset	  
					x0 += xc
					y0 += yc
					mintp += 1
				dc.SetTextForeground((255, 255, 255))
				self.drawTimepoint(dc, mintp - 1, x0, y0)
				
				for i in range(mintp, maxtp + 1):
					objectValue, pos = track.getObjectAtTime(i)
					if objectValue != -1:
						x1, y1, z1 = pos
						
						x1 *= self.parent.zoomFactor
						y1 *= self.parent.zoomFactor
						x1 += self.parent.xoffset
						y1 += self.parent.yoffset				 
						
						x1 += xc
						y1 += yc
						self.drawTimepoint(dc, i, x1, y1)						 
							
						def angle(x_1, y_1, x_2, y_2):
							ang = math.atan2(y_2 - y_1, x_2 - x_1) * 180.0 / math.pi
							ang = math.atan2(y_2 - y_1, x_2 - x_1) * 180.0 / math.pi
							ang2 = ang
							#if ang<0:ang=180+ang
							return ang
							
						if x0 != x1:
							dc.DrawLine(x0, y0, x1, y1)
							a1 = angle(x0, y0, x1, y1)
							if 0:
								ang = ang * ((2 * math.pi) / 360.0)
								#l=5*self.parent.zoomFactor
								xs = 5
								ys = 5
								xs *= self.parent.zoomFactor
								ys *= self.parent.zoomFactor
								x2 = math.cos(ang) * xs - math.sin(ang) * ys
								y2 = math.sin(ang) * xs + math.cos(ang) * ys
								x2 += x0
								y2 += y0
								dc.DrawLine(x0, y0, x2, y2)
								l = 5 * self.parent.zoomFactor
								xs = -5
								ys = 5
								xs *= self.parent.zoomFactor
								ys *= self.parent.zoomFactor								
								x2 = math.cos(ang) * xs - math.sin(ang) * ys
								y2 = math.sin(ang) * xs + math.cos(ang) * ys
								x2 += x0
								y2 += y0
								dc.DrawLine(x0, y0, x2, y2)								   
						
							
						x0, y0 = x1, y1
						
	def drawTimepoint(self, dc, tp, x, y):
		"""
		Created: 26.11.2006, KP
		Description: Draw the text label for given timepoint
		"""
		if tp != scripting.visualizer.getTimepoint():
			dc.SetFont(wx.Font(7, wx.SWISS, wx.NORMAL, wx.NORMAL))
			dc.DrawCircle(x, y, 3)
		else:
			dc.SetFont(wx.Font(9, wx.SWISS, wx.NORMAL, wx.NORMAL))
			dc.DrawCircle(x, y, 5)
		dc.DrawText("%d" % (tp), x - 10, y)
	
class CenterOfMassHelper(PainterHelper):
	def __init__(self, parent):
		"""
		Created: 21.11.2006, KP
		Description: Initialize the helper
		"""
		PainterHelper.__init__(self, parent)
		self.centerOfMass = None
		lib.messenger.connect(None, "show_centerofmass", self.onShowCenterOfMass)
		
	def onShowCenterOfMass(self, obj, evt, label, centerofmass):
		"""
		Created: 04.07.2006, KP
		Description: Show the given center of mass
		"""			   
		self.centerOfMass = (label, centerofmass)
		
		
	def paintOnDC(self, dc):
		"""
		Created: 21.11.2006, KP
		Description: Paint the contents
		"""
		if self.centerOfMass:
			label, (x, y, z) = self.centerOfMass
			
			x *= self.parent.zoomFactor
			y *= self.parent.zoomFactor
			x += self.parent.xoffset
			y += self.parent.yoffset
			x0, y0, w, h = self.parent.GetClientRect()
			x += x0
			y += y0
			dc.SetBrush(wx.TRANSPARENT_BRUSH)
			dc.SetPen(wx.Pen((255, 255, 255), 2))
			dc.DrawCircle(x, y, 10)
			dc.SetTextForeground((255, 255, 255))
			dc.SetFont(wx.Font(9, wx.SWISS, wx.NORMAL, wx.BOLD))
			dc.DrawText("%d" % label, x - 5, y - 5)	   
	
class AnnotationHelper(PainterHelper):
	"""
	Created: 06.10.2006, KP
	Description: A class that capsulates the behaviour of drawing the annotations
	"""
	def __init__(self, parent):
		PainterHelper.__init__(self, parent)
				
	def paintOnDC(self, dc):
		"""
		Created: 06.10.2006, KP
		Description: Paint the annotations on a DC
		"""
		self.parent.diagram.Redraw(dc)
		
		
	def setParent(self, parent):
		"""
		Created: 02.07.2007, KP
		Description: set the parent
		"""		   
		self.parent = parent		

class InteractivePanel(ogl.ShapeCanvas):
	"""
	Created: 03.07.2005, KP
	Description: A panel that can be used to select regions of interest, draw
				 annotations on etc.
	"""
	def __init__(self, parent, **kws):
		"""
		Created: 24.03.2005, KP
		Description: Initialization
		"""	   
		self.annotationsEnabled = 1
		self.parent = parent
		self.is_windows = platform.system() == "Windows"
		self.is_mac = platform.system() == "Darwin"
		self.xoffset = 0
		self.yoffset = 0		
		self.maxX = 512
		self.maxY = 512
		self.currentSketch = None
		self.maxSizeX = 512
		self.maxSizeY = 512
		self.painterHelpers = []
		self.origX = 512
		self.origY = 512
		size = kws.get("size", (512, 512))
		
		self.dataUnit = None
		ogl.OGLInitialize()
		self.listeners = {}
		
		self.annotationClass = None
		
		self.voxelSize = (1, 1, 1) 
		self.bgColor = kws.get("bgColor", (0, 0, 0))
		self.action = 0
		self.imagedata = None
		self.bmp = None
		
		self.actionstart = (0, 0)
		self.actionend = (0, 0)
		self.prevPolyEnd = None
		
		x, y = size
		self.buffer = wx.EmptyBitmap(x, y)
		ogl.ShapeCanvas.__init__(self, parent, -1, size = size)
		
		self.diagram = ogl.Diagram()
		self.SetDiagram(self.diagram)
		self.diagram.SetCanvas(self)
		
		self.size = size
	
		self.lines = []
		
		self.subtractROI = None
		
		self.ID_VARY = wx.NewId()
		self.ID_NONE = wx.NewId()
		self.ID_LINEAR = wx.NewId()
		self.ID_CUBIC = wx.NewId()
		self.interpolation = -1
		self.renew = 1
		self.menu = wx.Menu()
		
		item = wx.MenuItem(self.menu, self.ID_VARY, "Interpolation depends on size", kind = wx.ITEM_RADIO)
		self.menu.AppendItem(item)
		self.menu.Check(self.ID_VARY, 1)
		item = wx.MenuItem(self.menu, self.ID_NONE, "No interpolation", kind = wx.ITEM_RADIO)
		self.menu.AppendItem(item)
		item = wx.MenuItem(self.menu, self.ID_LINEAR, "Linear interpolation", kind = wx.ITEM_RADIO)
		self.menu.AppendItem(item)
		item = wx.MenuItem(self.menu, self.ID_CUBIC, "Cubic interpolation", kind = wx.ITEM_RADIO)
		self.menu.AppendItem(item)
		
		self.subbgMenu = wx.Menu()
		self.ID_SUB_BG = wx.NewId()
		item = wx.MenuItem(self.subbgMenu, self.ID_SUB_BG, "Subtract background")
		self.subbgMenu.AppendItem(item)
		
		self.Bind(wx.EVT_MENU, self.onSetInterpolation, id = self.ID_VARY)
		self.Bind(wx.EVT_MENU, self.onSetInterpolation, id = self.ID_NONE)
		self.Bind(wx.EVT_MENU, self.onSetInterpolation, id = self.ID_LINEAR)
		self.Bind(wx.EVT_MENU, self.onSetInterpolation, id = self.ID_CUBIC)		   
		
		self.Bind(wx.EVT_MENU, self.onSubtractBackground, id = self.ID_SUB_BG)
		
		self.registerPainter( AnnotationHelper(self) )
		self.registerPainter( CenterOfMassHelper(self) )
		self.registerPainter( VisualizeTracksHelper(self) )
		
		self.zoomFactor = 1
		self.addListener(wx.EVT_RIGHT_DOWN, self.onFinishPolygon)
		self.addListener(wx.EVT_RIGHT_DOWN, self.onRightClickROI)
		self.paintPreview()
		
		self.Unbind(wx.EVT_PAINT)
		self.Bind(wx.EVT_PAINT, self.OnPaint)
		

		self.Bind(wx.EVT_LEFT_DOWN, self.markActionStart)
		self.Bind(wx.EVT_MOTION, self.updateActionEnd)
		self.Bind(wx.EVT_RIGHT_DOWN, self.onRightDown)
		self.Bind(wx.EVT_LEFT_UP, self.executeAction)
		self.Bind(wx.EVT_SIZE, self.OnSize)
		
		lib.messenger.connect(None, "update_helpers", self.onUpdateHelpers)
		
	def disableAnnotations(self):
		"""
		Created: 25.07.2007, KP
		Description: disable the annotations
		"""
		self.annotationsEnabled = 0
		
	def onSubtractBackground(self, event):
		"""
		Created: 20.04.2007, KP
		Description: subtract a background using the given ROI
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
		shift, scale = ds.getIntensityScale()
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
		Created: 01.08.2005, KP
		Description: Set the inteprolation method
		"""		 
		eID = event.GetId()
		flags = (1, 0, 0, 0)
		interpolation = -1
		if eID == self.ID_NONE:
			flags = (0, 1, 0, 0)
			interpolation = 0
		elif eID == self.ID_LINEAR:
			flags = (0, 0, 1, 0)
			interpolation = 1
		elif eID == self.ID_CUBIC:
			flags = (0, 0, 0, 1)
			interpolation = 2
		
		self.menu.Check(self.ID_VARY, flags[0])
		self.menu.Check(self.ID_NONE, flags[1])
		self.menu.Check(self.ID_LINEAR, flags[2])
		self.menu.Check(self.ID_CUBIC, flags[3])
		if self.interpolation != interpolation:
			self.interpolation = interpolation
			self.updatePreview()
	
	
	def setOffset(self, x, y):
		"""
		Created: 24.10.2006, KP
		Description: Set the offset of this interactive panel. The offset is variable
					 based on the size of the screen vs. the dataset size.
		"""
#		 assert x>=0,"Offset cannot be negative"
#		 assert y>=0,"Offset cannot be negative"
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
		Created: 24.10.2006, KP
		Description: Return a coordinate from which the offsets have been subtracted
		"""
		if type(args[0]) == types.TupleType:
			return (args[0][0] - self.xoffset, args[0][1] - self.yoffset)
		else:
			return (args[0] - self.xoffset, args[1] - self.yoffset)
		
	def getOffset(self):
		"""
		Created: 24.10.2006, KP
		Description: Return the offset
		"""
		return self.xoffset, self.yoffset
		
	def addListener(self, evt, func):
		"""
		Created: 10.10.2006, KP
		Description: Add a listener to an event
		"""		   
		if not self.listeners.has_key(evt):
			self.listeners [evt] = [func]
		else:
			self.listeners [evt].append(func)

		
	def registerPainter(self, painter):
		"""
		Created: 06.10.2006, KP
		Description: Add a painter helper that will be used to paint on the DC after everything else
		"""
		self.painterHelpers.append(painter)		 
	  
	def onUpdateHelpers(self, obj, evt, update):
		"""
		Created: KP
		Description: a callback for updating the helpers based on messenger messages
		"""
		self.repaintHelpers(update)
		if update:
			self.Refresh()
			
	def repaintHelpers(self, update = 1):
		"""
		Created: 06.10.2006, KP
		Description: Repaint the helpers but nothing else
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
		Created: 04.08.2006
		Description: Return all the regions of interest draw in this panel	  
		"""
		shapelist = self.diagram.GetShapeList()
		rois = []
		for shape in shapelist:
			if isinstance(shape, OGLAnnotation) and shape.isROI():
				rois.append(shape)
		return rois
		
	def roiToMask(self):
		"""
		Created: 20.06.2006, KP
		Description: Convert the selected ROI to mask
		"""
		mx, my, mz = self.dataUnit.getDimensions()
		rois = self.getRegionsOfInterest()
		names = [roi.getName() for roi in rois]
		n, maskImage = lib.ImageOperations.getMaskFromROIs(rois, mx, my, mz)
		
		return maskImage, names
		
		
	def createPolygon(self, points, zoomFactor = -1):
		"""
		Created: 07.05.2006, KP
		Description: Create a polygon
		"""			   
		if zoomFactor == -1:
			zoomFactor = self.zoomFactor
		shape = MyPolygon(zoomFactor = self.zoomFactor)
		shape._offset = (self.xoffset, self.yoffset)		
		
		pts = []
		mx, my = shape.polyCenter(points)
		
		for x, y in points:
			pts.append((((x - mx)), ((y - my))))
		shape.Create(pts)
		shape.SetX(mx)
		shape.SetY(my)
		self.addNewShape(shape)
		
		self.paintPreview()
		self.Refresh()
		
	   

	def OnSize(self, evt):
		"""
		Created: 11.08.2005, KP
		Description: The size evet
		"""			   
		self.maxSizeX, self.maxSizeY = self.parent.GetClientSize()
		evt.Skip()
		
	def setBackgroundColor(self, bg):
		"""
		Created: 04.07.2005, KP
		Description: Sets the background color
		"""	   
		self.bgColor = bg
		
	def getDrawableRectangles(self):
		"""
		Created: 04.07.2005, KP
		Description: Return the rectangles can be drawn on as four-tuples
		"""	   
		a, b, c, d = self.GetClientRect()
		return [(a, c, b, d)]
		
	def onLeftDown(self, event):
		return self.markActionStart(event)

	def onRightClickROI(self, event):
		"""
		Created: 20.04.2007, KP
		Description: a method that checks whether a right click event happens on a ROI
					 and acts upon it
		"""
		x, y = event.GetPosition()
		obj, attach = self.FindShape(x, y)
		if obj and obj.isROI():
			self.subtractROI = obj
			self.PopupMenu(self.subbgMenu, event.GetPosition())
		

	def onRightDown(self, event):
		"""
		Created: 10.10.2006, KP
		Description: An event handler for when the right button is clicked down
		"""
		if wx.EVT_RIGHT_DOWN in self.listeners:
			for method in self.listeners[wx.EVT_RIGHT_DOWN]:
				method(event)
				flag = event.GetSkipped()
				if not flag:
					return
		event.Skip()
		self.PopupMenu(self.menu, event.GetPosition())

	def onFinishPolygon(self, event):
		"""
		Created: 10.10.2006, KP
		Description: Turn the sketch polygon into a real polygon
		"""
		if self.currentSketch:
			pts = self.currentSketch.getPoints()
			self.currentSketch.Delete()
			self.RemoveShape(self.currentSketch)
			del self.currentSketch
			self.currentSketch = None
			self.createPolygon(pts)
			self.repaintHelpers()
			self.Refresh()
			self.action = 0
			self.actionstart = (0, 0)
			self.actionend = (0, 0)
			self.saveAnnotations()
		else:
			event.Skip()
		return 1


	def markActionStart(self, event):
		"""
		Created: 24.03.2005, KP
		Description: Sets the starting position of rubber band for zooming
		"""	   
		event.Skip()
				   
				
		pos = event.GetPosition()

		x, y = pos
		foundDrawable = 0
		for x0, x1, y0, y1 in self.getDrawableRectangles():
			if x >= x0 and x <= x1 and y >= y0 and y <= y1:
				foundDrawable = 1 
				break
		event.Skip()					
		if not foundDrawable:
			Logging.info("Attempt to draw in non-drawable area: %d,%d" % (x, y), kw = "iactivepanel")
			# we zero the action so nothing further will be done by updateActionEnd
			
			self.action = 0
			
			return 1
			
		if self.currentSketch:
			self.currentSketch.AddPoint(pos)			
		self.actionstart = pos
		return 1
		
	def updateActionEnd(self, event):
		"""
		Created: 24.03.2005, KP
		Description: Draws the rubber band to current mou		 
		"""
		if event.LeftIsDown():
			self.actionend = event.GetPosition()
		pos = event.GetPosition()
		if self.currentSketch:
			self.actionend = pos
			x0, y0, w, h = self.GetClientRect()
			
			self.currentSketch.setTentativePoint((pos))
			dc = wx.ClientDC(self)
			self.PrepareDC(dc)
			
			self.currentSketch.Erase(dc)
			 
			self.currentSketch.Draw(dc)			   
			
			dc.EndDrawing()
		event.Skip()

	def onDeactivate(self):
		"""
		Created: 28.05.2007, KP
		Description: event handler called when the visualization mode is about to be deactivated
		"""
		if not self.dataUnit:
			return
		if self.dataUnit and self.dataUnit.getDataSource(): 
			settings = self.dataUnit.getSettings()
			if self.annotationsEnabled:
				self.saveAnnotations()
				scripting.storeSettingsToCache(self.dataUnit.getFileName() + "_" + self.dataUnit.getName() + "_annotations", [settings])
				self.dataUnit.getSettings().set("Annotations", [])
					   
	def getDuplicateDC(self, dc):
		"""
		Created: 04.04.2007, KP
		Description: return a duplicate of the current client dc as a buffer
		"""
		x0, y0, w, h = self.GetClientRect()
		retbuf = wx.EmptyBitmap(w, h)
		memdc = wx.MemoryDC()
		memdc.SelectObject(retbuf)
		memdc.Blit(0, 0, w, h, dc, x0, y0)
		return memdc
		
	def actionEnd(self, event):
		"""
		Created: 05.07.2005, KP
		Description: Unconditionally end the current action
		"""	   
		
		self.action = 0
		self.annotationClass = None

		self.actionstart = (0, 0)
		self.actionend = (0, 0)
		
		event.Skip()
		
	def executeAction(self, event):
		"""
		Created: 03.07.2005, KP
		Description: Call the right callback depending on what we're doing
		"""	   
		if self.action == ZOOM_TO_BAND:
			self.zoomToRubberband(event)
		elif self.action == ADD_ANNOTATION:
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
		elif self.action == DELETE_ANNOTATION:			  
			x, y = self.actionstart
			
			obj, attach = self.FindShape(x, y)
			if obj:
				self.RemoveShape(obj)
				obj.Delete()			
				self.paintPreview()
				self.Refresh()
				
		
		self.action = 0
		self.actionstart = (0, 0)
		self.actionend = (0, 0)
		self.annotationClass = None					   
		event.Skip()


	def addNewAnnotation(self, annotationClass, x, y, ex, ey, noUpdate = 0, scaleFactor = -1):
		"""
		Created: 03.07.2007, KP
		Description: add an annotaiton of given type
		"""
		if scaleFactor == -1:
			scaleFactor = self.zoomFactor
		if annotationClass == "CIRCLE":
			diff = max(abs(x - ex), abs(y - ey))
			if diff < 2:diff = 2
			
			shape = MyCircle(2 * diff, zoomFactor = scaleFactor)
			shape.SetCentreResize(0)
			
			shape.SetX( ex )
			shape.SetY( ey )

		elif annotationClass == "RECTANGLE":
			dx = abs(x - ex)
			dy = abs(y - ey)
			shape = MyRectangle(dx, dy, zoomFactor = scaleFactor)
			shape.SetCentreResize(0)  
			shape.SetX( ex + (x - ex) / 2 )
			shape.SetY( ey + (y - ey) / 2 )
		elif annotationClass == "FINISHED_POLYGON":
			shape = MyPolygon(zoomFactor = scaleFactor)
			
		elif annotationClass == "POLYGON":
			if not self.currentSketch:
				shape = MyPolygonSketch(zoomFactor = scaleFactor)
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
			shape = MyScalebar(dx, dy, voxelsize = self.voxelSize, zoomFactor = scaleFactor)
			shape.SetCentreResize(0)  
			shape.SetX( ex + (x - ex) / 2 )
			shape.SetY( ey + (y - ey) / 2 )
		elif annotationClass == "TEXT":
			dx = abs(x - ex)
			dy = abs(y - ey)
			shape = MyText(dx, dy, zoomFactor = scaleFactor)
			shape.SetCentreResize(0)  
			shape.SetX( ex + (x - ex) / 2 )
			shape.SetY( ey + (y - ey) / 2 )				   
		
		if shape:	 
			shape._offset = (self.xoffset, self.yoffset)		
			self.addNewShape(shape, noUpdate = noUpdate)
			
		self.saveAnnotations()
		if not noUpdate:
			lib.messenger.send(None, "update_annotations")
		return shape
		
	def saveAnnotations(self):
		"""
		Created: 25.10.2006, KP
		Description: Save the annotations to the settings
		"""
		annotations = self.diagram.GetShapeList()
			
		annotations = filter(lambda x:isinstance(x, OGLAnnotation), annotations)
		annotations = filter(lambda x:not isinstance(x, MyPolygonSketch), annotations)
		
		if self.dataUnit:
			self.dataUnit.getSettings().set("Annotations", annotations)
						
	
	def addNewShape(self, shape, noUpdate = 0):
		"""
		Created: 07.05.2005, KP
		Description: Add a new shape to the canvas
		"""		   
		evthandler = MyEvtHandler(self)
		evthandler.SetShape(shape)
		evthandler.SetPreviousHandler(shape.GetEventHandler())
		shape.SetEventHandler(evthandler)
		shape.SetDraggable(True, True)
		shape.SetCanvas(self)
		shape.SetBrush(wx.TRANSPARENT_BRUSH)
		shape.SetPen(wx.Pen((0, 255, 0), 1))
		
		self.AddShape( shape )				   
		
		if not noUpdate:
			self.diagram.ShowAll(1)
			self.repaintHelpers()
			self.Refresh()		  
		
	def updateAnnotations(self):
		"""
		Created: 04.07.2005, KP
		Description: Update all the annotations
		"""
		for i in self.diagram.GetShapeList():
			if hasattr(i, "setScaleFactor"):
				i.setScaleFactor(self.zoomFactor)
		
	def markROI(self, roitype):
		"""
		Created: 05.07.2005
		Description: Add a ROI to the panel
		"""
		Logging.info("Adding a %s region of interest" % roitype, kw = "iactivepanel")
		self.action = ADD_ROI
		
	def startRubberband(self):
		"""
		Created: 03.07.2005
		Description: Start rubber band
		"""
		self.action = ZOOM_TO_BAND
		
	def deleteAnnotation(self):
		"""
		Created: 15.08.2005, KP
		Description: Delete annotations on the scene
		"""
		self.action = DELETE_ANNOTATION		   
		
	def addAnnotation(self, annClass, **kws):
		"""
		Created: 04.07.2005, KP
		Description: Add an annotation to the scene
		"""
		self.action = ADD_ANNOTATION
		self.annotationClass = annClass
		
		
	def zoomToRubberband(self, event):
		"""
		Created: 24.03.2005, KP
		Description: Zooms to the rubberband
		""" 
		x1, y1 = self.actionstart
		x2, y2 = self.actionend
		Logging.info("Zooming to rubberband defined by (%d,%d),(%d,%d)" % (x1, y1, x2, y2), kw = "iactivepanel")
		
		self.actionstart = (0, 0)
		self.actionend = (0, 0)
		x1, x2 = min(x1, x2), max(x1, x2)
		y1, y2 = min(y1, y2), max(y1, y2)
		
		if self.zoomFactor != 1:
			f = float(self.zoomFactor)
			x1, x2, y1, y2 = int(x1 / f), int(x2 / f), int(y1 / f), int(y2 / f)
			x1 /= float(self.zoomx)
			x2 /= float(self.zoomx)
			y1 /= float(self.zoomy)
			y2 /= float(self.zoomy)
			
		
		x1, y1 = self.getScrolledXY(x1, y1)
		x2, y2 = self.getScrolledXY(x2, y2)

		w, h = self.size
		self.setZoomFactor(lib.ImageOperations.getZoomFactor((x2 - x1), (y2 - y1), w, h))
		
		self.scrollTo = (self.zoomFactor * x1 * self.zoomx, self.zoomFactor * y1 * self.zoomy)
		
		self.updatePreview()
		
	def getZoomFactor(self):
		"""
		Created: 1.08.2005, KP
		Description: Return the zoom factor
		"""		   
		return self.zoomFactor
		
	def getScrolledXY(self, x, y):
		"""
		Created: 24.03.2005, KP
		Description: Returns the x and y coordinates moved by the 
					 x and y scroll offset
		"""
		tpl = self.CalcUnscrolledPosition(x, y)
		if self.zoomFactor == 1:
			return tpl
		else:
			return [int(float(x) / self.zoomFactor) for x in tpl]	   
		
	def resetScroll(self):
		"""
		Created: 24.03.2005, KP
		Description: Sets the scrollbars to their initial values
		"""	   
		self.Scroll(0, 0)			 
		
	def setDataUnit(self, dataUnit):
		"""
		Created: 04.07.2005, KP
		Description: Sets the data unit that is displayed
		"""	   
		self.dataUnit = dataUnit
		self.voxelSize = dataUnit.getVoxelSize()
		x, y, z = self.dataUnit.getDimensions()
		self.buffer = wx.EmptyBitmap(x, y)
		self.origX, self.origY = x, y
		wx.CallAfter(self.readAnnotationsFromCache)

	def readAnnotationsFromCache(self):
		"""
		Created: 04.07.2007, KP
		Description: a method that iwll read cached annotations and show them after the panel has bee initialized
		"""
		if not self.annotationsEnabled:
			return
		if not self.dataUnit.getDataSource():		
			return
		cachedSettings, cacheParser = scripting.getSettingsFromCache(self.dataUnit.getFileName() + "_" + self.dataUnit.getName() + "_annotations")

		if cachedSettings:
			self.restoreAnnotations(cachedSettings[0])

	def restoreAnnotations(self, settings):
		"""
		Created: 03.07.2007, KP
		Description: restore annotations from cache
		"""
		annotations = settings.get("Annotations")
				
		for obj in annotations:
			obj.SetEventHandler(obj)
			newobj = self.addNewAnnotation(obj.AnnotationType, 0, 0, 10, 10, noUpdate = 1, scaleFactor = 1)
			newobj.restoreFrom(obj)
			newobj._offset = (0, 0)
		self.setOffset(self.xoffset, self.yoffset)
		self.updateAnnotations()

		self.diagram.ShowAll(1)
		self.repaintHelpers()
		
		self.Refresh()
		
	def OnPaint(self, event):
		"""
		Created: 28.04.2005, KP
		Description: Does the actual blitting of the bitmap
		"""
		scrolledWinDC = 0
		if self.is_windows:
			x, y = self.GetViewStart()
			if x or y:
				scrolledWinDC = 1
				Logging.info("Resorting to unbuffered drawing because of scrolling", kw = "iactivepanel")
				dc = wx.PaintDC(self)
				
				self.PrepareDC(dc)
				dc.BeginDrawing()
				dc.DrawBitmap(self.buffer, 0, 0, False)

		if not scrolledWinDC:
			
			dc = wx.BufferedPaintDC(self, self.buffer)#,self.buffer)
			
		if scrolledWinDC:
			dc.EndDrawing()
					


	def paintPreview(self):
		"""
		Created: 24.03.2005, KP
		Description: Paints the image to a DC
		"""
					 
		dc = self.dc
		bmp = self.bmp
		
		w, h = bmp.GetWidth(), bmp.GetHeight()
		
		w *= self.zoomx
		h *= self.zoomy
		if self.action == ZOOM_TO_BAND:
			if self.actionstart and self.actionend:
				x1, y1 = self.actionstart
				x2, y2 = self.actionend
				x1, x2 = min(x1, x2), max(x1, x2)
				y1, y2 = min(y1, y2), max(y1, y2)
				d1, d2 = abs(x2 - x1), abs(y2 - y1)
	
				if self.zoomFactor != 1:
					f = self.zoomFactor
					x1, y1 = self.getScrolledXY(x1, y1)
					x1, y1 = int(f * x1), int(f * y1)
					
				dc.SetPen(wx.Pen(wx.Colour(255, 0, 0), 2))
				dc.SetBrush(wx.TRANSPARENT_BRUSH)
				dc.DrawRectangle(x1, y1, d1, d2)
		
		
	def setScrollbars(self, xdim, ydim):
		"""
		Created: 24.03.2005, KP
		Description: Configures scroll bar behavior depending on the
					 size of the dataset, which is given as parameters.
		"""
		Logging.info("\n\n*** Setting scrollbars to %d, %d" % (xdim, ydim), kw = "preview")
		w, h = self.buffer.GetWidth(), self.buffer.GetHeight()
		
		maxX = self.maxX
		maxY = self.maxY
		if self.maxSizeX > maxX:maxX = self.maxSizeX
		if self.maxSizeY > maxY:maxY = self.maxSizeY
		Logging.info("maxX=", self.maxX, "maxSizeX=", self.maxSizeX, "xdim=", xdim, "origX=", self.origX, kw = "iactivepanel");
		newy = maxY
		newx = maxX
		if xdim < maxX:
			newx = xdim
		if ydim < maxY:
			newy = ydim
		if newx <= self.origX and self.origX <= self.maxSizeX:
			newx = self.origX
		if newy <= self.origY and self.origY <= self.maxSizeY:
			newy = self.origY
		s = self.GetClientSize()
		Logging.info("Setting size of", self, " to ", newx, newy, "virtual size to ", xdim, ydim, kw = "iactivepanel")
		self.SetClientSize((newx, newy))
		s = self.GetVirtualSize()
		self.SetVirtualSize((xdim, ydim))
		xrate, yrate = 0, 0
		if xdim > newx:
			xrate = self.scrollsize
		if ydim > newy:
			yrate = self.scrollsize
		
		self.SetScrollRate(xrate, yrate)
				
	def makeBackgroundBuffer(self, dc):
		"""
		Created: 06.10.2006, KP
		Description: Copy the current buffer to a background buffer
		"""
		w, h = self.buffer.GetWidth(), self.buffer.GetHeight()
		self.bgbuffer = wx.EmptyBitmap(w, h)
		memdc = wx.MemoryDC()
		memdc.SelectObject(self.bgbuffer)
		memdc.Blit(0, 0, w, h, dc, 0, 0)
		memdc.SelectObject(wx.NullBitmap)
