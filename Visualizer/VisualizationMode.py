# -*- coding: iso-8859-1 -*-

"""
 Unit: VisualizationMode
 Project: BioImageXD
 Created: 28.04.2005, KP
 Description:

 A module that contains the base class for various view modes
          
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
from ModuleConfiguration import *
import Dialogs
import Logging
import Modules
import DataUnit

import messenger
import glob
import os,sys

class VisualizationMode:
    """
    Class: VisualizationMode
    Created: 21.07.2005, KP
    Description: A class representing a visualization mode
    """
    def __init__(self,parent,visualizer,**kws):
        """
        Method: __init__(parent)
        Created: 28.04.2005, KP
        Description: Initialization
        """    

        self.parent = parent
        self.dataUnit = None
        self.enabled=1
        self.iactivePanel = None
        self.timepoint=0

        self.visualizer=visualizer
        
   
    def layoutTwice(self):
        """
        Method: layoutTwice()
        Created: 20.12.2005, KP
        Description: Method that is queried for whether the mode needs to
                     be laid out twice
        """
        return False
        
    def annotate(self,annclass,**kws):
        """
        Method: annotate(annotationclass)
        Created: 04.07.2005, KP
        Description: Add an annotation to the scene
        """
        if self.iactivePanel:
            self.iactivePanel.addAnnotation(annclass,**kws)
        
    def manageAnnotation(self):
        """
        Method: manageAnnotation()
        Created: 04.07.2005, KP
        Description: Manage annotations on the scene
        """
        if self.iactivePanel:
            self.iactivePanel.manageAnnotation()

    def deleteAnnotation(self):
        """
        Method: deleteAnnotation()
        Created: 15.08.2005, KP
        Description: Delete annotations on the scene
        """
        if self.iactivePanel:
            self.iactivePanel.deleteAnnotation()
            
    def zoomObject(self):
        """
        Method: zoomObject()
        Created: 04.07.2005, KP
        Description: Zoom to a user selected portion of the image
        """
        if self.iactivePanel:
            self.iactivePanel.startRubberband()
            
        
    def zoomToFit(self):
        """
        Method: zoomToFit()
        Created: 05.06.2005, KP
        Description: Zoom the dataset to fit the available screen space
        """
        if self.iactivePanel:
            self.iactivePanel.zoomToFit()
            
    
    def setZoomFactor(self,factor):
        """
        Method: setZoomFactor(factor)
        Created: 05.06.2005, KP
        Description: Set the factor by which the image is zoomed
        """
        if self.iactivePanel:
            self.iactivePanel.setZoomFactor(factor)  
            
    def getZoomFactor(self):
        """
        Method: getZoomFactor(factor)
        Created: 01.08.2005, KP
        Description: Get the zoom factor
        """
        if self.iactivePanel:
            return self.iactivePanel.getZoomFactor()   
        return 1.0
            
    def showSideBar(self):
        """
        Method: showSideBar()
        Created: 24.05.2005, KP
        Description: Method that is queried to determine whether
                     to show the sidebar
        """
        return False
        
    def showSliceSlider(self):
        """
        Method: showSliceSlider()
        Created: 07.08.2005, KP
        Description: Method that is queried to determine whether
                     to show the zslider
        """
        return False   
   
    def showViewAngleCombo(self):
        """
        Method: showViewAngleCombo()
        Created: 11.08.2005, KP
        Description: Method that is queried to determine whether
                     to show the view angle combo box in the toolbar
        """
        return False  
        
    def closeOnReload(self):
        """
        Method: closeOnReload
        Created: 1.09.2005, KP
        Description: Method to determine whether the visualization mode
                     should be closed if the user clicks it again.
        """    
        return False
  
    def setBackground(self,r,g,b):
        """
        Method: setBackground(r,g,b)
        Created: 24.05.2005, KP
        Description: Set the background color
        """        
        self.iactivePanel.setBackground(r,g,b)

    def setDataUnit(self,dataunit):
        """
        Method: setDataUnit(self)
        Created: 28.04.2005, KP
        Description: Sets the dataunit this module uses for visualization
        """            
        self.dataUnit = dataunit
        if not dataunit.getSettings():
            settings=DataUnit.DataUnitSettings()
            dataunit.setSettings(settings)        
        if self.iactivePanel:
            self.iactivePanel.setDataUnit(dataunit)
        
    def getDataUnit(self):
        """
        Method: getDataUnit()
        Created: 28.04.2005, KP
        Description: Returns the dataunit this module uses for visualization
        """     
        return self.dataUnit
        
    def setTimepoint(self,tp):
        """
        Method: setTimepoint
        Created: 25.05.2005, KP
        Description: Set the timepoint to be visualized
        """
        self.timepoint=tp
        self.iactivePanel.setTimepoint(tp)

    def saveSnapshot(self,filename):
        """
        Method: saveSnapshot(filename)
        Created: 05.06.2005, KP
        Description: Save a snapshot of the scene
        """      
        self.iactivePanel.saveSnapshot(filename)
        
    def deactivate(self,newmode=None):
        """
        Method: deactivate()
        Created: 24.05.2005, KP
        Description: Unset the mode of visualization
        """
        self.iactivePanel.Show(0)        
        
    def Render(self):
        """
        Method: Render()
        Created: 24.05.2005, KP
        Description: Update the rendering
        """      
        self.iactivePanel.Refresh()
                
    def relayout(self):
        """
        Method: relayout()
        Created: 07.08.2005, KP
        Description: Method called when the size of the window changes
        """    
        pass
        
    def reloadMode(self):
        """
        Method: reloadMode()
        Created: 1.09.2005, KP
        Description: Method called when the user tries to reload the mode
        """    
        pass
