# -*- coding: iso-8859-1 -*-
"""
 Unit: CombinedDataUnit
 Project: BioImageXD
 Created: 03.11.2004, JM
 Description: Classes for managing combined 4D data.

 Modified:  04.11.2004 JM - added methods

            04.11.2004 JM - added and modified methods
            08.11.2004 JM - removed and added methods
            09.11.2004 KP - doPreview() uses the data source to read the source 
                            data files
            09.11.2004 JV - implemented ColorCombinationDataUnit.doPreview()
            10.11.2004 KP - getSettingsManager() modified into getSetting(name)
                            for cleaner interface
            10.11.2004 JM - numerous bug fixes made and compliance with class
                            diagrams checked
            10.11.2004 JV - updated ColorCombinationDataUnit.doPreview()
            15.11.2004 KP - Addedd a callback to give progress info back to the
                            GUI
            16.11.2004 JM - DataUnitManager is no more. DataUnitManager has 
                            deceised. This is an ex-class.
                            (Seriously, DataUnitManager was replaced by simple 
                            dictionaries and lists)
            17.11.2004 JM - tidied up the class hierarchy, moved common 
                            functionalities to the base class
            24.11.2004 JM - Added validity checks to set-methods
            24.11.2004 JV - updated colorcombination
            26.11.2004 JM - more comments added
            03.12.2004 JV - Color combination gets right colors from datasource
                            and creates the .vti-files and .du-file
            04.12.2004 JV - Intensity transfer function is stored in .du 
                            (colors not!)            
            14.12.2004 JM - Previously entered Colocalization Depth is now 
                            loaded properly
            03.02.2005 KP - Renamed doCombine to doProcessing for compatibility
                            between combined and processed dataunits

            27.03.2005 KP - Started merging / refactoring classes
                            
 Selli includes the following persons:
 JH - Juha Hyytiäinen, juhyytia@st.jyu.fi
 JM - Jaakko Mäntymaa, jahemant@cc.jyu.fi
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 JV - Jukka Varsaluoma,varsa@st.jyu.fi

 BioImageXD includes the following persons:

 DW - Dan White, dan@chalkie.org.uk
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 PK - Pasi Kankaanpää, ppkank@bytl.jyu.fi
 
 Copyright (c) 2004 Selli Project, 2005 BioImageXD Project
"""

__author__ = "Selli Project <http://sovellusprojektit.it.jyu.fi/selli/>"
__version__ = "$Revision: 1.74 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import DataUnit
from DataUnitSetting import *
import Colocalization
import ColorMerging
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
                self.module.setSettings(self.settings)
                for dataunit in self.sourceunits:
                    image=dataunit.getTimePoint(timePoint)
                    self.module.addInput(image)
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
        print "doPreview"
        # If the renew flag is true, we need to regenerate the preview
        if renew:
            # We then tell the color merging module to reset itself and
            # initialize it again
            self.module.reset()
            print "Setting settings=",self.settings
            # Go through all the source datasets for the color merging
            self.module.setSettings(self.settings)
            for dataunit in self.sourceunits:
                image=dataunit.getTimePoint(timePoint)
                self.module.addInput(image)

        # module.getPreview() returns a vtkImageData object
        return self.module.getPreview(depth)
        
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
        
class ColorMergingDataUnit(CombinedDataUnit):
    def getSettingClass(self):
        """
        Method: getSettingClass()
        Created: 02.04.2005, KP
        Description: Return the class that represents settings for this dataunit
        """
        return ColorMergingSettings

class ColocalizationDataUnit(CombinedDataUnit):
    def getSettingClass(self):
        """
        Method: getSettingClass()
        Created: 02.04.2005, KP
        Description: Return the class that represents settings for this dataunit
        """
        return ColocalizationSettings

        
    
        
