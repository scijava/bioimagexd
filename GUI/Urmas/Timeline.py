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
 
 Selli 2 includes the following persons:
 
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 
 Copyright (c) 2005 BioImageXD Project.
"""
__author__ = "Selli 2 Project <http://sovellusprojektit.it.jyu.fi/selli/>"
__version__ = "$Revision: 1.22 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import  wx.lib.scrolledpanel as scrolled
import wx
import wx.lib.masked as masked

from Track import *
import Animator

import os.path
import sys
import operator

if __name__=='__main__':
    import sys
    sys.path.append(os.path.normpath(os.path.join(os.getcwd(),"..")))


    
class TimelineConfig(wx.Panel):
    """
    Class: TimelineConfig
    Created: 04.02.2005
    Creator: KP
    Description: Contains configuration options for the timeline
    """    
    def __init__(self,parent):
        print  "TimeLineConfig"
        wx.Panel.__init__(self,parent,-1)#,style=wx.SUNKEN_BORDER)
        self.sizer=wx.GridBagSizer(5,5)
        self.parent=parent
        
        self.outputsizer=wx.GridBagSizer(5,5)
        box=wx.StaticBox(self,wx.HORIZONTAL,"Rendering")
        self.outputstaticbox=wx.StaticBoxSizer(box,wx.HORIZONTAL)
        self.outputstaticbox.Add(self.outputsizer)

        self.animationsizer=wx.GridBagSizer(5,5)
        box=wx.StaticBox(self,wx.HORIZONTAL,"Animation")
        self.animationstaticbox=wx.StaticBoxSizer(box,wx.HORIZONTAL)
        self.animationstaticbox.Add(self.animationsizer)

        self.animateCheckbox=wx.CheckBox(self,-1,"Use animator")
        self.controlPointsLabel=wx.StaticText(self,-1,"Number of control points")
        self.controlPoints=wx.TextCtrl(self,-1,"5")
        self.controlPoints.Bind(wx.EVT_TEXT,self.updateControlPoints)
        self.animateCheckbox.Bind(wx.EVT_CHECKBOX,self.updateAnimation)
        
        self.animationsizer.Add(self.animateCheckbox,(0,0))
        self.animationsizer.Add(self.controlPointsLabel,(1,0))
        self.animationsizer.Add(self.controlPoints,(2,0))
        
        self.formatLabel=wx.StaticText(self,-1,"Result")
        self.formatMenu=wx.Choice(self,-1,choices=["Images","Video"])
        self.formatMenu.Bind(wx.EVT_CHOICE,self.updateFormat)
        
        self.totalFramesLabel=wx.StaticText(self,-1,"Frames:")
        self.durationLabel=wx.StaticText(self,-1,"Duration:")
        self.fpsLabel=wx.StaticText(self,-1,"FPS: 0.5")

        self.totalFrames=wx.TextCtrl(self,-1,"30",size=(50,-1),style=wx.TE_PROCESS_ENTER)
        self.duration=masked.TextCtrl(self,-1,"00:00:60",autoformat="24HRTIMEHHMMSS",size=(50,-1),style=wx.TE_PROCESS_ENTER)

        self.totalFrames.Bind(wx.EVT_TEXT_ENTER,self.updateFrameCount)
        self.duration.Bind(wx.EVT_TEXT,self.updateDuration)
        
        
        self.outputsizer.Add(self.formatLabel,(0,0))
        self.outputsizer.Add(self.formatMenu,(0,1))

        self.outputsizer.Add(self.durationLabel,(1,0))
        self.outputsizer.Add(self.duration,(1,1))        
        
        self.outputsizer.Add(self.totalFramesLabel,(2,0))
        self.outputsizer.Add(self.totalFrames,(2,1))
                
        self.outputsizer.Add(self.fpsLabel,(3,0))
                
        self.sizer.Add(self.outputstaticbox,(0,0))
        self.sizer.Add(self.animationstaticbox,(0,1))

#        self.useButton=wx.Button(self,-1,"Use settings")
#        self.useButton.Bind(wx.EVT_BUTTON,self.reportToParent)
        
#        self.sline=wx.StaticLine(self)
#        self.sizer.Add(self.sline,(4,0),flag=wx.EXPAND|wx.RIGHT|wx.LEFT)
#        self.sizer.Add(self.useButton,(5,0))
        
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)
        self.updateFormat()
        self.reportToParent()

    def updateControlPoints(self,event):
        pass
        
    def updateAnimation(self,event):
        if not self.animateCheckbox.GetValue():
            self.controlPoints.Enable(0)
            self.parent.timeline.setAnimationMode(0)
        else:
            self.controlPoints.Enable(1)        
            self.parent.useTimeline(1)
            self.parent.timeline.setAnimationMode(1)
        
    def updateFormat(self,event=None):
        format=self.formatMenu.GetString(self.formatMenu.GetSelection())
        if format!="Video":
            self.duration.Enable(0)
            self.totalFrames.Enable(0)
            self.parent.useTimeline(0)
        else:
            self.duration.Enable(1)
            self.totalFrames.Enable(1)
            self.parent.useTimeline(1)
            
    
    def reportToParent(self,event=None):
        print "Trying to report..."
        try:
            duration=self.duration.GetValue()
            print "Got duration=",duration
            hh,mm,ss=map(int,duration.split(":"))
            print hh,mm,ss
            secs=hh*3600+mm*60+ss
            print "Getting value.."
            frameCount=self.totalFrames.GetValue()
            print "frameCount=",frameCount
            frameCount=int(frameCount)
            print "Got frameCount=",frameCount
            print "Reporting to parent"
            self.parent.configureTimeline(secs,frameCount)
        except:
            pass
        self.parent.sizer.Fit(self.parent)
        
    def updateDuration(self,event):
        duration=self.duration.GetValue()
        try:
            hh,mm,ss=map(int,duration.split(":"))
            frameCount=int(self.totalFrames.GetValue())
        except:
            return
        secs=hh*3600.0+mm*60.0+ss
        if secs==0:
            return
        newfps=frameCount/secs
        self.fpsLabel.SetLabel("FPS: %.2f"%newfps)
        
    def updateFrameCount(self,event):
        duration=self.duration.GetValue()
        hh,mm,ss=map(int,duration.split(":"))
        try:
            frameCount=int(self.totalFrames.GetValue())
        except:
            return
        if frameCount==0:
            return
        secs=hh*3600.0+mm*60.0+ss
        newfps=frameCount/secs
        self.fpsLabel.SetLabel("FPS: %.2f"%newfps)
        
class TimelinePanel(wx.Panel):
    """
    Class: TimelinePanel
    Created: 04.02.2005
    Creator: KP
    Description: Contains the timescale and the different "tracks"
    """    
    def __init__(self,parent):
        wx.Panel.__init__(self,parent,-1,style=wx.RAISED_BORDER)
        self.sizer=wx.GridBagSizer()
        
        self.animator=Animator.AnimatorPanel(self)
        self.sizer.Add(self.animator,(0,0),flag=wx.EXPAND|wx.ALL)
        
        
        sline=wx.StaticLine(self)
        self.sizer.Add(sline,(1,0),flag=wx.EXPAND|wx.LEFT|wx.RIGHT)
        
        self.timeline=Timeline(self)
        self.sizer.Add(self.timeline,(2,0),flag=wx.EXPAND|wx.ALL)
        
        sline=wx.StaticLine(self)
        self.sizer.Add(sline,(3,0),flag=wx.EXPAND|wx.LEFT|wx.RIGHT)
        
        self.timelineConfig=TimelineConfig(self)
        self.sizer.Add(self.timelineConfig,(4,0),flag=wx.EXPAND|wx.ALL,border=10)
        
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)
        
    def useTimeline(self,flag):
        if not flag:
            self.timeline.setAnimationMode(0)
            self.timeline.setDisabled(1)
        else:
            self.timeline.setDisabled(0)

    def configureTimeline(self,seconds,frames):
        print "Calling timeline.configureTimeline(",seconds,",",frames,")"
        self.timeline.configureTimeline(seconds,frames)
        
    def setDataUnit(self,dataUnit):
        self.dataUnit=dataUnit
        self.timeline.setDataUnit(dataUnit)
        
class Timeline(scrolled.ScrolledPanel):
    """
    Class: Timeline
    Created: 04.02.2005
    Creator: KP
    Description: Class representing the timeline with different "tracks"
    """    
    def __init__(self,parent):
        scrolled.ScrolledPanel.__init__(self,parent,-1,size=(640,200))
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
        
   
if __name__=='__main__':
    class MyApp(wx.App):
        def OnInit(self):
            frame=wx.Frame(None,size=(640,480))
            self.panel=TimelinePanel(frame)
            #self.panel=TimeScale(frame)
            #self.panel.setDuration(60)
            self.SetTopWindow(frame)
            frame.Show(True)
            return True
    app=MyApp()
    app.MainLoop()
 
