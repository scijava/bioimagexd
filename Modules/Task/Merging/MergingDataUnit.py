# -*- coding: iso-8859-1 -*-
"""
 Unit: MergingDataUnit
 Project: BioImageXD
 Created: 01.01.2004, KP
 Description: A dataunit class that represents a data unit processed through filters

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

from DataUnit import CombinedDataUnit
import MergingSettings

class MergingDataUnit(CombinedDataUnit):
    """
    Class: MergingDataUnit
    Created: 03.07.2005, KP
    Description: Class for an merged channels dataset
    """
    def __init__(self, name=""):
        """
        Method: __init__
        Created: 03.11.2004, JM
        Description: Constructor
        """
        CombinedDataUnit.__init__(self,name)
        self.handleOriginal=0
    

    def getBitDepth(self):
        return 32
        
    def getSettingsClass(self):
        """
        Method: getSettingsClass()
        Created: 02.04.2005, KP
        Description: Return the class that represents settings for this dataunit
        """
        return MergingSettings.MergingSettings
        
    def setOutputChannel(self,ch,flag):
        """
        Method: setOutputChannel(ch,flag)
        Created: 22.07.2005, KP
        Description: Mark a channel as being part of the output
        """
        # We duplicate a bit of functionality from combined data unit
        # with this, but because they need to function differently, it
        # is easier than to duplicate the doPreview() function
        self.sourceunits[ch].getSettings().set("PreviewChannel",flag)
        
