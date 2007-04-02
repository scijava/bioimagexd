#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: UIElements
 Project: BioImageXD
 Created: 09.02.2005, KP
 Description:

 UIElements is a module with functions for generating various pieces
 of GUI that would otherwise require lots of repetitive code, like 
 label-field pairs or path field - browse button pairs
 
 Modified: 12.03.2005 KP - Created the module

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
__version__ = "$Revision: 1.22 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import wx
import  wx.lib.filebrowsebutton as filebrowse
import Configuration
import messenger
import platform
class AcceptedValidator(wx.PyValidator):
    def __init__(self, accept,above=-1,below=-1):
        wx.PyValidator.__init__(self)
        self.accept=accept
        self.above=above
        self.below=below
        self.Bind(wx.EVT_CHAR, self.OnChar)

    def Clone(self):
        return AcceptedValidator(self.accept)

    def Validate(self, win):
        tc = self.GetWindow()
        val = tc.GetValue()
        if self.above !=-1 or self.below != -1:
            try:
                ival=int(val)
            except:
                return False
            if above!=-1 and ival <above:return False
            if below!=-1 and ival >below:return False    
            

        for x in val:
            if x not in self.accept:
                return False

        return True    
        
    def OnChar(self, event):
        key = event.KeyCode()

        if key < wx.WXK_SPACE or key == wx.WXK_DELETE or key > 255:
            event.Skip()
            return
            
        if chr(key) in self.accept:
            event.Skip()
            return

        if not wx.Validator_IsSilent():
            wx.Bell()

        # Returning without calling even.Skip eats the event before it
        # gets to the text control
        return

class MyStaticBox(wx.StaticBox):
    """
    Created: 1.11.2006, KP
    Description: A static box replacement that allows us to control how it is painted
    """
    def __init__(self, parent, wid, label, pos = wx.DefaultPosition, size  = wx.DefaultSize, style = 0, name="MyStaticBox"):
        self.buffer = wx.EmptyBitmap(w,h,-1)
        wx.StaticBox.__init__(self,parent,wid,label,pos,size,style,name)
        
        self.parent = parent
        self.label = label
        self.Bind(wx.EVT_PAINT,self.onPaint)
        self.Bind(wx.EVT_SIZE,self.onSize)
        w,h = size
        
        self.owncol = (255,255,255)
        self.paintSelf()
        self.Raise()
        
        
    def SetOwnBackgroundColour(self,col):
        self.owncol=col
        
    def onPaint(self, evt):
        """
        Created: 1.11.2006, KP
        Description: Paint the static box
        """
        dc=wx.BufferedPaintDC(self,self.buffer)#,self.buffer)

    def onSize(self,evt):
        """
        Created: 1.11.2006, KP
        Description: Repaint self when size changes
        """
        w,h=evt.GetSize()
        self.buffer = wx.EmptyBitmap(w,h,-1)
        
        self.paintSelf()
        self.Raise()
    def paintSelf(self):
        """
        Created: 05.05.2005, KP
        Description: Paints the label
        """
        
        #self.dc = wx.BufferedDC(wx.ClientDC(self),self.buffer)        
        self.dc = wx.MemoryDC()
        self.dc.SelectObject(self.buffer)
               
        self.dc.BeginDrawing()
        #self.SetBackgroundColour(self.parent.GetBackgroundColour())
        self.dc.SetBackground(wx.Brush(self.parent.GetBackgroundColour()))
        self.dc.Clear()
        
        
            #self.dc.SetBackground(wx.Brush(self.bg))
        self.dc.SetBrush(wx.Brush(self.owncol))
        
        #self.dc.SetBrush(wx.TRANSPARENT_BRUSH)
        self.dc.SetPen(wx.Pen((208,208,191), 1))
        
        w,h = self.buffer.GetWidth(),self.buffer.GetHeight()
        self.dc.DrawRoundedRectangle(0,7,w,h-4,5)
            
        self.dc.SetTextForeground((0,70,213))
        weight=wx.NORMAL
        self.dc.SetBrush(wx.Brush(self.parent.GetBackgroundColour()))
        self.dc.SetPen(wx.Pen(self.parent.GetBackgroundColour(),1))
        
        font = wx.Font(8,wx.SWISS,wx.NORMAL,weight)
        
        self.dc.SetFont(font)
        w,h = self.dc.GetTextExtent(self.label)
        
        self.dc.DrawRectangle(8,0,w+4,h)
        self.dc.DrawText(self.label,10,0)
            

        self.dc.EndDrawing()
        self.dc.SelectObject(wx.NullBitmap)
        self.dc = None

