# -*- coding: iso-8859-1 -*-

"""
 Unit: PreviewFrame.py
 Project: Selli
 Created: 03.11.2004
 Creator: KP
 Description:

 A widget that can be used to Preview any operations done by a subclass of Module

 Modified 03.11.2004 KP - Methods for colocalization window to pass on the file 
                          names to be processed
          04.11.2004 KP - Inherited specialized preview classes from the 
                          PreviewFrame
          08.11.2004 KP - Preview now uses the dataunit's doPreview() method to do 
                      the preview. No more nosing around with dataunits internal
                      structure
          08.11.2004 KP - Preview now uses the color of the dataunits
          08.11.2004 KP - The preview is now generated in a single image at the
                          specified depth, and the previewed depth is controlled
                          with vtkImageMapper's SetZSlice()-method
          09.11.2004 KP - Added the ability to display a pixels value
          10.11.2004 JV - Added class ColorCombinationPreview (made after 
                          ColocalizationPreview)
          11.11.2004 JV - Changed setPreviewedSlicer so that it works with color merging
                          preview
          16.11.2004 KP - Refactoring code from ColocalizationPreview back to the 
                          base class PreviewFrame
          13.12.2004 KP - Added code for previewing in MayaVi

 Selli includes the following persons:
 JH - Juha Hyytiäinen, juhyytia@st.jyu.fi
 JM - Jaakko Mäntymaa, jahemant@cc.jyu.fi
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 JV - Jukka Varsaluoma,varsa@st.jyu.fi

 Copyright (c) 2004 Selli Project.
"""

__author__ = "Selli Project <http://sovellusprojektit.it.jyu.fi/selli/>"
__version__ = "$Revision: 1.63 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import os.path,sys
import RenderingInterface
import ImageOperations
import VTKScrollPanel
import WxPreviewPanel
import time

from Logging import *

import vtk
import wx

ZOOM_TO_FIT=-1

