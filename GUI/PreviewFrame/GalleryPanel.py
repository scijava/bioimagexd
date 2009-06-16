# -*- coding: iso-8859-1 -*-

"""
 Unit: GalleryPanel
 Project: BioImageXD
 Created: 23.05.2005, KP
 Description:

 A panel that can display previews of all the optical slices of
 volume data independent of a VTK render window,using the tools provided by wxPython.
 
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

from GUI.InteractivePanel import InteractivePanel as InteractivePanel
import lib.ImageOperations
import lib.messenger
import Logging
import math
import optimize
import scripting
import wx
import vtk

class GalleryPanel(InteractivePanel):
	"""
	A panel that can be used to preview volume data several slice at a time
	"""
	def __init__(self, parent, visualizer, size = (512, 512), **kws):
		"""
		Initialization
		"""
		self.imagedata = None
		self.visualizer = visualizer
		self.bmp = None
		self.bgcolor = (127, 127, 127)
		Logging.info("Size of gallery =", size, kw = "preview")
		self.enabled = 1
		self.slices = []
		self.zoomx = 1
		self.zoomy = 1
		if kws.has_key("slicesize"):
			self.sliceSize = kws["slicesize"]
		else:
			self.sliceSize = (128, 128)
		self.originalSliceSize = self.sliceSize
		
		x, y = size
		self.paintSize = size
		self.reqSize = size
		self.buffer = wx.EmptyBitmap(x, y)
		self.oldBufferDims = None
		self.oldBufferMaxXY = None
		InteractivePanel.__init__(self, parent, size = size, **kws)
		
		self.size = size
		self.sizeChanged = False
		self.rows = 0
		self.cols = 0
		self.scrollsize = 32
		self.scrollTo = None
		self.drawableRects = []
		self.slice = 0
		self.ctf = None
		
		self.interpolation = 0
		
		self.voxelSize = (0, 0, 0)
		self.showTimepoints = 0
		self.timepoint = 0
		self.paintPreview()
		self.Bind(wx.EVT_PAINT, self.OnPaint)
		self.Bind(wx.EVT_SIZE, self.onSize)
		lib.messenger.connect(None, "zslice_changed", self.setPreviewedSlice)
		
	def deregister(self):
		"""
		Delete all known references because this view mode is to be removed
		"""
		lib.messenger.disconnect(None, "zslice_changed", self.setPreviewedSlice)
		InteractivePanel.deregister(self)
		
	def setPreviewedSlice(self, obj, evt, slice):
		"""
		If the panel is showing a slice in each timepoint, set the shown slice
		"""
		if self.showTimepoints:
			self.setShowTimepoints(True, slice)
		
	def setShowTimepoints(self, showtps, slice):
		"""
		Configure whether to show z slices or timepoints
		"""
		self.slice = slice
		self.showTimepoints = showtps
		print "Showing slice ", slice
		self.getTimepointSlicesAt(slice)
		self.updatePreview()
		self.Refresh()
		
	def getDrawableRectangles(self):
		"""
		Return the rectangles can be drawn on as four-tuples
		"""
		return self.drawableRects
		
	def zoomToFit(self):
		"""
		Zoom the dataset to fit the available screen space
		"""
		self.zoomToFitFlag = True
		self.calculateBuffer()
		
	def setZoomFactor(self, factor):
		"""
		Set the factor by which the image is zoomed
		"""
		self.zoomFactor = factor
		self.zoomToFitFlag = False
		self.updateAnnotations()
		x, y = self.originalSliceSize
		x *= factor
		y *= factor
		self.sizeChanged = True
		self.calculateBuffer()

		self.sliceSize = (int(x), int(y))
		self.slices = []
		
		
	def setBackground(self, r, g, b):
		"""
		Set the background color
		"""
		self.bgcolor = (r, g, b)

	def onSize(self, event):
		"""
		Size event handler
		"""
		InteractivePanel.OnSize(self, event)
		self.paintSize = self.GetClientSize()
		self.sizeChanged = True
		if scripting.renderingEnabled:
			self.calculateBuffer()
			self.updatePreview()

	def setDataUnit(self, dataunit):
		"""
		Sets the dataunit to display
		"""
		self.dataUnit = dataunit
		if not dataunit:
			return
		self.dims = dataunit.getDimensions()
		self.voxelSize = dataunit.getVoxelSize()
		InteractivePanel.setDataUnit(self, dataunit)
		tp = self.timepoint
		self.timepoint = -1
		self.setTimepoint(tp)
		x, y = self.paintSize
		#self.setScrollbars(x, y)
		self.calculateBuffer()
		self.updatePreview()
			#self.imagedata=image
		
		
	def setTimepoint(self, timepoint, update = 1):
		"""
		Sets the timepoint to display
		"""
		if self.timepoint == timepoint and self.slices:
			return
		
		self.timepoint = timepoint
		if not scripting.renderingEnabled:
			return
		# if we're showing one slice of each timepointh
		# instead of each slice of one timepoint, call the
		# appropriate function
		if self.showTimepoints:
			return self.getTimepointSlicesAt(self.slice)

		if self.visualizer.getProcessedMode():
			image = self.dataUnit.doPreview(scripting.WHOLE_DATASET_NO_ALPHA, 1, self.timepoint)
			self.ctf = self.dataUnit.getSourceDataUnits()[0].getColorTransferFunction()
#			Logging.info("Using ", image, "for gallery", kw = "preview")
		else:
			image = self.dataUnit.getTimepoint(timepoint)
			self.ctf = self.dataUnit.getColorTransferFunction()

		#self.imagedata = lib.ImageOperations.imageDataTo3Component(image,ctf)
		self.imagedata = image
		self.imagedata.SetUpdateExtent(self.imagedata.GetWholeExtent())
		self.imagedata.Update()
		
		x, y, z = self.dataUnit.getDimensions()
		
		self.slices = []

		for i in range(z):
			image = optimize.optimize(image = self.imagedata, updateExtent = (0, x - 1, 0, y - 1, i, i))
			image = lib.ImageOperations.getSlice(image, i)
			
			lib.messenger.send(None, "update_progress", i / float(z), "Loading slice %d / %d for Gallery view" % (i + 1, z + 1))
			self.slices.append(image)
		
		lib.messenger.send(None, "update_progress", 1.0, "All slices loaded.")  
		self.calculateBuffer()
		if update:
			print "Updating preview"
			self.updatePreview()
			self.Refresh()
			
	def getScaledSlice(self, slice):
		"""
		@param slice The number of the slice to return
		"""
		w, h = self.sliceSize
		try:
			slice = lib.ImageOperations.imageDataTo3Component(self.slices[slice], self.ctf)
			slice.Update()
		except:
			return
		
		x, y, z = slice.GetDimensions()
		factor = lib.ImageOperations.getZoomFactor(x, y, w, h)
		
		if self.interpolation:
			slice = self.zoomImageWithInterpolation(slice, factor, self.interpolation, 0)
		else:
			slice = lib.ImageOperations.vtkImageDataToWxImage(slice)
			slice.Rescale(w, h)
		return slice
		
	def forceUpdate(self):
		"""
		force update of the preview
		"""
		tp = self.timepoint
		self.slices = []
		self.timepoint = -1
		self.setTimepoint(tp)

		
	def getTimepointSlicesAt(self, slice):
		"""
		Sets the slice to show
		"""
		self.slice = slice
		# if we're showing each slice of one timepoint
		# instead of one slice of each timepoint, call the
		# appropriate function
		self.slices = []
		if not self.showTimepoints:
			return self.setTimepoint(self.timepoint)
		
		count = self.dataUnit.getNumberOfTimepoints()
		for tp in range(0, count):
			if self.dataUnit.isProcessed():
				image = self.dataUnit.doPreview(self.slice, 1, tp)
				self.ctf = self.dataUnit.getSourceDataUnits()[0].getColorTransferFunction()
				Logging.info("Using ", image, "for gallery", kw = "preview")
			else:
				image = self.dataUnit.getTimepoint(tp)
				x, y, z = self.dataUnit.getDimensions()
				image = optimize.optimize(image, updateExtent = (0, x - 1, 0, y - 1, self.slice, self.slice))
				image = lib.ImageOperations.getSlice(image, self.slice)
				image.Update()
				self.ctf = self.dataUnit.getColorTransferFunction()
			
			tp = vtk.vtkImageData()
			tp.DeepCopy(image)
			self.slices.append(tp)
			
		self.calculateBuffer()
		self.updatePreview()

	def calculateBuffer(self):
		"""
		Calculate the drawing buffer required
		"""
		if not self.imagedata:
			return

		x, y, z = self.dataUnit.getDimensions()
		
		if not self.sizeChanged and (x, y, z) == self.oldBufferDims and self.oldBufferMaxXY == (self.maxClientSizeX, self.maxClientSizeY):
			return
		
		yfromx = y / float(x)
		maxX = self.maxClientSizeX
		maxY = self.maxClientSizeY

		n = z
		if len(self.slices) > z:
			Logging.info("Using number of slices (%d) instead of z dim (%d)" % (len(self.slices), z), kw = "preview")
			n = len(self.slices)

		self.oldBufferDims = (x, y, z)
		self.oldBufferMaxXY = (maxX, maxY)
		
		if not self.zoomToFitFlag:
			w, h = self.sliceSize
			Logging.info("maxX=", maxX, "maxY=", maxY, kw = "preview")
			xreq = maxX // (w + 6)
			if not xreq:
				xreq = 1
			yreq = math.ceil(n / float(xreq))
		else:
			sizes = range(0, 1024, 8)
			for j in range(len(sizes) - 1, 0, -1):
				i = sizes[j]
				nx = maxX // (i + 6)

				if not nx:continue
				ny = math.ceil(n / float(nx))
				if ny * (i + 6) * yfromx < maxY and (nx * ny) > n:
					w = i
					h = i * yfromx
					self.sliceSize = (w, h)
					xreq = nx
					yreq = ny
					break
				else:
					pass
		Logging.info("Need %d x %d grid to show the dataset" % (xreq, yreq), kw = "preview")
		

		# allow for 3 pixel border
		x = 12 + (xreq) * (w + 6)
		y = 12 + (yreq) * (h + 6)
		
		self.rows = yreq
		self.cols = xreq
		if self.reqSize != (x, y):
			self.reqSize = (x, y)

		x2, y2 = self.paintSize
		if x > x2:
			x2 = x
		if y > y2:
			y2 = y

		self.buffer = wx.EmptyBitmap(x2, y2)
		self.setScrollbars(x2, y2)
		

	def resetScroll(self):
		"""
		Sets the scrollbars to their initial values
		"""
		self.Scroll(0, 0)


	def enable(self, flag):
		"""
		Enable/Disable updates
		"""
		self.enabled = flag
#		if flag:
#			self.updatePreview()

	def updatePreview(self):
		"""
		Updates the viewed image
		"""
		if not self.enabled:
			Logging.info("\n\nWon't draw gallery cause not enabled", kw = "preview")
			return
		if not self.dataUnit:
			return			
		if not self.slices:
			print "Updating slices"
			self.setTimepoint(self.timepoint, update = 0)
		self.paintPreview()
		self.updateScrolling()
		self.Refresh()
		
	def updateScrolling(self, event = None):
		"""
		Updates the scroll settings
		"""
		if self.scrollTo:
			x, y = self.scrollTo
			Logging.info("Scrolling to ", x, y, kw = "preview")
			sx = int(x / self.scrollsize)
			sy = int(y / self.scrollsize)
			#sx=x/self.scrollsize
			#sy=y/self.scrollsize
			self.Scroll(sx, sy)
			self.scrollTo = None

	def OnPaint(self, event):
		"""
		Does the actual blitting of the bitmap
		"""

		InteractivePanel.OnPaint(self, event)
#		dc=wx.BufferedPaintDC(self,self.buffer)#,self.buffer)

	def paintPreview(self):
		"""
		Paints the image to a DC
		"""
		dc = wx.MemoryDC()
		dc.SelectObject(self.buffer)
		dc.BeginDrawing()
		dc.SetBackground(wx.Brush(wx.Colour(*self.bgcolor)))
		dc.SetPen(wx.Pen(wx.Colour(*self.bgcolor), 0))
		dc.SetBrush(wx.Brush(wx.Color(*self.bgcolor)))
		w, h = self.buffer.GetWidth(), self.buffer.GetHeight()
		#dc.DrawRectangle(0,0,self.paintSize[0],self.paintSize[1])
		xs, ys, x1, y1 = self.GetClientRect()
		dc.DrawRectangle(xs, ys, w, h)
		
		if not self.slices:
			Logging.info("Haven't got any slices", kw = "preview")
			self.makeBackgroundBuffer(dc)
			dc.EndDrawing()
			return
		row, col = 0, 0
	
		xs += 9
		ys += 9
		for i,slice in enumerate(self.slices):
			w, h = self.sliceSize
#			slice.Rescale(w, h)
			slice = self.getScaledSlice(i)
			bmp = slice.ConvertToBitmap()
			if bmp.GetWidth()>w:
				print "\n\nTOO WIDE, slice size=",(w,h), "current=",bmp.GetWidth(),bmp.GetHeight()
			if bmp.GetHeight()>h:
				print "\n\nTOOHIGH,  slice size=",(w,h), "current=",bmp.GetWidth(),bmp.GetHeight()

			x = xs + col * (3 + self.sliceSize[0])
			y = xs + row * (3 + self.sliceSize[1])

			
			dc.DrawBitmap(bmp, x, y, False)
			col += 1
			if col >= self.cols:
				col = 0
				row += 1
			# Mark the rectangle as drawable
			x0, x1 = x, x + w
			y0, y1 = y, y + h
			self.drawableRects.append((x0, x1, y0, y1))
		
		y = 9 + (self.rows) * (3 + self.sliceSize[1])
		self.bmp = self.buffer

		self.makeBackgroundBuffer(dc)
		dc.EndDrawing()
	
