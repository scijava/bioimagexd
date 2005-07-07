# -*- coding: iso-8859-1 -*-
"""
 Unit: SlicesMode
 Project: BioImageXD
 Created: 28.04.2005, KP
 Description:

 A slices viewing rendering mode for Visualizer
 
 Modified 28.04.2005 KP - Created the class
          23.05.2005 KP - Split the class to a module of it's own
          
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
import DataUnit

import PreviewFrame

def getName():return "gallery"
def getClass():return GalleryMode
def getImmediateRendering(): return False
def getConfigPanel(): return None
def getRenderingDelay(): return 500
def showZoomToolbar(): return True
    
class GalleryMode:
    def __init__(self,parent,visualizer):
        """
        Method: __init__
        Created: 24.05.2005, KP
        Description: Initialization
        """
        self.parent=parent
        self.visualizer=visualizer
        self.galleryPanel=None
        self.timepoint=0
        self.enabled=1
        self.dataUnit=None
        
    def annotate(self,annclass,**kws):
        """
        Method: annotate(annotationclass)
        Created: 04.07.2005, KP
        Description: Add an annotation to the scene
        """
        if self.galleryPanel:
            self.galleryPanel.addAnnotation(annclass,**kws)
        
    def manageAnnotation(self):
        """
        Method: manageAnnotation()
        Created: 04.07.2005, KP
        Description: Manage annotations on the scene
        """
        if self.galleryPanel:
            self.galleryPanel.manageAnnotation()

    def zoomObject(self):
        """
        Method: zoomObject()
        Created: 04.07.2005, KP
        Description: Zoom to a user selected portion of the image
        """
        if self.preview:
            self.preview.renderpanel.zoomObject()
                
        
    def zoomToFit(self):
        """
        Method: zoomToFit()
        Created: 05.06.2005, KP
        Description: Zoom the dataset to fit the available screen space
        """
        if self.galleryPanel:
            self.galleryPanel.zoomToFit()
    
    def setZoomFactor(self,factor):
        """
        Method: setZoomFactor(factor)
        Created: 05.06.2005, KP
        Description: Set the factor by which the image is zoomed
        """
        if self.galleryPanel:
            self.galleryPanel.setZoomFactor(factor)        
        
    def showSideBar(self):
        """
        Method: showSideBar()
        Created: 24.05.2005, KP
        Description: Method that is queried to determine whether
                     to show the sidebar
        """
        return False
  
    def setBackground(self,r,g,b):
        """
        Method: setBackground(r,g,b)
        Created: 24.05.2005, KP
        Description: Set the background color
        """        
        self.galleryPanel.setBackground(r,g,b)
        
    def Render(self):
        """
        Method: Render()
        Created: 24.05.2005, KP
        Description: Update the rendering
        """      
        pass        
        
    def enable(self,flag):
        """
        Method: enable(flag)
        Created: 02.06.2005, KP
        Description: Enable/Disable updates
        """
        self.enabled=flag        
        
    def updateRendering(self):
        """
        Method: updateRendering
        Created: 26.05.2005, KP
        Description: Update the rendering
        """      
        if not self.enabled:
            Logging.info("Visualizer is disabled, won't update gallery",kw="visualizer")
            return
        Logging.info("Updating gallery",kw="visualizer")
        self.galleryPanel.setTimepoint(self.timepoint)
        self.galleryPanel.updatePreview()
        self.galleryPanel.Refresh()
  
    def activate(self,sidebarwin):
        """
        Method: activate()
        Created: 24.05.2005, KP
        Description: Set the mode of visualization
        """
        if not self.galleryPanel:
            x,y=self.visualizer.visWin.GetSize()
            self.galleryPanel=PreviewFrame.GalleryPanel(self.parent,self.visualizer,size=(x,y))
        return self.galleryPanel
        
    def deactivate(self):
        """
        Method: deactivate()
        Created: 24.05.2005, KP
        Description: Unset the mode of visualization
        """
        self.galleryPanel.Show(0)        
        
    def setDataUnit(self,dataUnit):
        """
        Method: setDataUnit
        Created: 25.05.2005, KP
        Description: Set the dataunit to be visualized
        """
        self.galleryPanel.setDataUnit(dataUnit)
        self.dataUnit=dataUnit
        
    def setTimepoint(self,tp):
        """
        Method: setTimepoint
        Created: 25.05.2005, KP
        Description: Set the timepoint to be visualized
        """
        self.timepoint=tp
        self.galleryPanel.setTimepoint(tp)

    def saveSnapshot(self,filename):
        """
        Method: saveSnapshot(filename)
        Created: 05.06.2005, KP
        Description: Save a snapshot of the scene
        """      
        self.galleryPanel.saveSnapshot(filename)
