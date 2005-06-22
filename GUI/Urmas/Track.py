# -*- coding: iso-8859-1 -*-

"""
 Unit: Track
 Project: BioImageXD
 Created: 05.02.2005
 Creator: KP
 Description:

 URM/AS - The Unified Rendering Manager / Animator for Selli
 
 Urmas is a timeline based GUI for controlling the rendering of datasets. The GUI allows users
 to specify a path for the camera to follow (using Heikki Uuksulainen's MayaVi animator code)
 and also allows them to produce videos of the rendering using ffmpeg.
 
 The widgets that implement the Tracks of the timeline are implemented in this module.

 Modified: 04.02.2005 KP - Created the module
 
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

import os.path
import sys
import math,random
import threading

from TrackItem import *
import UrmasPalette
import ImageOperations
import Dialogs
import TimepointSelection

from UIElements import NamePanel

class Track(wx.Panel):
    """
    Class: Track
    Created: 04.02.2005, KP
    Description: A class representing a track in the timeline
    """
    def __init__(self,name,parent,**kws):
        wx.Panel.__init__(self,parent,-1,style=wx.SIMPLE_BORDER)
        self.number=0
        self.duration=0
        self.frames=0
        height=80
        self.editable=1
        self.SetBackgroundColour((255,255,255))
        self.control = kws["control"]
        self.splineEditor = self.control.getSplineEditor()
        self.label = name
        self.previtem = None
        print "Height = ",height
        if kws.has_key("height"):
           print "Setting height to ",kws["height"]
           height=kws["height"]
        if kws.has_key("editable"):
            self.editable=kws["editable"]
        self.timescale=kws["timescale"]
        if kws.has_key("number"):
            self.number=kws["number"]
        print "Height now=",height
        self.sizer=wx.GridBagSizer()
        self.itemBox=None
        self.color=None
        self.parent=parent

        self.enabled = 1


        self.namePanel=NamePanel(self,name,(255,255,255),size=(125,height))
        self.sizer.Add(self.namePanel,(0,0))

        #self.sizer.Add(self.itemBox,(0,1))
        
        self.dragEndPosition=0
                
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)
        self.items=[]
        self.itemAmount = 0
        self.oldNamePanelColor = 0
    
        self.initTrack()
        
        self.namePanel.Bind(wx.EVT_LEFT_UP,self.setSelected)
        d,s=self.control.getDuration(),self.control.getFrames()
        print "duration=",d,"frames=",s
        self.setDuration(d,s)
        
    def getItems(self):
        """
        Method: getItems()
        Created: 19.04.2005, KP
        Description: Return items in this track
        """ 
        return self.items
        
    def setSelected(self,event):
        """
        Method: setSelected(event)
        Created: 14.04.2005, KP
        Description: Selects this track
        """
        print "setSelected(",event,")"
        if event:
            self.namePanel.setWeight(1)
            self.parent.setSelectedTrack(self)
        else:
            self.SetWindowStyle(wx.SIMPLE_BORDER)
            self.namePanel.setWeight(0)
            
    def setEnabled(self,flag):
        """
        Method: setEnabled(flag)
        Created: 14.04.2005, KP
        Description: Enables / disables this track
        """ 
        self.enabled = flag
        if not flag:
            self.oldNamePanelColor=col
            r=g=b=200
            print "Setting background to ",r,g,b
            self.namePanel.setColor((128,128,128),(r,g,b))
        else:
            self.namePanel.setColor((0,0,0),self.nameColor)

        
    def OnDragOver(self,x,y,d):
        """
        Method: OnDragOver
        Created: 12.04.2005, KP
        Description: Method called to indicate that a user is dragging
                     something to this track
        """ 
        #print "OnDragOver(%d,%d,%s)"%(x,y,d)
        if not self.oldNamePanelColor:
            #col=self.namePanel.GetBackgroundColour()
            col=self.namePanel.bg
            #r,g,b=col.Red(),col.Green(),col.Blue()
            r,g,b=col
            self.oldNamePanelColor=col
            r=int(r*0.8)
            g=int(g*0.8)
            b=int(b*0.8)
            self.namePanel.setColor((255,255,255),(r,g,b))
        self.namePanel.Refresh()
        curritem=None
        for item in self.items:
            ix,iy=item.GetPosition()
            #print "ix,iy=",ix,iy
            if ix<= x:
                #print "Found item",item
                curritem=item
                self.dragEndPosition = self.items.index(item)+1
        if curritem:
            if self.previtem and self.previtem != curritem:
                self.previtem.drawItem()
                self.previtem.Refresh()
            curritem.OnDragOver(x,y)
            self.previtem = curritem
        else:
            self.dragEndPosition = 0
        
    def OnDragLeave(self):
        """
        Method: OnDragLeave
        Created: 12.04.2005, KP
        Description: Method called to indicate that a user is no longer dragging
                     something to this track
        """     
        self.oldNamePanelColor = None
        self.namePanel.setColor((0,0,0),self.nameColor)
        self.namePanel.Refresh()

    def refresh(self):
        """
        Method: refresh()
        Created: 11.04.2005, KP
        Description: Method called by UrmasPersist to allow the object
                     to refresh before it's items are created
        """    
        self.setItemAmount(self.itemAmount)
        self.namePanel.setLabel(self.label)

    def updateLabels(self):
        """
        Method: updateLabels
        Created: 19.03.2005, KP
        Description: A method that updates all the items in this track
        """           
        print "Updating labels"
        for item in self.items:
            item.updateItem()
            item.drawItem()
            item.Refresh()
        self.Refresh()
        self.Layout()
        
    def remove(self):
        """
        Method: remove()
        Created: 06.04.2005, KP
        Description: Remove all items from self
        """               
        if self.itemBox:
            print "Removing ",len(self.items)," items"    
            
            self.sizer.Show(self.itemBox,0)
            self.sizer.Detach(self.itemBox)
            for i in range(len(self.items)):
                self.removeItem(i)
            self.itemBox.Show(self.positionItem,0)
            self.itemBox.Detach(self.positionItem)
            self.positionItem.Destroy()
            self.positionItem = None
            self.itemBox.Destroy()    

    def removeItem(self,position):
        """
        Method: removeItem(position)
        Created: 14.04.2005, KP
        Description: Remove an item from this track
        """              
        item=self.items[position]
        self.itemBox.Show(item,0)
        self.itemBox.Detach(item)
        self.positionItem = None
        self.items.remove(item)
        item.Destroy()
        
        
    def setDataUnit(self,dataUnit):
        """
        Method: setDataUnit
        Created: 04.02.2005, KP
        Description: A method to set the dataunit this track contains
        """           
        self.dataUnit=dataUnit
    
        
    def getLength(self):
        """
        Method: getLength()
        Created: 04.02.2005, KP
        Description: Return the number of items in this track
        """               
        return len(self.items)
        
      
    def itemCanResize(self,fromWidth,toWidth):
        """
        Method: itemCanResize(fromWidth,toWidth)
        Created: 04.02.2005, KP
        Description: A method that tells whether an item can change its size
                     from the specified size to a new size
        """               
        diff=toWidth-fromWidth
        w,h=self.itemBox.GetSize()
        w+=diff
        
        print "w=",w,"duration=",self.duration,"pps=",self.timescale.getPixelsPerSecond()
        if w>self.duration*self.timescale.getPixelsPerSecond():
            return 0
        return 1
        
    def initTrack(self):
        """
        Method: initTrack
        Created: 11.04.2005, KP
        Description: Initialize the GUI portion of this track
        """               
        self.itemBox=wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.itemBox,(0,1))
        self.positionItem = wx.Panel(self,-1)#EmptyItem(self,(0,1))
        self.positionItem.SetBackgroundColour(self.GetBackgroundColour())
        self.positionItem.SetSize((0,-1))
        self.itemBox.Insert(0,self.positionItem)
        
        self.updateLayout()
        self.items=[]
   
        
    def setDuration(self,seconds,frames,**kws):
        """
        Method: setDuration
        Created: 04.02.2005, KP
        Description: A method to set the length of this track, affecting
                     size of its items
        """              
        self.duration=seconds
        self.frames=frames

    def expandToMax(self):
        """
        Method: expandToMax()
        Created: 19.04.2005, KP
        Description: Expand this track to it's maximum size
        """              
        n=len(self.items)
        if not n:
            return
        
        w=float(self.duration)/float(n)
        w*=self.timescale.getPixelsPerSecond()
        
        tot=0
        last=0
        for i in self.items:
            i.setWidth(w)
            tot+=w
            last=i
       
        diff=self.duration*self.timescale.getPixelsPerSecond()-tot
        if diff>1:
            #print "diff=",diff
            last.setWidth(w+diff)
        self.updateLayout()
        
    def setToSize(self,size=8):
        """
        Method: setToSize(size)
        Created: 19.04.2005, KP
        Description: Set each item on this track to given size
        """              
        n=len(self.items)
        if not n:
            return
        
        tot=0
        last=0
        for i in self.items:
            i.setWidth(size)
            tot+=size
            last=i
       
        self.updateLayout()

    def setEmptySpace(self,space):
        """
        Method: setEmptySpace(self,space)
        Created: 15.04.2005, KP
        Description: Sets the empty space at the beginning of a track
        """        
        maxempty = self.parent.getLargestTrackLength(self)
        print "maxempty=",maxempty
        if space<0:
            space=0
        if space>maxempty:
            print "Won't grow beyond %d"%maxempty
            space=maxempty
        #self.positionItem.setWidth(space)
        self.positionItem.SetSize((space,-1))
        #self.Layout()
        self.parent.Layout()
        #self.updateLayout()
        print "setting positionItem size",self.positionItem.GetSize()
        
        
    def getLabelWidth(self):
        """
        Method: getLabelWidth()
        Created: 04.02.2005, KP
        Description: A method that returns the width of the name panel
        """               
        return self.namePanel.GetSize()[0]

    def setColor(self,col):
        """
        Method: setColor
        Created: 04.02.2005, KP
        Description: A method that sets the color of this track's items
        """               
        self.color=col
        self.headercolor=(127,127,127)
        for item in self.items:
            item.setColor(col,self.headercolor)
            item.Layout()
            
    def updateLayout(self):
        """
        Method: updateLayout
        Created: 04.02.2005, KP
        Description: A method that updates the layout of this track
        """               
        self.Layout()
        self.parent.Layout()
        for item in self.items:
            item.updateItem()
         
        
    def getDuration(self,pixels):
        """
        Method: getDuration
        Created: 20.03.2005, KP
        Description: A method that returns the time the camera takes to travel
                     given part of the spline
        """ 
        return float(pixels) / self.control.getPixelsPerSecond()
        
    def getPixels(self,duration):
        """
        Method: getPixels
        Created: 11.04.2005, KP
        Description: A method that returns the amount of pixels a given
                     number of seconds streches on the timeline
        """ 
        return float(duration) * self.control.getPixelsPerSecond()
        
    def __str__(self):
        """
        Method: __str__
        Created: 05.04.2005, KP
        Description: Return string representation of self
        """        
        s="%s [\n"%self.label
        s+=", ".join(map(str,self.items))
        s+="]\n"
        return s
        
    def __getstate__(self):
        """
        Method: __getstate__
        Created: 11.04.2005, KP
        Description: Return the dict that is to be pickled to disk
        """      
        odict={}
        keys=[""]
        self.itemAmount = len(self.items)
        for key in ["label","items","color","nameColor","number","itemAmount"]:
            odict[key]=self.__dict__[key]
        return odict        
    

 
class SplineTrack(Track):
    """
    Class: SplineTrack
    Created: 13.04.2005, KP
    Description: A class representing a spline track in the timeline
    """       
    def __init__(self,name,parent,**kws):
        Track.__init__(self,name,parent,**kws)   
        self.closed = 0
        self.nameColor = (0,148,213)
        self.namePanel.setColor((0,0,0),self.nameColor)
        if "item" in kws:
            self.itemClass=kws["item"]
        else:
            self.itemClass=SplinePoint
        if "closed" in kws:
            self.closed = kws["closed"]
        dt = UrmasPalette.UrmasDropTarget(self,"Spline")
        self.SetDropTarget(dt)
        
    def getClosed(self):
        """
        Method: getClosed()
        Created: 14.04.2005, KP
        Description: Is this spline closed or not
        """     
        return self.closed
        
    def setClosed(self,flag,add=1):
        """
        Method: setClosed
        Created: 14.04.2005, KP
        Description: Sets the spline represented by this flag to be closed
        """     
        print "setClosed(",flag,")"
        self.closed = flag
        self.splineEditor.setClosed(flag)
        if flag and add:
            self.addSplinePoint(len(self.items))
        elif add:
            self.removeItem(len(self.items))

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
            print "got bounds=",bounds
            pts=bounds[0:4]
            for i in range(4):
                self.addSplinePoint(pos,(i==3),point=bounds[i])
                pos=pos+1
            self.setClosed(1,0)
        elif data=="Perpendicular":
            pos = 0
            if len(self.items):
                Dialogs.showerror(self,"Perpendicular camera path can only be placed on an empty track","Cannot place camera path")
                return
            x,y,z = self.splineEditor.dataDimensions()
            r = max(x,y,z)
            x0,y0,z0 = self.splineEditor.getCameraFocalPointCenter()
            
            # On top
            p0 = (x0,y0,z0+r)
            p1 = (x0+r,y0,z0)
            p2 = (x0,y0,z0-r)
            p3 = (x0-r,y0,z0)
            pts=[p0,p1,p2,p3]
            for i in range(4):
                print "adding %d = "%pos,pts[i]
                self.addSplinePoint(pos,(i==3),point=pts[i])
                pos=pos+1
            self.setClosed(1,0)
            
        else:
            dlg = wx.TextEntryDialog(self,"How many control points should the camera path have:","Configure Camera path")
            dlg.SetValue("5")
            if dlg.ShowModal()==wx.ID_OK:
                try:
                    val=int(dlg.GetValue())
                except:
                    return
                print "Adding %d spline points"%val
                pos=self.dragEndPosition
                for i in range(val):
                    self.addSplinePoint(pos)
                    pos=pos+1
                
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
        self.removeItem(position)
        self.showSpline()
        self.Layout()
        #self.sizer.Fit(self)        

        
        
    def addSplinePoint(self,position,update=1,**kws):
        """
        Method: addItem
        Created: 04.02.2005, KP
        Description: A method to add a new item to this track
        """
        h=self.namePanel.GetSize()[1]
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
            pts.append(item.getPoint())
 #       print "current=",pts
        pts.insert(position,point)

        if len(pts)>=2:
            self.splineEditor.setClosed(self.closed)
            self.splineEditor.setSplinePoints(pts)
            self.control.setSplineInteractionCallback(self.updateLabels)

        item=self.itemClass(self,"%d"%position,(20,h),**itemkws)
        if self.color:
            item.setColor(self.color,self.headercolor)
        self.items.insert(position,item)
        # +1 accounts for the empty item
        self.itemBox.Insert(position+1,item)

        for i in range(len(self.items)):
            self.items[i].setItemNumber(i)
            self.items[i].setText("%d"%i)
            if update:
                self.items[i].updateItem()
                self.items[i].drawItem()
        
        if update:
            self.Layout()
            #self.sizer.Fit(self)
            

        
    def __getstate__(self):
        """
        Method: __getstate__
        Created: 14.04.2005, KP
        Description: Return the dict that is to be pickled to disk
        """      
        odict = Track.__getstate__(self)
        for key in ["closed"]:
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
            self.showSpline()
            self.control.setSplineInteractionCallback(self.updateLabels)        
    def showSpline(self):
        """
        Method: showSpline()
        Created: 18.04.2005, KP
        Description: Show spline represented by this track
        """ 
        pts=[]
        for item in self.items:
            pts.append(item.getPoint())
        if len(pts)>=2:
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
        
        
class TimepointTrack(Track):
    """
    Class: TimepointTrack
    Created: 13.04.2005, KP
    Description: A class representing a timepoint track in the timeline
    """       
    def __init__(self,name,parent,**kws):
        Track.__init__(self,name,parent,**kws)
        self.nameColor = (128,195,155)
        self.namePanel.setColor((0,0,0),self.nameColor)
        if "item" in kws:
            self.itemClass=kws["item"]
        else:
            self.itemClass=TrackItem
        dt = UrmasPalette.UrmasDropTarget(self,"Timepoint")
        self.SetDropTarget(dt)
        self.thumbnail=1
    
    def AcceptDrop(self,x,y,data):
        """
        Method: AcceptDrop
        Created: 12.04.2005, KP
        Description: Method called to indicate that a user is no longer dragging
                     something to this track
        """
        oldlen=len(self.items)
        timepoints=TimepointSelection.TimepointSelection(self.parent)
        timepoints.setDataUnit(self.control.getDataUnit())
        if timepoints.ShowModal()==wx.ID_OK:
            tps=timepoints.getSelectedTimepoints()
            self.insertTimepoints(tps)
        if not oldlen:
            self.expandToMax()
            
    def showThumbnail(self,flag):
        """
        Method: showThumbnail
        Created: 04.02.2005, KP
        Description: A method to set a flag indicating, whether to show a
                     thumbnail on the items in this track
        """           
        self.thumbnail=flag
        for item in self.items:
            #print "Setting thumbnail on",item
            item.setThumbnailDataunit(self.dataUnit)
    
    def insertTimepoints(self,timepoints):
        """
        Method: insertTimepoints(tps)
        Created: 13.04.2005, KP
        Description: Insert the given timepoints to the track
        """              
        pos=self.dragEndPosition
        for tp in timepoints:
            self.addTimepoint(pos,tp,0)
            pos+=1
        self.Layout()
        #self.sizer.Fit(self)
            

    def addTimepoint(self,position,timepoint,update=1):
        """
        Method: addTimepoint
        Created: 04.02.2005, KP
        Description: A method to add a new item to this track
        """              
        h=self.namePanel.GetSize()[1]
        kws={"editable":self.editable}
        kws["dataunit"]=self.dataUnit
        kws["thumbnail"]=timepoint
        kws["timepoint"]=timepoint
        text="%d"%timepoint
        item=self.itemClass(self,text,(20,h),**kws)
        if self.color:
            item.setColor(self.color,self.headercolor)
        self.items.insert(position,item)
        # +1 accounts for the empty item
        self.itemBox.Insert(position+1,item)
        
        for i,item in enumerate(self.items):
            item.setItemNumber(i)
            
        if update:
            self.Layout()
            self.sizer.Fit(self)
        item.updateItem()
            
    def setItemAmount(self,n):
        """
        Method: setItemAmount
        Created: 20.04.2005, KP
        Description: A method to set the amount of items in this track
        """               
        self.remove()
        self.initTrack()
        for i in range(n):
            self.addTimepoint(i,i,0)
