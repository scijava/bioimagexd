# -*- coding: iso-8859-1 -*-
"""
 Unit: ColocalizationDataUnit
 Project: Selli
 Created: 02.02.2005
 Creator: KP
 Description: A class for managing combined 4D colocalization dataset series.

 Modified:  02.02.2004 KP - Migrated Colocalization Specific parts from
                            CombinedDataUnit

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
from CombinedDataUnit import *
from DataUnitSetting import *
from Color24bit import *
import Colocalization
import ColorMerging
import vtk


class ColocalizationDataUnit(CombinedDataUnit):
    """
    Class: ColocalizationDataUnit
    Created: 03.11.2004, JM
    Description: Combined DataUnit that forms a colocalization map from the
    assigned SourceDataUnits
    """

    def __init__(self,name=""):
        """
        Method: __init__(name)
        Created: 03.11.2004, KP
        Description: Initializes the data unit and creates a colocalization
                     module for use in generating preview and actual 
                     colocalization map
        """
        CombinedDataUnit.__init__(self,name)

        #Set the module used to do the actual work:
        self.module=Colocalization.Colocalization()

        #This could be something nicer than a string, but works this way.
        self.format="1-bit"

        self.color = Color24bit(255,255,0)

    def setDataSource(self, dataSource):
        """
        Method: setDataSource
        Created: 16.11.2004, KP
        Description: Sets a DataSource for this SourceDataUnit
        Parameters: dataSource  A DataSource to manage actual
                                image data located on disk
        """
        # Call to base class:
        CombinedDataUnit.setDataSource(self,dataSource)

        self.loadCommonSettings(self.dataSource)

    def loadCommonSettings(self, dataSource):
        """
        Method: loadCommonSettings
        Created: 15.12.2004, JM, JV
        Description: Loads the settings common to whole ColocalizationDataUnit
        Parameters: dataSource  A DataSource that reads the actual data
        """
        #Then load the settings specific to ColocalizationDataUnit
        color=dataSource.getSetting("ColocalizationDataUnit","color")
        print "color='%s'"%color
        red,green,blue=color.split(",")
        self.setColor(int(red),int(green),int(blue))

        format=dataSource.getSetting("ColocalizationDataUnit","format")
        self.setFormat(format)

    def setFormat(self, format):
        """
        Method: setFormat
        Created: 03.11.2004, JM
        Description: Sets the format for the colocalization map
        Parameters: format      The new format
        """
        self.format = format

    def getFormat(self):
        """
        Method: getFormat
        Created: 03.11.2004, JM
        Description: Returns the currently selected format
        """
        return self.format

    def setColor(self, red, green, blue):
        """
        Method: setColor
        Created: 04.11.2004, JM
        Description: sets the color of this DataUnit
        Parameters: red     The value of red component
                    green   The value of green component
                    blue    The value of blue component
        """
        self.color.setValues(red,green,blue)

    def getColor(self):
        """
        Method: getColor
        Created: 08.11.2004, KP
        Description: returns the color of this dataunit
        """
        return self.color.getColor()

    def doPreview(self,z,renew,timePoint=0):
        """
        Method: doPreview(z,renew)
        Created: 08.11.2004, KP
        Description: Forms a preview of a colocalization map from the selected 
                     depth using the current settings

       Parameters: depth       The preview depth
                   renew       Flag indicating, whether the preview should be
                               regenerated or if a stored image can be reused
                   timePoint   The timepoint from which to generate the preview.
                               Defaults to 0
        """

        # If the given timepoint > number of timepoints,
        # it is scaled to be in the range 0-getDataUnitCount()-1
        # with the modulo operator
        timePoint=timePoint%self.getLength()
        print "timePoint %d"%timePoint

        # If the renew flag is true, we need to regenerate the preview
        if renew:
            # We then tell the colocalization module to reset itself and 
            # initialize it again
            self.module.reset()
            self.initializeModule()
            # Go through all the source datasets for the colocalization
            for dataunit in self.getSourceDataUnits():
                # Get the vtkImageData object
                image=dataunit.getTimePoint(timePoint)
                self.addInputToModule(dataunit,image)

        # module.getPreview() returns a vtkImageData object
        return self.module.getPreview(z)


    def addInputToModule(self,dataunit,image):
        """
        Method: addInputToModule(dataunit,image)
        Created: 1.12.2004, JM, KP
        Description: A method to add a dataunit as an input to the module
                     This is a method of its own because adding input data to
                     the module requires the parameters associated with the
                     input data to be passed along as well, and this should
                     not be done in more than one place.
        Parameters:
                dataunit    The dataunit that is the source of the image data
                image       The imagedata to be added as input to the module
        """
        # get the threshold for this timepoint from the settings
        setting=self.dataUnitsAndSettings[dataunit.getName()][1]
        # We add the vtkImageData of the time point together with the threshold
        self.module.addInput(image,threshold=setting.getThreshold())

    def initializeModule(self):
        """
        Method: initializeModule()
        Created: 1.12.2004, JM, KP
        Description: Code to initialize the module when it has been reset
        """
        self.module.setBitDepth(self.format)
        self.module.setZoomFactor(self.zoomFactor)

    def createDuFile(self):
        """
        Method: createDuFile
        Created: 1.12.2004, KP, JM
        Description: Writes a du file to disk
        """
        CombinedDataUnit.createDuFile(self)

        colorStr="%d,%d,%d"%self.getColor()
        self.dataSource.addDataUnitSettings("DataUnit",
        {"format":"ColocalizationDataUnit","name":self.getName()})
        self.dataSource.addDataUnitSettings("ColocalizationDataUnit",
        {"color":colorStr})
        self.dataSource.addDataUnitSettings("ColocalizationDataUnit",
        {"format":self.getFormat()})
        self.dataSource.writeToDuFile()

    def getColocalizationInfo(self):
        """
        Method: getColocalizationInfo
        Created: 1.12.2004, KP
        Creator: KP
        Description: Returns the number of colocalizing voxels and the number
                     of possible colocalizing voxels
        """

        least=self.module.getLeastVoxelsOverTheThreshold()
        coloc=self.module.getColocalizationAmount()
        return coloc,least

    def newSetting(self, settingString="", rgb=(255,255,255)):
        """
        Method: newSetting
        Created: 17.11.2004, JM
        Description: returns a new ColocalizationDataUnitSetting
        Parameters:  settingString  If specified, the new setting is parsed
                                    from this string
        """
        if (settingString == ""):
            return ColocalizationDataUnitSetting()
        return ColocalizationDataUnitSetting(settingString)

