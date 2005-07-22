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



class NamePanel(wx.Panel):
    """
    Class: NamePanel
    Created: 05.05.2005, KP
    Description: A panel that paints a string it's given
    """
    def __init__(self,parent,label,color,**kws):
        size=kws["size"]
        wx.Panel.__init__(self,parent,-1,size=size)
        self.label=label
        self.xoff,self.yoff=0,0
        if kws.has_key("xoffset"):self.xoff=kws["xoffset"]
        if kws.has_key("yoffset"):self.yoff=kws["yoffset"]
        self.size=size
        self.origsize=size
        self.bold=0
        w,h=self.size
        #print "Height of track=",h
        self.btn = None
        self.buffer = wx.EmptyBitmap(w,h,-1)
        self.setColor((0,0,0),color)
        self.dc = None
        if kws.has_key("expand"):
            self.expandFunc=kws["expand"]
            self.bh=1
            self.btn = wx.ToggleButton(self,-1,"<<",(w-32,self.bh),(24,24))
            self.btn.SetValue(1)
            self.btn.SetBackgroundColour(self.fg)
            self.btn.SetForegroundColour(self.bg)
            font=self.btn.GetFont()
            font.SetPointSize(6)
            self.btn.SetFont(font)
            self.btn.Bind(wx.EVT_TOGGLEBUTTON,self.onToggle)
        self.Bind(wx.EVT_PAINT,self.onPaint)
        self.Bind(wx.EVT_SIZE,self.onSize)
            
    def onToggle(self,event):
        """
        Method: onToggle
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
        Method: onSize
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
        Method: setWeight(self,bold)
        Created: 05.05.2005, KP
        Description: Set the weight of the font
        """
        self.bold=bold
        self.paintLabel()

    def setLabel(self,label):
        """
        Method: setLabel(self,label)
        Created: 05.05.2005, KP
        Description: Set the label
        """
        self.label=label
        self.paintLabel()


    def setColor(self,fg,bg):
        """
        Method: setColor
        Created: 05.05.2005, KP
        Description: Set the color to use
        """
        self.fg=fg
        self.bg=bg
        if self.btn:
            self.btn.SetBackgroundColour(self.fg)
            self.btn.SetForegroundColour(self.bg)
        self.paintLabel()

    def onPaint(self,event):
        dc=wx.BufferedPaintDC(self,self.buffer)#,self.buffer)

    def paintLabel(self,bold=None):
        """
        Method: paintLabel
        Created: 05.05.2005, KP
        Description: Paints the label
        """
        self.dc = wx.BufferedDC(wx.ClientDC(self),self.buffer)

        self.dc.SetBackground(wx.Brush(self.bg))
        self.dc.Clear()
        self.dc.BeginDrawing()
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
    
    
    
