# -*- coding: iso-8859-1 -*-
"""
 Unit: ColorMerging.py
 Project: Selli
 Created: 24.11.2004
 Creator: JV
 Description:

 Merges two (or more) 8-bit datasets to one 24-bit using the Numeric Python 
 library. Modified from ColocalizationNumpy

 Modified:
        03.12.2004 JV - Changed ColorMergingNumpy to ColorMerging
        10.12.2004 JV - Does not do intensity mapping if function is identical
        10.01.2005 JV -

 Selli includes the following persons:
 JH - Juha Hyytiäinen, juhyytia@st.jyu.fi
 JM - Jaakko Mäntymaa, jahemant@cc.jyu.fi
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 JV - Jukka Varsaluoma,varsa@st.jyu.fi

 Copyright (c) 2004 Selli Project.
"""

__author__ = "Selli Project <http://sovellusprojektit.it.jyu.fi/selli/>"
__version__ = "$Revision: 1.18 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"


import vtk
import time
from Module import *
from Numeric import *

class ColorMerging(NumericModule):
    """
    Class: ColorMergingNumpy
    Created: 24.11.2004
    Creator: JV
    Description: Merges two or more datasets to one
    """


    def __init__(self,**kws):
        """
        Method: __init__(**keywords)
        Created: 24.11.2004
        Creator: JV
        Description: Initialization
        """
    	NumericModule.__init__(self,**kws)

    	self.doRGB=True
        self.doAlpha=1
    	self.extent=[]
    	self.thresholds=[]
    	self.running=False

    	self.reset()

    def reset(self):
        """
        Method: reset()
        Created: 24.11.2004
        Creator: JV
        Description: Resets the module to initial state. This method is
                     used mainly when doing previews, when the parameters
                     that control the colocalization are changed and the
                     preview data becomes invalid.
        """
        Module.reset(self)
    	self.processedZSlices=[]
    	self.preview=None
    	self.numpyarrays=[]
    	self.arrays=[]
    	self.infos=[]
        self.intensityTransferFunctions = []
        self.rgbs=[]


    def addInput(self,data,**kws):
        """
        Method: addInput(data,**keywords)
        Created: 24.11.2004
        Creator: JV
        Description: Adds an input for the color merging filter
        Keywords:   rgb                    (red,green,blue) each in [0-255]
                    intensityTransferList  256 values, each in [0-255]
        """
        # ugly

        neenedkwds = ["rgb","intensityTransferFunction","alphaTransferFunction"]
        for neededkwd in neenedkwds:
            if not kws.has_key(neededkwd):
                raise "No "+neededkwd+" for color merging specified!"

        self.rgbs.append(kws["rgb"])
        self.alphaTF=kws["alphaTransferFunction"]
        self.intensityTransferFunctions.append(kws["intensityTransferFunction"])

        Module.addInput(self,data,**kws)

    def getPreview(self,z):
        """
        Method: getPreview(z)
        Created: 24.11.2004
        Creator: JV
        Description: Does a preview calculation for the x-y plane at depth z
        """
        self.doAlpha=0
        if not self.preview:
            self.preview=self.doOperation()
        self.doAlpha=1
        return self.preview


    def doOperation(self):
        """
        Method: doOperation
        Created: 24.11.2004
        Creator: JV
        Description: Does color merging for the whole dataset
                     using doColorMergingXBit() where X is user defined
        """
        #if not self.arrays:
        #    for i in self.images:
        #        array,info=self.VTKtoNumpy(i)
        #        print "Got array with shape ",array.shape
        #        self.arrays.append(array)
        #        self.infos.append(info)

        if self.doRGB:
            print "Doing 24-bit color merging"
            return self.doColorCombination24Bit()
        else:
            print "Doing 8-bit color merging"
            return self.doColorCombination8Bit()

    def doColorCombination24Bit(self):
        """
        Method: doColorCombination8Bit()
        Created: 24.11.2004
        Creator: JV
        Description: Does 8-bit color combination for the whole dataset
                     using numeric python
        """
        t1=time.time()
        datasets=[]
        alphas=[]

        # Map scalars with intensity transfer list

        print "We are processing %d arrays"%len(self.arrays)

        processed=[]
        imagelen=len(self.images)
        for i in range(0,imagelen):
            mapIntensities=vtk.vtkImageMapToIntensities()
            mapIntensities.SetIntensityTransferFunction(self.intensityTransferFunctions[i])
            mapIntensities.SetInput(self.images[i])
            mapIntensities.Update()
            data=mapIntensities.GetOutput()
            processed.append(data)
        # Color and combine 8-bit datasets to an 24-bit dataset

        # result rgb

        if self.doAlpha:
            createalpha=vtk.vtkImageAlphaFilter()
            for i in processed:
                createalpha.AddInput(i)
            createalpha.Update()
            alpha=createalpha.GetOutput()

        merge=vtk.vtkImageMerge()
        if self.doAlpha:
            merge.SetAlphaChannel(alpha)
        for i in processed:
            merge.AddInput(i)
        merge.SetColor(rgb)
        merge.Update()
        data=merge.GetOutput()
            # slower again, handles overflow
#            red   = minimum(add( red,   multiply( datasets[i], rgb[0] ) ),255)
#            green = minimum(add( green, multiply( datasets[i], rgb[1] ) ),255)
#            blue  = minimum(add( blue,  multiply( datasets[i], rgb[2] ) ),255)

        print result.shape
        t3=time.time()
        print "Calculations took %f seconds"%(t3-t1)
        t2=time.time()
        print "Doing color merging took %f seconds"%(t2-t1)
        return data



