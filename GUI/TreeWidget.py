# -*- coding: cp1252 -*-
"""
 Unit: TreeWidget
 Project: BioImageXD
 Created: 10.01.2005
 Creator: KP
 Description:

 A widget for displaying a hierarchical tree of items.

 Modified: 10.01.2005 - Re-wrote old module with wxPython

 BioImageXD includes the following persons:
 DW - Dan White, dan@chalkie.org.uk
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 PK - Pasi Kankaanpää, ppkank@bytl.jyu.fi
 
 Copyright (c) 2005 BioImageXD Project.
"""
__author__ = "BioImageXD Project"
__version__ = "$Revision: 1.21 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"
import wx

class TreeWidget(wx.Panel):
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
        wx.Panel.__init__(self,parent,-1)
        self.Bind(wx.EVT_SIZE,self.onSize)
        self.treeId=wx.NewId()
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

       
        self.lsmfiles=self.tree.AppendItem(self.root,"LSM Files")
        self.tree.SetPyData(self.lsmfiles,None)
        self.tree.SetItemImage(self.lsmfiles,fldridx,which=wx.TreeItemIcon_Normal)
        self.tree.SetItemImage(self.lsmfiles,fldropenidx,which=wx.TreeItemIcon_Expanded)

        self.vtifiles=self.tree.AppendItem(self.root,"Single Data Sets")
        self.tree.SetPyData(self.vtifiles,None)        
        self.tree.SetItemImage(self.vtifiles,fldridx,which=wx.TreeItemIcon_Normal)
        self.tree.SetItemImage(self.vtifiles,fldropenidx,which=wx.TreeItemIcon_Expanded)
        
        self.dufiles=self.tree.AppendItem(self.root,"Dataset series")
        self.tree.SetPyData(self.dufiles,None)        
        self.tree.SetItemImage(self.dufiles,fldridx,which=wx.TreeItemIcon_Normal)
        self.tree.SetItemImage(self.dufiles,fldropenidx,which=wx.TreeItemIcon_Expanded)

        self.tree.Expand(self.root)
        
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
            item=self.lsmfiles
            item=self.tree.AppendItem(item,name)
            self.tree.SetPyData(item,None)        
            self.tree.SetItemImage(item,fldropenidx,which=wx.TreeItemIcon_Expanded)
        elif objtype=="du":
            item=self.dufiles
        else:
            item=self.vtifiles
        for obj in objs:
            added=self.tree.AppendItem(item,obj.getName())
            self.tree.SetPyData(added,obj)        
            self.tree.SetItemImage(added,fileidx,which=wx.TreeItemIcon_Normal)
            #self.tree.SetItemImage(added,fldropenidx,which=wx.TreeItemIcon_Expanded)

    def getSelectedDataUnits(self):
        """
        Method: getSelectedDataUnits()
        Created: 10.01.2005, KP
        Description: Returns the selected dataunits
        """            
        items=self.tree.GetSelections()
        objs=[self.tree.GetPyData(x) for x in items]
        print "Selected items=",objs
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
