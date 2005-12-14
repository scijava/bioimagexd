# -*- coding: iso-8859-1 -*-

"""
 Unit: KeyframeTrack
 Project: BioImageXD
 Created: 05.02.2005, KP
 Description:

 URM/AS - The Unified Rendering Manager / Animator for Selli
 
 Urmas is a timeline based GUI for controlling the rendering of datasets. The GUI allows users
 to specify a path for the camera to follow (using Heikki Uuksulainen's MayaVi animator code)
 and also allows them to produce videos of the rendering using ffmpeg.
 
 The widgets that implement the Tracks of the timeline are implemented in this module.

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
import Logging
import os.path
import sys
import math,random
import threading

from Urmas.TrackItem import *
from Urmas import UrmasPalette
import ImageOperations
import Dialogs
import TimepointSelection

import messenger

from SplineTrack import *
 
class KeyframeTrack(SplineTrack):
    """
    Class: KeyframeTrack
    Created: 17.08.2005, KP
    Description: A class representing a Keyframe track in the timeline
    """       
    def __init__(self,name,parent,**kws):
        self.nameColor = (255,51,153)
        self.fg=(0,0,0)
        self.bg=self.nameColor
        kws["height"]=80
        self.overlayPosInPixels=0
        self.overlayPosInPixelsEnd=0
        self.overlayPos=-1
        self.overlayItem=None        
        Track.__init__(self,name,parent,**kws)   
        #self.namePanel.setColor((0,0,0),self.nameColor)
        if "item" in kws:
            self.itemClass=kws["item"]
        else:
            self.itemClass=KeyframePoint
        if "closed" in kws:
            self.closed = kws["closed"]
        dt = UrmasPalette.UrmasDropTarget(self,"Keyframe")
        self.SetDropTarget(dt)
        messenger.connect(None,"set_camera",self.onSetCamera)
        messenger.connect(None,"show_time_pos",self.onDisableOverlay)

    def onDisableOverlay(self,obj,evt,*arg):
        """
        Method: onDisableOverlay
        Created: 7.09.2005, KP
        Description: Disable the overlay when the user uses the timeslider
        """        
        self.overlayPos=-1
        self.overlayItem=None
    def onDown(self,event):
        """
        Method: onDown
        Created: 17.07.2005, KP
        Description: Item is clicked
        """
        ret=Track.onDown(self,event)
        #print "ret=",ret,"selectedItem=",self.selectedItem
        if ret:
            item=self.selectedItem
            #print "dragmode=",self.selectedItem.dragMode
        else:
            item=None
            
        if self.selectedItem and self.selectedItem.dragMode:
            return ret
        self.selectedItem=None
        if item:
            #print "Setting overlay item"
            #self.timePosItem=self.selectedItem
            start,end=item.getPosition()
            self.overlayItem=item
            self.overlayPos=start
            messenger.send(None,"set_timeslider_value",start*10.0)
            messenger.send(None,"render_time_pos",start)
            self.paintTrack()
            self.Refresh()
            return ret
        else:
            self.overlayPos=-1
            self.overlayItem=None            
        return ret
        
    def onPaintTrack(self):
        """
        Method: onPaintTrack(self)
        Created: 22.08.2005, KP
        Description: Called by Track so that track types can do their own painting
        """
        if self.renew != 2 and self.overlayPosInPixels:
            self.dc.Blit(self.overlayPosInPixels-1,0,self.overlayPosInPixelsEnd,self.height,self.mdc,self.overlayPosInPixels-1,0)                    
        
        print "overlayPos=",self.overlayPos,"overlayItem=",self.overlayItem
        if self.overlayPos!=-1:
            if not self.overlayItem or (self.overlayPos != self.overlayItem.getPosition()[0]):
                curr=None
                for item in self.items:
                    start,end=item.getPosition()
                    if start<= self.overlayPos and end >= self.overlayPos:
                        curr=item
                        break
                self.overlayItem=curr
                self.overlayPos=start

            start,end=self.overlayItem.getPosition()
            pps=self.timescale.getPixelsPerSecond() 
            w=(end-start)*pps
            h=self.height
            print "Painting overlay at ",self.overlayPos*pps
            try:
                overlay=ImageOperations.getOverlay(int(w),int(h),(0,255,0),25)
            except Exception, e:
                print "Failed to create overlay:",e
                sys.stdin.readline()
            overlay=overlay.ConvertToBitmap()
            
            pos=self.getLabelWidth() + self.overlayPos*pps
            self.overlayPosInPixelsEnd=pos+w+1
            self.overlayPosInPixels=pos
            self.dc.DrawBitmap(overlay,pos,0,1)    
        
            
    def onSetCamera(self,obj,evt,cam):
        """
        Method: onSetCamera
        Created: 18.08.2005, KP
        Description: Set the camera for the current item
        """             
        print "overlayItem=",self.overlayItem
        if self.overlayItem:    
            self.overlayItem.getThumbnail()
            self.overlayItem.drawItem()
            self.paintTrack()
            #self.Refresh()
            
    def AcceptDrop(self,x,y,data):
        """
        Method: AcceptDrop
        Created: 12.04.2005, KP
        Description: Method called to indicate that a user is no longer dragging
                     something to this track
        """     
        oldlen=len(self.items)
        pos=self.dragEndPosition
        if pos==-1:
            pos=len(self.items)
        Logging.info("Adding keyframe at pos ",pos,kw="animator")
        self.addKeyframePoint(pos)
        pos=pos+1
        self.Refresh()
        self.Layout()
                
        # If there were no items before this, then expand to max
        #if not oldlen:
        #    self.expandToMax()
            
    def removeItem(self,position):
        """
        Method: removeItem(position)
        Created: 14.04.2005, KP
        Description: Remove an item from this track
        """
        #self.removeItem(position)
        #self.showKeyframe()
        self.Layout()
        #self.sizer.Fit(self)     
        
    def addKeyframePoint(self,position,update=1,**kws):
        """
        Method: addItem
        Created: 04.02.2005, KP
        Description: A method to add a new item to this track
        """
        h=self.height
        itemkws={"itemnum":position,"editable":self.editable}

        item=self.itemClass(self,"%d"%position,(20,h),**itemkws)
        if self.color:
            item.setColor(self.color,self.headercolor)
        if position>=len(self.items):
            Logging.info("Appending item ",item.itemnum,kw="animator")
            self.items.append(item)
        else:
            Logging.info("Inserting item ",item.itemnum,kw="animator")
            self.items.insert(position,item)
        # +1 accounts for the empty item
        spc=0
        for i,item in enumerate(self.items):
            if not item.isStopped():
                self.items[i].setItemNumber(spc)
                self.items[i].setText("%d"%spc)
                spc+=1
                if update:
                    self.items[i].updateItem()
                    self.items[i].drawItem()
        
        self.updatePositions()

        if update:
            self.paintTrack()
            self.Refresh()
            #self.sizer.Fit(self)
        return item
            
    def __getstate__(self):
        """
        Method: __getstate__
        Created: 14.04.2005, KP
        Description: Return the dict that is to be pickled to disk
        """      
        odict = Track.__getstate__(self)
        n=0
        pos=0
        for key in ["closed","maintainUpDirection"]:
            odict[key]=self.__dict__[key]
        return odict        
        
    def setSelected(self,event):
        """
        Method: setSelected(event)
        Created: 14.04.2005, KP
        Description: Selects this track
        """ 
        Track.setSelected(self,event)
        if event:
            self.showKeyframe()
            #self.control.setKeyframeInteractionCallback(self.updateLabels)        
            
    def showKeyframe(self):
        """
        Method: showKeyframe()
        Created: 18.04.2005, KP
        Description: Show Keyframe represented by this track
        """ 
        messenger.send(None,"set_keyframe_mode",1)
        self.splineEditor.setViewMode(0)
            
            
    def __set_pure_state__(self,state):
        """
        Method: __set_pure_state__()
        Created: 11.04.2005, KP
        Description: Method called by UrmasPersist to allow the object
                     to refresh before it's items are created
        """ 
        Track.__set_pure_state__(self,state)
        self.closed = state.closed
        spc=0
        
        for i,item in enumerate(state.items):
            if not "stopitem" in  dir(item):
                Logging.info("Add Keyframe point spc=%d,i=%d, itemnum=%d"%(spc,i,item.itemnum),kw="animator")
                tp=self.addKeyframePoint(spc,0,point=item.point)
                tp.__set_pure_state__(item)
                spc+=1
            else:
                Logging.info("Add stop point i=%d, itemnum=%d"%(i,item.itemnum),kw="animator")
                tp=self.addStopPoint(i)
                tp.__set_pure_state__(item)
        #self.updatePositions()
        for i,item in enumerate(self.items):
            print "item at %d: %s"%(i,str(item))
        self.paintTrack()
        
        
