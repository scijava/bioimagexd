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
import os
import lib.Particle
import lib.Math
import re
import scripting

class Track:
	"""
	Created: 23.11.2006, KP
	Description: A class representing a track
	"""
	def __init__(self):
		self.points = {}
		self.values = {}
		self.mintp, self.maxtp = 1000, 0
		self.length = -1
		self.voxelSize = (1.0,1.0,1.0) # In um
		self.timeStamps = [] # Seconds between time points

	def __len__(self):
		return len(self.points)
	
	def distance(self, tp1, tp2):
		"""
		return the distance between objects at tp1 and tp2 in um
		"""
		if tp1 not in self.points:
			return 0
		if tp2 not in self.points:
			return 0

		pt = list(self.points[tp1])
		pt2 = list(self.points[tp2])
		for i,size in enumerate(self.voxelSize):
			pt[i] *= size
			pt2[i] *= size

		dx = pt[0] - pt2[0]
		dy = pt[1] - pt2[1]
		dz = pt[2] - pt2[2]
		return math.sqrt(dx * dx + dy * dy + dz * dz)

	def getLength(self):
		"""
		return the length of this track in um
		"""
		if self.length < 0:
			self.length = 0.0
			for i in range(self.mintp, self.maxtp):
				self.length += self.distance(i, i + 1)
		return self.length

	def getSpeed(self):
		"""
		return the speed in um/s
		"""
		return self.getLength() / (self.timeStamps[self.maxtp] - self.timeStamps[self.mintp])

	def getDirectionalPersistence(self):
		"""
		return the directional persistence of this track
		"""
		length = self.getLength()
		if length == 0.0:
			return 1.0
		
		return self.distance(self.mintp, self.maxtp) / self.getLength()

	def getAverageAngle(self):
		"""
		return the average of the angle differences
		"""
		angles = []
		for i in range(self.mintp, self.maxtp):
			vec1 = list(self.points[i])
			vec2 = list(self.points[i + 1])
			# Create unit vectors in real space
			lenVec1 = 0.0
			lenVec2 = 0.0
			for i,size in enumerate(self.voxelSize):
				vec1[i] *= self.voxelSize[i]
				vec2[i] *= self.voxelSize[i]
				lenVec1 += vec1[i]
				lenVec2 += vec2[i]

			for i in range(3):
				vec1[i] /= lenVec1
				vec2[i] /= lenVec2

			angle = lib.Particle.ParticleTracker.angle(vec1,vec2)
			angles.append(angle)

		return lib.Math.meanstdeverr(angles)
		
	def addTrackPoint(self, timepoint, objval, position):
		"""
		add a point to this track
		"""
		if not objval: # Return if object is none particle
			return
		
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
		Return the range in time this track occupies
		"""
		return self.mintp, self.maxtp
	
	def getObjectAtTime(self, timePoint):
		"""
		Return the object value and position at timepoint t
		"""
		if timePoint not in self.points:
			return -1, (-1, -1, -1)
		return self.values[timePoint], self.points[timePoint]

	def getNumberOfTimepoints(self):
		"""
		Return the number of timepoints in this track
		"""
		return self.maxtp - self.mintp + 1

	def setTimeStamps(self, timestamps):
		"""
		Set the interval of time points
		"""
		self.timeStamps = timestamps

	def setVoxelSize(self, voxelSize):
		"""
		Set the voxel size of the image, needed for distance and angle calculations.
		"""
		if len(voxelSize) == 3:
			self.voxelSize = voxelSize


class TrackReader:
	"""
	Created: 12.07.2006, KP
	Description: A class for reading tracks from a file
	"""
	def __init__(self, filename = ""):
		"""
		Initialization
		"""
		self.filename = filename
		self.tracks = []
		self.maxLength = -1
		self.reader = None
		if os.path.exists(filename):
			self.readFromFile(filename)		   
				
	def readFromFile(self, filename):
		"""
		Return the number of tracks
		""" 
		self.maxLength = -1
		try:
			csvfileObject = open(filename)
			self.reader = csv.reader(csvfileObject, dialect = "excel", delimiter = ";")
			self.parser = scripting.MyConfigParser()
			ext = filename.split(".")[-1]
			pat = re.compile('.%s'%ext)
			iniFilename = pat.sub('.ini',filename)
			self.parser.read([iniFilename])
			
		except IOError, ioError:
			print ioError
			self.reader = None
			self.parser = None
		if self.reader and self.parser:
			self.tracks = self.readTracks(self.reader)
			try:
				timeStamps = eval(self.parser.get("TimeStamps", "TimeStamps"))
				voxelSize = eval(self.parser.get("VoxelSize", "VoxelSize"))
				for i in range(len(voxelSize)):
					voxelSize[i] *= 1000000.0

				for track in self.tracks:
					track.setVoxelSize(voxelSize)
					track.setTimeStamps(timeStamps)
			except:
				pass
			
			self.getMaximumTrackLength()
			
	def getTrack(self, trackNumber, minLength = 3):
		"""
		Method desc
		"""   
		tracks = self.getTracks(minLength)
		print "Tracks with minlength =", minLength, "=", tracks
		return tracks[trackNumber]
		
	def getMaximumTrackLength(self):
		"""
		Return the maximum length of a track
		"""			  
		if self.maxLength <= 0:
			for track in self.tracks:
				trackLength = len(track)
				if trackLength > self.maxLength:
					self.maxLength = trackLength
		
		return self.maxLength
		
	def getNumberOfTracks(self, minLength = 3):
		"""
		Return the number of tracks
		"""			  
		return len(self.getTracks(minLength))
		
	def getTracks(self, minLength = 3):
		"""
		Return the tracks with length >= minLength
		"""
		def isLongerThanOrEqual(trackObject, minimumLength):
			"""
			Created 12.07.2006, KP
			Returns whether trackObjects length is greater than minimumLength
			"""
			return len(trackObject) >= minimumLength
		
		if not self.tracks:
			return []
		
		return [trackObject for trackObject in self.tracks if isLongerThanOrEqual(trackObject, minLength)]

	@staticmethod
	def readTracks(reader):
		"""
		Read tracks from the given file
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
			try:
				objval = int(objval)
				xCoordinate = float(xCoordinate)
				yCoordinate = float(yCoordinate)
				zCoordinate = float(zCoordinate)
			except: # None particle
				objval = None
				xCoordinate = None
				yCoordinate = None
				zCoordinate = None
			
			if tracknum != currtrack:
				if ctrack:
					#print "Adding track", ctrack
					tracks.append(ctrack)
					ctrack = Track()			
				currtrack = tracknum
			ctrack.addTrackPoint(timepoint, objval, (xCoordinate, yCoordinate, zCoordinate))
			
		if ctrack not in tracks:
			tracks.append(ctrack)
		return tracks
