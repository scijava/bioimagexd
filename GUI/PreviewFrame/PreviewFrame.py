# -*- coding: iso-8859-1 -*-

"""
 Unit: PreviewFrame.py
 Project: BioImageXD
 Created: 03.11.2004
 Creator: KP
 Description:

 A widget that can be used to Preview any operations done by a subclass of Module

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
__version__ = "$Revision: 1.63 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import os.path,sys
#from enthought.tvtk import messenger
import messenger

import ImageOperations

import PreviewPanel
import time

from GUI import Events
import Logging

import vtk
import wx

ZOOM_TO_FIT=-1


class PreviewFrame(wx.Panel):
    """
    Class: PreviewFrame
    Created: 03.11.2004, KP
    Description: A widget that uses the wxVTKRenderWidget to display a preview
                 of operations done by a subclass of Module
    """
    def __init__(self,parent,parentwin=None,**kws):
        """
        Method: __init__(parent)
        Created: 03.11.2004, KP
        Description: Initialization
        Parameters:
               master  The widget containing this preview
        """
        wx.Panel.__init__(self,parent,-1)
        self.parent=parent
        self.depthT=0
        self.timeT=0
        self.finalImage=None
        self.xdiff,self.ydiff=0,0
        self.updateFactor = 0.001
        self.zoomFactor=1
        self.selectedItem=-1
        size=(512,512)
        self.oldx,self.oldy=0,0
        self.show={}
        self.show["PIXELS"]=1
        self.show["TIMESLIDER"]=1
        self.show["ZSLIDER"]=1
        self.show["SCROLL"]=1
        self.modeChoice = None
        self.zoomx,self.zoomy=1,1
        Logging.info("kws=",kws,kw="preview")
        if not parentwin:
            parentwin=parent
        self.parentwin=parentwin
        if kws.has_key("zslider"):
            self.show["ZSLIDER"]=kws["zslider"]
        if kws.has_key("previewsize"):
            size=kws["previewsize"]
            Logging.info("Got previewsize=",size,kw="preview")
        if kws.has_key("pixelvalue"):
            self.show["PIXELS"]=kws["pixelvalue"]
        if kws.has_key("timeslider"):
            self.show["TIMESLIDER"]=kws["timeslider"]
        if kws.has_key("zoom_factor"):
            self.zoomFactor=kws["zoom_factor"]
        if kws.has_key("zoomx"):
            self.zoomx=kws["zoomx"]
        if kws.has_key("zoomy"):
            self.zoomy=kws["zoomy"]
        if kws.has_key("scrollbars"):
            self.show["SCROLL"]=kws["scrollbars"]
        
        self.dataUnit=None
        self.rgbMode=0
        
        self.sizer=wx.GridBagSizer()
        self.previewsizer=wx.BoxSizer(wx.VERTICAL)
        # These are the current image and color transfer function
        # They are used when getting the value of a pixel
        self.currentImage=None
        self.currentCt=None
        Logging.info("Creating preview panel with size=",size,kw="preview")
        self.renderpanel = PreviewPanel.PreviewPanel(self,size=size,scroll=self.show["SCROLL"],zoomx=self.zoomx,zoomy=self.zoomy)
        self.sizer.Add(self.renderpanel,(0,0))
        
        # The preview can be no larger than these
        self.maxX,self.maxY=size
        self.xdim,self.ydim,self.zdim=0,0,0
                       
        if self.show["PIXELS"]:
            self.renderpanel.Bind(wx.EVT_LEFT_DOWN,self.getPixelValue)
        
        self.renderpanel.Bind(wx.EVT_LEFT_UP,self.getVoxelValue)
        
        if self.show["TIMESLIDER"]:
            self.timeslider=wx.Slider(self,value=0,minValue=0,maxValue=1,size=(300,-1),
            style=wx.SL_HORIZONTAL|wx.SL_AUTOTICKS|wx.SL_LABELS)
            self.sizer.Add(self.timeslider,(1,0),flag=wx.EXPAND|wx.LEFT|wx.RIGHT)
            self.timeslider.Bind(wx.EVT_SCROLL,self.updateTimePoint)
        if self.show["ZSLIDER"]:
            self.zslider=wx.Slider(self,value=0,minValue=0,maxValue=100,size=(-1,300),
            style=wx.SL_VERTICAL|wx.SL_AUTOTICKS|wx.SL_LABELS)
            self.zslider.Bind(wx.EVT_SCROLL,self.setPreviewedSlice)
            self.sizer.Add(self.zslider,(0,1),flag=wx.EXPAND|wx.TOP|wx.BOTTOM)

        if self.show["PIXELS"]:
            self.pixelPanel=wx.Panel(self,-1)
            self.pixelLbl=wx.StaticText(self.pixelPanel,-1,"Scalar 0 at (0,0,0) maps to (0,0,0)")
            self.sizer.Add(self.pixelPanel,(3,0),flag=wx.EXPAND|wx.RIGHT)

        self.running=0

        self.rgb=(255,255,0)

        self.z=0
        self.timePoint=0
        
        self.SetAutoLayout(True)
        self.SetSizer(self.sizer)
        self.sizer.Fit(self)
        self.sizer.SetSizeHints(self)
        
    def setSelectedItem(self,item):
        """
        Method: setSelectedItem(n)
        Created: 05.04.2005, KP
        Description: Set the item selected for configuration
        """
        Logging.info("Selected item "+str(item),kw="preview")
        self.selectedItem = item
        self.settings = self.dataUnit.getSourceDataUnits()[item].getSettings()
        self.settings.set("PreviewedDataset",item)
        self.updatePreview(1)
        
                
        
    def getVoxelValue(self,event):
        """
        Method: getVoxelValue(event)
        Created: 23.05.2005, KP
        Description: Send an event containing the current voxel position
        """
        if not self.currentImage:
            return
        x,y=event.GetPosition()
        x,y=self.renderpanel.getScrolledXY(x,y)
        z=self.z
        dims=[x,y,z]
        rx,ry,rz=dims
        Logging.info("Returning x,y,z=(%d,%d,%d)"%(rx,ry,rz))
        messenger.send(None,"get_voxel_at",rx,ry,rz)
        event.Skip()
    
    def getPixelValue(self,event):
        """
        Method: getPixelValue(event)
        Created: 10.11.2004, KP
        Description: Shows the RGB and scalar value of a clicked pixel
        """
        if not self.currentImage:
            return
        x,y=event.GetPosition()
        x,y=self.renderpanel.getScrolledXY(x,y)
        
        
        if self.rgbMode==0:
            scalar=self.currentImage.GetScalarComponentAsDouble(x,y,self.z,0)
            val=[0,0,0]
            self.currentCt.GetColor(scalar,val)
            r,g,b=val
            r*=255
            g*=255
            b*=255
            frgb=(255-r,255-g,255-b)
            self.pixelLbl.SetForegroundColour(frgb)
            self.pixelPanel.SetBackgroundColour((r,g,b))
            self.pixelLbl.SetBackgroundColour((r,g,b))
            self.pixelLbl.SetLabel("Scalar %d at (%d,%d,%d) maps to (%d,%d,%d)"%\
            (scalar,x,y,self.z,r,g,b))
        else:
            r=self.currentImage.GetScalarComponentAsDouble(x,y,self.z,0)
            g=self.currentImage.GetScalarComponentAsDouble(x,y,self.z,1)
            b=self.currentImage.GetScalarComponentAsDouble(x,y,self.z,2)
            alpha=-1
            if self.currentImage.GetNumberOfScalarComponents()>3:
                alpha=self.currentImage.GetScalarComponentAsDouble(x,y,self.z,3)
            frgb=(255-r,255-g,255-b)
            self.pixelLbl.SetForegroundColour(frgb)
            self.pixelPanel.SetBackgroundColour((r,g,b))
            self.pixelLbl.SetBackgroundColour((r,g,b))
            txt="Color at (%d,%d,%d) is (%d,%d,%d)"%(x,y,self.z,r,g,b)
            if alpha!=-1:
                txt=txt+" with alpha %d"%alpha
            self.pixelLbl.SetLabel(txt)
        event.Skip()
            
    def setPreviewedSlice(self,event,val=-1):
        """
        Method: setPreviewedSlice()
        Created: 4.11.2004, KP
        Description: Sets the preview to display the selected z slice
        """
        t=time.time()
        if abs(self.depthT-t) < self.updateFactor: return
        self.depthT=time.time()
        if event:
            newz=self.zslider.GetValue()
        else:
            newz=val
        if self.z!=newz:
            self.z=newz
#            print "Sending zslice changed event"
            messenger.send(None,"zslice_changed",newz)
            
            # was updatePreview(1)
            self.updatePreview(0)

    def setTimepoint(self,tp):
        """
        Method: setTimepoint(tp)
        Created: 09.12.2004, KP
        Description: The previewed timepoint is set to the given timepoint
        Parameters:
                tp      The timepoint to show
        """
        if self.show["TIMESLIDER"]:
            self.timeslider.SetValue(tp)
        
        self.updateTimePoint(None,tp)

    def updateTimePoint(self,event,tp=-1):
        """
        Method: updateTimePoint()
        Created: 04.11.2004, KP
        Description: Sets the time point displayed in the preview
        """
        t=time.time()
        if abs(self.timeT-t) < self.updateFactor: return
        self.timeT=time.time()

        if self.show["TIMESLIDER"]:
            timePoint=self.timeslider.GetValue()
        else:
            timePoint=tp
#        print "Use time point %d"%timePoint
        if self.timePoint!=timePoint:
            self.timePoint=timePoint
            self.updatePreview(1)
            messenger.send(None,"timepoint_changed",timePoint)
                
    def setZoomCombobox(self,combo):
        """
        Method: setZoomCombobox(combo)
        Created: 19.03.2005, KP
        Description: Set the combo box that shows the zoom percentage
        """        
        self.zoomCombo = combo

    def setDataUnit(self,dataUnit,selectedItem=-1):
        """
        Method: setDataUnit(dataUnit)
        Created: 04.11.2004, KP
        Description: Set the dataunit used for preview. Should be a combined 
                     data unit, the source units of which we can get and read 
                     as ImageData
        """
        self.dataUnit=dataUnit
        self.settings = dataUnit.getSettings()
        self.renderpanel.setDataUnit(self.dataUnit)
        
        try:
            count=dataUnit.getLength()
            x,y,z=dataUnit.getDimensions()
        except Logging.GUIError, ex:
            ex.show()
            return
            
        dims=[x,y,z]
        self.xdim,self.ydim,self.zdim=x,y,z
        
        if self.show["ZSLIDER"]:
            #print "zslider goes to %d"%(z-1)
            self.zslider.SetRange(0,z-1)
        if x>self.maxX or y>self.maxY:
            Logging.info("Setting scrollbars to %d,%d"%(x,y),kw="preview")
            self.renderpanel.setScrollbars(x,y)
        
        if x>self.maxX:x=self.maxX
        if y>self.maxY:y=self.maxY
        
        if self.show["TIMESLIDER"]:
            self.timeslider.SetRange(0,count-1)

        x*=self.zoomx
        y*=self.zoomy
        Logging.info("Setting renderpanel to %d,%d"%(x,y),kw="preview")
        self.renderpanel.SetSize((x,y))
        

        if selectedItem!=-1:
            self.setSelectedItem(selectedItem)

        if self.zoomFactor:
            #print "Got zoom factor",
            if self.zoomFactor == ZOOM_TO_FIT:
                Logging.info("Factor = zoom to fit",kw="preview")
                self.renderpanel.zoomToFit()
                self.updatePreview(1)
            else:
                #print "Factor = ",self.zoomFactor
                self.renderpanel.setZoomFactor(self.zoomFactor)
                self.updatePreview(1)
        

        self.renderpanel.Layout()
        self.Layout()
        self.parent.Layout()
        self.sizer.Fit(self)
        self.updatePreview(1)
        #self.sizer.SetSizeHints(self)

    def updatePreview(self,renew=1):
        """
        Method: updatePreview(renew=1)
        Created: 03.11.2004,MIP KP
        Description: Update the preview
        Parameters:
            renew    Whether the method should recalculate the images
        """
        raise "updatePreview() called from the base class"
       
    def saveSnapshot(self,filename):
        """
        Method: saveSnapshot(filename)
        Created: 19.03.2005, KP
        Description: Method to save the currently displayed screen
        """        
        data=self.finalImage
        if not data:
            raise "No data"
        ImageOperations.saveImageAs(data,self.z,filename)
            


