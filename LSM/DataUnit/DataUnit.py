# -*- coding: iso-8859-1 -*-
"""
 Unit: DataUnit.py
 Project: BioImageXD
 Created: 03.11.2004, JM
 Description: Classes for 4D DataUnits
           
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
import vtk

class DataUnit:
    """
    Class: DataUnit
    Created: 03.11.2004, JM
    Description: A class representing a timeseries of 3D data
    """

    def __init__(self, name=""):
        """
        Method: __init__
        Created: 03.11.2004, JM
        Description: Constructor
        Parameters: name    Name for the DataUnit, default to ""
        """
        self.name = name
        self.length = 0
        self.dataSource=None
        self.color= None
        self.ctf = None
        self.settings = None
    

    def getColorTransferFunction(self):
        """
        Method: getColorTransferFunction()
        Created: 26.04.2005, KP
        Description: Returns the ctf of this object
        """
        if not self.dataSource and not self.ctf:
            print "Using no CTF"
            return None
        if not self.ctf:
            self.ctf=self.dataSource.getColorTransferFunction()
#            print "Got color from datasource:",self.ctf
        return self.ctf
    
    
    def setSettings(self,settings):
        """
        Method: setSettings
        Created: 27.03.2005, KP
        Description: Sets the settings object of this dataunit
        """
        #print "Setting settings to ",repr(settings)
        self.settings = settings
        self.updateSettings()
    
    def updateSettings(self):
        """
        Method: updateSettings()
        Created: 28.03.2005, KP
        Description: Sets the settings of this object based on the datasource
        """
        if not self.settings:
            print "No settings, wont update"
            return
        if not (self.settings and self.settings.get("ColorTransferFunction")):
            ctf = self.getColorTransferFunction()
            # Watch out not to overwrite the palette
            #self.ctf = self.settings.get("ColorTransferFunction")
            #ctf = self.ctf
            #print "Setting ctf to ",ctf
            self.settings.set("ColorTransferFunction",ctf)
            if ctf and self.settings.get("Type")=="ColorMergingSettings":
                self.settings.set("MergingColorTransferFunction",ctf)
                

        if self.dataSource:
            self.settings.set("VoxelSize",self.dataSource.getVoxelSize())
            self.settings.set("Spacing",self.dataSource.getSpacing())
            self.settings.set("Dimensions",self.dataSource.getDimensions())
            self.settings.set("BitDepth",self.dataSource.getBitDepth())
            
    def getSettings(self):
        """
        Method: getSettings
        Created: 27.03.2005, KP
        Description: Returns the settings object of this dataunit
        """
        return self.settings
        
        
    def getName(self):
        """
        Method: getName
        Created: 03.11.2004, JM
        Description: Returns the name of this DataUnit
        """
        return self.name

    def setName(self,name):
        """
        Method: setName(name)
        Created: 8.12.2004, JM
        Description: Sets the name of this dataunit
        """
        self.name=name
        if self.settings:
            self.settings.set("Name",name)
 
    def getTimePoint(self,n):
        """
        Method: getTimePoint(n)
        Created: 17.11.2004, KP
        Description: Returns the requested time point
        Parameters:
                n       The timepoint we need to return
        """
        if not self.dataSource:
            raise "No datasource specified"
            Logging.error("No datasource specified",
            "No datasource specified for DataUnit, unable to get timepoint!")
            return None
        return self.dataSource.getDataSet(n)

    def getLength(self):
        """
        Method: getLength
        Created: 10.11.2004, JM
        Description: Returns the length of this DataUnit
        """
        return self.length

    def setDataSource(self, dataSource):
        """
        Method: setDataSource
        Created: 09.11.2004, JM
        Description: Sets a DataSource for this SourceDataUnit
        Parameters: dataSource  A DataSource to manage actual
                                image data located on disk
        """
        # Then load the settings specific to SourceDataUnit:
        self.dataSource = dataSource
        self.name = dataSource.getName()
        self.length=dataSource.getDataSetCount()
        
        self.getDimensions = dataSource.getDimensions
        self.getSpacing = dataSource.getSpacing
        self.getVoxelSize = dataSource.getVoxelSize
        self.getBitDepth = dataSource.getBitDepth
        print "Got datasource..."
        
        #self.updateSettings()
        
    def __str__(self):
        """
        Method: __str__
        Created: 27.03.2005, KP
        Description: Return the path to the file this dataunit represents
        """
        return str(self.dataSource)
