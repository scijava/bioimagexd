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
    
ID_OPEN             =101
ID_QUIT             =110
ID_ABOUT            =111
ID_COLOCALIZATION   =1000
ID_COLORMERGING     =1001
ID_VSIA             =1010
ID_ADJUST           =1011
ID_RENDER           =1100
ID_REEDIT           =1101
ID_TREE             =1110
ID_IMPORT           =1111
ID_EXPORT           =10000
ID_EXPORT_VTIFILES  =10001
ID_EXPORT_IMAGES    =10010
ID_IMPORT_VTIFILES  =10011
ID_IMPORT_IMAGES    =10100
ID_HELP             =10101
ID_SETTINGS         =10110
ID_PREFERENCES      =10111
ID_RESLICE          =11000
ID_MAYAVI           =11001
ID_VIS_SECTIONS     =11010
ID_VIS_SLICES       =11011
ID_VIS_3D           =11100
ID_INFO             =11101
ID_SHOW_TREE        =11110
ID_VIS_GALLERY      =11111
ID_LIGHTS           =100000
ID_RENDERWIN        =100001
ID_RELOAD           =100010

ID_TREE_WIN         =100011
ID_VIS_WIN          =100100
ID_TASK_WIN         =100101
ID_OPEN_SETTINGS    =100110
ID_SAVE_SETTINGS    =100111

ID_RESTORE          =101000

class MenuManager:
    """
    Class: MenuManager
    Created: 29.05.2005, KP
    Description: A class for managing the menu
    """
    instance=None
    mainwin=None
    mapping={}
    def __init__(self,mainwin):
        """
        Method: __init__(parent,id,app)
        Created: 03.11.2004, KP
        Description: Initialization
        """
        self.mainwin=mainwin
        # This is the menubar object that holds all the menus
        self.mapping={}

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

        
        
        
