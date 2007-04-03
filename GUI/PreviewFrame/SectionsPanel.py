# -*- coding: iso-8859-1 -*-

"""
 Unit: SectionsPanel.py
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
__author__ = "BioImageXD Project <http://www.bioimagexd.org/>"
__version__ = "$Revision: 1.9 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import wx    
from wx.lib.statbmp  import GenStaticBitmap as StaticBitmap
import ImageOperations
import vtk
import Logging
import InteractivePanel
import messenger
import math

class SectionsPanel(InteractivePanel.InteractivePanel):
    """
    Created: 23.05.2005, KP
    Description: A widget that previews the xy,xz and yz planes of a dataset
    """
    def __init__(self,parent,visualizer,size=(512,512),**kws):
        """
        Created: 24.03.2005, KP
        Description: Initialization
        """    
        self.imagedata=None
        self.fitLater =0
        self.visualizer=visualizer
        self.noUpdate = 0
        self.bmp=None
        self.bgcolor=(127,127,127)
        self.enabled=1
        self.slices=[]
            
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
        self.dataUnit=None
        
        self.drawableRects=[]
        self.zspacing = 1
        
        self.zoomZ=1.0
        self.zoomx=1
        self.zoomy=1
        
        self.xmargin=5
        self.xmargin_default=5
        self.ymargin=5
        self.ymargin_default=5
        
        self.voxelSize=(0,0,0)
        self.x,self.y,self.z=0,0,0

        
        self.timepoint=0
        self.paintPreview()
        self.Bind(wx.EVT_PAINT,self.OnPaint)
        self.Bind(wx.EVT_SIZE,self.onSize)
        self.Bind(wx.EVT_LEFT_DOWN,self.onLeftDown)
        self.Bind(wx.EVT_MOTION,self.onLeftDown)
        
        messenger.connect(None,"zslice_changed",self.onSetZSlice)        
        
    def getDrawableRectangles(self):
        """
        Created: 04.07.2005, KP
        Description: Return the rectangles can be drawn on as four-tuples
        """    
        return self.drawableRects
        
    def setZoomFactor(self,factor):
        """
        Created: 05.06.2005, KP
        Description: Set the factor by which the image is zoomed
        """
        self.zoomFactor=factor
        if self.dataUnit:
            self.setTimepoint(self.timepoint)
        self.updateAnnotations()
        self.sizeChanged=1

                
        self.xmargin=int(self.xmargin_default*self.zoomFactor)
        self.ymargin=int(self.ymargin_default*self.zoomFactor)
        if self.xmargin<3:self.xmargin=3
        if self.ymargin<3:self.ymargin=3
        x0,y0,x1,y1 = self.GetClientRect()
        self.xmargin += x0
        self.ymargin += y0

        self.calculateBuffer()
            
        self.updatePreview()
        self.Refresh()
        
    def onSetZSlice(self,obj,event,arg):
        """
        Created: 1.08.2005, KP
        Description: Set the shown zslice
        """    
        # A flag to indicate that we won't react on our own messages
        if self.noUpdate:
            return
        nx,ny=self.x,self.y
        nz=arg
        self.z=arg
        self.drawPos=[x*self.zoomFactor for x in (nx,ny,nz)]
        
        self.setTimepoint(self.timepoint)
        self.updatePreview()        
        
    def onLeftDown(self,event):
        """
        Created: 06.06.2005, KP
        Description: Handler for mouse clicks
        """    
        # if left mouse key is not down or the key down is related to
        # interactive panel events
        if self.action:
            event.Skip()
            return
        if not event.LeftIsDown():
            event.Skip()
            return
        x,y=event.GetPosition()
        
        #x,y=self.getScrolledXY(x,y)
        x-=self.xmargin
        y-=self.ymargin
        #Logging.info("x=%d,y=%d"%(x,y))
        
        x/=float(self.zoomFactor)
        y/=float(self.zoomFactor)
                
        dims=self.imagedata.GetDimensions()
        #Logging.info("x,y=(%d,%d)"%(x,y),"dims=",dims,"margins=",self.xmargin,self.ymargin)
        #dims=(dims[0],dims[1],dims[2]*self.zoomZ)
        #dims=[i*self.zoomFactor for i in dims]
        
        # the yz plane
        #print "x=%d,mx=%d+%d"%(x,dims[0],self.xmargin)
        # calculate scaled margins, because the click coordinates are scaled as well
        sxmargin=self.xmargin/self.zoomFactor
        symargin=self.ymargin/self.zoomFactor
        
        if x>=dims[0]+sxmargin+dims[2]*self.zspacing:
            x=dims[0]+sxmargin+dims[2]*self.zspacing-1
        if y>=dims[1]+symargin+dims[2]*self.zspacing:
            y=dims[1]+symargin+dims[2]*self.zspacing-1
            
            
        if x>dims[0]+(sxmargin) and y>0 and y<dims[1] and x<dims[0]+sxmargin+dims[2]*self.zspacing:
            nz=x-dims[0]-sxmargin
            nz/=self.zspacing
            ny=y#-self.ymargin
            nx=self.x
        elif x>0 and x<dims[0] and y>0 and y< dims[1]:
            nx=x#+self.xmargin
            ny=y#+self.ymargin
            nz=self.z
        # the xz plane
        elif x> 0 and x< dims[0] and y>dims[1]+symargin and y<dims[1]+symargin+dims[2]*self.zspacing:
            nx=x#-self.xmargin
            nz=y-dims[1]-symargin
            nz/=self.zspacing
            ny=self.y
        # the gray area
        elif x>dims[0]+sxmargin and x<dims[0]+sxmargin+dims[2]*self.zspacing and y>dims[1]+symargin and y<dims[1]+symargin+dims[2]*self.zspacing:
            if y>x:
                nz=y-dims[1]-symargin
            else:
                nz=x-dims[0]-sxmargin
            nx=self.x
            ny=self.y
        else:
            Logging.info("Out of bounds (%d,%d)"%(x,y),kw="preview")
            return
        #nz/=self.zoomFactor
        #print "showing ",nx,ny,nz
        
#        self.drawPos=[a*self.zoomFactor for a in (self.x,self.y,self.z)]
    
        self.drawPos=[math.ceil(a*self.zoomFactor) for a in (nx,ny,nz)]
#        Logging.info("drawPos=",self.drawPos,"zoomFactor=",self.zoomFactor,"nx=%d, ny=%d, nz=%d"%(nx,ny,nz))
        if self.x!=nx or self.y!=ny or self.z!=nz:
            self.x,self.y,self.z=nx,ny,nz
    
            #print "Redrawing slices"
            self.setTimepoint(self.timepoint)
        self.updatePreview()
        self.noUpdate=1
        messenger.send(None,"zslice_changed",nz) 
        self.noUpdate = 0                
        ncomps=self.imagedata.GetNumberOfScalarComponents()
        if ncomps==1:
            scalar=self.imagedata.GetScalarComponentAsDouble(self.x,self.y,self.z,0)
            rv=-1
            gv=-1
            bv=-1
            alpha=-1
            val=[0,0,0]
            self.ctf.GetColor(scalar, val)
            r,g,b = val

        else:
            rv=self.imagedata.GetScalarComponentAsDouble(self.x,self.y,self.z,0)
            gv=self.imagedata.GetScalarComponentAsDouble(self.x,self.y,self.z,1)
            bv=self.imagedata.GetScalarComponentAsDouble(self.x,self.y,self.z,2)
            r,g,b = rv,gv,bv
            scalar=0xdeadbeef
            alpha=-1
            if ncomps>3:
                alpha=self.imagedata.GetScalarComponentAsDouble(self.x,self.y,self.z,3)
        
        rx, ry, rz = self.x, self.y, self.z
    
    
        messenger.send(None,"get_voxel_at",rx,ry,rz, scalar, rv,gv,bv,r,g,b,alpha,self.ctf)

        
        event.Skip()
            
        
    def onSize(self,event):
        """
        Created: 23.05.2005, KP
        Description: Size event handler
        """    
        InteractivePanel.InteractivePanel.OnSize(self,event)
        self.size=event.GetSize()
        Logging.info("Sections panel size changed to ",self.size,kw="preview")
        self.sizeChanged=1
        
    def setBackground(self,r,g,b):
        """
        Created: 24.05.2005, KP
        Description: Set the background color
        """        
        self.bgcolor=(r,g,b)        
        
    def setDataUnit(self,dataUnit,selectedItem=-1):
        """
        Created: 23.05.2005, KP
        Description: Set the dataunit used for preview. 
        """
        self.dataUnit=dataUnit                
        
        self.dims=dataUnit.getDimensions()
        
        x,y,z=self.dims
        x/=2
        y/=2
        z/=2
        z*=self.zoomZ
        
        self.x,self.y,self.z=x,y,z
        self.drawPos=(x,y,z)

        self.voxelSize=dataUnit.getVoxelSize()
        InteractivePanel.InteractivePanel.setDataUnit(self,dataUnit)
        self.setTimepoint(self.timepoint)
        self.calculateBuffer()
        self.updatePreview()
        self.Refresh()
        
    def setTimepoint(self,tp):
        """
        Created: 23.05.2005, KP
        Description: Set the timepoint
        """
        self.timepoint=tp
        if self.dataUnit.isProcessed():
            print "Sections view doing preview"
            image=self.dataUnit.doPreview(-2,1,self.timepoint)
            
            self.ctf = self.dataUnit.getColorTransferFunction()
        else:
            image=self.dataUnit.getTimePoint(tp)
            self.ctf=self.dataUnit.getColorTransferFunction()
        
        image.Update()
        self.zspacing = image.GetSpacing()[2]
        self.imagedata = ImageOperations.imageDataTo3Component(image,self.ctf)
        
        if self.fitLater:
            self.fitLater=0
            self.zoomToFit()        
        self.dims=self.imagedata.GetDimensions()
            
        self.slices=[]
        # obtain the slices

        z=self.z/self.zoomZ
        #z/=self.zoomFactor
        if self.zoomFactor!=1:
            img=ImageOperations.scaleImage(self.imagedata,self.zoomFactor,z)
            slice=ImageOperations.vtkImageDataToWxImage(img)        
            
        else:
            slice=ImageOperations.vtkImageDataToWxImage(self.imagedata,z)
            
        self.slices.append(slice)
        
        slice=ImageOperations.getPlane(self.imagedata,"zy",self.x,self.y,z)
        #slice=ImageOperations.getPlane(self.imagedata,"xz",self.x,self.y,z)
        if self.zoomFactor != 1 or self.zspacing != 1:
            slice=ImageOperations.scaleImage(slice,self.zoomFactor, yfactor=1, xfactor=self.zspacing)
        #if self.zoomZ != 1:
        #    slice=ImageOperaations.scaleImage(slice,xfactor=self.zoomZ)
        
        slice=ImageOperations.vtkImageDataToWxImage(slice)
        self.slices.append(slice)
        slice=ImageOperations.getPlane(self.imagedata,"xz",self.x,self.y,z)
        #slice=ImageOperations.getPlane(self.imagedata,"zy",self.x,self.y,z)
        if self.zoomFactor != 1 or self.zoomZ != 1  or self.zspacing != 1:
            slice=ImageOperations.scaleImage(slice,self.zoomFactor, yfactor=self.zspacing, xfactor=1)
        #if self.zoomZ != 1:
        #    slice=ImageOperaations.scaleImage(slice,yfactor=self.zoomZ)        
        slice=ImageOperations.vtkImageDataToWxImage(slice)
        self.slices.append(slice)        

        self.calculateBuffer()
        self.updatePreview()
    
    def calculateBuffer(self):
        """
        Created: 23.05.2005, KP
        Description: Calculate the drawing buffer required
        """    
        if not self.imagedata:
            return
        x,y,z=self.imagedata.GetDimensions()
        x,y,z=[i*self.zoomFactor for i in (x,y,z)]
        Logging.info("scaled size =", x,y,z,kw="visualizer")
        
        x+=z*self.zoomZ+2*self.xmargin
        y+=z*self.zoomZ+2*self.ymargin
        if self.maxSizeX>x:
            x=self.maxSizeX
        if self.maxSizeY>y:
            y=self.maxSizeY
        self.paintSize=(x,y)
        if self.buffer.GetWidth()!=x or self.buffer.GetHeight()!=y:
            self.buffer = wx.EmptyBitmap(x,y)
            Logging.info("Paint size=",self.paintSize,kw="preview")
            #print "paintSize=",self.paintSize
            
            self.setScrollbars(x,y)
        
        
    def enable(self,flag):
        """
        Created: 02.06.2005, KP
        Description: Enable/Disable updates
        """
        self.enabled=flag
        if flag:
            self.updatePreview()

    def updatePreview(self):
        """
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

    def OnPaint(self,event):
        """
        Created: 28.04.2005, KP
        Description: Does the actual blitting of the bitmap
        """
        if self.sizeChanged:
            Logging.info("Size changed, calculating buffer",kw="preview")
            self.calculateBuffer()
            self.updatePreview()
            self.sizeChanged=0
        InteractivePanel.InteractivePanel.OnPaint(self,event)    
    
    
    def paintPreview(self):
        """
        Created: 24.03.2005, KP
        Description: Paints the image to a DC
        """
        dc = self.dc = wx.BufferedDC(wx.ClientDC(self),self.buffer)
        dc.BeginDrawing()
        dc.SetBackground(wx.Brush(wx.Colour(*self.bgcolor)))
        dc.SetPen(wx.Pen(wx.Colour(*self.bgcolor),0))
        dc.SetBrush(wx.Brush(wx.Color(*self.bgcolor)))
        
        x0,y0,x1,y1 = self.GetClientRect()

        dc.DrawRectangle(x0,y0,self.paintSize[0],self.paintSize[1])
        x0,y0=0,0
        
        if not self.slices:
            print "Haven't got any slices"
            dc.EndDrawing()
            self.dc = None
            return
        row,col=0,0

        x,y,z=[i*self.zoomFactor for i in self.dims]
        z*=self.zoomZ*self.zspacing

        pos=[(self.xmargin,self.ymargin),(x+(2*self.xmargin),self.ymargin),(self.xmargin,y+(2*self.ymargin))]
        for i,slice in enumerate(self.slices):
                                  

            w,h=slice.GetWidth(),slice.GetHeight()
            #print "Widht, height of slice=",w,h
            #if i==2:
                #slice=slice.Mirror(1)
            bmp=slice.ConvertToBitmap()

            sx,sy=pos[i]
            sx+=x0
            sy+=y0
            dc.DrawBitmap(bmp,sx,sy,False)
            self.drawableRects.append((sx,sx+w,sy,sy+h))
            
        if self.drawPos:
            posx,posy,posz=self.drawPos
            posx+=self.xmargin
            posy+=self.ymargin
            dc.SetPen(wx.Pen((255,255,255),1))
            # horiz across the xy
            dc.DrawLine(x0+0,y0+posy,(2*self.xmargin)+x+z,posy)
            # vert across the xy
            dc.DrawLine(x0+posx,y0,x0+posx,y0+(2*self.ymargin)+y+z)
            # horiz across the lower
            dc.DrawLine(x0,y0+y+(2*self.ymargin)+posz*self.zspacing,x0+(2*self.xmargin)+x+z,y0+y+(2*self.ymargin)+posz*self.zspacing
            )
            # vert across the right
            dc.DrawLine(x0+(2*self.xmargin)+x+posz*self.zspacing,y0,x0+(2*self.xmargin)+x+posz*self.zspacing,y0+y+(2*self.ymargin)+z)
            
        y=pos[-1][1]
            
            
        self.bmp=self.buffer
        InteractivePanel.InteractivePanel.paintPreview(self)
            

        dc.EndDrawing()
        self.dc = None
        
    def zoomToFit(self):
        """
        Created: 14.08.2005, KP
        Description: Calculate and set the zoom factor so that the dataset
                     fits in the available screen space
        """
        if not self.imagedata:
            self.fitLater = 1
            return
        x,y,z=self.imagedata.GetDimensions()
        
        x+=z*self.zoomZ+2*self.xmargin
        y+=z*self.zoomZ+2*self.ymargin
        f=self.maxSizeX/x
        f2=self.maxSizeY/y
        f=min(f,f2)
        self.setZoomFactor(f)
        
