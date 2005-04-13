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

    def OnLeave(self):
        """
        Method: OnLeave
        Created: 13.04.2005, KP
        Description: Track mouse movement for reporting to target
        """
        self.target.OnDragLeave()
        
    def OnDrop(self,x,y):
        """
        Method: OnDrop(x,y)
        Created: 12.04.2005, KP
        Description: Return true to accept drop
        """
        print "Got drop at %d,%d"%(x,y)
        self.target.OnDragLeave()
        return True
        
    def OnDragOver(self,x,y,d):
        """
        Method: OnDragOver(x,y,d)
        Created: 12.04.2005, KP
        Description: 
        """
        #print "OnDragOver ",x,y,d
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
            print "Got at %d,%d: %s"%(x,y,data)
            self.target.AcceptDrop(x,y,type,data)
        
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
        wx.Panel.__init__(self,parent,style=wx.RAISED_BORDER)
        self.sizer=wx.BoxSizer(wx.HORIZONTAL)
        iconpath=reduce(os.path.join,["Icons"])
        self.ID_NEWSPLINE=wx.NewId()
        
        p=wx.Panel(self,-1,size=(64,64))#,style=wx.RAISED_BORDER)
        bmp=wx.Image(os.path.join(iconpath,"spline.gif"),wx.BITMAP_TYPE_GIF).ConvertToBitmap()
        self.newspline=wx.StaticBitmap(p,self.ID_NEWSPLINE,bmp,style=wx.RAISED_BORDER)
        self.newspline.Bind(wx.EVT_MOTION,self.onToolNewSpline)
        self.sizer.Add(p,flag=wx.RIGHT,border=10)

        p=wx.Panel(self,-1,size=(64,64))#,style=wx.RAISED_BORDER)
        self.ID_NEWTIMEPOINT=wx.NewId()
        bmp=wx.Image(os.path.join(iconpath,"timepoint.gif"),wx.BITMAP_TYPE_GIF).ConvertToBitmap()
        self.newtimepoint=wx.StaticBitmap(p,self.ID_NEWTIMEPOINT,bmp,style=wx.RAISED_BORDER)
        self.newtimepoint.Bind(wx.EVT_MOTION,self.onToolNewTimepoint)
        #self.newtimepoint.Bind(wx.EVT_BUTTON,self.onToolNewTimepoint)
        #self.newtimepoint.Bind(wx.EVT_BUTTON,self.onToolSelectTimepoints)
        self.sizer.Add(p,flag=wx.RIGHT,border=5)

        
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)
        
    def onToolNewSpline(self,event):
        """
        Method: onToolNewSpline
        Created: 06.04.2005, KP
        Description: A method for dragging a spline from palette
        """
        
        if event.Dragging():
            self.dropItem("Spline")

    def onToolNewTimepoint(self,event):
        """
        Method: onToolNewTimepoint
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
        print "Result=",result        
        return result
