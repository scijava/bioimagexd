# -*- coding: iso-8859-1 -*-
"""
 Unit: DataUnit.py
 Project: Selli
 Created: 03.11.2004
 Creator: JM
 Description: Classes for 4D DataUnits

 Modified: 09.11.2004 JM
    - modified: SourceDataUnit.__init__()
    - added: SourceDataUnit.setDataSource()
           09.11.2004 KP - getTimePoint() uses DataSource for reading timepoints
                           from disk

           10.11.2004 JM - numerous bug fixes made and compliance with class 
                           diagrams checked

           24.11.2004 JM - Added validity checks to set-methods,
                           class ProcessedSourceDataUnit added

           25.11.2004 JV - Added VSIA

           26.11.2004 JM - more comments added
           09.12.2004 KP - Added method for intepolating intensity transfer 
                           functions
           10.12.2004 JV - set/getNeighborhood, 
                           set/getProcessingSolitaryThreshold,
                           passes settings to DataUnitProcessing
           11.12.2004 JV - Added: doProcessing, does not work
           13.12.2004 JV - Processing and saving works
           14.12.2004 JM - More validity checks added
           14.12.2004 JV,JM - Loading of settings in ProcessedSourceDataUnit
           17.12.2004 JV - Handles the settings to module
           04.01.2005 JV - VSIASourceDataUnit saves and loads settings

 Selli includes the following persons:
 JH - Juha Hyytiäinen, juhyytia@st.jyu.fi
 JM - Jaakko Mäntymaa, jahemant@cc.jyu.fi
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 JV - Jukka Varsaluoma, varsa@st.jyu.fi

 Copyright (c) 2004 Selli Project.
"""

__author__ = "Selli Project <http://sovellusprojektit.it.jyu.fi/selli/>"
__version__ = "$Revision: 1.93 $"
__date__ = "$Date: 2005/01/13 14:09:15 $"

import Interpolation

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
        if len(self.interpolationTimePoints)<2:
            Logging.error("Cannot interpolate from one timepoint",
            "You need to specify at least two timepoints for interpolation")
            return
        lst=self.interpolationTimePoints[:]
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
        params1=self.intensityTransferFunctions[timepoint1].getAsParameterList()
        params2=self.intensityTransferFunctions[timepoint2].getAsParameterList()
        # There are n-1 timepoints between the specified timepoints
        params=Interpolation.interpolate(params1,params2,n-1)
        print "params1=",params1
        for i in params:
            print i
        print "params2=",params2
        print "Interpolated %d new paramlists"%len(params)
        for i in range(n-1):
            print "Setting new parameters for timepoint ",timepoint1+i+1
            iTF=self.intensityTransferFunctions[timepoint1+i+1]
            iTF.setFromParameterList(params[i])
       
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
        self.updateSettings()
  
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
    
