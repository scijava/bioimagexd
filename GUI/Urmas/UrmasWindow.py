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
        ico=reduce(os.path.join,["Icons","Selli.ico"])
        self.icon = wx.Icon(ico,wx.BITMAP_TYPE_ICO)
        self.SetIcon(self.icon)

        self.CreateStatusBar()
        self.SetStatusText("Initializing project...")

        self.createMenu()
        
        self.control = UrmasControl.UrmasControl(self)

        self.Bind(wx.EVT_CLOSE,self.closeWindowCallback)

        self.sizer=wx.BoxSizer(wx.VERTICAL)
        self.palette = UrmasPalette.UrmasPalette(self,self.control)
        self.sizer.Add(self.palette,1,flag=wx.EXPAND)

        self.timelinePanel=TimelinePanel.TimelinePanel(self,self.control,size=(1024,500))
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
        self.trackMenu = wx.Menu()
        self.renderMenu=wx.Menu()
        self.cameraMenu = wx.Menu()
         # and add them as sub menus to the menubar
        self.menu.Append(self.fileMenu,"&File")
        self.menu.Append(self.settingsMenu,"&Settings")
        self.menu.Append(self.trackMenu,"&Track")
        self.menu.Append(self.renderMenu,"&Rendering")
        self.menu.Append(self.cameraMenu,"&Camera")
        self.menu.Append(self.helpMenu,"&Help")
      
        self.ID_PREFERENCES = wx.NewId()
        self.settingsMenu.Append(self.ID_PREFERENCES,"&Preferences...")
        wx.EVT_MENU(self,self.ID_PREFERENCES,self.onMenuPreferences)
        
        self.ID_OPEN=wx.NewId()
        self.ID_SAVE=wx.NewId()
        self.fileMenu.Append(self.ID_OPEN,"Open project...","Open a BioImageXD Rendering Project")
        self.fileMenu.Append(self.ID_SAVE,"Save project as...","Save current BioImageXD Rendering Project")
        wx.EVT_MENU(self,self.ID_OPEN,self.onMenuOpenProject)
        wx.EVT_MENU(self,self.ID_SAVE,self.onMenuSaveProject)
        
        self.ID_ADD_SPLINE=wx.NewId()
        self.ID_ADD_TIMEPOINT=wx.NewId()
        self.addTrackMenu=wx.Menu()
        self.addTrackMenu.Append(self.ID_ADD_TIMEPOINT,"Timepoint Track","Add a timepoint track to the timeline")
        self.addTrackMenu.Append(self.ID_ADD_SPLINE,"Camera Path Track","Add a camera path track to the timeline")
        self.addTrackMenu.Enable(self.ID_ADD_SPLINE,0)
        wx.EVT_MENU(self,self.ID_ADD_SPLINE,self.onMenuAddSplineTrack)
        wx.EVT_MENU(self,self.ID_ADD_TIMEPOINT,self.onMenuAddTimepointTrack)
        self.ID_ADD_TRACK=wx.NewId()
        self.trackMenu.AppendMenu(self.ID_ADD_TRACK,"&Add Track",self.addTrackMenu)
        self.trackMenu.AppendSeparator()
        
        self.ID_FIT_TRACK = wx.NewId()
        self.ID_MIN_TRACK = wx.NewId()
        self.ID_SET_TRACK = wx.NewId()
        self.trackMenu.Append(self.ID_FIT_TRACK,"Expand to maximum","Expand the track to encompass the whole timeline")
        self.trackMenu.Append(self.ID_MIN_TRACK,"Shrink to minimum","Shrink the track to as small as possible")
        self.trackMenu.Append(self.ID_SET_TRACK,"Set item size","Set each item on this track to be of given size")
        
        wx.EVT_MENU(self,self.ID_FIT_TRACK,self.onMaxTrack)
        wx.EVT_MENU(self,self.ID_MIN_TRACK,self.onMinTrack)
        wx.EVT_MENU(self,self.ID_SET_TRACK,self.onSetTrack)
        
        self.ID_ANIMATE = wx.NewId()
        self.renderMenu.AppendCheckItem(self.ID_ANIMATE,"&Animated rendering","Select whether to produce animation or still images")
        wx.EVT_MENU(self,self.ID_ANIMATE,self.onMenuAnimate)
        
        self.renderMenu.AppendSeparator()
        
        self.ID_RENDER_PREVIEW=wx.NewId()
        self.renderMenu.Append(self.ID_RENDER_PREVIEW,"Rendering &Preview","Preview rendering")
        wx.EVT_MENU(self,self.ID_RENDER_PREVIEW,self.onMenuRender)

        self.ID_MAYAVI=wx.NewId()
        self.renderMenu.Append(self.ID_MAYAVI,"&Start Renderer Program","Start Mayavi for rendering")
        wx.EVT_MENU(self,self.ID_MAYAVI,self.onMenuMayavi)

        self.ID_RENDER=wx.NewId()
        self.renderMenu.Append(self.ID_RENDER,"&Render project","Render this project")
        wx.EVT_MENU(self,self.ID_RENDER,self.onMenuRender)
    
        #self.renderMenu.Enable(self.ID_RENDER,0)

        self.ID_SPLINE_CLOSED = wx.NewId()
        self.cameraMenu.AppendCheckItem(self.ID_SPLINE_CLOSED,"&Closed Path","Set the camera path to open / closed.")
        wx.EVT_MENU(self,self.ID_SPLINE_CLOSED,self.onMenuClosedSpline)

        self.ID_SPLINE_SET_BEGIN = wx.NewId()
        self.cameraMenu.Append(self.ID_SPLINE_SET_BEGIN,"&Begin at the end of previous path","Set this camera path to begin where the previous path ends")
        wx.EVT_MENU(self,self.ID_SPLINE_SET_BEGIN,self.onMenuSetBegin)
        
        self.ID_SPLINE_SET_END = wx.NewId()
        self.cameraMenu.Append(self.ID_SPLINE_SET_END,"&End at the beginning of next path","Set this camera path to end where the next path starts")
        wx.EVT_MENU(self,self.ID_SPLINE_SET_END,self.onMenuSetEnd)
            
        self.cameraMenu.Enable(self.ID_SPLINE_SET_BEGIN,0)
        self.cameraMenu.Enable(self.ID_SPLINE_SET_END,0)

    def updateMenus(self):
        """
        Method: updateMenus()
        Created: 18.04.2005, KP
        Description: A method to update the state of menu items
        """
        spltracks=len(self.control.timeline.getSplineTracks())
        flag=(spltracks>=2)
        print "updateMenus()",spltracks
        self.cameraMenu.Enable(self.ID_SPLINE_SET_BEGIN,flag)
        self.cameraMenu.Enable(self.ID_SPLINE_SET_END,flag)
        
    def onMenuMayavi(self,event):
        """
        Method: onMenuMayavi
        Created: 20.04.2005, KP
        Description: Start mayavi for rendering
        """
        self.renderMenu.Enable(self.ID_RENDER,1)
        self.control.startMayavi()

    def onMenuRender(self,event):
        """
        Method: onMenuRender()
        Created: 19.04.2005, KP
        Description: Render this project
        """
        if event.GetId() == self.ID_RENDER:
            video=VideoGeneration.VideoGeneration(self,self.control)
            video.ShowModal()
            
            #self.control.renderProject(0)
        else:
            self.control.renderProject(1)
        
    def onMinTrack(self,evt):
        """
        Method: onMinTrack
        Created: 19.04.2005, KP
        Description: Callback function for menu item minimize track
        """
        active = self.control.getSelectedTrack()
        active.setToSize()

    def onSetTrack(self,evt):
        """
        Method: onMinTrack
        Created: 19.04.2005, KP
        Description: Callback function for menu item minimize track
        """
        dlg = wx.TextEntryDialog(self,"Set duration of each item (seconds):","Set item duration")
        dlg.SetValue("5")
        if dlg.ShowModal()==wx.ID_OK:
            try:
                val=int(dlg.GetValue())
            except:
                return
        size=val*self.control.getPixelsPerSecond()
        print "Setting to size ",size,"(",val,"seconds)"
        active = self.control.getSelectedTrack()
        active.setToSize(size)

    def onMaxTrack(self,evt):
        """
        Method: onMinTrack
        Created: 19.04.2005, KP
        Description: Callback function for menu item minimize track
        """
        active = self.control.getSelectedTrack()
        active.expandToMax()

    def onMenuSetBegin(self,evt):
        """
        Method: onMenuSetBegin
        Created: 18.04.2005, KP
        Description: Callback function for menu item begin at end of previous
        """
        active = self.control.getSelectedTrack()
        self.control.timeline.setBeginningToPrevious(active)
        
    def onMenuSetEnd(self,evt):
        """
        Method: onMenuSetEnd
        Created: 18.04.2005, KP
        Description: Callback function for menu item end at beginning of next
        """
        active = self.control.getSelectedTrack()
        self.control.timeline.setEndToNext(active)
        
    def onMenuClosedSpline(self,evt):
        """
        Method: onMenuClosedSpline
        Created: 14.04.2005, KP
        Description: Callback function for menu item camera path is closed
        """
        track=self.control.getSelectedTrack()
        if "setClosed" in dir(track):
            track.setClosed(evt.IsChecked())
        
    def onMenuAnimate(self,evt):
        """
        Method: onMenuAnimate
        Created: 14.04.2005, KP
        Description: Callback function for menu item animated rendering
        """
        flag=evt.IsChecked()
        self.control.setAnimationMode(flag)
        self.addTrackMenu.Enable(self.ID_ADD_SPLINE,flag)
        

    def onMenuAddSplineTrack(self,evt):
        """
        Method: onMenuAddSplineTrack
        Created: 13.04.2005, KP
        Description: Callback function for adding camera path track
        """
        self.control.timeline.addSplinepointTrack("")
        
    def onMenuAddTimepointTrack(self,evt):
        """
        Method: onMenuAddTimepointTrack
        Created: 13.04.2005, KP
        Description: Callback function for adding timepoint track
        """
        self.control.timeline.addTrack("")
        

    def onMenuPreferences(self,evt):
        """
        Method: onMenuPreferences()
        Created: 09.02.2005, KP
        Description: Callback function for menu item "Preferences"
        """
        self.settingswindow=SettingsWindow.SettingsWindow(self)
        self.settingswindow.ShowModal()

    def onMenuOpenProject(self,event):
        """
        Method: onMenuOpenProject(self,event)
        Created: 06.04.2005, KP
        Description: Callback function for opening a project
        """
        wc="Rendering Project (*.rxd)|*.rxd"
        name=Dialogs.askOpenFileName(self,"Open Rendering Project",wc,0)
        if name:
            self.control.readFromDisk(name[0])
        
    def onMenuSaveProject(self,event):
        """
        Method: onMenuSaveProject(self,event)
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
