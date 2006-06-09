# -*- coding: iso-8859-1 -*-

"""
 Unit: WarpScalar
 Project: BioImageXD
 Created: 29.05.2006, KP
 Description:

 A WarpScalar rendering module
           
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

import GUIBuilder
import types
from Visualizer.VisualizationModules import *

def getClass():return WarpScalarModule
def getConfigPanel():return WarpScalarConfigurationPanel
def getName():return "WarpScalar"


class WarpScalarModule(VisualizationModule):
    """
    Class: WarpScalarModule
    Created: 24.06.2005, KP
    Description: A module for clipping the dataset
    """    
    def __init__(self,parent,visualizer,**kws):
        """
        Method: __init__(parent)
        Created: 03.05.2005, KP
        Description: Initialization
        """     
        VisualizationModule.__init__(self,parent,visualizer,**kws)   

        self.descs = {"Normals":"Smooth surface with Normals","FeatureAngle":"Feature Angle of Normals",
        "Slice":"Select slice to be warped","Scale":"Scale factor for warping"}

        self.luminance = vtk.vtkImageLuminance()
        
        #DataGeometry filter, image to polygons
        self.geometry = vtk.vtkImageDataGeometryFilter()
        
        self.colorMapper = None
        #warp scalars!
        self.warp = vtk.vtkWarpScalar()
        self.warp.SetScaleFactor(-0.1)
        
        #merge image and new warped data
        self.merge = vtk.vtkMergeFilter()
        
        self.normals = vtk.vtkPolyDataNormals()        
        self.normals.SetFeatureAngle (90)
        #first the mapper
        self.mapper = vtk.vtkPolyDataMapper()
        
        #make the actor from the mapper
        self.actor = vtk.vtkActor()
        self.actor.SetMapper(self.mapper)

        self.renderer = self.parent.getRenderer()
        self.renderer.AddActor(self.actor)

#        iactor = self.wxrenwin.GetRenderWindow().GetInteractor()
        
    def getParameters(self):
        """
        Method: getParameters
        Created: 31.05.2006, KP
        Description: Return the list of parameters needed for configuring this GUI
        """            
        return [ ["Smoothing",("Normals","FeatureAngle")],
       ["Warping",("Slice","Scale")] ]
        
    def getDefaultValue(self,parameter):
        """
        Method: getDefaultValue
        Created: 13.04.2006, KP
        Description: Return the default value of a parameter
        """           
        if parameter == "Slice":return 0
        if parameter=="Normals":return 1
        if parameter=="FeatureAngle":return 90
        if parameter=="Scale":return -0.2
            
    def getRange(self, parameter):
        """
        Method: getRange
        Created: 31.05.2006, KP
        Description: If a parameter has a certain range of valid values, the values can be queried with this function
        """     
        if parameter=="Slice":
            x,y=(0,self.dataUnit.getDimensions()[2])
            print "Range of slice=",x,y 
            return x,y
        return -1,-1
        
    def getType(self,parameter):
        """
        Method: getType
        Created: 13.04.2006, KP
        Description: Return the type of the parameter
        """    
        if parameter == "Slice":return GUIBuilder.SLICE
        if parameter=="Normals":return types.BooleanType
        if parameter=="FeatureAngle":return types.IntType
        if parameter=="Scale":return types.FloatType
        
    def __getstate__(self):
        """
        Method: __getstate__
        Created: 02.08.2005, KP
        Description: A getstate method that saves the lights
        """            
        odict=VisualizationModule.__getstate__(self)
        #print "Saving Slice =" ,self.parameters["Slice"]
        #print "Returning",odict
        odict["parameters"] = self.parameters
        return odict
        
    def __set_pure_state__(self,state):
        """
        Method: __set_pure_state__()
        Created: 02.08.2005, KP
        Description: Set the state of the light
        """        
        VisualizationModule.__set_pure_state__(self,state)
        self.parameters = state.parameters
        self.sendUpdateGUI()
                
    def setDataUnit(self,dataunit):
        """
        Method: setDataUnit(self)
        Created: 28.04.2005, KP
        Description: Sets the dataunit this module uses for visualization
        """       
        VisualizationModule.setDataUnit(self,dataunit)

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
        data = self.data
        if data.GetNumberOfScalarComponents()>3:
            extract = vtk.vtkImageExtractComponents()
            extract.SetInput(data)
            extract.SetComponents(1,1,1)
            data = extract.GetOutput()
        if data.GetNumberOfScalarComponents()>1:
            self.luminance.SetInput(data)
            data = self.luminance.GetOutput()
            
        dims = self.data.GetDimensions()
        x,y,z=dims
        z = self.parameters["Slice"]
        ext=(0,x-1,0,y-1,z,z)

        voi = vtk.vtkExtractVOI()
        voi.SetVOI(ext)
        voi.SetInput(data)
        slice = voi.GetOutput()
        self.geometry.SetInput(slice)         
        
        self.warp.SetInput(self.geometry.GetOutput())
        self.warp.SetScaleFactor(self.parameters["Scale"])        
        
        self.merge.SetGeometry(self.warp.GetOutput())

        
        if slice.GetNumberOfScalarComponents()==1:
            maptocol=vtk.vtkImageMapToColors()
            ctf = self.dataUnit.getColorTransferFunction()
            maptocol.SetInput(slice)
            maptocol.SetLookupTable(ctf)
            maptocol.Update()
            scalars = maptocol.GetOutput()
        else:
            scalars = slice
            
        self.merge.SetScalars(scalars)
        
        data = self.merge.GetOutput()
        
        if self.parameters["Normals"]:
            self.normals.SetInput(data)
            self.normals.SetFeatureAngle(self.parameters["FeatureAngle"])
            print "Feature angle=",self.parameters["FeatureAngle"]            
            data = self.normals.GetOutput()
        
        
        self.mapper.SetInput(data)

        
        self.mapper.Update()
        VisualizationModule.updateRendering(self)
        self.parent.Render()    

        
    def setProperties(self,ambient,diffuse,specular,specularpower):
        """
        Method: setProperties(ambient,diffuse,specular,specularpower)
        Created: 16.05.2005, KP
        Description: Set the ambient, diffuse and specular lighting of this module
        """         
        pass
    def setShading(self,shading):
        """
        Method: setShading(shading)
        Created: 16.05.2005, KP
        Description: Set shading on / off
        """          
        pass


class WarpScalarConfiguration(ModuleConfiguration):
    def __init__(self,parent,visualizer):
        """
        Method: __init__(parent)
        Created: 29.05.2006, KP
        Description: Initialization
        """     
        ModuleConfiguration.__init__(self,parent,"WarpScalar")
        self.panel=WarpScalarConfigurationPanel(self,visualizer)

class WarpScalarConfigurationPanel(ModuleConfigurationPanel):
    def __init__(self,parent,visualizer,name="WarpScalar",**kws):
        """
        Method: __init__(parent)
        Created: 29.05.2006, KP
        Description: Initialization
        """     
        ModuleConfigurationPanel.__init__(self,parent,visualizer,name,**kws)
    
    def initializeGUI(self):
        """
        Method: initializeGUI()
        Created: 28.04.2005, KP
        Description: Initialization
        """          
        pass
        
    def setModule(self,module):
        """
        Method: setModule(module)
        Created: 28.04.2005, KP
        Description: Set the module to be configured
        """  
        ModuleConfigurationPanel.setModule(self,module)
        print "module=",module
        self.module=module
        self.gui = GUIBuilder.GUIBuilder(self, self.module)
        self.module.sendUpdateGUI()
        self.contentSizer.Add(self.gui,(0,0))

    def onApply(self,event):
        """
        Method: onApply()
        Created: 28.04.2005, KP
        Description: Apply the changes
        """     
        self.module.updateRendering()
        pass