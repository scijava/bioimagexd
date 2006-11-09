# -*- coding: iso-8859-1 -*-

"""
 Unit: AnnotationToolbar
 Project: BioImageXD
 Created: 03.02.2005, KP
 Description:

 A toolbar for the annotations in visualizer

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
__author__ = "BioImageXD Project"
__version__ = "$Revision: 1.21 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"


import  wx
import wx.lib.buttons as buttons
import  wx.lib.colourselect as  csel

import MenuManager
import scripting
import messenger

import os

class AnnotationToolbar(wx.Window):
    """
    Created: 06.11.2006, KP
    Description: A class representing the vertical annotation toolbar of the visualizer
    """
    def __init__(self, parent, visualizer):
        wx.Window.__init__(self, parent,-1)
        self.visualizer = visualizer
        self.channelButtons = {}
        self.annotateColor = (0,255,0)
        
        self.sizer = wx.GridBagSizer(2,2)
        self.SetSizer(self.sizer)
        
        self.SetAutoLayout(1)
        
        self.numberOfChannels = 0
        messenger.connect(None,"update_annotations",self.updateAnnotations)
        self.createAnnotationToolbar()        
        
    def createAnnotationToolbar(self):
        """
        Created: 05.10.2006, KP
        Description: Method to create a toolbar for the annotations
        """        
        def createBtn(bid, gifname, tooltip, btnclass = buttons.GenBitmapToggleButton):
            icondir = scripting.get_icon_dir()  
            bmp = wx.Image(os.path.join(icondir,gifname),wx.BITMAP_TYPE_GIF).ConvertToBitmap()
            
            btn = btnclass(self, bid, bmp)
            
            btn.SetBestSize((32,32))
            #btn.SetBitmapLabel()
            btn.SetToolTipString(tooltip)
            return btn
        
        self.circleBtn = createBtn(MenuManager.ID_ROI_CIRCLE,"circle.gif","Select a circular area of the image")
        self.sizer.Add(self.circleBtn, (0,0))
        
        self.rectangleBtn = createBtn(MenuManager.ID_ROI_RECTANGLE,"rectangle.gif","Select a circular area of the image")
        self.sizer.Add(self.rectangleBtn, (0,1))
        
        self.polygonBtn = createBtn(MenuManager.ID_ROI_POLYGON,"polygon.gif","Select a polygonal area of the image")
        self.sizer.Add(self.polygonBtn, (1,0))
        
        self.scaleBtn = createBtn(MenuManager.ID_ADD_SCALE,"scale.gif","Draw a scale bar on the image")
        self.sizer.Add(self.scaleBtn, (1,1))



        self.textBtn = createBtn(MenuManager.ID_ANNOTATION_TEXT,"text.gif","Add a text annotation")
        self.sizer.Add(self.textBtn, (2,0))

        self.deleteAnnotationBtn = createBtn(MenuManager.ID_DEL_ANNOTATION,"delete_annotation.gif","Delete an annotation")
        self.sizer.Add(self.deleteAnnotationBtn, (4,1))   

        self.roiToMaskBtn = createBtn(MenuManager.ID_ROI_TO_MASK,"roitomask.gif","Convert the selected Region of Interest to a Mask", btnclass=buttons.GenBitmapButton)
        self.sizer.Add(self.roiToMaskBtn, (4,0))

        #self.fontBtn = createBtn(MenuManager.ID_ANNOTATION_FONT,"fonts.gif","Set the font for annotations", btnclass=buttons.GenBitmapButton)
        #self.sizer.Add(self.fontBtn, (3,1))

        self.colorSelect = csel.ColourSelect(self, -1, "", self.annotateColor, size = (65,-1))
        self.sizer.Add(self.colorSelect, (5,0),span=(1,2))

        self.circleBtn.Bind(wx.EVT_BUTTON, self.addAnnotation)
        self.rectangleBtn.Bind(wx.EVT_BUTTON, self.addAnnotation)
        self.polygonBtn.Bind(wx.EVT_BUTTON, self.addAnnotation)
        self.scaleBtn.Bind(wx.EVT_BUTTON, self.addAnnotation)
        self.roiToMaskBtn.Bind(wx.EVT_BUTTON,self.roiToMask)
        #wx.EVT_TOOL(self.parent,MenuManager.ID_ADD_SCALE,self.addAnnotation)
        self.deleteAnnotationBtn.Bind(wx.EVT_BUTTON,self.deleteAnnotation)

    def clearChannelItems(self):
        """
        Created: 06.11.2006, KP
        Description: Remove all the channel items
        """
        for key in self.channelButtons.keys():
            btn = self.channelButtons[key]
            btn.Show(0)
            self.sizer.Detach(btn)
            self.sizer.Remove(btn)
            del btn
        self.numberOfChannels=0
        
        
    def addChannelItem(self,name,bitmap,toolid,func):
        """
        Created: 01.06.2005, KP
        Description: Add a channel item
        """ 
        icondir = scripting.get_icon_dir()         
        btn = buttons.GenBitmapToggleButton(self, toolid, bitmap)
        w,h = bitmap.GetWidth(),bitmap.GetHeight()
        #btn.SetBestSize((w,h))            
        btn.SetSize((64,64))
        btn.SetToolTipString(name)
        btn.Bind(wx.EVT_BUTTON,func)
        
        self.numberOfChannels+=1
        self.sizer.Add(btn, (5+self.numberOfChannels,0),span=(1,2))
        self.channelButtons[toolid]=btn
        self.Layout()
        
    def toggleChannelItem(self, toolid, flag):
        """
        Created: 06.11.2006, KP
        Description: Toggle a channel item on or off
        """
        self.channelButtons[toolid].SetToggle(flag)
        
    def addAnnotation(self,event):
        """
        Created: 03.07.2005, KP
        Description: Draw a scale to the visualization
        """
        if not self.visualizer.currMode:
            return
        annclass=None
        eid=event.GetId()
        multiple=0
        if eid==MenuManager.ID_ADD_SCALE:
            annclass="SCALEBAR"
        elif eid == MenuManager.ID_ANNOTATION_TEXT:
            annclass="TEXT"
        elif eid == MenuManager.ID_ROI_CIRCLE:
            annclass="CIRCLE"

        elif eid==MenuManager.ID_ROI_RECTANGLE:
            annclass="RECTANGLE"
        elif eid==MenuManager.ID_ROI_POLYGON:
            annclass="POLYGON"
            multiple=1
        else:
            Logging.info("BOGUS ANNOTATION SELECTED!",kw="visualizer")
                        
        self.visualizer.currMode.annotate(annclass,multiple=multiple)
        
        
    def deleteAnnotation(self,event):
        """
        Created: 04.07.2005, KP
        Description: DElete annotations on the image
        """
        if self.visualizer.currMode:
            self.visualizer.currMode.deleteAnnotation()

    def updateAnnotations(self, *args):
        """
        Created: 05.10.2006, KP
        Description: Untoggle the annotation buttons because an annotation was added
        """
        self.scaleBtn.SetToggle(False)
        self.circleBtn.SetToggle(False)
        self.rectangleBtn.SetToggle(False)
        self.polygonBtn.SetToggle(False)
                
                
    def roiToMask(self, evt):
        """
        Created: 20.06.2006, KP
        Description: Convert the selected ROI to mask
        """
        if hasattr(self.visualizer.currentWindow, "roiToMask"):
            imagedata, names=self.visualizer.currentWindow.roiToMask()
            #name = self.dataUnit.getName()
            name=",".join(names)
            dims = self.visualizer.dataUnit.getDimensions()
            mask = MaskTray.Mask(name,dims,imagedata)
            self.visualizer.setMask(mask)                
