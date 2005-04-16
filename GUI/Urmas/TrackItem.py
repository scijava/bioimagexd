# -*- coding: iso-8859-1 -*-

"""
 Unit: TrackItem
 Project: BioImageXD
 Created: 19.03.2005
 Creator: KP
 Description:

 URM/AS - The Unified Rendering Manager / Animator for Selli
 
 Urmas is a timeline based GUI for controlling the rendering of datasets. The GUI allows users
 to specify a path for the camera to follow (using Heikki Uuksulainen's MayaVi animator code)
 and also allows them to produce videos of the rendering using ffmpeg.
 
 Theitems placed on the track are implemented in this module

 Modified: 04.02.2005 KP - Original code created
           19.03.2005 KP - Placed code in file of its own
 
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

import ImageOperations
import UrmasControl

        
class TrackItem(wx.Panel):
    """
    Class: TrackItem
    Created: 10.02.2005, KP
    Description: A class representing one item on a track
    """       

    def __init__(self,parent,text,size,**kws):
        wx.Panel.__init__(self,parent,-1)#,style=wx.SIMPLE_BORDER)
        self.text=text
        self.editable=1
        self.parent=parent
        self.minSize=5
        self.getting=0
        self.position=(0,0)
        self.dc=0
        self.buffer=0
        self.destroyed=0
        self.lastdiff=0
        self.thumbnailbmp=0
        self.labelheight=15
        self.thumbtimepoint=-1
        self.itemnum=0
        self.timepoint = -1
        if "itemnum" in kws:
            self.itemnum=kws["itemnum"]
        if "timepoint" in kws:
            self.timepoint = kws["timepoint"]
        if kws.has_key("editable"):
            self.editable=kws["editable"]
        if kws.has_key("dataunit"):
            self.dataUnit=kws["dataunit"]
        if kws.has_key("thumbnail"):
            self.thumbtimepoint=kws["thumbnail"]
        self.color=(255,255,255)
        self.headercolor=(127,127,127)
        self.Bind(wx.EVT_PAINT,self.onPaint)
        self.width,self.height=size
        self.SetSize((self.width,self.height))
        self.setWidth(self.width)
                        
        if self.editable:
            self.Bind(wx.EVT_LEFT_DOWN,self.onDown)
            self.Bind(wx.EVT_MOTION,self.onDrag)
            self.Bind(wx.EVT_LEFT_UP,self.onUp)
                        
        self.beginX=0
        self.dragMode=0
        
    def getItemNumber(self):
        """
        Method: getItemNumber()
        Created: 14.04.2005, KP
        Description: Return the item number of this item
        """       
        return self.itemnum
        
    def setItemNumber(self,n):
        """
        Method: setItemNumber(m)
        Created: 14.04.2005, KP
        Description: Set the item number of this item
        """       
        self.itemnum = n
        
    def setText(self,s):
        """
        Method: setText
        Created: 14.04.2005, KP
        Description: Set the text number of this item
        """       
        self.text=s

    def OnDragOver(self,x,y):
        """
        Method: OnDragOver(x,y)
        Created: 12.04.2005, KP
        Description: A method called when something is being dragged over this item
        """       
        w,h=self.GetSize()
        ix,iy=self.GetPosition()
        d=abs(ix-x)
        if d>w/2:
            hilight=w-1
        else:
            hilight=2
        self.drawItem(hilight)
        self.Refresh()
        self.parent.Refresh()
        #self.parent.Layout()
            
    
        
    def setThumbnailDataunit(self,dataunit):
        """
        Method: setThumbnail
        Created: 06.05.2005, KP
        Description: Sets the setting for thumbnail generation
        """       
        self.dataUnit=dataunit
        self.thumbtimepoint=self.timepoint
        
    def refresh(self):
        """
        Method: refresh()
        Created: 11.04.2005, KP
        Description: Update the item
        """       
        start,end=self.position
        
        start=self.parent.getPixels(start)
        end=self.parent.getPixels(end)
        start+=self.parent.getLabelWidth()
        end+=self.parent.getLabelWidth()
        x,y=self.GetPosition()
        self.SetPosition((start,y))
        print "Setting position to ",start,y
        w,h=self.GetSize()
        w=(end-start)
        print "Start=",start,"end=",end
        self.setWidth(w)
        self.drawItem()
        self.parent.Refresh()
        self.Refresh()
        self.parent.Layout()
        
    def setColor(self,col,headercolor):
        """
        Method: setColor(color, headercolor)
        Created: 10.02.2005, KP
        Description: Set the color and header color for this item
        """       
        self.color=col
        self.headercolor=headercolor
        self.drawItem()

        
    def onPaint(self,event):
        """
        Method: onPaint
        Created: 10.02.2005, KP
        Description: A method that will blit the buffer to screen
        """       
        dc=wx.BufferedPaintDC(self,self.buffer)

    def drawHeader(self):
        """
        Method: drawHeader()
        Created: 19.03.2005, KP
        Description: A method that draws the header of this item
        """       
        # Set the color to header color
        r,g,b=self.headercolor
        col=wx.Colour(r,g,b)
        
        # And draw the header block
        self.dc.SetBrush(wx.Brush(col))
        self.dc.SetPen(wx.Pen((0,0,0)))
        self.dc.SetBackground(wx.Brush(col))
        self.dc.DrawRectangle(0,0,self.width,self.labelheight)

        # Draw the text inside the header
        if self.text!="":
            self.dc.SetTextForeground((0,0,0))
            self.dc.SetFont(wx.Font(8,wx.SWISS,wx.NORMAL,wx.NORMAL))
            self.dc.DrawText(self.text,5,2)            
        
    def drawItem(self,hilight=-1):
        """
        Method: drawItem()
        Created: 10.02.2005, KP
        Description: A method that draws this track item
        """       
        self.dc.Clear()
        self.dc.BeginDrawing()
        self.dc.SetPen(wx.Pen((0,0,0)))

        # draw the body
        r,g,b=self.color
        col=wx.Colour(r,g,b)
        self.dc.SetBrush(wx.Brush(wx.BLACK))
        self.dc.SetBackground(wx.Brush(wx.BLACK))
        self.dc.DrawRectangle(0,0,self.width,self.height)        

        self.drawHeader()
        if hilight != -1:
            self.hilight(hilight)
        if self.thumbtimepoint>=0:
            self.drawThumbnail()
        r,g,b=self.headercolor
        self.dc.SetPen(wx.Pen(wx.Colour(r,g,b),2))
        self.dc.DrawLine(self.width-1,0,self.width-1,self.height)

    
        
        self.dc.EndDrawing()

    def hilight(self,h):
        """
        Method: hilight
        Created: 12.04.2005, KP
        Description: A method to highlight the spot where a drop would occur
        """ 
        self.dc.SetPen(wx.Pen(wx.Colour(0,0,0),2))
        self.dc.DrawLine(h,0,h,self.height)
 
    def getThumbnail(self):
        """
        Method: getThumbnail()
        Created: 19.03.2005, KP
        Description: A method that creates a thumbnail for a timepoint
        """ 
        # This may bail if the item gets deleted while the thread
        # is still running
        try:
            self.volume=self.dataUnit.getTimePoint(self.thumbtimepoint)
        except:
            pass
    def updateAfterThumbnail(self):
        """
        Method: updateAfterThumbnail()
        Created: 11.04.2005, KP
        Description: A method that refereshes this item, when a thumbnail has been generated
        """   
        try:
            self.drawItem()
        except:
            return
        self.parent.Refresh()
        self.Refresh()
        self.parent.Layout()
        wx.Yield()
                
        
    def drawThumbnail(self):
        """
        Method: drawThumbnail()
        Created: 10.02.2005, KP
        Description: A method that draws a thumbnail on an item. If no thumbnail exists,
                     this will create a thread to create one and return
        """   
        if not self.thumbnailbmp:
            if not self.getting:
                self.volume=0
                self.getting=1
                n=(1+self.thumbtimepoint)*750
                t=threading.Thread(None,self.getThumbnail)
                wx.FutureCall(n,lambda t=t:t.start())
                wx.FutureCall(n+300,self.updateAfterThumbnail)
                
                
            elif self.volume:
                vx,vy,vz=self.volume.GetDimensions()
                self.thumbnailbmp=ImageOperations.vtkImageDataToPreviewBitmap(self.volume,self.dataUnit.getColor(),0,self.height-self.labelheight)                            
            if not self.thumbnailbmp:
                return
        iw,ih=self.thumbnailbmp.GetSize()
        #print "image size=",iw,ih
        wdiff=(self.width-iw)/2
        if wdiff<0:wdiff=0
        self.dc.DrawBitmap(self.thumbnailbmp,wdiff,self.labelheight)
        
    def setMinimumWidth(self,w):
        """
        Method: setMinimumWidt(width)
        Created: 10.02.2005, KP
        Description: Set the minimum width for this item, below which it cannot
                     be resized
        """       
        self.minSize=w
        
    def setWidth(self,w):
        """
        Method: setWidth(width)
        Created: 10.02.2005, KP
        Description: Set the width of this item. Will allocate buffer for
                     drawing self.
        """       
        self.width=w
        self.SetSize((w,self.height))
        del self.buffer
        self.buffer=wx.EmptyBitmap(self.width,self.height)
        del self.dc
        self.dc = wx.BufferedDC(None,self.buffer)
        self.drawItem()
        
    def onDown(self,event):
        """
        Method: onDown(event)
        Created: 10.02.2005, KP
        Description: Event handler for when the mouse is pressed down over
                     this item. Will store the position in order to enable
                     dragging.
        """       
        x,y=event.GetPosition()
        #print "onDow()",x,y
        self.dragMode=0
        w,h=self.GetSize()
        posx,posy=self.GetPosition()
        if self.itemnum == 0 and x<8:
            self.dragMode=2
        if abs(x-w)<8:
            self.dragMode=1
            self.beginX=x
        return
            
    def onUp(self,event):
        """
        Method: onUp(event)
        Created: 10.02.2005, KP
        Description: Event handler for when mouse is released over this item.
                     Will store the position in order to enable dragging.
        """    
        x,y=event.GetPosition()
        self.beginX=x
        self.updateItem()

    def updateItem(self):
        """
        Method: updateItem()
        Created: 06.04.2005, KP
        Description: A method called when the item has been resized
        """       
        posx,posy=self.GetPosition()
        posx-=self.parent.getLabelWidth()
        start=self.parent.getDuration(posx)
        w,h=self.GetSize()
        end=self.parent.getDuration(posx+w)
        self.position=(start,end)
        
    def getPosition(self):
        """
        Method: getPosition()
        Created: 11.04.2005, KP
        Description: Return the starting and ending position of this item
        """       
        return self.position

        
    def onDrag(self,event):
        """
        Method: onDrag(event)
        Created: 10.02.2005, KP
        Description: Event handler for when the mouse is dragged on the item.
                     Will resize the item accordingly.
        """       
    
        if not event.Dragging():
            return
        if not self.dragMode:
            print "Click closer to the edge"
            return
        if self.dragMode == 2:
            x,y=event.GetPosition()
            x2,y2=self.GetPosition()
            x+=x2
            x-=self.parent.getLabelWidth()
            print "Setting empty space to ",x
            self.parent.setEmptySpace(x)
            #self.parent.updateLayout()
            return
        x,y=event.GetPosition()
        posx,posy=self.GetPosition()
                
        diff=x-self.beginX
        if self.width+diff<self.minSize:
            print "Not allowing < %d"%self.minSize
            return
        if diff>0 and not self.parent.itemCanResize(self.width,self.width+diff):
            print "Would go over the timescale"
            return
        self.lastdiff=diff
        self.setWidth(self.width+diff)
        self.parent.updateLayout()
        self.beginX=x
        
        
    def __getstate__(self):
        """
        Method: __getstate__
        Created: 11.04.2005, KP
        Description: Return the dict that is to be pickled to disk
        """      
        odict={}
        keys=[""]
        for key in ["position"]:
            odict[key]=self.__dict__[key]
        if self.timepoint != -1:
            odict["timepoint"]=self.timepoint
        return odict    

    def __str__(self):
        """
        Method: __str__
        Created: 05.04.2005, KP
        Description: Return string representation of self
        """  
        if self.timepoint != -1:
            desc="T%d"%self.timepoint
        else:
            desc="I"
        start,end=self.position
        return "[%s %ds:%ds]"%(desc,start,end)
        

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
        TrackItem.__init__(self,parent,text,size,**kws)
        if kws.has_key("point"):
            self.setPoint(kws["point"])
        else:
            self.setPoint((0,0,0))
        self.Bind(wx.EVT_RIGHT_DOWN,self.onRightClick)
        self.ID_CAMERA=wx.NewId()

            
        
    def getPoint(self):
        """
        Method: getPoint(self)
        Created: 14.04.2005, KP
        Description: Return the point this spline point represents
        """      
        return self.point
        
    def setPoint(self,pt):
        """
        Method: setPoint(self)
        Created: 14.04.2005, KP
        Description: Return the point this spline point represents
        """      
        self.point = pt
        
    def onRightClick(self,event):
        """
        Method: onRightClick
        Created: 20.03.2005, KP
        Description: Method that is called when the right mouse button is
                     pressed down on this item
        """      
        menu=wx.Menu()
        item = wx.MenuItem(menu,self.ID_CAMERA,"Add Camera Control")
        self.Bind(wx.EVT_MENU,self.addCameraControl,id=self.ID_CAMERA)
        menu.AppendItem(item)
        self.PopupMenu(menu,event.GetPosition())
        menu.Destroy()
        
    def addCameraControl(self,event):
        """
        Method: addCameraControl
        Created: 19.03.2005, KP
        Description: A method that adds a control handle to the visualization
                     for configuring the camera on this part of the spline
        """       
        print "Adding camera handle for ",self.itemnum
        self.parent.control.splineEditor.addCameraHandle(self.itemnum)
        
    def drawItem(self,hilight=-1):
        """
        Method: drawItem()
        Created: 19.03.2005, KP
        Description: A method that draws the item.
        """       
        self.dc.Clear()
        self.dc.BeginDrawing()
        self.dc.SetPen(wx.Pen((0,0,0)))

        # draw the body
        r,g,b=self.color
        col=wx.Colour(r,g,b)
        self.dc.SetBrush(wx.Brush(col))
        #self.dc.SetBackground(wx.Brush(wx.BLACK))
        self.dc.DrawRectangle(0,0,self.width,self.height)        

        TrackItem.drawHeader(self)
        
        r,g,b=self.headercolor
        self.dc.SetPen(wx.Pen(wx.Colour(r,g,b),2))
        self.dc.DrawLine(self.width-1,0,self.width-1,self.height)

        
        self.dc.SetTextForeground((0,0,0))
        self.dc.SetFont(wx.Font(8,wx.SWISS,wx.NORMAL,wx.NORMAL))
        l=self.parent.getSplineLength(self.itemnum)
        s=self.parent.getDuration(self.GetSize()[0])
        text=u"Length:\t%.2f\u03bcm\nDuration:\t%.2fs"%(l,s)
        self.dc.DrawText(text,5,self.labelheight+5)            
 
        if hilight != -1:
            self.hilight(hilight)
 
        
        self.dc.EndDrawing()
    
    def updateItem(self):
        """
        Method: updateItem()
        Created: 06.04.2005, KP
        Description: A method called when the item has been resized
        """     
        TrackItem.updateItem(self)  
        pos=self.parent.getSplinePoint(self.itemnum)
        self.point = pos
        
    def refresh(self):
        """
        Method: refresh()
        Created: 11.04.2005, KP
        Description: Update the item
        """       
        TrackItem.refresh(self)
        print "Setting spline point ",self.itemnum,"to ",self.point
        self.parent.setSplinePoint(self.itemnum,self.point)
        
    def __getstate__(self):
        """
        Method: __getstate__
        Created: 11.04.2005, KP
        Description: Return the dict that is to be pickled to disk
        """     
        odict=TrackItem.__getstate__(self)
        for key in ["point","itemnum"]:
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

class TransitionItem(TrackItem):
    """
    Class: TransitionItem
    Created: 13.04.2005, KP
    Description: A class representing a transition from one track to another
    """       
    def __init__(self,parent,size,**kws):
        """
        Method: __init__
        Created: 13.04.2005, KP
        Description: Initialize
        """       
        TrackItem.__init__(self,parent,"",size,**kws)
        if not "linked" in kws:
            raise "No linked item given for TransitionItem"
        self.linked = kws["linked"]
        
    def drawItem(self,hilight=-1):
        """
        Method: drawItem()
        Created: 13.04.2005, KP
        Description: A method that draws the item.
        """
        self.dc.Clear()
        self.dc.BeginDrawing()
        col=self.GetBackgroundColour()
        r,g,b=col.Red(),col.Green(),col.Blue()
        col=wx.Colour(r,g,b)
        self.dc.SetBrush(wx.Brush(col))
        self.dc.DrawRectangle(0,0,self.width,self.height)        
        self.dc.EndDrawing()
    
    def updateItem(self):
        """
        Method: updateItem()
        Created: 13.04.2005, KP
        Description: A method called when the item has been resized
        """     
        TrackItem.updateItem(self) 
        w,h=self.GetSize()
        w,y=self.linked.GetPosition()
        self.setWidth(w)
         
        
    def refresh(self):
        """
        Method: refresh()
        Created: 13.04.2005, KP
        Description: Update the item
        """       
        TrackItem.refresh(self)
        
    def __str__(self):
        """
        Method: __str__
        Created: 13.04.2005, KP
        Description: Return string representation of self
        """  
        start,end=self.position
        desc="TRANS"
        return "[%s %ds:%ds]"%(desc,start,end)      
        

class EmptyItem(TrackItem):
    """
    Class: EmptyItem
    Created: 16.04.2005, KP
    Description: An item representing empty space
    """       
    def __init__(self,parent,size,**kws):
        """
        Method: __init__
        Created: 16.04.2005, KP
        Description: Initialize
        """       
        TrackItem.__init__(self,parent,"",size,**kws)
        
    def drawItem(self,hilight=-1):
        """
        Method: drawItem()
        Created: 13.04.2005, KP
        Description: A method that draws the item.
        """
        self.dc.Clear()
        self.dc.BeginDrawing()
        col=self.GetBackgroundColour()
        r,g,b=col.Red(),col.Green(),col.Blue()
        col=wx.Colour(r,g,b)
        self.dc.SetBrush(wx.Brush(col))
        self.dc.DrawRectangle(0,0,self.width,self.height)        
        self.dc.EndDrawing()
        
    def __str__(self):
        """
        Method: __str__
        Created: 13.04.2005, KP
        Description: Return string representation of self
        """  
        start,end=self.position
        return "[E %ds:%ds]"%(start,end)      
        
