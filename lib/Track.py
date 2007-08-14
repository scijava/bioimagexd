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

import math
import csv

class Track:
	"""
	Created: 23.11.2006, KP
	Description: A class representing a track
	"""
	def __init__(self):
		self.points = {}
		self.values = {}
		self.mintp, self.maxtp = 0, 0
		self.length = -1

	def __len__(self):
		return len(self.points.keys())
	
	def distance(self, tp1, tp2):
		"""
		Created: 01.07.2007, KP
		Description: return the distance between objects at tp1 and tp2
		"""
		if tp1 not in self.points:
			return 0 #TODO: why 0? this equals to distance(p1, p1) - 14.8.2007 SS
		if tp2 not in self.points:
			return 0
		pt = self.points[tp1]
		pt2 = self.points[tp2]
		dx, dy, dz = pt[0] - pt2[0], pt[1] - pt2[1], pt[2] - pt2[2]
		return math.sqrt(dx * dx + dy * dy + dz * dz)

	def getLength(self):
		"""
		Created: 01.07.2007, KP
		Description: return the length of this track
		"""
		if self.length < 0:
			self.length = 0
			for i in range(self.mintp, self.maxtp):
				self.length += self.distance(i, i + 1)
		return self.length

	def getSpeed(self):
		"""
		Created: 01.07.2007, KP
		Description: return the speed
		"""
		return self.getLength() / (self.maxtp - self.mintp)

	def getDirectionalPersistence(self):
		"""
		Created: 01.07.2007, KP
		Description: return the directional persistence of this track
		"""
		return  self.distance(self.mintp, self.maxtp) / self.getLength()

	def getAverageAngle(self):
		"""
		Created: 01.07.2007, KP
		Description: return the average of the angle differences
		"""
		tot = 0
		n = 0
		for i in range(self.mintp, self.maxtp):
			x1, y1 = self.points[i][0:2]
			x2, y2 = self.points[i + 1][0:2]
			ang = math.atan2(y2 - y1, x2 - x1) * 180.0 / math.pi;
			ang2 = ang
			if ang < 0:
				ang2 = 180 + ang
			tot += ang2
			n += 1
		return tot / float(n)
		
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
		# Set the length to -1 so it will be re-calculated
		self.length = -1


	def getTimeRange(self):
		"""
		Created: 23.11.2006, KP
		Description: Return the range in time this track occupies
		"""
		return self.mintp, self.maxtp
	
	def getObjectAtTime(self, timePoint):
		"""
		Created: 23.11.2006, KP
		Description: Return the object value and position at timepoint t
		"""
		if timePoint not in self.points:
			return - 1, (-1, -1, -1)
		return self.values[timePoint], self.points[timePoint]

class TrackReader:
	"""
	Created: 12.07.2006, KP
	Description: A class for reading tracks from a file
	"""
	def __init__(self, filename = ""):
		"""
		Created: 12.07.2006, KP
		Description: Initialization
		"""
		self.filename = filename
		self.tracks = []
		self.maxLength = -1
		self.reader = None
		self.readFromFile(filename)		   
				
	def readFromFile(self, filename):
		"""
		Created: 12.07.2006, KP
		Description: Return the number of tracks
		""" 
		self.maxLength = -1
		try:
			csvfileObject = open(filename)
			self.reader = csv.reader(csvfileObject, dialect = "excel", delimiter = ";")
		except IOError, ioError:
			print ioError
			self.reader = None
		if self.reader:
			self.tracks = self.readTracks(self.reader)
			self.getMaximumTrackLength()
			
	def getTrack(self, trackNumber, minLength = 3):
		"""
		Created: 20.06.2006, KP
		Description: Method desc
		"""   
		tracks = self.getTracks(minLength)
		print "Tracks with minlength =", minLength, "=", tracks
		return tracks[trackNumber]
		
	def getMaximumTrackLength(self):
		"""
		Created: 12.07.2006, KP
		Description: Return the maximum length of a track
		"""			  
		if self.maxLength <= 0:
			for i in self.tracks:
				trackLength = len(i)
				if trackLength > self.maxLength:
					self.maxLength = trackLength
		
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
		def isLongerThan(trackObject, minimumLength):
			"""
			Created 12.07.2006, KP
			Description: Returns whether trackObjects length is greater than minimumLength
			"""
			return len(trackObject) > minimumLength
		print "number of tracks =", len(self.tracks)
		if not self.tracks:
			return []
		#return filter(lambda trackObject, minLength: isLongerThan(trackObject, minimumLength), self.tracks)
		return [trackObject for trackObject in self.tracks if isLongerThan(trackObject, minLength)]
	
	@staticmethod
	def readTracks(reader):
		"""
		Created: 12.07.2006, KP
		Description: Read tracks from the given file
		"""   
		tracks = []
		ctrack = Track()

		currtrack = -1
		#print "Reading..."
		
		for track, objval, timepoint, xCoordinate, yCoordinate, zCoordinate in reader:
			try:
				tracknum = int(track)
			except ValueError:
				continue
			
			timepoint = int(timepoint)
			objval = int(objval)
			xCoordinate = float(xCoordinate)
			yCoordinate = float(yCoordinate)
			zCoordinate = float(zCoordinate)
			if tracknum != currtrack:
				if ctrack:
					#print "Adding track",ctrack
					tracks.append(ctrack)
					ctrack = Track()			
				currtrack = tracknum
			ctrack.addTrackPoint(timepoint, objval, (xCoordinate, yCoordinate, zCoordinate))
			
		if ctrack not in tracks:
			tracks.append(ctrack)
		return tracks
