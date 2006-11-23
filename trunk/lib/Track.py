# -*- coding: iso-8859-1 -*-

"""
 Unit: Track
 Project: BioImageXD
 Created: 12.07.2006, KP
 Description:

 A module containing the classes for manipulating tracks
           
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
__author__ = "BioImageXD Project"
__version__ = "$Revision: 1.9 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"


import sys
import csv
import codecs
import struct
import vtk

class Track:
    """
    Created: 23.11.2006, KP
    Description: A class representing a track
    """
    def __init__(self):
        self.points = {}
        self.values = {}
        self.mintp, self.maxtp = 0,0
    
    def __len__(self):
        return len(self.points.keys())
        
    def addTrackPoint(self, timepoint, objval, position):
        """
        Created: 23.11.2006, KP
        Description: add a point to this track
        """
        if timepoint < self.mintp:
            self.mintp = timepoint
        if timepoint > self.maxtp:
            self.maxtp = timepoint
        self.points[timepoint] = position
        self.values[timepoint] = objval
        
    def getTimeRange(self):
        """
        Created: 23.11.2006, KP
        Description: Return the range in time this track occupies
        """
        return self.mintp, self.maxtp
    
    def getObjectAtTime(self, t):
        """
        Created: 23.11.2006, KP
        Description: Return the object value and position at timepoint t
        """
        if t not in self.points:
            return -1,(-1,-1,-1)
        return self.values[t],self.points[t]

class TrackReader:
    """
    Created: 12.07.2006, KP
    Description: A class for reading tracks from a file
    """
    def __init__(self,filename=""):
        """
        Created: 12.07.2006, KP
        Description: Initialization
        """
        self.filename = filename
        self.maxLength = -1
        self.readFromFile(filename)        
        
    def readFromFile(self,filename):
        """
        Created: 12.07.2006, KP
        Description: Return the number of tracks
        """ 
        self.maxLength = -1        
        try:
            self.reader = csv.reader(open(filename), dialect="excel",delimiter=";")            
        except:
            self.reader = None
            self.tracks = []
        if self.reader:
            self.tracks = self.readTracks(self.reader)
            self.getMaximumTrackLength()
            
    def getTrack(self, n, minLength = 3):
        """
        Created: 20.06.2006, KP
        Description: Method desc
        """   
        tracks = self.getTracks(minLength)
        print "Tracks with minlength=",minLength,"=",tracks
        return tracks[n]
        
    def getMaximumTrackLength(self):
        """
        Created: 12.07.2006, KP
        Description: Return the maximum length of a track
        """           
        if self.maxLength<=0:
            for i in self.tracks:
                n = len(i)
                if n>self.maxLength:self.maxLength = n
        return self.maxLength
        
        
    def getNumberOfTracks(self, minLength = 3):
        """
        Created: 12.07.2006, KP
        Description: Return the number of tracks
        """           
        return len(self.getTracks(minLength))
        
    def getTracks(self, minLength = 3):
        """
        Created: 12.07.2006, KP
        Description: Return the tracks with length >= minLength
        """   
        def f(x,y):
            return len(x)>y
        print "number of tracks=",len(self.tracks)
        if not self.tracks:
            return []
        return filter(lambda x, m = minLength:f(x,m), self.tracks)
            
    def readTracks(self, reader):
        """
        Created: 12.07.2006, KP
        Description: Read tracks from the given file
        """   
        tracks=[]
        ctrack=Track()
        
        currtrack=-1
        print "Reading..."
        
        for track, objval,timepoint, x,y,z in reader:
            try:
                tracknum=int(track)
            except:
                continue
            
            timepoint = int(timepoint)
            objval = int(objval)
            x = float(x)
            y = float(y)
            z = float(z)
            if tracknum != currtrack:
                if ctrack:
                    #print "Adding track",ctrack
                    tracks.append(ctrack)
                    ctrack=Track()          
                currtrack = tracknum
            ctrack.addTrackPoint(timepoint, objval, (x,y,z))
            
        if ctrack and not tracks:
            tracks.append(ctrack)
        return tracks
