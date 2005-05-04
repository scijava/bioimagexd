# -*- coding: iso-8859-1 -*-

"""
 Unit: ModuleConfiguration
 Project: BioImageXD
 Created: 30.04.2005, KP
 Description:

 A module containing the configuration dialogs for various rendering 
 modules.
 
 Modified 30.04.2005 KP - Created the class by splitting VisualizationModules.py
          
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

import vtk
from Events import *
from VisualizationModules  import *
import ColorTransferEditor
import Dialogs



class ModuleConfiguration(wx.MiniFrame):
    """
    Class: ModuleConfiguration
    Created: 28.04.2005, KP
    Description: A base class for module configuration dialogs
    """    
    def __init__(self,parent,name):
        """
        Method: __init__(parent)
        Created: 28.04.2005, KP
        Description: Initialization
        """     
        wx.MiniFrame.__init__(self,parent,-1,"Configure: %s"%name)
        self.sizer = wx.GridBagSizer()
        self.parent = parent
        self.name = name
        
        self.buttonBox = wx.BoxSizer(wx.HORIZONTAL)
        self.okButton = wx.Button(self,-1,"Ok")
        self.applyButton = wx.Button(self,-1,"Apply")
        self.cancelButton = wx.Button(self,-1,"Cancel")
        
        self.okButton.Bind(wx.EVT_BUTTON,self.onOk)
        self.applyButton.Bind(wx.EVT_BUTTON,self.onApply)
        self.cancelButton.Bind(wx.EVT_BUTTON,self.onCancel)
        
        
        self.buttonBox.Add(self.okButton)
        self.buttonBox.Add(self.applyButton)
        self.buttonBox.Add(self.cancelButton)
        
        self.contentSizer = wx.GridBagSizer()
        self.sizer.Add(self.contentSizer,(0,0))
        
        self.line = wx.StaticLine(self,-1)
        self.sizer.Add(self.line,(1,0),flag=wx.EXPAND|wx.LEFT|wx.RIGHT)
        self.sizer.Add(self.buttonBox,(2,0))
        
        self.initializeGUI()
        
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)
        
        self.findModule()
        
    def onCancel(self,event):
        """
        Method: onCancel()
        Created: 28.04.2005, KP
        Description: Close this dialog
        """     
        self.Close()
        
    def onOk(self,event):
        """
        Method: onApply()
        Created: 28.04.2005, KP
        Description: Apply changes and close
        """ 
        self.onApply(None)
        self.Close()
        
    def findModule(self):
        """
        Method: findModule()
        Created: 28.04.2005, KP
        Description: Refresh the modules affected by this configuration
        """     
        modules = self.parent.getModules()
        for module in modules:
            if module.getName() == self.name:
                self.setModule(module)
                print "Configuring module",module
                return

    def setModule(self,module):
        """
        Method: setModule(module)
        Created: 28.04.2005, KP
        Description: Set the module to be configured
        """  
        print "Module is",module
        self.module = module

class VolumeConfiguration(ModuleConfiguration):
    def __init__(self,parent):
        """
        Method: __init__(parent)
        Created: 28.04.2005, KP
        Description: Initialization
        """     
        ModuleConfiguration.__init__(self,parent,"Volume Rendering")
        self.method=0
    
    def initializeGUI(self):
        """
        Method: initializeGUI()
        Created: 28.04.2005, KP
        Description: Initialization
        """  
        self.colorLbl = wx.StaticText(self,-1,"Dataset palette:")
        #self.colorBtn = ColorTransferEditor.CTFButton(self,alpha=1)
        self.colorPanel = ColorTransferEditor.ColorTransferEditor(self,alpha=1)
        #self.colorPanel.setColorTransferFunction(self.ctf)

        self.contentSizer.Add(self.colorLbl,(0,0))
        self.contentSizer.Add(self.colorPanel,(1,0))
        
        self.methodLbl = wx.StaticText(self,-1,"Volume rendering method:")
        self.moduleChoice = wx.Choice(self,-1,choices=["Ray Casting","Ray Casting for RGBA datasets","Texture Mapping","Maximum Intensity Projection"])
        self.moduleChoice.Bind(wx.EVT_CHOICE,self.onSelectMethod)
      
        self.contentSizer.Add(self.methodLbl,(2,0))
        self.contentSizer.Add(self.moduleChoice,(3,0))
        
        self.qualityLbl = wx.StaticText(self,-1,"Rendering quality:")
        self.qualitySlider = wx.Slider(self,value=0, minValue=0,maxValue = 10,
        style=wx.HORIZONTAL|wx.SL_AUTOTICKS|wx.SL_LABELS,size=(250,-1))
        self.contentSizer.Add(self.qualityLbl,(4,0),flag=wx.EXPAND|wx.LEFT|wx.RIGHT)
        self.contentSizer.Add(self.qualitySlider,(5,0))
        
    def onSelectMethod(self,event):
        """
        Method: onSelectMethod
        Created: 28.04.2005, KP
        Description: Select the volume rendering method
        """  
        self.method = self.moduleChoice.GetSelection()
            
      
    def setModule(self,module):
        """
        Method: setModule(module)
        Created: 28.04.2005, KP
        Description: Set the module to be configured
        """  
        ModuleConfiguration.setModule(self,module)
        ctf= module.getDataUnit().getColorTransferFunction()
        self.colorPanel.setColorTransferFunction(ctf)
        
    def onApply(self,event):
        """
        Method: onApply()
        Created: 28.04.2005, KP
        Description: Apply the changes
        """     
        #if self.colorPanel.isChanged():
        otf = self.colorPanel.getOpacityTransferFunction()
        self.module.setOpacityTransferFunction(otf)
        self.module.setMethod(self.method)
        self.module.setQuality(self.qualitySlider.GetValue())
        self.module.updateRendering()

class SurfaceConfiguration(ModuleConfiguration):
    def __init__(self,parent):
        """
        Method: __init__(parent)
        Created: 28.04.2005, KP
        Description: Initialization
        """     
        ModuleConfiguration.__init__(self,parent,"Surface Rendering")
        self.method=0
        
    
    def initializeGUI(self):
        """
        Method: initializeGUI()
        Created: 28.04.2005, KP
        Description: Initialization
        """          
        self.methodLbl = wx.StaticText(self,-1,"Surface rendering method:")
        self.moduleChoice = wx.Choice(self,-1,choices=["Contour Filter","Marching Cubes","Iso-Surface Volume Rendering"])
        self.moduleChoice.SetSelection(1)
        self.moduleChoice.Bind(wx.EVT_CHOICE,self.onSelectMethod)
        n=0
        self.contentSizer.Add(self.methodLbl,(n,0))
        n+=1
        self.contentSizer.Add(self.moduleChoice,(n,0))
        n+=1
        self.normalsBox = wx.CheckBox(self,-1,"Smooth surface with surface normals")
        self.normalsBox.SetValue(0)
        self.normalsBox.Bind(wx.EVT_CHECKBOX,self.onSetSmoothing)
        self.featureLbl=wx.StaticText(self,-1,"Feature angle of normals:")
        self.featureAngle = wx.TextCtrl(self,-1,"45")
        self.featureAngle.Enable(0)
        
        self.contentSizer.Add(self.normalsBox,(n,0))
        n+=1
        self.contentSizer.Add(self.featureLbl,(n,0))
        n+=1
        self.contentSizer.Add(self.featureAngle,(n,0))
        n+=1
        self.isoValueLbl = wx.StaticText(self,-1,"Iso value:")
        self.isoSlider = wx.Slider(self,value=128, minValue=0,maxValue = 255,
        style=wx.HORIZONTAL|wx.SL_AUTOTICKS|wx.SL_LABELS,size=(255,-1))
        
        
        self.contentSizer.Add(self.isoValueLbl,(n,0),flag=wx.EXPAND|wx.LEFT|wx.RIGHT)
        n+=1
        self.contentSizer.Add(self.isoSlider,(n,0))
        n+=1
        self.rangeLbl = wx.StaticText(self,-1,"Generate surfaces in range:")
        self.isoRangeBegin = wx.SpinCtrl(self,-1,"",style=wx.SP_VERTICAL)
        
        self.isoRangeEnd = wx.SpinCtrl(self,-1,"",style=wx.SP_VERTICAL)
        self.amntLbl = wx.StaticText(self,-1,"Amount of surfaces:")
        self.isoRangeSurfaces = wx.SpinCtrl(self,-1,"",style=wx.SP_VERTICAL)

        self.isoRangeSurfaces.SetRange(0,255)
        self.isoRangeSurfaces.SetValue(0)
        self.isoRangeBegin.SetRange(0,255)
        self.isoRangeBegin.SetValue(0)
        self.isoRangeEnd.SetRange(0,255)
        self.isoRangeEnd.SetValue(255)
        
        box=wx.BoxSizer(wx.HORIZONTAL)
        box.Add(self.isoRangeBegin)
        box.Add(self.isoRangeEnd)
        
        self.contentSizer.Add(self.rangeLbl ,(n,0))
        n+=1
        self.contentSizer.Add(box,(n,0))
        n+=1
        self.contentSizer.Add(self.amntLbl,(n,0))
        n+=1
        self.contentSizer.Add(self.isoRangeSurfaces,(n,0))
        n+=1

    def onSetSmoothing(self,event):
        """
        Method: onSetSmoothing
        Created: 30.04.2005, KP
        Description: Enable/Disable smoothing
        """     
        flag=event.IsChecked()
        self.featureAngle.Enable(flag)


    def onApply(self,event):
        """
        Method: onApply()
        Created: 30.04.2005, KP
        Description: Apply the changes
        """     
        self.module.setMethod(self.method)
        if self.normalsBox.GetValue():
            angle=float(self.featureAngle.GetValue())
            print "Setting generated normals to",angle
            self.module.setGenerateNormals(angle)
        if self.isoRangeSurfaces.GetValue() != 0:
            start=int(self.isoRangeBegin.GetValue())
            end=int(self.isoRangeEnd.GetValue())
            n=int(self.isoRangeSurfaces.GetValue())
            self.module.setContourRange(start,end,n)
        else:
            self.module.setIsoValue(self.isoSlider.GetValue())

        self.module.updateRendering()
        
    def onSelectMethod(self,event):
        """
        Method: onSelectMethod
        Created: 30.04.2005, KP
        Description: Select the surface rendering method
        """  
        self.method = self.moduleChoice.GetSelection()
        flag=(self.method!=2)
        self.isoRangeBegin.Enable(flag)
        self.isoRangeEnd.Enable(flag)
        self.isoRangeSurfaces.Enable(flag)
        
class ImagePlaneConfiguration(ModuleConfiguration):
    def __init__(self,parent):
        """
        Method: __init__(parent)
        Created: 04.05.2005, KP
        Description: Initialization
        """     
        ModuleConfiguration.__init__(self,parent,"Orthogonal Slices")
    
    def initializeGUI(self):
        """
        Method: initializeGUI()
        Created: 28.04.2005, KP
        Description: Initialization
        """  
        
        self.xLbl = wx.StaticText(self,-1,"X Slice:")
        self.xSlider = wx.Slider(self,value=0, minValue=0,maxValue = 10,
        style=wx.HORIZONTAL|wx.SL_AUTOTICKS|wx.SL_LABELS,size=(250,-1))
        
        self.yLbl = wx.StaticText(self,-1,"Y Slice:")
        self.ySlider = wx.Slider(self,value=0, minValue=0,maxValue = 10,
        style=wx.HORIZONTAL|wx.SL_AUTOTICKS|wx.SL_LABELS,size=(250,-1))
        
        self.zLbl = wx.StaticText(self,-1,"Z Slice:")
        self.zSlider = wx.Slider(self,value=0, minValue=0,maxValue = 10,
        style=wx.HORIZONTAL|wx.SL_AUTOTICKS|wx.SL_LABELS,size=(250,-1))
        
        self.contentSizer.Add(self.xLbl,(0,0),flag=wx.EXPAND|wx.LEFT|wx.RIGHT)
        self.contentSizer.Add(self.xSlider,(1,0))

        self.contentSizer.Add(self.yLbl,(2,0),flag=wx.EXPAND|wx.LEFT|wx.RIGHT)
        self.contentSizer.Add(self.ySlider,(3,0))

        self.contentSizer.Add(self.zLbl,(4,0),flag=wx.EXPAND|wx.LEFT|wx.RIGHT)
        self.contentSizer.Add(self.zSlider,(5,0))
            
        self.xSlider.Bind(wx.EVT_SCROLL,self.onUpdateSlice)
        self.ySlider.Bind(wx.EVT_SCROLL,self.onUpdateSlice)
        self.zSlider.Bind(wx.EVT_SCROLL,self.onUpdateSlice)
        
    def setModule(self,module):
        """
        Method: setModule(module)
        Created: 28.04.2005, KP
        Description: Set the module to be configured
        """  
        ModuleConfiguration.setModule(self,module)
        ext=module.getDataUnit().getTimePoint(0).GetWholeExtent()
        x,y,z=ext[1],ext[3],ext[5]
        print "x=%d, y=%d, z=%d"%(x,y,z)
        self.xSlider.SetRange(0,x)
        self.xSlider.SetValue(x/2)
        
        self.ySlider.SetRange(0,y)
        self.ySlider.SetValue(y/2)
        
        self.zSlider.SetRange(0,z)
        self.zSlider.SetValue(z/2)
        
    def onUpdateSlice(self,event):
        """
        Method: onUpdateSlice(self,event):
        Created: 04.05.2005, KP
        Description: Update the slice to be displayed
        """  
        x=self.xSlider.GetValue()
        y=self.ySlider.GetValue()
        z=self.zSlider.GetValue()
        self.module.setDisplaySlice(x,y,z)
        self.module.updateRendering()
    
        
    def onApply(self,event):
        """
        Method: onApply()
        Created: 28.04.2005, KP
        Description: Apply the changes
        """     
        self.module.updateRendering()
