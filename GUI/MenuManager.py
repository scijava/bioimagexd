#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: MenuManager
 Project: BioImageXD
 Created: 29.05.2005, KP
 Description:

 A module for managing the menus

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
import messenger


# We preface all ids with 99 so they won't overlap with ids returned by wx.NewId()    
ID_OPEN             =99100
ID_QUIT             =99101
ID_ABOUT            =99102
ID_COLOCALIZATION   =99103
ID_COLORMERGING     =99104
ID_VSIA             =99105
ID_ADJUST           =99106
ID_VIS_ANIMATOR     =99107
ID_REEDIT           =99108
ID_TREE             =99109
ID_IMPORT           =99110
ID_EXPORT           =99111
ID_EXPORT_VTIFILES  =99112
ID_EXPORT_IMAGES    =99113
ID_IMPORT_VTIFILES  =99114
ID_IMPORT_IMAGES    =99115
ID_HELP             =99116
ID_SETTINGS         =99117
ID_PREFERENCES      =99118
ID_RESLICE          =99119
ID_MAYAVI           =99120
ID_VIS_SECTIONS     =99121
ID_VIS_SLICES       =99122
ID_VIS_3D           =99123
ID_INFO             =99124
ID_SHOW_TREE        =99125
ID_VIS_GALLERY      =99126
ID_LIGHTS           =99127
ID_RENDERWIN        =99128
ID_RELOAD           =99129

ID_TREE_WIN         =99130
ID_VIS_WIN          =99131
ID_TASK_WIN         =99132
ID_OPEN_SETTINGS    =99133
ID_SAVE_SETTINGS    =99134

ID_RESTORE          =99135
ID_SAVE_SNAPSHOT    =99136

ID_CAPTURE          =99137
ID_ZOOM_OUT         =99138
ID_ZOOM_IN          =99139
ID_ZOOM_TO_FIT      =99140
ID_ZOOM_OBJECT      =99141
        
ID_PREFERENCES      =99142
ID_ADD_SPLINE       =99143
ID_ADD_TIMEPOINT    =99144
ID_ADD_TRACK        =99145
ID_ANIMATE          =99146
ID_FIT_TRACK        =99147
ID_MIN_TRACK        =99148
ID_OPEN_PROJECT     =99149
ID_RENDER_PROJECT   =99150
ID_RENDER_PREVIEW   =99151
ID_SAVE_PROJECT     =99152
ID_SET_TRACK        =99153
ID_SPLINE_CLOSED    =99154
ID_SPLINE_SET_BEGIN =99155
ID_SPLINE_SET_END   =99156
ID_SET_TRACK_TOTAL  =99157
ID_CLOSE_PROJECT    =99158
ID_MAINTAIN_UP      =99159
ID_SET_TRACK_RELATIVE=99160
ID_ADD_SCALE        =99161
ID_DRAG_ANNOTATION  =99162
ID_ROI_CIRCLE       =99163
ID_ROI_RECTANGLE    =99164
ID_ROI_POLYGON      =99165

ID_VIEW_CONFIG      =99166
ID_VIEW_TASKPANEL   =99167
ID_VIEW_TOOLBAR     =99168
ID_VIEW_HISTOGRAM   =99169
ID_CLOSE_TASKWIN    =99170

ID_DELETE_TRACK     =99171
ID_VIS_SIMPLE       =99172

ID_SET_VIEW         =99173
ID_VIEW_TOOL_NAMES  =99174

ID_VIEW_SHELL       =99175
ID_SHELL_WIN        =99176
ID_INFO_WIN         =99177
ID_VIEW_INFO        =99178
ID_LOAD_SCENE       =99179
ID_SAVE_SCENE       =99180
ID_SEPARATOR        =99181

ID_TOOL_WIN         =99182
ID_VISAREA_WIN      =99183
ID_VISTREE_WIN      =99184
ID_VISSLIDER_WIN    =99185
ID_ZSLIDER_WIN      =99186
ID_HISTOGRAM_WIN    =99187

ID_DEL_ANNOTATION   =99188

ID_ADD_KEYFRAME     =99189
ID_RESAMPLE         =99190
ID_TOOL_WIN2        =99191
ID_ZOOM_COMBO       =99192
ORIG_BUTTON         =99193
CONTEXT_HELP        =99194

PITCH               =99195
YAW                 =99196
ROLL                =99197

