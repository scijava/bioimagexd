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

import wx
import types
import os,os.path
import vtk
import Command
import re
try:
    import itk
except:
    pass
import messenger
import scripting as bxd

from lib import ProcessingFilter
import GUI.GUIBuilder as GUIBuilder
import ImageOperations

from lib import Particle

from lib import Track


import messenger

            
TRACKING="Tracking"

import  wx
import  wx.grid as  gridlib

#---------------------------------------------------------------------------

class TrackTable(gridlib.PyGridTableBase):
    """
    Created: 21.11.2006, KP
    Description: A class representing the table containing the tracks
    """
    def __init__(self, rows = 1, cols = 10):
        """
        Created: 21.11.2006, KP
        Description: Initialize the track table
        """
        gridlib.PyGridTableBase.__init__(self)
    
        self.enabledCol = 0
        self.odd=gridlib.GridCellAttr()
        #self.odd.SetBackgroundColour("sky blue")
        self.even=gridlib.GridCellAttr()
        self.even.SetBackgroundColour(wx.Colour(230,247,255))
        self.disabledAttr = gridlib.GridCellAttr()
        self.disabledAttr.SetBackgroundColour(wx.Colour(128,128,128))
        self.numberOfCols = cols
        self.numberOfRows = rows
        self.odd.SetReadOnly(1)
        self.even.SetReadOnly(1)
        self.gridValues={}
        
    def setEnabledColumn(self, col):
        """
        Created: 23.11.2006, KP
        Description: set the column that can be modified
        """
        self.enabledCol = col
        
    def GetColLabelValue(self, col):
        """
        Created: 21.11.2006, KP
        Description: Return the labels of the columns
        """

        return "Tp#%d"%(col+1)

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

    def AppendRows(self, n = 1):
        """
        Created: 21.11.2006, KP
        Description: Add a row
        """
        self.numberOfRows+=n
        print "NUmber of rows=",self.numberOfRows
        
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
        if (row,col) in self.gridValues:
            return "(%d,%d,%d)"%self.gridValues[(row,col)]
        return ""
        
    def getPointsAtColumn(self, getcol):
        """
        Created: 22.11.2006, KP
        Description: return the points at given columns
        """
        ret=[]
        for row,col in self.gridValues.keys():
            if col==getcol:
                ret.append(self.gridValues[(row,col)])
        return ret

    def SetValue(self, row, col, value):
        """
        Created: 21.11.2006, KP
        Description: Set the value of a cell
        """                  
        if col != self.enabledCol:
            return
        print "Setting value at",row,col,"to",value
        self.gridValues[(row,col)]= value


