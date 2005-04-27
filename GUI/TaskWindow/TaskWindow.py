#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: TaskWindow.py
 Project: Selli
 Created: 23.11.2004
 Creator: KP
 Description:

 A Tkinter Toplevel window that is a base class for all the windows that are 
 used to control the settings for the various modules. Expects to be handed a 
 CombinedDataUnit() containing the datasets that the module processes
 Uses the PreviewFrame for previewing.

 Modified:
    	   23.11.2004 KP - Created from ColocalizationWindow

 Selli includes the following perso ns:
 JH - Juha Hyytiäinen, juhyytia@st.jyu.fi
 JM - Jaakko Mäntymaa, jahemant@cc.jyu.fi
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 JV - Jukka Varsaluoma,varsa@st.jyu.fi

 Copyright (c) 2004 Selli Project.
"""
__author__ = "Selli Project <http://sovellusprojektit.it.jyu.fi/selli/>"
__version__ = "$Revision: 1.21 $"
__date__ = "$Date: 2005/01/13 14:36:20 $"

import wx

import os.path

from DataUnit import *
from PreviewFrame import *
from Logging import *
from ProcessingManager import *

import Dialogs
import sys
import Colocalization
import ColorMerging
import ImageOperations
import ColorTransferEditor

def showTaskWindow(windowclass,combinedUnit,mainwin):
    """
    Function: showTaskWindow(combinedUnit,mainwin)
    Created: 15.11.2004, KP
    Description: A function that displays the window and
                 waits for the user to do what he wishes. After
                 the user presses ok or cancel , the results
                 are returned to the caller. Mainly for use in
                 modules  the classes of which inherit the TaskWindow
    """
#    mainwin.withdraw()
    window=windowclass(mainwin)
    window.setCombinedDataUnit(combinedUnit)
    window.Show()
    #window.ShowModal()
    res=window.getResult()
    return res



class TaskWindow(wx.Frame):
    """
    Class: TaskWindow
    Created: 23.11.2004, KP
    Description: A baseclass for a window for controlling the settings of the 
                 various task module
    """
    def __init__(self,root):
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
        wx.Frame.__init__(self,root,-1,"Task Window",style=wx.DEFAULT_FRAME_STYLE, #|wx.NO_FULL_REPAINT_ON_RESIZE,
        size=(1024,768))
        self.panel=wx.Panel(self,-1)
        self.buttonPanel = wx.Panel(self.panel,-1)
        self.root=root
        self.preview=None
        # Associate this window with the parent window (root)
        ico=reduce(os.path.join,["Icons","Selli.ico"])
        self.icon = wx.Icon(ico,wx.BITMAP_TYPE_ICO)
        self.SetIcon(self.icon)

        self.Bind(wx.EVT_CLOSE,self.closeWindowCallback)
        self.mainsizer=wx.GridBagSizer()


        self.settingsSizer=wx.GridBagSizer()
        self.mainsizer.Add(self.settingsSizer,(0,1),flag=wx.EXPAND|wx.ALL)

        self.settingsNotebook=wx.Notebook(self.panel,-1)

        self.staticLine=wx.StaticLine(self.panel)
        self.mainsizer.Add(self.staticLine,(2,0),span=(1,2),flag=wx.EXPAND)

        self.buttonSizer=wx.BoxSizer(wx.HORIZONTAL)
        self.buttonPanel.SetSizer(self.buttonSizer)
        self.buttonPanel.SetAutoLayout(1)
        self.mainsizer.Add(self.buttonPanel,(3,0),span=(1,2),flag=wx.EXPAND)

        self.previewSizer=wx.GridBagSizer()
        self.mainsizer.Add(self.previewSizer,(0,0),flag=wx.EXPAND|wx.ALL)

        # Preview has to be generated here
        self.preview=IntegratedPreview(self.panel,self)
        self.Bind(EVT_ZSLICE_CHANGED,self.updateZSlice,id=self.preview.GetId())
        self.Bind(EVT_TIMEPOINT_CHANGED,self.updateTimepoint,id=self.preview.GetId())
        #self.preview = ColorMergingPreview(self)
        self.previewSizer.Add(self.preview,(0,1),flag=wx.EXPAND|wx.ALL)
    
    
        self.filePath=None
        self.dataUnit=None
        self.settings = None
        self.cancelled=0


        # Make the column containing the settings widgets at least 200 pixels
        # wide

        self.createButtonBox()
        self.createOptionsFrame()

        self.panel.SetSizer(self.mainsizer)
        self.panel.SetAutoLayout(True)
        self.mainsizer.Fit(self.panel)
        self.mainsizer.SetSizeHints(self.panel)

        self.Bind(wx.EVT_SIZE,self.OnSize)

    def createToolBar(self):
        """
        Method: createToolBar()
        Created: 19.03.2005, KP
        Description: Method to create a toolbar for the window
        """                
        self.tb = self.CreateToolBar(wx.TB_HORIZONTAL)#|wx.NO_BORDER|wx.TB_FLAT|wx.TB_TEXT)
        ID_CAPTURE=wx.NewId()
        ID_ZOOM_OUT=wx.NewId()
        ID_ZOOM_IN=wx.NewId()
        ID_ZOOM_TO_FIT=wx.NewId()
        ID_ZOOM_OBJECT=wx.NewId()
        self.tb.AddSimpleTool(ID_CAPTURE,wx.Image(os.path.join("Icons","camera.gif"),wx.BITMAP_TYPE_GIF).ConvertToBitmap(),"Capture slice","Capture the current optical slice")
        self.tb.AddSimpleTool(ID_ZOOM_OUT,wx.Image(os.path.join("Icons","zoom-out.gif"),wx.BITMAP_TYPE_GIF).ConvertToBitmap(),"Zoom out","Zoom out on the optical slice")
        #EVT_TOOL(self,ID_OPEN,self.menuOpen)
        
        self.zoomCombo=wx.ComboBox(self.tb,-1,"100%",choices=["12.5%","25%","33.33%","50%","66.67%","75%","100%","125%","150%","200%","300%","400%","600%","800%"],size=(100,-1),style=wx.CB_DROPDOWN)
        self.zoomCombo.SetSelection(6)
        self.tb.AddControl(self.zoomCombo)
        self.preview.setZoomCombobox(self.zoomCombo)
        self.tb.AddSimpleTool(ID_ZOOM_IN,wx.Image(os.path.join("Icons","zoom-in.gif"),wx.BITMAP_TYPE_GIF).ConvertToBitmap(),"Zoom in","Zoom in on the slice")
        self.tb.AddSimpleTool(ID_ZOOM_TO_FIT,wx.Image(os.path.join("Icons","zoom-to-fit.gif"),wx.BITMAP_TYPE_GIF).ConvertToBitmap(),"Zoom to Fit","Zoom the slice so that it fits in the window")
        self.tb.AddSimpleTool(ID_ZOOM_OBJECT,wx.Image(os.path.join("Icons","zoom-object.gif"),wx.BITMAP_TYPE_GIF).ConvertToBitmap(),"Zoom object","Zoom user selected portion of the slice")

        wx.EVT_TOOL(self,ID_CAPTURE,self.preview.captureSlice)
        wx.EVT_TOOL(self,ID_ZOOM_IN,self.preview.zoomIn)
        wx.EVT_TOOL(self,ID_ZOOM_OUT,self.preview.zoomOut)
        wx.EVT_TOOL(self,ID_ZOOM_TO_FIT,self.preview.zoomToFit)
        wx.EVT_TOOL(self,ID_ZOOM_OBJECT,self.preview.zoomObject)
        self.zoomCombo.Bind(wx.EVT_COMBOBOX,self.preview.zoomToComboSelection)

    def createItemToolbar(self):
        """
        Method: createItemToolbar()
        Created: 31.03.2005, KP
        Description: Method to create a toolbar for the window that allows use to select processed channel
        """      
        #self.tb2 = self.CreateToolBar(wx.TB_HORIZONTAL)
        print "Creating item toolbar"
        self.tb2 = wx.ToolBar(self,-1,style=wx.TB_VERTICAL|wx.TB_TEXT)
        self.tb2.SetToolBitmapSize((64,64))# this required for non-standard size buttons on MSW
        n=0
        print "FOOoo\n\n\n\n\n"
        for dataunit in self.dataUnit.getSourceDataUnits():
            #color = dataunit.getColor()
            ctf = dataunit.getColorTransferFunction()
            name = dataunit.getName()
            print "Adding item ",name
            dc= wx.MemoryDC()
            bmp=ImageOperations.vtkImageDataToPreviewBitmap(dataunit.getTimePoint(0),ctf,64,64)
            dc.SelectObject(bmp)
            dc.BeginDrawing()
            dc.SetFont(wx.Font(9,wx.SWISS,wx.NORMAL,wx.BOLD))
            dc.SetTextForeground(wx.Colour(255,255,255))
            w,h=dc.GetTextExtent(name)
            d=(64-w)/2.0
            dy=(62-h)
            if d<0:d=0
            dc.DrawText(name,d,dy)
            dc.EndDrawing()
            dc.SelectObject(wx.EmptyBitmap(0,0))
            toolid=wx.NewId()
            self.tb2.AddRadioTool(toolid,bmp,shortHelp=name)
            self.Bind(wx.EVT_TOOL,lambda e,x=n,s=self:s.selectItem(e,x),id=toolid)
            n=n+1
        self.tb2.Realize()
        #self.mainsizer.Add(self.tb2,(0,4))
        self.previewSizer.Add(self.tb2,(0,0))
        
    def OnSize(self,event):
        """
        Method: OnSize(event)
        Created: n/a, KP
        Description: Method called when the window size changes
        """        
        self.SetSize(event.GetSize())
        self.panel.SetSize(event.GetSize())
        self.panel.Layout()
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
        
        self.buttonsSizer1=wx.BoxSizer(wx.HORIZONTAL)
        
        self.savesettings=wx.Button(self.buttonPanel,-1,"Save settings")
        self.savesettings.Bind(wx.EVT_BUTTON,self.saveSettingsCallback)
        self.buttonsSizer1.Add(self.savesettings,flag=wx.ALIGN_LEFT)

        self.loadsettings=wx.Button(self.buttonPanel,-1,"Load settings")
        self.loadsettings.Bind(wx.EVT_BUTTON,self.loadSettingsCallback)
        self.buttonsSizer1.Add(self.loadsettings,flag=wx.ALIGN_LEFT)
        self.buttonsSizer1.AddSizer((100,-1))
        self.buttonSizer.Add(self.buttonsSizer1)
        
        self.buttonsSizer2=wx.BoxSizer(wx.HORIZONTAL)
        
        self.processButton=wx.Button(self.buttonPanel,-1,"Process dataset series")
        #self.processDatasetButton.Bind(EVT_BUTTON,self.doProcessingCallback)
        self.buttonsSizer2.Add(self.processButton)

        self.previewButton=wx.Button(self.buttonPanel,-1,"Preview")
        self.previewButton.Bind(wx.EVT_BUTTON,self.doPreviewCallback)
        self.buttonsSizer2.Add(self.previewButton)        

        
        self.closeButton=wx.Button(self.buttonPanel,-1,"Close")
        self.closeButton.Bind(wx.EVT_BUTTON,self.closeWindowCallback)
        self.buttonsSizer2.Add(self.closeButton)
        
        self.buttonSizer.Add(self.buttonsSizer2)    

        
    def createOptionsFrame(self):
        """
        Method: createOptionsFrame()
        Created: 03.11.2004, KP
        Description: Creates a frame that contains the various widgets
                     used to control the colocalization settings
        """

        self.commonSettingsPanel=wx.Panel(self.settingsNotebook,-1)
        self.settingsNotebook.AddPage(self.commonSettingsPanel,"General")
#        self.commonSettingsPanel.SetBackgroundColour(wx.Colour(255,0,0))
        self.commonSettingsSizer=wx.GridBagSizer()

        self.namesizer=wx.BoxSizer(wx.VERTICAL)
        self.commonSettingsSizer.Add(self.namesizer,(0,0))

        self.taskNameLbl=wx.StaticText(self.commonSettingsPanel,-1,"Dataunit Name:")
        self.taskName=wx.TextCtrl(self.commonSettingsPanel,-1,size=(250,-1))
        self.namesizer.Add(self.taskNameLbl)
        self.namesizer.Add(self.taskName)

        self.commonSettingsPanel.SetSizer(self.commonSettingsSizer)
        self.commonSettingsPanel.SetAutoLayout(1)


#        self.commonSettingsPanel.SetBackgroundColour(self.panel.GetBackgroundColour())
#        self.taskNameLbl.SetBackgroundColour(self.panel.GetBackgroundColour())
        self.settingsSizer.Add(self.settingsNotebook,(0,0))#,flag=wx.EXPAND|wx.ALL)


    def selectItem(self,event,index=-1):
        """
        Method: selectItem(event)
        Created: 03.11.2004, KP
        Description: A callback function called when a channel is selected in
                     the menu
        """
        if index==-1:
            raise "No index given"
            index=self.itemMenu.GetSelection()
        print "Selecting item %d"%index
        #name=self.itemMenu.GetString(index)
        #print "Now configuring item",name
        #print "self.Dataunit.getSetting()=",self.dataUnit.getSettings()
        self.settings = self.dataUnit.getSourceDataUnits()[index].getSettings()
        self.preview.setSelectedItem(index)
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
        if self.preview:
            self.preview.updatePreview()

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
            self.preview.setDataUnit(dataUnit)
            units=self.dataUnit.getSourceDataUnits()
            
        except GUIError, ex:
            ex.show()
        #names=[i.getName() for i in units]
        #for name in names:
        #        self.itemMenu.Append(name)
        self.selectItem(None,0)
        #self.itemMenu.SetSelection(0)
        self.createItemToolbar()
