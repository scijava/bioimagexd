# -*- coding: iso-8859-1 -*-

"""
 Unit: FilterBasedTaskSettings
 Project: BioImageXD
 Created: 26.03.2005, KP
 Description:

 This is a base class for all tasks that are based on the notion of a list of filters

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
__version__ = "$Revision: 1.21 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import vtk
from DataUnitSetting import DataUnitSettings
#import ManipulationFilters

class FilterBasedTaskSettings(DataUnitSettings):
    """
    Created: 27.03.2005, KP
    Description: Stores settings related to single unit Manipulationing
    """
    def __init__(self,n=-1):
        """
        Method: __init__
        Created: 27.03.2005, KP
        Description: Constructor
        """
        DataUnitSettings.__init__(self,n)
        self.set("Type","No Type Set")
        
        self.registerPrivate("ColorTransferFunction",1)        
        self.registerCounted("Source")
        self.register("FilterList", serialize = 1)
        self.register("VoxelSize")
        self.register("Spacing")
        #self.register("Origin")
        self.register("Dimensions")
        self.register("Type")
        self.register("Name")
        self.register("BitDepth")
        
    def initialize(self,dataunit,channels, timepoints):
        """
        Method: initialize(dataunit,channels, timepoints)
        Created: 27.03.2005
        Description: Set initial values for settings based on 
                     number of channels and timepoints
        """
        DataUnitSettings.initialize(self,dataunit,channels,timepoints)
        if hasattr(dataunit,"getScalarRange"):
            minval,maxval = dataunit.getScalarRange()
        else:
            minval,maxval = dataunit.getSourceDataUnits()[0].getScalarRange()
        ctf = vtk.vtkColorTransferFunction()
        ctf.AddRGBPoint(minval,0,0,0)
        ctf.AddRGBPoint(maxval, 1.0, 1.0, 1.0)
        self.set("ColorTransferFunction",ctf)

        
    def writeTo(self,parser):
        """
        Created: 05.06.2005
        Description: Attempt to write all keys to a parser
        """    
        DataUnitSettings.writeTo(self, parser)
        lst = self.get("FilterList")
        print "Filter list to write=",lst
        flist = eval(self.serialize("FilterList",lst))
        print "Got serialized=",flist
        for i,fname in enumerate(flist):
            currfilter = lst[i]
            keys = currfilter.getPlainParameters()
            for key in keys:
                if not parser.has_section(fname):
                    parser.add_section(fname)
                print "writing ",key,"to",fname
                parser.set(fname,key,currfilter.getParameter(key))

    def deserialize(self,name,value):
        """
        Created: 05.06.2005
        Description: Returns the value of a given key
        """
        if name=="FilterList":
            fnames = eval(value)
            flist=[]
            filters = self.filterModule.getFilterList()
            nametof={}
            for f in filters:
                nametof[f.getName()] = f
            for name in fnames:
                fclass = nametof[name]
                flist.append(fclass)
            return flist
                
        else:
            return DataUnitSettings.deserialize(self, name, value)
        
        
    def serialize(self,name,value):
        """
        Created: 05.06.2005
        Description: Returns the value of a given key in a format
                     that can be written to disk.
        """
        if name=="FilterList":
            print "Serializing",value
            filterlist = value
            names=[]
            for filter in filterlist:
                names.append(filter.getName())
            return str(names)
        else:
            return DataUnitSettings.serialize(self,name,value)
