# -*- coding: iso-8859-1 -*-
"""
 Unit: ColocalizationNumpy.py
 Project: Selli
 Created: 16.11.2004
 Creator: KP
 Description:

 Creates a colocalization map using the Numeric Python library

 Modified: 03.11.2004 JV - Added comments.
           08.11.2004 KP - The preview is now generated in a single image at the
			   specified depth, and the previewed depth is controlled
			   with vtkImageMapper's SetZSlice()-method
		   16.11.2004 KP - Copied the old Colocalization module for reference
		   16.11.2004 KP - The calculations are now done using Numeric and the
		                   whole image is processed at once
 Selli includes the following persons:
 JH - Juha Hyytiäinen, juhyytia@st.jyu.fi
 JM - Jaakko Mäntymaa, jahemant@cc.jyu.fi
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 JV - Jukka Varsaluoma,varsa@st.jyu.fi

 Copyright (c) 2004 Selli Project.
 --------------------------------------------------------------
"""

__author__ = "Selli Project <http://sovellusprojektit.it.jyu.fi/selli/>"
__version__ = "$Revision: 1.24 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"


import vtk
import time
from Module import *
from Numeric import *

class Colocalization(NumericModule):
    """
    --------------------------------------------------------------
    Class: Colocalization
    Created: 03.11.2004
    Creator: KP
    Description: Creates a colocalization map
    -------------------------------------------------------------
    """


    def __init__(self,**kws):
        """
        --------------------------------------------------------------
        Method: __init__(**keywords)
        Created: 03.11.2004
        Creator: KP
        Description: Initialization
        -------------------------------------------------------------
        """
    	NumericModule.__init__(self,**kws)

        # TODO: remove attributes that already exist in base class!
    	self.images=[]
    	self.doRGB=0
    	self.x,self.y,self.z=0,0,0
    	self.extent=None
    	self.thresholds=[]
    	self.preview=None
    	self.running=0
    	self.arrays=[]
    	self.depth=8
    	self.leastVoxels=0
    	self.colocAmount=0
    	self.infos=[]

    def setBitDepth(self,depth):
        """
        --------------------------------------------------------------
        Method: setBitDepth(depth)
        Created: 17.11.2004
        Creator: KP
        Description: Sets the bit depth of the genrated colocalization map
        -------------------------------------------------------------
        """
        if depth=="1-bit":
            self.depth=1
        elif depth=="8-bit":
            self.depth=8
        elif depth=="24-bit":
            self.depth=24
        else:
            print "Depth %s not recognized"%depth
            self.depth=8



    def reset(self):
        """
        --------------------------------------------------------------
        Method: reset()
        Created: 04.11.2004
        Creator: KP
        Description: Resets the module to initial state. This method is
                     used mainly when doing previews, when the parameters
                     that control the colocalization are changed and the
                     preview data becomes invalid.
        -------------------------------------------------------------
        """
        Module.reset(self)
        self.thresholds=[]
    	self.preview=None
    	self.numpyarrays=[]
    	self.arrays=[]
    	self.infos=[]

    def addInput(self,data,**kws):
        """
        --------------------------------------------------------------
        Method: addInput(data,**keywords)
        Created: 03.11.2004
        Creator: KP
        Description: Adds an input for the colocalization filter
        Keywords:
          threshold=0-255    An integer ranging from 0-255. If voxel (x,y,z)
                             in all input datasets has a higher intensity than 
                             the given threshold then the voxel is considered to
                             be colocalizing
        -------------------------------------------------------------
        """
        if not kws.has_key("threshold"):
           raise "No colocalization threshold specified!"
        self.thresholds.append(kws["threshold"])
        Module.addInput(self,data,**kws)

    def getPreview(self,z):
        """
        --------------------------------------------------------------
        Method: getPreview(z)
        Created: 03.11.2004
        Creator: KP
        Description: Does a preview calculation for the x-y plane at depth z
        -------------------------------------------------------------
        """
        if not self.preview:
            self.preview=self.doOperation()
        return self.preview


    def doOperation(self):
        """
        --------------------------------------------------------------
        Method: doOperation
        Created: 10.11.2004
        Creator: KP
        Description: Does colocalization for the whole dataset
                     using doColocalizationXBit() where X is user defined
        -------------------------------------------------------------
        """

        if not self.arrays:
            for i in self.images:
                array,info=self.VTKtoNumpy(i)
                self.arrays.append(array)
                self.infos.append(info) 
        
        print "Doing %d-bit colocalization"%self.depth
        if self.depth==1:
            return self.doColocalization1Bit()
        elif self.depth==8:
            return self.doColocalization8Bit()
        elif self.depth==24:
            print "Cannot create 24-bit colocalization, doing 8-bit instead"
            return self.doColocalization8Bit()
        else:
            print "Unknown depth %d, doing 8-bit colocalization"%self.depth
            return self.doColocalization8Bit()


    def doColocalization8Bit(self):
        """
        --------------------------------------------------------------
        Method: doColocalization8Bit()
        Created: 10.11.2004
        Creator: KP
        Description: Does 8-bit colocalization for the whole dataset
                     using numeric python
        -------------------------------------------------------------
        """
        t1=time.time()
        datasets=[]

        # First we filter the positions with scalar values lesser than the 
        # threshold to have the value 0
        for i in range(0,len(self.arrays)):
            m=where(less(self.arrays[i],self.thresholds[i]),0,self.arrays[i])
            datasets.append(m)
        # Next we need to AND the datasets so that if any dataset has a zero 
        # in (x,y,z) then all the datasets will have zero at (x,y,z)

        # Get the one bit colocalization that works as a mask
        # telling us where there is colocalization and where is not
        # Also, we do not have to calculate the dataset with least voxels over
        # the threshold and the actual amount of colocalization when we use the
        # 1-bit colocalization
        mask=self.get1BitMask()

        # Now we have the mask that tells us where the colocalization is
        filtered=[]
        # Next we take the datasets that have values less than the threshold
        # filtered to 0. We need to also filter out the values that are > 0
        # but are 0 in some other dataset. These filtered datasets we append
        # to a list
        for i in range(0,len(datasets)):
            tmpdata=where(mask,datasets[i],0)
            filtered.append(tmpdata)

        # We then add the items in the list together to form one dataset
        # where the colocalizing voxels have a value that is the sum of
        # all the datasets values in that voxels
        # Here we need to set the type of the result array to Int16 since we may
        # overflow the Int8 in the code below
        result=filtered[0].astype(UnsignedInt16)
        for i in range(1,len(filtered)):
            tmpres=add(result,filtered[i])
            result=tmpres
        # The values of all the voxels in this resulting dataset
        # are then divided by the amount of source datasets, thus
        # scaling the values of the resulting voxels back to 0-255
        # The value of each voxel is then the average of the values
        # of that voxel in all of the datasets
        result/=len(filtered)
        print result.shape

        # Now the data is back to 8 bit again, so we can return it with the
        # proper type
        data=self.NumpyToVTK(result.astype(UnsignedInt8),self.infos[0])
        t2=time.time()
        print "Doing colocalization took %f seconds"%(t2-t1)
        return data


    def getColocalizationAmount(self):
        """
        --------------------------------------------------------------
        Method: getColocalizationAmount
        Created: 1.12.2004
        Creator: KP
        Description: Returns the number of colocalizing voxels
        -------------------------------------------------------------
        """

        return self.colocAmount

    def getLeastVoxelsOverTheThreshold(self):
        """
        --------------------------------------------------------------
        Method: getLeastVoxelsOverTheThreshold()
        Created: 1.12.2004
        Creator: KP
        Description: Returns the number of voxels over the threshold from the
                dataset that has the least number of voxels over the threshold.
        -------------------------------------------------------------
        """

        return self.leastVoxels

    def get1BitMask(self):
        """
        --------------------------------------------------------------
        Method: get1BitMask()
        Created: 1.12.2004
        Creator: KP
        Description: Returns a Numeric Array mask with 1's where the
                     voxel scalar is over the specified threshold
        -------------------------------------------------------------
        """
        masks=[]

        for i in range(0,len(self.arrays)):
            m=greater_equal(self.arrays[i],self.thresholds[i])
            masks.append(m)
        self.leastVoxels=0

        for mask in masks:
            masksum=sum(mask.flat)
            if not self.leastVoxels or masksum<self.leastVoxels:
                self.leastVoxels=masksum
        print "Least voxels that are > threshold: ",self.leastVoxels

        result=masks[0]
        for i in range(1,len(masks)):
            res2=logical_and(result,masks[i])
            result=res2
        self.colocAmount=sum(result.flat)
        return result

    def doColocalization1Bit(self):
        """
        --------------------------------------------------------------
        Method: doColocalization1Bit()
        Created: 10.11.2004
        Creator: KP
        Description: Does 1-bit colocalization for the whole dataset
                     using numeric python
        -------------------------------------------------------------
        """
        t1=time.time()
        result=self.get1BitMask()
        result*=255
        print result.shape
        data=self.NumpyToVTK(result,self.infos[0])
        t2=time.time()
        print "Doing colocalization took %f seconds"%(t2-t1)
        return data

