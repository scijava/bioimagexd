# -*- coding: cp1252 -*-
"""
 Unit: TreeWidget.py
 Project: Selli
 Created: 03.11.2004
 Creator: KP
 Description:

 A widget for displaying a hierarchical tree of items.

 Modified: 03.11.2004 KP - Added methods for getting filenames of selected items
           08.11.2004 KP - Tree now selects dataset series instead of single 
                           datasets

 Selli includes the following persons:
 JH - Juha Hyytiäinen, juhyytia@st.jyu.fi
 JM - Jaakko Mäntymaa, jahemant@cc.jyu.fi
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 JV - Jukka Varsaluoma,varsa@st.jyu.fi

 Copyright (c) 2004 Selli Project.
"""
__author__ = "Selli Project <http://sovellusprojektit.it.jyu.fi/selli/>"
__version__ = "$Revision: 1.14 $"
__date__ = "$Date: 2005/01/13 14:52:39 $"

from wxPython.wx import *
import wx

class TreeWidget(wxPanel):
    def __init__(self,parent,callback=None):
        wxPanel.__init__(self,parent,-1)
        self.Bind(wx.EVT_SIZE,self.onSize)
        self.treeId=wxNewId()
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
        self.tree.SetItemImage(self.root,fldridx,which=wxTreeItemIcon_Normal)
        self.tree.SetItemImage(self.root,fldropenidx,which=wxTreeItemIcon_Expanded)

       
        self.lsmfiles=self.tree.AppendItem(self.root,"LSM Files")
        self.tree.SetPyData(self.lsmfiles,None)
        self.tree.SetItemImage(self.lsmfiles,fldridx,which=wxTreeItemIcon_Normal)
        self.tree.SetItemImage(self.lsmfiles,fldropenidx,which=wxTreeItemIcon_Expanded)

        self.vtifiles=self.tree.AppendItem(self.root,"Single Data Sets")
        self.tree.SetPyData(self.vtifiles,None)        
        self.tree.SetItemImage(self.vtifiles,fldridx,which=wxTreeItemIcon_Normal)
        self.tree.SetItemImage(self.vtifiles,fldropenidx,which=wxTreeItemIcon_Expanded)
        
        self.dufiles=self.tree.AppendItem(self.root,"Dataset series")
        self.tree.SetPyData(self.dufiles,None)        
        self.tree.SetItemImage(self.dufiles,fldridx,which=wxTreeItemIcon_Normal)
        self.tree.SetItemImage(self.dufiles,fldropenidx,which=wxTreeItemIcon_Expanded)

        self.tree.Expand(self.root)
        
    def onSize(self, event):
        w,h = self.GetClientSizeTuple()
        self.tree.SetDimensions(0,0,w,h)
    
    def hasItem(self,path):
        return path in self.items
    
    def addToTree(self,name,path,objtype,objs):
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
            self.tree.SetItemImage(item,fldropenidx,which=wxTreeItemIcon_Expanded)
        elif objtype=="du":
            item=self.dufiles
        else:
            item=self.vtifiles
        for obj in objs:
            added=self.tree.AppendItem(item,obj.getName())
            self.tree.SetPyData(added,obj)        
            self.tree.SetItemImage(added,fileidx,which=wxTreeItemIcon_Normal)
            #self.tree.SetItemImage(added,fldropenidx,which=wxTreeItemIcon_Expanded)

    def getSelectedDataUnits(self):
        items=self.tree.GetSelections()
        objs=[self.tree.GetPyData(x) for x in items]
        print "Selected items=",objs
        return objs

class LSMTree(wxTreeCtrl):
    def __init__(self,parent,id,callback=None):
        wxTreeCtrl.__init__(self,parent,id,wx.DefaultPosition,wx.DefaultSize,
        wx.TR_HAS_BUTTONS|wx.TR_MULTIPLE)
        self.Bind(wx.EVT_TREE_SEL_CHANGED,self.onSelectionChanged,id=self.GetId())
        self.callback=callback
        
    def onSelectionChanged(self,event):
        item=event.GetItem()
        obj=self.GetPyData(item)
        if obj:
            self.callback(obj)
