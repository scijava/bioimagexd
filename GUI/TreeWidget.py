# -*- coding: iso-8859-1 -*-
"""
 Unit: TreeWidget
 Project: BioImageXD
 Created: 10.01.2005
 Creator: KP
 Description:

 A widget for displaying a hierarchical tree of items.

 Modified: 10.01.2005 - Re-wrote old module with wxPython

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
__version__ = "$Revision: 1.21 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"
import wx

class TreeWidget(wx.SashLayoutWindow):
    """
    Class: TreeWidget
    Created: 10.01.2005, KP
    Description: A panel containing thre tree
    """
    def __init__(self,parent,callback=None):
        """
        Method: __init__
        Created: 10.01.2005, KP
        Description: Initialization
        """        
        #wx.Panel.__init__(self,parent,-1)
        wx.SashLayoutWindow.__init__(self,parent,-1)
        #self.Bind(wx.EVT_SIZE,self.onSize)
        self.treeId=wx.NewId()
        self.parent=parent
        self.tree = LSMTree(self,self.treeId,callback)
    
        self.items={}
    
        isz = (16,16)
        il = wx.ImageList(isz[0], isz[1])
        fldridx     = il.Add(wx.ArtProvider_GetBitmap(wx.ART_FOLDER,      wx.ART_OTHER, isz))
        fldropenidx = il.Add(wx.ArtProvider_GetBitmap(wx.ART_FILE_OPEN,   wx.ART_OTHER, isz))
        fileidx     = il.Add(wx.ArtProvider_GetBitmap(wx.ART_REPORT_VIEW, wx.ART_OTHER, isz))
        
        self.tree.SetImageList(il)
        self.il=il
    
        self.root=self.tree.AddRoot("Data Sets")
        self.tree.SetPyData(self.root,None)
        self.tree.SetItemImage(self.root,fldridx,which=wx.TreeItemIcon_Normal)
        self.tree.SetItemImage(self.root,fldropenidx,which=wx.TreeItemIcon_Expanded)

        self.lsmfiles=None
        self.leicafiles=None
        self.dufiles=None
        
    def onSize(self, event):
        """
        Method: onSize()
        Created: 10.01.2005, KP
        Description: Callback that modifies the tree size according to
                     own changes in size
        """                
        w,h = self.GetClientSizeTuple()
        self.tree.SetDimensions(0,0,w,h)
    
    def hasItem(self,path):
        """
        Method: hasItem(path)
        Created: 10.01.2005, KP
        Description: Returns whether the tree has a specified item
        """            
        return path in self.items
    
    def addToTree(self,name,path,objtype,objs):
        """
        Method: addToTree(name, path, objectype, objs)
        Created: 10.01.2005, KP
        Description: Add item to the tree
        Parameters:
            name        Name of the item
            path        Path of the item
            objtype     Type of the object (lsm, du)
            objs        objects to add
        """            
        item=None
        isz = (16,16)
        il = wx.ImageList(isz[0], isz[1])
        fldridx     = il.Add(wx.ArtProvider_GetBitmap(wx.ART_FOLDER,      wx.ART_OTHER, isz))
        fldropenidx = il.Add(wx.ArtProvider_GetBitmap(wx.ART_FILE_OPEN,   wx.ART_OTHER, isz))
        fileidx     = il.Add(wx.ArtProvider_GetBitmap(wx.ART_REPORT_VIEW, wx.ART_OTHER, isz))

        self.items[path]=1
        
        if objtype=="lsm":
            if not self.lsmfiles:
                self.lsmfiles=self.tree.AppendItem(self.root,"LSM Files")
                self.tree.SetPyData(self.lsmfiles,None)
                self.tree.SetItemImage(self.lsmfiles,fldridx,which=wx.TreeItemIcon_Normal)
                self.tree.SetItemImage(self.lsmfiles,fldropenidx,which=wx.TreeItemIcon_Expanded)
            item=self.lsmfiles
            item=self.tree.AppendItem(item,name)
            self.tree.SetPyData(item,None)        
            self.tree.SetItemImage(item,fldropenidx,which=wx.TreeItemIcon_Expanded)
        elif objtype=="txt":
            if not self.leicafiles:
                self.leicafiles=self.tree.AppendItem(self.root,"Leica Files")
                self.tree.SetPyData(self.leicafiles,None)
                self.tree.SetItemImage(self.leicafiles,fldridx,which=wx.TreeItemIcon_Normal)
                self.tree.SetItemImage(self.leicafiles,fldropenidx,which=wx.TreeItemIcon_Expanded)        

            item=self.leicafiles
            item=self.tree.AppendItem(item,name)
            self.tree.SetPyData(item,None)
            self.tree.SetItemImage(item,fldropenidx,which=wx.TreeItemIcon_Expanded)
        elif objtype=="du":
            if not self.dufiles:
                self.dufiles=self.tree.AppendItem(self.root,"Dataset series")
                self.tree.SetPyData(self.dufiles,None)        
                self.tree.SetItemImage(self.dufiles,fldridx,which=wx.TreeItemIcon_Normal)
                self.tree.SetItemImage(self.dufiles,fldropenidx,which=wx.TreeItemIcon_Expanded)

            item=self.dufiles

        for obj in objs:
            added=self.tree.AppendItem(item,obj.getName())
            self.tree.SetPyData(added,obj)        
            self.tree.SetItemImage(added,fileidx,which=wx.TreeItemIcon_Normal)
            #self.tree.SetItemImage(added,fldropenidx,which=wx.TreeItemIcon_Expanded)
        self.tree.Expand(self.root)

    def getSelectedDataUnits(self):
        """
        Method: getSelectedDataUnits()
        Created: 10.01.2005, KP
        Description: Returns the selected dataunits
        """            
        items=self.tree.GetSelections()
        objs=[self.tree.GetPyData(x) for x in items]
        return objs

class LSMTree(wx.TreeCtrl):
    """
    Class: LSMTree
    Created: 10.01.2005, KP
    Description: A tree inherited from wx.TreeCtrl
    """            
    def __init__(self,parent,id,callback=None):
        """
        Method: __init__
        Created: 10.01.2005, KP
        Description: Initialization
        """                
        wx.TreeCtrl.__init__(self,parent,id,wx.DefaultPosition,wx.DefaultSize,
        wx.TR_HAS_BUTTONS|wx.TR_MULTIPLE)
        self.Bind(wx.EVT_TREE_SEL_CHANGED,self.onSelectionChanged,id=self.GetId())
        self.callback=callback
        
    def onSelectionChanged(self,event):
        """
        Method: onSelectionChanged
        Created: 10.01.2005, KP
        Description: A event handler called when user selects and item.
        """        
        item=event.GetItem()
        obj=self.GetPyData(item)
        if obj:
            self.callback(obj)
