# -*- coding: iso-8859-1 -*-
"""
 Unit: CombinedDataUnit
 Project: Selli
 Created: 03.11.2004
 Creator: JM
 Description: Classes for managing combined 4D data.

 Modified:  04.11.2004 JM - added: ColocalizationDataUnit.SetColor(),
            ColocalizationDataUnit.doColocalization(),
            ColorCombinationDataUnit.doColorCombination(),
            ColorCombinationDataUnit.setOpacityTransfer(),
            ColorCombinationDataUnit.getOpacityTransfer()

            04.11.2004 JM - added:
            ColocalizationDataUnit.addSourceDataUnit(),
            ColorCombinationDataUnit.addSourceDataUnit()
            modified:
            CombinedDataUnit.__init__()

            08.11.2004 JM
            - removed:
            ColocalizationDataUnit.doColocalization(),
            ColorCombinationDataUnit.doColorCombination()
            - added:
            CombinedDataUnit.doPreview(),
            CombinedDataUnit.doCombine(),
            ColocalizationDataUnit.doPreview(),
            ColocalizationDataUnit.doCombine(),
            ColorCombinationDataUnit.doPreview(),
            ColorCombinationUnit.doCombine()

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

 Selli includes the following persons:
 JH - Juha Hyytiäinen, juhyytia@st.jyu.fi
 JM - Jaakko Mäntymaa, jahemant@cc.jyu.fi
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 JV - Jukka Varsaluoma,varsa@st.jyu.fi

 Copyright (c) 2004 Selli Project.
"""

__author__ = "Selli Project <http://sovellusprojektit.it.jyu.fi/selli/>"
__version__ = "$Revision: 1.74 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import DataUnit
from DataUnitSetting import *
from Color24bit import *
import Colocalization
import ColorMerging
import DataSource
import vtk

