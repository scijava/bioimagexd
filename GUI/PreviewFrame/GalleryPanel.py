# -*- coding: iso-8859-1 -*-

"""
 Unit: GalleryPanel
 Project: BioImageXD
 Created: 23.05.2005, KP
 Description:

 A panel that can display previews of all the optical slices of
 volume data independent of a VTK render window,using the tools provided by wxPython.
 
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
import vtk

import math
import Logging
import InteractivePanel

class GalleryPanel(InteractivePanel.InteractivePanel):
    """
    Class: GalleryPanel
    Created: 23.05.2005, KP
    Description: A panel that can be used to preview volume data several slice at a time
    """
    def __init__(self,parent,visualizer,size=(512,512),**kws):
        """
        Method: __init__(parent)
        Created: 24.03.2005, KP
        Description: Initialization
        """    
        self.imagedata=None
        self.visualizer=visualizer
        self.bmp=None
        self.bgcolor=(127,127,127)
        Logging.info("Size of gallery =",size,kw="preview")
        self.enabled=1
        self.slices=[]
        self.zoomx=1
        self.zoomy=1
        self.zoomToFitFlag=0
        if kws.has_key("slicesize"):
            self.sliceSize=kws["slicesize"]
        else:
            self.sliceSize=(128,128)
        self.originalSliceSize=self.sliceSize
        
        x,y=size
        self.paintSize=size
        self.buffer = wx.EmptyBitmap(x,y)
        
        #wx.ScrolledWindow.__init__(self,parent,-1,size=size,**kws)
        InteractivePanel.InteractivePanel.__init__(self,parent,size=size,**kws)
        
        self.size=size
        self.sizeChanged=0
        self.rows=0
        self.cols=0
        self.scrollsize=32
        self.scrollTo=None
        self.drawableRects=[]
        self.dataUnit=None
        self.slice=0
        
        self.voxelSize=(0,0,0)
        self.showTimepoints=0
        self.timepoint=0
        self.paintPreview()
        self.Bind(wx.EVT_PAINT,self.OnPaint)
        self.Bind(wx.EVT_SIZE,self.onSize)
        
    def setShowTimepoints(self,showtps,slice):
        """
        Method: setShowTimepoints
        Created: 21.07.2005, KP
        Description: Configure whether to show z slices or timepoints
        """    
        self.slice=slice
        self.showTimepoints=showtps
        self.setSlice(slice)
        self.updatePreview()
        self.Refresh()
        
    def getDrawableRectangles(self):
        """
        Method: getDrawableRectangles()
        Created: 04.07.2005, KP
        Description: Return the rectangles can be drawn on as four-tuples
        """    
        return self.drawableRects
        
    def zoomToFit(self):
        """
        Method: zoomToFit()
        Created: 05.06.2005, KP
        Description: Zoom the dataset to fit the available screen space
        """
        self.zoomToFitFlag=1
        self.calculateBuffer()
        
    def setZoomFactor(self,factor):
        """
        Method: setZoomFactor(factor)
        Created: 05.06.2005, KP
        Description: Set the factor by which the image is zoomed
        """
        self.zoomFactor=factor
        self.zoomToFitFlag=0
        self.updateAnnotations()
        x,y=self.originalSliceSize
        x*=factor
        y*=factor
        

        self.sliceSize=(x,y)
        self.slices=[]
        self.updatePreview()
        self.Refresh()
        
    def setBackground(self,r,g,b):
        """
        Method: setBackground(r,g,b)
        Created: 24.05.2005, KP
        Description: Set the background color
        """        
        self.bgcolor=(r,g,b)

    def onSize(self,event):
        """
        Method: onSize
        Created: 23.05.2005, KP
        Description: Size event handler
        """    
        InteractivePanel.InteractivePanel.OnSize(self,event)
        #self.gallerySize=event.GetSize()
        #Logging.info("Gallery size changed to ",self.gallerySize,kw="preview")
        self.sizeChanged=1

    def setDataUnit(self,dataunit):
        """
        Method: setDataUnit(dataunit)
        Created: 23.05.2005, KP
        Description: Sets the dataunit to display
        """    
        self.dataUnit=dataunit
        
        self.dims=dataunit.getDimensions()
        self.voxelSize=dataunit.getVoxelSize()
        InteractivePanel.InteractivePanel.setDataUnit(self,dataunit)
        self.setTimepoint(self.timepoint)
        x,y=self.paintSize
        self.setScrollbars(x,y)
        #self.imagedata=image
        
        
    def setTimepoint(self,timepoint):
        """
        Method: setTimepoint(tp)
        Created: 23.05.2005, KP
        Description: Sets the timepoint to display
        """    
        #self.scrollTo=self.getScrolledXY(0,0)
        #self.resetScroll()
        self.timepoint=timepoint
        # if we're showing one slice of each timepoint
        # instead of each slice of one timepoint, call the
        # appropriate function
        if self.showTimepoints:
            return self.setSlice(self.slice)
        if self.visualizer.getProcessedMode():
            image=self.dataUnit.doPreview(-2,1,self.timepoint)
            ctf = self.dataUnit.getSourceDataUnits()[0].getColorTransferFunction()
            Logging.info("Using ",image,"for gallery",kw="preview")
        else:
            image=self.dataUnit.getTimePoint(timepoint)
            ctf=self.dataUnit.getColorTransferFunction()

        self.imagedata = ImageOperations.imageDataTo3Component(image,ctf)
        
        x,y,z=self.imagedata.GetDimensions()
        
        self.slices=[]
        for i in range(z):
            slice=ImageOperations.vtkImageDataToWxImage(self.imagedata,i)    
            self.slices.append(slice)
        self.calculateBuffer()
        self.updatePreview()
        
        
    def setSlice(self,slice):
        """
        Method: setSlice(tp)
        Created: 21.07.2005, KP
        Description: Sets the slice to show
        """    
        self.slice=slice
        # if we're showing each slice of one timepoint
        # instead of one slice of each timepoint, call the
        # appropriate function
        if not self.showTimepoints:
            return self.setTimepoint(self.timepoint)
        count=self.dataUnit.getLength()
        self.slices=[]
        for tp in range(0,count):
            if self.visualizer.getProcessedMode():
                image=self.dataUnit.doPreview(self.slice,1,tp)
                ctf = self.dataUnit.getSourceDataUnits()[0].getColorTransferFunction()
                Logging.info("Using ",image,"for gallery",kw="preview")
            else:
                image=self.dataUnit.getTimePoint(tp)
                image=ImageOperations.getSlice(image,self.slice)
                ctf=self.dataUnit.getColorTransferFunction()
    
            self.imagedata = ImageOperations.imageDataTo3Component(image,ctf)
            
            slice=ImageOperations.vtkImageDataToWxImage(self.imagedata,self.slice)
            self.slices.append(slice)
            
        self.calculateBuffer()
        
        self.updatePreview()


    def calculateBuffer(self):
        """
        Method: calculateBuffer()
        Created: 23.05.2005, KP
        Description: Calculate the drawing buffer required
        """    
        if not self.imagedata:
            return
        x,y,z=self.imagedata.GetDimensions()
        maxX=self.maxX
        maxY=self.maxY
        n=z
        if len(self.slices)>z:
            Logging.info("Using number of slices (%d) instead of z dim (%d)"%(len(self.slices),z),kw="preview")
            n=len(self.slices)

        if self.maxSizeX>maxX:maxX=self.maxSizeX
        if self.maxSizeY>maxY:maxY=self.maxSizeY
        if not self.zoomToFitFlag:
            w,h=self.sliceSize
            Logging.info("maxX=",maxX,"maxY=",maxY,kw="preview")
            xreq=maxX//(w+6)
            if not xreq:xreq=1
                
            yreq=math.ceil(n/float(xreq))
        else:
            sizes=range(0,1024,8)
            Logging.info("Searching for right gallery size...",kw="preview")
            for j in range(len(sizes)-1,0,-1):
                i=sizes[j]
                nx=maxX//(i+6)
                if not nx:continue
                ny=math.ceil(n/float(nx))
                if ny*i <maxY and (nx*ny)>n:
                    Logging.info("Size %dx%d which takes %dx%d squares fits into %dx%d"%(i,i,nx,ny,maxX,maxY),kw="preview")
                    w=i
                    h=i
                    self.sliceSize=(w,h)
                    xreq=nx
                    yreq=ny
                    break
                else:
                    pass
                    #Logging.info("%dx%d doesn't fit"%(i,i),kw="preview")
        Logging.info("Need %d x %d grid to show the dataset"%(xreq,yreq),kw="preview")
        

        # allow for 3 pixel border
        x=12+(xreq)*(w+6)
        y=12+(yreq)*(h+6)
        
        self.rows=yreq
        self.cols=xreq
        if self.paintSize!=(x,y):    
            self.paintSize=(x,y)            
            self.setScrollbars(x,y)
        Logging.info("paintSize=",self.paintSize,kw="preview")


    def resetScroll(self):
        """
        Method: resetScroll()
        Created: 24.03.2005, KP
        Description: Sets the scrollbars to their initial values
        """    
        self.Scroll(0,0)


    def enable(self,flag):
        """
        Method: enable(flag)
        Created: 02.06.2005, KP
        Description: Enable/Disable updates
        """
        self.enabled=flag
        if flag:self.updatePreview()

    def updatePreview(self):
        """
        Method: updatePreview()
        Created: 24.03.2005, KP
        Description: Updates the viewed image
        """
        if not self.enabled:
           Logging.info("Won't draw gallery cause not enabled",kw="preview")
           return
        if not self.slices:
            self.setTimepoint(self.timepoint)
        self.paintPreview()
        self.updateScrolling()
        self.Refresh()
        #wx.GetApp().Yield(1)
        
        
    def updateScrolling(self,event=None):
        """
        Method: updateScrolling
        Created: 24.03.2005, KP
        Description: Updates the scroll settings
        """
        if self.scrollTo:
            x,y=self.scrollTo
            Logging.info("Scrolling to ",x,y,kw="preview")
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
        if self.sizeChanged:
            Logging.info("size changed, calculating buffer",kw="preview")
            self.calculateBuffer()
            self.updatePreview()
            self.sizeChanged=0
        InteractivePanel.InteractivePanel.OnPaint(self,event)
#        dc=wx.BufferedPaintDC(self,self.buffer)#,self.buffer)

    def paintPreview(self):
        """
        Method: paintPreview()
        Created: 24.03.2005, KP
        Description: Paints the image to a DC
        """
        dc = self.dc = wx.BufferedDC(wx.ClientDC(self),self.buffer)
        dc.BeginDrawing()
        dc.SetBackground(wx.Brush(wx.Colour(*self.bgcolor)))
        dc.SetPen(wx.Pen(wx.Colour(*self.bgcolor),0))
        dc.SetBrush(wx.Brush(wx.Color(*self.bgcolor)))
        dc.DrawRectangle(0,0,self.paintSize[0],self.paintSize[1])
        
        if not self.slices:
            Logging.info("Haven't got any slices",kw="preview")
            dc.EndDrawing()
            self.dc = None
            return
        row,col=0,0
    
        for slice in self.slices:
            w,h=self.sliceSize
            slice.Rescale(w,h)
            bmp=slice.ConvertToBitmap()

            x=9+col*(3+self.sliceSize[0])
            y=9+row*(3+self.sliceSize[1])
            
            dc.DrawBitmap(bmp,x,y,False)
            col+=1
            if col>=self.cols:
                col=0
                row+=1
                
            # Mark the rectangle as drawable
            x0,x1=x,x+w
            y0,y1=y,y+h
            self.drawableRects.append((x0,x1,y0,y1))
        
        y=9+(self.rows)*(3+self.sliceSize[1])
        self.bmp=self.buffer

        InteractivePanel.InteractivePanel.paintPreview(self)

        dc.EndDrawing()
        self.dc = None
        
    def saveSnapshot(self,filename):
        """
        Method: saveSnapshot(filename)
        Created: 05.06.2005, KP
        Description: Save a snapshot of the scene
        """      
        ext=filename.split(".")[-1].lower()
        if ext=="jpg":ext="jpeg"
        if ext=="tif":ext="tiff"
        mime="image/%s"%ext
        img=self.buffer.ConvertToImage()
        img.SaveMimeFile(filename,mime)
        
