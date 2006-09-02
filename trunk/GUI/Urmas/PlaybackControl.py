"""
 Unit: PlaybackControl
 Project: BioImageXD
 Created: 25.02.2006, KP
 Description:

 URM/AS - The Unified Rendering Manager / Animator for Selli
 
 This is a timeline based GUI for controlling the rendering of datasets. The GUI allows users
 to specify a path for the camera to follow (using Heikki Uuksulainen's MayaVi animator code)
 and also allows them to produce videos of the rendering using ffmpeg.
 
 This is the playback control panel for Urmas
 
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
t.
"""
__author__ = "BioImageXD Project"
__version__ = "$Revision: 1.22 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import wx
import messenger
import os
import time
import scripting

PLAY_MODE=0
PAUSE_MODE=1

class PlaybackControl(wx.Panel):
#class PlaybackControl(wx.SashLayoutWindow):
    """
    Class: PlaybackCOntrol
    Created: 25.01.2006, KP
    Description: A panel that contains a slider and stop and play/pause buttons 
    """
    def __init__(self,parent,n):    
        """
        Method: createSliders
        Created: 25.01.2006, KP
        Description: Method that initializes the class
        """        
        wx.Panel.__init__(self,parent,-1,size=(1024,64))
        #wx.SashLayoutWind#ow.__init__(self,parent,-1)
        self.sizer = wx.BoxSizer()
        #self.SetBackgroundColour((255,0,0))
        iconpath=scripting.get_icon_dir()
        self.playicon = wx.Image(os.path.join(iconpath,"play.gif"),wx.BITMAP_TYPE_GIF).ConvertToBitmap()
        self.pauseicon = wx.Image(os.path.join(iconpath,"pause.gif"),wx.BITMAP_TYPE_GIF).ConvertToBitmap()
        self.stopicon = wx.Image(os.path.join(iconpath,"stop.gif"),wx.BITMAP_TYPE_GIF).ConvertToBitmap()
        
        self.playpause=wx.BitmapButton(self,-1,self.playicon)
        self.stop = wx.BitmapButton(self,-1,self.stopicon)
        self.timeslider=wx.Slider(self,value=1,minValue=1,maxValue=n,
        style=wx.SL_HORIZONTAL|wx.SL_LABELS|wx.SL_AUTOTICKS)
        
        self.sizer.Add(self.playpause,)
        self.sizer.Add(self.stop)
        self.sizer.Add(self.timeslider,1,flag=wx.EXPAND|wx.LEFT|wx.RIGHT)
        
        self.callback = None
        self.changing=0
        
        self.mode=PLAY_MODE
        self.playpause.Bind(wx.EVT_BUTTON,self.onPlayPause)
        self.stop.Bind(wx.EVT_BUTTON,self.onStop)
        self.stop.Enable(0)
        
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)
        
        messenger.connect(None,"set_timeslider_value",self.onSetTimeslider)
        messenger.connect(None,"set_time_range",self.onSetTimeRange)
        messenger.connect(None,"timepoint_changed",self.onSetTimepoint)        
        messenger.connect(None,"set_play_mode",self.onSetPlay)
        
        
    def onSetPlay(self,obj,evt,*args):
        """
        Method: pnSetPlay
        Created: 30.01.2006, KP
        Description: A callback for setting the control panel to play mode
        """     
        self.mode = PLAY_MODE
        self.onPlayPause(None,no_events=1)
    
        
    def bindTimeslider(self,method,all=0):
        """
        Method: bindTimeslider
        Created: 15.08.2005, KP
        Description: Bind the timeslider to a method
        """     
        if not all and platform.system() in ["Windows","Darwin"]:
            self.timeslider.Unbind(wx.EVT_SCROLL_ENDSCROLL)
            #self.timeslider.Unbind(wx.EVT_SCROLL_THUMBRELEASE)
            self.timeslider.Bind(wx.EVT_SCROLL_ENDSCROLL,method)
            #self.timeslider.Bind(wx.EVT_SCROLL_THUMBRELEASE,method)
        else:
            self.timesliderMethod = method
            self.timeslider.Unbind(wx.EVT_SCROLL)
            self.timeslider.Bind(wx.EVT_SCROLL,self.delayedTimesliderEvent)        
        
    def delayedTimesliderEvent(self,event):
        """
        Method: delayedTimesliderEvent
        Created: 28.04.2005, KP
        Description: Set the timepoint to be shown
        """
        self.changing=time.time()
        wx.FutureCall(200,lambda e=event,s=self:s.timesliderMethod(e))        
        
    def onStop(self,evt):
        """
        Method: onStop
        Created: 25.01.2006, KP
        Description: Callback for when the stop button is pressed
        """        
        self.mode = PLAY_MODE
        self.playpause.SetBitmapLabel(self.playicon)
        self.playpause.Refresh()
        self.stop.Enable(0)
        
        messenger.send(None,"playback_stop")
        self.timeslider.SetValue(0)
        
        
    def onPlayPause(self,evt,no_events=0):
        """
        Method: onPlayPause
        Created: 25.01.2006, KP
        Description: Callback for when the play/pause icon is pressed
        """
        if self.mode==PLAY_MODE:
            self.playpause.SetBitmapLabel(self.pauseicon)
            self.mode=PAUSE_MODE
            self.stop.Enable(1)
            if not no_events:
                messenger.send(None,"playback_play")
        else:
            self.playpause.SetBitmapLabel(self.playicon)
            self.mode=PLAY_MODE
            if not no_events:
                messenger.send(None,"playback_pause")
        self.playpause.Refresh()            
            
    def onSetTimeslider(self,obj,event,tp):
        """
        Method: onSetTimeslider
        Created: 21.08.2005, KP
        Description: Update the timeslider according to an event
        """
        self.timeslider.SetValue(tp) 
    def onSetTimeRange(self,obj,event,r1,r2):
        """
        Method: onSetTimeRange
        Created: 15.08.2005, KP
        Description: Set the range that the time slider shows
        """        
        self.timeslider.SetRange(r1,r2)
        self.timeslider.Refresh()        
        
    def onSetTimepoint(self,obj,event,timepoint):
        """
        Method: onSetTimepoint
        Created: 21.06.2005, KP
        Description: Update the timepoint according to an event
        """
        curr=self.timeslider.GetValue()
        if curr-1!=timepoint:
            self.timeslider.SetValue(timepoint+1)
