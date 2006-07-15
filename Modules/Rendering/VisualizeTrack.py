# -*- coding: iso-8859-1 -*-

"""
 Unit: VisualizeTrack
 Project: BioImageXD
 Created: 29.05.2006, KP
 Description:

 A VisualizeTrack rendering module
           
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

import Track

def getClass():return VisualizeTrackModule
def getConfigPanel():return VisualizeTrackConfigurationPanel
def getName():return "Visualize Track"


class VisualizeTrackModule(VisualizationModule):
    """
    Class: VisualizeTrackModule
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

        self.descs = {"TrackFile":"Select the track file","AllTracks":"Show all tracks","Track":"Select the track to visualize","MinLength":"Minimum length of track"}
        
        self.track = None
        self.mapper = vtk.vtkDataSetMapper()
        self.actor = vtk.vtkActor()
        self.actor.SetMapper(self.mapper)
        self.actor.GetProperty().SetDiffuseColor(1,1,1)
        self.renderer = self.parent.getRenderer()
        self.renderer.AddActor(self.actor)

#        iactor = self.wxrenwin.GetRenderWindow().GetInteractor()
        

    def setParameter(self,parameter,value):
        """
        Method: setParameter
        Created: 13.04.2006, KP
        Description: Set a value for the parameter
        """    
        VisualizationModule.setParameter(self, parameter, value)
        if parameter == "TrackFile":
            print "Creating track with filename",value
            self.track = Track.Track(value)
            messenger.send(self,"update_MinLength")
            messenger.send(self,"update_Track")
            
        if parameter=="MinLength":
            messenger.send(self,"update_Track")
        
    def getParameters(self):
        """
        Method: getParametersit 
        Created: 31.05.2006, KP
        Description: Return the list of parameters needed for configuring this GUI
        """            
        return [ ["Load track",(("TrackFile","Select track file to load","*.csv"),)],
       ["Visualized track",("AllTracks","Track","MinLength")] ]
        
    def getDefaultValue(self,parameter):
        """
        Method: getDefaultValue
        Created: 13.04.2006, KP
        Description: Return the default value of a parameter
        """           
        if parameter == "TrackFile":return "tracks.csv"
        if parameter=="Track":return 0
        if parameter=="MinLength":return 3
        if parameter=="AllTracks":return False
            
    def getRange(self, parameter):
        """
        Method: getRange
        Created: 31.05.2006, KP
        Description: If a parameter has a certain range of valid values, the values can be queried with this function
        """     
        if parameter=="Track":
            if self.track:
                minlength = self.parameters["MinLength"]
                return 0,self.track.getNumberOfTracks(minlength)
                
            else:
                return 0,5
        elif parameter=="MinLength":
            if self.track:
                return 1,self.track.getMaximumTrackLength()
            else:
                return 1,100
        return 1,1
        
    def getType(self,parameter):
        """
        Method: getType
        Created: 13.04.2006, KP
        Description: Return the type of the parameter
        """    
        if parameter == "TrackFile":return GUIBuilder.FILENAME
        if parameter=="Track":return GUIBuilder.SLICE
        if parameter=="MinLength":return GUIBuilder.SLICE
        if parameter=="AllTracks":return types.BooleanType
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
        #data = self.data
        #self.mapper.SetInput(data)
        n, minLength = self.parameters["Track"],self.parameters["MinLength"]
        allTracks=self.parameters["AllTracks"]
        if self.track:
            if not allTracks:
                print "Getting track",n
                track = self.track.getTrack(n,minLength)
                tracks=[track]
            else:
                tracks = self.track.getTracks(minLength)
            polyGrid = vtk.vtkUnstructuredGrid()
            polyGrid.Allocate(len(tracks), 1)
                
            for track in tracks:
                print "Visualizing track=",track
                
                npts = len(track)
                polyLinePoints = vtk.vtkPoints()
                polyLinePoints.SetNumberOfPoints(npts)
                for i,point in enumerate(track):
                    polyLinePoints.InsertPoint(i,*point)
                
                polyLine = vtk.vtkPolyLine()
                polyLine.GetPointIds().SetNumberOfIds(npts)
                for i in range(npts):
                    polyLine.GetPointIds().SetId(i,i)
                polyGrid.InsertNextCell(polyLine.GetCellType(),
                                     polyLine.GetPointIds())
                            
                polyGrid.SetPoints(polyLinePoints)
            self.mapper.SetInput(polyGrid)
    
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


class VisualizeTrackConfiguration(ModuleConfiguration):
    def __init__(self,parent,visualizer):
        """
        Method: __init__(parent)
        Created: 29.05.2006, KP
        Description: Initialization
        """     
        ModuleConfiguration.__init__(self,parent,"VisualizeTrack")
        self.panel=VisualizeTrackConfigurationPanel(self,visualizer)

class VisualizeTrackConfigurationPanel(ModuleConfigurationPanel):
    def __init__(self,parent,visualizer,name="VisualizeTrack",**kws):
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
