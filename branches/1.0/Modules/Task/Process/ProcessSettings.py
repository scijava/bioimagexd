# -*- coding: iso-8859-1 -*-

"""
 Unit: ProcessSetting
 Project: BioImageXD
 Created: 26.03.2005, KP
 Description:

 This is a class that holds all settings of a dataunit. A dataunit's 
 setting object is the only thing differentiating it from another
 dataunit.
 
 This code was re-written for clarity. The code produced by the
 Selli-project was used as a starting point for producing this code.
 http://sovellusprojektit.it.jyu.fi/selli/ 

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
__author__ = "BioImageXD Project <http://www.bioimagexd.org/>"
__version__ = "$Revision: 1.21 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

from DataUnit import DataUnitSettings

class ProcessSettings(DataUnitSettings):
    """
    Class: ProcessSettings
    Created: 27.03.2005, KP
    Description: Stores settings related to single unit processing
    """
    def __init__(self,n=-1):
        """
        Method: __init__
        Created: 27.03.2005, KP
        Description: Constructor
        """
        DataUnitSettings.__init__(self,n)
#        self.register("ColorTransferFunction")        
        self.register("MedianFiltering",serialize=1)
        self.register("AnisotropicDiffusion",serialize=1)
        self.register("AnisotropicDiffusionMeasure",serialize=1)
        self.register("AnisotropicDiffusionThreshold",serialize=1)
        self.register("AnisotropicDiffusionFactor",serialize=1)
        self.register("AnisotropicDiffusionFaces",serialize=1)
        self.register("AnisotropicDiffusionEdges",serialize=1)
        self.register("AnisotropicDiffusionCorners",serialize=1)
        
        
        self.register("MedianNeighborhood",serialize=1)
        self.register("SolitaryFiltering",serialize=1)
        self.register("SolitaryHorizontalThreshold",serialize=1)
        self.register("SolitaryVerticalThreshold",serialize=1)
        self.register("SolitaryProcessingThreshold",serialize=1)
        self.set("Type","Process")
        
        self.registerPrivate("ColorTransferFunction",1)        
        self.registerCounted("Source")
        self.register("VoxelSize")
        self.register("Spacing")
        #self.register("Origin")
        self.register("Dimensions")
        self.register("Type")
        self.register("Name")
        self.register("BitDepth")
        
        self.set("MedianFiltering",0)
        self.set("MedianNeighborhood",[1,1,1])
        self.set("SolitaryFiltering",0)
        self.set("SolitaryHorizontalThreshold",0)
        self.set("SolitaryVerticalThreshold",0)
        self.set("SolitaryProcessingThreshold",0)      

        self.set("AnisotropicDiffusionFaces",1)
        self.set("AnisotropicDiffusionCorners",1)
        self.set("AnisotropicDiffusionEdges",1)
        self.set("AnisotropicDiffusionMeasure",1)
        self.set("AnisotropicDiffusionThreshold",5.0)
        self.set("AnisotropicDiffusionFactor",1.0)
        
    def initialize(self,dataunit,channels, timepoints):
        """
        Method: initialize(dataunit,channels, timepoints)
        Created: 27.03.2005
        Description: Set initial values for settings based on 
                     number of channels and timepoints
        """
        DataUnitSettings.initialize(self,dataunit,channels,timepoints)
        ctf = self.get("ColorTransferFunction")