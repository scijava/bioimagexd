# -*- coding: iso-8859-1 -*-

"""
 Unit: CutWidget
 Project: BioImageXD
 Created: 29.05.2007, KP
 Description:

 A widget for cutting off a piece from a volume
           
 Copyright (C) 2007  BioImageXD Project
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
__date__ = "$Date: 2007/01/13 13:42:03 $"

import wx

import vtk
import ColorTransferEditor
import Dialogs

from GUI import GUIBuilder
import types
from Visualizer.VisualizationModules import *

import scripting as bxd

def getClass():return CutBoxModule
def getConfigPanel():return CutBoxConfigurationPanel
def getName():return "Cut with box"


class CutBoxModule(VisualizationModule):
    """
    Created: 22.04.2007, KP
    Description: A module for clipping the dataset
    """    
    def __init__(self,parent,visualizer,**kws):
        """
        Created: 22.04.2007, KP
        Description: Initialization
        """     
        self.boxWidget = None
        VisualizationModule.__init__(self,parent,visualizer,**kws)   

        self.descs = {"ShowControls":"Show the controls","ClippedModule":"Clip the module","AllModules":"Clip all modules","InsideOut":"Clip from the outside"}
        boxWidget = self.boxWidget = vtk.vtkBoxWidget()
        self.cut = 0
      
        self.clippedMappers = []

        self.renderer = self.parent.getRenderer()
        iactor = parent.wxrenwin.GetRenderWindow().GetInteractor()
        self.boxWidget.SetInteractor(iactor)
        self.boxWidget.SetPlaceFactor(1.0)
        
        outlineProperty = boxWidget.GetOutlineProperty()
        outlineProperty.SetRepresentationToWireframe()
        outlineProperty.SetAmbient(1.0)
        outlineProperty.SetAmbientColor(1, 1, 1)
        outlineProperty.SetLineWidth(3)
        
        selectedOutlineProperty = boxWidget.GetSelectedOutlineProperty()
        selectedOutlineProperty.SetRepresentationToWireframe()
        selectedOutlineProperty.SetAmbient(1.0)
        selectedOutlineProperty.SetAmbientColor(1, 0, 0)
        selectedOutlineProperty.SetLineWidth(3)
#        iactor = self.wxrenwin.GetRenderWindow().GetInteractor()
        boxWidget.AddObserver("InteractionEvent", self.clipVolumeRender)

    def getParameterLevel(self, parameter):
        """
        Created: 22.04.2007, KP
        Description: Return the level of the given parameter
        """
        if parameter in ["ShowControls","ClippedModule","AllModules","InsideOut"]:
            return bxd.COLOR_BEGINNER

    def getModulesToClip(self):
        """
        Created: 18.04.2007, KP
        Description: return all the visualizer modules that are to be clipped based on user choices
        """
        if not self.parameters.get("AllModules",0):
            modname = self.parent.getModules()[self.parameters["ClippedModule"]].getName()
            modules = filter(lambda x, n = modname:x.getName()==n, self.parent.getModules())
        else:
            modules = self.parent.getModules()
        return modules
        
    def setParameter(self, parameter, value):
        """
        Created: 22.04.2007, KP
        Description: set a parameter to given value
        """
        VisualizationModule.setParameter(self, parameter, value)
        if parameter == "ShowControls" and self.boxWidget:
            self.showPlane(value)
            
        
    def getParameters(self):
        """
        Created: 22.04.2007, KP
        Description: Return the list of parameters needed for configuring this GUI
        """            
        # return [ ["Smoothing",("Normals","FeatureAngle")],
        #["Warping",("Slice","Scale")] ]
        return [["",("ShowControls","ClippedModule","AllModules")]]
        
    def getDefaultValue(self,parameter):
        """
        Created: 22.04.2007, KP
        Description: Return the default value of a parameter
        """           
        if parameter == "ShowControls":return 1
        if parameter == "AllModules":return False
        if parameter == "ClippedModule": return 0
        if parameter == "InsideOut": return 1
    def getRange(self, parameter):
        """
        Created: 22.04.2007, KP
        Description: If a parameter has a certain range of valid values, the values can be queried with this function
        """     
        names = [module.getName() for module in self.parent.getModules()]
        names.remove(self.getName())
        return names
        
    def getType(self,parameter):
        """
        Created: 22.04.2007, KP
        Description: Return the type of the parameter
        """    
        if parameter in ["ShowControls","AllModules","InsideOut"]: return types.BooleanType
        if parameter=="ClippedModule": return GUIBuilder.CHOICE      
        
    def __getstate__(self):
        """
        Created: 22.04.2007, KP
        Description: A getstate method that saves the lights
        """            
        odict=VisualizationModule.__getstate__(self)
        #print "Saving Slice =" ,self.parameters["Slice"]
        #print "Returning",odict
        odict["parameters"] = self.parameters
        return odict
        
    def __set_pure_state__(self,state):
        """
        Created: 22.04.2007, KP
        Description: Set the state of the light
        """        
        VisualizationModule.__set_pure_state__(self,state)
        self.parameters = state.parameters
        self.sendUpdateGUI()
                
    def setDataUnit(self,dataunit):
        """
        Created: 22.04.2007, KP
        Description: Sets the dataunit this module uses for visualization
        """       
        VisualizationModule.setDataUnit(self,dataunit)
        data = self.getInput(1)

        self.boxWidget.SetInput(data)
        self.boxWidget.PlaceWidget()
        self.boxWidget.On()
        

    def showTimepoint(self,value):
        """
        Created: 22.04.2007, KP
        Description: Set the timepoint to be displayed
        """          
        self.renew=1
        VisualizationModule.showTimepoint(self,value)

    def clipVolumeRender(self, obj, evt,*args):
        """
        CreateD: 22.04.2007, KP
        Description: clip the module based on the given clipping planes
        """
        modules = self.getModulesToClip()
        planes = vtk.vtkPlanes()
        obj.GetPlanes(planes)
        
        print "Bounds=",self.boxWidget.GetProp3D().GetBounds()
               
        for mapper in self.clippedMappers:
            mapper.RemoveAllClippingPlanes()
        self.clippedMappers=[]
        
        for module in modules:
            if hasattr(module,"mapper") and hasattr(module.mapper,"SetClippingPlanes"):  
                module.mapper.SetClippingPlanes(planes)   
                self.clippedMappers.append(module.mapper)
#                else:
#                    module.mapper.RemoveAllClippingPlanes()
    def updateRendering(self):
        """
        Created: 22.04.2007, KP
        Description: Update the Rendering of this module
        """             
        input=self.getInput(1)

        if self.parameters["InsideOut"]:
            self.boxWidget.InsideOutOn()
        else:
            self.boxWidget.InsideOutOff()
        self.boxWidget.SetInput(input)
#        self.mapper.SetInput(data)
     

        
        #self.mapper.Update()
        VisualizationModule.updateRendering(self)
        self.parent.Render()    

        
    def setProperties(self,ambient,diffuse,specular,specularpower):
        """
        Created: 22.04.2007, KP
        Description: Set the ambient, diffuse and specular lighting of this module
        """         
        pass
    def setShading(self,shading):
        """
        Created: 22.04.2007, KP
        Description: Set shading on / off
        """          
        pass
    def disableRendering(self):
        """
        Created: 15.05.2005, KP
        Description: Disable the Rendering of this module
        """          
        for mapper in self.clippedMappers:
            mapper.RemoveAllClippingPlanes()        
        self.boxWidget.Off()
        self.wxrenwin.Render()
    def enableRendering(self):
        """
        Created: 24.06.2005, KP
        Description: Enable the Rendering of this module
        """          
        self.boxWidget.On()
        self.wxrenwin.Render()        
    def showPlane(self,flag):
        """
        Created: 24.06.2005, KP
        Description: Show / hide the plane controls
        """          
        if flag:
            self.boxWidget.On()
        else:
            self.boxWidget.Off()
        


class CutBoxConfigurationPanel(ModuleConfigurationPanel):
    def __init__(self,parent,visualizer,name="CutBox",**kws):
        """
        Created: 29.05.2007, KP
        Description: Initialization
        """     
        self.cut = 0
        ModuleConfigurationPanel.__init__(self,parent,visualizer,name,**kws)
    
    def initializeGUI(self):
        """
        Created: 22.04.2007, KP
        Description: Initialization
        """          
        pass
        
    def setModule(self,module):
        """
        Created: 22.04.2007, KP
        Description: Set the module to be configured
        """  
        ModuleConfigurationPanel.setModule(self,module)
        self.module=module
        self.gui = GUIBuilder.GUIBuilder(self, self.module)
        self.module.sendUpdateGUI()
        self.contentSizer.Add(self.gui,(0,0))

    def onApply(self,event):
        """
        Created: 22.04.2007, KP
        Description: Apply the changes
        """     
        self.module.updateRendering()
