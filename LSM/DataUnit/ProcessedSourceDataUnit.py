# -*- coding: iso-8859-1 -*-
"""
 Unit: DataUnit.py
 Project: Selli
 Created: 03.11.2004
 Creator: JM
 Description: Classes for 4D DataUnits

 Modified: 09.11.2004 JM
    - modified: SourceDataUnit.__init__()
    - added: SourceDataUnit.setDataSource()
           09.11.2004 KP - getTimePoint() uses DataSource for reading timepoints
                           from disk

           10.11.2004 JM - numerous bug fixes made and compliance with class 
                           diagrams checked

           24.11.2004 JM - Added validity checks to set-methods,
                           class ProcessedSourceDataUnit added

           25.11.2004 JV - Added VSIA

           26.11.2004 JM - more comments added
           09.12.2004 KP - Added method for intepolating intensity transfer 
                           functions
           10.12.2004 JV - set/getNeighborhood, 
                           set/getProcessingSolitaryThreshold,
                           passes settings to DataUnitProcessing
           11.12.2004 JV - Added: doProcessing, does not work
           13.12.2004 JV - Processing and saving works
           14.12.2004 JM - More validity checks added
           14.12.2004 JV,JM - Loading of settings in ProcessedSourceDataUnit
           17.12.2004 JV - Handles the settings to module
           04.01.2005 JV - VSIASourceDataUnit saves and loads settings

 Selli includes the following persons:
 JH - Juha Hyytiäinen, juhyytia@st.jyu.fi
 JM - Jaakko Mäntymaa, jahemant@cc.jyu.fi
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 JV - Jukka Varsaluoma, varsa@st.jyu.fi

 Copyright (c) 2004 Selli Project.
"""

__author__ = "Selli Project <http://sovellusprojektit.it.jyu.fi/selli/>"
__version__ = "$Revision: 1.93 $"
__date__ = "$Date: 2005/01/13 14:09:15 $"

import Interpolation
from IntensityTransferFunction import *
from Color24bit import *


import DataUnitProcessing
import VSIA
import Logging
from DataUnit import *

