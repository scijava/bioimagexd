#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: TaskWindow.py
 Project: Selli
 Created: 23.11.2004
 Creator: KP
 Description:

 A panel that is a base class for all the task panels that are 
 used to control the settings for the various modules. Expects to be handed a 
 CombinedDataUnit() containing the datasets that the module processes
 Uses the Visualizer for previewing.

 Modified:
    	   23.11.2004 KP - Created from ColocalizationWindow

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
__version__ = "$Revision: 1.21 $"
__date__ = "$Date: 2005/01/13 14:36:20 $"

import wx
import wx.lib.scrolledpanel as scrolled


import os.path

from DataUnit import *
from PreviewFrame import *
from Logging import *
from ProcessingManager import *
#from Events import *
#import Events
from GUI import Events

import Dialogs
import sys
import Colocalization
import ColorMerging
import ImageOperations
import ColorTransferEditor


class TaskWindow(scrolled.ScrolledPanel):
    """
    Class: TaskWindow
    Created: 23.11.2004, KP
    Description: A baseclass for a window for controlling the settings of the 
                 various task module
    """
    def __init__(self,root,tb):
        """
        Method: __init__(root,title)
        Created: 03.11.2004, KP
        Description: Initialization
        Parameters:
                root    Is the parent widget of this window
                title   Is the title for this window
        """
        #wx.Dialog.__init__(self,root,-1,"Task Window",
        #style=wx.CAPTION|wx.STAY_ON_TOP|wx.CLOSE_BOX|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX|wx.RESIZE_BORDER|wx.DIALOG_EX_CONTEXTHELP,
        #wx.Frame.__init__(self,root,-1,"Task Window",style=wx.DEFAULT_FRAME_STYLE, #|wx.NO_FULL_REPAINT_ON_RESIZE,
        #size=(1024,768))
        scrolled.ScrolledPanel.__init__(self,root,-1,size=(200,-1))
        self.toolMgr = tb
        # Unbind to not get annoying behaviour of scrolling
        # when clicking on the panel
        self.Unbind(wx.EVT_CHILD_FOCUS)
        
        #self.panel=self#wx.Panel(self,-1)
        self.buttonPanel = wx.Panel(self,-1)
        self.root=root
        self.preview=None

        #self.Bind(wx.EVT_CLOSE,self.closeWindowCallback)
        self.mainsizer=wx.GridBagSizer()


        self.settingsSizer=wx.GridBagSizer()
        #self.mainsizer.Add(self.settingsSizer,(0,1),flag=wx.EXPAND|wx.ALL)
        self.mainsizer.Add(self.settingsSizer,(0,0),flag=wx.EXPAND|wx.ALL)
        self.settingsNotebook=wx.Notebook(self,-1,style=wx.NB_MULTILINE)
        
        font=self.settingsNotebook.GetFont()
        font.SetPointSize(font.GetPointSize()-1)
        self.settingsNotebook.SetFont(font)

        #self.staticLine=wx.StaticLine(self)
        #self.mainsizer.Add(self.staticLine,(2,0),span=(1,1),flag=wx.EXPAND)

        self.buttonSizer=wx.BoxSizer(wx.HORIZONTAL)
        self.buttonPanel.SetSizer(self.buttonSizer)
        self.buttonPanel.SetAutoLayout(1)
        self.mainsizer.Add(self.buttonPanel,(1,0),span=(1,1),flag=wx.EXPAND)

        
        # GET THESE
        #self.Bind(EVT_ZSLICE_CHANGED,self.updateZSlice,id=self.preview.GetId())
        #self.Bind(EVT_TIMEPOINT_CHANGED,self.updateTimepoint,id=ID_TIMEPOINT)
        
        #self.preview = ColorMergingPreview(self)
        #self.previewSizer.Add(self.preview,(0,1),flag=wx.EXPAND|wx.ALL)
    
    
        self.filePath=None
        self.dataUnit=None
        self.settings = None
        self.cancelled=0

        self.createButtonBox()
        self.createOptionsFrame()

        self.SetSizer(self.mainsizer)
        self.SetAutoLayout(True)
        #self.mainsizer.Fit(self)
        #self.mainsizer.SetSizeHints(self)
        
        self.SetupScrolling()
        #self.Bind(wx.EVT_SIZE,self.OnSize)

    def createItemToolbar(self):
        """
        Method: createItemToolbar()
        Created: 31.03.2005, KP
        Description: Method to create a toolbar for the window that allows use to select processed channel
        """      
        #self.tb2 = self.CreateToolBar(wx.TB_HORIZONTAL)
        self.toolMgr.clearItemsBar()
        print "Creating item toolbar"
        #self.tb2 = wx.ToolBar(self,-1,style=wx.TB_VERTICAL|wx.TB_TEXT)
        #self.tb2.SetToolBitmapSize((32,32))# this required for non-standard size buttons on MSW
        #self.tb2 = self.toolbar
        n=0
        #self.tb2.AddSeparator()
        
        for dataunit in self.dataUnit.getSourceDataUnits():
            #color = dataunit.getColor()
            ctf = dataunit.getColorTransferFunction()
            name = dataunit.getName()
            dc= wx.MemoryDC()
            bmp=ImageOperations.vtkImageDataToPreviewBitmap(dataunit.getTimePoint(0),ctf,30,30)
            dc.SelectObject(bmp)
            dc.BeginDrawing()
