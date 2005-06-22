# -*- coding: iso-8859-1 -*-
"""
 Unit: DataUnitProcessing
 Project: BioImageXD
 Created: 25.11.2004, KP
 
 Description:
 A Module for all processing done to a single dataset series. This includes but
 is not limited to: Correction of bleaching, mapping intensities through 
 intensity transfer function and noise removal.


 Modified: 25.11.2004 JV - Created the module
           10.12.2004 JV - Doesn't do intensity mapping if function is identical
                           Gets settings in preview
                           Does filtering, almost
           11.12.2004 JV - Fixed: Algorithm in Solitary Filtering
           11.01.2005 JV - Init calls reset, uodated solitary algorithm

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
__version__ = "$Revision: 1.13 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"


import vtk
import time
from Module import *

class DataUnitProcessing(Module):
    """
    Class: DataUnitProcessing
    Created: 25.11.2004, KP
    Description: Processes a single dataunit in specified ways
    """

    def __init__(self,**kws):
        """
        Method: __init__(**keywords)
        Created: 25.11.2004, KP
        Description: Initialization
        """
        Module.__init__(self,**kws)

        # TODO: remove attributes that already exist in base class!
        self.images=[]
        self.x,self.y,self.z=0,0,0
        self.extent=None
        self.running=0
        self.depth=8

        self.reset()

    def reset(self):
        """
        Method: reset()
        Created: 25.11.2004, KP
        Description: Resets the module to initial state. This method is
                     used mainly when doing previews, when the parameters
                     that control the colocalization are changed and the
                     preview data becomes invalid.
        """
        Module.reset(self)
        self.preview=None
        self.intensityTransferFunctions = []
        self.doMedian=False
        self.medianNeighborhood=(1,1,1)
        self.doSolitary=False
        self.solitaryX=0
        self.solitaryY=0
        self.solitaryThreshold=0
        self.extent=None
        self.n=-1

    def addInput(self,dataunit,data):
        """
        Method: addInput(data)
        Created: 1.12.2004, KP, JV
        Description: Adds an input for the single dataunit processing filter
        """
        Module.addInput(self,dataunit,data)
        settings = dataunit.getSettings()
        #self.n+=1
        #settings=self.settings
        #tf=settings.getCounted("IntensityTransferFunctions",self.n)
        tf = settings.getCounted("IntensityTransferFunctions",self.timepoint)
        if not tf:            
            raise ("No Intensity Transfer Function given for Single DataUnit "
            "to be processed")
        self.intensityTransferFunctions.append(tf)

        if settings.get("MedianFiltering"):
            self.doMedian=True
            self.medianNeighborhood=settings.get("MedianNeighborhood")

        if settings.get("SolitaryFiltering"):
            self.doSolitary=True
            self.solitaryX=settings.get("SolitaryHorizontalThreshold")
            self.solitaryY=settings.get("SolitaryVerticalThreshold")
            self.solitaryThreshold=settings.get("SolitaryProcessingThreshold")

    def getPreview(self,z):
        """
        Method: getPreview(z)
        Created: 1.12.2004, KP
        Description: Does a preview calculation for the x-y plane at depth z
        """
        if not self.preview:
            dims=self.images[0].GetDimensions()
            if z>=0:
                self.extent=(0,dims[0]-1,0,dims[1]-1,z,z)
            else:
                self.extent=None
            self.preview=self.doOperation()
            self.extent=None
        return self.zoomDataset(self.preview)


    def doOperation(self):
        """
        Method: doOperation
        Created: 1.12.2004, KP, JV
        Description: Processes the dataset in specified ways
        """
        t1=time.time()

        # Map scalars with intensity transfer list
        n=0
        if len(self.images)>1:
            settings = self.dataunits[0].getSettings()
            n=settings.get("PreviewedDataset")
            print "More than one source dataset for Single DataUnit Processing, using %d"%n
            
        mapdata=self.images[n]
        mapIntensities=vtk.vtkImageMapToIntensities()
        mapIntensities.SetIntensityTransferFunction(self.intensityTransferFunctions[n])
        mapIntensities.SetInput(mapdata)
        
        data=mapIntensities.GetOutput()
        if self.extent:
            print "Update extent=",self.extent
            mapdata.SetUpdateExtent(self.extent)
            data.SetUpdateExtent(self.extent)
        mapIntensities.Update()
        
        if self.doSolitary:
            print "Doing New Solitary Filtering"
            t3=time.time()
            # Using VTK´s vtkImageMedian3D-filter
            solitary = vtk.vtkImageSolitaryFilter()
            solitary.SetInput(data)
            solitary.SetFilteringThreshold(self.solitaryThreshold)
            solitary.SetHorizontalThreshold(self.solitaryX)
            solitary.SetVerticalThreshold(self.solitaryY)
            solitary.Update()
            t4=time.time()
            print "New Solitary filtering took ",(t4-t3),"seconds"
            data=solitary.GetOutput()
            print "data type=",data.GetScalarTypeAsString()
            print "data dimensions=",data.GetDimensions()
        # Median filtering
        if self.doMedian:
            print "Doing Median Filtering"
            # Using VTK´s vtkImageMEdian3D-filter
            median = vtk.vtkImageMedian3D()
            median.SetInput(data)
            median.SetKernelSize(self.medianNeighborhood[0],
                                 self.medianNeighborhood[1],
                                 self.medianNeighborhood[2])
            #median.ReleaseDataFlagOff()
            median.Update()
            data=median.GetOutput()

        t2=time.time()
        print "Processing took %f seconds"%(t2-t1)

        return data
