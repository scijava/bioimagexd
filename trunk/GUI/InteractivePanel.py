# -*- coding: iso-8859-1 -*-

"""
 Unit: InteractivePanel
 Project: BioImageXD
 Created: 24.03.2005, KP
 Description:

 A panel that can select regions of interest, draw annotations, etc.
         
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

import ImageOperations
import Logging
import platform
import wx.lib.ogl as ogl
import messenger

import math
ZOOM_TO_BAND=1
MANAGE_ANNOTATION=2
ADD_ANNOTATION=3
ADD_ROI=4
SET_THRESHOLD=5
DELETE_ANNOTATION=6

from OGLAnnotations import *

#class InteractivePanel(wx.ScrolledWindow):
class InteractivePanel(ogl.ShapeCanvas):
    """
    Class: InteractivePanel
    Created: 03.07.2005, KP
    Description: A panel that can be used to select regions of interest, drawn
                 annotations on etc.
    """
    def __init__(self,parent,**kws):
        """
        Created: 24.03.2005, KP
        Description: Initialization
        """    
        self.parent=parent
        self.is_windows=1#=platform.system()=="Windows"
        self.maxX=512
        self.maxY=512
        self.maxSizeX=512
        self.maxSizeY=512
        self.origX = 512
        self.origY = 512
        size=kws.get("size",(512,512))
        self.multiple=0
        self.dataUnit=None
        ogl.OGLInitialize()
        
        self.annotations=[]
        self.annotationClass=None
        self.currentAnnotation=None
        self.voxelSize=(1,1,1)
        self.bgColor = kws.get("bgColor",(0,0,0))
        self.action=0
        self.imagedata=None
        self.bmp=None
        
        self.actionstart=(0,0)
        self.actionend=(0,0)
        self.prevPolyEnd=None
        
        x,y=size
        self.buffer = wx.EmptyBitmap(x,y)
        #wx.ScrolledWindow.__init__(self,parent,-1,size=size)
        ogl.ShapeCanvas.__init__(self,parent,-1,size=size)
        
        self.diagram = ogl.Diagram()
        self.SetDiagram(self.diagram)
        self.diagram.SetCanvas(self)
        
        self.size=size
    
        self.lines = []
        

        self.zoomFactor=1
        
        
        self.paintPreview()
        
        self.Unbind(wx.EVT_PAINT)
        self.Bind(wx.EVT_PAINT,self.OnPaint)
        

        self.Bind(wx.EVT_LEFT_DOWN,self.markActionStart)
        self.Bind(wx.EVT_MOTION,self.updateActionEnd)
        self.Bind(wx.EVT_RIGHT_UP,self.onCheckPolygon)
        self.Bind(wx.EVT_LEFT_UP,self.executeAction)
        #self.Bind(wx.EVT_RIGHT_UP,self.actionEnd)
        self.Bind(wx.EVT_SIZE,self.OnSize)
        
        #messenger.connect(None,"create_polygon",self.onCreatePolygon)
        
    def deleteLines(self,lines):
        """
        Method: onEraseLines
        Created: 08.06.2006, KP
        Description: Erase the given lines from this canvas
        """            
        for line in lines:
            print "Deleting",line            
            line.Delete()
            self.RemoveShape(line)
            self.lines.remove(line)
            del line
            
    def getRegionsOfInterest(self):
        """
        Created: 04.08.2006
        Description: Return all the regions of interest draw in this panel    
        """
        shapelist = self.diagram.GetShapeList()
        rois=[]
        for shape in shapelist:
            if isinstance(shape,OGLAnnotation) and shape.isROI():
                rois.append(shape)
        return rois
        
    def roiToMask(self):
        """
        Created: 20.06.2006, KP
        Description: Convert the selected ROI to mask
        """
        mx,my,mz = self.dataUnit.getDimensions()
        rois=self.getRegionsOfInterest()
        names=[roi.getName() for roi in rois]
        print "Dimensions=",mx,my,mz
        print "Rois=",rois
        maskImage = ImageOperations.getMaskFromROIs(rois,mx,my,mz)
        
        return maskImage,names
        
    def polyCenter(self,points):
        """
        Method: polyCenter
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
        
    def createPolygon(self,points):
        """
        Method: createPolygon
        Created: 07.05.2006, KP
        Description: Create a polygon
        """            
        shape = MyPolygon(zoomFactor = self.zoomFactor)
        pts=[]
        print "points=",points
        #shape.SetCentreResize(0)
        mx,my= self.polyCenter(points)
        print "Center of polygon=",mx,my
        
        for x,y in points:
            pts.append((((x-mx)),((y-my))))
        shape.Create(pts)
        shape.SetX(mx)
        shape.SetY(my)
        self.addNewShape(shape)
        
        self.paintPreview()
        self.Refresh()
        print "Added",shape,pts
                    

    def OnSize(self,evt):
        """
        Created: 11.08.2005, KP
        Description: The size evet
        """            
        self.maxSizeX,self.maxSizeY=self.parent.GetClientSize()
        evt.Skip()
        
    def setBackgroundColor(self,bg):
        """
        Created: 04.07.2005, KP
        Description: Sets the background color
        """    
        self.bgColor=bg
        
    def getDrawableRectangles(self):
        """
        Method: getDrawableRectangles()
        Created: 04.07.2005, KP
        Description: Return the rectangles can be drawn on as four-tuples
        """    
        w=self.buffer.GetWidth()
        h=self.buffer.GetHeight()
        return [(0,w,0,h)]
        
    def onLeftDown(self,event):
        return self.markActionStart(event)
        
    def onCheckPolygon(self,event):
        lst=self.lines
        lst.reverse()
        for shape in lst:
            #points,lines = shape.CheckIfPolygon()
            points, lines = shape.getPointList()
            if points:
                print "got",points,lines
                print "Is a polygon, deleting lines..."
                self.deleteLines(lines)
                self.createPolygon(points)
                self.action = None
                self.actionstart = (0,0)
                self.actionend = (0,0)
                self.prevPolyEnd = None

        del lst
        event.Skip()        
    def markActionStart(self,event):
        """
        Method: markActionStart
        Created: 24.03.2005, KP
        Description: Sets the starting position of rubber band for zooming
        """    
        event.Skip()
        
            
        pos=event.GetPosition()

        x,y=pos
        foundDrawable=0
        for x0,x1,y0,y1 in self.getDrawableRectangles():
            if x>=x0 and x<=x1 and y>=y0 and y<=y1:
                foundDrawable=1 
                break
        event.Skip()                    
        if not foundDrawable:
            Logging.info("Attempt to draw in non-drawable area: %d,%d"%(x,y),kw="iactivepanel")
            # we zero the action so nothing further will be done by updateActionEnd
            self.action=0
            
            return 1
            
        self.actionstart=pos
        return 1
    def updateActionEnd(self,event):
        """
        Method: updateActionEnd
        Created: 24.03.2005, KP
        Description: Draws the rubber band to current mou        
        """
        if event.LeftIsDown():
            self.actionend=event.GetPosition()
        event.Skip()
            
    def actionEnd(self,event):
        """
        Method: actionEnd
        Created: 05.07.2005, KP
        Description: Unconditionally end the current action
        """    
        self.currentAnnotation=None
        self.action=0
        self.annotationClass=None
        event.Skip()
        
    def executeAction(self,event):
        """
        Method: executeAction
        Created: 03.07.2005, KP
        Description: Call the right callback depending on what we're doing
        """    
        #Logging.info("Executing action: ",self.action,kw="iactivepanel")
        
        if self.action==ZOOM_TO_BAND:
            self.zoomToRubberband(event)
        elif self.action==ADD_ANNOTATION:
            #self.updateObject(self.annotationClass,event
            print "Adding annotation"
            x,y=event.GetPosition()
            ex,ey = self.actionstart
            
            if self.annotationClass == "CIRCLE":
                
                
                diff = max(abs(x-ex),abs(y-ey))
                if diff<2:diff=2
                shape = MyCircle(2*diff,zoomFactor = self.zoomFactor)
                print "start=",ex,ey
                shape.SetX( ex )
                shape.SetY( ey )

            elif self.annotationClass == "RECTANGLE":
                dx = abs(x-ex)
                dy = abs(y-ey)
                shape = MyRectangle(dx,dy, zoomFactor = self.zoomFactor)
                shape.SetCentreResize(0)  
                shape.SetX( ex+(x-ex)/2 )
                shape.SetY( ey+(y-ey)/2 )
  
            elif self.annotationClass == "POLYGON":
                #shape = MyPolygon()
                shape = MyLine(zoomFactor = self.zoomFactor)
                
                shape.MakeLineControlPoints(2)
                if self.prevPolyEnd:
                    ex,ey = self.prevPolyEnd
                shape.SetEnds(ex,ey,x,y)
                shape.FindConnectedLines(self.diagram)                               
                
                #shape.Create([(10.1,10.1),(10.1,100.1),(100.0,100.1),(100.0,10.1)])
                shape.SetCentreResize(0)    
                self.lines.append(shape)
            elif self.annotationClass == "SCALEBAR":
                dx = abs(x-ex)
                dy = abs(y-ey)
                shape = MyScalebar(dx,dy, voxelsize = self.voxelSize, zoomFactor = self.zoomFactor)
                shape.SetCentreResize(0)  
                shape.SetX( ex+(x-ex)/2 )
                shape.SetY( ey+(y-ey)/2 )
            
            self.addNewShape(shape)
            
            if self.annotationClass=="POLYGON":
                self.actionstart=self.actionend   
                self.prevPolyEnd = self.actionend
            else:
                self.action = None
                self.actionstart = (0,0)
                self.actionend = (0,0)
                self.prevPolyEnd=None
                
            messenger.send(None,"update_annotations")

            #self.updateAnnotations()
            return 1
        elif self.action==SET_THRESHOLD:
            self.setThreshold()
        elif self.action==DELETE_ANNOTATION:            
            x,y = self.actionstart
            
            print "Deleting annotation at",x,y
            obj,attach = self.FindShape(x,y)
            if obj:
                print "Deleting",obj
                self.RemoveShape(obj)
                obj.Delete()            
                self.paintPreview()
                self.Refresh()
                
        if not self.multiple:
            self.currentAnnotation=None
            self.action=0
        self.annotationClass=None                    
        #ogl.ShapeCanvas.OnMouseEvent(self,event)
        event.Skip()
    
    def addNewShape(self, shape):
        """
        Method: addNewShape
        Created: 07.05.2005, KP
        Description: Add a new shape to the canvas
        """        
        evthandler = MyEvtHandler(self)
        evthandler.SetShape(shape)
        evthandler.SetPreviousHandler(shape.GetEventHandler())
        shape.SetEventHandler(evthandler)
        shape.SetDraggable(True, True)
        shape.SetCanvas(self)
        shape.SetBrush(wx.TRANSPARENT_BRUSH)
        shape.SetPen(wx.Pen((0,255,0),1))
        
        self.AddShape( shape )                   
        self.diagram.ShowAll( 1 )           
        self.Refresh()        
        
    def updateAnnotations(self):
        """
        Method: updateAnnotations()
        Created: 04.07.2005, KP
        Description: Update all the annotations
        """
        for i in self.diagram.GetShapeList():
            if hasattr(i,"setScaleFactor"):
                i.setScaleFactor(self.zoomFactor)
        
    def markROI(self,roitype):
        """
        Created: 05.07.2005
        Description: Add a ROI to the panel
        """
        Logging.info("Adding a %s region of interest"%roitype,kw="iactivepanel")
        self.action=ADD_ROI
        
    def startRubberband(self):
        """
        Created: 03.07.2005
        Description: Start rubber band
        """
        self.action=ZOOM_TO_BAND
        
    def manageAnnotation(self):
        """
        Created: 04.07.2005, KP
        Description: Manage annotations on the scene
        """
        self.action=MANAGE_ANNOTATION
        
    def deleteAnnotation(self):
        """
        Created: 15.08.2005, KP
        Description: Delete annotations on the scene
        """
        self.action=DELETE_ANNOTATION        
        
    def addAnnotation(self,annClass,**kws):
        """
        Created: 04.07.2005, KP
        Description: Add an annotation to the scene
        """
        self.multiple = kws.get("multiple",0)
        self.action=ADD_ANNOTATION
        self.annotationClass=annClass
        
        
    def zoomToRubberband(self,event):
        """
        Created: 24.03.2005, KP
        Description: Zooms to the rubberband
        """ 
        x1,y1=self.actionstart
        x2,y2=self.actionend
        Logging.info("Zooming to rubberband defined by (%d,%d),(%d,%d)"%(x1,y1,x2,y2),kw="iactivepanel")
        
        self.actionstart=(0,0)
        self.actionend=(0,0)
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
        
    def getZoomFactor(self):
        """
        Created: 1.08.2005, KP
        Description: Return the zoom factor
        """        
        return self.zoomFactor
        
    def getScrolledXY(self,x,y):
        """
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
        Created: 24.03.2005, KP
        Description: Sets the scrollbars to their initial values
        """    
        self.Scroll(0,0)            
        
    def setDataUnit(self,dataUnit):
        """
        Created: 04.07.2005, KP
        Description: Sets the data unit that is displayed
        """    
        self.dataUnit=dataUnit
        self.voxelSize=dataUnit.getVoxelSize()
        x,y,z=self.dataUnit.getDimensions()
        self.buffer = wx.EmptyBitmap(x,y)
        self.origX, self.origY = x,y
        Logging.info("Got dataunit, voxelSize=",self.voxelSize,kw="iactivepanel")
        ann=dataUnit.getSettings().get("Annotations")
        if ann:
            Logging.info("Got %d annotations"%len(ann),kw="iactivepanel")
            self.annotations=ann
            
    def OnPaint(self,event):
        """
        Created: 28.04.2005, KP
        Description: Does the actual blitting of the bitmap
        """
        if self.is_windows:
            x,y=self.GetViewStart()
            if x or y:
                #Logging.info("Resorting to unbuffered drawing because of scrolling",kw="iactivepanel")
                dc=wx.PaintDC(self)
                
                self.PrepareDC(dc)
                dc.BeginDrawing()
                dc.DrawBitmap(self.buffer,0,0,False)
                self.diagram.Redraw(dc)                
                dc.EndDrawing()
                return

        self.bgbuffer = self.buffer.GetSubBitmap(wx.Rect(0,0,self.buffer.GetWidth(),self.buffer.GetHeight()))
        dc=wx.BufferedPaintDC(self,self.buffer)#,self.buffer)
        self.diagram.Redraw(dc)


    def paintPreview(self):
        """
        Created: 24.03.2005, KP
        Description: Paints the image to a DC
        """
                     
        dc=self.dc
        bmp=self.bmp
        
        w,h=bmp.GetWidth(),bmp.GetHeight()
        
        w*=self.zoomx
        h*=self.zoomy
        if self.action==ZOOM_TO_BAND:
            if self.actionstart and self.actionend:
                x1,y1=self.actionstart
                x2,y2=self.actionend
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

        #Logging.info("%d annotations to paint"%len(self.annotations),kw="iactivepanel")
        #for i in self.annotations:
        #    i.drawToDC(dc)
        
        #dc.EndDrawing()
        #self.dc = None
        
    def setScrollbars(self,xdim,ydim):
        """
        Created: 24.03.2005, KP
        Description: Configures scroll bar behavior depending on the
                     size of the dataset, which is given as parameters.
        """
        w,h=self.buffer.GetWidth(),self.buffer.GetHeight()
        
        if w!=xdim or h!=ydim:
            self.buffer = wx.EmptyBitmap(xdim,ydim)

        maxX=self.maxX
        maxY=self.maxY
        if self.maxSizeX>maxX:maxX=self.maxSizeX
        if self.maxSizeY>maxY:maxY=self.maxSizeY
        Logging.info("maxX=",self.maxX,"maxSizeX=",self.maxSizeX,"xdim=",xdim,"origX=",self.origX,kw="iactivepanel");
        newy=maxY
        newx=maxX
        if xdim<maxX:
            newx=xdim
        if ydim<maxY:
            newy=ydim
        if newx<=self.origX and self.origX<=self.maxSizeX:
            newx=self.origX
        if newy<=self.origY and self.origY<=self.maxSizeY:
            newy=self.origY
        s=self.GetSize()
        #if s!=(newx,newy):
        Logging.info("Setting size of",self," to ",newx,newy,"virtual size to ",xdim,ydim,kw="iactivepanel")
        self.SetSize((newx,newy))
        s=self.GetVirtualSize()
        #if s!=(xdim,ydim):
        self.SetVirtualSize((xdim,ydim))
        xrate,yrate=0,0
        if xdim>newx:
            xrate=self.scrollsize
        if ydim>newy:
            yrate=self.scrollsize
       
        self.SetScrollRate(xrate,yrate)
        
