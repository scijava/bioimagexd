# -*- coding: iso-8859-1 -*-

"""
 Unit: VisualizationModules
 Project: BioImageXD
 Created: 28.04.2005, KP
 Description:

 A module containing the various Rendering modules for the visualization
 
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
        self.renderer = self.parent.getRenderer()
        
    
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
        Description: Disable the Rendering of this module
        """          
        self.renderer.RemoveActor(self.actor)

        self.wxrenwin.Render()
        
    def enableRendering(self):
        """
        Method: enableRendering()
        Created: 15.05.2005, KP
        Description: Enable the Rendering of this module
        """          
        self.renderer.AddActor(self.actor)
        self.wxrenwin.Render()

class VolumeModule(VisualizationModule):
    """
    Class: VolumeModule
    Created: 28.04.2005, KP
    Description: A volume Rendering module
    """    
    def __init__(self,parent):
        """
        Method: __init__(parent)
        Created: 28.04.2005, KP
        Description: Initialization
        """     
        VisualizationModule.__init__(self,parent)   
        self.name = "Volume Rendering"
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
        self.volume.SetProperty(self.volumeProperty)
        self.setMethod(2)
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
        
    def setVolumeProAcceleration(self,acc):
        """
        Method: setVolumeProAcceleration(acceleration)
        Created: 15.05.2005, KP
        Description: Set volume pro acceleration
        """ 
        self.method=-1
        self.mapper = vtk.vtkVolumeProMapper()
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
            self.volumeProperty.ShadeOn()
            self.volumeProperty.SetInterpolationTypeToLinear()
            
        elif quality==9:
            self.volumeProperty.ShadeOff()
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
        self.method=method
        print "Setting volume rendering method to ",method
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
        print "Rendering!"
        self.mapper.SetInput(input)
        print "self.mapper=",self.mapper
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
        
    
class SurfaceModule(VisualizationModule):
    """
    Class: SurfaceModule
    Created: 28.04.2005, KP
    Description: A surface Rendering module
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


class ImagePlaneModule(VisualizationModule):
    """
    Class: ImagePlaneModule
    Created: 03.05.2005, KP
    Description: A module for slicing the dataset
    """    
    def __init__(self,parent):
        """
        Method: __init__(parent)
        Created: 03.05.2005, KP
        Description: Initialization
        """     
        self.x,self.y,self.z=-1,-1,-1
        VisualizationModule.__init__(self,parent)   
        self.name = "Orthogonal Slices"
        self.on = 0
        self.renew = 1
        self.mapper = vtk.vtkPolyDataMapper()
        
        self.outline = vtk.vtkOutlineFilter()
        self.outlineMapper = vtk.vtkPolyDataMapper()
        self.outlineActor = vtk.vtkActor()
        self.outlineActor.SetMapper(self.outlineMapper)
        
        self.picker = vtk.vtkCellPicker()
        self.picker.SetTolerance(0.005)
        
        self.planeWidgetX = vtk.vtkImagePlaneWidget()
        self.planeWidgetX.DisplayTextOn()
        self.planeWidgetX.SetPlaneOrientationToXAxes()
        self.planeWidgetX.SetPicker(self.picker)
        self.planeWidgetX.SetKeyPressActivationValue("x")
        #self.planeWidgetX.UserControlledLookupTableOn()
        self.prop1 = self.planeWidgetX.GetPlaneProperty()
#        self.prop1.SetColor(1, 0, 0)
        self.planeWidgetX.SetResliceInterpolateToCubic()

        self.planeWidgetY = vtk.vtkImagePlaneWidget()
        self.planeWidgetY.DisplayTextOn()
        self.planeWidgetY.SetPlaneOrientationToYAxes()
        self.planeWidgetY.SetPicker(self.picker)
        self.planeWidgetY.SetKeyPressActivationValue("y")
        self.prop2 = self.planeWidgetY.GetPlaneProperty()
        self.planeWidgetY.SetResliceInterpolateToCubic()
        #self.planeWidgetY.UserControlledLookupTableOn()
#        self.prop2.SetColor(1, 1, 0)


        # for the z-slice, turn off texture interpolation:
        # interpolation is now nearest neighbour, to demonstrate
        # cross-hair cursor snapping to pixel centers
        self.planeWidgetZ = vtk.vtkImagePlaneWidget()
        self.planeWidgetZ.DisplayTextOn()
        self.planeWidgetZ.SetPlaneOrientationToZAxes()
        self.planeWidgetZ.SetPicker(self.picker)
        self.planeWidgetZ.SetKeyPressActivationValue("z")
        self.prop3 = self.planeWidgetZ.GetPlaneProperty()
#        self.prop3.SetColor(0, 0, 1)
        #self.planeWidgetZ.UserControlledLookupTableOn()
        self.planeWidgetZ.SetResliceInterpolateToCubic()
        self.renderer = self.parent.getRenderer()
        self.renderer.AddActor(self.outlineActor)
        
        iactor = self.wxrenwin.GetRenderWindow().GetInteractor()
        self.planeWidgetX.SetInteractor(iactor)
        self.planeWidgetY.SetInteractor(iactor)
        self.planeWidgetZ.SetInteractor(iactor)
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
        data=self.dataUnit.getTimePoint(0)
        self.origin = data.GetOrigin()
        self.spacing = data.GetSpacing()
        self.extent = data.GetWholeExtent()

        x=self.extent[1]/2
        y=self.extent[3]/2
        z=self.extent[5]/2
        self.setDisplaySlice(x,y,z)

        ctf = self.dataUnit.getColorTransferFunction()
        self.planeWidgetX.GetColorMap().SetLookupTable(ctf)
        self.planeWidgetX.maxDim = x
        
        self.planeWidgetY.GetColorMap().SetLookupTable(ctf)
        self.planeWidgetY.maxDim = y
        
        self.planeWidgetZ.GetColorMap().SetLookupTable(ctf)
        self.planeWidgetZ.maxDim = z
    
    def setDisplaySlice(self,x,y,z):
        """
        Method: setDisplaySlice
        Created: 04.05.2005, KP
        Description: Set the slices to display
        """           
        self.x,self.y,self.z=x,y,z
        #self.parent.getRenderer().ResetCameraClippingRange()
        #self.wxrenwin.GetRenderWindow().Render()
        print "Showing slices ",self.x,self.y,self.z

    def showTimepoint(self,value):
        """
        Method: showTimepoint(tp)
        Created: 28.04.2005, KP
        Description: Set the timepoint to be displayed
        """          
        self.renew=1
        VisualizationModule.showTimepoint(self,value)
        
    def alignCamera(self,widget):
        """
        Method: alignCamera(widget)
        Created: 15.05.2005, KP
        Description: Align the camera so that it shows a given widget
        """          
        xMin,xMax,yMin,yMax,zMin,zMax=self.extent
        sx,sy,sz=self.spacing
        ox,oy,oz=self.origin
        slice_number = widget.maxDim / 2
        cx = ox+(0.5*(xMax-xMin))*sx
        cy = oy+(0.5*(yMax-yMin))*sy
        cz = oy+(0.5*(zMax-zMin))*sz
        vx, vy, vz = 0, 0, 0
        nx, ny, nz = 0, 0, 0
        iaxis = widget.GetPlaneOrientation()
        if iaxis == 0:
            vz = 1
            nx = ox + xMax*sx
            cx = ox + slice_number*sx
          
        elif iaxis == 1:
            vz = 1
            ny = oy+yMax*sy
            cy = oy+slice_number*sy
          
        else:
            vy = 1
            nz = oz+zMax*sz
            cz = oz+slice_number*sz
          
    
        
        px = cx+nx*2
        py = cy+ny*2
        d=float(xMax)/zMax
        if d<1:d=1
        print "d=",d
        pz = cz+nz*(3.0+d)
    
        camera = self.renderer.GetActiveCamera()
        camera.SetViewUp(vx, vy, vz)
        camera.SetFocalPoint(cx, cy, cz)
        camera.SetPosition(px, py, pz)
            
        camera.OrthogonalizeViewUp()
        self.renderer.ResetCameraClippingRange()
        self.wxrenwin.Render()

        
    def updateRendering(self):
        """
        Method: updateRendering()
        Created: 03.05.2005, KP
        Description: Update the Rendering of this module
        """             
        self.outline.SetInput(self.data)
        self.outlineMapper.SetInput(self.outline.GetOutput())
        
        self.outlineMapper.Update()

        if self.renew:

            self.planeWidgetX.SetInput(self.data)
            self.planeWidgetZ.SetInput(self.data)
            self.planeWidgetY.SetInput(self.data)
            self.renew=0
        self.planeWidgetX.SetSliceIndex(self.x)
        self.planeWidgetY.SetSliceIndex(self.y)
        self.planeWidgetZ.SetSliceIndex(self.z)
        
        if not self.on:
            self.planeWidgetX.On()
            self.planeWidgetY.On()
            self.planeWidgetZ.On()
            self.on = 1
        
        #self.mapper.Update()
        self.parent.Render()    

    def disableRendering(self):
        """
        Method: disableRendering()
        Created: 15.05.2005, KP
        Description: Disable the Rendering of this module
        """          
        self.renderer.RemoveActor(self.outlineActor)
        self.planeWidgetX.Off()
        self.planeWidgetY.Off()
        self.planeWidgetZ.Off()
        self.wxrenwin.Render()
        
    def enableRendering(self):
        """
        Method: enableRendering()
        Created: 15.05.2005, KP
        Description: Enable the Rendering of this module
        """          
        self.renderer.AddActor(self.outlineActor)
        self.planeWidgetX.On()
        self.planeWidgetY.On()
        self.planeWidgetZ.On()
        self.wxrenwin.Render()


class ArbitrarySliceModule(VisualizationModule):
    """
    Class: ArbitrarySliceModule
    Created: 04.05.2005, KP
    Description: A module for slicing the dataset in arbitrary ways
    """    
    def __init__(self,parent):
        """
        Method: __init__(parent)
        Created: 03.05.2005, KP
        Description: Initialization
        """     
        self.x,self.y,self.z=-1,-1,-1
        VisualizationModule.__init__(self,parent)   
        self.name = "Arbitrary Slices"
        self.on = 0
        self.renew = 1
        
        self.outline = vtk.vtkOutlineFilter()
        self.outlineMapper = vtk.vtkPolyDataMapper()
        self.outlineActor = vtk.vtkActor()
        self.outlineActor.SetMapper(self.outlineMapper)
        
        self.parent.getRenderer().AddActor(self.outlineActor)
        
        self.planeWidget = vtk.vtkPlaneWidget()
        
        self.planeWidget.NormalToXAxisOn()
        self.planeWidget.SetResolution(20)
        self.planeWidget.SetRepresentationToOutline()
        
        self.plane = vtk.vtkPolyData()
        self.planeWidget.GetPolyData(self.plane)

        iactor = self.wxrenwin.GetRenderWindow().GetInteractor()
        self.planeWidget.SetInteractor(iactor)
        
        self.probe = vtk.vtkProbeFilter()
        
        self.planeWidget.AddObserver("EnableEvent", self.BeginInteraction)
        self.planeWidget.AddObserver("StartInteractionEvent", self.BeginInteraction)
        self.planeWidget.AddObserver("InteractionEvent", self.ProbeData)

        
        self.planes=[]
        
        print "adding actor"
        #self.updateRendering()
        
    def BeginInteraction(self,obj,event):
        obj.GetPolyData(self.plane)
    
    def ProbeData(self,obj,event):
        obj.GetPolyData(self.plane)
        
        
    def setDataUnit(self,dataunit):
        """
        Method: setDataUnit(self)
        Created: 04.05.2005, KP
        Description: Sets the dataunit this module uses for visualization
        """       
        VisualizationModule.setDataUnit(self,dataunit)
        print "got dataunit",dataunit
        data=self.dataUnit.getTimePoint(0)
        self.origin = data.GetOrigin()
        self.spacing = data.GetSpacing()
        self.extent = data.GetWholeExtent()

        x=self.extent[1]/2
        y=self.extent[3]/2
        z=self.extent[5]/2
        self.x,self.y,self.z=x,y,z
        self.volumeModule = VolumeModule(self.parent)
        self.volumeModule.setMethod(0)
        self.volumeModule.setDataUnit(self.dataUnit)

        
    
    def setDisplaySlice(self,x,y,z):
        """
        Method: setDisplaySlice
        Created: 04.05.2005, KP
        Description: Set the slices to display
        """           
        self.x,self.y,self.z=x,y,z
        self.planeWidgetX.SetSliceIndex(self.x)
        self.planeWidgetY.SetSliceIndex(self.y)
        self.planeWidgetZ.SetSliceIndex(self.z)
        #self.parent.getRenderer().ResetCameraClippingRange()
        #self.wxrenwin.GetRenderWindow().Render()
        print "Showing slices ",self.x,self.y,self.z

    def showTimepoint(self,value):
        """
        Method: showTimepoint(tp)
        Created: 28.04.2005, KP
        Description: Set the timepoint to be displayed
        """          
        self.renew=1
        VisualizationModule.showTimepoint(self,value)

        
    def updateRendering(self):
        """
        Method: updateRendering()
        Created: 03.05.2005, KP
        Description: Update the Rendering of this module
        """             
        self.planeWidget.SetInput(self.data)
        self.probe.SetInput(self.plane)
        self.probe.SetSource(self.data)
        self.planeWidget.PlaceWidget()
        data=self.probe.GetOutput()
        print "data=",data
        self.volumeModule.updateRendering(data)

        self.outline.SetInput(self.data)
        self.outlineMapper.SetInput(self.outline.GetOutput())
        
        self.outlineMapper.Update()

        if self.renew:
            self.planeWidget.SetInput(self.data)
            self.renew=0
        
        if not self.on:
            self.planeWidget.On()
            self.on = 1
        
        #self.mapper.Update()
        self.parent.Render()    
        
