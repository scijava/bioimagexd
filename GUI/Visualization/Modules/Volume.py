# -*- coding: iso-8859-1 -*-

"""
 Unit: Volume
 Project: BioImageXD
 Created: 28.04.2005, KP
 Description:

 A module containing the volume rendering module for the visualization
 
 Modified 24.05.2005 KP - Split the class to a module of it's own
          
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
import ColorTransferEditor
import Dialogs
from Visualization.VisualizationModules import *

def getClass():return VolumeModule
def getConfig():return VolumeConfigurationPanel
def getName():return "Volume Rendering"


class VolumeModule(VisualizationModule):
    """
    Class: VolumeModule
    Created: 28.04.2005, KP
    Description: A volume Rendering module
    """    
    def __init__(self,parent,visualizer,**kws):
        """
        Method: __init__(parent)
        Created: 28.04.2005, KP
        Description: Initialization
        """     
        VisualizationModule.__init__(self,parent,visualizer,**kws)   
        #self.name = "Volume Rendering"
        self.quality = 10
        self.method=2
        self.opacityTransferFunction = vtk.vtkPiecewiseFunction()
        self.opacityTransferFunction.AddPoint(0, 0.0)
        self.opacityTransferFunction.AddPoint(255, 0.2)
        
        self.colorTransferFunction = None

        self.volumeProperty =  vtk.vtkVolumeProperty()
        self.volumeProperty.SetScalarOpacity(self.opacityTransferFunction)
        self.setQuality(10)
        self.volume = vtk.vtkVolume()
        self.actor = self.volume
        self.volume.SetProperty(self.volumeProperty)
        self.setMethod(2)
        self.parent.getRenderer().AddVolume(self.volume)
        self.setShading(0)
        #self.updateRendering()
        
    def setDataUnit(self,dataunit):
        """
        Method: setDataUnit(self)
        Created: 28.04.2005, KP
        Description: Sets the dataunit this module uses for visualization
        """       
        print "Volume got dataunit",dataunit
        if dataunit.getBitDepth()==32:
            self.setMethod(1)
        VisualizationModule.setDataUnit(self,dataunit)
        # If 32 bit data, use method 1
        if self.visualizer.getProcessedMode():
            print "Using ctf of first source"
            self.colorTransferFunction = self.dataUnit.getSourceDataUnits()[0].getColorTransferFunction()
        else:    
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
        
    def setVolumeProAcceleration(self,acc):
        """
        Method: setVolumeProAcceleration(acceleration)
        Created: 15.05.2005, KP
        Description: Set volume pro acceleration
        """ 
        self.method=-1
        try:
            self.mapper = vtk.vtkVolumeProMapper()
        except:
            # no support for volumepro available
            print "No support for volumepro"
            self.haveVolpro=0
            self.volpro.Enable(0)
            self.volpro.SetValue(0)
            return
        cmd="self.mapper.SetBlendModeTo%s()"%acc
        print "Setting blending mode to ",acc
        eval(cmd)
        print "Setting parallel projection"
        self.renderer.GetActiveCamera().ParallelProjectionOn()
        
    def setQuality(self,quality,raw=0):
        """
        Method: setQuality(self,quality)
        Created: 28.04.2005, KP
        Description: Set the quality of Rendering
        """ 
        if self.method<0:return 0
        if raw:
            print "Setting quality setting to raw",quality
            if self.method == 2:
                print "Setting maximum number of planes to ",quality
                self.mapper.SetMaximumNumberOfPlanes(quality)
            else:
                print "Setting sample distance to ",quality
                self.mapper.SetSampleDistance(quality)
            return quality
            
        else:
            print "Setting quality to ",quality
        if quality==10:
            self.volumeProperty.SetInterpolationTypeToLinear()            
        elif quality==9:
            self.volumeProperty.SetInterpolationTypeToNearest()
        elif quality<9:
            quality=10-quality
            if self.method != 2:
                self.mapper.SetSampleDistance(quality)
                return quality
                print "Image Sample distance=",self.mapper.GetSampleDistance()
            else:
                self.mapper.SetMaximumNumberOfPlanes(25-quality)
                print "Maximum planes=",self.mapper.GetMaximumNumberOfPlanes()
                return 25-quality
        return 0

    def setMethod(self,method):
        """
        Method: setMethod(self,method)
        Created: 28.04.2005, KP
        Description: Set the Rendering method used
        """             
        self.vtkcvs=0
        try:
            from vtk import vtkFixedPointVolumeRayCastMapper
            self.vtkcvs=1

        except:
            pass
        if self.vtkcvs:
           rgbf=None
        else:
            rgbf=vtk.vtkVolumeRayCastRGBCompositeFunction
        self.method=method
        print "Setting volume rendering method to ",method
        #Ray Casting, RGBA Ray Casting, Texture Mapping, MIP
        composites = [vtk.vtkVolumeRayCastCompositeFunction,
                      rgbf,
                      None,
                      vtk.vtkVolumeRayCastMIPFunction,
                      vtk.vtkVolumeRayCastIsosurfaceFunction
                      ]
        if self.vtkcvs and method == 1:
            self.mapper = vtk.vtkFixedPointVolumeRayCastMapper()
            self.volumeProperty.IndependentComponentsOff()
        #elif method==3:
        #    self.mapper=vtk.vtkVolumeShearWarpMapper()
            
        elif method in [0,1,3,4]:
            if self.vtkcvs:
                self.mapper = vtk.vtkFixedPointVolumeRayCastMapper()
                self.volumeProperty.IndependentComponentsOff()
            else:
                self.mapper = vtk.vtkVolumeRayCastMapper()
                self.function = composites[method]()
                print "using function",self.function
                self.mapper.SetVolumeRayCastFunction(self.function)
        elif method==2: # texture mapping
            self.mapper = vtk.vtkVolumeTextureMapper2D()
        
        self.volume.SetMapper(self.mapper)    
        
#        self.renderer.GetActiveCamera().ParallelProjectionOff()

    def updateRendering(self,input = None):
        """
        Method: updateRendering()
        Created: 28.04.2005, KP
        Description: Update the Rendering of this module
        """             
        if not input:
            input=self.data
        print "Rendering: ",self.mapper.__class__
        self.mapper.SetInput(input)
#        print "self.mapper=",self.mapper
        self.mapper.Update()
        self.parent.Render()
        
    def disableRendering(self):
        """
        Method: disableRendering()
        Created: 30.04.2005, KP
        Description: Disable the Rendering of this module
        """          
        self.renderer.RemoveVolume(self.volume)
        self.wxrenwin.Render()
        
    def enableRendering(self):
        """
        Method: enableRendering()
        Created: 15.05.2005, KP
        Description: Enable the Rendering of this module
        """          
        self.renderer.AddVolume(self.volume)
        self.wxrenwin.Render()        
        
    
class VolumeConfiguration(ModuleConfiguration):
    def __init__(self,parent,visualizer):
        """
        Method: __init__(parent)
        Created: 28.04.2005, KP
        Description: Initialization
        """     
        
        ModuleConfiguration.__init__(self,parent,"Volume Rendering")
        self.panel=VolumeConfigurationPanel(self,visualizer)
        

class VolumeConfigurationPanel(ModuleConfigurationPanel):
    def __init__(self,parent,visualizer,name="Volume Rendering",**kws):
        """
        Method: __init__(parent)
        Created: 28.04.2005, KP
        Description: Initialization
        """     
        self.method=2
        ModuleConfigurationPanel.__init__(self,parent,visualizer,name,**kws)
        self.editFlag=0

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

        n=0
        self.contentSizer.Add(self.colorLbl,(n,0))
        n+=1
        self.contentSizer.Add(self.colorPanel,(n,0))
        n+=1
        
        modes = ["Ray Casting","Ray Casting for RGBA datasets","Texture Mapping","Maximum Intensity Projection"]
        try:
            volpro=vtk.vtkVolumeProMapper()
            self.haveVolpro=1
            if volpro.GetNumberOfBoards():
                self.haveVolpro=1
        except:
            self.haveVolpro=0
        if self.haveVolpro:
            modes.append("Minimum Intensity Projection")
        
        self.methodLbl = wx.StaticText(self,-1,"Volume rendering method:")
        self.moduleChoice = wx.Choice(self,-1,choices = modes)
    
        self.moduleChoice.Bind(wx.EVT_CHOICE,self.onSelectMethod)
        self.moduleChoice.SetSelection(self.method)
        
      
        self.contentSizer.Add(self.methodLbl,(n,0))
        n+=1
        self.contentSizer.Add(self.moduleChoice,(n,0))
        n+=1
            
        if self.haveVolpro:
            self.volpro=wx.CheckBox(self,-1,"Use VolumePro acceleration")
            self.volpro.Enable(0)
            self.contentSizer.Add(self.volpro,(n,0))
            n+=1
        self.qualityLbl = wx.StaticText(self,-1,"Rendering quality:")
        self.qualitySlider = wx.Slider(self,value=10, minValue=0,maxValue = 10,
        style=wx.HORIZONTAL|wx.SL_AUTOTICKS|wx.SL_LABELS,size=(250,-1))
        self.qualitySlider.Bind(wx.EVT_SCROLL,self.onSetQuality)
        
        self.contentSizer.Add(self.qualityLbl,(n,0),flag=wx.EXPAND|wx.LEFT|wx.RIGHT)
        n+=1
        self.contentSizer.Add(self.qualitySlider,(n,0))
        n+=1
        
        self.settingLbl=wx.StaticText(self,-1,"Maximum number of planes:")
        self.settingEdit = wx.TextCtrl(self,-1,"")
        self.settingEdit.Bind(wx.EVT_TEXT,self.onEditQuality)
        self.contentSizer.Add(self.settingLbl,(n,0))
        n+=1
        self.contentSizer.Add(self.settingEdit,(n,0))
        n+=1
        
        self.shadingBtn=wx.CheckBox(self.lightPanel,-1,"Use shading")
        self.shadingBtn.SetValue(0)
        self.shading=0
        self.shadingBtn.Bind(wx.EVT_CHECKBOX,self.onCheckShading)
        
        self.lightSizer.Add(self.shadingBtn,(4,0))
        
        
    def onCheckShading(self,event):
        """
        Method: onCheckShading
        Created: 16.05.2005, KP
        Description: Toggle use of shading
        """  
        self.shading=event.IsChecked()
            

    def onEditQuality(self,event):
        """
        Method: onEditQuality
        Created: 15.05.2005, KP
        Description: Set the quality
        """  
        self.editFlag=1
        
    def onSetQuality(self,event):
        """
        Method: onSetQuality
        Created: 15.05.2005, KP
        Description: Set the quality
        """  
        if event:
            self.editFlag=0
        if not self.editFlag:
            q=self.qualitySlider.GetValue()
        else:
            try:
                q=int(self.settingEdit.GetValue())
            except:
                q=self.qualitySlider.GetValue()
        setting = self.module.setQuality(q,self.editFlag)
        if setting:
            val="%d"%setting
        else:val=""
        self.settingEdit.SetValue(val)
        
        
    def onSelectMethod(self,event):
        """
        Method: onSelectMethod
        Created: 28.04.2005, KP
        Description: Select the volume rendering method
        """  
        self.method = self.moduleChoice.GetSelection()
        if self.haveVolpro:
            flag=(self.method in [0,3,4])
            self.volpro.Enable(flag)
        if self.method==4:
            self.volpro.SetValue(1)
            
      
    def setModule(self,module):
        """
        Method: setModule(module)
        Created: 28.04.2005, KP
        Description: Set the module to be configured
        """  
        ModuleConfigurationPanel.setModule(self,module)
        unit=module.getDataUnit()
        self.method=module.method
        self.moduleChoice.SetSelection(self.method)
        if unit.getBitDepth()==32:
            self.colorPanel.setAlphaMode(1)
            
        else:
            if module.visualizer.getProcessedMode():
                ctf = module.getDataUnit().getSourceDataUnits()[0].getColorTransferFunction()
            else:
                ctf= module.getDataUnit().getColorTransferFunction()
            self.colorPanel.setColorTransferFunction(ctf)
        
    def onApply(self,event):
        """
        Method: onApply()
        Created: 28.04.2005, KP
        Description: Apply the changes
        """     
        ModuleConfigurationPanel.onApply(self,event)
        #if self.colorPanel.isChanged():
        self.module.setShading(self.shading)
        
        
        otf = self.colorPanel.getOpacityTransferFunction()
        self.module.setOpacityTransferFunction(otf)
        if self.haveVolpro and self.method in [0,3,4] and self.volpro.GetValue():
            # use volumepro accelerated rendering
            modes=["Composite",None,None,"MaximumIntensity","MinimumIntensity"]
            self.module.setVolumeProAcceleration(modes[self.method])
            self.settingEdit.Enable(0)
            self.qualitySlider.Enable(0)
        else:
            self.settingEdit.Enable(1)
            self.qualitySlider.Enable(1)
            self.module.setMethod(self.method)
            if self.method==2:
                self.settingLbl.SetLabel("Maximum number of planes:")
            else:
                self.settingLbl.SetLabel("Sample Distance:")
            self.Layout()

        self.onSetQuality(None)
        self.module.updateData()
        # module.updateData() will call updateRendering()
        #self.module.updateRendering()
