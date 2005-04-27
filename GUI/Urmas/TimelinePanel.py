#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

"""
 Unit: TimelinePanel
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
           12.03.2005 KP - Split the classes to a module of their own
 
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

from Track import *
from Timeline import *
import PreviewFrame
import Animator

import os.path
import sys,types
import operator


class TimelineConfig(wx.Panel):
    """
    Class: TimelineConfig
    Created: 04.02.2005, KP
    Description: Contains configuration options for the timeline
    """    
    def __init__(self,parent,control):
        self.control=control
        print  "TimeLineConfig"
        wx.Panel.__init__(self,parent,-1)#,style=wx.SUNKEN_BORDER)
        #wx.wizard.WizardPageSimple.__init__(self,parent)
        self.control.setTimelineConfig(self)
        self.sizer=wx.GridBagSizer(5,5)
        self.parent=parent
        
        self.outputsizer=wx.GridBagSizer(5,5)
        box=wx.StaticBox(self,wx.HORIZONTAL,"Rendering")
        self.outputstaticbox=wx.StaticBoxSizer(box,wx.HORIZONTAL)
        self.outputstaticbox.Add(self.outputsizer)
        
        self.totalFramesLabel=wx.StaticText(self,-1,"Frames:")
        self.durationLabel=wx.StaticText(self,-1,"Duration:")
        self.fpsLabel=wx.StaticText(self,-1,"FPS: 0.5")

        self.totalFrames=wx.TextCtrl(self,-1,"30",size=(50,-1),style=wx.TE_PROCESS_ENTER)
        self.duration=masked.TextCtrl(self,-1,"00:00:60",autoformat="24HRTIMEHHMMSS",size=(50,-1),style=wx.TE_PROCESS_ENTER)

        self.totalFrames.Bind(wx.EVT_TEXT,self.updateFrameCount)
        self.duration.Bind(wx.EVT_TEXT,self.updateDuration)
        
        
        
        self.outputsizer.Add(self.durationLabel,(0,0))
        self.outputsizer.Add(self.duration,(0,1))        
        
        self.outputsizer.Add(self.totalFramesLabel,(1,0))
        self.outputsizer.Add(self.totalFrames,(1,1))
                
        self.outputsizer.Add(self.fpsLabel,(2,0))
                
        self.sizer.Add(self.outputstaticbox,(0,0),flag=wx.EXPAND|wx.ALL)
        #self.sizer.Add(self.animationstaticbox,(0,1),flag=wx.EXPAND|wx.ALL)

        self.useButton=wx.Button(self,-1,"Use settings")
        self.useButton.Bind(wx.EVT_BUTTON,self.useSettings)
        self.outputsizer.Add(self.useButton,(3,0))
        
        #self.sline=wx.StaticLine(self)
        #self.sizer.Add(self.sline,(4,0),flag=wx.EXPAND|wx.RIGHT|wx.LEFT)
        #self.sizer.Add(self.useButton,(5,0))
        
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)
        #self.updateFormat()
        self.useSettings()

    def setFrames(self,n):
        self.totalFrames.SetValue(str(n))
        self.useSettings()
        
    def setDuration(self,t):
        if type(t) != types.StringType:
            h=t/3600
            m=t/60
            s=t%60
            t="%.2d:%.2d:%.2d"%(h,m,s)
        self.duration.SetValue(t)
        self.useSettings()
    
    def useSettings(self,event=None):
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
            self.control.configureTimeline(secs,frameCount)
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
    Created: 04.02.2005, KP
    Description: Contains the timescale and the different "tracks"
    """    
    def __init__(self,parent,control,size=(800,300)):
        wx.Panel.__init__(self,parent,-1,style=wx.RAISED_BORDER,size=size)
        #wx.wizard.PyWizardPage.__init__(self,parent)
        self.parent=parent
        self.control=control
        self.sizer=wx.GridBagSizer()
        #self.Bind(wx.EVT_SIZE,self.onSize)
        w=size[0]
        print "size=",size
        self.timeline=Timeline(self,self.control,size=(w,300))
        self.sizer.Add(self.timeline,(0,0),span=(1,2),flag=wx.EXPAND|wx.ALL)
        
        sline=wx.StaticLine(self)
        self.sizer.Add(sline,(1,0),span=(1,2),flag=wx.EXPAND|wx.LEFT|wx.RIGHT)
        
        self.timelineConfig=TimelineConfig(self,control)
        
        #self.confBox=wx.StaticBox(self,-1,"Animation Configuration")
        #self.confBoxSizer=wx.StaticBoxSizer(self.confBox,wx.VERTICAL)
        #self.confBoxSizer.Add(self.timelineConfig)
        
        #self.sizer.Add(self.confBoxSizer,(2,0),flag=wx.EXPAND|wx.ALL)
        self.sizer.Add(self.timelineConfig,(2,0),flag=wx.EXPAND|wx.ALL)
        self.animBox=wx.StaticBox(self,-1,"Animation Control Pane")
        self.animBoxSizer=wx.StaticBoxSizer(self.animBox,wx.VERTICAL)
        self.animator = Animator.AnimatorPanel(self,self.control)
        self.control.setAnimator(self.animator)
        self.animBoxSizer.Add(self.animator)
        self.sizer.Add(self.animBoxSizer,(2,1),flag=wx.EXPAND|wx.ALL)
        
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)
        

    def onSize(self,evt):
        x,y=evt.GetSize()
        tx,ty=self.timeline.GetSize()
        self.timeline.SetSize((x,ty))
        self.timeline.Layout()
        self.Layout()
        
    def useTimeline(self,flag):
        if not flag:
            self.timeline.setDisabled(1)
        else:
            self.timeline.setDisabled(0)
        
    def setDataUnit(self,dataUnit):
        self.dataUnit=dataUnit
        self.timeline.setDataUnit(dataUnit)
