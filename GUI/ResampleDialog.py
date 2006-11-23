4#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: ResampleDialog
 Project: BioImageXD
 Created: 1.09.2005, KP
 Description:

 A dialog for importing different kinds of data to form a .bxd file
 
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
__version__ = "$Revision: 1.40 $"
__date__ = "$Date: 2005/01/13 14:52:39 $"
import sys
import Logging
import wx
import UIElements
import string

class ResampleDialog(wx.Dialog):
    """
    Created: 1.09.2005, KP
    Description: A dialog for resampling a dataset
    """
    def __init__(self, parent,imageMode=1):
        """
        Created: 1.09.2005, KP
        Description: Initialize the dialog
        """    
        wx.Dialog.__init__(self, parent, -1, 'Resample dataset')
        
        self.sizer=wx.GridBagSizer()
        self.btnsizer=self.CreateButtonSizer(wx.OK|wx.CANCEL)
    
        self.createResample()
        self.sizer.Add(self.btnsizer,(1,0),flag=wx.EXPAND|wx.RIGHT|wx.LEFT)
        wx.EVT_BUTTON(self,wx.ID_OK,self.onOkButton)
        self.result=0
        self.currSize=(512,512,25)
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.blockDimUpdate=0
        self.blockFactorUpdate=0
        self.sizer.Fit(self)
        
    def onOkButton(self,event):
        """
        Created: 21.04.2005, KP
        Description: Executes the procedure
        """
        for i in self.dataUnits:
            print "\nSETTING RESAMPLE DIMS TO ",self.currSize
            i.dataSource.setResampleDimensions(self.currSize)
        
        self.result=1
        self.Close()

        
    def setDataUnits(self,dataunits):
        """
        Created: 1.09.2005, KP
        Description: Set the dataunits to be resampled
        """        
        self.dataUnits=dataunits
        
        x,y,z=self.dataUnits[0].getDimensions()
        self.dims=(x,y,z)       
        self.newDimX.SetValue("%d"%x)
        self.newDimY.SetValue("%d"%y)
        self.newDimZ.SetValue("%d"%z)
        self.dimsLbl.SetLabel(self.currDimText%(x,y,z))
        self.onUpdateDims(None)
        
    def onUpdateDims(self,evt):
        """
        Created: 1.09.2005, KP
        Description: Update the dimensions
        """
        if self.blockDimUpdate:
            return        
        rx,ry,rz=self.dims
        try:
            rx=int(self.newDimX.GetValue())
            ry=int(self.newDimY.GetValue())
            rz=int(self.newDimZ.GetValue())
        except:
            pass
        self.currSize=(rx,ry,rz)
        x,y,z=self.dataUnits[0].dataSource.getOriginalDimensions()
        xf=rx/float(x)
        yf=ry/float(y)
        zf=rz/float(z)
        #self.factorsLbl.SetLabel(self.currFactorText%(xf,yf,zf))
        self.blockFactorUpdate=1
        self.factorX.SetValue("%.2f"%xf)
        self.factorY.SetValue("%.2f"%yf)
        self.factorZ.SetValue("%.2f"%zf)
        self.blockFactorUpdate=0
        
    def onUpdateFactors(self,evt):
        """
        Created: 23.07.2006, KP
        Description: Update the factors, resulting in change in the dimensions
        """
        if self.blockFactorUpdate:
            print "Blocking factor update"
            return
        x,y,z=self.dataUnits[0].dataSource.getOriginalDimensions()
        fx=1
        fy=1
        fz=1
        try:
            fx=float(self.factorX.GetValue())
            fy=float(self.factorY.GetValue())
            fz=float(self.factorZ.GetValue())
        except:
            pass
        x*=fx
        y*=fy
        z*=fz
        #self.factorsLbl.SetLabel(self.currFactorText%(xf,yf,zf))
        self.blockDimUpdate=1
        self.newDimX.SetValue("%d"%x)
        self.newDimY.SetValue("%d"%y)
        self.newDimZ.SetValue("%d"%z)
        self.currSize = (x,y,z)
        self.blockDimUpdate=0


    def createResample(self):
        """
        Created: 1.09.2005, KP
        Description: Creates the GUI for setting the resampled size
        """            
        box=wx.StaticBox(self,-1,"Resample dataset")
        boxsizer=wx.StaticBoxSizer(box,wx.VERTICAL)
        panel=wx.Panel(self,-1)
        boxsizer.Add(panel,1)
        
        sizer=wx.GridBagSizer()
        self.currDimText=u"Current dimensions: %d x %d x %d"
        self.dimsLbl=wx.StaticText(panel,-1,self.currDimText%(0,0,0))
        n=0
        sizer.Add(self.dimsLbl,(n,0),flag=wx.EXPAND|wx.LEFT|wx.RIGHT)
        n+=1
        #self.currFactorText=u"Scale factors: %.2f x %.2f x %.2f"
        #self.factorsLbl=wx.StaticText(panel,-1,self.currFactorText%(1,1,1))
        #sizer.Add(self.factorsLbl,(n,0),flag=wx.EXPAND|wx.LEFT|wx.RIGHT)
        self.factorBox = wx.BoxSizer(wx.HORIZONTAL)
        factorLabel=wx.StaticText(panel,-1,"Scale factors:")
        self.factorBox.Add(factorLabel)
        self.factorX = wx.TextCtrl(panel,-1,"%.2f"%1,size=(50,-1))
        self.factorBox.Add(self.factorX)    
        x1=wx.StaticText(panel,-1,"x")
        self.factorBox.Add(x1)
        self.factorY = wx.TextCtrl(panel,-1,"%.2f"%1,size=(50,-1))
        self.factorBox.Add(self.factorY)    
        x2=wx.StaticText(panel,-1,"x")
        self.factorBox.Add(x2)
        self.factorZ = wx.TextCtrl(panel,-1,"%.2f"%1,size=(50,-1))
        self.factorBox.Add(self.factorZ)    

        sizer.Add(self.factorBox, (n,0),flag=wx.EXPAND|wx.LEFT|wx.RIGHT)
        n+=1
        
        newDimXLbl=wx.StaticText(panel,-1,"New X dimension: ")
        newDimYLbl=wx.StaticText(panel,-1,"New Y dimension: ")
        newDimZLbl=wx.StaticText(panel,-1,"New Z dimension: ")
        val=UIElements.AcceptedValidator
        self.newDimX=wx.TextCtrl(panel,-1,"512",validator=val(string.digits))
        self.newDimY=wx.TextCtrl(panel,-1,"512",validator=val(string.digits))
        self.newDimZ=wx.TextCtrl(panel,-1,"25",validator=val(string.digits))
        
        self.newDimX.Bind(wx.EVT_TEXT,self.onUpdateDims)
        self.newDimY.Bind(wx.EVT_TEXT,self.onUpdateDims)
        self.newDimZ.Bind(wx.EVT_TEXT,self.onUpdateDims)
        self.factorX.Bind(wx.EVT_TEXT,self.onUpdateFactors)
        self.factorY.Bind(wx.EVT_TEXT,self.onUpdateFactors)
        self.factorZ.Bind(wx.EVT_TEXT,self.onUpdateFactors)
        
        
        sizer.Add(newDimXLbl,(n,0))
        sizer.Add(self.newDimX,(n,1))
        n+=1
        sizer.Add(newDimYLbl,(n,0))
        sizer.Add(self.newDimY,(n,1))
        n+=1
        sizer.Add(newDimZLbl,(n,0))
        sizer.Add(self.newDimZ,(n,1))
        
        panel.SetSizer(sizer)
        panel.SetAutoLayout(1)
        sizer.Fit(panel)
        
        self.sizer.Add(boxsizer,(0,0))

        self.panel=panel
