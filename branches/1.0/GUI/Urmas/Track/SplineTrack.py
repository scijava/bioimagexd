# -*- coding: iso-8859-1 -*-

"""
 Unit: SplineTrack
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
from Track import *
class SplineTrack(Track):
    """
    Class: SplineTrack
    Created: 13.04.2005, KP
    Description: A class representing a spline track in the timeline
    """       
    def __init__(self,name,parent,**kws):
        self.nameColor = (0,148,213)
        self.fg=(0,0,0)
        self.bg=self.nameColor
        # A flag that indicates that keyframe track is similiar to
        # camera path track in that it defines the camera movement
        self.trackType = "DEFINE_CAMERA"
        
        Track.__init__(self,name,parent,**kws)   
        
        self.paintOverlay=1
        self.overlayColor = ((0,0,255),25)                
        
        self.closed = 0
        self.maintainUpDirection=0
        #self.namePanel.setColor((0,0,0),self.nameColor)
        if "item" in kws:
            self.itemClass=kws["item"]
        else:
            self.itemClass=SplinePoint
        if "closed" in kws:
            self.closed = kws["closed"]
        dt = UrmasPalette.UrmasDropTarget(self,"Spline")
        self.SetDropTarget(dt)
            
    def setMaintainUpDirection(self,flag):
        """
        Method: setMaintainUpDirection(flag)
        Created: 25.06.2005, KP
        Description: Toggles whether up direction is maintained in track
        """     
        Logging.info("Will maintain up direction: %s"%(flag!=0),kw="animator")
        self.maintainUpDirection=flag
        
    def getClosed(self):
        """
        Method: getClosed()
        Created: 14.04.2005, KP
        Description: Is this spline closed or not
        """     
        return self.closed
        
    def onDown(self,event):
        """
        Method: onDown
        Created: 17.07.2005, KP
        Description: Item is clicked
        """
        ret=Track.onDown(self,event)
        if self.overlayItem and self.overlayPos != -1:
            self.paintTrack()
            self.Refresh()
            return ret        
        
    def setClosed(self,flag,add=1):
        """
        Method: setClosed
        Created: 14.04.2005, KP
        Description: Sets the spline represented by this flag to be closed
        """     
        Logging.info("Track is closed: %s"%(flag!=0),kw="animator")
        self.closed = flag
        self.splineEditor.setClosed(flag)
        #if flag and add:
        #    #self.addSplinePoint(len(self.items))
        #    
        #elif add:
        #    self.removeItem(len(self.items))

    def AcceptDrop(self,x,y,data):
        """
        Method: AcceptDrop
        Created: 12.04.2005, KP
        Description: Method called to indicate that a user is no longer dragging
                     something to this track
        """     
        oldlen=len(self.items)
        if data=="Circular":
            pos = 0
            if len(self.items):
                Dialogs.showerror(self,"Circular camera path can only be placed on an empty track","Cannot place camera path")
                return
            bounds = self.splineEditor.getBounds()
            pts=bounds[0:4]
            for i in range(4):
                self.addSplinePoint(pos,(i==3),point=bounds[i])
                pos=pos+1
            self.setClosed(1,0)
            self.setMaintainUpDirection(1)
        elif data=="Perpendicular":
            pos = 0
            if len(self.items):
                Dialogs.showerror(self,"Perpendicular camera path can only be placed on an empty track","Cannot place camera path")
                return
            x,y,z = self.splineEditor.dataDimensions()
            r = 2*max(x,y,z)
            x0,y0,z0 = self.splineEditor.getCameraFocalPointCenter()
            
            # On top
            p0 = (x0,y0,z0+r)
            p1 = (x0+r,y0,z0)
            p2 = (x0,y0,z0-r)
            p3 = (x0-r,y0,z0)
            pts=[p0,p1,p2,p3]
            for i in range(4):
                self.addSplinePoint(pos,(i==3),point=pts[i])
                pos=pos+1
            self.setClosed(1,0)
        # If this is a stop-camera item
        elif data=="Stop":
            pos=self.dragEndPosition
            self.addStopPoint(pos)
            self.paintTrack()
            self.Refresh()
        else:
            dlg = wx.TextEntryDialog(self,"How many control points should the camera path have:","Configure Camera path")
            dlg.SetValue("5")
            if dlg.ShowModal()==wx.ID_OK:
                try:
                    val=int(dlg.GetValue())
                except:
                    return
                pos=self.dragEndPosition
                for i in range(val):
                    self.addSplinePoint(pos)
                    pos=pos+1
                self.setMaintainUpDirection(1)

                self.Refresh()
                self.Layout()
                
        # If there were no items before this, then expand to max
        if not oldlen:
            self.expandToMax()
            
    def getSplineLength(self,splinepoint):
        """
        Method: getSplineLength
        Created: 19.03.2005, KP
        Description: A method that returns the physical length of a spline
                     range given the spline points width
        """ 
        if not self.duration:
            return 0
        return self.splineEditor.getSplineLength(splinepoint,splinepoint+1)

    def setToRelativeSize(self,size):
        """
        Method: setToRelativeSize(size)
        Created: 19.04.2005, KP
        Description: Set duration of all items in this track
        """              
        n=len(self.items)
        total=self.splineEditor.getSplineLength(0,n-1)
        
        if not n:
            return
        
        tot=0
        last=0
        Logging.info("total size=",total," (pixels=",size,")",kw="animator")
        for i in self.items:
            if i.isStopped():
                i.setWidth(30)
                continue
            n=self.getSplineLength(i.getItemNumber())
            if n:
                percent=float(n)/total
                Logging.info("item ",i.getItemNumber(),"is ",n,"which is ",percent,"percent",kw="animator")
    
                i.setWidth(size*percent)
                tot+=size*percent
                last=i
            else:
                i.setWidth(8)
       
        self.updateLayout()


    def getSplinePoint(self,point):
        """
        Method: getSplinePoint
        Created: 06.04.2005, KP
        Description: A method that returns the physical position of a spline
                     control point
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

    def removeItem(self,position):
        """
        Method: removeItem(position)
        Created: 14.04.2005, KP
        Description: Remove an item from this track
        """
        #self.removeItem(position)
        spc=0
        for i,item in enumerate(self.items):
            if not item.isStopped():
                self.items[i].setItemNumber(spc)
                self.items[i].setText("%d"%spc)
                spc+=1        
        self.showSpline()
        self.Layout()
        #self.sizer.Fit(self)     
        
    def removeActiveItem(self):
        """
        Method: removeActiveItem
        Created: 31.01.2006, KP
        Description: Remove the currently selected item
        """       
        Track.removeActiveItem(self)
        spc=0
        for i,item in enumerate(self.items):
            if not item.isStopped():
                self.items[i].setItemNumber(spc)
                self.items[i].setText("%d"%spc)
                spc+=1        
        self.showSpline()

    def addStopPoint(self,position):
        """
        Method: addStopPoint
        Created: 24.06.2005, KP
        Description: A method to add a stop in the camera movement
        """
        h=self.height
        item=StopItem(self,(30,h))
        self.items.insert(position,item)
        self.updatePositions()
        return item
        
    def addSplinePoint(self,position,update=1,**kws):
        """
        Method: addItem
        Created: 04.02.2005, KP
        Description: A method to add a new item to this track
        """
        h=self.height
        itemkws={"itemnum":position,"editable":self.editable}
        
        if kws.has_key("point"):
            point = kws["point"]
        else:
            point = self.splineEditor.getRandomPoint()
        itemkws["point"]=point
        
