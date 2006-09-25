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

class ToolCommandEvent(wx.PyCommandEvent):
    def __init__(self,eventType, eid, isdown):
        wx.PyCommandEvent.__init__(self,eventType,eid)
        self.isdown = isdown
        
    def IsChecked(self):
        return self.isdown

class Toolbar(wx.Panel):
    """
    Class: Toolbar
    Created: 27.04.2006, KP
    Description: A toolbar that can change it's amount of tool rows based on it's size
    """        
    def __init__(self,parent,wid, pos = wx.DefaultPosition, size = wx.DefaultSize,style = wx.TB_HORIZONTAL | wx.NO_BORDER, name = ""):
        """
        Method: __init__
        Created: 27.04.2006, KP
        Description: Initialize the toolbar
        """    
        wx.Panel.__init__(self,parent,wid,pos,size,style)        
        #self.SetBackgroundColour((255,255,0))
        self.toolSize = (32,32)
        self.parent = parent
        self.x=0
        self.ctrlToRow={}
        self.toolSeparation = 4
        self.sizer = wx.GridBagSizer(self.toolSeparation,self.toolSeparation)
        self.sizes=[]
        self.rowsizers=[]
        self.oldLayout=[]
        self.ctrls = []
        self.idToTool={}
        self.minSize = 999999
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.Bind(wx.EVT_SIZE,self.OnSize)
        
    def OnSize(self,evt):
        """
        Created: 27.04.2006, KP
        Description: Event handler for size events
        """ 
        size = evt.GetSize()
        layout = self.getLayout(size[0])
        self.createRows(layout)

        #print "curr layout=",len(layout),"old=",len(self.oldLayout)
        if layout != self.oldLayout:            
            self.ReOrderItems2(layout, size[0])            
            self.oldLayout = layout
            
            x=self.GetSize()[0] 
            y=44*len(layout)
            print "x=",x,"y=",y
            self.parent.SetDefaultSize((x,y))
            self.sizer.Fit(self)                
            self.Layout()
            self.parent.Layout()
            
        
            
    def ReOrderItems2(self, layout, width):
        """
        Created: 28.07.2006, KP
        Description: Re-order the items based on a given layout
        """ 
        for sizer in self.rowsizers:
            try:
                while sizer.GetItem(0):
                    sizer.Detach(0)
            except:
                pass
        ms = 0
        for y,row in enumerate(layout):
            self.x =0
            for i,ctrl in enumerate(row):            
                self.rowsizers[y].Add(ctrl)
                self.rowsizers[y].AddSpacer((self.toolSeparation,0))                
                self.ctrlToRow[ctrl] = self.rowsizers[y]
                ms += self.sizes[i] + self.toolSeparation
        self.minSize = ms
        
    def getLayout(self, width):
        """
        Created: 28.07.2006, KP
        Description: Get the optimal layout for current controls and given width
        """   
        ctrls=[]
        curr=[]
        ms=0
        #print "getting layout for width=",width
        
        for i,ctrl in enumerate(self.ctrls):            
            #print "ms=",ms,"size=",self.sizes[i],"tgtsize=",tgtsize            
            if ms+self.toolSeparation+self.sizes[i] > width:
                ctrls.append(curr)        
                curr=[]
                ms = 0
            curr.append(ctrl)
            ms += self.sizes[i] + self.toolSeparation
        if curr not in ctrls:
            ctrls.append(curr)
        n=0
        for i in ctrls:
            n+=len(i)
        if n!=len(self.ctrls):
            print "\n\n\n****** Lengths do not match, only ",n,"controls placed, there are",len(self.ctrls)
        return ctrls
        
        
    def EnableTool(self,toolid,flag):
        """
        Created: 27.04.2006, KP
        Description: Enable / Disable a tool
        """       
        self.idToTool[toolid].Enable(flag)
        
    def createRows(self, layout):
        """
        Created: 28.07.2006, KP
        Description: Create enough rows to fit a given layout
        """   
        for y in range(len(layout)):
            if len(self.rowsizers) <=y:
                rowsizer = wx.BoxSizer(wx.HORIZONTAL)            
                self.rowsizers.append(rowsizer)
                print "Adding rowsizer to",y,0
                self.sizer.Add(rowsizer,(y,0),flag=wx.EXPAND|wx.LEFT|wx.RIGHT)
        
    def Realize(self):
        """
        Created: 27.04.2006, KP
        Description: Render the toolbar
        """          
        w=self.GetSize()[0]
        layout = self.getLayout(w)
        print "Layout for width",w,"has",len(layout),"rows"
        self.createRows(layout)        
        self.ReOrderItems2(layout, w)            