class DimensionInfo(wx.Window):
    """
    Created: 1.11.2006, KP
    Description: A static box replacement that allows us to control how it is painted
    """
    def __init__(self, parent, wid, pos = wx.DefaultPosition, size  = wx.DefaultSize, style = 0, name="Dims info"):
        w,h = size
        self.buffer = wx.EmptyBitmap(w,h,-1)
        wx.Window.__init__(self,parent,wid,pos,size,style,name)
        
        self.parent = parent
        
        self.Bind(wx.EVT_PAINT,self.onPaint)
        self.Bind(wx.EVT_SIZE,self.onSize)
        w,h = size
        self.origX, self.origY, self.origZ = 0,0,0
        self.currX, self.currY, self.currZ = 0,0,0
        
        self.nondarwin = platform.system()!="Darwin"
        
        messenger.connect(None,"set_resample_dims", self.onSetResampleDims)
        messenger.connect(None,"set_current_dims",self.onSetCurrentDims)
        self.owncol = (255,255,255)
        self.paintSelf()
        self.Raise()
        
    def onSetResampleDims(self, obj, evt, dims, origDims):
        """
        Created: 19.12.2006, KP
        Description: set the resampled dimensions to show
        """
        self.currX, self.currY, self.currZ = dims
        self.origX, self.origY, self.origZ = origDims
        self.paintSelf()
        self.Refresh()

    def onSetCurrentDims(self, obj, evt, dims):
        """
        Created: 19.12.2006, KP
        Description: set the current dimensions to show
        """
        self.currX, self.currY, self.currZ = dims
        self.origX, self.origY, self.origZ = dims
        w,h=self.GetSize()
        self.buffer = wx.EmptyBitmap(w,h,-1)
        
        self.paintSelf()    
        self.Refresh()
        
    def SetOwnBackgroundColour(self,col):
        self.owncol=col
        
    def onPaint(self, evt):
        """
        Created: 1.11.2006, KP
        Description: Paint the static box
        """
        dc=wx.BufferedPaintDC(self,self.buffer)#,self.buffer)

    def onSize(self,evt):
        """
        Created: 1.11.2006, KP
        Description: Repaint self when size changes
        """
        w,h=evt.GetSize()
        self.buffer = wx.EmptyBitmap(w,h,-1)
        
        self.paintSelf()
        
    def paintSelf(self):
        """
        Created: 05.05.2005, KP
        Description: Paints the label
        """
        
        #self.dc = wx.BufferedDC(wx.ClientDC(self),self.buffer)        
        self.dc = wx.MemoryDC()
        self.dc.SelectObject(self.buffer)
               
        self.dc.BeginDrawing()
        #self.SetBackgroundColour(self.parent.GetBackgroundColour())
        # We don't clear the background on non-darwin to keep the striped 
        # default look,but on windows we set it to parents background color
        # because otherwise it would be black
        if self.nondarwin:
            self.dc.SetBackground(wx.Brush(self.parent.GetBackgroundColour()))
            self.dc.Clear()
        else:
            pass    
        
        
            #self.dc.SetBackground(wx.Brush(self.bg))
        #self.dc.SetBrush(wx.Brush(self.owncol))
        
        #self.dc.SetBrush(wx.TRANSPARENT_BRUSH)
        self.dc.SetPen(wx.Pen((208,208,191), 1))
        
        w,h = self.buffer.GetWidth(),self.buffer.GetHeight()
        #self.dc.DrawRoundedRectangle(0,7,w,h-4,5)
            
        
        weight=wx.NORMAL
        self.dc.SetBrush(wx.Brush(self.parent.GetBackgroundColour()))
        self.dc.SetPen(wx.Pen(self.parent.GetBackgroundColour(),1))
        
        if platform.system()=="Windows":
            font = wx.Font(8, wx.SWISS, wx.NORMAL, weight)
        else:
            font = wx.Font(9,wx.SWISS,wx.NORMAL,weight)
        self.dc.SetTextForeground((0,0,0))
        self.dc.SetFont(font)
        txt="%3d x %3d x %3d"%(self.currX, self.currY, self.currZ)
        
        self.dc.DrawText("Now:",1,0)
        self.dc.DrawText(txt,45,0)
        self.dc.SetTextForeground((80,80,80))
        self.dc.DrawText("Original:",1,18)
        txt="%3d x %3d x %3d"%(self.origX, self.origY, self.origZ)
        self.dc.DrawText(txt, 45,18)
        self.dc.EndDrawing()
        self.dc.SelectObject(wx.NullBitmap)
        self.dc = None    

