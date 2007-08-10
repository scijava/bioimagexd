#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: TrackingFilters
 Project: BioImageXD
 Created: 13.04.2006, KP
 Description:

 A module containing filters used in the tracking task
							
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

#import lib.Particle

import scripting
import GUI.CSVListView as CSVListView
import wx.grid as gridlib
import GUI.GUIBuilder as GUIBuilder
import lib.ImageOperations
import lib.messenger
from lib import Particle
import lib.ProcessingFilter
import lib.Track
import os
import os.path
import SegmentationFilters
import types
import vtk
import wx

TRACKING = "Tracking"

#---------------------------------------------------------------------------

class TrackTable(gridlib.PyGridTableBase):
	"""
	Created: 21.11.2006, KP
	Description: A class representing the table containing the tracks
	"""
	def __init__(self, rows = 1, cols = 10, canEnable = 0):
		"""
		Created: 21.11.2006, KP
		Description: Initialize the track table
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
		Created: 14.04.2007, KP
		Description: return the rows that are enabled
		"""
		ret = []
		for key, val in self.enabled.items():
			print "value of ", key, "is", val
			if val:
				ret.append(key)
		return ret

	def GetTypeNameDISABLED(self, row, col):
		"""
		Created: 14.04.2007, KP
		Description: return the type of the given row and col
		"""
		if not self.canEnable or col != 0:
			return gridlib.PyGridTableBase.GetTypeName(self, row, col)
		if col == 0:
			return gridlib.GRID_VALUE_BOOL
		
	def setEnabledColumn(self, col):
		"""
		Created: 23.11.2006, KP
		Description: set the column that can be modified
		"""
		# if there is a column for enabling / disabling this row, then offset
		# the column by one
		if self.canEnable:
			col += 1
		self.enabledCol = col
		
	def GetColLabelValue(self, col):
		"""
		Created: 21.11.2006, KP
		Description: Return the labels of the columns
		"""
		if self.canEnable and col == 0:
			return ""
		elif self.canEnable:
			col -= 1
		return "t%d" % (col + 1)

	def GetAttr(self, row, col, kind):
		"""
		Created: 21.11.2006, KP
		Description: Return the attribute for a given row,col position
		"""
		attr = [self.even, self.odd][row % 2]
		attr.IncRef()
		if col != self.enabledCol:
			self.disabledAttr.IncRef()
			return self.disabledAttr
		return attr

	def GetNumberRows(self):
		"""
		Created: 21.11.2006, KP
		Description: Return the number of rows
		"""    
		return self.numberOfRows
		
	def Clear(self):
		"""
		Created: 26.11.2006, KP
		Description: clear the table
		"""
		self.numberOfRows = 0
		self.gridValues = {}

	def AppendRows(self, n = 1):
		"""
		Created: 21.11.2006, KP
		Description: Add a row
		"""
		self.numberOfRows += n
		print "NUmber of rows=", self.numberOfRows
		
	def GetNumberCols(self):
		"""
		Created: 21.11.2006, KP
		Description: Return the number of cols
		"""        
		return self.numberOfCols

	def IsEmptyCell(self, row, col):
		"""
		Created: 21.11.2006, KP
		Description: Determine whether a cell is empty or not
		"""            
		return False

	def GetValue(self, row, col):
		"""
		Created: 21.11.2006, KP
		Description: Return the value of a cell
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
		Created: 26.11.2006, KP
		Description: return the points at a given row
		"""
		ret = []
		for row, col in self.gridValues.keys():
			if row == getrow:
				ret.append(self.gridValues[(row, col)])
		return ret        
	def getPointsAtColumn(self, getcol):
		"""
		Created: 22.11.2006, KP
		Description: return the points at given columns
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
		Created: 21.11.2006, KP
		Description: Set the value of a cell
		"""                  
		print "SetValue", row, col, value, override
		if self.canEnable:
			if col == 0:
				print "Row", row, "has value=", value
				self.enabled[row] = value
				
				lib.messenger.send(None, "set_shown_tracks", self.getEnabled())
				return
			
		
		if col != self.enabledCol and not override:
			return
		print "Setting value at", row, col, "to", value
		self.gridValues[(row, col)] = tuple(map(int, value))


