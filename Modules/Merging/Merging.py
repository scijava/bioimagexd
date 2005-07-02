# -*- coding: iso-8859-1 -*-
"""
 Unit: ColorMerging.py
 Project: Selli
 Created: 24.11.2004, JV
 Description:

 Merges two (or more) 8-bit datasets to one 24-bit using classes in the VTK
 library.

 Modified:
        03.12.2004 JV - Changed ColorMergingNumpy to ColorMerging
        10.12.2004 JV - Does not do intensity mapping if function is identical

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
__version__ = "$Revision: 1.18 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"


import vtk
import time
from Module import *

class ColorMerging(Module):
    """
    Class: ColorMerging
    Created: 24.11.2004, JV
    Description: Merges two or more datasets to one
    """
    def __init__(self,**kws):
        """
        Method: __init__(**keywords)
        Created: 24.11.2004, JV
        Description: Initialization
        """
        Module.__init__(self,**kws)
        self.doAlpha=1
        self.extent=[]
        self.thresholds=[]
        self.running=False

        self.reset()

    def reset(self):
        """
        Method: reset()
        Created: 24.11.2004, JV
        Description: Resets the module to initial state. This method is
                     used mainly when doing previews, when the parameters
                     that control the colocalization are changed and the
                     preview data becomes invalid.
        """
        Module.reset(self)
        self.preview=None

        self.infos=[]
        self.intensityTransferFunctions = []
        self.ctfs=[]
        self.alphaMode=[0,0]
        self.n=-1
        

    def addInput(self,dataunit,data):
        """
        Method: addInput(dataunit,data)
        Created: 24.11.2004, JV
        Description: Adds an input for the color merging filter
        """
        Module.addInput(self,dataunit,data)

        self.n+=1
        # ugly
        dims=data.GetDimensions()
        settings = dataunit.getSettings()
        #rgb=self.settings.getCounted("Color",self.n)
        ctf = settings.get("MergingColorTransferFunction")
        self.ctfs.append(ctf)
        self.alphaTF=settings.get("AlphaTransferFunction")
        self.alphaMode=settings.get("AlphaMode")
        #print "n=",self.n,"self.settings=",self.settings
        #itf=self.settings.getCounted("IntensityTransferFunction",self.n)
        itf=settings.get("IntensityTransferFunction")
        if not itf:
            print "Didn't get itf"
        self.intensityTransferFunctions.append(itf)


    def getPreview(self,z):
        """
        Method: getPreview(z)
        Created: 24.11.2004, JV
        Description: Does a preview calculation for the x-y plane at depth z
        """
        if z!=-1:
            self.doAlpha=0
        else: # If the whole volume is requested, then we will also do alpha
            print "Will do alpha as whole volume was requested"
            self.doAlpha=1
        if not self.preview:
            self.preview=self.doOperation()
        self.doAlpha=1
        return self.preview

    def doOperation(self):
        """
        Method: doOperation
        Created: 24.11.2004, JV
        Description: Does color merging for the whole dataset
                     using doColorMergingXBit() where X is user defined
        """
        t1=time.time()
        datasets=[]
        alphas=[]

        # Map scalars with intensity transfer list

        print "\nDOING COLORMERGING\n"
        processed=[]
        imagelen=len(self.images)
        #print "Mapping through intensities..."
        for i in range(0,imagelen):
            #self.images[i].GlobalReleaseDataFlagOn()
            mapIntensities=vtk.vtkImageMapToIntensities()
            mapIntensities.SetIntensityTransferFunction(self.intensityTransferFunctions[i])
            mapIntensities.SetInput(self.images[i])
            mapIntensities.Update()
            data=mapIntensities.GetOutput()
            processed.append(data)
        #print "Mapped %d datasets"%len(processed)
        
        luminance=0
        if self.doAlpha:
            #print "Creating alpha..."
            createalpha=vtk.vtkImageAlphaFilter()
            #print "self.alpaMode=",self.alphaMode
            if self.alphaMode[0]==0:
                print "Maximum mode"
                createalpha.MaximumModeOn()
            elif self.alphaMode[0]==1:
                print "Average mode, threshold=",self.alphaMode[1]
                createalpha.AverageModeOn()
                createalpha.SetAverageThreshold(self.alphaMode[1])
            else:
                luminance=1
            
            if not luminance:
                for i in processed:
                    createalpha.AddInput(i)
                createalpha.Update()
                alpha=createalpha.GetOutput()
                #print "alpha=",alpha
                #print "Created alpha with dims and datatype:",alpha.GetDimensions(),alpha.GetScalarTypeAsString()
        
        # Color the datasets to 24-bit datasets using VTK classes            
        
        colored=[]
        for i in range(0,imagelen):
            if processed[i].GetNumberOfScalarComponents()==1:
                #print "Mapping through..."
                mapToColors=vtk.vtkImageMapToColors()
                mapToColors.SetOutputFormatToRGB()
                ct=self.ctfs[i]
                mapToColors.SetLookupTable(ct)
                mapToColors.SetInput(processed[i])
                mapToColors.Update()
                colored.append(mapToColors.GetOutput())
            else:
                print "Dataset %d is RGB Data, will not map through ctf"%i
                colored.append(processed[i])
        # result rgb
        #print "Mapped %d datasets"%len(colored)
        #print "Merging..."
        merge=vtk.vtkImageMerge()
        for i in colored:
            merge.AddInput(i)
        merge.Update()
        data=merge.GetOutput()
        
        print "Result with dims and type",data.GetDimensions(),data.GetScalarTypeAsString(),"components:",data.GetNumberOfScalarComponents()

        if luminance:
            print "Using vtkImageLuminance"
            lum=vtk.vtkImageLuminance()
            lum.SetInput(data)
            lum.Update()
            alpha=lum.GetOutput()
        
        if self.doAlpha:
            print "appending alpha..."
            appendcomp=vtk.vtkImageAppendComponents()
            appendcomp.AddInput(data)
            appendcomp.AddInput(alpha)
            appendcomp.Update()
            data=appendcomp.GetOutput()
            print "After appending alpha, num of Comps:",data.GetNumberOfScalarComponents()

        t3=time.time()
        print "Calculations took %f seconds"%(t3-t1)
        
        #data.GlobalReleaseDataFlagOn()
        return data

