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
 JH - Juha Hyytiäinen, juhyytia@st.jyu.fi
 JM - Jaakko Mäntymaa, jahemant@cc.jyu.fi
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 JV - Jukka Varsaluoma,varsa@st.jyu.fi

 Copyright (c) 2004 Selli Project.
"""
__author__ = "Selli Project <http://sovellusprojektit.it.jyu.fi/selli/>"
__version__ = "$Revision: 1.19 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import vtk
import ImageOperations



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
        self.dataunits=[]
        self.doRGB=0
        self.x,self.y,self.z=0,0,0
        self.extent=None
        self.zoomFactor=1
        self.settings=None
    
    def setSettings(self,settings):
        """
        Method: setSettings(settings)
        Created: 27.03.2005, KP
        Description: Sets the settings object of this module
        """
        self.settings=settings
        
    def setZoomFactor(self,factor):
        """
        Method: setZoomFactor(factor)
        Created: 23.02.2005, KP
        Description: Sets the zoom factor for the produced dataset.
                     This means that the preview dataset will be zoomed with
                     the specified zoom factor
        """
        self.zoomFactor=factor
            
    def zoomDataset(self,dataset):
        """
        Method: setZoomFactor(factor)
        Created: 23.02.2004, KP
        Description: Returns the dataset zoomed with the zoom factor
        """
        if self.zoomFactor != 1:
            return ImageOperations.vtkZoomImage(dataset,self.zoomFactor)
        return dataset
            
    def getZoomFactor(self,factor):
        """
        Method: setZoomFactor(factor)
        Created: 23.02.2004, KP
        Description: Returns the zoom factor
        """
        return self.zoomFactor

    def reset(self):
         """
         Method: reset()
         Created: 04.11.2004, KP
         Description: Resets the module to initial state
         """
         self.images=[]
         self.extent=None
         self.x,self.y,self.z=0,0,0

    def addInput(self,dataunit,imageData):
        """
         Method: addInput(imageData)
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
        self.dataunits.append(dataunit)

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

