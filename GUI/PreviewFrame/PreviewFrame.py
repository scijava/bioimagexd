# -*- coding: iso-8859-1 -*-

"""
 Unit: PreviewFrame.py
 Project: BioImageXD
 Created: 03.11.2004, KP
 Description:

 A widget that can be used to Preview any operations done by a subclass of Module

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
__version__ = "$Revision: 1.63 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import scripting
from GUI.InteractivePanel import InteractivePanel as InteractivePanel
import lib.ImageOperations
import lib.messenger
import Logging
import Modules
import optimize
import sys
import time
import vtk
import vtkbxd
import wx

ZOOM_TO_FIT = -1

class PreviewFrame(InteractivePanel):
	"""
	Created: 03.11.2004, KP
	Description: A visualization mode used to show either a given single slice, or an MIP
				 of the given datanit
	"""
	count = 0
	def __init__(self, parent, **kws):
		"""
		Created: 03.11.2004, KP
		Description: Initialize the panel
		"""
		xframe = sys._getframe(1)
		self.graySize = (0, 0)
		self.bgcolor = (127, 127, 127)
		self.maxClientSizeX, self.maxClientSizeY = 512, 512
		self.dataWidth, self.dataHeight = 512 , 512
		self.lastEventSize = None
		self.paintSize = (512, 512)
		self.creator = xframe.f_code.co_filename + ": " + str(xframe.f_lineno)
		self.parent = parent
		self.blackImage = None
		self.finalImage = None
		self.xdiff, self.ydiff = 0, 0
		self.oldZoomFactor = 1
		self.selectedItem = -1
		self.show = {}
		self.rawImages = []
		self.rawImage = None
		
		self.oldx, self.oldy = 0, 0
		Logging.info("kws=", kws, kw = "preview")
		self.fixedSize = kws.get("previewsize", None)
		size = kws.get("previewsize", (1024, 1024))

		self.zoomFactor = kws.get("zoom_factor", 1)
		self.zoomx = kws.get("zoomx", 1)
		self.zoomy = kws.get("zoomy", 1)
		
		self.show["SCROLL"] = kws.get("scrollbars", 0)
		
		self.dataUnit = None
		self.rgbMode = 0
		self.currentImage = None
		self.currentCt = None
		
		# The preview can be no larger than these
		
		self.dataDimX, self.dataDimY, self.dataDimZ = 0, 0, 0
		self.running = 0

		self.rgb = (255, 255, 0)

		self.timePoint = 0
		
		self.mapToColors = vtk.vtkImageMapToColors()
		self.mapToColors.SetLookupTable(self.currentCt)
		self.mapToColors.SetOutputFormatToRGB()
		
		self.enabled = 1

		self.previewtype = ""
		self.tmodules = Modules.DynamicLoader.getTaskModules()
		self.tmodules[""] = self.tmodules["Process"]
		self.modules = {}
		for key in self.tmodules:
			self.modules[key] = self.tmodules[key][0]
			
		self.renewNext = 0
		lib.messenger.connect(None, "zslice_changed", self.setPreviewedSlice)
		lib.messenger.connect(None, "renew_preview", self.setRenewFlag)
		
		self.fitLater = 0
		self.imagedata = None
		self.bmp = None
		self.parent = parent
		self.scroll = 1
		Logging.info("preview panel size=", size, kw = "preview")
		
		x, y = size
		self.buffer = wx.EmptyBitmap(x, y)
		
		if kws.has_key("zoomx"):
			del kws["zoomx"]
		if kws.has_key("zoomy"):
			del kws["zoomy"]
			
		Logging.info("zoom xf=%f, yf=%f" % (self.zoomx, self.zoomy), kw = "preview")

		self.size = size
		self.slice = None
		self.z = 0
		self.zooming = 0
		self.singleslice = 0
		self.scrollTo = None
		
		InteractivePanel.__init__(self, parent, size = size, bgColor = self.bgcolor, **kws)
		
		self.calculateBuffer()
		self.paintSize = self.GetClientSize()
		self.paintPreview()
		
		self.addListener(wx.EVT_RIGHT_DOWN, self.onRightClick)
		
		self.Bind(wx.EVT_SIZE, self.onSize)
		self.Bind(wx.EVT_LEFT_DOWN, self.getVoxelValue)
		self.SetHelpText("This window displays the selected dataset slice by slice.")
		
		if not self.show["SCROLL"]:
			Logging.info("Disabling scrollbars", kw="preview")
			self.SetScrollbars(0, 0, 0, 0)
		self.updateAnnotations()
		
	def isMipMode(self):
		"""
		Created: 23.11.2006, KP
		Description: return the flag that indicates whether this window is in mip mode or not
		"""
		return self.previewType == "MIP"
		
	def calculateBuffer(self):
		"""
		Created: 23.05.2005, KP
		Description: Calculate the drawing buffer required
		"""
		cx, cy = self.GetClientSize()
		Logging.info("Calculating buffer from client size %d,%d"%(cx, cy), kw="preview")

		# if the client size is larger than the original client size, use that
		newX = max(self.maxClientSizeX, cx)
		newY = max(self.maxClientSizeY, cy)
		
		if self.fixedSize:
			x, y = self.fixedSize
			Logging.info("Using fixed size %d,%d"%(x,y), kw="preview")
			
		# If the old size is different from the new size
		if self.paintSize != (newX, newY):
			# Calculate the width and height of the original image data scaled by the 
			# current zoom factor, and if that size is larger than the requested
			# size, then use that 
			x2, y2 = [a*self.zoomFactor for a in [self.dataDimX, self.dataDimY]]
			newX = max(newX, x2)
			newY = max(newY, y2)

			self.paintSize = (newX, newY)
			
			if self.buffer.GetWidth() != newX or self.buffer.GetHeight() != newY:
				Logging.info("Making buffer the size of %d,%d"%(newX, newY), kw="preview")
				self.buffer = wx.EmptyBitmap(newX, newY)
				self.setScrollbars(newX, newY)

	def onSize(self, event):
		"""
		Created: 23.05.2005, KP
		Description: Size event handler
		"""
		if event.GetSize() == self.lastEventSize:
			return
		self.lastEventSize = event.GetSize()
		
		InteractivePanel.OnSize(self, event)
		self.sizeChanged = 1
		if self.enabled:
			self.calculateBuffer()
			self.updatePreview(renew = 0)
		event.Skip()
		
	def setRenewFlag(self, *args):
		"""
		Created: 12.08.2005, KP
		Description: Set the flag telling the preview to renew
		"""
		self.renewNext = 1
		
	def setSelectedItem(self, item, update = 1):
		"""
		Created: 05.04.2005, KP
		Description: Set the channel of the combined dataunit selected for viewing
		"""
		Logging.info("Selected item " + str(item), kw = "preview")
		self.selectedItem = item
		if self.dataUnit.isProcessed():
			self.settings = self.dataUnit.getSourceDataUnits()[item].getSettings()
			self.settings.set("PreviewedDataset", item)
		else:
			self.settings = self.dataUnit.getSettings()
		if update:
			self.updatePreview(1)
		
	def onRightClick(self, event):
		"""
		Created: 02.04.2005, KP
		Description: Method that is called when the right mouse button is
					 pressed down on this item
		""" 
		x, y = event.GetPosition()
		shape = self.FindShape(x, y)
		if shape:
			event.Skip()

	def getVoxelValue(self, event):
		"""
		Created: 23.05.2005, KP
		Description: Send an event containing the current voxel position
		"""
		self.onLeftDown(event)
		event.Skip()
		if not self.rawImage and not self.rawImages:
			return
		if self.rawImages:
			self.rawImage = self.rawImages[0]
		elif self.rawImage and not self.rawImages:
			self.rawImages = [self.rawImage]
		if self.isMipMode():
			self.rawImage = self.currentImage
			self.rawImages = [self.rawImage]
		x, y = event.GetPosition()
		x -= self.xoffset
		y -= self.yoffset

		x0, y0, w, h = self.GetClientRect()
		
		x, y = self.getScrolledXY(x, y)
		x -= x0
		y -= y0
		z = self.z

		dims = [x, y, z]
		rx, ry, rz = dims

		# ensure x, y are not below zero
		x = max(x, 0)
		y = max(y, 0)
		if x >= self.dataDimX:
			x = self.dataDimX - 1
		if y >= self.dataDimY:
			y = self.dataDimY - 1
		Logging.info("Returning x,y,z=(%d,%d,%d)" % (rx, ry, rz), kw = "preview")
		ncomps = self.rawImage.GetNumberOfScalarComponents()
		if ncomps == 1:
			Logging.info("One component in raw image", kw = "preview")
			rv, gv, bv = -1, -1, -1
			alpha = -1
			if len(self.rawImages) < 2:
				scalar = self.rawImages[0].GetScalarComponentAsDouble(x, y, self.z, 0)
			else:
				scalar = []
				for i, img in enumerate(self.rawImages):
#					img.SetExtent(img.GetWholeExtent())
					if self.dataUnit.getOutputChannel(i):
						scalar.append(img.GetScalarComponentAsDouble(x, y, self.z, 0))
				scalar = tuple(scalar)

		else:
			rv = self.rawImage.GetScalarComponentAsDouble(x, y, self.z, 0)
			gv = self.rawImage.GetScalarComponentAsDouble(x, y, self.z, 1)
			bv = self.rawImage.GetScalarComponentAsDouble(x, y, self.z, 2)
			scalar = 0xdeadbeef
			
		r = self.currentImage.GetScalarComponentAsDouble(x, y, self.z, 0)
		g = self.currentImage.GetScalarComponentAsDouble(x, y, self.z, 1)
		b = self.currentImage.GetScalarComponentAsDouble(x, y, self.z, 2)
		alpha = -1
		if ncomps > 3:
			alpha = self.currentImage.GetScalarComponentAsDouble(x, y, self.z, 3)

		lib.messenger.send(None, "get_voxel_at", rx, ry, rz, scalar, rv, gv, bv, r, g, b, alpha, self.currentCt)
			
	def setPreviewedSlice(self, obj, event, newz = -1):
		"""
		Created: 4.11.2004, KP
		Description: Sets the preview to display the selected z slice
		"""
		if self.z != newz:
			self.z = newz
			self.updatePreview(0)

	def setTimepoint(self, timePoint):
		"""
		Created: 09.12.2004, KP
		Description: The previewed timepoint is set to the given timepoint
		Parameters:
				timePoint	The timepoint to show
		"""
		if self.timePoint != timePoint:
			self.timePoint = timePoint
			self.updatePreview(1)

	def setDataUnit(self, dataUnit, selectedItem = -1):
		"""
		Created: 04.11.2004, KP
		Description: Set the dataunit used for preview. Should be a combined 
					 data unit, the source units of which we can get and read 
					 as ImageData
		"""
		if not dataUnit:
			self.dataUnit = None
			self.z = 0
			self.slice = None
			self.updatePreview()
			self.Refresh()
			return
		self.dataUnit = dataUnit
		self.settings = dataUnit.getSettings()
		self.updateColor()
		InteractivePanel.setDataUnit(self, self.dataUnit)
		
		try:
			count = dataUnit.getNumberOfTimepoints()
			x, y, z = dataUnit.getDimensions()
		except Logging.GUIError, ex:
			ex.show()
			return
			
		self.dataDimX, self.dataDimY, self.dataDimZ = x, y, z

		self.paintSize = (0, 0)
		self.calculateBuffer()
		
		if selectedItem != -1:
			self.setSelectedItem(selectedItem, update = 0)

		updated = 0
		Logging.info("zoomFactor = ", self.zoomFactor, kw = "preview")
		
		if self.enabled:
			self.Layout()
			self.parent.Layout()
			if not updated:
				self.updatePreview(1)

	def updatePreview(self, renew = 1):
		"""
		Created: 03.04.2005, KP
		Description: Update the preview
		Parameters:
		renew    Whether the method should recalculate the images
		"""
		if scripting.inIO:
			return
		if self.renewNext:
			renew = 1
			self.renewNext = 0
		if not self.dataUnit:
			self.paintPreview()
			return
		if not self.enabled:
			Logging.info("Preview not enabled, won't render", kw = "preview")
			return
		self.updateColor()
		if not self.running:
			renew = 1
			self.running = 1
		
		if self.dataUnit.isProcessed():
			try:
				z = self.z
				# if we're doing a MIP, we need to set z to -1
				# to indicate we want the whole volume
				if self.isMipMode():z = -1
				self.rawImages = []
				for source in self.dataUnit.getSourceDataUnits():
					self.rawImages.append(source.getTimepoint(self.timePoint))  
				
				preview = self.dataUnit.doPreview(z, renew, self.timePoint)
				#Logging.info("Got preview",preview.GetDimensions(),kw="preview")
			except Logging.GUIError, ex:
				ex.show()
				return
		else:
			preview = self.dataUnit.getTimepoint(self.timePoint)
			self.rawImage = preview
			Logging.info("Using timepoint %d as preview" % self.timePoint, kw = "preview")
		
		black = 0
		if not preview:
			preview = None
			black = 1
		if not black:
			colorImage = self.processOutputData(preview)
		else:
			colorImage = preview
		
		usedUpdateExt = 0
		uext = None
		if self.z != -1 and not self.isMipMode():
			x, y = self.dataDimX, self.dataDimY
			usedUpdateExt = 1
			#colorImage.SetUpdateExtent(0,x-1,0,y-1,self.z,self.z)
			uext = (0, x - 1, 0, y - 1, self.z, self.z)
		
		t = time.time()
		colorImage = optimize.optimize(image = colorImage, updateExtent = uext)

		t2 = time.time()
		Logging.info("Executing pipeline took %f seconds" % (t2 - t), kw = "pipeline")
		self.currentImage = colorImage

		if colorImage:
			x, y, z = colorImage.GetDimensions()
			
			if not usedUpdateExt and not self.isMipMode():
				scripting.visualizer.zslider.SetRange(1, z)
			if x != self.oldx or y != self.oldy:
				#self.resetScroll()
				#self.setScrollbars(x,y)
				self.oldx = x
				self.oldy = y
			self.setImage(colorImage)
			self.setZSlice(self.z)
		
			z = self.z
			if self.singleslice:
				#Logging.info("Single slice, will use z=0",kw="preview")
				z = 0
		if not self.imagedata:
			Logging.info("No imagedata to preview", kw = "preview")
#			return
			self.slice = None
		else:
			self.slice = lib.ImageOperations.vtkImageDataToWxImage(self.imagedata, z)
			
		self.paintPreview()
		self.updateScrolling()
		self.finalImage = colorImage
		self.Refresh()
		
	def processOutputData(self, data):
		"""
		Created: 03.04.2005, KP
		Description: Process the data before it's send to the preview
		"""
		data.UpdateInformation()
		ncomps = data.GetNumberOfScalarComponents()
		if ncomps > 3:
			extract = vtk.vtkImageExtractComponents()
			extract.SetComponents(0, 1, 2)
			extract.SetInput(data)
			data = extract.GetOutput()
			
		if self.isMipMode():
			mip = vtkbxd.vtkImageSimpleMIP()
			mip.SetInput(data)
			
			data = mip.GetOutput()
		
		if ncomps == 1:
			Logging.info("Mapping trough ctf", kw = "preview")
			
			self.mapToColors = vtk.vtkImageMapToColors()
			self.mapToColors.SetInput(data)			
			
			self.updateColor()

			colorImage = self.mapToColors.GetOutput()
			
			outdata  = colorImage
			return outdata
			
		else:
			pass
			
		return data

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
		#img=self.snapshot.ConvertToImage()
		w, h = self.snapshotSize
		x, y = self.snapshotPos
		buff = wx.EmptyBitmap(w, h)
		memdc = wx.MemoryDC()
		memdc.SelectObject(buff)
		bltdc = wx.MemoryDC()
		bltdc.SelectObject(self.buffer)
		memdc.Blit( 0, 0, w, h, bltdc, x, y)
		memdc.SelectObject(wx.NullBitmap)
		bltdc.SelectObject(wx.NullBitmap)
		img = buff.ConvertToImage()
		
		img.SaveMimeFile(filename, mime)
		
	def enable(self, flag):
		"""
		Created: 02.06.2005, KP
		Description: Enable/Disable updates
		"""
		self.enabled = flag
		if flag:
			self.calculateBuffer()
		
	def setPreviewType(self, newType):
		"""
		Created: 03.04.2005, KP
		Description: Method to set the proper previewtype
		"""
		if type(newType) == type(""):
			self.previewType = newType
		
	def updateColor(self):
		"""
		Created: 20.11.2004, KP
		Description: Update the preview to use the selected color transfer 
					 function
		"""
		if self.dataUnit:
			#ct = self.settings.get("ColorTransferFunction")
			ct = self.dataUnit.getColorTransferFunction()

			val = [0, 0, 0]
			if self.selectedItem != -1:
				ctc = self.settings.getCounted("ColorTransferFunction", self.selectedItem)

				if ctc:
					ctc.GetColor(255, val)
					Logging.info("Using ctf of selected item", val, kw = "ctf")
					
					Logging.info("Using item %d (counted)" % self.selectedItem, kw = "preview")
					ct = ctc
	 
		self.currentCt = ct
		
		#ct.GetColor(255,val)
		#Logging.info("value of 255=",val,kw="ctf")
	
		self.mapToColors.SetLookupTable(self.currentCt)
		self.mapToColors.SetOutputFormatToRGB()
 
	def setSingleSliceMode(self, mode):
		"""
		Created: 05.04.2005, KP
		Description: Sets this preview to only show a single slice
		"""
		self.singleslice = mode

	def setZSlice(self, z):
		"""
		Created: 24.03.2005, KP
		Description: Sets the optical slice to preview
		"""
		self.z = z
		
	def setImage(self, image):
		"""
		Created: 24.03.2005, KP
		Description: Sets the image to display
		"""
		self.imagedata = image
		
		x, y = self.size
		image.UpdateInformation()   
		x2, y2, z = image.GetDimensions()
		if x2 < x:
			x = x2
		if y2 < y:
			y = y2
		
		if self.fitLater:
			self.fitLater = 0
			self.zoomToFit()
		
	def setZoomFactor(self, newFactor):
		"""
		Created: 24.03.2005, KP
		Description: Sets the factor by which the image should be zoomed
		"""
		if newFactor > 10:
			newFactor = 10
		Logging.info("Setting zoom factor to ", newFactor, kw = "preview")
		x, y = [a*newFactor for a in (self.dataDimX, self.dataDimY)]

		if scripting.resampleToFit:
			optimize.set_target_size(x, y)
			newFactor = 1
		px, py = self.paintSize
		
		x = max(px, x)
		y = max(py, y)
		
		self.buffer = wx.EmptyBitmap(x, y)
		self.setScrollbars(x, y)
		if newFactor < self.zoomFactor:
			# black the preview
			slice = self.slice
			self.slice = None
			self.paintPreview()
			self.slice = slice
		self.zoomFactor = newFactor
		scripting.zoomFactor = newFactor
		self.updateAnnotations()
		
	def zoomToFit(self):
		"""
		Created: 25.03.2005, KP
		Description: Sets the zoom factor so that the image will fit into the screen
		"""
		if self.dataUnit:
			#x,y,z=self.imagedata.GetDimensions()
			x, y, z = self.dataUnit.getDimensions()
			maxX = self.maxClientSizeX
			maxY = self.maxClientSizeY
			maxX -= 10 # marginal
			maxY -= 10 #marginal
			if self.fixedSize:
				maxX, maxY = self.fixedSize
			
			Logging.info("Determining zoom factor from (%d,%d) to (%d,%d)" % (x, y, maxX, maxY), kw = "preview")
			factor = lib.ImageOperations.getZoomFactor(x, y, maxX, maxY)
			self.setZoomFactor(factor)
			scripting.zoomFactor = factor
		else:
			Logging.info("Will zoom to fit later", kw = "preview")
			self.fitLater = 1
		
	def updateScrolling(self, event = None):
		"""
		Created: 24.03.2005, KP
		Description: Updates the scroll settings
		"""
		if not self.bmp:
			return

		if self.scrollTo:
			x, y = self.scrollTo
			Logging.info("Scrolling to %d,%d" % (x, y), kw = "preview")
			sx = int(x / self.scrollStepSize)
			sy = int(y / self.scrollStepSize)

			self.Scroll(sx, sy)
			self.scrollTo = None

	def paintPreview(self, clientdc = None):
		"""
		Created: 24.03.2005, KP
		Description: Paints the image to a DC
		"""
		Logging.info("PreviewFrame is enbled=", bool(self.enabled), kw="preview")
		# Don't paint anything if there's going to be a redraw anyway

		if not self.slice and self.graySize == self.paintSize:
			return
		dc = wx.MemoryDC()
		dc.SelectObject(self.buffer)
		dc.BeginDrawing()
		
		dc.SetBackground(wx.Brush(wx.Colour(*self.bgcolor)))
		dc.SetPen(wx.Pen(wx.Colour(*self.bgcolor), 0))
		dc.SetBrush(wx.Brush(wx.Color(*self.bgcolor)))
		x0, y0 = 0, 0
		w, h = self.buffer.GetWidth(), self.buffer.GetHeight()
		
		dc.DrawRectangle(x0, y0, self.paintSize[0] + x0, self.paintSize[1] + x0)

		if not self.slice or not self.enabled:
			self.graySize = self.paintSize
			self.makeBackgroundBuffer(dc)
			dc.EndDrawing()
			self.repaintHelpers(update = 0)
			return

		bmp = self.slice
		Logging.info("Zoom factor for painting =", self.zoomFactor, kw = "preview")
		if self.zoomFactor != 1 or self.zoomFactor != self.oldZoomFactor:
			self.oldZoomFactor = self.zoomFactor
			interpolation = self.interpolation
			if interpolation == -1:
				x, y, z = self.imagedata.GetDimensions()
				# if x*y < 512*512, cubic
				pixels = (x * self.zoomFactor) * (y * self.zoomFactor)
				if pixels <= 1024 * 1024:
					Logging.info("Using cubic", kw = "preview")
					interpolation = 2
				# if x*y < 1024*1024, linear
				elif pixels <= 2048 * 2048:
					Logging.info("Using nearest", kw = "preview")
					interpolation = 1
				else:
					Logging.info("Using no interpolation", kw = "preview")
					interpolation = 0
			if interpolation == 0:
				bmp = lib.ImageOperations.zoomImageByFactor(self.slice, self.zoomFactor)
			else:
				img = lib.ImageOperations.scaleImage(self.imagedata, self.zoomFactor, self.z, interpolation)

				bmp = lib.ImageOperations.vtkImageDataToWxImage(img)
			w, h = bmp.GetWidth(), bmp.GetHeight()

		if self.zoomx != 1 or self.zoomy != 1:
			w, h = bmp.GetWidth(), bmp.GetHeight()
			w *= self.zoomx
			h *= self.zoomy
			Logging.info("Scaling to ", w, h, kw = "preview")
			bmp.Rescale(w, h)
			self.calculateBuffer()
			#self.setScrollbars(w,h)
		
		bmp = bmp.ConvertToBitmap()

		self.snapshot = bmp
		bw, bh = bmp.GetWidth(), bmp.GetHeight()
		
		tw, th = self.buffer.GetWidth(), self.buffer.GetHeight()
		xoff = (tw - bw) / 2
		yoff = (th - bh) / 2
		x0, y0, w, h = self.GetClientRect()
		
		self.snapshotPos = xoff + x0 * 2, yoff + y0 * 2
		self.snapshotSize = bw, bh

		self.setOffset(xoff, yoff)
		dc.DrawBitmap(bmp, xoff + x0, yoff + x0, True)

		self.bmp = self.buffer
		
		InteractivePanel.paintPreview(self, dc)

		self.makeBackgroundBuffer(dc)
		
		dc.EndDrawing()
		dc.DestroyClippingRegion()
		self.repaintHelpers()

	def makeBackgroundBuffer(self, dc):
		"""
		Created: 06.10.2006, KP
		Description: Copy the current buffer to a background buffer
		"""
		w, h = self.buffer.GetWidth(), self.buffer.GetHeight()
		self.bgbuffer = wx.EmptyBitmap(w, h)
		memdc = wx.MemoryDC()
		print "Selecting object, bufsize=",w,h
		memdc.SelectObject(self.bgbuffer)
		print "done"
		memdc.Blit(0, 0, w, h, dc, 0, 0)
		memdc.SelectObject(wx.NullBitmap)
