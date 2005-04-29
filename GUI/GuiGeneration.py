#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: GuiGeneration
 Project: BioImageXD
 Created: 09.02.2005
 Creator: KP
 Description:

 GuiGeneration is a module with functions for generating various pieces
 of GUI that would otherwise require lots of repetitive code, like 
 label-field pairs or path field - browse button pairs
 
 Modified: 12.03.2005 KP - Created the module

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


import wx
import  wx.lib.filebrowsebutton as filebrowse
import Configuration

def createDirBrowseButton(parent,label,callback):
    sizer=wx.BoxSizer(wx.VERTICAL)
    sizer2=wx.BoxSizer(wx.HORIZONTAL)
    lbl=wx.StaticText(parent,-1,label)
    sizer.Add(lbl)
    field=wx.TextCtrl(parent,-1,"")
    sizer2.Add(field)
    btn=filebrowse.DirBrowseButton(parent,-1,changeCallback = callback)
    sizer2.Add(btn)
    sizer.Add(sizer2)
    return sizer
    
def getImageFormatMenu(parent,label="Image Format: "):
    sizer=wx.BoxSizer(wx.HORIZONTAL)
    lbl=wx.StaticText(parent,-1,label)
    sizer.Add(lbl)
    formats=["PNG","BMP","JPEG","TIFF"]
    menu=wx.Choice(parent,-1,choices=formats)
    sizer.Add(menu)
    sizer.menu=menu
    return sizer

def getSliceSelection(parent):
    sizer=wx.GridBagSizer()
    #lbl=wx.StaticText(parent,-1,"Select processed slices:")
    fromlbl=wx.StaticText(parent,-1,"Slices from ")
    tolbl=wx.StaticText(parent,-1," to ")
    everylbl=wx.StaticText(parent,-1,"Every nth slice:")
    fromedit=wx.SpinCtrl(parent,-1)
    toedit=wx.SpinCtrl(parent,-1)
    fromedit.SetRange(0,25)
    fromedit.SetValue(0)
    toedit.SetRange(0,25)
    toedit.SetValue(0)
    everyedit=wx.TextCtrl(parent,-1,"1")
    sizer.Add(fromlbl,(0,0))
    sizer.Add(fromedit,(0,1))
    sizer.Add(tolbl,(0,2))
    sizer.Add(toedit,(0,3))
    sizer.Add(everylbl,(1,0))
    sizer.Add(everyedit,(1,1))
    return sizer
    
    
    
