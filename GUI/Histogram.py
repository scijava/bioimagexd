# -*- coding: iso-8859-1 -*-
"""
 Unit: Histogram
 Project: BioImageXD
 Created: 30.10.2004, KP
 Description:

 A widget used to view a histogram
 
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
__author__ = "BioImageXD Project <http://www.bioimagexd.org/>"
__version__ = "$Revision: 1.28 $"
__date__ = "$Date: 2005/01/13 14:52:39 $"

import ImageOperations
import Logging
import wx
#from enthought.tvtk import messenger
import messenger

class Histogram(wx.Panel):
    """
    Class: Histogram
    Created: 11.07.2005, KP
    Description: A widget that can paint a histogram
    """
    def __init__(self,parent,**kws):
        """
        Method: __init__(parent)
        Created: 24.03.2005, KP
        Description: Initialization
        """    
        wx.Panel.__init__(self,parent,-1,**kws)
        self.parent=parent
        self.timePoint=0
        self.buffer=wx.EmptyBitmap(256,150)
        self.bg=None
        self.Bind(wx.EVT_PAINT,self.OnPaint)
        messenger.connect(None,"timepoint_changed",self.onSetTimepoint)
        messenger.connect(None,"threshold_changed",self.updatePreview)
        self.Bind(wx.EVT_RIGHT_DOWN,self.onRightClick)

        self.ID_LOGARITHMIC=wx.NewId()
        self.ID_IGNORE_BORDER=wx.NewId()
        self.logarithmic=1
        self.ignoreBorder=0
        self.histogram=None
        self.renew=1
        self.menu=wx.Menu()
        self.mode="lower"
        item = wx.MenuItem(self.menu,self.ID_LOGARITHMIC,"Logarithmic scale",kind=wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU,self.onSetLogarithmic,id=self.ID_LOGARITHMIC)
        self.menu.AppendItem(item)
        self.menu.Check(self.ID_LOGARITHMIC,1)

        item = wx.MenuItem(self.menu,self.ID_IGNORE_BORDER,"Ignore border bin",kind=wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU,self.onSetIgnoreBorder,id=self.ID_IGNORE_BORDER)
        self.menu.AppendItem(item)
        
        self.actionstart=None
        self.Bind(wx.EVT_LEFT_DOWN,self.markActionStart)
        self.Bind(wx.EVT_MOTION,self.updateActionEnd)
        self.Bind(wx.EVT_LEFT_UP,self.setThreshold)
        

    def markActionStart(self,event):
        """
        Method: markActionStart
        Created: 12.07.2005, KP
        Description: Sets the starting position of rubber band for zooming
        """    
        pos=event.GetPosition()
        x,y=pos
        y=255-y
        get=self.dataUnit.getSettings().get
        lower=get("ColocalizationLowerThreshold")
        if lower==None:
            return
        self.actionstart=(x,y)
        upper=get("ColocalizationUpperThreshold")
        
        self.mode="upper"
        if abs(x-lower)<abs(x-upper):self.mode="lower"
        if x<lower:self.mode="lower"
        if x>upper:self.mode="upper"
        self.updatePreview()
            
    def updateActionEnd(self,event):
        """
        Method: updateActionEnd
        Created: 12.07.2005, KP
        Description: Draws the rubber band to current mouse pos       
        """
        if event.LeftIsDown():
            x,y=event.GetPosition()
            y=255-y
            self.actionstart=(x,y)
            self.updatePreview()
            
    def setThreshold(self,event=None):
        """
        Method: setThreshold(event)
        Created: 24.03.2005, KP
        Description: Sets the thresholds based on user's selection
        """
        if not self.actionstart:return
        x1,y1=self.actionstart
        
        set=self.dataUnit.getSettings().set
        get=self.dataUnit.getSettings().get
        lower=get("ColocalizationLowerThreshold")
        upper=get("ColocalizationUpperThreshold")
        if self.mode=="upper":
            set("ColocalizationUpperThreshold",x1)
        else:
            set("ColocalizationLowerThreshold",x1)
            
        messenger.send(None,"threshold_changed") 
        self.actionstart=None
        
         
        
    def onRightClick(self,event):
        """
        Method: onRightClick
        Created: 02.04.2005, KP
        Description: Method that is called when the right mouse button is
                     pressed down on this item
        """      
        self.PopupMenu(self.menu,event.GetPosition())

    def onSetLogarithmic(self,evt):
        """
        Method: onSetLogarithmic
        Created: 12.07.2005, KP
        Description: Set the scale to logarithmic
        """
        self.logarithmic=evt.IsChecked()
        self.renew=1
        self.updatePreview()
        self.Refresh()

    def onSetIgnoreBorder(self,evt):
        """
        Method: onSetLogarithmic
        Created: 12.07.2005, KP
        Description: Set the scale to logarithmic
        """
        self.ignoreBorder=evt.IsChecked()
        self.renew=1
        self.updatePreview()
        
    def onSetTimepoint(self,obj,evt,timepoint):
        """
        Method: onSetTimepoint(obj,evt,timepoint)
        Created: 12.07.2005, KP
        Description: Set the timepoint to be shown
        """
        self.timePoint=timepoint
        self.renew=1
        self.updatePreview()
        
    def setDataUnit(self,dataUnit):
        """
        Method: setDataUnit
        Created: 28.04.2005, KP
        Description: Does the actual blitting of the bitmap
        """
        self.dataUnit=dataUnit
        self.renew=1
        self.updatePreview()
        
        
    def updatePreview(self,*args):
        """
        Method: updatePreview()
        Created: 12.07.2005, KP
        Description: Update the histogram
        """
        get=self.dataUnit.getSettings().get
        lower=get("ColocalizationLowerThreshold")
        upper=get("ColocalizationUpperThreshold")
                

        if self.renew:
            self.data=self.dataUnit.getTimePoint(self.timePoint)
            self.ctf=self.dataUnit.getSettings().get("ColorTransferFunction")
            if not self.ctf:Logging.info("No ctf!")
            self.bg=self.parent.GetBackgroundColour()
                
            
            histogram,self.percent,self.values = ImageOperations.histogram(self.data,bg=self.bg,ctf=self.ctf,
                             logarithmic=self.logarithmic,
                            ignore_border=self.ignoreBorder,
                            lower=lower,
                            upper=upper)
            self.histogram=histogram
            w,h=self.histogram.GetWidth(),self.histogram.GetHeight()
            self.buffer=wx.EmptyBitmap(w,h)
            Logging.info("Setting size to",w,h,kw="imageop")
            self.SetSize((w,h))
            self.parent.Layout()
            self.renew=0
            
        self.paintPreview()
        
        # Commented because in windows looks bad and not needed
        #self.Refresh()
        
    def paintPreview(self):
        """
        Method: paintPreview
        Created: 12.07.2005, KP
        Description: Paints the scatterplot
        """
        dc = wx.BufferedDC(wx.ClientDC(self),self.buffer)
        dc.BeginDrawing()
        dc.DrawBitmap(self.histogram,0,0,1)
        get=self.dataUnit.getSettings().get
        set=self.dataUnit.getSettings().set
        if self.actionstart or get("ColocalizationLowerThreshold")!=None:
            lower1=int(get("ColocalizationLowerThreshold"))
            upper1=int(get("ColocalizationUpperThreshold"))
            
            if self.actionstart:
                x1,y1=self.actionstart
                if self.mode=="upper":
                    upper1=x1
                else:
                    lower1=x1
                if self.mode=="upper" and upper1<lower1:
                    self.mode="lower"                    
                    upper1,lower1=lower1,upper1
                    set("ColocalizationLowerThreshold",lower1)
                    set("ColocalizationUpperThreshold",upper1)
                elif self.mode=="lower" and upper1<lower1:
                    self.mode="upper"
                    upper1,lower1=lower1,upper1
                    set("ColocalizationLowerThreshold",lower1)
                    set("ColocalizationUpperThreshold",upper1)
                    

        
            dc.SetPen(wx.Pen(wx.Colour(255,255,0),2))
            # vertical line 
            dc.DrawLine(lower1,0,lower1,150)
            # horizontal line
            #dc.DrawLine(lower1,255,upper1,255)
            # vertical line 2 
            dc.DrawLine(upper1,0,upper1,150)
            # horizontal line 2
            #dc.DrawLine(lower1,0,upper1,0)
            
            overlay=ImageOperations.getOverlay(upper1-lower1,150,(255,255,0),32)
            overlay=overlay.ConvertToBitmap()
            dc.DrawBitmap(overlay,lower1,0,1)
            if self.values:
                tot=0
                totth=0
                for i,val in enumerate(self.values):
                    tot+=val
                    if i>=lower1 and i<=upper1:totth+=val
                self.percent=totth/float(tot)
            
            if self.percent:
                dc.SetFont(wx.Font(8,wx.SWISS,wx.NORMAL,wx.NORMAL))
                
                dc.DrawText("%.2f%% of data selected"%(100*self.percent),10,182)
                
        
        dc.EndDrawing()
        dc = None


        
    def OnPaint(self,event):
        """
        Method: paintPreview()
        Created: 28.04.2005, KP
        Description: Does the actual blitting of the bitmap
        """
        dc=wx.BufferedPaintDC(self,self.buffer)#,self.buffer)
        

