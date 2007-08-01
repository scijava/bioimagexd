# -*- coding: iso-8859-1 -*-
"""
 Unit: IntensityTransferEditor
 Project: BioImageXD
 Created: 30.10.2004, KP
 Description:

 A widget used to view and modify an intensity transfer function. The widget
 draws the graph of the function and allows the user to modify six points that
 affect the function.

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
__version__ = "$Revision: 1.36 $"
__date__ = "$Date: 2005/01/13 14:52:39 $"

import wx
import os.path
import sys
import time
import messenger

import vtk
from RangedSlider import *


class PaintPanel(wx.Panel):
	"""
	Created: 10.01.2005, KP
	Description: A widget onto which the transfer function is painted
	"""
	def __init__(self, parent):
		self.maxx = 255
		self.maxy = 255
		self.scale = 1

		self.xoffset = 16
		self.yoffset = 22
		w = self.xoffset + self.maxx / self.scale
		h = self.yoffset + self.maxy / self.scale
		wx.Panel.__init__(self, parent, -1, size = (w + 15, h + 15))
		self.buffer = wx.EmptyBitmap(w + 15, h + 15, -1)
		self.w = w + 15
		self.h = h + 15
		self.dc = None
		self.Bind(wx.EVT_PAINT, self.onPaint)

	def onPaint(self, event):
		dc = wx.BufferedPaintDC(self, self.buffer)#,self.buffer)

	def createLine(self, x1, y1, x2, y2, color = "WHITE", brush = None, **kws):
		"""
		Created: 30.10.2004, KP
		Description: Draws a line from (x1,y1) to (x2,y2). The method
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
		Created: 30.10.2004, KP
		Description: Draws an oval at point (x,y) with given radius
		"""
		self.dc.SetBrush(wx.Brush(color, wx.SOLID))
		self.dc.SetPen(wx.Pen(color))        
		y = self.maxy - y + self.yoffset
		ox = x / self.scale
		ox += self.xoffset
		if ox <= self.w and y / self.scale <= self.h and ox >= 0 and y >= 0:
			print "drawing circle", ox, y, self.scale, r
			self.dc.DrawCircle(ox, y / self.scale, r)

	def createText(self, x, y, text, color = "WHITE", **kws):
		"""
		Created: 30.10.2004, KP
		Description: Draws a text at point (x,y) using the given font
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
		

	def paintTransferFunction(self, iTF):
		"""
		Created: 30.10.2004, KP
		Description: Paints the graph of the function specified by the six points
		"""

		#dc = wx.BufferedDC(None,self.buffer)

		#dc = wx.MemoryDC()
		self.dc = wx.BufferedDC(wx.ClientDC(self), self.buffer)

		self.dc.SetBackground(wx.Brush("BLACK"))
		self.dc.Clear()
		self.dc.BeginDrawing()
		# get the slope start and end points
		# TF=iTF.GetAsList()
		x0, y0 = 0, 0

		self.createLine(0, 0, 0, 260, arrow = "VERTICAL")
		self.createLine(0, 0, 260, 0, arrow = "HORIZONTAL")

		for i in range(32, 255, 32):
			# Color gray and stipple with gray50
			self.createLine(i, 0, i, 255, 'GREY', wx.LIGHT_GREY_BRUSH)
			self.createLine(0, i, 255, i, 'GREY', wx.LIGHT_GREY_BRUSH)

		maxval = iTF.GetRangeMax()
		d = maxval / 255.0
		if d < 1:d = 1
		coeff = float(self.maxx) / maxval
		for x1 in range(0, maxval + 1, int(d)):
			y1 = iTF.GetValue(x1)
			# We cheat a bit here to get the line from point 
			# (maxthreshold,maxvalue) to (maxthreshold+1,0) to be straight
			if min(y0, y1) == 0 and max(y0, y1) > 0:
				if x1 > 0:
					x1 -= 1
			l = self.createLine(x0 * coeff, y0 * coeff, x1 * coeff, y1 * coeff, '#00ff00')
			x0, y0 = x1, y1

		x, y = iTF.GetReferencePoint()
		self.createOval(x * coeff, y * coeff, 2)
		
		gammaPoints = [iTF.GetGammaStart(), iTF.GetGammaEnd()]
		if 1 and gammaPoints and gammaPoints[0] > -1:
			[x0, y0], [x1, y1] = gammaPoints
			self.createOval(x0 * coeff, y0 * coeff, 2, "GREEN")
			self.createOval(x1 * coeff, y1 * coeff, 2, "GREEN")

		textcol = "GREEN"
		self.createText(0, -5, "0", textcol)
		self.createText(127, -5, "%d" % (maxval / 2), textcol)
		self.createText(255, -5, "%d" % maxval, textcol)

		self.createText(-10, 127, "%d" % (maxval / 2), textcol)
		self.createText(-10, 255, "%d" % maxval, textcol)
		self.dc.EndDrawing()
		self.dc = None

		

