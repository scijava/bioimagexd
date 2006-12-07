# -*- coding: iso-8859-1 -*-

"""
 Unit: PreviewFrame.py
 Project: BioImageXD
 Created: 03.11.2004, KP
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
import messenger

import ImageOperations

import time

import Logging
import Modules
from DataUnit import CombinedDataUnit
import InteractivePanel
import vtk
import wx

ZOOM_TO_FIT=-1
import sys

class PreviewFrame(InteractivePanel.InteractivePanel):
    """
    Class: PreviewFrame
    Created: 03.11.2004, KP
    Description: A widget that uses the wxVTKRenderWidget to display a preview
                 of operations done by a subclass of Module
    """
    count=0
    def __init__(self,parent,**kws):
        """
        Method: __init__(parent)
        Created: 03.11.2004, KP
        Description: Initialization
        """
        #PreviewFrame.count+=1
        #wx.Panel.__init__(self,parent,-1)
        xframe=sys._getframe(1)
        self.creator=xframe.f_code.co_filename+": "+str(xframe.f_lineno)
        self.parent=parent
        self.blackImage=None
        self.finalImage=None
        self.xdiff,self.ydiff=0,0
        self.oldZoomFactor=1
        self.zoomFactor=1
        self.selectedItem=-1
        self.show={"SCROLL":0}
        size=(1024,1024)
        self.oldx,self.oldy=0,0
        self.zoomx,self.zoomy=1,1
        Logging.info("kws=",kws,kw="preview")
        if kws.has_key("previewsize"):
            size=kws["previewsize"]
            Logging.info("Got previewsize=",size,kw="preview")
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
        self.currentImage=None
        self.currentCt=None
        
        # The preview can be no larger than these
        
        self.xdim,self.ydim,self.zdim=0,0,0
                               
        self.running=0

        self.rgb=(255,255,0)

        self.z=0
        self.timePoint=0
        
        self.mapToColors=vtk.vtkImageMapToColors()
        self.mapToColors.SetLookupTable(self.currentCt)
        self.mapToColors.SetOutputFormatToRGB()
        
        self.enabled=1
               
        self.mip = 0
        self.previewtype=""
        self.modules=Modules.DynamicLoader.getTaskModules()
        self.modules[""]=self.modules["Process"]
        for key in self.modules:
            self.modules[key]=self.modules[key][0]
            
        self.renewNext=0
        messenger.connect(None,"zslice_changed",self.setPreviewedSlice)
        messenger.connect(None,"renew_preview",self.setRenewFlag)
        
        self.fitLater=0
        self.imagedata=None
        self.bmp=None
        self.parent = parent
        self.scroll=1
        Logging.info("preview panel size=",size,kw="preview")
        
        x,y=size
        self.buffer = wx.EmptyBitmap(x,y)
        if kws.has_key("zoomx"):
            self.zoomx=kws["zoomx"]
            del kws["zoomx"]
        if kws.has_key("zoomy"):
            self.zoomy=kws["zoomy"]
            del kws["zoomy"]
        Logging.info("zoom xf=%f, yf=%f"%(self.zoomx,self.zoomy),kw="preview")
        #if kws.has_key("scrollbars"):
        #    self.scroll=kws["scrollbars"]
        self.size=size
        self.slice=None
        self.z = 0
        self.zooming = 0
        self.scrollsize=32
        self.singleslice=0
        self.scrollTo=None
        InteractivePanel.InteractivePanel.__init__(self,parent,size=size,**kws)
        
        
        self.paintPreview()
        
        self.Bind(wx.EVT_RIGHT_DOWN,self.onRightClick)
        
        self.ID_VARY=wx.NewId()
        self.ID_NONE=wx.NewId()
        self.ID_LINEAR=wx.NewId()
        self.ID_CUBIC=wx.NewId()
        self.interpolation=-1
        self.renew=1
        self.menu=wx.Menu()
        
        item = wx.MenuItem(self.menu,self.ID_VARY,"Interpolation depends on size",kind=wx.ITEM_RADIO)
        self.menu.AppendItem(item)
        self.menu.Check(self.ID_VARY,1)
        item = wx.MenuItem(self.menu,self.ID_NONE,"No interpolation",kind=wx.ITEM_RADIO)
        self.menu.AppendItem(item)
        item = wx.MenuItem(self.menu,self.ID_LINEAR,"Linear interpolation",kind=wx.ITEM_RADIO)
        self.menu.AppendItem(item)
        item = wx.MenuItem(self.menu,self.ID_CUBIC,"Cubic interpolation",kind=wx.ITEM_RADIO)
        self.menu.AppendItem(item)
        
        self.Bind(wx.EVT_MENU,self.onSetInterpolation,id=self.ID_VARY)
        self.Bind(wx.EVT_MENU,self.onSetInterpolation,id=self.ID_NONE)
        self.Bind(wx.EVT_MENU,self.onSetInterpolation,id=self.ID_LINEAR)
        self.Bind(wx.EVT_MENU,self.onSetInterpolation,id=self.ID_CUBIC)

        
        #self.Bind(wx.EVT_PAINT,self.OnPaint)        
        self.Bind(wx.EVT_LEFT_DOWN,self.getVoxelValue)
        self.SetHelpText("This window displays the selected dataset slice by slice.")
#    def __del__(self):        
#        PreviewFrame.count-=1
    def setRenewFlag(self,obj,evt):
        """
        Method: setRenewFlag
        Created: 12.08.2005, KP
        Description: Set the flag telling the preview to renew
        """        
        self.renewNext=1
        
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
        
    def onSetInterpolation(self,event):
        """
        Method: onSetInterpolation
        Created: 01.08.2005, KP
        Description: Set the inteprolation method
        """      
        eID=event.GetId()
        flags=(1,0,0,0)
        interpolation=-1
        if eID == self.ID_NONE:
            flags=(0,1,0,0)
            interpolation=0
        elif eID == self.ID_LINEAR:
            flags=(0,0,1,0)
            interpolation=1
        elif eID == self.ID_CUBIC:
            flags=(0,0,0,1)
            interpolation=2
        
        self.menu.Check(self.ID_VARY,flags[0])
        self.menu.Check(self.ID_NONE,flags[1])
        self.menu.Check(self.ID_LINEAR,flags[2])
        self.menu.Check(self.ID_CUBIC,flags[3])
        if self.interpolation != interpolation:
            self.interpolation=interpolation
            self.updatePreview()
        
        
    def onRightClick(self,event):
        """
        Method: onRightClick
        Created: 02.04.2005, KP
        Description: Method that is called when the right mouse button is
                     pressed down on this item
        """      
        self.PopupMenu(self.menu,event.GetPosition())
                
        
    def getVoxelValue(self,event):
        """
        Method: getVoxelValue(event)
        Created: 23.05.2005, KP
        Description: Send an event containing the current voxel position
        """
        if not self.currentImage:
            return
        x,y=event.GetPosition()
        x,y=self.getScrolledXY(x,y)
        z=self.z
        dims=[x,y,z]
        rx,ry,rz=dims
        Logging.info("Returning x,y,z=(%d,%d,%d)"%(rx,ry,rz),kw="preview")
        ncomps=self.currentImage.GetNumberOfScalarComponents()
        if ncomps==1:
            r=self.currentImage.GetScalarComponentAsDouble(x,y,self.z,0)
            g=-1
            b=-1
            alpha=-1
        else:
            r=self.currentImage.GetScalarComponentAsDouble(x,y,self.z,0)
            g=self.currentImage.GetScalarComponentAsDouble(x,y,self.z,1)
            b=self.currentImage.GetScalarComponentAsDouble(x,y,self.z,2)
            alpha=-1
            if ncomps>3:
                alpha=self.currentImage.GetScalarComponentAsDouble(x,y,self.z,3)
    
        messenger.send(None,"get_voxel_at",rx,ry,rz,r,g,b,alpha,self.currentCt)
        event.Skip()
    
            
    def setPreviewedSlice(self,obj,event,val=-1):
        """
        Method: setPreviewedSlice()
        Created: 4.11.2004, KP
        Description: Sets the preview to display the selected z slice
        """
        newz=val
        if self.z!=newz:
            self.z=newz
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
        timePoint=tp
        if self.timePoint!=timePoint:
            self.timePoint=timePoint
            self.updatePreview(1)
                
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
        self.updateColor()
        InteractivePanel.InteractivePanel.setDataUnit(self,self.dataUnit)
        
        try:
            count=dataUnit.getLength()
            x,y,z=dataUnit.getDimensions()
        except Logging.GUIError, ex:
            ex.show()
            return
            
        dims=[x,y,z]
        self.xdim,self.ydim,self.zdim=x,y,z
        
        if x>self.maxX or y>self.maxY:
            Logging.info("Setting scrollbars to %d,%d"%(x,y),kw="preview")
            self.setScrollbars(x,y)
        
        if x>self.maxX:x=self.maxX
        if y>self.maxY:y=self.maxY
        
        x*=self.zoomx
        y*=self.zoomy
        Logging.info("Setting preview to %d,%d"%(x,y),kw="preview")
        self.SetSize((x,y))
        

        if selectedItem!=-1:
            self.setSelectedItem(selectedItem)

        if self.zoomFactor:
            if self.zoomFactor == ZOOM_TO_FIT:
                Logging.info("Factor = zoom to fit",kw="preview")
                self.zoomToFit()
                self.updatePreview(1)
            else:
                self.setZoomFactor(self.zoomFactor)
                self.updatePreview(1)
        
        self.Layout()
        self.parent.Layout()
        self.updatePreview(1)


    def updatePreview(self,renew=1):
        """
        Method: updatePreview(renew=1)
        Created: 03.04.2005, KP
        Description: Update the preview
        Parameters:
        renew    Whether the method should recalculate the images
        """
        if self.renewNext:
            renew=1
            self.renewNext=0
        
        if not self.dataUnit:
            return
        if not self.enabled:
            Logging.info("Preview not enabled, won't render",kw="preview")
            return
        self.updateColor()
        if not self.running:
            renew=1
            self.running=1
        if isinstance(self.dataUnit,CombinedDataUnit):
            try:
                z=self.z
                # if we're doing a MIP, we need to set z to -1
                # to indicate we want the whole volume
                if self.mip:z=-1
                preview=self.dataUnit.doPreview(z,renew,self.timePoint)
                
                #Logging.info("Got preview",preview.GetDimensions(),kw="preview")
            except Logging.GUIError, ex:
                ex.show()
                return
        else:
            preview = self.dataUnit.getTimePoint(self.timePoint)
            Logging.info("Using timepoint %d as preview"%self.timePoint,kw="preview")
        black=0
        if not preview:
            Logging.info("Creating black preview",kw="preview")
            if not self.blackImage:
                #xor=vtk.vtkImageLogic()
                #xor.SetOperationToXor()
                data=self.dataUnit.getSourceDataUnits()[0].getTimePoint(0)
                #xor.AddInput(data)
                
                #xor.AddInput(data)
                #xor.Update()
                extent=data.GetExtent()
                dims=data.GetDimensions()
                #self.blackImage=xor.GetOutput()
                self.blackImage=vtk.vtkImageData()
                self.blackImage.SetDimensions(dims)
                self.blackImage.SetScalarTypeToUnsignedChar()
                self.blackImage.SetNumberOfScalarComponents(3)
                self.blackImage.SetExtent(extent)       
                self.blackImage.AllocateScalars()
            #print "preview=",self.blackImage
            preview=self.blackImage
            black=1
        self.currentImage=preview
        
        if not black:
            #print "Processing preview=",preview.GetDimensions()
            colorImage = self.processOutputData(preview)
        else:
            colorImage=preview
        
                    
        x,y,z=colorImage.GetDimensions()
        #print "Preview dims=",preview.GetDimensions()
        if x!=self.oldx or y!=self.oldy:
            #self.resetScroll()
            self.setScrollbars(x,y)
            self.oldx=x
            self.oldy=y
        #print "colorImage=",colorImage.GetDimensions()
        Logging.info("Setting image (not null: %s)"%(not not colorImage),kw="preview")
        self.setImage(colorImage)
        self.setZSlice(self.z)
        
        z=self.z
        if self.singleslice:
            Logging.info("Single slice, will use z=0",kw="preview")
            z=0
        if not self.imagedata:
            Logging.info("No imagedata to preview",kw="preview")
            return
        else:
            self.slice=ImageOperations.vtkImageDataToWxImage(self.imagedata,z)
            
        Logging.info("Painting preview",kw="preview")
        self.paintPreview()
        self.Refresh()
        wx.GetApp().Yield(1)
        #print "self.bmp=",self.bmp,self.bmp.GetWidth(),self.bmp.GetHeight()
        self.updateScrolling()
        
        self.finalImage=colorImage

    def processOutputData(self,data):
        """
        Method: processOutputData()
        Created: 03.04.2005, KP
        Description: Process the data before it's send to the preview
        """            
        ncomps = data.GetNumberOfScalarComponents()
        #Logging.info("I was created by: ",self.creator,"I am the ",PreviewFrame.count,"th instance")
        #Logging.backtrace()
        #Logging.info("Data has %d components"%ncomps,kw="preview")
        if ncomps>3:
            Logging.info("Previewed data has %d components, extracting"%ncomps,kw="preview")
            extract=vtk.vtkImageExtractComponents()
            extract.SetComponents(0,1,2)
            extract.SetInput(data)
            data=extract.GetOutput()
            extract.Update()
            
        if self.mip:
            Logging.info("Doing mip",data.GetWholeExtent(),kw="preview")
            #data.SetUpdateExtent(data.GetWholeExtent())
            mip=vtk.vtkImageSimpleMIP()
            mip.SetInput(data)
            mip.Update()
            data=mip.GetOutput()
            Logging.info("Got MIP with extent=",data.GetWholeExtent(),kw="preview")
            data.SetUpdateExtent(data.GetWholeExtent())
            
            #print "Output from mip:",data
        if ncomps == 1:            
            Logging.info("Mapping trough ctf",kw="preview")
            #self.mapToColors.RemoveAllInputs()
            self.mapToColors=vtk.vtkImageMapToColors()
            self.mapToColors.SetInput(data)
            
            self.updateColor()

            colorImage=self.mapToColors.GetOutput()
            colorImage.SetUpdateExtent(data.GetExtent())
            #print "upadte extent=",data.GetExtent()
            
            #print "colorImage=",colorImage.GetDimensions()
            self.mapToColors.Update()
            data=self.mapToColors.GetOutput()

            #data.ReleaseDataFlagOff()
            return data
            #print "data =",data.GetDimensions()
        else:
            pass
            
        #print "data =",data.GetDimensions()
        return data
       

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
        
    def enable(self,flag):
        """
        Method: enable(flag)
        Created: 02.06.2005, KP
        Description: Enable/Disable updates
        """
        self.enabled=flag
        
    def setPreviewType(self,event):
        """
        Method: setPreviewType
        Created: 03.04.2005, KP
        Description: Method to set the proper previewtype
        """     
        
        if type(event)==type(""):
            if event=="MIP":
                self.previewtype=""
                self.mip=1
                return
            else:
                self.previewtype=event
                return
    
        self.mip = 0
        self.setSingleSliceMode(0)            
        m=self.modules[self.previewtype]
        Logging.info("Module that corresponds to %s: %s"%(self.previewtype,m),kw="preview")
        self.dataUnit.setModule(m)
        sourceunits=self.dataUnit.getSourceDataUnits()
        t=self.previewtype
        if not t:t="SingleUnitProcessing"
        for unit in sourceunits:
            settingstype="%sSettings"%t
            settings = unit.getSettings()
            if settings:
                #Logging.info("\n\n\n\nConverting settings of %s to %s"%(unit,settingstype))#,kw="preview")
                settings = settings.asType(settingstype)
            else:
                raise "Got no settings from dataunit",unit
            unit.setSettings(settings)
            Logging.info("Type of settings now:",unit.getSettings().get("Type"),kw="preview")
        self.setSelectedItem(0)
        
        self.updatePreview(1)
            
        
    def updateColor(self):
        """
        Method: updateColor()
        Created: 20.11.2004, KP
        Description: Update the preview to use the selected color transfer 
                     function
        Parameters:
        """
        if self.previewtype=="Merging":
            return
        if self.dataUnit:
            ct = self.settings.get("ColorTransferFunction")
            #print "Mapping through",ct
            val=[0,0,0]
            if self.selectedItem != -1:
                ctc = self.settings.getCounted("ColorTransferFunction",self.selectedItem)            
                
                if ctc:
                    ctc.GetColor(255,val)
                    Logging.info("Using ctf of selected item",val,kw="ctf")
                    
                    Logging.info("Using item %d (counted)"%self.selectedItem,kw="preview")
                    ct=ctc
            
        self.currentCt = ct
        
        #ct.GetColor(255,val)
        #Logging.info("value of 255=",val,kw="ctf")
    
        self.mapToColors.SetLookupTable(self.currentCt)
        self.mapToColors.SetOutputFormatToRGB()

 
    def setSingleSliceMode(self,mode):
        """
        Method: setSingleSliceMode()
        Created: 05.04.2005, KP
        Description: Sets this preview to only show a single slice
        """    
        self.singleslice = mode
                
    def setZSlice(self,z):
        """
        Method: setZSlice(z)
        Created: 24.03.2005, KP
        Description: Sets the optical slice to preview
        """    
        self.z=z
        
    def setImage(self,image):
        """
        Method: setImage(image)
        Created: 24.03.2005, KP
        Description: Sets the image to display
        """    
        self.imagedata=image
        x,y=self.size
        x2,y2,z=image.GetDimensions()
        if x2<x:
            x=x2
        if y2<y:
            y=y2
        
        #Logging.info("Setting scrollbars for size %d,%d"%(x,y),kw="preview")
        #self.setScrollbars(x,y)
        #if x==x2 or y==y2:
        #    if x==x2:s="x"
        #    if y==y2:
        #        if s:s+=" and "
        #        s+="y"
        #    Logging.info("Using smaller %s for size"%s,kw="preview")            
        #self.Layout()
        if self.fitLater:
            self.fitLater=0
            self.zoomToFit()
        
        
    def setZoomFactor(self,f):
        """
        Method: setZoomFactor
        Created: 24.03.2005, KP
        Description: Sets the factor by which the image should be zoomed
        """
        if f>10:
            f=10
        Logging.info("Setting zoom factor to ",f,kw="preview")
        if f<self.zoomFactor:
            # black the preview
            slice=self.slice
            self.slice=None
            self.paintPreview()
            self.slice=slice
            
        self.zoomFactor=f
        self.updateAnnotations()
        #self.Scroll(0,0)
        
    def zoomToFit(self):
        """
        Method: zoomToFit()
        Created: 25.03.2005, KP
        Description: Sets the zoom factor so that the image will fit into the screen
        """
        #if self.imagedata:
        if self.dataUnit:
            #x,y,z=self.imagedata.GetDimensions()
            x,y,z=self.dataUnit.getDimensions()
            Logging.info("Determining zoom factor from (%d,%d) to (%d,%d)"%(x,y,self.maxX,self.maxY),kw="preview")
            self.setZoomFactor(ImageOperations.getZoomFactor(x,y,self.maxX,self.maxY))
        else:
            Logging.info("Will zoom to fit later",kw="preview")
            self.fitLater=1

        
    def updateScrolling(self,event=None):
        """
        Method: updateScrolling
        Created: 24.03.2005, KP
        Description: Updates the scroll settings
        """
        if not self.bmp:
            return
        if self.bmp:
            Logging.info("Updating scroll settings (size %d,%d)"%(self.bmp.GetWidth(),self.bmp.GetHeight()),kw="preview")
            self.setScrollbars(self.bmp.GetWidth()*self.zoomx,self.bmp.GetHeight()*self.zoomy)       
        if self.scrollTo:
            x,y=self.scrollTo
            Logging.info("Scrolling to %d,%d"%(x,y),kw="preview")
            sx=int(x/self.scrollsize)
            sy=int(y/self.scrollsize)
            #sx=x/self.scrollsize
            #sy=y/self.scrollsize
            self.Scroll(sx,sy)
            self.scrollTo=None

    def paintPreview(self):
        """
        Method: paintPreview()
        Created: 24.03.2005, KP
        Description: Paints the image to a DC
        """
        if not self.slice:
            Logging.info("Black preview",kw="preview")
            dc = self.dc = wx.BufferedDC(wx.ClientDC(self),self.buffer)
            dc.BeginDrawing()
            dc.SetBackground(wx.Brush(wx.Colour(0,0,0)))
            dc.SetPen(wx.Pen(wx.Colour(0,0,0),0))
            dc.SetBrush(wx.Brush(wx.Color(0,0,0)))
            dc.DrawRectangle(0,0,self.size[0],self.size[1])
            dc.EndDrawing()
            self.dc = None
            return
        bmp=self.slice
        Logging.info("Zoom factor for painting =",self.zoomFactor,kw="preview")
        if self.zoomFactor != 1 or self.zoomFactor!=self.oldZoomFactor:
            self.oldZoomFactor=self.zoomFactor
            interpolation = self.interpolation
            if interpolation == -1:
                x,y,z=self.imagedata.GetDimensions()
                # if x*y < 512*512, cubic
                pixels=(x*self.zoomFactor)*(y*self.zoomFactor)
                if pixels<=1024*1024:
                    Logging.info("Using cubic",kw="preview")
                    interpolation=2
                # if x*y < 1024*1024, linear
                elif pixels<=2048*2048:
                    Logging.info("Using nearest",kw="preview")
                    interpolation=1
                else:
                    Logging.info("Using no interpolation",kw="preview")
                    interpolation=0
            if interpolation == 0:
                bmp=ImageOperations.zoomImageByFactor(self.slice,self.zoomFactor)                
            else:
                img=ImageOperations.scaleImage(self.imagedata,self.zoomFactor,self.z,interpolation)
                bmp=ImageOperations.vtkImageDataToWxImage(img)
            w,h=bmp.GetWidth(),bmp.GetHeight()
            Logging.info("Setting scrollbars (%d,%d) because of zooming"%(w,h),kw="preview")
            self.setScrollbars(w,h)

        Logging.info("Buffer for drawing=",self.buffer.GetWidth(),self.buffer.GetHeight(),kw="preview")
        dc = self.dc = wx.BufferedDC(wx.ClientDC(self),self.buffer)
        
        if self.zoomx!=1 or self.zoomy!=1:
            w,h=bmp.GetWidth(),bmp.GetHeight()
            w*=self.zoomx
            h*=self.zoomy
            Logging.info("Scaling to ",w,h,kw="preview")
            bmp.Rescale(w,h)
            
            self.setScrollbars(w,h)
        
        bmp=bmp.ConvertToBitmap()

        dc.DrawBitmap(bmp,0,0,True)
        self.bmp=self.buffer
        
        InteractivePanel.InteractivePanel.paintPreview(self)

        
        dc.EndDrawing()
        self.dc = None