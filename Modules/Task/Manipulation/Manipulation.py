# -*- coding: iso-8859-1 -*-
"""
 Unit: Manipulation
 Project: BioImageXD
 Created: 04.04.2006, KP
 
 Description:
 A module for various data manipulation purposes

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
__version__ = "$Revision: 1.13 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"


import vtk
import time
import Logging
import lib.Module
from lib.Module import *

class Manipulation(Module):
    """
    Class: Manipulation
    Created: 04.04.2006, KP
    Description: Manipulationes a single dataunit in specified ways
    """

    def __init__(self,**kws):
        """
        Method: __init__(**keywords)
        Created: 25.11.2004, KP
        Description: Initialization
        """
        Module.__init__(self,**kws)

        # TODO: remove attributes that already exist in base class!
        self.images=[]
        self.cachedTimepoint = -1
        self.x,self.y,self.z=0,0,0
        self.extent=None
        self.running=0
        self.cached = None
        self.depth=8
        self.modified = 0

        self.reset()
        
    def setModified(self,flag):
        """
        Method: setModified
        Created: 14.05.2006
        Description: Set a flag indicating whether filter parameters have changed
        """
        self.modified = flag

    def reset(self):
        """
        Method: reset()
        Created: 25.11.2004, KP
        Description: Resets the module to initial state. This method is
                     used mainly when doing previews, when the parameters
                     that control the colocalization are changed and the
                     preview data becomes invalid.
        """
        Module.reset(self)
        self.preview=None
        self.extent=None
        self.n=-1

    def addInput(self,dataunit,data):
        """
        Method: addInput(data)
        Created: 04.04.2006, KP
        Description: Adds an input for the single dataunit Manipulationing filter
        """
        Module.addInput(self,dataunit,data)
        settings = dataunit.getSettings()


    def getPreview(self,z):
        """
        Method: getPreview(z)
        Created: 04.04.2006, KP
        Description: Does a preview calculation for the x-y plane at depth z
        """
        if self.settings.get("ShowOriginal"):
            return self.images[0]        
        if not self.preview:
            dims=self.images[0].GetDimensions()
            if z>=0:
                self.extent=(0,dims[0]-1,0,dims[1]-1,z,z)
            else:
                self.extent=None
            self.preview=self.doOperation(preview=1)
            self.extent=None
        return self.zoomDataset(self.preview)


    def doOperation(self,preview=0):
        """
        Method: doOperation
        Created: 04.04.2006, KP
        Description: Manipulationes the dataset in specified ways
        """
        
        if preview and not self.modified and self.cached and self.timepoint == self.cachedTimepoint:
            print "\n\n***** Returning cached data, timepoint=",self.timepoint,"cached timepoint=",self.cachedTimepoint,"\n\n******"
            return self.cached
        else:
            del self.cached
            self.cached = None
        filterlist = self.settings.get("FilterList")
        print "Filters in filterlist=",filterlist
        
        if type(filterlist)==type(""):
            filterlist=[]
        self.settings.set("FilterList",filterlist)
        data = self.images
        if not filterlist:
            return self.images[0]
        filterlist=filter(lambda x:x.getEnabled(),filterlist)
        n=len(filterlist)-1
        
        lastfilter = None
        lasttype = "UC3"
        for i,currfilter in enumerate(filterlist):
                flag=(i==n)
                if i>0:
                    currfilter.setPrevFilter(filterlist[i-1])
                else:
                    currfilter.setPrevFilter(None)
                if not flag:
                    currfilter.setNextFilter(filterlist[i+1])
                else:
                    currfilter.setNextFilter(None)
                data = currfilter.execute(data,update=flag,last=flag)
                lastfilter = currfilter
                
                if not preview:
                    currfilter.writeOutput(self.controlUnit, self.timepoint)
                lasttype = currfilter.getImageType()
                
                
                data=[data]
                if not data:
                    print "GOT NO DATA"
                    self.cached = None
                    return None                
        
        data = data[0]
        if data.__class__ != vtk.vtkImageData:
            
            data = lastfilter.convertITKtoVTK(data,imagetype=lasttype)

        data.ReleaseDataFlagOff()
        #self.cached = data
        #self.cachedTimepoint = self.timepoint
        self.modified = 0
        return data
