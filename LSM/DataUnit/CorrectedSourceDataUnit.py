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
from Color24bit import *

import vtk

import DataUnitProcessing
import Logging
import DataSource
from ProcessedSourceDataUnit import *


class CorrectedSourceDataUnit(ProcessedSourceDataUnit):
    """
    Class: CorrectedSourceDataUnit
    Created: 24.11.2004
    Creator: JM,JV
    Description: Class for a corrected single-channel 4D DataUnit
    """

    def __init__(self,name=""):
        """
        Method: __init__
        Created: 24.11.2004
        Creator: JM
        Description: Constructor

        TODO: explain the attributes in comments
        """
        ProcessedSourceDataUnit.__init__(self,name)

        self.intensityTransferFunctions = []
        self.doMedianFiltering = False
        self.neighborhood = [1,1,1]
        self.removeSolitary = False
        self.horizontalSolitaryThreshold = 0
        self.verticalSolitaryThreshold = 0
        self.processingSolitaryThreshold = 0
        self.module=DataUnitProcessing.DataUnitProcessing()
        self.interpolationTimePoints=[]

    def setOriginal(self, dataUnit):
        """
        Method: setOriginal
        Created: 14.12.2004
        Creator: JM,JV
        Description: Sets the original DataUnit for this ProcessedSourceDataUnit
        Parameters: dataUnit  The original unmodified DataUnit
        """

        ProcessedSourceDataUnit.setOriginal(self,dataUnit)

        # Create the IntensityTransferFunction instances for each time point
        for i in range(self.length):
            iTF=vtk.vtkIntensityTransferFunction()
            self.intensityTransferFunctions.append(iTF)

