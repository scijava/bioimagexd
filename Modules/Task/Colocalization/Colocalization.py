# -*- coding: iso-8859-1 -*-
"""
 Unit: Colocalization.py
 Project: Selli
 Created: 16.11.2004, KP
 Description:

 Creates a colocalization map using the Numeric Python library

 Modified: 03.11.2004 JV - Added comments.
           08.11.2004 KP - The preview is now generated in a single image at the
                           specified depth, and the previewed depth is controlled
                           with vtkImageMapper's SetZSlice()-method
           16.11.2004 KP - Copied the old Colocalization module for reference
           16.11.2004 KP - The calculations are now done using Numeric and the
                           whole image is processed at once
 
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
        self.reset()

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
        self.n=-1
    
    def addInput(self,dataunit,data):
        """
        Method: addInput(data)
        Created: 03.11.2004, KP
        Description: Adds an input for the colocalization filter
        """
        
        Module.addInput(self,dataunit,data)
        settings = dataunit.getSettings()
        th0=settings.get("ColocalizationLowerThreshold")
        th1=settings.get("ColocalizationUpperThreshold")
        self.thresholds.append((th0,th1))
        self.depth = self.settings.get("ColocalizationDepth")
        
 
    def getPreview(self,z):
        """
        Method: getPreview(z)
        Created: 03.11.2004, KP
        Description: Does a preview calculation for the x-y plane at depth z
        """
        if not self.preview:
            self.preview=self.doOperation()
        return self.zoomDataset(self.preview)


    def doOperation(self):
        """
        Method: doOperation
        Created: 10.11.2004, KP
        Description: Does colocalization for the whole dataset
                     using doColocalizationXBit() where X is user defined
        """        
        
        print "Doing ",self.depth,"-bit colocalization"
        t1=time.time()
        self.colocFilter.SetOutputDepth(self.depth)
        for i in range(len(self.images)):
            #print self.thresholds,self.settings
            self.colocFilter.AddInput(self.images[i])
            print "Using %d as lower and %d as upper threshold"%self.thresholds[i]
            self.colocFilter.SetColocalizationLowerThreshold(i,self.thresholds[i][0])
            self.colocFilter.SetColocalizationUpperThreshold(i,self.thresholds[i][1])
        self.colocFilter.Update()
        
        settings = self.dataunits[0].getSettings()
        for i in ["ColocalizationAmount","PearsonsCorrelation","OverlapCoefficient",
        "OverlapCoefficientK1","OverlapCoefficientK2",
        "ColocalizationCoefficientM1","ColocalizationCoefficientM2"]:
            method="self.colocFilter.Get%s()"%i
            #print "%s = "%i,eval(method)
            settings.set(i,eval(method))
        least=self.colocFilter.GetLeastVoxelsOverThreshold()
        settings.set("ColocalizationLeastVoxelsOverThreshold",least)
        t2=time.time()
        #print "Doing colocalization took %f seconds"%(t2-t1)
        return self.colocFilter.GetOutput()