class TrackTableGrid(gridlib.Grid):
    """
    Created: 21.11.2006, KP
    Description: A grid widget containing the track table
    """
    def __init__(self, parent, dataUnit, trackFilter):
        """
        Created: 21.11.2006, KP
        Description: Initialize the grid
        """
        gridlib.Grid.__init__(self, parent, -1, size=(-1,120))

        self.dataUnit = dataUnit
        self.trackFilter = trackFilter
        n = dataUnit.getLength()
        table = TrackTable(cols = n )

        # The second parameter means that the grid is to take ownership of the
        # table and will destroy it when done.  Otherwise you would need to keep
        # a reference to it and call it's Destroy method later.
        self.SetTable(table, False)
        self.table = table
        self.selectedCol = None
        self.selectedRow = None

        self.Bind(gridlib.EVT_GRID_CELL_RIGHT_CLICK, self.OnRightDown)  
        self.Bind(gridlib.EVT_GRID_CELL_LEFT_CLICK, self.OnLeftDown) 
        messenger.connect(None,"get_voxel_at",self.onUpdateCell)
        messenger.connect(None,"timepoint_changed",self.onSetTimepoint)
        
    def onSetTimepoint(self, obj, event, timepoint):
        """
        Created: 23.11.2006, KP
        Description: Update the column that can be edited based on the timepoint
        """
        self.table.setEnabledColumn(timepoint)
        self.ForceRefresh()
        
    def onUpdateCell(self,obj,event,x,y,z,scalar,rval,gval,bval,r,g,b,a,ctf):
        """
        Created: 21.11.2006, KP
        Description: Store a coordinate in the cell
        """
        #print self.selectedCol,self.selectedRow,x,y,z
        currWin = bxd.visualizer.getCurrentWindow()
        if currWin.isMipMode():
             
            image = self.trackFilter.getInput(1)
            xdim,ydim,zdim = image.GetDimensions()
            possibleObjects=[]
            added=[]
            for zval in range(0,zdim):
                
                val = int(image.GetScalarComponentAsDouble(x,y,zval,0))
                if val not in [0,1] and val not in added:
                    possibleObjects.append((val,zval))
                    added.append(val)
            
            menu=wx.Menu()  
            
            if len(possibleObjects)==1:
                z=possibleObjects[0][1]
                print "Only one object"
            else:
                print len(possibleObjects),"objects"
                for val,zval in possibleObjects:
                    menuid = wx.NewId()
                    newitem = wx.MenuItem(menu, menuid,"Object #%d at depth %d"%(val,zval))
                    col=[0,0,0]
                    ctf = self.dataUnit.getColorTransferFunction()
                    ctf.GetColor(val, col)
                    r,g,b=col
                    r*=255
                    g*=255
                    b*=255
                    newitem.SetBackgroundColour(wx.Colour(r,g,b))
                    print "Zval = ",zval,"val=",val
                    f=lambda evt, zval=zval,xval=x,yval=y,s=self:s.onSetCell(x=xval,y=yval,z=zval)
                    currWin.Bind(wx.EVT_MENU,f,id=menuid)
                    menu.AppendItem(newitem)
                    
                pos = currWin.xoffset+x*currWin.zoomFactor, currWin.yoffset + y*currWin.zoomFactor
                print "Showing at ",pos
                currWin.PopupMenu(menu, pos)
            
                return
        self.onSetCell(x,y,z)                
            
    def onSetCell(self, x,y,z):
        """
        Created: 23.11.2006, KP
        Description: Set the value of the grid at given points
        """
        print "onSetCell(%d,%d,%d)"%(x,y,z)
        if self.selectedRow != None and self.selectedCol != None:
            self.table.SetValue(self.selectedRow,self.selectedCol,(x,y,z))
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
        return self.selectedCol
        
    def getSeedPoints(self):
        """
        Created: 22.11.2006, KP
        Description: return the selected seed points
        """
        if self.selectedCol!=None:            
            return self.table.getPointsAtColumn(self.selectedCol)
        return []
        
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
        #print "Selected",event.GetRow(),event.GetCol()
        self.selectedRow = event.GetRow()
        self.selectedCol = event.GetCol()
        
class CreateTracksFilter(ProcessingFilter.ProcessingFilter):
    """
    Created: 13.04.2006, KP
    Description: A filter for shifting the values of dataset by constant and scaling by a constant
    """     
    name = "Create Tracks"
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
        
        ProcessingFilter.ProcessingFilter.__init__(self,(1,1))
        
        self.descs={
            "MaxVelocity":"Maximum change in distance)",
            "MaxSizeChange":"Maximum size change (% of size)",
            "MaxDirectionChange":"Direction (angle of the allowed sector in degrees)",
            "MaxIntensityChange":"Maximum change of average intensity (% of max. diff.)",
            "MinLength":"Minimum length of track (timepoints)",
            "MinSize":"Minimum size of tracked objects",
            "TrackFile":"Object statistics file:",
            "SizeWeight":"","DirectionWeight":"","IntensityWeight":"",
            "ResultsFile":"File to store the results:",
            "Track":"Track to visualize"}
    
        self.numberOfPoints = None
        
        self.particleFile = ""
    def setParameter(self,parameter,value):
        """
        Created: 13.04.2006, KP
        Description: Set a value for the parameter
        """    
        ProcessingFilter.ProcessingFilter.setParameter(self, parameter, value)
        if parameter == "TrackFile":
            self.particleFile = value
        elif parameter == "ResultsFile" and os.path.exists(value):
            pass
