#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

"""
 Unit: TimelinePanel
 Project: BioImageXD
 Created: 04.02.2005, KP
 Description:

 URM/AS - The Unified Rendering Manager / Animator for Selli
 
 This is a timeline based GUI for controlling the rendering of datasets. The GUI allows users
 to specify a path for the camera to follow (using Heikki Uuksulainen's MayaVi animator code)
 and also allows them to produce videos of the rendering using ffmpeg.
 
 The timeline widget and it's configuration is implemented in this module.
 
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
        self.storedCameraPosition=None
        self.parent=parent
        
        self.outputsizer=wx.GridBagSizer(5,5)
        box=wx.StaticBox(self,wx.HORIZONTAL,"Rendering parameters")
        self.outputstaticbox=wx.StaticBoxSizer(box,wx.HORIZONTAL)
        self.outputstaticbox.Add(self.outputsizer)
        
        self.totalFramesLabel=wx.StaticText(self,-1,"Frames:")
        self.durationLabel=wx.StaticText(self,-1,"Duration:")
        self.fpsLabel=wx.StaticText(self,-1,"FPS: 0.5")

        self.totalFrames=wx.TextCtrl(self,-1,"30",size=(50,-1),style=wx.TE_PROCESS_ENTER)
        self.spin = wx.SpinButton( self, -1,style=wx.SP_VERTICAL )
        self.duration=masked.TimeCtrl(self,-1,"00:01:00",fmt24hr=True,size=(50,-1),style=wx.TE_PROCESS_ENTER,spinButton=self.spin)

        self.totalFrames.Bind(wx.EVT_TEXT,self.updateFrameCount)
        self.duration.Bind(wx.EVT_TEXT,self.updateDuration)
        
        box=wx.BoxSizer(wx.HORIZONTAL)
        box.Add(self.duration)
        box.Add(self.spin)
        
        self.outputsizer.Add(self.durationLabel,(0,0))
        #self.outputsizer.Add(self.duration,(0,1))   
        self.outputsizer.Add(box,(0,1))   
        
        self.outputsizer.Add(self.totalFramesLabel,(1,0))
        self.outputsizer.Add(self.totalFrames,(1,1))
                
        self.outputsizer.Add(self.fpsLabel,(2,0))
                
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
        try:
            duration=self.duration.GetValue()
            hh,mm,ss=map(int,duration.split(":"))
            print hh,mm,ss
            secs=hh*3600+mm*60+ss
            frameCount=self.totalFrames.GetValue()
            frameCount=int(frameCount)
            messenger.send(None,"set_duration",secs)
            messenger.send(None,"set_frames",frameCount)
            #self.control.configureTimeline(secs,frameCount)
        except:
            pass
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
        
        self.parent=parent
        self.control=control
        self.sizer=wx.GridBagSizer()
        
        w=size[0]
        self.timeline=Timeline(self,self.control,size=(w,200))
        self.sizer.Add(self.timeline,(0,0),span=(1,2),flag=wx.EXPAND|wx.LEFT|wx.RIGHT)
        
        sline=wx.StaticLine(self)
        self.sizer.Add(sline,(1,0),span=(1,2),flag=wx.EXPAND|wx.LEFT|wx.RIGHT)
        

        self.confPanel=wx.Panel(self,-1)
        self.confSizer=wx.GridBagSizer()
        
        self.timelineConfig=TimelineConfig(self.confPanel,control)

        self.confSizer.Add(self.timelineConfig,(0,0),flag=wx.EXPAND|wx.ALL)
        self.confPanel.SetSizer(self.confSizer)
        self.confPanel.SetAutoLayout(1)

        sbox=wx.StaticBox(self,-1,"Animator configuration")
        sboxsizer=wx.StaticBoxSizer(sbox,wx.VERTICAL)
        sboxsizer.Add(self.confPanel)
        
        self.useButton=wx.Button(self.confPanel,-1,"Use settings")
        self.useButton.Bind(wx.EVT_BUTTON,self.useSettings)
           
        self.confSizer.Add(self.useButton,(1,0))
        
        #self.modeBox=wx.RadioBox(self.confPanel,-1,"Keyframe mode",
        #choices=["Modify Keyframe",
        #"Set Camera angle",
        #"Add Keyframe"],
        #majorDimension=2,
        #style=wx.RA_SPECIFY_ROWS    
        #)
        #self.confSizer.Add(self.modeBox,(0,1))
        self.sizer.Add(sboxsizer,(2,0),flag=wx.EXPAND|wx.ALL)        
        
        
        
        self.wxrenwin=VisualizerWindow.VisualizerWindow(self,size=(400,260))
        
        self.wxrenwin.Render()
#        self.wxrenwin.Initialize()
#        self.wxrenwin.Start()

        self.splineEditor=SplineEditor.SplineEditor(self,self.wxrenwin)
        self.control.setSplineEditor(self.splineEditor)        

        sbox=wx.StaticBox(self,-1,"Rendering preview")
        sboxsizer=wx.StaticBoxSizer(sbox,wx.VERTICAL)                
        sboxsizer.Add(self.wxrenwin)
        
        self.sizer.Add(sboxsizer,(2,1))#,flag=wx.EXPAND|wx.ALL) 
        
        
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)
#        self.wxrenwin.RightButtonPressEvent()
#        self.wxrenwin.SetEventInformationFlipY(0,0,0,0,chr(0),0,None)
#        self.wxrenwin.MouseMoveEvent()

#        self.wxrenwin.RightButtonReleaseEvent()

        self.wxrenwin.Render()
        self.wxrenwin.Refresh()
        self.Refresh()
        messenger.send(None,"set_time_range",1,600)
        messenger.connect(None,"set_keyframe_mode",self.onSetKeyframeMode)
        

        
    def onSetKeyframeMode(self,obj,evt,arg):
        """
        Method: onSetKeyframeMode
        Created: 18.08.2005, KP
        Description: Toggles the keyframe mode on / off
        """            
        pass
        #self.modeBox.Enable(arg)
        
    def useSettings(self,evt):
        """
        Method: useSettings
        Created: 16.08.2005, KP
        Description: Use the configured settings
        """    
        self.timelineConfig.useSettings(evt)
        n=self.control.getDuration()
        messenger.send(None,"set_time_range",1,n*10)
        #keyframeMode=self.modeBox.GetSelection()
        #self.control.setViewMode(keyframeMode)
        
        
        cam = self.splineEditor.getCamera()
#       if keyframeMode:
#           print "Storing position"
#            self.storedCameraPosition=cam.GetPosition()
#            self.parent.onShowFrame(None)
#        else:
#            if self.storedCameraPosition:
#                print "Restoring position"
#                cam.SetPosition(self.storedCameraPosition)
#        self.splineEditor.render()
        
    def useTimeline(self,flag):
        print "useTimeline called!"
        if not flag:
            self.timeline.setDisabled(1)
        else:
            self.timeline.setDisabled(0)
        
    def setDataUnit(self,dataUnit):
        print "setDataUnit called!"
        self.dataUnit=dataUnit
        self.timeline.setDataUnit(dataUnit)

    def __del__(self):
        del self.wxrenwin
        
        
