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

ID_TIMEPOINT=wx.NewId()

myEVT_TIMEPOINT_CHANGED=wx.NewEventType()
EVT_TIMEPOINT_CHANGED=wx.PyEventBinder(myEVT_TIMEPOINT_CHANGED,1)

myEVT_ZSLICE_CHANGED=wx.NewEventType()
EVT_ZSLICE_CHANGED=wx.PyEventBinder(myEVT_ZSLICE_CHANGED,1)

myEVT_VOXEL=wx.NewEventType()
EVT_VOXEL=wx.PyEventBinder(myEVT_VOXEL,1)

myEVT_DATA_UPDATE=wx.NewEventType()
EVT_DATA_UPDATE=wx.PyEventBinder(myEVT_DATA_UPDATE,1)

myEVT_THRESHOLD_CHANGED=wx.NewEventType()
EVT_THRESHOLD_CHANGED=wx.PyEventBinder(myEVT_THRESHOLD_CHANGED,1)

class ThresholdEvent(wx.PyCommandEvent):
    """
    Class: ThresholdEvent
    Created: 03.04.2005, KP
    Description: An event type that represents a lower and upper threshold change
    """
    def __init__(self,evtType,id):
        wx.PyCommandEvent.__init__(self,evtType,id)
        self.greenthreshold=(127,127)
        self.redthreshold=(127,127)
    def getGreenThreshold(self):
        return self.greenthreshold
        
    def getRedThreshold(self):
        return self.redthreshold
        
    def setGreenThreshold(self,lower,upper):
        self.greenthreshold = (lower,upper)
        
    def setRedThreshold(self,lower,upper):
        self.redthreshold = (lower,upper)


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
        
class VoxelEvent(wx.PyCommandEvent):
    """
    Class: VoxelEvent
    Created: 23.05.2005, KP
    Description: An event type that represents a value of voxel (x,y,z)
    """    
    def __init__(self,evtType,id):
        wx.PyCommandEvent.__init__(self,evtType,id)
        self.x,self.y,self.z=0,0,0
        
    def setCoord(self,x,y,z):
        self.x,self.y,self.z=x,y,z
    def getCoord(self):
        return self.x,self.y,self.z
        
        
class DataUpdateEvent(wx.PyCommandEvent):
    """
    Class: DataUpdateEvent
    Created: 25.05.2005, KP
    Description: An event type that is used to signal an update to a data
                 that needs to be reflected in the rendering of the data
    """    
    def __init__(self,evtType,id,**kws):
        wx.PyCommandEvent.__init__(self,evtType,id)
        if kws.has_key("delay"):
            self.delay=kws["delay"]
    
    def getDelay(self):
        """
        Method: getDelay
        Created: 25.05.2005, KP
        Description: Returns the delay flag. If delay is set, then the
                     change should not be immediately reflected in rendering
                     but rather after a small delay. This is because there
                     might be more changes coming soon.
        """    
        return self.delay
