# -*- coding: iso-8859-1 -*-

"""
 Unit: Surface
 Project: BioImageXD
 Created: 28.04.2005, KP
 Description:

 A module containing the surface rendering modules for the visualization
 
 Modified 28.04.2005 KP - Created the class
          
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

def getClass():return SurfaceModule
def getConfig():return SurfaceConfigurationPanel
def getName():return "Surface Rendering"

    
class SurfaceModule(VisualizationModule):
    """
    Class: SurfaceModule
    Created: 28.04.2005, KP
    Description: A surface Rendering module
    """    
    def __init__(self,parent,visualizer):
        """
        Method: __init__(parent)
        Created: 28.04.2005, KP
        Description: Initialization
        """     
        VisualizationModule.__init__(self,parent,visualizer)   
        self.name = "Surface Rendering"
        self.normals = vtk.vtkPolyDataNormals()
        self.generateNormals = 0
        self.volumeModule = None
        self.isoValue = 128
        self.contourRange = (-1,-1,-1)
        self.setIsoValue(128)
        
        self.setMethod(1)
        self.init=0
        self.mapper = vtk.vtkPolyDataMapper()
        
        self.actor = self.lodActor = vtk.vtkLODActor()
        self.lodActor.SetMapper(self.mapper)
        self.lodActor.SetNumberOfCloudPoints(10000)
        
        self.parent.getRenderer().AddActor(self.lodActor)
        print "adding actor"
        #self.updateRendering()
        
    def setDataUnit(self,dataunit):
        """
        Method: setDataUnit(self)
        Created: 28.04.2005, KP
        Description: Sets the dataunit this module uses for visualization
        """       
        VisualizationModule.setDataUnit(self,dataunit)
        print "got dataunit",dataunit
            
    def setIsoValue(self,isovalue):
        """
        Method: setIsoValue(isovalue)
        Created: 30.04.2005, KP
        Description: Set the isovalue to be shown
        """  
        self.contourRange = (-1,-1,-1)
        self.isoValue = isovalue
        print "Iso value=",self.isoValue
        
    def setContourRange(self,start,end,contours):
        """
        Method: setContourRange(start,end,contours)
        Created: 30.04.2005, KP
        Description: Set the range and number of contours to be generated
        """             
        self.isoValue = -1
        self.contourRange = (start,end,contours)
        print "contour range=",start,end,contours

    def setGenerateNormals(self,angle):
        """
        Method: setGenerateNormals(self,angle)
        Created: 30.04.2005, KP
        Description: Set the feature angle at which normals are generated
        """             
        self.generateNormals = 1
        self.normals.SetFeatureAngle(angle)
        

    def setMethod(self,method):
        """
        Method: setMethod(self,method)
        Created: 28.04.2005, KP
        Description: Set the Rendering method used
        """             
        self.method=method
        if method<2:
            #Ray Casting, RGBA Ray Casting, Texture Mapping, MIP
            filters = [vtk.vtkContourFilter,vtk.vtkMarchingCubes]
            print "Using ",filters[method],"as  contourer"
            self.contour = filters[method]()
            if self.volumeModule:
                self.volumeModule.disableRendering()
                self.volumeModule = None
        else:
            print "Using volume Rendering for isosurfacing"
            self.disableRendering()
            self.volumeModule = VolumeModule(self.parent)
            self.volumeModule.setMethod(5)
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
        self.contour.SetInput(self.data)
        
        self.mapper.SetLookupTable(self.dataUnit.getColorTransferFunction())
        self.mapper.ScalarVisibilityOn()
        self.mapper.SetScalarRange(0,255)
        self.mapper.SetColorModeToMapScalars()
    
        if self.isoValue != -1:
            self.contour.SetValue(0,self.isoValue)
        else:
            print "Generating %d values in range %d-%d"%(n,begin,end)
            begin,end,n=self.contourRange
            self.contour.GenerateValues(n,begin,end)
        if self.generateNormals:
            print "Generating normals"
            self.normals.SetInput(self.contour.GetOutput())
            self.mapper.SetInput(self.normals.GetOutput())
        else:
            self.mapper.SetInput(self.contour.GetOutput())
        self.mapper.Update()
        self.parent.Render()    



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
    def __init__(self,parent,visualizer,**kws):
        """
        Method: __init__(parent)
        Created: 28.04.2005, KP
        Description: Initialization
        """     
        ModuleConfigurationPanel.__init__(self,parent,visualizer,"Surface Rendering",**kws)
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
        ModuleConfigurationPanel.onApply(self,event)
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

        self.updateData()
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
