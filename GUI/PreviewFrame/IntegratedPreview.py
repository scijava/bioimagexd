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
__version__ = "$Revision: 1.40 $"
__date__ = "$Date: 2005/01/13 14:52:39 $"

import os.path

from PreviewFrame import *
import wx
from DataUnit import CombinedDataUnit

import ColorTransferEditor

import Modules
import Logging
import vtk
import wx.lib.scrolledpanel as scrolled

class IntegratedPreview(PreviewFrame):
    """
    Class: IntegratedPreview
    Created: 03.04.2005, KP
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
        
        self.enabled=1
        
        self.ID_MERGE=wx.NewId()
        self.ID_COLOC=wx.NewId()
        self.ID_SINGLE=wx.NewId()
        self.ID_MIP=wx.NewId()
               
        self.mip = 0
        self.previewtype=""
        self.modules=Modules.DynamicLoader.getTaskModules()
        self.modules[""]=self.modules["Process"]
        for key in self.modules:
            self.modules[key]=self.modules[key][0]
        
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
        item = wx.MenuItem(self.typemenu,self.ID_MIP,"Maximum Intensity Projection")
        self.Bind(wx.EVT_MENU,self.setPreviewType,id=self.ID_MIP)
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
            if event=="MIP":
                self.previewtype=""
                self.mip=1
                return
            else:
                self.previewtype=event
                return
        else:
            eid=event.GetId()
            if eid==self.ID_COLOC:
                self.previewtype="Colocalization"
            elif eid==self.ID_MERGE:
                self.previewtype="Merging"
            elif eid==self.ID_MIP:
                self.previewtype=""
                self.mip =1 
                return
            else:
                self.previewtype=""
    
        self.mip = 0
        self.renderpanel.setSingleSliceMode(0)            
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
                Logging.info("Converting settings of %s to %s"%(unit,settingstype),kw="preview")
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
            ct = self.settings.get("%sColorTransferFunction"%self.previewtype)
        
            if self.selectedItem != -1:
                ctc = self.settings.getCounted("%sColorTransferFunction"%self.previewtype,self.selectedItem)            
                if ctc:
                    Logging.info("Using item %d (counted)"%self.selectedItem,kw="preview")
                    ct=ctc
            
        self.currentCt = ct
        #self.currentCt=ImageOperations.getColorTransferFunction(self.rgb)
        
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
            if self.mip:
                data.SetUpdateExtent(data.GetWholeExtent())
                mip=vtk.vtkImageSimpleMIP()
                mip.SetInput(data)
                mip.Update()
                data=mip.GetOutput()
                data.SetUpdateExtent(data.GetWholeExtent())
            
            self.mapToColors.RemoveAllInputs()
            self.mapToColors.SetInput(data)
            
            self.updateColor()
            
            colorImage=self.mapToColors.GetOutput()
            colorImage.SetUpdateExtent(data.GetExtent())
            self.mapToColors.Update()
            data=self.mapToColors.GetOutput()
        else:
            pass
                
        return data
        
    def enable(self,flag):
        """
        Method: enable(flag)
        Created: 02.06.2005, KP
        Description: Enable/Disable updates
        """
        self.enabled=flag
        
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
        if not self.enabled:
            Logging.info("Preview not enabled, won't render",kw="preview")
            return
        self.updateColor()
        if not self.running:
            renew=1
            self.running=1
        if isinstance(self.dataUnit,CombinedDataUnit):
            try:
                preview=self.dataUnit.doPreview(self.z,renew,self.timePoint)
            except Logging.GUIError, ex:
                ex.show()
                return
        else:
            preview = self.dataUnit.getTimePoint(self.timePoint)
        if not preview:
            raise "Did not get a preview"
        self.currentImage=preview

        colorImage = self.processOutputData(preview)
        
        x,y,z=preview.GetDimensions()
    
        if x!=self.oldx or y!=self.oldy:
            self.renderpanel.resetScroll()
            self.renderpanel.setScrollbars(x,y)
            self.oldx=x
            self.oldy=y
            
        Logging.info("Setting image of renderpanel (not null: %s)"%(not not colorImage),kw="preview")
        self.renderpanel.setImage(colorImage)
        self.renderpanel.setZSlice(self.z)
        self.renderpanel.updatePreview()
    
        self.finalImage=colorImage


