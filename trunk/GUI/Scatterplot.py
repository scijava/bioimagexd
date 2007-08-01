#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
Unit: Scatterplot
Project: BioImageXD
Created: 25.03.2005, KP
Description:

A module that displays a scatterplot and allows the user
select the colocalization threshold based on the plot. Uses the vtkImageAcculat 
to calculate the scatterplot

BioImageXD includes the following persons:

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
__version__ = "$Revision: 1.22 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

#from enthought.tvtk import messenger
import messenger
import InteractivePanel
import vtk
import ImageOperations
import Logging
import sys
import wx

import Dialogs
import Configuration

import math

	
class Scatterplot(InteractivePanel.InteractivePanel):
	"""
	Created: 25.03.2005, KP
	Description: A panel showing the scattergram
	"""
	def __init__(self, parent, size = (256, 256), **kws):
		"""
		Created: 03.11.2004, KP
		Description: Initialization
		"""
		#wx.Panel.__init__(self,parent,-1,size=size,**kws)
		self.parent = parent
		self.size = size
		self.slice = None
		# Empty space is the space between the legends and the scatterplot
		self.emptySpace = 4
		self.z = 0
		self.timepoint = 0
		self.scatterHeight = 255
		self.scatterBitmap = None
		self.drawLegend = kws.get("drawLegend")
		# Legend width is the width / height of the scalar colorbar
		self.legendWidth = 24
		self.horizontalLegend = None
		self.verticalLegend = None
		self.scatterLegend = None
		if self.drawLegend:
			w, h = self.size
			h += self.legendWidth + self.emptySpace
			w += self.legendWidth * 2 + self.emptySpace * 4 + 10
			self.size = (w, h)
			size = (w, h)
		self.xoffset = 0
		if self.drawLegend:
			self.xoffset = self.legendWidth + self.emptySpace
			
		self.scatterCTF = None
		self.mode = (1, 2)
		
			
		self.lower1 = 127
		self.upper1 = 255
		self.lower2 = 127
		self.upper2 = 255
		
		self.middlestart = [0, 0]    
		self.zoomx = 1
		self.zoomy = 1
		self.action = 5
		self.countVoxels = 1
		self.renew = 1
		self.wholeVolume = 1
		self.logarithmic = 1
		self.scatter = None
		self.scatterplot = None
		
		
		InteractivePanel.InteractivePanel.__init__(self, parent, size = size, **kws)

		self.action = 5
		self.Bind(wx.EVT_PAINT, self.OnPaint)
		#self.Bind(wx.EVT_LEFT_UP,self.setThreshold)

		self.Bind(wx.EVT_RIGHT_DOWN, self.onRightClick)
		self.ID_COUNTVOXELS = wx.NewId()
		self.ID_WHOLEVOLUME = wx.NewId()
		self.ID_LOGARITHMIC = wx.NewId()
		self.ID_SAVE_AS = wx.NewId()
		self.menu = wx.Menu()
		self.SetScrollbars(0, 0, 0, 0)        
		messenger.connect(None, "threshold_changed", self.updatePreview)
		

		item = wx.MenuItem(self.menu, self.ID_LOGARITHMIC, "Logarithmic scale", kind = wx.ITEM_CHECK)
		self.Bind(wx.EVT_MENU, self.onSetLogarithmic, id = self.ID_LOGARITHMIC)
		self.menu.AppendItem(item)
		self.menu.Check(self.ID_LOGARITHMIC, 1)    
		
		self.menu.AppendSeparator()
		item = wx.MenuItem(self.menu, self.ID_SAVE_AS, "Save as...")
		self.Bind(wx.EVT_MENU, self.onSaveScatterplot, id = self.ID_SAVE_AS)
		self.menu.AppendItem(item)
		
		
		self.Bind(wx.EVT_LEFT_DOWN, self.markActionStart)
		self.Bind(wx.EVT_MOTION, self.updateActionEnd)
		self.Bind(wx.EVT_LEFT_UP, self.setThreshold)
		self.actionstart = None
		self.actionend = None
		self.buffer = wx.EmptyBitmap(256, 256)
		
		messenger.connect(None, "timepoint_changed", self.onUpdateScatterplot)
	
	def onSaveScatterplot(self, event):
		"""
		Created: 21.11.2006, KP
		Description: Save the scatterplot to a file
		"""
		if not self.scatterBitmap:
			return
		wcDict = {"png": "Portable Network Graphics Image (*.png)", "jpeg": "JPEG Image (*.jpeg)",
		"tiff": "TIFF Image (*.tiff)", "bmp": "Bitmap Image (*.bmp)"}
		#wc="PNG file|*.png|JPEG file|*.jpeg|TIFF file|*.tiff|BMP file|*.bmp"
	
		conf = Configuration.getConfiguration()    
		defaultExt = conf.getConfigItem("ImageFormat", "Output")
		if defaultExt == "jpg":
			defaultExt = "jpeg"
		if defaultExt == "tif":
			defaultExt = "tiff"
		
		if defaultExt not in wcDict:
			defaultExt = "png"
		initFile = "scatterplot.%s" % (defaultExt)            
		wc = wcDict[defaultExt] + "|*.%s" % defaultExt
		del wcDict[defaultExt]
		
		for key in wcDict.keys():
			wc += "|%s|*.%s" % (wcDict[key], key)
		#print "wc=",wc
		filename = Dialogs.askSaveAsFileName(self, "Save scatterplot", initFile, wc, "scatterImage")            
			
		ext = filename.split(".")[-1].lower()
		if ext == "jpg":ext = "jpeg"
		if ext == "tif":ext = "tiff"
		mime = "image/%s" % ext
		img = self.scatterBitmap.ConvertToImage()
		#print "Saving mimefile ",filename,mime
		img.SaveMimeFile(filename, mime)        
	
	def onUpdateScatterplot(self, evt, obj, *args):
		"""
		Created: 9.09.2005, KP
		Description: Update the scatterplot when timepoint changes
		"""        
		self.renew = 1
