# -*- coding: iso-8859-1 -*-

"""
 Unit: RescaleDialog
 Project: BioImageXD
 Created: 13.02.2006, KP
 Description:

 A dialog for controlling the rescaling that occurs for 12-bit datasets.
 
 Copyright (C) 2006  BioImageXD Project
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
import sys
import Logging
import wx
import UIElements
import string

import PreviewFrame
import Histogram
import Modules
import messenger
import  wx.lib.fancytext as fancytext

class RescaleDialog(wx.Dialog):
    """
    Created: 11.04.2006, KP
    Description: A dialog for rescaling a dataset to 8-bit
    """
    def __init__(self, parent):
        """
        Created: 1.09.2005, KP
        Description: Initialize the dialog
        """    
        wx.Dialog.__init__(self, parent, -1, 'Select mapping to 8-bit values',size=(640,480))
        
        self.sizer=wx.GridBagSizer()
        self.btnsizer=self.CreateButtonSizer(wx.OK|wx.CANCEL)
        self.histograms=[]
        self.dataUnits=[]
        self.resampleDims=[]
        self.shift = 0
        self.scale = 0
        self.taskPanels = Modules.DynamicLoader.getTaskModules()
        self.createRescale()
        self.lbl = wx.StaticText(self,-1,
"""BioImageXD uses 8-bit color depth (256 different intensity values). You are loading a file with a non-8-bit
color depth. Use the histograms below to the select how the intensities in your file are mapped to range 0-255.
""")
        lblbox=wx.BoxSizer(wx.VERTICAL)
        
        hdr = wx.StaticText(self, -1, "Select mapping to 8-bit values", (20, 120))
        font = wx.Font(14, wx.SWISS, wx.NORMAL, wx.NORMAL)
        hdr.SetFont(font)
        lblbox.Add(hdr)
        lblbox.Add(self.lbl)
        self.sizer.Add(lblbox,(1,0),flag=wx.EXPAND|wx.LEFT|wx.RIGHT)
        self.sizer.Add(self.btnsizer,(3,0),flag=wx.EXPAND|wx.RIGHT|wx.LEFT)
        wx.EVT_BUTTON(self,wx.ID_OK,self.onOkButton)
        wx.EVT_BUTTON(self,wx.ID_CANCEL,self.onCancelButton)
        
        self.noScalingButton = wx.Button(self,-1,"No mapping")
        self.noScalingButton.Bind(wx.EVT_BUTTON, self.onNoScaling)
        self.btnsizer.Add(self.noScalingButton)
        self.result=0
        
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)
     
    def onNoScaling(self,event):
        """
        Created: 11.07.2006, KP
        Description: Do not use any intensity scaling
        """        
        self.result = 1
        for i,dataUnit in enumerate(self.dataUnits):
            ds=dataUnit.getDataSource()
            #ds.setResampleDimensions(self.resampleDims[i])
            ds.setIntensityScale(-1,-1)
        self.EndModal(wx.ID_OK)
        
    def onCancelButton(self,event):
        """
        Created: 12.04.2006, KP
        Description: Cancel the procedure
        """        
        for i,dataUnit in enumerate(self.dataUnits):
            ds=dataUnit.getDataSource()
            ds.setIntensityScale(0,0)
            #ds.setResampleDimensions(self.resampleDims[i])
            
        self.result=0
        self.EndModal(wx.ID_CANCEL)   
        
    def onOkButton(self,event):
        """
        Created: 21.04.2005, KP
        Description: Executes the procedure
        """
        for i,dataUnit in enumerate(self.dataUnits):
            ds=dataUnit.getDataSource()
            print "Setting shift and scale to ",self.shift, self.scale
            ds.setIntensityScale(self.shift,self.scale)
            ds.resetColorTransferFunction()
            dataUnit.resetColorTransferFunction()
            #ds.setResampleDimensions(self.resampleDims[i])
            
        self.result=1
        #self.Close()    
        self.EndModal(wx.ID_OK)
        
    def zoomToFit(self):
        self.preview.zoomToFit()
        
    def setDataUnits(self,dataunits):
        """
        Created: 1.09.2005, KP
        Description: Set the dataunits to be resampled
        """        
        self.dataUnits=dataunits
        unitclass = self.taskPanels["Merging"][2].getDataUnit()
        self.mergeUnit = unitclass("Preview for scaling intensity")
                
        for dataUnit in dataunits:
            print "Creating histogram for ",dataUnit
            self.mergeUnit.addSourceDataUnit(dataUnit)
            x,y,z=dataUnit.getDimensions()
            
            ds=dataUnit.getDataSource()
            minval,maxval = ds.getOriginalScalarRange()
            print "Original scalar range = ",minval,maxval
            self.resampleDims.append(ds.getResampleDimensions())
#            if x>512 or y>512:
#                ds.setResampleDimensions((512,512,z))
                
            scale = maxval / 255.0
            print "Using scale",scale
            histogram = Histogram.Histogram(self,scale=scale)
            self.histogramSizer.Add(histogram)
            self.histograms.append(histogram)
            histogram.setThresholdMode(1)
            histogram.setDataUnit(dataUnit,noupdate=1)
            messenger.connect(histogram,"threshold_changed",self.onSetThreshold)
            x,y,z=dataUnit.getDimensions()
            self.zslider.SetRange(1,z)
        
        moduletype = self.taskPanels["Merging"][0]
        module=moduletype()
        self.mergeUnit.setModule(module)
        self.preview.setDataUnit(self.mergeUnit)
        self.preview.zoomToFit()
        self.preview.updatePreview()
        self.sizer.Fit(self)
        self.Layout()
        
    def onSetThreshold(self,obj,event,lower,upper):
        """
        Created: 12.04.2006, KP
        Description: An event handler for updating the thresholds based on one of the histograms
        """            
        n=self.histograms.index(obj)
        dataUnit=self.dataUnits[n]
        minval,maxval = dataUnit.getDataSource().getOriginalScalarRange()
        print "Original scalar range=",minval,maxval
        if lower==0 and upper==255:
            self.shift=0
            self.scale=255.0 / maxval
            print "\n\nSetting shift to ",self.shift,self.scale
            
        else:
            upper = upper * (maxval/255.0)
            lower = lower * (maxval/255.0)
            
            print "lower=",lower,"upper=",upper
            self.shift = -int(lower)
            print "\nCalculating scale based on maxval",maxval
            self.scale = 256.0 / ((upper-lower))
            print "Setting shift and scale to ",self.shift,"and",self.scale
        dataUnit.getDataSource().setIntensityScale(self.shift,self.scale)
        dataUnit.resetColorTransferFunction()
        self.preview.updatePreview(1)
        
        
    def createRescale(self):
        """
        Created: 11.04.2006, KP
        Description: Creates the GUI for controlling the rescaling
        """            
        box=wx.StaticBox(self,-1,"Preview selected mapping")
        previewBox=wx.StaticBoxSizer(box,wx.HORIZONTAL)
        self.preview = PreviewFrame.PreviewFrame(self,previewsize=(256,256),scrollbars=False)
        self.preview.setPreviewType("")
                
        previewBox.Add(self.preview)
        
        self.zslider=wx.Slider(self,value=1,minValue=1,maxValue=1,
        style=wx.SL_VERTICAL|wx.SL_LABELS|wx.SL_AUTOTICKS)
        self.zslider.SetHelpText("Use this slider to select the displayed optical slice.")
        self.zslider.Bind(wx.EVT_SCROLL,self.onChangeZSlice)
        
        previewBox.Add(self.zslider,1,wx.EXPAND)
            
        box=wx.StaticBox(self,-1,"Channel histograms")
        self.histogramSizer = wx.StaticBoxSizer(box,wx.HORIZONTAL)
        
        
        self.sizer.Add(previewBox,(0,0),flag=wx.EXPAND|wx.ALL)
        self.sizer.Add(self.histogramSizer,(2,0),flag=wx.EXPAND|wx.ALL)
        
    def onChangeZSlice(self,event):
        """
        Created: 12.04.2006, KP
        Description: Set the zslice displayed
        """             
        self.preview.setZSlice(self.zslider.GetValue()-1)
        print "Setting preview to ",self.zslider.GetValue()-1
        self.preview.updatePreview(0)