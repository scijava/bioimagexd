# -*- coding: iso-8859-1 -*-
"""
 Unit: VSIA
 Project: Selli
 Created: 25.11.2004, JV
 Description:

 Modified: 25.11.2004 JV - Created the module
           17.12.2004 JV - Updated AddInput
           11.01.2205 JV - Init calls reset, updated comments

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

__author__ = "Selli Project <http://sovellusprojektit.it.jyu.fi/selli/>"
__version__ = "$Revision: 1.14 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"


import vtk
import time
from Module import *
from Numeric import *

class VSIA(Module):
    """
    Class: VSIA
    Created: 25.11.2004
    Creator: JV
    Description:
    """


    def __init__(self,**kws):
        """
        Method: __init__(**keywords)
        Created: 25.11.2004, JV
        Description: Initialization
        """
        Module.__init__(self,**kws)

     	self.images=[]
     	self.doRGB=0
     	self.x,self.y,self.z=0,0,0
     	self.extent=None
     	self.running=0
     	self.depth=8

        self.renderingMode=0
        self.reset()

    def reset(self):
        """
        Method: reset()
        Created: 04.11.2004, KP
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
        self.lowerLimit=0
        self.upperLimit=0
        self.exactValues=0
        self.surfaceCount=0
        self.surface=0
        self.filterSettings=[]
        self.gaussianRadius=0


    def setSurfaceGeneration(self,filterClass,filterSettings,lower,upper,count,
        exact):
        """
        Method: setSurfaceGeneration(filterClass,lower,upper,count,exact)
        Created: 15.12.2004
        Creator: KP
        Description: Sets the parameters controlling surface generation
        Parameters:
                filterClass Which class to use for surface generation
                lower   Lower limit for surface generation, integer
                upper   Upper limit for surface generation, integer
                count   How many surfaces to genrate, integer
                exact   Flag indicating whether to select only exact values,
                        or ranges
        """
        print "upper=",upper
        self.lowerLimit=lower
        self.upperLimit=upper
        self.surfaceCount=count
        self.filterClass=filterClass
        self.exactValues=exact
        self.filterSettings=filterSettings

    def setSelectedSurface(self,surface):
        """
        Method: setSelectedSurface(surface)
        Created: 15.12.2004
        Creator: KP
        Description: Sets the surface to be generated
        """
        self.surface=surface



    def addInput(self,data,**kws):
        """
        Method: addInput(data,**keywords)
        Created: 03.11.2004
        Creator: KP
        Description: Adds an input for the VSIA filter
        Keywords:
        """

        #note: the settings come through setSurfaceGeneration

