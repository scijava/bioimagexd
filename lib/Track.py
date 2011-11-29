# -*- coding: iso-8859-1 -*-

"""
 Unit: Track
 Project: BioImageXD
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
import lib.Math
import re
import scripting
import vtk

class Track:
	"""
	A class representing a track
	"""
	def __init__(self):
		self.points = {}
		self.values = {}
		self.fronts = {}
		self.rears = {}
		self.mintp, self.maxtp = 1000, 0
		self.voxelSize = (1.0,1.0,1.0) # In um
		self.timeStamps = [] # Seconds between time points

	def __len__(self):
		return len(self.points)
	
	def distance(self, tp1, tp2, points):
		"""
		return the distance between objects at tp1 and tp2 in um
		"""
		if tp1 not in points:
			return 0
		if tp2 not in points:
			return 0

		pt = list(points[tp1])
		pt2 = list(points[tp2])
		for i,size in enumerate(self.voxelSize):
			pt[i] *= size
			pt2[i] *= size

		dx = pt[0] - pt2[0]
		dy = pt[1] - pt2[1]
		dz = pt[2] - pt2[2]
		return math.sqrt(dx * dx + dy * dy + dz * dz)

	def getLength(self, points = None):
		"""
		return the length of this track in um
		"""
		if points is None:
			points = self.points
		
		length = 0.0
		for i in range(self.mintp, self.maxtp):
			length += self.distance(i, i + 1, points)
		return length

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
		
		return self.distance(self.mintp, self.maxtp, self.points) / self.getLength()

	def getAverageAngle(self):
		"""
		return the average of the angle differences
		"""
		angles = []
		for i in range(self.mintp+2, self.maxtp+1):
			try:
				point1 = list(self.points[i-2])
				point2 = list(self.points[i-1])
				point3 = list(self.points[i])
			except:
				continue

			vec1 = []
			lenVec1 = 0.0
			vec2 = []
			lenVec2 = 0.0
			for i,size in enumerate(self.voxelSize):
				vec1.append((point2[i]-point1[i]) * self.voxelSize[i])
				lenVec1 += vec1[i]**2
				vec2.append((point3[i]-point2[i]) * self.voxelSize[i])
				lenVec2 += vec2[i]**2

			if (lenVec1 == 0 or lenVec2 == 0):
				angles.append(0.0)
				continue

			lenVec1 = math.sqrt(lenVec1)
			lenVec2 = math.sqrt(lenVec2)
			for i in range(len(vec1)):
				vec1[i] /= lenVec1
				vec2[i] /= lenVec2

			angle = lib.Math.angle(vec1,vec2)
			angles.append(angle)

		return lib.Math.meanstdeverr(angles)

	def getFrontCoordinates(self):
		"""
		Return object front coordinates
		"""
		frontPoints = []
		for tp in range(self.mintp, self.maxtp + 1):
			frontPoints.append(self.getFrontCoordinatesAtTime(tp))

		return frontPoints

	def getFrontCoordinatesAtTime(self, tp):
		"""
		Return front coordinates for tp
		"""
		try:
			fPos = self.fronts[tp]
		except:
			fPos = (-1,-1,-1)
		return fPos

	def getRearCoordinates(self):
		"""
		Return object rear coordinates
		"""
		rearPoints = []
		for tp in range(self.mintp, self.maxtp + 1):
			rearPoints.append(self.getRearCoordinatesAtTime(tp))

		return rearPoints

	def getRearCoordinatesAtTime(self, tp):
		"""
		Return rear coordinates for tp
		"""
		try:
			rPos = self.rears[tp]
		except:
			rPos = (-1,-1,-1)
		return rPos

	def getFrontSpeed(self):
		"""
		Calculate and return object front speed
		"""
		return self.getLength(points = self.fronts) / (self.timeStamps[self.maxtp] - self.timeStamps[self.mintp])

	def getRearSpeed(self):
		"""
		Calculate and return object rear speed
		"""
		return self.getLength(points = self.rears) / (self.timeStamps[self.maxtp] - self.timeStamps[self.mintp])
		
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

	def calculateFrontAndRear(self, reader, maxPush, minPush):
		"""
		Method to calculate front and rear of objects in the track
		Image parameter must be vtkImageData
		"""
		spacing = []
		for i in range(len(self.voxelSize)):
			spacing.append(self.voxelSize[i] / self.voxelSize[0])
		
		for tp in range(self.mintp, self.maxtp + 1):
			label = self.values[tp]
			com1 = self.points[tp]

			if tp == self.maxtp: # Use latest direction
				for i in range(len(direction)):
					direction[i] *= -1.0
			else:
				com2 = self.points[tp+1]
				direction = []
				for i in range(len(com1)):
					direction.append(com2[i] - com1[i])

			# Polygon data
			image = reader.getDataSet(tp)
			objThreshold = vtk.vtkImageThreshold()
			objThreshold.SetInput(image)
			objThreshold.SetOutputScalarTypeToUnsignedChar()
			objThreshold.SetInValue(255)
			objThreshold.SetOutValue(0)
			objThreshold.ThresholdBetween(label,label)
			marchingCubes = vtk.vtkMarchingCubes()
			marchingCubes.SetInput(objThreshold.GetOutput())
			marchingCubes.SetValue(0, 255)
			marchingCubes.Update()
			polydata = marchingCubes.GetOutput()
			polydata.Update()

			front = self.locateOutmostPoint(polydata, com1, direction, maxPush, minPush)
			for i in range(len(direction)):
				direction[i] *= -1.0
			rear = self.locateOutmostPoint(polydata, com1, direction, maxPush, minPush)
			for i in range(len(front)):
				front[i] /= spacing[i]
				rear[i] /= spacing[i]
			
			self.fronts[tp] = tuple(front)
			self.rears[tp] = tuple(rear)
		
	def locateOutmostPoint(self, polydata, com, direction, maxPushDistance, minPushDistance):
		"""
		Locates the outmost point of an object depending on the direction parameter.

		A plane is created to clip the data in the direction of the variable
		'direction' until there's a minimum of polygons left. The precision,
		measured in number of polygons, depends on the max and minimum of the push
		distance (specified by maxPushDistance and minPushDistance).

		The remaining polygons' points are processed for an average, which is then
		returned.
		"""
		# Plane setup
		plane = vtk.vtkPlane()
		plane.SetOrigin(com[0], com[1], com[2])
		plane.SetNormal(direction[0], direction[1], direction[2])

		# Clipped data
		clipPolyData = vtk.vtkClipPolyData()
		clipPolyData.SetInput(polydata)
		clipPolyData.SetClipFunction(plane)
		clippedData = clipPolyData.GetOutput()
		clippedData.Update()
		polygons = clippedData.GetNumberOfPolys()

		# Push the plane until it cuts the volume
		pushDistance = maxPushDistance
		while (pushDistance > minPushDistance):
			while (polygons > 0):
				plane.Push(pushDistance)
				clippedData.Update()
				polygons = clippedData.GetNumberOfPolys()
		
			plane.Push(-pushDistance)
			clippedData.Update()
			polygons = clippedData.GetNumberOfPolys()
			pushDistance = pushDistance / 2.0
    
		polyData = clippedData.GetPolys().GetData()
		id = 0
		points = []
		for poly in range(polygons):
			numOfPoints = int(polyData.GetTuple1(id))
			id += 1
			for pid in range(id, id + numOfPoints):
				pointID = polyData.GetTuple1(pid)
				points.append(clippedData.GetPoint(pointID))
				id += 1

		numOfPts = len(points)
		xAvg, yAvg, zAvg = 0.0, 0.0, 0.0
		for point in points:
			xAvg += point[0]
			yAvg += point[1]
			zAvg += point[2]

		xAvg = xAvg/numOfPts
		yAvg = yAvg/numOfPts
		zAvg = zAvg/numOfPts

		return [xAvg, yAvg, zAvg]


class TrackReader:
	"""
	A class for reading tracks from a file
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
