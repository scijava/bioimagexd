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
import time
import scripting as bxd
import Command


class TreeWidget(wx.SashLayoutWindow):
    """
    Created: 10.01.2005, KP
    Description: A panel containing thre tree
    """
    def __init__(self,parent):
        """
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
        
        self.lastobj = None
        self.tree.Bind(wx.EVT_TREE_SEL_CHANGED,self.onSelectionChanged,id=self.tree.GetId())    
        self.tree.Bind(wx.EVT_TREE_ITEM_ACTIVATED,self.onActivateItem,id=self.tree.GetId())
        self.items={}
        self.greenitems=[]
        self.yellowitems=[]
        self.dataUnitToPath={}
        
        isz = (16,16)
        il = wx.ImageList(isz[0], isz[1])
        fldridx     = il.Add(wx.ArtProvider_GetBitmap(wx.ART_FOLDER,      wx.ART_OTHER, isz))
        fldropenidx = il.Add(wx.ArtProvider_GetBitmap(wx.ART_FILE_OPEN,   wx.ART_OTHER, isz))
        fileidx     = il.Add(wx.ArtProvider_GetBitmap(wx.ART_REPORT_VIEW, wx.ART_OTHER, isz))
        
        self.tree.SetImageList(il)
        self.il=il
    
        self.root=self.tree.AddRoot("Datasets")
        self.tree.SetPyData(self.root,"1")
        self.tree.SetItemImage(self.root,fldridx,which=wx.TreeItemIcon_Normal)
        self.tree.SetItemImage(self.root,fldropenidx,which=wx.TreeItemIcon_Expanded)

        self.lsmfiles=None
        self.leicafiles=None
        self.bxdfiles=None
        self.oiffiles=None
        self.bioradfiles=None
        self.interfilefiles=None
        
        self.dataUnitItems=[]
        
        self.itemColor=(0,0,0)
        
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
        Created: 10.01.2005, KP
        Description: Callback that modifies the tree size according to
                     own changes in size
        """                
        w,h = self.GetClientSizeTuple()
        self.tree.SetDimensions(0,0,w,h)
        
    def getSelectionContainer(self):
        """
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
                item=self.tree.GetNextSibling(item)
        
        return dataunits,items
        
        
    def markGreen(self,items):
        """
        Created: 16.09.2005, KP
        Description: Mark given items green and set the old green item to default color
        """                    
        if self.greenitems:
            for item in self.greenitems:
                self.tree.SetItemBold(item,0)
            pass
        self.greenitems=items    
        for item in items:
            #if not item.IsOk():raise "Item not ok"
            #print "Marking ",item,"green"
            #self.itemColor=self.tree.GetItemTextColour(item)
            self.tree.SetItemBold(item,1)
            
    def markYellow(self,items):
        """
        Created: 16.09.2005, KP
        Description: Mark given items yellow and set the old yellow item to default color
        """        
        if self.yellowitems:
            for item in self.yellowitems:
                self.tree.SetItemBackgroundColour(item,(255,255,255))
            pass
        self.yellowitems=items    
        for item in items:
            #self.itemColor=self.tree.GetItemTextColour(item)
            self.tree.SetItemBackgroundColour(item,(255,255,0))    
        
    def markRed(self,items,appendchar=""):
        """
        Created: 11.09.2005, KP
        Description: Mark given items red
        """                
        for item in items:
            if appendchar!="":
                txt=self.tree.GetItemText(item)
                if txt[-len(appendchar):]!=appendchar:
                    self.tree.SetItemText(item,txt+appendchar)
            self.tree.SetItemTextColour(item,(255,0,0))

    def markBlue(self,items,appendchar=""):
        """
        Created: 15.08.2006, KP
        Description: Mark given items blue
        """                
        for item in items:
            if appendchar!="":
                txt=self.tree.GetItemText(item)
                if txt[-len(appendchar):]!=appendchar:
                    self.tree.SetItemText(item,txt+appendchar)
            self.tree.SetItemTextColour(item,(0,0,255))

        
    def hasItem(self,path):
        """
        Created: 10.01.2005, KP
        Description: Returns whether the tree has a specified item
        """            
        return path in self.items
        
    def getItemNames(self):
        """
        Created: 15.08.2006, KP
        Description: Return the names of the dataunits in the tree
        """
        return self.items.keys()
    
    def addToTree(self,name,path,objtype,objs):
        """
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
        
        for i in objs:
            self.dataUnitToPath[i]=path

        if objtype=="lsm":
        
            if not self.lsmfiles:
                self.lsmfiles=self.tree.AppendItem(self.root,"LSM files")
                self.tree.SetPyData(self.lsmfiles,"1")
                self.tree.SetItemImage(self.lsmfiles,fldridx,which=wx.TreeItemIcon_Normal)
                self.tree.SetItemImage(self.lsmfiles,fldropenidx,which=wx.TreeItemIcon_Expanded)
        
            item=self.lsmfiles
            self.tree.Expand(item)            
            item=self.tree.AppendItem(item,name)
            self.tree.Expand(item)

