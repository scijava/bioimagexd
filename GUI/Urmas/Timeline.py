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
from TimeScale import *

import PreviewFrame
import Animator

import os.path
import sys,types
import operator
    
        
class Timeline(scrolled.ScrolledPanel):
    """
    Class: Timeline
    Created: 04.02.2005, KP
    Description: Class representing the timeline with different "tracks"
    """    
    def __init__(self,parent,control,**kws):
        """
        Method: __init__
        Created: 04.02.2005, KP
        Description: Initialize
        """
        height=250
        width=640
        #if kws.has_key("width"):
        #    width=kws["width"]
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
        self.Unbind(wx.EVT_CHILD_FOCUS)

        self.timepoints=Track("Time Points",
        self,number=1,timescale=self.timeScale,control=self.control)
        
        self.timeScale.setOffset(self.timepoints.getLabelWidth())
        
        self.sizer.Add(self.timepoints,(2,0),flag=wx.EXPAND|wx.ALL)

        self.timepoints.setColor((56,196,248))

        w,h=self.GetSize()
        w2,h=self.timeScale.GetSize()
        self.timeScale.SetSize((w,h))

        
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.SetupScrolling()
        #self.SetVirtualSize((w,h))
        #self.SetScrollbars(20,0,500,0)
        self.sizer.Fit(self)
        self.timepoints.setItemAmount(1)

    def setDisabled(self,flag):
        """
        Method: setDisabled(mode)
        Created: 04.02.2005, KP
        Description: Disables / Enables this timeline
        """
        self.timeScale.setDisabled(flag)

    def setAnimationMode(self,flag):
        """
        Method: setAnimationMode(mode)
        Created: 04.02.2005, KP
        Description: Sets animation mode on or off. This affects the spline points
                     track.
        """
        if flag:
            self.splinepoints=Track("Spline Points",
                self,number=1,height=50,timescale=self.timeScale,item=SplinePoint,
                control=self.control)
            self.control.setSplineInteractionCallback(self.splinepoints.updateLabels)
            self.splinepoints.setColor((248,196,56))
            #self.setSplinePoints(7)
            self.sizer.Add(self.splinepoints,(3,0),flag=wx.EXPAND|wx.ALL)
        else:
            if self.splinepoints:
                self.sizer.Show(self.splinepoints,0)
                self.sizer.Detach(self.splinepoints)
                self.control.setSplineInteractionCallback(None)
                del self.splinepoints
                self.splinepoints=None
        self.Layout()
        self.sizer.Fit(self)#self.SetScrollbars(20,0,tx/20,0)

    def setSplinePoints(self,n):
        """
        Method: setSplinePoints(n)
        Created: 04.02.2005, KP
        Description: Set the amount of spline points
        """    
        self.splinepoints.setItemAmount(n)
        
    def setDataUnit(self,dataUnit):
        """
        Method: setDataUnit(dataunit)
        Created: 04.02.2005, KP
        Description: Sets the dataunit on this timeline
        """
        self.dataUnit=dataUnit
        self.timepoints.setDataUnit(dataUnit)
        self.timepoints.showThumbnail(True)
        self.timepoints.setItemAmount(self.dataUnit.getLength())

        
    def reconfigureTimeline(self):
        """
        Method: reconfigureTimeline()
        Created: 19.03.2005, KP
        Description: Method to reconfigure items on timeline with
                     the same duration and frame amount
        """    
        self.configureTimeline(self.seconds,self.frames)
        
    def getDuration(self):
        """
        Method: getDuration()
        Created: 20.03.2005, KP
        Description: Returns the duration of this timeline
        """
        return self.seconds
    
        
    def configureTimeline(self,seconds,frames):
        """
        Method: configureTimeline(seconds,frames)
        Created: 04.02.2005, KP
        Description: Method that sets the duration of the timeline to
                     given amount of seconds, and the frame amount to
                     given amount of frames
        """
    
        self.seconds = seconds
        self.frames = frames
        print "Configuring frame amount to ",frames
        frameWidth=(seconds*self.timeScale.getPixelsPerSecond())/float(frames)
        print "frame width=",frameWidth
        self.timeScale.setDuration(seconds)
        tx,ty=self.timeScale.GetSize()
        self.Layout()
        for i in [self.timepoints,self.splinepoints]:
            if i:
                i.setDuration(seconds,frames)
        
