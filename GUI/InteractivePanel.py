# -*- coding: iso-8859-1 -*-

"""
 Unit: InteractivePanel
 Project: BioImageXD
 Created: 24.03.2005, KP
 Description:

 A panel that can select regions of interest, draw annotations, etc.
         
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
__version__ = "$Revision: 1.9 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import wx    
from wx.lib.statbmp  import GenStaticBitmap as StaticBitmap
import ImageOperations
import Logging

class InteractivePanel(wx.ScrolledWindow):
    """
    Class: InteractivePanel
    Created: 03.07.2005, KP
    Description: A panel that can be used to select regions of interest, drawn
                 annotations on etc.
    """
    def __init__(self,parent,size=(512,512),scroll=0,**kws):
        """
        Method: __init__(parent)
        Created: 24.03.2005, KP
        Description: Initialization
        """    
        self.action=0
        self.imagedata=None
        self.bmp=None
        self.scroll=scroll
        Logging.info("interactive panel size=",size,kw="iactivepanel")
        
        self.actionstart=None
        self.actionend=None
        self.scalepos=None
        
        x,y=size
        self.buffer = wx.EmptyBitmap(x,y)
        wx.ScrolledWindow.__init__(self,parent,-1,size=size)
        self.size=size

        self.scaleBar = None
        self.scaleBarWidth = 0
        self.voxelSize=(1,1,1)
        self.zoomFactor=1
        
        self.paintPreview()
        self.Bind(wx.EVT_PAINT,self.OnPaint)

        self.Bind(wx.EVT_LEFT_DOWN,self.markActionStart)
        self.Bind(wx.EVT_MOTION,self.updateActionEnd)
        self.Bind(wx.EVT_LEFT_UP,self.executeAction)
        
    def executeAction(self,event):
        """
        Method: executeAction
        Created: 03.07.2005, KP
        Description: Call the right callback depending on what we're doing
        """    
        if self.action==0:
            self.zoomToRubberband(event)
        elif self.action==1:
            self.updateScaleBar(event)
        
    def drawScaleBar(self,width,voxelsize):
        """
        Method: drawScaleBar(width,voxelsize)
        Created: 05.06.2005, KP
        Description: Gets the scale bar information
        """    
        self.scaleBarWidth = width
        self.voxelSize = voxelsize
        Logging.info("zoom factor for scale bar=%f"%self.zoomFactor,kw="preview")
        
    def updateScaleBar(self,event=None):
        """
        Method: updateScaleBar
        Created: 05.06.2005, KP
        Description: Draw a scale bar of given size
        """
        x0,y0=self.scalePos
        x1,y1=self.actionend
        xd=x1-x0
        yd=y1-y0
        vertical=0
        diff=xd
        if yd>xd:
            vertical=1
            diff=yd
        
        self.scaleBar = ImageOperations.drawScaleBar(widthPx=diff,
            widthMicro=0,voxelSize=self.voxelSize,
            bgColor=(0,0,0),
            scaleFactor=self.zoomFactor,
            vertical=vertical,
            round=1)
                
    def markActionStart(self,event):
        """
        Method: markActionStart
        Created: 24.03.2005, KP
        Description: Sets the starting position of rubber band for zooming
        """    
        if not self.action:
            return False
        self.actionstart=event.GetPosition()
        if self.action==2:
            self.scalePos=self.actionstart
        
    def updateActionEnd(self,event):
        """
        Method: updateActionEnd
        Created: 24.03.2005, KP
        Description: Draws the rubber band to current mouse position
        """
        if not self.action:
            return
        if event.LeftIsDown():
            self.actionend=event.GetPosition()
            if self.action==2:
                self.updateScaleBar(event)    
        self.updatePreview()
        
    def startRubberband(self):
        """
        Method: startRubberband()
        Created: 03.07.2005
        Description: Start rubber band
        """
        self.action=1
        
    def startScale(self):
        """
        Method: startRubberband()
        Created: 03.07.2005
        Description: Start rubber band
        """
        self.action=2
        
    def zoomToRubberband(self,event):
        """
        Method: zoomToRubberband()
        Created: 24.03.2005, KP
        Description: Zooms to the rubberband
        """ 
        if not (self.rubberBanding or self.scaleDrawing):
            Logging.info("Not drawing rubberband,returning",kw="iactivepanel")
            return
        self.rubberBanding=0
        x1,y1=self.actionstart
        x2,y2=self.actionend
        Logging.info("Zooming to rubberband defined by (%d,%d),(%d,%d)"%(x1,y1,x2,y2),kw="iactivepanel")
        
        self.actionstart=None
        self.actionend=None
        x1,x2=min(x1,x2),max(x1,x2)
        y1,y2=min(y1,y2),max(y1,y2)
        
        if self.zoomFactor!=1:
            f=float(self.zoomFactor)
            x1,x2,y1,y2=int(x1/f),int(x2/f),int(y1/f),int(y2/f)
            x1/=float(self.zoomx)
            x2/=float(self.zoomx)
            y1/=float(self.zoomy)
            y2/=float(self.zoomy)
            
        
        x1,y1=self.getScrolledXY(x1,y1)
        x2,y2=self.getScrolledXY(x2,y2)

        w,h=self.size
        self.setZoomFactor(ImageOperations.getZoomFactor((x2-x1),(y2-y1),w,h))
        
        self.scrollTo=(self.zoomFactor*x1*self.zoomx,self.zoomFactor*y1*self.zoomy)
        
        self.updatePreview()
        
    def setMaximumSize(self,x,y):
        """
        Method: setMaximumSize(x,y)
        Created: 24.03.2005, KP
        Description: Sets the maximum size for this widget
        """    
        Logging.info("Maximum size for preview is (%d,%d)"%(x,y),kw="preview")
        self.maxX,self.maxY=x,y

    def OnPaint(self,event):
        """
        Method: paintPreview()
        Created: 28.04.2005, KP
        Description: Does the actual blitting of the bitmap
        """
        dc=wx.BufferedPaintDC(self,self.buffer)#,self.buffer)


    def paintPreview(self):
        """
        Method: paintPreview()
        Created: 24.03.2005, KP
        Description: Paints the image to a DC
        """
        dc=self.dc
        bmp=self.bmp
        
        w,h=bmp.GetWidth(),bmp.GetHeight()
        
        w*=self.zoomx
        h*=self.zoomy
        if self.action==1:
            if self.actionstart and self.actionend:
                x1,y1=self.actionstart
                x2,y2=self.actionend
                x1,x2=min(x1,x2),max(x1,x2)
                y1,y2=min(y1,y2),max(y1,y2)
                d1,d2=abs(x2-x1),abs(y2-y1)
    
                if self.zoomFactor!=1:
                    f=self.zoomFactor
                    x1,y1=self.getScrolledXY(x1,y1)
                    x1,y1=int(f*x1),int(f*y1)
                    
                dc.SetPen(wx.Pen(wx.Colour(255,0,0),2))
                dc.SetBrush(wx.TRANSPARENT_BRUSH)
                dc.DrawRectangle(x1,y1,d1,d2)
        if self.scaleBar:
            x,y=self.scalePos
            dc.DrawBitmap(self.scaleBar,x,y,True)
        
        dc.EndDrawing()
        self.dc = None