class TrackTableGrid(gridlib.Grid):
	"""
	Created: 21.11.2006, KP
	Description: A grid widget containing the track table
	"""
	def __init__(self, parent, dataUnit, trackFilter, canEnable = 0):
		"""
		Created: 21.11.2006, KP
		Description: Initialize the grid
		"""
		gridlib.Grid.__init__(self, parent, -1, size = (350, 250))

		self.dataUnit = dataUnit
		self.trackFilter = trackFilter
		n = dataUnit.getNumberOfTimepoints()
		self.canEnable = canEnable
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
		for i in range(n):
			
			self.SetColSize(i, 60)        
		
		if canEnable:
			self.SetColSize(0, 25)
		self.Bind(gridlib.EVT_GRID_CELL_RIGHT_CLICK, self.OnRightDown)  
		self.Bind(gridlib.EVT_GRID_CELL_LEFT_CLICK, self.OnLeftDown) 
		lib.messenger.connect(None, "get_voxel_at", self.onUpdateCell)
		lib.messenger.connect(None, "timepoint_changed", self.onSetTimepoint)
		
	def getTable(self):

		return self.table
		
	def onSetTimepoint(self, obj, event, timepoint):
		"""
		Created: 23.11.2006, KP
		Description: Update the column that can be edited based on the timepoint
		"""
		self.table.setEnabledColumn(timepoint)
		self.ForceRefresh()
		
	def onUpdateCell(self, obj, event, x, y, z, scalar, rval, gval, bval, r, g, b, a, ctf):
		"""
		Created: 21.11.2006, KP
		Description: Store a coordinate in the cell
		"""
		#print self.selectedCol,self.selectedRow,x,y,z
		print "onUpdateCell", x, y, z
		currWin = scripting.visualizer.getCurrentWindow()
		if currWin.isMipMode():
			 
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
				print "Only one object"
			else:
				print len(possibleObjects), "objects"
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
					print "Zval = ", zval, "val=", val
					f = lambda evt, zval = zval, xval = x, yval = y, s = self:s.onSetCell(x = xval, y = yval, z = zval)
					currWin.Bind(wx.EVT_MENU, f, id = menuid)
					menu.AppendItem(newitem)
					
				pos = currWin.xoffset + x * currWin.zoomFactor, currWin.yoffset + y * currWin.zoomFactor
				print "Showing at ", pos
				currWin.PopupMenu(menu, pos)
			
				return
		self.onSetCell(x, y, z)                
			
	def onSetCell(self, x, y, z):
		"""
		Created: 23.11.2006, KP
		Description: Set the value of the grid at given points
		"""        
		if self.selectedRow != None and self.selectedCol != None:
			self.table.SetValue(self.selectedRow, self.selectedCol, (x, y, z))
		self.ForceRefresh()
		
	def onNewTrack(self, event):
		"""
		Created: 21.11.2006, KP
		Description: Add a new track to the table
		"""
		self.AppendRows()
		self.SetTable(self.table, False)
		self.ForceRefresh() 
		
	def getTimepoint(self):
		"""
		Created: 22.11.2006, KP
		Description: return the last modified timepoint
		"""
		if not self.selectedCol:
			return 0
		return self.selectedCol
		
	def getSeedPoints(self):
		"""
		Created: 22.11.2006, KP
		Description: return the selected seed points
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
		Created: 21.11.2006, KP
		Description: An event handler for right clicking
		"""
		print self.GetSelectedRows()
		
	def OnLeftDown(self, event):
		"""
		Created: 21.11.2006, KP
		Description: An event handler for left clicking
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


def getFilters():
    """
    Created: 10.8.2007, SS
    Description: This function returns all the filter-classes in this module and is used by ManipulationFilters.getFilterList()
    """
    return [CreateTracksFilter, ViewTracksFilter, AnalyzeTracksFilter]


class CreateTracksFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	Created: 13.04.2006, KP
	Description: A filter for tracking objects in a segmented image
	"""     
	name = "Create tracks"
	category = TRACKING
	
	def __init__(self):
		"""
		Created: 13.04.2006, KP
		Description: Initialization
		"""        
		self.tracks = []
		self.track = None
		self.tracker = None
		self.trackGrid = None
		self.objectsReader = None
		self.delayReading = 0
		self.ctf = None
		self.particleFile = ""

		lib.ProcessingFilter.ProcessingFilter.__init__(self, (1, 1))
		
		self.descs = {
			"MaxVelocity": "Max. change in distance (% of max.movement)",
			"MaxSizeChange": "Max. size change (% of size)",
			"MaxDirectionChange": "Direction (angle of the allowed sector in degrees)",
			"MaxIntensityChange": "Max. change of average intensity (% of max. diff.)",
			"MinLength": "Min. length of track (# of timepoints)",
			"MinSize": "Min. size of tracked objects",
			"TrackFile": "Object statistics file:",
			"SizeWeight": "Weight (0-100%):", "DirectionWeight": "Weight (0-100%):",
			"IntensityWeight": "Weight (0-100%):",
			"VelocityWeight": "Weight (0-100%):",
			"ResultsFile": "File to store the results:",
			"Track": "Track to visualize",
			"UseROI": "Select seed objects using ROI:", "ROI": "ROI for tracking:"}
			
		lib.messenger.connect(None, "selected_objects", self.onSetSelectedObjects)
	
		self.numberOfPoints = None
		self.selectedTimepoint = 0
		lib.messenger.connect(None, "timepoint_changed", self.onSetTimepoint)
		
		
	def onSetTimepoint(self, obj, event, timepoint):
		"""
		Created: 23.11.2006, KP
		Description: Update the column that can be edited based on the timepoint
		"""        
		self.selectedTimepoint = timepoint
		self.updateObjects()
		
	def onSetSelectedObjects(self, obj, event, objects, isROI = 0):
		"""
		Created: 26.11.2006, KP
		Description: An event handler for highlighting selected objects
		"""
		print "\n\nonSetSelectedObjects(", obj, event, objects, ")"
		if not self.ctf:
			self.ctf = self.dataUnit.getColorTransferFunction()
		if not objects:
			
			self.dataUnit.getSettings().set("ColorTransferFunction", self.ctf)
			lib.messenger.send(None, "data_changed", 0)
			return

		if not isROI:
			# Since these object id's come from the list indices, instead of being the actual
			# intensity values, we need to add 2 to each object value to account for the
			# pseudo objects 0 and 1 produced by the segmentation results
			objects = [x + 2 for x in objects]
		self.selections = objects
		ctf = vtk.vtkColorTransferFunction()
		minval, maxval = self.ctf.GetRange()
		hv = 0.4
		ctf.AddRGBPoint(0, 0, 0, 0)
		ctf.AddRGBPoint(1, 0, 0, 0)
		ctf.AddRGBPoint(2, hv, hv, hv)
		ctf.AddRGBPoint(maxval, hv, hv, hv)
		for obj in objects:
			val = [0, 0, 0]
			if obj - 1 not in objects:
				ctf.AddRGBPoint(obj - 1, hv, hv, hv)
			ctf.AddRGBPoint(obj, 0.0, 1.0, 0.0)
			if obj + 1 not in objects:
				ctf.AddRGBPoint(obj + 1, hv, hv, hv)
		print "Setting CTF where highlighted=", objects
		self.dataUnit.getSettings().set("ColorTransferFunction", ctf)
		lib.messenger.send(None, "data_changed", 0)
		
		
	def setParameter(self, parameter, value):
		"""
		Created: 13.04.2006, KP
		Description: Set a value for the parameter
		"""    
		lib.ProcessingFilter.ProcessingFilter.setParameter(self, parameter, value)
		if parameter == "TrackFile":
			self.particleFile = value
		elif parameter == "ResultsFile" and os.path.exists(value):
			pass
