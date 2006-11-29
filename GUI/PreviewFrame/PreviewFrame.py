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
import scripting as bxd
import Modules
from DataUnit import CombinedDataUnit
import InteractivePanel
import vtk
import wx


ZOOM_TO_FIT=-1
import sys

class PreviewFrame(InteractivePanel.InteractivePanel):
    """
    Created: 03.11.2004, KP
    Description: A widget that shows a single optical slice of a volume dataset
    """
    count=0
    def __init__(self,parent,**kws):
        """
        Created: 03.11.2004, KP
        Description: Initialization
        """
        #PreviewFrame.count+=1
        #wx.Panel.__init__(self,parent,-1)
        xframe=sys._getframe(1)
        self.graySize = (0,0)
        self.bgcolor = (127,127,127)
        self.maxSizeX, self.maxSizeY = 512, 512
        self.maxX, self.maxY         = 512, 512
        self.origX, self.origY       = 512 ,512
        self.lastEventSize = None
        self.paintSize = (512,512)
        self.creator=xframe.f_code.co_filename+": "+str(xframe.f_lineno)
        self.parent=parent
        self.blackImage=None
        self.finalImage=None
        self.xdiff,self.ydiff=0,0
        self.oldZoomFactor=1
        self.zoomFactor=1
        self.selectedItem=-1
        self.show={"SCROLL":0}
        self.rawImages = []
        self.rawImage = None
        size=(1024,1024)
        self.fixedSize = None
        
        self.oldx,self.oldy=0,0
        self.zoomx,self.zoomy=1,1
        Logging.info("kws=",kws,kw="preview")
        if kws.has_key("previewsize"):
            size=kws["previewsize"]
            self.fixedSize  = size
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
        self.tmodules=Modules.DynamicLoader.getTaskModules()
        print self.tmodules,self.tmodules.keys()
        self.tmodules[""]=self.tmodules["Process"]
        self.modules={}
        for key in self.tmodules:
            self.modules[key]=self.tmodules[key][0]
            
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
        
        InteractivePanel.InteractivePanel.__init__(self,parent,size=size,bgColor = self.bgcolor,**kws)
        
        self.calculateBuffer()
        
        self.paintPreview()
        
        
        self.addListener(wx.EVT_RIGHT_DOWN, self.onRightClick)
        #self.Bind(wx.EVT_RIGHT_DOWN,self.onRightClick)
        
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

        
        self.Bind(wx.EVT_SIZE,self.onSize)
        #self.Bind(wx.EVT_PAINT,self.OnPaint)        
        self.Bind(wx.EVT_LEFT_DOWN,self.getVoxelValue)
        self.SetHelpText("This window displays the selected dataset slice by slice.")
        
    def isMipMode(self):
        """
        Created: 23.11.2006, KP
        Description: return the flag that indicates whether this window is in mip mode or not
        """
        return self.mip
        
    def calculateBuffer(self):
        """
        Created: 23.05.2005, KP
        Description: Calculate the drawing buffer required
        """    
        #if not self.enabled:
        #    return
        if not self.imagedata:
            x,y = self.parent.GetClientSize()
            maxX, maxY = x,y
        else:
            x,y,z=self.imagedata.GetDimensions()
            maxX=self.maxX
            maxY=self.maxY

        if self.maxSizeX>maxX:maxX=self.maxSizeX
        if self.maxSizeY>maxY:maxY=self.maxSizeY
        x,y=maxX,maxY
        if self.fixedSize:
            x,y = self.fixedSize
        if self.paintSize!=(x,y):    
            self.paintSize=(x,y)            
            self.setScrollbars(x,y)
        Logging.info("paintSize=",self.paintSize,kw="preview")
        #if bxd.visualizer.zoomToFitFlag:
        #    self.zoomToFit()

    def onSize(self,event):
        """
        Created: 23.05.2005, KP
        Description: Size event handler
        """    
        if event.GetSize() == self.lastEventSize:
            #print "**** LAST SIZE THE SAME"
            return
        #print "Last size=",self.lastEventSize, "new size=",event.GetSize()
        self.lastEventSize = event.GetSize()
        
        InteractivePanel.InteractivePanel.OnSize(self,event)
        self.sizeChanged=1
        if self.enabled:
            self.calculateBuffer()
            self.updatePreview(renew=0)
        event.Skip()
        
    def setRenewFlag(self,obj,evt):
        """
        Created: 12.08.2005, KP
        Description: Set the flag telling the preview to renew
        """        
        self.renewNext=1
        
    def setSelectedItem(self,item,update=1):
        """
        Created: 05.04.2005, KP
        Description: Set the item selected for configuration
        """
        Logging.info("Selected item "+str(item),kw="preview")
        self.selectedItem = item
