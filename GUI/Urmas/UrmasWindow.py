#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

"""
 Unit: UrmasWindow
 Project: BioImageXD
 Created: 10.02.2005
 Creator: KP
 Description:

 URM/AS - The Unified Rendering Manager / Animator for Selli
 
 This is a timeline based GUI for controlling the rendering of datasets. The GUI allows users
 to specify a path for the camera to follow (using Heikki Uuksulainen's MayaVi animator code)
 and also allows them to produce videos of the rendering using ffmpeg.
 
 This is the wx.Dialog based window that contains the Urmas.
 
 Modified: 10.02.2005 KP - Created the module
 
 BioImageXD includes the following persons:
 
 DW - Dan White, dan@chalkie.org.uk
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 PK - Pasi Kankaanpää, ppkank@bytl.jyu.fi
 
 Copyright (c) 2005 BioImageXD Project.
"""
__author__ = "BioImageXD Project"
__version__ = "$Revision: 1.22 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import wx
import wx.wizard
from Timeline import *
import TimelinePanel
import UrmasTimepointSelection
import RenderingInterface
import UrmasControl
import VideoGeneration

import Dialogs

import UrmasPalette
        
class UrmasWindow(wx.Frame):
    """
    Class: UrmasWindow
    Created: 10.02.2005, KP
    Description: A window for controlling the rendering/animation/movie generation.
                 The window has a notebook with different pages for rendering and
                 animation modes, and a page for configuring the movie generation.
    """
    def __init__(self,parent):
        wx.Frame.__init__(self,parent,-1,"Rendering Manager / Animator",size=(1024,768))
        self.status=wx.ID_OK
        ico=reduce(os.path.join,["..","Icons","Selli.ico"])
        self.icon = wx.Icon(ico,wx.BITMAP_TYPE_ICO)
        self.SetIcon(self.icon)
        self.createMenu()
        self.control = UrmasControl.UrmasControl(self)

        self.Bind(wx.EVT_CLOSE,self.closeWindowCallback)

        self.sizer=wx.BoxSizer(wx.VERTICAL)
        self.palette = UrmasPalette.UrmasPalette(self)
        self.sizer.Add(self.palette,1)

        self.timelinePanel=TimelinePanel.TimelinePanel(self,self.control)
        self.control.setTimelinePanel(self.timelinePanel)
        
        self.sizer.Add(self.timelinePanel)

        
        
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)



        
    def createMenu(self):
        """
        Method: createMenu()
        Created: 06.04.2005, KP
        Description: Creates a menu for the window
        """
        # This is the menubar object that holds all the menus
        self.menu = wx.MenuBar()
        self.SetMenuBar(self.menu)
        
        # We create the menu objects
        self.fileMenu=wx.Menu()
        self.helpMenu=wx.Menu()
        
        self.settingsMenu=wx.Menu()

         # and add them as sub menus to the menubar
        self.menu.Append(self.fileMenu,"&File")
        self.menu.Append(self.settingsMenu,"&Settings")
        self.menu.Append(self.helpMenu,"&Help")
      
        self.ID_PREFERENCES = wx.NewId()
        self.settingsMenu.Append(self.ID_PREFERENCES,"&Preferences...")
        wx.EVT_MENU(self,self.ID_PREFERENCES,self.menuPreferences)
        
        self.ID_OPEN=wx.NewId()
        self.ID_SAVE=wx.NewId()
        self.fileMenu.Append(self.ID_OPEN,"Open project...")
        self.fileMenu.Append(self.ID_SAVE,"Save project as...")
        wx.EVT_MENU(self,self.ID_OPEN,self.menuOpenProject)
        wx.EVT_MENU(self,self.ID_SAVE,self.menuSaveProject)
        

        #self.FitToPage(self.timepointSelection)

    def menuPreferences(self,evt):
        """
        Method: menuPreferences()
        Created: 09.02.2005, KP
        Description: Callback function for menu item "Preferences"
        """
        self.settingswindow=SettingsWindow.SettingsWindow(self)
        self.settingswindow.ShowModal()

    def menuOpenProject(self,event):
        """
        Method: menuOpenProject(self,event)
        Created: 06.04.2005, KP
        Description: Callback function for opening a project
        """
        wc="Rendering Project (*.rxd)|*.rxd"
        name=Dialogs.askOpenFileName(self,"Open Rendering Project",wc)
        if name:
            self.control.readFromDisk(name[0])
        
    def menuSaveProject(self,event):
        """
        Method: menuSaveProject(self,event)
        Created: 06.04.2005, KP
        Description: Callback function for saving a project
        """
        wc="Rendering Project (*.rxd)|*.rxd"
        dlg=wx.FileDialog(self,"Save Rendering Project as...",defaultFile="project.rxd",wildcard=wc,style=wx.SAVE)
        if dlg.ShowModal()==wx.ID_OK:
            name=dlg.GetPath()
        if name:
            self.control.writeToDisk(name)
        
    def startWizard(self):
        """
        Method: startWizard()
        Created: 14.03.2005, KP
        Description: Start this wizard
        """              
        #self.RunWizard(self.timepointSelection)
        
    
    def onSize(self,evt):
        """
        Method: onSize()
        Created: 22.2.2005, KP
        Description: Event handler used to resize the window
        """        
        x,y=evt.GetSize()
        if 1 or self.animatorOn == False:
            self.notebook.SetSize((x,y))
        else:
            self.notebook.SetSize((x/2,y))
            self.animator.SetSize((x/2,y))
        
    
    def showAnimator(self,flag):
        """
        Method: showAnimator(flag)
        Created: 22.2.2005, KP
        Description: Method used to either show or hide the animator
        """    
        if flag == True:
            self.animator.Show(1)
            self.animatorOn=1
            w,h=self.GetSize()
            wa,ha=self.animator.GetSize()
            self.SetSize((w,h+ha))
            self.splitter.SplitHorizontally(self.notebook,self.animator,h)
        else:
            self.animatorOn=0
            w,h=self.GetSize()
            wa,ha=self.animator.GetSize()
            self.SetSize((w,h-ha))
            self.splitter.Unsplit(self.animator)
            

    def setDataUnit(self,dataUnit):
        """
        Method: setDataUnit(dataUnit)
        Created: 10.2.2005, KP
        Description: Method used to set the dataunit we're processing
        """
        #self.timepointSelection.setDataUnit(dataUnit)
        #self.timelinePanel.setDataUnit(dataUnit)
        self.control.setDataUnit(dataUnit)
        
    def closeWindowCallback(self,event):
        """
        Method: closeWindowCallback
        Created: 10.2.2005, KP
        Description: A callback that is used to close this window
        """
        #self.EndModal(self.status)
        self.Destroy()
