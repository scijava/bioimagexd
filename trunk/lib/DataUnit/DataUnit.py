# -*- coding: iso-8859-1 -*-
"""
 Unit: DataUnit.py
 Project: BioImageXD
 Created: 03.11.2004, JM
 Description: Classes for 4D DataUnits
           
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
__version__ = "$Revision: 1.93 $"
__date__ = "$Date: 2005/01/13 14:09:15 $"

import Logging
import vtk
import ImageOperations
import DataUnitSetting
class DataUnit:
    """
    Created: 03.11.2004, JM
    Description: A class representing a timeseries of 3D data
    """

    def __init__(self, name=""):
        """
        Created: 03.11.2004, JM
        Description: Constructor
        Parameters: name    Name for the DataUnit, default to ""
        """
        self.name = name
        self.length = 0
        self.dataSource=None
        self.color= None
        self.ctf = None
        self.randomCTF = None
        self.settings = DataUnitSetting.DataUnitSettings()
        self.mip=None
        self.mipTimepoint=-1
        
    def resetSettings(self):
        """
        Created: 23.10.2006, KP
        Description: Reset the settings of this dataunit. This is done for example after a task
                     has been closed to reset the dataunit back to it's original state
        """
        self.settings.resetSettings()
        self.settings = DataUnitSetting.DataUnitSettings()
        
    def setMask(self, mask):
        """
        Created: 20.06.2006, KP
        Description: Set the mask applied to this dataunit
        """   
        self.dataSource.setMask(mask)

    def isProcessed(self):
        """
        Created: 31.05.2005, KP
        Description: A method for querying whether this dataset is a processed one
        """    
        return 0


    def getDataSource(self):
        """
        Created: 12.04.2006, KP
        Description: Returns the data source of this dataset
        """        
        return self.dataSource
        
    def getMIP(self,tp,color,small=0):
        """
        Created: 01.09.2005, KP
        Description: Returns MIP of the given timepoint
        """        
        if self.mip and self.mipTimepoint==tp:
            #Logging.info("Using existing MIP")
            return self.mip
        else:
            #Logging.info("Generating MIP of tp=",tp)
            if not small:
                imagedata=self.getTimePoint(tp)
            else:
                imagedata = self.dataSource.getMIPdata(tp)
            if not color:
                color=self.getColorTransferFunction()
            self.mip=ImageOperations.getMIP(imagedata,color)
            return self.mip

    def resetColorTransferFunction(self):
        """
        Created: 12.10.2006, KP
        Description: A method that will reset the CTF from the datasource.
                     This is useful e.g. when scaling the intensities of the    
                     dataset
        """
        self.ctf = None
        self.dataSource.resetColorTransferFunction()
        ctf = self.getColorTransferFunction()
        self.settings.set("ColorTransferFunction",ctf)

    def getColorTransferFunction(self):
        """
        Created: 26.04.2005, KP
        Description: Returns the ctf of this object
        """
        
        if not self.dataSource and not self.ctf:
            Logging.backtrace()
            Logging.info("Using no ctf because datasource=",self.dataSource,kw="ctf")
            return None
        if not self.ctf:
            self.ctf=self.dataSource.getColorTransferFunction()
            #Logging.info("Ctf from datasource=",self.ctf,kw="ctf")
        return self.ctf
    
    
    def setSettings(self,settings):
        """
        Created: 27.03.2005, KP
        Description: Sets the settings object of this dataunit
        """
        self.settings = settings
        self.updateSettings()
    
    def updateSettings(self):
        """
        Created: 28.03.2005, KP
        Description: Sets the settings of this object based on the datasource
        """
        if not self.settings:
            Logging.info("No settings present, won't update",kw="dataunit")
            return
        if not (self.settings and self.settings.get("ColorTransferFunction")):
            ctf = self.getColorTransferFunction()
            # Watch out not to overwrite the palette
            #self.ctf = self.settings.get("ColorTransferFunction")
            #ctf = self.ctf
            self.settings.set("ColorTransferFunction",ctf)
            #if ctf and self.settings.get("Type")=="ColorMergingSettings":
            #    self.settings.set("MergingColorTransferFunction",ctf)
                

        if self.dataSource:
            self.settings.set("VoxelSize",self.dataSource.getVoxelSize())
            self.settings.set("Spacing",self.dataSource.getSpacing())
            self.settings.set("Dimensions",self.dataSource.getDimensions())
            self.settings.set("BitDepth",self.dataSource.getBitDepth())
            self.settings.set("EmissionWavelength",self.dataSource.getEmissionWavelength())
            self.settings.set("ExcitationWavelength",self.dataSource.getExcitationWavelength())
            self.settings.set("NumericalAperture",self.dataSource.getNumericalAperture())
            
    def getSettings(self):
        """
        Created: 27.03.2005, KP
        Description: Returns the settings object of this dataunit
        """
        return self.settings
        
    def getName(self):
        """
        Created: 03.11.2004, JM
        Description: Returns the name of this DataUnit
        """
        return self.name

    def setName(self,name):
        """
        Created: 8.12.2004, JM
        Description: Sets the name of this dataunit
        """
        self.name=name
        if self.settings:
            self.settings.set("Name",name)
 
    def getTimePoint(self,n):
        """
        Created: 17.11.2004, KP
        Description: Returns the requested time point
        Parameters:
                n       The timepoint we need to return
        """
        if not self.dataSource:
            print self,self.name
            raise "No datasource specified"
            Logging.error("No datasource specified",
            "No datasource specified for DataUnit, unable to get timepoint!")
            return None
        return self.dataSource.getDataSet(n)
        

    def getLength(self):
        """
        Created: 10.11.2004, JM
        Description: Returns the length of this DataUnit
        """
        return self.length

    def setDataSource(self, dataSource):
        """
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
        self.getResampledVoxelSize = dataSource.getResampledVoxelSize
        self.getBitDepth = dataSource.getBitDepth
        self.getScalarRange = dataSource.getScalarRange
        self.getEmissionWavelength = dataSource.getEmissionWavelength
        self.getExcitationWavelength = dataSource.getExcitationWavelength
        self.getNumericalAperture = dataSource.getNumericalAperture
        Logging.info("Dataunit ",repr(self),"got datasource",repr(self.dataSource),kw="datasource")
        
        #self.updateSettings()
    def doProcessing(self,duFile,**kws):
        """
        Created: 14.07.2005, KP
        Description: Executes the module's operation using the current settings
        Parameters:
                duFile      The name of the created .bxd file
        Keywords:
                callback    The callback used to give progress info to the GUI
                            The callback is a method that takes two arguments:
                            timepoint     The timepoint we're processing now
                            total         Total number of timepoints we're 
                                           processing
                settings_only   If this parameter is set, then only the 
                                settings will be written out and not the VTI 
                                files.
                timepoints      The timepoints that should be processed
        """
        callback=None
        timepoints=kws.get("timepoints",range(self.getLength()))
        
        settings_only=kws.get("settings_only",0)
        # We create the vtidatasource with the name of the dataunit file
        # so it knows where to store the vtkImageData objects
        import DataSource
        self.dataWriter=DataSource.BXDDataWriter(duFile)

        imageList=[]
        self.n=1
        if not settings_only:
            for timePoint in timepoints:
                # We get the processed timepoint from each of the source data 
                # units
                #self.module.setSettings(self.settings)
                imageData=dataunit.getTimePoint(timePoint)
                self.n+=1
                # Write the image data to disk
                if not settings_only:
                    self.dataWriter.addImageData(imageData)
                    self.dataWriter.sync()

        if settings_only:
            self.settings.set("SettingsOnly","True")
        self.createDataUnitFile(self.dataWriter)

    def createDataUnitFile(self,writer):
        """
        Created: 1.12.2004, KP, JM
        Description: Writes a du file to disk
        """
        parser=writer.getParser()
        
        # Write out the names of the datasets used for this operation
    
        key="Source"
        # Use the string representation of the dataunit to get the type 
        # and path of the dataunit
        value=str(self)
        self.settings.setCounted(key,0,value)
    
        self.settings.writeTo(parser)
        writer.write()

    def getFileName(self):
        """
        Created: 21.03.2006, KP
        Description: Return the path to the file this dataunit represents
        """
        return self.dataSource.getFileName()
        