class NamePanel(wx.Window):
    """
    Created: 05.05.2005, KP
    Description: A panel that paints a string it's given
    """
    def __init__(self,parent,label,color,**kws):
        size=kws["size"]
        self.parent=parent
        wx.Window.__init__(self,parent,-1,size=size)
        self.label=label
        self.xoff,self.yoff=8,0
        if kws.has_key("xoffset"):self.xoff=kws["xoffset"]
        if kws.has_key("yoffset"):self.yoff=kws["yoffset"]
        self.size=size
        self.origsize=size
        self.bold=1
        w,h=self.size
        self.btn = None
        cs = self.parent.GetClientSize()
        if w<0:
            w=cs[0]
        if h<0:
            h=cs[1]
        self.buffer = wx.EmptyBitmap(w,h,-1)

        self.setColor((0,0,0),color)
        self.dc = None
        if kws.has_key("expand"):
            self.expandFunc=kws["expand"]
            self.bh=1
            self.btn = wx.ToggleButton(self,-1,"<<",(w-32,self.bh),(24,24))
            self.btn.SetValue(1)
            Logging.info("Setting background color to ",self.fg)
            self.btn.SetBackgroundColour(self.fg)
            if self.bg:
                Logging.info("Setting foreground color to ",self.bg)

                self.btn.SetForegroundColour(self.bg)
            font=self.btn.GetFont()
            font.SetPointSize(6)
            self.btn.SetFont(font)
            self.btn.Bind(wx.EVT_TOGGLEBUTTON,self.onToggle)
        self.Bind(wx.EVT_PAINT,self.onPaint)
        self.Bind(wx.EVT_SIZE,self.onSize)
            
    def onToggle(self,event):
        """
        Created: 26.05.2005, KP
        Description: Handle toggle events
        """
        val=self.btn.GetValue()
        if val==0:
            self.btn.SetLabel(">>")
        else:
            self.btn.SetLabel("<<")
        self.expandFunc(val)
        
    def onSize(self,event):
        """
        Created: 26.05.2005, KP
        Description: Size event handler
        """
        w,h=self.origsize
        self.size=event.GetSize()
        #print "sizing %s to "%self.label,self.size
        w,h2=self.size
        self.size=w,h
        self.buffer = wx.EmptyBitmap(w,h,-1)
        self.SetSize(self.size)
        if self.btn:
            self.btn.Move((w-32,self.bh))
        self.paintLabel()
        #self.Refresh()
                         
    def setWeight(self,bold):
        """
        Created: 05.05.2005, KP
        Description: Set the weight of the font
        """
        self.bold=bold
        self.paintLabel()

    def setLabel(self,label):
        """
        Created: 05.05.2005, KP
        Description: Set the label
        """
        self.label=label
        self.paintLabel()


    def setColor(self,fg,bg):
        """
        Created: 05.05.2005, KP
        Description: Set the color to use
        """
        self.fg=fg
        self.bg=bg
        if self.btn:
            self.btn.SetBackgroundColour(self.fg)
            if self.bg:
                self.btn.SetForegroundColour(self.bg)
        self.paintLabel()

    def onPaint(self,event):
        dc=wx.BufferedPaintDC(self,self.buffer)#,self.buffer)

    def paintLabel(self,bold=None):
        """
        Created: 05.05.2005, KP
        Description: Paints the label
        """
        self.dc = wx.BufferedDC(wx.ClientDC(self),self.buffer)
        
        
        
        self.dc.BeginDrawing()
        self.SetBackgroundColour(self.parent.GetBackgroundColour())
        self.dc.SetBackground(wx.Brush(self.parent.GetBackgroundColour()))
        self.dc.Clear()
        if self.bg:
            #self.dc.SetBackground(wx.Brush(self.bg))
            self.dc.SetBrush(wx.Brush(self.bg))
            self.dc.SetPen(wx.Pen(self.bg, 1))
            w,h = self.buffer.GetWidth(),self.buffer.GetHeight()
            self.dc.DrawRoundedRectangle(0,0,w,h,5)
            
        self.dc.SetTextForeground(self.fg)
        weight=wx.NORMAL
        if self.bold:
           weight=wx.BOLD
        self.dc.SetFont(wx.Font(9,wx.SWISS,wx.NORMAL,weight))
        self.dc.DrawText(self.label,self.xoff,self.yoff)

        self.dc.EndDrawing()
        self.dc = None


