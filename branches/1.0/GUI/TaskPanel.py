# -*- coding: iso-8859-1 -*-
"""
 Unit: TaskPanel
 Project: BioImageXD
 Created: 23.11.2004, KP
 Description:

 A panel that is a base class for all the task panels that are 
 used to control the settings for the various modules. Expects to be handed a 
 CombinedDataUnit() containing the datasets that the module processes
 Uses the Visualizer for previewing.

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
__author__ = "BioImageXD Project <http://www.bioimagexd.org>"
__version__ = "$Revision: 1.21 $"
__date__ = "$Date: 2005/01/13 14:36:20 $"

import wx
import wx.lib.scrolledpanel as scrolled


import os.path

from DataUnit import *
from PreviewFrame import *
from Logging import *
from ProcessingManager import *

import Dialogs
import sys
import ImageOperations
import ColorTransferEditor
import ChannelListBox


class TaskPanel(scrolled.ScrolledPanel):
    """
    Class: TaskPanel
    Created: 23.11.2004, KP
    Description: A baseclass for a panel for controlling the settings of the 
                 various task modules
    """
    def __init__(self,root,tb):
        """
        Method: __init__(root,title)
        Created: 03.11.2004, KP
        Description: Initialization
        Parameters:
                root    Is the parent widget of this window
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
        if not hasattr(self,"createItemSelection"):
            self.createItemSelection=0

        n=0
        self.channelBox=None
        if self.createItemSelection:
            self.channelBox = ChannelListBox.ChannelListBox(self, size=(250, 72), style=wx.BORDER_SUNKEN|wx.LB_NEEDED_SB)
            self.mainsizer.Add(self.channelBox,(n,0))
            n+=1
        
        self.settingsSizer=wx.GridBagSizer()
        #self.mainsizer.Add(self.settingsSizer,(0,1),flag=wx.EXPAND|wx.ALL)
        self.mainsizer.Add(self.settingsSizer,(n,0),flag=wx.EXPAND|wx.ALL)
        n+=1
        self.settingsNotebook=wx.Notebook(self,-1,style=wx.NB_MULTILINE)
        
        font=self.settingsNotebook.GetFont()
        font.SetPointSize(font.GetPointSize()-1)
        self.settingsNotebook.SetFont(font)

        #self.staticLine=wx.StaticLine(self)
        #self.mainsizer.Add(self.staticLine,(2,0),span=(1,1),flag=wx.EXPAND)

        self.buttonSizer=wx.BoxSizer(wx.HORIZONTAL)
        self.buttonPanel.SetSizer(self.buttonSizer)
        self.buttonPanel.SetAutoLayout(1)
        self.mainsizer.Add(self.buttonPanel,(n,0),span=(1,1),flag=wx.EXPAND)
        n+=1
        self.filePath=None
        self.dataUnit=None
        self.settings = None
        self.cancelled=0

        self.createButtonBox()
        self.createOptionsFrame()

        self.SetSizer(self.mainsizer)
        self.SetAutoLayout(True)
        
        self.SetupScrolling()
        wx.FutureCall(500,self.doPreviewCallback)
        
        #messenger.connect(None,"itf_update",self.doPreviewCallback)
        messenger.connect(None,"channel_selected",self.selectItem)
        messenger.connect(None,"switch_datasets",self.onSwitchDatasets)
        messenger.connect(None,"update_settings_gui",self.onUpdateGUI)
        
    def onUpdateGUI(self,*arg):
        """
        Method: onUpdateGUI
        Created: 07.02.2006, KP
        Description: A callback for updating the GUI when settings have been changed
        """         
        self.updateSettings()
        
    def onSwitchDatasets(self,obj,evt,args):
        """
        Method: onSwitchDatasets(obj,args)
        Created: 11.08.2005, KP
        Description: Switch the used source datasets
        """     
        try:
            self.dataUnit.switchSourceDataUnits(args)
        except GUIError,err:
            err.show()
        self.doPreviewCallback()
        
    def createItemToolbar(self):
        """
        Method: createItemToolbar()
        Created: 31.03.2005, KP
        Description: Method to create a toolbar for the window that allows use to select processed channel
        """      
        #self.tb2 = self.CreateToolBar(wx.TB_HORIZONTAL)
        self.toolMgr.clearItemsBar()
        Logging.info("Creating item toolbar",kw="init")
        #self.tb2 = wx.ToolBar(self,-1,style=wx.TB_VERTICAL|wx.TB_TEXT)
        #self.tb2.SetToolBitmapSize((32,32))# this required for non-standard size buttons on MSW
        #self.tb2 = self.toolbar
        n=0
        #self.tb2.AddSeparator()
        self.toolIds=[]
        sourceUnits=self.dataUnit.getSourceDataUnits()
        if len(sourceUnits)==1:
            return
        for i,dataunit in enumerate(sourceUnits):
            #color = dataunit.getColor()
            ctf = dataunit.getColorTransferFunction()
            name = dataunit.getName()
            dc= wx.MemoryDC()
            bmp,pngstr=ImageOperations.vtkImageDataToPreviewBitmap(dataunit,0,None,30,30,getpng=1)
            if self.channelBox:
                self.channelBox.setPreview(i,pngstr)
            dc.SelectObject(bmp)
            dc.BeginDrawing()
            #dc.SetFont(wx.Font(8,wx.SWISS,wx.NORMAL,wx.BOLD))
            #dc.SetTextForeground(wx.Colour(255,255,255))
            #w,h=dc.GetTextExtent(name)
            #d=(32-w)/2.0
            #dy=(32-h)
            #if d<0:d=0
            #dc.DrawText(name,d,dy)
            val=[0,0,0]
            dc.SetBrush(wx.TRANSPARENT_BRUSH)
            if ctf:
                ctf.GetColor(255,val)
    
                r,g,b=val
                r*=255
                g*=255
                b*=255
            else:
                r=255
                g=255
                b=255
            dc.SetPen(wx.Pen(wx.Colour(r,g,b),4))
            dc.DrawRectangle(0,0,32,32)
            dc.EndDrawing()
            #dc.SelectObject(wx.EmptyBitmap(0,0))
            dc.SelectObject(wx.NullBitmap)
	    toolid=wx.NewId()
            self.toolIds.append(toolid)
            self.toolMgr.addItem(name,bmp,toolid,lambda e,x=n,s=self:s.setPreviewedData(e,x))
            self.toolMgr.toggleTool(toolid,1)
            self.dataUnit.setOutputChannel(i,1)
            n=n+1
        if self.channelBox:
            self.channelBox.SetSelection(0)
        return n
        
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
        self.buttonsSizer2.Add(self.previewButton,1,wx.RIGHT|wx.TOP|wx.ALIGN_CENTER,10)
        
        self.processButton=wx.Button(self.buttonPanel,-1,"Process")
        self.buttonsSizer2.Add(self.processButton,1,wx.RIGHT|wx.TOP|wx.ALIGN_CENTER,10)

        self.helpButton=wx.Button(self.buttonPanel,-1,"Help")
        self.helpButton.Bind(wx.EVT_BUTTON,self.onHelp)
        self.buttonsSizer2.Add(self.helpButton,1,wx.RIGHT|wx.TOP|wx.ALIGN_CENTER,10)        
        self.buttonSizer.Add(self.buttonsSizer2)  

    def onHelp(self,evt):
        """
        Method: onHelp
        Created: 03.11.2004, KP
        Description: Shows a help for this task panel
        """
        messenger.send(None,"view_help",self.operationName)
        
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
        

        #self.commonSettingsPanel.SetSizer(self.commonSettingsSizer)
        #self.commonSettingsPanel.SetAutoLayout(1)

