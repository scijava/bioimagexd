#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

"""
 Unit: Timeline
 Project: BioImageXD
 Created: 04.02.2005
 Creator: KP
 Description:

 URM/AS - The Unified Rendering Manager / Animator for Selli
 
 This is a timeline based GUI for controlling the rendering of datasets. The GUI allows users
 to specify a path for the camera to follow (using Heikki Uuksulainen's MayaVi animator code)
 and also allows them to produce videos of the rendering using ffmpeg.
 
 The timeline widget and the timescale are implemented in this module.

 Modified: 04.02.2005 KP - Created the module
 
 BioImageXD includes the following persons:
 
 DW - Dan White, dan@chalkie.org.uk
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 PK - Pasi Kankaanpää, ppkank@bytl.jyu.fi
 
 Copyright (c) 2005 BioImageXD Project.
"""
__author__ = "BioImageXD Project"
__version__ = "$Revision: 1.22 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import  wx.lib.scrolledpanel as scrolled
import wx
import wx.lib.masked as masked
import wx.wizard

from Track import *

import PreviewFrame
import Animator

import os.path
import sys,types
import operator
    
        
class Timeline(scrolled.ScrolledPanel):
    """
    Class: Timeline
    Created: 04.02.2005
    Creator: KP
    Description: Class representing the timeline with different "tracks"
    """    
    def __init__(self,parent,control,**kws):
        height=200
        width=640
        if kws.has_key("width"):
            width=kws["width"]
        scrolled.ScrolledPanel.__init__(self,parent,-1,size=(width,height))
        self.control = control
        control.setTimeline(self)
        self.sizer=wx.GridBagSizer(5,1)
        self.timeScale=TimeScale(self)
        # Set duration to 2 hours, let's stress test the thing
        self.timeScale.setDuration(5)
        self.timeScale.setDisabled(1)
        self.splinepoints=None
        self.sizer.Add(self.timeScale,(0,0))

        self.timepoints=Track("Time Points",self,number=1,timescale=self.timeScale)
        
        self.timeScale.setOffset(self.timepoints.getLabelWidth())
        
        self.sizer.Add(self.timepoints,(2,0),flag=wx.EXPAND|wx.ALL)

        self.timepoints.setColor((56,196,248))

        w,h=self.GetSize()
        w2,h=self.timeScale.GetSize()
        self.timeScale.SetSize((w,h))

        
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.SetupScrolling()
        self.sizer.Fit(self)
        self.timepoints.setItemAmount(1)

    def setDisabled(self,flag):
        self.timeScale.setDisabled(flag)
        
    def setAnimationMode(self,flag):
        if flag:
            self.splinepoints=Track("Spline Points",self,number=1,timescale=self.timeScale)
            self.splinepoints.setColor((248,196,56))
            self.setSplinePoints(7)
            self.sizer.Add(self.splinepoints,(3,0),flag=wx.EXPAND|wx.ALL)
        else:
            if self.splinepoints:
                self.sizer.Show(self.splinepoints,0)
                self.sizer.Detach(self.splinepoints)
                del self.splinepoints
                self.splinepoints=None
        self.Layout()
        self.sizer.Fit(self)

    def setSplinePoints(self,n):
        self.splinepoints.setItemAmount(n)
        
    def setDataUnit(self,dataUnit):
        self.dataUnit=dataUnit
        self.timepoints.setDataUnit(dataUnit)
        self.timepoints.showThumbnail(True)
        self.timepoints.setItemAmount(self.dataUnit.getLength())

        
    def configureTimeline(self,seconds,frames):
        print "Configuring frame amount to ",frames
        frameWidth=(seconds*self.timeScale.getPixelsPerSecond())/float(frames)
        print "frame width=",frameWidth
        self.timeScale.setDuration(seconds)
        for i in [self.timepoints,self.splinepoints]:
            if i:
                i.setDuration(seconds,frames)
        
class TimeScale(wx.Panel):
    """
    Class: TimeScale
    Created: 04.02.2005
    Creator: KP
    Description: Shows a time scale of specified length
    """
    def __init__(self,parent):
        wx.Panel.__init__(self,parent,-1,style=wx.RAISED_BORDER)
        self.Bind(wx.EVT_PAINT,self.onPaint)
        self.bgcolor=(255,255,255)
        self.fgcolor=(0,0,0)
        
        self.perSecond=24
        self.xOffset=15
        self.yOffset=6
        
    def setDisabled(self,flag):
        if not flag:
            self.Enable(True)
            self.fgcolor=(0,0,0)
            self.bgcolor=(255,255,255)
        else:
            self.Enable(False)
#            col=self.GetForegroundColour()
#            r,g,b=col.Red(),col.Green(),col.Blue()
#            self.fgcolor=(r,g,b)
            self.fgcolor=(127,127,127)
            col=self.GetBackgroundColour()
            r,g,b=col.Red(),col.Green(),col.Blue()
            self.bgcolor=(r,g,b)
        self.setDuration(self.seconds)
            
    def setOffset(self,x):
        self.xOffset=x
        self.paintScale()
        
    def setPixelsPerSecond(self,x):
        self.perSecond=x
        print "pixels per second=",x
        
    def getPixelsPerSecond(self):
        return self.perSecond
    
    def setDuration(self,seconds):
        self.seconds=seconds
        self.width=self.perSecond*seconds+2*self.xOffset
        self.height=20+self.yOffset
        self.SetSize((self.width+10,self.height))
        print "Set Size to %d,%d"%(self.width+10,self.height+10)
        self.buffer=wx.EmptyBitmap(self.width,self.height)
        dc = wx.BufferedDC(None,self.buffer)
        #col=self.GetBackgroundColour()
        r,g,b=self.bgcolor
        col=wx.Colour(r,g,b)
        dc.SetBackground(wx.Brush(col))
        dc.Clear()
        self.dc=dc
        self.paintScale()
    
    def paintScale(self):
        self.dc.Clear()
        self.dc.BeginDrawing()

        # draw the horizontal line
        #self.dc.DrawLine(self.xOffset,0,self.xOffset+self.seconds*self.perSecond,0)
        #self.dc.DrawLine(self.xOffset,self.height-1,self.xOffset+self.seconds*self.perSecond,self.height-1)

        #self.dc.SetTextForeground(color)        
        self.dc.SetFont(wx.Font(8,wx.SWISS,wx.NORMAL,wx.NORMAL))
        # and the tick marks and times
        self.dc.DrawLine(self.xOffset,0,self.width,0)
        r,g,b=self.fgcolor
        self.dc.SetPen(wx.Pen((r,g,b)))
        for i in range(0,self.seconds+1):
            x=i*self.perSecond+self.xOffset
            y=10+self.yOffset
            if not i%10:
                h=int(i/3600)
                m=int(i/60)
                s=int(i%60)
                timeString=""
                if 1 or h:
                    timeString="%.2d:"%h
                timeString+="%.2d:%.2d"%(m,s)
                tw,th=self.dc.GetTextExtent(timeString)
                self.dc.SetTextForeground((r,g,b))

                self.dc.DrawText(timeString,x-(tw/2),self.height/4)    
            if not i%30:
                d=4
            elif not i%10:
                d=4
            else:
                d=2
            if d:
                self.dc.DrawLine(x,-1,x,d)
                self.dc.DrawLine(x,self.height-d-4,x,self.height)
        self.dc.EndDrawing()
      
    
    def onPaint(self,event):
        dc=wx.BufferedPaintDC(self,self.buffer)     
        
   
