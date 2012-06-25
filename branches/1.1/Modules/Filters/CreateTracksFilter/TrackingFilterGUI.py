#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
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
__version__ = "$Revision: 1.42 $"
__date__ = "$Date: 2005/01/13 14:52:39 $"

import wx.grid as gridlib
import wx
import lib.messenger
import scripting

class TrackTable(gridlib.PyGridTableBase):
	"""
	A class representing the table containing the tracks
	"""
	def __init__(self, rows = 1, cols = 10, canEnable = 0):
		"""
		Initialize the track table
		"""
		gridlib.PyGridTableBase.__init__(self)
	
		self.enabledCol = 0
		self.canEnable = canEnable
		if canEnable:
			self.enabledCol = 1
		self.odd = gridlib.GridCellAttr()
		#self.odd.SetBackgroundColour("sky blue")
		self.even = gridlib.GridCellAttr()
		self.even.SetBackgroundColour(wx.Colour(230, 247, 255))
		self.disabledAttr = gridlib.GridCellAttr()
		self.disabledAttr.SetBackgroundColour(wx.Colour(128, 128, 128))
		self.numberOfCols = cols
		self.numberOfRows = rows
		self.odd.SetReadOnly(1)
		self.even.SetReadOnly(1)
		self.gridValues = {}
		self.enabled = {}
		
	def getEnabled(self):
		"""
		return the rows that are enabled
		"""
		ret = []
		for key, val in self.enabled.items():
			#print "value of ", key, "is", val
			if val:
				ret.append(key)
		return ret

	def setEnabled(self, row, value):
		"""
		Mark row as enabled
		"""
		if value:
			self.enabled[row] = True
		else:
			self.enabled[row] = False

	def GetTypeNameDISABLED(self, row, col):
		"""
		return the type of the given row and col
		"""
		if not self.canEnable or col != 0:
			return gridlib.PyGridTableBase.GetTypeName(self, row, col)
		if col == 0:
			return gridlib.GRID_VALUE_BOOL
		
	def setEnabledColumn(self, col):
		"""
		set the column that can be modified
		"""
		# if there is a column for enabling / disabling this row, then offset
		# the column by one
		if self.canEnable:
			col += 1
		self.enabledCol = col
		
	def GetColLabelValue(self, col):
		"""
		Return the labels of the columns
		"""
		if self.canEnable and col == 0:
			return ""
		elif self.canEnable:
			col -= 1
		return "t%d" % (col + 1)

	def GetAttr(self, row, col, kind):
		"""
		Return the attribute for a given row,col position
		"""
		attr = [self.even, self.odd][row % 2]
		attr.IncRef()
		if col != self.enabledCol:
			self.disabledAttr.IncRef()
			return self.disabledAttr
		return attr

	def GetNumberRows(self):
		"""
		Return the number of rows
		"""    
		return self.numberOfRows
		
	def Clear(self):
		"""
		clear the table
		"""
		self.numberOfRows = 0
		self.gridValues = {}

	def AppendRows(self, n = 1):
		"""
		Add a row
		"""
		self.numberOfRows += n
		print "Number of rows=", self.numberOfRows
		
	def GetNumberCols(self):
		"""
		Return the number of cols
		"""        
		return self.numberOfCols

	def IsEmptyCell(self, row, col):
		"""
		Determine whether a cell is empty or not
		"""            
		return False

	def GetValue(self, row, col):
		"""
		Return the value of a cell
		"""
		if not self.canEnable:
			if (row, col) in self.gridValues:
				return "(%d,%d,%d)" % self.gridValues[(row, col)]
			return ""
		if col == 0:
			val = self.enabled.get(row, False)
			if val:
				return "[x]"
			else:
				return "[  ]"
			
		if (row, col) in self.gridValues:
			return "(%d,%d,%d)" % self.gridValues[(row, col)]
		return ""

	def getPointsAtRow(self, getrow):
		"""
		return the points at a given row
		"""
		ret = []
		for row, col in self.gridValues.keys():
			if row == getrow:
				ret.append(self.gridValues[(row, col)])
		return ret
	
	def getPointsAtColumn(self, getcol):
		"""
		return the points at given columns
		"""
		ret = []
		#for row,col in self.gridValues.keys():
		#    if col==getcol:
		#        ret.append(self.gridValues[(row,col)])
		for row in range(0, self.GetNumberRows()):
			if (row, getcol) in self.gridValues:
				ret.append((self.gridValues[(row, getcol)]))
			else:
				ret.append(None)
		return ret
	
	def CanGetValueAs(self, row, col, typeName):
		return True
	
	def SetValue(self, row, col, value, override = 0):
		"""
		Set the value of a cell
		"""                  
		if self.canEnable:
			if col == 0:
				self.enabled[row] = value
				lib.messenger.send(None, "set_shown_tracks", self.getEnabled())
				return
			
		if col != self.enabledCol and not override:
			return
		self.gridValues[(row, col)] = tuple(map(int, value))


