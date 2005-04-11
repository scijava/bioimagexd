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
 
 This module contains the UrmasControl that is controlling the whole 
 Urmas experience as well as representations of the tracks and items of
 the timeline that can be written out or sent to the renderer that produces
 the final movie.
 
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
import TrackItem

#import pickle
import UrmasPersist


class UrmasControl:
    """
    Class: UrmasControl
    Created: 22.02.2005, KP
    Description: A class that controls Urmas
    """
    def __init__(self,window):
        self.window = window
        self.splineEditor = None
        self.splinePointAmount = 5
        self.duration = 60 # seconds
        self.frames = 120 # frames
        self.animationMode= 0
        
    def writeToDisk(self,filename):
        """
        Method: writeToDisk(filename)
        Created: 06.04.2005, KP
        Description: Writes the whole control datastructures to disk by way of
                     pickling
        """    
        #f=open(filename,"w")
        #pickle.dump(self,f)
        p=UrmasPersist.UrmasPersist(self)
        p.persist(filename)
        

    def readFromDisk(self,filename):
        """
        Method: readFromDisk(filename)
        Created: 06.04.2005, KP
        Description: Read the whole control datastructures from disk by way of
                     pickling
        """    
        self.clearGUI()
        print "\nAfter clearing myself: ",self,"\n"

        p=UrmasPersist.UrmasPersist(self)
        p.depersist(filename)
        
        # Assimilate the loaded object's dict
#        self.timeline.__dict__.update(ctrl.timeline.__dict__)
#        del ctrl.timeline
#        self.__dict__.update(ctrl.__dict__)
        print "\nUnpersisted ",self,"\n"
        #self.updateGUI()

    def clearGUI(self):
        """
        Method: clearGUI()
        Created: 06.04.2005, KP
        Description: Clear the GUI
        """    
        self.timeline.clearTracks()
        
    def updateGUI(self):
        """
        Method: updateGUI()
        Created: 06.04.2005, KP
        Description: Update the GUI to match the data structures
        """    
        #print "updateGUI frames=%d duration=%d"%(self.frames,self.duration)
        self.refresh()
        self.setSplinePoints(self.splinePointAmount)
        self.updateLayouts()
        
    def refresh(self):
        """
        Method: refresh()
        Created: 11.04.2005, KP
        Description: Update the GUI to match the data structures
        """    
        self.setAnimationMode(self.animationMode)
        self.timelineConfig.setFrames(self.frames)
        self.timelineConfig.setDuration(self.duration)
        self.configureTimeline(self.duration,self.frames)
        
    def getFrames(self):
        """
        Method: getFrames()
        Created: 04.04.2005, KP
        Description: Return the number of frames
        """    
        return self.frames
        
    def getDuration(self):
        """
        Method: getDuration()
        Created: 20.03.2005, KP
        Description: Return the duration of the timeline
        """    
        return self.duration
        
    def getPixelsPerSecond(self):
        """
        Method: getPixelsPerSecond()
        Created: 20.03.2005, KP
        Description: Return how many pixels there are per second on the timescale
        """    
        return self.timeline.timeScale.getPixelsPerSecond()

    def setAnimator(self,animator):
        """
        Method: setAnimator(animator)
        Created: 20.03.2005, KP
        Description: Sets the animator controlled by this
        """    
        self.animator = animator

    def setTimelinePanel(self,timelinepanel):
        """
        Method: setTimelinePanel(tpl)
        Created: 20.03.2005, KP
        Description: Sets the timeline panel controlled by this
        """    
        self.timelinePanel = timelinepanel

    def setDataUnit(self,dataunit):
        """
        Method: setDataUnit(dataunit)
        Created: 20.03.2005, KP
        Description: Sets the dataunit used as a source of data
        """    
        RenderingInterface.getRenderingInterface().setDataUnit(dataunit)
        self.dataUnit = dataunit
        self.timelinePanel.setDataUnit(dataunit)
        #n=10*self.dataUnit.getLength()
        #self.timelineConfig.setFrames(n)
        #self.timelineConfig.setDuration(n/2)
        
        self.timeline.addTrack("Timepoint",self.dataUnit.getLength())
        self.updateGUI()
        self.updateLayouts()
        self.animator.animator.initData()
        
        
    def updateLayouts(self):
        """
        Method: updateLayouts()
        Created: 20.03.2005, KP
        Description: Update various parts of the window as the layout changes
        """    
        self.timeline.Layout()
        self.timelineConfig.Layout()
        self.timelinePanel.Layout()
        self.window.Layout()

        
    def setSplinePoints(self,n):
        """
        Method: setSplinePoints(points)
        Created: 20.03.2005, KP
        Description: Sets the number of spline points in the camera path
        Parameters:
            points      If points is an integer, it is used as a number of handles
                        for a random spline. Otherwise it is used as a list of
                        points for the spline
        """    
        if type(n)==type(0):
            self.splinePointsAmount=n
            self.timeline.setSplinePoints(n)
            self.splineEditor.initSpline(n+1)
        else:
            self.splinePointsAmount=len(n)
            self.timeline.setSplinePoints(len(n))
            self.splineEditor.setSplinePoints(n)
        
    def setAnimationMode(self,mode):
        """
        Method: setAnimationMode()
        Created: 12.03.2005, KP
        Description: Method used to either show or hide the animator
        """        
        self.animationMode = mode
        #self.window.showAnimator(mode)
        self.timeline.setAnimationMode(mode)
        if mode:
            self.timeline.setSplinePoints(self.timelineConfig.getSplinePoints())
            self.timeline.reconfigureTimeline()
        self.updateLayouts()
        
    def setTimeline(self,timeline):
        """
        Method: setTimeline(timeline)
        Created: 20.03.2005, KP
        Description: Sets the timeline controlled by this
        """    
        self.timeline=timeline
        
    def setTimelineConfig(self,config):
        """
        Method: setTimelienConfig(panel)
        Created: 20.03.2005, KP
        Description: Sets the timeline config panel controlled by this
        """    
    
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
        """
        Method: configureTimeline(seconds, frames)
        Created: 20.03.2005, KP
        Description: Set the duration and frames of the movie
        """    
        #print "Calling timeline.configureTimeline(",seconds,",",frames,")"
        self.duration = seconds
        self.frames = frames
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

    def findControlPoint(self,point):
        """
        Method: findControlPoint(point)
        Created: 06.04.2005, KP
        Description: Method that returns a control point of the spline
        """        
        return self.splineEditor.findControlPoint(point)
        
    def setSplinePoint(self,pointnum,point):
        """
        Method: setSplinePoint
        Created: 11.04.2005, KP
        Description: A method that sets the physical position of a spline
                     control point
        """ 
        return self.splineEditor.setSplinePoint(pointnum,point)
        
    def __str__(self):
        """
        Method: __str__
        Created: 05.04.2005, KP
        Description: Return string representation of self
        """        
        s="Urmas rendering\nDuration: %.2fs\nFrames: %d\n"%(self.duration,self.frames)
        s+=str(self.timeline)
        return s
        
    def __getstate__(self):
        """
        Method: __getstate__
        Created: 06.04.2005, KP
        Description: Return the dict that is to be pickled to disk
        """      
        odict={}
        for key in ["duration","frames","timeline","animationMode"]:
            odict[key]=self.__dict__[key]
        return odict
        
