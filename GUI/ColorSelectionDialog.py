#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: ColourDialog.py
 Project: Selli 2
 Created: 2.2.2005
 Creator: KP
 Description:
 
 A color selection widget that inherits a wxpython widget implemented in python
 and overrides a method to capture the color selection and relay the selected
 color using a given callback method. Also validates the color

 Modified:  
            02.02.2005 KP - Created the class

 Selli 2 includes the following persons:
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 
 Copyright (c) 2004 Selli 2 Project.
"""
__author__ = "Selli 2 Project <http://sovellusprojektit.it.jyu.fi/selli/>"
__version__ = "$Revision: 1.28 $"
__date__ = "$Date: 2005/01/13 14:52:39 $"

from wxPython.wx import *
import wx.lib.colourchooser as cc

class ColorSelectionDialog(cc.PyColourChooser):
    """
    Class: ColorSelectionDialog
    Created: 03.11.2004
    Creator: KP
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
            print "Converting ",colorlst
            coeff=255.0/mval
            ncolor=[int(x*coeff) for x in colorlst]
            print "new color,",ncolor
            col=wxColour(ncolor[0],ncolor[1],ncolor[2])
            return self.SetValue(col)
        else:
            if self.callback:
                self.callback(col.Red(),col.Green(),col.Blue())
            cc.PyColourChooser.UpdateEntries(self,col)
