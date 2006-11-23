# -*- coding: iso-8859-1 -*-
"""
 Unit: DataSource.py
 Project: BioImageXD
 Created: 03.11.2004, JM
 Description: Classes for managing 4D data located on disk

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
__version__ = "$Revision: 1.37 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

from ConfigParser import *
from DataSource import *
import messenger
import DataUnit
import vtk
import os.path
import ImageOperations

import Logging
import DataUnit

class MyConfigParser(RawConfigParser):
    def optionxform(self, optionstr):
        return optionstr

def getExtensions(): return ["bxd"]
def getFileType(): return "BioImageXD datasets (*.bxd)"
def getClass(): return BXDDataSource


class BXDDataSource(DataSource):
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
        self.setPath(filename)
        # path to the .du-file and .vti-file(s)
        self.path=""
        self.reader=None
        self.shift=None
        # Number of datasets added to this datasource
        self.counter=0
        self.parser = None

        # TODO: what is this?
        self.dataUnitSettings={}
        self.dimensions=None
        self.spacing = None
        self.voxelsizes=None
        
    def getFileName(self):
        """
        Method: getFileName()
        Created: 21.07.2005
        Description: Return the file name
        """    
        return self.filename
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

    def getDataSet(self, i,raw=0):
        """
        Method: getDataSet
        Created: 03.11.2004, JM
        Description: Returns the DataSet at the specified index
        Parameters:   i       The index
        """
        data=self.loadVti(self.dataSets[i])
        data=self.getResampledData(data,i)
        
        
        if data.GetScalarType()!=3 and not raw and self.settings.getType()!="Process":
            data=self.getIntensityScaledData(data)

        data.ReleaseDataFlagOff()
        return data

    def readInfo(self,data):
        """
        Method: readInfo
        Created: 28.5.2005, KP
        Description: Read various bits of info from the dataset
        """
        self.dimensions=data.GetDimensions()
        self.spacing=data.GetSpacing()
        #self.bitdepth=8*data.GetNumberOfScalarComponents()

    def getDimensions(self):
        """
        Method: getDimensions()
        Created: 14.12.2004, KP
        Description: Returns the (x,y,z) dimensions of the datasets this 
                     dataunit contains
        """
        if self.resampleDims:
            return self.resampleDims        
        if not self.dimensions:
            #data=self.getDataSet(0)
            #self.readInfo(data)
            self.dimensions = eval(self.settings.get("Dimensions"))
            
            
        return self.dimensions
    def updateProgress(self,obj,evt):
        """
        Method: updateProgress
        Created: 13.07.2004, KP
        Description: Sends progress update event
        """        
        if not obj:
            progress=1.0
        else:
            progress=obj.GetProgress()
        notinvtk=0
        if progress==1.0:notinvtk=1
        messenger.send(None,"update_progress",progress,"Reading %s..."%self.shortname,notinvtk)
             
        
    def getSpacing(self):
        """
        Method: getSpacing()
        Created: 31.03.2005, KP
        Description: Returns the spacing of the datasets this 
                     dataunit contains
        """
        if not self.spacing:
            #data=self.getDataSet(0)
            #self.readInfo(data)
            self.spacing = eval(self.settings.get("Spacing"))
        return self.spacing
        
    def getVoxelSize(self):
        """
        Method: getVoxelSize()
        Created: 31.03.2005, KP
        Description: Returns the spacing of the datasets this 
                     dataunit contains
        """
        try:
            vsiz=self.parser.get("VoxelSize","VoxelSize")
        except:
            vsiz = self.parser.get("VoxelSize","voxelsize")
        if type(vsiz)==type(""):            
            return eval(vsiz)
        return vsiz
    
    def loadVti(self, filename):
        """
        Method: loadVti
        Created: 03.11.2004, JM
        Description: Loads the specified DataSet from disk and returns
                     it as vtkImageData
        Parameters:   filename  The file where Dataset is loaded from
        """
        if not self.reader or self.filename != filename:
            self.filename = filename
            self.reader=vtk.vtkXMLImageDataReader()
            self.reader.AddObserver("ProgressEvent",self.updateProgress)
            filepath=os.path.join(self.path,filename)
            if not self.reader.CanReadFile(filepath):
                Logging.error("Cannot read file",
                "Cannot read XML Image Data File %s"%filename)
            self.reader.SetFileName(filepath)
            self.reader.Update()
            self.updateProgress(None,None)
        return self.reader.GetOutput()

    def loadDuFile(self, filename):
        """
        Created: 15.12.2004, JM, JV
        Description: Loads the specified .du-file, the checks the format
                     of the loaded dataunit and returns it

        Parameters:   filename  The .du-file to be loaded
        """
        self.filename = filename
        self.path=os.path.dirname(filename)
        Logging.info("Trying to open %s"%filename,kw="datasource")
        try:
            # A SafeConfigParser is used to parse the .du-file
            self.parser = MyConfigParser()
            self.parser.read([filename])
            # First, the DataUnit format is checked
            try:
                dataUnitFormat = self.parser.get("Type", "Type")
            except:
                dataUnitFormat = self.parser.get("Type","type")
        except Exception, ex:
            Logging.error("Failed to open file for reading",
            "DUDataSource failed to open %s for reading. Reason: %s"%(filename,str(ex)))
            return [None]
        return dataUnitFormat

    def loadFromFile(self, filename):
        """
        Created: 09.11.2004, JM
        Description: Loads the specified .du-file and imports data from it.
                     Also returns a DataUnit of the type stored in the loaded
                     .du-file or None if something goes wrong. The dataunit is
                     returned in a list with one item for interoperability with
                     LSM data source (ie. bad .du-file or wrong filename)

        Parameters:   filename  The .du-file to be loaded
        """
        self.shortname=os.path.basename(filename)
        dataUnitFormat = self.loadDuFile(filename)
        Logging.info("format of unit=",dataUnitFormat,kw="datasource")

        if (not dataUnitFormat) or (not self.parser):
            Logging.info("No dataUnitFormat or parser: %s and %s"%(dataUnitFormat,self.parser),kw="datasource")
            return None

        # Then, the number of datasets/timepoints that belong to this dataset
        # series
        try:
            count = self.parser.get("ImageData", "numberOfFiles")
        except:
            count = self.parser.get("ImageData","numberoffiles")
            
        Logging.info("format=",dataUnitFormat,"count=",count,kw="datasource")


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

        dataunitclass=DataUnit.DataUnit

        # If everything went well, we create a new DataUnit-instance of the
        # correct subclass, so that the DataUnit-instace can take over and
        # resume data processing. First, we return the DataUnit to the caller,
        # so it can set a reference to it:
        dataunit=dataunitclass()
        #settingsclass = "DataUnit."+self.parser.get("Type","Type")+"()"
        
        settings = DataUnit.DataUnitSettings()
        #settings = eval(settingsclass)
        settings = settings.readFrom(self.parser)
        self.originalDimensions = eval(settings.get("Dimensions"))
        self.settings = settings
        dataunit.setDataSource(self)
        dataunit.setSettings(settings)
        
        return [dataunit]

    def getName(self):
        """
        Created: 18.11.2004, KPloadFrom
        Description: Returns the name of the dataset series which this datasource
                     operates on
        """
        return self.settings.get("Name")

    def getColorTransferFunction(self):
        """
        Created: 26.04.2005, KP
        Description: Returns the ctf of the dataset series which this datasource
                     operates on
        """
        Logging.info("Getting colortransferfunction from settings",kw="ctf")
        
        #self.settings.set("ColorTransferFunction",palette)
#            except:
#                raise "FOO"
#                pass
        
        
        if not self.ctf:
            ctf = self.settings.get("ColorTransferFunction")
            #Logging.info("settings.ctf=",ctf,kw="ctf")
            try:
                #ctf=self.parser.get("ColorTransferFunction","ColorTransferFunction")
                ctf=self.settings.get("ColorTransferFunction")                
                if not ctf:
                    ctf=self.settings.get("ColocalizationColorTransferFunction")
            except:
                return None
            if not ctf:
                Logging.info("Will return no CTF",kw="ctf")
                ctf = vtk.vtkColorTransferFunction()
                ctf.AddRGBPoint(0,0,0,0)
                ctf.AddRGBPoint(255,1,1,1)                
            else:
                #Logging.info("Using CTF read from dataset",ctf,kw="ctf")
                pass
            self.ctf = ctf
        return self.ctf
