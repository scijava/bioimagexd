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
          11.11.2004 JV - Changed updateDepth so that it works with color merging
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
 ""
__author__ = "Selli Project <http://sovellusprojektit.it.jyu.fi/selli/>"
__version__ = "$Revision: 1.63 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"
"""
import os.path
import RenderingInterface
import ImageOperations
import Slicer
import wx
import time
from Logging import *
from vtk.wx.wxVTKRenderWindowInteractor import *
#from wxrenwin.wxVTKRenderWindowInteractor import *
import vtk
import wx.lib.scrolledpanel as scrolled


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
        self.zoomed=0
        self.depthT=0
        self.timeT=0
        self.updateFactor = 0.001
        size=(512,512)
        self.show={}
        self.show["PIXELS"]=1
        self.show["RENDERING"]=1
        self.show["ZOOM"]=1
        self.show["TIMESLIDER"]=1
        self.show["ZSLIDER"]=1
        self.modeCheckbox = None
        if not parentwin:
            parentwin=parent
        self.parentwin=parentwin
        if kws.has_key("previewsize"):
            size=kws["previewsize"]
        if kws.has_key("pixelvalue"):
            self.show["PIXELS"]=kws["pixelvalue"]
        if kws.has_key("renderingpreview"):
            self.show["RENDERING"]=kws["renderingpreview"]
        if kws.has_key("zoom"):
            self.show["ZOOM"]=kws["zoom"]
        if kws.has_key("timeslider"):
            self.show["TIMESLIDER"]=kws["timeslider"]
            
        
        self.dataUnit=None
        self.rgbMode=0
        
        self.sizer=wx.GridBagSizer()
        self.previewsizer=wx.BoxSizer(wx.VERTICAL)
    	# These are the current image and color transfer function
    	# They are used when getting the value of a pixel
    	self.currentImage=None
    	self.currentCt=None

        self.renderpanel = scrolled.ScrolledPanel(self, -1,style=wx.SUNKEN_BORDER,size=size)
        #self.renderpanel = wx.ScrolledWindow(self,-1,style=wx.SUNKEN_BORDER,size=(512,512))
        
        self.wxrenwin = wxVTKRenderWindowInteractor(self.renderpanel,-1,size=size)
        self.wxrenwin.Initialize()
        self.wxrenwin.Start()

        self.previewsizer.Add(self.wxrenwin)

        self.renderpanel.SetSizer(self.previewsizer)
        self.renderpanel.SetAutoLayout(1)
        #self.renderpanel.SetupScrolling()
        
        self.sizer.Add(self.renderpanel,(0,0))

        self.renwin=self.wxrenwin.GetRenderWindow()
        #self.renwin.SetSize(size)
        self.renderer=vtk.vtkRenderer()
        self.renwin.AddRenderer(self.renderer)
        # The preview can be no larger than these
        self.maxX,self.maxY=size
        # Variables for scrolling the render window
        self.offset=0
        self.xdim,self.ydim,self.zdim=0,0,0
        # If the user scrolls the render widget, this is the starting point
        self.startX,self.startY=0,0

        self.bgColor=(0,0,0)
        r,g,b=self.bgColor
        self.renderer.SetBackground(r,g,b)
        ren=self.renderer
              
        #self.renwin.Render()
        # This is set here because if inherited widgets define mapper, 
        # the scrollRenderWindow uses that for the scrolling
        self.mapper=None
        if self.show["PIXELS"]:
            self.wxrenwin.Bind(EVT_LEFT_DOWN,self.getPixelValue)
        if self.show["TIMESLIDER"]:
            self.timeslider=wx.Slider(self,value=0,minValue=0,maxValue=1,size=(300,-1),
            style=wx.SL_HORIZONTAL|wx.SL_AUTOTICKS|wx.SL_LABELS)
            self.sizer.Add(self.timeslider,(1,0),flag=wx.EXPAND|wx.LEFT|wx.RIGHT)
            self.timeslider.Bind(EVT_SCROLL,self.updateTimePoint)
        if self.show["ZSLIDER"]:
            self.zslider=wx.Slider(self,value=0,minValue=0,maxValue=100,size=(-1,300),
            style=wx.SL_VERTICAL|wx.SL_AUTOTICKS|wx.SL_LABELS)
            self.zslider.Bind(EVT_SCROLL,self.updateDepth)
            self.sizer.Add(self.zslider,(0,1),flag=wx.EXPAND|wx.TOP|wx.BOTTOM)

        if self.show["PIXELS"]:
            self.pixelPanel=wx.Panel(self,-1)
            self.pixelLbl=wx.StaticText(self.pixelPanel,-1,"Scalar 0 at (0,0,0) maps to (0,0,0)")
            self.sizer.Add(self.pixelPanel,(3,0),flag=wx.EXPAND|wx.RIGHT)

        if self.show["RENDERING"]:
            self.modeCheckbox=wx.CheckBox(self,-1,"Preview rendering")
            self.sizer.Add(self.modeCheckbox,(5,0))
                
        if self.show["ZOOM"]:
            self.zoombox=wx.BoxSizer(wx.HORIZONTAL)
            ids=[wx.ID_ZOOM_100,wx.ID_ZOOM_FIT,wx.ID_ZOOM_IN]#,wx.ID_ZOOM_OUT]
            for id in ids:
                btn=wx.Button(self,id)
                self.zoombox.Add(btn)
            EVT_BUTTON(self,wx.ID_ZOOM_100,self.zoomTo100)
            EVT_BUTTON(self,wx.ID_ZOOM_FIT,self.zoomToFit)
            EVT_BUTTON(self,wx.ID_ZOOM_IN,self.zoomIn)
            #EVT_BUTTON(self,wx.ID_ZOOM_OUT,self.zoomOut)   
            
            self.sizer.Add(self.zoombox,(2,0))
        self.timePointChangeCallback=None

        self.renderingInterface=RenderingInterface.getRenderingInterface()

        self.running=0

    	self.rgb=(255,255,0)

        self.z=0
        self.timePoint=0
        
        self.SetAutoLayout(True)
        self.SetSizer(self.sizer)
        self.sizer.Fit(self)
        self.sizer.SetSizeHints(self)
        
    def zoomIn(self,evt):
        """
        Method: zoomIn()
        Created: 21.02.2005, KP
        Description: Sets the zoom factor to fit the image into the preview window
        """
        pass        
        
              
    def zoomToFit(self,evt):
        """
        Method: zoomToFit()
        Created: 21.02.2005, KP
        Description: Sets the zoom factor to fit the image into the preview window
        """
        pass
        
    def zoomTo100(self,evt):
        """
        Method: zoomTo100
        Created: 21.02.2005, KP
        Description: Sets the zoom factor to 1
        """
        pass
        
        
    def renderingPreviewEnabled(self):
        """
        Method: renderingPreviewEnabled()
        Created: 21.02.2005, KP
        Description: Returns true if the rendering preview is enabled
        """
        if self.modeCheckbox:
            return self.modeCheckbox.GetValue()
        return 0
        
        
    def scrollRenderWidget(self,event):
        """
        Method: scrollRenderWidget(self,event)
        Created: 24.11.2004, KP
        Description: Scrolls the preview according to the mouse events received
        Parameters:  event   Tkinter's Event object 
        """
        if not self.mapper:
            return
        self.mapper.UseCustomExtentsOn()
        if self.mapper:
            self.mapper.UseCustomExtentsOn()
            x,y=event.GetPosition()
            xdiff,ydiff=self.startX-x,y-self.startY

            xend=xdiff+self.width
            yend=ydiff+self.height

            if xend>self.xdim:
                xend=self.xdim
            if yend>self.ydim:
                yend=self.ydim
            if xdiff<0:
                xdiff=0
            if ydiff<=0:
                ydiff=0

            print "Viewing from %d,%d to %d,%d"%(xdiff,ydiff,xend,yend)
            self.mapper.SetCustomDisplayExtents([xdiff,xend,ydiff,yend])
            self.updatePreview(0)

            xoff=((1.0*xdiff)/self.xdim)
            yoff=(1.0*ydiff)/self.ydim

    def setTimePointCallback(self,f):
        """
        Method: setTimePointCallback(f)
        Created: 24.11.2004
        Creator: KP
        Description: Registers a callback function for notification when the 
                     previewed timepoint is changed
        """
        self.timePointChangeCallback=f
        f(self.timePoint)

    def getPixelValue(self,event):
        """
        Method: getPixelValue(event)
        Created: 10.11.2004
        Creator: KP
        Description: Shows the RGB and scalar value of a clicked pixel
        Parameters:  event   wx.Python's Event object
        """
        if not self.currentImage:
            return
        x,y=event.GetPosition()
        print "Getting pixel value from %d,%d"%(x,y)
        y=self.ydim-y
        self.startX,self.startY=x,y

        if self.rgbMode==0:
            scalar=self.currentImage.GetScalarComponentAsDouble(x,y,self.z,0)
            print "scalar=",scalar
            r,g,b=self.currentCt.GetColor(scalar)
            r*=255
            g*=255
            b*=255
            frgb=(255-r,255-g,255-b)
            self.pixelLbl.SetForegroundColour(frgb)
            self.pixelPanel.SetBackgroundColour((r,g,b))
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
            txt="Color at (%d,%d,%d) is (%d,%d,%d)"%(x,y,self.z,r,g,b)
            if alpha!=-1:
                txt=txt+" with alpha %d"%alpha
            self.pixelLbl.SetLabel(txt)

    def updateDepth(self,event):
        """
        Method: updateDepth()
        Created: 4.11.2004
        Creator: KP
        Description: Sets the preview to display the selected z slice
        """
        t=time.time()
        if abs(self.depthT-t) < self.updateFactor: return
        self.depthT=time.time()
        newz=self.zslider.GetValue()
        if self.z!=newz:
            self.z=newz
            # was updatePreview(1)
            self.updatePreview(0)

    def gotoTimePoint(self,tp):
        """
        Method: gotoTimePoint(tp)
        Created: 09.12.2004
        Creator: KP
        Description: The previewed timepoint is set to the given timepoint
        Parameters:
                tp      The timepoint to show
        """
        self.timeslider.SetValue(tp)
        self.updateTimePoint(None)

    def updateTimePoint(self,event):
        """
        Method: updateTimePoint()
        Created: 04.11.2004
        Creator: KP
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
            if self.timePointChangeCallback:
                self.timePointChangeCallback(timePoint)

    def setDataUnit(self,dataUnit):
        """
        Method: setDataUnit(dataUnit)
        Created: 04.11.2004
        Creator: KP
        Description: Set the dataunit used for preview. Should be a combined 
                     data unit, the source units of which we can get and read 
                     as ImageData
        """
        self.dataUnit=dataUnit
        try:
            count=dataUnit.getLength()
            x,y,z=dataUnit.getDimensions()
        except GUIError, ex:
            ex.show()
            return
        self.xdim,self.ydim,self.zdim=x,y,z
        
        nx,ny=x,y
        dx,dy=0,0
        if x<512:
            nx=512
        if y<512:
            ny=512
        print "Setting size to %d,%d"%(nx,ny)
        self.wxrenwin.SetSize((x,y))
        self.renderpanel.SetBackgroundColour(wxColour(0,0,0))
