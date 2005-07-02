# -*- coding: iso-8859-1 -*-
"""
 Unit: Logging.py
 Project: Selli
 Created: 13.12.2004, KP
 Description:

 A module for reporting and logging errors

 Modified: 13.12.2004 KP - Created the module
           11.01.2005 JV - Added comments
 
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
__author__ = "Selli Project <http://sovellusprojektit.it.jyu.fi/selli/>"
__version__ = "$Revision: 1.6 $"
__date__ = "$Date: 2005/01/11 14:36:00 $"


import traceback
import wx
import os.path

HIDE_DEBUG=["visualizer","init","io","scale"]
KWS=["visualizer","main","init","animator","io","task","preview","scale"]

import sys

class GUIError:
    """
    Class: GUIError
    Created: 13.12.2004
    Creator: KP
    Description: Displays an error message.
    """
    def __init__(self,title,msg):
        """
        Method: __init__
        Created: 13.12.2004
        Creator: KP
        Description: Constructor
        Parameters:
            title      Title for the error message
            msg        The actual error message
        """
        self.msg=msg
        self.title=title

    def show(self):
        """
        Method: show
        Created: 13.12.2004
        Creator: KP
        Description: Displays the error message in a tkMessageBox.
        """
        dlg=wx.MessageDialog(None,self.msg,self.title,wx.OK|wx.ICON_ERROR)
        dlg.ShowModal()
        dlg.Destroy()

    def __str__(self):
        """
        Method: __str__
        Created: 13.12.2004
        Creator: KP
        Description: Returns the error message in a string.
        """
        return "[Error: %s: %s]"%(self.title,self.msg)

    def __repr__(self):
        """
        Method: __repr__
        Created: 13.12.2004
        Creator: KP
        Description: Returns the error message in a string.
        """
        return str(self)


def error(title,msg,x=sys._getframe()):
    """
    Function: error
    Created: 13.12.2004
    Creator: KP
    Description: Raises an GuiError.
    Parameters:
            title      Title for the error message
            msg        The actual error message
    """
    print "%s: %s"%(x.f_code.co_filename,x.f_lineno),"ERROR: %s"%msg
    raise GUIError(title,"%s: %s"%(x.f_code.co_filename,x.f_lineno)+" "+msg)


def info(msg,*args,**kws):
    """
    Function: info
    Created: 13.12.2004
    Creator: KP
    Description: Prints information
    Parameters:
            msg        The message
            args       Arguments to be printed along with message
    """
    xframe=sys._getframe(1)
    if "kw" in kws and kws["kw"] not in KWS:raise Exception("Unknown keyword "+kws["kw"])
    if not ("kw" in kws) or (("kw" in kws) and (kws["kw"] not in HIDE_DEBUG)):
        file=os.path.split(xframe.f_code.co_filename)[-1]
        lineno=xframe.f_lineno
        print "%s:%d: %s %s"%(file,lineno,msg," ".join(map(str,args)))
