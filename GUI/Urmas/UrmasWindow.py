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

def makeChain(*args):
    lst=args
    lst[0].prev=None
    for i in range(1,len(lst)):
        lst[i].prev=lst[i-1]
        lst[i-1].next=lst[i]
    lst[-1].next=None
    return lst
        
class UrmasWindow(wx.wizard.Wizard):
    """
    Class: UrmasWindow
    Created: 10.02.2005, KP
    Description: A window for controlling the rendering/animation/movie generation.
                 The window has a notebook with different pages for rendering and
                 animation modes, and a page for configuring the movie generation.
    """
    def __init__(self,parent):
        wx.wizard.Wizard.__init__(self,parent,-1,"Rendering Manager / Animator",
        style=wx.RESIZE_BORDER|wx.CAPTION|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX|wx.CLOSE_BOX|wx.SYSTEM_MENU)
        self.status=wx.ID_OK
        ico=reduce(os.path.join,["..","Icons","Selli.ico"])
        self.icon = wx.Icon(ico,wx.BITMAP_TYPE_ICO)
        self.SetIcon(self.icon)
        self.control = UrmasControl.UrmasControl(self)

        self.Bind(wx.EVT_CLOSE,self.closeWindowCallback)
        
        self.timepointSelection=UrmasTimepointSelection.UrmasTimepointSelection(self)
        

        self.timelinePanel=TimelinePanel.TimelinePanel(self,self.control)
        self.control.setTimelinePanel(self.timelinePanel)
        
        self.videogeneration=VideoGeneration.VideoGeneration(self)
        
        makeChain(self.timepointSelection,self.timelinePanel,self.videogeneration)
        self.timepointSelection.SetSize(self.timelinePanel.GetSize())
        self.FitToPage(self.timelinePanel)
        self.timelinePanel.Show(0)
        #self.FitToPage(self.timepointSelection)
    
    def startWizard(self):
        """
        Method: startWizard()
        Created: 14.03.2005, KP
        Description: Start this wizard
        """              
        self.RunWizard(self.timepointSelection)
    
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
        self.timepointSelection.setDataUnit(dataUnit)
        #self.timelinePanel.setDataUnit(dataUnit)
        self.control.setDataUnit(dataUnit)
        
    def closeWindowCallback(self,event):
        """
        Method: closeWindowCallback
        Created: 10.2.2005, KP
        Description: A callback that is used to close this window
        """
        self.EndModal(self.status)
