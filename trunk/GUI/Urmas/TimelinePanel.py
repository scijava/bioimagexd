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
import CameraView
import RenderingConfigPanel

class SplitPanel(wx.SplitterWindow):
    """
    Created: 25.01.2006, KP
    Description: A splitterwindow containing the timeline and it's configuration
    """    
    def __init__(self, parent, ID):
        wx.SplitterWindow.__init__(self, parent, ID,
                                   #style = wx.SP_LIVE_UPDATE
                                   )        
class TimelinePanel(wx.Panel):
    """
    Created: 04.02.2005, KP
    Description: Contains the timescale and the different "tracks"
    """    
    def __init__(self,parent,control,size=(750,300),p=None):
        wx.Panel.__init__(self,parent,-1,style=wx.RAISED_BORDER,size=size)
        self.parent=parent
        self.control=control
        self.sizer=wx.GridBagSizer()        
        w=size[0]

        self.confSizer=wx.GridBagSizer()
        
        self.timelineConfig=RenderingConfigPanel.RenderingConfigPanel(self,control)

        # The timelineConfig is not actually a panel, just an object that contains
        # the sizer we want to add to the layout. This is done to thin the hierarchy of
        # panels because MacOS X doesn't like many nested panels. That's why we just
        # add the sizer 
        self.confSizer.Add(self.timelineConfig.sizer,(0,0),flag=wx.EXPAND|wx.ALL)
        
        #sbox=wx.StaticBox(self,-1,"Animator configuration")
        #sboxsizer=wx.StaticBoxSizer(sbox,wx.HORIZONTAL)
        #sboxsizer.Add(self.confSizer)
        
        sboxsizer = self.confSizer
    
        self.useButton=wx.Button(self,-1,"Use settings")

        self.useButton.Bind(wx.EVT_BUTTON,self.useSettings)
           
        self.confSizer.Add(self.useButton,(1,0))
        
        self.sizer.Add(sboxsizer,(0,0),flag=wx.EXPAND|wx.ALL)
        #f=wx.Frame(self,-1)
        self.wxrenwin=VisualizerWindow.VisualizerWindow(self,size=(300,300))
        
        
        self.splineEditor=SplineEditor.SplineEditor(self,self.wxrenwin)
        self.control.setSplineEditor(self.splineEditor)        


        # Try to shallow the hierarchy
        #self.sbox=wx.StaticBox(self,-1,"Rendering preview")
        #self.sboxsizer=wx.StaticBoxSizer(self.sbox,wx.VERTICAL)                
        #self.sboxsizer.Add(self.wxrenwin)
        
        #self.sizer.Add(self.sboxsizer,(0,1))#,flag=wx.EXPAND|wx.ALL) 
        self.sizer.Add(self.wxrenwin,(0,1))#,flag=wx.EXPAND|wx.ALL) 
        
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)

        
        self.Refresh()
        
        n = self.timelineConfig.getFrameAmount()
        
        messenger.send(None,"set_frames",n)
        messenger.connect(None,"set_frame_size",self.onSetFrameSize)
        messenger.connect(None,"set_keyframe_mode",self.onSetKeyframeMode)

    def onSetFrameSize(self,obj,evt,size,onlyAspect):
        """
        Created: 19.12.2005, KP
        Description: Event to change the size of the rendering preview
                     based on the size of the actual rendered frames
        """
        x,y=size
        xtoy=float(x)/y
        if onlyAspect:
            y=300
            x=xtoy*y
        
        
        self.wxrenwin.SetSize((x,y))
        self.wxrenwin.SetMinSize((x,y))
        print "Setting size of renderwindow to ",(x,y)
        
        self.wxrenwin.Update()
        #self.sboxsizer.SetMinSize((x+10,y+25))
        #self.wxrenwin.SetMinSize((x+10,y+25))
        #self.sbox.SetSize((x+10,y+25))
        
        self.wxrenwin.Render()
        
        
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
#        n=self.control.getDuration()
        n = self.timelineConfig.getFrameAmount()
        
        messenger.send(None,"set_frames",n)
        
        #Qmessenger.send(None,"set_time_range",1,n*10)
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
        
        
        
# safeguard
