# -*- coding: iso-8859-1 -*-
"""
 Unit: MaskTray
 Project: BioImageXD
 Created: 20.06.2006, KP
 Description:

 A panel that shows all the masks created in the software
 
 Copyright (C) 2006  BioImageXD Project
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

import wx
import  wx.lib.scrolledpanel as scrolled
import  wx.lib.buttons  as  buttons

import ImageOperations
import vtk

masks = []

class Mask:
    """
    Class: Mask
    Created: 20.06.2006, KP
    Description: A mask class
    """
    def __init__(self,name, size, image):
        """
        Method: __init__(parent)
        Created: 20.06.2006, KP
        Description: Initialization
        """
        self.name = name
        self.size = size
        self.image = image
        self.ctf = vtk.vtkColorTransferFunction()
        self.ctf.AddRGBPoint(0,0,0,0)
        self.ctf.AddRGBPoint(255,1.0,1.0,1.0)
        
    def getMaskImage(self):
        """
        Method: getMaskImage
        Created: 26.06.2006, KP
        Description: Return the mask image
        """   
        return self.image
        
    def getAsBitmap(self, bg = wx.Colour(255,255,255)):
        """
        Method: getAsBitmap
        Created: 20.06.2006, KP
        Description: Return a preview bitmap of the mask
        """           
        preview = ImageOperations.getMIP(self.image, self.ctf)
        preview = ImageOperations.vtkImageDataToWxImage(preview)
        preview.Rescale(80,80)
        preview = preview.ConvertToBitmap()
        
        bmp = wx.EmptyBitmap(100,120,-1)
        dc = wx.MemoryDC()
        dc.SelectObject(bmp)
        dc.BeginDrawing()
        dc.SetBackground(wx.Brush(bg))
        dc.Clear()
        dc.DrawBitmap(preview, 10,10)
        
        dc.SetFont(wx.Font(9,wx.SWISS,wx.NORMAL,wx.BOLD))
        dc.DrawText(self.name, 10,90)
        
        dc.SetTextForeground(wx.Colour(40,40,40))
        dc.SetFont(wx.Font(8,wx.SWISS,wx.NORMAL,wx.NORMAL))
        x,y,z=self.size
        dc.DrawText("%d x %d x %d"%(x,y,z),10,105)
        
                        
        dc.EndDrawing()
        dc.SelectObject(wx.NullBitmap)
        dc = None    
        return bmp
        


class MaskTray(wx.MiniFrame):
    """
    Class: MaskTray
    Created: 20.06.2006, KP
    Description: A frame used to let the user select from the different masks
    """
    def __init__(self,parent,**kws):
        """
        Method: __init__(parent)
        Created: 20.06.2006, KP
        Description: Initialization
        """          
        wx.MiniFrame.__init__(self, parent, -1, "Mask selection", size=(400,200),style = wx.DEFAULT_FRAME_STYLE)
                
        self.panel = wx.Panel(self, -1)
        self.sizer = wx.GridBagSizer()
        self.panel.SetSizer(self.sizer)
        self.panel.SetAutoLayout(1)
        
        self.masks = []
        self.buttons = []
        self.selectedMask=None
        
        self.scrollSizer = wx.GridBagSizer()
        self.scroll = scrolled.ScrolledPanel(self.panel, -1,size=(400,150))
        self.scroll.SetSizer(self.scrollSizer)
        self.scroll.SetAutoLayout(1)
        self.scroll.SetupScrolling()
        
        self.sizer.Add(self.scroll,(0,0),flag=wx.EXPAND|wx.ALL)
        
        
        self.buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.okButton = wx.Button(self.panel, -1, "Select")
        self.nomaskButton = wx.Button(self.panel, -1, "No mask")
        self.cancelButton = wx.Button(self.panel, -1, "Cancel")
        
        self.okButton.Bind(wx.EVT_BUTTON,self.onSelectMask)
        self.nomaskButton.Bind(wx.EVT_BUTTON,self.onSetNoMask)
        self.cancelButton.Bind(wx.EVT_BUTTON,self.onCancel)
        
        self.buttonSizer.Add(self.cancelButton,0,wx.ALIGN_RIGHT)
        self.buttonSizer.Add((20,20),0,wx.EXPAND)
        self.buttonSizer.Add(self.nomaskButton,0,wx.ALIGN_RIGHT)
        self.buttonSizer.Add((20,20),0,wx.EXPAND)
        self.buttonSizer.Add(self.okButton,0,wx.ALIGN_RIGHT)
        
        
        self.sizer.Add(self.buttonSizer,(1,0),flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER)
        
        self.panel.Fit()
        
    def onSetNoMask(self,evt):
        """
        Method: onSetNoMask
        Created: 26.06.2006, KP
        Description: Disable the use of masks
        """   
        self.dataUnit.setMask(None)
        self.Close(True)
        
    def addMask(self, mask = None, name = "Mask", imagedata = None):
        """
        Method: methodName
        Created: 20.06.2006, KP
        Description: Method desc
        """   
        if not mask and (name and imagedata):
            m = Mask(name, imagedata.GetDimensions(), imagedata)
        elif mask:
            m = mask
        else:
            raise "No mask given"
        self.masks.append(m)
        
        bmp = m.getAsBitmap(self.GetBackgroundColour())
                
                
        b = buttons.GenBitmapToggleButton(self.scroll, -1, bmp)
        self.Bind(wx.EVT_BUTTON, self.onToggleButton, b)
        self.buttons.append(b)
    
        n = len(self.masks)
        
        self.scrollSizer.Add(b, (0,n-1))        
        self.scroll.SetupScrolling()
        self.Layout()
        
    def onToggleButton(self,evt):
        """
        Method: onToggleButton
        Created: 20.06.2006, KP
        Description: A callback for when the user toggles a button
        """   
        for i,btn in enumerate(self.buttons):
            if btn.GetId() != evt.GetId():
                btn.SetValue(0)
            else:
                self.selectedMask = self.masks[i]
                
    def setDataUnit(self,dataUnit):
        """
        Method: setDataUnit
        Created: 20.06.2006, KP
        Description: Set the dataunit to which the selected mask will be applied
        """   
        self.dataUnit = dataUnit
        
    def onSelectMask(self, evt):
        """
        Method: onSelectMask
        Created: 20.06.2006, KP
        Description: A callback for when the user has selected a mask
        """   
        if self.selectedMask:
            self.dataUnit.setMask(self.selectedMask)
        self.Close(True)
        
    def onCancel(self, evt):
        """
        Method: onCancel
        Created: 20.06.2006, KP
        Description: A callback for when the user wishes to cancel the selection
        """   
        self.Close(True)
