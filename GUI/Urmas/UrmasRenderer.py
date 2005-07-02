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

import RenderingInterface
from UrmasControl import *
import time
import Dialogs
import wx

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
        self.renderingInterface = RenderingInterface.getRenderingInterface(1)
        self.oldTimepoint=-1
        self.lastpoint=None
        self.currTrack=None
        self.lastSplinePoint=None

    def startAnimation(self,control):
        """
        Class: startMayavi
        Created: 20.04.2005, KP
        Description: Start mayavi for rendering
        """
        self.control = control
        self.dataUnit = control.getDataUnit()
        data = self.dataUnit.getTimePoint(0)
        print "Setting dataunit to",self.dataUnit
        self.renderingInterface.setDataUnit(self.dataUnit)
        self.renderingInterface.setCurrentTimepoint(0)
        self.renderingInterface.setTimePoints([0])
        settings = self.dataUnit.getSettings()
#        ctf= settings.get("ColorTransferFunction")
#        self.renderingInterface.doRendering(preview=data,ctf = ctf)

        
    def render(self,control,preview=0,**kws):
        """
        Class: Render(control)
        Created: 04.04.2005, KP
        Description: Render the timeline
        """    
        renderpath="."
        self.control = control
        self.dataUnit = control.getDataUnit()
        self.duration = duration = control.getDuration()
        self.frames = frames = control.getFrames()
        if not preview and not self.renderingInterface.isVisualizationSoftwareRunning():
            Dialogs.showerror(self.control.window,"Cannot render project: visualization software is not running","Visualizer is not running")
            return -1
        if kws.has_key("size"):
            self.renderingInterface.setRenderWindowSize(kws["size"])
        if kws.has_key("renderpath"):renderpath=kws["renderpath"]
        if not preview:
            self.renderingInterface.setOutputPath(renderpath)
            self.renderingInterface.setCurrentTimepoint(0)
            
            self.renwin = self.renderingInterface.getRenderWindow() 
#            print "self.renwin=",self.renwin
            self.ren = self.renderingInterface.getRenderer()
            if self.renderingInterface.isVisualizationModuleLoaded() == False:
                Dialogs.showwarning(self.control.window,"You must specify some module to MayaVi first!","Oops!")
                return

            if not self.ren:
                Dialogs.showwarning(self.control.window,"No renderer in main render window!! This should not be possible!","Oops!")
                return
#            self.dlg = wx.ProgressDialog("Rendering","Rendering at %.2fs / %.2fs (frame %d / %d)"%(0,0,0,0),maximum = frames, parent = self.control.window)
#            self.dlg.Show()

        self.splineEditor = control.getSplineEditor()
        spf = duration / float(frames)

        if preview:
            cam = self.splineEditor.getCamera()
            self.ren = self.splineEditor.renderer
        else:
            self.ren = self.renderingInterface.getRenderer()
            cam = self.ren.GetActiveCamera()
        self.cam = cam
        #cam.SetViewUp(self.splineEditor.get_camera().GetViewUp())
        
        
#        cam.ComputeViewPlaneNormal()
#        cam.OrthogonalizeViewUp()

        for n in range(frames):
            self.renderFrame(n,(n+1)*spf,spf,preview=preview)
        if not preview:
            pass
#            self.dlg.Destroy()
            
    def getTimepointAt(self,time):
        """
        Method: getTimepointAt(time)
        Created: 05.04.2005, KP
        Description: Returns the timepoint used at given time
        Parameters:
        time    The current time in the timeline
        """            
        tracks = self.control.timeline.getTimepointTracks()
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
        tracks = self.control.timeline.getSplineTracks()
        points=[]
        for track in tracks:
            # See the stop items first
            for item in track.getStopItems():
                start,end=item.getPosition()
                if time >= start and time <= end:
                    print "Found in stop items"
                    return item
            
            for item in track.getItems():
                start,end=item.getPosition()
                if time >= start and time <= end:
                    if track != self.currTrack:
                        # Reset camera everytime we switch tracks
                        self.cam.SetFocalPoint(0,0,0)        
                        self.cam.SetViewUp((0,0,1))        
                        self.ren.ResetCamera()

                        self.currTrack=track
                        track.showSpline()
                    return item
                    
                
        return None
        
    def renderFrame(self,frame,timepos,spf,preview=0):
        """
        Method: renderFrame(frame,time)
        Created: 04.04.2005, KP
        Description: This renders a given frame
        Parameters:
        frame   The frame we're rendering
        time    The current time in the timeline
        spf     Seconds per one frame
        """            
        print "renderFrame at ",timepos
        timepoint = self.getTimepointAt(timepos)
        if not preview and (timepoint != self.oldTimepoint):
            # Set the timepoint to be used
            self.renderingInterface.setCurrentTimepoint(timepoint)
            # and update the renderer to use the timepoint
            self.renderingInterface.updateDataset()
            self.oldTimepoint = timepoint
        point = self.getSplinepointsAt(timepos)
        if not point:
            print "No camera position"