from Events import *

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
        self.show["RENDERING"]=1
        self.show["TIMESLIDER"]=1
        self.show["ZSLIDER"]=1
        self.show["SCROLL"]=1
        self.modeChoice = None
        if not parentwin:
            parentwin=parent
        self.parentwin=parentwin
        if kws.has_key("previewsize"):
            size=kws["previewsize"]
        if kws.has_key("pixelvalue"):
            self.show["PIXELS"]=kws["pixelvalue"]
        if kws.has_key("renderingpreview"):
            self.show["RENDERING"]=kws["renderingpreview"]
        if kws.has_key("timeslider"):
            self.show["TIMESLIDER"]=kws["timeslider"]
        if kws.has_key("zoom_factor"):
            self.zoomFactor=kws["zoom_factor"]
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

        self.renderpanel = WxPreviewPanel.WxPreviewPanel(self,size=size,scroll=self.show["SCROLL"])
        self.sizer.Add(self.renderpanel,(0,0))

        # The preview can be no larger than these
        self.maxX,self.maxY=size
        self.xdim,self.ydim,self.zdim=0,0,0
                       
        if self.show["PIXELS"]:
            self.renderpanel.Bind(wx.EVT_LEFT_DOWN,self.getPixelValue)
        if self.show["TIMESLIDER"]:
            self.timeslider=wx.Slider(self,value=0,minValue=0,maxValue=1,size=(300,-1),
            style=wx.SL_HORIZONTAL|wx.SL_AUTOTICKS|wx.SL_LABELS)
            self.sizer.Add(self.timeslider,(1,0),flag=wx.EXPAND|wx.LEFT|wx.RIGHT)
            self.timeslider.Bind(wx.EVT_SCROLL,self.updateTimePoint)
        if self.show["ZSLIDER"]:
            self.zslider=wx.Slider(self,value=0,minValue=0,maxValue=100,size=(-1,300),
            style=wx.SL_VERTICAL|wx.SL_AUTOTICKS|wx.SL_LABELS)
            self.zslider.Bind(wx.EVT_SCROLL,self.setPreviewedSlicer)
            self.sizer.Add(self.zslider,(0,1),flag=wx.EXPAND|wx.TOP|wx.BOTTOM)

        if self.show["PIXELS"]:
            self.pixelPanel=wx.Panel(self,-1)
            self.pixelLbl=wx.StaticText(self.pixelPanel,-1,"Scalar 0 at (0,0,0) maps to (0,0,0)")
            self.sizer.Add(self.pixelPanel,(3,0),flag=wx.EXPAND|wx.RIGHT)

        if self.show["RENDERING"]:
            self.modeBox=wx.BoxSizer(wx.VERTICAL)
            self.modeLbl=wx.StaticText(self,-1,"Select preview method:")
            self.modes=["2D Slice","Volume Rendering","Surface Rendering","24-bit Volume Rendering","Maximum Intensity Projection"]
            self.modeChoice=wx.Choice(self,-1,choices=self.modes)
            self.modeChoice.SetSelection(0)
            self.modeBox.Add(self.modeLbl)
            self.modeBox.Add(self.modeChoice)
            self.sizer.Add(self.modeBox,(4,0))

        self.renderingInterface=RenderingInterface.getRenderingInterface()

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
        print "Selected item = ",item
        self.selectedItem = item
        self.settings = self.dataUnit.getSourceDataUnits()[item].getSettings()
        self.settings.set("PreviewedDataset",item)
        self.updatePreview(1)
        
    def zoomObject(self,evt):
        """
        Method: zoomObject()
        Created: 19.03.2005, KP
        Description: Lets the user select the part of the object that is zoomed
        """
        self.renderpanel.startZoom()
        
    def zoomOut(self,evt):
        """
        Method: zoomOut()
        Created: 19.03.2005, KP
        Description: Makes the zoom factor smaller
        """
        return self.zoomComboDirection(-1)
        
    def zoomToComboSelection(self,evt):
        """
        Method: zoomToComboSelection()
        Created: 19.03.2005, KP
        Description: Sets the zoom according to the combo selection
        """
        return self.zoomComboDirection(0)        
        
    def zoomComboDirection(self,dir):
        """
        Method: zoomComboDirection()
        Created: 21.02.2005, KP
        Description: Makes the zoom factor larger/smaller based on values in the zoom combobox
        """
        pos=self.zoomCombo.GetSelection()
        s=self.zoomCombo.GetString(pos)
        if dir>0 and pos >= self.zoomCombo.GetCount():
            #print "Zoom at max: ",s
            return
        if dir<0 and pos==0:
            #print "Zoom at min: ",s
            return
        pos+=dir
        s=self.zoomCombo.GetString(pos)
        factor = float(s[:-1])/100.0
        self.zoomCombo.SetSelection(pos)
        self.renderpanel.setZoomFactor(factor)
        #print "Set zoom factor to ",s,"=",factor
        self.updatePreview(1)
        
        
    def zoomIn(self,evt,factor=-1):
        """
        Method: zoomIn()
        Created: 21.02.2005, KP0
        Description: Makes the zoom factor larger 
        """
        return self.zoomComboDirection(1)
              
    def zoomToFit(self,evt):
        """
        Method: zoomToFit()
        Created: 21.02.2005, KP
        Description: Sets the zoom factor to fit the image into the preview window
        """
        self.renderpanel.zoomToFit()
        self.updatePreview(1)
        
    def zoomTo100(self,evt):
        """
        Method: zoomTo100
        Created: 21.02.2005, KP
        Description: Sets the zoom factor to 1
        """
        self.renderpanel.setZoomFactor(1.0)
        self.updatePreview(1)
                
    def renderingPreviewEnabled(self):
        """
        Method: renderingPreviewEnabled()
        Created: 21.02.2005, KP
        Description: Returns true if the rendering preview is enabled
        """
        if self.modeChoice:
            return self.modeChoice.GetSelection()!=0
        return 0
        
    
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
            r,g,b=self.currentCt.GetColor(scalar)
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
            
    def setPreviewedSlicer(self,event):
        """
        Method: setPreviewedSlicer()
        Created: 4.11.2004, KP
        Description: Sets the preview to display the selected z slice
        """
        t=time.time()
        if abs(self.depthT-t) < self.updateFactor: return
        self.depthT=time.time()
        newz=self.zslider.GetValue()
        if self.z!=newz:
            self.z=newz
            evt=ChangeEvent(myEVT_ZSLICE_CHANGED,self.GetId())
            evt.setValue(newz)
            self.GetEventHandler().ProcessEvent(evt)
            
            # was updatePreview(1)
            self.updatePreview(0)

    def gotoTimePoint(self,tp):
        """
        Method: gotoTimePoint(tp)
        Created: 09.12.2004, KP
        Description: The previewed timepoint is set to the given timepoint
        Parameters:
                tp      The timepoint to show
        """
        self.timeslider.SetValue(tp)
        self.updateTimePoint(None)

    def updateTimePoint(self,event):
        """
        Method: updateTimePoint()
        Created: 04.11.2004, KP
        Description: Sets the time point displayed in the preview
        """
        t=time.time()
        if abs(self.timeT-t) < self.updateFactor: return
        self.timeT=time.time()

        timePoint=self.timeslider.GetValue()
