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
 JH - Juha Hyyti�inen, juhyytia@st.jyu.fi
 JM - Jaakko M�ntymaa, jahemant@cc.jyu.fi
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
    Created: 23.11.2004
    Creator: KP
    Description: A baseclass for a window for controlling the settings of the 
                 various task module
    """
    def __init__(self,root):
        """
        Method: __init__(root,title)
        Created: 03.11.2004
        Creator: KP
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

        self.Bind(EVT_CLOSE,self.closeWindowCallback)
        self.mainsizer=wx.GridBagSizer()

        self.previewSizer=wx.GridBagSizer()
        self.mainsizer.Add(self.previewSizer,(0,0),flag=wx.EXPAND|wx.ALL)

        self.settingsSizer=wx.GridBagSizer()
        self.mainsizer.Add(self.settingsSizer,(0,1),flag=wx.EXPAND|wx.ALL)

        self.settingsNotebook=wx.Notebook(self.panel,-1)

#        self.infoSizer=wx.GridBagSizer()
#        self.mainsizer.Add(self.infoSizer,(1,0),flag=wx.EXPAND|wx.ALL)

#        self.staticLine=wx.StaticLine(self.panel)
#        self.mainsizer.Add(self.staticLine,(2,0),span=(1,2),flag=wx.EXPAND)

        self.buttonSizer=wx.BoxSizer(wx.HORIZONTAL)
        self.buttonPanel.SetSizer(self.buttonSizer)
        self.buttonPanel.SetAutoLayout(1)
        self.mainsizer.Add(self.buttonPanel,(2,0),span=(1,2),flag=wx.EXPAND)

        self.filePath=None
        self.dataUnit=None
        self.configSetting=None
        self.cancelled=0



        # Make the column containing the settings widgets at least 200 pixels
        # wide

        self.createChannelMenu()
        self.createButtonBox()
        self.createOptionsFrame()

        self.panel.SetSizer(self.mainsizer)
        self.panel.SetAutoLayout(True)
        self.mainsizer.Fit(self.panel)
        self.mainsizer.SetSizeHints(self.panel)

        self.Bind(wx.EVT_SIZE,self.OnSize)

    def OnSize(self,event):
        self.SetSize(event.GetSize())
        self.panel.SetSize(event.GetSize())
        self.panel.Layout()
        self.Layout()
        self.buttonPanel.Layout()



    def getResult(self):
        """
        Method: getResult()
        Created: 15.11.2004
        Creator: KP
        Description: Method to get the results of this colocalization window.
                     If cancel was pressed, returns None, otherwise returns the
                     new dataunit
        """
        if self.cancelled:
            return None,None
        return self.dataUnit,self.filePath

    def createButtonBox(self):
        
        self.buttonsSizer1=wx.BoxSizer(wx.HORIZONTAL)
        
        self.savesettings=wx.Button(self.buttonPanel,-1,"Save settings")
        self.savesettings.Bind(EVT_BUTTON,self.saveSettingsCallback)
        self.buttonsSizer1.Add(self.savesettings,flag=wx.ALIGN_LEFT)

        self.loadsettings=wx.Button(self.buttonPanel,-1,"Load settings")
        self.loadsettings.Bind(EVT_BUTTON,self.loadSettingsCallback)
        self.buttonsSizer1.Add(self.loadsettings,flag=wx.ALIGN_LEFT)
        self.buttonsSizer1.AddSizer((100,-1))
        self.buttonSizer.Add(self.buttonsSizer1)
        
        self.buttonsSizer2=wx.BoxSizer(wx.HORIZONTAL)
        
        self.processButton=wx.Button(self.buttonPanel,-1,"Process dataset series")
        #self.processDatasetButton.Bind(EVT_BUTTON,self.doProcessingCallback)
        self.buttonsSizer2.Add(self.processButton)

        self.previewButton=wx.Button(self.panel,-1,"Preview")
        self.previewButton.Bind(EVT_BUTTON,self.doPreviewCallback)
        self.buttonsSizer2.Add(self.previewButton)        

        
        self.closeButton=wx.Button(self.buttonPanel,-1,"Close")
        self.closeButton.Bind(EVT_BUTTON,self.closeWindowCallback)
        self.buttonsSizer2.Add(self.closeButton)
        
        self.buttonSizer.Add(self.buttonsSizer2)    

    def createChannelMenu(self):
        """
        Method: createChannelMenu()
        Created: 03.11.2004, KP
        Description: Creates a menu that displays the names of the processed
                     channels
        """
        self.choicePanel=wx.Panel(self.panel,-1)
        self.menusizer=wx.BoxSizer(wx.VERTICAL)
        self.channelsLbl=wx.StaticText(self.choicePanel,-1,"Items:")
        self.itemMenu = wx.Choice(self.choicePanel,-1)
        self.itemMenu.Bind(wx.EVT_CHOICE,self.selectItem)

        self.menusizer.Add(self.channelsLbl)
        self.menusizer.Add(self.itemMenu)

        self.choicePanel.SetSizer(self.menusizer)
        self.choicePanel.SetAutoLayout(1)
        self.menusizer.Fit(self.choicePanel)
        self.settingsSizer.Add(self.choicePanel,(0,0),span=(1,2),flag=wx.EXPAND|wx.ALL)

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
        self.settingsSizer.Add(self.settingsNotebook,(1,0))#,flag=wx.EXPAND|wx.ALL)


    def setColorCallback(self):
        """
        Method: setColorCallback(self)
        Created: 03.11.2004
        Creator: KP
        Description: A callback function called when the button to configure
                     the channel color is pressed
        """
        defaultColor = (0,0,0)
        if self.dataUnit:
            defaultColor = self.dataUnit.getColor()
        color=Dialogs.askcolor(title="Select color for the channel",
                                      initialcolor=defaultColor)

    	if color[0]:
            r,g,b=color[0]
            self.setColor(r,g,b)        

    def selectItem(self,event,index=-1):
        """
        Method: selectItem(event)
        Created: 03.11.2004, KP
        Description: A callback function called when a channel is selected in
                     the menu
        """
        if index==-1:
            index=self.itemMenu.GetSelection()
        name=self.itemMenu.GetString(index)
        print "Now configuring item",name
        self.configSetting=self.dataUnit.getSetting(name)
        self.updateSettings()



    def updateSettings(self):
        """
        Method: updateSettings()
        Created: 03.11.2004, KP
        Description: A method used to set the GUI widgets to their proper values
                     based on the selected channel, the settings of which are
                     stored in the instance variable self.configSetting
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
        if self.preview:
            self.preview.closePreview()
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
        Created: 03.11.2004
        Creator: KP
        Description: A callback for the button "Preview" and other events
                     that wish to update the preview
        """
        if self.preview:
            self.preview.updatePreview()

    def loadSettingsCallback(self):
        """
        Method: loadSettingsCallback()
        Created: 30.11.2004
        Creator: KP
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


    def saveSettingsCallback(self):
        """
        Method: saveSettingsCallback()
        Created: 30.11.2004
        Creator: KP
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
        names=[i.getName() for i in units]
        for name in names:
                self.itemMenu.Append(name)
        self.selectItem(None,0)
        self.itemMenu.SetSelection(0)
