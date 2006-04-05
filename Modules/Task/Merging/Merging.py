# -*- coding: iso-8859-1 -*-
"""
 Unit: Merging
 Project: BioImageXD
 Created: 24.11.2004, JV
 Description:

 Merges two (or more) 8-bit datasets to one 24-bit using classes in the VTK
 library.

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
import lib.Module
from lib.Module import *

class Merging(Module):
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
        settings = dataunit.getSettings()
        if not settings.get("PreviewChannel"):
            Logging.info("Not including ",dataunit,"in merging",kw="processing")
            return
        Module.addInput(self,dataunit,data)

        self.n+=1
        # ugly
        dims=data.GetDimensions()
            
        ctf = settings.get("ColorTransferFunction")
#        Logging.info("ctf=",ctf,kw="processing")
        self.ctfs.append(ctf)
        self.alphaTF=settings.get("AlphaTransferFunction")
        self.alphaMode=settings.get("AlphaMode")
        #print "n=",self.n,"self.settings=",self.settings
        #itf=self.settings.getCounted("IntensityTransferFunction",self.n)
        itf=settings.get("IntensityTransferFunction")
        if not itf:
            Logging.info("Didn't get iTF",kw="processing")
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
            Logging.info("Will create alpha channel, because whole volume requested",kw="processing")
            self.doAlpha=1
        if self.settings.get("ShowOriginal"):
            ret=self.doOperation()      
            self.doAlpha=1
            return ret
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

        Logging.info("Merging channels...",kw="processing")
        processed=[]
        imagelen=len(self.images)
        if not imagelen:
            return None
        self.shift=0
        self.scale=0.333
        self.scale/=imagelen
        
        luminance=0
        self.shift=0.333
        self.scale=0.333
        merge=vtk.vtkImageColorMerge()
        
        if self.doAlpha:
            merge.BuildAlphaOn()
            if self.alphaMode[0]==0:
                Logging.info("Alpha mode = maximum", kw="processing")
                merge.MaximumModeOn()
                
            elif self.alphaMode[0]==1:
                Logging.info("Alpha mode = average, threshold = ",self.alphaMode[1],kw="processing")
                merge.AverageModeOn()
                merge.SetAverageThreshold(self.alphaMode[1])
            else:
                luminance=1
            
        self.shift=0.666
        self.scale=0.333
        
        
        merge.AddObserver("ProgressEvent",self.updateProgress)
        for i,image in enumerate(self.images):
            merge.AddInput(image)
            merge.AddLookupTable(self.ctfs[i])
            print self.ctfs[i]
            merge.AddIntensityTransferFunction(self.intensityTransferFunctions[i])
        merge.Update()
        data=merge.GetOutput()
        
        Logging.info("Result with dims and type",data.GetDimensions(),data.GetScalarTypeAsString(),"components:",data.GetNumberOfScalarComponents())
        print data.GetScalarRange()
        if luminance:
            Logging.info("Alpha mode = luminance", kw="processing")
            lum=vtk.vtkImageLuminance()
            lum.GetOutput().ReleaseDataFlagOn()
            lum.SetInput(data)
            lum.Update()
            alpha=lum.GetOutput()
        
        if self.doAlpha and luminance:
            Logging.info("Appending alpha component", kw="processing")
            #merge.GetOutput().ReleaseDataFlagOn()
            appendcomp=vtk.vtkImageAppendComponents()
            #appendcomp.GetOutput().ReleaseDataFlagOn()
            appendcomp.AddInput(data)
            appendcomp.AddInput(alpha)
            appendcomp.Update()
            data=appendcomp.GetOutput()
            Logging.info("After appending alpha, # of comps=%d",data.GetNumberOfScalarComponents(),kw="processing")

        t3=time.time()
        Logging.info("Merging took %.4f seconds"%(t3-t1),kw="processing")
        messenger.send(None,"update_progress",100,"Done.")
        
        #data.GlobalReleaseDataFlagOn()
        return data

