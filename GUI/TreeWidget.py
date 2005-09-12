# -*- coding: iso-8859-1 -*-
"""
 Unit: TreeWidget
 Project: BioImageXD
 Created: 10.01.2005, KP
 Description:

 A widget for displaying a hierarchical tree of datasets

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
import Logging
import types
import messenger


class TreeWidget(wx.SashLayoutWindow):
    """
    Class: TreeWidget
    Created: 10.01.2005, KP
    Description: A panel containing thre tree
    """
    def __init__(self,parent):
        """
        Method: __init__
        Created: 10.01.2005, KP
        Description: Initialization
        """        
        #wx.Panel.__init__(self,parent,-1)
        wx.SashLayoutWindow.__init__(self,parent,-1)
        #self.sizer=wx.GridBagSizer()
        #self.Bind(wx.EVT_SIZE,self.onSize)
        self.treeId=wx.NewId()
        self.parent=parent
        self.tree = wx.TreeCtrl(self,self.treeId,style=wx.TR_HAS_BUTTONS|wx.TR_MULTIPLE)
        
        self.tree.Bind(wx.EVT_TREE_SEL_CHANGED,self.onSelectionChanged,id=self.tree.GetId())    
        self.items={}
    
        isz = (16,16)
        il = wx.ImageList(isz[0], isz[1])
        fldridx     = il.Add(wx.ArtProvider_GetBitmap(wx.ART_FOLDER,      wx.ART_OTHER, isz))
        fldropenidx = il.Add(wx.ArtProvider_GetBitmap(wx.ART_FILE_OPEN,   wx.ART_OTHER, isz))
        fileidx     = il.Add(wx.ArtProvider_GetBitmap(wx.ART_REPORT_VIEW, wx.ART_OTHER, isz))
        
        self.tree.SetImageList(il)
        self.il=il
    
        self.root=self.tree.AddRoot("Data Sets")
        self.tree.SetPyData(self.root,"1")
        self.tree.SetItemImage(self.root,fldridx,which=wx.TreeItemIcon_Normal)
        self.tree.SetItemImage(self.root,fldropenidx,which=wx.TreeItemIcon_Expanded)

        self.lsmfiles=None
        self.leicafiles=None
        self.bxdfiles=None
        
        self.tree.Bind(wx.EVT_RIGHT_DOWN,self.onRightClick)
        self.Bind(wx.EVT_RIGHT_DOWN,self.onRightClick)
        self.ID_CLOSE_DATAUNIT=wx.NewId()
        self.menu=wx.Menu()
        self.tree.SetHelpText("Files that you open appear in this tree.")        
       
        item = wx.MenuItem(self.menu,self.ID_CLOSE_DATAUNIT,"Close dataset")
        self.tree.Bind(wx.EVT_MENU,self.onCloseDataset,id=self.ID_CLOSE_DATAUNIT)
        self.Bind(wx.EVT_MENU,self.onCloseDataset,id=self.ID_CLOSE_DATAUNIT)
        self.menu.AppendItem(item)
        
        #self.switchPanel=wx.Panel(self,-1,style=wx.RAISED_BORDER)
#        self.switchBtn=wx.Button(self,-1,"Switch dataset")
            
        #self.sizer.Add(self.tree,(0,0),flag=wx.EXPAND|wx.ALL)
#        self.sizer.Add(self.switchBtn,(1,0),flag=wx.EXPAND|wx.ALL)
        #self.SetSizer(self.sizer)
        #self.SetAutoLayout(1)
        #self.sizer.Fit(self)
            
    def onRightClick(self,event):
        """
        Method: onRightClick
        Created: 21.07.2005
        Description: Method that is called when the right mouse button is
                     pressed down on this item
        """      
        pt = event.GetPosition()
        item, flags = self.tree.HitTest(pt)
        if not item:
            Logging.info("No item to select",kw="ui")
            return
        self.tree.SelectItem(item)
        self.selectedItem=item
        self.PopupMenu(self.menu,event.GetPosition())   
 
    def onCloseDataset(self,event):
        """
        Method: onCloseDataset
        Created: 21.07.2005, KP
        Description: Method to close a dataset
        """        
        item=self.selectedItem
        obj=self.tree.GetPyData(item)
        if obj!="1":
            messenger.send(None,"delete_dataset",obj)
            self.tree.Delete(item)
            
        else:
            Logging.info("Cannot delete top-level entry",kw="ui")
            
    def onSize(self, event):
        """
        Method: onSize()
        Created: 10.01.2005, KP
        Description: Callback that modifies the tree size according to
                     own changes in size
        """                
        w,h = self.GetClientSizeTuple()
        self.tree.SetDimensions(0,0,w,h)
        
    def getSelectionContainer(self):
        """
        Method: getSelectionContainer
        Created: 11.09.2005, KP
        Description: Return the dataset that contains a channel
        """         
        selections=self.tree.GetSelections()
        dataunits=[]
        items=[]
        for i in selections:
            parent=self.tree.GetItemParent(i)
            data=self.tree.GetPyData(parent)
            if data =="2":
                item,cookie=self.tree.GetFirstChild(parent)
            else:
                item,cookie=self.tree.GetFirstChild(parent)
            while item.IsOk():
                data=self.tree.GetPyData(item)
                dataunits.append(data)
                items.append(item)
                item,cookie=self.tree.GetNextChild(item,cookie)
                
        return dataunits,items
        
    def markRed(self,items,appendchar=""):
        """
        Method: markRed(items)
        Created: 11.09.2005, KP
        Description: Mark given items red
        """                
        for item in items:
            if appendchar!="":
                txt=self.tree.GetItemText(item)
                self.tree.SetItemText(item,txt+appendchar)
            self.tree.SetItemTextColour(item,(255,0,0))
        
        
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
            objtype     Type of the object (lsm, bxd)
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
                self.tree.SetPyData(self.lsmfiles,"1")
                self.tree.SetItemImage(self.lsmfiles,fldridx,which=wx.TreeItemIcon_Normal)
                self.tree.SetItemImage(self.lsmfiles,fldropenidx,which=wx.TreeItemIcon_Expanded)
            item=self.lsmfiles
            self.tree.Expand(item)            
            item=self.tree.AppendItem(item,name)
            self.tree.Expand(item)

            self.tree.Expand(item)
            self.tree.SetPyData(item,"2")        
            self.tree.SetItemImage(item,fldropenidx,which=wx.TreeItemIcon_Expanded)
        elif objtype=="txt":
            if not self.leicafiles:
                self.leicafiles=self.tree.AppendItem(self.root,"Leica Files")
                self.tree.SetPyData(self.leicafiles,"1")
                self.tree.SetItemImage(self.leicafiles,fldridx,which=wx.TreeItemIcon_Normal)
                self.tree.SetItemImage(self.leicafiles,fldropenidx,which=wx.TreeItemIcon_Expanded)        

            item=self.leicafiles
            self.tree.Expand(item)
            item=self.tree.AppendItem(item,name)
            self.tree.Expand(item)
            
            self.tree.SetPyData(item,"2")
            self.tree.SetItemImage(item,fldropenidx,which=wx.TreeItemIcon_Expanded)
        elif objtype=="bxd":
            if not self.bxdfiles:
                self.bxdfiles=self.tree.AppendItem(self.root,"Dataset series")
                self.tree.SetPyData(self.bxdfiles,"1")        
                self.tree.SetItemImage(self.bxdfiles,fldridx,which=wx.TreeItemIcon_Normal)
                self.tree.SetItemImage(self.bxdfiles,fldropenidx,which=wx.TreeItemIcon_Expanded)

            item=self.bxdfiles
            self.tree.Expand(item)
        
        self.tree.Expand(item)
        for obj in objs:
            added=self.tree.AppendItem(item,obj.getName())

            self.tree.SetPyData(added,obj)        
            self.tree.SetItemImage(added,fileidx,which=wx.TreeItemIcon_Normal)
            #self.tree.SetItemImage(added,fldropenidx,which=wx.TreeItemIcon_Expanded)
            self.tree.EnsureVisible(added)
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
        
    def onSelectionChanged(self,event=None):
        """
        Method: onSelectionChanged
        Created: 10.01.2005, KP
        Description: A event handler called when user selects and item.
        """        
        if event:
            self.item=event.GetItem()
            wx.FutureCall(10,self.onSelectionChanged)
            return
        item=self.item
        print "item=",item
        obj=self.tree.GetPyData(item)
        if obj and type(obj)!=types.StringType:
            messenger.send(None,"tree_selection_changed",obj)        