#        print "Setting point to ",point
        pts=[]
        for item in self.items:
 #           print "item=",item
            if not hasattr(item,"stopitem"):
                pts.append(item.getPoint())
            
        if position>=len(pts)-1:
            Logging.info("append pts, pos=%d,len=%d"%(position,len(pts)),kw="animator")
            pts.append(point)
        else:
            Logging.info("insert pts",kw="animator")
            pts.insert(position,point)
        Logging.info("spline pts=",pts,kw="animator")    

        if len(pts)>=2:
            self.splineEditor.setClosed(self.closed)
            self.splineEditor.setSplinePoints(pts)
            self.control.setSplineInteractionCallback(self.updateLabels)

        item=self.itemClass(self,"%d"%position,(20,h),**itemkws)
        if self.color:
            item.setColor(self.color,self.headercolor)
        if position>=len(pts)-1:
            print "appending item",item.itemnum
            self.items.append(item)
        else:
            print "Inserting items"
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
        messenger.send(None,"set_keyframe_mode",0)
        self.splineEditor.setViewMode(0)
        if event:
            self.showSpline()
            self.control.setSplineInteractionCallback(self.updateLabels)        

    def shiftItems(self,direction):
        """
        Method: shiftItems
        Created: 15.12.2005, KP
        Description: Shift items in the given direction
        """        
        Track.shiftItems(self,direction)
        for i in self.items:
            i.setText("%d"%i.getItemNumber())
        #spc=0
        #for i,item in enumerate(self.items):
        #    if not item.isStopped():
        #        self.items[i].setItemNumber(spc)
        #        self.items[i].setText("%d"%spc)
        #        spc+=1                
        #        self.items[i].updateItem()
        #        self.items[i].drawItem()        
        self.showSpline()
            
    def showSpline(self):
        """
        Method: showSpline()
        Created: 18.04.2005, KP
        Description: Show spline represented by this track
        """ 
        messenger.send(None,"set_keyframe_mode",0)
        pts=[]
        for item in self.items:
            if not isinstance(item,StopItem):
                pts.append(item.getPoint())
        if len(pts)>=2:
            print "Setting spline points: ",pts
            self.splineEditor.setSplinePoints(pts)
            self.splineEditor.setClosed(self.closed)
            self.splineEditor.render()
            
    def setItemAmount(self,n):
        """
        Method: setItemAmount
        Created: 20.04.2005, KP
        Description: A method to set the amount of items in this track
        """               
        self.remove()
        self.initTrack()
        for i in range(n):
            self.addSplinePoint(i,0)
            
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
                Logging.info("Add spline point spc=%d,i=%d, itemnum=%d"%(spc,i,item.itemnum),kw="animator")
                tp=self.addSplinePoint(spc,0,point=item.point)
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
        
        
        
#foobar    
