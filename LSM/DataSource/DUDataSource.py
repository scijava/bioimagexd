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
from DataSource import *
import DataUnit
import vtk
import os.path

import Logging
import DataUnit


class VtiDataSource(DataSource):
    """
    Class: DataSource
    Created: 03.11.2004, JM
    Description: Manages 4D data stored in du- and vti-files
    """

    def __init__(self,filename=""):
        """
        Method: __init__
        Created: 03.11.2004, JM
        Description: Constructor
        """
        DataSource.__init__(self)
        # list of references to individual datasets (= timepoints) stored in 
        # vti-files
        self.dataSets = []
        # filename of the .du-file
        self.filename = filename
        # path to the .du-file and .vti-file(s)
        self.path=""
        
        # Number of datasets added to this datasource
        self.counter=0
        self.parser = None

        # TODO: what is this?
        self.dataUnitSettings={}
        self.dimensions=None
        self.spacing = None
        self.voxelsizes=None
        
    def getParser(self):
        """
        Method: getParser()
        Created: 27.03.2005, KP
        Description: Returns the parser that is used to read the .du file
        """
        return self.parser
        
    def getDataSetCount(self):
        """
        Method: getDataSetCount
        Created: 03.11.2004, JM
        Description: Returns the number of individual DataSets (=time points)
        managed by this DataSource
        """
        return len(self.dataSets)

    def getDataSet(self, i):
        """
        Method: getDataSet
        Created: 03.11.2004, JM
        Description: Returns the DataSet at the specified index
        Parameters:   i       The index
        """
        return self.loadVti(self.dataSets[i])

    def getDimensions(self):
        """
        Method: getDimensions()
        Created: 14.12.2004, KP
        Description: Returns the (x,y,z) dimensions of the datasets this 
                     dataunit contains
        """
        if not self.dimensions:
            data=self.getDataSet(0)
            self.dimensions=data.GetDimensions()
        return self.dimensions
        
    def getSpacing(self):
        """
        Method: getSpacing()
        Created: 31.03.2005, KP
        Description: Returns the spacing of the datasets this 
                     dataunit contains
        """
        if not self.spacing:
            data=self.getDataSet(0)
            self.spacing=data.GetSpacing()
        return self.spacing
        
    def getVoxelSize(self):
        """
        Method: getVoxelSize()
        Created: 31.03.2005, KP
        Description: Returns the spacing of the datasets this 
                     dataunit contains
        """
        return self.parser.get("VoxelSize","VoxelSize")
    

    def loadVti(self, filename):
        """
        Method: loadVti
        Created: 03.11.2004, JM
        Description: Loads the specified DataSet from disk and returns
                     it as vtkImageData
        Parameters:   filename  The file where Dataset is loaded from
        """
        self.reader=vtk.vtkXMLImageDataReader()
        filepath=os.path.join(self.path,filename)
        if not self.reader.CanReadFile(filepath):
            Logging.error("Cannot read file",
            "Cannot read XML Image Data File %s"%filename)
        self.reader.SetFileName(filepath)
        self.reader.Update()
        return self.reader.GetOutput()

    def loadDuFile(self, filename):
        """
        Method: loadDuFile
        Created: 15.12.2004, JM, JV
        Description: Loads the specified .du-file, the checks the format
                     of the loaded dataunit and returns it

        Parameters:   filename  The .du-file to be loaded
        """
        self.filename = filename
        self.path=os.path.dirname(filename)
        print "Trying to open %s"%filename
        try:
            # A SafeConfigParser is used to parse the .du-file
            self.parser = SafeConfigParser()
            self.parser.read([filename])
            # First, the DataUnit format is checked
            DataUnitFormat = self.parser.get("Type", "Type")
        except:
            Logging.error("Failed to open file for reading",
            "VTIDataSource failed to open %s for reading."%(filename))
            return [None]
        return DataUnitFormat

    def loadFromFile(self, filename):
        """
        Method: loadFromFile
        Created: 09.11.2004, JM
        Description: Loads the specified .du-file and imports data from it.
                     Also returns a DataUnit of the type stored in the loaded
                     .du-file or None if something goes wrong. The dataunit is
                     returned in a list with one item for interoperability with
                     LSM data source (ie. bad .du-file or wrong filename)

        Parameters:   filename  The .du-file to be loaded
        """
        DataUnitFormat = self.loadDuFile(filename)

        if (not DataUnitFormat) or (not self.parser):
            return None

        # Then, the number of datasets/timepoints that belong to this dataset
        # series
        count = self.parser.get("ImageData", "numberOfFiles")
        print DataUnitFormat,count


        # Then read the .vti-filenames and store them in the dataSets-list:
        filedir=os.path.dirname(filename)
        for i in range(int(count)):
            currentFile = "file_" + str(i)
            filename=self.parser.get("ImageData",currentFile)
            reader=vtk.vtkXMLImageDataReader()
            filepath=os.path.join(filedir,filename)
            if not reader.CanReadFile(filepath):
                Logging.error("Cannot read file",
                "Cannot read source XML Image Data File %s"%filename)
                return

            self.dataSets.append(filename)
            Logging.info("dataset[%d]=%s"%(i,self.dataSets[i]))

        dataunitclass=DataUnit.DataUnit.DataUnit

        # If everything went well, we create a new DataUnit-instance of the
        # correct subclass, so that the DataUnit-instace can take over and
        # resume data processing. First, we return the DataUnit to the caller,
        # so it can set a reference to it:
        dataunit=dataunitclass()
        settings = DataUnit.DataUnitSettings()
        settings = settings.readFrom(self.parser)
        self.settings = settings
        dataunit.setSettings(settings)
        dataunit.setDataSource(self)
        return [dataunit]

    def getName(self):
        """
        Method: getName
        Created: 18.11.2004, KP
        Description: Returns the name of the dataset series which this datasource
                     operates on
        """
        return self.settings.get("Name")

    def getColor(self):
        """
        Method: getColor()
        Created: 27.03.2005, KP
        Description: Returns the color of the dataset series which this datasource
                     operates on
        """
        return eval(self.parser.get("Color","Color"))
