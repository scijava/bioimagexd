# -*- coding: iso-8859-1 -*-

"""
 Unit: PreviewPanel.py
 Project: BioImageXD
 Created: 24.03.2005, KP
 Description:

 A panel that can display previews of optical slices of volume data independent
 of a VTK render window, using the tools provided by wxPython.
           
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
import InteractivePanel

class PreviewPanel(InteractivePanel.InteractivePanel):
    """
    Class: PreviewPanel
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
        Logging.info("preview panel size=",size,kw="preview")
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
        Logging.info("zoom xf=%f, yf=%f"%(self.zoomx,self.zoomy),kw="preview")
        if kws.has_key("scrollbars"):
            self.scroll=kws["scrollbars"]
        self.size=size
        self.slice=None
        self.z = 0
        self.zooming = 0
        self.scrollsize=32
        self.singleslice=0
        self.scrollTo=None
        InteractivePanel.InteractivePanel.__init__(self,parent,size=size,**kws)
        
        self.paintPreview()
        self.Bind(wx.EVT_PAINT,self.OnPaint)

    def setSingleSliceMode(self,mode):
        """
        Method: setSingleSliceMode()
        Created: 05.04.2005, KP
        Description: Sets this preview to only show a single slice
        """    
        self.singleslice = mode
                
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
        x2,y2,z=image.GetDimensions()
        if x2<x:
            x=x2
        if y2<y:
            y=y2
        Logging.info("Setting scrollbars for size %d,%d"%(x,y),kw="preview")
        self.setScrollbars(x,y)
        if x==x2 or y==y2:
            if x==x2:s="x"
            if y==y2:
                if s:s+=" and "
                s+="y"
            Logging.info("Using smaller %s for size"%s,kw="preview")            
            self.Layout()
        if self.fitLater:
            self.fitLater=0
            self.zoomToFit()
        
    def setMaximumSize(self,x,y):
        """
        Method: setMaximumSize(x,y)
        Created: 24.03.2005, KP
        Description: Sets the maximum size for this widget
        """    
        Logging.info("Maximum size for preview is (%d,%d)"%(x,y),kw="preview")
        self.maxX,self.maxY=x,y
                
        
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
        Logging.info("Setting zoom factor to ",f,kw="preview")
        self.zoomFactor=f
        self.updateAnnotations()
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
            if w!=x or h!=y:
                Logging.info("Determining zoom factor from (%d,%d) to (%d,%d)"%(x,y,w,h),kw="preview")
                self.setZoomFactor(ImageOperations.getZoomFactor(x,y,w,h))
        else:
            Logging.info("Will zoom to fit later",kw="preview")
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
            Logging.info("ENABLING SCROLLING, size=(%d,%d)"%(xdim,ydim),kw="preview")
            self.SetVirtualSize((xdim,ydim))
            self.SetScrollRate(self.scrollsize,self.scrollsize)
            

    def zoomObject(self):
        """
        Method: startZoomObject()
        Created: 24.03.2005, KP
        Description: Sets a flag indicating that the user wishes to zoom in
                     by drawing a "rubber band"
        """
        Logging.info("Will zoom",kw="preview")
        self.startRubberband()
        self.zooming=1


    def updatePreview(self):
        """
        Method: updatePreview()
        Created: 24.03.2005, KP
        Description: Updates the viewed image
        """
        z=self.z
        if self.singleslice:
            Logging.info("Single slice, will use z=0",kw="preview")
            z=0
        if not self.imagedata:
            Logging.info("No imagedata to preview",kw="preview")
            return
        else:
            self.slice=ImageOperations.vtkImageDataToWxImage(self.imagedata,z)
        Logging.info("Painting preview",kw="preview")
        self.paintPreview()
        wx.GetApp().Yield(1)
        self.updateScrolling()
        
    def updateScrolling(self,event=None):
        """
        Method: updateScrolling
        Created: 24.03.2005, KP
        Description: Updates the scroll settings
        """
        if not self.bmp:
            return
        if self.bmp:
            Logging.info("Updating scroll settings (size %d,%d)"%(self.bmp.GetWidth(),self.bmp.GetHeight()),kw="preview")
            self.setScrollbars(self.bmp.GetWidth()*self.zoomx,self.bmp.GetHeight()*self.zoomy)       
        if self.scrollTo:
            x,y=self.scrollTo
            Logging.info("Scrolling to %d,%d"%(x,y),kw="preview")
            sx=int(x/self.scrollsize)
            sy=int(y/self.scrollsize)
            #sx=x/self.scrollsize
            #sy=y/self.scrollsize
            self.Scroll(sx,sy)
            self.scrollTo=None

    def paintPreview(self):
        """
        Method: paintPreview()
        Created: 24.03.2005, KP
        Description: Paints the image to a DC
        """

        if not self.slice:
            Logging.info("Black preview",kw="preview")
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
        Logging.info("Zoom factor for painting =",self.zoomFactor,kw="preview")
        if self.zoomFactor!=1:
            bmp=ImageOperations.zoomImageByFactor(self.slice,self.zoomFactor)
            w,h=bmp.GetWidth(),bmp.GetHeight()
            Logging.info("Setting scrollbars (%d,%d) because of zooming"%(w,h),kw="preview")
            
            self.setScrollbars(w,h)
        
        if self.zoomx!=1 or self.zoomy!=1:
            w,h=bmp.GetWidth(),bmp.GetHeight()
            w*=self.zoomx
            h*=self.zoomy
            Logging.info("Scaling to ",w,h,kw="preview")
            bmp.Rescale(w,h)
            
            self.setScrollbars(w,h)
        
        bmp=bmp.ConvertToBitmap()
        dc = self.dc = wx.BufferedDC(wx.ClientDC(self),self.buffer)
        dc.BeginDrawing()

        dc.DrawBitmap(bmp,0,0,True)
        self.bmp=self.buffer
        
        InteractivePanel.InteractivePanel.paintPreview(self)

        
        dc.EndDrawing()
        self.dc = None
