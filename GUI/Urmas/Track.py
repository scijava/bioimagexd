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
import UrmasPalette
import ImageOperations
import TimepointSelection

        
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
    
        self.enabled = 1
    
        self.namePanel=wx.Panel(self,-1)
        self.nameLbl=wx.StaticText(self.namePanel,-1,name,size=(100,height))
        self.namePanel.SetSize((200,height))
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
        self.nameLbl.Bind(wx.EVT_LEFT_UP,self.setSelected)
        #self.Bind(wx.EVT_LEFT_UP,self.setSelected)
        
    def setSelected(self,event):
        """
        Method: setSelected(event)
        Created: 14.04.2005, KP
        Description: Selects this track
        """ 
        print "setSelected(",event,")"
        if event:
            font=self.nameLbl.GetFont()
            font.SetWeight(wx.BOLD)
            self.nameLbl.SetFont(font)
            self.parent.setSelectedTrack(self)
        else:
            self.SetWindowStyle(wx.SIMPLE_BORDER)
            font=self.nameLbl.GetFont()
            font.SetWeight(wx.NORMAL)
            self.nameLbl.SetFont(font)
        
            
    def setEnabled(self,flag):
        """
        Method: setEnabled(flag)
        Created: 14.04.2005, KP
        Description: Enables / disables this track
        """ 
        self.enabled = flag
        if not flag:
            col=self.namePanel.GetBackgroundColour()
            self.nameLbl.SetForegroundColour((128,128,128))
            r,g,b=col.Red(),col.Green(),col.Blue()
            self.oldNamePanelColor=col
            r=g=b=200
            print "Setting background to ",r,g,b
            self.namePanel.SetBackgroundColour((r,g,b))
        else:
            self.namePanel.SetBackgroundColour(self.nameColor)
            self.nameLbl.SetForegroundColour((0,0,0))
        
        
    def OnDragOver(self,x,y,d):
        """
        Method: OnDragOver
        Created: 12.04.2005, KP
        Description: Method called to indicate that a user is dragging
                     something to this track
        """ 
        #print "OnDragOver(%d,%d,%s)"%(x,y,d)
        if not self.oldNamePanelColor:
            col=self.namePanel.GetBackgroundColour()
            r,g,b=col.Red(),col.Green(),col.Blue()
            self.oldNamePanelColor=col
            r=int(r*0.8)
            g=int(g*0.8)
            b=int(b*0.8)
            self.namePanel.SetBackgroundColour((r,g,b))
            self.nameLbl.SetForegroundColour((255,255,255))
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
        self.namePanel.SetBackgroundColour(self.nameColor)
        self.oldNamePanelColor = None
        self.nameLbl.SetForegroundColour((0,0,0))
        self.namePanel.Refresh()

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
            for i in range(len(self.items)):
                self.removeItem(i)
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
        if not n:
            return
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
        kws["height"]=40
        Track.__init__(self,name,parent,**kws)   
        self.closed = 0
        self.nameColor = (0,148,213)
        self.namePanel.SetBackgroundColour(wx.Colour(*self.nameColor))
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
        
    def setClosed(self,flag):
        """
        Method: setClosed
        Created: 14.04.2005, KP
        Description: Sets the spline represented by this flag to be closed
        """     
        print "setClosed(",flag,")"
        self.closed = flag
        self.splineEditor.setClosed(flag)
        if flag:
            self.addSplinePoint(len(self.items))
        else:
            self.removeItem(len(self.items))

    def AcceptDrop(self,x,y,type,data):
        """
        Method: AcceptDrop
        Created: 12.04.2005, KP
        Description: Method called to indicate that a user is no longer dragging
                     something to this track
        """     
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
        pts=[]
        for i in len(self.items):
            item=self.items[i]
            item.setItemNumber(i)
            pts.append(item.getPoint())
        self.splineEditor.setSplinePoints(pts)
        self.Layout()
        self.sizer.Fit(self)        

        
        
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
        pts=[]
        for item in self.items:
            pts.append(item.getPoint())
        pts.insert(position,point)
        if len(pts)>=2:
            self.splineEditor.setSplinePoints(pts)
        
        item=self.itemClass(self,"%d"%position,(20,h),**itemkws)
        if self.color:
            item.setColor(self.color,self.headercolor)
        self.items.insert(position,item)
        self.itemBox.Insert(position,item)

        for i in range(len(self.items)):
            self.items[i].setItemNumber(i)
            self.items[i].setText("%d"%i)
            if update:
                self.items[i].updateItem()
                self.items[i].drawItem()
        
        if update:
            self.Layout()
            self.sizer.Fit(self)
            

        
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

        
class TimepointTrack(Track):
    """
    Class: TimepointTrack
    Created: 13.04.2005, KP
    Description: A class representing a timepoint track in the timeline
    """       
    def __init__(self,name,parent,**kws):
        kws["height"]=40
        Track.__init__(self,name,parent,**kws)   
        self.nameColor = (128,195,155)
        self.namePanel.SetBackgroundColour(wx.Colour(*self.nameColor))
        if "item" in kws:
            self.itemClass=kws["item"]
        else:
            self.itemClass=TrackItem
        dt = UrmasPalette.UrmasDropTarget(self,"Timepoint")
        self.SetDropTarget(dt)
        self.thumbnail=1
    
    def AcceptDrop(self,x,y,type,data):
        """
        Method: AcceptDrop
        Created: 12.04.2005, KP
        Description: Method called to indicate that a user is no longer dragging
                     something to this track
        """     
        timepoints=TimepointSelection.TimepointSelection(self.parent)
        timepoints.setDataUnit(self.control.getDataUnit())
        if timepoints.ShowModal()==wx.ID_OK:
            tps=timepoints.getSelectedTimepoints()
            self.insertTimepoints(tps)
            
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
        self.sizer.Fit(self)
            

    def addTimepoint(self,position,timepoint,update=1):
        """
        Method: addTimepoint
        Created: 04.02.2005, KP
        Description: A method to add a new item to this track
        """              
        h=self.namePanel.GetSize()[1]
        kws={"itemnum":timepoint,"editable":self.editable}
        kws["dataunit"]=self.dataUnit
        kws["thumbnail"]=timepoint
        kws["timepoint"]=timepoint
        text="%d"%timepoint
        item=self.itemClass(self,text,(20,h),**kws)
        if self.color:
            item.setColor(self.color,self.headercolor)
        self.items.insert(position,item)
        self.itemBox.Insert(position,item)
        if update:
            self.Layout()
            self.sizer.Fit(self)
        item.updateItem()
            
