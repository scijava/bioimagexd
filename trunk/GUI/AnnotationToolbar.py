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
import UIElements
import MaskTray

import vtk

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
        self.interactor = None
        
        self.sizer = wx.GridBagSizer(2,2)
        self.SetSizer(self.sizer)
        self.eventRecorder = vtk.vtkInteractorEventRecorder()
        self.SetAutoLayout(1)
        messenger.connect(None,"visualizer_mode_loading",self.onLoadMode)
        
        self.numberOfChannels = 0
        messenger.connect(None,"update_annotations",self.updateAnnotations)
        self.createAnnotationToolbar()        
        
    def onLoadMode(self, obj, evt, vismode):
        """
        Created: 23.04.2007, KP
        Description: an event handler for when visualizer is loading a mode
        """
        renwin = vismode.getRenderWindow()
        if renwin:
            self.interactor = renwin.GetInteractor()
            self.eventRecorder.SetInteractor(self.interactor)
        else:
            self.interactor = None
            
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
        
        self.resamplingBtn = createBtn(MenuManager.ID_RESAMPLING, "resample.gif","Enable or disable the resampling of image data")
        self.resamplingBtn.SetToggle(1)
        
        self.resampleToFitBtn = createBtn(MenuManager.ID_RESAMPLE_TO_FIT, "resample_tofit.gif","Enable or disable the resampling of image data")
        
        self.sizer.Add(self.resamplingBtn, (6,0))
        self.sizer.Add(self.resampleToFitBtn, (6,1))
        
#        self.recordBtn = buttons.GenToggleButton(self, MenuManager.ID_RECORD_EVENTS, "Record", size=(64,-1))
#        self.sizer.Add(self.recordBtn, (7,0), span=(1,2))
        
#        self.playBtn = createBtn(MenuManager.ID_PLAY_EVENTS,"player_play.gif","Play the recorded events", btnclass=buttons.GenBitmapButton)
#        self.stopBtn = createBtn(MenuManager.ID_PLAY_EVENTS,"player_pause.gif","Stop playing the recorded events", btnclass=buttons.GenBitmapButton)
#        self.sizer.Add(self.playBtn, (8,0))
#        self.sizer.Add(self.stopBtn, (8,1))
        
#        self.playBtn.Bind(wx.EVT_BUTTON, self.onPlayRecording)
#        self.stopBtn.Bind(wx.EVT_BUTTON, self.onStopPlaying)
#        self.recordBtn.Bind(wx.EVT_BUTTON, self.onRecord)        
        
          #bmp = wx.Image(os.path.join(iconpath,"resample.gif")).ConvertToBitmap()
        #tb.DoAddTool(MenuManager.ID_RESAMPLING,"Resampling",bmp,kind=wx.ITEM_CHECK,shortHelp="Enable or disable the resampling of image data")
        #wx.EVT_TOOL(self,MenuManager.ID_RESAMPLING,self.onResampleData)
        #tb.EnableTool(MenuManager.ID_RESAMPLING,0)
        #tb.ToggleTool(MenuManager.ID_RESAMPLING,1)
        
        #sbox = wx.StaticBox(self,-1,"Resampling")
        #sboxsizer = wx.StaticBoxSizer(sbox, wx.VERTICAL)
        #self.resamplingOff = wx.RadioButton(self,-1,"Disabled", style = wx.RB_GROUP)
        #self.resamplingOn = wx.RadioButton(self,-1,"Enabled")
        #self.resampleToFit = wx.RadioButton(self,-1,"To fit")
        
        #sboxsizer.Add(self.resamplingOn)
        #sboxsizer.Add(self.resamplingOff)
        #sboxsizer.Add(self.resampleToFit)
        #self.sizer.Add(sboxsizer, (6,0),span=(1,2))
        #self.sizer.Add(self.resamplingOn, (7,0),span=(1,2))
        #self.sizer.Add(self.resampleToFit, (8,0),span=(1,2))
        
        #self.dimInfo = UIElements.DimensionInfo(self,-1, size=(120,50))
        #self.sizer.Add(self.dimInfo, (6,0), span=(1,2))
    
        self.sizerCount = 8
        self.resamplingBtn.Bind(wx.EVT_BUTTON, self.onResampleData)
        self.resampleToFitBtn.Bind(wx.EVT_BUTTON, self.onResampleToFit)
        self.circleBtn.Bind(wx.EVT_BUTTON, self.addAnnotation)
        self.rectangleBtn.Bind(wx.EVT_BUTTON, self.addAnnotation)
        self.polygonBtn.Bind(wx.EVT_BUTTON, self.addAnnotation)
        self.scaleBtn.Bind(wx.EVT_BUTTON, self.addAnnotation)
        self.roiToMaskBtn.Bind(wx.EVT_BUTTON,self.roiToMask)
        #wx.EVT_TOOL(self.parent,MenuManager.ID_ADD_SCALE,self.addAnnotation)
        self.deleteAnnotationBtn.Bind(wx.EVT_BUTTON,self.deleteAnnotation)
        
    def onRecord(self, evt):
        """
        Created: 23.04.2007, KP
        Description: Start / stop recording events
        """
        flag = evt.GetIsDown()
        self.playBtn.Enable(not flag)
        self.stopBtn.Enable(not flag)
        if flag:
            self.eventRecorder.SetEnabled(1)
            self.eventRecorder.SetFileName("events.log")
            self.eventRecorder.Record()
        else:
            self.eventRecorder.Stop()
            self.eventRecorder.SetEnabled(0)

            print "Recorded",self.eventRecorder.GetInputString()
            
    def onPlayRecording(self, evt):
        """
        Created: 23.04.2007, KP
        Description: play a recorded event sequence
        """
        self.eventRecorder.Play()
    def onStopPlaying(self, evt):
        """
        Created: 23.04.2007, KP
        Description: stop playing a recorded event sequence
        """
        self.eventRecorder.Stop()

    def onResampleToFit(self,evt):
        """
        Created: 23.07.2006, KP
        Description: Toggle the resampling on / off
        """
#        flag=self.resampleBtn.GetValue()
        
        flag=evt.GetIsDown()
        scripting.resampleToFit = flag
        self.visualizer.updateRendering()              
    def onResampleData(self,evt):
        """
        Created: 23.07.2006, KP
        Description: Toggle the resampling on / off
        """
#        flag=self.resampleBtn.GetValue()
        
        flag=evt.GetIsDown()
        scripting.resamplingDisabled = not flag
        self.visualizer.updateRendering()              
        if self.zoomToFitFlag:            
            self.visualizer.zoomToFit(None)
        
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
        self.sizer.Add(btn, (self.sizerCount+self.numberOfChannels,0),span=(1,2))
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
