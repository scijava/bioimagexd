# -*- coding: iso-8859-1 -*-
"""
 Unit: ColorMergingDataUnit
 Project: Selli
 Created: 02.02.2005
 Creator: KP
 Description: A class for managing combined 4D color merged dataset series.

 Modified:  02.02.2004 KP - Migrated Color Merging Specific parts from
                            CombinedDataUnit

 Selli includes the following persons:
 JH - Juha Hyytiäinen, juhyytia@st.jyu.fi
 JM - Jaakko Mäntymaa, jahemant@cc.jyu.fi
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 JV - Jukka Varsaluoma,varsa@st.jyu.fi

 Copyright (c) 2004 Selli Project.
 --------------------------------------------------------------
"""

__author__ = "Selli Project <http://sovellusprojektit.it.jyu.fi/selli/>"
__version__ = "$Revision: 1.74 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import DataUnit
from CombinedDataUnit import *
from DataUnitSetting import *
from Color24bit import *
import Colocalization
import ColorMerging
import vtk

class ColorMergingDataUnit(CombinedDataUnit):
    """
    --------------------------------------------------------------
    Class: ColorMergingDataUnit
    Created: 03.11.2004
    Creator: JM
    Description: Combined DataUnit that forms rgb-data from the
    assigned SourceDataUnits
    --------------------------------------------------------------
    """

    def __init__(self,name=""):
        """
        --------------------------------------------------------------
        Method: __init__(name)
        Created: 08.11.2004
        Creator: JV
        Description: Initializes the data unit and creates color merging
                     module for use in generating preview and actual
                     merged data.
                     (Made after ColocalizationDataUnit)
        -------------------------------------------------------------
        """
        CombinedDataUnit.__init__(self,name)
        self.module=ColorMerging.ColorMerging()
        self.opacityTransfer=vtk.vtkIntensityTransferFunction()

    def setDataSource(self, dataSource):
        """
        --------------------------------------------------------------
        Method: setDataSource
        Created: 23.11.2004
        Creator: JV
        Description: Sets a DataSource for this SourceDataUnit
        Parameters: dataSource  A DataSource to manage actual
                                image data located on disk
        -------------------------------------------------------------
        """
        CombinedDataUnit.setDataSource(self,dataSource)
        
    def loadCommonSettings(self, dataSource):
        """
        --------------------------------------------------------------
        Method: loadCommonSettings
        Created: 16.12.2004
        Creator: JM
        Description: Loads the settings common to whole ColorCombinationDataUnit
        Parameters: dataSource  A DataSource that reads the actual data
        -------------------------------------------------------------
        """
#         #Then load the settings specific to ColocalizationDataUnit
#         color=dataSource.getSetting("ColocalizationDataUnit","color")
#         print "color='%s'"%color
#         red,green,blue=color.split(",")
#         self.setColor(int(red),int(green),int(blue))
# 
#         format=dataSource.getSetting("ColocalizationDataUnit","format")
#         self.setFormat(format)


    def setOpacityTransfer(self, opacityTransfer):
        """
        --------------------------------------------------------------
        Method: setOpacityTransfer
        Created: 04.11.2004
        Creator: JM
        Description: Sets the Intensity transfer function used to produce the
                     alpha channel
        Parameters: opacityTransfer  The intensity transfer function
        -------------------------------------------------------------
        """
        self.opacityTransfer = opacityTransfer

    def getOpacityTransfer(self):
        """
        --------------------------------------------------------------
        Method: getOpacityTransfer
        Created: 04.11.2004
        Creator: JM
        Description: Returns the current intensity transfer function used to
                     produce the alpha channel
        -------------------------------------------------------------
        """
        return self.opacityTransfer

    def doPreview(self,z,renew,timePoint=0):
        """
        --------------------------------------------------------------
        Method: doPreview
        Created: 08.11.2004
        Creator: JM,JV
        Description: Makes a two-dimensional preview of the color
                     combination using current settings
        Parameters:  depth       The preview depth
	                 renew       Flag indicating, whether the preview should be
                                 regenerated or if a stored image can be reused
		             timePoint   The timepoint from which to generate the preview
                                 Defaults to 0

        -------------------------------------------------------------
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
            self.initializeModule()
            # Go through all the source datasets for the color merging
            for dataunit in self.getSourceDataUnits():
                # Get the vtkImageData object
                image=dataunit.getTimePoint(timePoint)
                self.addInputToModule(dataunit,image)

        # module.getPreview() returns a vtkImageData object
        return self.module.getPreview(z)


    def newSetting(self, settingString="", rgb=(255,255,255)):
        """
        --------------------------------------------------------------
        Method: newSetting
        Created: 17.11.2004
        Creator: JM
        Description: returns a new ColorCombinationDataUnitSetting
        Parameters:  settingString  If specified, the new setting is parsed
                                    from this string
        -------------------------------------------------------------
        """
        #if (settingString == ""):
        #    return ColorCombinationDataUnitSetting()
        return ColorMergingDataUnitSetting(settingString,rgb)

    def initializeModule(self):
        """
        --------------------------------------------------------------
        Method: initializeModule()
        Created: 1.12.2004
        Creator: JM,KP
        Description: Code to initialize the module when it has been reset
        """
        #self.module.setBitDepth(self.format)
        pass


    def addInputToModule(self,dataunit,image):
        """
        --------------------------------------------------------------
        Method: addInputToModule(dataunit,image)
        Created: 1.12.2004
        Creator: JM,KP,JV
        Description: A method to add a dataunit as an input to the module
                     This is a method of its own because adding input data to
                     the module requires the parameters associated with the
                     input data to be passed along as well, and this should
                     not be done in more than one place.
        Parameters:
                dataunit    The dataunit that is the source of the image data
                image       The imagedata to be added as input to the module
        -------------------------------------------------------------
        """
        # get the settings for this timepoint from the settings
        setting=self.dataUnitsAndSettings[dataunit.getName()][1]
        # add the vtkImageData of the time point together with the settings
        self.module.addInput(image,intensityTransferFunction=\
        setting.getIntensityTransferFunction(),rgb=setting.getColor(),
                            alphaTransferFunction=self.opacityTransfer)

    def createDuFile(self):
        """
        --------------------------------------------------------------
        Method: createDuFile
        Created: 1.12.2004
        Creator: KP,JM,JV
        Description: Writes a du file to disk
        -------------------------------------------------------------
        """
        CombinedDataUnit.createDuFile(self)

        #colorStr="%d,%d,%d"%self.getColor()
        self.dataSource.addDataUnitSettings("DataUnit",
        {"format":"ColorMergingDataUnit","name":self.getName()})
        
        self.dataSource.writeToDuFile()

    def loadCommonSettings(self, dataSource):
        """
        --------------------------------------------------------------
        Method: loadCommonSettings
        Created: 15.12.2004
        Creator: JM, JV
        Description: Loads the settings common to whole ColocalizationDataUnit
        Parameters: dataSource  A DataSource that reads the actual data
        -------------------------------------------------------------
        """
        pass

import DataSource