#        self.timeslider.SetSize((x,-1))
#        self.zslider.SetSize((-1,y))
        
        if self.show["ZSLIDER"]:
            print "zslider goes to %d"%(z-1)
            self.zslider.SetRange(0,z-1)
        if x>self.maxX:
            x=self.maxX
        if y>self.maxY:
            y=self.maxY
        self.width=x
        self.height=y
        if self.show["TIMESLIDER"]:
            self.timeslider.SetRange(0,count-1)
        self.renderingInterface.setDataUnit(dataUnit)

        print "Setting renderpanel to %d,%d"%(x,y)
        self.renderpanel.SetSize((x,y))
        self.renwin.SetSize((x,y))
        if x>self.maxX or y>self.maxY:       
            self.renderpanel.SetupScrolling()
        self.renderpanel.Layout()
        #self.wxrenwin.SetSize((x,y))
        #self.renderpanel.SetupScrolling()
        #self.renderpanel.Layout()
        #self.previewsizer.Fit(self.renderpanel)
        #self.previewsizer.SetSizeHints(self.renderpanel)
        
        self.Layout()
        self.sizer.Fit(self)
        self.sizer.SetSizeHints(self)
        
        self.Layout()
        self.parentwin.mainsizer.Fit(self.parentwin)
        self.parentwin.Layout()

    def previewInMayavi(self,imagedata,ctf=None,renew=1):
        """
        Method: previewInMayavi(imagedata,ctf,renew)
        Created: 13.12.2004
        Creator: KP
        Description:
        Parameters:
                imagedata    Data to preview
                ctf          Color transfer function for the data
        """
        if not renew:
            return
        self.renderingInterface.setPath(".")
        self.renderingInterface.setTimePoints([self.timePoint])
        self.renderingInterface.doRendering(preview=imagedata,ctf=ctf)


    def updatePreview(self,renew=1):
        """
        Method: updatePreview(renew=1)
        Created: 03.11.2004
        Creator: KP
        Description: Update the preview
        Parameters:
            renew    Whether the method should recalculate the images
        """
        raise "updatePreview() called from the base class"

    