#            Dialogs.showerror(self.control.window,"Camera path ended prematurely","Cannot determine camera position")
        if point and not point.isStopped():
                
            p0=point.getPoint()
            #self.dlg.Update(frame,"Rendering at %.2fs / %.2fs (frame %d / %d)"%(timepos,self.duration,frame,self.frames))
            print "Rendering frame %d using timepoint %d, time is %f"%(frame,timepoint,timepos)
            start,end=point.getPosition()
            # how far along this part of spline we are
            d=timepos-start
            # how long is it in total
            n = end-start
            # gives us a percent of the length we've traveled
            percentage = d/float(n)
            #print "time %.2f is %.3f%% between %.2f and %.2f"%(timepos,percentage,start,end)
            n=point.getItemNumber()
            #print "p0=",p0,"item=",n
            p,point = self.control.splineEditor.getCameraPosition(n,p0,percentage)
            x,y,z=point
            self.lastSplinePoint=(x,y,z)
        elif point:
            print "Camera stopped, using last point"
            x,y,z=self.lastSplinePoint
            point=(x,y,z)
        focal = self.splineEditor.getCameraFocalPointCenter()
        if not preview:
            cam = self.ren.GetActiveCamera()
            ren=self.ren
        else:
            cam = self.splineEditor.getCamera()
            ren=self.splineEditor.renderer
            
        self.setCameraParameters(cam,ren, point, focal)
            
        if not preview:
            # With this we can be sure that all of the props will be visible.
            #self.ren.ResetCameraClippingRange()
            curr_file_name = self.renderingInterface.getFilename(frame)
            print "Saving with name",curr_file_name
            self.renderingInterface.render()     
            self.renderingInterface.saveFrame(curr_file_name)
        else:
            self.splineEditor.render()
            time.sleep(0.1)
        
    def setCameraParameters(self,cam,renderer,point,focal):
        """
        Method: setCameraParameters(camera,renderer, point, focal)
        Created: 04.04.2005, KP
        Description: Sets the camera parameters
        """
        if point:
            cam.SetPosition(point)        
        cam.SetFocalPoint(focal)
        # if the track wishes to maintain up direction
        if self.currTrack and self.currTrack.maintainUpDirection:
            cam.SetViewUp((0,0,1))
            cam.ComputeViewPlaneNormal()
            cam.OrthogonalizeViewUp()
        elif self.currTrack:
            # if there's movement in z direction
            if self.lastpoint and abs(self.lastpoint[2]-point[2])>2:
                print "Orthogonalizing because old z=",self.lastpoint[2],"!= new z",point[2]
                cam.OrthogonalizeViewUp()
        self.lastpoint=point
        renderer.ResetCameraClippingRange()
        

                    
    def renderPreviewFrame(self,frame,timepos,spf):
        """
        Method: renderFrame(frame,time)
        Created: 04.04.2005, KP
        Description: This renders a given frame
        Parameters:
        frame   The frame we're rendering
        time    The current time in the timeline
        spf     Seconds per one frame
        """            

        timepoint = self.getTimepointAt(timepos)
        point = self.getSplinepointsAt(timepos)
        if not point:
            print "No camera position"
#            Dialogs.showerror(self.control.window,"Camera path ended prematurely","Cannot determine camera position")
            return -1
        p0=point.getPoint()
        print "Rendering frame %d using timepoint %d, time is %f"%(frame,timepoint,timepos)
        start,end=point.getPosition()
        # how far along this part of spline we are
        d=timepos-start
        # how long is it in total
        n = end-start
        # gives us a percent of the length we've traveled
        percentage = d/float(n)
        #print "time %.2f is %.3f%% between %.2f and %.2f"%(timepos,percentage,start,end)
        n=point.getItemNumber()
        #print "p0=",p0,"item=",n
        
        p,point = self.control.splineEditor.getCameraPosition(n,p0,percentage)
        x,y,z=point
        print "Camera position is point %d = %.2f,%.2f,%.2f"%(p,x,y,z)
        
        cam = self.splineEditor.getCamera()
        focal = self.splineEditor.getCameraFocalPointCenter()
        
        self.setCameraParameters(cam,ren, point, focal)
        self.splineEditor.renderer.ResetCameraClippingRange()
        self.splineEditor.render()
        #time.sleep(0.1)
