# -*- coding: iso-8859-1 -*-
"""
 Unit: Dialogs.py
 Project: Selli 2
 Created: 28.01.2005
 Creator: KP
 Description:

 Shortcut methods for displaying most of the normal dialogs.
 

 Modified: 28.01.2005 KP - Created the modules

 Selli 2 includes the following persons:
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi

 Copyright (c) 2004 Selli 2 Project.
"""
__author__ = "Selli 2 Project <http://sovellusprojektit.it.jyu.fi/selli/>"
__version__ = "$Revision: 1.71 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import math
import wx


def showmessage(parent,message,title,flags=wx.OK):
    dlg=wx.MessageDialog(parent,message,title,flags)
    dlg.ShowModal()
    dlg.Destroy()

def showwarning(parent,message,title,flags=wx.OK|wx.ICON_WARNING):
    showmessage(parent,message,title,flags)
    
def showerror(parent,message,title,flags=wx.OK|wx.ICON_ERROR):
    showmessage(parent,message,title,flags)

    
def askcolor(**kws):
    dlg = wx.ColourDialog(self)
    dlg.GetColourData().SetChooseFull(True)
    if dlg.ShowModal()==wx.ID_OK:
        gcolor=dlg.GetColourData()
    else:
        return None
    print "got color",gcolor
    color=gcolor[0]
    if 255 not in color:
        mval=max(color)
        coeff=255.0/mval
        ncolor=[int(x*coeff) for x in color]
        print "ncolor=",ncolor
        dlg=wx.MessageDialog(self,
            "The color you selected: %d,%d,%d is incorrect."
            "At least one of the R, G or B components\n"
            "of the color must be 255. Therefore, "
            "I have modified the color a bit. "
            "It is now %d,%d,%d. Have a nice day."%(color[0],
            color[1],color[2],ncolor[0],ncolor[1],ncolor[2]),"Selected color is incorrect",wx.OK|wx.ICON_WARNING)
        dlg.ShowModal()
        dlg.Destroy()
        gcolor=ncolor
    return (gcolor,"#%2x%2x%2x"%(gcolor[0],gcolor[1],gcolor[2]))


def askDirectory(parent,title,initialDir="."):
    filepath=""
    dlg = wx.DirDialog(parent, title,initialDir,
                      style=wx.DD_DEFAULT_STYLE|wx.DD_NEW_DIR_BUTTON)
    if dlg.ShowModal() == wx.ID_OK:
        filepath=dlg.GetPath()
    dlg.Destroy()
    return filepath

    
def askSaveAsFileName(parent,operation,name):
    initFile="%s.du"%(name)
    
    wc="%s Dataunit (*.du)|*.du"%operation
    filename=""
    dlg=wx.FileDialog(parent,"Write %s Data Unit to file"%operation,defaultFile=initFile,wildcard=wc,style=wx.SAVE)
    filename=None
    if dlg.ShowModal()==wx.ID_OK:
        filename=dlg.GetPath()
    dlg.Destroy()
    if filename:
        if filename[-3:].lower()!=".du":
            filename+=".du"            

    return filename
