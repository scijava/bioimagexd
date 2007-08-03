#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: ResampleDialog
 Project: BioImageXD
 Created: 1.09.2005, KP
 Description:

 A dialog for importing different kinds of data to form a .bxd file
 
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
__version__ = "$Revision: 1.40 $"
__date__ = "$Date: 2005/01/13 14:52:39 $"

import scripting
import string
import UIElements
import wx

class ResampleDialog(wx.Dialog):
	"""
	Created: 1.09.2005, KP
	Description: A dialog for resampling a dataset
	"""
	def __init__(self, parent, imageMode = 1):
		"""
		Created: 1.09.2005, KP
		Description: Initialize the dialog
		"""
		wx.Dialog.__init__(self, parent, -1, 'Resample dataset', style = wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
		self.dataUnits = []
		self.sizer = wx.GridBagSizer(5, 0)
		self.btnsizer = self.CreateButtonSizer(wx.OK | wx.CANCEL)
	
		self.createResample()
		self.sizer.Add(self.btnsizer, (2, 0), flag = wx.EXPAND | wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTRE)
		wx.EVT_BUTTON(self, wx.ID_OK, self.onOkButton)
		self.result = 0
		self.currSize = (512, 512, 25)
		self.SetSizer(self.sizer)
		#self.SetAutoLayout(1)
		self.blockDimUpdate = 0
		self.blockFactorUpdate = 0
		#self.sizer.Fit(self)
		w, h = self.sizer.GetMinSize()
		w += 30
		#h+=50
		self.SetSize((w, h))
		self.sizer.SetSizeHints(self)
		
	def onOkButton(self, event):
		"""
		Created: 21.04.2005, KP
		Description: Executes the procedure
		"""
		for i in self.dataUnits:
			#print "\nSETTING RESAMPLE DIMS TO ",self.currSize
			i.dataSource.setResampleDimensions(self.currSize)
			i.dataSource.getDataSet(scripting.visualizer.getTimepoint()).SetUpdateExtent((0, -1, 0, -1, 0, -1))
		self.result = 1
		self.Close()
		
	def setDataUnits(self, dataunits):
		"""
		Created: 1.09.2005, KP
		Description: Set the dataunits to be resampled
		"""
		self.dataUnits = dataunits
		
		x, y, z = self.dataUnits[0].getDimensions()
		self.dims = (x, y, z)
		self.newDimX.SetValue("%d" % x)
		self.newDimY.SetValue("%d" % y)
		self.newDimZ.SetValue("%d" % z)
		self.dimsLbl.SetLabel(self.currDimText % (x, y, z))
		self.onUpdateDims(None)
		self.onSetToHalfSize(None)
	def onUpdateDims(self, evt):
		"""
		Created: 1.09.2005, KP
		Description: Update the dimensions
		"""
		if self.blockDimUpdate:
			return
		rx, ry, rz = self.dims
		try:
			rx = int(self.newDimX.GetValue())
			ry = int(self.newDimY.GetValue())
			rz = int(self.newDimZ.GetValue())
		except:
			pass
		self.currSize = (rx, ry, rz)
		x, y, z = self.dataUnits[0].dataSource.getOriginalDimensions()
		xf = rx / float(x)
		yf = ry / float(y)
		zf = rz / float(z)
		#self.factorsLbl.SetLabel(self.currFactorText%(xf,yf,zf))
		self.blockFactorUpdate = 1
		self.factorX.SetValue("%.2f" % xf)
		self.factorY.SetValue("%.2f" % yf)
		self.factorZ.SetValue("%.2f" % zf)
		self.blockFactorUpdate = 0
		
	def onUpdateFactors(self, evt):
		"""
		Created: 23.07.2006, KP
		Description: Update the factors, resulting in change in the dimensions
		"""
		if self.blockFactorUpdate:
			print "Blocking factor update"
			return
		x, y, z = self.dataUnits[0].dataSource.getOriginalDimensions()
		fx = 1
		fy = 1
		fz = 1
		try:
			fx = float(self.factorX.GetValue())
			fy = float(self.factorY.GetValue())
			fz = float(self.factorZ.GetValue())
		except:
			pass
		x *= fx
		y *= fy
		z *= fz
		#self.factorsLbl.SetLabel(self.currFactorText%(xf,yf,zf))
		self.blockDimUpdate = 1
		self.newDimX.SetValue("%d" % x)
		self.newDimY.SetValue("%d" % y)
		self.newDimZ.SetValue("%d" % z)
		self.currSize = (x, y, z)
		self.blockDimUpdate = 0


	def createResample(self):
		"""
		Created: 1.09.2005, KP
		Description: Creates the GUI for setting the resampled size
		"""
		box = wx.StaticBox(self, -1, "Resample now to")
		self.currDimText = u"Current dataset original dimensions: %d x %d x %d"
		self.dimsLbl = wx.StaticText(self, -1, self.currDimText % (0, 0, 0))
		
		boxsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
		panel = wx.Panel(self, -1)
		boxsizer.Add(panel, 1)
		
		sizer = wx.GridBagSizer()
		
		
		#self.currFactorText=u"Scale factors: %.2f x %.2f x %.2f"
		#self.factorsLbl=wx.StaticText(panel,-1,self.currFactorText%(1,1,1))
		#sizer.Add(self.factorsLbl,(n,0),flag=wx.EXPAND|wx.LEFT|wx.RIGHT)
		self.factorBox = wx.BoxSizer(wx.HORIZONTAL)
		self.factorLabel = factorLabel = wx.StaticText(panel, -1, "scale:")
		#self.factorBox.Add(factorLabel,0,wx.ALIGN_CENTER_VERTICAL)
		self.factorX = wx.TextCtrl(panel, -1, "%.2f" % 1, size = (50, -1))
		self.factorBox.Add(self.factorX)
		x1 = wx.StaticText(panel, -1, "x")
		self.factorBox.Add(x1, 0, wx.ALIGN_CENTER_VERTICAL)
		self.factorY = wx.TextCtrl(panel, -1, "%.2f" % 1, size = (50, -1))
		self.factorBox.Add(self.factorY, 0, wx.ALIGN_CENTER_VERTICAL)
		x2 = wx.StaticText(panel, -1, "x")
		self.factorBox.Add(x2, 0, wx.ALIGN_CENTER_VERTICAL)
		self.factorZ = wx.TextCtrl(panel, -1, "%.2f" % 1, size = (50, -1))
		self.factorBox.Add(self.factorZ, 0, wx.ALIGN_CENTER_VERTICAL)

		
		self.dimLabel = dimLabel = wx.StaticText(panel, -1, "dimensions: ")
		val = UIElements.AcceptedValidator
		x1 = wx.StaticText(panel, -1, "x")
		x2 = wx.StaticText(panel, -1, "x")
		
		self.newDimX = wx.TextCtrl(panel, -1, "512", validator = val(string.digits), size = (50, -1))
		self.newDimY = wx.TextCtrl(panel, -1, "512", validator = val(string.digits), size = (50, -1))
		self.newDimZ = wx.TextCtrl(panel, -1, "25", validator = val(string.digits), size = (50, -1))
		
		self.newDimX.Bind(wx.EVT_TEXT, self.onUpdateDims)
		self.newDimY.Bind(wx.EVT_TEXT, self.onUpdateDims)
		self.newDimZ.Bind(wx.EVT_TEXT, self.onUpdateDims)
		
		self.factorX.Bind(wx.EVT_TEXT, self.onUpdateFactors)
		self.factorY.Bind(wx.EVT_TEXT, self.onUpdateFactors)
		self.factorZ.Bind(wx.EVT_TEXT, self.onUpdateFactors)
		
		
		dimsizer  = wx.BoxSizer(wx.HORIZONTAL)
		#dimsizer.Add(newDimXLbl,0,wx.ALIGN_CENTER_VERTICAL)
		dimsizer.Add(self.newDimX, 0, wx.ALIGN_CENTER_VERTICAL)
		dimsizer.Add(x1, 0, wx.ALIGN_CENTER_VERTICAL)
		dimsizer.Add(self.newDimY, 0, wx.ALIGN_CENTER_VERTICAL)
		dimsizer.Add(x2, 0, wx.ALIGN_CENTER_VERTICAL)
		dimsizer.Add(self.newDimZ, 0, wx.ALIGN_CENTER_VERTICAL)
		
		halfSize = wx.RadioButton(panel, -1, "1/2 original size")
		halfSize.SetValue(1)
		halfSize.Bind(wx.EVT_RADIOBUTTON, self.onSetToHalfSize)
	
		fourthSize = wx.RadioButton(panel, -1, "1/4 original size")
		fourthSize.Bind(wx.EVT_RADIOBUTTON, self.onSetToFourthSize)
		custDims = wx.RadioButton(panel, -1, "custom size")
		custDims.Bind(wx.EVT_RADIOBUTTON, self.onSetToCustDims)
		halfSizeBox = wx.BoxSizer(wx.HORIZONTAL)
		fourthSizeBox = wx.BoxSizer(wx.HORIZONTAL)
		
		parenLbl = wx.StaticText(panel, -1, "(")
		parenLbl2 = wx.StaticText(panel, -1, "(")
		
		
		self.halfResampleZ = wx.CheckBox(panel, -1, "resample Z)")
		self.halfResampleZ.Bind(wx.EVT_CHECKBOX, self.onSetToHalfSize)
		self.fourthResampleZ = wx.CheckBox(panel, -1, "resample Z)")
		self.fourthResampleZ.Bind(wx.EVT_CHECKBOX, self.onSetToFourthSize)
		halfSizeBox.Add(parenLbl)
		halfSizeBox.Add(self.halfResampleZ)
		
		fourthSizeBox.Add(parenLbl2)
		fourthSizeBox.Add(self.fourthResampleZ)
		
		custDimScaleSizer = wx.GridBagSizer()
		
		n = 0
		custDimScaleSizer.Add(dimLabel, (n, 0))
		custDimScaleSizer.Add(dimsizer, (n, 1))
		n += 1
		custDimScaleSizer.Add(factorLabel, (n, 0))
		custDimScaleSizer.Add(self.factorBox, (n, 1), flag = wx.EXPAND | wx.LEFT | wx.RIGHT)
		
		n = 0
		sizer.Add(self.dimsLbl, (n, 0), flag = wx.EXPAND | wx.LEFT | wx.RIGHT, span = (1, 2))
		n += 1
		
		sizer.Add(halfSize, (n, 0))
		sizer.Add(halfSizeBox, (n, 1))
		n += 1
		sizer.Add(fourthSize, (n, 0))
		sizer.Add(fourthSizeBox, (n, 1))
		n += 1
		sizer.Add(custDims, (n, 0))
		sizer.Add(custDimScaleSizer, (n, 1))
		
		panel.SetSizer(sizer)
		panel.SetAutoLayout(1)
		sizer.Fit(panel)
		self.dimsPanel = panel
		
		self.sizer.Add(self.dimsLbl, (0, 0), flag = wx.ALIGN_CENTRE | wx.EXPAND | wx.LEFT | wx.RIGHT)
		self.sizer.Add(boxsizer, (1, 0), flag = wx.ALIGN_CENTRE | wx.EXPAND | wx.ALL)

		self.panel = panel

	def onSetToCustDims(self, evt):
		"""
		Created: 19.12.2006, KP
		Description: Select the custom dimensions to be used for resampling
		"""
		self.halfResampleZ.Enable(0)
		self.fourthResampleZ.Enable(0)
		
		for obj in [self.factorLabel, self.dimLabel, self.newDimX, self.newDimY, self.newDimZ, self.factorX, self.factorY, self.factorZ]:
			obj.Enable(1)
		try:
			rx = int(self.newDimX.GetValue())
			ry = int(self.newDimY.GetValue())
			rz = int(self.newDimZ.GetValue())
			self.currSize = (rx, ry, rz)
		except:
			pass
		
		
	def onSetToHalfSize(self, evt):
		"""
		Created: 19.12.2006, KP
		Description: Select a half size to be used for resampling
		"""
		self.halfResampleZ.Enable(1)
		if self.dataUnits:
			x, y, z = self.dataUnits[0].dataSource.getOriginalDimensions()
			zf = 1
			
			if self.halfResampleZ.GetValue():
				zf = 0.5
			self.currSize = int(0.5 * x), int(0.5 * y), int(zf * z)
			print "Resampling in Z = ", zf
		self.fourthResampleZ.Enable(0)
		for obj in [self.factorLabel, self.dimLabel, self.newDimX, self.newDimY, self.newDimZ, self.factorX, self.factorY, self.factorZ]:
			obj.Enable(0)
		
	def onSetToFourthSize(self, evt):
		"""
		Created: 19.12.2006, KP
		Description: Select a fourth size to be used for resampling
		"""
		self.halfResampleZ.Enable(0)
		self.fourthResampleZ.Enable(1)
		if self.dataUnits:
			zf = 1
			x, y, z = self.dataUnits[0].dataSource.getOriginalDimensions()
			
			if self.fourthResampleZ.GetValue():
				zf = 0.25
			self.currSize = int(0.25 * x), int(0.25 * y), int(zf * z)   
			print "Resampling in Z = ", zf
		for obj in [self.factorLabel, self.dimLabel, self.newDimX, self.newDimY, self.newDimZ, self.factorX, self.factorY, self.factorZ]:
			obj.Enable(0)

