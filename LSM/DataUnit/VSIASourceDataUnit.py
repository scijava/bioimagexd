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
 --------------------------------------------------------------
"""

__author__ = "Selli Project <http://sovellusprojektit.it.jyu.fi/selli/>"
__version__ = "$Revision: 1.93 $"
__date__ = "$Date: 2005/01/13 14:09:15 $"

import Interpolation
from Color24bit import *


import DataUnitProcessing
import VSIA
import Logging
from ProcessedSourceDataUnit import *

class VSIASourceDataUnit(ProcessedSourceDataUnit):
    """
    --------------------------------------------------------------
    Class: VSIASourceDataUnit
    Created: 25.11.2004
    Creator: JV
    Description: Class for a single-channel 4D DataUnit
                 with VSIA information
    --------------------------------------------------------------
    """

    def __init__(self,name=""):
        """
        --------------------------------------------------------------
        Method: __init__
        Created: 25.11.2004
        Creator: JV
        Description: Constructor
        -------------------------------------------------------------
        """
        SourceDataUnit.__init__(self,name)
        self.lowerLimit=1
        self.upperLimit=255
        self.surfaceCount=1
        self.selectedSurface=0
        self.exactValues=0
        self.filterClass="vtkGaussianSplatter"
        self.Original = None
        self.module=VSIA.VSIA()
        self.classes={"Gaussian Splat":"vtkGaussianSplatter",
                      "Shepard Method":"vtkShepardMethod",
                      "Delaunay Triangulation":"vtkDelaunay3D",
                      "Surface Reconstruction":"vtkSurfaceReconstructionFilter"}

        self.filterSettings=[]

    def setSourceDataUnit(self, dataUnit):
        """
        --------------------------------------------------------------
        Method: setSourceDataUnit
        Created: 24.11.2004
        Creator: JM
        Description: Sets the 4D dataUnit to be processed.
        Parameters: dataUnit    The SourceDataUnit to be processed.
        -------------------------------------------------------------
        """

        self.name = "Smoothed_%s"%dataUnit.getName()
        col=dataUnit.getColor()
        self.setColor(*col)

        self.Original = dataUnit
        self.length = dataUnit.length

    def getDimensions(self):
        """
        --------------------------------------------------------------
        Method: getDimensions()
        Created: 24.11.2004
        Creator: JM
        Description: Returns the (x,y,z) dimensions of the datasets this 
                     dataunit contains
        -------------------------------------------------------------
        """
        image=self.Original.getTimePoint(0)
        dimensions=image.GetDimensions()
        return dimensions

    def setFilter(self,fclass,fsettings):
        """
        --------------------------------------------------------------
        Method: setFilter(filterclass)
        Created: 16.12.2004
        Creator: KP,JV
        Description: Sets the class used for processing the data
        -------------------------------------------------------------
        """
        if not self.classes.has_key(fclass):
            raise "No processing class %s found"%fclass
        self.filterClass=self.classes[fclass]
        self.filterSettings=fsettings

    def getFilterAndSettings(self):
        """
        --------------------------------------------------------------
        Method: getFilterAndSettings()
        Created: 04.01.2005
        Creator: JV
        Description: Returns the classes name (used in GUI) used for
                     processing the data and it´s settings
        -------------------------------------------------------------
        """
        if self.filterClass:
            # Let´s iterate through dictionary values to get the right key
            i = self.classes.iteritems()
            returnClass=""
            for j in range(len(self.classes)):
                className=i.next()
                if className[1]==self.filterClass:
                    returnClass=className[0]

            if returnClass=="":
                raise "No processing class %s found"%self.filterClass

            return returnClass,self.filterSettings

    def setLowerLimit(self,limit):
        """
        --------------------------------------------------------------
        Method: setLowerLimit(limit, exact=0)
        Created: 15.12.2004
        Creator: KP
        Description: Sets the lower limit for variable threshold
        -------------------------------------------------------------
        """
        self.lowerLimit=limit

    def setUpperLimit(self,limit):
        """
        --------------------------------------------------------------
        Method: setUpperLimit(limit)
        Created: 15.12.2004
        Creator: KP
        Description: Sets the lower limit for variable threshold
        -------------------------------------------------------------
        """
        self.upperLimit=limit

    def setSurfaceCount(self,count):
        """
        --------------------------------------------------------------
        Method: setSurfaceCount(count)
        Created: 15.12.2004
        Creator: KP
        Description: Sets the parameter controlling how many surfaces are
                      generated between the lower and upper limit.
        -------------------------------------------------------------
        """
        self.surfaceCount=count

    def setExactValues(self,exact):
        """
        --------------------------------------------------------------
        Method: setExactValues(exact)
        Created: 15.12.2004
        Creator: KP
        Description: Sets the flag indicating whether the values selected
                     should be ranges or exact values
        -------------------------------------------------------------
        """
        self.exactValues=exact

    def setSelectedSurface(self,surface):
        """
        --------------------------------------------------------------
        Method: setSelectedSurface(surface)
        Created: 15.12.2004
        Creator: KP
        Description: Sets the surface to be generated (in case variable 
                     threshold is set)
        -------------------------------------------------------------
        """
        self.selectedSurface=surface

    def getSelectedSurface(self):
        """
        --------------------------------------------------------------
        Method: getSelectedSurface()
        Created: 15.12.2004
        Creator: KP
        Description: Returns the surface to be generated (in case variable 
                     threshold is set)
        -------------------------------------------------------------
        """
        return self.selectedSurface

    def getLowerLimit(self):
        """
        --------------------------------------------------------------
        Method: getLowerLimit()
        Created: 15.12.2004
        Creator: KP
        Description: Returns the lower limit for variable threshold
        -------------------------------------------------------------
        """
        return self.lowerLimit

    def getUpperLimit(self):
        """
        --------------------------------------------------------------
        Method: getUpperLimit()
        Created: 15.12.2004
        Creator: KP
        Description: Returns the lower limit for variable threshold
        -------------------------------------------------------------
        """
        return self.upperLimit

    def getSurfaceCount(self):
        """
        --------------------------------------------------------------
        Method: setSurfaceCount()
        Created: 15.12.2004
        Creator: KP
        Description: Returns the parameter controlling how many surfaces are
                     generated between the lower and upper limit.
        -------------------------------------------------------------
        """
        return self.surfaceCount

    def getExactValues(self):
        """
        --------------------------------------------------------------
        Method: getExactValues()
        Created: 15.12.2004
        Creator: KP
        Description: Returns the flag indicating whether the values selected
                     should be ranges or exact values
        -------------------------------------------------------------
        """
        return self.exactValues

    def addInputToModule(self,image,timePoint):
        """
        --------------------------------------------------------------
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
        -------------------------------------------------------------
        """

        # note: info is added in initializemodule.

        print "Adding input"
#         self.module.addInput(image,
#                              filterClass=self.filterClass,
#                              filterSettings=self.filterSettings,
#                              lowerLimit=self.lowerLimit,
#                              upperLimit=self.upperLimit,
#                              surfaceCount=self.surfaceCount,
#                              exactValues=self.exactValues)
        self.module.addInput(image)

    def initializeModule(self):
        """
        --------------------------------------------------------------
        Method: initializeModule()
        Created: 15.12.2004
        Creator: KP
        Description: Code to initialize the module when it has been reset
        """
        # If only the lower limit is specified, then we only select points
        # from the lower limit upwards
        self.module.setSurfaceGeneration(self.filterClass,self.filterSettings,
        self.lowerLimit,self.upperLimit,self.surfaceCount,self.exactValues)
        # If user requested variable surfaces,
        if self.upperLimit and self.surfaceCount>1:
            self.module.setSelectedSurface(self.selectedSurface)

    def doPreview(self, depth,renew,timePoint=0,**kws):
        """
        --------------------------------------------------------------
        Method: doPreview
        Created: 24.11.2004
        Creator: KP
        Description: Makes a two-dimensional preview

        Parameters: depth       The preview depth
	                renew       Flag indicating, whether the preview should be 
                                regenerated or if a stored image can be reused
		            timePoint   The timepoint from which to generate the preview
                                Defaults to 0
		Keywords:
		            rendering   If this keyword is set, then the preview will be
                                for rendering.This differs from normal preview 
                                in that the dataset will be passed through the 
                                selected processing module.

        -------------------------------------------------------------
        """
        self.module.setRenderingMode(0)
        print kws
        if kws.has_key("rendering"):
            print "Rendering mode on!"
            self.module.setRenderingMode(1)
        return ProcessedSourceDataUnit.doPreview(self,depth,renew,timePoint)

    def createDuFile(self):
        """
        --------------------------------------------------------------
        Method: createDuFile
        Created: 4.1.2005
        Creator: KP,JM,JV
        Description: Writes a du file to disk
        -------------------------------------------------------------
        """

        ProcessedSourceDataUnit.createDuFile(self)

        colorStr="%d,%d,%d"%self.getColor()
        self.dataSource.addDataUnitSettings("DataUnit",{"format":
        "VSIASourceDataUnit","name":self.getName()})
        self.dataSource.addDataUnitSettings("SourceDataUnit",{"color":colorStr})

        # surface settings
        print "self.lowerLimit=",self.lowerLimit
        print "self.upperLimit=",self.upperLimit
        print "self.surfaceCount=",self.surfaceCount

        lowerLim=self.getLowerLimit()
        upperLim=self.getUpperLimit()
        surfCoun=self.getSurfaceCount()
        exactVal=self.getExactValues()
        seleSurf=self.getSelectedSurface()

        settingStr=str(lowerLim)+"|"+str(upperLim)+"|"+str(surfCoun)+"|"+\
        str(exactVal)+"|"+str(seleSurf)
        self.dataSource.addDataUnitSettings("VSIASourceDataUnit",
        {"settings":settingStr})

        # filter and it´s settings
        # (note: should every filter´s settings be saved?)

        filterStr=str(self.filterClass)
        self.dataSource.addDataUnitSettings("VSIASourceDataUnit",
        {"filter":filterStr})

        fsettingStr="None"
        if self.filterClass=="vtkGaussianSplatter":
            fsettingStr=str(self.filterSettings[0])
        self.dataSource.addDataUnitSettings("VSIASourceDataUnit",
        {"filterSettings":fsettingStr})


        self.dataSource.writeToDuFile()

    def loadCommonSettings(self, dataSource):
        """
        --------------------------------------------------------------
        Method: loadCommonSettings
        Created: 4.1.2005
        Creator: JM, JV
        Description: Loads the settings common to whole VSIASourceDataUnit
        Parameters: dataSource  A DataSource that reads the actual data
        -------------------------------------------------------------
        """

        # surface settings

        settingStr=dataSource.getSetting("VSIASourceDataUnit","settings")
        settings=settingStr.split("|")
        if len(settings)!=5:
             raise "VSIA has wrong number of surface settings!"

        self.setLowerLimit(int(settings[0]))
        self.setUpperLimit(int(settings[1]))
        self.setSurfaceCount(int(settings[2]))
        self.setExactValues(int(settings[3]))
        self.setSelectedSurface(int(settings[4]))

        # filter and it´s settings

        filterStr=dataSource.getSetting("VSIASourceDataUnit","filter")
        if not filterStr in self.classes.values():
            raise "Filter %s not supported!"%filterStr
        self.filterClass=filterStr

        fsettingStr=dataSource.getSetting("VSIASourceDataUnit","filterSettings")
        self.filterSettings=[]
        if self.filterClass=="vtkGaussianSplatter":
            self.filterSettings.append(float(fsettingStr))

import DataSource

