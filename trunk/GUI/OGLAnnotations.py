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
                        print "set widthMicro to=",self.widthMicro

                # when we set widthPx to 0 it will be recalculated below
                maxsize=0
            else:
                print "An integer width micro",self.widthMicro,"is ok"
        else:
            return
                
        if self.widthMicro and not maxsize:
            w=self.widthMicro/vx
            w*= self.scaleFactor
            

            if self.vertical:
                print "Setting height to",w
                self.SetHeight(int(w))
            else:
                print "Setting width to",w
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
        print "widthMicro=",self.widthMicro
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
        
    def OnDrawControlPoints(self, dc):
        if not self._drawHandles:
            return

        dc.SetBrush(wx.BLACK_BRUSH)
        dc.SetPen(wx.BLACK_PEN)

        for control in self._controlPoints:
            control.SetPen(wx.WHITE_PEN)
            control.SetBrush(wx.WHITE_BRUSH)
            control.Draw(dc)

    def getCoveredPoints(self):
        cx, cy = self.GetX(), self.GetY()
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
        
    def setScaleFactor(self,factor):
        """
        Method: setScaleFactor
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



class MyLine(OGLAnnotation, ogl.LineShape):    
    def __init__(self, zoomFactor = 1.0):
        """
        Method: __init__
        Created: 26.06.2006, KP
        Description: Initialization
        """   
        ogl.LineShape.__init__(self)
        self.endConnections = {0:(None,None),1:(None,None)}
        self.checked = 0
        self.scaleFactor = zoomFactor
        
    def setScaleFactor(self,factor):
        """
        Method: setScaleFactor
        Created: 21.06.2006, KP
        Description: Set the scaling factor in use
        """   
        w,h,x,y = self.GetEnds()
        
        w/=self.scaleFactor
        h/=self.scaleFactor
        x/=self.scaleFactor
        y/=self.scaleFactor
        self.scaleFactor = factor
        w*=self.scaleFactor
        h*=self.scaleFactor
        x*=self.scaleFactor
        y*=self.scaleFactor        
        self.SetEnds(w,h,x,y)
        self.ResetControlPoints() 
                    
    def FindConnectedLines(self,diagram = None):        
        ex,ey,x,y = self.GetEnds()
        if not diagram:
            diagram = self.GetCanvas().GetDiagram()
        found=0
        for i in diagram.GetShapeList():
            if isinstance(i,MyLine):
                x0,y0,x1,y1 = i.GetEnds()
                p0 = (abs(x0-x)<15 and abs(y0-y)<15)
                p1 = (abs(x1-x)<15 and abs(y1-y)<15)                        
                p2 = (abs(x0-ex)<15 and abs(y0-ey)<15)
                p3 = (abs(x1-ex)<15 and abs(y1-ey)<15)                        
                
                if p0 or p1:
                    if p0:p=0
                    if p1:p=1
                    if not (i.GetEndConnected(p)[0] or self.GetEndConnected(1)[0]):
                        print "Connecting end ",p,"of ",i,"to end 1 of ",self
                        i.SetEndConnected((self,1),p)
                        self.SetEndConnected((i,p),1)
                        found=1
                if p2 or p3:
                    if p2:p=0
                    if p3:p=1
                    
                    if not (self.GetEndConnected(0)[0] or i.GetEndConnected(p)[0]):
                        print "Connecting end ",p,"of ",i,"to end 0 of ",self
                        i.SetEndConnected((self,0),p)
                        self.SetEndConnected((i,p),0)
                        found=1
                        
                    break            

    def SetEndConnected(self,shape,end):
        self.endConnections[end] = shape
            
            
    def GetEndConnected(self,end):
        if end in self.endConnections:            
            return self.endConnections[end]
        return None,None
                        
    def MakeControlPoints(self):
        for point in self._lineControlPoints:            
            print "Creating control point at ",point
            x,y=point
            x-=self._lineControlPoints[0][0]
            y-=self._lineControlPoints[0][1]
            control = MyPolygonControlPoint(self._canvas, self, ogl.CONTROL_POINT_SIZE, point, x,y)
            self._canvas.AddShape(control)
            self._controlPoints.append(control)
            
        self.ResetControlPoints()
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
        
    def SetPointsFromControl(self,pt, end = 0):
        dc = wx.ClientDC(self.GetCanvas())
        self.GetCanvas().PrepareDC(dc)
        
        self.Erase(dc)
        #xoff=self._controlPoints[0][0]
        #yoff=self._controlPoints[0][1]        
        xoff=self._xpos
        yoff=self._ypos

        
        for i,control in enumerate(self._controlPoints):
            x,y = control.GetX(),control.GetY()
            self._lineControlPoints[i] = wx.RealPoint(x,y)
            #print self.endConnections
            if self.endConnections[i][0]:
                #print "Fixing connection ",i,"to",x,y
                shape,end = self.endConnections[i]
                #print "connected to end",end
                x0,y0,x1,y1 = shape.GetEnds()
                if end:
                    x1,y1=x,y
                else:
                    x0,y0=x,y
                shape.Erase(dc)
                shape.GetEventHandler().OnDraw(dc)
                
                shape.SetEnds(x0,y0,x1,y1)
                shape.ResetControlPoints()
                
        #self.FindConnectedLines()        
        self.GetEventHandler().OnDraw(dc)
        
        
    
    def CheckShape(self):
        if self.checked:
            return self.checked
        shape,end = self.GetEndConnected(0)
        shape2,end = self.GetEndConnected(1)
        
        
        if not shape or not shape2:
            self.checked = 0
            return 0
        print "Have both connections",self
        self.checked = 1
        if not shape.CheckShape():
            return 0
        if not shape2.CheckShape():
            return 0
            
        return 1
        
    def getPointList2(self,lines):
        pts=[]
        for i in lines:
            a,b,c,d = i.GetEnds()
            pts.append((a,b))
            pts.append((c,d))
            
        
        print "Orig list=",pts
        pts2=pts[:]
        i=0
        j=0
        ret=[]
        for x0,y0 in pts:
            dontadd=0
            for x1,y1 in ret:
                if (x0!=x1 and y0!=y1) and abs(math.sqrt((x1-x0)**2+(y1-y0)**2))<10:
                    dontadd=1
            if not dontadd:                
                ret.append((x0,y0))
                
        ret2=[]
        for i,pt in enumerate(ret):
            if not pt in ret[i+1:]:
                ret2.append(pt)
        print "Points=",ret2
        return ret2
        
    def getPointList(self):
        ret=[]
        lines=[]
        shape = self
        end=0
        while 1:
            if not shape:
                print "Didn't get shape, returning",lines
                ptlst=self.getPointList2(lines)
                return ptlst,lines

            shape2, end = shape.GetEndConnected(not end)            
            x=(not end)*2
            x2=x+2
            pts=shape.GetEnds()
            a,b=pts[x:x2]
        
            if shape in lines:
#            if (a,b) in ret:
                ptlst=self.getPointList2(lines)
                return ptlst,lines

                #return ret,lines
            if shape not in lines:
                lines.append(shape)
            ret.append((a,b))
            shape=shape2
        
    def __str__(self):
        return str(ogl.LineShape)+" "+str(self.GetEnds())
        
    def CheckIfPolygon(self):
        found=1
        found = self.CheckShape()        
        if found:            
            return self.getPointList()
        return None,None
        
        
    def ResetControlPoints(self):
        for i in range(min(len(self._lineControlPoints), len(self._controlPoints))):
            point = self._lineControlPoints[i]
#            xoff=self._lineControlPoints[0][0]
#            yoff=self._lineControlPoints[0][1]
            xoff=self._xpos
            yoff=self._ypos

            self._controlPoints[i]._xoffset = point[0]-xoff
            self._controlPoints[i]._yoffset = point[1]-yoff
            
            #print "Resetting point",i,"to",point[0]-xoff,point[1]-yoff
            
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
        self.GetCanvas().paintPreview()
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
        if shape.isROI():
            print "Name of shape=",shape.getName()
            dlg = wx.TextEntryDialog(self.parent,
                    'What is the name of this Region of Interest',
                    'Name of the Region of Interest', shape.getName())
    
            dlg.SetValue(shape.getName())
    
            if dlg.ShowModal() == wx.ID_OK:
                value = dlg.GetValue()
                shape.setName(value)
                self.parent.paintPreview()
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
        self.parent.paintPreview(dc)
        self.parent.Refresh()
        
    def OnEndDragLeft(self, x, y, keys=0, attachment=0):
        shape = self.GetShape()
        #print "OnEndDragLeft"
        ogl.ShapeEvtHandler.OnEndDragLeft(self, x, y, keys, attachment)

        if not shape.Selected():
            self.OnLeftClick(x, y, keys, attachment)
        self.parent.paintPreview()
        self.parent.Refresh()
    def OnSizingEndDragLeft(self, pt, x, y, keys, attch):
        #print "OnSizingEndDragLeft"
        ogl.ShapeEvtHandler.OnSizingEndDragLeft(self, pt, x, y, keys, attch)
        
        self.parent.paintPreview()
        self.parent.Refresh()
    def OnMovePost(self, dc, x, y, oldX, oldY, display):
        print "OnMovePost"
        ogl.ShapeEvtHandler.OnMovePost(self, dc, x, y, oldX, oldY, display)
        canvas = self.parent
        shape = self.GetShape()
        dc = wx.ClientDC(canvas)
        canvas.PrepareDC(dc)
        shape.Erase(dc)
        
#        self.parent.paintPreview()
        self.parent.Refresh()

    def OnRightClick(self, *args):
        shape = self.GetShape()
        if hasattr(shape,"OnRightClick"):
            shape.OnRightClick(*args)

