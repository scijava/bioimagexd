#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

"""
 Unit: UrmasControl
 Project: BioImageXD
 Created: 22.02.2005
 Creator: KP
 Description:

 URM/AS - The Unified Rendering Manager / Animator for Selli
 
 This is a timeline based GUI for controlling the rendering of datasets. The GUI allows users
 to specify a path for the camera to follow (using Heikki Uuksulainen's MayaVi animator code)
 and also allows them to produce videos of the rendering using ffmpeg.
 
 This is the class controlling the whole Urmas experience
 
 Modified: 22.02.2005 KP - Created the module
           12.03.2005 KP - Created a module of it's own for the control
 
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
import wx.wizard
from Timeline import *
import TimepointSelection
import RenderingInterface

class UrmasControl:
    """
    Class: UrmasControl
    Created: 22.02.2005, KP
    Description: A class that controls Urmas
    """
    def __init__(self,window):
        self.window = window
        self.splineEditor = None
        
    def getDuration(self):
        """
        Method: getDuration()
        Created: 20.03.2005, KP
        Description: Return the duration of the timeline
        """    
        return self.timeline.getDuration()
        
    def getPixelsPerSecond(self):
        """
        Method: getPixelsPerSecond()
        Created: 20.03.2005, KP
        Description: Return how many pixels there are per second on the timescale
        """    
        return self.timeline.timeScale.getPixelsPerSecond()

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
        
    def setSplinePoints(self,n):
        self.timeline.setSplinePoints(n)
        self.splineEditor.init_spline(n+1)
        
    def setAnimationMode(self,mode):
        """
        Method: setAnimationMode()
        Created: 12.03.2005, KP
        Description: Method used to either show or hide the animator
        """        
        #self.window.showAnimator(mode)
        self.timeline.setAnimationMode(mode)
        if mode:
            self.timeline.setSplinePoints(self.timelineConfig.getSplinePoints())
            self.timeline.reconfigureTimeline()
        self.updateLayouts()
        
    def setTimeline(self,timeline):
        self.timeline=timeline
        
    def setTimelineConfig(self,config):
        self.timelineConfig=config
        
    def setSplineInteractionCallback(self,cb):
        """
        Method: setSplineInteractionCallback
        Created: 19.03.2005, KP
        Description: Method to set a callback that is called when interaction
                     with the spline editor ends
        """        
        self.splineEditor.setInteractionCallback(cb)
    
        
    def configureTimeline(self,seconds,frames):
        print "Calling timeline.configureTimeline(",seconds,",",frames,")"
        self.timeline.configureTimeline(seconds,frames)
        self.updateLayouts()

    def setSplineEditor(self,spe):
        """
        Method: setSplineEditor
        Created: 19.03.2005, KP
        Description: Method used to set the spline editor
        """        
        self.splineEditor = spe
    
        
    def getSplineLength(self,point):
        """
        Method: setAnimationMode()
        Created: 19.03.2005, KP
        Description: Method that returns the total length of the spline
        """        
        return self.splineEditor.getSplineLength(point,point+1)
