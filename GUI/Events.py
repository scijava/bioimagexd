# -*- coding: iso-8859-1 -*-

"""
 Unit: Events
 Project: BioImageXD
 Created: 28.04.2005, KP
 Description:

 A module that contains all the events BioImageXD sends / receives
 
 Modified 28.04.2005 KP - Separated code to a module of it's own
          
 BioImageXD includes the following persons:
 DW - Dan White, dan@chalkie.org.uk
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 PK - Pasi Kankaanpää, ppkank@bytl.jyu.fi
 
 Copyright (c) 2005 BioImageXD
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
