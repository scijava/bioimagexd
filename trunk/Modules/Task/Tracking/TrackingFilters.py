#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: TrackingFilters
 Project: BioImageXD
 Created: 13.04.2006, KP
 Description:

 A module containing filters used in the tracking task
                            
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
__version__ = "$Revision: 1.42 $"
__date__ = "$Date: 2005/01/13 14:52:39 $"

import wx
import types
import os,os.path
import vtk
import Command
import re
try:
    import itk
except:
    pass
import messenger
import scripting as bxd

from lib import ProcessingFilter
import GUI.GUIBuilder as GUIBuilder
import ImageOperations

import Particle

from lib import Track

import messenger

def getFilterList():
    return [CreateTracksFilter]
            
TRACKING="Tracking"



class CreateTracksFilter(ProcessingFilter.ProcessingFilter):
    """
    Created: 13.04.2006, KP
    Description: A filter for shifting the values of dataset by constant and scaling by a constant
    """     
    name = "Create Tracks"
    category = TRACKING
    
    def __init__(self):
        """
        Created: 13.04.2006, KP
        Description: Initialization
        """        
        self.tracks = []
        self.track = None
        self.tracker = None

        ProcessingFilter.ProcessingFilter.__init__(self,(1,1))
        
        self.descs={
            "MaxVelocity":"Maximum change in distance)",
            "MaxSizeChange":"Maximum size change (% of size)",
            "MaxDirectionChange":"Direction (angle of the allowed sector in degrees)",
            "MaxIntensityChange":"Maximum change of average intensity (% of max. diff.)",
            "MinLength":"Minimum length of track (timepoints)",
            "MinSize":"Minimum size of tracked objects",
            "TrackFile":"First file of track",
            "SizeWeight":"","DirectionWeight":"","IntensityWeight":"",
            "ResultsFile":"File containing the tracking results",
            "Track":"Track to visualize"}
    
        self.numberOfPoints = None
        
        self.particleFileBase = ""
    def setParameter(self,parameter,value):
        """
        Created: 13.04.2006, KP
        Description: Set a value for the parameter
        """    
        ProcessingFilter.ProcessingFilter.setParameter(self, parameter, value)
        if parameter == "TrackFile":
            parts = value.split("_")
            self.particleFileBase = "_".join(parts[:-1])
        elif parameter == "ResultsFile" and os.path.exists(value):
            self.track = Track.Track(value)
            self.tracks = self.track.getTracks(self.parameters["MinLength"])
            print "Read %d tracks"%(len(self.tracks))
            messenger.send(self,"update_Track")
            if self.parameters.has_key("Track"):
                messenger.send(None,"visualize_tracks",self.tracks,self.parameters["Track"])
        elif parameter == "Track":
            if self.tracks:
                messenger.send(None,"visualize_tracks",self.tracks,self.parameters["Track"])            
        if parameter=="MinLength":
            messenger.send(self,"update_Track")
    
    def getParameters(self):
        """
        Created: 14.08.2006, KP
        Description: Return the list of parameters needed for configuring this GUI
        """            
        return [["Change between consecutive objects",("MaxVelocity","MaxSizeChange","MaxIntensityChange", "MaxDirectionChange")],
        ["Tracking",("MinLength","MinSize")],
        ["Load track",(("TrackFile","Select track file to load","*.csv"),)],
        ["Tracking Results",(("ResultsFile","Select track file that contains the results","*.csv"),)],
        ["Visualization",("Track",)]]
        
    def getDesc(self,parameter):
        """
        Created: 14.08.2006, KP
        Description: Return the description of the parameter
        """    
        return self.descs[parameter]
        
    def getLongDesc(self,parameter):
        """
        Created: 14.08.2006, KP
        Description: Return a long description of the parameter
        """ 
        return ""
        
        
    def getType(self,parameter):
        """
        Created: 14.08.2006, KP
        Description: Return the type of the parameter
        """    
        if parameter == "UseSize":
            return types.BooleanType
        elif parameter in ["MaxVelocity","MaxSizeChange","MinLength","MinSize"]:
            return GUIBuilder.SPINCTRL
        elif parameter in ["SizeWeight","DirectionWeight","IntensityWeight","MaxDirectionChange","MaxIntensityChange","MaxSizeChange"]:
            return GUIBuilder.SPINCTRL
        if parameter=="Track":return GUIBuilder.SLICE            
        return GUIBuilder.FILENAME
        
    def getRange(self,parameter):
        """
        Created: 14.08.2006, KP
        Description: Return the range of given parameter
        """             
        if parameter in ["MaxVelocity","MinSize"]:
            return (0,999)
        if parameter=="MaxSizeChange":
            return (0,100)
        if parameter=="Track":
            if self.track:
                minlength = self.parameters["MinLength"]
                return 0,self.track.getNumberOfTracks(minlength)            
        if parameter=="MinLength":
            if self.numberOfPoints:
                return 0,self.numberOfPoints
            return 0,1
        if parameter=="MaxDirectionChange":
            return (0,360)
        return (0,100)
                
    def getDefaultValue(self,parameter):
        """
        Created: 14.08.2006, KP
        Description: Return the default value of a parameter
        """     
        if parameter=="UseSize":
            return 1
        if parameter=="MinSize":
            return 6
        if parameter=="MaxVelocity":
            return 30
        if parameter=="MaxSizeChange":
            return 30
        if parameter=="MinLength":
            return 3
        if parameter in ["IntensityWeight","SizeWeight","DirectionWeight"]:
            return 33
        if parameter == "MaxDirectionChange":
            return 45
        if parameter == "MaxIntensityChange":
            return 10
        if parameter == "MaxSizeChange":
            return 25
        if parameter=="Track":return 0            
        if parameter == "ResultsFile":
            return "track_results.csv"
        return "tracks.csv"
        
    def execute(self,inputs,update=0,last=0):
        """
        Created: 14.08.2006, KP
        Description: Execute the filter with given inputs and return the output
        """            
        if not ProcessingFilter.ProcessingFilter.execute(self,inputs):
            return None
        
        image = self.getInput(1)
        #print "Using ",image
        #self.vtkfilter.SetInput(image)
        
        if not self.tracker:
            self.tracker = Particle.ParticleTracker()
        try:
            self.tracker.setFilterObjectSize(self.parameters["MinSize"])
            
            self.tracker.readFromFile(self.particleFileBase)        
            self.tracker.setMinimumTrackLength(self.parameters["MinLength"])
            self.tracker.setDistanceChange(self.parameters["MaxVelocity"]/100.0)
            self.tracker.setSizeChange(self.parameters["MaxSizeChange"]/100.0)
            self.tracker.setIntensityChange(self.parameters["MaxIntensityChange"]/100.0)
            self.tracker.setAngleChange(self.parameters["MaxDirectionChange"])
            
            self.tracker.track()
            self.tracker.writeTracks(self.parameters["ResultsFile"])
        except:
            pass
            
        return image
        
