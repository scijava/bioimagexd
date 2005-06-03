#! /usr/bin/env python
#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: MenuManager
 Project: BioImageXD
 Created: 29.05.2005, KP
 Description:

 A module for managing the menus

 Modified: 29.05.2005 KP - Created the class
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
__version__ = "$Revision: 1.71 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import wx
    
ID_OPEN             =100
ID_QUIT             =101
ID_ABOUT            =102
ID_COLOCALIZATION   =103
ID_COLORMERGING     =104
ID_VSIA             =105
ID_ADJUST           =106
ID_RENDER           =107
ID_REEDIT           =108
ID_TREE             =109
ID_IMPORT           =110
ID_EXPORT           =111
ID_EXPORT_VTIFILES  =112
ID_EXPORT_IMAGES    =113
ID_IMPORT_VTIFILES  =114
ID_IMPORT_IMAGES    =115
ID_HELP             =116
ID_SETTINGS         =117
ID_PREFERENCES      =118
ID_RESLICE          =119
ID_MAYAVI           =120
ID_VIS_SECTIONS     =121
ID_VIS_SLICES       =122
ID_VIS_3D           =123
ID_INFO             =124
ID_SHOW_TREE        =125
ID_VIS_GALLERY      =126
ID_LIGHTS           =127
ID_RENDERWIN        =128
ID_RELOAD           =129

ID_TREE_WIN         =130
ID_VIS_WIN          =131
ID_TASK_WIN         =132
ID_OPEN_SETTINGS    =133
ID_SAVE_SETTINGS    =134

ID_RESTORE          =135

class MenuManager:
    """
    Class: MenuManager
    Created: 29.05.2005, KP
    Description: A class for managing the menu
    """
    instance=None
    mainwin=None
    mapping={}
    def __init__(self,mainwin,**kws):
        """
        Method: __init__(parent,id,app)
        Created: 03.11.2004, KP
        Description: Initialization
        """
        self.text=1
        if kws.has_key("text"):
           self.text=kws["text"]
        self.mainwin=mainwin
        # This is the menubar object that holds all the menus
        self.mapping={}
        self.visualizer=None
        self.itemBar = None
        self.toolIds=[]
        
    def setVisualizer(self,visualizer):
        """
        Method: setVisualizer
        Created: 01.06.2005, KP
        Description: Set the visualizer instance managed by this class
        """
        self.visualizer=visualizer
    def clearItemsBar(self):
        """
        Method: clearItemsBar()
        Created: 01.06.2005, KP
        Description: Clear items bar
        """
        if not self.itemBar:return
        for i in self.toolIds:
            self.itemBar.DeleteTool(i)
        self.toolIds=[]
        self.itemBar.Realize()
        

    def addItem(self,name,bitmap,toolid,func):
        """
        Method: addItem
        Created: 01.06.2005, KP
        Description: Add a toolbar item
        """
        self.toolIds.append(toolid)
        if not self.itemBar:
            if self.text:
                flags=wx.TB_HORIZONTAL|wx.TB_TEXT
            else:
                flags=wx.TB_HORIZONTAL
            self.itemBar = wx.ToolBar(self.visualizer.itemWin,-1,style=wx.TB_HORIZONTAL)
            self.itemBar.SetToolBitmapSize((32,32))

        self.visualizer.itemWin.Bind(wx.EVT_TOOL,func,id=toolid)

        self.itemBar.DoAddTool(toolid,name,bitmap,kind=wx.ITEM_RADIO)
        self.itemBar.Realize()

    def addMenuItem(self,menu,menuid,name,hlp=None,callback=None):
        """
        Method: addMenuItem
        Created: 29.05.2005, KP
        Description: Add a menu item
        """
        if not callback:
            if hlp and type(hlp)!=type(""):
                callback=hlp
                hlp=None
        self.mapping[menuid]=menu
        if not hlp:
            menu.Append(menuid,name)
        else:
            menu.Append(menuid,name,hlp)
        if callback:
            wx.EVT_MENU(self.mainwin,menuid,callback)
        
        
    def disable(self,itemid):
        """
        Method: disable(itemid)
        Created: 29.05.2005, KP
        Description: Disable a menu item
        """
        self.mapping[itemid].Enable(itemid,0)
        
    def enable(self,itemid,callback=None):
        """
        Method: enable(itemid)
        Created: 29.05.2005, KP
        Description: Enable a menu item
        """
        self.mapping[itemid].Enable(itemid,1)
        if callback:
            wx.EVT_MENU(self.mainwin,itemid,callback)

        
        
        
