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
import DataUnitProcessing

import PreviewFrame

def getName():return "slices"
def getClass():return SlicesMode
def getImmediateRendering(): return True
def getRenderingDelay(): return 1500

        
class SlicesMode:
    def __init__(self,parent,visualizer):
        """
        Method: __init__
        Created: 24.05.2005, KP
        Description: Initialization
        """
        self.parent=parent
        self.visualizer=visualizer
        self.preview=None
        self.init=1
        self.dataUnit=None
        
    def showSideBar(self):
        """
        Method: showSideBar()
        Created: 24.05.2005, KP
        Description: Method that is queried to determine whether
                     to show the sidebar
        """
        return False
        
    def Render(self):
        """
        Method: Render()
        Created: 24.05.2005, KP
        Description: Update the rendering
        """      
        self.preview.updatePreview(0)
        
    def updateRendering(self):
        """
        Method: updateRendering
        Created: 26.05.2005, KP
        Description: Update the rendering
        """      
        print "Updating rendering..."
        self.preview.updatePreview(1)
        
    def setBackground(self,r,g,b):
        """
        Method: setBackground(r,g,b)
        Created: 24.05.2005, KP
        Description: Set the background color
        """      
        pass
  
    def deactivate(self):
        """
        Method: deactivate()
        Created: 24.05.2005, KP
        Description: Unset the mode of visualization
        """
        self.preview.Show(0)
  
    def activate(self,sidebarwin):
        """
        Method: activate()
        Created: 24.05.2005, KP
        Description: Set the mode of visualization
        """
        if not self.preview:
            print "Generating preview"
            self.preview=PreviewFrame.IntegratedPreview(self.parent,
            previewsize=(512,512),pixelvalue=False,renderingpreview=False,
            zoom=False,zslider=True,timeslider=False,scrollbars=False)
        return self.preview
            
        
        
    def setDataUnit(self,dataUnit):
        """
        Method: setDataUnit
        Created: 25.05.2005, KP
        Description: Set the dataunit to be visualized
        """
        print "setDataUnit(",dataUnit,")"
        if dataUnit == self.dataUnit:
            print "\n\n\nGot same dataunit\n\n\n"
            return
        if self.init:
            print "Setting preview type"
            self.preview.setPreviewType("")
            self.init=0
        if not self.visualizer.getProcessedMode():
            print "Using corrected source data unit"
            unit=DataUnit.CorrectedSourceDataUnit("preview")
            unit.addSourceDataUnit(dataUnit)
            unit.setModule(DataUnitProcessing.DataUnitProcessing())
        else:
            print "Using dataunit",dataUnit
            unit=dataUnit
        self.preview.setDataUnit(unit,0)
        
    def setTimepoint(self,tp):
        """
        Method: setTimepoint
        Created: 25.05.2005, KP
        Description: Set the timepoint to be visualized
        """
        print "Setting previewed timepoint"
        self.preview.setTimepoint(tp)