#        self.commonSettingsPanel.SetBackgroundColour(self.GetBackgroundColour())
        self.settingsSizer.Add(self.commonSettingsSizer,(0,0),flag=wx.EXPAND|wx.ALL)
        self.settingsSizer.Add(self.settingsNotebook,(1,0),flag=wx.EXPAND|wx.ALL)
        self.Layout()

    def setPreviewedData(self,event,index=-1):
        """
        Method: setPreviewedData
        Created: 22.07.2005, KP
        Description: A callback function for marking channels to be rendered
                     in the preview.
        """
        flag=event.IsChecked()
        self.dataUnit.setOutputChannel(index,flag)
        self.doPreviewCallback(None)
        
    def selectItem(self,obj,event,index=-1):
        """
        Method: selectItem(event)
        Created: 03.11.2004, KP
        Description: A callback function called when a channel is selected in
                     the menu
        """
        Logging.info("Select item %d"%index, kw="dataunit")
        if index==-1:       
            raise "No index given"

        self.settings = self.dataUnit.getSourceDataUnits()[index].getSettings()
        
        #self.preview.setSelectedItem(index)
        
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
        mgr=ProcessingManager(self,self.operationName)
        mgr.setDataUnit(self.dataUnit)
        self.grayOut()

        mgr.ShowModal()
        mgr.Destroy()
        self.grayOut(1)

    def grayOut(self,enable=0):
        """
        Method: grayOut(enable=0)
        Created: 16.11.2004, KP
        Description: Grays out the widget while doing colocalization
        Parameters:
            enable      If the enable parameter is defined, the effect of the
                        function is reversed and the widgets are set to normal
                        state

        """
        self.Enable(enable)

    def doPreviewCallback(self,*args):
        """
        Method: doPreviewCallback()
        Created: 03.11.2004, KP
        Description: A callback for the button "Preview" and other events
                     that wish to update the preview
        """
        Logging.info("Sending preview update event",kw="event")
        messenger.send(None,"data_changed",-1)


    def loadSettingsCallback(self,event):
        """
        Method: loadSettingsCallback()
        Created: 30.11.2004, KP
        Description: A callback to load the settings for this operation from a
                     du file
        """
        wc="Dataset Settings(*.bxd)|*.bxd"
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
        wc="Dataset Settings(*.bxd)|*.bxd"
        dlg=wx.FileDialog(self,"Save dataset settings to file",wildcard=wc,style=wx.SAVE)
        filename=None
        if dlg.ShowModal()==wx.ID_OK:
            filename=dlg.GetPath()
        
        dlg.Destroy()

        if not filename:
            return
        if filename[-3:].lower()!=".bxd":
            filename+=".bxd"

        Logging.info("Saving to ",filename,kw="processing")

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
        messenger.send(None,"current_task",self.operationName)
        
        
        self.dataUnit=dataUnit
        name=dataUnit.getName()
        Logging.info("Name of dataunit is ",name,kw="dataunit")
        #self.taskName.SetValue(name)
        try:
            #self.preview.setDataUnit(dataUnit)
            units=self.dataUnit.getSourceDataUnits()
            
        except GUIError, ex:
            ex.show()
        fileNames=[]
        for unit in units:
            ds=unit.dataSource.getFileName()
            ds=os.path.basename(ds)
            if ds not in fileNames:
                fileNames.append(ds)
        if self.channelBox:
            self.channelBox.setDataUnit(dataUnit)
        
        messenger.send(None,"current_file",", ".join(fileNames))         
        
        self.selectItem(None,None,0)
        # Delay the call, maybe it will make it work on mac
        wx.FutureCall(100,self.createItemToolbar)
#        self.createItemToolbar()