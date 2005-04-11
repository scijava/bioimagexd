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

import os.path
import sys
import math,random
import threading

from TrackItem import *
import ImageOperations

        
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
        if "item" in kws:
            self.itemClass=kws["item"]
        else:
            self.itemClass=TrackItem
            
        self.control = kws["control"]
        
        self.label = name
        self.timepointTrack=kws.has_key("timepoint")
        
        if kws.has_key("height"):
            height=kws["height"]
        if kws.has_key("editable"):
            self.editable=kws["editable"]
        self.timescale=kws["timescale"]
        if kws.has_key("number"):
            self.number=kws["number"]

        self.sizer=wx.GridBagSizer()
        self.itemBox=None
        self.color=None
        self.parent=parent

        self.namePanel=wx.Panel(self,-1)
        self.namePanel.SetBackgroundColour(wx.Colour(127,127,127))
        self.nameLbl=wx.StaticText(self.namePanel,-1,name,size=(100,height))
        self.namePanel.SetSize((200,height))
        self.sizer.Add(self.namePanel,(0,0))

        #self.sizer.Add(self.itemBox,(0,1))
                
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)
        self.items=[]
        self.thumbnail=0
        self.itemAmount = 0
        #self.setItemAmount(1)
        self.initTrack()
        
        
    def refresh(self):
        """
        Method: refresh()
        Created: 11.04.2005, KP
        Description: Method called by UrmasPersist to allow the object
                     to refresh before it's items are created
        """    
        self.setItemAmount(self.itemAmount,0)
        self.nameLbl.SetLabel(self.label)
        
    def updateLabels(self):
        """
        Method: updateLabels
        Created: 19.03.2005, KP
        Description: A method that updates all the items in this track
        """           
        print "Refreshing..."
        for item in self.items:
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
            for i in self.items:
                self.itemBox.Show(i,0)
                self.itemBox.Detach(i)
                self.items.remove(i)
                i.Destroy()
            self.itemBox.Destroy()    
        
    def setDataUnit(self,dataUnit):
        """
        Method: setDataUnit
        Created: 04.02.2005, KP
        Description: A method to set the dataunit this track contains
        """           
        self.dataUnit=dataUnit
    
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
        #print "Trying to resize ",diff
        w,h=self.itemBox.GetSize()
        #print "current size=",w
        w+=diff
        
        #print "w=",w,">self.duration*pps",self.duration,self.timescale.getPixelsPerSecond()
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
        
        self.updateLayout()
        self.items=[]

        
    def setItemAmount(self,n,update=1):
        """
        Method: setItemAmount
        Created: 04.02.2005, KP
        Description: A method to set the amount of items in this track
        """               
        self.remove()
        self.initTrack()
        print "Adding ",n,"items"
        for i in range(n):
            lbl=""
            if self.number:
                lbl="%d"%i
            self.addItem(i,lbl,update)
        if update:
            self.updateLayout()
   
        
    def setDuration(self,seconds,frames,**kws):
        """
        Method: setDuration
        Created: 04.02.2005, KP
        Description: A method to set the length of this track, affecting
                     size of its items
        """                   
        n=len(self.items)
        
        w=float(seconds)/float(n)
        #print "New size=",w
        self.duration=seconds
        self.frames=frames
        w*=self.timescale.getPixelsPerSecond()
        
        tot=0
        last=0
        for i in self.items:
            i.setWidth(w)
#            # Do not allow any track item to be of width less than one frame
#            i.setMinimumWidth(w)
            tot+=w
            last=i
        
        diff=seconds*self.timescale.getPixelsPerSecond()-tot
        if diff>1:
            #print "diff=",diff
            last.setWidth(w+diff)
        #print "Updating layout"
        self.updateLayout()
        
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
        #print "updateLayout()"
        self.Layout()
        self.parent.Layout()
        for item in self.items:
            item.updateItem()
        #print "Control structure now:"
        #print self.control
        
        
    def addItem(self,n,item,update=1):
        """
        Method: addItem
        Created: 04.02.2005, KP
        Description: A method to add a new item to this track
        """              
        h=self.namePanel.GetSize()[1]
        kws={"itemnum":n,"editable":self.editable}
        if self.thumbnail:
            kws["dataunit"]=self.dataUnit
            kws["thumbnail"]=int(item)
        if self.timepointTrack:
            kws["timepoint"]=int(item)
        item=self.itemClass(self,item,(20,h),**kws)
        if self.color:
            item.setColor(self.color,self.headercolor)
        self.items.append(item)
        self.itemBox.Add(item)
        if update:
            self.Layout()
            self.sizer.Fit(self)
        item.updateItem()

    def getSplineLength(self,splinepoint):
        """
        Method: getSplineLength
        Created: 19.03.2005, KP
        Description: A method that returns the physical length of a spline
                     range given the spline points width
        """ 
        if not self.duration:
            return 0
        return self.control.getSplineLength(splinepoint)
        
    def getSplinePoint(self,point):
        """
        Method: getSplinePoint
        Created: 06.04.2005, KP
        Description: A method that returns the physical position of a spline
                     control point
        """ 
        return self.control.findControlPoint(point)

    def setSplinePoint(self,pointnum,point):
        """
        Method: setSplinePoint
        Created: 11.04.2005, KP
        Description: A method that sets the physical position of a spline
                     control point
        """ 
        return self.control.setSplinePoint(pointnum,point)
        
        
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
        for key in ["label","items","color","number","itemAmount"]:
            odict[key]=self.__dict__[key]
        return odict        
 
