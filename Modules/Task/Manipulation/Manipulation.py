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
            self.preview=self.doOperation()
            self.extent=None
        return self.zoomDataset(self.preview)


    def doOperation(self):
        """
        Method: doOperation
        Created: 04.04.2006, KP
        Description: Manipulationes the dataset in specified ways
        """
        if not self.modified and self.cached:
            print "Returning cached data"
            return self.cached
        else:
            del self.cached
            self.cached = None
        filterlist = self.settings.get("FilterList")
        data = self.images
        if not filterlist:
            return self.images[0]
        n=len(filterlist)-1
        filterlist=filter(lambda x:x.getEnabled(),filterlist)
        
        
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
                
                data=[data]
                if not data:
                    self.cached = None
                    return None                
        
        data = data[0]
        data.ReleaseDataFlagOff()
        self.cached = data
        return data