class CombinedDataUnit(DataUnit.DataUnit):
    """
    Class: CombinedDataUnit
    Created: 03.11.2004
    Creator: JM
    Description: Base class for combined 4d data.
    """

    def __init__(self, name=""):
        """
        Method: __init__
        Created: 03.11.2004
        Creator: JM
        Description: Constructor
        """
        DataUnit.DataUnit.__init__(self, name)
        # A dictionary to store SouceDataUnits (channels) together
        # with channel-specific settings. Keys are names of the DataUnits,
        # values are two-member lists with the actual DataUnit instance in 
        # index 0 and its setting in index 1.
        self.dataUnitsAndSettings = {}

    def setDataSource(self, dataSource):
        """
        Method: setDataSource
        Created: 17.11.2004
        Creator: JM
        Description: Sets a DataSource for this CombinedDataUnit
        Parameters: dataSource  A DataSource to manage actual
                                image data located on disk

        """
        # A validity check for dataSource
        if not isinstance(dataSource, DataSource.VtiDataSource):
            raise "A CombinedDataUnit can only be loaded from a VtiDataSource"

        # Call to base class, to run common setDataSource
        DataUnit.DataUnit.setDataSource(self,dataSource)

        # Then start loading SourceDataUnits, first check the number of them:
        sourceCount = int(self.dataSource.getSetting("CombinedDataUnit",
        "numberofsources"))

        # Next parse the information about SourceDataUnits and their settings:
        for i in range(sourceCount):
            sourceUnitString = self.dataSource.getSetting("CombinedDataUnit",
            "source" + str(i))
            sourceSettingString = self.dataSource.getSetting("CombinedDataUnit",
            "setting" + str(i))

            sourceUnitList=sourceUnitString.split("|")

            print sourceUnitList

            # A SourceDataUnit can be stored in either vti- or lsm-format, act
            # accordingly:
            if sourceUnitList[0]=="vti":
                if len(sourceUnitList)!=2:
                    raise "Wrong format for source%d: %s"%(i,sourceUnitString)

                datasource=DataSource.VtiDataSource()
                sourceUnit = datasource.loadFromDuFile(sourceUnitList[1])
                # Since loadFromDuFile returns a list, we need to take the first
                #  item from the list and use that
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
            self.addSourceDataUnit(sourceUnit, 
            self.newSetting(sourceSettingString))

    def addInputToModule(self,dataunit,image):
        """
        Method: addInputToModule(dataunit,image)
        Created: 1.12.2004
        Creator: JM,KP
        Description: A method to add a dataunit as an input to the module
                     This is a method of its own because adding input data to
                     the module requires the parameters associated with the
                     input data to be passed along as well, and this should
                     not be done in more than one place.
        Parameters:
                dataunit    The dataunit that is the source of the image data
                image       The imagedata to be added as input to the module
        """
        raise "addInputToModule() of base class CombinedDataUnit called"

    def initializeModule(self):
        """
        Method: initializeModule()
        Created: 1.12.2004
        Creator: JM,KP
        Description: Code to initialize the module when it has been reset
        """
        raise "initializeModule() of base class CombinedDataUnit called"

    def getDimensions(self):
        """
        Method: getDimensions()
        Created: 10.11.2004
        Creator: KP
        Description: Returns the (x,y,z) dimensions of the datasets this 
                     dataunit contains
        """
        sourceunits=self.getSourceDataUnits()
        source=sourceunits[0]
        image=source.getTimePoint(0)
        dimensions=image.GetDimensions()
        return dimensions

    def getDataUnitCount(self):
        """
        Method: getDataUnitCount
        Created: 03.11.2004
        Creator: JM
        Description: Returns the count of DataUnits
        """
        return len(self.dataUnitsAndSettings.keys())

    def getSourceDataUnits(self):
        """
        Method: getSourceDataUnits
        Created: 03.11.2004
        Creator: JM
        Description: Returns a list of references to the contained DataUnits
        """
        return [value[0] for value in self.dataUnitsAndSettings.values()]

    def getSetting(self,name):
        """
        Method: getSetting(name)
        Created: 10.11.2004
        Creator: KP
        Description: Returns the setting-object of the requested dataunit
        Parameters:
                name    The name of the dataunit, the settings-object of which
                        the caller is interested in
        """
        # settings are in index 1
        return self.dataUnitsAndSettings[name][1]

    #def doProcessing(self,duFile,callback=None,settings_only=0,**kws):
    def doProcessing(self,duFile,**kws):
        """
        Method: doProcessing(duFile, callback)
        Created: 08.11.2004
        Creator: JM
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
        self.dataSource=DataSource.VtiDataSource(duFile)

        imageList=[]
        self.n=1
        self.guicallback=callback
        if not settings_only:
            for timePoint in timepoints:
                print "Now processing timepoint %d"%timePoint
                # First we reset the module, so that we can start the operation
                # from clean slate
                self.module.reset()
                self.initializeModule()
                # We get the processed timepoint from each of the source data 
                # units
                for dataunit in self.getSourceDataUnits():
                    image=dataunit.getTimePoint(timePoint)
                    self.addInputToModule(dataunit,image)
                # Get the vtkImageData containing the results of the operation 
                # for this time point
                imageData=self.module.doOperation()
                if self.guicallback:
                    self.guicallback(timePoint,self.n,len(timepoints))
                self.n+=1
                # Write the image data to disk
                if not settings_only:
                    self.dataSource.addVtiObject(imageData)
        if settings_only:
            self.dataSource.addDataUnitSettings("DataUnit",
            {"SettingsOnly":"true"})
        print "Processing done."
        self.createDuFile()

    def createDuFile(self):
        """
        Method: createDuFile
        Created: 1.12.2004
        Creator: KP,JM
        Description: Writes a du file to disk
        """

        settingdict={"NumberOfSources":"%d"%self.getDataUnitCount()}
        sourceunits=self.getSourceDataUnits()
        # Write out the names of the datasets used for this operation
        for i in range(0,self.getDataUnitCount()):
            key="source%d"%i
            # Use the string representation of the dataunit to get the type 
            # and path of the dataunit
            value=str(sourceunits[i])
            settingdict[key]=value
            key="setting%d"%i
            # Fetch the dataunit and setting from the dictionary
            dataunit,setting=self.dataUnitsAndSettings[sourceunits[i].getName()]
            # Use the string representation of the data unit's settings
            value=str(setting)
            settingdict[key]=value
        self.dataSource.addDataUnitSettings("CombinedDataUnit",settingdict)


    def addSourceDataUnit(self, dataUnit, dataUnitSetting=None):
        """
        Method: addSourceDataUnit
        Created: 03.11.2004
        Creator: JM
        Description: Adds 4D data to the unit together with channel-specific
        settings.
        Parameters: dataUnit    The SourceDataUnit to be added
        """
        # If one or more SourceDataUnits have already been added, check that the
        # new SourceDataUnit has the same length as the previously added one(s):
        print dataUnit
        if (self.length != 0) and (self.length != dataUnit.length):
            raise "Given dataunit had wrong length (%d != %d)"%\
            (self.length,dataUnit.length)

        # The DataUnit to be added must have a different name than the
        # previously added, or the dictionary won't work:
        name = dataUnit.getName()
        if self.dataUnitsAndSettings.has_key(name):
            raise "Dataunit %s already exists"%name

        if (not dataUnitSetting):
            rgb = dataUnit.getColor()
            #rgbString = rgb...
            #settingString = rgbString
            #print "Settings for dataunit: ", settingString
            settingString=""
            # changed newsetting to get string and rgb, rgb is always needed
            # todo: all settings to string, including rgb?
            dataUnitSetting = self.newSetting(settingString,rgb)

        self.dataUnitsAndSettings[name] = [dataUnit, dataUnitSetting]

        # If we just added the first SourceDataUnit, this sets the correct length
        # for the entire CombinedDataUnit. If not, it doesn't change anything.
        self.length = dataUnit.length

    def doPreview(self, depth,renew,timePoint=0):
        """
        Method: doPreview
        Created: 08.11.2004
        Creator: JM
        Description: Makes a two-dimensional preview using
                     the class-specific combination function
                     NOT IMPLEMENTED HERE
        Parameters: depth       The preview depth
                    renew       Flag indicating, whether the preview should be 
                                regenerated or if a stored image can be reused
                    timePoint   The timepoint from which to generate the preview
                                Defaults to 0
        """
        raise "Abstract method doPreview() in CombinedDataUnit called"

    def newSetting(self, settingString="", rgb=(255,255,255)):
        """
        Method: newSetting
        Created: 17.11.2004
        Creator: JM
        Description: returns a new DataUnitSetting suitable for current
                     subclass
        Parameters:  settingString  If specified, the new setting is parsed
                                    from this string

                     NOT IMPLEMENTED HERE
        """
        raise "Abstract method newSetting() in CombinedDataUnit called"

    def loadCommonSettings(self, dataSource):
        """
        Method: loadCommonSettings
        Created: 15.12.2004
        Creator: JM, JV
        Description: Loads the settings common to whole CombinedDataUnit
        Parameters: dataSource  A DataSource that reads the actual data
        """
        raise "Abstract method loadCommonSettings() in CombinedDataUnit called"


    def loadSettings(self,filename):
        """
        Method: loadSettings
        Created: 15.12.2004
        Creator: JM, JV
        Description: Loads the settings from a previously saved .du-file,
                     if possible.
        Parameters:  filename  name and path of the .du-file
        """
        settingSource = DataSource.VtiDataSource()

        dataUnitType = settingSource.loadDuFile(filename)

        #TODO: a proper error message
#        if not (dataUnitType == "ColocalizationDataUnit"):
        if not isinstance(self,eval(dataUnitType)):
            raise "Unsuitable .du-file"

        self.loadCommonSettings(settingSource)

        # Then start loading SourceDataUnit-specific settings
        sourceCount = int(settingSource.getSetting("CombinedDataUnit",
        "numberofsources"))

        #TODO: a proper error message
        if sourceCount != self.getDataUnitCount():
            raise "The setting-.du has different number of sources"

        # Next parse the information about the settings:
        sourceSettingList=[]
        for i in range(sourceCount):
            sourceSettingList.append(settingSource.getSetting("CombinedDataUnit",
            "setting" + str(i)))

        data=self.dataUnitsAndSettings.values()
        for i in range(len(data)):
            dataunit,setting = data[i]
            setting.parseSettingsString(sourceSettingList[i])