#            self.track = Track.Track(value)
#            self.tracks = self.track.getTracks(self.parameters["MinLength"])
#            print "Read %d tracks"%(len(self.tracks))
#            messenger.send(self,"update_Track")
            #if self.parameters.has_key("Track") and self.tracks:
            #    messenger.send(None,"visualize_tracks",[self.tracks[self.parameters["Track"]]])
            #    messenger.send(None,"update_helpers",1)
        elif parameter == "Track":
            if self.tracks:
                messenger.send(None,"visualize_tracks",[self.tracks[self.parameters["Track"]]])            
                messenger.send(None,"update_helpers",1)
        if parameter=="MinLength":
            messenger.send(self,"update_Track")
    
    def getParameters(self):
        """
        Created: 14.08.2006, KP
        Description: Return the list of parameters needed for configuring this GUI
        """            
        return [["Change between consecutive objects",("MaxVelocity","MaxSizeChange","MaxIntensityChange", "MaxDirectionChange")],
        ["Tracking",("MinLength","MinSize")],
        ["Load object info",(("TrackFile","Select file with object statistics to load","*.csv"),)],
        ["Tracking Results",(("ResultsFile","Select track file that contains the results","*.csv"),)],
        ["Visualization",("Track",)]]
        
    def getDesc(self,parameter):
        """
        Created: 14.08.2006, KP
        Description: Return the description of the parameter
        """    
        return self.descs[parameter]
        
    def getLongDesc(self,parameter):
        """
        Created: 14.08.2006, KP
        Description: Return a long description of the parameter
        """ 
        return ""
        
        
    def getType(self,parameter):
        """
        Created: 14.08.2006, KP
        Description: Return the type of the parameter
        """    
        if parameter == "UseSize":
            return types.BooleanType
        elif parameter in ["MaxVelocity","MaxSizeChange","MinLength","MinSize"]:
            return GUIBuilder.SPINCTRL
        elif parameter in ["SizeWeight","DirectionWeight","IntensityWeight","MaxDirectionChange","MaxIntensityChange","MaxSizeChange"]:
            return GUIBuilder.SPINCTRL
        if parameter=="Track":return GUIBuilder.SLICE            
        return GUIBuilder.FILENAME
        
    def getRange(self,parameter):
        """
        Created: 14.08.2006, KP
        Description: Return the range of given parameter
        """             
        if parameter in ["MaxVelocity","MinSize"]:
            return (0,999)
        if parameter=="MaxSizeChange":
            return (0,100)
        if parameter=="Track":
            if self.track:
                minlength = self.parameters["MinLength"]
                return 0,self.track.getNumberOfTracks(minlength)            
        if parameter=="MinLength":
            if self.numberOfPoints:
                return 0,self.numberOfPoints
            return 0,1
        if parameter=="MaxDirectionChange":
            return (0,360)
        return (0,100)
                
    def getDefaultValue(self,parameter):
        """
        Created: 14.08.2006, KP
        Description: Return the default value of a parameter
        """     
        if parameter=="UseSize":
            return 1
        if parameter=="MinSize":
            return 6
        if parameter=="MaxVelocity":
            return 30
        if parameter=="MaxSizeChange":
            return 30
        if parameter=="MinLength":
            return 3
        if parameter in ["IntensityWeight","SizeWeight","DirectionWeight"]:
            return 33
        if parameter == "MaxDirectionChange":
            return 45
        if parameter == "MaxIntensityChange":
            return 10
        if parameter == "MaxSizeChange":
            return 25
        if parameter=="Track":return 0            
        if parameter == "ResultsFile":
            return "track_results.csv"
        return "tracks.csv"
        
        
    def getGUI(self,parent,taskPanel):
        """
        Created: 21.11.2006, KP
        Description: Return the GUI for this filter
        """              
        gui = ProcessingFilter.ProcessingFilter.getGUI(self,parent,taskPanel)
        
                
        if not self.trackGrid:
            self.trackGrid = TrackTableGrid(self.gui, self.dataUnit, self)
                        
            sizer = wx.BoxSizer(wx.VERTICAL)
            
            sizer.Add(self.trackGrid,1)
            
            box = wx.BoxSizer(wx.HORIZONTAL)
            
            self.readBtn = wx.Button(self.gui, -1,"Read objects")
            self.readTracksBtn = wx.Button(self.gui, -1,"Read tracks")
            self.newTrackBtn = wx.Button(self.gui, -1,"New track")
            self.calcTrackBtn = wx.Button(self.gui, -1,"Calculate tracks")
            box.Add(self.readBtn)
            box.Add(self.readTracksBtn)
            box.Add(self.newTrackBtn)
            box.Add(self.calcTrackBtn)
            
            #self.newTrackBtn.Enable(0)
            self.calcTrackBtn.Enable(0)
            
            self.readTracksBtn.Bind(wx.EVT_BUTTON, self.onReadTracks)
            self.readBtn.Bind(wx.EVT_BUTTON, self.onReadObjects)
            self.newTrackBtn.Bind(wx.EVT_BUTTON,self.trackGrid.onNewTrack)
            self.calcTrackBtn.Bind(wx.EVT_BUTTON, self.onDoTracking)
            
            sizer.Add(box)
            pos=(0,0)
            item = gui.sizer.FindItemAtPosition(pos)
            if item.IsWindow():
                win = item.GetWindow()
            elif item.IsSizer():
                win = item.GetSizer()
            elif item.IsSpacer():
                win = item.GetSpacer()
            
            gui.sizer.Detach(win)            
            gui.sizer.Add(sizer,(0,0),flag=wx.EXPAND|wx.ALL)
            gui.sizer.Add(win,(1,0),flag=wx.EXPAND|wx.ALL)
            
        return gui
        
        
    def execute(self,inputs,update=0,last=0):
        """
        Created: 14.08.2006, KP
        Description: Execute the filter with given inputs and return the output
        """            
        if not ProcessingFilter.ProcessingFilter.execute(self,inputs):
            return None
        
        image = self.getInput(1)
        return image
    
    def onReadTracks(self, event):
        """
        Created: 22.11.2006, KP
        Description: Read tracks from a file instead of calculating them
        """
        filename = self.parameters["ResultsFile"]
        if not os.path.exists(filename):
            return
        self.track = Track.TrackReader()
        self.track.readFromFile(filename)
        self.tracks = self.track.getTracks(self.parameters["MinLength"])
        n = len(self.tracks)
        messenger.send(self,"update_Track")
        print "Read %d tracks"%(n)
        print self.tracks
    
    def onReadObjects(self, event):
        """
        Created: 22.11.2006, KP
        Description: Read the object statistics from the given file
        """
        if not self.particleFile:
            return
        if not self.tracker:
            self.tracker = Particle.ParticleTracker()
        self.tracker.setFilterObjectSize(self.parameters["MinSize"])

        self.tracker.readFromFile(self.particleFile)      
        self.calcTrackBtn.Enable(1)
        
    def getObjectFromCoord(self, pt):
        """
        Created: 22.11.2006, KP
        Description: return an intensity value at given x,y,z
        """
        x,y,z = pt
        print "Getting from ",x,y,z
        image = self.getInput(1)
        intensity = int(image.GetScalarComponentAsDouble(x,y,z,0))
        return intensity
        
    def onDoTracking(self, event):
        """
        Created: 22.11.2006, KP
        Description: Do the actual tracking
        """
        #print "Using ",image
        #self.vtkfilter.SetInput(image)

        self.tracker.setMinimumTrackLength(self.parameters["MinLength"])
        self.tracker.setDistanceChange(self.parameters["MaxVelocity"]/100.0)
        self.tracker.setSizeChange(self.parameters["MaxSizeChange"]/100.0)
        self.tracker.setIntensityChange(self.parameters["MaxIntensityChange"]/100.0)
        self.tracker.setAngleChange(self.parameters["MaxDirectionChange"])
        fromTp = self.trackGrid.getTimepoint()
        print "Tracking from timepoint",fromTp,"forward"
        
        pts = self.trackGrid.getSeedPoints()
        print "Seed points=",pts
        its = map(self.getObjectFromCoord, pts)
        print "Tracking objects with itensities=",its
        
        self.tracker.track(fromTimepoint = fromTp, seedParticles = its)
        self.tracker.writeTracks(self.parameters["ResultsFile"])
    
        self.onReadTracks(None)
        
