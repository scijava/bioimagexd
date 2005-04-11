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
    Description: Class representing the timeline with different tracks
    """    
    def __init__(self,parent,control,**kws):
        """
        Method: __init__
        Created: 04.02.2005, KP
        Description: Initialize
        """
        height=250
        width=640
        self.n=1
        #if kws.has_key("width"):
        #    width=kws["width"]
        scrolled.ScrolledPanel.__init__(self,parent,-1,size=(width,height))
        self.control = control
        control.setTimeline(self)
        self.sizer=wx.GridBagSizer(5,1)
        self.timeScale=TimeScale(self)
        self.timeScale.setDuration(self.control.getDuration())
        self.timeScale.setDisabled(1)
        self.sizer.Add(self.timeScale,(0,0))
        self.Unbind(wx.EVT_CHILD_FOCUS)

   
        self.timepointTracks=[]
        self.splinepointTracks=[]
        self.timepointTrackAmnt=0
        self.splinepointTrackAmnt=0
        
        w,h=self.GetSize()
        w2,h=self.timeScale.GetSize()
        self.timeScale.SetSize((w,h))

        
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.SetupScrolling()
        self.sizer.Fit(self)

    def refresh(self):
        """
        Method: refresh()
        Created: 11.04.2005, KP
        Description: Method called by UrmasPersist to allow the object
                     to refresh before it's items are created
        """ 
        for n in range(self.timepointTrackAmnt-len(self.timepointTracks)):
            self.addTrack("TmpTrack%d"%n,n)
        for n in range(self.splinepointTrackAmnt-len(self.splinepointTracks)):
            self.addSplinepointTrack("TmpSpline%d"%n)
            
    def addTrack(self,label,n):
        """
        Method: addTrack(label,itemamount)
        Created: 06.04.2005, KP
        Description: Adds a track to the timeline
        """    
        tr=Track(label,
        self,number=self.n,timescale=self.timeScale,control=self.control,
        timepoint=1)
        self.timeScale.setOffset(tr.getLabelWidth())
        self.sizer.Add(tr,(self.n+1,0),flag=wx.EXPAND|wx.ALL)
        self.n=self.n+1
        tr.setColor((56,196,248))
        tr.setItemAmount(n)
        
        self.timepointTracks.append(tr)
        
        if self.dataUnit:
            print "Setting dataunit & Enabling thumbnail"
            tr.setDataUnit(self.dataUnit)
            tr.showThumbnail(True)
            
    def addSplinepointTrack(self,label):
        """
        Method: addSplinepointTrack(label)
        Created: 11.04.2005, KP
        Description:
        """
        tr=Track(label,
            self,number=1,height=50,timescale=self.timeScale,item=SplinePoint,
            control=self.control)
        self.control.setSplineInteractionCallback(tr.updateLabels)
        tr.setColor((248,196,56))
        #self.setSplinePoints(7)
        self.sizer.Add(tr,(self.n+1,0),flag=wx.EXPAND|wx.ALL)
        self.n=self.n+1
        self.splinepointTracks.append(tr)            
            
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
            if not len(self.splinepointTracks):
                self.addSplinepointTrack("Spline Points")
        else:
            if len(self.splinepointTracks):
                for track in self.splinepointTracks:
                    self.removeTrack(track)
                    self.control.setSplineInteractionCallback(None)
                    self.splinepointTracks.remove(track)
        self.Layout()
        self.sizer.Fit(self)#self.SetScrollbars(20,0,tx/20,0)
    
    def clearTracks(self):
        """
        Method: clearTracks()
        Created: 06.04.2005, KP
        Description: Remove all tracks
        """    
        self.control.setSplineInteractionCallback(None)
        for track in self.timepointTracks:
            self.removeTrack(track)
        for track in self.splinepointTracks:
            self.removeTrack(track)
        self.splinepointTracks=[]
        self.timepointTracks=[]
        
    def removeTrack(self,track):
        """
        Method: removeTrack(track)
        Created: 06.04.2005, KP
        Description: Remove a track from the GUI
        """    
        self.sizer.Show(track,0)
        self.sizer.Detach(track)
        track.remove()

        
    def setSplinePoints(self,n):
        """
        Method: setSplinePoints(n)
        Created: 04.02.2005, KP
        Description: Set the amount of spline points
        """    
        for track in self.splinepointTracks:
            track.setItemAmount(n)
        
    def setDataUnit(self,dataUnit):
        """
        Method: setDataUnit(dataunit)
        Created: 04.02.2005, KP
        Description: Sets the dataunit on this timeline
        """
        self.dataUnit=dataUnit
        for track in self.timepointTracks:
            track.setDataUnit(dataUnit)
            track.showThumbnail(True)
        
    def reconfigureTimeline(self):
        """
        Method: reconfigureTimeline()
        Created: 19.03.2005, KP
        Description: Method to reconfigure items on timeline with
                     the same duration and frame amount
        """    
        self.configureTimeline(self.control.getDuration(),self.control.getFrames())
    
        
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
        for i in self.timepointTracks:
            if i:
                i.setDuration(seconds,frames)
        for i in self.splinepointTracks:
            if i:
                i.setDuration(seconds,frames)
        
    def __str__(self):
        """
        Method: __str__
        Created: 05.04.2005, KP
        Description: Return string representation of self
        """        
        s="Timepoint tracks: {"
        s+=", ".join(map(str,self.timepointTracks))
        s+="}\n"
        s+="Splinepoint tracks: {"
        s+=", ".join(map(str,self.splinepointTracks))
        s+="}\n"
        return s
    
    def __getstate__(self):
        """
        Method: __getstate__
        Created: 11.04.2005, KP
        Description: Return the dict that is to be pickled to disk
        """      
        odict={}
        keys=[""]
        self.timepointTrackAmnt = len(self.timepointTracks)
        self.splinepointTrackAmnt = len(self.splinepointTracks)
        for key in ["timepointTracks","splinepointTracks","n","splinepointTrackAmnt","timepointTrackAmnt"]:
            odict[key]=self.__dict__[key]
        return odict        
 
