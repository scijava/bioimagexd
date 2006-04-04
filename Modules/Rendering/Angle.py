# -*- coding: iso-8859-1 -*-

"""
 Unit: Angle
 Project: BioImageXD
 Created: 04.04.2006, KP
 Description:

 A module containing an angle measuring widget
           
 Copyright (C) 2006  BioImageXD Project
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


from Visualizer.VisualizationModules import *

def getClass():return AngleModule
def getConfigPanel():return AngleConfigurationPanel
def getName():return "Angle"


class AngleModule(VisualizationModule):
    """
    Class: angleModule
    Created: 03.04.2005, KP
    Description: A module for measuring the angle between two points
    """    
    def __init__(self,parent,visualizer,**kws):
        """
        Method: __init__(parent)
        Created: 03.05.2005, KP
        Description: Initialization
        """     
        self.x,self.y,self.z=-1,-1,-1
        VisualizationModule.__init__(self,parent,visualizer,**kws)   
        #self.name = "Clipping Plane"
        self.on = 0
        self.renew = 1
    
        self.angleWidget = vtk.vtkAngleWidget()
        self.angleWidget.CreateDefaultRepresentation()
        self.renderer = self.parent.getRenderer()
        iactor = self.wxrenwin.GetRenderWindow().GetInteractor()
        self.angleWidget.SetInteractor(iactor)
        #self.updateRendering()
        
    def __getstate__(self):
        """
        Method: __getstate__
        Created: 02.08.2005, KP
        Description: A getstate method that saves the lights
        """            
        odict=VisualizationModule.__getstate__(self)
        odict.update({"angleWidget":self.getVTKState(self.angleWidget)})
        
        odict.update({"renderer":self.getVTKState(self.renderer)})
        odict.update({"camera":self.getVTKState(self.renderer.GetActiveCamera())})
        return odict
        
    def __set_pure_state__(self,state):
        """
        Method: __set_pure_state__()
        Created: 02.08.2005, KP
        Description: Set the state of the light
        """        
        self.setVTKState(self.angleWidget,state.angleWidget)
        
        self.setVTKState(self.renderer,state.renderer)
        self.setVTKState(self.renderer.GetActiveCamera(),state.camera)

        VisualizationModule.__set_pure_state__(self,state)
                
        
        
    def setDataUnit(self,dataunit):
        """
        Method: setDataUnit(self)
        Created: 28.04.2005, KP
        Description: Sets the dataunit this module uses for visualization
        """       
        VisualizationModule.setDataUnit(self,dataunit)
        if self.visualizer.getProcessedMode():
            data=self.dataUnit.getSourceDataUnits()[0].getTimePoint(0)
        else:
            data=self.dataUnit.getTimePoint(0)
        sx,sy,sz = data.GetSpacing()
        
        

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
        
        if self.renew:

#            self.angleWidget.SetInput(self.data)
            self.renew=0
        
        if not self.on:
            self.angleWidget.On()
            self.on = 1
        
        #self.mapper.Update()
        VisualizationModule.updateRendering(self,input)
        self.parent.Render()    

    def disableRendering(self):
        """
        Method: disableRendering()
        Created: 15.05.2005, KP
        Description: Disable the Rendering of this module
        """          
        self.angleWidget.Off()
        self.wxrenwin.Render()
        
    def showPlane(self,flag):
        """
        Method: showPlane
        Created: 24.06.2005, KP
        Description: Show / hide the plane controls
        """          
        if flag:
            self.angleWidget.On()
        else:
            self.angleWidget.Off()
        
        
    def enableRendering(self):
        """
        Method: enableRendering()
        Created: 24.06.2005, KP
        Description: Enable the Rendering of this module
        """          
        self.angleWidget.On()
        self.wxrenwin.Render()
        
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


class AngleConfiguration(ModuleConfiguration):
    def __init__(self,parent,visualizer):
        """
        Method: __init__(parent)
        Created: 04.05.2005, KP
        Description: Initialization
        """     
        ModuleConfiguration.__init__(self,parent,"Angle")
        self.panel=angleConfigurationPanel(self,visualizer)

class AngleConfigurationPanel(ModuleConfigurationPanel):
    def __init__(self,parent,visualizer,name="Angle",**kws):
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
        
    def onApply(self,event):
        """
        Method: onApply()
        Created: 28.04.2005, KP
        Description: Apply the changes
        """     
        pass
