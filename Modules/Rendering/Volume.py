# -*- coding: iso-8859-1 -*-

"""
 Unit: Volume
 Project: BioImageXD
 Created: 28.04.2005, KP
 Description:

 A module containing the volume rendering module for the visualization
          
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
import messenger

import ColorTransferEditor
import Dialogs
import types
from Visualizer.VisualizationModules import *
import Logging

TEXTURE_MAPPING=1
TEXTURE_MAPPING_3D=2
RAYCAST=0
MIP=3
ISOSURFACE=4
def getClass():return VolumeModule
def getConfigPanel():return VolumeConfigurationPanel
def getName():return "Volume rendering"


class VolumeModule(VisualizationModule):
    """
    Created: 28.04.2005, KP
    Description: A volume Rendering module
    """    
    def __init__(self,parent,visualizer,**kws):
        """
        Created: 28.04.2005, KP
        Description: Initialization
        """     
        VisualizationModule.__init__(self,parent,visualizer,**kws)   
        self.mapper = None
        #self.name = "Volume Rendering"
        self.quality = 10
        self.method=TEXTURE_MAPPING
        self.otfs=[]
        self.interpolation = 0
        
        # This is the MIP otf
        otf2=vtk.vtkPiecewiseFunction()
        otf2.AddPoint(0, 0.0)
        otf2.AddPoint(255, 1.0)

        # this is the normal otf
        otf = vtk.vtkPiecewiseFunction()
        otf.AddPoint(0, 0.0)
        otf.AddPoint(255, 0.2)
        self.otfs.append(otf) # ray cast
        self.otfs.append(otf) # texture map
        self.otfs.append(otf) # texture map 3d
        self.otfs.append(otf2) #mip
        self.otfs.append(otf) # isosurface
        self.eventDesc="Rendering volume"
        self.colorTransferFunction = None

        self.volumeProperty =  vtk.vtkVolumeProperty()
        self.volumeProperty.SetScalarOpacity(self.otfs[self.method])
        self.setQuality(10)
        self.volume = vtk.vtkVolume()
        self.actor = self.volume
        self.volume.SetProperty(self.volumeProperty)
        self.setMethod(1)
        self.parent.getRenderer().AddVolume(self.volume)
        self.setShading(0)
        self.setInterpolation(0)
        #self.updateRendering()
        
    def __getstate__(self):
        """
        Created: 02.08.2005, KP
        Description: A getstate method that saves the lights
        """            
        odict=VisualizationModule.__getstate__(self)
        odict.update({"mapper":self.getVTKState(self.mapper)})
        odict.update({"volume":self.getVTKState(self.volume)})
        odict.update({"volumeProperty":self.getVTKState(self.volumeProperty)})
        odict.update({"actor":self.getVTKState(self.actor)})
        odict.update({"otf0":self.getVTKState(self.otfs[0])})
        odict.update({"otf1":self.getVTKState(self.otfs[1])})
        odict.update({"otf2":self.getVTKState(self.otfs[2])})
        odict.update({"otf3":self.getVTKState(self.otfs[3])})
        odict.update({"otf4":self.getVTKState(self.otfs[4])})
        odict.update({"renderer":self.getVTKState(self.renderer)})
        odict.update({"camera":self.getVTKState(self.renderer.GetActiveCamera())})
        odict.update({"quality":self.quality})
        odict.update({"method":self.method})
        return odict
        
    def __set_pure_state__(self,state):
        """
        Created: 02.08.2005, KP
        Description: Set the state of the light
        """        
        self.setVTKState(self.mapper,state.mapper)
        self.setVTKState(self.volume,state.volume)
        self.setVTKState(self.volumeProperty,state.volumeProperty)
        self.setVTKState(self.actor,state.actor)
        self.setVTKState(self.otfs[0],state.otf0)
        self.setVTKState(self.otfs[1],state.otf1)        
        self.setVTKState(self.otfs[2],state.otf2)       
        self.setVTKState(self.otfs[3],state.otf3)       
        self.setVTKState(self.otfs[4],state.otf4)    
        self.setVTKState(self.renderer,state.renderer)
        self.setVTKState(self.renderer.GetActiveCamera(),state.camera)
        self.setMethod(state.method)
        self.setQuality(state.quality)
        VisualizationModule.__set_pure_state__(self,state)
        
    def setDataUnit(self,dataunit):
        """
        Created: 28.04.2005, KP
        Description: Sets the dataunit this module uses for visualization
        """       
        Logging.info("Dataunit for Volume Rendering:",dataunit,kw="rendering")
        VisualizationModule.setDataUnit(self,dataunit)
        # If 32 bit data, use method 1
        if self.visualizer.getProcessedMode():
            Logging.info("Processed mode, using ctf of first source",kw="rendering")
            self.colorTransferFunction = self.dataUnit.getSourceDataUnits()[0].getColorTransferFunction()
        else:    
            self.colorTransferFunction = self.dataUnit.getColorTransferFunction()
        
        self.volumeProperty.SetColor(self.colorTransferFunction)
        
    def setOpacityTransferFunction(self,otf,method):
        """
        Created: 28.04.2005, KP
        Description: Set the opacity transfer function
        """
        self.otfs[method]=otf
        self.volumeProperty.SetScalarOpacity(otf)
        
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
            Logging.info("No support for VolumePro detected",kw="rendering")
            self.haveVolpro=0
            self.volpro.Enable(0)
            self.volpro.SetValue(0)
            return
        cmd="self.mapper.SetBlendModeTo%s()"%acc
        Logging.info("Setting blending mode to ",acc,kw="rendering")
        eval(cmd)
        Logging.info("Setting parallel projetion",kw="rendering")
        self.renderer.GetActiveCamera().ParallelProjectionOn()
        
    def setQuality(self,quality,raw=0):
        """
        Method: setQuality(self,quality)
        Created: 28.04.2005, KP
        Description: Set the quality of Rendering
        """ 
        self.quality = quality
        if self.method<0:return 0
        if raw:
            Logging.info("Setting quality to raw ",quality,kw="rendering")
            if self.method in [TEXTURE_MAPPING]:
                Logging.info("Setting maximum number of planes to",quality,kw="rendering")
                self.mapper.SetMaximumNumberOfPlanes(quality)
            else:
                
                if quality<=0.00001:
                    toq=0.1
                    Dialogs.showwarning(None,"The selected sample distance (%f) is too small, %f will be used."%(quality,toq),"Too small sample distance")
                    quality=toq
                Logging.info("Setting sample distance to ",quality,kw="rendering")                    
                self.mapper.SetSampleDistance(quality)
            return quality
        else:
            Logging.info("Setting quality to",quality,kw="rendering")
        if quality==10:
            if self.mapper:
                if self.method not in [TEXTURE_MAPPING]:
                    self.mapper.SetSampleDistance(self.sampleDistance)
                else:
                    self.mapper.SetMaximumNumberOfPlanes(self.maxPlanes)
        #elif quality==9:
        #    self.volumeProperty.SetInterpolationTypeToNearest()
        elif quality<10:
           
            if self.method not in [TEXTURE_MAPPING]:
                self.mapper.SetSampleDistance(15-quality)
                return 15-quality
            else:
                quality=10-quality
                self.mapper.SetMaximumNumberOfPlanes(25-quality)
                return 25-quality
        return 0
        
    def setInterpolation(self,interpolation):
        """
        Created: 28.04.2005, KP
        Description: Set the interpolation method used
        """             
        self.interpolation=interpolation
        ints=["nearest neighbor","linear"]
        Logging.info("Using %s interpolation"%ints[self.interpolation],kw="rendering")
        if self.interpolation==0:
            self.volumeProperty.SetInterpolationTypeToNearest()
        else:
            self.volumeProperty.SetInterpolationTypeToLinear() 
        self.volume.SetProperty(self.volumeProperty)

    def setMethod(self,method):
        """
        Created: 28.04.2005, KP
        Description: Set the Rendering method used
        """             
        self.vtkcvs=0
        try:
            from vtk import vtkFixedPointVolumeRayCastMapper
            self.vtkcvs=1

        except:
            pass
        self.method=method
        self.volumeProperty.SetScalarOpacity(self.otfs[self.method])
        
        tbl=["Ray cast","Texture Map","3D texture map","MIP","Isosurface"]
        Logging.info("Volume rendering method: ",tbl[method],kw="rendering")
        
        #Ray Casting, RGBA Ray Casting, Texture Mapping, MIP
        composites = [vtk.vtkVolumeRayCastCompositeFunction,
                      None,
                      None,
                      vtk.vtkVolumeRayCastMIPFunction,
                      vtk.vtkVolumeRayCastIsosurfaceFunction
                      ]
        blendModes=["Composite","Composite","Composite","MaximumIntensity","Composite"]
        if method in [RAYCAST,MIP,ISOSURFACE]:
            # Iso surfacing with fixedpoint mapper is not supported
            if self.vtkcvs and method!=ISOSURFACE:
                self.mapper = vtk.vtkFixedPointVolumeRayCastMapper()
                #self.mapper.SetAutoAdjustSampleDistances(1)
                self.sampleDistance = self.mapper.GetSampleDistance()
                #self.volumeProperty.IndependentComponentsOff()
                mode=blendModes[method]
                Logging.info("Setting fixed point rendering mode to ",mode,kw="rendering")
                cmd="self.mapper.SetBlendModeTo%s()"%(mode)
                #print cmd
                eval(cmd)
            else:
                self.mapper = vtk.vtkVolumeRayCastMapper()
                self.function = composites[method]()
                Logging.info("Using ray cast function ",self.function,kw="rendering")
                self.mapper.SetVolumeRayCastFunction(self.function)
        elif method==TEXTURE_MAPPING_3D: # 3d texture mapping
            self.mapper = vtk.vtkVolumeTextureMapper3D()
            self.sampleDistance = self.mapper.GetSampleDistance()
        elif method==TEXTURE_MAPPING: # texture mapping
            self.mapper = vtk.vtkVolumeTextureMapper2D()
            self.maxPlanes = self.mapper.GetMaximumNumberOfPlanes()
        
        self.volume.SetMapper(self.mapper)    
        
#        self.renderer.GetActiveCamera().ParallelProjectionOff()

    def updateRendering(self,input = None):
        """
        Created: 28.04.2005, KP
        Description: Update the Rendering of this module
        """             
        if not input:
            input=self.data
        ncomps=input.GetNumberOfScalarComponents()
        Logging.info("Number of comps=",ncomps,kw="rendering")
        if ncomps>1 and self.method == TEXTURE_MAPPING:
            self.setMethod(0)
            messenger.send(None,"update_module_settings")
        if ncomps>1:
            self.volumeProperty.IndependentComponentsOff()
        else:
            self.volumeProperty.IndependentComponentsOn()            
            
        Logging.info("Rendering using, ",self.mapper.__class__,kw="rendering")
        self.mapper.SetInput(input)
        #self.mapper.AddObserver("ProgressEvent",self.updateProgress)

        VisualizationModule.updateRendering(self,input)
        self.parent.Render()
        if self.method == TEXTURE_MAPPING_3D:
            if not self.mapper.IsRenderSupported(self.volumeProperty):
                messenger.send(None,"show_error","3D texture mapping not supported",
                "Your graphics hardware does not support 3D accelerated texture mapping. Please use one of the other volume rendering methods.")
                
            
        
    def disableRendering(self):
        """
        Created: 30.04.2005, KP
        Description: Disable the Rendering of this module
        """          
        self.renderer.RemoveVolume(self.volume)
        self.wxrenwin.Render()
        
    def enableRendering(self):
        """
        Created: 15.05.2005, KP
        Description: Enable the Rendering of this module
        """          
        self.renderer.AddVolume(self.volume)
        self.wxrenwin.Render()        
        
    
class VolumeConfiguration(ModuleConfiguration):
    def __init__(self,parent,visualizer):
        """
        Created: 28.04.2005, KP
        Description: Initialization
        """     
        
        ModuleConfiguration.__init__(self,parent,"Volume rendering")
        self.panel=VolumeConfigurationPanel(self,visualizer)
        

class VolumeConfigurationPanel(ModuleConfigurationPanel):
    def __init__(self,parent,visualizer,name="Volume rendering",**kws):
        """
        Created: 28.04.2005, KP
        Description: Initialization
        """     
        self.method=TEXTURE_MAPPING
        ModuleConfigurationPanel.__init__(self,parent,visualizer,name,**kws)
        self.editFlag=0

    def initializeGUI(self):
        """
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
        
        modes = ["Ray casting","Texture mapping","3D texture mapping","Maximum intensity projection"]
        try:
            volpro=vtk.vtkVolumeProMapper()
            self.haveVolpro=0
            if volpro.GetNumberOfBoards():
                self.haveVolpro=1
        except:
            self.haveVolpro=0
        if self.haveVolpro:
            modes.append("Minimum intensity projection")
        
        #self.methodLbl = wx.StaticText(self,-1,"Volume rendering method:")
        
        self.methodBox=wx.StaticBox(self,-1,"Volume rendering method")
        self.methodSizer=wx.StaticBoxSizer(self.methodBox,wx.VERTICAL)
        self.moduleChoice = wx.Choice(self,-1,choices = modes)
    
        self.moduleChoice.Bind(wx.EVT_CHOICE,self.onSelectMethod)
        self.moduleChoice.SetSelection(self.method)
        
      
        #self.contentSizer.Add(self.methodLbl,(n,0))
        n+=1
        self.methodSizer.Add(self.moduleChoice)
        self.contentSizer.Add(self.methodSizer,(n,0),flag=wx.EXPAND|wx.LEFT|wx.RIGHT)
        n+=1
        
        self.qualityBox=wx.StaticBox(self,-1,"Rendering quality")
        self.qualitySizer=wx.StaticBoxSizer(self.qualityBox,wx.VERTICAL)
        self.interpolationBox = wx.RadioBox(
                self, -1, "Interpolation", wx.DefaultPosition, wx.DefaultSize,
                ["Nearest neighbor","Linear"], 2, wx.RA_SPECIFY_COLS
                )
        s="""Set the type of interpolation used in rendering.
Nearest Neighbor interpolation is faster than Linear interpolation, 
but using linear interpolation yields a better rendering quality."""
        self.interpolationBox.SetToolTip(wx.ToolTip(s))
        self.interpolationBox.SetHelpText(s)
        self.interpolationBox.Bind(wx.EVT_RADIOBOX,self.onSetInterpolation)
        self.contentSizer.Add(self.interpolationBox,(n,0),flag=wx.EXPAND|wx.LEFT|wx.RIGHT)
        n+=1
        #self.qualitySizer.Add(self.interpolationBox)
                
        if self.haveVolpro:
            self.volpro=wx.CheckBox(self,-1,"Use VolumePro acceleration")
            self.volpro.Enable(0)
            self.contentSizer.Add(self.volpro,(n,0))
            n+=1
        
        self.qualitySlider = wx.Slider(self,value=10, minValue=0,maxValue = 10,
        style=wx.HORIZONTAL|wx.SL_AUTOTICKS|wx.SL_LABELS,size=(250,-1))
        self.qualitySlider.Bind(wx.EVT_SCROLL,self.onSetQuality)
        
        self.qualitySizer.Add(self.qualitySlider)
        self.contentSizer.Add(self.qualitySizer,(n,0),flag=wx.EXPAND|wx.LEFT|wx.RIGHT)
        n+=1
        
        self.settingLbl=wx.StaticText(self,-1,"Maximum number of planes:")
        self.settingEdit = wx.TextCtrl(self,-1,"")
        self.settingEdit.Bind(wx.EVT_TEXT,self.onEditQuality)
        self.qualitySizer.Add(self.settingLbl)
        self.qualitySizer.Add(self.settingEdit)
        
        self.shadingBtn=wx.CheckBox(self.lightPanel,-1,"Use shading")
        self.shadingBtn.SetValue(0)
        self.shading=0
        self.shadingBtn.Bind(wx.EVT_CHECKBOX,self.onCheckShading)
        
        self.lightSizer.Add(self.shadingBtn,(4,0))
        
    def onSetInterpolation(self,event):
        """
        Created: 08.08.2005, KP
        Description: Set the interpolation used
        """  
        self.interpolation=self.interpolationBox.GetSelection()      
        
    def onCheckShading(self,event):
        """
        Created: 16.05.2005, KP
        Description: Toggle use of shading
        """  
        self.shading=event.IsChecked()
            

    def onEditQuality(self,event):
        """
        Created: 15.05.2005, KP
        Description: Set the quality
        """  
        self.editFlag=1
        
    def onSetQuality(self,event):
        """
        Created: 15.05.2005, KP
        Description: Set the quality
        """  
        if event:
            self.editFlag=0
        if not self.editFlag:
            q=self.qualitySlider.GetValue()
        else:
            try:
                q=float(self.settingEdit.GetValue())
            except:
                q=self.qualitySlider.GetValue()
        setting = self.module.setQuality(q,self.editFlag)
        if setting:
            if type(setting)==types.FloatType:
                val="%f"%setting
            else:
                val="%d"%setting
        else:val=""
        flag=self.editFlag
        self.settingEdit.SetValue(val)
        self.editFlag=flag
        
        
    def onSelectMethod(self,event):
        """
        Created: 28.04.2005, KP
        Description: Select the volume rendering method
        """  
        self.method = self.moduleChoice.GetSelection()
        if self.haveVolpro:
            flag=(self.method in [RAYCASTING,MIP,ISOSURFACE])
            self.volpro.Enable(flag)
        if self.method==4:
            self.volpro.SetValue(1)
        Logging.info("Setting otf to ",self.method)
        self.colorPanel.setOpacityTransferFunction(self.module.otfs[self.method])
        if self.method == TEXTURE_MAPPING:
            self.settingLbl.SetLabel("Maximum number of planes:")
        else:
            self.settingLbl.SetLabel("Sample distance:")            
      
    def setModule(self,module):
        """
        Created: 28.04.2005, KP
        Description: Set the module to be configured
        """  
        ModuleConfigurationPanel.setModule(self,module)
        unit=module.getDataUnit()
        self.method=module.method
        self.moduleChoice.SetSelection(self.method)
        self.colorPanel.setOpacityTransferFunction(self.module.otfs[self.method])
        self.interpolation=module.interpolation
        self.interpolationBox.SetSelection(module.interpolation)
        if unit.getBitDepth()==32:
            self.colorPanel.setAlphaMode(1)
            
        else:
            if module.visualizer.getProcessedMode():
                ctf = module.getDataUnit().getSourceDataUnits()[0].getColorTransferFunction()
            else:
                ctf= module.getDataUnit().getColorTransferFunction()
            self.colorPanel.setColorTransferFunction(ctf)
        self.qualitySlider.SetValue(module.quality)
        self.shadingBtn.SetValue(module.shading)
        
        
    def onApply(self,event):
        """
        Created: 28.04.2005, KP
        Description: Apply the changes
        """     
        ModuleConfigurationPanel.onApply(self,event)
        #if self.colorPanel.isChanged():
        self.module.setShading(self.shading)
        self.module.setInterpolation(self.interpolation)
        
        otf = self.colorPanel.getOpacityTransferFunction()
        self.module.setOpacityTransferFunction(otf,self.method)
        if self.haveVolpro and self.method in [RAYCAST,ISOSURFACE,MIP] and self.volpro.GetValue():
            # use volumepro accelerated rendering
            modes=["Composite",None,None,"MaximumIntensity","MinimumIntensity"]
            self.module.setVolumeProAcceleration(modes[self.method])
            self.settingEdit.Enable(0)
            self.qualitySlider.Enable(0)
        else:
            self.settingEdit.Enable(1)
            self.qualitySlider.Enable(1)
            self.module.setMethod(self.method)
            if self.method==1:
                self.settingLbl.SetLabel("Maximum number of planes:")
            else:
                self.settingLbl.SetLabel("Sample Distance:")
            self.Layout()

        self.onSetQuality(None)
        self.module.updateData()
        # module.updateData() will call updateRendering()
        #self.module.updateRendering()
