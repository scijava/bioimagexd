# -*- coding: iso-8859-1 -*-

"""
 Unit: OGLAnnotations
 Project: BioImageXD
 Created: 10.02.2005, KP
 Description:

 This is a module that contains classes for annotating images using the OGL library
 
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
import wx.lib.ogl as ogl
import messenger
import math

count={}

class OGLAnnotation:

    def OnDrawControlPoints(self, dc):
        if not self._drawHandles:
            return

        dc.SetBrush(wx.BLACK_BRUSH)
        dc.SetPen(wx.BLACK_PEN)

        for control in self._controlPoints:
            control.SetPen(wx.WHITE_PEN)
            control.SetBrush(wx.WHITE_BRUSH)
            control.Draw(dc)
            
#    def OnDrawOutline(self, dc,x,y,w,h):
#        print "Draw outline to ",x,y,"width=",w,"height=",h
            
    def getAsMaskImage(self):
        """
        Created: 04.08.2006
        Description: Return a mask image representing this region of interest
        """
        if not self.isROI():
            return None
        insideMap={}
        insideMap.update(self.getCoveredPoints())
        insMap={}
        for x,y in insideMap.keys():
            insMap[(x,y)]=1
        parent = self.GetCanvas()
        mx, my, mz = parent.dataUnit.getDimensions()
        return ImageOperations.getMaskFromPoints(insMap,mx,my,mz)        
            
    def setName(self, name):
        """
        Created: 04.08.2006, KP
        Description: Set the name of this annotation
        """
        self._name = name
        self.ClearText()
        self.SetTextColour("#00ff00")
        lines = name.split("\n")
        for line in lines:
            self.AddText(line)
    def addAttr(self, dicti, attr):        
        dicti[attr]=self.__dict__[attr]
        
    def getAttr(self,dicti,attr):
        self.__dict__[attr]=dicti[attr]
        
    def getName(self):
        """
        Created: 04.08.2006
        Description: return the name of this annotation
        """
        if not hasattr(self,"_name"):
            self._name=""
        return self._name
    def isROI(self):
        if not hasattr(self,"_isROI"):
            self._isROI=0
        return self._isROI
        
        
    def __getstate__(self):
        """
        Created: 24.10.2006, KP
        Description: Return a dictionary describing this object in such details
                     that it can later be reconstructed based on said dictionary
        """
        ret={}
        if "_xpos" not in self.attrList:
            self.attrList.append("_xpos")
            self.attrList.append("_ypos")
        for attr in self.attrList:
            self.addAttr(ret,attr)
        return ret

        
    def __setstate__(self, state):
        """
        Created: 24.10.2006, KP
        Description: Reconstruct state of this object from given dictionary
        """
        for key in state.keys():
            self.getAttr(state,key)
        
class MyText(OGLAnnotation, ogl.TextShape):
    """
    Created: 05.10.2006, KP
    Description: A text annotation
    """
    def __init__(self, width, height):
        ogl.TextShape.__init__(self,width,height)
        self._isROI = 0
        

class MyScalebar(OGLAnnotation, ogl.RectangleShape):
    
    def __init__(self, w, h, voxelsize = (1e-7,1e-7,1e-7), zoomFactor = 1.0):
        ogl.RectangleShape.__init__(self, w, h)
        self.bgColor = (127,127,127)
        self.voxelSize=voxelsize
        self.createSnapToList()
        self.widthMicro = -0
        
        self.oldMaxSize =0
        self.vertical = 0
        self.scaleFactor = zoomFactor
        messenger.connect(None,"set_voxel_size",self.onSetVoxelSize)
        self.attrList = ["vertical","voxelSize","widthMicro","oldMaxSize","_width","_height","_xpos","_ypos"]
    
    

        
    def onSetVoxelSize(self, obj, evt, arg):
        """
        Created: 21.06.2006, KP
        Description: onSetVoxelSize
        """   
        self.voxelSize = arg
        
        
    def setScaleFactor(self,factor):
        """
        Created: 21.06.2006, KP
        Description: Set the scaling factor in use
        """   
        w,h,x,y = self._width,self._height,self.GetX(),self.GetY()
        w/=self.scaleFactor
        h/=self.scaleFactor
        x/=self.scaleFactor
        y/=self.scaleFactor
        self.scaleFactor = factor
        w*=self.scaleFactor
        h*=self.scaleFactor
        x*=self.scaleFactor
        y*=self.scaleFactor        
        if self.vertical:
            vx = self.voxelSize[1]*1000000
            h = int(1+self.widthMicro / vx)
            h*=self.scaleFactor
            print "Keeping microwidth constant, size now",h
        else:
            vx = self.voxelSize[0]*1000000
            w = int(1+self.widthMicro/vx)
            w*=self.scaleFactor
            print "Keeping microwidth constant, size now",w
        
        self.SetWidth(w)
        self.SetHeight(h)
        self.SetX(x)
        self.SetY(y)
        self.ResetControlPoints()
        
    def createSnapToList(self):
        """
        Created: 04.07.2005, KP
        Description: Create the list of micrometer lengths to snap to
        """   
        self.snapToMicro=[0.5,1.0,2.0,5.0,7.5,10.0,12.5,15.0,17.5]
        for i in range(40,10000,5):
            i/=2.0
            self.snapToMicro.append(float(i))
        self.snapToMicro.sort()
        
        
    def snapToRoundLength(self):
        """
        Created: 04.07.2005, KP
        Description: Snap the length in pixels to a round number of micrometers
        """   
        vx = self.voxelSize[0]
        vx*=1000000
       
        maxsize = self._width
        if self.vertical:
            maxsize=self._height
        absMaxSize=maxsize
        maxsize /= self.scaleFactor
        #print "absMaxSize=",absMaxSize,"oldmaxsize=",self.oldMaxSize
        if maxsize and absMaxSize != self.oldMaxSize:
            self.widthMicro=maxsize*vx
            #print "width in micro=",self.widthMicro
            if int(self.widthMicro)!=self.widthMicro and self.widthMicro not in self.snapToMicro:
                for i,micro in enumerate(self.snapToMicro[:-1]):
                    
                    if micro<=self.widthMicro and (self.snapToMicro[i+1]-self.widthMicro)>1e-6:
                        #print "micro=",micro,"<",self.widthMicro,"next=",self.snapToMicro[i+1],">",self.widthMicro
                        Logging.info("Pixel width %.4f equals %.4f um. Snapped to %.4fum (%.5fpx)"%(maxsize,self.widthMicro,micro,micro/vx),kw="annotation")
                        self.widthMicro=micro
                        #print "set widthMicro to=",self.widthMicro

                # when we set widthPx to 0 it will be recalculated below
                maxsize=0
            #else:
                #print "An integer width micro",self.widthMicro,"is ok"
                
        else:
            return
                
        if self.widthMicro and not maxsize:
            w=self.widthMicro/vx
            w*= self.scaleFactor
            

            if self.vertical:
                #print "Setting height to",w
                self.SetHeight(int(w))
            else:
                #print "Setting width to",w
                self.SetWidth(int(w))
            self.oldMaxSize = int(w)
            #print "widthmicro at end=",self.widthMicro
            #Logging.info("%f micrometers is %f pixels"%(self.widthMicro,self.widthPx),kw="annotation")
            #self.widthPx=int(self.widthPx)
            
        
    def OnDraw(self, dc):
        #print "OnDraw"
        x1 = self._xpos - self._width / 2.0
        y1 = self._ypos - self._height / 2.0
        
        if self._width<self._height:
            self.vertical = 1
        else:
            self.vertical = 0
        
        self.snapToRoundLength()
        #print "widthMicro now=",self.widthMicro

        bg=self.bgColor
        vx = self.voxelSize[0]
        vx*=1000000
        #print "voxelsizes=",self.voxelSize
        #Logging.info("voxel width=%d, scale=%f, scaled %.4f"%(vx,self.scaleFactor,vx/self.scaleFactor),kw="annotation")
        # as the widths and positions are already scaled back, 
        # we don't need to scale the voxel size
        #vx/=float(self.scaleFactor)
 
        if not self.vertical:
            self.SetHeight(32)
        else:
            self.SetWidth(32)
            
        #widthPx*=self.scaleFactor
        #heightPx*=self.scaleFactor
        
        # Set the font for the label and calculate the extent
        # so we know if we need to create a bitmap larger than 
        # the width of the scalebar
        if not self.vertical:
            dc.SetFont(wx.Font(8,wx.SWISS,wx.NORMAL,wx.NORMAL))
        else:
            dc.SetFont(wx.Font(9,wx.SWISS,wx.NORMAL,wx.NORMAL))
        #print "widthMicro=",self.widthMicro
        if int(self.widthMicro)==self.widthMicro:
            text=u"%d\u03bcm"%self.widthMicro
        else:
            text=u"%.2f\u03bcm"%self.widthMicro
        w,h=dc.GetTextExtent(text)
            
        bmpw=self._width
        bmph=self._height
        if w>bmpw:bmpw=w
        if h>bmph:bmph=h
        #bmp = wx.EmptyBitmap(bmpw,bmph)
        
        #dc.SelectObject(bmp)
        #dc.BeginDrawing()
        dc.SetBackground(wx.Brush(bg))
        dc.SetBrush(wx.Brush(bg))
        dc.SetPen(wx.Pen(bg,1))
        #dc.DrawRectangle(x1+0,y1+0,x1+bmpw,y1+bmph)
        
        dc.SetPen(wx.Pen((255,255,255),2))
        if not self.vertical:
            dc.DrawLine(x1,y1+6,x1+self._width,y1+6)
            dc.DrawLine(x1+1,y1+3,x1+1,y1+9)
            dc.DrawLine(x1+self._width-1,y1+3,x1+self._width-1,y1+9)
        else:
            dc.DrawLine(x1+6,y1,x1+6,y1+self._height)
            dc.DrawLine(x1+3,y1+1,x1+9,y1+1)
            dc.DrawLine(x1+3,y1+self._height-1,x1+9,y1+self._height-1)
            
        dc.SetTextForeground((255,255,255))
        if not self.vertical:
            x=bmpw/2
            x-=(w/2)
            dc.DrawText(text,x1+x,y1+12)
        else:
            y=bmph/2
            y-=(h/2)
            dc.DrawRotatedText(text,x1+12,y1+y,90)
            
class MyPolygonSketch(OGLAnnotation, ogl.Shape):   
    def __init__(self,zoomFactor = 1.0):
        """
        Created: 26.06.2006, KP
        Description: Initialization
        """   
        ogl.Shape.__init__(self)
        self.scaleFactor = zoomFactor
        self._isROI=1
        global count
        if not self.__class__ in count:
            count[self.__class__]=1
        self.setName("Polygon #%d"%count[self.__class__])
        count[self.__class__]+=1
        self.points = []
        self.tentativePoint = None
        self.minx,self.maxx, self.miny,self.maxy=9999,0,9999,0
        
    def getTentativeBB(self):
        """
        Created: 23.10.2006, KP
        Description: Return the BB that this polygon currently occupies
        """
        return self.minx,self.miny,self.maxx,self.maxy
        
    def getPoints(self):
        #print "Points in polygon=",self.points
        return self.points
    
    
    def setTentativePoint(self, pt):
        self.tentativePoint = pt
        x,y=pt
        if x<self.minx:
            self.minx=x
        if x>self.maxx:
            self.maxx=x
        if y>self.maxy:
            self.maxy=y
        if y<self.miny:
            self.miny=y
        
    def AddPoint(self, pt):
        if pt in self.points:
            return
        self.points.append(pt)
        x,y=pt
        if x<self.minx:
            self.minx=x
        if x>self.maxx:
            self.maxx=x
        if y>self.maxy:
            self.maxy=y
        if y<self.miny:
            self.miny=y        
        
    def OnDraw(self, dc):
        brush = wx.TRANSPARENT_BRUSH
        dc.SetBrush(brush)
        pen = wx.Pen(wx.Colour(255,0,0),1)
        dc.SetPen(pen)
        
        
        pts = self.points[:]
        if self.tentativePoint:
            pts.append(self.tentativePoint)
        dc.DrawPolygon(pts)
        del pts

    def setScaleFactor(self,factor):
        """
        Created: 21.06.2006, KP
        Description: Set the scaling factor in use
        """   
        pass
        

    def getCoveredPoints(self):
        return []

    def OnErase(self,dc):
        bg = self.GetCanvas().bgbuffer
        if not self._visible:
            return

        xp, yp = self.GetX(), self.GetY()
        minX, minY = self.GetBoundingBoxMin()
        maxX, maxY = self.GetBoundingBoxMax()

        topLeftX = xp - maxX / 2.0 - 2
        topLeftY = yp - maxY / 2.0 - 2

        penWidth = 0
        if self._pen:
            penWidth = self._pen.GetWidth()

        dc.SetPen(self.GetBackgroundPen())
        dc.SetBrush(self.GetBackgroundBrush())
        
        dc.SetClippingRegion(self.minx,self.miny,self.maxx,self.maxy)
        #dc.SetClippingRegion(topLeftX-penWidth,topLeftY-penWidth,maxX+penWidth*2+4, maxY + penWidth * 2 + 4)
        dc.DrawBitmap(bg,0,0)
        dc.DestroyClippingRegion()
        
    

class MyRectangle(OGLAnnotation, ogl.RectangleShape):   
    def __init__(self, w, h, zoomFactor = 1.0):
        """
        Created: 26.06.2006, KP
        Description: Initialization
        """   
        ogl.RectangleShape.__init__(self, w,h)
        self.scaleFactor = zoomFactor
        self._isROI=1
        global count
        if not self.__class__ in count:
            count[self.__class__]=1
        self.setName("Rectangle #%d"%count[self.__class__])
        count[self.__class__]+=1
        self.attrList = ["_width","_height","_xpos","_ypos"]

    def setScaleFactor(self,factor):
        """
        Created: 21.06.2006, KP
        Description: Set the scaling factor in use
        """   
        w,h,x,y = self._width,self._height,self.GetX(),self.GetY()
        w/=self.scaleFactor
        h/=self.scaleFactor
        x/=self.scaleFactor
        y/=self.scaleFactor
        self.scaleFactor = factor
        w*=self.scaleFactor
        h*=self.scaleFactor
        x*=self.scaleFactor
        y*=self.scaleFactor        
        
        print "Size of rectangle=",w,"x",h,"at",x,y
        self.SetWidth(w)
        self.SetHeight(h)
        self.SetX(x)
        self.SetY(y)    
        self.ResetControlPoints()
        

    def getCoveredPoints(self):
        cx, cy = self.GetX(), self.GetY()
        ox,oy = self.GetCanvas().getOffset()
        cx-=ox
        cy-=oy
        w, h = self._width, self._height
        cx /= self.scaleFactor
        cy /=self.scaleFactor
        w /=self.scaleFactor
        h /=self.scaleFactor
        pts={}
        w/=2.0
        h/=2.0
        print "Looping from ",cx-w,"to",cx+w
        print "Looping from ",cy-h,"to",cy+h
        print "Points tot",(2*w)*(2*h)
        fromx=int(math.ceil(cx-w))
        tox=int(math.floor(cx+w))
        fromy = int(math.ceil(cy-h))
        toy=int(math.floor(cy+h))
        for x in range(fromx,tox):
           for y in range(fromy,toy):
               pts[(x,y)] = 1
        return pts
               

    def OnErase(self,dc):
        bg = self.GetCanvas().bgbuffer
        if not self._visible:
            return

        xp, yp = self.GetX(), self.GetY()
        minX, minY = self.GetBoundingBoxMin()
        maxX, maxY = self.GetBoundingBoxMax()

        topLeftX = xp - maxX / 2.0 - 2
        topLeftY = yp - maxY / 2.0 - 2

        penWidth = 0
        if self._pen:
            penWidth = self._pen.GetWidth()

        dc.SetPen(self.GetBackgroundPen())
        dc.SetBrush(self.GetBackgroundBrush())
        
        dc.SetClippingRegion(topLeftX-penWidth,topLeftY-penWidth,maxX+penWidth*2+4, maxY + penWidth * 2 + 4)
        dc.DrawBitmap(bg,0,0)
        dc.DestroyClippingRegion()

       

class MyCircle(OGLAnnotation, ogl.CircleShape):    
    def __init__(self, diam, zoomFactor = 1.0):
        """
        Created: 26.06.2006, KP
        Description: Initialization
        """   
        ogl.CircleShape.__init__(self, diam)
        self.scaleFactor = zoomFactor
        self._isROI=1
        global count
        if not self.__class__ in count:
            count[self.__class__]=1
        self.setName("Circle #%d"%count[self.__class__])
        count[self.__class__]+=1
        self.attrList = ["_width","_height","_xpos","_ypos"]
        
    def setScaleFactor(self,factor):
        """
        Created: 21.06.2006, KP
        Description: Set the scaling factor in use
        """   
        w,h,x,y = self._width,self._height,self.GetX(),self.GetY()
        
        w/=self.scaleFactor
        h/=self.scaleFactor
        x/=self.scaleFactor
        y/=self.scaleFactor
        self.scaleFactor = factor
        w*=self.scaleFactor
        h*=self.scaleFactor
        x*=self.scaleFactor
        y*=self.scaleFactor        
        
        self.SetWidth(w)
        self.SetHeight(h)
        self.SetX(x)
        self.SetY(y)    
        self.ResetControlPoints()        
     
     
     
    def getCoveredPoints(self):
        cx, cy = self.GetX(), self.GetY()
        ox,oy = self.GetCanvas().getOffset()
        cx-=ox
        cy-=oy        
        
        cx//=self.scaleFactor
        cy//=self.scaleFactor
        
        w = self._width
        h = self._height
        w//=self.scaleFactor
        h//=self.scaleFactor
        
        a = max(w,h)/2
        b = min(w,h)/2
        
        c = math.sqrt(a**2-b**2)
        if w>h:
            f1 = (cx-c,cy)
            f2 = (cx+c,cy)
        else:
            f1 = (cx,cy-c)
            f2 = (cx,cy+c)
            

        pts={}
        def d(x,y):
            return math.sqrt((x[0]-y[0])**2+((x[1]-y[1])**2))
        for x in range(cx-w//2,cx+w//2):
            for y in range(cy-h/2,cy+h/2):
                #print "d=",(d((x,y),f1)+d((x,y),f2)),"2a=",2*a
                if (d((x,y),f1)+d((x,y),f2)) < a*2:
                    pts[(x,y)] = 1
        return pts
        
    
    def OnErase(self,dc):
        bg = self.GetCanvas().bgbuffer
        if not self._visible:
            return

        xp, yp = self.GetX(), self.GetY()
        minX, minY = self.GetBoundingBoxMin()
        maxX, maxY = self.GetBoundingBoxMax()

        topLeftX = xp - maxX / 2.0 - 2
        topLeftY = yp - maxY / 2.0 - 2

        penWidth = 0
        if self._pen:
            penWidth = self._pen.GetWidth()

        dc.SetPen(self.GetBackgroundPen())
        dc.SetBrush(self.GetBackgroundBrush())
        
        dc.SetClippingRegion(topLeftX-penWidth,topLeftY-penWidth,maxX+penWidth*2+4, maxY + penWidth * 2 + 4)
        dc.DrawBitmap(bg,0,0)
        dc.DestroyClippingRegion()

class MyPolygon(OGLAnnotation, ogl.PolygonShape):    
    def __init__(self, zoomFactor = 1.0):
        """
        Created: 26.06.2006, KP
        Description: Initialization
        """   
        ogl.PolygonShape.__init__(self)
        self.scaleFactor = zoomFactor
        self._isROI=1
        global count
        if not self.__class__ in count:
            count[self.__class__]=1
        self.setName("Polygon #%d"%count[self.__class__])
        count[self.__class__]+=1
        self.attrList = ["_points"]
        
    def __setstate__(self, state):
        """
        Created: 24.10.2006, KP
        Description: Reconstruct state of this object from given dictionary
        """
        for key in state.keys():
            self.getAttr(state,key)
        self.MakeControlPoints()
        
    
        
    def polyCenter(self,points):
        """
        Created: 16.06.2006, KP
        Description: Calculte the center of mass of polygon
        """          
        A=0
        for i,pt in enumerate(points[:-1]):
            
            x,y=pt
            A+=(x*points[i+1][1]-points[i+1][0]*y)
        A/=2.0
        
        cx = 0
        cy = 0
        
        for i,pt in enumerate(points[:-1]):
            x,y=pt
            cx+=(x+points[i+1][0])*(x*points[i+1][1]-points[i+1][0]*y)
            cy+=(y+points[i+1][1])*(x*points[i+1][1]-points[i+1][0]*y)
        cx /= 6.0*A
        cy /= 6.0*A
        return (cx,cy)
        
        
    def setScaleFactor(self,factor):
        """
        Created: 21.06.2006, KP
        Description: Set the scaling factor in use
        """   
        pts = []
        
        for x,y in self._points:
            x/=self.scaleFactor
            y/=self.scaleFactor
            x*=factor
            y*=factor
            pts.append((x,y))
        self._points = pts
        x/= self.scaleFactor
        y/=self.scaleFactor
        x*=factor
        y*=factor
        x,y = self.GetX(),self.GetY()
        self.SetX(x)
        self.SetY(y)
        self.UpdateOriginalPoints()
        self.scaleFactor = factor
        self.ResetControlPoints()    
        
    
    def getMinMaxXY(self):
        my,mx=10000,10000
        Mx,My=0,0
        for x,y in self._points:
            if x<mx:mx=x
            if y<my:my=y
            if x>Mx:Mx=x
            if y>My:My=y
        return mx,my,Mx,My
    def getCoveredPoints(self):
        x0,y0,x1,y1=self.getMinMaxXY()
        pts={}
        cx,cy = self.GetX(),self.GetY()
        ox,oy = self.GetCanvas().getOffset()
        cx-=ox
        cy-=oy        
        x0+=cx
        y0+=cy
        x1+=cx
        y1+=cy
        x0//=self.scaleFactor
        y0//=self.scaleFactor
        x1//=self.scaleFactor
        y1//=self.scaleFactor        
        cx//=self.scaleFactor
        cy//=self.scaleFactor
        
        poly = [(x//self.scaleFactor,y//self.scaleFactor) for x,y in self._points] 
        #poly = self._points
        #tot = (x1-x0)*(y1-y0)
        for x in range(x0,x1):
            for y in range(y0,y1):
                if self.collidepoint(poly,(x,y),cx,cy):                    
                    pts[(x,y)] = 1
                
        return pts

    def collidepoint(self,poly,point,cx,cy):
        """collidepoint(point) -> Whether the point is inside this polygon"""
        i,j,c=0,0,0
        #poly=self._points
        
        x,y=point
        x-=cx
        y-=cy
        l=len(poly)
        for i in range(0,l):
            j+=1
            if j==l:j=0
            if (((poly[i][1]<=y) and (y<poly[j][1])) or\
            ((poly[j][1]<=y) and (y<poly[i][1]))) and\
            (x<(poly[j][0]-poly[i][0])*(y-poly[i][1])/(poly[j][1]-poly[i][1])+poly[i][0]):
                c=not c
        return c
       
    def OnErase(self,dc):
        bg = self.GetCanvas().bgbuffer
        if not self._visible:
            return

        xp, yp = self.GetX(), self.GetY()
        minX, minY = self.GetBoundingBoxMin()
        maxX, maxY = self.GetBoundingBoxMax()

        topLeftX = xp - maxX / 2.0 - 2
        topLeftY = yp - maxY / 2.0 - 2

        penWidth = 0
        if self._pen:
            penWidth = self._pen.GetWidth()

        dc.SetPen(self.GetBackgroundPen())
        dc.SetBrush(self.GetBackgroundBrush())
        
        dc.SetClippingRegion(topLeftX-penWidth-4,topLeftY-penWidth-4,maxX+penWidth*2+8, maxY + penWidth * 2 + 8)
        dc.DrawBitmap(bg,0,0)
        dc.DestroyClippingRegion()

    # Make as many control points as there are vertices
    def MakeControlPoints(self):
        for point in self._points:
            control = MyPolygonControlPoint(self._canvas, self, ogl.CONTROL_POINT_SIZE, point, point[0], point[1])
            self._canvas.AddShape(control)
            self._controlPoints.append(control)
            
    def SetPointsFromControl(self,pt, end = 0):
        dc = wx.ClientDC(self.GetCanvas())
        self.GetCanvas().PrepareDC(dc)
        
        self.Erase(dc)
        
        for i,control in enumerate(self._controlPoints):
            self._points[i] = wx.RealPoint(control.GetX()-self._xpos,control.GetY()-self._ypos)
            self._originalPoints[i] = wx.RealPoint(control.GetX()-self._xpos,control.GetY()-self._ypos)
        self.CalculatePolygonCentre()
        self.CalculateBoundingBox()        
        
        
        dc.SetLogicalFunction(ogl.OGLRBLF)

        dottedPen = wx.Pen(wx.Colour(0, 0, 0), 1, wx.DOT)
        dc.SetPen(dottedPen)
        dc.SetBrush(wx.TRANSPARENT_BRUSH)
        
        if not end:
            self.GetEventHandler().OnDrawOutline(dc, self.GetX(), self.GetY(), self._originalWidth,self._originalHeight)
        else:
            self.GetEventHandler().OnDraw(dc, self.GetX(), self.GetY())
            
     
class MyPolygonControlPoint(ogl.PolygonControlPoint):

    # Implement resizing polygon or moving the vertex
    def OnDragLeft(self, draw, x, y, keys = 0, attachment = 0):
        #self._shape.GetEventHandler().OnSizingDragLeft(self, draw, x, y, keys, attachment)
        #self.CalculateNewSize(x,y)
        self.SetX(x)
        self.SetY(y)
        #print "Setting x,y to",x,y
        self._shape.SetPointsFromControl(self)    

    def OnErase(self,dc):
        bg = self.GetCanvas().bgbuffer
        if not self._visible:
            return

        xp, yp = self.GetX(), self.GetY()
        minX, minY = self.GetBoundingBoxMin()
        maxX, maxY = self.GetBoundingBoxMax()

        topLeftX = xp - maxX / 2.0 - 2
        topLeftY = yp - maxY / 2.0 - 2

        penWidth = 0
        if self._pen:
            penWidth = self._pen.GetWidth()

        dc.SetPen(self.GetBackgroundPen())
        dc.SetBrush(self.GetBackgroundBrush())
        
        dc.SetClippingRegion(topLeftX-penWidth-4,topLeftY-penWidth-4,maxX+penWidth*2+8, maxY + penWidth * 2 + 8)
        dc.DrawBitmap(bg,0,0)
        dc.DestroyClippingRegion()



    def OnBeginDragLeft(self, x, y, keys = 0, attachment = 0):
        #self._shape.GetEventHandler().OnSizingBeginDragLeft(self, x, y, keys, attachment)
        
        self.SetX(x)
        self.SetY(y)
        self._shape.SetPointsFromControl(self) 
    def OnEndDragLeft(self, x, y, keys = 0, attachment = 0):
        #self._shape.GetEventHandler().OnSizingEndDragLeft(self, x, y, keys, attachment)
        self._shape.SetPointsFromControl(self)    
        self._shape.ResetControlPoints()
        #self.GetCanvas().paintPreview()
        self.GetCanvas().repaintHelpers()
        # Uncomment
        self.GetCanvas().Refresh()
        
        #self.SetX(x)
        #self.SetY(y)
        #self._shape.SetPointsFromControl(self, end = 1) 


        

class MyEvtHandler(ogl.ShapeEvtHandler):
    def __init__(self,parent):
        self.parent = parent
        ogl.ShapeEvtHandler.__init__(self)
    def OnLeftDoubleClick(self, x, y, keys = 0, attachment = 0):
        
        shape = self.GetShape()
        flag=1
        if hasattr(shape,"OnDoubleClick"):
            flag=shape.OnDoubleClick(x,y)
            
        if flag and shape.isROI():
            print "Name of shape=",shape.getName()
            dlg = wx.TextEntryDialog(self.parent,
                    'What is the name of this Region of Interest',
                    'Name of the Region of Interest', shape.getName())
    
            dlg.SetValue(shape.getName())
    
            if dlg.ShowModal() == wx.ID_OK:
                value = dlg.GetValue()
                shape.setName(value)
                self.parent.repaintHelpers()
                self.parent.Refresh()
            dlg.Destroy()        

    def OnLeftClick(self, x, y, keys=0, attachment=0):
        shape = self.GetShape()
        #canvas = shape.GetCanvas()
        canvas = self.parent
        dc = wx.ClientDC(canvas)
        canvas.PrepareDC(dc)
        if shape.Selected():
            shape.Select(False, dc)
            
            #self.parent.diagram.Redraw(dc)
        else:
            redraw = False
            shapeList = canvas.GetDiagram().GetShapeList()
            toUnselect = []

            for s in shapeList:
                if s.Selected():
                    # If we unselect it now then some of the objects in
                    # shapeList will become invalid (the control points are
                    # shapes too!) and bad things will happen...
                    toUnselect.append(s)

            shape.Select(True, dc)

            if toUnselect:
                for s in toUnselect:
                    s.Select(False, dc)
                
            #self.parent.paintPreview(dc)
                #self.parent.diagram.Redraw(dc)
        
        self.parent.repaintHelpers()
        self.parent.Refresh()
        
    def OnDragLeft(self, draw, x, y, keys = 0, attachment = 0):
        print "OnDragLeft",x,y
        ogl.ShapeEvtHandler.OnDragLeft(self, draw, x,y, keys, attachment)
    
        self.parent.repaintHelpers()       
        #self.parent.Refresh()
    #def OnDragRight(self, draw, x, y, keys = 0, attachment = 0):
    #    print "OnDragRight"
    #    ogl.ShapeEvtHandler.OnDragRight(self, x, y, keys, attachment)


    def OnEndDragLeft(self, x, y, keys=0, attachment=0):
        shape = self.GetShape()
        print "OnEndDragLeft",x,y
        ogl.ShapeEvtHandler.OnEndDragLeft(self, x, y, keys, attachment)

        if not shape.Selected():
            self.OnLeftClick(x, y, keys, attachment)
        #self.parent.paintPreview()
        self.parent.repaintHelpers()
        self.parent.Refresh()
    def OnSizingEndDragLeft(self, pt, x, y, keys, attch):
        print "OnSizingEndDragLeft",x,y
        ogl.ShapeEvtHandler.OnSizingEndDragLeft(self, pt, x, y, keys, attch)
        
        #self.parent.paintPreview()
        self.parent.repaintHelpers()
        self.parent.Refresh()
    def OnMovePost(self, dc, x, y, oldX, oldY, display):
        print "OnMovePost"
        ogl.ShapeEvtHandler.OnMovePost(self, dc, x, y, oldX, oldY, display)

#        self.parent.paintPreview()
        #self.parent.Refresh()

    def OnRightClick(self, *args):
        shape = self.GetShape()
        if hasattr(shape,"OnRightClick"):
            shape.OnRightClick(*args)

