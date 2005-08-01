#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
Unit: Scatterplot
Project: BioImageXD
Created: 25.03.2005, KP
Description:

A module that displays a scatterplot and allows the user
select the colocalization threshold based on the plot. Uses the information
acquired from vtkImageAutoThresholdColocalization. For a scattergram calculated
from two images, see Scattergram.py

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
__author__ = "BioImageXD Project <http://www.bioimagexd.org/>"
__version__ = "$Revision: 1.22 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

#from enthought.tvtk import messenger
import messenger
import InteractivePanel
import vtk
import ImageOperations
import Logging
import sys
import wx

from GUI import Events

class Scatterplot(InteractivePanel.InteractivePanel):
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
        #wx.Panel.__init__(self,parent,-1,size=size,**kws)
        self.size=size
        self.slice=None
        self.z = 0
        self.timepoint=0
        self.zoomx=1
        self.zoomy=1
        self.action = 5
        self.countVoxels = 1
        self.renew=1
        self.wholeVolume = 1
        self.logarithmic=1
        self.scatter=None
        self.scatterplot=None
        
        self.buffer = wx.EmptyBitmap(256,256)
        InteractivePanel.InteractivePanel.__init__(self,parent,size=size,**kws);
        self.action=5
        self.Bind(wx.EVT_PAINT,self.OnPaint)
        #self.Bind(wx.EVT_LEFT_UP,self.setThreshold)

        self.Bind(wx.EVT_RIGHT_DOWN,self.onRightClick)
        self.ID_COUNTVOXELS=wx.NewId()
        self.ID_WHOLEVOLUME=wx.NewId()
        self.ID_LOGARITHMIC=wx.NewId()
        self.menu=wx.Menu()
        
        messenger.connect(None,"threshold_changed",self.updatePreview)
        
#        item = wx.MenuItem(self.menu,self.ID_COUNTVOXELS,"Show frequency",kind=wx.ITEM_CHECK)
#        self.Bind(wx.EVT_MENU,self.setVoxelCount,id=self.ID_COUNTVOXELS)
#        self.menu.AppendItem(item)
#        self.menu.Check(self.ID_COUNTVOXELS,1)
#        item = wx.MenuItem(self.menu,self.ID_WHOLEVOLUME,"Show scattergram of whole volume",kind=wx.ITEM_CHECK)
#        self.Bind(wx.EVT_MENU,self.setWholeVolume,id=self.ID_WHOLEVOLUME)
#        self.menu.AppendItem(item)
#        self.menu.Check(self.ID_WHOLEVOLUME,1)
        item = wx.MenuItem(self.menu,self.ID_LOGARITHMIC,"Logarithmic scale",kind=wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU,self.onSetLogarithmic,id=self.ID_LOGARITHMIC)
        self.menu.AppendItem(item)
        self.menu.Check(self.ID_LOGARITHMIC,1)    

        self.Bind(wx.EVT_LEFT_DOWN,self.markActionStart)
        self.Bind(wx.EVT_MOTION,self.updateActionEnd)
        self.Bind(wx.EVT_LEFT_UP,self.setThreshold)
        self.actionstart=None
        self.actionend=None
        
    def onRightClick(self,event):
        """
        Method: onRightClick
        Created: 02.04.2005, KP
        Description: Method that is called when the right mouse button is
                     pressed down on this item
        """      
        self.PopupMenu(self.menu,event.GetPosition())
        #menu.Destroy()
        
    def onSetLogarithmic(self,evt):
        """
        Method: onSetLogarithmic
        Created: 12.07.2005, KP
        Description: Set the scale to logarithmic
        """
        self.logarithmic=not self.logarithmic
        self.menu.Check(self.ID_LOGARITHMIC,self.logarithmic)
        self.renew=1
        self.updatePreview()
        self.Refresh()
        
        
    def markActionStart(self,event):
        """
        Method: markActionStart
        Created: 12.07.2005, KP
        Description: Sets the starting position of rubber band for zooming
        """    
        pos=event.GetPosition()
        x,y=pos
        y=255-y
        if x>255:x=255
        if y>255:y=255
        if x<0:x=0
        if y<0:y=0        
        self.actionstart=(x,y)
            
    def updateActionEnd(self,event):
        """
        Method: updateActionEnd
        Created: 12.07.2005, KP
        Description: Draws the rubber band to current mouse pos       
        """
        if event.LeftIsDown():
            x,y=event.GetPosition()
            y=255-y
            if x>255:x=255
            if y>255:y=255
            if x<0:x=0
            if y<0:y=0            
            self.actionend=(x,y)
            self.updatePreview()
            
        
    def setDataUnit(self,dataUnit):
        """
        Method: setDataUnit(self,dataUnit)
        Created: 04.07.2005, KP
        Description: Sets the data unit that is displayed
        """            
        InteractivePanel.InteractivePanel.setDataUnit(self,dataUnit)
        self.sources=dataUnit.getSourceDataUnits()
        self.settings =self.sources[0].getSettings()
        
    def setVoxelCount(self,event):
        """
        Method: setVoxelCount()
        Created: 02.04.2005, KP
        Description: Method to set on / off the voxel counting mode of scattergram
        """       
        self.countVoxels = event.Checked()
        self.renew=1
        self.updatePreview()
        
            
    def setWholeVolume(self,event):
        """
        Method: setWholeVolume()
        Created: 02.04.2005, KP
        Description: Method to set on / off the construction of scattergram from 
                     the whole volume
        """       
        self.wholeVolume = event.Checked()
        self.renew=1
        self.updatePreview()
        
    def setThreshold(self,event=None):
        """
        Method: setThreshold(event)
        Created: 24.03.2005, KP
        Description: Sets the thresholds based on user's selection
        """
        x1,y1=self.actionstart
        x2,y2=self.actionend
        if x2<x1:
            x1,x2=x2,x1
        if y2<y1:
            y1,y2=y2,y1
        
        print "Using %d-%d as green and %d-%d as red range"%(x1,x2,y1,y2)
        reds=self.sources[0].getSettings()
        greens=self.sources[1].getSettings()
        