#        print "Use time point %d"%timePoint
        if self.timePoint!=timePoint:
            self.timePoint=timePoint
            self.updatePreview(1)
            evt=ChangeEvent(myEVT_TIMEPOINT_CHANGED,self.GetId())
            evt.setValue(timePoint)
            self.GetEventHandler().ProcessEvent(evt)
                
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
        try:
            count=dataUnit.getLength()
            x,y,z=dataUnit.getDimensions()
        except GUIError, ex:
            ex.show()
            return
        self.xdim,self.ydim,self.zdim=x,y,z
        
        if self.show["ZSLIDER"]:
            #print "zslider goes to %d"%(z-1)
            self.zslider.SetRange(0,z-1)
        if x>self.maxX or y>self.maxY:
            self.renderpanel.setScrollbars(x,y)
        
        if x>self.maxX:x=self.maxX
        if y>self.maxY:y=self.maxY
        
        if self.show["TIMESLIDER"]:
            self.timeslider.SetRange(0,count-1)
        self.renderingInterface.setDataUnit(dataUnit)

        #print "Setting renderpanel to %d,%d"%(x,y)
        self.renderpanel.SetSize((x,y))
        self.renderpanel.Layout()

        if selectedItem!=-1:
            self.setSelectedItem(selectedItem)

        if self.zoomFactor:
            #print "Got zoom factor",
            if self.zoomFactor == ZOOM_TO_FIT:
                #print "Factor = zoom to fit"
                self.zoomToFit(None)
            else:
                #print "Factor = ",self.zoomFactor
                self.renderpanel.setZoomFactor(self.zoomFactor)
                self.updatePreview(1)
        
        self.Layout()
        self.sizer.Fit(self)
        self.sizer.SetSizeHints(self)
        
    def previewInMayavi(self,imagedata,ctf=None,renew=1):
        """
        Method: previewInMayavi(imagedata,ctf,renew)
        Created: 13.12.2004,KP
        Description:
        Parameters:
                imagedata    Data to preview
                ctf          Color transfer function for the data
        """
        if not renew:
            return
        self.renderingInterface.setOutputPath(".")
        self.renderingInterface.setTimePoints([self.timePoint])
        self.renderingInterface.doRendering(preview=imagedata,ctf=ctf)


    def updatePreview(self,renew=1):
        """
        Method: updatePreview(renew=1)
        Created: 03.11.2004, KP
        Description: Update the preview
        Parameters:
            renew    Whether the method should recalculate the images
        """
        raise "updatePreview() called from the base class"
       
    def captureSlice(self,event):
        """
        Method: captureSlice(event)
        Created: 19.03.2005, KP
        Description: Method to capture the currently displayed optical slice
        """        
        data=self.finalImage
        if not data:
            raise "No data"
        wc="PNG file|*.png|JPEG file|*.jpeg|TIFF file|*.tiff|BMP file|*.bmp"
        initFile="%s_%d.png"%(self.dataUnit.getName(),self.z)
        dlg=wx.FileDialog(self.parent,"Save optical slice to file",defaultFile=initFile,wildcard=wc,style=wx.SAVE)
        filename=None
        if dlg.ShowModal()==wx.ID_OK:
            filename=dlg.GetPath()
            ImageOperations.saveImageAs(data,self.z,filename)
            
            


