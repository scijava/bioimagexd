# -*- coding: iso-8859-1 -*-

"""
 Unit: GalleryPanel.py
 Project: BioImageXD
 Created: 23.05.2005, KP
 Description:

 A panel that can display previews of all the optical slices of
 volume data independent of a VTK render window,using the tools provided by wxPython.
 
 Modified 23.05.2005 KP - Created the class

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

class GalleryPanel(wx.ScrolledWindow):
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
        print "size=",size
        self.enabled=1
        self.slices=[]
        
        if kws.has_key("slicesize"):
            self.sliceSize=kws["slicesize"]
        else:
            self.sliceSize=(128,128)
        self.originalSliceSize=self.sliceSize
        
        x,y=size
        self.paintSize=size
        self.buffer = wx.EmptyBitmap(x,y)
        wx.ScrolledWindow.__init__(self,parent,-1,size=size,**kws)
        self.size=size
        self.sizeChanged=0
        self.rows=0
        self.cols=0
        self.scrollsize=32
        self.scrollTo=None
        self.dataUnit=None
        
        self.scaleBar = None
        self.scaleBarWidth = 0
        self.voxelSize=(0,0,0)

        
        self.timepoint=0
        self.paintPreview()
        self.Bind(wx.EVT_PAINT,self.OnPaint)
        self.Bind(wx.EVT_SIZE,self.onSize)
        
    def drawScaleBar(self,width):
        """
        Method: drawScaleBar(width,voxelsize)
        Created: 05.06.2005, KP
        Description: Draw a scale bar of given size
        """    
        self.scaleBarWidth = width
        f=self.sliceSize[0]/float(self.dims[0])
        print "Scale factor for gallery=",f
        self.scaleBar = ImageOperations.drawScaleBar(64,0,self.voxelSize,(0,0,0),f)
        
    def zoomToFit(self):
        """
        Method: zoomToFit()
        Created: 05.06.2005, KP
        Description: Zoom the dataset to fit the available screen space
        """
        pass
        
    def setZoomFactor(self,factor):
        """
        Method: setZoomFactor(factor)
        Created: 05.06.2005, KP
        Description: Set the factor by which the image is zoomed
        """
        x,y=self.originalSliceSize
        x*=factor
        y*=factor        #for preview in [self.xypreview,self.xzpreview,self.yzpreview]:
        #    preview.setTimepoint(tp)
        #    preview.updatePreview(1)
        #self.xypreview.setTimepoint(tp)
        

        self.sliceSize=(x,y)
        self.slices=[]
        self.drawScaleBar(self.scaleBarWidth)
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
        self.size=event.GetSize()
        print "gallery size changed",self.size
        self.sizeChanged=1

    def setDataUnit(self,dataunit):
        """
        Method: setDataUnit(dataunit)
        Created: 23.05.2005, KP
        Description: Sets the dataunit to display
        """    
        self.dataUnit=dataunit
        if self.visualizer.getProcessedMode():
            dataunit=dataunit.getSourceDataUnits()[0]
        
        self.dims=dataunit.getDimensions()
        self.voxelSize=dataunit.getVoxelSize()
        print "Got dataunit"
        #print "Got image",image
        #self.imagedata=image
        
        
    def setTimepoint(self,timepoint):
        """
        Method: setTimepoint(tp)
        Created: 23.05.2005, KP
        Description: Sets the timepoint to display
        """    
        self.timepoint=timepoint
        if self.visualizer.getProcessedMode():
            image=self.dataUnit.doPreview(-2,1,self.timepoint)
            ctf = self.dataUnit.getSourceDataUnits()[0].getColorTransferFunction()
            print "Got data ",image
        else:
            image=self.dataUnit.getTimePoint(timepoint)
            ctf=self.dataUnit.getColorTransferFunction()
        
        if self.dataUnit.getBitDepth()!=32:
            maptocolor=vtk.vtkImageMapToColors()
            maptocolor.SetInput(image)
            maptocolor.SetLookupTable(ctf)
            maptocolor.SetOutputFormatToRGB()
            maptocolor.Update()
            self.imagedata=maptocolor.GetOutput()
        else:
            self.imagedata=image
        self.calculateBuffer()
        x,y,z=self.imagedata.GetDimensions()
        
        
        self.slices=[]
        print "x,y,z=",x,y,z
        for i in range(z):
            slice=ImageOperations.vtkImageDataToWxImage(self.imagedata,i)    
            self.slices.append(slice)

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
        
        w,h=self.sliceSize
        
        xreq=self.size[0]//(w+6)
        yreq=math.ceil(z/float(xreq))
        print "Need %d x %d grid to show the dataset"%(xreq,yreq)
        

        # allow for 3 pixel border
        x=12+(xreq)*(w+6)
        y=12+(yreq)*(h+6)
        
        self.rows=yreq
        self.cols=xreq
            
        self.paintSize=(x,y)
        print "paintSize=",self.paintSize
        
        self.setScrollbars(x,y)

    def setMaximumSize(self,x,y):
        """
        Method: setMaximumSize(x,y)
        Created: 24.03.2005, KP
        Description: Sets the maximum size for this widget
        """    
        self.maxX,self.maxY=x,y
                        
    def resetScroll(self):
        """
        Method: resetScroll()
        Created: 24.03.2005, KP
        Description: Sets the scrollbars to their initial values
        """    
        self.Scroll(0,0)

    def setScrollbars(self,xdim,ydim):
        """
        Method: setScrollbars(x,y)
        Created: 24.03.2005, KP
        Description: Configures scroll bar behavior depending on the
                     size of the dataset, which is given as parameters.
        """
        print "setScrollbars(%d,%d)"%(xdim,ydim)
        w,h=self.buffer.GetWidth(),self.buffer.GetHeight()
        
        if w!=xdim or h!=ydim:
            self.buffer = wx.EmptyBitmap(xdim,ydim)
            
        self.SetVirtualSize((xdim,ydim))
        self.SetScrollRate(self.scrollsize,self.scrollsize)

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
           print "Won't draw gallery cause not enabled"
           return
        if not self.slices:
            self.setTimepoint(self.timepoint)
        self.paintPreview()
        wx.GetApp().Yield(1)
        self.updateScrolling()
        
    def updateScrolling(self,event=None):
        """
        Method: updateScrolling
        Created: 24.03.2005, KP
        Description: Updates the scroll settings
        """
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
        if self.sizeChanged:
            print "size changed, calculating buffer"
            self.calculateBuffer()
            self.updatePreview()
            self.sizeChanged=0
        dc=wx.BufferedPaintDC(self,self.buffer)#,self.buffer)

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
            print "Haven't got any slices"
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
        
        y=9+(self.rows)*(3+self.sliceSize[1])
        if self.scaleBar:
            print "Drawing scalebar at ",5,y-40
            dc.DrawBitmap(self.scaleBar,12,y-30,True)


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
        
