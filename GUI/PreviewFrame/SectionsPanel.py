# -*- coding: iso-8859-1 -*-

"""
 Unit: SectionsPanel.py
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
__author__ = "BioImageXD Project <http://www.bioimagexd.org/>"
__version__ = "$Revision: 1.9 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import scripting
import GUI.InteractivePanel
import lib.ImageOperations
import lib.messenger
import Logging
import math
import wx
import vtk

class SectionsPanel(GUI.InteractivePanel.InteractivePanel):
	"""
	A widget that previews the xy,xz and yz planes of a dataset
	"""
	def __init__(self, parent, visualizer, size = (512, 512), **kws):
		"""
		Initialization
		"""
		self.imagedata = None
		self.fitLater = 0
		self.visualizer = visualizer
		self.noUpdate = 0
		
		self.voi = None
		self.permute = None
		self.oldBufferDims = None
		self.oldBufferMaxXY = None
		
		self.bmp = None
		self.bgcolor = (127, 127, 127)
		self.enabled = 1
		self.slices = []
			
		x, y = size
		self.paintSize = size
		self.buffer = wx.EmptyBitmap(x, y)
		GUI.InteractivePanel.InteractivePanel.__init__(self, parent, size = size, **kws)
		self.size = size
		self.sizeChanged = False
		self.rows = 0
		self.cols = 0
		self.scrollsize = 32
		self.scrollTo = None
		self.dataUnitChanged = False
		
		self.drawableRects = []
		self.zspacing = 1
		
		self.zoomZ = 1.0
		self.zoomx = 1
		self.zoomy = 1
		
		self.xmargin = 5
		self.xmargin_default = 5
		self.ymargin = 5
		self.ymargin_default = 5
		
		self.voxelSize = (0, 0, 0)
		self.x, self.y, self.z = 0, 0, 0

		
		self.timepoint = 0
		self.paintPreview()
		self.Bind(wx.EVT_PAINT, self.OnPaint)
		self.Bind(wx.EVT_SIZE, self.onSize)
		self.Bind(wx.EVT_LEFT_DOWN, self.onLeftDown)
		self.Bind(wx.EVT_MOTION, self.onLeftDown)
		
		lib.messenger.connect(None, "zslice_changed", self.onSetZSlice)

	def deregister(self):
		"""
		Delete all known references because this view mode is to be removed
		"""
		try:
			lib.messenger.disconnect(None, "zslice_changed", self.onSetZSlice)
		except:
			pass
		GUI.InteractivePanel.InteractivePanel.deregister(self)
		
	def getDrawableRectangles(self):
		"""
		Return the rectangles can be drawn on as four-tuples
		"""
		return self.drawableRects
		
	def setZoomFactor(self, factor):
		"""
		Set the factor by which the image is zoomed
		"""
		self.zoomFactor = factor
		self.updateAnnotations()
		self.sizeChanged = True

		self.xmargin = int(self.xmargin_default * self.zoomFactor)
		self.ymargin = int(self.ymargin_default * self.zoomFactor)
		if self.xmargin < 3:
			self.xmargin = 3
		if self.ymargin < 3:
			self.ymargin = 3
		x0, y0, x1, y1 = self.GetClientRect()
		self.xmargin += x0
		self.ymargin += y0

		self.calculateBuffer()
		
	def onSetZSlice(self, obj, event, arg):
		"""
		Set the shown zslice
		"""
		# A flag to indicate that we won't react on our own messages
		if self.noUpdate:
			return
		nx, ny = self.x, self.y
		nz = arg
		self.z = arg
		self.drawPos = [x * self.zoomFactor for x in (nx, ny, nz)]
		
		self.setTimepoint(self.timepoint)
		
	def onLeftDown(self, event):
		"""
		Handler for mouse clicks
		"""
		# if left mouse key is not down or the key down is related to
		# interactive panel events
		if self.action:
			event.Skip()
			return
		if not event.LeftIsDown():
			event.Skip()
			return

		x, y = event.GetPosition()
		x -= self.xmargin
		y -= self.ymargin
		x, y = self.getScrolledXY(x,y)
		
		#x /= float(self.zoomFactor)
		#y /= float(self.zoomFactor)

		dims = self.imagedata.GetDimensions()
		
		# the yz plane
		# calculate scaled margins, because the click coordinates are scaled as well
		sxmargin = self.xmargin / self.zoomFactor
		symargin = self.ymargin / self.zoomFactor
		
		if x >= dims[0] + sxmargin + dims[2] * self.zspacing:
			x = dims[0] + sxmargin + dims[2] * self.zspacing - 1
		if y >= dims[1] + symargin + dims[2] * self.zspacing:
			y = dims[1] + symargin + dims[2] * self.zspacing - 1
			
			
		if x > dims[0] + (sxmargin) and y > 0 and y < dims[1] and x < dims[0] + sxmargin + dims[2] * self.zspacing:
			nz = x - dims[0] - sxmargin
			nz /= self.zspacing
			ny = y
			nx = self.x
		elif x > 0 and x < dims[0] and y > 0 and y < dims[1]:
			nx = x
			ny = y
			nz = self.z
		# the xz plane
		elif x > 0 and x < dims[0] and y > dims[1] + symargin and y < dims[1] + symargin + dims[2] * self.zspacing:
			nx = x
			nz = y - dims[1] - symargin
			nz /= self.zspacing
			ny = self.y
		# the gray area
		elif x > dims[0] + sxmargin and x < dims[0] + sxmargin + dims[2] * self.zspacing and y > dims[1] + symargin and y < dims[1] + symargin + dims[2] * self.zspacing:
			if y > x:
				nz = y - dims[1] - symargin
			else:
				nz = x - dims[0] - sxmargin
			nx = self.x
			ny = self.y
		else:
			Logging.info("Out of bounds (%d,%d)" % (x, y), kw = "preview")
			return
		
		self.drawPos = [math.ceil(a * self.zoomFactor) for a in (nx, ny, nz)]
		if self.x != nx or self.y != ny or self.z != nz:
			self.x, self.y, self.z = int(nx), int(ny), int(nz)
			self.setTimepoint(self.timepoint)
		else:
			self.updatePreview()
		
		self.noUpdate = 1
		lib.messenger.send(None, "zslice_changed", nz) 
		self.noUpdate = 0
		ncomps = self.imagedata.GetNumberOfScalarComponents()
		if ncomps == 1:
			scalar = self.imagedata.GetScalarComponentAsDouble(self.x, self.y, self.z, 0)
			rv = -1
			gv = -1
			bv = -1
			alpha = -1
			val = [0, 0, 0]
			self.ctf.GetColor(scalar, val)
			r, g, b = val

		else:
			rv = self.imagedata.GetScalarComponentAsDouble(self.x, self.y, self.z, 0)
			gv = self.imagedata.GetScalarComponentAsDouble(self.x, self.y, self.z, 1)
			bv = self.imagedata.GetScalarComponentAsDouble(self.x, self.y, self.z, 2)
			r, g, b = rv, gv, bv
			scalar = 0xdeadbeef
			alpha = -1
			if ncomps > 3:
				alpha = self.imagedata.GetScalarComponentAsDouble(self.x, self.y, self.z, 3)
		
		rx, ry, rz = self.x, self.y, self.z
	
	
		lib.messenger.send(None, "get_voxel_at", rx, ry, rz, scalar, rv, gv, bv, r, g, b, alpha, self.ctf)
		
		event.Skip()
		
	def onSize(self, event):
		"""
		Size event handler
		"""
		GUI.InteractivePanel.InteractivePanel.OnSize(self, event)
		if self.size != event.GetSize():
			self.size = event.GetSize()
			Logging.info("Sections panel size changed to ", self.size, kw = "preview")
			self.sizeChanged = True
			self.calculateBuffer()
			self.paintPreview()
			
	def setBackground(self, r, g, b):
		"""
		Set the background color
		"""
		self.bgcolor = (r, g, b)
		
	def setDataUnit(self, dataUnit, selectedItem = -1):
		"""
		Set the dataunit used for preview. 
		"""
		self.dataUnit = dataUnit
		
		self.dims = dataUnit.getDimensions()
		
		x, y, z = self.dims
		x /= 2
		y /= 2
		z /= 2
		z *= self.zoomZ
		
		self.x, self.y, self.z = x, y, z
		self.drawPos = (x, y, z)

		self.voxelSize = dataUnit.getVoxelSize()
		GUI.InteractivePanel.InteractivePanel.setDataUnit(self, dataUnit)
		self.dataUnitChanged = True
		
	def getPlane(self, data, plane, xCoordinate, yCoordinate, zCoordinate, applyZScaling = 0):
		"""
		Get a plane from given the volume
		"""   
		xAxis, yAxis, zAxis = 0, 1, 2
		dataWidth, dataHeight, dataDepth = data.GetDimensions()
		if not self.voi:
			self.voi = vtk.vtkExtractVOI()
		else:
			self.voi.RemoveAllInputs()
		if not self.permute:
			self.permute = vtk.vtkImagePermute()
		else:
			self.permute.RemoveAllInputs()
			
		self.permute.SetInputConnection(data.GetProducerPort())
		
		spacing = data.GetSpacing()

		xscale = 1
		yscale = 1
		if plane == "zy":
			data.SetUpdateExtent(xCoordinate, xCoordinate, 0, dataHeight - 1, 0, dataDepth - 1)
			self.permute.SetFilteredAxes(zAxis, yAxis, xAxis)
			self.permute.Update()
			data = self.permute.GetOutput()
			self.voi.SetInput(data)
	
			self.voi.SetVOI(0, dataDepth - 1, 0, dataHeight - 1, xCoordinate, xCoordinate)
	
			#data.SetUpdateExtent(0, dataDepth - 1, 0, dataHeight - 1, 0, 0)
			#data.SetWholeExtent(0, dataDepth - 1, 0, dataHeight - 1, 0, 0)
			xdim = dataDepth
			ydim = dataHeight
			
			if applyZScaling: 
				xdim *= spacing[2]
				xscale = spacing[2]
			
		elif plane == "xz":
			data.SetUpdateExtent(0, dataWidth - 1, yCoordinate, yCoordinate, 0, dataDepth - 1)
			self.permute.SetFilteredAxes(xAxis, zAxis, yAxis)
			self.permute.Update()
			data = self.permute.GetOutput()
	
			self.voi.SetInput(data)
			self.voi.SetVOI(0, dataWidth - 1, 0, dataDepth - 1, yCoordinate, yCoordinate)

			xdim = dataWidth
			ydim = dataDepth
			if applyZScaling: 
				ydim *= spacing[2]
				yscale = 1
			
		self.voi.Update()
		if applyZScaling:
			self.voi.Update()
			return lib.ImageOperations.scaleImage(self.voi.GetOutput(), interpolation = 2, xfactor = xscale, yfactor = yscale)
			
		self.voi.Update()
		return self.voi.GetOutput()

	def setTimepoint(self, tp, update = 1):
		"""
		Set the timepoint
		"""
		recalculate = False
		# This doesn't work when adjust is open so now just recalculate every tim
		recalculate = True
		#if tp != self.timepoint or self.dataUnitChanged:
			#recalculate = True
		self.timepoint = tp
		if not scripting.renderingEnabled:
			return
		
		if recalculate or not self.imagedata:
			if self.dataUnit.isProcessed():
				image = self.dataUnit.doPreview(scripting.WHOLE_DATASET_NO_ALPHA, 1, self.timepoint)
				self.ctf = self.dataUnit.getColorTransferFunction()
			else:
				image = self.dataUnit.getTimepoint(tp)
				image.SetUpdateExtent(image.GetWholeExtent())
				self.ctf = self.dataUnit.getColorTransferFunction()
			
			self.cachedImage = image
			self.imagedata = lib.ImageOperations.imageDataTo3Component(image, self.ctf)
			self.imagedata.Update()
			self.zspacing = image.GetSpacing()[2]
			self.dataUnitChanged = False
		
		if self.fitLater:
			self.fitLater = 0
			self.zoomToFit()
			return

		self.dims = self.imagedata.GetDimensions()
		self.slices = []

#		obtain the slices
		z = self.z / self.zoomZ
		if self.zoomFactor != 1:
			if self.interpolation:
				imgslice = self.zoomImageWithInterpolation(self.imagedata, self.zoomFactor, self.interpolation, z)
			else:
				img = lib.ImageOperations.scaleImage(self.imagedata, self.zoomFactor, z)
				imgslice = lib.ImageOperations.vtkImageDataToWxImage(img)
		else:
			imgslice = lib.ImageOperations.vtkImageDataToWxImage(self.imagedata, z)
		
		self.slices.append(imgslice)
		
		Logging.info("\n\nzspacing = %f\n"%self.zspacing, kw="preview")
		imgslice = self.getPlane(self.imagedata, "zy", self.x, self.y, int(z))
		w, h = imgslice.GetDimensions()[0:2]
		interpolation = self.interpolation
		if self.interpolation == -1:
			interpolation = self.getInterpolationForSize(w, h, self.zoomFactor)
		if not interpolation: 
			interpolation = 1
		if self.zoomFactor != 1 or self.zspacing != 1:
			imgslice = lib.ImageOperations.scaleImage(imgslice, self.zoomFactor, interpolation = interpolation, yfactor = 1, xfactor = self.zspacing)
		
		imgslice = lib.ImageOperations.vtkImageDataToWxImage(imgslice)
		self.slices.append(imgslice)
		imgslice = self.getPlane(self.imagedata, "xz", self.x, self.y, z)
		if self.zoomFactor != 1 or self.zoomZ != 1  or self.zspacing != 1:
			imgslice = lib.ImageOperations.scaleImage(imgslice, self.zoomFactor, interpolation = interpolation, yfactor = self.zspacing, xfactor = 1)
		imgslice = lib.ImageOperations.vtkImageDataToWxImage(imgslice)
		self.slices.append(imgslice)

		self.calculateBuffer()
		if update:
			self.updatePreview()

	def calculateBuffer(self):
		"""
		Calculate the drawing buffer required
		"""
		if not self.imagedata:
			return
		x, y, z = self.imagedata.GetDimensions()
		x, y, z = self.dataUnit.getDimensions()
		
		if not self.sizeChanged and (x, y, z) == self.oldBufferDims and self.oldBufferMaxXY == (self.maxClientSizeX, self.maxClientSizeY):
			return
		
		self.oldBufferDims = (x, y, z)
		self.oldBufferMaxXY = (self.maxClientSizeX, self.maxClientSizeY)

		x, y, z = [int(i * self.zoomFactor) for i in (x, y, z)]
		Logging.info("scaled size =", x, y, z, kw = "visualizer")
	
		x += z * self.zoomZ * self.zspacing + 2 * self.xmargin
		y += z * self.zoomZ * self.zspacing+ 2 * self.ymargin
		x = int(max(x, self.maxClientSizeX))
		y = int(max(y, self.maxClientSizeY))
		self.paintSize = (x, y)
		if self.buffer.GetWidth() != x or self.buffer.GetHeight() != y:
			self.buffer = wx.EmptyBitmap(x, y)
			Logging.info("Paint size=", self.paintSize, kw = "preview")
			self.setScrollbars(x, y)

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
			Logging.info("\n\n\nWon't draw sections cause not enabled", kw="preview")
			return
		if not self.slices:
			self.setTimepoint(self.timepoint, update = 0)
		self.paintPreview()
		self.Refresh()

	def OnPaint(self, event):
		"""
		Does the actual blitting of the bitmap
		"""
		GUI.InteractivePanel.InteractivePanel.OnPaint(self, event)
	
	def paintPreview(self):
		"""
		Paints the image to a DC
		"""
		dc = wx.MemoryDC()
		dc.SelectObject(self.buffer)
		dc.BeginDrawing()
		dc.SetBackground(wx.Brush(wx.Colour(*self.bgcolor)))
		dc.SetPen(wx.Pen(wx.Colour(*self.bgcolor), 0))
		dc.SetBrush(wx.Brush(wx.Colour(*self.bgcolor)))
		
		x0, y0, x1, y1 = self.GetClientRect()

		dc.DrawRectangle(x0, y0, self.paintSize[0], self.paintSize[1])
		x0, y0 = 0, 0
		
		if not self.slices:
			self.makeBackgroundBuffer(dc)	
			dc.EndDrawing()
			return
		
		row, col = 0, 0

		x, y, z = [i * self.zoomFactor for i in self.dims]
		z *= self.zoomZ * self.zspacing
		pos = [(self.xmargin, self.ymargin), (x + (2 * self.xmargin), self.ymargin), (self.xmargin, y + (2 * self.ymargin))]
		for i, slice in enumerate(self.slices):
			w, h = slice.GetWidth(), slice.GetHeight()
			bmp = slice.ConvertToBitmap()

			sx, sy = pos[i]
			sx += x0
			sy += y0
			dc.DrawBitmap(bmp, sx, sy, False)
			self.drawableRects.append((sx, sx + w, sy, sy + h))
			
		if self.drawPos:
			posx, posy, posz = self.drawPos
			posx += self.xmargin
			posy += self.ymargin
			dc.SetPen(wx.Pen((255, 255, 255), 1))
			# horiz across the xy
			dc.DrawLine(x0 + 0, y0 + posy, (2 * self.xmargin) + x + z, posy)
			# vert across the xy
			dc.DrawLine(x0 + posx, y0, x0 + posx, y0 + (2 * self.ymargin) + y + z)
			# horiz across the lower
			dc.DrawLine(x0, y0 + y + (2 * self.ymargin) + posz * self.zspacing, x0 + (2 * self.xmargin) + x + z, y0 + y + (2 * self.ymargin) + posz * self.zspacing
			)
			# vert across the right
			dc.DrawLine(x0 + (2 * self.xmargin) + x + posz * self.zspacing, y0, x0 + (2 * self.xmargin) + x + posz * self.zspacing, y0 + y + (2 * self.ymargin) + z)
			
		y = pos[-1][1]
			
			
		self.bmp = self.buffer
		self.makeBackgroundBuffer(dc)

		GUI.InteractivePanel.InteractivePanel.paintPreview(self, dc)

		dc.EndDrawing()
		
	def zoomToFit(self):
		"""
		Calculate and set the zoom factor so that the dataset
					 fits in the available screen space
		"""
		if not self.imagedata:
			self.fitLater = 1
			return

		x, y, z = self.imagedata.GetDimensions()
		x += z * self.zspacing + 3 * self.xmargin
		y += z * self.zspacing + 3 * self.ymargin
		f = self.maxClientSizeX / x
		f2 = self.maxClientSizeY / y
		f = min(f, f2)
		self.setZoomFactor(f)
	
