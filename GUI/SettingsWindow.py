#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: SettingsWindow.py
 Project: BioImageXD
 Created: 09.02.2005
 Creator: KP
 Description:

 A wxPython wxDialog window that is used to control the settings for the
 whole application.
 
 Modified: 09.02.2005 KP - Created the module

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
__author__ = "BioImageXD Project"
__version__ = "$Revision: 1.22 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import os.path

import wx
#import GuiGeneration
import  wx.lib.filebrowsebutton as filebrowse
import Configuration
import GuiGeneration

class GeneralSettings(wx.Panel):
    """
    Class: GeneralSettings
    Created: 09.02.2005, KP
    Description: A window for controlling the general settings of the application
    """ 
    def __init__(self,parent):
        wx.Panel.__init__(self,parent,-1)
        self.sizer = wx.GridBagSizer(5,5)
        conf = Configuration.getConfiguration()
        format = conf.getConfigItem("ImageFormat","Output")
        
        self.imageBox=wx.StaticBox(self,-1,"Image Format",size=(600,150))
        self.imageBoxSizer=wx.StaticBoxSizer(self.imageBox,wx.VERTICAL)
        self.imageBoxSizer.SetMinSize(self.imageBox.GetSize())
        
        self.lbl=wx.StaticText(self,-1,"Default format for Images:")
        self.choice=wx.Choice(self,-1,choices=["PNG","PNM","BMP","JPEG","TIFF"])
        
        self.choice.SetStringSelection(format.upper())

        self.imageBoxSizer.Add(self.lbl)
        self.imageBoxSizer.Add(self.choice)
        
        self.sizer.Add(self.imageBoxSizer,(0,0))
        
        
        
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)
        
    def writeSettings(self,conf):
        """
        Method: writeSettings(config)
        Created: 05.04.2005, KP
        Description: A method that writes out the settings that have been modified
                     in this window.
        """     
        format=self.choice.GetStringSelection()
        print "Setting format to ",format.lower()
        conf.setConfigItem("ImageFormat","Output",format.lower())
        
class PathSettings(wx.Panel):
    """
    Class: PathSettings
    Created: 09.02.2005, KP
    Description: A window for controlling the path settings of the application
    """ 
    def __init__(self,parent):
        wx.Panel.__init__(self,parent,-1,size=(640,480))
        self.sizer=wx.GridBagSizer(5,5)
        #self.SetBackgroundColour(wx.Colour(255,0,0))
        
        conf=Configuration.getConfiguration()
        vtkpath = conf.getConfigItem("VTKPath","VTK")
        mayavipath = conf.getConfigItem("MayaviPath","Mayavi")
        datapath=conf.getConfigItem("DataPath","Paths")
        systemmayavi = conf.getConfigItem("UseSystemMayavi","Mayavi")
        removevtk = conf.getConfigItem("RemoveOldVTK","VTK")
        remember =conf.getConfigItem("RememberPath","Paths")
        
        self.vtkBox=wx.StaticBox(self,-1,"VTK Path",size=(600,150))
        self.vtkBoxSizer=wx.StaticBoxSizer(self.vtkBox,wx.VERTICAL)
        self.vtkBoxSizer.SetMinSize(self.vtkBox.GetSize())
        self.vtkbrowse=filebrowse.DirBrowseButton(self,-1,labelText="Location of VTK",
        toolTip="Set the location of the version of VTK you want to use",
        startDirectory=vtkpath)
        self.vtkbrowse.SetValue(vtkpath)
        
        self.vtkBoxSizer.Add(self.vtkbrowse,0,wx.EXPAND)
        self.removeVTKCheckbox = wx.CheckBox(self,-1,"Remove old VTK from path")
        removevtk=int(removevtk)
        self.removeVTKCheckbox.SetValue(removevtk)
        self.vtkBoxSizer.Add(self.removeVTKCheckbox)
        
        
        self.mayaviBox=wx.StaticBox(self,-1,"MayaVi Path",size=(600,150))
        self.mayaviBoxSizer=wx.StaticBoxSizer(self.mayaviBox,wx.VERTICAL)
        self.mayaviBoxSizer.SetMinSize(self.mayaviBox.GetSize())        
        self.mayavibrowse=filebrowse.DirBrowseButton(self,-1,labelText="Location of MayaVi",
        toolTip="Set the location of the version of Mayavi you want to use",
        startDirectory=mayavipath)
        self.mayavibrowse.SetValue(mayavipath)
        self.mayaviBoxSizer.Add(self.mayavibrowse,0,wx.EXPAND)
        self.removeMayaviCheckbox = wx.CheckBox(self,-1,"Use system version of MayaVi")
        systemmayavi=int(systemmayavi)
        self.removeMayaviCheckbox.SetValue(systemmayavi)
        self.mayaviBoxSizer.Add(self.removeMayaviCheckbox)
        
        
        self.dataBox=wx.StaticBox(self,-1,"Data Files Directory",size=(600,150))
        self.dataBoxSizer=wx.StaticBoxSizer(self.dataBox,wx.VERTICAL)
        self.dataBoxSizer.SetMinSize(self.dataBox.GetSize())
        self.databrowse=filebrowse.DirBrowseButton(self,-1,labelText="Location of Data Files",
        toolTip="Set the default directory for data files",
        startDirectory=datapath)
        self.databrowse.SetValue(datapath)
        
        self.dataBoxSizer.Add(self.databrowse,0,wx.EXPAND)
        self.useLastCheckbox = wx.CheckBox(self,-1,"Use last opened directory as default directory")
        remember=int(remember)
        self.useLastCheckbox.SetValue(remember)
        self.dataBoxSizer.Add(self.useLastCheckbox)        
        
        
        self.sizer.Add(self.vtkBoxSizer, (0,0),flag=wx.EXPAND|wx.ALL)
        self.sizer.Add(self.mayaviBoxSizer, (1,0),flag=wx.EXPAND|wx.ALL)
        self.sizer.Add(self.dataBoxSizer,(2,0),flag=wx.EXPAND|wx.ALL)        
        self.SetAutoLayout(1)
        self.SetSizer(self.sizer)
        self.Layout()
        self.sizer.Fit(self)
        
    def writeSettings(self,conf):
        """
        Method: writeSettings(config)
        Created: 12.03.2005, KP
        Description: A method that writes out the settings that have been modified
                     in this window.
        """     
        vtkpath=self.vtkbrowse.GetValue()
        mayavipath=self.mayavibrowse.GetValue()
        datapath=self.databrowse.GetValue()
        rememberlast=self.useLastCheckbox.GetValue()
        usesystemmayavi=self.removeMayaviCheckbox.GetValue()
        removevtk=self.removeVTKCheckbox.GetValue()
        conf.setConfigItem("VTKPath","VTK",vtkpath)
        conf.setConfigItem("MayaviPath","Mayavi",mayavipath)
        conf.setConfigItem("DataPath","Paths",datapath)
        conf.setConfigItem("UseSystemMayavi","Mayavi",usesystemmayavi)
        conf.setConfigItem("RemoveOldVTK","VTK",removevtk)
        conf.setConfigItem("RememberPath","Paths",rememberlast)        


        
