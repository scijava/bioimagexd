# -*- coding: iso-8859-1 -*-
"""
 Unit: DataSource.py
 Project: BioImageXD
 Created: 03.11.2004, JM
 Description: Classes for managing 4D data located on disk

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
__version__ = "$Revision: 1.37 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"


from ConfigParser import *
import vtk
import os.path

import Logging
from DataUnit import *

class DataWriter:
    """
    Class: DataWriter
    Created: 26.03.2005
    Description: A base class for different kinds of DataWriters
    """
    def __init__(self):
        """
        Method: __init__
        Created: 26.03.2005
        Description: Constructor
        """    
        pass
        
        
    def sync(self):
        """
        Method: sync()
        Created: 26.03.2005
        Description: Write pending imagedata to disk
        """    
        raise "Abstract method sync() called"
    
    def write(self):
        """
        Method: write()
        Created: 26.03.2005
        Description: Write the data to disk
        """    
        raise "Abstract method write() called"    
        
    def addImageData(self,imageData):
        """
        Method: addImageData(imageData)
        Created: 26.03.2005,KP
        Description: Add a vtkImageData object to be written to the disk.
        """    
        raise "Abstract method addImageData"
        

    def addImageDataObjects(self,imageDataList):        
        """
        Method: addImageDataObjects(imageDataList)
        Created: 26.03.2005, KP
        Description: Adds a list of vtkImageData objects to be written to the
                      disk. Uses addVtiObject to do all the dirty work
        """
        raise "Abstract method addImageDataObjects called"
        
class DataSource:
    """
    Class: DataSource
    Created: 03.11.2004, JM
    Description: A base class for different kinds of DataSources
    """

    def __init__(self):
        """
        Method: __init__()
        Created: 17.11.2004, KP
        Description: Initialization
        """
        self.ctf = None

    def getDataSetCount(self):
        """
        Method: getDataSetCount
        Created: 03.11.2004, JM
        Description: Returns the number of individual DataSets (=time points)
        managed by this DataSource
        NOT IMPLEMENTED HERE
        """
        raise "Abstract method getDataSetCount() in DataSource called"

    def getFileName(self):
        """
        Method: getFileName()
        Created: 21.07.2005
        Description: Return the file name
        """    
        raise "Abstract method getFileName() called in DataSource"

    def getDataSet(self, i):
        """
        Method: getDataSet
        Created: 03.11.2004, JM
        Description: Returns the DataSet at the specified index
        Parameters:   i       The index
        NOT IMPLEMENTED HERECreator: KP
        """
        raise "Abstract method getDataSet() in DataSource called"

    def getName(self):
        """
        Method: getName()
        Created: 18.11.2004, KP
        Description: Returns the name of the dataset series which this datasource
                     operates on
        """
        raise "Abstract method getName() in DataSource called"
        
    def getDimensions(self):
        """
        Method: getDimensions()
        Created: 14.12.2004, KP
        Description: Returns the (x,y,z) dimensions of the datasets this 
                     dataunit contains
        """
        raise "Abstract method getDimensions() in DataSource called"

