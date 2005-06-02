# -*- coding: iso-8859-1 -*-

"""
 Unit: SectionsPanel.py
 Project: BioImageXD
 Created: 23.05.2005, KP
 Description:

 A panel that can display previews of all the optical slices of
 volume data independent of a VTK render window,using the tools provided by wxPython.
 
 Modified 23.05.2005 KP - Created the class
          
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
import vtk
from IntegratedPreview import *
from GUI import Events

class SectionsPanel(wx.Panel):
    """
    Class: SectionsPanel
    Created: 23.05.2005, KP
    Description: A widget that previews the xy,xz and yz planes of a dataset
    """
    def __init__(self,parent,**kws):
        """
        Method: __init__
        Created: 23.5.2005, KP
        Description: Initialize
        """    
        wx.Panel.__init__(self,parent,-1,**kws)
        self.sizer=wx.GridBagSizer()
        
        self.xypreview=IntegratedPreview(self,
        previewsize=(512,512),pixelvalue=False,renderingpreview=False,
                zoom=False,zslider=False,timeslider=False,scrollbars=False
                )
        self.xypreview.setPreviewType("")
        
        self.xzpreview=IntegratedPreview(self,
        previewsize=(75,512),pixelvalue=False,renderingpreview=False,
                zoom=False,zslider=False,timeslider=False,scrollbars=False,
                plane="zx")
        self.xzpreview.setPreviewType("")
        
        self.yzpreview=IntegratedPreview(self,
        previewsize=(512,75),pixelvalue=False,renderingpreview=False,
                zoom=False,zslider=False,timeslider=False,scrollbars=False,
                plane="yz")
        self.yzpreview.setPreviewType("")
        
        self.sizer.Add(self.xypreview,(0,0),flag=wx.EXPAND|wx.ALL,border=5)
        self.sizer.Add(self.xzpreview,(0,1),flag=wx.EXPAND|wx.ALL,border=5)
        self.sizer.Add(self.yzpreview,(1,0),flag=wx.EXPAND|wx.ALL,border=5)

        self.xypreview.Bind(EVT_VOXEL,self.onSetVoxel,id=self.xypreview.GetId())
        self.xzpreview.Bind(EVT_VOXEL,self.onSetVoxel,id=self.xzpreview.GetId())
        self.yzpreview.Bind(EVT_VOXEL,self.onSetVoxel,id=self.yzpreview.GetId())
        
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)
        
    def onSetVoxel(self,event):
        """
        Method: onSetVoxel
        Created: 23.05.2005, KP
        Description: Set the plane to be shown
        """
        x,y,z=event.getCoord()
        print "showing ",x,y,z
        if event.GetId()==self.xypreview.GetId():
            self.yzpreview.setPreviewedSlice(None,x)
            self.xzpreview.setPreviewedSlice(None,y)
        if event.GetId()==self.xzpreview.GetId():
            self.yzpreview.setPreviewedSlice(None,x)
            print "Setting z to",z
            self.xypreview.setPreviewedSlice(None,z)
        if event.GetId()==self.yzpreview.GetId():
            self.xzpreview.setPreviewedSlice(None,y)
            self.xypreview.setPreviewedSlice(None,z)
            print "Setting z to",z
            
            
        
    def setDataUnit(self,dataUnit,selectedItem=-1):
        """
        Method: setDataUnit(dataUnit)
        Created: 23.05.2005, KP
        Description: Set the dataunit used for preview. 
        """
        for preview in [self.xypreview,self.xzpreview,self.yzpreview]:
            preview.setDataUnit(dataUnit,selectedItem)
        #self.xypreview.setDataUnit(dataUnit,selectedItem)
        
    def setTimepoint(self,tp):
        """
        Method: setTimepoint(dataUnit)
        Created: 23.05.2005, KP
        Description: Set the timepoint
        """
        for preview in [self.xypreview,self.xzpreview,self.yzpreview]:
            preview.setTimepoint(tp)
            preview.updatePreview(1)
        #self.xypreview.setTimepoint(tp)
        
    
