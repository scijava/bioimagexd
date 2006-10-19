# -*- coding: iso-8859-1 -*-
"""
 Unit: MergingSettings.py
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

import vtk
from DataUnit import DataUnitSettings      
import Logging
        
class MergingSettings(DataUnitSettings):
    """
    Created: 27.03.2005, KP
    Description: Stores color merging related settings
    """
    def __init__(self,n=-1):
        """
        Created: 27.03.2005, KP
        Description: Constructor
        """
        DataUnitSettings.__init__(self,n)
        #self.registerCounted("MergingColorTransferFunction",1)       
        self.set("Type","Merging")
        self.registerCounted("IntensityTransferFunction",1)
        self.register("AlphaTransferFunction",1)
        self.register("AlphaMode")
        self.registerCounted("PreviewChannel")
        
        tf=vtk.vtkIntensityTransferFunction()
        self.set("AlphaTransferFunction",tf)
        self.set("AlphaMode",[0,0])

    def initialize(self,dataunit,channels, timepoints):
        """
        Created: 27.03.2005
        Description: Set initial values for settings based on 
                     number of channels and timepoints
        """
        DataUnitSettings.initialize(self,dataunit,channels,timepoints)

        #tf=vtk.vtkIntensityTransferFunction()
        #print "\n\n****' SETING RANGE OF ALPHA TF =",maxval
        #tf.SetRangeMax(maxval)    
        #self.set("AlphaTransferFunction",tf)
        
        
        for i in range(channels):
            tf=vtk.vtkIntensityTransferFunction()
            self.setCounted("IntensityTransferFunction",i,tf,0)
        self.set("PreviewChannel",1)
            
    def get(self,name):
        """
        Created: 03.07.2005
        Description: Return the value of a key
        """
        val=DataUnitSettings.get(self,name)
        if name=="MergingColorTransferFunction" and not val:
            val=DataUnitSettings.get(self,"ColorTransferFunction")
            Logging.info("Returning proxyed ctf for merging",val,kw="ctf")
            self.set("MergingColorTransferFunction",val)
            return val
        return val