#        print "reds.n=",reds.n,"greens.n=",greens.n
        greens.set("ColocalizationLowerThreshold",y1)
        greens.set("ColocalizationUpperThreshold",y2)
        reds.set("ColocalizationLowerThreshold",x1)
        reds.set("ColocalizationUpperThreshold",x2)

        messenger.send(None,"threshold_changed",(y1,y2),(x1,x2))
        messenger.send(None,"data_changed",1)

        self.renew=1
        self.updatePreview()

        #self.Refresh()
        self.actionstart = None
        self.actionend = None
        
    def setTimepoint(self,tp):
        """
        Method: setTimepoint
        Created: 11.07.2005, KP
        Description: Sets the timepoint to be shown
        """    
        self.timepoint=tp
        
    def setZSlice(self,z):
        """
        Method: setTimepoint
        Created: 11.07.2005, KP
        Description: Sets the timepoint to be shown
        """    
        self.z=z
        
    def setScatterplot(self,plot):
        """
        Method: setScatterplot(plot)
        Created: 11.07.2005, KP
        Description: Sets the scatterplot as vtkImageData
        """    
        self.scatterplot=plot
        #print "Got coloc=",coloc
        x0,x1=self.scatterplot.GetScalarRange()
        Logging.info("Scalar range of scatterplot=",x0,x1,kw="processing")
        self.ctf=ImageOperations.loadLUT("LUT/rainbow2.lut",None,(x0,x1))
        print self.ctf
        
    def updatePreview(self,*args):
        """
        Method: updatePreview()
        Created: 25.03.2005, KP
        Description: A method that draws the scattergram
        """
        if self.renew and self.dataUnit:
            t1=self.sources[0].getTimePoint(self.timepoint)
            t2=self.sources[1].getTimePoint(self.timepoint)            
            self.scatter = ImageOperations.scatterPlot(t1,t2,-1,self.countVoxels,self.wholeVolume,logarithmic=self.logarithmic)
            self.scatter=self.scatter.Mirror(0)
            self.renew=0
        self.paintPreview()
        wx.GetApp().Yield(1)
        # Commented for windows' sake
        #self.Refresh()

    def OnPaint(self,event):
        """
        Method: OnPaint()
        Created: 25.03.2005, KP
        Description: Does the actual blitting of the bitmap
        """
        dc=wx.BufferedPaintDC(self,self.buffer)#,self.buffer)

    def paintPreview(self):
        """
        Method: paintPreview
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

        lower1=int(self.sources[0].getSettings().get("ColocalizationLowerThreshold"))
        lower2=int(self.sources[1].getSettings().get("ColocalizationLowerThreshold"))           
        upper1=int(self.sources[0].getSettings().get("ColocalizationUpperThreshold"))
        upper2=int(self.sources[1].getSettings().get("ColocalizationUpperThreshold"))

        if self.actionstart and self.actionend:
            x1,y1=self.actionstart
            x2,y2=self.actionend
            if x2<x1:
                x1,x2=x2,x1
            if y2<y1:
                y1,y2=y2,y1
            lower1,upper1=x1,x2
            lower2,upper2=y1,y2

        bmp=self.scatter.ConvertToBitmap()
    
        dc.DrawBitmap(bmp,0,0,True)
        self.bmp=self.buffer

        slope=self.settings.get("Slope")
        intercept=self.settings.get("Intercept")
        dc.SetPen(wx.Pen(wx.Colour(255,255,255),1))
        if slope and intercept:
            Logging.info("slope=",slope,"intercept=",intercept,kw="dataunit")
            x=255
            y=255-(255*slope+intercept)
            
            dc.DrawLine(0,255,x,y)
        
        # These are the threshold lines
        dc.DrawLine(lower1,0,lower1,255)
        dc.DrawLine(0,255-lower2,255,255-lower2)
        dc.DrawLine(upper1,0,upper1,255)
        dc.DrawLine(0,255-upper2,255,255-upper2)
        
        dc.SetPen(wx.Pen(wx.Colour(255,255,0),2))
        # vertical line 
        dc.DrawLine(lower1,255-upper2,lower1,255-lower2)
        # horizontal line
        dc.DrawLine(lower1,255-lower2,upper1,255-lower2)
        # vertical line 2 
        dc.DrawLine(upper1,255-upper2,upper1,255-lower2)
        # horizontal line 2
        dc.DrawLine(lower1,255-upper2,upper1,255-upper2)
        
        overlay=ImageOperations.getOverlay(upper1-lower1,upper2-lower2,(255,255,0),64)
        overlay=overlay.ConvertToBitmap()
        dc.DrawBitmap(overlay,lower1,255-upper2,1)
        
        
        self.dc=dc
#        InteractivePanel.InteractivePanel.paintPreview(self)
        del self.dc
        dc.EndDrawing()
        dc = None
