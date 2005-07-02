# -*- coding: iso-8859-1 -*-
"""
 Unit: CombinedDataUnit
 Project: BioImageXD
 Created: 03.11.2004, JM
 Description: Classes for managing combined 4D data.
                            
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
__version__ = "$Revision: 1.74 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import DataUnit
from DataUnitSetting import *
import DataSource
import vtk

class CombinedDataUnit(DataUnit.DataUnit):
    """
    Class: CombinedDataUnit
    Created: 03.11.2004, JM
    Description: Base class for combined 4d data.
    """

    def __init__(self, name=""):
        """
        Method: __init__
        Created: 03.11.2004, JM
        Description: Constructor
        """
        DataUnit.DataUnit.__init__(self, name)
        self.sourceunits=[]
        settingclass=self.getSettingClass()
        print "settingclass=",settingclass
        self.settings = settingclass()
        self.byName={}
        self.module = None
    
    def setModule(self,module):
        """
        Method: setModule(module)
        Created: 27.03.2005, KP
        Description: Sets the module that does the calculations for
                     this dataunit
        """
        self.module = module

    def getSettings(self):
        """
        Method: getSettings
        Created: 27.03.2005, KP
        Description: Returns the settings object of this dataunit
        """
        return self.settings

    def setSettings(self,settings):
        """
        Method: setSettings
        Created: 27.03.2005, KP
        Description: Sets the settings object of this dataunit
        """
        self.settings = settings
        self.settings.initialize(self,len(self.sourceunits),self.length)
        

    def getSourceUnit(self,name):
        """
        Method: getSourceUnit
        Created: 28.03.2005, KP
        Description: Returns a source unit of given name
        """
        return self.sourceunits[self.byName[name]]

        
    def setDataSource(self, dataSource):
        """
        Method: setDataSource
        Created: 17.11.2004, JM
        Description: Sets a DataSource for this CombinedDataUnit
        Parameters: dataSource  A DataSource to manage actual
                                image data located on disk
        """
        # A validity check for dataSource
        if not isinstance(dataSource, DataSource.VtiDataSource):
            raise "A CombinedDataUnit can only be loaded from a VtiDataSource"
        # Call to base class, to run common setDataSource
        DataUnit.DataUnit.setDataSource(self,dataSource)

    def loadSourceDataUnits(self):
        """
        Method: setSourceDataUnits()
        Created: 27.03.2005, KP
        Description: Load source data units from disk
        """
        self.settings = DataUnitSetting.DataUnitSettings()
        parser = self.dataSource.getParser()
        self.settings = self.settings.readFrom(parser)
        # Then start loading SourceDataUnits, first check the number of them:
        sourceCount = self.settings.get("SourceCount")
        # Next parse the information about SourceDataUnits and their settings:
        for i in range(sourceCount):
            sourceUnitString = self.setting["Source_%d"%i]
            
            sourceUnitList=sourceUnitString.split("|")

            print sourceUnitList

            # A SourceDataUnit can be stored in either vti- or lsm-format, act
            # accordingly:
            if sourceUnitList[0]=="vti":
                datasource=DataSource.VtiDataSource()
                sourceUnit = datasource.loadFromDuFile(sourceUnitList[1])
                sourceUnit=sourceUnit[0]
            elif sourceUnitList[0]=="lsm":
                datasource=DataSource.LsmDataSource(sourceUnitList[1],
                int(sourceUnitList[2]))
                sourceUnit=DataUnit.SourceDataUnit()
                sourceUnit.setDataSource(datasource)
            else:
                raise "Wrong format for source%d: %s"%(i,sourceList[0])

            if not sourceUnit:
                Logging.error("Failed to read dataunit",
                "Failed to read dataunit %s of type %s"%\
                (sourceUnitList[1],sourceUnitList[0]))

            # Finally, if everything worked out, add SourceDataUnits and
            # settings to the dictionary
            self.addSourceDataUnit(sourceUnit)
        
    def getDimensions(self):
        """
        Method: getDimensions()
        Created: 10.11.2004
        Creator: KP
        Description: Returns the (x,y,z) dimensions of the datasets this 
                     dataunit contains
        """
        return self.sourceunits[0].getDimensions()
        
    def getDataUnitCount(self):
        """
        Method: getDataUnitCount
        Created: 03.11.2004, JM
        Description: Returns the count of DataUnits
        """
        return len(self.sourceunits)

    def getSourceDataUnits(self):
        """
        Method: getSourceDataUnits
        Created: 03.11.2004, KP
        Description: Returns a list of references to the contained DataUnits
        """
        return self.sourceunits

    def doProcessing(self,duFile,**kws):
        """
        Method: doProcessing(duFile, callback)
        Created: 08.11.2004, JM
        Description: Executes the module's operation using the current settings
        Parameters:
                duFile      The name of the created .DU file
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
        settings_only=0
        callback=None
        timepoints=range(self.getLength())
        if "settings_only" in kws:
            settings_only=kws["settings_only"]
        if "callback" in kws:
            callback=kws["callback"]
        if "timepoints" in kws:
            timepoints=kws["timepoints"]
        # We create the vtidatasource with the name of the dataunit file
        # so it knows where to store the vtkImageData objects
        self.dataWriter=DataSource.DUDataWriter(duFile)

        imageList=[]
        self.n=1
        self.guicallback=callback
        if not settings_only:
            for timePoint in timepoints:
                print "Now processing timepoint %d"%timePoint
                # First we reset the module, so that we can start the operation
                # from clean slate
                self.module.reset()
                # We get the processed timepoint from each of the source data 
                # units
                #self.module.setSettings(self.settings)
                self.module.setTimepoint(timePoint)                
                for dataunit in self.sourceunits:
                    image=dataunit.getTimePoint(timePoint)
                    self.module.addInput(dataunit,image)
                # Get the vtkImageData containing the results of the operation 
                # for this time point
                # TODO: Change this to a wxpython event
                imageData=self.module.doOperation()
                if self.guicallback:
                    self.guicallback(timePoint,self.n,len(timepoints))
                self.n+=1
                # Write the image data to disk
                if not settings_only:
                    self.dataWriter.addImageData(imageData)
                    self.dataWriter.sync()

        if settings_only:
            self.settings.set("SettingsOnly","True")
        print "Processing done."
        self.createDataUnitFile(self.dataWriter)

    def createDataUnitFile(self,writer):
        """
        Method: createDataUnitFile
        Created: 1.12.2004, KP, JM
        Description: Writes a du file to disk
        """
        parser=writer.getParser()
        
        # Write out the names of the datasets used for this operation
        for i in range(0,self.getDataUnitCount()):
            key="Source"
            # Use the string representation of the dataunit to get the type 
            # and path of the dataunit
            value=str(self.sourceunits[i])
            self.settings.setCounted(key,i,value)
        
        print "Writing settings",self.settings
        print "writing ctf=",self.settings.get("ColorTransferFunction")
        self.settings.writeTo(parser)
        writer.write()

    def addSourceDataUnit(self, dataUnit):
        """
        Method: addSourceDataUnit
        Created: 03.11.2004, JM
        Description: Adds 4D data to the unit together with channel-specific
        settings.
        Parameters: dataUnit    The SourceDataUnit to be added
        """
        # If one or more SourceDataUnits have already been added, check that the
        # new SourceDataUnit has the same length as the previously added one(s):
        print dataUnit
        if (self.length != 0) and (self.length != dataUnit.length):
            # XXX: Raise
            print "Given dataunit had wrong length (%d != %d)"%\
            (self.length,dataUnit.length)

        # The DataUnit to be added must have a different name than the
        # previously added, or the dictionary won't work:
        name = dataUnit.getName()
        if name in self.byName:
            raise "Dataunit %s already exists"%name
        
        count = len(self.sourceunits)
        #count+=1
        self.byName[name]=count
        self.sourceunits.append(dataUnit)

        # Create a settings object of correct type for dataunit
        # using the count as the index
        setting=self.getSettingClass()(count)
        dataUnit.setSettings(setting)
        # Fetch correct settings for the dataunit from the datasource
        dataUnit.updateSettings()
        # If we just added the first SourceDataUnit, this sets the correct length
        # for the entire CombinedDataUnit. If not, it doesn't change anything.
        self.length = dataUnit.length
        
        for unit in self.sourceunits:
            unit.getSettings().initialize(unit,count+1,unit.getLength())        
        self.settings.initialize(self,count,self.sourceunits[0].getLength())
            
    def doPreview(self, depth,renew,timePoint=0):
        """
        Method: doPreview
        Created: 08.11.2004, JM
        Description: Makes a two-dimensional preview using
                     the class-specific combination function
                     NOT IMPLEMENTED HERE
        Parameters: depth       The preview depth
                    renew       Flag indicating, whether the preview should be 
                                regenerated or if a stored image can be reused
                    timePoint   The timepoint from which to generate the preview
                                Defaults to 0
        """
        # If the given timepoint > number of timepoints,
        # it is scaled to be in the range 0-getDataUnitCount()-1
        # with the modulo operator
        timePoint=timePoint%self.getLength()
        # If the renew flag is true, we need to regenerate the preview
        if renew:
            # We then tell the color merging module to reset itself and
            # initialize it again
            self.module.reset()
            #print "Setting settings=",self.settings
            # Go through all the source datasets for the color merging
            self.module.setSettings(self.settings)
            self.module.setTimepoint(timePoint)
            for dataunit in self.sourceunits:
                image=dataunit.getTimePoint(timePoint)
                self.module.addInput(dataunit,image)

        # module.getPreview() returns a vtkImageData object
        return self.module.getPreview(depth)

    def getBitDepth(self):
        """
        Method: getBitDepth()
        Created: 30.05.2005, KP
        Description: Return the bit depth of the combined dataunit
        """
        return 8


    def getColor(self):
        """
        Method: getColor()
        Created: 27.03.2005, KP
        Description: An "approximation" of getColor(), since this is
                     for simple use only.
        """
        if not len(self.sourceunits):
            return (0,0,0)
        return self.sourceunits[0].getColor()
        
    def getSettingClass(self):
        """
        Method: getSettingClass()
        Created: 02.04.2005, KP
        Description: Return the class that represents settings for this dataunit
        """
        return DataUnitSettings
        
