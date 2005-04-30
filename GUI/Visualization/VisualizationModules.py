# -*- coding: iso-8859-1 -*-

"""
 Unit: VisualizationModules
 Project: BioImageXD
 Created: 28.04.2005, KP
 Description:

 A module containing the various rendering modules for the visualization
 
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
        
    def disableRendering(self):
        """
        Method: disableRendering()
        Created: 30.04.2005, KP
        Description: Disable the rendering of this module
        """          
        self.mapper.RemoveActor(self.actor)

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
                      vtk.vtkVolumeRayCastRGBCompositeFunction,
                      None,
                      vtk.vtkVolumeRayCastMIPFunction,
                      vtk.vtkVolumeRayCastIsosurfaceFunction
                      ]
        if method in [0,1,3,4]:
            self.mapper = vtk.vtkVolumeRayCastMapper()
            self.function = composites[method]()
            self.mapper.SetVolumeRayCastFunction(self.function)
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
        
    def disableRendering(self):
        """
        Method: disableRendering()
        Created: 30.04.2005, KP
        Description: Disable the rendering of this module
        """          
        self.mapper.RemoveVolume(self.volume)
        
    
class SurfaceModule(VisualizationModule):
    """
    Class: SurfaceModule
    Created: 28.04.2005, KP
    Description: A surface rendering module
    """    
    def __init__(self,parent):
        """
        Method: __init__(parent)
        Created: 28.04.2005, KP
        Description: Initialization
        """     
        VisualizationModule.__init__(self,parent)   
        self.name = "Surface Rendering"
        self.normals = vtk.vtkPolyDataNormals()
        self.generateNormals = 0
        self.volumeModule = None
        self.isoValue = 128
        self.contourRange = (-1,-1,-1)
        
        #self.normals.SetFeatureAngle(45)
        self.setMethod(1)
        self.init=0
        self.mapper = vtk.vtkPolyDataMapper()
        
        self.actor = self.lodActor = vtk.vtkLODActor()
        self.lodActor.SetMapper(self.mapper)
        self.lodActor.SetNumberOfCloudPoints(1000)
        
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
        Description: Set the rendering method used
        """             
        self.method=method
        if method<2:
            #Ray Casting, RGBA Ray Casting, Texture Mapping, MIP
            filters = [vtk.vtkContourFilter,vtk.vtkMarchingCubes]
            self.contour = filters[method]()
            if self.volumeModule:
                self.volumeModule.disableRendering()
                self.volumeModule = None
        else:
            self.disableRendering()
            self.volumeModule = VolumeModule(self.parent)
            self.volumeModule.setMethod(4)
            self.volumeModule.setDataUnit(self.dataUnit)
            self.volumeModule.showTimepoint(self.timepoint)
            
                    
    def updateRendering(self):
        """
        Method: updateRendering()
        Created: 28.04.2005, KP
        Description: Update the rendering of this module
        """             
        if self.volumeModule:
            self.volumeModule.function.SetIsoValue(self.isovalue)
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
            begin,end,n=self.contourRange
            self.contour.GenerateValues(n,begin,end)
        if self.generateNormals:
            self.normals.SetInput(self.contour.GetOutput())
            self.mapper.SetInput(self.normals.GetOutput())
        else:
            self.mapper.SetInput(self.contour.GetOutput())
        self.wxrenwin.Render()    


