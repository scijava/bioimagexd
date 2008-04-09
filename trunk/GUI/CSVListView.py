#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: UIElements
 Project: BioImageXD
 Created: 30.6.2007, KP
 Description:

 A list view that will take input similiar to what the csv module takes, and view it as a list ctrl
 with the option to open it in a spreadsheet program or export it out a file
 
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
import wx
import lib.messenger

class CSVListView(wx.ListCtrl):
	"""
	A list control that takes a list of lists and shows that
	"""
	def __init__(self, parent, size = (350, 200)):
		wx.ListCtrl.__init__(
			self, parent, -1, 
			size = size,
			style = wx.LC_REPORT | wx.LC_VIRTUAL | wx.LC_HRULES | wx.LC_VRULES,
			)

		self.SetItemCount(1)
		self.data = []
		
		self.attr1 = wx.ListItemAttr()
		self.attr1.SetBackgroundColour("white")

		self.attr2 = wx.ListItemAttr()
		self.attr2.SetBackgroundColour("light blue")
		self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)

	def exportToCsv(self, filename, headers = []):
		"""
		write out the data to a .csv file
		"""
		f = codecs.open(filename, "wb", "latin-1")
		w = csv.writer(f, dialect = "excel", delimiter = ";")
		self.writeOut(w, headers)
		
	def writeOut(self, w, headers = []):
		"""
		Write the data out
		"""
		for i in headers:
			w.writerow(i)
		for line in self.data:
			w.writerow(line)
		return w

		
	def importFromCsv(self, filename):
		"""
		read a .csv file and show it in the list box
		"""
		pass
		
	def OnItemActivated(self, event):
		self.currentItem = event.m_itemIndex
		lib.messenger.send(self, "item_activated", event.m_itemIndex)

		
	def setContents(self, data):
		"""
		Set the contents of the list view
		"""    
		assert type(data) == types.ListType
		self.ClearAll()
		for i, headerName in enumerate(data[0]):
			self.InsertColumn(i, headerName)
		self.data = data[1:]
		self.SetItemCount(len(data[1:]))

	def OnGetItemText(self, item, col):
		"""
		A method that returns the value of the given column of given row
		"""        
		try:
			row = self.data[item]
			if not row:
				return ""
			data = row[col]
			if not data:
				return ""
		except:
			return ""
		if type(data) not in [types.StringType, types.UnicodeType]:
			return str(data)
		return data
 
	def OnGetItemImage(self, item):
		"""
		Return an image for the item
		"""    
		return - 1

	def OnGetItemAttr(self, item):
		"""
		Return the attribute for the given item
		"""    
	
		if item % 2 == 1:
			return self.attr1
		elif item % 2 == 0:
			return self.attr2
		else:
			return None
