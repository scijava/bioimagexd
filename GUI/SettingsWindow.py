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

import wx

class GeneralSettings(wx.Panel):
    """
    Class: GeneralSettings
    Created: 09.02.2005, KP
    Description: A window for controlling the general settings of the application
    """ 
    def __init__(self,parent):
        pass
        
class PathSettings(wx.Panel):
    pass
class MovieSettings(wx.Panel):
    pass
    


class SettingsWindow(wx.Dialog):
    """
    Class: SettingsWindow
    Created: 09.02.2005, KP
    Description: A window for controlling the settings of the application
    """ 
    def __init__(self,parent):
        wx.Dialog.__init__(self,parent,-1,"Settings for Selli",style=wx.CAPTION|wx.STAY_ON_TOP|wx.CLOSE_BOX|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX|wx.RESIZE_BORDER|wx.DIALOG_EX_CONTEXTHELP,
        size=(640,480))
        self.listbook=wx.Listbook(self,-1,style=wx.LB_LEFT)
        self.listbook.SetSize((640,480))
        self.sizer=wx.BoxSizer(wx.VERTICAL)
        
        self.imagelist=wx.ImageList(32,32)
        self.listbook.AssignImageList(self.imagelist)
        imgpath=reduce(os.path.join,["Icons"])
        for i in ["General.gif","Paths.gif","Video.gif"]:
            icon=os.path.join(imgpath,i)
            bmp=wx.Bitmap(icon,wx.BITMAP_TYPE_GIF)
            self.imagelist.Add(bmp)
        self.generalPanel=GeneralSettings(self)
        self.pathsPanel=PathSettings(self)
        self.moviePanel=MovieSettings(self)
        
        self.listbook.AddPage(self.generalPanel,"General",imageId=0)
        self.listbook.AddPage(self.pathsPanel,"Paths",imageId=1)
        self.listbook.AddPage(self.moviePanel,"Video Output",imageId=2)

        self.sizer.Add(self.listbook,flag=wx.EXPAND|wx.ALL)
        
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)
