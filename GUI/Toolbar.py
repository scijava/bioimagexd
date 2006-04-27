# -*- coding: iso-8859-1 -*-

"""
 Unit: Toolbar
 Project: BioImageXD
 Created: 03.02.2005, KP
 Description:

 A resizing toolbar

 Copyright (C) 2006  BioImageXD Project
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


import  wx
import wx.lib.buttons as buttons

class Toolbar(wx.Panel):
    def __init__(self,parent, visualizer,wid, pos = wx.DefaultPosition, size = wx.DefaultSize,style = wx.TB_HORIZONTAL | wx.NO_BORDER, name = ""):
        wx.Panel.__init__(self,parent,wid,pos,size,style)        
        #self.SetBackgroundColour((255,255,0))
        self.toolSize = (32,32)
        self.visualizer = visualizer
        self.parent = parent
        self.toolSeparation = 4
        self.sizer = wx.GridBagSizer(self.toolSeparation,self.toolSeparation)
        self.x=0
        self.sizes=[]
        self.rowsizers=[]
        self.ctrlToRow={}
        self.y=0
        self.ctrls = []
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.Bind(wx.EVT_SIZE,self.OnSize)
        
    def OnSize(self,evt):
        
        #if self.sizer.GetMinSize()[0]>evt.GetSize()[0]:
        if 1:
            self.ReOrderItems(evt.GetSize()[0])
            
            x=self.GetSize()[0]
            print "self.y=",self.y
            n=self.y+1
            print "n=",n
            print "self.getsize()[1]=",self.GetSize()[1]
            y=44*n
            self.parent.SetDefaultSize((x,y))
            print "Setting defaultsize to ",(x,y)
            #self.visualizer.OnSize(None)
        
    def ReOrderItems(self,tgtsize=None):
        for ctrl in self.ctrls:
            if ctrl in self.ctrlToRow:
                sizer = self.ctrlToRow[ctrl]
                if sizer:
                    if sizer in self.rowsizers:
                        #print "Detaching rowsizer..."
                        self.sizer.Detach(sizer)
                        self.rowsizers.remove(sizer)
                    #print "Detaching ",ctrl
                    sizer.Detach(ctrl)
                    self.ctrlToRow[ctrl]=None
        self.rowsizers = []
        print "Reordering...",tgtsize

        if not tgtsize:
            tgtsize = self.parent.GetSize()
            
        self.x=0
        self.y=0
        tgs=tgtsize
        ms  = 0
        rowsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(rowsizer,(self.y,0))                

        self.rowsizers.append(rowsizer)
        for i,ctrl in enumerate(self.ctrls):
            print "ms=",ms,"tgtsize=",tgtsize,"ctrl size=",ctrl.GetSize()
            if ms+self.sizes[i] > tgtsize:
                print "Switching row...",self.y
                self.x=0                
                self.y+=1
                tgtsize=(self.y+1)*tgs
                rowsizer = wx.BoxSizer(wx.HORIZONTAL)
                self.sizer.Add(rowsizer,(self.y,0))                
                self.rowsizers.append(rowsizer)
            #print "Adding",ctrl," to ",self.y,self.x
            rowsizer.Add(ctrl)
            rowsizer.AddSpacer((self.toolSeparation,0))
            #rowsizer.Insert(self.toolSeparation,self.toolSeparation,0)
            self.ctrlToRow[ctrl] = rowsizer
            self.x+=1
            ms += self.sizes[i] + self.toolSeparation
        self.Layout()
        self.sizer.Fit(self)
        
    def Realize(self):
        self.Refresh()
        self.Layout()                
        
    def AddControl(self,ctrl):
        self.ctrls.append(ctrl)
        self.sizes.append(ctrl.GetSize()[0])
        #self.sizer.Add(ctrl,(self.y,self.x))
        self.x+=1
        print "Added ",ctrl
        
    def AddSimpleTool(self, id, bitmap, shortHelpString = '',
                      longHelpString = '',
                      isToggle = 0):
        if not isToggle:
            #btn = wx.BitmapButton(self,id,bitmap,size=self.toolSize)
            btn = buttons.GenBitmapButton(self,id,bitmap,style = wx.BORDER_NONE,size=self.toolSize)
            
        else:
            btn = buttons.GenBitmapToggleButton(self,id,bitmap,size=(-1,self.toolSize[1]))
        btn.SetToolTipString(longHelpString)            
        #self.sizer.Add(btn,(self.y,self.x))
        self.ctrls.append(btn)
        self.sizes.append(btn.GetSize()[0])
        self.x+=1
        
        
    def AddSeparator(self):
        sep = wx.Panel(self,-1,size=(2,32),style = wx.SUNKEN_BORDER)
        #self.sizer.Add(sep, (self.y,self.x))
        self.x+=1
        self.ctrls.append(sep)
        self.sizes.append(sep.GetSize()[0])

    def GetToolSeparation(self):
        return self.toolSeparation

        
        
    def GetToolSize(self):
        return self.toolSize
        
    def SetToolBitmapSize(self,size):
        self.toolSize = size