ID_HIDE_INFO        =99198
ID_ANIM_ZOOM_COMBO  =99199
ID_ITEM_SIZES       =99200
ID_ITEM_ORDER       =99201
ID_ITEM_ROTATE_CW   =99202
ID_ITEM_ROTATE_CCW  =99203
ID_FIT_TRACK_RATIO  =99204
ID_DELETE_ITEM      =99205
    
ID_VIEW_SCRIPTEDIT  =99206
ID_RECORD_SCRIPT    =99207
ID_STOP_RECORD      =99208
ID_RUN_SCRIPT       =99209

ID_UNDO             =99210
ID_REDO             =99211
ID_COMMAND_HISTORY  =99212

ID_SAVE_SCRIPT      =99213
ID_LOAD_SCRIPT      =99214
ID_CLOSE_SCRIPTEDITOR=99215

ID_IMMEDIATE_RENDER =99216

ID_MANIPULATE       =99217

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
        self.separators={}
        if kws.has_key("text"):
           self.text=kws["text"]
        self.mainwin=mainwin
        # This is the menubar object that holds all the menus
        self.mapping={}
        self.menus={}
        self.visualizer=None
        self.itemBar = None
        self.mainToolbar=None
        self.toolIds=[]
        self.tools={}
        
        
        self.commands = []
        
        self.showToolNames=0
        
    def getCommands(self):
        """
        Method: getCommands
        Created: 13.02.2006, KP
        Description: Return the list of commands
        """     
        return self.commands
        
        
    def addCommand(self,cmd):
        """
        Method: addCommand
        Created: 13.02.2006, KP
        Description: Add a command to the list of executed commands
        """    
        if cmd not in self.commands:
            self.commands.append(cmd)
        
    def getLastCommand(self):
        """
        Method: getLastCommand
        Created: 13.02.2006, KP
        Description: Return the last executed command
        """        
        return self.commands[-1]
        
    def setUndoedCommand(self,cmd):
        """
        Method: setUndoedCommand
        Created: 13.02.2006, KP
        Description: Set the last command that was undoed
        """        
        self.undoCmd=cmd
    
    def getUndoedCommand(self):
        """
        Method: getUndoedCommand
        Created: 13.02.2006, KP
        Description: Return the last undoed command
        """        
        return self.undoCmd
        
        
    def setMenuBar(self,menubar):
        """
        Method: setMenuBar
        Created: 19.06.2005, KP
        Description: Set the menubar
        """
        self.menubar=menubar

    def setMainToolbar(self,bar):
        """
        Method: setMenuBar
        Created: 19.06.2005, KP
        Description: Set the menubar
        """
        self.mainToolbar=bar       
    def removeSeparator(self,sepid):
        """
        Method: removeSeparator
        Created: 02.09.2005, KP
        Description: delete a separator
        """    
        menu=self.menus[self.mapping[sepid]]
        menu.RemoveItem(self.separators[sepid])
        
    def addSeparator(self,menuname,sepid=None,before=None):
        """
        Method: addSeparator(menuname)
        Created: 19.06.2005, KP
        Description: add a separator
        """
        if not before:
            if not sepid:
                self.menus[menuname].AppendSeparator()
            else:
                
                item=wx.MenuItem(self.menus[menuname],wx.ID_SEPARATOR,kind=wx.ITEM_SEPARATOR)
                self.separators[sepid]=item
                self.menus[menuname].Append(item)
                self.mapping[sepid]=menuname
        else:
            menu=self.menus[menuname]
            # Find the position where the item belongs            
            k=0
            for i in range(0,999):
                if menu.FindItemByPosition(i).GetId()==before:
                    k=i
                    break
            if not sepid:
                menu.InsertSeparator(k)
            else:
                item=wx.MenuItem(self.menus[menuname],wx.ID_SEPARATOR,kind=wx.ITEM_SEPARATOR)
                self.separators[sepid]=item
                
                self.menus[menuname].InsertItem(k,item)
                self.mapping[sepid]=menuname                

    def check(self,itemid,flag):
        """
        Method: check(itemid,flag)
        Created: 25.06.2005, KP
        Description: Check / uncheck a menu item
        """
        menu=self.mapping[itemid]
        self.menus[menu].Check(itemid,flag)
        
    def isChecked(self,itemid):
        """
        Method: isChecked(itemid)
        Created: 21.07.2005, KP
        Description: Return whether an item is checked
        """
        menu=self.mapping[itemid]
        self.menus[menu].IsChecked(itemid)
        
    def addSubMenu(self,menuname,submenuname,title,menuid):
        """
        Method: addSubMenu(menuname,submenuname,title,menuid)
        Created: 19.06.2005, KP
        Description: make a menu a submenu of another
        """
        self.menus[menuname].AppendMenu(menuid,title,self.menus[submenuname])
        
    def createMenu(self,menuname,menutitle,place=1,before=None):
        """
        Method: createMenu(name,title)
        Created: 19.06.2005, KP
        Description: Create a menu with a given id and title
        """
        self.menus[menuname]=wx.Menu()
        if not place:
            return
        if not before:
            self.menubar.Append(self.menus[menuname],menutitle)
        else:
            menu=self.menus[before]
            print "Searching for menu ",menu,   menu.GetTitle()
            for i in range(0,self.menubar.GetMenuCount()):
                gmenu=self.menubar.GetMenu(i)
                if gmenu==menu:
                    pos=i
                    break
            #pos=self.menubar.FindMenu(menu.GetTitle())
            
            self.menubar.Insert(pos,self.menus[menuname],menutitle)
            
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
#        if not self.itemBar:
#            if self.text:
#                flags=wx.TB_HORIZONTAL|wx.TB_TEXT
#            else:
#                flags=wx.TB_HORIZONTAL
#            self.itemBar = wx.ToolBar(self.visualizer.itemWin,-1,style=wx.TB_HORIZONTAL)
#            self.itemBar.SetToolBitmapSize((32,32))

        self.itemBar=self.visualizer.tb
        self.visualizer.tb.Bind(wx.EVT_TOOL,func,id=toolid)
    
        self.tools[toolid]=(name,bitmap,func)
        self.itemBar.DoAddTool(toolid,name,bitmap,kind=wx.ITEM_CHECK)
        self.itemBar.Realize()
       
    def restoreItemToolbar(self):
        """
        Method: restoreItemToolbar
        Created: 06.09.2005, KP
        Description: Restore the MIP items to the toolbar
        """ 
        if not self.visualizer:return
        self.itemBar=self.visualizer.tb
        
        for itemid in self.toolIds:
            name,bitmap,func=self.tools[itemid]
            self.itemBar.DoAddTool(itemid,name,bitmap,kind=wx.ITEM_CHECK)
            self.visualizer.tb.Bind(wx.EVT_TOOL,func,id=itemid)
        self.itemBar.Realize()
    
    def toggleTool(self,toolid,flag):
        """
        Method: toggleTool(toolid,flag)
        Created: 22.07.2005, KP
        Description: Toggle a toolbar item
        """
        self.visualizer.tb.ToggleTool(toolid,flag)

    def addMenuItem(self,menu,menuid,name,hlp=None,callback=None,before=None,check=0,checked=1):
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
        menu=self.menus[menu]
        if check:method=menu.AppendCheckItem
        else:method=menu.Append
        if not before:
            if not hlp:
                method(menuid,name)            # Find the position where the item belongs
            else:
                method(menuid,name,hlp)
        else:
            if check:method=menu.Insert
            else:method=menu.InsertCheckItem
            # Find the position where the item belongs
            k=0
            for i in range(0,999):
                if menu.FindItemByPosition(i).GetId()==before:
                    k=i
                    break
            if not hlp:
                menu.Insert(k,menuid,name)
            else:
                menu.Insert(k,menuid,name,hlp)
            
            
        if callback:
            wx.EVT_MENU(self.mainwin,menuid,callback)
        if check and checked:
            self.check(menuid,1)

        
        
    def disable(self,itemid):
        """
        Method: disable(itemid)
        Created: 29.05.2005, KP
        Description: Disable a menu item
        """
        self.menus[self.mapping[itemid]].Enable(itemid,0)
        
    def enable(self,itemid,callback=None):
        """
        Method: enable(itemid)
        Created: 29.05.2005, KP
        Description: Enable a menu item
        """
        self.menus[self.mapping[itemid]].Enable(itemid,1)
        if callback:
            wx.EVT_MENU(self.mainwin,itemid,callback)
            
    def removeMenu(self,menuname):
        """
        Method: removeMenu(menuname)
        Created: 19.06.2005, KP
        Description: Remove a menu
        """
        title=self.menus[menuname].GetTitle()
        for i in range(self.menubar.GetMenuCount()):
            menu=self.menubar.GetMenu(i)
            if menu.GetTitle()==title:
                self.menubar.Remove(i)
                break
        
            
    def remove(self,itemid):
        """
        Method: remove(itemid)
        Created: 19.06.2005, KP
        Description: Remove a menu item
        """
        menu=self.menus[self.mapping[itemid]]
        menu.Delete(itemid)
        self.mapping[itemid]=None
