# -*- coding: iso-8859-1 -*-
"""
 Unit: DataSource.py
 Project: Selli
 Created: 03.11.2004
 Creator: JM
 Description: Classes for managing 4D data located on disk

 Modified:  04.11.2004 JM - Fixed a few bugs and implemented a few methods

            09.11.2004 JM
            - modified: VtiDataSource.__init__()
            - added: VtiDataSource.LoadFromDuFile()

            10.11.2004 JM - numerous bug fixes made and compliance with class 
                            diagrams checked
            10.11.2004 KP, JM - DataSource gets the vtkImageData objects from 
                                CombinedDataUnit and writes them to disk
            17.11.2004 KP, JM - loadFromDuFile() now returns a dataunit of the 
                                type specified in the .du file

            26.11.2004 JM - More comments added
            11.01.2005 JV - Added comments

 Selli includes the following persons:
 JH - Juha Hyytiäinen, juhyytia@st.jyu.fi
 JM - Jaakko Mäntymaa, jahemant@cc.jyu.fi
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 JV - Jukka Varsaluoma, varsa@st.jyu.fi

 Copyright (c) 2004 Selli Project.
"""

__author__ = "Selli Project <http://sovellusprojektit.it.jyu.fi/selli/>"
__version__ = "$Revision: 1.37 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"


from ConfigParser import *
import vtk
import os.path

import Logging
import DataUnit

class DataSource:
    """
    Class: DataSource
    Created: 03.11.2004
    Creator: JM
    Description: A base class for different kinds of DataSources
    """


    def __init__(self):
        """
        Method: __init__()
        Created: 17.11.2004
        Creator: KP
        Description: Initialization
        """
        # DataSource has to know what kind of DataUnits it is able to load,
        # so they are listed here:
        self.classByName={"SourceDataUnit": DataUnit.SourceDataUnit,
        "ColocalizationDataUnit": DataUnit.ColocalizationDataUnit,
        "ColorCombinationDataUnit":DataUnit.ColorMergingDataUnit,
        "CorrectedSourceDataUnit":DataUnit.CorrectedSourceDataUnit,
        "VSIASourceDataUnit":DataUnit.VSIASourceDataUnit}

    def getDataSetCount(self):
        """
        Method: getDataSetCount
        Created: 03.11.2004
        Creator: JM
        Description: Returns the number of individual DataSets (=time points)
        managed by this DataSource
        NOT IMPLEMENTED HERE
        """
        raise "Abstract method getDataSetCount() in DataSource called"

    def getDataSet(self, i):
        """
        Method: getDataSet
        Created: 03.11.2004
        Creator: JM
        Description: Returns the DataSet at the specified index
        Parameters:   i       The index
        NOT IMPLEMENTED HERE
        """
        raise "Abstract method getDataSet() in DataSource called"

    def getName(self):
        """
        Method: getName()
        Created: 18.11.2004
        Creator: KP
        Description: Returns the name of the dataset series which this datasource
                     operates on
        """
        raise "Abstract method getName() in DataSource called"

    def getDimensions(self):
        """
        Method: getDimensions()
        Created: 14.12.2004
        Creator: KP
        Description: Returns the (x,y,z) dimensions of the datasets this 
                     dataunit contains
        """
        raise "Abstract method getDimensions() in DataSource called"

