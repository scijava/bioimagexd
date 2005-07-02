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

def getName():return "sections"
def getClass():return SectionsMode
def getImmediateRendering(): return False
def getConfigPanel(): return None
def getRenderingDelay(): return 500
def showZoomToolbar(): return True    

        
class SectionsMode:
    def __init__(self,parent,visualizer):
        """
        Method: __init__
        Created: 24.05.2005, KP
        Description: Initialization
        """
        self.parent=parent
        self.timepoint=0
        self.visualizer=visualizer
        self.dataUnit=None
        self.sectionsPanel=None
        
    def setBackground(self,r,g,b):
        """
        Method: setBackground(r,g,b)
        Created: 24.05.2005, KP
        Description: Set the background color
        """      
        pass
    def Render(self):
        """
        Method: Render()
        Created: 24.05.2005, KP
        Description: Update the rendering
        """      
        pass        
    def updateRendering(self):
        """
        Method: updateRendering
        Created: 26.05.2005, KP
        Description: Update the rendering
        """      
        self.sectionsPanel.setTimepoint(self.timepoint)
        
    def showSideBar(self):
        """
        Method: showSideBar()
        Created: 24.05.2005, KP
        Description: Method that is queried to determine whether
                     to show the sidebar
        """
        return False
  
    def activate(self,sidebarwin):
        """
        Method: activate()
        Created: 24.05.2005, KP
        Description: Set the mode of visualization
        """
        if not self.sectionsPanel:
            x,y=self.visualizer.visWin.GetSize()
            self.sectionsPanel=PreviewFrame.SectionsPanel(self.parent,self.visualizer,size=(x,y))
        return self.sectionsPanel
        
    def deactivate(self):
        """
        Method: deactivate()
        Created: 24.05.2005, KP
        Description: Unset the mode of visualization
        """
        self.sectionsPanel.Show(0)
        

        
    def setDataUnit(self,dataUnit):
        """
        Method: setDataUnit
        Created: 25.05.2005, KP
        Description: Set the dataunit to be visualized
        """
        self.sectionsPanel.setDataUnit(dataUnit)
        self.dataUnit=dataUnit
        
    def setTimepoint(self,tp):
        """
        Method: setTimepoint
        Created: 25.05.2005, KP
        Description: Set the timepoint to be visualized
        """
        self.timepoint=tp
        self.sectionsPanel.setTimepoint(tp)
