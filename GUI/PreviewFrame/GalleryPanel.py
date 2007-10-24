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

class GalleryPanel(InteractivePanel):
	"""
	Created: 23.05.2005, KP
	Description: A panel that can be used to preview volume data several slice at a time
	"""
	def __init__(self, parent, visualizer, size = (512, 512), **kws):
		"""
		Created: 24.03.2005, KP
		Description: Initialization
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
		self.zoomToFitFlag = 0
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
		#wx.ScrolledWindow.__init__(self,parent,-1,size=size,**kws)
		InteractivePanel.__init__(self, parent, size = size, **kws)
		
		self.size = size
		self.sizeChanged = 0
		self.rows = 0
		self.cols = 0
		self.scrollsize = 32
		self.scrollTo = None
		self.drawableRects = []
		self.dataUnit = None
		self.slice = 0
		
		self.interpolation = 0
		
		self.voxelSize = (0, 0, 0)
		self.showTimepoints = 0
		self.timepoint = 0
		self.paintPreview()
		self.Bind(wx.EVT_PAINT, self.OnPaint)
		self.Bind(wx.EVT_SIZE, self.onSize)
		
	def setShowTimepoints(self, showtps, slice):
		"""
		Created: 21.07.2005, KP
		Description: Configure whether to show z slices or timepoints
		"""
		self.slice = slice
		self.showTimepoints = showtps
		print "Showing slice ", slice
		self.setSlice(slice)
		self.updatePreview()
		self.Refresh()
		
	def getDrawableRectangles(self):
		"""
		Created: 04.07.2005, KP
		Description: Return the rectangles can be drawn on as four-tuples
		"""
		return self.drawableRects
		
	def zoomToFit(self):
		"""
		Created: 05.06.2005, KP
		Description: Zoom the dataset to fit the available screen space
		"""
		self.zoomToFitFlag = 1
		self.calculateBuffer()
		
	def setZoomFactor(self, factor):
		"""
		Created: 05.06.2005, KP
		Description: Set the factor by which the image is zoomed
		"""
		self.zoomFactor = factor
		self.zoomToFitFlag = 0
		self.updateAnnotations()
		x, y = self.originalSliceSize
		x *= factor
		y *= factor
		self.sizeChanged = 1
		self.calculateBuffer()

		self.sliceSize = (x, y)
		self.slices = []
		
		self.updatePreview()
		self.Refresh()
		
	def setBackground(self, r, g, b):
		"""
		Created: 24.05.2005, KP
		Description: Set the background color
		"""
		self.bgcolor = (r, g, b)

	def onSize(self, event):
		"""
		Created: 23.05.2005, KP
		Description: Size event handler
		"""
		InteractivePanel.OnSize(self, event)
		self.paintSize = self.GetClientSize()
		#self.gallerySize=event.GetSize()
		#Logging.info("Gallery size changed to ",self.gallerySize,kw="preview")
		self.sizeChanged = 1
		self.calculateBuffer()
		self.updatePreview()

	def setDataUnit(self, dataunit):
		"""
		Created: 23.05.2005, KP
		Description: Sets the dataunit to display
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
		self.setScrollbars(x, y)
		self.calculateBuffer()
		self.updatePreview()
			#self.imagedata=image
		
		
	def setTimepoint(self, timepoint, update = 1):
		"""
		Created: 23.05.2005, KP
		Description: Sets the timepoint to display
		"""
		if self.timepoint == timepoint and self.slices:
			return
		self.timepoint = timepoint
		# if we're showing one slice of each timepointh
		# instead of each slice of one timepoint, call the
		# appropriate function
		if self.showTimepoints:
			return self.setSlice(self.slice)
		if self.visualizer.getProcessedMode():
			image = self.dataUnit.doPreview(scripting.WHOLE_DATASET_NO_ALPHA, 1, self.timepoint)
			ctf = self.dataUnit.getSourceDataUnits()[0].getColorTransferFunction()
#			Logging.info("Using ", image, "for gallery", kw = "preview")
		else:
			image = self.dataUnit.getTimepoint(timepoint)
			ctf = self.dataUnit.getColorTransferFunction()

		#self.imagedata = lib.ImageOperations.imageDataTo3Component(image,ctf)
		self.imagedata = image
		self.imagedata.SetUpdateExtent(self.imagedata.GetWholeExtent())
		self.imagedata.Update()
		
		x, y, z = self.dataUnit.getDimensions()
		
		self.slices = []
		
		for i in range(z):
			#print "Using as update ext",(0,x-1,0,y-1,i,i)
			image = optimize.optimize(image = self.imagedata, updateExtent = (0, x - 1, 0, y - 1, i, i))
			
			#self.imagedata.Update()
			image = lib.ImageOperations.getSlice(image, i)
		
			
			slice = lib.ImageOperations.imageDataTo3Component(image, ctf)
			slice.Update()
			w, h = self.sliceSize
			factor = lib.ImageOperations.getZoomFactor(x, y, w, h)
			
			if self.interpolation:
				slice = self.zoomImageWithInterpolation(slice, factor, self.interpolation, 0)
			else:
				slice = lib.ImageOperations.vtkImageDataToWxImage(slice)
				slice.Rescale(w, h)
			
			lib.messenger.send(None, "update_progress", i / float(z), "Loading slice %d / %d for Gallery view" % (i + 1, z + 1))
			self.slices.append(slice)
		lib.messenger.send(None, "update_progress", 1.0, "All slices loaded.")  
		self.calculateBuffer()
		if update:
			print "Updating preview"
			self.updatePreview()
			self.Refresh()
			
	def forceUpdate(self):
		"""
		Created: 17.1.2007, KP
		Description: force update of the preview
		"""
		tp = self.timepoint
		self.slices = []
		self.timepoint = -1
		self.setTimepoint(tp)
