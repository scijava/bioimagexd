# -*- coding: iso-8859-1 -*-
"""
 Unit: Module.py
 Project: Selli
 Created: 03.11.2004
 Creator: KP
 Description:

 A Base Class for all data processing modules. Inherits Thread for
 smooth user experience while processing the data

 Modified: 03.11.2004 JV - Comments.
           15.11.2004 KP - Made Module inherit Thread
           25.11.2004 KP - Module no longer inherits Thread, made a class 
                           NumericModule that has some methods
                           required by modules that use Numeric for calculations
           01.12.2004 JV - Added NumpyToVTK24bit (to be renamed?)
           03.12.2004 KP - Modified NumpyToVTK to support 3-component data based
                           on Numeric Array shape, removed
                           NumpyToVTK24bit

 Selli includes the following persons:
 JH - Juha Hyyti�inen, juhyytia@st.jyu.fi
 JM - Jaakko M�ntymaa, jahemant@cc.jyu.fi
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 JV - Jukka Varsaluoma,varsa@st.jyu.fi

 Copyright (c) 2004 Selli Project.
"""
__author__ = "Selli Project <http://sovellusprojektit.it.jyu.fi/selli/>"
__version__ = "$Revision: 1.19 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import vtk
from Numeric import *



class Module:
    """
    Class: Module
    Created: 03.11.2004, KP
    Description: A Base class for all data processing modules
    """
    def __init__(self,**kws):
        """
        Method: __init__(**keywords)
        Created: 03.11.2004, KP
        Description: Initialization
        """
        self.images=[]
        self.doRGB=0
        self.x,self.y,self.z=0,0,0
        self.extent=None

    def reset(self):
         """
         Method: reset()
         Created: 04.11.2004, KP
         Description: Resets the module to initial state
         """
         self.images=[]
         self.extent=None
         self.x,self.y,self.z=0,0,0

    def addInput(self,imageData,**kws):
        """
         Method: addInput(imageData,**keywords)
         Created: 03.11.2004, KP
         Description: Adds an input vtkImageData dataset for the module.
        """
        imageData.SetScalarTypeToUnsignedChar()
        x,y,z=imageData.GetDimensions()
        if self.x and self.y and self.z:
            if x!=self.x or y!=self.y or z!=self.z:
                raise ("ERROR: Dimensions do not match: currently (%d,%d,%d), "
                "new dimensions (%d,%d,%d)"%(self.x,self.y,self.z,x,y,z))
        else:
            self.x,self.y,self.z=imageData.GetDimensions()
            print "Set dimensions to %d,%d,%d"%(x,y,z)
        extent=imageData.GetExtent()
        if self.extent:
            if self.extent!=extent:
                raise "ERROR: Extents do not match"
        else:
            self.extent=extent
        self.images.append(imageData)

    def allocateImageData(self,x,y,z):
        """
        Method: allocateImageData(x,y,z)
        Created: 03.11.2004, KP
        Description: Allocates a vtkImageData object with the given
                     dimensions. If the resulting image should be RGB, the
                     number of components in the object is set to 4.
        Parameters:  x,y,z     The dimensions for the new vtkImageDataObject
        """
        new=vtk.vtkImageData()
        if not self.extent:
            raise "ERROR: No extent defined, use addInput() first"
        new.SetExtent(self.extent)
        if not self.x:
            raise "ERROR: No dimensions defined, use addInput() first"
        new.SetDimensions(self.x+1,self.y+1,self.z+1)
        new.SetScalarTypeToUnsignedChar()
        if self.doRGB:
            # When we do rgb rendering, we use 4 components
            print "Set number of scalar components to 3"
            new.SetNumberOfScalarComponents(3)
        new.AllocateScalars()
        return new


    def getPreview(self,z):
        """
        Method: getPreview(z)
        Created: 03.11.2004, KP
        Description: Does a preview calculation for the x-y plane at depth z
        """
        raise "Abstract method getPreview() called"

    def processData(self,z,newData,toZ=None):
        """
        Method: processData(z,newData,toZ)
        Created: 03.11.2004, KP
        Description: Processes the input data
        Parameters: z        The z coordinate of the plane to be processed
                    newData  The output vtkImageData object
                    toZ      Optional parameter defining the z coordinate
                             where the colocalization data is written
        """
        raise "Abstract method processData(z,data)"

    def doOperation(self):
        """
        Method: doOperation()
        Created: 01.12.2004, KP
        Description: Does the operation for the specified datasets.
        """
        raise "Abstract method doOperation() called"

