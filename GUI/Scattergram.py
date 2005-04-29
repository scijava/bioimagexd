#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
Unit: Scattergram
Project: BioImageXD
Created: 25.03.2005
Creator: KP
Description:

A module that displays a scattergram of two images and lets the user
select the colocalization threshold based on the plot

Modified: 25.03.2005 KP - Created the module

BioImageXD includes the following persons:

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



import ImageOperations
import sys
import wx

myEVT_THRESHOLD_CHANGED=wx.NewEventType()
EVT_THRESHOLD_CHANGED=wx.PyEventBinder(myEVT_THRESHOLD_CHANGED,1)

class ThresholdEvent(wx.PyCommandEvent):
    """
    Class: ThresholdEvent
    Created: 03.04.2005, KP
    Description: An event type that represents a lower and upper threshold change
    """
    def __init__(self,evtType,id):
        wx.PyCommandEvent.__init__(self,evtType,id)
        self.greenthreshold=(127,127)
        self.redthreshold=(127,127)
    def getGreenThreshold(self):
        return self.greenthreshold
        
    def getRedThreshold(self):
        return self.redthreshold
        
    def setGreenThreshold(self,lower,upper):
        self.greenthreshold = (lower,upper)
        
    def setRedThreshold(self,lower,upper):
        self.redthreshold = (lower,upper)