#            dc.SetFont(wx.Font(9,wx.SWISS,wx.NORMAL,wx.BOLD))
#            dc.SetTextForeground(wx.Colour(255,255,255))
#            w,h=dc.GetTextExtent(name)
#            d=(32-w)/2.0
#            dy=(32-h)
#            if d<0:d=0
#            dc.DrawText(name,d,dy)
            val=[0,0,0]
            ctf.GetColor(255,val)
            dc.SetBrush(wx.TRANSPARENT_BRUSH)
            r,g,b=val
            r*=255
            g*=255
            b*=255
            dc.SetPen(wx.Pen(wx.Colour(r,g,b),4))
            dc.DrawRectangle(0,0,32,32)
            dc.EndDrawing()
            dc.SelectObject(wx.EmptyBitmap(0,0))
            toolid=wx.NewId()
            #self.tb2.AddRadioTool(toolid,name,bmp,shortHelp=name)
            self.toolMgr.addItem(name,bmp,toolid,lambda e,x=n,s=self:s.selectItem(e,x))
            #self.tb2.AddTool(toolid,bmp)#,shortHelp=name)
            n=n+1

        #self.mainsizer.Add(self.tb2,(0,4))
        #self.tb2.Realize()
        #return self.tb2
        #self.previewSizer.Add(self.tb2,(0,0))
        #self.Bind(EVT_DATA_UPDATE,self.updateRendering,id=self.GetId())
        
    def OnSize(self,event):
        """
        Method: OnSize(event)
        Created: n/a, KP
        Description: Method called when the window size changes
        """        
        self.SetSize(event.GetSize())
        self.Layout()
        self.buttonPanel.Layout()

    def updateZSlice(self,event):
        """
        Method: updateZSlice(event)
        Created: 03.04.2005, KP
        Description: A callback function called when the zslice is changed
        """
        pass
        
    def updateTimepoint(self,event):
        """
        Method: updateTimepoint(event)
        Created: 04.04.2005, KP
        Description: A callback function called when the timepoint is changed
        """
        pass
        
    def getResult(self):
        """
        Method: getResult()
        Created: 15.11.2004, KP
        Description: Method to get the results of this task window.
                     If cancel was pressed, returns None, otherwise returns the
                     new dataunit
        """
        if self.cancelled:
            return None,None
        return self.dataUnit,self.filePath

    def createButtonBox(self):
        
        
        self.buttonsSizer2=wx.BoxSizer(wx.HORIZONTAL)

        self.previewButton=wx.Button(self.buttonPanel,-1,"Preview")
        self.previewButton.Bind(wx.EVT_BUTTON,self.doPreviewCallback)
        self.buttonsSizer2.Add(self.previewButton)        
        
        self.processButton=wx.Button(self.buttonPanel,-1,"Process dataset")
        #self.processDatasetButton.Bind(EVT_BUTTON,self.doProcessingCallback)
        self.buttonsSizer2.Add(self.processButton)

        self.buttonSizer.Add(self.buttonsSizer2)    

        
    def createOptionsFrame(self):
        """
        Method: createOptionsFrame()
        Created: 03.11.2004, KP
        Description: Creates a frame that contains the various widgets
                     used to control the colocalization settings
        """

        #self.commonSettingsPanel=wx.Panel(self.settingsNotebook,-1)
        #self.settingsNotebook.AddPage(self.commonSettingsPanel,"General")
#        self.commonSettingsPanel.SetBackgroundColour(wx.Colour(255,0,0))
        self.commonSettingsSizer=wx.GridBagSizer()

        self.namesizer=wx.BoxSizer(wx.VERTICAL)
        self.commonSettingsSizer.Add(self.namesizer,(0,0))
        

        self.taskNameLbl=wx.StaticText(self,-1,"Dataunit Name:")
        self.taskName=wx.TextCtrl(self,-1,size=(250,-1))
        self.namesizer.Add(self.taskNameLbl)
        self.namesizer.Add(self.taskName)

        #self.commonSettingsPanel.SetSizer(self.commonSettingsSizer)
        #self.commonSettingsPanel.SetAutoLayout(1)

