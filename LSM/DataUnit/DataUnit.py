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
from Color24bit import *


import DataUnitProcessing
import VSIA
import Logging




class DataUnit:
    """
    Class: DataUnit
    Created: 03.11.2004
    Creator: JM
    Description: Base class for a 4D DataUnit
    """

    def __init__(self, name=""):
        """
        Method: __init__
        Created: 03.11.2004
        Creator: JM
        Description: Constructor
        Parameters: name    Name for the DataUnit, default to ""
        """
        self.name = name
        self.length = 0

    def getName(self):
        """
        Method: getName
        Created: 03.11.2004
        Creator: JM
        Description: Returns the name of this DataUnit
        """
        return self.name

    def setName(self,name):
        """
        Method: setName(name)
        Created: 8.12.2004
        Creator: JM
        Description: Sets the name of this dataunit
        """
        self.name=name


    def setDataSource(self,dataSource):
        """
        Method: setDataSource()
        Created: 15.11.2004
        Creator: KP
        Description: Sets the datasource for this dataunit. Also reads the name 
                     and length of the dataunit from the datasource.
        """
        self.dataSource = dataSource
        self.name = dataSource.getName()
        self.length=dataSource.getDataSetCount()
#        self.name = dataSource.getSetting("DataUnit","name")
#        self.length = int(dataSource.getSetting("VTIFiles", "numberOfFiles"))


    def getTimePoint(self,n):
        """
        Method: getTimePoint(n)
        Created: 17.11.2004
        Creator: KP
        Description: Returns the requested time point
        Parameters:
                n       The timepoint we need to return
        """
        if not self.dataSource:
            Logging.error("No datasource specified",
            "No datasource specified for DataUnit, unable to get timepoint!")
            return None
        return self.dataSource.getDataSet(n)


    def getLength(self):
        """
        Method: getLength
        Created: 10.11.2004
        Creator: JM
        Description: Returns the length of this DataUnit
        """
        return self.length

    def __str__(self):
        """
        Method: __str__
        Created: 03.11.2004
        Creator: JM
        Description: Returns the basic information of this instance as a string
                     (mainly for testing purposes)
        """
        return str(self.dataSource)

class SourceDataUnit(DataUnit):
    """
    Class: SourceDataUnit
    Created: 03.11.2004
    Creator: JM
    Description: Base class for a single-channel 4D DataUnit
    """

    def __init__(self,name=""):
        """
        Method: __init__
        Created: 03.11.2004
        Creator: JM
        Description: Constructor
        """
        DataUnit.__init__(self,name)
        self.dataSource=None
        self.color = Color24bit()

    def setDataSource(self, dataSource):
        """
        Method: setDataSource
        Created: 09.11.2004
        Creator: JM
        Description: Sets a DataSource for this SourceDataUnit
        Parameters: dataSource  A DataSource to manage actual
                                image data located on disk
        """
        # Call the base class to read the basic information from the file
        DataUnit.setDataSource(self,dataSource)

        # Then load the settings specific to SourceDataUnit:
        color=dataSource.getSetting("SourceDataUnit","color")
        print "color='%s'"%color
        red,green,blue=color.split(",")
        self.setColor(int(red),int(green),int(blue))

    def getDimensions(self):
        """
        Method: getDimensions()
        Created: 14.12.2004
        Creator: KP
        Description: Returns the (x,y,z) dimensions of the datasets this 
                     dataunit contains
        """
        return self.dataSource.getDimensions()

    def getOrigin(self):
        """
        Method: getOrigin()
        Created: 21.02.2005
        Creator: KP
        Description: Returns the origin of the dataset
        """
        return self.dataSource.getOrigin()
        
    def getSpacing(self):
        """
        Method: getSpacing()
        Created: 21.02.2005
        Creator: KP
        Description: Returns the spacing of the dataset
        """
        return self.dataSource.getSpacing()
        
    def getVoxelSize(self):
        """
        Method: getVoxelSize()
        Created: 21.02.2005
        Creator: KP
        Description: Returns the size of the voxel
        """    
        return self.dataSource.getVoxelSize()

    def setColor(self, red, green, blue):
        """
        Method: setColor
        Created: 03.11.2004
        Creator: JM
        Description: sets the color of this DataUnit
        Parameters: red     The value of red component
                    green   The value of green component
                    blue    The value of blue component
        """
        self.color.setValues(red, green, blue)

    def getColor(self):
        """
        Method: getColor
        Created: 24.11.2004
        Creator: JM
        Description: returns the color of this dataunit
        """
        return self.color.getColor()


