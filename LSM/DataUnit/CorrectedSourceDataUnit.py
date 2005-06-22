# -*- coding: iso-8859-1 -*-
"""
 Unit: CorrectedSourceDataUnit.py
 Project: BioImageXD
 Created: 01.01.2004, KP
 Description: Classes for 4D DataUnits

 Modified: 01.01.2005 KP - Split the class from DataUnit.py to a module of it's own

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

__author__ = "Selli Project <http://sovellusprojektit.it.jyu.fi/selli/>"
__version__ = "$Revision: 1.93 $"
__date__ = "$Date: 2005/01/13 14:09:15 $"

import Interpolation
import ImageOperations

import vtk

import DataUnitProcessing
import Logging
import DataSource
from CombinedDataUnit import *


class CorrectedSourceDataUnit(CombinedDataUnit):
    """
    Class: CorrectedSourceDataUnit
    Created: 24.11.2004, JM, JV
    Description: Class for a corrected single-channel 4D DataUnit
    """

    def __init__(self,name=""):
        """
        Method: __init__
        Created: 27.03.2005 KP
        Description: Constructor
        """
        CombinedDataUnit.__init__(self,name)
        self.original = None

    def setOriginal(self, dataUnit):
        """
        Method: setOriginal
        Created: 14.12.2004, JM, JV
        Description: Sets the original DataUnit for this ProcessedSourceDataUnit
        Parameters: dataUnit  The original unmodified DataUnit
        """
        self.original = dataUnit
        self.length = dataUnit.length

    def interpolateIntensities(self):
        """
        Method: interpolateIntensities()
        Created: 13.12.2004, KP
        Description: Interpolates intensity transfer functions for timepoints 
                     between a given list of timepoints
        """
        interpolationTimepoints=self.settings.get("InterpolationTimepoints")
        if len(interpolationTimepoints)<2:
            Logging.error("Cannot interpolate from one timepoint",
            "You need to specify at least two timepoints for interpolation")
            return
        lst=interpolationTimepoints[:]
        while -1 in lst:
            lst.remove(-1)
        for i in range(1,len(lst)):
            fromtp=lst[i-1]
            totp=lst[i]
            n=max(fromtp,totp)
            if n>=self.length:
                Logging.error("No such timepoint",
                "Timepoint %d is out of range. "\
                "There are %d timepoints"%(n,self.length))
                continue
            print "Interpolating from %d to %d"%(fromtp,totp)
            self.interpolateIntensitiesBetween(fromtp,totp)

    def interpolateIntensitiesBetween(self,timepoint1,timepoint2):
        """
        Method: interpolateIntensitiesBetween(timepoint1,timepoint2)
        Created: 09.12.2004, KP
        Description: Interpolates intensity transfer functions for timepoints 
                     between timepoint1 and timepoint2
        """
        if timepoint1>timepoint2:
            timepoint2,timepoint1=timepoint1,timepoint2
        n=timepoint2-timepoint1
        itf1=self.settings.getCounted("IntensityTransferFunctions",timepoint1)
        itf2=self.settings.getCounted("IntensityTransferFunctions",timepoint2)
        params1=ImageOperations.getAsParameterList(itf1)
        params2=ImageOperations.getAsParameterList(itf2)
        # There are n-1 timepoints between the specified timepoints
        params=Interpolation.interpolate(params1,params2,n-1)
        print "params1=",params1
        print "params2=",params2
        print "Interpolated %d new paramlists"%len(params)
        for i in range(n-1):
            print "Setting new parameters for timepoint ",timepoint1+i+1
            iTF=self.settings.getCounted("IntensityTransferFunctions",timepoint1+i+1)
            ImageOperations.setFromParameterList(iTF,params[i])
            self.settings.setCounted("IntensityTransferFunctions",timepoint1+i+1,iTF)
       

    def getColorTransferFunction(self):
        """
        Method: getColorTransferFunction()
        Created: 21.06.2005, KP
        Description: Returns the ctf of the source dataunit
        """
        return self.original.getColorTransferFunction()
       
    def addSourceDataUnit(self,dataUnit):
        """
        Method: addSourceDataUnit
        Created: 27.03.2005
        Creator: KP
        Description: Adds a source data unit to this dataunit"
        """
        self.setOriginal(dataUnit)    
        CombinedDataUnit.addSourceDataUnit(self,dataUnit)
        self.name = "Processed_%s"%dataUnit.getName()
        print "Updating settings for corrected source dataunit"
        #print dataUnit.getColorTransferFunction()
        self.updateSettings()
        #print self.settings.get("ColorTransferFunction")
  
    def copyIntensityTransferFunctionToAll(self,iTF):
        """
        Method: copyIntensityTransferFunctionToAll(transferfunction)
        Created: 13.1.2005
        Creator: KP
        Description: Sets the IntensityTransferFunction instace for
                     all timePoints
        """
        for tf in self.intensityTransferFunctions:
            tf.setFromParameterList(iTF.getAsParameterList())
    
    def getSettingClass(self):
        """
        Method: getSettingClass()
        Created: 02.04.2005, KP
        Description: Return the class that represents settings for this dataunit
        """
        return SingleUnitProcessingSettings

        
    def __str__(self):
        """
        Method: __str__
        Created: 02.06.2005, KP
        Description: Return string representation of self
        """
        return str(self.__class__)