#        self.ReOrderItems()
        self.Refresh()
        
    def DeleteTool(self,toolid):
        """
        Created: 27.04.2006, KP
        Description: Delete a tool 
        """
        ctrl = self.idToTool[toolid]
        self.ctrls.remove(ctrl)
        del self.idToTool[toolid]
        if ctrl in self.ctrlToRow:
            sizer = self.ctrlToRow[ctrl]
            sizer.Detach(ctrl)
            ctrl.Show(0)
            sizer.Remove(ctrl) 
            
        w=self.GetSize()[0]
        layout = self.getLayout(w)        
        self.ReOrderItems2(layout, w)            
            
        #self.ReOrderItems()
        
        
    def AddControl(self,ctrl):
        """
        Created: 27.04.2006, KP
        Description: Add a control to the toolbar
        """          
        self.ctrls.append(ctrl)
        self.idToTool[ctrl.GetId()] = ctrl
        self.sizes.append(ctrl.GetSize()[0])
        #self.sizer.Add(ctrl,(self.y,self.x))
        self.x+=1
        
    def onToolButton(self,evt):
        """
        Created: 27.04.2006, KP
        Description: A method for passing the events forward in event chain
        """        
        nevt = ToolCommandEvent(wx.EVT_TOOL.evtType[0],evt.GetId(),evt.GetIsDown())        
        self.GetEventHandler().ProcessEvent(nevt)
        
        
        
    def AddSimpleTool(self, wid, bitmap, shortHelpString = '',longHelpString = '', isToggle = 0):
        """
        Created: 27.04.2006, KP
        Description: A method for adding a tool to the toolbar
        """                            
        if not isToggle:
            #btn = wx.BitmapButton(self,id,bitmap,size=self.toolSize)
            btn = buttons.GenBitmapButton(self,wid,bitmap,style = wx.BORDER_NONE,size=self.toolSize)            
        else:
            btn = buttons.GenBitmapToggleButton(self,wid,bitmap,size=(-1,self.toolSize[1]))
        
        btn.Bind(wx.EVT_BUTTON,self.onToolButton)
        btn.SetToolTipString(longHelpString)            
        #self.sizer.Add(btn,(self.y,self.x))
        self.ctrls.append(btn)
        self.idToTool[wid] = btn
        self.sizes.append(btn.GetSize()[0])
        self.x+=1
        
    def ToggleTool(self,toolid,flag):
        """
        Created: 27.04.2006, KP
        Description: A method for toggling a togglebutton on or off
        """      
        ctrl = self.idToTool[toolid]
        ctrl.SetToggle(flag)   
        
    def DoAddTool(self, wid, label, bitmap, bmpDisabled=None,
        kind=wx.ITEM_NORMAL, shortHelp='',longHelp = '',clientData = None):
        """
        Created: 27.04.2006, KP
        Description: A method for adding a tool to the toolbar
        """     
        if kind == wx.ITEM_NORMAL:
            self.AddSimpleTool(wid,bitmap,shortHelp,longHelp,0)
        elif kind == wx.ITEM_CHECK:
            self.AddSimpleTool(wid,bitmap,shortHelp,longHelp,1)
        
    def AddSeparator(self):
        """
        Created: 27.04.2006, KP
        Description: A method for adding a separator to the toolbar
        """          
        sep = wx.Panel(self,-1,size=(2,32),style = wx.SUNKEN_BORDER)
        #self.sizer.Add(sep, (self.y,self.x))
        self.x+=1
        self.ctrls.append(sep)
        self.idToTool[sep.GetId()] = sep
        self.sizes.append(sep.GetSize()[0])

    def GetToolSeparation(self):
        """
        Created: 27.04.2006, KP
        Description: Return the width between tools
        """          
        return self.toolSeparation

        
        
    def GetToolSize(self):
        """
        Created: 27.04.2006, KP
        Description: Return the size of a toolbar item
        """          
        return self.toolSize
        
    def SetToolBitmapSize(self,size):
        """
        Created: 27.04.2006, KP
        Description: Set the bitmap size of the toolbar
        """          
        self.toolSize = size