#		self.updatePreview()
#		self.Refresh()
		
	def setSlice(self, slice):
		"""
		Created: 21.07.2005, KP
		Description: Sets the slice to show
		"""
		self.slice = slice
		# if we're showing each slice of one timepoint
		# instead of one slice of each timepoint, call the
		# appropriate function
		if not self.showTimepoints:
			self.slices = []
			return self.setTimepoint(self.timepoint)
		count = self.dataUnit.getNumberOfTimepoints()
		self.slices = []
		for tp in range(0, count):
			if self.dataUnit.isProcessed():
				image = self.dataUnit.doPreview(self.slice, 1, tp)
				ctf = self.dataUnit.getSourceDataUnits()[0].getColorTransferFunction()
				Logging.info("Using ", image, "for gallery", kw = "preview")
			else:
				image = self.dataUnit.getTimepoint(tp)
				x, y, z = self.dataUnit.getDimensions()
				image = optimize.optimize(image, updateExtent = (0, x - 1, 0, y - 1, self.slice, self.slice))
				image = lib.ImageOperations.getSlice(image, self.slice)
				image.Update()
#				print "Got slice =", image
				ctf = self.dataUnit.getColorTransferFunction()
#			print "tp =", tp
			self.imagedata = lib.ImageOperations.imageDataTo3Component(image, ctf)
			self.imagedata.Update()
#			print "Got ", self.imagedata
			slice = lib.ImageOperations.vtkImageDataToWxImage(self.imagedata, self.slice)
			self.slices.append(slice)
			
		self.calculateBuffer()
		self.updatePreview()

	def calculateBuffer(self):
		"""
		Created: 23.05.2005, KP
		Description: Calculate the drawing buffer required
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
				if ny * i * yfromx < maxY and (nx * ny) > n:
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
		flag = 0
		if x > x2:
			x2 = x
		if y > y2:
			y2 = y
		
		self.buffer = wx.EmptyBitmap(x2, y2)
		self.setScrollbars(x2, y2)
		


	def resetScroll(self):
		"""
		Created: 24.03.2005, KP
		Description: Sets the scrollbars to their initial values
		"""
		self.Scroll(0, 0)


	def enable(self, flag):
		"""
		Created: 02.06.2005, KP
		Description: Enable/Disable updates
		"""
		self.enabled = flag
		if flag:
			self.updatePreview()

	def updatePreview(self):
		"""
		Created: 24.03.2005, KP
		Description: Updates the viewed image
		"""
		if not self.enabled:
			Logging.info("Won't draw gallery cause not enabled", kw = "preview")
			return
		if not self.dataUnit:
			return			
		if not self.slices:
			print "Updating slices"
			self.setTimepoint(self.timepoint, update = 0)
		self.paintPreview()
		self.updateScrolling()
		self.Refresh()
		#wx.GetApp().Yield(1)
		
		
	def updateScrolling(self, event = None):
		"""
		Created: 24.03.2005, KP
		Description: Updates the scroll settings
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
		Created: 28.04.2005, KP
		Description: Does the actual blitting of the bitmap
		"""
#		if self.sizeChanged:
#			#Logging.info("size changed, calculating buffer",kw="preview")
#			self.calculateBuffer()
#			self.updatePreview()
#			self.sizeChanged = 0

		InteractivePanel.OnPaint(self, event)
#		dc=wx.BufferedPaintDC(self,self.buffer)#,self.buffer)

	def paintPreview(self):
		"""
		Created: 24.03.2005, KP
		Description: Paints the image to a DC
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
		for slice in self.slices:
			w, h = self.sliceSize
#			slice.Rescale(w, h)
			bmp = slice.ConvertToBitmap()

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
		
	def saveSnapshot(self, filename):
		"""
		Created: 05.06.2005, KP
		Description: Save a snapshot of the scene
		"""
		ext = filename.split(".")[-1].lower()
		if ext == "jpg":
			ext = "jpeg"
		if ext == "tif":
			ext = "tiff"
		mime = "image/%s" % ext
		img = self.buffer.ConvertToImage()
		img.SaveMimeFile(filename, mime)
		