#            self.tree.Expand(item)
            self.tree.SetPyData(item,"2")        
            self.tree.SetItemImage(item,fldropenidx,which=wx.TreeItemIcon_Expanded)
        
        elif objtype=="txt":
            if not self.leicafiles:
                self.leicafiles=self.tree.AppendItem(self.root,"Leica files")
                self.tree.SetPyData(self.leicafiles,"1")
                self.tree.SetItemImage(self.leicafiles,fldridx,which=wx.TreeItemIcon_Normal)
                self.tree.SetItemImage(self.leicafiles,fldropenidx,which=wx.TreeItemIcon_Expanded)        

            item=self.leicafiles
            self.tree.Expand(item)
            item=self.tree.AppendItem(item,name)
            self.tree.Expand(item)
            
            self.tree.SetPyData(item,"2")
            self.tree.SetItemImage(item,fldropenidx,which=wx.TreeItemIcon_Expanded)
        elif objtype=="oif":
            if not self.oiffiles:
                self.oiffiles=self.tree.AppendItem(self.root,"Olympus files")
                self.tree.SetPyData(self.oiffiles,"1")
                self.tree.SetItemImage(self.oiffiles,fldridx,which=wx.TreeItemIcon_Normal)
                self.tree.SetItemImage(self.oiffiles,fldropenidx,which=wx.TreeItemIcon_Expanded)
            item=self.oiffiles
            self.tree.Expand(item)
            item=self.tree.AppendItem(item,name)
            self.tree.Expand(item)
            self.tree.SetPyData(item,"2")
            self.tree.SetItemImage(item,fldropenidx,which=wx.TreeItemIcon_Expanded)
        elif objtype=="pic":
            if not self.bioradfiles:
                self.bioradfiles=self.tree.AppendItem(self.root,"BioRad files")
                self.tree.SetPyData(self.bioradfiles,"1")
                self.tree.SetItemImage(self.bioradfiles,fldridx,which=wx.TreeItemIcon_Normal)
                self.tree.SetItemImage(self.bioradfiles,fldropenidx,which=wx.TreeItemIcon_Expanded)
            item=self.bioradfiles
            self.tree.Expand(item)
        elif objtype == "hdr":
            if not self.interfilefiles:
                self.interfilefiles = self.tree.AppendItem(self.root, "Interfile files")
                self.tree.SetPyData(self.interfilefiles, "1")
                self.tree.SetItemImage(self.interfilefiles, fldridx, which=wx.TreeItemIcon_Normal)
                self.tree.SetItemImage(self.interfilefiles,fldropenidx,which=wx.TreeItemIcon_Expanded)
            item = self.interfilefiles
            self.tree.Expand(item)
        elif objtype=="bxd":
            if not self.bxdfiles:
                self.bxdfiles=self.tree.AppendItem(self.root,"BioImageXD files")
                self.tree.SetPyData(self.bxdfiles,"1")        
                self.tree.SetItemImage(self.bxdfiles,fldridx,which=wx.TreeItemIcon_Normal)
                self.tree.SetItemImage(self.bxdfiles,fldropenidx,which=wx.TreeItemIcon_Expanded)

            item=self.bxdfiles
            self.tree.Expand(item)
        
        self.tree.Expand(item)
        selected=0
        for obj in objs:
            
            added=self.tree.AppendItem(item,obj.getName())
                
            resampledims=obj.dataSource.getResampleDimensions()
            if resampledims and resampledims != (0,0,0):
                self.markRed([added],"*")
            self.tree.SetPyData(added,obj)        
            self.tree.SetItemImage(added,fileidx,which=wx.TreeItemIcon_Normal)
            #self.tree.SetItemImage(added,fldropenidx,which=wx.TreeItemIcon_Expanded)
            self.tree.EnsureVisible(added)
            self.dataUnitItems.append(added)
            
            if len(self.items.keys())==1 and not selected:
                self.tree.SelectItem(added,1)
                selected=1
                print "obj=",obj
                messenger.send(None,"tree_selection_changed",obj)            
            
        self.tree.Expand(self.root)

    def getSelectedDataUnits(self):
        """
        Created: 10.01.2005, KP
        Description: Returns the selected dataunits
        """            
        items=self.tree.GetSelections()
        objs=[self.tree.GetPyData(x) for x in items]
        return objs
        
    def getSelectedPaths(self):
        """
        Created: 23.10.2006, KP
        Description: Return the paths of the selected dataunits
        """
        
        objs = self.getSelectedDataUnits()
        return [self.dataUnitToPath[x] for x in objs]
        

    def onActivateItem(self,event=None):
        """
        Created: 03.04.2006, KP
        Description: A event handler called when user double clicks an item
        """      
        item = event.GetItem()
        if not item.IsOk():
            return
        obj=self.tree.GetPyData(item)
        self.item = item
        messenger.send(None,"tree_selection_changed",obj)
        self.markGreen([item])
        
        event.Skip()
        
    def onSelectionChanged(self,event=None):
        """
        Method: onSelectionChanged
        Created: 10.01.2005, KP
        Description: A event handler called when user selects and item.
        """      
        item=event.GetItem()
        #items=self.tree.GetSelections()
        #item=items[-1]
        if not item.IsOk():
            return

      
        
        obj=self.tree.GetPyData(item)
        self.item=item
        if obj and type(obj)!=types.StringType:
            if self.lastobj != obj:
                print "Last obj=",self.lastobj,"!=",obj
                Logging.info("Switching to ",obj)
                messenger.send(None,"tree_selection_changed",obj)        
                self.markGreen([item])        
                self.lastobj = obj
        #event.Skip()

    def unselectAll(self):
        """
        Method: unselectAll
        Created: 16.07.2006, KP
        Description: Unselect everything in the tree
        """
        self.tree.UnselectAll()
        
    def getChannelsByName(self, unit, channels):
        """
        Created: 16.07.2006, KP
        Description: Return items in the tree by their names
        """   
        return self.selectByName(unit, channels, dontSelect=1)
        
    def selectChannelsByNumber(self, unit, numbers):
        """
        Created: 06.09.2006, KP
        Description: Select channels with the given numhers
        """
        n=-1
        ret=[]
        for item in self.dataUnitItems:
            obj = self.tree.GetPyData(item)
            if unit == self.dataUnitToPath[obj]:
                n+=1
            if n in numbers:
                ret.append(obj)
        return ret
    def selectChannelsByName(self, unit, channels, dontSelect=0):
        """
        Created: 16.07.2006, KP
        Description: Select items in the tree by their names
        """   
        ret=[]
        for item in self.dataUnitItems:
            obj = self.tree.GetPyData(item)
            #print "obj=",obj.getName(),"in channels=",(obj.getName() in channels)
            if obj.getName() in channels and unit == self.dataUnitToPath[obj]:
                if not dontSelect:
                    self.tree.SelectItem(item)
                #print "FOUND",obj
                ret.append(obj)
        #print "RETURNING",ret
        return ret
