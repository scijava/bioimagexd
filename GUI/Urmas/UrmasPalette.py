#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

"""
 Unit: UrmasPalette
 Project: BioImageXD
 Created: 12.04.2005, KP
 Description:

 URM/AS - The Unified Rendering Manager / Animator for Selli
 
 This is a timeline based GUI for controlling the rendering of datasets. The GUI allows users
 to specify a path for the camera to follow (using Heikki Uuksulainen's MayaVi animator code)
 and also allows them to produce videos of the rendering using ffmpeg.
 
 This is a palette containing different items that can be dragged to the timeline.
 
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
__version__ = "$Revision: 1.22 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import wx
import Dialogs
import MenuManager
import os.path
import messenger
import scripting

from wx.lib.statbmp  import GenStaticBitmap as StaticBitmap

class UrmasDropTarget(wx.PyDropTarget):
    """
    Created: 12.04.2005, KP
    Description: A drop target for dragging from the palette to timeline
    """
    def __init__(self,tgt,datatype):
        """
        Method: __init__
        Created: 12.04.2005, KP
        Description: Initialization
        """
        wx.PyDropTarget.__init__(self)
        self.target=tgt
        self.dataformat = wx.CustomDataFormat(datatype)
        self.data = wx.CustomDataObject(self.dataformat)
        self.SetDataObject(self.data)

    def OnLeave(self):
        """
        Created: 13.04.2005, KP
        Description: Track mouse movement for reporting to target
        """
        
        self.target.OnDragLeave()
        
    def OnDrop(self,x,y):
        """
        Created: 12.04.2005, KP
        Description: Return true to accept drop
        """
        
        self.target.OnDragLeave()
        return 1
        
    def OnDragOver(self,x,y,d):
        """
        Created: 12.04.2005, KP
        Description: 
        """
        
        self.target.OnDragOver(x,y,d)
        return wx.DragCopy
        
    def OnData(self,x,y,d):
        """
        Created: 12.04.2005, KP
        Description: Get the dropped data
        """
        
        if self.GetData():
            data=self.data.GetData()
            #print "Got at %d,%d: %s"%(x,y,data)
            self.target.AcceptDrop(x,y,data)

        return d

class UrmasPalette(wx.Panel):
    """
    Created: 12.04.2005, KP
    Description: A palette from which items can be dragged to the timeline
    """
    def __init__(self,parent,control):
        """
        Created: 12.04.2005, KP
        Description: Initialization
        Parameters:
            control     UrmasControl object
        """
        self.parent=parent
        self.control=control
        self.dropsource = None
        self.icons={}
        self.panels={}
        self.sbmps={}
        #try:
        #    import psyco
        #    psyco.cannotcompile(self.dropItem)
        #except ImportError:
        #    pass
        wx.Panel.__init__(self,parent,style=wx.RAISED_BORDER,size=(750,32))
        self.sizer=wx.BoxSizer(wx.HORIZONTAL)
        
        self.iconpath=scripting.get_icon_dir()
        
        self.ID_NEWTIMEPOINTTRACK=wx.NewId()
        toolTip = wx.ToolTip("Drag this on to the timeline to add a track for controlling animated timepoints.")
        self.addDragDropItem(self.ID_NEWTIMEPOINTTRACK,
        "timepoint_track.JPG",self.onToolNewTimepointTrack,toolTip)        
        
        self.ID_NEWSPLINETRACK=wx.NewId()
        toolTip = wx.ToolTip("Drag this on to the timeline to add a track for controlling the camera movement using a spline curve.")
        self.addDragDropItem(self.ID_NEWSPLINETRACK,
        "spline_track.JPG",self.onToolNewSplineTrack,toolTip)        

        
        self.ID_NEWKEYFRAMETRACK=wx.NewId()
        toolTip = wx.ToolTip("Drag this on to the timeline to add a track for controlling the camera movement by creating keyframes.")
        self.addDragDropItem(self.ID_NEWKEYFRAMETRACK,
        "keyframe_track.JPG",self.onToolNewKeyframeTrack,toolTip)        
        
        p=wx.Panel(self,-1,size=(50,1))
        self.sizer.Add(p,flag=wx.RIGHT,border=2)
        
        self.ID_NEWTIMEPOINT=wx.NewId()
        toolTip = wx.ToolTip("Drag this on to a timepoint track to select visualized timepoints.")
        self.addDragDropItem(self.ID_NEWTIMEPOINT,
        "timepoint.jpg",self.onToolNewTimepoint,toolTip)        

        self.ID_NEWSPLINE=wx.NewId()                
        toolTip = wx.ToolTip("Drag this on to a camera path track to add a random camera path.")
        self.addDragDropItem(self.ID_NEWSPLINE,
        "spline_random.jpg",self.onToolNewSpline,toolTip)        
        
        self.ID_NEWCIRCULAR=wx.NewId()
        toolTip=wx.ToolTip("Drag this on to a camera path track to make camera rotate around X axis.")
        self.addDragDropItem(self.ID_NEWCIRCULAR,
        "spline_rotate_x.jpg",self.onToolNewCircular,toolTip)        
        
        self.ID_NEWPERPENDICULAR=wx.NewId()
        toolTip=wx.ToolTip("Drag this on to a camera path track to make camera rotate around Y axis.")
        self.addDragDropItem(self.ID_NEWPERPENDICULAR,
        "spline_rotate_y.jpg",self.onToolNewPerpendicular,toolTip)        
        
        self.ID_STOP_CAMERA=wx.NewId()        
        toolTip=wx.ToolTip("Drag this on to a camera path to add a pause in camera movement.")
        self.addDragDropItem(self.ID_STOP_CAMERA,
        "spline_stop.jpg",self.onToolNewStop,toolTip)        
        
        
        self.ID_ADD_KEYFRAME=wx.NewId()
        toolTip=wx.ToolTip("Drag this on to a keyframe track to add a keyframe at the current camera position.")        
        self.addDragDropItem(self.ID_ADD_KEYFRAME,
        "add_keyframe.jpg",self.onToolNewKeyframe,toolTip)     
        
        self.zoomLevels=[0.25,0.3333,0.5,0.6667,0.75,1.0, 1.25, 1.5, 2.0, 3.0, 4.0, 6.0]
        self.zoomCombo=wx.ComboBox(self,MenuManager.ID_ANIM_ZOOM_COMBO,
                          choices=["25%","33.33%","50%","66.67%","75%","100%","125%","150%","200%","300%","400%","600%"],size=(100,-1),style=wx.CB_DROPDOWN)
        self.zoomCombo.SetSelection(5)
        self.zoomCombo.SetHelpText("This controls the zoom level of animator tracks.")        
        self.zoomCombo.Bind(wx.EVT_COMBOBOX,self.zoomToComboSelection)
        
        self.sizer.Add(self.zoomCombo,flag=wx.RIGHT,border=2)
        
        
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)
        
    def zoomToComboSelection(self,event):
        """
        Created: 15.12.2005, KP
        Description: Set the zoom level of the tracks
        """        
        pos=self.zoomCombo.GetSelection()
        lvl=self.zoomLevels[pos]
        messenger.send(None,"set_animator_zoom",lvl)
        
        
    def addDragDropItem(self,newid,icon,dragCallback,toolTip):        
        """
        Created: 12.12.2005, KP
        Description: Add an item to the toolbar
        """
        bmp=wx.Image(os.path.join(self.iconpath,icon),wx.BITMAP_TYPE_JPEG).ConvertToBitmap()
        self.icons[newid]=bmp
        sbmp=StaticBitmap(self,newid,bmp,style=wx.RAISED_BORDER)
        self.sbmps[newid]=sbmp
        sbmp.Bind(wx.EVT_MOTION,dragCallback)        
        #p.Bind(wx.EVT_MOTION,dragCallback)        
        #self.sizer.Add(p,flag=wx.RIGHT,border=2)
        #p.Bind(               wx.EVT_LEFT_UP,self.onToolClick)
        self.sizer.Add(sbmp,flag=wx.RIGHT,border=2)
        
        sbmp.Bind(wx.EVT_LEFT_UP,self.onToolClick)
        
        sbmp.SetHelpText(toolTip.GetTip())
        sbmp.SetToolTip(toolTip)        
        #p.SetToolTip(toolTip)        
        
    def onToolClick(self,event):
        """
        Created: 07.08.2005, KP
        Description: A method that displays instructions if the user clicks on the palette
        """
        Dialogs.showwarning(None,"You need to drag and drop this item on to a track.","Drag item instead of clicking")
        
    def onToolNewPerpendicular(self,event):
        """
        Created: 20.04.2005, KP
        Description: A method for dragging a spline from palette
        """
        if event.Dragging():
            self.dropItem("Spline","Perpendicular")
        event.Skip()

    def onToolNewKeyframe(self,event):
        """
        Created: 20.04.2005, KP
        Description: A method for dragging a spline from palette
        """
        if event.Dragging():
            self.dropItem("Keyframe","Keyframe")
        event.Skip()
        
    def onToolNewKeyframeTrack(self,event):
        """
        Created: 2.09.2005, KP
        Description: A method for dragging a keyframe track from palette
        """
        
        if event.Dragging():
            self.dropItem("Track","Keyframe")
        event.Skip()

    def onToolNewSplineTrack(self,event):
        """
        Created: 2.09.2005, KP
        Description: A method for dragging a spline track from palette
        """
        
        if event.Dragging():
            self.dropItem("Track","Spline")
        event.Skip()
        
    def onToolNewTimepointTrack(self,event):
        """
        Created: 2.09.2005, KP
        Description: A method for dragging a timepoint track from palette
        """
        if event.Dragging():
            self.dropItem("Track","Timepoint")
        event.Skip()
        

        
    def onToolNewStop(self,event):
        """
        Created: 06.04.2005, KP
        Description: A method for dragging a spline from palette
        """
        if event.Dragging():
            self.dropItem("Spline","Stop")
        event.Skip()

    def onToolNewCircular(self,event):
        """
        Created: 06.04.2005, KP
        Description: A method for dragging a spline from palette
        """
        if event.Dragging():
            self.dropItem("Spline","Circular")
        event.Skip()
        
    def onToolNewSpline(self,event):
        """
        Created: 06.04.2005, KP
        Description: A method for dragging a spline from palette
        """
        
        if event.Dragging():
            self.dropItem("Spline")
        event.Skip()
        
    def onToolNewTimepoint(self,event):
        """
        Created: 06.04.2005, KP
        Description: A method for dragging a spline from palette
        """
        if event.Dragging():
            self.dropItem("Timepoint")
        event.Skip()        
            
        
    def dropItem(self,datatype,indata="Hello, World!"):
        """
        Created: 06.04.2005, KP
        Description: A method that creates a DnD of specified type
        """
        
        data = wx.CustomDataObject(wx.CustomDataFormat(datatype))
        data.SetData(indata)
        
        self.dropsource = wx.DropSource(self)
        self.dropsource.SetData(data)
        
        res = self.dropsource.DoDragDrop(wx.Drag_AllowMove)
        
        return res

