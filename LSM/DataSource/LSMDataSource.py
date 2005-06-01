# -*- coding: iso-8859-1 -*-
"""
 Unit: DataSource.py
 Project: Selli
 Created: 03.11.2004, JM
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
__version__ = "$Revision: 1.37 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"


from ConfigParser import *
from DataSource import *
import vtk
import os.path

import Logging
import DataUnit
import time

class LsmDataSource(DataSource):
    """
    Class: LsmDataSource
    Created: 18.11.2004
    Creator: KP
    Description: Manages 4D data stored in an lsm-file
    """
    def __init__(self,filename="",channelNum=-1):
        """
        Method: __init__
        Created: 18.11.2004
        Creator: KP
        Description: Constructor
        """
        DataSource.__init__(self)
        # Name and path of the lsm-file:
        self.filename = filename
        self.path=""
        # An lsm-file may contain multiple channels. However, LsmDataSource only
        # handles one channel. The following attribute indicates, which channel
        # within the lsm-file is hadled by this LsmDataSource instance.
        self.channelNum=channelNum

        # TODO: what is this?
        self.dataUnitSettings={}
        # TODO: what is this?
        self.count=0

        self.dimensions=None
        self.spacing=None
        self.origin=None
        self.voxelsize=None
        # vtkLSMReader is used to do the actual reading:
        self.reader=vtk.vtkLSMReader()

        # If a filename was specified, the file is loaded
        if self.filename:
            self.path=os.path.dirname(filename)
            print "LsmDataSource created with file %s and channelNum=%d"%\
            (self.filename,channelNum)
            try:
                f=open(filename)
                f.close()
            except IOError, ex:
                Logging.error("Failed to open LSM File",
                "Failed to open file %s for reading: %s"%(filename,str(ex)))
                return
            self.reader.SetFileName(self.filename)
            self.reader.Update()
            

    def getDataSetCount(self):
        """
        Method: getDataSetCount
        Created: 03.11.2004, JM
        Description: Returns the number of individual DataSets (=time points)
        managed by this DataSource
        """
        if not self.dimensions:
            self.getDimensions()
        return self.dimensions[3]

    def getDimensions(self):
        """
        Method: getDimensions()
        Created: 14.12.2004, KP
        Description: Returns the (x,y,z) dimensions of the datasets this 
                     dataunit contains
        """
        if not self.dimensions:
            self.dimensions=self.reader.GetDimensions()
        return self.dimensions[0:3]

    def getSpacing(self):
        if not self.spacing:
            a,b,c=self.reader.GetVoxelSizes()
            print "Voxel sizes = ",a,b,c
            self.spacing=[1,b/a,c/a]
        return self.spacing
        
    def getBitDepth(self):
        """
        Method: getBitDepth
        Created: 28.05.2005, KP
        Description: Return the bit depth of data
        """
        return 8
        
    def getVoxelSize(self):
        if not self.voxelsize:
            self.voxelsize=self.reader.GetVoxelSizes()
        return self.voxelsize
            
        
    def getDataSet(self, i):
        """
        Method: getDataSet
        Created: 18.11.2004
        Creator: KP
        Description: Returns the timepoint at the specified index
        Parameters:   i       The index
        """
        # No timepoint can be returned, if this LsmDataSource instance does not
        #  know what channel it is supposed to handle within the lsm-file.
        if self.channelNum==-1:
            Logging.error("No channel number specified",
            "LSM Data Source got a request for dataset from timepoint "
            "%d, but no channel number has been specified"%(i))
            return None
        self.reader.SetUpdateTimePoint(i)
        self.reader.SetUpdateChannel(self.channelNum)
        self.reader.Update()
        data=self.reader.GetOutput()

        return data

    def loadFromFile(self,filename):
        """
        Method: loadFromLsmFile(filename)
        Created: 18.11.2004
        Creator: KP
        Description: Loads all channels from a specified LSM file to DataUnit-
                     instances and returns them as a list.
        Parameters:   filename  The .lsm-file to be loaded
        """
        self.filename=filename
        self.path=os.path.dirname(filename)
        self.reader.SetFileName(filename)
        try:
            f=open(filename)
            f.close()
        except IOError, ex:
            Logging.error("Failed to open LSM File",
            "Failed to open file %s for reading: %s"%(filename,str(ex)))

        self.reader.Update()
        dataunits=[]
        channelNum=self.reader.GetNumberOfChannels()
        print "There are %d channels"%channelNum
        for i in range(channelNum):
            # We create a datasource with specific channel number that
            #  we can associate with the dataunit
            datasource=LsmDataSource(filename,i)
            dataunit=DataUnit.DataUnit.DataUnit()
            dataunit.setDataSource(datasource)
            dataunits.append(dataunit)
            
        return dataunits


    def writeToDuFile(self):
        """
        Method: writeToDuFile
        Created: 10.11.2004
        Creator: KP
        Description: Writes the given datasets and their information to a 
                     .du file

        TODO: check if this method could use self.parser!
        TODO: comments...
        """
        parser=ConfigParser()
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
        Method: getSetting
        Created: 18.11.2004
        Creator: KP
        Description: This adds a pair of setting keys and their values to an 
                     internal dictionary that are written to the .du file when 
                     it is written out.
        """
        if not self.dataUnitSettings.has_key(section):
            self.dataUnitSettings[section]=[]
        self.dataUnitSettings[section].append(settingDict)

            
    def getColor(self):
        """
        Method: getName()
        Created: 27.03.2005, KP
        Description: Returns the color of the dataset series which this datasource
                     operates on
        """
        raise "DON'T CALL GETCOLOR!!!"
        r=self.reader.GetChannelColorComponent(self.channelNum,0)
        g=self.reader.GetChannelColorComponent(self.channelNum,1)
        b=self.reader.GetChannelColorComponent(self.channelNum,2)
        return (r,g,b)
    def getColorTransferFunction(self):
        """
        Method: getColorTransferFunction()
        Created: 26.04.2005, KP
        Description: Returns the ctf of the dataset series which this datasource
                     operates on
        """
        if not self.ctf:
            print "Using ctf based on LSM Color"
            ctf = vtk.vtkColorTransferFunction()
            r=self.reader.GetChannelColorComponent(self.channelNum,0)
            g=self.reader.GetChannelColorComponent(self.channelNum,1)
            b=self.reader.GetChannelColorComponent(self.channelNum,2)
            r/=255.0
            g/=255.0
            b/=255.0
            ctf.AddRGBPoint(0,0,0,0)
            ctf.AddRGBPoint(255,r,g,b)
            self.ctf = ctf
        return self.ctf
        
    def getName(self):
        """
        Method: getName()
        Created: 18.11.2004, KP
        Description: Returns the name of the dataset series which this datasource
                     operates on
        """
        if self.channelNum<0:
            Logging.error("No channel number specified",
            "LSM Data Source got a request for the name of the channel, "
            "but no channel number has been specified")
            return ""
        return self.reader.GetChannelName(self.channelNum)

    def __str__(self):
        """
        Method: __str__
        Created: 18.11.2004
        Creator: KP
        Description: Returns the basic information of this instance as a string
                     The info should be accurate enough that this instance can
                     be reconstructed using only it.
        """
        return "lsm|%s|%d"%(self.filename,self.channelNum)

