# -*- coding: iso-8859-1 -*-
"""
 Unit: DataUnit.py
 Project: Selli
 Created: 03.11.2004
 Creator: JM
 Description: Classes for 4D DataUnits

 Modified: 09.11.2004 JM - modified: SourceDataUnit.__init__()
                           added: SourceDataUnit.setDataSource()
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
           27.03.2005 KP - Started merging / refactoring classes together
           
 Selli includes the following persons:
 JH - Juha Hyytiäinen, juhyytia@st.jyu.fi
 JM - Jaakko Mäntymaa, jahemant@cc.jyu.fi
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 JV - Jukka Varsaluoma, varsa@st.jyu.fi

 Copyright (c) 2004 Selli Project
"""

__author__ = "Selli Project <http://sovellusprojektit.it.jyu.fi/selli/>"
__version__ = "$Revision: 1.93 $"
__date__ = "$Date: 2005/01/13 14:09:15 $"

import Interpolation


import DataUnitProcessing
import Logging

class DataUnit:
    """
    Class: DataUnit
    Created: 03.11.2004, JM
    Description: A class representing a timeseries of 3D data
    """

    def __init__(self, name=""):
        """
        Method: __init__
        Created: 03.11.2004, JM
        Description: Constructor
        Parameters: name    Name for the DataUnit, default to ""
        """
        self.name = name
        self.length = 0
        self.dataSource=None
        self.color= None
        self.settings = None
    
    def getColor(self):
        """
        Method: getColor()
        Created: 27.03.2005, KP
        Description: Returns the color of this object
        """
        if not self.dataSource:
            return (010,101,010)
        if not self.color:
            self.color=self.dataSource.getColor()
            print "Got color from datasource:",self.color
        return self.color
        
    def setColor(self,color):
        """
        Method: getColor()
        Created: 28.03.2005, KP
        Description: Sets the color of this object
        """       
        self.color=color
    
    def setSettings(self,settings):
        """
        Method: setSettings
        Created: 27.03.2005, KP
        Description: Sets the settings object of this dataunit
        """
        self.settings = settings
        self.updateSettings()
    
    def updateSettings(self):
        """
        Method: updateSettings()
        Created: 28.03.2005, KP
        Description: Sets the settings of this object based on the datasource
        """
        if not self.settings:
            return
        color=self.getColor()
        print "My color is ",color
        if color:
            print "Setting color to ",color
            self.settings.set("Color",color)
        if self.dataSource:
            self.settings.set("VoxelSize",self.dataSource.getVoxelSize())
            self.settings.set("Spacing",self.dataSource.getSpacing())
            self.settings.set("Dimensions",self.dataSource.getDimensions())

    def getSettings(self):
        """
        Method: getSettings
        Created: 27.03.2005, KP
        Description: Returns the settings object of this dataunit
        """
        return self.settings
        
        
    def getName(self):
        """
        Method: getName
        Created: 03.11.2004, JM
        Description: Returns the name of this DataUnit
        """
        return self.name

    def setName(self,name):
        """
        Method: setName(name)
        Created: 8.12.2004, JM
        Description: Sets the name of this dataunit
        """
        self.name=name
        if self.settings:
            self.settings.set("Name",name)
 
    def getTimePoint(self,n):
        """
        Method: getTimePoint(n)
        Created: 17.11.2004, KP
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
        Created: 10.11.2004, JM
        Description: Returns the length of this DataUnit
        """
        return self.length

    def setDataSource(self, dataSource):
        """
        Method: setDataSource
        Created: 09.11.2004, JM
        Description: Sets a DataSource for this SourceDataUnit
        Parameters: dataSource  A DataSource to manage actual
                                image data located on disk
        """
        # Then load the settings specific to SourceDataUnit:
        self.dataSource = dataSource
        self.name = dataSource.getName()
        self.length=dataSource.getDataSetCount()
        
        self.getDimensions = dataSource.getDimensions
        self.getSpacing = dataSource.getSpacing
        self.getVoxelSize = dataSource.getVoxelSize
        print "Got datasource..."
        #self.updateSettings()
        
    def __str__(self):
        """
        Method: __str__
        Created: 27.03.2005, KP
        Description: Return the path to the file this dataunit represents
        """
        return str(self.dataSource)
