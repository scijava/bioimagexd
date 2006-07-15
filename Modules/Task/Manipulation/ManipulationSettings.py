# -*- coding: iso-8859-1 -*-

"""
 Unit: ManipulationSetting
 Project: BioImageXD
 Created: 26.03.2005, KP
 Description:

 This is a class that holds all settings of a dataunit. A dataunit's 
 setting object is the only thing differentiating it from another
 dataunit.
 
 This code was re-written for clarity. The code produced by the
 Selli-project was used as a starting point for producing this code.
 http://sovellusprojektit.it.jyu.fi/selli/ 

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
from DataUnit import DataUnitSettings
import ManipulationFilters

class ManipulationSettings(DataUnitSettings):
    """
    Class: ManipulationSettings
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
        self.set("Type","Process")
        
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
        ctf = vtk.vtkColorTransferFunction()
        ctf.AddRGBPoint(0,0,0,0)
        ctf.AddRGBPoint(255, 1.0, 1.0, 1.0)
        self.set("ColorTransferFunction",ctf)
        
    def initialize(self,dataunit,channels, timepoints):
        """
        Method: initialize(dataunit,channels, timepoints)
        Created: 27.03.2005
        Description: Set initial values for settings based on 
                     number of channels and timepoints
        """
        DataUnitSettings.initialize(self,dataunit,channels,timepoints)
        ctf = self.get("ColorTransferFunction")
        
    def writeTo(self,parser):
        """
        Method: writeTo(parser)
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
        Method: deserialize(name,value)
        Created: 05.06.2005
        Description: Returns the value of a given key
        """
        if name=="FilterList":
            fnames = eval(value)
            flist=[]
            filters = ManipulationFilters.getFilterList()
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
        Method: serialize(name,value)
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
