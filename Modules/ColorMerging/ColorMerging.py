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
 --------------------------------------------------------------
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
    --------------------------------------------------------------
    Class: ColorMergingNumpy
    Created: 24.11.2004
    Creator: JV
    Description: Merges two or more datasets to one
    -------------------------------------------------------------
    """


    def __init__(self,**kws):
        """
        --------------------------------------------------------------
        Method: __init__(**keywords)
        Created: 24.11.2004
        Creator: JV
        Description: Initialization
        -------------------------------------------------------------
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
        --------------------------------------------------------------
        Method: reset()
        Created: 24.11.2004
        Creator: JV
        Description: Resets the module to initial state. This method is
                     used mainly when doing previews, when the parameters
                     that control the colocalization are changed and the
                     preview data becomes invalid.
        -------------------------------------------------------------
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
        --------------------------------------------------------------
        Method: addInput(data,**keywords)
        Created: 24.11.2004
        Creator: JV
        Description: Adds an input for the color merging filter
        Keywords:   rgb                    (red,green,blue) each in [0-255]
                    intensityTransferList  256 values, each in [0-255]
        -------------------------------------------------------------
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
        --------------------------------------------------------------
        Method: getPreview(z)
        Created: 24.11.2004
        Creator: JV
        Description: Does a preview calculation for the x-y plane at depth z
        -------------------------------------------------------------
        """
        self.doAlpha=0
        if not self.preview:
            self.preview=self.doOperation()
        self.doAlpha=1
        return self.preview


    def doOperation(self):
        """
        --------------------------------------------------------------
        Method: doOperation
        Created: 24.11.2004
        Creator: JV
        Description: Does color merging for the whole dataset
                     using doColorMergingXBit() where X is user defined
        -------------------------------------------------------------
        """
        if not self.arrays:
            for i in self.images:
                array,info=self.VTKtoNumpy(i)
                print "Got array with shape ",array.shape
                self.arrays.append(array)
                self.infos.append(info)

        if self.doRGB:
            print "Doing 24-bit color merging"
            return self.doColorCombination24Bit()
        else:
            print "Doing 8-bit color merging"
            return self.doColorCombination8Bit()

    def doColorCombination24Bit(self):
        """
        --------------------------------------------------------------
        Method: doColorCombination8Bit()
        Created: 24.11.2004
        Creator: JV
        Description: Does 8-bit color combination for the whole dataset
                     using numeric python
        -------------------------------------------------------------
        """
        t1=time.time()
        datasets=[]
        alphas=[]

        # Map scalars with intensity transfer list

        print "We are processing %d arrays"%len(self.arrays)

        if self.doAlpha:
            alphadataset = zeros(self.arrays[0].shape,UnsignedInt8)
        arraylen=len(self.arrays)
        for i in range(0,arraylen):
            dataset=zeros(self.arrays[i].shape,UnsignedInt16)
            alpha=zeros(self.arrays[i].shape,UnsignedInt16)

            # No mapping if intensity transfer function is identical
            if self.intensityTransferFunctions[i].isIdentical():
                print "Identical dataset"
                datasets.append(self.arrays[i].astype(UnsignedInt16))
            else:
                print "Mapping through iTF"
                table=self.intensityTransferFunctions[i].getAsList()
                table=array(table,UnsignedInt8)
                dataset.flat[:] = take(table, self.arrays[i].flat)
                datasets.append(dataset.astype(UnsignedInt16))

            # If we need to produce an alpha channel, then we create it using
            # the average of all the scalar values of the channels and passing
            # that value through the iTF
            if self.doAlpha:
                print "Creating alpha..."
                avg=divide(dataset,arraylen)
                alphadataset+=avg.astype(UnsignedInt8)
#        val=max(alphadataset.flat)
#        coeff=256/float(val)
#        alphadataset*=coeff

        # Color and combine 8-bit datasets to an 24-bit dataset

        # result rgb
        red   = zeros(datasets[0].shape,UnsignedInt16)
        green = zeros(datasets[0].shape,UnsignedInt16)
        blue  = zeros(datasets[0].shape,UnsignedInt16)


        if self.doAlpha:
            alphatable=array(self.alphaTF.getAsList(),UnsignedInt8)
            alpha.flat[:] = take(alphatable,alphadataset.flat)


        for i in range(0,len(datasets)):
            rgb=divide(self.rgbs[i],255.0)
            print "rgb=",rgb
            # faster, adds directly to array (does not handle overflow)
            if rgb[0]:
                add( red, multiply(datasets[i],
                    rgb[0]).astype(UnsignedInt16), red)
            if rgb[1]:
                add( green,multiply(datasets[i],
                    rgb[1]).astype(UnsignedInt16), green)
            if rgb[2]:
                add( blue, multiply(datasets[i],
                    rgb[2]).astype(UnsignedInt16), blue)

            # slower again, handles overflow
#            red   = minimum(add( red,   multiply( datasets[i], rgb[0] ) ),255)
#            green = minimum(add( green, multiply( datasets[i], rgb[1] ) ),255)
#            blue  = minimum(add( blue,  multiply( datasets[i], rgb[2] ) ),255)

        # If we want to combine the three different arrays to one three-
        # component array, we need to first interleave the arrays to one array
        # with a size three times that of the input array

	a=array((5,5),Int32)
	tc=minimum(a,3).typecode()
        minimum(red, 255, red.astype(tc))
        minimum(green, 255, green.astype(tc))
        minimum(blue, 255, blue.astype(tc))
        newshape=list(red.shape)
        # 4 means three color channels (red, green, blue) and one alpha channel
        components=4
        if not self.doAlpha:
            components=3
        newshape.append(components)
        offset=reduce(multiply,newshape)
        # If red.shape = (x,y,z), offset is now x*y*z
        # so the first indices should be like [0,3,6,...,x*y*z-3]
        # the second indices should be like   [1,4,7,...,x*y*z-2]
        # the third indices should be like    [2,5,8,...,x*y*z-1]

        # 4 means three color channels (red, green, blue) and one alpha channel
        ind=arange(0,offset,components)
        ind2=add(ind,1)
        ind3=add(ind,2)
        ind4=add(ind,3)
        result=zeros(newshape)
        put(result,ind,red)
        put(result,ind2,green)
        put(result,ind3,blue)
        if self.doAlpha:
            put(result,ind4,alpha)

        print result.shape
        t3=time.time()
        print "Calculations took %f seconds"%(t3-t1)
        data=self.NumpyToVTK(result,self.infos[0])
        t2=time.time()
        print "Doing color merging took %f seconds"%(t2-t1)
        return data



