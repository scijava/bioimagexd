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
 --------------------------------------------------------------
"""

__author__ = "Selli Project <http://sovellusprojektit.it.jyu.fi/selli/>"
__version__ = "$Revision: 1.37 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"


from ConfigParser import *
from DataSource import *
import vtk
import os.path

import Logging
import DataUnit


class VtiDataSource(DataSource):
    """
    --------------------------------------------------------------
    Class: DataSource
    Created: 03.11.2004
    Creator: JM
    Description: Manages 4D data stored in du- and vti-files
    --------------------------------------------------------------
    """

    def __init__(self,filename=""):
        """
        --------------------------------------------------------------
        Method: __init__
        Created: 03.11.2004
        Creator: JM
        Description: Constructor
        -------------------------------------------------------------
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

        # TODO: what is this?
        self.dataUnitSettings={}
        self.dimensions=None

    def getDataSetCount(self):
        """
        --------------------------------------------------------------
        Method: getDataSetCount
        Created: 03.11.2004
        Creator: JM
        Description: Returns the number of individual DataSets (=time points)
        managed by this DataSource
        -------------------------------------------------------------
        """
        return len(self.dataSets)

    def getDataSet(self, i):
        """
        --------------------------------------------------------------
        Method: getDataSet
        Created: 03.11.2004
        Creator: JM
        Description: Returns the DataSet at the specified index
        Parameters:   i       The index
        -------------------------------------------------------------
        """
        return self.loadVti(self.dataSets[i])

    def getDimensions(self):
        """
        --------------------------------------------------------------
        Method: getDimensions()
        Created: 14.12.2004
        Creator: KP
        Description: Returns the (x,y,z) dimensions of the datasets this 
                     dataunit contains
        -------------------------------------------------------------
        """
        if not self.dimensions:
            data=self.getDataSet(0)
            self.dimensions=data.GetDimensions()
        return self.dimensions

    def loadVti(self, filename):
        """
        --------------------------------------------------------------
        Method: loadVti
        Created: 03.11.2004
        Creator: JM
        Description: Loads the specified DataSet from disk and returns
                     it as vtkImageData
        Parameters:   filename  The file where Dataset is loaded from
        -------------------------------------------------------------
        """
        reader=vtk.vtkXMLImageDataReader()
        filepath=os.path.join(self.path,filename)
        if not reader.CanReadFile(filepath):
            Logging.error("Cannot read file",
            "Cannot read XML Image Data File %s"%filename)
        reader.SetFileName(filepath)
        reader.Update()
        return reader.GetOutput()

    def loadDuFile(self, filename):
        """
        --------------------------------------------------------------
        Method: loadDuFile
        Created: 15.12.2004
        Creator: JM, JV
        Description: Loads the specified .du-file, the checks the format
                     of the loaded dataunit and returns it

        Parameters:   filename  The .du-file to be loaded
        -------------------------------------------------------------
        """
        self.filename = filename
        self.path=os.path.dirname(filename)
        print "Trying to open %s"%filename
        try:
            # A SafeConfigParser is used to parse the .du-file
            self.parser = SafeConfigParser()
            self.parser.read([filename])
            # First, the DataUnit format is checked
            DataUnitFormat = self.parser.get("DataUnit", "format")
        except Exception,ex:
            Logging.error("Failed to open file for reading",
            "VTIDataSource failed to open %s for reading."%(filename),ex)
            return [None]
        return DataUnitFormat

    def loadFromDuFile(self, filename):
        """
        --------------------------------------------------------------
        Method: loadFromDuFile
        Created: 09.11.2004
        Creator: JM
        Description: Loads the specified .du-file and imports data from it.
                     Also returns a DataUnit of the type stored in the loaded
                     .du-file or None if something goes wrong. The dataunit is
                     returned in a list with one item for interoperability with
                     LSM data source (ie. bad .du-file or wrong filename)

        Parameters:   filename  The .du-file to be loaded
        -------------------------------------------------------------
        """
        DataUnitFormat = self.loadDuFile(filename)

        if (not DataUnitFormat) or (not self.parser):
            return None


        # Then, the number of datasets/timepoints that belong to this dataset
        # series
        count = self.parser.get("VTIFiles", "numberOfFiles")
        print DataUnitFormat,count


        # Then read the .vti-filenames and store them in the dataSets-list:
        filedir=os.path.dirname(filename)
        for i in range(int(count)):
            currentFile = "file" + str(i)
            filename=self.parser.get("VTIFiles",currentFile)
            reader=vtk.vtkXMLImageDataReader()
            filepath=os.path.join(filedir,filename)
            if not reader.CanReadFile(filepath):
                Logging.error("Cannot read file",
                "Cannot read source XML Image Data File %s"%filename)
                return

            self.dataSets.append(filename)
            Logging.info("dataset[%d]=%s"%(i,self.dataSets[i]))

        # Raise an exception, if the DataUnit format is not recognized:
        if not self.classByName.has_key(DataUnitFormat):
            Logging.error("No class for dataunit type",
            "No class for dataunit of type %s specified. Known classes:\n%s"%\
            (DataUnitFormat,"\n".join(self.classByName.keys())))
            return [None]
        dataunitclass=self.classByName[DataUnitFormat]

        # If everything went well, we create a new DataUnit-instance of the
        # correct subclass, so that the DataUnit-instace can take over and
        # resume data rocessing. First, we return the DataUnit to the caller,
        # so it can set a reference to it:
        dataunit=dataunitclass()
        dataunit.setDataSource(self)
        return [dataunit]

    def writeToDuFile(self):
        """
        --------------------------------------------------------------
        Method: writeToDuFile
        Created: 10.11.2004
        Creator: KP
        Description: Writes the given datasets and their information to a du file

        TODO: check if this method could use self.parser!
        TODO: comments...
        -------------------------------------------------------------
        """
        # Create a parser to write settings to disk:
        parser=ConfigParser()

        # Write the needed sections and general DataUnit information
        for sectionName in self.dataUnitSettings.keys():
            if not parser.has_section(sectionName):
                parser.add_section(sectionName)
            for settingsDict in self.dataUnitSettings[sectionName]:
                for key in settingsDict.keys():
                    parser.set(sectionName,key,settingsDict[key])
        parser.add_section("VTIFiles")
        n=len(self.dataSets)
        parser.set("VTIFiles","numberOfFiles","%d"%n)
        for i in range(n):
            parser.set("VTIFiles","file%d"%i,self.dataSets[i])
        try:
            fp=open(self.filename,"w")
        except IOError,ex:
            Logging.error("Failed to write settings",
            "VTIDataSource Failed to open .du file %s for writing settings"%\
            filename,ex)
            return
        parser.write(fp)
        fp.close()

    def addDataUnitSettings(self,section,settingDict):
        """
        --------------------------------------------------------------
        Method: addDataUnitSettings(section, settingsDict)
        Created: 1.12.2004
        Creator: KP
        Description: Adds settings to dataUnitSettings-structure.
        Parameters:   section      Section of the .du-file where to store
                                   information in settingsDict
                      settingDict  Settings to be saved in a dictionary
        -------------------------------------------------------------
        """
        # If section does not exist, create it
        if not self.dataUnitSettings.has_key(section):
            self.dataUnitSettings[section]=[]
        # Append settings
        self.dataUnitSettings[section].append(settingDict)

    def addVtiObject(self,imageData):
        """
        --------------------------------------------------------------
        Method: addVtiObject(imageData)
        Created: 1.12.2004
        Creator: KP
        Description: Add a vtkImageData object to be written to the disk.
        -------------------------------------------------------------
        """
        # We find out the path to the directory where the image data is written
        if not self.path:
            # This is determined from self.filename which is the name of the 
            # .du file this datasource has been loaded from
            self.path=os.path.dirname(self.filename)

        # Next we determine the name for the .vti file we are writing
        # We take the name of the .du file this datasource is associated with
        duFileName=os.path.basename(self.filename)
        # and strip the .du from the end
        i=duFileName.rfind(".")
        imageDataName=duFileName[:i]
        fileName="%s_%d.vti"%(imageDataName,self.counter)
        self.counter+=1
        # Add the file name to our internal list of datasets
        self.dataSets.append(fileName)
        filepath=os.path.join(self.path,fileName)
        # Write the image data to disk
        self.writeVti(imageData,filepath)


    def addVtiObjects(self,imageDataList):
        """
        --------------------------------------------------------------
        Method: addVtiObjects(imageDataList)
        Created: 10.11.2004
        Creator: KP
        Description: Adds a list of vtkImageData objects to be written to the
                      disk. Uses addVtiObject to do all the dirty work
        -------------------------------------------------------------
        """
        for i in range(0,len(imageDataList)):
            self.addVtiObject(imageDataList[i])

    def writeVti(self,imageData,filename):
        """
        --------------------------------------------------------------
        Method: writeVti
        Created: 09.11.2004
        Creator: JM
        Description: Writes the given vtkImageData-instance to disk
                     as .vti-file with the given filename

        Parameters:   imageData  vtkImageData-instance to be written
                      filename  filename to be used
        -------------------------------------------------------------
        """
        print "Writing image data to %s"%filename
        try:
            writer=vtk.vtkXMLImageDataWriter()
            writer.SetFileName(filename)
            writer.SetInput(imageData)
            ret=writer.Write()
            if ret==0:
                Logging.error("Failed to write image data",
                "Failed to write vtkImageData object to file %s"%filename)
                return
        except Exception, ex:
            Logging.error("Failed to write image data",
            "Failed to write vtkImageData object to file %s"%filename,ex)
            return
        print "done"



    def getSetting(self, section, setting):
        """
        --------------------------------------------------------------
        Method: getSetting
        Created: 09.11.2004
        Creator: JM
        Description: Returns the specified setting from the loaded
                     .du-file or "failure" if something goes wrong.
                     (ie. such setting does not exist)

        Parameters:   section  The section, where the setting should be
                      setting  The setting to be returned
        -------------------------------------------------------------
        """
        try:
            settingValue = self.parser.get(section, setting)
        except:
            settingValue = "failure"

        return settingValue


    def getName(self):
        """
        --------------------------------------------------------------
        Method: getName()
        Created: 18.11.2004
        Creator: KP
        Description: Returns the name of the dataset series which this datasource
                     operates on
        -------------------------------------------------------------
        """
        return self.getSetting("DataUnit","name")

    def __str__(self):
        """
        --------------------------------------------------------------
        Method: __str__
        Created: 18.11.2004
        Creator: KP
        Description: Returns the basic information of this instance as a string
                     The info should be accurate enough that this instance cna
                     be reconstructed using onlyit.
        -------------------------------------------------------------
        """
        return "vti|%s"%self.filename
