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
t.
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

from GUI import MenuManager

class UrmasWindow(wx.SashLayoutWindow):
    """
    Class: UrmasWindow
    Created: 10.02.2005, KP
    Description: A window for controlling the rendering/animation/movie generation.
                 The window has a notebook with different pages for rendering and
                 animation modes, and a page for configuring the movie generation.
    """
    def __init__(self,parent,menumanager,taskwin,visualizer):
        #wx.Frame.__init__(self,parent,-1,"Rendering Manager / Animator",size=(1024,768))
        wx.SashLayoutWindow.__init__(self,parent,-1)
    
        self.taskWin=taskwin
        self.visualizer=visualizer

        self.menuManager=menumanager
        self.createMenu(menumanager)
        
        self.control = UrmasControl.UrmasControl(self)

        #self.Bind(wx.EVT_CLOSE,self.closeWindowCallback)

        self.sizer=wx.BoxSizer(wx.VERTICAL)
        self.palette = UrmasPalette.UrmasPalette(self,self.control)
        self.sizer.Add(self.palette,0,flag=wx.EXPAND)

        self.timelinePanel=TimelinePanel.TimelinePanel(self,self.control,size=(1024,500))
        self.control.setTimelinePanel(self.timelinePanel)
        
        self.sizer.Add(self.timelinePanel,1,flag=wx.EXPAND)

        self.control.setAnimationMode(1)

        
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)
        #self.SetStatusText("Done.")

        
    def cleanMenu(self):
        """
        Method: createMenu()
        Created: 06.04.2005, KP
        Description: Removes the menu items from menu
        """
        mgr=self.menuManager
        
        mgr.remove(MenuManager.ID_PREFERENCES)
        mgr.remove(MenuManager.ID_ADD_SPLINE)
        mgr.remove(MenuManager.ID_ADD_TIMEPOINT)
        mgr.remove(MenuManager.ID_ADD_TRACK)
        mgr.remove(MenuManager.ID_ANIMATE)

        mgr.remove(MenuManager.ID_FIT_TRACK)
    
        mgr.remove(MenuManager.ID_MIN_TRACK)
        mgr.remove(MenuManager.ID_OPEN_PROJECT)
        mgr.remove(MenuManager.ID_RENDER_PROJECT)
        mgr.remove(MenuManager.ID_RENDER_PREVIEW)
        mgr.remove(MenuManager.ID_SAVE)
        mgr.remove(MenuManager.ID_SET_TRACK)
        mgr.remove(MenuManager.ID_SET_TRACK_RELATIVE)
        mgr.remove(MenuManager.ID_MAINTAIN_UP)
        mgr.remove(MenuManager.ID_SPLINE_CLOSED)
        mgr.remove(MenuManager.ID_SPLINE_SET_BEGIN)
        mgr.remove(MenuManager.ID_SPLINE_SET_END)
        mgr.remove(MenuManager.ID_CLOSE_PROJECT)

        mgr.removeMenu("track")
        mgr.removeMenu("rendering")
        mgr.removeMenu("camera")

    def createMenu(self,mgr):
        """
        Method: createMenu()
        Created: 06.04.2005, KP
        Description: Creates a menu for the window
        """
        mgr.createMenu("track","&Track",before="help")
        mgr.createMenu("rendering","&Rendering",before="help")
        mgr.createMenu("camera","&Camera",before="help")
      
        mgr.addMenuItem("settings",MenuManager.ID_PREFERENCES,"&Preferences",self.onMenuPreferences)
        
        mgr.addMenuItem("file",MenuManager.ID_OPEN_PROJECT,"Open project...","Open a BioImageXD Animator Project",self.onMenuOpenProject,before=MenuManager.ID_IMPORT)
        mgr.addMenuItem("file",MenuManager.ID_SAVE_PROJECT,"Save project as...","Save current BioImageXD Animator Project",self.onMenuSaveProject,before=MenuManager.ID_IMPORT)
        mgr.addMenuItem("file",MenuManager.ID_CLOSE_PROJECT,"Close project","Close this Animator Project",self.onMenuCloseProject,before=MenuManager.ID_IMPORT)
        mgr.addSeparator("file",before=MenuManager.ID_IMPORT)
        
        mgr.createMenu("addtrack","&Add Track",place=0)
        
        mgr.addMenuItem("addtrack",MenuManager.ID_ADD_TIMEPOINT,"Timepoint Track","Add a timepoint track to the timeline",self.onMenuAddTimepointTrack)
        mgr.addMenuItem("addtrack",MenuManager.ID_ADD_SPLINE,"Camera Path Track","Add a camera path track to the timeline",self.onMenuAddSplineTrack)
        
        mgr.addSubMenu("track","addtrack","&Add Track",MenuManager.ID_ADD_TRACK)
        mgr.addMenuItem("track",MenuManager.ID_DELETE_TRACK,"&Remove track","Remove the track from timeline",self.onMenuRemoveTrack)
        mgr.addSeparator("track")
        
        mgr.addMenuItem("track",MenuManager.ID_FIT_TRACK,"Expand to maximum","Expand the track to encompass the whole timeline",self.onMaxTrack)
        mgr.addMenuItem("track",MenuManager.ID_MIN_TRACK,"Shrink to minimum","Shrink the track to as small as possible",self.onMinTrack)
        mgr.addMenuItem("track",MenuManager.ID_SET_TRACK,"Set item size","Set each item on this track to be of given size",self.onSetTrack)
        mgr.addMenuItem("track",MenuManager.ID_SET_TRACK_TOTAL,"Set total length","Set total length of items on this track",self.onSetTrackTotal)
        mgr.addMenuItem("track",MenuManager.ID_SET_TRACK_RELATIVE,"Set to physical length","Set the length of items on this track to be relative to their physical length",self.onSetTrackRelative)
        mgr.addMenuItem("rendering",MenuManager.ID_ANIMATE,"&Animated rendering","Select whether to produce animation or still images",self.onMenuAnimate,check=1)
        mgr.addSeparator("rendering")
        mgr.addMenuItem("rendering",MenuManager.ID_RENDER_PREVIEW,"Rendering &Preview","Preview rendering",self.onMenuRender)
        mgr.addMenuItem("rendering",MenuManager.ID_RENDER_PROJECT,"&Render project","Render this project",self.onMenuRender)
    
        mgr.addMenuItem("camera",MenuManager.ID_SPLINE_CLOSED,"&Closed Path","Set the camera path to open / closed.",self.onMenuClosedSpline,check=1)
        mgr.addMenuItem("camera",MenuManager.ID_SPLINE_SET_BEGIN,"&Begin at the end of previous path","Set this camera path to begin where the previous path ends",self.onMenuSetBegin)
        mgr.addMenuItem("camera",MenuManager.ID_SPLINE_SET_END,"&End at the beginning of next path","Set this camera path to end where the next path starts",self.onMenuSetEnd)
        mgr.addSeparator("camera")
        mgr.addMenuItem("camera",MenuManager.ID_MAINTAIN_UP,"&Maintain up direction",self.onMenuSetMaintainUp,check=1)
            
        mgr.disable(MenuManager.ID_SPLINE_SET_BEGIN)
        mgr.disable(MenuManager.ID_SPLINE_SET_END)

    def updateMenus(self):
        """
        Method: updateMenus()
        Created: 18.04.2005, KP
        Description: A method to update the state of menu items
        """
        spltracks=len(self.control.timeline.getSplineTracks())
        flag=(spltracks>=2)
        #print "updateMenus()",spltracks
        self.menuManager.enable(MenuManager.ID_SPLINE_SET_BEGIN)
        self.menuManager.enable(MenuManager.ID_SPLINE_SET_END)
        active = self.control.getSelectedTrack()
        if active and hasattr(active,"maintainUpDirection"):
            self.menuManager.check(MenuManager.ID_MAINTAIN_UP,active.maintainUpDirection)
        
    def onMenuMayavi(self,event):
        """
        Method: onMenuMayavi
        Created: 20.04.2005, KP
        Description: Start mayavi for rendering
        """
        self.renderMenu.Enable(MenuManager.ID_RENDER_PROJECT,1)
        self.control.startMayavi()

    def onMenuRender(self,event):
        """
        Method: onMenuRender()
        Created: 19.04.2005, KP
        Description: Render this project
        """
        if event.GetId() == MenuManager.ID_RENDER_PROJECT:
            w,h=self.taskWin.GetSize()
            self.taskWin.SetDefaultSize((300,h))
            video=VideoGeneration.VideoGeneration(self.taskWin,self.control,self.visualizer)
            video.SetSize((300,h))
            video.Show()
            self.visualizer.mainwin.OnSize(None)
            #print "Setting taskwin size to ",200,h

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
        val=5
        if dlg.ShowModal()==wx.ID_OK:
            try:
                val=int(dlg.GetValue())
            except:
                return
        size=val*self.control.getPixelsPerSecond()
        print "Setting to size ",size,"(",val,"seconds)"
        active = self.control.getSelectedTrack()
        active.setToSize(size)
        
    def onSetTrackRelative(self,evt):
        """
        Method: onSetTrackTotal
        Created: 25.06.2005, KP
        Description: Set the length of items in a track relative to their physical size
        """
        active = self.control.getSelectedTrack()
        
        dlg = wx.TextEntryDialog(self,"Set total duration (seconds) of items in track:","Set track duration")
        dlg.SetValue("30")
        val=5
        if dlg.ShowModal()==wx.ID_OK:
            try:
                val=int(dlg.GetValue())
            except:
                return
        size=val*self.control.getPixelsPerSecond()
        print "Setting to size ",size,"(",val,"seconds)"

        active.setToRelativeSize(size)
        

    def onSetTrackTotal(self,evt):
        """
        Method: onSetTrackTotal
        Created: 23.06.2005, KP
        Description: Set the total length of items in a track
        """

        dlg = wx.TextEntryDialog(self,"Set total duration (seconds) of items in track:","Set track duration")
        dlg.SetValue("30")
        val=5
        if dlg.ShowModal()==wx.ID_OK:
            try:
                val=int(dlg.GetValue())
            except:
                return
        size=val*self.control.getPixelsPerSecond()
        print "Setting to size ",size,"(",val,"seconds)"
        active = self.control.getSelectedTrack()
        active.setToSizeTotal(size)


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
        
    def onMenuSetMaintainUp(self,evt):
        """
        Method: onMenuSetMaintainUp
        Created: 18.04.2005, KP
        Description: Set the track to maintain up direction
        """
        active = self.control.getSelectedTrack()
        if hasattr(active,"setMaintainUpDirection"):
            active.setMaintainUpDirection(evt.IsChecked())
        
    def onMenuClosedSpline(self,evt):
        """
        Method: onMenuClosedSpline
        Created: 14.04.2005, KP
        Description: Callback function for menu item camera path is closed
        """
        track=self.control.getSelectedTrack()
        if hasattr(track,"setClosed"):
            track.setClosed(evt.IsChecked())
        
    def onMenuAnimate(self,evt):
        """
        Method: onMenuAnimate
        Created: 14.04.2005, KP
        Description: Callback function for menu item animated rendering
        """
        flag=evt.IsChecked()
        self.control.setAnimationMode(flag)
        self.addTrackMenu.Enable(MenuManager.ID_ADD_SPLINE,flag)
        
    def onMenuRemoveTrack(self,evt):
        """
        Method: onMenuRemoveTrack
        Created: 18.07.2005, KP
        Description: Callback function for removing a track
        """
        track=self.control.getSelectedTrack()
        self.control.timeline.removeTrack(track,1)
        

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
        
    def onMenuCloseProject(self,event):
        """
        Method: onMenuCloseProject(self,event)
        Created: 24.06.2005, KP
        Description: Reset the animator
        """
        self.control.resetAnimator()


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
        name=None
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
        
