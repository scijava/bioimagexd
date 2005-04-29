# -*- coding: iso-8859-1 -*-

"""
 Unit: Events
 Project: BioImageXD
 Created: 28.04.2005, KP
 Description:

 A module that contains all the events BioImageXD sends / receives
 
 Modified 28.04.2005 KP - Separated code to a module of it's own
          
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
__version__ = "$Revision: 1.9 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import wx

myEVT_TIMEPOINT_CHANGED=wx.NewEventType()
EVT_TIMEPOINT_CHANGED=wx.PyEventBinder(myEVT_TIMEPOINT_CHANGED,1)

myEVT_ZSLICE_CHANGED=wx.NewEventType()
EVT_ZSLICE_CHANGED=wx.PyEventBinder(myEVT_ZSLICE_CHANGED,1)

class ChangeEvent(wx.PyCommandEvent):
    """
    Class: ChangeEvent
    Created: 25.03.2005, KP
    Description: An event type that represents value of zslider or timepoint slider
    """
    def __init__(self,evtType,id):
        wx.PyCommandEvent.__init__(self,evtType,id)
        self.changeTo=0
    def getValue(self):
        return self.changeTo
    def setValue(self,val):
        self.changeTo=val
