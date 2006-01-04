#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

"""
 Unit: RenderingConfigPanel
 Project: BioImageXD
 Created: 19.12.2005, KP
 Description:

 URM/AS - The Unified Rendering Manager / Animator for Selli
 
 This is a timeline based GUI for controlling the rendering of datasets. The GUI allows users
 to specify a path for the camera to follow (using Heikki Uuksulainen's MayaVi animator code)
 and also allows them to produce videos of the rendering using ffmpeg.
 
 The configuration panel for the rendering is implemented in this module.
 
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
import wx.lib.masked as masked
#from vtk.wx.wxVTKRenderWindowInteractor import wxVTKRenderWindowInteractor
from Visualizer import VisualizerWindow

from Track import *
from Timeline import *
import PreviewFrame
#import Animator
import SplineEditor

import os.path
import sys,types
import operator
import messenger
import CameraView

class RenderingConfigPanel(wx.Panel):
    """
    Class: TimelineConfig
    Created: 04.02.2005, KP
    Description: Contains configuration options for the timeline
    """    
    def __init__(self,parent,control):
        self.control=control
        wx.Panel.__init__(self,parent,-1)#,style=wx.SUNKEN_BORDER)
        #wx.wizard.WizardPageSimple.__init__(self,parent)
        self.control.setTimelineConfig(self)
        self.sizer=wx.GridBagSizer(5,5)
        
        self.parent=parent
        
        self.outputsizer=wx.GridBagSizer(5,5)
        box=wx.StaticBox(self,wx.HORIZONTAL,"Rendering parameters")
        self.outputstaticbox=wx.StaticBoxSizer(box,wx.HORIZONTAL)
        self.outputstaticbox.Add(self.outputsizer)
        
        self.totalFramesLabel=wx.StaticText(self,-1,"Frames:")
        self.durationLabel=wx.StaticText(self,-1,"Duration:")
        self.fpsLabel=wx.StaticText(self,-1,"12 / second")

        self.totalFrames=wx.TextCtrl(self,-1,"720",size=(50,-1),style=wx.TE_PROCESS_ENTER)
        self.spin = wx.SpinButton( self, -1,style=wx.SP_VERTICAL )
        self.duration=masked.TimeCtrl(self,-1,"00:01:00",fmt24hr=True,size=(50,-1),style=wx.TE_PROCESS_ENTER,spinButton=self.spin)
        
        self.totalFrames.Bind(wx.EVT_TEXT,self.updateFrameCount)
        self.duration.Bind(wx.EVT_TEXT,self.updateDuration)
        
        box=wx.BoxSizer(wx.HORIZONTAL)
        box.Add(self.duration)
        box.Add(self.spin)
        
        self.frameSizeLbl = wx.StaticText(self,-1,"Frame size:")
        self.frameSize = wx.Choice(self,-1,choices=["320 x 240","512 x 512","640 x 480","800 x 600"])
        self.frameSize.SetSelection(1)        
        
        self.outputsizer.Add(self.durationLabel,(0,0))
        #self.outputsizer.Add(self.duration,(0,1))   
        self.outputsizer.Add(box,(0,1))   
        
        self.outputsizer.Add(self.totalFramesLabel,(1,0))
        self.outputsizer.Add(self.totalFrames,(1,1))
                
        self.outputsizer.Add(self.fpsLabel,(2,1))
        self.outputsizer.Add(self.frameSizeLbl,(3,0))
        self.outputsizer.Add(self.frameSize,(3,1))
                
        self.sizer.Add(self.outputstaticbox,(0,0),flag=wx.EXPAND|wx.ALL)
        #self.sizer.Add(self.animationstaticbox,(0,1),flag=wx.EXPAND|wx.ALL)
        
        #self.sline=wx.StaticLine(self)
        #self.sizer.Add(self.sline,(4,0),flag=wx.EXPAND|wx.RIGHT|wx.LEFT)
        #self.sizer.Add(self.useButton,(5,0))
        
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)
        #self.updateFormat()
        self.useSettings()
        
    def getFrameAmount(self):
        """
        Method: getFrameAmount
        Created: 15.08.2005, KP
        Description: Return the number of frames selected
        """     
        try:
            n=int(self.totalFrames.GetValue())
            return n
        except:
            return 0

    def setFrames(self,n):
        """
        Method: setFrames
        Created: N/A, KP
        Description: Set the number of frames in the GUI
        """        
        self.totalFrames.SetValue(str(n))
        self.useSettings()
        
    def setDuration(self,t):
        """
        Method: setDuration
        Created: N/A, KP
        Description: Set the duration in the GUI
        """            
        if type(t) != types.StringType:
            h=t/3600
            m=t/60
            s=t%60
            t="%.2d:%.2d:%.2d"%(h,m,s)
        self.duration.SetValue(t)
        self.useSettings()
    
    def useSettings(self,event=None):
        """
        Method: useSettings
        Created: N/A, KP
        Description: Use the GUI settings
        """        
        duration = -1
        frameCount = -1
        try:
            duration=self.duration.GetValue()
            hh,mm,ss=map(int,duration.split(":"))
            print hh,mm,ss
            secs=hh*3600+mm*60+ss
            messenger.send(None,"set_duration",secs)
        except:
            pass
        try:
            frameCount=self.totalFrames.GetValue()
            frameCount=int(frameCount)
            messenger.send(None,"set_frames",frameCount)
        except:
            pass
        if duration != -1 and frameCount != -1:
            self.control.configureTimeline(secs,frameCount)
            
        try:
            size=self.frameSize.GetStringSelection()
            x,y=size.split("x")
            x=int(x)
            y=int(y)
            
            self.control.setFrameSize(x,y)
            messenger.send(None,"set_frame_size",(x,y))
        except:
            pass            
            
            
            #self.control.configureTimeline(secs,frameCount)

        #self.parent.sizer.Fit(self.parent)
        
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
        self.fpsLabel.SetLabel("%.2f / second"%newfps)
        
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
        self.fpsLabel.SetLabel("%.2f / second"%newfps)
