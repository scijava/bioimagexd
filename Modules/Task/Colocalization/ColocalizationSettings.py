# -*- coding: iso-8859-1 -*-

"""
 Unit: ColocalizationSettings
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
        
class ColocalizationSettings(DataUnitSettings):
    """
    Class: ColocalizationSettings
    Created: 26.03.2005, KP
    Description: Registers keys related to colocalization in a dataunitsetting
    """
    def __init__(self,n=-1):
        """
        Method: __init__
        Created: 26.03.2005, KP
        Description: Constructor
        """
        DataUnitSettings.__init__(self,n)
        
        self.set("Type","ColocalizationSettings")
        self.registerCounted("ColocalizationLowerThreshold")
        self.registerCounted("ColocalizationUpperThreshold")

        self.register("PearsonsCorrelation")
        self.register("OverlapCoefficient")
        self.register("OverlapCoefficientK1")
        self.register("OverlapCoefficientK2")
        self.register("ColocalizationCoefficientM1")
        self.register("ColocalizationCoefficientM2")
        
        self.set("PearsonsCorrelation",0)
        self.set("OverlapCoefficient",0)
        self.set("OverlapCoefficientK1",0)
        self.set("OverlapCoefficientK2",0)
        self.set("ColocalizationCoefficientM1",0)
        self.set("ColocalizationCoefficientM2",0)        
        
        self.register("ColocalizationColorTransferFunction",1)
        ctf = vtk.vtkColorTransferFunction()
        ctf.AddRGBPoint(0,0,0,0)
        ctf.AddRGBPoint(255, 1.0, 1.0, 1.0)
        self.set("ColocalizationColorTransferFunction",ctf)
        self.register("ColocalizationDepth")
        self.set("ColocalizationDepth",8)
        self.register("ColocalizationAmount")
        self.register("ColocalizationLeastVoxelsOverThreshold")

    def initialize(self,dataunit,channels, timepoints):
        """
        Method: initialize(dataunit,channels, timepoints)
        Created: 27.03.2005
        Description: Set initial values for settings based on 
                     number of channels and timepoints
        """
        DataUnitSettings.initialize(self,dataunit,channels,timepoints)
        print "Initializing colocaliztion for %d channels"%channels
        for i in range(channels):
            self.setCounted("ColocalizationLowerThreshold",i,128,0)
            self.setCounted("ColocalizationUpperThreshold",i,255,0)    
