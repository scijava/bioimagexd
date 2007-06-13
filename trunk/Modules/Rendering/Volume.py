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

import Dialogs
import types
from Visualizer.VisualizationModules import *
import Logging

import Configuration

import scripting as bxd

TEXTURE_MAPPING=1
TEXTURE_MAPPING_3D=2
RAYCAST=0
MIP=3
ISOSURFACE=4
def getClass():return VolumeModule
def getConfigPanel():return VolumeConfigurationPanel
def getName():return "Volume rendering"
def getQuickKeyCombo(): return "Shift-Ctrl-V"


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
        self.modes = ["Ray casting","Texture mapping","3D texture mapping","Maximum intensity projection"]
        self.haveVolpro = 0
        self.mapper = None
        conf=Configuration.getConfiguration()

        self.defaultMode=conf.getConfigItem("DefaultVolumeMode","Rendering")
        if self.defaultMode != None:
            self.defaultMode = int(self.defaultMode)
        else:
            self.defaultMode = RAYCAST
        
        try:
            volpro=vtk.vtkVolumeProMapper()
            self.haveVolpro=0
            if volpro.GetNumberOfBoards():
                self.haveVolpro=1
        except:
            self.haveVolpro=0
        if self.haveVolpro:
            self.modes.append("Minimum intensity projection")
        self.colorTransferFunction = None
        otf, otf2 = vtk.vtkPiecewiseFunction(), vtk.vtkPiecewiseFunction()
       
        otf2.AddPoint(0, 0.0)
        otf2.AddPoint(255, 1.0)
        otf.AddPoint(0, 0.0)
        otf.AddPoint(255, 0.2)
        
        self.otfs = [otf,otf,otf,otf2,otf]
        
        
        self.volumeProperty =  vtk.vtkVolumeProperty()
        self.volume = vtk.vtkVolume()
        self.actor = self.volume
        self.volume.SetProperty(self.volumeProperty)

        
        VisualizationModule.__init__(self,parent,visualizer,**kws)   
        self.mapper = None
        #self.name = "Volume Rendering"
        self.setParameter("Quality",10)
        self.parameters["Method"] = RAYCAST

        if self.defaultMode != None:
            print "Setting default method to ",self.defaultMode
            self.parameters["Method"] = int(self.defaultMode)
 
                   
        self.volumeProperty.SetScalarOpacity(self.otfs[self.parameters["Method"]])
        
        self.descs={"Palette":"","Method":"","Interpolation":"Interpolation","NearestNeighbor":"Nearest Neighbour","Linear":"Linear",
        "Quality":"","QualityValue":"Maximum number of planes:","UseVolumepro":"Use VolumePro acceleration"}
        
        
        self.eventDesc="Rendering volume"
        self.qualityRange = 0,10
               
        self.parent.getRenderer().AddVolume(self.volume)
        self.setShading(0)


        #self.updateRendering()
        
        
    def setParameter(self,parameter,value):
        """
        Created: 13.04.2006, KP
        Description: Set a value for the parameter
        """    
 
        VisualizationModule.setParameter(self, parameter,value)
        if parameter=="Method":
            conf=Configuration.getConfiguration()
            conf.setConfigItem("DefaultVolumeMode","Rendering", value)
            conf.writeSettings()
            self.updateOpacityTransferFunction()
            if value==1:
                messenger.send(self,"update_QualityValue_label","Maximum number of planes:")
            else:
                messenger.send(self,"update_QualityValue_label","Sample distance:")
        if parameter == "Quality":
            self.parameters["QualityValue"] = None
            self.updateQuality()
            
            
    def updateOpacityTransferFunction(self):
        """
        Created: 18.03.2007, KP
        Description: Set the GUI OTF to it's correct value
        """
        messenger.send(self,"set_Palette_otf",self.otfs[self.parameters["Method"]])

    
    def getParameters(self):
        """
        Created: 12.03.2007, KP
        Description: Return the list of parameters needed for configuring this GUI
        """            
        params=[ ["Dataset palette", ("Palette",)],
        ["Rendering method",("Method",) ],
        ["Interpolation",( ("NearestNeighbor","Linear"),("cols",2))],
        ["Rendering quality",("Quality","QualityValue")]]       
        if self.haveVolpro:
            params.insert(2,["",("UseVolumepro",)])
        return params
        
        
    def getRange(self, parameter):
        """
        Created: 12.03.2007, KP
        Description: If a parameter has a certain range of valid values, the values can be queried with this function
        """     
        if parameter=="Method":
            return self.modes
        if parameter=="Quality":
            return 0,10        
        if parameter == "QualityValue":
            return self.qualityRange
        return -1,-1
    def getType(self,parameter):
        """
        Created: 12.03. 2007, KP
        Description: Return the type of the parameter
        """   
        if parameter == "Method":return GUIBuilder.CHOICE
        if parameter in ["NearestNeighbor","Linear"]: return GUIBuilder.RADIO_CHOICE
        if parameter == "Quality": return GUIBuilder.SLICE
        if parameter == "QualityValue": return types.FloatType
        if parameter == "Palette": return GUIBuilder.CTF
        if parameter == "UseVolumepro": return types.BooleanType
        
    def getDefaultValue(self,parameter):
        """
        Created: 12.03.2007, KP
        Description: Return the default value of a parameter
        """           
        if parameter == "Method":
            return self.defaultMode
        if parameter == "Quality": return 10
        if parameter == "QualityValue": return 0
        if parameter == "Linear": return 0
        if parameter == "NearestNeighbor": return 1
        if parameter == "UseVolumepro": return False
        if parameter == "Palette":
            return self.colorTransferFunction
        
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

        otf, otf2 = vtk.vtkPiecewiseFunction(), vtk.vtkPiecewiseFunction()
        d = dataunit.getSingleComponentBitDepth()
        maxv = 2**d
            
        print "\n\n\nMaximum value=",maxv
        otf2.AddPoint(0, 0.0)
        otf2.AddPoint(maxv, 1.0)
        otf.AddPoint(0, 0.0)
        otf.AddPoint(maxv, 0.2)
        
        self.otfs = [otf,otf,otf,otf2,otf]
        
        

        self.setInputChannel(1,0)
        self.parameters["Palette"] = self.colorTransferFunction
        
        
    def updateQuality(self):
        """
        Created: 12.03.2006, KP
        Description: Update the quality of rendering
        """ 
        method = self.parameters["Method"]
        if self.parameters["QualityValue"]: 
            quality = self.parameters["QualityValue"]
            Logging.info("Setting quality to raw ",quality,kw="rendering")
            if method in [TEXTURE_MAPPING]:
                Logging.info("Setting maximum number of planes to",quality,kw="rendering")
                self.mapper.SetMaximumNumberOfPlanes(quality)
            else:                
                if quality<=0.00001:
                    toq=0.1
                    Dialogs.showwarning(None,"The selected sample distance (%f) is too small, %f will be used."%(quality,toq),"Too small sample distance")
                    quality=toq
                Logging.info("Setting sample distance to ",quality,kw="rendering")                    
                self.mapper.SetSampleDistance(quality)
        else:
            quality = self.parameters["Quality"]
            if quality==10:
                if self.mapper:
                    if method not in [TEXTURE_MAPPING]:
                        self.mapper.SetSampleDistance(self.sampleDistance)
                        messenger.send(self,"set_QualityValue",self.sampleDistance)
                    else:
                        self.mapper.SetMaximumNumberOfPlanes(self.maxPlanes)
                        messenger.send(self,"set_QualityValue",self.maxPlanes)

            elif quality<10:               
                if method not in [TEXTURE_MAPPING]:
                    self.mapper.SetSampleDistance(15-quality)
                    messenger.send(self,"set_QualityValue",15-quality)
                else:
                    quality=10-quality
                    self.mapper.SetMaximumNumberOfPlanes(25-quality)
                    messenger.send(self,"set_QualityValue",25-quality)
            return 0     
            
        
    def setInputChannel(self,inputNum,chl):
        """
        Created: 17.04.2006, KP
        Description: Set the input channel for input #inputNum
        """            
        VisualizationModule.setInputChannel(self, inputNum, chl)
        inputDataUnit = self.getInputDataUnit(1)
        if not inputDataUnit:
            inputDataUnit = self.dataUnit
        self.colorTransferFunction =    ctf = inputDataUnit.getColorTransferFunction()
        messenger.send(self,"set_Palette_ctf",self.colorTransferFunction)
             
        self.volumeProperty.SetColor(self.colorTransferFunction)

        
    def updateInterpolation(self):
        """
        Created: 28.04.2005, KP
        Description: Set the interpolation method used
        """             
        
        if self.parameters["Linear"]:
            self.volumeProperty.SetInterpolationTypeToLinear() 
        elif self.parameters["NearestNeighbor"]:
            self.volumeProperty.SetInterpolationTypeToNearest()
        self.volume.SetProperty(self.volumeProperty)

    def updateMethod(self):
        """
        Created: 28.04.2005, KP
        Description: Set the Rendering method used
        """             
        method = self.parameters["Method"]
        self.volumeProperty.SetScalarOpacity(self.otfs[method])
        self.updateOpacityTransferFunction()
        
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
            if method!=ISOSURFACE:
                self.mapper = vtk.vtkFixedPointVolumeRayCastMapper()
                
                #self.mapper.SetAutoAdjustSampleDistances(1)
                self.sampleDistance = self.mapper.GetSampleDistance()
                #self.volumeProperty.IndependentComponentsOff()
                mode=blendModes[method]
                Logging.info("Setting fixed point rendering mode to ",mode,kw="rendering")
                eval("self.mapper.SetBlendModeTo%s()"%mode)
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
        
        
        if self.haveVolpro and self.method in [RAYCAST,ISOSURFACE,MIP] and self.parameters["UseVolumepro"]:
            # use volumepro accelerated rendering
            self.mapper = vtk.vtkVolumeProMapper()

            modes=["Composite",None,None,"MaximumIntensity","MinimumIntensity"]
            acc = modes[method]
            cmd="self.mapper.SetBlendModeTo%s()"%acc
            Logging.info("Setting blending mode to ",acc,kw="rendering")
            eval(cmd)
            Logging.info("Setting parallel projetion",kw="rendering")
            self.renderer.GetActiveCamera().ParallelProjectionOn()            
            #self.settingEdit.Enable(0)
            #self.qualitySlider.Enable(0)
        else:
            self.renderer.GetActiveCamera().ParallelProjectionOff()     
            
        self.volume.SetMapper(self.mapper)    


    def updateRendering(self,input = None):
        """
        Created: 28.04.2005, KP
        Description: Update the Rendering of this module
        """             
        self.updateMethod()
        self.updateQuality()
        self.updateInterpolation()
        
        
        if not input:
            input=self.getInput(1)
        x,y,z = self.dataUnit.getDimensions()
        
        input = bxd.mem.optimize(image = input, updateExtent = (0,x-1,0,y-1,0,z-1))
                    
                    
                    
        ncomps=input.GetNumberOfScalarComponents()
        Logging.info("Number of comps=",ncomps,kw="rendering")
        dataType = input.GetScalarType()
        if (ncomps>1 or dataType not in [3,5]) and self.parameters["Method"] == TEXTURE_MAPPING:
            self.setParameter("Method",0)
            messenger.send(None,"update_module_settings")
        if ncomps>1:
            self.volumeProperty.IndependentComponentsOff()
        else:
            self.volumeProperty.IndependentComponentsOn()            
            
        Logging.info("Rendering using, ",self.mapper.__class__,kw="rendering")
        
        self.mapper.SetInput(input)

        VisualizationModule.updateRendering(self,input)
        self.parent.Render()
        if self.parameters["Method"] == TEXTURE_MAPPING_3D:
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
        ModuleConfigurationPanel.__init__(self,parent,visualizer,name,**kws)

    def initializeGUI(self):
        """
        Created: 28.04.2005, KP
        Description: Initialization
        """  
        self.shadingBtn=wx.CheckBox(self.lightPanel,-1,"Use shading")
        self.shadingBtn.SetValue(0)
        self.shading=0
        self.shadingBtn.Bind(wx.EVT_CHECKBOX,self.onCheckShading)
        
        self.lightSizer.Add(self.shadingBtn,(4,0))
        
    def onCheckShading(self,event):
        """
        Created: 16.05.2005, KP
        Description: Toggle use of shading
        """  
        self.shading=event.IsChecked()        
        self.module.setShading(self.shading)
    def getLongDesc(self, parameter):
        """
        Created: 12.03.2007, KP
        Description: return a long desc for the given parameter
        """
        if parameter in ["NearestNeighbor","Linear"]:
            return """Set the type of interpolation used in rendering.
Nearest Neighbor interpolation is faster than Linear interpolation, 
but using linear interpolation yields a better rendering quality."""
                  
    def setModule(self,module):
        """
        Created: 28.04.2005, KP
        Description: Set the module to be configured
        """  
        self.module = module
        ModuleConfigurationPanel.setModule(self,module)
        unit=module.getDataUnit()        
        self.gui = GUIBuilder.GUIBuilder(self, self.module)
        
        self.contentSizer.Add(self.gui,(0,0))
        module.updateOpacityTransferFunction()
        
        if unit.getBitDepth()==32:
            #self.colorPanel.setAlphaMode(1)
            pass
        else:
            if module.visualizer.getProcessedMode():
                ctf = module.getDataUnit().getSourceDataUnits()[0].getColorTransferFunction()
            else:
                ctf= module.getDataUnit().getColorTransferFunction()

        
            messenger.send(module,"set_Palette_ctf",ctf)
        
    def onApply(self,event):
        """
        Created: 28.04.2005, KP
        Description: Apply the changes
        """     
        ModuleConfigurationPanel.onApply(self,event)
        
#        otf = self.colorPanel.getOpacityTransferFunction()
#        self.module.setOpacityTransferFunction(otf,self.method)

        self.module.updateData()
        # module.updateData() will call updateRendering()
        #self.module.updateRendering()
