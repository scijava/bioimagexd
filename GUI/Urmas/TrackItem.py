# -*- coding: iso-8859-1 -*-

"""
 Unit: TrackItem
 Project: BioImageXD
 Created: 19.03.2005
 Creator: KP
 Description:

 URM/AS - The Unified Rendering Manager / Animator for Selli
 
 Urmas is a timeline based GUI for controlling the rendering of datasets. The GUI allows users
 to specify a path for the camera to follow (using Heikki Uuksulainen's MayaVi animator code)
 and also allows them to produce videos of the rendering using ffmpeg.
 
 Theitems placed on the track are implemented in this module

 Modified: 04.02.2005 KP - Original code created
           19.03.2005 KP - Placed code in file of its own
 
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
import sys
import math,random
import threading

import ImageOperations


        
class TrackItem(wx.Panel):
    """
    Class: TrackItem
    Created: 10.02.2005, KP
    Description: A class representing one item on a track
    """       

    def __init__(self,parent,text,size,**kws):
        wx.Panel.__init__(self,parent,-1)#,style=wx.SIMPLE_BORDER)
        self.text=text
        self.editable=1
        self.parent=parent
        self.minSize=5
        self.getting=0
        self.dc=0
        self.buffer=0
        self.lastdiff=0
        self.thumbnailbmp=0
        self.labelheight=15
        self.thumbtimepoint=-1
        self.itemnum=0
        if "itemnum" in kws:
            self.itemnum=kws["itemnum"]
        if kws.has_key("editable"):
            self.editable=kws["editable"]
        if kws.has_key("dataunit"):
            self.dataUnit=kws["dataunit"]
        if kws.has_key("thumbnail"):
            self.thumbtimepoint=kws["thumbnail"]
        self.color=(255,255,255)
        self.headercolor=(127,127,127)
        self.Bind(wx.EVT_PAINT,self.onPaint)
        self.width,self.height=size
        self.SetSize((self.width,self.height))
        self.setWidth(self.width)
                        
        if self.editable:
            self.Bind(wx.EVT_LEFT_DOWN,self.onDown)
            self.Bind(wx.EVT_MOTION,self.onDrag)
            self.Bind(wx.EVT_LEFT_UP,self.onUp)
                        
        self.beginX=0
        self.ok=0

    def setColor(self,col,headercolor):
        """
        Method: setColor(color, headercolor)
        Created: 10.02.2005, KP
        Description: Set the color and header color for this item
        """       
        self.color=col
        self.headercolor=headercolor
        self.drawItem()

        
    def onPaint(self,event):
        """
        Method: onPaint
        Created: 10.02.2005, KP
        Description: A method that will blit the buffer to screen
        """       
        dc=wx.BufferedPaintDC(self,self.buffer)

    def drawHeader(self):
        """
        Method: drawHeader()
        Created: 19.03.2005, KP
        Description: A method that draws the header of this item
        """       
        # Set the color to header color
        r,g,b=self.headercolor
        col=wx.Colour(r,g,b)
        
        # And draw the header block
        self.dc.SetBrush(wx.Brush(col))
        self.dc.SetPen(wx.Pen((0,0,0)))
        self.dc.SetBackground(wx.Brush(col))
        self.dc.DrawRectangle(0,0,self.width,self.labelheight)

        # Draw the text inside the header
        if self.text!="":
            self.dc.SetTextForeground((0,0,0))
            self.dc.SetFont(wx.Font(8,wx.SWISS,wx.NORMAL,wx.NORMAL))
            self.dc.DrawText(self.text,5,2)            
        
    
        
    def drawItem(self):
        """
        Method: drawItem()
        Created: 10.02.2005, KP
        Description: A method that draws this track item
        """       
        self.dc.Clear()
        self.dc.BeginDrawing()
        self.dc.SetPen(wx.Pen((0,0,0)))

        # draw the body
        r,g,b=self.color
        col=wx.Colour(r,g,b)
        self.dc.SetBrush(wx.Brush(wx.BLACK))
        self.dc.SetBackground(wx.Brush(wx.BLACK))
        self.dc.DrawRectangle(0,0,self.width,self.height)        

        self.drawHeader()
        
        if self.thumbtimepoint>=0:
            self.drawThumbnail()
        r,g,b=self.headercolor
        self.dc.SetPen(wx.Pen(wx.Colour(r,g,b),2))
        self.dc.DrawLine(self.width-1,0,self.width-1,self.height)

        
        self.dc.EndDrawing()

    def getThumbnail(self):
        """
        Method: getThumbnail()
        Created: 19.03.2005, KP
        Description: A method that creates a thumbnail for a timepoint
        """   
        self.volume=self.dataUnit.getTimePoint(self.thumbtimepoint)
        
    def drawThumbnail(self):
        """
        Method: drawThumbnail()
        Created: 10.02.2005, KP
        Description: A method that draws a thumbnail on an item. If no thumbnail exists,
                     this will create a thread to create one and return
        """   
        if not self.thumbnailbmp:
            if not self.getting:
                self.volume=0
                self.getting=1
                n=(1+self.thumbtimepoint)*750
                t=threading.Thread(None,self.getThumbnail)
                wx.FutureCall(n,lambda t=t:t.start())
                wx.FutureCall(n+100,self.drawItem)
                
                wx.FutureCall(n+300,self.parent.Refresh)
                wx.FutureCall(n+200,self.Refresh)
                wx.FutureCall(n+400,lambda p=self.parent:p.Layout())
                wx.FutureCall(n+500,wx.Yield)
                
                
            elif self.volume:
                vx,vy,vz=self.volume.GetDimensions()
                self.thumbnailbmp=ImageOperations.vtkImageDataToPreviewBitmap(self.volume,self.dataUnit.getColor(),0,self.height-self.labelheight)                            
            if not self.thumbnailbmp:
                return
        iw,ih=self.thumbnailbmp.GetSize()
        #print "image size=",iw,ih
        wdiff=(self.width-iw)/2
        if wdiff<0:wdiff=0
        self.dc.DrawBitmap(self.thumbnailbmp,wdiff,self.labelheight)
        
    def setMinimumWidth(self,w):
        """
        Method: setMinimumWidt(width)
        Created: 10.02.2005, KP
        Description: Set the minimum width for this item, below which it cannot
                     be resized
        """       
        self.minSize=w
        
    def setWidth(self,w):
        """
        Method: setWidth(width)
        Created: 10.02.2005, KP
        Description: Set the width of this item. Will allocate buffer for
                     drawing self.
        """       
        self.width=w
        self.SetSize((w,self.height))
        del self.buffer
        self.buffer=wx.EmptyBitmap(self.width,self.height)
        del self.dc
        self.dc = wx.BufferedDC(None,self.buffer)
        self.drawItem()
        
    def onDown(self,event):
        """
        Method: onDown(event)
        Created: 10.02.2005, KP
        Description: Event handler for when the mouse is pressed down over
                     this item. Will store the position in order to enable
                     dragging.
        """       
        x,y=event.GetPosition()
        print "onDow()",x,y
        self.ok=0
        w,h=self.GetSize()
        posx,posy=self.GetPosition()
        if abs(x-w)<8:
            self.ok=1
            self.beginX=x
        return
            
    def onUp(self,event):
        """
        Method: onUp(event)
        Created: 10.02.2005, KP
        Description: Event handler for when mouse is released over this item.
                     Will store the position in order to enable dragging.
        """       
    
        x,y=event.GetPosition()
        posx,posy=self.GetPosition()
        self.beginX=x 
        
    def onDrag(self,event):
        """
        Method: onDrag(event)
        Created: 10.02.2005, KP
        Description: Event handler for when the mouse is dragged on the item.
                     Will resize the item accordingly.
        """       
    
        if not event.Dragging():
            return
        if not self.ok:
            print "Click closer to the edge"
            return
        x,y=event.GetPosition()
        posx,posy=self.GetPosition()
                
        diff=x-self.beginX
        if self.width+diff<self.minSize:
            print "Not allowing < %d"%self.minSize
            return
        if diff>0 and not self.parent.itemCanResize(self.width,self.width+diff):
            print "Would go over the timescale"
            return
        self.lastdiff=diff
        self.setWidth(self.width+diff)
        self.parent.updateLayout()
        self.beginX=x

class SplinePoint(TrackItem):
    """
    Class: SplinePoint
    Created: 19.03.2005, KP
    Description: A class representing an item in a spline points track.
    """       
    def __init__(self,parent,text,size,**kws):
        """
        Method: __init__
        Created: 20.03.2005, KP
        Description: Initialize the method
        """       
        TrackItem.__init__(self,parent,text,size,**kws)
        self.Bind(wx.EVT_RIGHT_DOWN,self.onRightClick)
        self.ID_CAMERA=wx.NewId()
        
    def onRightClick(self,event):
        """
        Method: onRightClick
        Created: 20.03.2005, KP
        Description: Method that is called when the right mouse button is
                     pressed down on this item
        """      
        menu=wx.Menu()
        item = wx.MenuItem(menu,self.ID_CAMERA,"Add Camera Control")
        self.Bind(wx.EVT_MENU,self.addCameraControl,id=self.ID_CAMERA)
        menu.AppendItem(item)
        self.PopupMenu(menu,event.GetPosition())
        menu.Destroy()
        
    def addCameraControl(self,event):
        """
        Method: addCameraControl
        Created: 19.03.2005, KP
        Description: A method that adds a control handle to the visualization
                     for configuring the camera on this part of the spline
        """       
        print "Adding camera handle for ",self.itemnum
        self.parent.control.splineEditor.addCameraHandle(self.itemnum)
    
        
    def drawItem(self):
        """
        Method: drawItem()
        Created: 19.03.2005, KP
        Description: A method that draws the item.
        """       
        self.dc.Clear()
        self.dc.BeginDrawing()
        self.dc.SetPen(wx.Pen((0,0,0)))

        # draw the body
        r,g,b=self.color
        col=wx.Colour(r,g,b)
        self.dc.SetBrush(wx.Brush(col))
        #self.dc.SetBackground(wx.Brush(wx.BLACK))
        self.dc.DrawRectangle(0,0,self.width,self.height)        

        TrackItem.drawHeader(self)
        
        r,g,b=self.headercolor
        self.dc.SetPen(wx.Pen(wx.Colour(r,g,b),2))
        self.dc.DrawLine(self.width-1,0,self.width-1,self.height)

        
        self.dc.SetTextForeground((0,0,0))
        self.dc.SetFont(wx.Font(8,wx.SWISS,wx.NORMAL,wx.NORMAL))
        l=self.parent.getSplineLength(self.itemnum)
        s=self.parent.getSplineDuration(self.GetSize()[0])
        text=u"Length:\t%.2f\u03bcm\nDuration:\t%.2fs"%(l,s)
        self.dc.DrawText(text,5,self.labelheight+5)            

        
        self.dc.EndDrawing()
    
