# -*- coding: iso-8859-1 -*-

"""
 Unit: WxPreviewPanel.py
 Project: BioImageXD
 Created: 24.03.2005, KP
 Description:

 A panel that can display previews of optical slices of volume data independent
 of a VTK render window,using the tools provided by wxPython.
 
 Modified 24.03.2005 KP - Created the class
          
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

class WxPreviewPanel(wx.ScrolledWindow):
    """
    Class: WxPreviewPanel
    Created: 24.03.2005, KP
    Description: A panel that can be used to preview volume data one slice at a time
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
        print "size=",size
        
        self.rubberstart=None
        self.yielding=0
        x,y=size
        self.buffer = wx.EmptyBitmap(x,y)
        self.rubberend=None
        if kws.has_key("zoomx"):
            self.zoomx=kws["zoomx"]
            del kws["zoomx"]
        if kws.has_key("zoomy"):
            self.zoomy=kws["zoomy"]
            del kws["zoomy"]
        print "zoomx=",self.zoomx
        print "zoomy=",self.zoomy
        wx.ScrolledWindow.__init__(self,parent,-1,size=size,**kws)
        if kws.has_key("scrollbars"):
            self.scroll=kws["scrollbars"]
        self.size=size
        self.slice=None
        self.z = 0
        self.zooming = 0
        self.scrollsize=32
        self.zoomFactor=1
        self.singleslice=0
        self.scrollTo=None
        self.paintPreview()
        self.Bind(wx.EVT_PAINT,self.OnPaint)

        self.Bind(wx.EVT_LEFT_DOWN,self.markRubberband)
        self.Bind(wx.EVT_MOTION,self.updateRubberband)
        self.Bind(wx.EVT_LEFT_UP,self.zoomToRubberband)

    def setSingleSliceMode(self,mode):
        """
        Method: setSingleSliceMode()
        Created: 05.04.2005, KP
        Description: Sets this preview to only show a single slice
        """    
        self.singleslice = mode
        
        
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
        
    def setZSlice(self,z):
        """
        Method: setZSlice(z)
        Created: 24.03.2005, KP
        Description: Sets the optical slice to preview
        """    
        self.z=z
        
    def setImage(self,image):
        """
        Method: setImage(image)
        Created: 24.03.2005, KP
        Description: Sets the image to display
        """    
        self.imagedata=image
        x,y=self.size
        self.setScrollbars(x,y)
        if self.fitLater:
            self.fitLater=0
            self.zoomToFit()
        
    def setMaximumSize(self,x,y):
        """
        Method: setMaximumSize(x,y)
        Created: 24.03.2005, KP
        Description: Sets the maximum size for this widget
        """    
        self.maxX,self.maxY=x,y
                
    def getScrolledXY(self,x,y):
        """
        Method: getScrolledXY(x,y)
        Created: 24.03.2005, KP
        Description: Returns the x and y coordinates moved by the 
                     x and y scroll offset
        """
        tpl=self.CalcUnscrolledPosition(x,y)
        if self.zoomFactor==1:
            return tpl
        else:
            return [int(float(x)/self.zoomFactor) for x in tpl]
        
    def resetScroll(self):
        """
        Method: resetScroll()
        Created: 24.03.2005, KP
        Description: Sets the scrollbars to their initial values
        """    
        self.Scroll(0,0)
        
    def setZoomFactor(self,f):
        """
        Method: setZoomFactor
        Created: 24.03.2005, KP
        Description: Sets the factor by which the image should be zoomed
        """
        if f>10:
            f=10
        self.zoomFactor=f
        self.Scroll(0,0)
        
    def zoomToFit(self):
        """
        Method: zoomToFit()
        Created: 25.03.2005, KP
        Description: Sets the zoom factor so that the image will fit into the screen
        """
        if self.imagedata:
            w,h=self.size
            x,y,z=self.imagedata.GetDimensions()
            if x>w or h>y:
                self.setZoomFactor(ImageOperations.getZoomFactor(x,y,w,h))
        else:
            self.fitLater=1


    def setScrollbars(self,xdim,ydim):
        """
        Method: setScrollbars(x,y)
        Created: 24.03.2005, KP
        Description: Configures scroll bar behavior depending on the
                     size of the dataset, which is given as parameters.
        """        
        w,h=self.buffer.GetWidth(),self.buffer.GetHeight()
        
        if w!=xdim or h!=ydim:
            self.buffer = wx.EmptyBitmap(xdim,ydim)
            
        if self.scroll:
            self.SetVirtualSize((xdim,ydim))
            self.SetScrollRate(self.scrollsize,self.scrollsize)


    def startZoom(self):
        """
        Method: startZoomObject()
        Created: 24.03.2005, KP
        Description: Sets a flag indicating that the user wishes to zoom in
                     by drawing a "rubber band"
        """
        print "Zooming..."
        self.zooming=1


    def updatePreview(self):
        """
        Method: updatePreview()
        Created: 24.03.2005, KP
        Description: Updates the viewed image
        """
        z=self.z
        if self.singleslice:
            print "Using z = 0"
            z=0
        self.slice=ImageOperations.vtkImageDataToWxImage(self.imagedata,z)
        self.paintPreview()
        wx.GetApp().Yield(1)
        self.updateScrolling()
        
    def updateScrolling(self,event=None):
        """
        Method: updateScrolling
        Created: 24.03.2005, KP
        Description: Updates the scroll settings
        """
        if self.bmp:
            self.setScrollbars(self.bmp.GetWidth()*self.zoomx,self.bmp.GetHeight()*self.zoomy)       
        if self.scrollTo:
            x,y=self.scrollTo
            print "Scrolling to ",x,y
            sx=int(x/self.scrollsize)
            sy=int(y/self.scrollsize)
            #sx=x/self.scrollsize
            #sy=y/self.scrollsize
            self.Scroll(sx,sy)
            self.scrollTo=None

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

        if not self.slice:
            print "Drawing black"
            dc = self.dc = wx.BufferedDC(wx.ClientDC(self),self.buffer)
            dc.BeginDrawing()
            dc.SetBackground(wx.Brush(wx.Colour(0,0,0)))
            dc.SetPen(wx.Pen(wx.Colour(0,0,0),0))
            dc.SetBrush(wx.Brush(wx.Color(0,0,0)))
            dc.DrawRectangle(0,0,self.size[0],self.size[1])
            dc.EndDrawing()
            self.dc = None
            return
        bmp=self.slice

        if self.zoomFactor!=1:
            bmp=ImageOperations.zoomImageByFactor(self.slice,self.zoomFactor)
            w,h=bmp.GetWidth(),bmp.GetHeight()
            print "Setting scrollbars due to zoomfactor"
            
            self.setScrollbars(w,h)
        
        if self.zoomx!=1 or self.zoomy!=1:
            w,h=bmp.GetWidth(),bmp.GetHeight()
            w*=self.zoomx
            h*=self.zoomy
            print "Scaling zoom x,y=",self.zoomx,self.zoomy,w,h
            bmp.Rescale(w,h)
            
            self.setScrollbars(w,h)
        
        bmp=bmp.ConvertToBitmap()
        dc = self.dc = wx.BufferedDC(wx.ClientDC(self),self.buffer)
        dc.BeginDrawing()

        dc.DrawBitmap(bmp,0,0,True)
        self.bmp=bmp

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
        
        dc.EndDrawing()
        self.dc = None
