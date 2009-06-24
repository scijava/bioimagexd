#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: ColocListView
 Project: BioImageXD
 Description:

 Copyright (C) 2007 BioImageXD Project
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
__version__ = "$Revision: 1.22 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import codecs
import csv
import types
import scripting
import wx
import wx.lib.mixins.listctrl as listmix

class ColocListView(wx.ListCtrl, listmix.TextEditMixin):

	def __init__(self, parent, ID, pos = wx.DefaultPosition,
				 size = wx.DefaultSize, style = wx.BORDER_RAISED | wx.LC_REPORT):
		wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
		listmix.TextEditMixin.__init__(self) 
		self.beginner = wx.Colour(180, 255, 180)
		self.intermediate = wx.Colour(255, 255, 180)
		self.expert = wx.Colour(0, 180, 255)
		self.populateListCtrl()
		
	def setChannelNames(self, n1, n2):
		"""
		Modify the headers to have the correct names
		"""
		for i, val in enumerate(self.headervals):
			s = val[0]
			s = s.replace("%ch1%", n1)
			s = s.replace("%ch2%", n2)
			self.headervals[i][0] = s
			self.SetStringItem(i, 0, s)
	
	def CloseEditor(self, row = 0, col = 0):
		self.editor.Hide()
		self.SetFocus()			   
		
	def populateListCtrl(self):
		"""
		Add information to the list control
		"""
		self.cols = [self.beginner, self.intermediate, self.expert]
		self.headervals = [["%ch1% threshold (Lower / Upper)", "", "", 0],
		["%ch2% threshold (Lower / Upper)", "", "", 0],
		["P-Value", "", "", 0],
		["# of colocalized voxels", "", "", 0],
		["% of volume colocalized", "", "", 0],
		["% of %ch1% coloc. (voxels / intensity)", "", "", 1],
		["% of %ch2% coloc. (voxels / intensity)", "", "", 1],
		["% of %ch1% coloc. (total intensity)", "", "", 1],
		["% of %ch2% coloc. (total intensity)", "", "", 1],
		["Correlation", "", "", 1],
		["Correlation (voxels > threshold)", "", "", 1],
		["Correlation (voxels < threshold)", "", "", 1],
		["M1", "", "", 1],
		["M2", "", "", 1],
		["Sum of %ch1% (total / over threshold)", "", "", 2],
		["Sum of %ch2% (total / over threshold)", "", "", 2],
		["# of non-zero voxels (%ch1% / %ch2%)", "", "", 2],
		["# of voxels > threshold (%ch1% / %ch2%)", "", "", 2],
		["Differ. stain of %ch1% to %ch2% (voxels / intensity)", "", "", 2],
		["Differ. stain of %ch2% to %ch1% (voxels / intensity)", "", "", 2],
		["% of diff. stain of %ch1% (voxels / intensity)", "", "", 2],
		["% of diff. stain of %ch2% (voxels / intensity)", "", "", 2],
		["R(obs)", "", "", 2],
		[u"R(rand) (mean \u00B1 sd)", "", "", 2],
		["R(rand) > R(obs)", "", "", 2]
		]
		
		#if scripting.TFLag:
			# Remove diff stain & r(obs) from non-tekes version
		#	self.headervals = self.headervals[:-7]
			#+ self.headervals[-3:]


		self.InsertColumn(0, "Quantity")
		self.InsertColumn(1, "Value")
		#self.InsertColumn(1,"")
		
		self.SetColumnWidth(0, 180)
		self.SetColumnWidth(1, 180)
		for n, item in enumerate(self.headervals):
			txt, a, b, col = item
			self.InsertStringItem(n, txt)
			self.SetItemBackgroundColour(n, self.cols[col])

	def updateListCtrl(self, variables):
		"""
		Updates the list ctrl
		"""
		fs = "%.3f%%"
		fs2 = "%.4f"
		ds = "%d"
		ss = "%s"
		offset = -2
		coloffset = 1
		n = 2
		mapping = { "Ch1Th":(n, 0, ss),
				  "Ch2Th":(n + 1, 0, ss),
				  "PValue":(n + 2, 0, fs2),
				  "ColocAmount":(n + 3, 0, ds),
				  "ColocPercent":(n + 4, 0, fs, 100),
# volume = number of voxels (Imaris)
# material = intensity
				  "PercentageVolumeCh1":(n + 5, 0, ss),
#				   "PercentageMaterialCh1":(n+5,1,fs,100),
				  "PercentageVolumeCh2":(n + 6, 0, ss),
#				   "PercentageMaterialCh2":(n+6,1,fs,100),
				  "PercentageTotalCh1":(n + 7, 0, fs, 100),
				  "PercentageTotalCh2":(n + 8, 0, fs, 100),
				  "PearsonWholeImage":(n + 9, 0, fs2),
				  "PearsonImageAbove":(n + 10, 0, fs2),
				  "PearsonImageBelow":(n + 11, 0, fs2),
#				   "M1":(9,0,fs2),
#				   "M2":(10,0,fs2),
				  "ThresholdM1":(n + 12, 0, fs2),
				  "ThresholdM2":(n + 13, 0, fs2),
				  "SumCh1":(n + 14, 0, ss),
				  "SumCh2":(n + 15, 0, ss),
				  "NonZeroCh1":(n + 16, 0, ss),
				  "OverThresholdCh1":(n + 17, 0, ss),
				  "DiffStainVoxelsCh1":(n + 18, 0, ss),
				  "DiffStainVoxelsCh2":(n + 19, 0, ss),

				  "DiffStainPercentageCh1":(n + 20, 0, ss),
				  "DiffStainPercentageCh2":(n + 21, 0, ss),
				  "RObserved":(n + 22, 0, fs2),
				  "RRandMean":(n + 23, 0, ss),
				  "NumIterations":(n + 24, 0, ss)
		}
	 
	 	#if scripting.TFLag:
	 	#	del mapping["DiffStainPercentageCh1"]
	 	#	del mapping["DiffStainPercentageCh2"]
	 	#	del mapping["DiffStainVoxelsCh1"]
	 	#	del mapping["DiffStainVoxelsCh2"]
	 	#	del mapping["RObserved"]
	 	#	del mapping["RRandMean"]
	 	#	del mapping["NumIterations"]
	 		
	 		
	 	defined = len(variables.keys())
	 		
		for item in mapping.keys():
			val = 0.0
			val1 = ""
			val2 = ""
			if item == "Ch1Th":
				if defined:
					th1 = variables.get("LowerThresholdCh1")
					th2 = variables.get("UpperThresholdCh1")
					val = "%d / %d" % (th1, th2)
					val1 = th1
					val2 = th2
				else:
					val = "0 / 128"
					val1 = 0
					val2 = 128
			elif item == "Ch2Th":
				if defined:
					th1 = variables.get("LowerThresholdCh2")
					th2 = variables.get("UpperThresholdCh2")
					val = "%d / %d" % (th1, th2)
					val1, val2 = th1, th2
				else:
					val = "0 / 128"
					val1, val2 = 0, 128
			elif item == "PercentageVolumeCh1":
				if defined:
					pvolch = variables.get(item)
					pmatch = variables.get("PercentageMaterialCh1")
					if not pvolch:
						pvolch = 0
					if not pmatch:
						pmatch = 0
					val = "%.3f%% / %.3f%%" % (pvolch * 100, pmatch * 100)
					val1 = "%.3f%%" % (pvolch * 100)
					val2 = "%.3f%%" % (pmatch * 100)
				else:
					val = "0.000% / 0.000%"
					val1 = "0.000%"
					val2 = "0.000%"
			elif item == "PercentageVolumeCh2":
				if defined:
					pvolch = variables.get(item)
					pmatch = variables.get("PercentageMaterialCh2")
					if not pvolch:
						pvolch = 0
					if not pmatch:
						pmatch = 0
					val = "%.3f%% / %.3f%%" % (pvolch * 100, pmatch * 100)
					if not pvolch:
						pvolch = 0
					if not pmatch:
						pmatch = 0
					val1 = "%.3f%%" % (pvolch * 100)
					val2 = "%.3f%%" % (pmatch * 100)
				else:
					val = "0.000% / 0.000%"
					val1 = "0.000%"
					val2 = "0.000%"
			elif item == "SumCh1":
				if defined:
					sum = variables.get(item)
					sumth = variables.get("SumOverThresholdCh1")
					
					if not sum:
						sum = 0
					if not sumth:
						sumth = 0
					val = "%d / %d" % (sum, sumth)
					val1 = sum
					val2 = sumth
				else:
					val = "0 / 0"
					val1 = 0
					val2 = 0
			elif item == "SumCh2":
				if defined:
					sum = variables.get(item)
					sumth = variables.get("SumOverThresholdCh2")
					if not sum:
						sum = 0
					if not sumth:
						sumth = 0
					val = "%d / %d" % (sum, sumth)
					val1 = sum
					val2 = sumth
				else:
					val = "0 / 0"  
					val1 = 0
					val2 = 0
			elif item == "NonZeroCh1":
				if defined:
					sum = variables.get(item)
					sumth = variables.get("NonZeroCh2")
					if not sum:
						sum = 0
					if not sumth:
						sumth = 0
					val = "%d / %d" % (sum, sumth)
					val1 = sum
					val2 = sumth
				else:
					val = "0 / 0"  
					val1 = 0
					val2 = 0
			elif item == "OverThresholdCh1":
				if defined:
					sum = variables.get(item)
					sumth = variables.get("OverThresholdCh2")
					if not sum:
						sum = 0
					if not sumth:
						sumth = 0
					val = "%d / %d" % (sum, sumth)
					val1 = sum
					val2 = sumth
				else:
					val = "0 / 0"  
					val1 = 0
					val2 = 0   

			elif item == "DiffStainVoxelsCh1":
				if defined:
					ds = variables.get(item)
					dsint = variables.get("DiffStainIntCh1")
					if not ds:
						ds = 0
					if not dsint:
						dsint = 0
					val = "%.3f / %.3f" % (ds, dsint)
					val1 = ds
					val2 = dsint
				else:
					val = "0.000 / 0.000"			   
					val1 = 0.000
					val2 = 0.000
			elif item == "DiffStainVoxelsCh2":
				if defined:
					ds = variables.get(item)
					dsint = variables.get("DiffStainIntCh2")
					if not ds:
						ds = 0
					if not dsint:
						dsint = 0
					val = "%.3f / %.3f" % (ds, dsint)
					val1 = ds
					val2 = dsint
				else:
					val = "0.000 / 0.000"
					val1 = 0.000
					val2 = 0.000
					
			elif item == "DiffStainPercentageCh1":
				if defined:
					ds = variables.get("DiffStainVoxelsCh1")
					dsint = variables.get("DiffStainIntCh1")
					if not ds:
						ds = 0
					if not dsint:
						dsint = 0
					ds = 1.0 / (ds + 1)
					dsint = 1.0 / (dsint + 1.0)
					val = "%.3f / %.3f" % (ds, dsint)
					val1 = ds
					val2 = dsint
				else:
					val = "0.000 / 0.000"
					val1 = 0.0
					val2 = 0.0
			elif item == "DiffStainPercentageCh2":
				if defined:
					ds = variables.get("DiffStainVoxelsCh2")
					dsint = variables.get("DiffStainIntCh2")
					if not ds:
						ds = 0
					if not dsint:
						dsint = 0
					ds = 1.0 / (ds + 1)
					dsint = 1.0 / (dsint + 1.0)
					val = "%.3f / %.3f" % (ds, dsint)
					val1 = ds
					val2 = dsint
				else:
					val = "0.000 / 0.000"
					val1 = 0.0
					val2 = 0.0					  
			elif item == "RRandMean":
				if defined:
					randmean = variables.get(item)
					stdev = variables.get("RRandSD")
					if not randmean:
						randmean = 0
					if not stdev:
						stdev = 0
				else:
					randmean = 0
					stdev = 0
				val = u"%.3f \u00B1 %.5f" % (randmean, stdev)
			elif item == "NumIterations":
				if defined:
					n1 = variables.get("NumIterations")
					n2 = variables.get("ColocCount")
					if not n1:
						n1 = 0
					if not n2:
						n2 = 0
					val1 = int(n1 - n2)
					val2 = n2
				else:
					val1 = 0
					val2 = 0
				val = "%d / %d" % (val1, val2)
				
			else:
				val = variables.get(item, None)
			if not val:
				val = 0
			try:
				index, col, format, scale = mapping[item]
			except:
				index, col, format = mapping[item]
				scale = 1
			index += offset
			col += coloffset
			val *= scale
			
			if not val1:
				val1 = val
				val2 = ""
			self.headervals[index][1] = val1
			self.headervals[index][2] = val2
			self.SetStringItem(index, col, format % val)