class TrackTableGrid(gridlib.Grid):
	"""
	A grid widget containing the track table
	"""
	def __init__(self, parent, dataUnit, trackFilter, canEnable = 0):
		"""
		Initialize the grid
		"""
		gridlib.Grid.__init__(self, parent, -1, size = (350, 250))

		self.dataUnit = dataUnit
		self.trackFilter = trackFilter

		n = dataUnit.getNumberOfTimepoints()
		self.canEnable = canEnable
		if canEnable:
			n += 1
		table = TrackTable(cols = n, canEnable = canEnable)

		# The second parameter means that the grid is to take ownership of the
		# table and will destroy it when done.  Otherwise you would need to keep
		# a reference to it and call it's Destroy method later.
		self.SetTable(table, False)
		self.table = table
		self.selectedCol = None
		self.selectedRow = None
		self.SetColLabelSize(20)
		self.SetRowLabelSize(20)
		if canEnable:
			self.SetColSize(0, 25)
			for i in range(1,n):
				self.SetColSize(i, 60)        
		else:
			for i in range(n):
				self.SetColSize(i,60)
		
		self.Bind(gridlib.EVT_GRID_CELL_RIGHT_CLICK, self.OnRightDown)  
		self.Bind(gridlib.EVT_GRID_CELL_LEFT_CLICK, self.OnLeftDown) 
		lib.messenger.connect(None, "one_click_center", self.onUpdateCell)
		lib.messenger.connect(None, "timepoint_changed", self.onSetTimepoint)
		
	def getTable(self):

		return self.table
		
	def onSetTimepoint(self, obj, event, timepoint):
		"""
		Update the column that can be edited based on the timepoint
		"""
		self.table.setEnabledColumn(timepoint)
		self.ForceRefresh()
		
	def onUpdateCell(self, obj, event, x, y, z):
		"""
		Store a coordinate in the cell
		"""
		currWin = scripting.visualizer.getCurrentWindow()
		if scripting.currentVisualizationMode == "MIP":
			image = self.trackFilter.getInputFromChannel(0)
			image.Update()
			xdim, ydim, zdim = image.GetDimensions()
			
			possibleObjects = []
			added = []
			for zval in range(0, zdim):
				val = int(image.GetScalarComponentAsDouble(x, y, zval, 0))
				if val not in [0, 1] and val not in added:
					possibleObjects.append((val, zval))
					added.append(val)
			
			menu = wx.Menu()  
			
			if len(possibleObjects) == 1:
				z = possibleObjects[0][1]
			else:
				for val, zval in possibleObjects:
					menuid = wx.NewId()
					newitem = wx.MenuItem(menu, menuid, "Object #%d at depth %d" % (val, zval))
					col = [0, 0, 0]
					ctf = self.dataUnit.getColorTransferFunction()
					ctf.GetColor(val, col)
					r, g, b = col
					r *= 255
					g *= 255
					b *= 255
					newitem.SetBackgroundColour(wx.Colour(r, g, b))
					f = lambda evt, zval = zval, xval = x, yval = y, s = self:s.onSetCell(x = xval, y = yval, z = zval)
					currWin.Bind(wx.EVT_MENU, f, id = menuid)
					menu.AppendItem(newitem)
					
				pos = currWin.xoffset + x * currWin.zoomFactor, currWin.yoffset + y * currWin.zoomFactor
				currWin.PopupMenu(menu, pos)
			
				return
		self.onSetCell(x, y, z)                
			
	def onSetCell(self, x, y, z):
		"""
		Set the value of the grid at given points
		"""        
		if self.selectedRow != None and self.selectedCol != None:
			self.table.SetValue(self.selectedRow, self.selectedCol, (x, y, z))
		self.ForceRefresh()
		
	def onNewTrack(self, event):
		"""
		Add a new track to the table
		"""
		self.AppendRows()
		self.SetTable(self.table, False)
		self.ForceRefresh() 
		
	def getTimepoint(self):
		"""
		return the last modified timepoint
		"""
		if not self.selectedCol:
			return 0
		return self.selectedCol
		
	def getSeedPoints(self):
		"""
		return the selected seed points
		"""
		#rows=[]
		cols = []
		#for i in range(0,self.table.GetNumberRows()):
		#    rows.append(self.table.getPointsAtRow(i))
		for i in range(0, self.table.GetNumberCols()):
			pts = self.table.getPointsAtColumn(i)
			while None in pts:
				pts.remove(None)
			# If after removing all the empty cells there are no seed points in this 
			# timepoint then return the current columns
			if len(pts) == 0:
				return cols
			cols.append(pts)
		return cols
		#if self.selectedCol!=None:            
		#    return self.table.getPointsAtColumn(self.selectedCol)
		#return []
		
	def OnRightDown(self, event):
		"""
		An event handler for right clicking
		"""
		print self.GetSelectedRows()
		
	def OnLeftDown(self, event):
		"""
		An event handler for left clicking
		"""
		if event.GetCol() == 0 and self.canEnable:
			val = self.table.enabled.get(event.GetRow(), False)
			val = not val
			self.table.SetValue(event.GetRow(), event.GetCol(), val)
			self.ForceRefresh()

			return
		#print "Selected",event.GetRow(),event.GetCol()
		self.selectedRow = event.GetRow()
		self.selectedCol = event.GetCol()

	def showTracks(self, tracks):
		"""
		show the given tracks in the track grid
		"""
		table = self.getTable()
		table.Clear()
		table.AppendRows(len(tracks))
		for i, track in enumerate(tracks):
			mintp, maxtp = track.getTimeRange()
			for tp in range(mintp, maxtp + 1):
				val, pos = track.getObjectAtTime(tp)
				if val:
					table.SetValue(i, tp, pos, override = 1)
		self.SetTable(table)
		self.ForceRefresh()
