# -*- coding: iso-8859-1 -*-
"""
 Unit: DataUnitSetting
 Project: Selli
 Created: 03.11.2004
 Creator: JM
 Description: Classes to store DataUnit-specific extra settings

 Modified:  04.11.2004 JM - added: ColorCombinationDataUnitSetting.SetColor(),
            ColorCombinationDataUnit.setIntensityTransfer(),
            ColorCombinationDataUnit.getIntensityTransfer()

            10.11.2004 JV - updated: ColorCombinationDataUnitSetting.__init__
                            added: ColorCombinationDataUnitSetting.GetColor()

            17.11.2004 JM - Now ColocalizationDataUnitSetting can be parsed
                            from a string.

            24.11.2004 JM - Added validity checks to set-methods,
                            ColorCombinationDataUnitSetting.
                            intensityTransferFunction
                            is now stored as IntensityTransferfunction instance

            26.11.2004 JM - more comments added
            13.12.2004 JV - Setting string parsing in color combination
            14.12.2004 JV - Fixed: intensitytransferfuction.getasstr -> 
                            str(intensity...)


 Selli includes the following persons:
 JH - Juha Hyytiäinen, juhyytia@st.jyu.fi
 JM - Jaakko Mäntymaa, jahemant@cc.jyu.fi
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 JV - Jukka Varsaluoma, varsa@st.jyu.fi

 Copyright (c) 2004 Selli Project.
"""

__author__ = "Selli Project <http://sovellusprojektit.it.jyu.fi/selli/>"
__version__ = "$Revision: 1.28 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import vtk
from Color24bit import *
import ImageOperations as imOp

class DataUnitSetting:
    """
    Class: DataUnitSetting
    Created: 03.11.2004
    Creator: JM
    Description: A Base class for DataUnit-specific settings
    """

    def __init__(self, parseString=""):
        """
        Method: __init__
        Created: 17.11.2004
        Creator: JM
        Description: Constructor
        Parameters:  parseString   If specified, the new setting is parsed
                                   from this string
                                   NOT IMPLEMENTED HERE
        """
        raise "Abstract method __init__() in DataUnitSetting called"

    def __str__(self):
        """
        Method: __str__
        Created: 17.11.2004
        Creator: JM
        Description: Returns this DataUnitSetting as a string
                     NOT IMPLEMENTED HERE
        """
        raise "Abstract method __str__() in DataUnitSetting called"

    def parseSettingsString(self,parseString):
        """
        Method: parseSettingsString(parseString)
        Created: 15.12.2004
        Creator: KP
        Description: Parses settings for this setting object from a string
        """
        raise "Abstract method parseSettingsString in DataUnitSetting called"

class ColocalizationDataUnitSetting(DataUnitSetting):
    """
    Class: ColocalizationDataUnitSetting
    Created: 03.11.2004
    Creator: JM
    Description:    Stores DataUnit-specific settings related to forming
                    colocalization maps
    """

    def __init__(self, parseString=""):
        """
        Method: __init__
        Created: 03.11.2004
        Creator: JM
        Description: Constructor
        Parameters:  parseString   If specified, the new setting is parsed
                                   from this string
        """
        self.parseSettingsString(parseString)

    def parseSettingsString(self,parseString):
        """
        Method: parseSettingsString(parseString)
        Created: 15.12.2004
        Creator: KP
        Description: Parses settings for this setting object from a string
        """
        if (parseString==""):
            self.setThreshold(128)
            return
        self.setThreshold(int(parseString))

        print "created a ColocalizationDataUnitSetting with "\
        "threshold %d"%self.getThreshold()

    def __str__(self):
        """
        Method: __str__
        Created: 17.11.2004
        Creator: JM
        Description: Returns this ColocalizationDataUnitSetting as a string
        """
        return str(self.getThreshold())


    def setThreshold(self, threshold):
        """
        Method: setThreshold
        Created: 03.11.2004
        Creator: JM
        Description: Sets the colocalization threshold for the assigned DataUnit
        Parameters: threshold    the new threshold
        """
        if not (1 <= threshold and threshold <= 255):
            raise "Invalid threshold given: %d"%threshold
        self.threshold = threshold

    def getThreshold(self):
        """
        Method: getThreshold
        Created: 03.11.2004
        Creator: JM
        Description: Returns the current colocalization threshold
        """

        return self.threshold


class ColorMergingDataUnitSetting(DataUnitSetting):
    """
    Class: ColorCombinationDataUnitSetting
    Created: 03.11.2004
    Creator: JM
    Description: Stores DataUnit-specific settings related to forming
                 combined RGB-DataUnits
    """

    def __init__(self, parseString="", rgb=(255,255,255)):
        """
        Method: __init__
        Created: 03.11.2004
        Creator: JM,JV
        Description: Constructor
        Parameters:  parseString   If specified, the new setting is parsed
                                   from this string
                     rgb           Color from datasource (TO CHANGE?)
        """
        self.rgb=rgb
        self.parseSettingsString(parseString)

    def parseSettingsString(self,parseString):
        """
        Method: parseSettingsString(parseString)
        Created: 15.12.2004
        Creator: KP
        Description: Parses settings for this setting object from a string
        """
        #Constructs the default intensity transfer list
        self.intensityTransferFunction=vtk.vtkIntensityTransferFunction()

        #TODO: read the color from datasource
        # does not know sourcedataunit, color must come from parseString?
        # workaround (for now): rgb in parameters
        self.color = Color24bit(self.rgb[0],self.rgb[1],self.rgb[2])

        if (parseString.strip()!=""):
            il=parseString.split("|")
            iLen=len(imOp.getAsParameterList(self.intensityTransferFunction))
            if (len(il)!=3+iLen):
              raise "Wrong setting lenght in ColorMergingDataUnitSetting"
            self.setColor(int(il[0]),int(il[1]),int(il[2]))
            print "Parsing from ",il[3:iLen+3]
            imOp.setFromParameterList(self.intensityTransferFunction,il[3:iLen+3])


    def __str__(self):
        """
        Method: __str__
        Created: 17.11.2004
        Creator: JM,JV
        Description: Returns this ColorCombinationDataUnitSetting as a string

        TODO: proper implementation, once we know how to handle intesityTransfer
        """
        colors=self.getColor()
        colorString=str(colors[0])+"|"+str(colors[1])+"|"+str(colors[2])
        intensityString=str(self.intensityTransferFunction)
        resultString=colorString+"|"+intensityString
        print "Settings as string:",resultString
        return resultString

    def setColor(self, red, green, blue):
        """
        Method: setColor
        Created: 04.11.2004
        Creator: JM
        Description: sets the color in the combination for the assigned DataUnit
        Parameters: red     The value of red component
                    green   The value of green component
                    blue    The value of blue component
        """
        self.color.setValues(red, green, blue)

    def getColor(self):
        """
        Method: getColor
        Created: 10.11.2004
        Creator: JV
        Description: Returns the color in a tupple (red, green, blue)
        Parameters:
        """
        return self.color.getColor()

    def setIntensityTransferFunction(self, intensityTransfer):
         """
         Method: setIntensityTransfer
         Created: 04.11.2004
         Creator: JM
         Description: Sets the List intensityTransfer
         Parameters: intensityTransfer  New List intensityTransfer
         """
         self.intensityTransfer = intensityTransfer

    def getIntensityTransferFunction(self):
        """
        Method: getIntensityTransferFunction
        Created: 04.11.2004
        Creator: JM
        Description: Returns the current intensityTransferFunction
        """

        return self.intensityTransferFunction

