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

#from enthought.tvtk import messenger
import messenger
from ConfigParser import *
import DataSource
import vtk
import os.path

import Logging
import DataUnit
import time

def getExtensions(): return ["lsm"]
def getFileType(): return "Zeiss LSM 510 datasets (*.lsm)"
def getClass(): return LsmDataSource


class LsmDataSource(DataSource.DataSource):
    """
    Created: 18.11.2004, KP
    Description: Manages 4D data stored in an lsm-file
    """
    def __init__(self,filename="",channelNum=-1):
        """
        Method: __init__
        Created: 18.11.2004, KP
        Description: Constructor
        """
        DataSource.DataSource.__init__(self)
        # Name and path of the lsm-file:
        self.filename = filename
        self.timepoint=-1
        self.shortname=os.path.basename(filename)
        self.path=""
        # An lsm-file may contain multiple channels. However, LsmDataSource only
        # handles one channel. The following attribute indicates, which channel
        # within the lsm-file is hadled by this LsmDataSource instance.
        self.channelNum=channelNum
        self.setPath(filename)
        self.dataUnitSettings={}
        # TODO: what is this?
        self.count=0

        self.dimensions=None
        self.spacing=None
        self.origin=None
        self.voxelsize=None
        # vtkLSMReader is used to do the actual reading:
        self.reader=vtk.vtkLSMReader()
        #self.reader.DebugOn()
        self.reader.AddObserver("ProgressEvent",self.updateProgress)
        # If a filename was specified, the file is loaded
        if self.filename:
            self.path=os.path.dirname(filename)
            Logging.info("LsmDataSource created with file %s and channelNum=%d"%\
            (self.filename,channelNum),kw="datasource")
            try:
                f=open(filename)
                f.close()
            except IOError, ex:
                Logging.error("Failed to open LSM File",
                "Failed to open file %s for reading: %s"%(filename,str(ex)))
                return
            self.reader.SetFileName(self.filename)
            self.reader.Update()
            self.originalDimensions = self.reader.GetDimensions()[0:3]
            if self.reader.IsCompressed():
                raise Logging.GUIError("Cannot handle compressed dataset","The dataset you've selected (%s) is compressed. The LSM reader cannot currently read compressed data."%filename)
            self.updateProgress(None,None)
            
    def updateProgress(self,obj,evt):
        """
        Created: 13.07.2004, KP
        Description: Sends progress update event
        """        
        if not obj:
            progress=1.0
        else:
            progress=obj.GetProgress()
        if self.channelNum>=0:
            msg="Reading channel %d of %s"%(self.channelNum+1,self.shortname)
            if self.timepoint>=0:
                 msg+="(timepoint %d / %d)"%(self.timepoint+1,self.dimensions[3])
        else:
            msg="Reading %s..."%self.shortname
        notinvtk=0
        
        if progress==1.0:notinvtk=1
        messenger.send(None,"update_progress",progress,msg,notinvtk)
             

    def getDataSetCount(self):
        """
        Created: 03.11.2004, JM
        Description: Returns the number of individual DataSets (=time points)
        managed by this DataSource
        """
        if not self.dimensions:
            self.getDimensions()
        return self.dimensions[3]

    def getBitDepth(self):
        """
        Created: 07.08.2006, KP
        Description: Return the bit depth of data
        """
        if not self.bitdepth:
            d = self.reader.GetDataType()
            if d==1:
                self.bitdepth = 8
            if d==2:
                self.bitdepth = 16
        return self.bitdepth
        
    def getScalarRange(self):
        """
        Created: 28.05.2005, KP
        Description: Return the bit depth of data
        """        
        if not self.scalarRange:            
            data=self.getDataSet(0,raw=1)
            self.scalarRange=data.GetScalarRange()        
        return self.scalarRange

    def getDimensions(self):
        """
        Created: 14.12.2004, KP
        Description: Returns the (x,y,z) dimensions of the datasets this 
                     dataunit contains
        """
        if self.resampleDims:
            return self.resampleDims
        if not self.dimensions:
            self.dimensions=self.reader.GetDimensions()
            
        return self.dimensions[0:3]

    def getSpacing(self):
        
        if not self.spacing:
            a,b,c=self.reader.GetVoxelSizes()
            Logging.info("Voxel sizes = ",a,b,c,kw="datasource")
            self.spacing=[1,b/a,c/a]
        return self.spacing
        
        
    def getVoxelSize(self):
        if not self.voxelsize:
            self.voxelsize=self.reader.GetVoxelSizes()
        return self.voxelsize
            
        
    def getDataSet(self, i,raw=0):
        """
        Created: 18.11.2004, KP
        Description: Returns the timepoint at the specified index
        Parameters:   i       The timepoint to retrieve
                      raw     A flag indicating that the data is not to be processed in any way
        """
        # No timepoint can be returned, if this LsmDataSource instance does not
        #  know what channel it is supposed to handle within the lsm-file.
        if self.channelNum==-1:
            Logging.error("No channel number specified",
            "LSM Data Source got a request for dataset from timepoint "
            "%d, but no channel number has been specified"%(i))
            return None
    
        #Logging.backtrace()
        self.timepoint=i
        data=self.reader.GetTimePointOutput(i, self.channelNum)
        if not self.scalarRange:
            self.scalarRange = data.GetScalarRange()
        self.reader.Update()

        self.originalScalarRange=data.GetScalarRange()
        if raw:
            return data
        data=self.getResampledData(data,i)            
        if data.GetScalarType()!=3 and not raw:
            data=self.getIntensityScaledData(data)
        
        
        data.ReleaseDataFlagOff()
        return data
        
    def getFileName(self):
        """
        Created: 21.07.2005
        Description: Return the file name
        """    
        return self.filename
        
    def loadFromFile(self,filename):
        """
        Created: 18.11.2004, KP
        Description: Loads all channels from a specified LSM file to DataUnit-
                     instances and returns them as a list.
        Parameters:   filename  The .lsm-file to be loaded
        """
        self.filename=filename
        self.shortname=os.path.basename(filename)
        self.path=os.path.dirname(filename)
        self.reader.SetFileName(filename)
        
        try:
            f=open(filename)
            f.close()
        except IOError, ex:
            Logging.error("Failed to open LSM File",
            "Failed to open file %s for reading: %s"%(filename,str(ex)))

        self.reader.Update()
        if self.reader.IsCompressed():
            raise Logging.GUIError("Cannot handle compressed dataset","The dataset you've selected (%s) is compressed. The LSM reader cannot currently read compressed data."%filename)        
        dataunits=[]
        channelNum=self.reader.GetNumberOfChannels()
        self.timepointAmnt=channelNum
        Logging.info("There are %d channels"%channelNum,kw="datasource")
        for i in range(channelNum):
            # We create a datasource with specific channel number that
            #  we can associate with the dataunit
            datasource=LsmDataSource(filename,i)
            datasource.setPath(filename)
            dataunit=DataUnit.DataUnit()
            dataunit.setDataSource(datasource)
            dataunits.append(dataunit)
            
        return dataunits


    def writeToDuFile(self):
        """
        Created: 10.11.2004, KP
        Description: Writes the given datasets and their information to a BXD file
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
        Created: 18.11.2004, KP
        Description: This adds a pair of setting keys and their values to an 
                     internal dictionary that are written to the .du file when 
                     it is written out.
        """
        if not self.dataUnitSettings.has_key(section):
            self.dataUnitSettings[section]=[]
        self.dataUnitSettings[section].append(settingDict)

    def getColorTransferFunction(self):
        """
        Created: 26.04.2005, KP
        Description: Returns the ctf of the dataset series which this datasource
                     operates on
        """
        if not self.ctf:
            Logging.info("Using ctf based on LSM Color",kw="datasource")
            ctf = vtk.vtkColorTransferFunction()
            r=self.reader.GetChannelColorComponent(self.channelNum,0)
            g=self.reader.GetChannelColorComponent(self.channelNum,1)
            b=self.reader.GetChannelColorComponent(self.channelNum,2)
            print "Got color components=",r,g,b
            r/=255.0
            g/=255.0
            b/=255.0
            maxval=255
            if self.getBitDepth()==16:
                maxval=4096
            ctf.AddRGBPoint(0,0,0,0)
            ctf.AddRGBPoint(maxval,r,g,b)
            self.ctf = ctf
        return self.ctf
        
    def getName(self):
        """
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
        Created: 18.11.2004, KP
        Description: Returns the basic information of this instance as a string
        """
        return "LSM DataSource (%s, channel %d)"%(self.filename, self.channelNum)

