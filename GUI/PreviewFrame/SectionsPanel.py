# -*- coding: iso-8859-1 -*-

"""
 Unit: SectionsPanel.py
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
from IntegratedPreview import *
from GUI import Events

class SectionsPanel(wx.ScrolledWindow):
    """
    Class: SectionsPanel
    Created: 23.05.2005, KP
    Description: A widget that previews the xy,xz and yz planes of a dataset
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
        
        self.zoomZ=2.0
        
        self.scaleBar = None
        self.scaleBarWidth = 0
        self.voxelSize=(0,0,0)
        self.x,self.y,self.z=0,0,0

        
        self.timepoint=0
        self.paintPreview()
        self.Bind(wx.EVT_PAINT,self.OnPaint)
        self.Bind(wx.EVT_SIZE,self.onSize)
        self.Bind(wx.EVT_LEFT_DOWN,self.onLeftDown)
        self.Bind(wx.EVT_MOTION,self.onLeftDown)
        
    def onLeftDown(self,event):
        """
        Method: onLeftDown
        Created: 06.06.2005, KP
        Description: Handler for mouse clicks
        """    
        if not event.LeftIsDown():
            return
        x,y=event.GetPosition()
        dims=self.imagedata.GetDimensions()
        dims=(dims[0],dims[1],dims[2]*self.zoomZ)
        # the yz plane
        if x>dims[0]+6 and y>3 and y<dims[1] and x<dims[0]+6+dims[2]:
            #print "YZ plane"
            nz=x-dims[0]-6
            ny=y-3
            nx=self.x
        # the xy plane
        elif x>3 and x<dims[0]+3 and y>3 and y< dims[1]+3:
            #print "XY plane"
            nx=x-3
            ny=y-3
            nz=self.z
        # the xz plane
        elif x> 3 and x< dims[0]+3 and y>dims[1]+6 and y<dims[1]+6+dims[2]:
            #print "XZ plane"
            nx=x-3
            nz=y-dims[1]-6
            ny=self.y
        # the gray area
        elif x>dims[0]+6 and x<dims[0]+6+dims[2] and y>dims[1]+6 and y<dims[1]+6+dims[2]:
            #print "Gray area"
            if y>x:
                nz=y-dims[1]-6
            else:
                nz=x-dims[0]-6
            nx=self.x
            ny=self.y
        else:
            print "OUT OF BOUNDS ",x,y
            return
            
        #print "showing ",nx,ny,nz
        self.drawPos=(nx,ny,nz)
        if self.x!=nx or self.y!=ny or self.z!=nz:
            self.x,self.y,self.z=nx,ny,nz
            #print "Redrawing slices"
            self.setTimepoint(self.timepoint)
        self.updatePreview()
            
        
        
    def onSize(self,event):
        """
        Method: onSize
        Created: 23.05.2005, KP
        Description: Size event handler
        """    
        self.size=event.GetSize()
        print "gallery size changed",self.size
        self.sizeChanged=1
        
    def setBackground(self,r,g,b):
        """
        Method: setBackground(r,g,b)
        Created: 24.05.2005, KP
        Description: Set the background color
        """        
        self.bgcolor=(r,g,b)        
        
    def setDataUnit(self,dataUnit,selectedItem=-1):
        """
        Method: setDataUnit(dataUnit)
        Created: 23.05.2005, KP
        Description: Set the dataunit used for preview. 
        """
        self.dataUnit=dataUnit
        if self.visualizer.getProcessedMode():
            dataUnit=dataUnit.getSourceDataUnits()[0]
        
        self.dims=dataUnit.getDimensions()
        x,y,z=self.dims
        x/=2
        y/=2
        z/=2
        z*=self.zoomZ
        
        self.x,self.y,self.z=x,y,z
        self.drawPos=(x,y,z)

        self.voxelSize=dataUnit.getVoxelSize()
        
    def setTimepoint(self,tp):
        """
        Method: setTimepoint(dataUnit)
        Created: 23.05.2005, KP
        Description: Set the timepoint
        """
        self.timepoint=tp
        if self.visualizer.getProcessedMode():
            image=self.dataUnit.doPreview(-2,1,self.timepoint)
            ctf = self.dataUnit.getSourceDataUnits()[0].getColorTransferFunction()
            print "Got data ",image
        else:
            image=self.dataUnit.getTimePoint(tp)
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
        
        self.dims=self.imagedata.GetDimensions()
            
        self.slices=[]
        # obtain the slices
        slice=ImageOperations.vtkImageDataToWxImage(self.imagedata,self.z/self.zoomZ)
        self.slices.append(slice)
        slice=ImageOperations.getPlane(self.imagedata,"zy",self.x,self.y/self.zoomZ,self.z)
        slice=ImageOperations.vtkImageDataToWxImage(slice)
        self.slices.append(slice)
        slice=ImageOperations.getPlane(self.imagedata,"xz",self.x,self.y,self.z/self.zoomZ)
        slice=ImageOperations.vtkImageDataToWxImage(slice)
        self.slices.append(slice)        

        self.calculateBuffer()
    
    def calculateBuffer(self):
        """
        Method: calculateBuffer()
        Created: 23.05.2005, KP
        Description: Calculate the drawing buffer required
        """    
        if not self.imagedata:
            return
        x,y,z=self.imagedata.GetDimensions()
        
        x+=z*self.zoomZ+6
        y+=z*self.zoomZ+6
        self.paintSize=(x,y)
        #print "paintSize=",self.paintSize
        
        self.setScrollbars(x,y)
        
    def setScrollbars(self,xdim,ydim):
        """
        Method: setScrollbars(x,y)
        Created: 24.03.2005, KP
        Description: Configures scroll bar behavior depending on the
                     size of the dataset, which is given as parameters.
        """
        #print "setScrollbars(%d,%d)"%(xdim,ydim)
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
           print "Won't draw sections cause not enabled"
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

        x,y,z=self.dims
        z*=self.zoomZ

        pos=[(3,3),(x+6,3),(3,y+6)]
        for i,slice in enumerate(self.slices):
            w,h=slice.GetWidth(),slice.GetHeight()
            if i==1:
                slice.Rescale(w*self.zoomZ,h)
            elif i==2:
                slice.Rescale(w,h*self.zoomZ)
            bmp=slice.ConvertToBitmap()

            sx,sy=pos[i]
            dc.DrawBitmap(bmp,sx,sy,False)
            
        if self.drawPos:
            posx,posy,posz=self.drawPos
            dc.SetPen(wx.Pen((255,255,255),1))
            # horiz across the xy
            dc.DrawLine(0,posy,6+x+z,posy)
            # vert across the xy
            dc.DrawLine(posx,0,posx,6+y+z)
            # horiz across the lower
            dc.DrawLine(0,y+6+posz,6+x+z,y+6+posz)
            # vert across the right
            dc.DrawLine(6+x+posz,0,6+x+posz,y+6+z)
            
        y=pos[-1][1]
        if self.scaleBar:
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
        
