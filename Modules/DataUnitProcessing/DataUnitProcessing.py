# -*- coding: iso-8859-1 -*-
"""
 Unit: DataUnitProcessing
 Project: Selli
 Created: 25.11.2004
 Creator: KP
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

 Selli includes the following persons:
 JH - Juha Hyytiäinen, juhyytia@st.jyu.fi
 JM - Jaakko Mäntymaa, jahemant@cc.jyu.fi
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 JV - Jukka Varsaluoma,varsa@st.jyu.fi

 Copyright (c) 2004 Selli Project.
"""

__author__ = "Selli Project <http://sovellusprojektit.it.jyu.fi/selli/>"
__version__ = "$Revision: 1.13 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"


import vtk
import time
from Module import *
from Numeric import *



class DataUnitProcessing(Module):
    """
    Class: DataUnitProcessing
    Created: 25.11.2004, KP
    Description: Processes a single dataunit in specified ways
    """

    def __init__(self,**kws):
        """
        Method: __init__(**keywords)
        Created: 25.11.2004
        Creator: KP
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
        Created: 25.11.2004
        Creator: KP
        Description: Resets the module to initial state. This method is
                     used mainly when doing previews, when the parameters
                     that control the colocalization are changed and the
                     preview data becomes invalid.
        """
        Module.reset(self)
    	self.preview=None
    	self.numpyarrays=[]
    	self.arrays=[]
    	self.infos=[]
        self.intensityTransferFunctions = []
        self.doMedian=False
        self.medianNeighborhood=(1,1,1)
        self.doSolitary=False
        self.solitaryX=0
        self.solitaryY=0
        self.solitaryThreshold=0
        self.extent=None


    def addInput(self,data,**kws):
        """
        Method: addInput(data,**keywords)
        Created: 1.12.2004
        Creator: KP,JV
        Description: Adds an input for the single dataunit processing filter
        """

        if not kws.has_key("intensityTransferFunction"):
            raise ("No Intensity Transfer Function given for Single DataUnit "
            "to be processed")
        self.intensityTransferFunctions.append(kws["intensityTransferFunction"])

        if kws.has_key("medianNeighborhood"):
            self.doMedian=True
            self.medianNeighborhood=(kws["medianNeighborhood"])

        if kws.has_key("solitaryThresholds"):
            self.doSolitary=True
            self.solitaryX, self.solitaryY, self.solitaryThreshold = \
            (kws["solitaryThresholds"])

        Module.addInput(self,data,**kws)


    def getPreview(self,z):
        """
        Method: getPreview(z)
        Created: 1.12.2004
        Creator: KP
        Description: Does a preview calculation for the x-y plane at depth z
        """
        if not self.preview:
            dims=self.images[0].GetDimensions()
            self.extent=(0,dims[0]-1,0,dims[1]-1,z,z)
            self.preview=self.doOperation()
            self.extent=None
        return self.preview


    def doOperation(self):
        """
        Method: doOperation
        Created: 1.12.2004
        Creator: KP,JV
        Description: Processes the dataset in specified ways
        """
        t1=time.time()

        # Map scalars with intensity transfer list

        print "We are processing %d arrays"%len(self.images)
        if len(self.images)>1:
            raise "More than one source dataset for Single DataUnit Processing"

        mapdata=self.images[0]
        mapIntensities=vtk.vtkImageMapToIntensities()
        mapIntensities.SetIntensityTransferFunction(self.intensityTransferFunctions[0])
        mapIntensities.SetInput(mapdata)
        
        data=mapIntensities.GetOutput()
        if self.extent:
            print "Update extent=",self.extent
            #mapdata.SetUpdateExtent(self.extent)
            #data.SetUpdateExtent(self.extent)
        mapIntensities.Update()
        
        if self.doSolitary:
            print "Doing New Solitary Filtering"
            t3=time.time()
            #data=self.NumpyToVTK(retdataset,self.infos[0])
            # Using VTK´s vtkImageMEdian3D-filter
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

        #data=self.NumpyToVTK(retdataset,self.infos[0])
        return data
