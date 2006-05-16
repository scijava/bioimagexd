# -*- coding: iso-8859-1 -*-

"""
 Unit: Surface
 Project: BioImageXD
 Created: 28.04.2005, KP
 Description:

 A module containing the surface rendering modules for the visualization
           
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
import ColorTransferEditor
import Dialogs
import Logging
import Volume

from Visualizer.VisualizationModules import *

def getClass():return SurfaceModule
def getConfigPanel():return SurfaceConfigurationPanel
def getName():return "Surface Rendering"

    
class SurfaceModule(VisualizationModule):
    """
    Class: SurfaceModule
    Created: 28.04.2005, KP
    Description: A surface Rendering module
    """    
    def __init__(self,parent,visualizer,**kws):
        """
        Method: __init__(parent)
        Created: 28.04.2005, KP
        Description: Initialization
        """     
        VisualizationModule.__init__(self,parent,visualizer,**kws)   
        #self.name = "Surface Rendering"
        self.normals = vtk.vtkPolyDataNormals()
        self.generateNormals = 0
        self.volumeModule = None
        self.isoValue = 128
        self.scalarRange=(0,255)
        self.contourRange = (-1,-1,-1)
        self.opacity = 1.0
        self.setIsoValue(128)
        self.decimateLevel=0
        self.preserveTopology=1
        self.eventDesc="Rendering iso-surface"
        self.useGaussian=1
        self.decimate = vtk.vtkDecimatePro()
        self.setMethod(1)
        self.init=0
        self.mapper = vtk.vtkPolyDataMapper()
        
        self.actor = self.lodActor = vtk.vtkLODActor()
        self.lodActor.SetMapper(self.mapper)
        self.lodActor.SetNumberOfCloudPoints(10000)
        self.renderer = self.parent.getRenderer()
        self.renderer.AddActor(self.lodActor)
        #self.updateRendering()

    def setGaussian(self,flag):
        """
        Method: setGaussian(flag)
        Created: 20.08.2005, KP
        Description: Toggle use of gaussian smoothing
        """       
        self.useGaussian=flag
        
    def setOpacity(self,opacity):
        """
        Method: setOpacity(opacity)
        Created: 27.07.2005, KP
        Description: Set the opacity
        """       
        self.opacity = opacity
        Logging.info("Opacity = ",opacity,kw="visualizer")
        if opacity!=1:
            Logging.info("Setting traversing order to BackToFront",kw="visualizer")
            cullers = self.parent.getRenderer().GetCullers()
            cullers.InitTraversal()
            print cullers
            culler = cullers.GetNextItem()
            culler.SetSortingStyleToBackToFront()
        
    def setDecimate(self,level,preserveTopology):
        """
        Method: setDecimate(level,preserveTopology)
        Created: 07.07.2005, KP
        Description: Set the decimation settings
        """       
        self.decimateLevel=level
        self.preserveTopology=preserveTopology
        self.decimate.SetPreserveTopology(preserveTopology)
        if not preserveTopology:
            self.decimate.SplittingOn()
            self.decimate.BoundaryVertexDeletionOn()
        else:
            self.decimate.SplittingOff()
            self.decimate.BoundaryVertexDeletionOff()
        self.decimate.SetTargetReduction(level/100.0)
        
    def setDataUnit(self,dataunit):
        """
        Method: setDataUnit(self)
        Created: 28.04.2005, KP
        Description: Sets the dataunit this module uses for visualization
        """       
        VisualizationModule.setDataUnit(self,dataunit)
#        self.data=self.dataUnit.getTimePoint(0)
            
    def setIsoValue(self,isovalue):
        """
        Method: setIsoValue(isovalue)
        Created: 30.04.2005, KP
        Description: Set the isovalue to be shown
        """  
        self.contourRange = (-1,-1,-1)
        self.isoValue = isovalue
        Logging.info("Iso value for surface = ",self.isoValue,kw="visualizer")        
        
    def setContourRange(self,start,end,contours):
        """
        Method: setContourRange(start,end,contours)
        Created: 30.04.2005, KP
        Description: Set the range and number of contours to be generated
        """             
        self.isoValue = -1
        self.contourRange = (start,end,contours)
        Logging.info("Contour range = ",start,"to",end,"# of contours =",contours,kw="visualizer")

    def setGenerateNormals(self,gen,angle):
        """
        Method: setGenerateNormals(self,gen,angle)
        Created: 30.04.2005, KP
        Description: Set the feature angle at which normals are generated
        """             
        self.generateNormals = gen
        self.normals.SetFeatureAngle(angle)
        self.featureAngle=angle
        

    def setMethod(self,method):
        """
        Method: setMethod(self,method)
        Created: 28.04.2005, KP
        Description: Set the Rendering method used
        """             
        self.method=method
        if method<3:
            #Ray Casting, RGBA Ray Casting, Texture Mapping, MIP
            filters = [vtk.vtkContourFilter,vtk.vtkMarchingCubes,vtk.vtkDiscreteMarchingCubes]
            Logging.info("Using ",filters[method],"as  contourer",kw="visualizer")
            self.contour = filters[method]()
            if self.volumeModule:
                self.volumeModule.disableRendering()
                self.volumeModule = None
        else:
            Logging.info("Using volume rendering for isosurface")
            self.disableRendering()
            self.volumeModule = Volume.VolumeModule(self.parent,self.visualizer,moduleName="Volume",label="Volume")
            self.volumeModule.setMethod(Volume.ISOSURFACE)
            self.volumeModule.setDataUnit(self.dataUnit)
            self.volumeModule.showTimepoint(self.timepoint)

    def updateRendering(self):
        """
        Method: updateRendering()
        Created: 28.04.2005, KP
        Description: Update the Rendering of this module
        """             
        if self.volumeModule:
            self.volumeModule.function.SetIsoValue(self.isoValue)
            self.volumeModule.showTimepoint(self.timepoint)
            return
        if not self.init:
            self.init=1
            self.mapper.ColorByArrayComponent(0,0)
        self.mapper.AddObserver("ProgressEvent",self.updateProgress)
        self.mapper.SetLookupTable(self.dataUnit.getColorTransferFunction())
        self.mapper.ScalarVisibilityOn()
        min,max=self.data.GetScalarRange()
        print "Scalar range of data=",min,max
        
        
        self.mapper.SetScalarRange(min,max)
        self.mapper.SetColorModeToMapScalars()
        Logging.info("Using opacity ",self.opacity,kw="visualizer")
        self.actor.GetProperty().SetOpacity(self.opacity)
        input=self.data
        if self.useGaussian:
            Logging.info("Doing gaussian smoothing",kw="visualizer")
            self.smooth=vtk.vtkImageGaussianSmooth()
            self.smooth.SetInput(input)
            self.smooth.Update()
            input=self.smooth.GetOutput()
        self.scalarRange=input.GetScalarRange()
        self.contour.SetInput(input)
        input=self.contour.GetOutput()
        if self.isoValue != -1:
            self.contour.SetValue(0,self.isoValue)
        else:
            begin,end,n=self.contourRange
            Logging.info("Generating %d values in range %d-%d"%(n,begin,end),kw="visualizer")
            
            self.contour.GenerateValues(n,begin,end)
        if self.decimateLevel != 0:
            Logging.info("Decimating %.2f%%, preserve topology: %s"%(self.decimateLevel/100.0,self.preserveTopology),kw="visualizer")
            self.decimate.SetInput(input)
            input=self.decimate.GetOutput()
        #smooth=vtk.vtkSmoothPolyDataFilter()
        #smooth.SetInput(input)
        #smooth.SetNumberOfIterations(50)
        #smooth.SetRelaxationFactor(0.9)
        #smooth.SetFeatureEdgeSmoothing(1)
        #input=smooth.GetOutput()
        
        if self.generateNormals:
            Logging.info("Generating normals at angle",self.featureAngle,kw="visualizer")
    
            self.normals.SetInput(input)
            input=self.normals.GetOutput()
        
        self.mapper.SetInput(input)
        VisualizationModule.updateRendering(self,input)
        #self.mapper.Update()
        self.parent.Render()    

    def __getstate__(self):
        """
        Method: __getstate__
        Created: 02.08.2005, KP
        Description: A getstate method that saves the lights
        """            
        odict=VisualizationModule.__getstate__(self)
        odict.update({"mapper":self.getVTKState(self.mapper)})
        odict.update({"actor":self.getVTKState(self.actor)})
        odict.update({"renderer":self.getVTKState(self.renderer)})
        odict.update({"camera":self.getVTKState(self.renderer.GetActiveCamera())})
        odict.update({"method":self.method})
        
        odict.update({"generateNormals":self.generateNormals,
                      "isoValue":self.isoValue,
                      "contourRange":self.contourRange,
                      "opacity":self.opacity,
                      "decimateLevel":self.decimateLevel,
                      "preserveTopology":self.preserveTopology})
        return odict
        
    def __set_pure_state__(self,state):
        """
        Method: __set_pure_state__()
        Created: 02.08.2005, KP
        Description: Set the state of the light
        """        
        #print "\n\n\n__set_pure_state__\n\n\n"
        self.setVTKState(self.mapper,state.mapper)
        self.setVTKState(self.actor,state.actor)
        self.setVTKState(self.renderer,state.renderer)
        self.setVTKState(self.renderer.GetActiveCamera(),state.camera)
        self.setMethod(state.method)
        self.generateNormals = state.generateNormals
        print "state.isoValue=",state.isoValue
        self.isoValue = state.isoValue
        
        self.contourRange = state.contourRange
        self.opacity = state.opacity
        print "state.decimateLevel=",state.decimateLevel
        if state.decimateLevel:
            self.setDecimate(state.decimateLevel,state.preserveTopology)
        
        VisualizationModule.__set_pure_state__(self,state)        


class SurfaceConfiguration(ModuleConfiguration):
    def __init__(self,parent,visualizer):
        """
        Method: __init__(parent)
        Created: 28.04.2005, KP
        Description: Initialization
        """     
        ModuleConfiguration.__init__(self,parent,"Surface Rendering")
        self.panel=SurfaceConfigurationPanel(self,visualizer)
        self.method=0

class SurfaceConfigurationPanel(ModuleConfigurationPanel):
    def __init__(self,parent,visualizer,name="Surface Rendering",**kws):
        """
        Method: __init__(parent)
        Created: 28.04.2005, KP
        Description: Initialization
        """     
        ModuleConfigurationPanel.__init__(self,parent,visualizer,name,**kws)
        self.method=0
        
    def setModule(self,module):
        """
        Method: setModule(module)
        Created: 28.04.2005, KP
        Description: Set the module to be configured
        """  
        ModuleConfigurationPanel.setModule(self,module)
        print "Setting configuration from",module
        self.method=module.method
        self.moduleChoice.SetSelection(self.method)
        self.gaussianBox.SetValue(module.useGaussian)
        self.normalsBox.SetValue(module.generateNormals)
        print "normals=",module.generateNormals
        self.decimateSlider.SetValue(module.decimateLevel)
        print "decimate=",module.decimateLevel
        self.decimateCheckbox.SetValue(module.preserveTopology)
        print "isovalue=",module.isoValue
        if module.isoValue != -1:
            self.isoSlider.SetValue(module.isoValue)
        min,max=module.scalarRange
        self.isoSlider.SetRange(min,max)
        if module.contourRange != (-1,-1,-1):
            begin,end,n=module.contourRange
            self.isoRangeBegin.SetValue("%d"%begin)
            self.isoRangeEnd.SetValue("%d"%end)
            self.isoRangeSurfaces.SetValue("%d"%n)
            
        self.opacitySlider.SetValue(self.opacityMax-(self.opacityMax*module.opacity))
            
            
        #self.shadingBtn.SetValue(module.shading)        
            
    def initializeGUI(self):
        """
        Method: initializeGUI()
        Created: 28.04.2005, KP
        Description: Initialization
        """          
        self.methodLbl = wx.StaticText(self,-1,"Surface rendering method:")
        self.moduleChoice = wx.Choice(self,-1,choices=["Contour Filter","Marching Cubes","Discrete Marching Cubes","Iso-Surface Volume Rendering"])
        self.moduleChoice.SetSelection(1)
        self.moduleChoice.Bind(wx.EVT_CHOICE,self.onSelectMethod)
        n=0
        self.contentSizer.Add(self.methodLbl,(n,0))
        n+=1
        self.contentSizer.Add(self.moduleChoice,(n,0))
        n+=1
        self.gaussianBox = wx.CheckBox(self,-1,"Smooth surface with gaussian smoothing")
        self.gaussianBox.SetValue(1)
        
        #self.gaussianBox = wx.CheckBox(self,-1,"Smooth surface with gaussian smoothing")
        #self.gaussianBox.SetValue(0)        
        
        self.normalsBox = wx.CheckBox(self,-1,"Smooth surface with surface normals")
        self.normalsBox.SetValue(0)
        self.normalsBox.Bind(wx.EVT_CHECKBOX,self.onSetSmoothing)
        self.featureLbl=wx.StaticText(self,-1,"Feature angle of normals:")
        self.featureAngle = wx.TextCtrl(self,-1,"45")
        self.featureAngle.Enable(0)
        
        self.contentSizer.Add(self.gaussianBox,(n,0))
        n+=1
        self.contentSizer.Add(self.normalsBox,(n,0))
        n+=1
        self.contentSizer.Add(self.featureLbl,(n,0))
        n+=1
        self.contentSizer.Add(self.featureAngle,(n,0))
        n+=1
        
        self.decimateLbl=wx.StaticText(self,-1,"Simplify surface:")
        
        self.decimateSlider=wx.Slider(self,value=0,minValue=0,maxValue=100,style=wx.HORIZONTAL|wx.SL_AUTOTICKS|wx.SL_LABELS,size=(255,-1))
        self.decimateCheckbox=wx.CheckBox(self,-1,"Preserve topology")
        self.decimateCheckbox.SetValue(1)
        
        self.contentSizer.Add(self.decimateLbl,(n,0))
        n+=1
        self.contentSizer.Add(self.decimateSlider,(n,0))
        n+=1
        self.contentSizer.Add(self.decimateCheckbox,(n,0))
        
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

        self.opacityMax=100
        self.opacityLbl=wx.StaticText(self,-1,"Surface transparency:")
        self.opacitySlider=wx.Slider(self,-1,
        value=0,minValue=0,maxValue=self.opacityMax,
        style=wx.HORIZONTAL|wx.SL_AUTOTICKS|wx.SL_LABELS,size=(255,-1))
        

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
        self.contentSizer.Add(self.opacityLbl,(n,0))
        n+=1
        self.contentSizer.Add(self.opacitySlider,(n,0))
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
        ModuleConfigurationPanel.onApply(self,event)
        self.module.setMethod(self.method)
        if self.normalsBox.GetValue():
            angle=float(self.featureAngle.GetValue())
            print "Setting generated normals to",angle
            self.module.setGenerateNormals(1,angle)
        else:
            self.module.setGenerateNormals(0,0)
            
        self.module.setGaussian(self.gaussianBox.GetValue())
        if self.isoRangeSurfaces.GetValue() != 0:
            start=int(self.isoRangeBegin.GetValue())
            end=int(self.isoRangeEnd.GetValue())
            n=int(self.isoRangeSurfaces.GetValue())
            self.module.setContourRange(start,end,n)
        else:
            self.module.setIsoValue(self.isoSlider.GetValue())
        
        if self.decimateSlider.GetValue()!=0:
            self.module.setDecimate(self.decimateSlider.GetValue(),self.decimateCheckbox.GetValue())
        self.module.setOpacity((self.opacityMax-self.opacitySlider.GetValue())/float(self.opacityMax))
        self.module.updateData()
        self.module.updateRendering()
        
        min,max=self.module.data.GetScalarRange()
        self.isoSlider.SetRange(min,max)
        self.isoRangeBegin.SetRange(min,max)
        self.isoRangeEnd.SetRange(min,max)
        self.isoRangeSurfaces.SetRange(min,max)
        
    def onSelectMethod(self,event):
        """
        Method: onSelectMethod
        Created: 30.04.2005, KP
        Description: Select the surface rendering method
        """  
        self.method = self.moduleChoice.GetSelection()
        flag=(self.method!=3)
        self.isoRangeBegin.Enable(flag)
        self.isoRangeEnd.Enable(flag)
        self.isoRangeSurfaces.Enable(flag)
