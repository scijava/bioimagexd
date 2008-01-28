# -*- coding: iso-8859-1 -*-
"""
 Unit: ColorTransferEditor
 Project: BioImageXD
 Created: 30.10.2004, KP
 Description:

 A widget used to view and modify a color transfer function. The widget
 draws the graph of the function and allows the user to modify the function.

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
__version__ = "$Revision: 1.28 $"
__date__ = "$Date: 2005/01/13 14:52:39 $"

import wx.lib.buttons as buttons
import wx.lib.colourselect as csel
import GUI.Dialogs	
import lib.ImageOperations
import Logging
import scripting
import lib.messenger
import math
import os.path
try:
	import psyco
except:
	psyco = None
import time
import vtk
import wx


class CTFButton(wx.BitmapButton):
	"""
	Created: 18.04.2005, KP
	Description: A button that shows a ctf as a palette and lets the user modify it
				 by clicking on the button
	"""	   
	def __init__(self, parent, alpha = 0):
		"""
		Initialization
		"""	   
		wx.BitmapButton.__init__(self, parent, -1)
		self.changed = 0
		self.alpha = alpha
		self.ctf = vtk.vtkColorTransferFunction()
		self.ctf.AddRGBPoint(0, 0, 0, 0)
		self.ctf.AddRGBPoint(255, 1, 1, 1)
		self.bmp = lib.ImageOperations.paintCTFValues(self.ctf)
		self.SetBitmapLabel(self.bmp)
		self.Bind(wx.EVT_BUTTON, self.onModifyCTF)
		
	def isChanged(self):
		"""
		Was the ctf or otf changed
		"""		   
		return self.changed
		
	def setColorTransferFunction(self, ctf):
		"""
		Set the color transfer function that is edited
		"""	  
		self.ctf = ctf
		self.minval, self.maxval = ctf.GetRange()
		self.minval = int(self.minval)
		self.maxval = int(self.maxval)
		self.bmp = lib.ImageOperations.paintCTFValues(self.ctf)
		self.SetBitmapLabel(self.bmp)
		
	def getColorTransferFunction(self):
		"""
		Return the color transfer function that is edited
		"""		   
		return self.ctf
		
	def onModifyCTF(self, event):
		"""
		Modify the color transfer function
		"""		   
		dlg = wx.Dialog(self, -1, "Edit color transfer function")
		sizer = wx.BoxSizer(wx.VERTICAL)
		panel = ColorTransferEditor(dlg, alpha = self.alpha)
		panel.setColorTransferFunction(self.ctf)
		self.panel = panel
		sizer.Add(panel)
		dlg.SetSizer(sizer)
		dlg.SetAutoLayout(1)
		self.changed = 1
		sizer.Fit(dlg)
		dlg.ShowModal()
		self.bmp = lib.ImageOperations.paintCTFValues(self.ctf)
		self.SetBitmapLabel(self.bmp)
		lib.messenger.send(None, "data_changed", 0)
		lib.messenger.send(self, "ctf_modified")
		
	def getOpacityTransferFunction(self):
		"""
		Returns the opacity function
		"""
		return self.panel.getOpacityTransferFunction()
		
	def setOpacityTransferFunction(self, otf):
		"""
		Returns the opacity function
		"""
		return self.panel.setOpacityTransferFunction(otf)

class CTFPaintPanel(wx.Panel):
	"""
	Created: 16.04.2005, KP
	Description: A widget onto which the transfer function is painted
	"""
	def __init__(self, parent, **kws):
		self.maxx = 255
		self.maxy = 255
		self.scale = 1
		# maxval and minval are used in paintFreeMode and dont seem to be initialized anywhere. So lets make them None for now
		self.maxval = None	
		self.minval = None

		self.background = None
		
		self.xoffset = 16
		self.yoffset = 22
		if kws.has_key("width"):
			w = kws["width"]
		else:
			w = self.xoffset + self.maxx / self.scale
			w += 15
		if kws.has_key("height"):
			h = kws["height"]
		else:
			h = self.yoffset + self.maxy / self.scale
			h += 15
		wx.Panel.__init__(self, parent, -1, size = (w, h))
		self.buffer = wx.EmptyBitmap(w, h, -1)
		self.w = w
		self.h = h
		self.dc = None
		self.Bind(wx.EVT_PAINT, self.onPaint)
		

		
	def toGraphCoords(self, x, y, maxval):
		"""
		Returns x and y of the graph for given coordinates
		"""
		rx, ry = x - self.xoffset, self.maxy - (y - self.yoffset)
		
		
		xcoeff = maxval / self.maxx
		rx *= xcoeff
		
		if rx < 0:rx = 0
		if ry < 0:ry = 0
		if rx > maxval:rx = maxval
		if ry > maxval:ry = maxval
		return (rx, ry)
		
	def onPaint(self, event):
		dc = wx.BufferedPaintDC(self, self.buffer)
	def createLine(self, x1, y1, x2, y2, color = "WHITE", brush = None, **kws):
		"""
		Draws a line from (x1,y1) to (x2,y2). The method
					 takes into account the scale factor
		"""
		if brush:
			self.dc.SetBrush(brush)
		
		self.dc.SetPen(wx.Pen(color))
		# (x1,y1) and (x2,y2) are in coordinates where
		# origo is the lower left corner

		x12 = x1 + self.xoffset
		y12 = self.maxy - y1 + self.yoffset
		y22 = self.maxy - y2 + self.yoffset
		x22 = x2 + self.xoffset
		arr = None
		try:
			self.dc.DrawLine(x12 / self.scale, y12 / self.scale,
			x22 / self.scale, y22 / self.scale)
		except:
			Logging.info("Failed to draw line from %f/%f,%f/%f to %f/%f,%f/%f" % (x12, self.scale, y12, self.scale, x22, self.scale, y22, self.scale), kw = "ctf")
		if kws.has_key("arrow"):
			if kws["arrow"] == "HORIZONTAL":
				lst = [(x22 / self.scale - 3, y22 / self.scale - 3), (x22 / self.scale, y22 / self.scale), (x22 / self.scale - 3, y22 / self.scale + 3)]			
			elif kws["arrow"] == "VERTICAL":
				lst = [(x22 / self.scale - 3, y22 / self.scale + 3), (x22 / self.scale, y22 / self.scale), (x22 / self.scale + 3, y22 / self.scale + 3)]			
			
			self.dc.DrawPolygon(lst)
			

	def createOval(self, x, y, r, color = "GREY"):
		"""
		Draws an oval at point (x,y) with given radius
		"""
		self.dc.SetBrush(wx.Brush(color, wx.SOLID))
		self.dc.SetPen(wx.Pen(color))		 
		y = self.maxy - y + self.yoffset
		ox = x / self.scale
		ox += self.xoffset
		self.dc.DrawCircle(ox, y / self.scale, r)

	def createText(self, x, y, text, color = "WHITE", **kws):
		"""
		Draws a text at point (x,y) using the given font
		"""
		self.dc.SetTextForeground(color)
		self.dc.SetFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.NORMAL))

		useoffset = 1
		if kws.has_key("use_offset"):
			useoffset = kws["use_offset"]
		y = self.maxy - y
		if useoffset:
			y += self.yoffset
		ox = x / self.scale
		if useoffset:
			ox += self.xoffset
		self.dc.DrawText(text, ox, y / self.scale)
		
	def drawBackground(self, minval, maxval):
		"""
		Paint the background for the CTF as a bitmap so it won't have to be done each time
		"""		   
		olddc = self.dc
		dc = wx.MemoryDC()
		self.dc = dc
		x0, y0, w, h = self.GetClientRect()
		bmp = wx.EmptyBitmap(w, h)
		dc.SelectObject(bmp)
		dc.SetBackground(wx.Brush("BLACK"))
		dc.Clear()
		
		dc.BeginDrawing()

		self.createLine(0, 0, 0, self.maxy + 5, arrow = "VERTICAL")
		self.createLine(0, 0, self.maxx + 5, 0, arrow = "HORIZONTAL")

		for i in range(32, self.maxx, 32):
			# Color gray and stipple with gray50
			self.createLine(i, 0, i, self.maxy, 'GREY', wx.LIGHT_GREY_BRUSH)
			self.createLine(0, i, self.maxx, i, 'GREY', wx.LIGHT_GREY_BRUSH)		

		textcol = "GREEN"
		self.createText(0, -5, "0", textcol)
		
		halfval = int((maxval - minval) / 2)
		self.createText(self.maxx / 2, -5, "%d" % halfval, textcol)
		self.createText(self.maxx, -12, "%d" % maxval, textcol)

		self.createText(-10, self.maxy / 2, "127", textcol)
		self.createText(-10, self.maxy, "255", textcol)
		self.dc.EndDrawing()
		dc.EndDrawing()
		dc.SelectObject(wx.NullBitmap)
		self.dc = olddc
		return bmp
	
	def paintFreeMode(self, redfunc, greenfunc, bluefunc, alphafunc, maximumValue = -1):
		"""
		Paints the graph of the function specified as a list of all values of the function		   
		"""
		self.dc = wx.MemoryDC()
		self.dc.SelectObject(self.buffer)

		d = self.maxx / float(maximumValue)
		if d < 1:d = 1
		if not self.background:
			Logging.info("Constructing background from minval = %d, maxval = %d" % (self.minval, self.maxval))
			self.background = self.drawBackground(self.minval, self.maxval)
		self.dc.BeginDrawing()
		self.dc.DrawBitmap(self.background, 0, 0)
		coeff = float(self.maxx) / maximumValue

		redline = [(int(x * coeff), self.maxy - y) for x, y in enumerate(redfunc)]
		greenline = [(int(x * coeff), self.maxy - y) for x, y in enumerate(greenfunc)]
		blueline = [(int(x * coeff), self.maxy - y) for x, y in enumerate(bluefunc)]
		alphaline = [(int(x * coeff), self.maxy - y) for x, y in enumerate(alphafunc)]
		
		self.dc.SetPen(wx.Pen(wx.Colour(255, 0, 0), 1))
		self.dc.DrawLines(redline, self.xoffset, self.yoffset)
		self.dc.SetPen(wx.Pen(wx.Colour(0, 255, 0), 1))
		self.dc.DrawLines(greenline, self.xoffset, self.yoffset)
		self.dc.SetPen(wx.Pen(wx.Colour(0, 0, 255), 1))
		self.dc.DrawLines(blueline, self.xoffset, self.yoffset)
		self.dc.SetPen(wx.Pen(wx.Colour(255, 255, 255), 1))
		self.dc.DrawLines(alphaline, self.xoffset, self.yoffset)
		
		self.dc.SelectObject(wx.NullBitmap)
		self.dc = None		  
		
		
	def paintTransferFunction(self, alphaMode = None, selectedPoint = None, red = [], green = [], blue = [], maximumValue = -1, alpha = [], drawAlpha = 0):
		"""
		Paints the graph of the function specified by points in the graph
		"""
		(r, rv), (g, gv), (b, bv) = red[-1], green[-1], blue[-1]
		a = 0
		
		if alpha and drawAlpha:
			(a, av) = alpha[-1]
		maxval = max(r, g, b, a)
		
		(r, rv), (g, gv), (b, bv) = red[0], green[0], blue[0]
		a = maximumValue
		if alpha and drawAlpha:
			(a, av) = alpha[0]
		minval = min(r, g, b, a)
			
		d = maxval / float(self.maxx)
		if d < 1:d = 1
		self.dc = wx.MemoryDC()		   
		self.dc.SelectObject(self.buffer)
		self.dc.BeginDrawing()

		self.dc.Clear()
		
		if not self.background:
			self.background = self.drawBackground(minval, maxval)
				
		x0, y0, w, h = self.GetClientRect()
		self.dc.DrawBitmap(self.background, 0, 0)
		ax0, rx0, gx0, bx0 = 0, 0, 0, 0
		r0, g0, b0, a0 = 0, 0, 0, 0
		coeff = float(self.maxx) / maxval
			
		if selectedPoint:
			x, y = selectedPoint
			x *= coeff
			self.createOval(x, y, 2, (255, 255, 255))		 

		
		n = max(len(red), len(green), len(blue), len(alpha))
		
		for i in range(n):
			try:
				rx, r = red[i]
				rx *= coeff   
				self.createOval(rx, r, 2)
			except:
				r, rx = r0, rx0
			try:
				gx, g = green[i]
				gx *= coeff
				self.createOval(gx, g, 2)
			except:
				g, gx = g0, gx0
			try:
				bx, b = blue[i]
				bx *= coeff
				self.createOval(bx, b, 2)
			except:
				b, bx = b0, bx0
			if drawAlpha and alpha:
				try:
					ax, a = alpha[i]
					ax *= coeff
					self.createOval(ax, a, 2)
				except:
					a, ax = a0, ax0
			
			
			if drawAlpha and alpha:
				self.createLine(ax0, a0, ax, a, '#ffffff')
 
			if not alphaMode:
				self.createLine(rx0,r0,rx,r,'#ff0000')
				self.createLine(gx0, g0, gx, g, '#00ff00')
				self.createLine(bx0,b0,bx,b,'#0000ff')
			rx0, gx0, bx0 = rx, gx, bx
			r0, g0, b0 = r, g, b
			a0 = a
			#ax0 = ax
			if alpha and drawAlpha:
				ax0 = ax
		if abs(rx0 / coeff - maximumValue) > 0.5:
			self.createLine(rx0, r0, self.maxx, 0, '#ff0000')
		if abs(gx0/coeff - maximumValue)>0.5:
			self.createLine(gx0,g0,self.maxx, 0,'#00ff00')
		if abs(bx0 / coeff - maximumValue) > 0.5:
			self.createLine(bx0, b0, self.maxx, 0, '#0000ff')
		if abs(ax0/coeff - maximumValue)>0.5:
			self.createLine(ax0,a0,self.maxx, 0,'#ffffff')			  
		self.dc.SelectObject(wx.NullBitmap)
		self.dc = None
		
		

class CTFValuePanel(wx.Panel):
	"""
	Created: 17.04.2005, KP
	Description: A widget onto which the colors transfer function is painted
	"""
	def __init__(self, parent):
		self.lineheight = 32
		w, h = (256 + 16, self.lineheight)
		self.w, self.h = w, h
		wx.Panel.__init__(self, parent, -1, size = (w, h))
		self.buffer = wx.EmptyBitmap(w, h, -1)
		self.Bind(wx.EVT_PAINT, self.onPaint)		 
		self.xoffset = 16
		self.yoffset = 0
		
	def onPaint(self, event):
		dc = wx.BufferedPaintDC(self, self.buffer)
	def paintTransferFunction(self, ctf, pointlist = []):
		"""
		Paints the graph of the function specified by the six points
		"""
		dc = wx.MemoryDC()
		dc.SelectObject(self.buffer)
		dc.SetBackground(wx.Brush(self.GetBackgroundColour()))
		dc.Clear()
		dc.BeginDrawing()
		bmp = lib.ImageOperations.paintCTFValues(ctf, height = self.lineheight)
		dc.DrawBitmap(bmp, self.xoffset, 0)
		dc.EndDrawing()
		dc.SelectObject(wx.NullBitmap)
			   
		
class ColorTransferEditor(wx.Panel):
	"""
	Created: 30.10.2004, KP
	Description: A widget used to view and modify an intensity transfer function
	"""
	def __init__(self, parent, **kws):
		"""
		Initialization
		"""
		self.parent = parent
		self.selectedPoint = None
		self.hasPainted = 0
		wx.Panel.__init__(self, parent, -1)
		self.updateT = 0
		if kws.has_key("alpha"):
			self.alpha = kws["alpha"]
		self.updateCallback = 0
		self.ctf = vtk.vtkColorTransferFunction()
		self.doyield = 1
		self.calling = 0
		self.guiupdate = 0
		self.freeMode = 0
		self.selectThreshold = 35.0
		self.ptThreshold = 0.1
		self.color = 0
		self.modCount = 0
		self.minval = 0
		self.maxval = 255
		self.otf = vtk.vtkPiecewiseFunction()
		self.restoreDefaults()
		self.mainsizer = wx.BoxSizer(wx.VERTICAL)

		self.canvasBox = wx.BoxSizer(wx.VERTICAL)
		
		self.value = CTFValuePanel(self)
		self.canvasBox.Add(self.value, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
		
		self.canvas = CTFPaintPanel(self)
		self.canvasBox.Add(self.canvas, 1, wx.ALL | wx.EXPAND, 10)

		self.mainsizer.Add(self.canvasBox)
		
		self.itemBox = wx.BoxSizer(wx.HORIZONTAL)
		
		self.alphaMode = 0
		
		self.redBtn = buttons.GenToggleButton(self, -1, "", size = (32, 32))
		self.redBtn.SetValue(1)
		self.redBtn.SetBackgroundColour((255, 0, 0))
		self.greenBtn = buttons.GenToggleButton(self, -1, "", size = (32, 32))
		self.greenBtn.SetBackgroundColour((0, 255, 0))
		self.blueBtn = buttons.GenToggleButton(self, -1, "", size = (32, 32))
		self.blueBtn.SetBackgroundColour((0, 0, 255))
		
		if self.alpha:
			self.alphaBtn = buttons.GenToggleButton(self, -1, "Alpha", size = (32, 32))
			self.alphaBtn.Bind(wx.EVT_BUTTON, self.onEditAlpha)
			self.alphaBtn.SetBackgroundColour((255, 255, 255))
		iconpath = scripting.get_icon_dir()		   
		self.freeBtn = buttons.GenBitmapToggleButton(self, -1, None)
		self.freeBtn.SetBestSize((32, 32))
		bmp = wx.Image(os.path.join(iconpath, "draw.gif"), wx.BITMAP_TYPE_GIF).ConvertToBitmap()
		self.freeBtn.SetBitmapLabel(bmp)
		self.colorBtn = csel.ColourSelect(self, -1, "", size = (32, 32))
		self.colorBtn.Bind(csel.EVT_COLOURSELECT, self.onSetToColor)

		openGif = wx.Image(os.path.join(iconpath, "open.gif"), wx.BITMAP_TYPE_GIF).ConvertToBitmap()
		saveGif = wx.Image(os.path.join(iconpath, "save.gif"), wx.BITMAP_TYPE_GIF).ConvertToBitmap()
		self.openBtn = wx.BitmapButton(self, -1, openGif, size = (32, 32))
		self.saveBtn = wx.BitmapButton(self, -1, saveGif, size = (32, 32))
		
		self.maxNodes = wx.SpinCtrl(self, -1, "4096", min = 2, max = 9999, size = (54, -1), style = wx.TE_PROCESS_ENTER)
		self.maxNodes.SetToolTip(wx.ToolTip("Set the maximum number of nodes in the graph."))
		self.maxNodes.SetHelpText("Use this control to set the maximum number of nodes in the graph. This is useful if you have a hand drawn palette that you wish to edit by dragging the nodes.")
		self.maxNodes.Bind(wx.EVT_SPINCTRL, self.onSetMaxNodes)
		self.maxNodes.Bind(wx.EVT_TEXT_ENTER, self.onSetMaxNodes)
		
		self.itemBox.Add(self.redBtn)
		self.itemBox.Add(self.greenBtn)
		self.itemBox.Add(self.blueBtn)
		if self.alpha:
			self.itemBox.Add(self.alphaBtn)
		
		self.itemBox.Add(self.freeBtn)
		self.itemBox.Add(self.colorBtn)
		self.itemBox.Add(self.openBtn)
		self.itemBox.Add(self.saveBtn)
		self.itemBox.Add(self.maxNodes)
		
		self.redBtn.Bind(wx.EVT_BUTTON, self.onEditRed)
		self.greenBtn.Bind(wx.EVT_BUTTON, self.onEditGreen)
		self.blueBtn.Bind(wx.EVT_BUTTON, self.onEditBlue)
		
		self.freeBtn.Bind(wx.EVT_BUTTON, self.onFreeMode)
		
		self.openBtn.Bind(wx.EVT_BUTTON, self.onOpenLut)
		self.saveBtn.Bind(wx.EVT_BUTTON, self.onSaveLut)
		
		self.mainsizer.Add(self.itemBox)

		self.SetAutoLayout(True)
		self.SetSizer(self.mainsizer)
		self.mainsizer.SetSizeHints(self)

		self.upToDate = 0
		self.canvas.Bind(wx.EVT_LEFT_DOWN, self.onEditFunction)
		self.canvas.Bind(wx.EVT_LEFT_UP, self.updateCTFView)
		self.canvas.Bind(wx.EVT_LEFT_DCLICK, self.onDeletePoint)
		
		self.canvas.Bind(wx.EVT_RIGHT_DOWN, self.onCreatePoint)
		self.canvas.Bind(wx.EVT_MOTION, self.onDrawFunction)
		
		self.pos = (0, 0)
		
		if psyco and 0:
			psyco.bind(self.onSetMaxNodes)
			psyco.bind(self.onDrawFunction)
			psyco.bind(self.onEditFunction)
			psyco.bind(self.updateGraph)
			psyco.bind(self.setFromColorTransferFunction)
			psyco.bind(self.getPointsFromFree)
		
	def onSetMaxNodes(self, evt):
		"""
		Sets the maximum number of nodes
		"""				   
		n = len(self.points)
		tot = 0
		for i, pts in enumerate(self.points):
			tot += len(pts)
		
		maxpts = self.maxNodes.GetValue()
		if maxpts >= tot:
			return
		everyNth = float(tot) / maxpts
		Logging.info("Removing every %f pts (pts=%d)" % (everyNth, maxpts))
		n = 0
		k = 1
		toRemove = []
		for i, pts in enumerate(self.points):
			for j, point in enumerate(pts):
				firstOrLast = (j == 0 or j == len(pts) - 1)
				n += 1
				if not firstOrLast and k < everyNth:
					toRemove.append(point)
					k += 1
				else:
					k = 1
			for point in toRemove:
				pts.remove(point)
			toRemove = []
		
		tot = 0
		for i, pts in enumerate(self.points):
			tot += len(pts)
		Logging.info("Points left = %d" % tot)
		self.upToDate = 0
		self.updateGraph()
				
		
		
		
		
	def onDeletePoint(self, event):
		"""
		Delete the selected point
		"""		   
		if self.selectedPoint:
			for i, pts in enumerate(self.points):
				if self.selectedPoint in pts:
					pts.remove(self.selectedPoint)
			self.selectedPoint = None
			self.upToDate = 0			 
			self.updateGraph()
			
	def setAlphaMode(self, flag):
		"""
		Show only alpha channel
		"""
		self.alphaMode = flag
		
		self.colorBtn.Show(flag)
		self.redBtn.Show(flag)
		self.greenBtn.Show(flag)
		self.blueBtn.Show(flag)
		self.updateGraph()
		
	def onSaveLut(self, event):
		"""
		Save a lut file
		"""	   
		wc = "BioImageXD lookup table (*.bxdlut)|*.bxdlut|ImageJ Lookup table (*.lut)|*.lut"
		filename = GUI.Dialogs.askSaveAsFileName(self, "Save lookup table", "palette.bxdlut", wc, "palette")
	
		if filename:
			lib.ImageOperations.saveLUT(self.ctf, filename)

	def onOpenLut(self, event):
		"""
		Load a lut file
		"""	  
		wc = "BioImageXD lookup table (*.bxdlut)|*.bxdlut|ImageJ Lookup table (*.lut)|*.lut" 
		filename = GUI.Dialogs.askOpenFileName(self, "Load lookup table", wc, filetype = "palette")
		if filename:
			filename = filename[0]
			Logging.info("Opening palette", filename, kw = "ctf")
			self.freeMode = 0
			lib.ImageOperations.loadLUT(filename, self.ctf)
			self.setFromColorTransferFunction(self.ctf)
			self.getPointsFromFree()
			self.upToDate = 0
			self.updateGraph()
		
	def onSetToColor(self, event):
		"""
		Set the ctf to be a specific color
		"""	   
		col = event.GetValue()
		color = col.Red(), col.Green(), col.Blue()
		if 255 not in color:
			mval = max(color)
			coeff = 255.0 / mval
			ncolor = [int(x * coeff) for x in color]
			Logging.info("New color = ", ncolor, kw = "ctf")
			dlg = wx.MessageDialog(self,
				"The color you selected: %d,%d,%d is incorrect."
				"At least one of the R, G or B components\n"
				"of the color must be 255. Therefore, "
				"I have modified the color a bit. "
				"It is now %d,%d,%d. Have a nice day." % (color[0],
				color[1], color[2], ncolor[0], ncolor[1], ncolor[2]), "Selected color is incorrect", wx.OK | wx.ICON_WARNING)
			dlg.ShowModal()
			dlg.Destroy()
			color = ncolor
		r, g, b = color
		
		self.redpoints = [(0, 0), (self.maxval, r)]
		self.greenpoints = [(0, 0), (self.maxval, g)]
		self.bluepoints = [(0, 0), (self.maxval, b)]
		self.points = [self.redpoints, self.greenpoints, self.bluepoints, self.alphapoints]
		self.freeMode = 0
		self.upToDate = 0
		self.updateGraph()
		self.updateCTFView()
		lib.messenger.send(None, "data_changed", 0)
		self.colorBtn.SetColour(col)
		
		
	def onCreatePoint(self, event):
		"""
		Add a point to the function
		"""	   
		x, y = event.GetPosition()
		x, y = self.canvas.toGraphCoords(x, y, self.maxval)
		if not self.freeMode:
			d = 10
			currd = self.maxval
			hasx = 0
			pt = (x, y)
			self.points[self.color].append(pt)
			self.points[self.color].sort()
			self.upToDate = 0
			self.updateGraph()

		

	def onEditFunction(self, event):
		"""
		Edit the function
		"""	   
		x, y = event.GetPosition()
		x, y = self.canvas.toGraphCoords(x, y, self.maxval)
		if self.freeMode:
			self.pos = (x, y)
		else:
			d = 0
			currd = 99999999
			hasx = 0
			Logging.info("points for color %d = " % self.color, self.points[self.color])
			for pt in self.points[self.color]:
				d = self.dist((x, y), pt)
				if pt[0] == x:hasx = 1
				if d < self.selectThreshold and d < currd:
					self.selectedPoint = pt
					currd = d
					self.upToDate = 0
					break
				
	def dist(self, p1, p2):
		"""
		Return the distance between points p1 and p2
		"""		   
		return math.sqrt( (p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)
	
	def drawFreeMode(self, event):
		"""
		"""
		x, y = event.GetPosition()
		x, y = self.canvas.toGraphCoords(x, y, self.maxval)
		if y <= 0:y = 0
		if y >= 255:y = 255
		if x <= 0:x = 0
		if x >= self.maxval:x = self.maxval
		
		self.hasPainted = 1
		update = 0
		if self.pos[0]:
			x0 = min(self.pos[0], x)
			x1 = max(self.pos[0], x)
			n = (x1 - x0)
			if n:
				d = abs(y - self.pos[1]) / float(n)
				if x > self.pos[0] and y < self.pos[1]:d *= -1
				if x < self.pos[0] and y > self.pos[1]:d *= -1
			
				for i in range(x0, x1):
					ny = int(y + (i - x0) * d)
					if ny < 0:ny = 0
					if ny >= 255:ny = 255
					
					val = self.funcs[self.color][i]
					if val != ny:
						self.funcs[self.color][i] = ny
						update = 1
		
		
		val = self.funcs[self.color][x]
		if val != y:
			self.funcs[self.color][x] = y
			
			update = 1
		if update:
			self.updateGraph()	   
			self.upToDate = 0
			
		self.pos = (x, y)
		if not self.upToDate:
			wx.FutureCall(250	, self.updateCTFFromPoints)
		
	def modifyPoint(self, oldPoint, newPoint):
		"""
		move the given point to a new position
		"""
		removed = 0
		if oldPoint in self.points[self.color]:
			self.modCount -= 1
			self.points[self.color].remove(oldPoint)
					
		for i, (x, y) in enumerate(self.points[self.color]):
		
			if x > newPoint[0] and self.points[self.color][i - 1][0] < x:
				k = i
				if k == 0:k = 1
				
				self.points[self.color].insert(k, newPoint)
				self.modCount += 1
				self.selectedPoint = newPoint
				return
		self.points[self.color].append(newPoint)
		self.selectedPoint = newPoint
		self.modCount += 1
		 
			
	
	def onDrawFunction(self, event):
		"""
		Draw the function
		"""		   
		if event.Dragging():
			if self.freeMode:		 
				self.drawFreeMode(event)
			else:
				x, y = event.GetPosition()
				x, y = self.canvas.toGraphCoords(x, y, self.maxval)
	
	
				if self.selectedPoint:
					self.modifyPoint(self.selectedPoint, (x, y))
					self.upToDate = 0
					self.updateGraph()					  
				return
   
	def updatePreview(self):
		"""
		Send an event updating the preview
		"""			   
		if abs(time.time() - self.updateT) > 0.5:
			self.updateT = time.time()
			lib.messenger.send(None, "data_changed", 0)
	
	def onFreeMode(self, event):
		"""
		Toggle free mode on / off
		"""
		was = 0
		if self.freeMode:was = 1
		if not was and event.GetIsDown():
			self.updateCTFFromPoints()
			self.updateGraph()
			self.freeMode = 1
			
			self.setFromColorTransferFunction(self.ctf, self.otf)
			
		
		if was:
			self.updateCTFFromPoints()
		self.freeMode = event.GetIsDown()
		if not self.freeMode and was and self.hasPainted:
			Logging.info("Analyzing free mode for points", kw = "ctf")
			
			self.getPointsFromFree()
			n = len(self.points)
			tot = 0
			for i, pts in enumerate(self.points):
				tot += len(pts)
			
			maxpts = self.maxNodes.GetValue()
			if maxpts < tot:
				self.onSetMaxNodes(None)
		self.updateGraph()
				
	def onEditRed(self, event):
		"""
		Edit the red channel
		"""
		self.blueBtn.SetValue(0)
		self.greenBtn.SetValue(0)
		if self.alpha:self.alphaBtn.SetValue(0)
		self.color = 0
		self.updateGraph()

	def onEditAlpha(self, event):
		"""
		Edit the alpha channel
		"""
		self.blueBtn.SetValue(0)
		self.greenBtn.SetValue(0)
		self.redBtn.SetValue(0)
		Logging.info("Editing alpha channel")
		self.color = 3
		self.updateGraph()
		
	def onEditGreen(self, event):
		"""
		Edit the red channel
		"""
		self.blueBtn.SetValue(0)
		self.redBtn.SetValue(0)
		if self.alpha:self.alphaBtn.SetValue(0)
		self.color = 1
		self.updateGraph()

	def onEditBlue(self, event):
		"""
		Edit the red channel
		"""
		self.redBtn.SetValue(0)
		self.greenBtn.SetValue(0)
		if self.alpha:self.alphaBtn.SetValue(0)
		self.color = 2
		self.updateGraph()


	def restoreDefaults(self, event = None):
		"""
		Restores the default settings for this widget
		"""
		self.redfunc = [0] * (self.maxval + 1)
		self.greenfunc = [0] * (self.maxval + 1)
		self.bluefunc = [0] * (self.maxval + 1)
		self.alphafunc = [0] * (self.maxval + 1)
		self.funcs = [self.redfunc, self.greenfunc, self.bluefunc, self.alphafunc]
		
		self.redpoints = [(0, 0), (self.maxval, 255)]
		self.greenpoints = [(0, 0), (self.maxval, 255)]
		self.bluepoints = [(0, 0), (self.maxval, 255)]
		self.alphapoints = [(0, 0), (self.maxval, 51)]
		self.points = [self.redpoints, self.greenpoints, self.bluepoints, self.alphapoints]
		for i in xrange(0, self.maxval):
			self.redfunc[i] = i
			self.greenfunc[i] = i
			self.bluefunc[i] = i
			self.alphafunc[i] = int(i * 0.2)
		self.upToDate = 0
		self.ctf.RemoveAllPoints()
		
			
	def updateGraph(self):
		"""
		Clears the canvas and repaints the function
		"""		  
		if self.freeMode:
			self.canvas.paintFreeMode(self.redfunc, self.greenfunc, self.bluefunc, self.alphafunc, maximumValue = self.maxval)
		else:
			self.canvas.paintTransferFunction(self.alphaMode, self.selectedPoint, red = self.redpoints, green = self.greenpoints, blue = self.bluepoints, alpha = self.alphapoints, drawAlpha = self.alpha, maximumValue = self.maxval)
		self.canvas.Refresh()
		
		
	def updateCTFView(self, evt = None):
		"""
		Update the palette view of the ctf
		"""
		self.selectedPoint = None
		if self.upToDate:
			return
		if not self.freeMode:
			self.updateCTFFromPoints()
		self.value.paintTransferFunction(self.ctf)
		self.upToDate = 1
		self.value.Refresh()
		self.updatePreview()

	def updateCTFFromPoints(self):
		"""
		Updates the CTF from the values edited in points mode
		"""
		self.ctf.RemoveAllPoints()
		self.otf.RemoveAllPoints()
		if self.freeMode:
			for i in xrange(0, self.maxval):
				r, g, b = self.redfunc[i], self.greenfunc[i], self.bluefunc[i]
				r /= 255.0
				g /= 255.0
				b /= 255.0
				self.ctf.AddRGBPoint(i, r, g, b)
				if self.alpha:
					a = self.alphafunc[i]
					a /= 255.0
					self.otf.AddPoint(i, a)
		else:
			func = []
			for i in range(int(self.maxval + 1)):
				func.append([0, 0, 0, 0])
			self.points = [self.redpoints, self.greenpoints, self.bluepoints, self.alphapoints]			   
			for col, pointlist in enumerate(self.points):
				pointlist.sort()
				for i in xrange(1, len(pointlist)):
					x1, y1 = pointlist[i - 1]
					x2, y2 = pointlist[i]
					
					dx = x2 - x1
					if dx and (y2 != y1):
						dy = (y2 - y1) / float(dx)
					else:dy = 0
					if x2 > self.maxval:
						x2 = self.maxval
						x1 = x1 - 1
						
					for x in range(int(x1), int(x2 + 1)):
						func[x][col] = y1 + (x - x1) * dy
						
			ctfmax = 0
			for i in xrange(int(self.maxval + 1)):
				r, g, b, a = func[i]
				r /= 255.0
				g /= 255.0
				b /= 255.0
				a /= 255.0
				self.ctf.AddRGBPoint(i, r, g, b)
				if self.alpha:
					self.otf.AddPoint(i, a)
				ctfmax = i
				
			
	def getColorTransferFunction(self):
		"""
		Returns the color transfer function
		"""
		return self.ctf
		
	def setFromColorTransferFunction(self, TF, otf = None):
		"""
		Sets the colors of this graph
		"""
		
		self.minval, self.maxval = TF.GetRange()
		self.background = None
		
		self.minval = int(self.minval)
		self.maxval = int(self.maxval)
		
		self.redfunc = [0] * (self.maxval + 1)
		self.greenfunc = [0] * (self.maxval + 1)
		self.bluefunc = [0] * (self.maxval + 1)
		self.alphafunc = [0] * (self.maxval + 1)
		self.funcs = [self.redfunc, self.greenfunc, self.bluefunc, self.alphafunc]
		
		for i in range(self.maxval + 1):
			val = [0, 0, 0]
			TF.GetColor(i, val)
			
			r, g, b = val
			r *= 255
			g *= 255
			b *= 255
			
			r = int(r)
			g = int(g)
			b = int(b)
			
			self.redfunc[i] = r
			self.greenfunc[i] = g
			self.bluefunc[i] = b  
			if otf:
				a = otf.GetValue(i)
				self.alphafunc[i] = int(a * 255)
		self.updateCTFView()
	@staticmethod
	def slope(x0, y0, x1, y1):
		return float((y1 - y0)) / float((x1 - x0))

	def getPointsFromFree(self):
		"""
		Method that analyzes the color transfer function to
					 determine where to insert control points for the user
					 to edit
		"""
		xr0, xg0, xb0, xa0 = 0, 0, 0, 0
		kr, kg, kb, ka = 1, 1, 1, 1
		yr0, yg0, yb0, ya0 = 0, 0, 0, 0
		r0, g0, b0, a0 = 0, 0, 0, 0
		self.redpoints = []
		self.greenpoints = []
		self.bluepoints = []
		self.alphapoints = []
		
		# Go through each intensity value
		for x in range(int(self.maxval + 1)):
			if self.alpha:
				a = self.otf.GetValue(x)
				a *= self.maxval
				a = int(a)
				
			# Read the color from the CTF
			val = [0, 0, 0]
			self.ctf.GetColor(x, val)
			r, g, b = val
			
			# Convert the value to range 0-255 (from 0.0 - 1.0)
			r *= self.maxval
			g *= self.maxval
			b *= self.maxval
			r = int(r)
			g = int(g)
			b = int(b)
			if x == 0:
				r0, g0, b0 = r, g, b
				if self.alpha:
					a0 = a
			if x == 1:
				kr = ColorTransferEditor.slope(0, r0, 1, r)
				kg = ColorTransferEditor.slope(0, g0, 1, g)
				kb = ColorTransferEditor.slope(0, b0, 1, b)
				if self.alpha:
					ka = ColorTransferEditor.slope(0, a0, 1, a)
				
			if x in [0, int(self.maxval)]:
				self.redpoints.append((x, r))
				self.greenpoints.append((x, g))
				self.bluepoints.append((x, b))
				if self.alpha:
					self.alphapoints.append((x, a))
			elif x > 1:
				
				k = ColorTransferEditor.slope(xr0, r0, x, r)
				if abs(k - kr) > self.ptThreshold and x > xr0 + 1 and r != r0:
					self.redpoints.append((x, r))
					kr = k
					xr0 = x
					r0 = r
				k = ColorTransferEditor.slope(xg0, g0, x, g)	   
				
				if abs(k - kg) > self.ptThreshold and x > xg0 + 1 and g != g0:
					self.greenpoints.append((x, g))
					kg = k
					xg0 = x
					g0 = g
				k = ColorTransferEditor.slope(xb0, b0, x, b)					
				if abs(k - kb) > self.ptThreshold and x > xb0 + 1 and  b != b0:
					self.bluepoints.append((x, b))
					kb = k
					xb0 = x
					b0 = b
					
				if self.alpha:
					k = ColorTransferEditor.slope(xa0, a0, x, a)					
					if abs(k - ka) > self.ptThreshold and x > xa0 + 1 and a != a0:
						self.alphapoints.append((x, a))
						ka = k
						xa0 = x
						a0 = a				  
	   

		coeff = 255.0 / self.maxval
		
		
		self.redpoints = [(x, coeff * y) for (x, y) in self.redpoints]
		self.greenpoints = [(x, coeff * y) for (x, y) in self.greenpoints]
		self.bluepoints = [(x, coeff * y) for (x, y) in self.bluepoints]
		self.alphapoints = [(x, coeff * y) for (x, y) in self.alphapoints]
		self.points = [self.redpoints, self.greenpoints, self.bluepoints, self.alphapoints]
		self.updateGraph()
			
	def setColorTransferFunction(self, TF):
		"""
		Sets the color transfer function that is configured
					 by this widget
		"""
		self.ctf = TF
		self.minval, self.maxval = TF.GetRange()
		self.canvas.background = None
		self.getPointsFromFree()
		self.alphapoints = [(0, 0), (self.maxval, 51)]
		self.points = [self.redpoints, self.greenpoints, self.bluepoints, self.alphapoints]
		val = [0, 0, 0]
		self.ctf.GetColor(self.maxval, val)
		r, g, b = val
		r *= 255
		g *= 255
		b *= 255
		col = wx.Colour(int(r), int(g), int(b))
		self.colorBtn.SetColour(((int(r), int(g), int(b))))
		self.colorBtn.Refresh()

		self.updateGraph()
		self.updateCTFView()
		
	def getOpacityTransferFunction(self):
		"""
		Returns the opacity function
		"""
		return self.otf
		
	def setOpacityTransferFunction(self, otf):
		"""
		Returns the opacity function
		"""
		if otf == self.otf:
			return
		self.otf = otf
		self.getPointsFromFree()
		self.updateGraph()		  

