# -*- coding: iso-8859-1 -*-

"""
 Unit: Track
 Project: Selli 2
 Created: 05.02.2005
 Creator: KP
 Description:

 URM/AS - The Unified Rendering Manager / Animator for Selli
 
 Urmas is a timeline based GUI for controlling the rendering of datasets. The GUI allows users
 to specify a path for the camera to follow (using Heikki Uuksulainen's MayaVi animator code)
 and also allows them to produce videos of the rendering using ffmpeg.
 
 The widgets that implement the Tracks of the timeline are implemented in this module.

 Modified: 04.02.2005 KP - Created the module
 
 Selli 2 includes the following persons:
 
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 
 Copyright (c) 2005 Selli 2 Project.
 --------------------------------------------------------------
"""
__author__ = "Selli 2 Project <http://sovellusprojektit.it.jyu.fi/selli/>"
__version__ = "$Revision: 1.22 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

from wxPython.wx import *
import  wx.lib.scrolledpanel as scrolled
import wx

import os.path
import sys
import math

import ImageOperations

        
class TrackItem(wxPanel):
        
    def __init__(self,parent,text,size,**kws):
        wxPanel.__init__(self,parent,-1)#,style=wxSIMPLE_BORDER)
        self.text=text
        self.editable=1
        self.parent=parent
        self.minSize=5
        self.dc=0
        self.buffer=0
        self.lastdiff=0
        self.thumbnailbmp=0
        self.thumbtimepoint=-1
        if kws.has_key("editable"):
            self.editable=kws["editable"]
        if kws.has_key("dataunit"):
            self.dataUnit=kws["dataunit"]
        if kws.has_key("thumbnail"):
            self.thumbtimepoint=kws["thumbnail"]
            print "Thumbnail timepoint is ",self.thumbtimepoint
        self.color=(255,255,255)
        self.headercolor=(127,127,127)
        self.Bind(wx.EVT_PAINT,self.onPaint)
        self.width,self.height=size
        self.SetSize((self.width,self.height))
        self.setWidth(self.width)
                        
        if self.editable:
            self.Bind(EVT_LEFT_DOWN,self.onDown)
            self.Bind(EVT_MOTION,self.onDrag)
            self.Bind(EVT_LEFT_UP,self.onUp)
                              
        self.beginX=0
        self.ok=0

    def setColor(self,col,headercolor):
        #self.textPanel.SetBackgroundColour(wxColour(col[0],col[1],col[2]))
        self.color=col
        self.headercolor=headercolor
        self.drawItem()

        
    def onPaint(self,event):
        dc=wx.BufferedPaintDC(self,self.buffer)
        
    def drawItem(self):
        self.dc.Clear()
        self.dc.BeginDrawing()
        self.dc.SetPen(wxPen((0,0,0)))
        
        # Set the color to header color
        r,g,b=self.headercolor
        col=wxColour(r,g,b)
        
        # And draw the header block
        self.dc.SetBrush(wxBrush(col))
        self.dc.SetPen(wxPen((0,0,0)))
        self.dc.SetBackground(wxBrush(col))
        self.dc.DrawRectangle(0,0,self.width,15)

        # Draw the text inside the header
        if self.text!="":
            self.dc.SetTextForeground((0,0,0))
            self.dc.SetFont(wx.Font(8,wxSWISS,wxNORMAL,wxNORMAL))
            self.dc.DrawText(self.text,5,2)
            
        # draw the body
        r,g,b=self.color
        col=wxColour(r,g,b)
        self.dc.SetBrush(wxBrush(col))
        self.dc.SetBackground(wxBrush(col))
        self.dc.SetPen(wxPen((0,0,0)))
        self.dc.DrawRectangle(0,15,self.width,self.height)
        
        if self.thumbtimepoint>=0:
            self.drawThumbnail(0,15)
        
        self.dc.EndDrawing()

    def drawThumbnail(self,x,y):
        if not self.thumbnailbmp:
            volume=self.dataUnit.getTimePoint(self.thumbtimepoint)
            vx,vy,vz=volume.GetDimensions()
            self.thumbnailbmp=ImageOperations.vtkImageDataToBitmap(volume,vz/2,self.dataUnit.getColor(),0,self.height-y)
        self.dc.DrawBitmap(self.thumbnailbmp,x,y)
        
    def setMinimumWidth(self,w):
        self.minSize=w
        
    def setWidth(self,w):
        self.width=w
        self.SetSize((w,self.height))
        del self.buffer
#        print "New bitmap with size=",self.width,self.height
        self.buffer=wxEmptyBitmap(self.width,self.height)
        del self.dc
        self.dc = wxBufferedDC(None,self.buffer)
        #col=self.GetBackgroundColour()
