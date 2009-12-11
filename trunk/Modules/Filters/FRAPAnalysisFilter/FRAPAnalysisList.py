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
import Modules

loader = Modules.DynamicLoader.getPluginLoader()
IntensityMeasurementList = loader.getPluginItem("Filters","AnalyzeROIFilter",2).IntensityMeasurementsList

class FRAPAnalysisList(wx.ListCtrl):
	"""
	"""
	def __init__(self, parent, log):
		"""
		Initialize the list ctrl
		"""
		wx.ListCtrl.__init__(
			self, parent, -1,
			size = (350, 192),
			style = wx.LC_REPORT | wx.LC_VIRTUAL | wx.BORDER_RAISED | wx.LC_VRULES
			)

		self.quantities = []
		self.values = []
		self.setupList()

	def setupList(self):
		"""
		Setup list ctrl
		"""
		self.quantities.append("Baseline intensity")
		self.quantities.append("Lowest intensity")
		self.quantities.append("Intensity after recovery")
		self.quantities.append("Half recovery time")
		self.quantities.append("Slope")
		self.quantities.append("Recovery %")
		self.quantities.append("Diffusion constant")

		self.values.append(0.0)
		self.values.append(0.0)
		self.values.append(0.0)
		self.values.append(0.0)
		self.values.append(0.0)
		self.values.append(0.0)
		self.values.append(0.0)

		self.SetItemCount(7)
		self.InsertColumn(0, "Quantity")
		self.InsertColumn(1, "Value")
		self.SetColumnWidth(0, 250)
		self.SetColumnWidth(1, 100)

		self.attr = wx.ListItemAttr()
		self.color = wx.Colour(180,255,180)
		self.attr.SetBackgroundColour(self.color)


	def getColumnText(self, index, col):
		"""
		Return the text for the given row and column
		"""
		item = self.GetItem(index, col)
		return item.GetText()

	def OnGetItemText(self, item, col):
		"""
		"""
		if col == 0:
			return self.quantities[item]
		elif col == 1:
			if item == 3:
				return "%.3f s"%self.values[item]
			elif item == 5:
				return u"%.3f %%"%self.values[item]
			else:
				return "%.3f"%self.values[item]
		return ""

	def OnGetItemImage(self, item):
		return -1

	def OnGetItemAttr(self, item):
		"""
		Get item attribute
		"""
		return self.attr

	def setBaselineInt(self, baseInt):
		"""
		Set baseline intensity
		"""
		self.values[0] = baseInt

	def setLowestInt(self, lowInt):
		"""
		Set lowest intensity
		"""
		self.values[1] = lowInt

	def setAfterRecoveryInt(self, afterInt):
		"""
		Set intensity after recovery
		"""
		self.values[2] = afterInt

	def setHalfRecoveryTime(self, recTime):
		"""
		Set half recovery time
		"""
		self.values[3] = recTime
		
	def setSlope(self, slope):
		"""
		Set slope
		"""
		self.values[4] = slope

	def setRecoveryPercentage(self, recPerc):
		"""
		Set recovery percentage
		"""
		self.values[5] = recPerc

	def setDiffusionConstant(self, diffConst):
		"""
		Set diffusion constant
		"""
		self.values[6] = diffConst

		
class FRAPIntensityMeasurementList(IntensityMeasurementList.IntensityMeasurementsList):
	"""
	"""
	def __init__(self, parent, log):
		"""
		Initialize the list ctrl using IntensityMeasurementList
		"""
		IntensityMeasurementList.IntensityMeasurementsList.__init__(self, parent, log)
		item = self.GetColumn(0)
		item.SetText("Time point")
		self.SetColumn(0, item)
		self.SetColumnWidth(0, 50)

		self.attr1 = wx.ListItemAttr()
		self.attr1.SetBackgroundColour("white")
		self.attr2 = wx.ListItemAttr()
		self.attr2.SetBackgroundColour("light blue")

		self.stats = []


	def OnGetItemImage(self, item):
		return -1

	def OnGetItemAttr(self, item):
		"""
		Get item attribute
		"""
		if item % 2 == 0:
			return self.attr2
		elif item % 2 == 1:
			return self.attr1
		else:
			return None

	def OnGetItemText(self, item, col):
		"""
		Get text of cell
		"""
		if item >= len(self.stats):
			return ""

		itemStats = self.stats[item]
		if col == 0:
			return "%d"%(item+1)
		elif col == 1:
			return "%d"%itemStats["NumPixels"]
		elif col == 2:
			return "%.2f"%itemStats["TotInt"]
		elif col == 3:
			return "%.2f"%itemStats["MaxInt"]
		elif col == 4:
			return "%.2f"%itemStats["MinInt"]
		elif col == 5:
			return u"%.2f\u00B1%.2f"%(itemStats["MeanInt"], itemStats["Sigma"])
			

	def setStats(self, stats):
		"""
		Set stats
		"""
		self.stats = stats