def createDirBrowseButton(parent,label,callback):
    sizer=wx.BoxSizer(wx.VERTICAL)
    sizer2=wx.BoxSizer(wx.HORIZONTAL)
    lbl=wx.StaticText(parent,-1,label)
    sizer.Add(lbl)
    field=wx.TextCtrl(parent,-1,"")
    sizer2.Add(field)
    btn=filebrowse.DirBrowseButton(parent,-1,changeCallback = callback)
    sizer2.Add(btn)
    sizer.Add(sizer2)
    return sizer
    
def getImageFormatMenu(parent,label="Image Format: "):
    sizer=wx.BoxSizer(wx.HORIZONTAL)
    lbl=wx.StaticText(parent,-1,label)
    sizer.Add(lbl)
    formats=["PNG","BMP","JPEG","TIFF"]
    menu=wx.Choice(parent,-1,choices=formats)
    sizer.Add(menu)
    sizer.menu=menu
    return sizer

def getSliceSelection(parent):
    sizer=wx.GridBagSizer()
    #lbl=wx.StaticText(parent,-1,"Select processed slices:")
    fromlbl=wx.StaticText(parent,-1,"Slices from ")
    tolbl=wx.StaticText(parent,-1," to ")
    everylbl=wx.StaticText(parent,-1,"Every nth slice:")
    fromedit=wx.SpinCtrl(parent,-1)
    toedit=wx.SpinCtrl(parent,-1)
    fromedit.SetRange(0,25)
    fromedit.SetValue(0)
    toedit.SetRange(0,25)
    toedit.SetValue(0)
    everyedit=wx.TextCtrl(parent,-1,"1")
    sizer.Add(fromlbl,(0,0))
    sizer.Add(fromedit,(0,1))
    sizer.Add(tolbl,(0,2))
    sizer.Add(toedit,(0,3))
    sizer.Add(everylbl,(1,0))
    sizer.Add(everyedit,(1,1))
    return sizer
    
    
    
