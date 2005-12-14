# -*- coding: iso-8859-1 -*-
"""
 Unit: Timeline
 Project: BioImageXD
 Created: 04.02.2005, KP
 Description:

 URM/AS - The Unified Rendering Manager / Animator for Selli
 
 This is a timeline based GUI for controlling the rendering of datasets. The GUI allows users
 to specify a path for the camera to follow (using Heikki Uuksulainen's MayaVi animator code)
 and also allows them to produce videos of the rendering using ffmpeg.
 
 The timeline widget and the timescale are implemented in this module.
 
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

import  wx.lib.scrolledpanel as scrolled
import wx
import wx.lib.masked as masked
from Track import *
from TimeScale import *

import PreviewFrame

import os.path
import sys,types
import Logging
import operator
import messenger    
        
class Timeline(scrolled.ScrolledPanel):
#class Timeline(wx.ScrolledWindow):
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
        size=(750,600)
        
        if kws.has_key("size"):
            size=kws["size"]
        scrolled.ScrolledPanel.__init__(self,parent,-1,size=size)
        self.oldBgCol=self.GetBackgroundColour()
        #wx.ScrolledWindow.__init__(self,parent,-1,size=size)
        self.control = control
        self.parent = parent
        self.frames = 0
        self.selectedTrack = None
        control.setTimeline(self)
        self.sizer=wx.GridBagSizer(5,1)
        
        self.timepointSizer = wx.GridBagSizer(2,1)
        self.splineSizer = wx.GridBagSizer(2,1)
        self.keyframeSizer = wx.GridBagSizer(2,1)
        
        
        self.timeScale=TimeScale(self)
        self.timeScale.setDuration(self.control.getDuration())

        self.sizer.Add(self.timeScale,(0,0),flag=wx.EXPAND|wx.LEFT|wx.RIGHT)
        self.Unbind(wx.EVT_CHILD_FOCUS)

        # Add the sizers to which the tracks will be added
        # this way we don't need to for example shuffle
        # spline and keyframe tracks if timepoint tracks need
        # to be changed
        self.sizer.Add(self.timepointSizer,(1,0),flag=wx.EXPAND|wx.ALL)
        self.sizer.Add(self.splineSizer,(2,0),flag=wx.EXPAND|wx.ALL)
        self.sizer.Add(self.keyframeSizer,(3,0),flag=wx.EXPAND|wx.ALL)
   
        self.timepointTracks=[]
        self.splinepointTracks=[]
        self.keyframeTracks=[]
        self.timepointTrackAmnt=0
        self.splinepointTrackAmnt=0
        self.keyframeTrackAmnt=0
        self.trackOffset = 1
        
        w,h=self.GetSize()
        w2,h=self.timeScale.GetSize()
        self.timeScale.SetSize((w,h))
        dt = UrmasPalette.UrmasDropTarget(self,"Track")
        self.SetDropTarget(dt)
        
        
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.SetupScrolling()
        
        
        #self.sizer.Fit(self)
        messenger.connect(None,"set_timeline_size",self.setupScrolling)
        messenger.connect(None,"set_duration",self.onSetDuration)
        messenger.connect(None,"set_frames",self.onSetFrames)
        
        
    def AcceptDrop(self,x,y,data):
        """
        Method: AcceptDrop
        Created: 02.09.2005, KP
        Description: Method called to indicate that a user is no longer dragging
                     something to this track
        """     
        print "AcceptDrop",x,y,data
        if data=="Spline":
            self.addSplinepointTrack("")
        elif data=="Keyframe":
            self.addKeyframeTrack("")
        else:
            self.addTrack("")
            
    def OnDragLeave(self):
        """
        Method: OnDragLeave
        Created: 02.09.2005, KP
        Description: Method called to indicate that a user is no longer dragging
                     something to this track
        """     
        print "OnDragLeave"
        print "old bg color=",self.oldBgCol
        self.SetBackgroundColour(self.oldBgCol)
        self.Refresh()
            
    def OnDragOver(self,x,y,d):
        """
        Method: OnDragOver
        Created: 02.09.2005, KP
        Description: Method called to indicate that a user is dragging
                     something to this track
        """ 
        print "OnDragOver"
        self.SetBackgroundColour((192,192,192))
        self.Refresh()
        
    def setupScrolling(self,obj=None,evt=None,arg=None):
        """
        Method: setupScrolling
        Created: 21.08.2005, KP
        Description: Set the scrollbars
        """         
        self.SetupScrolling()
        
    def getSplineTracks(self):
        """
        Method: getSplineTracks
        Created: 18.04.2005, KP
        Description: Return the camera path tracks
        """ 
        return self.splinepointTracks
        
    def getTimepointTracks(self):
        """
        Method: getTimepointTracks
        Created: 19.04.2005, KP
        Description: Return the timepoint tracks
        """ 
        return self.timepointTracks
        
    def getKeyframeTracks(self):
        """
        Method: getKeyframeTracks
        Created: 18.08.2005, KP
        Description: Return the keyframe tracks
        """ 
        return self.keyframeTracks
        
    def getSelectedTrack(self):
        """
        Method: getSelectedTrack
        Created: 14.04.2005, KP
        Description: Return the track that is currently selected
        """ 
        return self.selectedTrack
        
    def setSelectedTrack(self,track):
        """
        Method: setSelectedTrack
        Created: 14.04.2005, KP
        Description: Set the track that is currently selected
        """ 
        if self.selectedTrack and track != self.selectedTrack:
            self.selectedTrack.setSelected(None)
        self.selectedTrack=track
        self.control.window.updateMenus()
        
        
    def setBeginningToPrevious(self,track):
        """
        Method: setBeginningToPrevious
        Created: 18.04.2005, KP
        Description: Set the given track to start at the position where
                     the previous track ends
        """ 
        i=self.splinepointTracks.index(track)
        if i<1:
            Dialogs.showwarning(self,"First track has no preceeding tracks","Cannot set beginning of track")
            return
        p=self.splinepointTracks[i-1].items[-1].getPoint()
        self.splinepointTracks[i].items[0].setPoint(p)
        print "Setting track %d to begin at %s"%(i,str(p))
        self.splinepointTracks[i].showSpline()
        
    def setEndToNext(self,track):
        """
        Method: setEndToNext
        Created: 18.04.2005, KP
        Description: Set the given track to end at the position where
                     the next track begins
        """ 
        i=self.splinepointTracks.index(track)
        
        if i==len(self.splinepointTracks)-1:
            Dialogs.showwarning(self,"Last track has no following tracks","Cannot set end of track")
            return
        p=self.splinepointTracks[i+1].items[0].getPoint()
        self.splinepointTracks[i].items[-1].setPoint(p)
        print "Setting track %d to end at %s"%(i,str(p))
        self.splinepointTracks[i].showSpline()
        
            
        
    def __set_pure_state__(self,state):
        """
        Method: __set_pure_state__()
        Created: 11.04.2005, KP
        Description: Method called by UrmasPersist to allow the object
                     to refresh before it's items are created
        """ 
        Logging.info("Setting pure state of timeline",kw="animator")
        # We add these tracks so that when the tracks are depersisted, they will simply overwrite these
        # since URPO doesn't know how to create the tracks, just how to load the contents
#        spamnt = self.splinepointTrackAmnt
#        tpamnt = self.timepointTrackAmnt
#        print "self.splinepointTrackAmnt=",self.splinepointTrackAmnt
#        print "self.timepointTrackAmnt=",self.timepointTrackAmnt
        #for tptrack in state.timepointTracks:
        for tptrack in state.timepointTracks:
            t=self.addTrack(tptrack.label)
            t.__set_pure_state__(tptrack)
        for sptrack in state.splinepointTracks:
            t=self.addSplinepointTrack(sptrack.label)
            t.__set_pure_state__(sptrack)

#        for n in range(tpamnt-len(self.timepointTracks)):
#            print "Adding timepoint track"
#            self.addTrack("Timepoints %d"%n,n)
#        for n in range(spamnt-len(self.splinepointTracks)):
#            print "Adding splinepoint track"
#            self.addSplinepointTrack("Camera Path %d"%n)
#        print "splinepointtracks now=",self.splinepointTracks
            
    def moveTracks(self,sizer,moveFrom,moveTo,howMany):
        """
        Method: moveTracks
        Created: 13.04.2005, KP
        Description: Moves the tracks placed on a sizer
        Parameters:
            moveFrom    Start moving the tracks from here
            moveTo      Move them here
            howMany     How many tracks there are to move
        """ 
        replace=[]
        for i in range(howMany):
            #item=self.sizer.FindItemAtPosition((self.trackOffset+moveFrom+i,0))
            item=sizer.FindItemAtPosition((moveFrom+i,0))
            item=item.GetWindow()
            #print "Got item =",item
            print "Detaching %d at (%d,0)"%(i,moveFrom+i)
            sizer.Show(item,0)
            sizer.Detach(item)
            replace.append(item)
        
        for i in range(0,len(replace)):
            item=replace[i]
            print "Placing %d to (%d,0)"%(i,moveTo+i)
            #self.sizer.Add(item,(self.trackOffset+moveTo+i,0),flag=wx.EXPAND|wx.ALL)
            sizer.Add(item,(moveTo+i,0),flag=wx.EXPAND|wx.ALL)
            item.SetSize((item.width,item.height))
            sizer.Show(item,1)
            
            
    def addTrack(self,label,n=0):
        """
        Method: addTrack(label,itemamount)
        Created: 06.04.2005, KP
        Description: Adds a track to the timeline
        """    
        if label=="":
            label="Timepoints %d"%len(self.timepointTracks)
        
        tr=TimepointTrack(label,self,number=1,timescale=self.timeScale,control=self.control,height=55)
        
        self.timeScale.setOffset(tr.getLabelWidth())
        self.splinepointTrackAmnt = len(self.splinepointTracks)
        self.timepointTrackAmnt = len(self.timepointTracks)
        self.keyframeTrackAmnt = len(self.keyframeTracks)
        # Move the splinepoints down by one step
#        if self.splinepointTrackAmnt:
#            self.moveTracks(self.timepointTrackAmnt,self.timepointTrackAmnt+1,self.splinepointTrackAmnt)
#        if self.keyframeTrackAmnt:
#            self.moveTracks(self.timepointTrackAmnt+self.splinepointTrackAmnt,self.timepointTrackAmnt+self.splinepointTrackAmnt+1,self.keyframeTrackAmnt)
#        self.Layout()
        print "Adding track to ",self.trackOffset+self.timepointTrackAmnt
        #self.sizer.Add(tr,(self.trackOffset+self.timepointTrackAmnt,0),flag=wx.EXPAND|wx.ALL)
        self.timepointSizer.Add(tr,(self.timepointTrackAmnt,0),flag=wx.EXPAND|wx.ALL)
        tr.setColor((56,196,248))
        if self.dataUnit:
            print "Setting dataunit",self.dataUnit
            tr.setDataUnit(self.dataUnit)
        
        if n:
            tr.setItemAmount(n)        
        
        self.FitInside()
        #self.SetupScrolling()
        self.Layout()            
        
        self.timepointTracks.append(tr)
        self.control.window.updateMenus()
        #print "almost done"
        if self.dataUnit:
            tr.showThumbnail(True)
        return tr
            
    def addSplinepointTrack(self,label):
        """
        Method: addSplinepointTrack(label)
        Created: 11.04.2005, KP
        Description:
        """
        if label=="":
            label="Camera Path %d"%len(self.splinepointTracks)
        tr=SplineTrack(label,self,number=1,timescale=self.timeScale,control=self.control,height=55)
        tr.setColor((56,196,248))
        self.splinepointTrackAmnt = len(self.splinepointTracks)
        self.timepointTrackAmnt = len(self.timepointTracks)
        self.keyframeTrackAmnt=len(self.keyframeTracks)
        #if self.keyframeTrackAmnt:
        #    self.moveTracks(self.timepointTrackAmnt+self.splinepointTrackAmnt,self.timepointTrackAmnt+self.splinepointTrackAmnt+1,self.keyframeTrackAmnt)        
        
        #self.sizer.Add(tr,(self.trackOffset+self.timepointTrackAmnt+self.splinepointTrackAmnt,0),flag=wx.EXPAND|wx.ALL)
        self.splineSizer.Add(tr,(self.splinepointTrackAmnt,0),flag=wx.EXPAND|wx.ALL)
        
        self.FitInside()
        self.Layout()
        #self.SetupScrolling()
        self.splinepointTracks.append(tr)    
        self.control.window.updateMenus()
        return tr

    def addKeyframeTrack(self,label):
        """
        Method: addKeyframeTrack(label)
        Created: 18.08.2005, KP
        Description:
        """
        if label=="":
            label="Keyframe %d"%len(self.keyframeTracks)
        tr=KeyframeTrack(label,self,number=1,timescale=self.timeScale,control=self.control,height=55)
        
        self.keyframeTrackAmnt = len(self.keyframeTracks)
        self.timepointTrackAmnt = len(self.timepointTracks)
        self.splinepointTrackAmnt=len(self.splinepointTracks)
        print "Adding track to ",self.trackOffset+self.timepointTrackAmnt+self.splinepointTrackAmnt
        #self.sizer.Add(tr,(self.trackOffset+self.timepointTrackAmnt+self.splinepointTrackAmnt+self.keyframeTrackAmnt,0),flag=wx.EXPAND|wx.ALL)
        self.keyframeSizer.Add(tr,(self.keyframeTrackAmnt,0),flag=wx.EXPAND|wx.ALL)
        
        self.FitInside()
        self.Layout()
        #self.SetupScrolling()
        self.keyframeTracks.append(tr)    
        self.control.window.updateMenus()
        
        return tr        
        
    def getLargestTrackLength(self,cmptrack):
        """
        Method: getLargestTrackLength
        Created: 16.02.2005, KP
        Description: Return the length of the largest track that is the
                     same type as the argument, but not the same
        """
        tracks=[]
        tracks.extend(self.timepointTracks)
        tracks.extend(self.splinepointTracks)
        tracks.extend(self.keyframeTracks)
        ret=0
        for track in tracks:
            if track != cmptrack and track.__class__ == cmptrack.__class__:
                item=track.items[-1]
                x,y=item.GetPosition()
                w,h=item.GetSize()
                curr=x+w-track.getLabelWidth()
                if ret<curr:
                    ret=curr
        return ret
        
            
            
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
        self.setDisabled(not flag)
        if len(self.splinepointTracks):
            for track in self.splinepointTracks:
                track.setEnabled(flag)
         
        self.Refresh()
        #self.Layout()
        #self.sizer.Fit(self)#self.SetScrollbars(20,0,tx/20,0)
    
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
        for track in self.keyframeTracks:
            self.removeTrack(track)
        self.splinepointTracks=[]
        self.timepointTracks=[]
        self.keyframeTracks=[]
        
    def removeTrack(self,track,reorder=0):
        """
        Method: removeTrack(track)
        Created: 06.04.2005, KP
        Description: Remove a track from the GUI
        """    
        print "Hiding ",track
        self.sizer.Show(track,0)
        self.sizer.Detach(track)
        track.remove()
        if reorder:
            if track in self.timepointTracks:
                lst=self.timepointTracks
                pos=lst.index(track)
                self.moveTracks(pos+1,pos,len(self.timepointTracks[pos:])+self.splinepointTrackAmnt)
                self.timepointTrackAmnt-=1                    
            elif track in self.splinepointTracks:
                lst=self.splinepointTracks
                pos=lst.index(track)
                n=pos
                pos+=self.timepointTrackAmnt
                print "Moving from ",pos+1,"to ",pos,"#",self.splinepointTrackAmnt-n
                self.moveTracks(pos+1,pos,self.splinepointTrackAmnt-n)
                self.splinepointTrackAmnt-=1
            else:
                lst=self.keyframeTracks
                pos=lst.index(track)
                pos+=self.timepointTrackAmnt+self.splinepointTrackAmnt
                self.moveTracks(pos+1,pos,self.keyframeTrackAmnt-n)
                self.keyframeTrackAmnt-=1
            lst.remove(track)
            
                
            self.Layout()

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
        
    def onSetDuration(self,obj,evt,duration):
        """
        Method: onSetDuration
        Created: 20.09.2005, KP
        Description: Method to set the timeline duration
        """
        print "On set duration",duration
        self.seconds = duration
        self.configureTimeline(duration,self.frames)
        
    def onSetFrames(self,obj,evt,frames):
        """
        Method: onSetDuration
        Created: 20.09.2005, KP
        Description: Method to set the timeline duration
        """
        self.frames = frames
        
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
        print "cONFIGURE TIMELINE"
        self.seconds = seconds
        self.frames = frames
        #print "Configuring frame amount to ",frames
        #frameWidth=(seconds*self.timeScale.getPixelsPerSecond())/float(frames)
        #print "frame width=",frameWidth
        self.timeScale.setDuration(seconds)
        tx,ty=self.timeScale.GetSize()
        #self.parent.SetSize((tx,-1))
        #w,h=self.GetSize()
        #Logging.info("Setting size of timeline to ",(tx,h),kw="animator")
        #self.SetSize((tx,h))
        #self.Layout()
        #self.sizer.Fit(self)
        #self.SetupScrolling()
        #print "foo"
        #print "Configuring tracks",self.timepointTracks,self.splinepointTracks,self.keyframeTracks
        for i in self.timepointTracks:
            if i:
                i.setDuration(seconds,frames)
        for i in self.splinepointTracks:
            if i:
                i.setDuration(seconds,frames)
        for i in self.keyframeTracks:
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
        s+="Keyframe tracks: {"
        s+=", ".join(map(str,self.keyframeTracks))
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
        self.keyframeTrackAmnt = len(self.keyframeTracks)
        for key in ["timepointTracks","splinepointTracks","splinepointTrackAmnt","timepointTrackAmnt","keyframeTracks","keyframeTrackAmnt"]:
            odict[key]=self.__dict__[key]
        return odict        
 
