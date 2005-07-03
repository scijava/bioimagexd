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
        self.fitLater=0
        self.imagedata=None
        self.bmp=None
        self.scroll=scroll
        Logging.info("interactive panel size=",size,kw="iactivepanel")
        
        self.rubberstart=None
        x,y=size
        self.buffer = wx.EmptyBitmap(x,y)
        self.rubberend=None
        wx.ScrolledWindow.__init__(self,parent,-1,size=size,**kws)
        self.size=size

        self.scaleBar = None
        self.scaleBarWidth = 0
        self.voxelSize=(1,1,1)
        self.zoomFactor=1
        
        self.paintPreview()
        self.Bind(wx.EVT_PAINT,self.OnPaint)

        self.Bind(wx.EVT_LEFT_DOWN,self.markRubberband)
        self.Bind(wx.EVT_MOTION,self.updateRubberband)
        self.Bind(wx.EVT_LEFT_UP,self.zoomToRubberband)
        
    def drawScaleBar(self,width,voxelsize):
        """
        Method: drawScaleBar(width,voxelsize)
        Created: 05.06.2005, KP
        Description: Draw a scale bar of given size
        """    
        self.scaleBarWidth = width
        self.voxelSize = voxelsize
        Logging.info("zoom factor for scale bar=%f"%self.zoomFactor,kw="preview")
        self.scaleBar = ImageOperations.drawScaleBar(0,self.scaleBarWidth,self.voxelSize,(0,0,0),self.zoomFactor)
                
    def markRubberband(self,event):
        """
        Method: markRubberband
        Created: 24.03.2005, KP
        Description: Sets the starting position of rubber band for zooming
        """    
        if not self.zooming:
            return False
        self.rubberstart=event.GetPosition()
        
    def updateRubberband(self,event):
        """
        Method: updateRubberband
        Created: 24.03.2005, KP
        Description: Draws the rubber band to current mouse position
        """
        if not self.zooming:
            return
        if event.LeftIsDown():
            self.rubberend=event.GetPosition()
        self.updatePreview()    
        
    def zoomToRubberband(self,event):
        """
        Method: zoomToRubberband()
        Created: 24.03.2005, KP
        Description: Zooms to the rubberband
        """
        if not self.zooming:
            return
        self.zooming=0
        x1,y1=self.rubberstart
        x2,y2=self.rubberend

        self.rubberstart=None
        self.rubberend=None
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
        if self.rubberstart and self.rubberend:
            x1,y1=self.rubberstart
            x2,y2=self.rubberend
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
            dc.DrawBitmap(self.scaleBar,5,h-40,True)
        
        dc.EndDrawing()
        self.dc = None
