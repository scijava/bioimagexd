# -*- coding: iso-8859-1 -*-

"""
 Unit: Orthogonal
 Project: BioImageXD
 Created: 28.04.2005, KP
 Description:

 A module containing the orthogonal slices module for the visualization
 
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

from Visualizer.VisualizationModules import *

def getClass():return ImagePlaneModule
def getConfigPanel():return ImagePlaneConfigurationPanel
def getName():return "Orthogonal Slices"


class ImagePlaneModule(VisualizationModule):
    """
    Class: ImagePlaneModule
    Created: 03.05.2005, KP
    Description: A module for slicing the dataset
    """    
    def __init__(self,parent,visualizer,**kws):
        """
        Method: __init__(parent)
        Created: 03.05.2005, KP
        Description: Initialization
        """     
        self.x,self.y,self.z=-1,-1,-1
        VisualizationModule.__init__(self,parent,visualizer,**kws)   
        #self.name = "Orthogonal Slices"
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
        if self.visualizer.getProcessedMode():
            data=self.dataUnit.getSourceDataUnits()[0].getTimePoint(0)
        else:
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
        
    def setProperties(self,ambient,diffuse,specular,specularpower):
        """
        Method: setProperties(ambient,diffuse,specular,specularpower)
        Created: 16.05.2005, KP
        Description: Set the ambient, diffuse and specular lighting of this module
        """         
        for widget in [self.planeWidgetX,self.planeWidgetY,self.planeWidgetZ]:
            property=widget.GetTexturePlaneProperty()
            property.SetAmbient(ambient)
            property.SetDiffuse(diffuse)
            property.SetSpecular(specular)
            property.SetSpecularPower(specularpower)
        
    def setShading(self,shading):
        """
        Method: setShading(shading)
        Created: 16.05.2005, KP
        Description: Set shading on / off
        """          
        for widget in [self.planeWidgetX,self.planeWidgetY,self.planeWidgetZ]:
            property=widget.GetTexturePlaneProperty()
            if shading:
                property.ShadeOn()
            else:
                property.ShadeOff()        



class ImagePlaneConfiguration(ModuleConfiguration):
    def __init__(self,parent,visualizer):
        """
        Method: __init__(parent)
        Created: 04.05.2005, KP
        Description: Initialization
        """     
        ModuleConfiguration.__init__(self,parent,"Orthogonal Slices")
        self.panel=ImagePlaneConfigurationPanel(self,visualizer)

class ImagePlaneConfigurationPanel(ModuleConfigurationPanel):
    def __init__(self,parent,visualizer,name="Orthogonal Slices",**kws):
        """
        Method: __init__(parent)
        Created: 04.05.2005, KP
        Description: Initialization
        """     
        ModuleConfigurationPanel.__init__(self,parent,visualizer,name,**kws)
    
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
            
        box=wx.BoxSizer(wx.HORIZONTAL)
        self.ID_X=wx.NewId()
        self.ID_Y=wx.NewId()
        self.ID_Z=wx.NewId()
        self.xBtn = wx.Button(self,self.ID_X,"X")
        self.yBtn = wx.Button(self,self.ID_Y,"Y")
        self.zBtn = wx.Button(self,self.ID_Z,"Z")
        self.xBtn.Bind(wx.EVT_BUTTON,self.alignCamera)
        self.yBtn.Bind(wx.EVT_BUTTON,self.alignCamera)
        self.zBtn.Bind(wx.EVT_BUTTON,self.alignCamera)
        
        box.Add(self.xBtn,1)
        box.Add(self.yBtn,1)
        box.Add(self.zBtn,1)
        self.contentSizer.Add(box,(6,0))
        
            
        self.xSlider.Bind(wx.EVT_SCROLL,self.onUpdateSlice)
        self.ySlider.Bind(wx.EVT_SCROLL,self.onUpdateSlice)
        self.zSlider.Bind(wx.EVT_SCROLL,self.onUpdateSlice)
        
        self.shadingBtn=wx.CheckBox(self.lightPanel,-1,"Use shading")
        self.shadingBtn.SetValue(1)
        self.shading=1
        self.shadingBtn.Bind(wx.EVT_CHECKBOX,self.onCheckShading)
        
        self.lightSizer.Add(self.shadingBtn,(4,0))
        
    def onCheckShading(self,event):
        """
        Method: onCheckShading
        Created: 16.05.2005, KP
        Description: Toggle use of shading
        """  
        self.shading=event.IsChecked()        
        
        
    def alignCamera(self,event):
        """
        Method: alignCamera
        Created: 15.05.2005, KP
        Description: Align the camera to face a certain plane
        """  
        if event.GetId()==self.ID_X:
            print "aliging to X"
            self.module.alignCamera(self.module.planeWidgetX)
        elif event.GetId()==self.ID_Y:
            print "aliging to Y"
            self.module.alignCamera(self.module.planeWidgetY)
        else:
            print "aliging to Z"
            self.module.alignCamera(self.module.planeWidgetZ)
        
    def setModule(self,module):
        """
        Method: setModule(module)
        Created: 28.04.2005, KP
        Description: Set the module to be configured
        """  
        ModuleConfigurationPanel.setModule(self,module)
        ext=module.getDataUnit().getTimePoint(0).GetWholeExtent()
        x,y,z=ext[1],ext[3],ext[5]
        print "x=%d, y=%d, z=%d"%(x,y,z)
        self.xSlider.SetRange(0,x)
        self.xSlider.SetValue(x/2)
        
        self.ySlider.SetRange(0,y)
        self.ySlider.SetValue(y/2)
        
        self.zSlider.SetRange(0,z)
        self.zSlider.SetValue(z/2)
        self.onUpdateSlice(None)
        
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
        ModuleConfigurationPanel.onApply(self,event)
        self.updateData()
        self.module.updateRendering()
