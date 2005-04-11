#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

"""
 Unit: UrmasRenderer
 Project: BioImageXD
 Created: 04.04.2005
 Creator: KP
 Description:

 URM/AS - The Unified Rendering Manager / Animator for Selli
 
 This is a timeline based GUI for controlling the rendering of datasets. The GUI allows users
 to specify a path for the camera to follow (using Heikki Uuksulainen's MayaVi animator code)
 and also allows them to produce videos of the rendering using ffmpeg.
 
 This module contains the class that takes a datastructure representation
 of the timeline and renders it to a movie or set of images. 
 
 Modified: 04.04.2005 KP - Created the module
 
 BioImageXD includes the following persons:
 
 DW - Dan White, dan@chalkie.org.uk
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 PK - Pasi Kankaanpää, ppkank@bytl.jyu.fi
 
 Copyright (c) 2005 BioImageXD Project.
"""
__author__ = "BioImageXD Project"
__version__ = "$Revision: 1.22 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

from UrmasControl import *

class UrmasRenderer:
    """
    Class: UrmasRenderer
    Created: 04.04.2005, KP
    Description: This class takes a datastructure representation of the 
                 timeline and renders it to a movie or set of images.
    """
    def __init__(self):
        """
        Class: __init__
        Created: 04.04.2005, KP
        Description: Initialization
        """    
        pass
        
    def Render(self,control):
        """
        Class: Render(control)
        Created: 04.04.2005, KP
        Description: Render the timeline
        """    
        self.control = control
        duration = control.getDuration()
        frames = control.getFrames()
        spf = duration / float(frames)
        for n in range(frames):
            self.renderFrame(n,(n+1)*spf,spf)
            
    def getTimepointAt(self,time):
        """
        Method: getTimepointAt(time)
        Created: 05.04.2005, KP
        Description: Returns the timepoint used at given time
        Parameters:
        time    The current time in the timeline
        """            
        tracks = self.control.getTimepointTracks()
        timepoint = 0
        for track in tracks:
            for item in track.getItems():
                start,end=item.getPosition()
                if time >= start and time <= end:
                    timepoint = item.getTimepoint()
        return timepoint
        
    def getSplinepointsAt(self,time):
        """
        Method: getSplinepointAt(time)
        Created: 05.04.2005, KP
        Description: Returns two splinepoints between wich the camera is located at this time
        Parameters:
        time    The current time in the timeline
        """            
        tracks = self.control.getSplineTracks()
        points=[]
        for track in tracks:
            for item in track.getItems():
                start,end=item.getPosition()
                if time >= start and time <= end:
                    points.append(item)
                if len(points)==2:
                    break
                
        return points       
        
    def renderFrame(self,frame,time,spf):
        """
        Method: renderFrame(frame,time)
        Created: 04.04.2005, KP
        Description: This renders a given frame
        Parameters:
        frame   The frame we're rendering
        time    The current time in the timeline
        spf     Seconds per one frame
        """            
        timepoint = self.getTimepointAt(time)
        splinepoints = self.getSplinepointsAt(time)
        p0=splinepoints[0]
        if len(splinepoints)==1:
            p1=(-1,-1,-1)
        else:
            p1=splinepoints[1]
        print "Rendering frame %d using timepoint %d, time is %f"%(frame,timepoint,time)
        
        p,point = self.control.splineEditor.getCameraPosition(p0,p1)
        print "Camera position is %d,%d,%d"%point
        
        
                    
                
        
        