#    def doPreview(self, depth,renew,timePoint=0):
#        print "Returning orignal"
#        return self.Original.getTimePoint(timePoint)

    def setDataSource(self, dataSource):
        """
        Method: setDataSource
        Created: 09.11.2004
        Creator: JM,JV
        Description: Sets a DataSource for this ProcessedSourceDataUnit
        Parameters: dataSource  A DataSource to manage actual
                                image data located on disk
        """


        ProcessedSourceDataUnit.setDataSource(self, dataSource)
        # Then load the settings specific to ProcessedSourceDataUnit:
        self.loadCommonSettings(dataSource)

    def setInterpolationTimePoints(self,timepointlist):
        """
        Method: setInterpolationTimePoints()
        Created: 13.12.2004
        Creator: KP
        Description: Sets the list of timepoints that need to be interpolated 
                     between
        """
        self.interpolationTimePoints=timepointlist

    def getInterpolationTimePoints(self):
        """
        Method: getInterpolationTimePoints()
        Created: 13.12.2004
        Creator: KP
        Description: Returns the list of timepoints that need to be interpolated
                     between
        """
        return self.interpolationTimePoints


    def interpolateIntensities(self):
        """
        Method: interpolateIntensities()
        Created: 13.12.2004
        Creator: KP
        Description: Interpolates intensity transfer functions for timepoints 
                     between a given list of timepoints
        """
        if len(self.interpolationTimePoints)<2:
            Logging.error("Cannot interpolate from one timepoint",
            "You need to specify at least two timepoints for interpolation")
            return
        lst=self.interpolationTimePoints[:]
        while -1 in lst:
            lst.remove(-1)
        for i in range(1,len(lst)):
            fromtp=lst[i-1]
            totp=lst[i]
            n=max(fromtp,totp)
            if n>=self.length:
                Logging.error("No such timepoint",
                "Timepoint %d is out of range. "\
                "There are %d timepoints"%(n,self.length))
                continue
            print "Interpolating from %d to %d"%(fromtp,totp)
            self.interpolateIntensitiesBetween(fromtp,totp)



    def interpolateIntensitiesBetween(self,timepoint1,timepoint2):
        """
        Method: interpolateIntensitiesBetween(timepoint1,timepoint2)
        Created: 09.12.2004
        Creator: KP
        Description: Interpolates intensity transfer functions for timepoints 
                     between timepoint1 and timepoint2
        """
        if timepoint1>timepoint2:
            timepoint2,timepoint1=timepoint1,timepoint2
        n=timepoint2-timepoint1
        params1=self.intensityTransferFunctions[timepoint1].getAsParameterList()
        params2=self.intensityTransferFunctions[timepoint2].getAsParameterList()
        # There are n-1 timepoints between the specified timepoints
        params=Interpolation.interpolate(params1,params2,n-1)
        print "params1=",params1
        for i in params:
            print i
        print "params2=",params2
        print "Interpolated %d new paramlists"%len(params)
        for i in range(n-1):
            print "Setting new parameters for timepoint ",timepoint1+i+1
            iTF=self.intensityTransferFunctions[timepoint1+i+1]
            iTF.setFromParameterList(params[i])


    def setSourceDataUnit(self, dataUnit):
        """
        Method: setSourceDataUnit
        Created: 24.11.2004
        Creator: JM
        Description: Sets the 4D dataUnit to be processed.
        Parameters: dataUnit    The SourceDataUnit to be processed.
        """

        self.name = "Processed_%s"%dataUnit.getName()
        col=dataUnit.getColor()
        self.setColor(*col)

        self.setOriginal(dataUnit)
        
    def addSourceDataUnit(self,dataUnit):
        return self.setSourceDataUnit(dataUnit)
        
        

    def setDoMedianFiltering(self,value):
        """
        Method: setDoMedianFiltering
        Created: 24.11.2004
        Creator: JM
        Description: Sets wether median filtering is done or not
        Parameters: value    New boolean value
        """
        self.doMedianFiltering = value

    def getDoMedianFiltering(self):
        """
        Method: getDoMedianFiltering
        Created: 24.11.2004
        Creator: JM
        Description: Returns the boolean attribute indicating
                     wether median filtering is done or not
        """

        return self.doMedianFiltering

    def setNeighborhood(self,x,y,z):
        """
        Method: setRemoveSolitary
        Created: 10.12.2004
        Creator: JV
        Description: Sets the neighborhood for the median filter
        Parameters: x,y,z    Neighborhood, integers
        """
        if (int(x) < 1) or (int(y) < 1) or (int(z) < 1):
            raise "Neighborhood values must be greater than 0"
        self.neighborhood = (int(x),int(y),int(z))

    def getNeighborhood(self):
        """
        Method: setRemoveSolitary
        Created: 10.12.2004
        Creator: JV
        Description: Returns the neighborhood for the median filter as a list
        """
        return self.neighborhood


    def setRemoveSolitary(self,value):
        """
        Method: setRemoveSolitary
        Created: 24.11.2004
        Creator: JM
        Description:Sets wether the Solitary intensity points are removed or not
        Parameters: value    New boolean value
        """
        self.removeSolitary = value;

    def getRemoveSolitary(self):
        """
        Method: getRemoveSolitary
        Created: 24.11.2004
        Creator: JM
        Description: Returns the boolean attribute indicating
                     wether the Solitary intensity points are removed or not
        """
        return self.removeSolitary

    def setHorizontalSolitaryThreshold(self,value):
        """
        Method: setHorizontalSolitaryThreshold
        Created: 24.11.2004
        Creator: JM
        Description: Sets the horizontalSolitaryThreshold attribute
        Parameters: value    New integer value
        """
        self.checkSolitaryThreshold(value)
        self.horizontalSolitaryThreshold = int(value)

    def getHorizontalSolitaryThreshold(self):
        """
        Method: getHorizontalSolitaryThreshold
        Created: 24.11.2004
        Creator: JM
        Description: Returns current horizontalSolitaryThreshold integer
                     attribute value
        """
        return self.horizontalSolitaryThreshold

    def setVerticalSolitaryThreshold(self,value):
        """
        Method: setVerticalSolitaryThreshold
        Created: 24.11.2004
        Creator: JM
        Description: Sets the verticalSolitaryThreshold attribute
        Parameters: value    New integer value
        """
        self.checkSolitaryThreshold(value)
        self.verticalSolitaryThreshold = int(value)

    def getVerticalSolitaryThreshold(self):
        """
        Method: getVerticalSolitaryThreshold
        Created: 24.11.2004
        Creator: JM
        Description: Returns current verticalSolitaryThreshold integer
                     attribute value
        """
        return self.verticalSolitaryThreshold

    def setProcessingSolitaryThreshold(self,value):
        """
        Method: setProcessingSolitaryThreshold
        Created: 10.12.2004
        Creator: JV
        Description: Sets the processingSolitaryThreshold attribute
        Parameters: value    New integer value
        """
        self.checkSolitaryThreshold(value)
        self.processingSolitaryThreshold = int(value)

    def getProcessingSolitaryThreshold(self):
        """
        Method: getProcessingSolitaryThreshold
        Created: 10.12.2004
        Creator: JV
        Description: Returns current processingSolitaryThreshold integer
                     attribute value
        """
        return self.processingSolitaryThreshold

    def checkSolitaryThreshold(self, value):
        """
        Method: ckeckSolitaryThreshold
        Created: 14.12.2004
        Creator: JM
        Description: Checks the validity of the given SolitaryThreshold value
        """
        if (int(value) < 0) or (int(value) > 255):
            raise "SolitaryThresholds must be between 0 and 255. Value was",\
            int(value)


    def getIntensityTransferFunction(self, timePoint):
        """
        Method: getIntensityTransferFunction(timepoint)
        Created: 24.11.2004
        Creator: JM
        Description: Returns the IntensityTransferFunction instace for
                     specified timePoint (integer value)
        """
        if not (0 <= timePoint or timePoint < self.length):
            Logging.error("Timepoint not found","Intensity transfer function "
            "of time point %d requested, but timepoint %d not found."%\
            (timePoint,timePoint))
            return None
        return self.intensityTransferFunctions[timePoint]

    def copyIntensityTransferFunctionToAll(self,iTF):
        """
        Method: copyIntensityTransferFunctionToAll(transferfunction)
        Created: 13.1.2005
        Creator: KP
        Description: Sets the IntensityTransferFunction instace for
                     all timePoints
        """
        for tf in self.intensityTransferFunctions:
            tf.setFromParameterList(iTF.getAsParameterList())

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

        # TODO: fix this mess?

        if self.doMedianFiltering and self.removeSolitary:
            self.module.addInput(image,
            intensityTransferFunction=self.intensityTransferFunctions[timePoint],
            medianNeighborhood=self.neighborhood,
            solitaryThresholds=(self.horizontalSolitaryThreshold,
            self.verticalSolitaryThreshold,
            self.processingSolitaryThreshold))

        if self.doMedianFiltering and not(self.removeSolitary):
            self.module.addInput(image,
            intensityTransferFunction=self.intensityTransferFunctions[timePoint],
            medianNeighborhood=self.neighborhood)

        if not(self.doMedianFiltering) and self.removeSolitary:
            self.module.addInput(image,
            intensityTransferFunction=self.intensityTransferFunctions[timePoint],
            solitaryThresholds=(self.horizontalSolitaryThreshold,
            self.verticalSolitaryThreshold,
            self.processingSolitaryThreshold))

        if not(self.doMedianFiltering) and not(self.removeSolitary):
            self.module.addInput(image, 
            intensityTransferFunction=self.intensityTransferFunctions[timePoint])



    def createDuFile(self):
        """
        Method: createDuFile
        Created: 1.12.2004
        Creator: KP,JM,JV
        Description: Writes a du file to disk
        """

        ProcessedSourceDataUnit.createDuFile(self)

        colorStr="%d,%d,%d"%self.getColor()
        self.dataSource.addDataUnitSettings("DataUnit",
        {"format":"CorrectedSourceDataUnit","name":self.getName()})
        self.dataSource.addDataUnitSettings("SourceDataUnit",{"color":colorStr})

        # Median filtering
        meN = self.getNeighborhood()
        doM = self.getDoMedianFiltering()
        print "median:",doM,meN
        medianStr = str(doM)+"|"+str(meN[0])+"|"+str(meN[1])+"|"+str(meN[2])
        print "medianStr:",medianStr
        self.dataSource.addDataUnitSettings("CorrectedSourceDataUnit",
        {"median":medianStr})

        # Solitary filtering
        solitaryStr = str(self.removeSolitary)+"|"+\
        str(self.getProcessingSolitaryThreshold())+"|"+\
        str(self.getHorizontalSolitaryThreshold())+"|"+\
        str(self.getVerticalSolitaryThreshold())
        self.dataSource.addDataUnitSettings("CorrectedSourceDataUnit",
        {"solitary":solitaryStr})

        # Loop through all intensity transfer functions
        for i in range(self.getLength()):
            iStr="intensityTransfer"+str(i)
            iStrSetting=str(self.intensityTransferFunctions[i])#.getAsString()
            self.dataSource.addDataUnitSettings("CorrectedSourceDataUnit",
            {iStr:iStrSetting})

        # Loop through interpolation settings
        tps=self.getInterpolationTimePoints()
        for i in range(len(tps)):
            n=tps[i]
            #if n!=-1:
            iStr="interpolationSetting"+str(i)
            iStrSetting=str(n)
            self.dataSource.addDataUnitSettings("CorrectedSourceDataUnit",
            {iStr:iStrSetting})

        self.dataSource.writeToDuFile()

    def loadCommonSettings(self, dataSource):
        """
        Method: loadCommonSettings
        Created: 15.12.2004
        Creator: JM, JV
        Description: Loads the settings common to whole CorrectedSourceDataUnit
        Parameters: dataSource  A DataSource that reads the actual data
        """
        medianStr=dataSource.getSetting("CorrectedSourceDataUnit","median")
        median=medianStr.split("|")
        if len(median)!=4:
             raise "Median has wrong number of settings"
        self.setDoMedianFiltering(int(median[0]))
        self.setNeighborhood(int(median[1]),int(median[2]),int(median[3]))

        solitaryStr=dataSource.getSetting("CorrectedSourceDataUnit","solitary")
        solitary=solitaryStr.split("|")
        if len(solitary)!=4:
             raise "Solitary filtering has wrong number of settings"
        self.setRemoveSolitary(int(solitary[0]))
        self.setProcessingSolitaryThreshold(int(solitary[1]))
        self.setHorizontalSolitaryThreshold(int(solitary[2]))
        self.setVerticalSolitaryThreshold(int(solitary[3]))

        print "solitarythreshold"
        print self.getProcessingSolitaryThreshold()

        # Loop through all intensity transfer functions
        for i in range(self.getLength()):
            iStr=dataSource.getSetting("CorrectedSourceDataUnit",
            "intensityTransfer"+str(i))
            self.intensityTransferFunctions[i].setFromString(iStr)

        # Loop through interpolation settings
        # NOTE! Must be same as in SingleUnitProcessingWindow!
        # (todo: fix)
        numOfPoints=5
        tps=[]
        for i in range(numOfPoints):
            iStr=dataSource.getSetting("CorrectedSourceDataUnit",
            "interpolationSetting"+str(i))
            try:
                iTp=int(iStr)
                tps.append(iTp)
            except:
                pass
        self.setInterpolationTimePoints(tps)


