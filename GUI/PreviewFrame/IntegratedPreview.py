# -*- coding: iso-8859-1 -*-

"""
 Unit: IntegratedFrame.py
 Project: BIoImageXD
 Created: 03.04.2005
 Creator: KP
 Description:

 A widget that can be used to Preview any operations done by a subclass of Module.
 The type of preview can be selected and depends on the type of data that is input.

 Modified 03.04.2005 KP - Started integration of code from all the different classes
                          into one integrated preview
 
  BioImageXD includes the following persons:

  DW - Dan White, dan@chalkie.org.uk
  KP - Kalle Pahajoki, kalpaha@st.jyu.fi
  PK - Pasi Kankaanpää, ppkank@bytl.jyu.fi
 """
__author__ = "BioImageXD Project"
__version__ = "$Revision: 1.40 $"
__date__ = "$Date: 2005/01/13 14:52:39 $"
import os.path
import RenderingInterface

from PreviewFrame import *
import wx

from Logging import *
import vtk
import wx.lib.scrolledpanel as scrolled

class IntegratedPreview(PreviewFrame):
    """
    Class: IntegratedPreview
    Created: 03.04.2005
    Creator: KP
    Description: A widget that previews data output by wide variety
                 of processing modules
    """
    def __init__(self,master,parentwin=None,**kws):
        PreviewFrame.__init__(self,master,parentwin,**kws)
        self.running=0
        self.mapToColors=vtk.vtkImageMapToColors()
        self.mapToColors.SetLookupTable(self.currentCt)
        self.mapToColors.SetOutputFormatToRGB()
        self.renderpanel.Bind(wx.EVT_RIGHT_DOWN,self.onRightClick)
        
        self.ID_MERGE=wx.NewId()
        self.ID_COLOC=wx.NewId()
        self.ID_SINGLE=wx.NewId()
        
        self.colortype=""
        self.menu=wx.Menu()
        self.typemenu=wx.Menu()        
        
        item = wx.MenuItem(self.typemenu,self.ID_MERGE,"Merged channels")
        self.Bind(wx.EVT_MENU,self.setPreviewType,id=self.ID_MERGE)
        self.typemenu.AppendItem(item)
        item = wx.MenuItem(self.typemenu,self.ID_COLOC,"Colocalization")
        self.Bind(wx.EVT_MENU,self.setPreviewType,id=self.ID_COLOC)
        self.typemenu.AppendItem(item)
        item = wx.MenuItem(self.typemenu,self.ID_SINGLE,"Single channel")
        self.Bind(wx.EVT_MENU,self.setPreviewType,id=self.ID_SINGLE)
        self.typemenu.AppendItem(item)
        self.menu.AppendMenu(-1,"&Preview type",self.typemenu)
        
        
        
    def onRightClick(self,event):
        """
        Method: onRightClick
        Created: 03.04.2005, KP
        Description: Method that is called when the right mouse button is
                     pressed down on this item
        """      
        self.PopupMenu(self.menu,event.GetPosition())
        
    def setPreviewType(self,event):
        """
        Method: setPreviewType
        Created: 03.04.2005, KP
        Description: Method to set the proper previewtype
        """      
        if type(event)==type(""):
            self.colortype=event
            return
        eid=event.GetId()
        if eid==self.ID_COLOC:
            self.colortype="Colocalization"
        else:
            self.colortype=""
            
        
    def updateColor(self):
        """
        Method: updateColor()
        Created: 20.11.2004, KP
        Description: Update the preview to use the selected color transfer 
                     function
        Parameters:
        """
        if self.dataUnit:
            self.rgb = self.settings.get("%sColor"%self.colortype)
            print "Got color ",self.rgb            
        self.currentCt=ImageOperations.getColorTransferFunction(self.rgb)
        self.mapToColors.SetLookupTable(self.currentCt)
        self.mapToColors.SetOutputFormatToRGB()

        
    def processOutputData(self,data):
        """
        Method: processOutputData()
        Created: 03.04.2005, KP
        Description: Process the data before it's send to the preview
        """
        ncomps = data.GetNumberOfScalarComponents()
        if ncomps == 1:
            self.mapToColors.RemoveAllInputs()
            self.mapToColors.SetInput(data)
            self.updateColor()
            #print "Coloring with ",self.currentCt
            colorImage=self.mapToColors.GetOutput()
            #colorImage.SetUpdateExtent(data.GetExtent())
            self.mapToColors.Update()
            data=self.mapToColors.GetOutput()

        return data
        
    def updatePreview(self,renew=1):
        """
        Method: updatePreview(renew=1)
        Created: 03.04.2005, KP
        Description: Update the preview
        Parameters:
        renew    Whether the method should recalculate the images
        """
        if not self.dataUnit:
            return
        
        if not self.running:
            renew=1
            self.running=1
        try:
            preview=self.dataUnit.doPreview(self.z,renew,self.timePoint)
        except GUIError, ex:
            ex.show()
            return
        if not preview:
            raise "Did not get a preview"
        self.currentImage=preview
        
        if self.renderingPreviewEnabled()==True:
            self.updateColor()
            return self.previewInMayavi(preview,self.currentCt,
            renew)
        

        colorImage = self.processOutputData(preview)
        
       
        x,y,z=preview.GetDimensions()
    
        if x!=self.oldx or y!=self.oldy:
            self.renderpanel.resetScroll()
            self.renderpanel.setScrollbars(x,y)
            self.oldx=x
            self.oldy=y
            
 
        self.renderpanel.setZSlice(self.z)
        self.renderpanel.setImage(colorImage)
        self.renderpanel.updatePreview()
    
        self.finalImage=colorImage
