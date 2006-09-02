# -*- coding: iso-8859-1 -*-

"""
 Unit: Annotations
 Project: BioImageXD
 Created: 10.02.2005, KP
 Description:

 This is a module that contains classes for annotating images
 
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
__version__ = "$Revision: 1.21 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import wx
import Logging


class Annotation:
    """
    Class: Annotation
    Created: 03.07.2005, KP
    Description: A base class for annotation objects
    """ 
    def __init__(self,x,y,voxelSize,scaleFactor):
        """
        Method: __init__(x,y)
        Created: 03.07.2005, KP
        Description: Create an annotation at given position
        """     
        self.vertical=0
        self.region=0
        self.bmp=None
        scaleFactor=float(scaleFactor)
        x/=scaleFactor
        y/=scaleFactor
        self.pos=(x,y)
        self.voxelSize=voxelSize
        self.scaleFactor=scaleFactor
        self.startpos=None
        self.endpos=None
        self.update=0
        self.pointList=[]
        self.widthPx=10
        self.heightPx=10
        self.widthMicro=0
        
    def addPosition(self,pos):
        """
        Method: addPosition(x,y)
        Created: 05.07.2005, KP
        Description: Add a point to the annotation
        """     
        if pos:
            self.pointList.append(pos)
            self.update=1
        
    def setPosition(self,pos):
        """
        Method: setPosition(x,y)
        Created: 04.07.2005, KP
        Description: Move the annotation to the given position
        """     
        try:
            ind=self.pointList.index(self.pos)
            self.pointList[ind]=pos
        except:
            pass
        else:
            if pos:
                self.pointList.append(pos)
        x,y=pos
        x/=self.scaleFactor
        y/=self.scaleFactor
        self.pos=(x,y)
        self.update=1
    
    def getAsBitmap(self):
        """
        Method: getAsBitmap()
        Created: 04.07.2005, KP
        Description: Return annotation as bitmap
        """     
        pass
        
    def drawToDC(self,dc):    
        """
        Method: drawToDC(dc)
        Created: 04.07.2005, KP
        Description: Draw the annotation to a drawing context
        """     
        bmp=self.getAsBitmap()
        x,y=self.getScaledPosition()
        dc.DrawBitmap(bmp,x,y,True)
        

    def setEndPosition(self,pos):
        """
        Method: setEndPosition(pos)
        Created: 04.07.2005, KP
        Description: Sets the ending position of annotation
                     Also does some calculations to determine
                     for example, is the annotation vertical or
                     horizontal and also the length of the annotation
                     in the vertical/horizontal direction
        """     
        x,y=pos
        x/=self.scaleFactor
        y/=self.scaleFactor
        pos=(x,y)
        self.endpos=pos
        x0,y0=self.pos
        x1,y1=self.endpos
        xd=x1-x0
        yd=y1-y0
        if xd<0:
            self.pos=(x1,y0)
            self.endpos=(x0,y1)
        x0,y0=self.pos
        x1,y1=self.endpos
        if yd<0:
            self.pos=(x0,y1)
            self.endpos=(x1,y0)
        x0,y0=self.pos
        x1,y1=self.endpos
        xd=x1-x0
        yd=y1-y0
        
        self.heightPx=abs(yd)
        vertical=0
        diff=xd

        if abs(yd)>abs(xd):
            vertical=1
            diff=yd
        diff=abs(diff)
        Logging.info("diff=",diff,kw="iactivepanel")
        self.setPixelLength(diff)
        self.setAlignment(vertical)            
        self.update=1
        
    def getScaledPosition(self):
        """
        Method: getScaledPosition
        Created: 15.08.2005, KP
        Description: Return the position scaled by the zoom factor
        """             
        return [x*self.scaleFactor for x in self.pos]
        
    def setAlignment(self,vertical=0):
        """
        Method: setAlignment(vertical)
        Created: 04.07.2005, KP
        Description: Sets the alignment to vertical/horizontal
        """     
        self.vertical=vertical        
        self.update=1
        
    def setPixelLength(self,px):
        """
        Method: setPixelLength(px)
        Created: 04.07.2005, KP
        Description: Set the length of scalebar in pixels
        """     
        self.widthPx=px
        self.widthMicro=0
        self.update=1
        
    def setPhysicalLength(self,um):
        """
        Method: setPhysicalLength(um)
        Created: 04.07.2005, KP
        Description: Set the length of the object in micrometers
        """     
        self.widthMicro=um
        self.update=1
        
        
    def setScaleFactor(self,factor):
        """
        Method: setScaleFactor(factor)
        Created: 04.07.2005, KP
        Description: Set the scale factor of annotations
        """     
        self.scaleFactor=factor
        self.update=1
        
    def __setstate__(self,d):
        """
        Method: __setstate__
        Created: 04.07.2005, KP
        Description: Return the dict to pickle
        """     
        self.__dict__.update(d)
        self.bmp=None
        
    def __getstate__(self):
        """
        Method: __getstate__
        Created: 04.07.2005, KP
        Description: Return the dict to pickle
        """     
        d=self.__dict__.copy()
        del d["bmp"]
        return d
        

        
class ScaleBar(Annotation):
    """
    Class: ScaleBar
    Created: 04.07.2005, KP
    Description: A class that represents a scale annotation
    """ 
    def __init__(self,x,y,voxelSize=(1,1,1),scaleFactor=1.0,**kws):
        """
        Method: __init__(x,y)
        Created: 04.07.2005, KP
        Description: Create an scale bar at given position
        """     
        Annotation.__init__(self,x,y,voxelSize,scaleFactor),
        self.bgColor = (127,127,127)
        if "bgColor" in kws:
            self.bgColor=kws["bgColor"]
        # Let's define a list of micrometer lengths that the scale can
        # "snap" to
        self.createSnapToList()
        
    def createSnapToList(self):
        """
        Method: createSnapToList(self)
        Created: 04.07.2005, KP
        Description: Create the list of micrometer lengths to snap to
        """   
        self.snapToMicro=[0.5,1,2,5,7.5,10,12.5,17.5]
        for i in range(10,5000,5):
            self.snapToMicro.append(i)
        self.snapToMicro.sort()
        
            
    def snapToRoundLength(self):
        """
        Method: snapToRoundLength()
        Created: 04.07.2005, KP
        Description: Snap the length in pixels to a round number of micrometers
        """   
        vx = self.voxelSize[0]
        vx*=1000000
        if self.widthMicro and self.widthPx:
            if self.widthMicro in self.snapToMicro:
                return
            if int(self.widthMicro)==self.widthMicro:
                return
        if self.widthPx:
            self.widthMicro=self.widthPx*vx
            if int(self.widthMicro)!=self.widthMicro:
                for i,micro in enumerate(self.snapToMicro[:-1]):
                    if micro<=self.widthMicro and self.snapToMicro[i+1]>self.widthMicro:
                        Logging.info("Pixel width %.4f equals %.4f um. Snapped to %.4fum (%.5fpx)"%(self.widthPx,self.widthMicro,micro,micro/vx),kw="annotation")
                        self.widthMicro=micro
                # when we set widthPx to 0 it will be recalculated below
                self.widthPx=0
                
        if self.widthMicro and not self.widthPx:
            self.widthPx=self.widthMicro/vx
            #Logging.info("%f micrometers is %f pixels"%(self.widthMicro,self.widthPx),kw="annotation")
            self.widthPx=int(self.widthPx)
        self.update=1
        
    def getAsBitmap(self):
        """
        Method: getAsBitmap()
        Created: 04.07.2005, KP
        Description: Return annotation as bitmap
        """     
        # if we have a cached image and no parameters have changed, 
        # then return the cached version
        if self.bmp and not self.update:
            return self.bmp
        #def drawScaleBar(widthPx=0,widthMicro=0,voxelSize=(1,1,1),bgColor=(127,127,127),scaleFactor=1.0,vertical=0,round=1):
        self.snapToRoundLength()

        bg=self.bgColor
        vx = self.voxelSize[0]
        vx*=1000000
        Logging.info("voxel width=%d, scale=%f, scaled %.4f"%(vx,self.scaleFactor,vx/self.scaleFactor),kw="annotation")
        # as the widths and positions are already scaled back, 
        # we don't need to scale the voxel size
        #vx/=float(self.scaleFactor)
 
        if not self.vertical:
            heightPx=32
            widthPx=self.widthPx
        else:
            heightPx=self.widthPx
            widthPx=32
            
        widthPx*=self.scaleFactor
        heightPx*=self.scaleFactor
        dc = wx.MemoryDC()

        # Set the font for the label and calculate the extent
        # so we know if we need to create a bitmap larger than 
        # the width of the scalebar
        if not self.vertical:
            dc.SetFont(wx.Font(8,wx.SWISS,wx.NORMAL,wx.NORMAL))
        else:
            dc.SetFont(wx.Font(9,wx.SWISS,wx.NORMAL,wx.NORMAL))
            
        if int(self.widthMicro)==self.widthMicro:
            text=u"%d\u03bcm"%self.widthMicro
        else:
            text=u"%.2f\u03bcm"%self.widthMicro
        w,h=dc.GetTextExtent(text)
            
        bmpw=widthPx
        bmph=heightPx
        if w>bmpw:bmpw=w
        if h>bmph:bmph=h
        bmp = wx.EmptyBitmap(bmpw,bmph)
        
        dc.SelectObject(bmp)
        dc.BeginDrawing()
        dc.SetBackground(wx.Brush(bg))
        dc.SetBrush(wx.Brush(bg))
        dc.SetPen(wx.Pen(bg,1))
        dc.DrawRectangle(0,0,bmpw,bmph)
        
        dc.SetPen(wx.Pen((255,255,255),2))
        if not self.vertical:
            dc.DrawLine(0,6,widthPx,6)
            dc.DrawLine(1,3,1,9)
            dc.DrawLine(widthPx-1,3,widthPx-1,9)
        else:
            dc.DrawLine(6,0,6,heightPx)
            dc.DrawLine(3,1,9,1)
            dc.DrawLine(3,heightPx-1,9,heightPx-1)
            
        dc.SetTextForeground((255,255,255))
        if not self.vertical:
            x=bmpw/2
            x-=(w/2)
        
            dc.DrawText(text,x,12)
        else:
            y=bmph/2
            y-=(h/2)
            dc.DrawRotatedText(text,12,y,90)
        
        dc.EndDrawing()
        dc.SelectObject(wx.NullBitmap)
        dc = None 
        self.bmp=bmp
        self.update=0
        mask=wx.Mask(bmp,bg)
        bmp.SetMask(mask)
        return bmp
        
    def __setstate__(self,d):
        """
        Method: __setstate__
        Created: 04.07.2005, KP
        Description: Return the dict to pickle
        """     
        self.__dict__.update(d)
        self.bmp=None
        self.createSnapToList()
        
    def __getstate__(self):
        """
        Method: __getstate__
        Created: 04.07.2005, KP
        Description: Return the dict to pickle
        """     
        d=self.__dict__.copy()
        del d["snapToMicro"]
        del d["bmp"]
        return d

class Circle(Annotation):
    """
    Class: Circle
    Created: 05.07.2005, KP
    Description: A class that represents a circle
    """ 
    def __init__(self,x,y,voxelSize=(1,1,1),scaleFactor=1.0,**kws):
        """
        Method: __init__(x,y)
        Created: 04.07.2005, KP
        Description: Create an scale bar at given position
        """     
        Annotation.__init__(self,x,y,voxelSize,scaleFactor)
        self.region=1
            
        
    def getAsBitmap(self):
        """
        Method: getAsBitmap()
        Created: 04.07.2005, KP
        Description: Return annotation as bitmap
        """     
        # if we have a cached image and no parameters have changed, 
        # then return the cached version
        if self.bmp and not self.update:
            return self.bmp

        dc = wx.MemoryDC()
        bmpw=self.widthPx+1
        bmp = wx.EmptyBitmap(bmpw,bmpw)
        bg=(127,127,127)
        dc.SelectObject(bmp)
        dc.BeginDrawing()
        dc.SetBackground(wx.Brush(bg))
        dc.SetBrush(wx.Brush(bg))
        dc.SetPen(wx.Pen(bg,1))
        dc.DrawRectangle(0,0,bmpw,bmpw)
        
        dc.SetPen(wx.Pen((0,255,0),2))
        widthPx=self.widthPx*self.scaleFactor
        dc.DrawCircle(widthPx/2,widthPx/2,widthPx/2)
        
        dc.EndDrawing()
        dc.SelectObject(wx.NullBitmap)
        dc = None 
        self.bmp=bmp
        self.update=0
        mask=wx.Mask(bmp,bg)
        bmp.SetMask(mask)
        return bmp
        
class Rectangle(Annotation):
    """
    Class: Rectangle
    Created: 05.07.2005, KP
    Description: A class that represents a rectangle
    """ 
    def __init__(self,x,y,voxelSize=(1,1,1),scaleFactor=1.0,**kws):
        """
        Method: __init__(x,y)
        Created: 04.07.2005, KP
        Description: Create an scale bar at given position
        """     
        Annotation.__init__(self,x,y,voxelSize,scaleFactor)
        self.region=1
            
        
    def getAsBitmap(self):
        """
        Method: getAsBitmap()
        Created: 04.07.2005, KP
        Description: Return annotation as bitmap
        """     
        # if we have a cached image and no parameters have changed, 
        # then return the cached version
        if self.bmp and not self.update:
            return self.bmp

        dc = wx.MemoryDC()
        bmpw=self.widthPx
        bmpw*=self.scaleFactor
        bmph=self.heightPx
        bmph*=self.scaleFactor
        bmp = wx.EmptyBitmap(bmpw,bmph)
        bg=(127,127,127)
        dc.SelectObject(bmp)
        dc.BeginDrawing()
        dc.SetBackground(wx.Brush(bg))
        dc.SetBrush(wx.Brush(bg))
        dc.SetPen(wx.Pen(bg,1))
        dc.DrawRectangle(0,0,bmpw,bmph)
        
        dc.SetPen(wx.Pen((0,255,0),2))

        dc.DrawRectangle(0,0,bmpw,bmph)
        
        dc.EndDrawing()
        dc.SelectObject(wx.NullBitmap)
        dc = None 
        self.bmp=bmp
        self.update=0
        mask=wx.Mask(bmp,bg)
        bmp.SetMask(mask)
        return bmp        
        
class Polygon(Annotation):
    """
    Class: Rectangle
    Created: 05.07.2005, KP
    Description: A class that represents a rectangle
    """ 
    def __init__(self,x,y,voxelSize=(1,1,1),scaleFactor=1.0,**kws):
        """
        Method: __init__(x,y)
        Created: 04.07.2005, KP
        Description: Create an scale bar at given position
        """     
        Annotation.__init__(self,x,y,voxelSize,scaleFactor)
        self.region=1
            
    def getAsBitmap(self):
        """
        Method: getAsBitmap()
        Created: 04.07.2005, KP
        Description: Return annotation as bitmap
        """     
        # if we have a cached image and no parameters have changed, 
        # then return the cached version
        if self.bmp and not self.update:
            return self.bmp

        dc = wx.MemoryDC()
        
        bmpw=10
        bmph=10
        x0,y0=0,0
        if self.pointList:
            x1,y1=0,0
            for x,y in self.pointList:
                x1=max(x1,x)
                y1=max(y1,y)
            bmpw=abs(x1-x0)+5
            bmph=abs(y1-y0)+5

        bmp = wx.EmptyBitmap(bmpw,bmph)
        bg=(127,127,127)
        dc.SelectObject(bmp)
        dc.BeginDrawing()
        dc.SetBackground(wx.Brush(bg))
        dc.SetBrush(wx.Brush(bg))
        dc.SetPen(wx.Pen(bg,1))
        dc.DrawRectangle(0,0,bmpw,bmph)
        
        Logging.info("width=",bmpw,"Height=",bmph,kw="iactivepanel")
        dc.SetPen(wx.Pen((0,255,0),2))
        
        if self.pointList:
            Logging.info("Drawing points in ",self.pointList,kw="iactivepanel")
            for point in self.pointList:
                x,y=point.x,point.y
                x*=self.scaleFactor
                y*=self.scaleFactor
                Logging.info("Drawing circle at ",x,y,kw="iactivepanel")
                dc.DrawCircle(x,y,2)
            
        if len(self.pointList)>1:
            Logging.info("Drawing lines...",kw="iactivepanel")
            p0=self.pointList[0]
            for p1 in self.pointList[1:]:
                x0,y0=p0
                x1,y1=p1
                x0,y0,x1,y1=[x*self.scaleFactor for x in (x0,y0,x1,y1)]
                dc.DrawLine(x0,y0,x1,y1)
                p0=p1
            x0,y0=self.pointList[-1]
            x1,y1=self.pointList[0]
            x0,y0,x1,y1=[x*self.scaleFactor for x in (x0,y0,x1,y1)]
            dc.DrawLine(x0,y0,x1,y1)
        
        dc.EndDrawing()
        dc.SelectObject(wx.NullBitmap)
        dc = None 
        self.bmp=bmp
        self.update=0
        mask=wx.Mask(bmp,bg)
        bmp.SetMask(mask)
        self.pos=0,0
        return bmp                
