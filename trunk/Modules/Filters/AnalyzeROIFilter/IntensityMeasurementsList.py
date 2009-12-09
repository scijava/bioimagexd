#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Copyright (C) 2009  BioImageXD Project
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
__author__ = "BioImageXD Project <http://www.bioimagexd.net/>"
__version__ = "$Revision$"
__date__ = "$Date$"

import wx

class IntensityMeasurementsList(wx.ListCtrl):
	def __init__(self, parent, log):

		wx.ListCtrl.__init__(self, parent, -1, size = (450, 250), \
							style = wx.LC_REPORT | wx.LC_VIRTUAL | wx.LC_HRULES | wx.LC_VRULES,)

		self.measurements = []
		self.InsertColumn(0, "ROI")
		self.InsertColumn(1, "Voxel #")
		self.InsertColumn(2, "Sum")

		self.InsertColumn(3, "Min")
		self.InsertColumn(4, "Max")
		self.InsertColumn(5, u"Mean\u00B1std.dev.")
	 
		#self.InsertColumn(2, "")
		self.SetColumnWidth(0, 70)
		self.SetColumnWidth(1, 60)
		self.SetColumnWidth(2, 60)
		self.SetColumnWidth(3, 50)
		self.SetColumnWidth(4, 50)
		self.SetColumnWidth(5, 100)

		self.SetItemCount(1000)

		self.attr1 = wx.ListItemAttr()
		self.attr1.SetBackgroundColour("white")

		self.attr2 = wx.ListItemAttr()
		self.attr2.SetBackgroundColour("light blue")
		
		self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected)

	def setMeasurements(self, measurements):
		self.measurements = measurements
		
	def OnItemSelected(self, event):
		self.currentItem = event.m_itemIndex

	def getColumnText(self, index, col):
		item = self.GetItem(index, col)
		return item.GetText()

	def OnGetItemText(self, item, col):
		
		
		if item >= len(self.measurements):
			return ""
		m = self.measurements[item]
		
		if col == 0:
			return "%s" % m[0]
		elif col in [3]:
			return "%.2f" % m[3]
		elif col == 5:
			return u"%.2f\u00B1%.2f" % (m[5], m[6])
		return "%d" % m[col]

	def OnGetItemImage(self, item):
		return - 1

	def OnGetItemAttr(self, item):
		if item % 2 == 1:
			return self.attr1
		elif item % 2 == 0:
			return self.attr2
		else:
			return None