#            self.track = lib.Track.Track(value)
#            self.tracks = self.track.getTracks(self.parameters["MinLength"])
#            print "Read %d tracks"%(len(self.tracks))
#            lib.messenger.send(self,"update_Track")
			#if self.parameters.has_key("Track") and self.tracks:
			#    lib.messenger.send(None,"visualize_tracks",[self.tracks[self.parameters["Track"]]])
			#    lib.messenger.send(None,"update_helpers",1)
		elif parameter == "Track":
			if self.tracks:
				lib.messenger.send(None, "visualize_tracks", [self.tracks[self.parameters["Track"]]])            
				lib.messenger.send(None, "update_helpers", 1)
		elif parameter == "ROI":
			roi = self.parameters["ROI"]
			if roi and self.parameters["UseROI"]:
				selections = self.getObjectsForROI(roi)
				# The last boolean is a flag indicating that this selection
				# comes from a ROI
				lib.messenger.send(None, "selected_objects", selections, True)
				
		if parameter == "MinLength":
			lib.messenger.send(self, "update_Track")
	
	def getParameters(self):
		"""
		Created: 14.08.2006, KP
		Description: Return the list of parameters needed for configuring this GUI
		"""            
		return [["Change between consecutive objects",
		("MaxVelocity", "VelocityWeight",
		"MaxSizeChange", "SizeWeight",
		"MaxIntensityChange", "IntensityWeight",
		"MaxDirectionChange", "DirectionWeight")],
		["Region of Interest", ("UseROI", "ROI")],
		["Tracking", ("MinLength", "MinSize")],
		["Load object info", (("TrackFile", "Select file with object statistics to load", "*.csv"), )],
		["Tracking Results", (("ResultsFile", "Select track file that contains the results", "*.csv"), )],
		]
		
	def getDesc(self, parameter):
		"""
		Created: 14.08.2006, KP
		Description: Return the description of the parameter
		"""    
		return self.descs[parameter]
		
	def getLongDesc(self, parameter):
		"""
		Created: 14.08.2006, KP
		Description: Return a long description of the parameter
		""" 
		return ""
		
		
	def getType(self, parameter):
		"""
		Created: 14.08.2006, KP
		Description: Return the type of the parameter
		"""    
		if parameter == "UseSize":
			return types.BooleanType
		elif parameter in ["MaxVelocity", "MaxSizeChange", "MinLength", "MinSize"]:
			return GUIBuilder.SPINCTRL
		elif parameter in ["SizeWeight", "DirectionWeight", "IntensityWeight", "MaxDirectionChange", \
							"MaxIntensityChange", "MaxSizeChange", "VelocityWeight"]:
			return GUIBuilder.SPINCTRL
		if parameter == "Track":
			return GUIBuilder.SLICE     
		if parameter == "ROI":
			return GUIBuilder.ROISELECTION
		if parameter == "UseROI":
			return types.BooleanType
		return GUIBuilder.FILENAME
		
	def getRange(self, parameter):
		"""
		Created: 14.08.2006, KP
		Description: Return the range of given parameter
		"""             
		if parameter in ["MaxVelocity", "MinSize"]:
			return (0, 999)
		if parameter == "MaxSizeChange":
			return (0, 100)
		if parameter == "Track":
			if self.track:
				minlength = self.parameters["MinLength"]
				return 0, self.track.getNumberOfTracks(minlength)            
		if parameter == "MinLength":
			if self.numberOfPoints:
				return 0, self.numberOfPoints
			return 0, 1
		if parameter == "MaxDirectionChange":
			return (0, 360)
		return (0, 100)
				
	def getDefaultValue(self, parameter):
		"""
		Created: 14.08.2006, KP
		Description: Return the default value of a parameter
		"""     
		if parameter == "UseSize":
			return 1
		if parameter == "MinSize":
			return 6
		if parameter == "MaxVelocity":
			return 5
		if parameter == "MaxSizeChange":
			return 35
		if parameter == "MinLength":
			return 3
		if parameter in ["IntensityWeight", "SizeWeight", "DirectionWeight", "VelocityWeight"]:
			return 25
		if parameter == "MaxDirectionChange":
			return 45
		if parameter == "MaxIntensityChange":
			return 40
		if parameter == "MaxSizeChange":
			return 25
		#if parameter=="Track":return 0            
		if parameter == "ResultsFile":
			return "track_results.csv"
		if parameter == "UseROI":
			return 0
		if parameter == "ROI":
			n = scripting.visualizer.getRegionsOfInterest()
			if n:
				return n[0]
			return 0            
		if parameter == "TrackFile":
			if self.particleFile:
				return self.particleFile
		return "statistics.csv"
		
	def setDataUnit(self, dataUnit):
		"""
		Created: 04.04.2007, KP
		Description: a method to set the dataunit used by this filter
		"""
		lib.ProcessingFilter.ProcessingFilter.setDataUnit(self, dataUnit)
		tracksFile = dataUnit.getSettings().get("StatisticsFile")
		print "GOT TRACKS FILE=", tracksFile
		if tracksFile and os.path.exists(tracksFile):
			print "ReaDING TRACKS FILE"
			self.parameters["TrackFile"] = tracksFile
			self.particleFile = tracksFile
			self.delayReading = 1
			
	def getGUI(self, parent, taskPanel):
		"""
		Created: 21.11.2006, KP
		Description: Return the GUI for this filter
		"""              
		gui = lib.ProcessingFilter.ProcessingFilter.getGUI(self, parent, taskPanel)
		
				
		if not self.trackGrid:
			self.trackGrid = TrackTableGrid(self.gui, self.dataUnit, self)
			self.reportGUI = SegmentationFilters.WatershedObjectList(self.gui, -1, (350, 100))
			sizer = wx.BoxSizer(wx.VERTICAL)
			sizer.Add(self.trackGrid, 1)
			
			
			#sizer.Add(self.trackGrid,1)
						
			box = wx.BoxSizer(wx.HORIZONTAL)
			
			self.readBtn = wx.Button(self.gui, -1, "Read objects")
			self.readTracksBtn = wx.Button(self.gui, -1, "Read tracks")
			self.newTrackBtn = wx.Button(self.gui, -1, "New track")
			self.calcTrackBtn = wx.Button(self.gui, -1, "Calculate tracks")
			box.Add(self.readBtn)
			box.Add(self.readTracksBtn)
			box.Add(self.newTrackBtn)
			box.Add(self.calcTrackBtn)
			
			#self.newTrackBtn.Enable(0)
			self.calcTrackBtn.Enable(0)
			
			self.readTracksBtn.Bind(wx.EVT_BUTTON, self.onReadTracks)
			self.readBtn.Bind(wx.EVT_BUTTON, self.onReadObjects)
			self.newTrackBtn.Bind(wx.EVT_BUTTON, self.trackGrid.onNewTrack)
			self.calcTrackBtn.Bind(wx.EVT_BUTTON, self.onDoTracking)
			
			sizer.Add(box)
			
			self.toggleBtn = wx.ToggleButton(self.gui, -1, "Show seed objects>>")
			self.toggleBtn.SetValue(0)
			self.toggleBtn.Bind(wx.EVT_TOGGLEBUTTON, self.onShowObjectList)
			sizer.Add(self.toggleBtn)            
			sizer.Add(self.reportGUI, 1)
			sizer.Show(self.reportGUI, 0)
			
			self.guisizer = sizer
			self.useSelectedBtn = wx.Button(self.gui, -1, "Use select as seeds")
			self.useSelectedBtn.Bind(wx.EVT_BUTTON, self.onUseSelectedSeeds)
			sizer.Add(self.useSelectedBtn)
			
			pos = (0, 0)
			item = gui.sizer.FindItemAtPosition(pos)
			if item.IsWindow():
				win = item.GetWindow()
			elif item.IsSizer():
				win = item.GetSizer()
			elif item.IsSpacer():
				win = item.GetSpacer()
			
			gui.sizer.Detach(win)            
			gui.sizer.Add(sizer, (0, 0), flag = wx.EXPAND | wx.ALL)
			gui.sizer.Add(win, (1, 0), flag = wx.EXPAND | wx.ALL)
			self.gui = gui
			
		if self.delayReading:
			self.onReadObjects(None)
			self.delayReading = 0
		return gui
		
	def getObjectsForROI(self, roi):
		"""
		Created: 26.11.2006, KP
		Description: return the intensity values of objects in a given roi
		"""
		
		imagedata = self.getInputFromChannel(0)
		mx, my, mz = self.dataUnit.getDimensions()
		n, maskImage = lib.ImageOperations.getMaskFromROIs([roi], mx, my, mz)
		maskFilter = vtk.vtkImageMask()
		maskFilter.SetMaskedOutputValue(0)
		maskFilter.SetMaskInput(maskImage)
		maskFilter.SetImageInput(imagedata)
		maskFilter.Update()
		data = maskFilter.GetOutput()
		histogram = lib.ImageOperations.get_histogram(data)
		ret = []
		for i in range(2, len(histogram)):
			if histogram[i]:
				ret.append(i)
		return ret
		
	def onUseSelectedSeeds(self, event):
		"""
		Created: 26.11.2006, KP
		Description: use the selected seed list
		"""
		if self.parameters["UseROI"]:
			roi = self.parameters["ROI"]
			selections = []
			if roi:
				selections = self.getObjectsForROI(roi)
		else:
			selections = self.selections[:]
		
		if self.ctf:
			self.dataUnit.getSettings().set("ColorTransferFunction", self.ctf)
			self.ctf = None
			lib.messenger.send(None, "data_changed", 0)

		print "Selected", len(selections), "objects"
		n = self.trackGrid.getTable().GetNumberRows()
		n2 = len(selections)
		if n2 > n:
			self.trackGrid.AppendRows(n2 - n)
			self.trackGrid.SetTable(self.trackGrid.getTable())
		
		currTp = self.trackGrid.getTimepoint()
		print "timepoint=", currTp
		particles = self.tracker.getParticles(currTp, selections)
		for i, obj in enumerate(particles):
			self.trackGrid.getTable().SetValue(i, currTp, obj.getCenterOfMass())
		self.trackGrid.ForceRefresh()
		
	def onShowObjectList(self, event):
		"""
		Created: 26.11.2006, KP
		Description: show a list of objects that can be used as seeds for trakcing
		"""
		val = self.toggleBtn.GetValue()
		if not val:
			self.toggleBtn.SetLabel("Show seed objects >>")
		else:
			self.toggleBtn.SetLabel("<< Hide seed objects")
		self.guisizer.Show(self.reportGUI, val)
		self.gui.Layout()
		#self.parent.Layout()
		#self.parent.FitInside()
		
		
	def execute(self, inputs, update = 0, last = 0):
		"""
		Created: 14.08.2006, KP
		Description: Execute the filter with given inputs and return the output
		"""            
		if not lib.ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None
		image = self.getInputFromChannel(0)
		return image
	
	def onReadTracks(self, event):
		"""
		Created: 22.11.2006, KP
		Description: Read tracks from a file instead of calculating them
		"""
		filename = self.parameters["ResultsFile"]
		if not os.path.exists(filename):
			return
		self.track = lib.Track.TrackReader()
		self.track.readFromFile(filename)
		self.tracks = self.track.getTracks(self.parameters["MinLength"])
		n = len(self.tracks)
		lib.messenger.send(self, "update_Track")
		print "Read %d tracks" % (n)
		print self.tracks
		self.showTracks(self.tracks)
		
	def showTracks(self, tracks):
		"""
		Created: 26.11.2006, KP
		Description: show the given tracks in the track grid
		"""
		table = self.trackGrid.getTable()
		table.Clear()
		table.AppendRows(len(tracks))
		for i, track in enumerate(tracks):
			mintp, maxtp = track.getTimeRange()
			print "Track", i, "has time range", mintp, maxtp
			for tp in range(mintp, maxtp + 1):
				val, pos = track.getObjectAtTime(tp)
				print "    value at tp ", tp, "(pos ", pos, ") is ", val
				table.SetValue(i, tp, pos, override = 1)
		self.trackGrid.SetTable(table)
		self.trackGrid.ForceRefresh()
		
		
	def onReadObjects(self, event):
		"""
		Created: 22.11.2006, KP
		Description: Read the object statistics from the given file
		"""
		if not self.particleFile:
			return
		if not self.tracker:
			self.tracker = Particle.ParticleTracker()
			#self.tracker = lib.Particle.ParticleTracker()
		self.tracker.setFilterObjectSize(self.parameters["MinSize"])

		self.tracker.readFromFile(self.particleFile, statsTimepoint = self.selectedTimepoint)      
		rdr = self.objectsReader = self.tracker.getReader()
		
		self.reportGUI.setVolumes(rdr.getVolumes())
		self.reportGUI.setCentersOfMass(rdr.getCentersOfMass())
		self.reportGUI.setAverageIntensities(rdr.getAverageIntensities())    
		
		self.calcTrackBtn.Enable(1)
		
	def updateObjects(self):
		"""
		Created: 26.11.2006, KP
		Description: update the objects list
		"""
		if self.objectsReader:
			rdr = self.objectsReader            
			rdr.read(statsTimepoint = self.selectedTimepoint)
			self.reportGUI.setVolumes(rdr.getVolumes())
			self.reportGUI.setCentersOfMass(rdr.getCentersOfMass())
			self.reportGUI.setAverageIntensities(rdr.getAverageIntensities())    
			
	def getObjectFromCoord(self, pt, timepoint = -1):
		"""
		Created: 22.11.2006, KP
		Description: return an intensity value at given x,y,z
		"""
		if not pt:
			return None
		x, y, z = pt
