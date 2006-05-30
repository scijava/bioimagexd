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
class MyRectangle(ogl.RectangleShape):    
    def OnDrawControlPoints(self, dc):
        if not self._drawHandles:
            return

        dc.SetBrush(wx.BLACK_BRUSH)
        dc.SetPen(wx.BLACK_PEN)

        for control in self._controlPoints:
            control.SetPen(wx.WHITE_PEN)
            control.SetBrush(wx.WHITE_BRUSH)
            control.Draw(dc)

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

       

class MyCircle(ogl.CircleShape):    
    def OnDrawControlPoints(self, dc):
        if not self._drawHandles:
            return

        dc.SetBrush(wx.BLACK_BRUSH)
        dc.SetPen(wx.BLACK_PEN)

        for control in self._controlPoints:
            control.SetPen(wx.WHITE_PEN)
            control.SetBrush(wx.WHITE_BRUSH)
            control.Draw(dc)
    
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



class MyLine(ogl.LineShape):    
    def __init__(self):
        ogl.LineShape.__init__(self)
        self.endConnections = {0:(None,None),1:(None,None)}
        self.checked = 0
    def OnDrawControlPoints(self, dc):
        if not self._drawHandles:
            return

        dc.SetBrush(wx.BLACK_BRUSH)
        dc.SetPen(wx.BLACK_PEN)

        for control in self._controlPoints:
            control.SetPen(wx.WHITE_PEN)
            control.SetBrush(wx.WHITE_BRUSH)
            control.Draw(dc)
            
            
    def FindConnectedLines(self,diagram = None):        
        ex,ey,x,y = self.GetEnds()
        if not diagram:
            diagram = self.GetCanvas().GetDiagram()
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
                if p2 or p3:
                    if p2:p=0
                    if p3:p=1
                    
                    if not (self.GetEndConnected(0)[0] or i.GetEndConnected(p)[0]):
                        print "Connecting end ",p,"of ",i,"to end 0 of ",self
                        i.SetEndConnected((self,0),p)
                        self.SetEndConnected((i,p),0)
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
        
        self.CheckIfPolygon()
    
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
        
    def CheckIfPolygon(self):
        found=1
        found = self.CheckShape()
        
        if found:
            print "WE ARE FAMILY!"
            print "I GOT ALL MY LINES WITH ME"
            
        points = []
        
            
            
        
    
        
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
            
class MyPolygon(ogl.PolygonShape):    
    def OnDrawControlPoints(self, dc):
        if not self._drawHandles:
            return

        dc.SetBrush(wx.BLACK_BRUSH)
        dc.SetPen(wx.BLACK_PEN)

        for control in self._controlPoints:
            control.SetPen(wx.WHITE_PEN)
            control.SetBrush(wx.WHITE_BRUSH)
            control.Draw(dc)

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
        print "Setting x,y to",x,y
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
        print "OnEndDragLeft"
        ogl.ShapeEvtHandler.OnEndDragLeft(self, x, y, keys, attachment)

        if not shape.Selected():
            self.OnLeftClick(x, y, keys, attachment)
        self.parent.paintPreview()
        self.parent.Refresh()
    def OnSizingEndDragLeft(self, pt, x, y, keys, attch):
        print "OnSizingEndDragLeft"
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