#        self.commonSettingsPanel.SetBackgroundColour(self.GetBackgroundColour())
#        self.taskNameLbl.SetBackgroundColour(self.GetBackgroundColour())
        self.settingsSizer.Add(self.commonSettingsSizer,(0,0),flag=wx.EXPAND|wx.ALL)
        self.settingsSizer.Add(self.settingsNotebook,(1,0),flag=wx.EXPAND|wx.ALL)
        self.Layout()

    def selectItem(self,event,index=-1):
        """
        Method: selectItem(event)
        Created: 03.11.2004, KP
        Description: A callback function called when a channel is selected in
                     the menu
        """
        print "Select item(",event,",",index,")"
        if index==-1:
            raise "No index given"
            index=self.itemMenu.GetSelection()
        print "Selecting item %d"%index
        #name=self.itemMenu.GetString(index)
        #print "Now configuring item",name
        #print "self.Dataunit.getSetting()=",self.dataUnit.getSettings()
        self.settings = self.dataUnit.getSourceDataUnits()[index].getSettings()
        
        #self.preview.setSelectedItem(index)
        
        #print "Got settings = ",self.settings
        self.updateSettings()

    def updateSettings(self):
        """
        Method: updateSettings()
        Created: 03.11.2004, KP
        Description: A method used to set the GUI widgets to their proper values
                     based on the selected channel, the settings of which are
                     stored in the instance variable self.settings
        """
        raise "Abstract method updateSetting() called from base class"

    def doOperation(self):
        """
        Method: doOperation()
        Created: 03.2.2005, KP
        Description: A method that executes the operation on the selected
                     dataset
        """
        name=self.taskName.GetValue()
        self.dataUnit.setName(name)
        
        mgr=ProcessingManager(self,self.operationName)
        mgr.setDataUnit(self.dataUnit)
        self.grayOut()

        if mgr.ShowModal() == wx.ID_OK:
            self.Close()
            return
        self.grayOut(1)

        
    def closeWindowCallback(self,event):
        """
        Method: closeWindowCallback()
        Created: 03.11.2004
        Creator: KP
        Description: A method that withdraws (i.e. hides) the colocalization
                     window, but does not destory it.
        """
        print "Closing..."
        self.cancelled=1
        # These calls are necessary to have proper functioning in windows
        self.preview.Show(0)
        self.preview.Destroy()
        self.Destroy()
        #self.EndModal(wx.ID_OK)

        
    def grayOut(self,enable=0):
        """
        Method: grayOut(enable=0)
        Created: 16.11.2004
        Creator: KP
        Description: Grays out the widget while doing colocalization
        Parameters:
            enable      If the enable parameter is defined, the effect of the
                        function is reversed and the widgets are set to normal
                        state

        """
        # TODO: Implement properly
        if enable==1:
            self.Enable(1)
    
        else:
            self.Enable(0)

    def doPreviewCallback(self,event=None):
        """
        Method: doPreviewCallback()
        Created: 03.11.2004, KP
        Description: A callback for the button "Preview" and other events
                     that wish to update the preview
        """
        #if self.preview:
        #    self.preview.updatePreview()
        print "Sending update event, id=",self.GetId()
        print "Sending out ",Events.myEVT_DATA_UPDATE
        evt=Events.DataUpdateEvent(Events.myEVT_DATA_UPDATE,self.GetId(),delay=0)
        self.GetEventHandler().ProcessEvent(evt)


    def loadSettingsCallback(self,event):
        """
        Method: loadSettingsCallback()
        Created: 30.11.2004, KP
        Description: A callback to load the settings for this operation from a
                     du file
        """
        wc="Dataset Settings(*.du)|*.du"
        dlg=wx.FileDialog(self,"Load dataset settings from file",wildcard=wc,style=wx.OPEN)
        filename=None
        if dlg.ShowModal()==wx.ID_OK:
            filename=dlg.GetPath()
        
        dlg.Destroy()
        if not filename:
            return
        self.dataUnit.loadSettings(filename)
        self.updateSettings()


    def saveSettingsCallback(self,event):
        """
        Method: saveSettingsCallback()
        Created: 30.11.2004, KP
        Description: A callback to save the settings for this operation to a 
                     du file
        """
        wc="Dataset Settings(*.du)|*.du"
        dlg=wx.FileDialog(self,"Save dataset settings to file",wildcard=wc,style=wx.SAVE)
        filename=None
        if dlg.ShowModal()==wx.ID_OK:
            filename=dlg.GetPath()
        
        dlg.Destroy()

        if not filename:
            return
        if filename[-3:].lower()!=".du":
            filename+=".du"

        print "Saving to ",filename

        self.updateSettings()
        self.dataUnit.doProcessing(filename,settings_only=True)

    def setCombinedDataUnit(self,dataUnit):
        """
        Method: setCombinedDataUnit(dataUnit)
        Created: 23.11.2004, KP
        Description: Sets the combined dataunit that is to be processed.
                     It is then used to get the names of all the source data
                     units and they are added to the menu.
        """
        self.dataUnit=dataUnit
        name=dataUnit.getName()
        print "Name of dataUnit=%s"%name
        self.taskName.SetValue(name)
        try:
            #self.preview.setDataUnit(dataUnit)
            units=self.dataUnit.getSourceDataUnits()
            
        except GUIError, ex:
            ex.show()
        #names=[i.getName() for i in units]
        #for name in names:
        #        self.itemMenu.Append(name)
        self.selectItem(None,0)
        #self.itemMenu.SetSelection(0)
        self.createItemToolbar()
