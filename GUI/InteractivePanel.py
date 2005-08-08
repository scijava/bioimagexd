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
from wx.lib.statbmp  import GenStaticBitmap as StaticBitmap
import ImageOperations
import Logging
import Annotation
import platform

ZOOM_TO_BAND=1
MANAGE_ANNOTATION=2
ADD_ANNOTATION=3
ADD_ROI=4
SET_THRESHOLD=5

class InteractivePanel(wx.ScrolledWindow):
    """
    Class: InteractivePanel
    Created: 03.07.2005, KP
    Description: A panel that can be used to select regions of interest, drawn
                 annotations on etc.
    """
    def __init__(self,parent,**kws):
        """
        Method: __init__(parent)
        Created: 24.03.2005, KP
        Description: Initialization
        """    
        self.is_windows=platform.system()=="Windows"
        size=(512,512)
        self.maxX=512
        self.maxY=512
        self.origX = 512
        self.origY = 512
        if "size" in kws:
            size=kws["size"]
        self.multiple=0
        self.dataUnit=None
        self.annotations=[]
        self.annotationClass=None
        self.currentAnnotation=None
        self.voxelSize=(1,1,1)
        self.bgColor=(0,0,0)
        if "bgColor" in kws:
            self.bgColor=kws["bgColor"]
        self.action=0
        self.imagedata=None
        self.bmp=None
        
        self.actionstart=(0,0)
        self.actionend=(0,0)
        
        x,y=size
        self.buffer = wx.EmptyBitmap(x,y)
        wx.ScrolledWindow.__init__(self,parent,-1,size=size)
        self.size=size

        self.zoomFactor=1
        
        self.paintPreview()
        self.Bind(wx.EVT_PAINT,self.OnPaint)

        self.Bind(wx.EVT_LEFT_DOWN,self.markActionStart)
        self.Bind(wx.EVT_MOTION,self.updateActionEnd)
        self.Bind(wx.EVT_LEFT_UP,self.executeAction)
        self.Bind(wx.EVT_RIGHT_UP,self.actionEnd)
        
        
    def setBackgroundColor(self,bg):
        """
        Method: setBackgroundColor(color)
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
        
    def markActionStart(self,event):
        """
        Method: markActionStart
        Created: 24.03.2005, KP
        Description: Sets the starting position of rubber band for zooming
        """    
        if not self.action:
            return False
            
        pos=event.GetPosition()
        if self.multiple and self.currentAnnotation:
            self.currentAnnotation.addPosition(pos)
            return

        x,y=pos
        foundDrawable=0
        for x0,x1,y0,y1 in self.getDrawableRectangles():
            if x>=x0 and x<=x1 and y>=y0 and y<=y1:
                foundDrawable=1 
                break
        if not foundDrawable:
            Logging.info("Attempt to draw in non-drawable area: %d,%d"%(x,y),kw="iactivepanel")
            # we zero the action so nothing further will be done by updateActionEnd
            self.action=0
            return
            
        self.actionstart=pos
        if self.action==MANAGE_ANNOTATION:
            self.findSelectedAnnotation()
            
    def updateActionEnd(self,event):
        """
        Method: updateActionEnd
        Created: 24.03.2005, KP
        Description: Draws the rubber band to current mou        
        """
        if not self.action:
            return
        if event.LeftIsDown():
            self.actionend=event.GetPosition()
            Logging.info("start=",self.actionstart,"end=",self.actionend,kw="iactivepanel")
            if self.action == ADD_ANNOTATION:
                self.updateObject(self.annotationClass,event)
            elif self.action == MANAGE_ANNOTATION:
                self.updateObject(self.annotationClass,event,moveOnly=1)
        self.updatePreview()
            
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
        if self.action==ZOOM_TO_BAND:
            self.zoomToRubberband(event)
        elif self.action==ADD_ANNOTATION:
            self.updateObject(self.annotationClass,event)
        elif self.action==SET_THRESHOLD:
            self.setThreshold()
        
        if not self.multiple:
            self.currentAnnotation=None
            self.action=0
        self.annotationClass=None
        
            
                
    def updateAnnotations(self):
        """
        Method: updateAnnotations()
        Created: 04.07.2005, KP
        Description: Update all the annotations
        """
        for i in self.annotations:
            i.setScaleFactor(self.zoomFactor)
                
    def updateObject(self,annotationClass,event=None,moveOnly=0):
        """
        Method: updateObject
        Created: 05.06.2005, KP
        Description: Draw a scale bar of given size
        """
        currobject=self.currentAnnotation  
        if not currobject:
            x0,y0=self.actionstart
            currobject=annotationClass(x0,y0,self.voxelSize,self.zoomFactor,bgColor=self.bgColor)
            self.annotations.append(currobject)
            self.currentAnnotation=currobject
            self.dataUnit.getSettings().set("Annotations",self.annotations)

        if not moveOnly:
            #Logging.info("Setting ",currobject,"to end at ",self.actionend,kw="iactivepanel")            Logging.info("Re-defining start ",self.actionstart,"and end ",self.actionend,"positions",kw="iactivepanel")
            currobject.setPosition(self.actionstart)
            currobject.setEndPosition(self.actionend)
        else:
            Logging.info("Moving annotation to ",self.actionend,kw="iactivepanel")
            currobject.setPosition(self.actionend)
                        

    def findSelectedAnnotation(self):
        """
        Method: findSelectedAnnotation(self)
        Created: 04.07.2005, KP
        Description: Find the annotation selected by clicking
        """
        x,y=self.actionstart
        for i in self.annotations:
            bmp=i.getAsBitmap()
            w,h=bmp.GetWidth(),bmp.GetHeight()
            x0,y0=i.pos
            if x>=x0 and y>=y0 and x<=x0+w and y<=y0+h:
                Logging.info("Annotation at %d,%d = %s"%(x,y,str(i.__class__)),kw="iactivepanel")
                self.currentAnnotation=i
                self.annotationClass=self.currentAnnotation.__class__
                break
        
    def markROI(self,roitype):
        """
        Method: markROI(roitype)
        Created: 05.07.2005
        Description: Add a ROI to the panel
        """
        Logging.info("Adding a %s region of interest"%roitype,kw="iactivepanel")
        self.action=ADD_ROI
        
    def startRubberband(self):
        """
        Method: startRubberband()
        Created: 03.07.2005
        Description: Start rubber band
        """
        self.action=ZOOM_TO_BAND
        
    def manageAnnotation(self):
        """
        Method: manageAnnotation()
        Created: 04.07.2005, KP
        Description: Manage annotations on the scene
        """
        self.action=MANAGE_ANNOTATION
        
    def addAnnotation(self,annClass,**kws):
        """
        Method: addAnnotation(annotationClass)
        Created: 04.07.2005, KP
        Description: Add an annotation to the scene
        """
        multiple=0
        if "multiple" in kws:
            multiple=kws["multiple"]
        self.multiple=multiple
        self.action=ADD_ANNOTATION
        self.annotationClass=annClass
        
    def zoomToRubberband(self,event):
        """
        Method: zoomToRubberband()
        Created: 24.03.2005, KP
        Description: Zooms to the rubberband
        """ 
        if not (self.rubberBanding or self.scaleDrawing):
            Logging.info("Not drawing rubberband,returning",kw="iactivepanel")
            return
        self.rubberBanding=0
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
        Method: getZoomFactor()
        Created: 1.08.2005, KP
        Description: Return the zoom factor
        """        
        return self.zoomFactor
    def getScrolledXY(self,x,y):
        """
        Method: getScrolledXY(x,y)
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
        Method: resetScroll()
        Created: 24.03.2005, KP
        Description: Sets the scrollbars to their initial values
        """    
        self.Scroll(0,0)            
        
    def setDataUnit(self,dataUnit):
        """
        Method: setDataUnit(self,dataUnit)
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
        Method: paintPreview()
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
                dc.EndDrawing()
                return
        dc=wx.BufferedPaintDC(self,self.buffer)#,self.buffer)


    def paintPreview(self):
        """
        Method: paintPreview()
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
        for i in self.annotations:
            i.drawToDC(dc)
        
        dc.EndDrawing()
        self.dc = None
        
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
            
        newy=self.maxY
        newx=self.maxX
        if xdim<self.maxX:
            newx=xdim
        if ydim<self.maxY:
            newy=ydim
        if newx<=self.origX:newx=self.origX
        if newy<=self.origY:newy=self.origY
        #s=self.GetSize()
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
        
