# -*- coding: iso-8859-1 -*-

"""
 Unit: VisualizationModules
 Project: BioImageXD
 Created: 28.04.2005, KP
 Description:

 A module containing the various rendering modules for the visualization
 
 Modified 28.04.2005 KP - Created the class
          
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

import vtk
from Events import *
import ColorTransferEditor
import Dialogs

class VisualizationModule:
    """
    Class: VisualizationModule
    Created: 28.04.2005, KP
    Description: A class representing a visualization module
    """
    def __init__(self,parent):
        """
        Method: __init__(parent)
        Created: 28.04.2005, KP
        Description: Initialization
        """    
        self.name="Module"
        self.timepoint = -1
        self.parent = parent
        self.wxrenwin = parent.wxrenwin
        self.renWin = self.wxrenwin.GetRenderWindow()        
        
    def getName(self):
        """
        Method: getName()
        Created: 28.04.2005, KP
        Description: Return the name of this module
        """            
        return self.name
        
    def setDataUnit(self,dataunit):
        """
        Method: setDataUnit(self)
        Created: 28.04.2005, KP
        Description: Sets the dataunit this module uses for visualization
        """            
        self.dataUnit = dataunit
        
    def getDataUnit(self):
        """
        Method: getDataUnit()
        Created: 28.04.2005, KP
        Description: Returns the dataunit this module uses for visualization
        """     
        return self.dataUnit

    def showTimepoint(self,value):
        """
        Method: showTimepoint(tp)
        Created: 28.04.2005, KP
        Description: Set the timepoint to be displayed
        """          
        self.timepoint = value
        self.data = self.dataUnit.getTimePoint(value)
        self.updateRendering()

class VolumeModule(VisualizationModule):
    """
    Class: VolumeModule
    Created: 28.04.2005, KP
    Description: A volume rendering module
    """    
    def __init__(self,parent):
        """
        Method: __init__(parent)
        Created: 28.04.2005, KP
        Description: Initialization
        """     
        VisualizationModule.__init__(self,parent)   
        self.name = "Volume Rendering"
        self.quality = 0
        self.method=0
        self.opacityTransferFunction = vtk.vtkPiecewiseFunction()
        self.opacityTransferFunction.AddPoint(0, 0.0)
        self.opacityTransferFunction.AddPoint(255, 0.2)
        
        self.colorTransferFunction = None

        self.volumeProperty =  vtk.vtkVolumeProperty()
        self.volumeProperty.SetScalarOpacity(self.opacityTransferFunction)
        self.setQuality(0)
        self.volume = vtk.vtkVolume()
        self.volume.SetProperty(self.volumeProperty)
        self.setMethod(0)
        self.parent.getRenderer().AddVolume(self.volume)
        #self.updateRendering()
        
    def setDataUnit(self,dataunit):
        """
        Method: setDataUnit(self)
        Created: 28.04.2005, KP
        Description: Sets the dataunit this module uses for visualization
        """       
        VisualizationModule.setDataUnit(self,dataunit)
        self.colorTransferFunction = self.dataUnit.getColorTransferFunction()
        self.volumeProperty.SetColor(self.colorTransferFunction)
        
    def setOpacityTransferFunction(self,otf):
        """
        Method: setOpacityTransferFunction(otf)
        Created: 28.04.2005, KP
        Description: Set the opacity transfer function
        """ 
        self.opacityTransferFunction = otf
        self.volumeProperty.SetScalarOpacity(self.opacityTransferFunction)
        
        
    def setQuality(self,quality):
        """
        Method: setQuality(self,quality)
        Created: 28.04.2005, KP
        Description: Set the quality of rendering
        """ 
        print "Setting quality to ",quality
        if quality==0:
            self.volumeProperty.ShadeOn()
            self.volumeProperty.SetInterpolationTypeToLinear()
            
        elif quality==1:
            self.volumeProperty.ShadeOff()
            self.volumeProperty.SetInterpolationTypeToNearest()
        elif quality>1:
            if self.method == 0:
                self.mapper.SetImageSampleDistance(quality)
                print "Image Sample distance=",self.mapper.GetImageSampleDistance()
            else:
                self.mapper.SetMaximumNumberOfPlanes(25-quality)
                print "Maximum planes=",self.mapper.GetMaximumNumberOfPlanes()
            

    def setMethod(self,method):
        """
        Method: setMethod(self,method)
        Created: 28.04.2005, KP
        Description: Set the rendering method used
        """             
        self.method=method
        #Ray Casting, RGBA Ray Casting, Texture Mapping, MIP
        composites = [vtk.vtkVolumeRayCastCompositeFunction,
                      vtk.vtkVolumeRayCastRGBCompositeFunction,None,
                      vtk.vtkVolumeRayCastMIPFunction]
        if method in [0,1,3]:
            self.mapper = vtk.vtkVolumeRayCastMapper()
            self.mapper.SetVolumeRayCastFunction(composites[method]())
        else: # texture mapping
            self.mapper = vtk.vtkVolumeTextureMapper2D()
        
        self.volume.SetMapper(self.mapper)    

    def updateRendering(self):
        """
        Method: updateRendering()
        Created: 28.04.2005, KP
        Description: Update the rendering of this module
        """             
        self.mapper.SetInput(self.data)
        self.wxrenwin.Render()
    


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
        #self.module.setMethod(method)
      
    def setModule(self,module):
        """
        Method: setModule(module)
        Created: 28.04.2005, KP
        Description: Set the module to be configured
        """  
        print "Module is",module
        self.module = module
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