class Scattergram(wx.Panel):
    """
    Class: Scattergram
    Created: 25.03.2005, KP
    Description: A panel showing the scattergram
    """
    def __init__(self,parent,size=(256,256),**kws):
        """
        Method: __init__(parent)
        Created: 03.11.2004, KP
        Description: Initialization
        """
        wx.Panel.__init__(self,parent,-1,size=size,**kws)
        self.rubberstart=None
        self.rubberend=None
        self.size=size
        self.slice=None
        self.z = 0
        self.countVoxels = 0
        self.renew=1
        self.wholeVolume = 0
        self.dataUnit=0
        self.scatter=None
        self.buffer = wx.EmptyBitmap(256,256)
        self.Bind(wx.EVT_PAINT,self.OnPaint)

        self.Bind(wx.EVT_LEFT_DOWN,self.markRubberband)
        self.Bind(wx.EVT_MOTION,self.updateRubberband)
        self.Bind(wx.EVT_LEFT_UP,self.setThresholdToRubberband)

        self.Bind(wx.EVT_RIGHT_DOWN,self.onRightClick)
        self.ID_COUNTVOXELS=wx.NewId()
        self.ID_WHOLEVOLUME=wx.NewId()

        self.menu=wx.Menu()
        item = wx.MenuItem(self.menu,self.ID_COUNTVOXELS,"Show frequency",kind=wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU,self.setVoxelCount,id=self.ID_COUNTVOXELS)
        self.menu.AppendItem(item)
        item = wx.MenuItem(self.menu,self.ID_WHOLEVOLUME,"Show scattergram of whole volume",kind=wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU,self.setWholeVolume,id=self.ID_WHOLEVOLUME)
        self.menu.AppendItem(item)
        
    def onRightClick(self,event):
        """
        Method: onRightClick
        Created: 02.04.2005, KP
        Description: Method that is called when the right mouse button is
                     pressed down on this item
        """      
        self.PopupMenu(self.menu,event.GetPosition())
        #menu.Destroy()
        
    def setVoxelCount(self,event):
        """
        Method: setVoxelCount()
        Created: 02.04.2005, KP
        Description: Method to set on / off the voxel counting mode of scattergram
        """       
        self.countVoxels = event.Checked()
        
            
    def setWholeVolume(self,event):
        """
        Method: setWholeVolume()
        Created: 02.04.2005, KP
        Description: Method to set on / off the construction of scattergram from 
                     the whole volume
        """       
        self.wholeVolume = event.Checked()
        

    def markRubberband(self,event):
        """
        Method: markRubberband
        Created: 24.03.2005, KP
        Description: Sets the starting position of rubber band for zooming
        """    
        self.rubberstart=event.GetPosition()
        
    def updateRubberband(self,event):
        """
        Method: updateRubberband
        Created: 24.03.2005, KP
        Description: Draws the rubber band to current mouse position
        """
        if event.LeftIsDown():
            self.rubberend=event.GetPosition()
        self.update()
    
        
    def setThresholdToRubberband(self,event):
        """
        Method: zoomToRubberband()
        Created: 24.03.2005, KP
        Description: Zooms to the rubberband
        """
        x1,y1=self.rubberstart
        x2,y2=self.rubberend
        print "Using %d-%d as green and %d-%d as red range"%(x1,x2,y1,y2)
        reds=self.red.getSettings()
        greens=self.green.getSettings()
        print "reds.n=",reds.n,"greens.n=",greens.n
        greens.set("ColocalizationLowerThreshold",x1)
        greens.set("ColocalizationUpperThreshold",x2)
        reds.set("ColocalizationLowerThreshold",y1)
        reds.set("ColocalizationUpperThreshold",y2)
        
        print "In red:"
        for key in reds.settings.keys():
            if "Threshold" in key:
                print key,reds.settings[key]
        print "In green:"
        for key in greens.settings.keys():
            if "Threshold" in key:
                print key,greens.settings[key]
        evt=ThresholdEvent(myEVT_THRESHOLD_CHANGED,self.GetId())
        evt.setRedThreshold(y1,y2)
        evt.setGreenThreshold(x1,x2)
        self.GetEventHandler().ProcessEvent(evt)

        
        self.rubberstart = None
        self.rubberend = None
        self.renew=1

        self.Refresh()
        

    def setZSlice(self,z):
        """
        Method: setZSlice(z)
        Created: 24.03.2005, KP
        Description: Sets the optical slice to preview
        """    
        self.z=z
        self.renew=1
        
    def setTimepoint(self,tp):
        """
        Method: setTimepoint(tp)
        Created: 24.03.2005, KP
        Description: Sets the timepoint to preview
        """    
        self.timepoint=tp
        self.renew=1
        
        
    def setDataunit(self,dataunit):
        """
        Method: setDataunit(dataunit)
        Created: 25.03.2005, KP
        Description: Sets the dataunit the source units of which are used
                     to generate the scattergram
        """    
        self.dataUnit=dataunit
        
    def update(self):
        """
        Method: update()
        Created: 25.03.2005, KP
        Description: A method that draws the scattergram
        """          
        if self.renew and self.dataUnit:
            dataunits=self.dataUnit.getSourceDataUnits()
            red=None
            green=None

            for i in dataunits:
                col=i.getColorTransferFunction().GetColor(255)
                if col[0]>col[1]:
                    self.red=i
                elif col[1]>col[0]:
                    self.green=i
            tp=self.timepoint
            reddata=self.red.getTimePoint(tp)
            greendata=self.green.getTimePoint(tp)
            #print "Using z=",self.z,reddata,greendata
            scatter=ImageOperations.scatterPlot(reddata,greendata,self.z, self.countVoxels, self.wholeVolume)
            self.scatter=scatter.Mirror(0)
            self.renew=0
            self.paintScattergram()
            self.Refresh()

    def OnPaint(self,event):
        """
        Method: OnPaint()
        Created: 25.03.2005, KP
        Description: Does the actual blitting of the bitmap
        """
        dc=wx.BufferedPaintDC(self,self.buffer)#,self.buffer)

    def paintScattergram(self):
        """
        Method: paintScattergram
        Created: 25.03.2005, KP
        Description: Paints the scattergram
        """
#        dc = wx.PaintDC(self)
        #self.DoPrepareDC(dc)
        dc = wx.BufferedDC(wx.ClientDC(self),self.buffer)
        dc.BeginDrawing()

        if not self.scatter:
            dc.SetBackground(wx.Brush(wx.Colour(0,0,0)))
            dc.SetPen(wx.Pen(wx.Colour(0,0,0),0))
            dc.SetBrush(wx.Brush(wx.Color(0,0,0)))
            dc.DrawRectangle(0,0,self.size[0],self.size[1])
            return
        bmp=self.scatter.ConvertToBitmap()

        dc.DrawBitmap(bmp,0,0,True)
        self.bmp=bmp
        
        if self.rubberstart and self.rubberend:
            x1,y1=self.rubberstart
            x2,y2=self.rubberend
            x1,x2=min(x1,x2),max(x1,x2)
            y1,y2=min(y1,y2),max(y1,y2)
            d1,d2=abs(x2-x1),abs(y2-y1)
                
            dc.SetPen(wx.Pen(wx.Colour(255,0,0),2))
            dc.SetBrush(wx.TRANSPARENT_BRUSH)
            dc.DrawRectangle(x1,y1,d1,d2)
        dc.EndDrawing()
        dc = None