#        print "Getting from ",x,y,z
		image = self.getInputFromChannel(0, timepoint = timepoint)
		intensity = int(image.GetScalarComponentAsDouble(x, y, z, 0))
		return intensity
		
	def onDoTracking(self, event):
		"""
		Created: 22.11.2006, KP
		Description: Do the actual tracking
		"""
		#print "Using ",image
		#self.vtkfilter.SetInput(image)

				
		self.tracker.setMinimumTrackLength(self.parameters["MinLength"])
		self.tracker.setDistanceChange(self.parameters["MaxVelocity"] / 100.0)
		self.tracker.setSizeChange(self.parameters["MaxSizeChange"] / 100.0)
		self.tracker.setIntensityChange(self.parameters["MaxIntensityChange"] / 100.0)
		self.tracker.setAngleChange(self.parameters["MaxDirectionChange"])
		w1 = self.parameters["VelocityWeight"]
		w2 = self.parameters["SizeWeight"]
		w3 = self.parameters["IntensityWeight"]
		w4 = self.parameters["DirectionWeight"]
		self.tracker.setWeights(w1, w2, w3, w4)
		
		
		objVals = []
		pts = self.trackGrid.getSeedPoints()
		print "Seed points=", pts
		
		for i, col in enumerate(pts):
			f = lambda coord, tp = i: self.getObjectFromCoord(coord, timepoint = tp)
			its = map(f, col)
			
			objVals.append(its)
		print "Objects=", objVals
		while 0 in objVals:
			print "Removing object 0"
			objVals.remove(0)
		while 1 in objVals:
			print "Removing object 1"
			objVals.remove(1)

		#print "Tracking objects with itensities=",its
		
		fromTp = self.trackGrid.getTimepoint()
		print "Tracking from timepoint", fromTp, "forward"        
		self.tracker.track(fromTimepoint = fromTp, seedParticles = objVals)
		self.tracker.writeTracks(self.parameters["ResultsFile"])
	
		self.onReadTracks(None)
		
class ViewTracksFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	Created: 25.04.2006, KP
	Description: A filter for controlling the visualization of the tracking results
	"""     
	name = "View tracks"
	category = TRACKING
	
	def __init__(self):
		"""
		Created: 13.04.2006, KP
		Description: Initialization
		"""        
		self.tracks = []
		self.track = None
		self.tracker = None
		self.trackGrid = None
		self.fileUpdated = 0
		lib.ProcessingFilter.ProcessingFilter.__init__(self, (1, 1))
		
		self.descs = {"MinLength": "Min. length of track (# of timepoints)",
			"ResultsFile": "Tracking results file:",
			"Track": "Track to visualize"}
	
		self.numberOfPoints = None
		lib.messenger.connect(None, "set_shown_tracks", self.updateSelectedTracks)
		
		self.particleFile = ""
	def setParameter(self, parameter, value):
		"""
		Created: 13.04.2006, KP
		Description: Set a value for the parameter
		"""    
		lib.ProcessingFilter.ProcessingFilter.setParameter(self, parameter, value)

		if parameter == "ResultsFile" and os.path.exists(value) and self.trackGrid:
			self.fileUpdated = 1
		 
#            self.track = lib.Track.Track(value)
#            self.tracks = self.track.getTracks(self.parameters["MinLength"])
#            print "Read %d tracks"%(len(self.tracks))
#            lib.messenger.send(self,"update_Track")
			#if self.parameters.has_key("Track") and self.tracks:
			#    lib.messenger.send(None,"visualize_tracks",[self.tracks[self.parameters["Track"]]])
			#    lib.messenger.send(None,"update_helpers",1)
		elif parameter == "Track":
			if self.tracks:
				lib.messenger.send(None, "visualize_tracks", [self.tracks[self.parameters["Track"]]])            
				lib.messenger.send(None, "update_helpers", 1)
		if parameter == "MinLength":
			lib.messenger.send(self, "update_Track")
		  
	def updateSelectedTracks(self, obj, evt, tracks):
		"""
		Created: 14.04.2007, KP
		Description: show the given tracks
		"""
		if self.tracks:
			showtracks = []
			for i in tracks:
				showtracks.append(self.tracks[i])
			lib.messenger.send(None, "visualize_tracks", showtracks)            
			lib.messenger.send(None, "update_helpers", 1)
	
	
	def getParameters(self):
		"""
		Created: 14.08.2006, KP
		Description: Return the list of parameters needed for configuring this GUI
		"""            
		return [["Tracking", ("MinLength", )],        
		["Tracking Results", (("ResultsFile", "Select track file that contains the results", "*.csv"), )],
		["Visualization", ("Track", )]]

		
	def getLongDesc(self, parameter):
		"""
		Created: 14.08.2006, KP
		Description: Return a long description of the parameter
		""" 
		return ""
		
		
	def getType(self, parameter):
		"""
		Created: 14.08.2006, KP
		Description: Return the type of the parameter
		"""    
		if parameter in ["MinLength"]:
			return GUIBuilder.SPINCTRL
		if parameter == "Track":
			return GUIBuilder.SLICE            
		return GUIBuilder.FILENAME
		
	def getRange(self, parameter):
		"""
		Created: 14.08.2006, KP
		Description: Return the range of given parameter
		"""
		print "Get range", parameter
		if parameter == "Track":
			if self.track:
				minlength = self.parameters["MinLength"]
				return 0, self.track.getNumberOfTracks(minlength)            
			else:
				return 0, 1
		if parameter == "MinLength":
			if self.numberOfPoints:
				return 0, self.numberOfPoints
			return 0, 1
				
	def getDefaultValue(self, parameter):
		"""
		Created: 14.08.2006, KP
		Description: Return the default value of a parameter
		"""
		if parameter == "Track":
			return 0    
		if parameter == "MinLength":
			return 3
		if parameter == "ResultsFile":
			return "track_results.csv"
		return "statistics.csv"
		
		
	def getGUI(self, parent, taskPanel):
		"""
		Created: 21.11.2006, KP
		Description: Return the GUI for this filter
		"""              
		gui = lib.ProcessingFilter.ProcessingFilter.getGUI(self, parent, taskPanel)
		
				
		if not self.trackGrid:
			self.trackGrid = TrackTableGrid(self.gui, self.dataUnit, self, canEnable = 1)
			sizer = wx.BoxSizer(wx.VERTICAL)
			
			sizer.Add(self.trackGrid, 1)
			box = wx.BoxSizer(wx.HORIZONTAL)
			
			self.readTracksBtn = wx.Button(self.gui, -1, "Read tracks")
			box.Add(self.readTracksBtn)
			
			self.readTracksBtn.Bind(wx.EVT_BUTTON, self.onReadTracks)
			
			sizer.Add(box)
			pos = (0, 0)
			item = gui.sizer.FindItemAtPosition(pos)
			if item.IsWindow():
				win = item.GetWindow()
			elif item.IsSizer():
				win = item.GetSizer()
			elif item.IsSpacer():
				win = item.GetSpacer()
			
			gui.sizer.Detach(win)            
			gui.sizer.Add(sizer, (0, 0), flag = wx.EXPAND | wx.ALL)
			gui.sizer.Add(win, (1, 0), flag = wx.EXPAND | wx.ALL)
			
		if self.prevFilter:
			filename = self.prevFilter.getParameter("ResultsFile")
			if filename and os.path.exists(filename):
				self.setParameter("ResultsFile", filename)
				self.onReadTracks(event = None)
		return gui
		
		
	def execute(self, inputs, update = 0, last = 0):
		"""
		Created: 14.08.2006, KP
		Description: Execute the filter with given inputs and return the output
		"""            
		if not lib.ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None
		
		image = self.getInputFromChannel(0)
		return image
	
	def onReadTracks(self, event):
		"""
		Created: 22.11.2006, KP
		Description: Read tracks from a file instead of calculating them
		"""
		filename = self.parameters["ResultsFile"]
		if not os.path.exists(filename):
			return
		self.track = lib.Track.TrackReader()
		self.track.readFromFile(filename)
		self.tracks = self.track.getTracks(self.parameters["MinLength"])
		n = len(self.tracks)
		lib.messenger.send(self, "update_Track")
		print "Read %d tracks" % (n)
		print self.tracks
		self.showTracks(self.tracks)
		
	def showTracks(self, tracks):
		"""
		Created: 26.11.2006, KP
		Description: show the given tracks in the track grid
		"""
		table = self.trackGrid.getTable()
		table.Clear()
		table.AppendRows(len(tracks))
		for i, track in enumerate(tracks):
			mintp, maxtp = track.getTimeRange()
			print "Track", i, "has time range", mintp, maxtp
			for tp in range(mintp, maxtp + 1):
				val, pos = track.getObjectAtTime(tp)
				print "    value at tp ", tp, "(pos ", pos, ") is ", val
				# Set the value at row i, column tp+1 (because there is the column for enabling
				# this track)
				table.SetValue(i, tp + 1, pos, override = 1)
		self.trackGrid.SetTable(table)
		self.trackGrid.ForceRefresh()

class AnalyzeTracksFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	Created: 1.7.2007, KP
	Description: A filter that calculates statistics from the tracks and allows them to be exported to csv
	"""
	name = "Analyze tracks"
	category = TRACKING

	def __init__(self):
		"""
		Created: 13.04.2006, KP
		Description: Initialization
		"""
		self.tracks = []
		self.track = None
		self.tracker = None
		self.trackListBox = None
		self.fileUpdated = 0
		lib.ProcessingFilter.ProcessingFilter.__init__(self, (1, 1))

		self.descs = {"ResultsFile": "Tracking results file:"}
		self.numberOfPoints = None
		self.particleFile = ""

	def setParameter(self, parameter, value):
		"""
		Created: 13.04.2006, KP
		Description: Set a value for the parameter
		"""
		lib.ProcessingFilter.ProcessingFilter.setParameter(self, parameter, value)

		if parameter == "ResultsFile" and os.path.exists(value) and self.trackListBox:
			self.fileUpdated = 1

	def getParameters(self):
		"""
		Created: 14.08.2006, KP
		Description: Return the list of parameters needed for configuring this GUI
		"""
		return [["Tracking Results", (("ResultsFile", "Select track file that contains the results", "*.csv"), )]]

	def getLongDesc(self, parameter):
		"""
		Created: 14.08.2006, KP
		Description: Return a long description of the parameter
		"""
		return ""

	def getType(self, parameter):
		"""
		Created: 14.08.2006, KP
		Description: Return the type of the parameter
		"""
		return GUIBuilder.FILENAME

	def getRange(self, parameter):
		"""
		Created: 14.08.2006, KP
		Description: Return the range of given parameter
		"""
		return 0, 0

	def getDefaultValue(self, parameter):
		"""
		Created: 14.08.2006, KP
		Description: Return the default value of a parameter
		"""

		if parameter == "ResultsFile":
			return "track_results.csv"

	def getGUI(self, parent, taskPanel):
		"""
		Created: 21.11.2006, KP
		Description: Return the GUI for this filter
		"""
		gui = lib.ProcessingFilter.ProcessingFilter.getGUI(self, parent, taskPanel)

		if not self.trackListBox:
			self.trackListBox = CSVListView.CSVListView(self.gui)
			sizer = wx.BoxSizer(wx.VERTICAL)

			sizer.Add(self.trackListBox, 1)
			box = wx.BoxSizer(wx.HORIZONTAL)

			self.readTracksBtn = wx.Button(self.gui, -1, "Read tracks")
			box.Add(self.readTracksBtn)

			self.readTracksBtn.Bind(wx.EVT_BUTTON, self.onReadTracks)

			sizer.Add(box)
			pos = (0, 0)
			item = gui.sizer.FindItemAtPosition(pos)
			if item.IsWindow():
				win = item.GetWindow()
			elif item.IsSizer():
				win = item.GetSizer()
			elif item.IsSpacer():
				win = item.GetSpacer()

			gui.sizer.Detach(win)
			gui.sizer.Add(sizer, (0, 0), flag = wx.EXPAND | wx.ALL)
			gui.sizer.Add(win, (1, 0), flag = wx.EXPAND | wx.ALL)

		if self.prevFilter:
			filename = self.prevFilter.getParameter("ResultsFile")
			if filename and os.path.exists(filename):
				self.setParameter("ResultsFile", filename)
				self.onReadTracks(event = None)
		return gui

	def execute(self, inputs, update = 0, last = 0):
		"""
		Created: 14.08.2006, KP
		Description: Execute the filter with given inputs and return the output
		"""
		if not lib.ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None

		image = self.getInputFromChannel(0)
		return image

	def onReadTracks(self, event):
		"""
		Created: 22.11.2006, KP
		Description: Read tracks from a file instead of calculating them
		"""
		filename = self.parameters["ResultsFile"]
		if not os.path.exists(filename):
			return
		self.track = lib.Track.TrackReader()
		self.track.readFromFile(filename)
		self.tracks = self.track.getTracks(0)
		self.showTracks(self.tracks)

	def showTracks(self, tracks):
		"""
		Created: 26.11.2006, KP
		Description: show the given tracks in the track grid
		"""
#		track length
#		Directional persistance = path length / distance to starting point
#		speed
#		angle (avg of changes)

		rows = [["Length", "Avg. speed", "Directional persistence", "Avg. angle"]]
		globalmin = 9999999999
		globalmax = 0
		for i, track in enumerate(tracks):
			length = track.getNumberOfTimepoints()
			speed = track.getSpeed()
			dp = track.getDirectionalPersistence()
			avgang = track.getAverageAngle()
			row = [length, speed, dp, avgang]
			mintp, maxtp = track.getTimeRange()
			if mintp < globalmin:
				globalmin = mintp
			if maxtp > globalmax:
				globalmax = maxtp
			for tp in range(0, maxtp + 1):
				if tp < mintp:
					row.append("")
					continue
				val, pos = track.getObjectAtTime(tp)
				print "    value at tp ", tp, "(pos ", pos, ") is ", val
				# Set the value at row i, column tp+1 (because there is the column for enabling
				# this track)
				row.append(pos)
			rows.append(row)

		for i in range(0, globalmax):
			rows[0].append("T%d" % i)

		self.trackListBox.setContents(rows)
