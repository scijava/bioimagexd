#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: ColourDialog.py
 Project: BioImageXD
 Created: 2.2.2005
 Creator: KP
 Description:
 
 A color selection widget that inherits a wxpython widget implemented in python
 and overrides a method to capture the color selection and relay the selected
 color using a given callback method. Also validates the color

 Modified:  
            02.02.2005 KP - Created the class

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
__version__ = "$Revision: 1.28 $"
__date__ = "$Date: 2005/01/13 14:52:39 $"

import wx
import wx.lib.colourchooser as cc

class ColorSelectionDialog(cc.PyColourChooser):
    """
    Class: ColorSelectionDialog
    Created: 03.11.2004, KP
    Description: A widget for selecting a color. Validates the color
                 and notifies parent via callback of the choice
    """
    def __init__(self,parent,callback=None):
        self.callback=callback
        cc.PyColourChooser.__init__(self,parent,-1)
        
    
    def UpdateEntries(self,color):
        col=color
        colorlst=[color.Red(),color.Green(),color.Blue()]
        if 255 not in colorlst and max(colorlst)>0:
            mval=max(colorlst)
	    Logging.info("Converting ",colorlst,kw="trivial")
            coeff=255.0/mval
            ncolor=[int(x*coeff) for x in colorlst]
	    Logging.info("New color ",ncolor,kw="trivial")
            col=wx.Colour(ncolor[0],ncolor[1],ncolor[2])
            return self.SetValue(col)
        else:
            if self.callback:
                self.callback(col.Red(),col.Green(),col.Blue())
            cc.PyColourChooser.UpdateEntries(self,col)
