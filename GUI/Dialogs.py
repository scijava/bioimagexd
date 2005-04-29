# -*- coding: iso-8859-1 -*-
"""
 Unit: Dialogs.py
 Project: BioImageXD
 Created: 28.01.2005
 Creator: KP
 Description:

 Shortcut methods for displaying most of the normal dialogs. 

 Modified: 28.01.2005 KP - Created the modules
           12.03.2005 KP - Made file dialogs save the last openend path

 BioImageXD includes the following persons:
 
 DW - Dan White, dan@chalkie.org.uk
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 PK - Pasi Kankaanpää, ppkank@bytl.jyu.fi
 
 Copyright (c) 2005 BioImageXD Project.
"""
__author__ = "BioImageXD Project"
__version__ = "$Revision: 1.22 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import Configuration
import wx
import os.path


def showmessage(parent,message,title,flags=wx.OK):
    """
    Method: showMessage(parent,message,title)
    Created: 28.01.2005, KP
    Description: A method to show a message
    """
    dlg=wx.MessageDialog(parent,message,title,flags)
    dlg.ShowModal()
    dlg.Destroy()

def showwarning(parent,message,title,flags=wx.OK|wx.ICON_WARNING):
    """
    Method: showwarning(parent,message,title)
    Created: 28.01.2005, KP
    Description: A method to show a warning
    """    
    showmessage(parent,message,title,flags)
    
def showerror(parent,message,title,flags=wx.OK|wx.ICON_ERROR):
    """
    Method: showerror(parent,message,title)
    Created: 28.01.2005, KP
    Description: A method to show an error message
    """    
    showmessage(parent,message,title,flags)

    
def askcolor(*args,**kws):
    """
    Method: askcolor()
    Created: 28.01.2005, KP
    Description: A method to input a color from user
    """    
    dlg = wx.ColourDialog(None)
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


def askDirectory(parent,title,initialDir=None):
    """
    Method: askDirectory(parent, title, initialDir)
    Created: 28.01.2005, KP
    Description: A method for showing a directory selection dialog
    """    
    filepath=""
    conf=Configuration.getConfiguration()
    remember=conf.getConfigItem("RememberPath","Paths")
    if not initialDir:
        if remember:
            initialDir = conf.getConfigItem("LastPath","Paths")
            if not initialDir:initialDir="."
        else:
            initialDir = conf.getConfigItem("DataPath","Paths")
    dlg = wx.DirDialog(parent, title,initialDir,
                      style=wx.DD_DEFAULT_STYLE|wx.DD_NEW_DIR_BUTTON)
    if dlg.ShowModal() == wx.ID_OK:
        filepath=dlg.GetPath()
        
    if remember:
        conf.setConfigItem("LastPath","Paths",filepath)
    dlg.Destroy()
    return filepath

def askOpenFileName(parent,title,wc,remember=-1):
    """
    Method: menuOpen()
    Created: 12.03.2005, KP
    Description: A method to show a open file dialog that supports multiple files
    """
    asklist=[]
    if remember == -1:
        conf=Configuration.getConfiguration()
        remember=conf.getConfigItem("RememberPath","Paths")
    lastpath=""
    type=wc.split("|")[1]
    type=type.split(".")[1]
    print "type=",type
    if remember:
        lastpath=conf.getConfigItem("LastPath_%s"%type,"Paths")
        if not lastpath:lastpath="."
    dlg=wx.FileDialog(parent,title,lastpath,wildcard=wc,style=wx.OPEN|wx.MULTIPLE)
    if dlg.ShowModal()==wx.ID_OK:
        asklist=dlg.GetPaths()
        if not asklist:return asklist
        if remember:
            filepath=os.path.dirname(asklist[0])
            conf.setConfigItem("LastPath_%s"%type,"Paths",filepath)
        
    dlg.Destroy()
    return asklist
    
def askSaveAsFileName(parent,title,initFile,wc):
    """
    Method: askSaveAsFileName(parent,operation,name)
    Created: 28.01.2005, KP
    Description: A method to show a save as dialog
    """    
    initialDir=None
    conf=Configuration.getConfiguration()
    remember=conf.getConfigItem("RememberPath","Paths")
    type=wc.split("|")[1]
    type=type.split(".")[1]

    if not initialDir:
        if remember:
            initialDir = conf.getConfigItem("LastPath_%s"%type,"Paths")
            if not initialDir:initialDir="."
        else:
            initialDir = conf.getConfigItem("DataPath","Paths")
    
    filename=""
    dlg=wx.FileDialog(parent,title,defaultFile=initFile,defaultDir=initialDir,wildcard=wc,style=wx.SAVE)
    filename=None
    if dlg.ShowModal()==wx.ID_OK:
        filename=dlg.GetPath()
    if remember and filename:
        filepath=os.path.dirname(filename)
        conf.setConfigItem("LastPath_%s"%type,"Paths",filepath)
                    
    dlg.Destroy()
    if filename:
        ext=wc.split(".")[-1]
        d=len(ext)
        if filename[-d:].lower()!=ext.lower():
            filename+=".%s"%ext 

    return filename