class MovieSettings(wx.Panel):
    """
    Class: MovieSettings
    Created: 09.02.2005, KP
    Description: A window for controlling the movie generation settings of the application
    """ 
    def __init__(self,parent):
        wx.Panel.__init__(self,parent,-1)
    


class SettingsWindow(wx.Dialog):
    """
    Class: SettingsWindow
    Created: 09.02.2005, KP
    Description: A window for controlling the settings of the application
    """ 
    def __init__(self,parent):
        wx.Dialog.__init__(self,parent,-1,"Settings for BioImageXD",style=wx.CAPTION|wx.STAY_ON_TOP|wx.CLOSE_BOX|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX|wx.RESIZE_BORDER|wx.DIALOG_EX_CONTEXTHELP,
        size=(640,480))
        self.listbook=wx.Listbook(self,-1,style=wx.LB_LEFT)
        self.listbook.SetSize((640,480))
        self.sizer=wx.BoxSizer(wx.VERTICAL)
        
        self.imagelist=wx.ImageList(32,32)
        self.listbook.AssignImageList(self.imagelist)
        imgpath=reduce(os.path.join,["Icons"])
        for i in ["General.gif","Paths.gif","Video.gif"]:
            icon=os.path.join(imgpath,i)
            print "icon=",icon
            bmp=wx.Bitmap(icon,wx.BITMAP_TYPE_GIF)
            self.imagelist.Add(bmp)
        self.generalPanel=GeneralSettings(self.listbook)
        self.pathsPanel=PathSettings(self.listbook)
        self.moviePanel=MovieSettings(self.listbook)
        
        self.listbook.AddPage(self.generalPanel,"General",imageId=0)
        self.listbook.AddPage(self.pathsPanel,"Paths",imageId=1)
        self.listbook.AddPage(self.moviePanel,"Video Output",imageId=2)

        self.sizer.Add(self.listbook,flag=wx.EXPAND|wx.ALL)
        
        self.staticLine=wx.StaticLine(self,-1)
        self.sizer.Add(self.staticLine,flag=wx.EXPAND)
        self.buttonSizer = self.CreateButtonSizer(wx.OK|wx.CANCEL)
        self.sizer.Add(self.buttonSizer,1,flag=wx.EXPAND|wx.ALL|wx.ALIGN_RIGHT)
        
        wx.EVT_BUTTON(self,wx.ID_OK,self.writeSettings)
        
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)

    def writeSettings(self,evt):
        conf=Configuration.getConfiguration()
        self.pathsPanel.writeSettings(conf)
        self.generalPanel.writeSettings(conf)
        conf.writeSettings()
        self.Close()
        