#        col=wxColour(255,255,255)
#        self.dc.SetBackground(wxBrush(col))
        self.drawItem()
        
    def onDown(self,event):
        x,y=event.GetPosition()
        self.ok=0
        w,h=self.GetSize()
        posx,posy=self.GetPosition()
        if abs(x-w)<8:
            self.ok=1
            self.beginX=x
            
    def onUp(self,event):
        x,y=event.GetPosition()
        posx,posy=self.GetPosition()
        #snapdiff=self.parent.getSnapDifference(posx,self.width,self.lastdiff) 
        #self.setWidth(self.width+snapdiff)
        self.parent.updateLayout()
        self.beginX=x 
        
    def onDrag(self,event):
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

        
class Track(wxPanel):
    def __init__(self,name,parent,**kws):
        wxPanel.__init__(self,parent,-1,style=wxSIMPLE_BORDER)
        self.number=0
        self.duration=0
        self.frames=0
        self.editable=1
        if kws.has_key("editable"):
            self.editable=kws["editable"]
        self.timescale=kws["timescale"]
        if kws.has_key("number"):
            self.number=kws["number"]

        self.sizer=wxGridBagSizer()
        self.itemBox=wxBoxSizer(wxHORIZONTAL)
        self.color=None
        self.parent=parent

        self.namePanel=wxPanel(self,-1)
        self.namePanel.SetBackgroundColour(wxColour(127,127,127))
        self.nameLbl=wxStaticText(self.namePanel,-1,name,size=(100,80))
        self.namePanel.SetSize((200,80))
        self.sizer.Add(self.namePanel,(0,0))

        self.sizer.Add(self.itemBox,(0,1))
                
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)
        self.items=[]
        self.thumbnail=0
        
    def setDataUnit(self,dataUnit):
        self.dataUnit=dataUnit
    
    def showThumbnail(self,flag):
        print "Showing thumbnail: ",str(flag==1)
        self.thumbnail=flag
        
    def getLength(self):
        return len(self.items)
        
    def getSnapDifference(self,x,width,diff):
        w2=float(self.duration*(self.timescale.getPixelsPerSecond()))/self.frames
        snapdiff=((x+width+diff)%w2)
        if diff<0:
            snapdiff*=-1
        return diff+snapdiff
        
    def itemCanResize(self,fromWidth,toWidth):
        diff=toWidth-fromWidth
        w,h=self.itemBox.GetSize()
        w+=diff
        if w>self.duration*self.timescale.getPixelsPerSecond():
            return 0
        return 1
        
    def setItemAmount(self,n):
        print "Removing ",len(self.items)," items"
        self.sizer.Show(self.itemBox,0)
        self.sizer.Detach(self.itemBox)
        for i in self.items:
            self.itemBox.Show(i,0)
            self.itemBox.Detach(i)
            self.items.remove(i)
            i.Destroy()
        self.itemBox.Destroy()
        self.itemBox=wxBoxSizer(wxHORIZONTAL)
        self.sizer.Add(self.itemBox,(0,1))
        
        self.updateLayout()
        self.items=[]
        print "Adding ",n,"items"
        for i in range(n):
            lbl=""
            if self.number:
                lbl="%d"%i
            print "addItem(%s)"%lbl
            self.addItem(lbl)
        self.updateLayout()
        
    def setDuration(self,seconds,frames,**kws):
        n=len(self.items)
        
        w=float(seconds)/float(n)
        print "New size=",w
        self.duration=seconds
        self.frames=frames
        w*=self.timescale.getPixelsPerSecond()
        
        tot=0
        last=0
        for i in self.items:
            i.setWidth(w)
#            # Do not allow any track item to be of width less than one frame
#            i.setMinimumWidth(w)
            tot+=w
            last=i
        
        diff=seconds*self.timescale.getPixelsPerSecond()-tot
        if diff>1:
            print "diff=",diff
            last.setWidth(w+diff)

        self.updateLayout()
        
    def getLabelWidth(self):
        return self.namePanel.GetSize()[0]

    def setColor(self,col):
        self.color=col
        self.headercolor=(127,127,127)
        for item in self.items:
            item.setColor(col,self.headercolor)
            item.Layout()
            
    def updateLayout(self):
        
        self.Layout()
        self.sizer.Fit(self)
        self.parent.Layout()
        self.parent.sizer.Fit(self.parent)
        
        
    
    def addItem(self,item):
        h=self.namePanel.GetSize()[1]
        print "self.thumbnail=",self.thumbnail
        if self.thumbnail:
            item=TrackItem(self,item,(20,h),editable=self.editable,dataunit=self.dataUnit,thumbnail=int(item))
        else:
            item=TrackItem(self,item,(20,h),editable=self.editable)
        if self.color:
            item.setColor(self.color,self.headercolor)
        self.items.append(item)
        self.itemBox.Add(item)
        self.Layout()
        self.sizer.Fit(self)
