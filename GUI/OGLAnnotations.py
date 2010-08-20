# -*- coding: iso-8859-1 -*-

"""
 Unit: OGLAnnotations
 Project: BioImageXD
 Created: 10.02.2005, KP
 Description:

 This is a module that contains classes for annotating images using the OGL library
 
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

__author__ = "BioImageXD Project <http://www.bioimagexd.org/>"
__version__ = "$Revision: 1.21 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import wx
import Logging
import wx.lib.ogl as ogl
import lib.messenger
import math
import lib.ImageOperations
import GUI
count = {}

class OGLAnnotation(ogl.Shape):
	"""
	A base class for all OGL based annotations
	"""
	AnnotationType = ""
	def __init__(self, canvas = None, parent = None):
		"""
		initialize the annotation
		"""
		self.parent = parent
		self.eraseRect = None
		ogl.Shape.__init__(self, canvas)
		self._offset = (0,0)
		self._name = ""
		self.attrList = ["_xpos","_ypos","scaleFactor"]

		
	def getCoveredPoints(self):
		"""
		return the points covered by this roi
		"""
		return []

	def unoffset(self, attr, value):
		"""
		unoffset a given attribute
		"""
		if not hasattr(self, "_canvas"):
			return
		canvas = self.GetCanvas()
		if not canvas:
			return
		sf = canvas.getZoomFactor()
		if attr in ["_xpos"]:
			return (value - self._offset[0]) / sf
		elif attr == "_ypos":
			return (value - self._offset[1]) / sf
		elif attr in ["_width", "_height"]:
			return value / sf
		elif attr in ["_points"]:
			pts = []
			for pt in value:
				x, y = pt
				pts.append((x / sf, y / sf))
			return pts
		return value

	def updateEraseRect(self):
		"""
		if the annotation defines a rectangle that needs to be erased upon repaint, update that
		"""
		return

	def setOffset(self, x, y):
		"""
		Set the offset that this annotation has
		"""
		self._offset = (x, y)

	def getOffset(self):
		"""
		return the offset of the annotation
		"""
		return self._offset
		
		
	def OnDrawControlPoints(self, dc):

		dc.SetBrush(wx.BLACK_BRUSH)
		dc.SetPen(wx.BLACK_PEN)

		for control in self._controlPoints:
			control.SetPen(wx.WHITE_PEN)
			control.SetBrush(wx.WHITE_BRUSH)
			control.Draw(dc)
			
	def getAsMaskImage(self):
		"""
		Return a mask image representing this region of interest
		"""
		if not self.isROI():
			return None
		insideMap = {}
		insideMap.update(self.getCoveredPoints())
		insMap = {}
		for x, y in insideMap.keys():
			insMap[(x, y)] = 1
		parent = self.GetCanvas()
		mx, my, mz = parent.dataUnit.getDimensions()
		return lib.ImageOperations.getMaskFromPoints(insMap, mx, my, mz)		
			
	def setName(self, name):
		"""
		Set the name of this annotation
		"""
		self._name = name
		self.ClearText()
		self.SetTextColour("#00ff00")
		lines = name.split("\n")
		for line in lines:
			self.AddText(line)

	def addAttr(self, dicti, attr):
		val = self.__dict__[attr]
		newval = self.unoffset(attr, val)
		dicti[attr] = newval

	def getAttr(self, dicti, attr):
		self.__dict__[attr] = dicti[attr]
		
	def getName(self):
		"""
		return the name of this annotation
		"""
		if not hasattr(self, "_name"):
			self._name = ""
		return self._name
	def isROI(self):
		if not hasattr(self, "_isROI"):
			self._isROI = 0
		return self._isROI
		
		
	def __getstate__(self):
		"""
		Return a dictionary describing this object in such details
					 that it can later be reconstructed based on said dictionary
		"""
		ret = {}
		if "_xpos" not in self.attrList:
			self.attrList.append("_xpos")
			self.attrList.append("_ypos")
			self.attrList.append("scaleFactor")
		for attr in self.attrList:
			self.addAttr(ret, attr)
		ret["attrList"]=self.attrList
		return {self.AnnotationType: ret}

	def restoreFrom(self, annotation):
		"""
		copy attributes of given annotation
		"""
		self.attrList = annotation.__dict__["attrList"]
		for i in self.attrList:
			self.__dict__[i] = annotation.__dict__[i]

	def __setstate__(self, state):
		"""
		Reconstruct state of this object from given dictionary
		"""
		for key in state.get(self.AnnotationType,{}).keys():
			self.getAttr(state[self.AnnotationType], key)

	def GetMaintainAspectRatio(self):
		"""
		Return a flag indicating whether we should maintain aspect ratio.
					 This is changed dynamically based on whether the user is dragging
					 from diagonal or non-diagonal handles
		"""
		if not hasattr(self, "doMaintainAspect"):
			return 0
		return self.doMaintainAspect
			
	def OnSizingDragLeft(self, pt, draw, x, y, keys = 0, attachment = 0):			 
		"""
		A handler for sizing events. This is overriden to manipulate
					 the sizing behaviour so that the diagonal handles always
					  maintain aspect ratio
		"""
		if pt._type == ogl.CONTROL_POINT_DIAGONAL:
			self.doMaintainAspect = 1
		else:
			self.doMaintainAspect = 0
			
		ogl.Shape.OnSizingDragLeft(self, pt, draw, x, y, keys, attachment)

	def fOnErase(self, dc):
		"""
		erase the rectangle
		"""
		bg = self.GetCanvas().bgbuffer
		if not self._visible:
			return

		dc.SetPen(self.GetBackgroundPen())
		dc.SetBrush(self.GetBackgroundBrush())

		srcdc = wx.MemoryDC()
		srcdc.SelectObject(bg)
		x0, y0, w, h = self.GetCanvas().GetClientRect()

		if not self.eraseRect:
			xp, yp = self.GetX(), self.GetY()
			minX, minY = self.GetBoundingBoxMin()
			maxX, maxY = self.GetBoundingBoxMax()

			topLeftX = xp - maxX / 2.0 - 2
			topLeftY = yp - maxY / 2.0 - 2

			penWidth = 0
			if self._pen:
				penWidth = self._pen.GetWidth()

			tox, toy = x0 + topLeftX, y0 + topLeftY
			tox -=	penWidth
			toy -= penWidth

			dc.Blit(tox, toy, maxX + 4 + 2 * penWidth, maxY + 4 + 2 * penWidth, srcdc, tox, toy)
		else:
			x1, y1, x2, y2 = self.eraseRect
			if x1 < 0:
				x1 = 0
			if y1 < 0:
				y1 = 0
			dc.Blit(x1 + x0, y1 + y0, abs(x2 - x1) + 2, abs(y2 - y1) + 2, srcdc, x1 + x0, y1 + y0)
		srcdc.SelectObject(wx.NullBitmap)

class MyText(OGLAnnotation, ogl.TextShape):
	"""
	Created: 05.10.2006, KP
	Description: A text annotation
	"""
	AnnotationType = "TEXT"
	def __init__(self, width, height):
		OGLAnnotation.__init__(self)
		ogl.TextShape.__init__(self, width, height)
		self._isROI = 0

class MyScalebar(OGLAnnotation, ogl.RectangleShape):

	AnnotationType = "SCALEBAR"
	def __init__(self, w, h, voxelsize = (1e-7, 1e-7, 1e-7), zoomFactor = 1.0):
		OGLAnnotation.__init__(self)
		ogl.RectangleShape.__init__(self, w, h)
		self.bgColor = (127, 127, 127)
		self.voxelSize = voxelsize
		self.createSnapToList()
		self.widthMicro = -0
		
		self.oldMaxSize = 0
		self.vertical = 0
		self.scaleFactor = zoomFactor
		lib.messenger.connect(None, "set_voxel_size", self.onSetVoxelSize)
		self.attrList = ["vertical", "voxelSize", "widthMicro", "oldMaxSize", "_width", "_height", "_xpos", "_ypos"]

	def onSetVoxelSize(self, obj, evt, arg):
		"""
		Set the voxel size
		"""
		self.voxelSize = arg

	def setScaleFactor(self, factor):
		"""
		Set the scaling factor in use
		"""	  
		w, h, x, y = self._width, self._height, self.GetX(), self.GetY()

		x -= self._offset[0]
		y -= self._offset[1]

		w /= self.scaleFactor
		h /= self.scaleFactor
		x /= self.scaleFactor
		y /= self.scaleFactor

		self.scaleFactor = factor

		w *= self.scaleFactor
		h *= self.scaleFactor
		x *= self.scaleFactor
		y *= self.scaleFactor		 

		x += self._offset[0]
		y += self._offset[1]

		if self.vertical:
			vx = self.voxelSize[1] * 1000000
			h = int(1 + self.widthMicro / vx)
			h *= self.scaleFactor
			print "Keeping microwidth constant, size now", h
		else:
			vx = self.voxelSize[0] * 1000000
			w = int(1 + self.widthMicro / vx)
			w *= self.scaleFactor
			print "Keeping microwidth constant, size now", w
		
		self.SetWidth(w)
		self.SetHeight(h)
		self.SetX(x)
		self.SetY(y)
		self.ResetControlPoints()
		
	def createSnapToList(self):
		"""
		Create the list of micrometer lengths to snap to
		"""	  
		self.snapToMicro = [0.5, 1.0, 2.0, 5.0, 7.5, 10.0, 12.5, 15.0, 17.5]
		for i in range(40, 10000, 5):
			i /= 2.0
			self.snapToMicro.append(float(i))
		self.snapToMicro.sort()
		
		
	def snapToRoundLength(self):
		"""
		Snap the length in pixels to a round number of micrometers
		"""	  
		vx = self.voxelSize[0]
		vx *= 1000000
	   
		maxsize = self._width
		if self.vertical:
			maxsize = self._height
		absMaxSize = maxsize
		maxsize /= self.scaleFactor
		#print "absMaxSize=",absMaxSize,"oldmaxsize=",self.oldMaxSize
		if maxsize and absMaxSize != self.oldMaxSize:
			self.widthMicro = maxsize * vx
			#print "width in micro=",self.widthMicro
			if int(self.widthMicro) != self.widthMicro and self.widthMicro not in self.snapToMicro:
				for i, micro in enumerate(self.snapToMicro[:-1]):
					
					if micro <= self.widthMicro and (self.snapToMicro[i + 1] - self.widthMicro) > 1e-6:
						#print "micro=",micro,"<",self.widthMicro,"next=",self.snapToMicro[i+1],">",self.widthMicro
						Logging.info("Pixel width %.4f equals %.4f um. Snapped to %.4fum (%.5fpx)" % (maxsize, self.widthMicro, micro, micro / vx), kw = "annotation")
						self.widthMicro = micro
						#print "set widthMicro to=",self.widthMicro

				# when we set widthPx to 0 it will be recalculated below
				maxsize = 0
			#else:
				#print "An integer width micro",self.widthMicro,"is ok"
				
		else:
			return
				
		if self.widthMicro and not maxsize:
			w = self.widthMicro / vx
			w *= self.scaleFactor
			

			if self.vertical:
				#print "Setting height to",w
				self.SetHeight(int(w))
			else:
				#print "Setting width to",w
				self.SetWidth(int(w))
			self.oldMaxSize = int(w)
			#print "widthmicro at end=",self.widthMicro
			#Logging.info("%f micrometers is %f pixels"%(self.widthMicro,self.widthPx),kw="annotation")
			#self.widthPx=int(self.widthPx)
			
		
	def OnDraw(self, dc):
		#print "OnDraw"
		x1 = self._xpos - self._width / 2.0
		y1 = self._ypos - self._height / 2.0
		
		x0, y0, w, h = self.GetCanvas().GetClientRect()
		x1 += x0
		y1 += y0
		
		
		if self._width < self._height:
			self.vertical = 1
		else:
			self.vertical = 0
		
		self.snapToRoundLength()
		#print "widthMicro now=",self.widthMicro

		bg = self.bgColor
		vx = self.voxelSize[0]
		vx *= 1000000
		#print "voxelsizes=",self.voxelSize
		#Logging.info("voxel width=%d, scale=%f, scaled %.4f"%(vx,self.scaleFactor,vx/self.scaleFactor),kw="annotation")
		# as the widths and positions are already scaled back, 
		# we don't need to scale the voxel size
		#vx/=float(self.scaleFactor)
 
		if not self.vertical:
			self.SetHeight(32)
		else:
			self.SetWidth(32)
			
		#widthPx*=self.scaleFactor
		#heightPx*=self.scaleFactor
		
		# Set the font for the label and calculate the extent
		# so we know if we need to create a bitmap larger than 
		# the width of the scalebar
		if not self.vertical:
			dc.SetFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.NORMAL))
		else:
			dc.SetFont(wx.Font(9, wx.SWISS, wx.NORMAL, wx.NORMAL))
		#print "widthMicro=",self.widthMicro
		if int(self.widthMicro) == self.widthMicro:
			text = u"%d\u03bcm" % self.widthMicro
		else:
			text = u"%.2f\u03bcm" % self.widthMicro
		w, h = dc.GetTextExtent(text)
			
		bmpw = self._width
		bmph = self._height
		if w > bmpw:
			bmpw = w
		if h > bmph:
			bmph = h
		#bmp = wx.EmptyBitmap(bmpw,bmph)
		
		#dc.SelectObject(bmp)
		#dc.BeginDrawing()
		dc.SetBackground(wx.Brush(bg))
		dc.SetBrush(wx.Brush(bg))
		dc.SetPen(wx.Pen(bg, 1))
		#dc.DrawRectangle(x1+0,y1+0,x1+bmpw,y1+bmph)
		
		dc.SetPen(wx.Pen((255, 255, 255), 2))
		if not self.vertical:
			dc.DrawLine(x1, y1 + 6, x1 + self._width, y1 + 6)
			dc.DrawLine(x1 + 1, y1 + 3, x1 + 1, y1 + 9)
			dc.DrawLine(x1 + self._width - 1, y1 + 3, x1 + self._width - 1, y1 + 9)
		else:
			dc.DrawLine(x1 + 6, y1, x1 + 6, y1 + self._height)
			dc.DrawLine(x1 + 3, y1 + 1, x1 + 9, y1 + 1)
			dc.DrawLine(x1 + 3, y1 + self._height - 1, x1 + 9, y1 + self._height - 1)
			
		dc.SetTextForeground((255, 255, 255))
		if not self.vertical:
			x = bmpw / 2
			x -= (w / 2)
			dc.DrawText(text, x1 + x, y1 + 12)
		else:
			y = bmph / 2
			y += (w / 2)
			dc.DrawRotatedText(text, x1 + 12, y + y1, 90)
			
class MyPolygonSketch(OGLAnnotation, ogl.Shape):

	AnnotationType = "POLYGONSKETCH"
	def __init__(self, zoomFactor = 1.0):
		"""
		Initialization
		"""
		ogl.Shape.__init__(self)
		OGLAnnotation.__init__(self)
		self.scaleFactor = zoomFactor
		self._isROI = 1
		global count
		if not self.__class__ in count:
			count[self.__class__] = 1
		self.setName("Polygon #%d" % count[self.__class__])
		count[self.__class__] += 1
		self.points = []
		self.tentativePoint = None
		self.minx, self.maxx, self.miny, self.maxy = 9900, 0, 9900, 0

	def GetBoundingBoxMin(self):
		"""
		return the minimal bounding box
		"""
		x0, y0, x1, y1 = self.getTentativeBB()
		return (x1 - x0), (y1 - y0)

	def getTentativeBB(self):
		"""
		Return the BB that this polygon currently occupies
		"""
		return self.minx, self.miny, self.maxx, self.maxy
		
	def getPoints(self):
		#print "Points in polygon=",self.points
		return self.points
	
	
	def setTentativePoint(self, pt):
		self.tentativePoint = pt
		x, y = pt
		self.minx = min(self.minx, x)
		self.miny = min(self.miny, y)
		self.maxx = max(self.maxx, x)
		self.maxy = max(self.maxy, y)

	def AddPoint(self, pt):
		if pt in self.points:
			return
		self.points.append(pt)
		x, y = pt
		self.minx = min(self.minx, x)
		self.miny = min(self.miny, y)
		self.maxx = max(self.maxx, x)
		self.maxy = max(self.maxy, y)

	def OnDraw(self, dc):
		"""
		draw the sketch of the polygon
		"""
		n = len(self.points)
		if self.tentativePoint:
			n += 1
		if n < 2:
			return

		brush = wx.TRANSPARENT_BRUSH
		dc.SetBrush(brush)
		pen = wx.Pen(wx.Colour(255, 0, 0), 1)
		dc.SetPen(pen)
		
		
		pts = self.points[:]
		if self.tentativePoint:
			pts.append(self.tentativePoint)
			
		x0, y0, w, h = self.GetCanvas().GetClientRect()
		dc.DrawPolygon(pts, x0, y0)
		self.eraseRect = self.getTentativeBB()
		del pts

	def setScaleFactor(self, factor):
		"""
		Set the scaling factor in use
		"""	  
		pass

class MyRectangle(OGLAnnotation, ogl.RectangleShape):	

	AnnotationType = "RECTANGLE"
	def __init__(self, w, h, zoomFactor = 1.0):
		"""
		Initialization
		"""
		OGLAnnotation.__init__(self)
		ogl.RectangleShape.__init__(self, w, h)
		self.scaleFactor = zoomFactor
		self._isROI = 1
		global count
		if not self.__class__ in count:
			count[self.__class__] = 1
		self.setName("Rectangle #%d" % count[self.__class__])
		count[self.__class__] += 1
		self.attrList = ["_width", "_height", "_xpos", "_ypos"]

	def setScaleFactor(self, factor):
		"""
		Set the scaling factor in use
		"""	  
		w, h, x, y = self._width, self._height, self.GetX(), self.GetY()

		x -= self._offset[0]
		y -= self._offset[1]

		w /= self.scaleFactor
		h /= self.scaleFactor
		x /= self.scaleFactor
		y /= self.scaleFactor

		self.scaleFactor = factor

		w *= self.scaleFactor
		h *= self.scaleFactor
		x *= self.scaleFactor
		y *= self.scaleFactor		 

		x += self._offset[0]
		y += self._offset[1]
		
		self.SetWidth(w)
		self.SetHeight(h)
		self.SetX(x)
		self.SetY(y)	
		self.ResetControlPoints()

	def getCoveredPoints(self):
		cx, cy = self.GetX(), self.GetY()
		ox, oy = self.GetCanvas().getOffset()
		cx -= ox
		cy -= oy
		w, h = self._width, self._height
		cx /= self.scaleFactor
		cy /= self.scaleFactor
		w /= self.scaleFactor
		h /= self.scaleFactor
		pts = {}
		w /= 2.0
		h /= 2.0
		fromx = int(math.ceil(cx - w))
		tox = int(math.floor(cx + w))
		fromy = int(math.ceil(cy - h))
		toy = int(math.floor(cy + h))
		for x in range(fromx, tox):
			for y in range(fromy, toy):
				pts[(x, y)] = 1
		return pts

class MyCircle(OGLAnnotation, ogl.CircleShape):

	AnnotationType = "CIRCLE"
	def __init__(self, diam, zoomFactor = 1.0):
		"""
		Initialization
		"""
		OGLAnnotation.__init__(self)
		ogl.CircleShape.__init__(self, diam)
		self.scaleFactor = zoomFactor
		self._isROI = 1
		global count
		if not self.__class__ in count:
			count[self.__class__] = 1
		self.setName("Circle #%d" % count[self.__class__])
		count[self.__class__] += 1
		self.attrList = ["_width", "_height", "_xpos", "_ypos"]
		
	def setScaleFactor(self, factor):
		"""
		Set the scaling factor in use
		"""	  
		w, h, x, y = self._width, self._height, self.GetX(), self.GetY()

		x -= self._offset[0]
		y -= self._offset[1]

		w /= self.scaleFactor
		h /= self.scaleFactor
		x /= self.scaleFactor
		y /= self.scaleFactor

		self.scaleFactor = factor

		w *= self.scaleFactor
		h *= self.scaleFactor
		x *= self.scaleFactor
		y *= self.scaleFactor		 

		x += self._offset[0]
		y += self._offset[1]
		
		self.SetWidth(w)
		self.SetHeight(h)
		self.SetX(x)
		self.SetY(y)	
		self.ResetControlPoints()		 

	def getCoveredPoints(self):
		cx, cy = self.GetX(), self.GetY()
		ox, oy = self.GetCanvas().getOffset()
		cx -= ox
		cy -= oy		

		cx //= self.scaleFactor
		cy //= self.scaleFactor
		
		w = self._width
		h = self._height
		w //= self.scaleFactor
		h //= self.scaleFactor
		
		a = max(w, h) / 2
		b = min(w, h) / 2
		
		c = math.sqrt(a ** 2 - b ** 2)
		if w > h:
			f1 = (cx - c, cy)
			f2 = (cx + c, cy)
		else:
			f1 = (cx, cy - c)
			f2 = (cx, cy + c)
			

		pts = {}
		def d(x, y):
			return math.sqrt((x[0] - y[0]) ** 2 + ((x[1] - y[1]) ** 2))
		for x in range(int(cx - w // 2), int(cx + w // 2)):
			for y in range(int(cy - h // 2), int(cy + h // 2)):
#				print "d=",(d((x,y),f1)+d((x,y),f2)),"2a=",2*a
				if (d((x, y), f1) + d((x, y), f2)) < a * 2:
					pts[(x, y)] = 1
		return pts

	def OnErasefoo(self, dc):
		bg = self.GetCanvas().bgbuffer
		if not self._visible:
			return

		xp, yp = self.GetX(), self.GetY()
		minX, minY = self.GetBoundingBoxMin()
		maxX, maxY = self.GetBoundingBoxMax()

		topLeftX = xp - maxX / 2.0 - 2
		topLeftY = yp - maxY / 2.0 - 2

		penWidth = 0
		if self._pen:
			penWidth = self._pen.GetWidth()

		
#		 dc.SetPen(wx.Pen(wx.Colour((255,0,0)),2))
#		 dc.DrawLine(1,1,500,1)
		
		dc.SetPen(self.GetBackgroundPen())
		dc.SetBrush(self.GetBackgroundBrush())

		x0, y0, w, h = self.GetCanvas().GetClientRect()
		
		cx0, cy0, cx1, cy1 = (x0 + topLeftX - penWidth, y0 + topLeftY - penWidth, x0 + maxX + penWidth * 2 + 4, y0 + maxY + penWidth * 2 + 4)
		
		if cy0 < 0:
			cy0 = 0
		if cx0 < 0:
			cx0 = 0
#		if cx0<x0:
#			cx0=x0
#		if cy0<y0:
#			cy0=y0
#		if cx1<x0:
#			cx1=x0
#		if cy1<y0:
#			cy1=y0
		dc.SetClippingRegion(cx0, cy0, cx1, cy1)
		
		memdc = wx.MemoryDC()
		memdc.SelectObject(bg)
		dc.Blit(cx0, cy0, abs(cx1 - cx0), abs(cy1 - cy0), memdc, cx0, cy0)
		memdc.SelectObject(wx.NullBitmap)
#		 dc.DrawBitmap(bg,0,0)
		   
		img = bg.ConvertToImage()
		dc.DestroyClippingRegion()

class MyPolygon(OGLAnnotation, ogl.PolygonShape):	 

	AnnotationType = "FINISHED_POLYGON"
	def __init__(self, zoomFactor = 1.0, sliceNumber = -1, parent = None):
		"""
		Initialization
		"""
		self.attrList = ["_points", "_xpos", "_ypos"]
		OGLAnnotation.__init__(self, parent)
		ogl.PolygonShape.__init__(self)
		self._isROI = 1
		self.scaleFactor = zoomFactor
		self.sliceNumber = sliceNumber
		self.parent = parent
		global count
		if self.parent != None:
			self.name = "3D Polygon #%d" % count[self.parent.__class__]
		else:
			if not self.__class__ in count:
				count[self.__class__] = 1
			else:
				count[self.__class__] += 1
			self.name = "Polygon #%d" % count[self.__class__]
		self.setName(self.name)

	def OnDraw(self, dc):
		"""
		method for drawing the object
		"""
		self.setName(self.name)
		self.Recentre(dc)
		ogl.PolygonShape.OnDraw(self, dc)

	def restoreFrom(self, annotation):
		"""
		copy attributes of given annotation
		"""
		self.ClearPoints()
		OGLAnnotation.restoreFrom(self, annotation)
		points = []
		pts = []
		x0, y0 = self._xpos, self._ypos
		for x, y in self._points:
			points.append((x + x0, y + y0))

		mx, my = self.polyCenter(points)

		for x, y in points:
			pts.append((((x - mx)), ((y - my))))
		self.Create(pts)
		self.SetX(mx)
		self.SetY(my)
#		self.CalculatePolygonCentre()
		self.CalculateBoundingBox()

	def __setstate__(self, state):
		"""
		Reconstruct state of this object from given dictionary
		"""
		OGLAnnotation.__setstate__(self, state)
#		self._originalPoints = self._points[:]

	def polyCenter(self, points):
		"""
		Calculte the center of mass of polygon
		"""			 
		A = 0
		for i, pt in enumerate(points[:-1]):
			
			x, y = pt
			A += (x * points[i + 1][1] - points[i + 1][0] * y)
		A /= 2.0
		
		cx = 0
		cy = 0
		
		for i, pt in enumerate(points[:-1]):
			x, y = pt
			cx += (x + points[i + 1][0]) * (x * points[i + 1][1] - points[i + 1][0] * y)
			cy += (y + points[i + 1][1]) * (x * points[i + 1][1] - points[i + 1][0] * y)
		cx /= 6.0 * A
		cy /= 6.0 * A
		return (cx, cy)
		
		
	def setScaleFactor(self, factor):
		"""
		Set the scaling factor in use
		"""	  
		pts = []
		
		for x, y in self._points:
			x /= self.scaleFactor
			y /= self.scaleFactor
			x *= factor
			y *= factor
			pts.append((x, y))
		self._points = pts

		x, y = self.GetX(), self.GetY()
		x -= self._offset[0]
		y -= self._offset[1]
		x /= self.scaleFactor
		y /= self.scaleFactor
		x *= factor
		y *= factor
		x += self._offset[0]
		y += self._offset[1]

		self.SetX(x)
		self.SetY(y)
		self.UpdateOriginalPoints()
		self.scaleFactor = factor
		self.ResetControlPoints()

		self.CalculateBoundingBox()
		self.updateEraseRect()

	def updateEraseRect(self):
		"""
		update the erase rect of this polygon
		"""
		x0, y0, x1, y1 = self.getMinMaxXY()
		x0 += self._xpos
		y0 += self._ypos
		x1 += self._xpos
		y1 += self._ypos
		self.eraseRect = (x0, y0, x1, y1)
		self.UpdateOriginalPoints()
		self.CalculateBoundingBox()

	def getMinMaxXY(self):
		my, mx = 10000, 10000
		Mx, My = 0, 0
		for x, y in self._points:
			if x < mx:
				mx = x
			if y < my:
				my = y
			if x > Mx:
				Mx = x
			if y > My:
				My = y
		return mx, my, Mx, My

	def getCoveredPoints(self):
		x0, y0, x1, y1 = self.getMinMaxXY()
		pts = {}
		cx, cy = self.GetX(), self.GetY()
		ox, oy = self.GetCanvas().getOffset()
		cx -= ox
		cy -= oy		
		x0 += cx
		y0 += cy
		x1 += cx
		y1 += cy
		x0 //= self.scaleFactor
		y0 //= self.scaleFactor
		x1 //= self.scaleFactor
		y1 //= self.scaleFactor
		cx //= self.scaleFactor
		cy //= self.scaleFactor
		
		poly = [(x // self.scaleFactor, y // self.scaleFactor) for x, y in self._points] 
		#poly = self._points
		#tot = (x1-x0)*(y1-y0)
		for x in range(x0, x1):
			for y in range(y0, y1):
				if self.collidepoint(poly, (x, y), cx, cy):
					pts[(x, y)] = 1
				
		return pts

	def collidepoint(self, poly, point, cx, cy):
		"""collidepoint(point) -> Whether the point is inside this polygon"""
		i, j, c = 0, 0, 0
		#poly=self._points
		
		x, y = point
		x -= cx
		y -= cy
		l = len(poly)
		for i in range(0, l):
			j += 1
			if j == l:j = 0
			if (((poly[i][1] <= y) and (y < poly[j][1])) or\
			((poly[j][1] <= y) and (y < poly[i][1]))) and\
			(x < (poly[j][0] - poly[i][0]) * (y - poly[i][1]) / (poly[j][1] - poly[i][1]) + poly[i][0]):
				c = not c
		return c

	# Make as many control points as there are vertices
	def MakeControlPoints(self):
		if not hasattr(self, "_canvas"):
			return
		for point in self._points:
			control = MyPolygonControlPoint(self._canvas, self, ogl.CONTROL_POINT_SIZE, point, point[0], point[1])
			self._canvas.AddShape(control)
			self._controlPoints.append(control)
			
	def SetPointsFromControl(self, pt, end = 0):
		dc = wx.ClientDC(self.GetCanvas())
		self.GetCanvas().PrepareDC(dc)
		
		x0, y0, w, h = self.GetCanvas().GetClientRect()
		
		self.Erase(dc)
		
		for i, control in enumerate(self._controlPoints):
			self._points[i] = wx.RealPoint(control.GetX() - self._xpos, control.GetY() - self._ypos)
			self._originalPoints[i] = wx.RealPoint(control.GetX() - self._xpos, control.GetY() - self._ypos)
		self.CalculatePolygonCentre()
		self.CalculateBoundingBox()
		
		
		dc.SetLogicalFunction(ogl.OGLRBLF)

		dottedPen = wx.Pen(wx.Colour(0, 0, 0), 1, wx.DOT)
		dc.SetPen(dottedPen)
		dc.SetBrush(wx.TRANSPARENT_BRUSH)

		self.updateEraseRect()

		if not end:
			self.GetEventHandler().OnDrawOutline(dc, self.GetX(), self.GetY(), self._originalWidth, self._originalHeight)
		else:
			self.GetEventHandler().OnDraw(dc, self.GetX(), self.GetY())
			
		dc.DrawBitmap(self.GetCanvas().buffer, x0, y0)
		self.UpdateOriginalPoints()

class My3DAnnotation():
	"""
	Parent class for all 3D annotations.
	"""
	AnnotationType = "3D_ANNOTATION"
	def __init__(self, annotations = []):
		"""
		Initialization
		"""
		self.annotations = annotations

	def AddAnnotation(self, annotation):
		print "ADD ANNOTATION:", self
		self.annotations.append(annotation)

	def GetAnnotations(self):
		return self.annotations

class My3DPolygon(My3DAnnotation):
	"""
	3D polygon. A list containing MyPolygon objects.
	"""
	AnnotationType = "3D_POLYGON"
	def __init__(self, polygons = []):
		"""
		Initialization
		"""
		My3DAnnotation.__init__(self, polygons)
		global count
		if not self.__class__ in count:
			count[self.__class__] = 1
		else:
			count[self.__class__] += 1

class MyPolygonControlPoint(ogl.PolygonControlPoint):

	AnnotationType = "POLYGONCONTROLPOINT"
	# Implement resizing polygon or moving the vertex
	def OnDragLeft(self, draw, x, y, keys = 0, attachment = 0):
		#self._shape.GetEventHandler().OnSizingDragLeft(self, draw, x, y, keys, attachment)
		#self.CalculateNewSize(x,y)
		self.SetX(x)
		self.SetY(y)
		#print "Setting x,y to",x,y
		self._shape.SetPointsFromControl(self)
		self._shape.updateEraseRect()

	def OnSizingDragLeft(self, pt, x, y, keys, attch):
		"""
		an event handler for when the polygon is resized
		"""
		ogl.PolygonControlPoint.OnSizingDragLeft(self, pt, x, y, keys, attch)
		self._shape.SetPointsFromControl(self)
		self._shape.updateEraseRect()

	def OnEndSizingDragLeft(self, pt, x, y, keys, attch):
		"""
		an event handler for when the polygon is resized
		"""
		ogl.PolygonControlPoint.OnSizingDragLeft(self, pt, x, y, keys, attch)
		self._shape.SetPointsFromControl(self)
		self._shape.ResetControlPoints()
		self._shape.updateEraseRect()
		self.GetCanvas().repaintHelpers()
		self.GetCanvas().Refresh()

	def OnBeginDragLeft(self, x, y, keys = 0, attachment = 0):
		#self._shape.GetEventHandler().OnSizingBeginDragLeft(self, x, y, keys, attachment)
		
		self.SetX(x)
		self.SetY(y)
		self._shape.SetPointsFromControl(self) 
		self._shape.updateEraseRect()

	def OnEndDragLeft(self, x, y, keys = 0, attachment = 0):
		#self._shape.GetEventHandler().OnSizingEndDragLeft(self, x, y, keys, attachment)
		self._shape.SetPointsFromControl(self)
		self._shape.ResetControlPoints()
		self._shape.updateEraseRect()
		self.GetCanvas().repaintHelpers()
		self.GetCanvas().Refresh()

class MyEvtHandler(ogl.ShapeEvtHandler):
	"""
	the event handler for the OGL based annotations
	"""
	def __init__(self, parent):
		self.parent = parent
		ogl.ShapeEvtHandler.__init__(self)

	def SetParent(self, parent):
		"""
		set the parent of the shape this handler works with
		"""
		self.parent = parent

	def OnLeftDoubleClick(self, x, y, keys = 0, attachment = 0):
		
		shape = self.GetShape()
		flag = 1
		if hasattr(shape, "OnDoubleClick"):
			flag = shape.OnDoubleClick(x, y)
			
		if flag and shape.isROI():
			dlg = wx.TextEntryDialog(self.parent,
					'What is the name of this Region of Interest',
					'Name of the Region of Interest', shape.getName())
	
			dlg.SetValue(shape.getName())
	
			if dlg.ShowModal() == wx.ID_OK:
				value = dlg.GetValue()
				shape.setName(value)
				self.parent.repaintHelpers()
				self.parent.Refresh()
			dlg.Destroy()		 

	def OnLeftClick(self, x, y, keys = 0, attachment = 0):
		shape = self.GetShape()
		#canvas = shape.GetCanvas()
		canvas = self.parent
		dc = wx.ClientDC(canvas)
		canvas.PrepareDC(dc)
		x0, y0, w, h = canvas.GetClientRect()
		if shape.Selected():
			shape.Select(False, dc)
			
			#self.parent.diagram.Redraw(dc)
		else:
			redraw = False
			shapeList = canvas.GetDiagram().GetShapeList()
			toUnselect = []

			for s in shapeList:
				if s.Selected():
					# If we unselect it now then some of the objects in
					# shapeList will become invalid (the control points are
					# shapes too!) and bad things will happen...
					toUnselect.append(s)

			shape.Select(True, dc)

			if toUnselect:
				for s in toUnselect:
					s.Select(False, dc)
				
			#self.parent.paintPreview(dc)
				#self.parent.diagram.Redraw(dc)
		
		self.parent.repaintHelpers()
		self.parent.Refresh()
		
	def OnDragLeft(self, draw, x, y, keys = 0, attachment = 0):
		ogl.ShapeEvtHandler.OnDragLeft(self, draw, x, y, keys, attachment)
	
		self.parent.repaintHelpers()

	def OnEndDragLeft(self, x, y, keys = 0, attachment = 0):
		shape = self.GetShape()
		ogl.ShapeEvtHandler.OnEndDragLeft(self, x, y, keys, attachment)

		if not shape.Selected():
			self.OnLeftClick(x, y, keys, attachment)
		self.GetShape().updateEraseRect()
		self.parent.repaintHelpers()
		self.parent.Refresh()
	def OnSizingEndDragLeft(self, pt, x, y, keys, attch):
		ogl.ShapeEvtHandler.OnSizingEndDragLeft(self, pt, x, y, keys, attch)
		
		#self.parent.paintPreview()
		self.parent.repaintHelpers()
		self.parent.Refresh()
	def OnMovePost(self, dc, x, y, oldX, oldY, display):
		ogl.ShapeEvtHandler.OnMovePost(self, dc, x, y, oldX, oldY, display)

#		self.parent.paintPreview()
#		self.parent.Refresh()

	def OnRightClick(self, *args):
		shape = self.GetShape()
		if hasattr(shape, "OnRightClick"):
			shape.OnRightClick(*args)