class IntensityTransferEditor(wx.Panel):
	"""
	Created: 30.10.2004, KP
	Description: A widget used to view and modify an intensity transfer function
	"""
	def __init__(self, parent, **kws):
		"""
		Created: 30.10.2004, KP
		Description: Initialization
		"""
		self.parent = parent
		wx.Panel.__init__(self, parent, -1)
		self.doyield = 1
		self.calling = 0
		self.guiupdate = 0

		self.iTF = vtk.vtkIntensityTransferFunction()
		
		self.mainsizer = wx.BoxSizer(wx.VERTICAL)

		self.canvasBox = wx.BoxSizer(wx.HORIZONTAL)
		self.contrastBox = wx.BoxSizer(wx.VERTICAL)
		self.gammaBox = wx.BoxSizer(wx.HORIZONTAL)
		
		self.brightnessBox = wx.BoxSizer(wx.HORIZONTAL)

		self.contrastSlider = RangedSlider(self, -1, 10000, size = (-1, 280), style = wx.SL_VERTICAL)
		self.contrastSlider.setSnapPoint(1.0, 0.1)
		self.contrastSlider.setRange(0, 50, 0.0001, 1.0)
		self.contrastSlider.setRange(50.01, 100, 1.0, 20.0)
		self.contrastSlider.setScaledValue(1.0)

		self.contrastLbl = wx.StaticText(self, -1, "Contrast")
		
		self.Bind(wx.EVT_COMMAND_SCROLL, self.setContrast, self.contrastSlider)

		self.canvas = PaintPanel(self)
		self.canvasBox.Add(self.canvas, 1, wx.ALL | wx.EXPAND, 10)
		self.canvasBox.Add(self.contrastBox)

		self.contrastEdit = wx.TextCtrl(self, -1, "1.00", size = (50, -1))
		self.contrastBox.Add(self.contrastLbl)
		self.contrastBox.Add(self.contrastEdit)
		
		self.contrastBox.Add(self.contrastSlider, 1, wx.TOP | wx.BOTTOM, 0)


		self.brightnessEdit = wx.TextCtrl(self, -1, "0.00", size = (70, -1), style = wx.TE_PROCESS_ENTER)
		self.gammaEdit = wx.TextCtrl(self, -1, "1.00", size = (70, -1), style = wx.TE_PROCESS_ENTER)

		self.brightnessSlider = RangedSlider(self, -1, 5000, size = (260, -1), style = wx.SL_HORIZONTAL)
		self.brightnessSlider.setRange(0, 100, -255, 255)
		self.brightnessSlider.setSnapPoint(0.0, 0.1)        
		self.brightnessSlider.setScaledValue(0.1)
		self.Bind(wx.EVT_COMMAND_SCROLL, self.setBrightness, self.brightnessSlider)


		self.gammaSlider = RangedSlider(self, -1, 10000, size = (260, -1), style = wx.SL_HORIZONTAL)
		self.gammaSlider.setRange(0, 50, 0.0001, 1.0)
		self.gammaSlider.setRange(50.01, 100, 1.0, 15.0)
		self.gammaSlider.setScaledValue(1.0)
		self.gammaSlider.setSnapPoint(1.0, 0.1)        
		self.Bind(wx.EVT_COMMAND_SCROLL, self.setGamma, self.gammaSlider)

		self.gammaBox.Add(self.gammaSlider)
		self.gammaBox.Add(self.gammaEdit, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL)

		self.brightnessBox.Add(self.brightnessSlider)
		self.brightnessBox.Add(self.brightnessEdit, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL)


		self.minValueLbl = wx.StaticText(self, wx.NewId(), "Min value:")
		self.maxValueLbl = wx.StaticText(self, wx.NewId(), "Max value:")

		self.minValue = wx.TextCtrl(self, -1, style = wx.TE_PROCESS_ENTER)
		self.maxValue = wx.TextCtrl(self, -1, style = wx.TE_PROCESS_ENTER)

		fieldsizer = wx.GridBagSizer(0, 5)


		valuesizer = wx.BoxSizer(wx.HORIZONTAL)
		fieldsizer.Add(self.minValueLbl, (0, 0))
		fieldsizer.Add(self.minValue, (0, 1))
		fieldsizer.Add(self.maxValueLbl, (0, 2))
		fieldsizer.Add(self.maxValue, (0, 3))
		
		self.minthresholdLbl = wx.StaticText(self, wx.NewId(), "Min threshold:")
		self.maxthresholdLbl = wx.StaticText(self, wx.NewId(), "Max threshold:")

		self.minthreshold = wx.TextCtrl(self, -1, style = wx.TE_PROCESS_ENTER)
		self.maxthreshold = wx.TextCtrl(self, -1, style = wx.TE_PROCESS_ENTER)

		fieldsizer.Add(self.minthresholdLbl, (1, 0))
		fieldsizer.Add(self.minthreshold, (1, 1))
		fieldsizer.Add(self.maxthresholdLbl, (1, 2))
		fieldsizer.Add(self.maxthreshold, (1, 3))

		#self.minProcessLbl=wx.StaticText(self,-1,"Processing\nthreshold:")
		#self.minProcess=wx.TextCtrl(self,-1,style=wx.TE_PROCESS_ENTER)

		#fieldsizer.Add(self.minProcessLbl,(2,0))
		#fieldsizer.Add(self.minProcess,(2,1))
		
		
		self.ssThresholdLbl = wx.StaticText(self, -1, "Smooth start:")
		self.ssThreshold = wx.TextCtrl(self, -1, "0", style = wx.TE_PROCESS_ENTER)
		
		self.ssgammaEdit = wx.TextCtrl(self, -1, "1.00", size = (70, -1), style = wx.TE_PROCESS_ENTER)        
		self.ssgammaSlider = RangedSlider(self, -1, 10000, size = (150, -1), style = wx.SL_HORIZONTAL)
		self.ssgammaSlider.setRange(0, 50, 0.0001, 1.0)
		self.ssgammaSlider.setRange(50.01, 100, 1.0, 15.0)
		self.ssgammaSlider.setScaledValue(1.0)
		self.ssgammaSlider.setSnapPoint(1.0, 0.1)        
		self.Bind(wx.EVT_COMMAND_SCROLL, self.setSSGamma, self.ssgammaSlider)
		
		fieldsizer.Add(self.ssThresholdLbl, (2, 0))
		fieldsizer.Add(self.ssThreshold, (2, 1))
		fieldsizer.Add(self.ssgammaSlider, (2, 2))        
		fieldsizer.Add(self.ssgammaEdit, (2, 3))

		self.seThresholdLbl = wx.StaticText(self, -1, "Smooth end:")
		self.seThreshold = wx.TextCtrl(self, -1, "255", style = wx.TE_PROCESS_ENTER)
		self.segammaEdit = wx.TextCtrl(self, -1, "1.00", size = (70, -1), style = wx.TE_PROCESS_ENTER)        
		self.segammaSlider = RangedSlider(self, -1, 10000, size = (150, -1), style = wx.SL_HORIZONTAL)
		self.segammaSlider.setRange(0, 50, 0.0001, 1.0)
		self.segammaSlider.setRange(50.01, 100, 1.0, 15.0)
		self.segammaSlider.setScaledValue(1.0)
		self.segammaSlider.setSnapPoint(1.0, 0.1)        
		self.Bind(wx.EVT_COMMAND_SCROLL, self.setSEGamma, self.segammaSlider)


		self.seThreshold.Bind(wx.EVT_KILL_FOCUS, self.updateSE)
		self.seThreshold.Bind(wx.EVT_TEXT_ENTER, self.updateSE)
		self.ssThreshold.Bind(wx.EVT_KILL_FOCUS, self.updateSS)
		self.ssThreshold.Bind(wx.EVT_TEXT_ENTER, self.updateSS)
		
		fieldsizer.Add(self.seThresholdLbl, (3, 0))
		fieldsizer.Add(self.seThreshold, (3, 1))
		fieldsizer.Add(self.segammaSlider, (3, 2))        
		fieldsizer.Add(self.segammaEdit, (3, 3))        
		
		self.gammaEdit.Bind(wx.EVT_KILL_FOCUS, self.updateGamma)
		self.gammaEdit.Bind(wx.EVT_TEXT_ENTER, self.updateGamma)
		self.contrastEdit.Bind(wx.EVT_KILL_FOCUS, self.updateContrast)
		self.contrastEdit.Bind(wx.EVT_TEXT_ENTER, self.updateContrast)
		self.brightnessEdit.Bind(wx.EVT_KILL_FOCUS, self.updateBrightness)
		self.brightnessEdit.Bind(wx.EVT_TEXT_ENTER, self.updateBrightness)

		self.minValue.Bind(wx.EVT_KILL_FOCUS, self.updateMinimumValue)
		self.minValue.Bind(wx.EVT_TEXT_ENTER, self.updateMinimumValue)
		self.maxValue.Bind(wx.EVT_KILL_FOCUS, self.updateMaximumValue)
		self.maxValue.Bind(wx.EVT_TEXT_ENTER, self.updateMaximumValue)

		self.minthreshold.Bind(wx.EVT_KILL_FOCUS, self.updateMinimumThreshold)
		self.minthreshold.Bind(wx.EVT_TEXT_ENTER, self.updateMinimumThreshold)
		self.maxthreshold.Bind(wx.EVT_KILL_FOCUS, self.updateMaximumThreshold)
		self.maxthreshold.Bind(wx.EVT_TEXT_ENTER, self.updateMaximumThreshold)

		#self.minProcess.Bind(wx.EVT_KILL_FOCUS,self.updateProcessingThreshold)
		#self.minProcess.Bind(wx.EVT_TEXT_ENTER,self.updateProcessingThreshold)
		
		self.setMinimumThreshold(0)
		self.setMaximumThreshold(255)
		#self.setProcessingThreshold(0)

		self.setMinimumValue(0)
		self.setMaximumValue(255)

		
		self.mainsizer.Add(self.canvasBox)

		self.gammaLbl = wx.StaticText(self, -1, "Gamma")
		self.brightnessLbl = wx.StaticText(self, -1, "Brightness")

		self.mainsizer.Add(self.brightnessLbl)
		self.mainsizer.Add(self.brightnessBox)

		self.mainsizer.Add(self.gammaLbl)
		self.mainsizer.Add(self.gammaBox)
		self.mainsizer.Add(fieldsizer)
 #       self.mainsizer.Add(self.defaultBtn)

		self.SetAutoLayout(True)
		self.SetSizer(self.mainsizer)
		self.mainsizer.SetSizeHints(self)

		self.updateGraph()


	def restoreDefaults(self, event):
		"""
		Created: 8.12.2004, KP
		Description: Restores the default settings for this widget
		"""
		Logging.info("Restoring defaults for iTF", kw = "ctf")
		self.iTF.Reset()
		self.setIntensityTransferFunction(self.iTF)

	def setAlphaMode(self, mode):
		"""
		Created: 7.12.2004, KP
		Description: Sets the widget to/from alpha editing mode
		"""
		wstate = "disabled"
		minvalstring = "Minimum alpha value:"
		maxvalstring = "Maximum alpha value:"
		if not mode:
			wstate = "normal"
			minvalstring = "Minimum value:"
			maxvalstring = "Maximum value:"

		self.minValueLbl.SetLabel(minvalstring)
		self.maxValueLbl.SetLabel(maxvalstring)
		self.Layout()

	def setGamma(self, event):
		"""
		Created: 30.10.2004, KP
		Description: Updates the gamma part of the function according to the
					 gamma slider in the GUI
		"""
		gamma = event.GetPosition()
		gammaEx = self.gammaSlider.getScaledValue()
		self.iTF.SetGamma(gammaEx)
		self.updateGraph()
		self.updateGUI()
		event.Skip()
		
	def setSSGamma(self, event):
		"""
		Created: 30.10.2004, KP
		Description: Updates the gamma part of the function according to the
					 gamma slider in the GUI
		"""
		gamma = event.GetPosition()
		gammaEx = self.ssgammaSlider.getScaledValue()
		self.iTF.SetSmoothStartGamma(gammaEx)
		self.updateGraph()
		self.updateGUI()
		event.Skip()
		
	def setSEGamma(self, event):
		"""
		Created: 30.10.2004, KP
		Description: Updates the gamma part of the function according to the
					 gamma slider in the GUI
		"""
		gamma = event.GetPosition()
		gammaEx = self.segammaSlider.getScaledValue()
		self.iTF.SetSmoothEndGamma(gammaEx)
		self.updateGraph()
		self.updateGUI()
		event.Skip()                
	

	def setContrast(self, event):
		"""
		Created: 30.10.2004, KP
		Description: Updates the coefficient for the line according to the
					 contrast slider in the GUI
		"""
		contrast = event.GetPosition()
		coeff = self.contrastSlider.getScaledValue()

		self.iTF.SetContrast(coeff)
		self.updateGraph()
		self.updateGUI()
		event.Skip()

	def setBrightness(self, event):
		"""
		Created: 30.10.2004, KP
		Description: Updates the reference point for the line according to the
					 brightness slider in the GUI
		"""
		val = self.brightnessSlider.getScaledValue()
		self.iTF.SetBrightness(val)
		self.updateGraph()
		self.updateGUI()
		event.Skip()

	def setProcessingThreshold(self, x):
		"""
		Created: 1.12.2004, KP
		Description: Sets the minimum processing threshold and updates
					 the GUI accordingly
		"""
		self.iTF.SetProcessingThreshold(x)
		self.minProcess.SetValue("%d" % x)

	def setMinimumThreshold(self, x):
		"""
		Created: 30.10.2004, KP
		Description: Sets the minimum threshold and updates the GUI accordingly
		"""
		self.iTF.SetMinimumThreshold(x)
		self.minthreshold.SetValue("%d" % x)

	def setMaximumThreshold(self, x):
		"""
		Created: 30.10.2004, KP
		Description: Sets the maximum threshold and updates the GUI accordingly
		"""
		self.maxthreshold.SetValue("%d" % x)
		self.iTF.SetMaximumThreshold(x)

	def setMinimumValue(self, x):
		"""
		Created: 30.10.2004, KP
		Description: Sets the minimum value and updates the GUI accordingly
		"""
		if self.guiupdate:return
		self.minValue.SetValue("%d" % x)
		self.iTF.SetMinimumValue(x)

	def setMaximumValue(self, x):
		"""
		Created: 30.10.2004, KP
		Description: Sets the maximum value and updates the GUI accordingly
		"""
		self.maxValue.SetValue("%d" % x)
		self.iTF.SetMaximumValue(x)

	def updateMinimumThreshold(self, event):
		"""
		Created: 30.10.2004, KP
		Description: A callback used to update the minimum threshold
					 to reflect the GUI settings
		"""
		if self.guiupdate:return
		self.setMinimumThreshold(int(self.minthreshold.GetValue()))
		self.updateGraph()
		event.Skip()

	def updateProcessingThreshold(self, event):
		"""
		Created: 1.12.2004, KP
		Description: A callback used to update the minimum processing threshold
					 to reflect the GUI settings
		"""
		if self.guiupdate:return
		self.setProcessingThreshold(int(self.minProcess.GetValue()))
		self.updateGraph()
		event.Skip()


	def updateMaximumThreshold(self, event):
		"""
		Created: 30.10.2004, KP
		Description: A callback used to update the maximum threshold
					 to reflect the GUI settings
		"""
		if self.guiupdate:return
		self.setMaximumThreshold(int(self.maxthreshold.GetValue()))
		self.updateGraph()
		event.Skip()

	def updateMinimumValue(self, event):
		"""
		Created: 30.10.2004, KP
		Description: A callback used to update the minimum value
					 to reflect the GUI settings
		"""
		if self.guiupdate:return
		self.setMinimumValue(int(self.minValue.GetValue()))
		self.updateGraph()
		event.Skip()
		
	def updateSS(self, event):
		"""
		Created: 3.10.2005, KP
		Description: A callback used to update the smooth start threshold
					 to reflect the GUI settings
		"""
		if self.guiupdate:return
		self.iTF.SetSmoothStart(int(self.ssThreshold.GetValue()))
		self.updateGraph()
		event.Skip()     
		
	def updateSE(self, event):
		"""
		Created: 3.10.2005, KP
		Description: A callback used to update the minimum value
					 to reflect the GUI settings
		"""
		if self.guiupdate:return
		self.iTF.SetSmoothEnd(int(self.seThreshold.GetValue()))
		self.updateGraph()
		event.Skip()                

	def updateGamma(self, event):
		"""
		Created: 09.12.2004, KP
		Description: A callback used to update the gamma
					 to reflect the entry value
		"""
		if self.guiupdate:return
		gamma = float(self.gammaEdit.GetValue())
		self.iTF.SetGamma(gamma)
		self.updateGraph()
		self.updateGUI(1)
		event.Skip()

	def updateContrast(self, event):
		"""
		Created: 09.12.2004, KP
		Description: A callback used to update the contrast
					 to reflect the entry value
		"""
		if self.guiupdate:return
		cont = float(self.contrastEdit.GetValue())
		self.iTF.SetContrast(cont)
		self.updateGraph()
		self.updateGUI(1)
		event.Skip()

	def updateBrightness(self, event):
		"""
		Created: 09.12.2004, KP
		Description: A callback used to update the brightness
					 to reflect the entry value
		"""
		if self.guiupdate:return
		br = float(self.brightnessEdit.GetValue())
		self.iTF.SetBrightness(br)
		self.updateGraph()
		self.updateGUI(1)
		event.Skip()

	def updateMaximumValue(self, event):
		"""
		Created: 30.10.2004, KP
		Description: A callback used to update the maximum threshold
					 to reflect the GUI settings
		"""
		if self.guiupdate:return
		self.setMaximumValue(int(self.maxValue.GetValue()))
		self.updateGraph()
		event.Skip()

	def updateGUI(self, sliders = 0):
		"""
		Created: 07.12.2004, KP
		Description: Updates the GUI settings to correspond to those of
					 the transfer function
		"""
		self.guiupdate = 1
		self.minValue.SetValue("%d" % self.iTF.GetMinimumValue())
		self.maxValue.SetValue("%d" % self.iTF.GetMaximumValue())
		self.minthreshold.SetValue("%d" % self.iTF.GetMinimumThreshold())
		self.maxthreshold.SetValue("%d" % self.iTF.GetMaximumThreshold())
		#self.minProcess.SetValue("%d"%self.iTF.GetProcessingThreshold())

		self.ssThreshold.SetValue("%d" % self.iTF.GetSmoothStart())
		self.seThreshold.SetValue("%d" % self.iTF.GetSmoothEnd())
		
		contrast = self.iTF.GetContrast()
		gamma = self.iTF.GetGamma()
		brightness = self.iTF.GetBrightness()
		ssgamma = self.iTF.GetSmoothStartGamma()
		segamma = self.iTF.GetSmoothEndGamma()
		if sliders:
			self.contrastSlider.setScaledValue(contrast)
			self.brightnessSlider.setScaledValue(brightness)
			self.gammaSlider.setScaledValue(gamma)
			self.ssgammaSlider.setScaledValue(ssgamma)
			self.segammaSlider.setScaledValue(segamma)
			
		self.gammaEdit.SetValue("%.2f" % gamma)
		self.brightnessEdit.SetValue("%.2f" % brightness)
		self.contrastEdit.SetValue("%.2f" % contrast)
		self.ssgammaEdit.SetValue("%.2f" % ssgamma)
		self.segammaEdit.SetValue("%.2f" % segamma)
		self.guiupdate = 0

			
	def updateGraph(self):
		"""
		Created: 30.10.2004, KP
		Description: Clears the canvas and repaints the function
		"""
		self.canvas.paintTransferFunction(self.iTF)

		if self.doyield:
		   self.doyield = 0
		   #wx.Yield()
		   self.doyield = 1

		messenger.send(None, "itf_update")

	def getIntensityTransferFunction(self):
		"""
		Created: 11.11.2004, JV
		Description: Returns the intensity transfer function
		"""
		return self.iTF

	def setIntensityTransferFunction(self, TF):
		"""
		Created: 24.11.2004, KP
		Description: Sets the intensity transfer function that is configured
					 by this widget
		"""
		self.iTF = TF

		
		maxval = TF.GetRangeMax()
		
		self.brightnessSlider.reset()
		self.brightnessSlider.setRange(0, 100, -maxval, maxval)
		self.brightnessSlider.setSnapPoint(0.0, 0.1)        
		self.brightnessSlider.setScaledValue(0.1)
		
		self.updateGUI(1)
		self.updateGraph()
		self.Refresh()