#        print "Setting timepoint to ",args[0]
		self.setTimepoint(args[0])
		self.updatePreview()
		
	def setScrollbars(self, xdim, ydim):
		"""
		Created: 24.03.2005, KP
		Description: Configures scroll bar behavior depending on the
					 size of the dataset, which is given as parameters.
		"""
		self.SetSize(self.size)
		self.SetVirtualSize(self.size)
		self.buffer = wx.EmptyBitmap(*self.size)
		
	def onRightClick(self, event):
		"""
		Created: 02.04.2005, KP
		Description: Method that is called when the right mouse button is
					 pressed down on this item
		"""      
		self.PopupMenu(self.menu, event.GetPosition())
		#menu.Destroy()
		
	def onSetLogarithmic(self, evt):
		"""
		Created: 12.07.2005, KP
		Description: Set the scale to logarithmic
		"""
		self.logarithmic = not self.logarithmic
		self.menu.Check(self.ID_LOGARITHMIC, self.logarithmic)
		self.renew = 1
		self.updatePreview()
		self.Refresh()
		
		
	def markActionStart(self, event):
		"""
		Created: 12.07.2005, KP
		Description: Sets the starting position of rubber band for zooming
		"""    
		pos = event.GetPosition()
		x, y = pos
		y = self.scatterHeight - y
		x -= self.xoffset
		x -= (self.verticalLegend.GetWidth() + 2 * self.emptySpace)
		
		if x > 255:x = 255
		if y > 255:y = 255
		if x < 0:x = 0
		if y < 0:y = 0       
		
		self.actionstart = (x, y)

		l1diff = abs(x - self.lower1)
		l2diff = abs(y - self.lower2)
		u1diff = abs(x - self.upper1)
		u2diff = abs(y - self.upper2)
		xmode = 0
		ymode = 0
		if l1diff < 45:
			xmode = 1
		if l2diff < 45:
			ymode = 2
			
		if l1diff > u1diff and u1diff < 45:
			# But if the user clicked closer to the upper threshold move that
			xmode = 3
		if l2diff > u2diff and u2diff < 45:
			# Same in y dir
			ymode = 4
		# If the user clicked "In the middle" (further than 30 pixels away from border)
		# Then just slide the thresholds
		
		#print "DIFFS=",(l1diff,u1diff),(l2diff,u2diff)
		if l2diff > 45 and u2diff > 45 and l1diff > 45 and l2diff > 45:
			ymode = 5
			xmode = 5
			self.middlestart[1] = y
			self.middlestart[0] = x
			#print "MODIFYING ALL"
		
		self.mode = (xmode, ymode)
		#print "MODE=",self.mode
		
	def updateActionEnd(self, event):
		"""
		Created: 12.07.2005, KP
		Description: Draws the rubber band to current mouse pos       
		"""
		if event.LeftIsDown():
			x, y = event.GetPosition()
			
			y = self.scatterHeight - y
