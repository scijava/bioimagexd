#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: SettingsWindow.py
 Project: Selli 2
 Created: 09.02.2005
 Creator: KP
 Description:

 A wxPython wxDialog window that is used to control the settings for the
 whole application.
 
 Modified: 09.02.2005 KP - Created the module

 Selli 2 includes the following persons:
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 
 Copyright (c) 2005 Selli 2 Project.
"""
__author__ = "Selli 2 Project <http://sovellusprojektit.it.jyu.fi/selli/>"
__version__ = "$Revision: 1.40 $"
__date__ = "$Date: 2005/01/13 14:52:39 $"

import os.path

from wxPython.wx import *

class GeneralSettings(wxPanel):
    pass
class PathSettings(wxPanel):
    pass
class MovieSettings(wxPanel):
    pass
    


class SettingsWindow(wxDialog):
    """
    Class: SettingsWindow
    Created: 09.02.2005
    Creator: KP
    Description: A window for controlling the settings of the application
    """ 
    def __init__(self,parent):
        wxDialog.__init__(self,parent,-1,"Settings for Selli",style=wxCAPTION|wxSTAY_ON_TOP|wxCLOSE_BOX|wxMAXIMIZE_BOX|wxMINIMIZE_BOX|wxRESIZE_BORDER|wxDIALOG_EX_CONTEXTHELP,
        size=(640,480))
        self.listbook=wxListbook(self,-1,style=wxLB_LEFT)
        self.listbook.SetSize((640,480))
        self.sizer=wxBoxSizer(wxVERTICAL)
        
        self.imagelist=wxImageList(32,32)
        self.listbook.AssignImageList(self.imagelist)
        imgpath=reduce(os.path.join,["..","Icons"])
        for i in ["General.gif","Paths.gif","Video.gif"]:
            icon=os.path.join(imgpath,i)
            bmp=wxBitmap(icon,wxBITMAP_TYPE_GIF)
            self.imagelist.Add(bmp)
        self.generalPanel=GeneralSettings(self)
        self.pathsPanel=PathSettings(self)
        self.moviePanel=MovieSettings(self)
        
        self.listbook.AddPage(self.generalPanel,"General",imageId=0)
        self.listbook.AddPage(self.pathsPanel,"Paths",imageId=1)
        self.listbook.AddPage(self.moviePanel,"Movie Generation",imageId=2)

        self.sizer.Add(self.listbook,flag=wxEXPAND|wxALL)
        
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)