class ProcessedSourceDataUnit(SourceDataUnit):
    """
    Class: ProcessedSourceDataUnit
    Created: 4.12.2004
    Creator: JM,JV
    Description: Class for a processed single-channel 4D DataUnit
    """

    def __init__(self,name=""):
        """
        Method: __init__
        Created: 14.12.2004
        Creator: JM
        Description: Constructor

        TODO: explain the attributes in comments
        """
        SourceDataUnit.__init__(self,name)

        self.Original = None
        self.module = None

    def setOriginal(self, dataUnit):
        """
        Method: setOriginal
        Created: 14.12.2004
        Creator: JM,JV
        Description: Sets the original DataUnit for this ProcessedSourceDataUnit
        Parameters: dataUnit  The original unmodified DataUnit
        """
        if not isinstance(dataUnit, DataUnit):
            raise "Original must be a DataUnit"
        self.Original=dataUnit
        self.length = self.Original.getLength()

    def getOriginal(self):
        """
        Method: getOriginal
        Created: 14.12.2004
        Creator: JV
        Description: Gets the original DataUnit for this ProcessedSourceDataUnit
        """
        return self.Original

    def setDataSource(self, dataSource):
        """
        Method: setDataSource
        Created: 09.11.2004
        Creator: JM,JV
        Description: Sets a DataSource for this ProcessedSourceDataUnit
        Parameters: dataSource  A DataSource to manage actual
                                image data located on disk
        """
        # A validity check for dataSource
        if not isinstance(dataSource, DataSource.VtiDataSource):
            raise "A ProcessedSourceDataUnit can only be loaded from a "\
            "VtiDataSource"

        # Call the base class to read the basic information from the file
        SourceDataUnit.setDataSource(self,dataSource)

        sourceUnitString =self.dataSource.getSetting("ProcessedSourceDataUnit",\
        "source")
        sourceUnitList=sourceUnitString.split("|")
        print sourceUnitList

        # A SourceDataUnit can be stored in either vti- or lsm-format, act
        # accordingly:
        if sourceUnitList[0]=="vti":
            if len(sourceUnitList)!=2:
                raise "Wrong format for source: %s"%(sourceUnitString)

            datasource=DataSource.VtiDataSource()
            sourceUnit = datasource.loadFromDuFile(sourceUnitList[1])
            # Since loadFromDuFile returns a list, we need to take the first
            # item from the list and use that
            sourceUnit=sourceUnit[0]

        elif sourceUnitList[0]=="lsm":
            datasource=DataSource.LsmDataSource(sourceUnitList[1],\
            int(sourceUnitList[2]))
            sourceUnit=SourceDataUnit()
            sourceUnit.setDataSource(datasource)
        else:
            raise "Wrong format for source%d: %s"%(i,sourceList[0])

        if not sourceUnit:
            Logging.error("Failed to read dataunit",
            "Failed to read dataunit %s of type %s"%(sourceUnitList[1],
            sourceUnitList[0]))

        # Finally, if everything worked out, let´s set the original dataunit
        self.setOriginal(sourceUnit)


    def setSourceDataUnit(self, dataUnit):
        """
        Method: setSourceDataUnit
        Created: 24.11.2004
        Creator: JM
        Description: Sets the 4D dataUnit to be processed.
        Parameters: dataUnit    The SourceDataUnit to be processed.
        """
        raise "Abstract method setSourceDataUnit() in "\
        "ProcessedSourceDataUnit called"

    def getDimensions(self):
        """
        Method: getDimensions()
        Created: 24.11.2004
        Creator: JM
        Description: Returns the (x,y,z) dimensions of the datasets this 
                     dataunit contains
        """
        image=self.Original.getTimePoint(0)
        dimensions=image.GetDimensions()
        return dimensions

    def addInputToModule(self,image,timePoint):
        """
        Method: addInputToModule(image,timePoint)
        Created: 13.12.2004
        Creator: JM,KP,JV
        Description: A method to add a dataunit as an input to the module
                     This is a method of its own because adding input data to
                     the module requires the parameters associated with the
                     input data to be passed along as well, and this should
                     not be done in more than one place.
        Parameters:
                image       The imagedata to be added as input to the module
                timePoint   The timepoint to be processed
        """
        raise "Abstract method addInputToModule() called from base class"


    def initializeModule(self):
        """
        Method: initializeModule()
        Created: 15.12.2004
        Creator: KP
        Description: Code to initialize the module when it has been reset
        """
        # Will not raise anything because empty initialization method is ok
        pass


    def doPreview(self, depth,renew,timePoint=0):
        """
        Method: doPreview
        Created: 24.11.2004
        Creator: KP,JV
        Description: Makes a two-dimensional preview

        Parameters: depth       The preview depth
                    renew       Flag indicating, whether the preview should be
                                regenerated or if a stored image can be reused
                    timePoint   The timepoint from which to generate the preview
                                Defaults to 0
        """
        timePoint=timePoint%self.getLength()

        # If the renew flag is true, we need to regenerate the preview
        if renew:
            # We then tell the single dataset processing module to reset itself
            # and initialize it again
            self.module.reset()
            self.initializeModule()
            image=self.Original.getTimePoint(timePoint)
            self.addInputToModule(image,timePoint)

        # module.getPreview() returns a vtkImageData object
        return self.module.getPreview(depth)

    def doProcessing(self,duFile,**kws):
        """
        Method: doProcessing(duFile, callback)
        Created: 11.12.2004
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
                #NOTE THIS
                self.initializeModule()

                # We get the processed timepoint from the source data unit

                image=self.Original.getTimePoint(timePoint)
                self.addInputToModule(image,timePoint)

                # Get the vtkImageData containing the results of the operation 
                # for this time point
                imageData=self.module.doOperation()
                if self.guicallback:
                    self.guicallback(timePoint,self.n,len(timepoints))
                self.n+=1
                if not settings_only:
                    # Write the image data to disk
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
        Creator: KP,JM,JV
        Description: Writes a du file to disk
        """
        sourceunit=self.getOriginal()

        # Write out the name of the dataset used for this operation
        # Use the string representation of the dataunit to get the type and 
        # path of the dataunit
        value=str(sourceunit)
        settingdict={"source":value}

        self.dataSource.addDataUnitSettings("ProcessedSourceDataUnit",\
        settingdict)

    def loadSettings(self,filename):
        """
        Method: loadSettings
        Created: 16.12.2004
        Creator: JM
        Description: Loads the settings from a previously saved .du-file,
                     if possible.
        Parameters:  filename  name and path of the .du-file
        """
        settingSource = DataSource.VtiDataSource()

        dataUnitType = settingSource.loadDuFile(filename)

        #TODO: a proper error message
        if not isinstance(self,eval(dataUnitType)):
            raise "Unsuitable .du-file"

        self.loadCommonSettings(settingSource)

    def loadCommonSettings(self, dataSource):
        """
        Method: loadCommonSettings
        Created: 15.12.2004
        Creator: JM, JV
        Description: Loads the settings common to whole ProcessedSourceDataUnit
        Parameters: dataSource  A DataSource that reads the actual data
        """
        raise "Abstract method loadCommonSettings() in "\
        "ProcessedSourceDataUnit called"