#            x -= self.xoffset
			x -= self.xoffset
			x -= (self.verticalLegend.GetWidth() + 2 * self.emptySpace)            
			if x > 255:x = 255
			if y > 255:y = 255
			if x < 0:x = 0
			if y < 0:y = 0            
				
			self.actionend = (x, y)
			
			x1, y1 = self.actionstart
			x2, y2 = self.actionend
			if x2 < x1:
				x1, x2 = x2, x1
			if y2 < y1:
				y1, y2 = y2, y1
			reds = self.sources[0].getSettings()
			greens = self.sources[1].getSettings()
			
			gl, gu = greens.get("ColocalizationLowerThreshold"), greens.get("ColocalizationUpperThreshold")
			rl, ru = reds.get("ColocalizationLowerThreshold"), reds.get("ColocalizationUpperThreshold")
			
			#print "Greens now=",gl,gu
			#print "Reds now=",rl,ru
			
			#print "mode=",self.mode
			if self.mode[0] == 1:
				greens.set("ColocalizationLowerThreshold", x1)
				gl = x1
				if gl > gu:
					#print "\n--->LOWER GREEN SWITCHING gl=",gl,"gu=",gu
					gu, gl = gl, gu
				self.lower1 = gl
				#print "Setting lower of green to ",x1
			if self.mode[0] == 3:
				greens.set("ColocalizationUpperThreshold", x2)
				gu = x2
				if gl > gu:
					gu, gl = gl, gu                
				#print "Setting upper of green to ",x2
				#self.lower2=x2
				self.upper1 = x2
			if self.mode[1] == 2:
				reds.set("ColocalizationLowerThreshold", y1)
				rl = y1
				if rl > ru:
					#print "\n--->LOWER RED SWITCHING rl=",rl,"ru=",ru                
					ru, rl = rl, ru                
				#self.upper1=y1
				self.lower2 = y1
				#print "Setting lower of red to",y1
			elif self.mode[1] == 4:
				reds.set("ColocalizationUpperThreshold", y2)
				ru = y2
				if rl > ru:
					ru, rl = rl, ru                                
				self.upper2 = y2
				#print "Setting upper of red to",y2
				
			#self.actionstart=(gl,rl)
			#self.actionend=(gu,ru)
			self.actionstart = (gu, ru)
			self.actionend = (gl, rl)
 
			#messenger.send(None,"threshold_changed",(y1,y2),(x1,x2))
			#

			self.updatePreview()
			
		
	def setDataUnit(self, dataUnit):
		"""
		Created: 04.07.2005, KP
		Description: Sets the data unit that is displayed
		"""            
		InteractivePanel.InteractivePanel.setDataUnit(self, dataUnit)
		self.sources = dataUnit.getSourceDataUnits()
		self.settings = self.sources[0].getSettings()
		self.buffer = wx.EmptyBitmap(256, 256)
		self.updatePreview()
		
	def setVoxelCount(self, event):
		"""
		Created: 02.04.2005, KP
		Description: Method to set on / off the voxel counting mode of scattergram
		"""       
		self.countVoxels = event.Checked()
		self.renew = 1
		self.updatePreview()
		
			
	def setWholeVolume(self, event):
		"""
		Created: 02.04.2005, KP
		Description: Method to set on / off the construction of scattergram from 
					 the whole volume
		"""       
		self.wholeVolume = event.Checked()
		self.renew = 1
		self.updatePreview()
		
	def setThreshold(self, event = None):
		"""
		Created: 24.03.2005, KP
		Description: Sets the thresholds based on user's selection
		"""
		x1, y1 = self.actionstart
		x2, y2 = self.actionend
		if x2 < x1:
			x1, x2 = x2, x1
		if y2 < y1:
			y1, y2 = y2, y1

		minval, maxval = self.sources[0].getScalarRange()
		c = maxval / 255.0
		x1 = int(x1 * c)
		x2 = int(x2 * c)
		y1 = int(y1 * c)
		y2 = int(y2 * c)
		
		#print "Using %d-%d as green and %d-%d as red range"%(x1,x2,y1,y2)
		reds = self.sources[0].getSettings()
		greens = self.sources[1].getSettings()
		
		gl, gu = x1, x2
		rl, ru = y1, y2
		
		messenger.send(None, "threshold_changed", (gl, gu), (rl, ru))
		
		messenger.send(None, "data_changed", 1)

		self.renew = 1
		self.updatePreview()

		#self.Refresh()
		self.actionstart = None
		self.actionend = None
		self.mode = (0, 0)
		
	def setTimepoint(self, tp):
		"""
		Created: 11.07.2005, KP
		Description: Sets the timepoint to be shown
		"""    
		self.timepoint = tp
		
	def setZSlice(self, z):
		"""
		Created: 11.07.2005, KP
		Description: Sets the timepoint to be shown
		"""    
		self.z = z
		
	def setScatterplot(self, plot):
		"""
		Created: 11.07.2005, KP
		Description: Sets the scatterplot as vtkImageData
		"""    
		self.scatterplot = plot
		#print "Got coloc=",coloc
		x0, x1 = self.scatterplot.GetScalarRange()
		Logging.info("Scalar range of scatterplot=", x0, x1, kw = "processing")
		#self.ctf=ImageOperations.loadLUT("LUT/rainbow2.lut",None,(x0,x1))
		#print self.ctf
		
	def updatePreview(self, *args):
		"""
		Created: 25.03.2005, KP
		Description: A method that draws the scattergram
		"""
		width, height = self.size
		if self.renew and self.dataUnit:
			self.buffer = wx.EmptyBitmap(width, height)
			#Logging.info("Generating scatterplot of timepoint",self.timepoint)
			# Red on the vertical and green on the horizontal axis
			t1 = self.sources[1].getTimepoint(self.timepoint)
			t2 = self.sources[0].getTimepoint(self.timepoint)            
			self.scatter, ctf = ImageOperations.scatterPlot(t2, t1, -1, self.countVoxels,
			self.wholeVolume, dataunits = self.sources, logarithmic = self.logarithmic, timepoint = self.timepoint)
			self.scatter = self.scatter.Mirror(0)
			self.scatterHeight = self.scatter.GetHeight()
			self.scatterCTF = ctf
			
			self.renew = 0
		self.paintPreview()
		self.Refresh()

	def OnPaint(self, event):
		"""
		Created: 25.03.2005, KP
		Description: Does the actual blitting of the bitmap
		"""
		dc = wx.BufferedPaintDC(self, self.buffer)#,self.buffer)

	def paintPreview(self):
		"""
		Created: 25.03.2005, KP
		Description: Paints the scattergram
		"""
		dc = wx.BufferedDC(wx.ClientDC(self), self.buffer)
		dc.BeginDrawing()

		colour = self.parent.GetBackgroundColour()
		
		dc.SetBackground(wx.Brush(colour))
		dc.SetPen(wx.Pen(colour, 0))
		dc.SetBrush(wx.Brush(colour))
		dc.DrawRectangle(0, 0, self.size[0], self.size[1])
		if not self.scatter:
			dc.EndDrawing()
			dc = None
			return

		lower1 = int(self.sources[0].getSettings().get("ColocalizationLowerThreshold"))
		lower2 = int(self.sources[1].getSettings().get("ColocalizationLowerThreshold"))           
		upper1 = int(self.sources[0].getSettings().get("ColocalizationUpperThreshold"))
		upper2 = int(self.sources[1].getSettings().get("ColocalizationUpperThreshold"))
	
		#print "Painting preview, hresholds=",lower1,upper1,lower2,upper2
	
		minval, maxval = self.sources[0].getScalarRange()
		c = 255.0 / maxval
		#print "COEFF=",c
		if self.actionstart and self.actionend:
			x1, y1 = self.actionstart
			x2, y2 = self.actionend
			if x2 < x1:
				x1, x2 = x2, x1
			if y2 < y1:
				y1, y2 = y2, y1
			lower1, upper1 = x1, x2
			lower2, upper2 = y1, y2
			lower1 = int(lower1 * (1.0 / c))
			lower2 = int(lower2 * (1.0 / c))
			upper1 = int(upper1 * (1.0 / c))
			upper2 = int(upper2 * (1.0 / c))
			
			

		#print "Thresholds=",lower1,upper1,lower2,upper2
		bmp = self.scatter.ConvertToBitmap()
		
		self.scatterBitmap = bmp
		
		if not self.verticalLegend:
			verticalLegend = ImageOperations.paintCTFValues(self.sources[1].getColorTransferFunction(), height = 256, width = self.legendWidth, paintScalars = 1)
			self.verticalLegend = verticalLegend
		else:
			verticalLegend = self.verticalLegend
		if not self.horizontalLegend:
			horizontalLegend = ImageOperations.paintCTFValues(self.sources[0].getColorTransferFunction(), width = 256, height = self.legendWidth, paintScalars = 1)
			self.horizontalLegend = horizontalLegend
		else:
			horizontalLegend = self.horizontalLegend
		hzlw = verticalLegend.GetWidth() + 2 * self.emptySpace
	
		dc.DrawBitmap(verticalLegend, 0, 0)
		dc.DrawBitmap(horizontalLegend, self.xoffset + hzlw, bmp.GetHeight() + self.emptySpace)
		dc.DrawBitmap(bmp, self.xoffset + hzlw, 0, True)
		
		self.bmp = self.buffer

		slope = self.settings.get("Slope")
		intercept = self.settings.get("Intercept")
		dc.SetPen(wx.Pen(wx.Colour(255, 255, 255), 1))
		if slope and intercept:
			Logging.info("slope=", slope, "intercept=", intercept, kw = "dataunit")
			x = 255
			y = 255 - (255 * slope + intercept)
			
			dc.DrawLine(self.xoffset + hzlw, 255, self.xoffset + hzlw + x, y)
		
		#ymax = self.size[1]
		ymax = 255
		# These are the threshold lines
		dc.DrawLine(self.xoffset + hzlw + lower1 * c, 0, self.xoffset + hzlw + lower1 * c, 255)
		dc.DrawLine(self.xoffset + hzlw, ymax - lower2 * c, self.xoffset + 255 + hzlw, ymax - lower2 * c)
		dc.DrawLine(self.xoffset + hzlw + upper1 * c, 0, self.xoffset + hzlw + upper1 * c, 255)
		dc.DrawLine(self.xoffset + hzlw, ymax - upper2 * c, self.xoffset + hzlw + 255, ymax - upper2 * c)
		
		#dc.SetPen(wx.Pen(wx.Colour(0,0,255),2))
		# vertical line 
		#dc.DrawLine(self.xoffset+hzlw+lower1*c,ymax-upper2*c,self.xoffset+hzlw+lower1*c,ymax-lower2*c)
		# horizontal line
		#dc.DrawLine(self.xoffset+hzlw+lower1*c,ymax-lower2*c,self.xoffset+hzlw+upper1*c,ymax-lower2*c)
		# vertical line 2 
		#dc.DrawLine(self.xoffset+hzlw+upper1*c,ymax-upper2*c,self.xoffset+hzlw+upper1*c,ymax-lower2*c)
		# horizontal line 2
		#dc.DrawLine(self.xoffset+hzlw+lower1*c,ymax-upper2*c,self.xoffset+hzlw+upper1*c,ymax-upper2*c)
		
		borders = ImageOperations.getOverlayBorders(int((upper1 - lower1) * c) + 1, int((upper2 - lower2) * c) + 1, (0, 0, 255), 90, lineWidth = 2)
		borders = borders.ConvertToBitmap()
		
		overlay = ImageOperations.getOverlay(int((upper1 - lower1) * c), int((upper2 - lower2) * c), (0, 0, 255), 64)
		overlay = overlay.ConvertToBitmap()
		dc.DrawBitmap(overlay, self.xoffset + hzlw + lower1 * c, ymax - upper2 * c, 1)
		dc.DrawBitmap(borders, self.xoffset + hzlw + lower1 * c, ymax - upper2 * c, 1)
		
		if not self.scatterLegend:
			scatterLegend = ImageOperations.paintCTFValues(self.scatterCTF, width = self.legendWidth, height = 256, paintScale = 1)
			self.scatterLegend = scatterLegend
		else:
			scatterLegend = self.scatterLegend
		dc.DrawBitmap(scatterLegend, self.xoffset + hzlw + 255 + 2 * self.emptySpace, 0)
		
		dc.SetTextForeground(wx.Colour(255, 255, 255))
		dc.SetFont(wx.Font(9, wx.SWISS, wx.NORMAL, wx.NORMAL))
		dc.DrawText("%d" % lower2, 3, ymax - lower2 * c)
		dc.DrawText("%d" % lower1, self.xoffset + hzlw + lower1 * c, 265)
		self.lower1 = lower1 * c
		self.lower2 = lower2 * c
		self.upper1 = upper1 * c
		self.upper2 = upper2 * c
		
		
		self.dc = dc

		del self.dc
		dc.EndDrawing()
		dc = None
