#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

"""
 Unit: UrmasWindow
 Project: BioImageXD
 Created: 10.02.2005
 Creator: KP
 Description:

 URM/AS - The Unified Rendering Manager / Animator for Selli
 
 This is a timeline based GUI for controlling the rendering of datasets. The GUI allows users
 to specify a path for the camera to follow (using Heikki Uuksulainen's MayaVi animator code)
 and also allows them to produce videos of the rendering using ffmpeg.
 
 This is the wx.Dialog based window that contains the Urmas.
 
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
from Timeline import *
import TimepointSelection
import RenderingInterface

class UrmasControl:
    def __init__(self,window):
        self.window = window

    def setAnimator(self,animator):
        self.animator = animator

    def setTimelinePanel(self,timelinepanel):
        self.timelinePanel = timelinepanel

    def setDataUnit(self,dataunit):
        RenderingInterface.getRenderingInterface().setDataUnit(dataunit)
        self.dataUnit = dataunit
        self.timelinePanel.setDataUnit(dataunit)
        n=10*self.dataUnit.getLength()
        self.timelineConfig.setFrames(n)
        self.timelineConfig.setDuration(n/2)
        self.updateLayouts()
        self.animator.animator.initData()
        
    def updateLayouts(self):
        self.timeline.Layout()
        self.timelineConfig.Layout()
        self.timelinePanel.Layout()
        self.window.Layout()
        
    def setAnimationMode(self,mode):
        self.window.showAnimator(mode)
        self.updateLayouts()
        
    def setTimeline(self,timeline):
        self.timeline=timeline
        
    def setTimelineConfig(self,config):
        self.timelineConfig=config
        
    def configureTimeline(self,seconds,frames):
        print "Calling timeline.configureTimeline(",seconds,",",frames,")"
        self.timeline.configureTimeline(seconds,frames)
        self.updateLayouts()
        
        
class UrmasWindow(wx.Dialog):
    """
    Class: UrmasWindow
    Created: 10.02.2005, KP
    Description: A window for controlling the rendering/animation/movie generation.
                 The window has a notebook with different pages for rendering and
                 animation modes, and a page for configuring the movie generation.
    """
    def __init__(self,parent):
        print "Creating UrmasWindow()"
        wx.Dialog.__init__(self,parent,-1,"Rendering Manager / Animator",size=(800,400),
        style=wx.RESIZE_BORDER|wx.CAPTION|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX|wx.CLOSE_BOX|wx.SYSTEM_MENU)
        self.status=wx.ID_OK
        ico=reduce(os.path.join,["..","Icons","Selli.ico"])
        self.icon = wx.Icon(ico,wx.BITMAP_TYPE_ICO)
        self.SetIcon(self.icon)
        self.control = UrmasControl(self)
        #self.Bind(wx.EVT_SIZE,self.onSize)
        self.Bind(wx.EVT_CLOSE,self.closeWindowCallback)

        self.splitter=wx.SplitterWindow(self,-1)
        self.animator = Animator.AnimatorPanel(self.splitter,self.control)
        self.animator.Show(0)
        self.animatorOn=0
        self.control.setAnimator(self.animator)
        
        self.notebook=wx.Notebook(self.splitter,-1)
        self.splitter.Initialize(self.notebook)
        
        self.timepointSelection=TimepointSelection.TimepointSelectionPanel(self.notebook)

        self.notebook.AddPage(self.timepointSelection,"Select Time Points")

        self.timelinePanel=TimelinePanel(self.notebook,self.control)
        self.control.setTimelinePanel(self.timelinePanel)
        print "Adding timeline panel to notebook"
        self.notebook.AddPage(self.timelinePanel,"Rendering")
        print "done"
        #self.mainsizer.Add(self.notebook,(0,0),flag=wx.EXPAND|wx.ALL)
        #self.mainsizer.Add(self.splitter,(0,0),flag=wx.EXPAND|wx.ALL)
        #self.SetSizer(self.mainsizer)
        #self.SetAutoLayout(True)
        #self.mainsizer.Fit(self)        
    
    def onSize(self,evt):
        x,y=evt.GetSize()
        if self.animatorOn == False:
            self.notebook.SetSize((x,y))
        else:
            self.notebook.SetSize((x/2,y))
            self.animator.SetSize((x/2,y))
        
    
    def showAnimator(self,flag):
        if flag == True:
            self.animator.Show(1)
            self.animatorOn=1
            w,h=self.GetSize()
            wa,ha=self.animator.GetSize()
            self.SetSize((w,h+ha))
            self.splitter.SplitHorizontally(self.notebook,self.animator,h)
        else:
            self.animatorOn=0
            w,h=self.GetSize()
            wa,ha=self.animator.GetSize()
            self.SetSize((w,h-ha))
            self.splitter.Unsplit(self.animator)
            

    def setDataUnit(self,dataUnit):
        self.timepointSelection.setDataUnit(dataUnit)
        #self.timelinePanel.setDataUnit(dataUnit)
        self.control.setDataUnit(dataUnit)
        
    def closeWindowCallback(self,event):
        """
        Method: closeWindowCallback
        Created: 10.2.2005, KP
        Description: A callback that is used to close this window
        """
        self.EndModal(self.status)