#        print "dataunit=",self.dataUnit
        if self.dataUnit.isProcessed():
            self.settings = self.dataUnit.getSourceDataUnits()[item].getSettings()
            self.settings.set("PreviewedDataset",item)
        else:
            self.settings = self.dataUnit.getSettings()
        if update:
            self.updatePreview(1)
        
    def onSetInterpolation(self,event):
        """
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
        Created: 02.04.2005, KP
        Description: Method that is called when the right mouse button is
                     pressed down on this item
        """ 
        #print "\n\n\n*** ON RIHG TCLICK"
        x,y=event.GetPosition()
        shape=self.FindShape(x,y)
        if shape:
            event.Skip()
        self.PopupMenu(self.menu,event.GetPosition())
                
        
    def getVoxelValue(self,event):
        """
        Created: 23.05.2005, KP
        Description: Send an event containing the current voxel position
        """
        self.onLeftDown(event)
        event.Skip()    
        if not self.rawImage and not self.rawImages:
            return
            
        if self.rawImages:
            self.rawImage = self.rawImages[0]
        elif self.rawImage and not self.rawImages:
            self.rawImages=[self.rawImage]
        if self.mip:
            self.rawImage = self.currentImage            
            self.rawImages=[self.rawImage]
        x,y=event.GetPosition()
        x-=self.xoffset
        y-=self.yoffset
                
        x,y=self.getScrolledXY(x,y)
        
        z=self.z
                
        dims=[x,y,z]
        rx,ry,rz=dims
                   
        if x<0:x=0
        if y<0:y=0
        if x>=self.xdim:x=self.xdim-1
        if y>=self.ydim:y=self.ydim-1
        Logging.info("Returning x,y,z=(%d,%d,%d)"%(rx,ry,rz),kw="preview")
        ncomps=self.rawImage.GetNumberOfScalarComponents()
        if ncomps==1:
            Logging.info("One component in raw image",kw="preview")
            rv= -1
            gv=-1
            bv=-1
            alpha=-1
            if len(self.rawImages) <2:
                scalar = self.rawImages[0].GetScalarComponentAsDouble(x,y,self.z,0)
                
            else:
                scalar = []
                for i,img in enumerate(self.rawImages):
                    if self.dataUnit.getOutputChannel(i):
                        scalar.append(img.GetScalarComponentAsDouble(x,y,self.z,0))
                    else:
                        print "OUTPUT CHANNEL %d NOT ON"%i
                scalar = tuple(scalar)
                print "Scalar is tuple=",scalar
                
        else:
            #Logging.info("%d components in raw image"%ncomps,kw="preview")
            rv=self.rawImage.GetScalarComponentAsDouble(x,y,self.z,0)
            gv=self.rawImage.GetScalarComponentAsDouble(x,y,self.z,1)
            bv=self.rawImage.GetScalarComponentAsDouble(x,y,self.z,2)
            scalar = 0xdeadbeef
            
        #Logging.info("# of comps in image: %d"%self.currentImage.GetNumberOfScalarComponents(),kw="preview")
        r=self.currentImage.GetScalarComponentAsDouble(x,y,self.z,0)
        g=self.currentImage.GetScalarComponentAsDouble(x,y,self.z,1)
        b=self.currentImage.GetScalarComponentAsDouble(x,y,self.z,2)            
        alpha=-1
        if ncomps>3:
            alpha=self.currentImage.GetScalarComponentAsDouble(x,y,self.z,3)
    
        messenger.send(None,"get_voxel_at",rx,ry,rz, scalar, rv,gv,bv,r,g,b,alpha,self.currentCt)
        
    
            
    def setPreviewedSlice(self,obj,event,val=-1):
        """
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
        Created: 09.12.2004, KP
        Description: The previewed timepoint is set to the given timepoint
        Parameters:
                tp      The timepoint to show
        """
        print "Setting timepoint for preview frame=",tp
        timePoint=tp
        if self.timePoint!=timePoint:
            self.timePoint=timePoint
            self.updatePreview(1)
                
    def setDataUnit(self,dataUnit,selectedItem=-1):
        """
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
            #self.setScrollbars(x,y)
            #self.calculateBuffer()
        
        if x>self.maxX:x=self.maxX
        if y>self.maxY:y=self.maxY
        
        x*=self.zoomx
        y*=self.zoomy
        Logging.info("Setting preview to %d,%d"%(x,y),kw="preview")
        #if self.enabled:
        self.paintSize = (0,0)
        self.calculateBuffer()
        print "Calculating buffer size, it's now",self.buffer.GetWidth(),self.buffer.GetHeight()    
        #    self.SetSize((x,y))
        
        if selectedItem!=-1:
            self.setSelectedItem(selectedItem,update=0)

        updated=0
        Logging.info("zoomFactor = ",self.zoomFactor,kw="preview")
        
        if self.enabled:
            self.Layout()
            self.parent.Layout()
            if not updated:
                self.updatePreview(1)


    def updatePreview(self,renew=1):
        """
        Created: 03.04.2005, KP
        Description: Update the preview
        Parameters:
        renew    Whether the method should recalculate the images
        """
        
        if self.renewNext:
            renew=1
            self.renewNext=0
        
        if not self.dataUnit:
            self.paintPreview()
            return
        if not self.enabled:
            Logging.info("Preview not enabled, won't render",kw="preview")
            return
        self.updateColor()
        if not self.running:
            renew=1
            self.running=1
        #if isinstance(self.dataUnit,CombinedDataUnit):
        
        if self.dataUnit.isProcessed():
            try:
                z=self.z
                # if we're doing a MIP, we need to set z to -1
                # to indicate we want the whole volume
                if self.mip:z=-1
                self.rawImages=[]
                for source in self.dataUnit.getSourceDataUnits():
                    self.rawImages.append(source.getTimePoint(self.timePoint))  
                
                preview=self.dataUnit.doPreview(z,renew,self.timePoint)
                #Logging.info("Got preview",preview.GetDimensions(),kw="preview")
            except Logging.GUIError, ex:
                ex.show()
                return
        else:
            
            preview = self.dataUnit.getTimePoint(self.timePoint)
            self.rawImage = preview
            Logging.info("Using timepoint %d as preview"%self.timePoint,kw="preview")
        
        black=0
        if not preview:
            preview=None
            black=1
        
        if not black:
            #print "Processing preview=",preview.GetDimensions()
            colorImage = self.processOutputData(preview)
        else:
            colorImage=preview
        
        
        usedUpdateExt=0
        print "self.z=",self.z,self.mip
        uext=None
        if self.z!=-1 and not self.mip:
            x,y = self.xdim, self.ydim
            print "\nSetting update extent to ",x,y,self.z
            usedUpdateExt=1
            #colorImage.SetUpdateExtent(0,x-1,0,y-1,self.z,self.z)
            uext=(0,x-1,0,y-1,self.z,self.z)
        
        t=time.time()    
        colorImage = bxd.mem.optimize(image = colorImage, updateExtent = uext)            
        #colorImage.SetUpdateExtent(0,self.xdim-1,0,self.ydim-1,self.z,self.z)        
        
        
        #colorImage.Update()
        t2=time.time()
        print "Executing pipeline took",t2-t,"seconds"            
        
        self.currentImage=colorImage
                    
        if colorImage:
            x,y,z=colorImage.GetDimensions()
            
            #print "\n\nIMAGE DIMENSIONS=",x,y,z,"EXTENT=",colorImage.GetWholeExtent()
            #print "Preview dims=",preview.GetDimensions()
            if not usedUpdateExt and not self.mip:
                bxd.visualizer.zslider.SetRange(1,z)
            if x!=self.oldx or y!=self.oldy:
                #self.resetScroll()
                #self.setScrollbars(x,y)
                self.oldx=x
                self.oldy=y
            #print "colorImage=",colorImage.GetDimensions()
            #Logging.info("Setting image (not null: %s)"%(not not colorImage),kw="preview")
            self.setImage(colorImage)
            self.setZSlice(self.z)
        
            z=self.z
            if self.singleslice:
                Logging.info("Single slice, will use z=0",kw="preview")
                z=0
        if not self.imagedata:
            Logging.info("No imagedata to preview",kw="preview")
#            return
            self.slice = None
        else:
            self.slice=ImageOperations.vtkImageDataToWxImage(self.imagedata,z)
            
        self.paintPreview()
        
        
        self.updateScrolling()
                
        self.finalImage=colorImage
        
        self.Refresh()
        
    def processOutputData(self,data):
        """
        Created: 03.04.2005, KP
        Description: Process the data before it's send to the preview
        """            
        data.UpdateInformation()
        ncomps = data.GetNumberOfScalarComponents()
        #Logging.info("I was created by: ",self.creator,"I am the ",PreviewFrame.count,"th instance")
        #Logging.backtrace()
        #Logging.info("Data has %d components"%ncomps,kw="preview")
        if ncomps>3:
            
            #Logging.info("\n\n\n*** Previewed data has %d components, extracting"%ncomps,kw="preview")
            extract=vtk.vtkImageExtractComponents()
            extract.SetComponents(0,1,2)
            extract.SetInput(data)
            data=extract.GetOutput()
            #extract.Update()
            #data = bxd.execute_limited(extract)
            
            
        if self.mip:
            #Logging.info("Doing mip",data,kw="preview")
            data.SetUpdateExtent(data.GetWholeExtent())
            mip=vtk.vtkImageSimpleMIP()
            mip.SetInput(data)
            
            data = mip.GetOutput()
            
            #ret = bxd.execute_limited(mip)
            #data.ReleaseDataFlagOn()
            #data.ReleaseData()
            #data = ret
            
            data.SetUpdateExtent(data.GetWholeExtent())
            
            #print "Output from mip:",data
        if ncomps == 1:            
            Logging.info("Mapping trough ctf",kw="preview")
            
            self.mapToColors=vtk.vtkImageMapToColors()
            self.mapToColors.SetInput(data)
            
            
            self.updateColor()

            colorImage=self.mapToColors.GetOutput()
            #colorImage.SetUpdateExtent(data.GetExtent())
            
            
            outdata  = colorImage
            #outdata = bxd.execute_limited(self.mapToColors)
            
            #outdata.ReleaseDataFlagOff()
            return outdata
            
        else:
            pass
            
        #print "data =",data.GetDimensions()
        return data
       

    def saveSnapshot(self,filename):
        """
        Created: 05.06.2005, KP
        Description: Save a snapshot of the scene
        """      
        ext=filename.split(".")[-1].lower()
        if ext=="jpg":ext="jpeg"
        if ext=="tif":ext="tiff"
        mime="image/%s"%ext
        img=self.buffer.ConvertToImage()
        #print "Saving mimefile ",filename,mime
        img.SaveMimeFile(filename,mime)
        
    def enable(self,flag):
        """
        Created: 02.06.2005, KP
        Description: Enable/Disable updates
        """
        self.enabled=flag
        if flag:
            self.calculateBuffer()
        
    def setPreviewType(self,event):
        """
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
        
    def updateColor(self):
        """
        Created: 20.11.2004, KP
        Description: Update the preview to use the selected color transfer 
                     function
        """
        if self.dataUnit:
            #ct = self.settings.get("ColorTransferFunction")
            ct = self.dataUnit.getColorTransferFunction()
                
            #print "Mapping through",ct
            val=[0,0,0]
            if self.selectedItem != -1:
                ctc = self.settings.getCounted("ColorTransferFunction",self.selectedItem)            
                
                if ctc:
                    ctc.GetColor(255,val)
                    Logging.info("Using ctf of selected item",val,kw="ctf")
                    
                    Logging.info("Using item %d (counted)"%self.selectedItem,kw="preview")
                    ct=ctc
            
     
        #print "Using ctf",ct
        self.currentCt = ct
        
        #ct.GetColor(255,val)
        #Logging.info("value of 255=",val,kw="ctf")
    
        self.mapToColors.SetLookupTable(self.currentCt)
        self.mapToColors.SetOutputFormatToRGB()

 
    def setSingleSliceMode(self,mode):
        """
        Created: 05.04.2005, KP
        Description: Sets this preview to only show a single slice
        """    
        self.singleslice = mode
                
    def setZSlice(self,z):
        """
        Created: 24.03.2005, KP
        Description: Sets the optical slice to preview
        """    
        self.z=z
        
    def setImage(self,image):
        """
        Created: 24.03.2005, KP
        Description: Sets the image to display
        """    
        self.imagedata=image
        
        x,y=self.size
        image.UpdateInformation()   
        x2,y2,z=image.GetDimensions()
        #print "Set image=",repr(image),"with dims=",x2,y2,z
        if x2<x:
            x=x2
        if y2<y:
            y=y2
        
        if self.fitLater:
            self.fitLater=0
            print "\n\n*** Zooming to fit"
            self.zoomToFit()
        
        
    def setZoomFactor(self,f):
        """
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
        Created: 25.03.2005, KP
        Description: Sets the zoom factor so that the image will fit into the screen
        """
        #if self.imagedata:
        
        if self.dataUnit:
            #x,y,z=self.imagedata.GetDimensions()
            x,y,z=self.dataUnit.getDimensions()
            maxX = self.maxSizeX
            maxY = self.maxSizeY
            maxX-=10 # marginal
            maxY-=10 #marginal
            #if self.maxSizeX<maxX:maxX=self.maxSizeX
            #if self.maxSizeY<maxY:maxY=self.maxSizeY
            
            Logging.info("Determining zoom factor from (%d,%d) to (%d,%d)"%(x,y,maxX,maxY),kw="preview")
            self.setZoomFactor(ImageOperations.getZoomFactor(x,y,maxX,maxY))
        else:
            Logging.info("Will zoom to fit later",kw="preview")
            self.fitLater=1

        
    def updateScrolling(self,event=None):
        """
        Created: 24.03.2005, KP
        Description: Updates the scroll settings
        """
        if not self.bmp:
            return
        else:
            #Logging.info("Updating scroll settings (size %d,%d)"%(self.bmp.GetWidth(),self.bmp.GetHeight()),kw="preview")
            #self.setScrollbars(self.bmp.GetWidth()*self.zoomx,self.bmp.GetHeight()*self.zoomy)       
            pass
        if self.scrollTo:
            x,y=self.scrollTo
            Logging.info("Scrolling to %d,%d"%(x,y),kw="preview")
            sx=int(x/self.scrollsize)
            sy=int(y/self.scrollsize)
            #sx=x/self.scrollsize
            #sy=y/self.scrollsize
            self.Scroll(sx,sy)
            self.scrollTo=None

    def paintPreview(self, clientdc = None):
        """
        Created: 24.03.2005, KP
        Description: Paints the image to a DC
        """        
        # Don't paint anything if there's going to be a redraw anyway
        #if self.fitLater:
        #    return
        if not self.slice and self.graySize == self.paintSize:
            return
        #Logging.backtrace()        
        if not clientdc:
            clientdc = wx.ClientDC(self)
        dc = self.dc = wx.BufferedDC(clientdc,self.buffer)
        dc.BeginDrawing()
        
        dc.SetBackground(wx.Brush(wx.Colour(*self.bgcolor)))
        dc.SetPen(wx.Pen(wx.Colour(*self.bgcolor),0))
        dc.SetBrush(wx.Brush(wx.Color(*self.bgcolor)))
        dc.DrawRectangle(0,0,self.paintSize[0],self.paintSize[1])
            
        if not self.slice or not self.enabled:
            self.graySize = self.paintSize
            self.makeBackgroundBuffer(dc)
            dc.EndDrawing()
            self.dc = None
            self.repaintHelpers(update=0)
            return
            
        bmp=self.slice
        Logging.info("Zoom factor for painting =",self.zoomFactor,kw="preview")
        if self.zoomFactor != 1 or self.zoomFactor!=self.oldZoomFactor:
            self.oldZoomFactor=self.zoomFactor
            interpolation = self.interpolation
            if interpolation == -1:
                x,y,z=self.imagedata.GetDimensions()
                #print "\n\n\nIMAGE SIZE=",x,y,z
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
                #print "Scaling image",self.imagedata
                img=ImageOperations.scaleImage(self.imagedata,self.zoomFactor,self.z,interpolation)
                
                bmp=ImageOperations.vtkImageDataToWxImage(img)
            w,h=bmp.GetWidth(),bmp.GetHeight()
            #Logging.info("Setting scrollbars (%d,%d) because of zooming"%(w,h),kw="preview")
            #self.setScrollbars(w,h)

        #Logging.info("Buffer for drawing=",self.buffer.GetWidth(),self.buffer.GetHeight(),kw="preview")
        #dc = self.dc = wx.BufferedDC(clientdc,self.buffer)
        
        if self.zoomx!=1 or self.zoomy!=1:
            w,h=bmp.GetWidth(),bmp.GetHeight()
            w*=self.zoomx
            h*=self.zoomy
            Logging.info("Scaling to ",w,h,kw="preview")
            bmp.Rescale(w,h)
            self.calculateBuffer()
            #self.setScrollbars(w,h)
        
        bmp=bmp.ConvertToBitmap()

        bw,bh = bmp.GetWidth(),bmp.GetHeight()
        
        tw,th = self.buffer.GetWidth(),self.buffer.GetHeight()
        #print "BMP Size=",bw,bh,"buffer size=",tw,th
        xoff = (tw-bw)/2
        yoff = (th-bh)/2
        self.setOffset(xoff, yoff)
        dc.DrawBitmap(bmp,xoff,yoff,True)
            
        self.bmp=self.buffer
        
        InteractivePanel.InteractivePanel.paintPreview(self)

        self.makeBackgroundBuffer(dc)
        
        dc.EndDrawing()
        self.dc = None
        self.repaintHelpers()
        

        
    def makeBackgroundBuffer(self, dc):
        """
        Created: 06.10.2006, KP
        Description: Copy the current buffer to a background buffer
        """
        w,h = self.buffer.GetWidth(),self.buffer.GetHeight()
        self.bgbuffer = wx.EmptyBitmap(w,h)
        memdc = wx.MemoryDC()
        memdc.SelectObject(self.bgbuffer)
        memdc.Blit(0,0,w,h,dc,0,0)
        memdc.SelectObject(wx.NullBitmap)
