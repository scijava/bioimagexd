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
        self.bitdepth=0
        self.resample=None
        self.mipData = None
        self.resampleDims=None
        self.resampleTp=-1
        self.scalarRange=None
        self.originalDimensions=None
        self.resampleFactors = None
        self.resampledVoxelSize=None
        
    def setResampleDimensions(self,dims):
        """
        Method: setResampleDimensions
        Created: 1.09.2005, KP
        Description: Set the resample dimensions
        """    
        self.resampleDims=dims
        
    def getResampleFactors(self):
        """
        Method: getResampleFactors
        Created: 07.04.2006, KP
        Description: Return the factors for the resampling
        """        
        if not self.resampleFactors and self.resampleDims:        
            if not self.originalDimensions:
                rd=self.resampleDims
                self.resampleDims=None
                self.originalDimensions = self.getDimensions()
                self.resampleDims=rd
            
            x,y,z=self.originalDimensions
            rx,ry,rz=self.resampleDims
            xf=rx/float(x)
            yf=ry/float(y)
            zf=rz/float(z)
            print "x,y,z=",x,y,z
            print "rz,ry,rz=",self.resampleDims
            self.resampleFactors = (xf,yf,zf)
        return self.resampleFactors
        
    def getResampledVoxelSize(self):
        if not self.resampleDims:
            return None
        if not self.resampledVoxelSize:
            
            vx,vy,vz=self.getVoxelSize()
        
            rx,ry,rz=self.getResampleFactors()           
            print rx,ry,rz
            self.resampledVoxelSize=(vx/rx,vy/ry,vz/rz)
        return self.resampledVoxelSize

        
    def getResampleDimensions(self):
        """
        Method: getResampleDimensions
        Created: 11.09.2005, KP
        Description: Get the resample dimensions
        """        
        return self.resampleDims
    
    def getMIPdata(self,n):
        """
        Method: getMIPdata
        Created: 05.06.2006, KP
        Description: Return a small resampled dataset of which a small
                     MIP can be created.
        """                
        if not self.mipData:
            print "Resampling data to get fast MIP"
            x,y,z=self.getDimensions()
            self.mipData = self.getResampledData(self.getDataSet(n),n,tmpDims = (128,128,z))
        return self.mipData
    
    def getResampledData(self,data,n,tmpDims=None):
        """
        Method: getResampledData
        Created: 1.09.2005, KP
        Description: Return the data resampled to given dimensions
        """
        dims=data.GetDimensions()
        if 0 and dims[0]*dims[1]>(1024*1024):
            self.resampleDims=(1024,1024,dims[2])
        if not tmpDims and not self.resampleDims:return data
        
        useDims = self.resampleDims
        if tmpDims:
            useDims = tmpDims
        
        if n==self.resampleTp and self.resample and not useDims:
            return self.resample.GetOutput()
        else:
            Logging.info("Resampling data to ",self.resampleDims,kw="dataunit")
            self.resample=vtk.vtkImageResample()
            self.resample.SetInput(data)
            x,y,z=data.GetDimensions()
            self.originalDimensions=(x,y,z)
            rx,ry,rz=useDims
            xf=rx/float(x)
            yf=ry/float(y)
            zf=rz/float(z)
            
            self.resample.SetAxisMagnificationFactor(0,xf)
            self.resample.SetAxisMagnificationFactor(1,yf)
            self.resample.SetAxisMagnificationFactor(2,zf)
            self.resample.Update()
            return self.resample.GetOutput()        

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

    def getDataSet(self, i,raw=0):
        """
        Method: getDataSet
        Created: 03.11.2004, JM
        Description: Returns the DataSet at the specified index
        Parameters:   i       The index
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

    def getScalarRange(self):
        """
        Method: getBitDepth
        Created: 28.05.2005, KP
        Description: Return the bit depth of data
        """
        self.getBitDepth()
        return self.scalarRange
        
    def getBitDepth(self):
        """
        Method: getBitDepth
        Created: 28.05.2005, KP
        Description: Return the bit depth of data
        """
        if not self.bitdepth:
            
            data=self.getDataSet(0,raw=1)
            
            self.scalarRange=data.GetScalarRange()
            print "Scalar range of data",self.scalarRange
            scalartype=data.GetScalarType()
            print "Scalar type",scalartype,data.GetScalarTypeAsString()
            print "Number of scalar components",data.GetNumberOfScalarComponents()
        
            if scalartype==4:
                self.bitdepth=16
            elif scalartype==5:
                self.bitdepth=16
#                if max(self.scalarRange)>4096:
#                    self.bitdepth=16
#                else:
#                    self.bitdepth=12
            elif scalartype==3:
                self.bitdepth=8
            elif scalartype==7:
                self.bitdepth=16
            elif scalartype==11:
                self.bitdepth=16
            else:

                raise "Bad LSM bit depth, %d,%s"%(scalartype,data.GetScalarTypeAsString())
            self.bitdepth*=data.GetNumberOfScalarComponents()
        return self.bitdepth
