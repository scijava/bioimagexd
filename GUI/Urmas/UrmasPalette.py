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
import os.path

class UrmasDropTarget(wx.PyDropTarget):
    """
    Class: UrmasDropTarget
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
        Method: OnLeave
        Created: 13.04.2005, KP
        Description: Track mouse movement for reporting to target
        """
        #print "OnLeave"
        self.target.OnDragLeave()
        
    def OnDrop(self,x,y):
        """
        Method: OnDrop(x,y)
        Created: 12.04.2005, KP
        Description: Return true to accept drop
        """
        #print "Got drop at %d,%d"%(x,y)
        self.target.OnDragLeave()
        return True
        
    def OnDragOver(self,x,y,d):
        """
        Method: OnDragOver(x,y,d)
        Created: 12.04.2005, KP
        Description: 
        """
        #print "OnDragOver(%d,%d)"%(x,y)
        self.target.OnDragOver(x,y,d)
        return wx.DragCopy
        
    def OnData(self,x,y,d):
        """
        Method: OnData(x,y,d)
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
    Class: UrmasPalette
    Created: 12.04.2005, KP
    Description: A palette from which items can be dragged to the timeline
    """
    def __init__(self,parent,control):
        """
        Method: __init__
        Created: 12.04.2005, KP
        Description: Initialization
        Parameters:
            control     UrmasControl object
        """
        self.parent=parent
        self.control=control
        wx.Panel.__init__(self,parent,style=wx.RAISED_BORDER,size=(800,32))
        self.sizer=wx.BoxSizer(wx.HORIZONTAL)
        
        iconpath=reduce(os.path.join,["Icons"])
        p=wx.Panel(self,-1,size=(32,32))#,style=wx.RAISED_BORDER)
        self.ID_NEWTIMEPOINTTRACK=wx.NewId()
        bmp=wx.Image(os.path.join(iconpath,"timepoint_track.jpg"),wx.BITMAP_TYPE_JPEG).ConvertToBitmap()
        self.newtimepointtrack=wx.StaticBitmap(p,self.ID_NEWTIMEPOINTTRACK,bmp,style=wx.RAISED_BORDER)
        #self.newtimepointtrack.Bind(wx.EVT_MOTION,self.onToolNewTimepointTrack)        
        self.sizer.Add(p,flag=wx.RIGHT,border=2)
        p=wx.Panel(self,-1,size=(32,32))#,style=wx.RAISED_BORDER)
        self.ID_NEWSPLINETRACK=wx.NewId()
        bmp=wx.Image(os.path.join(iconpath,"spline_track.jpg"),wx.BITMAP_TYPE_JPEG).ConvertToBitmap()
        self.newsplinetrack=wx.StaticBitmap(p,self.ID_NEWSPLINETRACK,bmp,style=wx.RAISED_BORDER)
        #self.newsplinetrack.Bind(wx.EVT_MOTION,self.onToolNewSplineTrack)        
        self.sizer.Add(p,flag=wx.RIGHT,border=2)
        p=wx.Panel(self,-1,size=(32,32))#,style=wx.RAISED_BORDER)
        self.ID_NEWKEYFRAMETRACK=wx.NewId()
        bmp=wx.Image(os.path.join(iconpath,"keyframe_track.jpg"),wx.BITMAP_TYPE_JPEG).ConvertToBitmap()
        self.newkeyframetrack=wx.StaticBitmap(p,self.ID_NEWKEYFRAMETRACK,bmp,style=wx.RAISED_BORDER)
        #self.newkeyframetrack.Bind(wx.EVT_MOTION,self.onToolNewKeyframeTrack)        
        self.sizer.Add(p,flag=wx.RIGHT,border=5)        
        self.ID_NEWSPLINE=wx.NewId()
        p=wx.Panel(self,-1,size=(32,32))#,style=wx.RAISED_BORDER)
        self.ID_NEWTIMEPOINT=wx.NewId()
        bmp=wx.Image(os.path.join(iconpath,"timepoint.jpg"),wx.BITMAP_TYPE_JPEG).ConvertToBitmap()
        self.newtimepoint=wx.StaticBitmap(p,self.ID_NEWTIMEPOINT,bmp,style=wx.RAISED_BORDER)
        self.newtimepoint.Bind(wx.EVT_MOTION,self.onToolNewTimepoint)
        
        toolTip = wx.ToolTip("Drag this on to a timepoint track to select visualized timepoints.")
        self.newtimepoint.SetHelpText(toolTip.GetTip())
        self.newtimepoint.SetToolTip(toolTip)        
        
        p.Bind(wx.EVT_MOTION,self.onToolNewTimepoint)
        p.Bind(                wx.EVT_LEFT_UP,self.onToolClick)
        self.newtimepoint.Bind(wx.EVT_LEFT_UP,self.onToolClick)
        self.sizer.Add(p,flag=wx.RIGHT,border=2)

        p=wx.Panel(self,-1,size=(32,32))#,style=wx.RAISED_BORDER)
        bmp=wx.Image(os.path.join(iconpath,"spline_random.jpg"),wx.BITMAP_TYPE_JPEG).ConvertToBitmap()
        self.newspline=wx.StaticBitmap(p,self.ID_NEWSPLINE,bmp,style=wx.RAISED_BORDER)
        self.newspline.Bind(wx.EVT_MOTION,self.onToolNewSpline)
        p.Bind(wx.EVT_MOTION,self.onToolNewSpline)
        p.Bind(             wx.EVT_LEFT_UP,self.onToolClick)
        self.newspline.Bind(wx.EVT_LEFT_UP,self.onToolClick)
        self.sizer.Add(p,flag=wx.RIGHT,border=2)
        
        toolTip = wx.ToolTip("Drag this on to a camera path track to add a random camera path.")
        self.newspline.SetToolTip(toolTip)        
        self.newspline.SetHelpText(toolTip.GetTip())
        p.SetToolTip(toolTip)
        
        p=wx.Panel(self,-1,size=(32,32))#,style=wx.RAISED_BORDER)
        self.ID_NEWCIRCULAR=wx.NewId()
        bmp=wx.Image(os.path.join(iconpath,"spline_rotate_x.jpg"),wx.BITMAP_TYPE_JPEG).ConvertToBitmap()
        self.newcircular=wx.StaticBitmap(p,self.ID_NEWCIRCULAR,bmp,style=wx.RAISED_BORDER)
        self.newcircular.Bind(wx.EVT_MOTION,self.onToolNewCircular)
        p.Bind(wx.EVT_MOTION,self.onToolNewCircular)
        p.Bind(               wx.EVT_LEFT_UP,self.onToolClick)
        self.newcircular.Bind(wx.EVT_LEFT_UP,self.onToolClick)
        self.sizer.Add(p,flag=wx.RIGHT,border=2)

        toolTip=wx.ToolTip("Drag this on to a camera path track to make camera rotate around X axis.")
        self.newcircular.SetToolTip(toolTip)
        self.newcircular.SetHelpText(toolTip.GetTip())
        p.SetToolTip(toolTip)

        p=wx.Panel(self,-1,size=(32,32))#,style=wx.RAISED_BORDER)
        self.ID_NEWPERPENDICULAR=wx.NewId()
        bmp=wx.Image(os.path.join(iconpath,"spline_rotate_y.jpg"),wx.BITMAP_TYPE_JPEG).ConvertToBitmap()
        self.newperpendicular=wx.StaticBitmap(p,self.ID_NEWPERPENDICULAR,bmp,style=wx.RAISED_BORDER)
        self.newperpendicular.Bind(wx.EVT_MOTION,self.onToolNewPerpendicular)
        p.Bind(wx.EVT_MOTION,self.onToolNewPerpendicular)
        p.Bind(                    wx.EVT_LEFT_UP,self.onToolClick)
        self.newperpendicular.Bind(wx.EVT_LEFT_UP,self.onToolClick)
        self.sizer.Add(p,flag=wx.RIGHT,border=2)
        
        toolTip=wx.ToolTip("Drag this on to a camera path track to make camera rotate around Y axis.")
        self.newperpendicular.SetToolTip(toolTip)
        self.newperpendicular.SetHelpText(toolTip.GetTip())
        p.SetToolTip(toolTip)

        p=wx.Panel(self,-1,size=(32,32))#,style=wx.RAISED_BORDER)
        self.ID_STOP_CAMERA=wx.NewId()
        bmp=wx.Image(os.path.join(iconpath,"spline_stop.jpg"),wx.BITMAP_TYPE_JPEG).ConvertToBitmap()
        self.newstop=wx.StaticBitmap(p,self.ID_STOP_CAMERA,bmp,style=wx.RAISED_BORDER)
        self.newstop.Bind(wx.EVT_MOTION,self.onToolNewStop)
        p.Bind(           wx.EVT_LEFT_UP,self.onToolClick)
        self.newstop.Bind(wx.EVT_LEFT_UP,self.onToolClick)
        p.Bind(wx.EVT_MOTION,self.onToolNewStop)
        
        toolTip=wx.ToolTip("Drag this on to a camera path to add a pause in camera movement.")
        self.newstop.SetToolTip(toolTip)
        self.newstop.SetHelpText(toolTip.GetTip())
        p.SetToolTip(toolTip)
        
        self.sizer.Add(p,flag=wx.RIGHT,border=2)
        
        p=wx.Panel(self,-1,size=(32,32))#,style=wx.RAISED_BORDER)
        self.ID_ADD_KEYFRAME=wx.NewId()
        bmp=wx.Image(os.path.join(iconpath,"add_keyframe.jpg"),wx.BITMAP_TYPE_JPEG).ConvertToBitmap()
        self.newkeyframe=wx.StaticBitmap(p,self.ID_ADD_KEYFRAME,bmp,style=wx.RAISED_BORDER)
        self.newkeyframe.Bind(wx.EVT_MOTION,self.onToolNewKeyframe)
        p.Bind(           wx.EVT_LEFT_UP,self.onToolClick)
        self.newkeyframe.Bind(wx.EVT_LEFT_UP,self.onToolClick)
        p.Bind(wx.EVT_MOTION,self.onToolNewKeyframe)
        toolTip=wx.ToolTip("Drag this on to a keyframe track to add a keyframe at the current camera position.")
        self.newkeyframe.SetToolTip(toolTip)
        self.newkeyframe.SetHelpText(toolTip.GetTip())
        p.SetToolTip(toolTip)
        
        self.sizer.Add(p,flag=wx.RIGHT,border=2)
        
        
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)
        
    def onToolClick(self,event):
        """
        Method: onToolNewPerpendicular
        Created: 07.08.2005, KP
        Description: A method that displays instructions if the user clicks on the palette
        """
        Dialogs.showwarning(None,"You need to drag and drop this item on to a track.","Drag item instead of clicking")
        
    def onToolNewPerpendicular(self,event):
        """
        Method: onToolNewPerpendicular
        Created: 20.04.2005, KP
        Description: A method for dragging a spline from palette
        """
        if event.Dragging():
            self.dropItem("Spline","Perpendicular")
        event.Skip()

    def onToolNewKeyframe(self,event):
        """
        Method: onToolNewKeyframe
        Created: 20.04.2005, KP
        Description: A method for dragging a spline from palette
        """
        if event.Dragging():
            self.dropItem("Keyframe","Keyframe")
        event.Skip()
        
    def onToolNewStop(self,event):
        """
        Method: onToolNewStop
        Created: 06.04.2005, KP
        Description: A method for dragging a spline from palette
        """
        if event.Dragging():
            self.dropItem("Spline","Stop")
        event.Skip()

    def onToolNewCircular(self,event):
        """
        Method: onToolNewCircular
        Created: 06.04.2005, KP
        Description: A method for dragging a spline from palette
        """
        if event.Dragging():
            self.dropItem("Spline","Circular")
        event.Skip()
        
    def onToolNewSpline(self,event):
        """
        Method: onToolNewSpline
        Created: 06.04.2005, KP
        Description: A method for dragging a spline from palette
        """
        
        if event.Dragging():
            self.dropItem("Spline")
        event.Skip()
        
    def onToolNewTimepoint(self,event):
        """
        Method: onToolNewTimepoint
        Created: 06.04.2005, KP
        Description: A method for dragging a spline from palette
        """
        if event.Dragging():
            self.dropItem("Timepoint")
        event.Skip()        
            
        
    def dropItem(self,datatype,indata="Hello, World!"):
        """
        Method: dropItem
        Created: 06.04.2005, KP
        Description: A method that creates a DnD of specified type
        """
        print "Dropping data of type %s:%s"%(datatype,indata)
        data = wx.CustomDataObject(wx.CustomDataFormat(datatype))
        data.SetData(indata)
        dropsource = wx.DropSource(self)
        dropsource.SetData(data)
        result = dropsource.DoDragDrop(wx.Drag_AllowMove)
        print "Result=",result        
        return result
