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
"""

__author__ = "Selli Project <http://sovellusprojektit.it.jyu.fi/selli/>"
__version__ = "$Revision: 1.24 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"


import vtk
import time
from Module import *
from Numeric import *

class Colocalization(Module):
    """
    Class: Colocalization
    Created: 03.11.2004, KP
    Description: Creates a colocalization map
    """


    def __init__(self,**kws):
        """
        Method: __init__(**keywords)
        Created: 03.11.2004, KP
        Description: Initialization
        """
        Module.__init__(self,**kws)

        # TODO: remove attributes that already exist in base class!
        self.images=[]
        self.doRGB=0
        self.x,self.y,self.z=0,0,0
        self.extent=None
        self.running=0
        self.depth=8
        self.leastVoxels=0
        self.colocAmount=0
        self.reset()

    def setBitDepth(self,depth):
        """
        Method: setBitDepth(depth)
        Created: 17.11.2004, KP
        Description: Sets the bit depth of the genrated colocalization map
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
        Method: reset()
        Created: 04.11.2004, KP
        Description: Resets the module to initial state. This method is
                     used mainly when doing previews, when the parameters
                     that control the colocalization are changed and the
                     preview data becomes invalid.
        """
        Module.reset(self)
        self.colocFilter=vtk.vtkImageColocalizationFilter()
        self.thresholds=[]
        self.preview=None
    
    def addInput(self,data,**kws):
        """
        Method: addInput(data,**keywords)
        Created: 03.11.2004, KP
        Description: Adds an input for the colocalization filter
        Keywords:
          threshold=0-255    An integer ranging from 0-255. If voxel (x,y,z)
                             in all input datasets has a higher intensity than 
                             the given threshold then the voxel is considered to
                             be colocalizing
        """
        if not kws.has_key("threshold"):
           raise "No colocalization threshold specified!"
        self.thresholds.append(kws["threshold"])
        Module.addInput(self,data,**kws)
 
    def getPreview(self,z):
        """
        Method: getPreview(z)
        Created: 03.11.2004, KP
        Description: Does a preview calculation for the x-y plane at depth z
        """
        if not self.preview:
            self.preview=self.doOperation()
        return self.preview


    def doOperation(self):
        """
        Method: doOperation
        Created: 10.11.2004, KP
        Description: Does colocalization for the whole dataset
                     using doColocalizationXBit() where X is user defined
        """        
        print "Doing %d-bit colocalization"%self.depth
        t1=time.time()
        self.colocFilter.SetOutputDepth(self.depth)
        for i in range(len(self.images)):
            self.colocFilter.AddInput(self.images[i])
            self.colocFilter.SetColocalizationThreshold(i,self.thresholds[i])
        self.colocFilter.Update()
        self.leastVoxels = self.colocFilter.GetLeastVoxelsOverThreshold()
        self.colocAmount = self.colocFilter.GetColocalizationAmount()
        t2=time.time()
        print "Doing colocalization took %f seconds"%(t2-t1)
        return self.colocFilter.GetOutput()

        
    def getColocalizationAmount(self):
        """
        Method: getColocalizationAmount
        Created: 1.12.2004, KP
        Description: Returns the number of colocalizing voxels
        """
        return self.colocAmount

    def getLeastVoxelsOverTheThreshold(self):
        """
        Method: getLeastVoxelsOverTheThreshold()
        Created: 1.12.2004, KP
        Description: Returns the number of voxels over the threshold from the
                dataset that has the least number of voxels over the threshold.
        """
        return self.leastVoxels
