#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

"""
 Unit: UrmasPalette
 Project: BioImageXD
 Created: 12.04.2005
 Creator: KP
 Description:

 URM/AS - The Unified Rendering Manager / Animator for Selli
 
 This is a timeline based GUI for controlling the rendering of datasets. The GUI allows users
 to specify a path for the camera to follow (using Heikki Uuksulainen's MayaVi animator code)
 and also allows them to produce videos of the rendering using ffmpeg.
 
 This is a palette containing different items that can be dragged to the timeline.
 
 Modified: 10.02.2005 KP - Created the module
 
 BioImageXD includes the following persons:
 
 DW - Dan White, dan@chalkie.org.uk
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 PK - Pasi Kankaanpää, ppkank@bytl.jyu.fi
 
 Copyright (c) 2005 BioImageXD Project.
"""
__author__ = "BioImageXD Project"
__version__ = "$Revision: 1.22 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import wx
import os.path

class UrmasDropTarget(wx.PyDropTarget):
    """
    Class: UrmasDropTarget
    Created: 12.04.2005, KP
    Description: A drop target for dragging from the palette to timeline
    """
    def __init__(self,tgt,type):
        """
        Method: __init__
        Created: 12.04.2005, KP
        Description: Initialization
        """
        wx.PyDropTarget.__init__(self)
        self.target=tgt
        self.dataformat = wx.CustomDataFormat(type)
        self.data = wx.CustomDataObject(self.dataformat)
        self.SetDataObject(self.data)
        
    def OnDrop(self,x,y):
        """
        Method: OnDrop(x,y)
        Created: 12.04.2005, KP
        Description: Return true to accept drop
        """
        print "Got drop at %d,%d"%(x,y)
        return True
        
    def OnDragOver(self,x,y,d):
        """
        Method: OnDragOver(x,y,d)
        Created: 12.04.2005, KP
        Description: 
        """
        #print "OnDragOver ",x,y,d
        self.target.OnDragOver(x,y,d)
        return d
        
    def OnData(self,x,y,d):
        """
        Method: OnData(x,y,d)
        Created: 12.04.2005, KP
        Description: Get the dropped data
        """
        if self.GetData():
            data=self.data.GetData()
            print "Got at %d,%d: %s"%(x,y,data)
        return d
        
class UrmasPalette(wx.Panel):
    """
    Class: UrmasPalette
    Created: 12.04.2005, KP
    Description: A palette from which items can be dragged to the timeline
    """
    def __init__(self,parent):
        """
        Method: __init__
        Created: 12.04.2005, KP
        Description: Initialization
        """
        wx.Panel.__init__(self,parent,style=wx.RAISED_BORDER)
        self.sizer=wx.BoxSizer(wx.HORIZONTAL)
        iconpath=reduce(os.path.join,["Icons"])
        self.ID_NEWSPLINE=wx.NewId()
        bmp=wx.Image(os.path.join(iconpath,"spline.gif"),wx.BITMAP_TYPE_GIF).ConvertToBitmap()
        self.newspline=wx.StaticBitmap(self,self.ID_NEWSPLINE,bmp)
        self.newspline.Bind(wx.EVT_MOTION,self.dropSpline)
        self.sizer.Add(self.newspline)
        
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)
        
    def dropSpline(self,event):
        """
        Method: dropSpline
        Created: 06.04.2005, KP
        Description: A method for dragging a spline from palette
        """
        if event.Dragging():
            self.dropItem("Spline")

    def dropTimepoint(self,event):
        """
        Method: dropSpline
        Created: 06.04.2005, KP
        Description: A method for dragging a spline from palette
        """
        if event.Dragging():
            self.dropItem("Timepoint")
            
        
    def dropItem(self,type,indata="Hello, World!"):
        """
        Method: dropItem
        Created: 06.04.2005, KP
        Description: A method that creates a DnD of specified type
        """
        data = wx.CustomDataObject(wx.CustomDataFormat(type))
        data.SetData(indata)
        dropsource = wx.DropSource(self)
        dropsource.SetData(data)
        result = dropsource.DoDragDrop(wx.Drag_AllowMove)
        if result == wx.DragMove:
            print "move"
        print "Result=",result        
