#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

"""
 Unit: UrmasWindow
 Project: Selli 2
 Created: 10.02.2005
 Creator: KP
 Description:

 URM/AS - The Unified Rendering Manager / Animator for Selli
 
 This is a timeline based GUI for controlling the rendering of datasets. The GUI allows users
 to specify a path for the camera to follow (using Heikki Uuksulainen's MayaVi animator code)
 and also allows them to produce videos of the rendering using ffmpeg.
 
 This is the wx.Dialog based window that contains the Urmas.
 
 Modified: 10.02.2005 KP - Created the module
 
 Selli 2 includes the following persons:
 
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 
 Copyright (c) 2005 Selli 2 Project.
"""
__author__ = "Selli 2 Project <http://sovellusprojektit.it.jyu.fi/selli/>"
__version__ = "$Revision: 1.22 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import wx
from Timeline import *
import TimepointSelection

class UrmasWindow(wx.Dialog):
    """
    Class: UrmasWindow
    Created: 10.02.2005, KP
    Description: A window for controlling the rendering/animation/movie generation.
                 The window has a notebook with different pages for rendering and
                 animation modes, and a page for configuring the movie generation.
    """
    def __init__(self,parent):
        print "Creating UrmasWindow()"
        wx.Dialog.__init__(self,parent,-1,"Rendering Manager / Animator",size=(640,480))
        self.status=wx.ID_OK
        ico=reduce(os.path.join,["..","Icons","Selli.ico"])
        self.icon = wx.Icon(ico,wx.BITMAP_TYPE_ICO)
        self.SetIcon(self.icon)
        
        self.Bind(wx.EVT_CLOSE,self.closeWindowCallback)
        self.mainsizer=wx.GridBagSizer(5,5)
    
#        self.buttonSizer=wx.BoxSizer(wxHORIZONTAL)
#        self.mainsizer.Add(self.buttonSizer,(4,0),span=(1,2),flag=wx.EXPAND|wx.LEFT|wx.RIGHT)

        self.notebook=wx.Notebook(self,-1)
        self.timepointSelection=TimepointSelection.TimepointSelectionPanel(self.notebook)

        self.notebook.AddPage(self.timepointSelection,"Select Time Points")

        self.timelinePanel=TimelinePanel(self.notebook)
        print "Adding timeline panel to notebook"
        self.notebook.AddPage(self.timelinePanel,"Rendering")
        print "done"
        self.mainsizer.Add(self.notebook,(0,0),flag=wx.EXPAND|wx.ALL)


        self.SetSizer(self.mainsizer)
        self.SetAutoLayout(True)
        self.mainsizer.Fit(self)
        
    def setDataUnit(self,dataUnit):
        self.timepointSelection.setDataUnit(dataUnit)
        self.timelinePanel.setDataUnit(dataUnit)
        
    def closeWindowCallback(self,event):
        """
        Method: closeWindowCallback
        Created: 10.2.2005, KP
        Description: A callback that is used to close this window
        """
        self.EndModal(self.status)
