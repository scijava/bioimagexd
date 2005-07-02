# -*- coding: iso-8859-1 -*-
"""
 Unit: process
 Project: BioImageXD
 Created: 25.11.2004, KP
 
 Description:
 A Module for processing a dataset, for example by filtering noise

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
import Logging
from Module import *

class Process(Module):
    """
    Class: Process
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
        self.doMedian=False
        self.doAnisotropic=False
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

        if settings.get("MedianFiltering"):
            self.doMedian=True
            self.medianNeighborhood=settings.get("MedianNeighborhood")

        if settings.get("SolitaryFiltering"):
            self.doSolitary=True
            self.solitaryX=settings.get("SolitaryHorizontalThreshold")
            self.solitaryY=settings.get("SolitaryVerticalThreshold")
            self.solitaryThreshold=settings.get("SolitaryProcessingThreshold")
        if settings.get("AnisotropicDiffusion"):
            self.doAnisotropic=True

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
            Logging.info("More than one source dataset for data processing, using %dth"%n,kw="processing")
            
        data=self.images[n]
        
        if self.doSolitary:
            Logging.info("Doing solitary filtering",kw="processing")
            t3=time.time()
            # Using VTK´s vtkImageMedian3D-filter
            solitary = vtk.vtkImageSolitaryFilter()
            solitary.SetInput(data)
            solitary.SetFilteringThreshold(self.solitaryThreshold)
            solitary.SetHorizontalThreshold(self.solitaryX)
            solitary.SetVerticalThreshold(self.solitaryY)
            solitary.Update()
            t4=time.time()
            Logging.info("It took %.4f seconds"%(t4-t3),kw="processing")
            data=solitary.GetOutput()
        # Median filtering
        if self.doMedian:
            Logging.info("Doing median filtering",kw="processing")
            # Using VTK´s vtkImageMEdian3D-filter
            median = vtk.vtkImageMedian3D()
            median.SetInput(data)
            median.SetKernelSize(self.medianNeighborhood[0],
                                 self.medianNeighborhood[1],
                                 self.medianNeighborhood[2])
            #median.ReleaseDataFlagOff()
            median.Update()
            data=median.GetOutput()
        if self.doAnisotropic:
            Logging.info("Doing anisotropic diffusion",kw="processing")
            aniso=vtk.vtkImageAnisotropicDiffusion3D()
            aniso.SetInput(data)
            aniso.Update()
            data=aniso.GetOutput()

        t2=time.time()
        Logging.info("Processing took %.4f seconds"%(t2-t1))

        return data
