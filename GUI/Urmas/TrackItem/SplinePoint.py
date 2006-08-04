# -*- coding: iso-8859-1 -*-

"""
 Unit: SplinePoint
 Project: BioImageXD
 Created: 19.03.2005, KP
 Description:

 URM/AS - The Unified Rendering Manager / Animator for Selli
 
 Urmas is a timeline based GUI for controlling the rendering of datasets. The GUI allows users
 to specify a path for the camera to follow (using Heikki Uuksulainen's MayaVi animator code)
 and also allows them to produce videos of the rendering using ffmpeg.

 The items placed on the track are implemented in this module
 
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

import ImageOperations
from Urmas import UrmasControl
import Logging        
DRAG_OFFSET=20

import messenger

from TrackItem import *


class SplinePoint(TrackItem):
    """
    Class: SplinePoint
    Created: 19.03.2005, KP
    Description: A class representing an item in a spline points track.
    """       
    def __init__(self,parent,text,size,**kws):
        """
        Method: __init__
        Created: 20.03.2005, KP
        Description: Initialize the method
        """ 
        self.point=(0,0,0)
        self.itemnum=kws.get("itemnum",0)
        self.focalPoint = (0,0,0)
        self.orientation=(0,0,1),(0,0,0)
        TrackItem.__init__(self,parent,text,size,**kws)
        if kws.has_key("point"):
            print "Got point",kws["point"]
            self.setPoint(kws["point"])
                
    def getItemNumber(self):
        """
        Method: getItemNumber()
        Created: 14.04.2005, KP
        Description: Return the item number of this item
        """       
        return self.itemnum
         
    def getPoint(self): return self.point
    def setPoint(self,pt):
        """
        Method: setPoint(self)
        Created: 14.04.2005, KP
        Description: Return the point this spline point represents
        """      
        self.point = pt
        
    def drawItem(self,hilight=-1):
        """
        Method: drawItem()
        Created: 19.03.2005, KP
        Description: A method that draws the splinetrack item.
        """       
        #self.dc = wx.BufferedDC(wx.ClientDC(self),self.buffer)
        self.dc = wx.MemoryDC()
        self.dc.SelectObject(self.buffer)

        r,g,b=self.color
        if hilight!=-1:
            r-=32
            g-=32
            b-=32
            if r<0:r=0
            if g<0:g=0
            if b<0:b=0
        
        col=wx.Colour(r,g,b)
        self.dc.SetBackground(wx.Brush(col))
        self.dc.Clear()
        self.dc.BeginDrawing()
        self.dc.SetPen(wx.Pen((0,0,0)))
        # draw the body
        self.dc.SetBrush(wx.Brush(col))
        #self.dc.SetBackground(wx.Brush(wx.BLACK))
        self.dc.DrawRectangle(0,0,self.width,self.height)        
        TrackItem.drawHeader(self,hilight)
        
        r,g,b=self.headercolor
        self.dc.SetPen(wx.Pen(wx.Colour(r,g,b),2))
        self.dc.DrawLine(self.width-1,0,self.width-1,self.height)


        self.dc.SetTextForeground((0,0,0))
        self.dc.SetFont(wx.Font(8,wx.SWISS,wx.NORMAL,wx.NORMAL))
        #Logging.info("Getting spline length of item",self.itemnum,kw="animator")
        l=self.parent.getSplineLength(self.itemnum)
        s=self.parent.getDuration(self.GetSize()[0])
        x,y,z=self.point
        #fx,fy,fz,fw=self.orientation
        text= u"Control point: %.2f,%.2f,%.2f"%(x,y,z)
        #text1=u"Orientation: %.2f,%.2f,%.2f,%.2f"%(fx,fy,fz,fw)
        nutext2="Length:       %.2fum"%l
        text2=u"Length:        %.2f\u03bcm"%l
        text3=u"Duration:      %.2fs"%(s)
        n=0
        for text,nonunicode in [(text,text),(text2,nutext2),(text3,text3)]:
            try:
                self.dc.DrawText(text,5,n+self.labelheight+5)
            except:
                self.dc.DrawText(nonunicode,5,n+self.labelheight+5)
            n+=10

        if hilight != -1:
            self.hilight(hilight)
 
        self.dc.SelectObject(wx.NullBitmap)
        self.dc.EndDrawing()
        self.dc = None
    
    def updateItem(self):
        """
        Method: updateItem()
        Created: 06.04.2005, KP
        Description: A method called when the item has been resized
        """     
        TrackItem.updateItem(self)  
        pos=self.parent.getSplinePoint(self.itemnum)
        self.point = pos
        
    def __set_pure_state__(self,state):
        """
        Method: __set_pure_state__()
        Created: 11.04.2005, KP
        Description: Update the item
        """       
        TrackItem.__set_pure_state__(self,state)
        self.point = state.point
        try:
            self.focalPoint = state.focalPoint
        except:
            self.focalPoint = (0,0,0)
        self.parent.setSplinePoint(self.itemnum,self.point)
        
    def __getstate__(self):
        """
        Method: __getstate__
        Created: 11.04.2005, KP
        Description: Return the dict that is to be pickled to disk
        """     
        odict=TrackItem.__getstate__(self)
        for key in ["point","focalPoint"]:
            odict[key]=self.__dict__[key]
        return odict        
        
    def __str__(self):
        """
        Method: __str__
        Created: 05.04.2005, KP
        Description: Return string representation of self
        """  
        start,end=self.position
        desc="SP%d(%d,%d,%d)"%(self.itemnum,self.point[0],self.point[1],self.point[2])
        return "[%s %ds:%ds]"%(desc,start,end)      
    
    def isStopped(self):return 0

    def onDown(self,event):
        """
        Method: onDown(event)
        Created: 14.12.2005, KP
        Description: Event handler for when the mouse is pressed down over
                     this item. 
        """      
        TrackItem.onDown(self,event)
        
        messenger.send(None,"show_arrow",self.point)    
        
class SplineEndPoint(SplinePoint):
    """
    Class: SplineEndPoint
    Created: 14.12.2005, KP
    Description: A class representing the last item in a spline track
    """       
    def __init__(self,parent,text,size,**kws):
        """
        Method: __init__
        Created: 14.12.2005, KP
        Description: Initialize the item
        """
        text="End Point"
        self.init_done=0
        w,h=size
        w=h
        print "Creating keyframe endpoint with size=",w,h
        KeyframePoint.__init__(self,parent,text,size,**kws)
        self.headercolor = (80,100,200)
        self.setWidth(w)
        
        
        self.init_done=1
        
    def setWidth(self,w):
        if self.init_done:
            return
        KeyframePoint.setWidth(self,w)
    def setColor(self,col,headercolor):
        """
        Method: setColor(color, headercolor)
        Created: 10.02.2005, KP
        Description: Set the color and header color for this item
        """       
        self.color=col
        self.drawItem()        
    def setText(self,s):
        """
        Method: setText
        Created: 14.04.2005, KP
        Description: Set the text number of this item
        """       
        pass        
        


        
        
# safeguard        