#         neenedkwds=["filterClass","filterSettings","lowerLimit","upperLimit",
#         "surfaceCount","exactValues"]
#         for neededkwd in neenedkwds:
#             if not kws.has_key(neededkwd):
#                 raise "No "+neededkwd+" for VSIA specified!"
#
#         self.setSurfaceGeneration(kws["filterClass"],kws["filterSettings"],
#         kws["lowerLimit"],
#              kws["upperLimit"],kws["surfaceCount"],kws["exactValues"])

        Module.addInput(self,data,**kws)

    def getPreview(self,z):
        """
        Method: getPreview(z)
        Created: 03.11.2004
        Creator: KP
        Description: Does a preview calculation for the x-y plane at depth z
        """
        if not self.preview:
            print "Previewing in rendering mode: %d"%self.renderingMode
            self.preview=self.doOperation(not self.renderingMode)
        return self.preview

    def setRenderingMode(self,status):
        """
        Method: setRenderingMode(status)
        Created: 12.1.2005
        Creator: KP
        Description: Sets the rendering mode on/off. If the rendering mode is on
                     then the previewed data will be also processed with the 
                     selected processing module.
        """
        self.renderingMode=status


    def selectPoints(self,preview=1):
        """
        Method: selectPoints()
        Created: 15.12.2004
        Creator: KP
        Description: Selects the points defined by upper and lower limit, 
                     surface count and the exact values flag
        """
        print "We got %d images"%len(self.images)
        if not self.arrays:
            for i in self.images:
                numpyarray,info=self.VTKtoNumpy(i)
                print "Got array with shape ",numpyarray.shape
                self.arrays.append(numpyarray)
                self.infos.append(info)

        self.array=self.arrays[0]

        if len(self.arrays)>1:
            raise "More than one source dataset for Single DataUnit Processing"

        if not self.upperLimit:
            ufunc=greater_equal
            if self.exactValues:
                print "Selecting values equal to ",self.lowerLimit
                ufunc=equal
            else:
                print "Selecting values greater than ",self.lowerLimit
            retdataset=where(ufunc(self.array,self.lowerLimit),self.array,0)

        else:
            start=self.lowerLimit
            diff=(self.upperLimit-self.lowerLimit)/self.surfaceCount
            start+=self.surface*diff
            end=start+diff
            if not self.exactValues:
                print "Selecting values from ",start,"to",end
                retdataset=where(greater_equal(self.array,start),self.array,0)
                retdataset=where(less_equal(retdataset,end),retdataset,0)
            else:
                print "Selecting values ",end
                retdataset=where(equal(self.array,end),self.array,0)

        if not preview:
            # Convert dataset to contain nothing but scalars 255
            print "Converting scalars to 255"
            retdataset=greater(retdataset,0)
            retdataset*=255
        else:
            print "Preview data with scalars 0-255"
        data=self.NumpyToVTK(retdataset,self.infos[0])
        return data



    def doOperation(self,preview=0):
        """
        Method: doOperation
        Created: 10.11.2004
        Creator: KP,JV
        Description: Does visualization of sparse intensity aggregations
                     for the whole dataset
        """
        imagedata=self.selectPoints(preview)
        if preview:
            return imagedata

        geom=vtk.vtkImageDataGeometryFilter()
        geom.SetInput(imagedata)
        geom.Update()
        print "Using filter class",self.filterClass
        if self.filterClass=="vtkGaussianSplatter":
            #parse settings from filterSettings
            self.gaussianRadius=float(self.filterSettings[0])
            return self.doGaussianSplat(imagedata,geom)
        elif self.filterClass=="vtkShepardMethod":
            return self.doShepardMethod(imagedata,geom)
        elif self.filterClass=="vtkSurfaceReconstructionFilter":
            return self.doSurfaceReconstruction(imagedata,geom)
        elif self.filterClass=="vtkDelaunay3D":
            return self.doDelaunay3D(imagedata,geom)

    def doGaussianSplat(self,imagedata,geom):
        """
        Method: doGaussianSplat
        Created: 16.12.2004
        Creator: KP
        Description: Converts a dataset to imagedata using vtkGaussianSplatter
        Parameters:
            imagedata   The original imagedata
            geom        Filter that will produce polydata of the imagedata
        """
        print "Splatting with radius %f..."%self.gaussianRadius
        splatter=vtk.vtkGaussianSplatter()
        splatter.SetInput(geom.GetOutput())
        splatter.SetSampleDimensions(imagedata.GetDimensions())
        if self.gaussianRadius:
            splatter.SetRadius(self.gaussianRadius)
        splatter.Update()
        print "Done"
        return splatter.GetOutput()

    def doShepardMethod(self,imagedata,geom):
        """
        Method: doShepardMethod
        Created: 16.12.2004
        Creator: KP
        Description: Converts a dataset to imagedata using vtkShepardMethod
        Parameters:
            imagedata   The original imagedata
            geom        Filter that will produce polydata of the imagedata
        """
        pass


    def doSurfaceReconstruction(self,imagedata,geom):
        """
        Method: doSurfaceReconstruction
        Created: 16.12.2004
        Creator: KP
        Description: Converts a dataset to imagedata using 
                     vtkSurfaceReconstructionFilter
        Parameters:
            imagedata   The original imagedata
            geom        Filter that will produce polydata of the imagedata
        """
        pass

    def doDelaunay3D(self,imagedata,geom):
        """
        Method: doDelaunay3D
        Created: 16.12.2004
        Creator: KP
        Description: Converts a dataset to imagedata using vtkDelaunay3D
        Parameters:
            imagedata   The original imagedata
            geom        Filter that will produce polydata of the imagedata
        """
        pass

