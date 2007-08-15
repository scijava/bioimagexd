#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: Particle
 Project: BioImageXD
 Created: 13.04.2006, KP
 Description:

 A module containing classes for manipulating the tracked particles
							
 Copyright (C) 2005  BioImageXD Project
 See CREDITS.txt for details

 This program is free software; you can redistribute it and / or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program; if not, write to the Free Software
 Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111 - 1307  USA

"""
__author__ = "BioImageXD Project < http://www.bioimagexd.org/>"
__version__ = "$Revision: 1.42 $"
__date__ = "$Date: 2005 / 01 / 13 14:52:39 $"

import os, os.path
import csv
import sys
import math
import codecs
import copy
try:
	import psyco
except ImportError:
	psyco = None

class ParticleReader:
	"""
	Created: KP
	Description: A class for reading all particle definitions from .CSV files created by the
				 segmentation code
	"""
	def __init__(self, filename, filterObjectSize = 2):
		"""
		Created: KP
		Description: Initialize the reader and necessary information for the reader
		"""
		self.rdr = csv.reader(open(filename), dialect = "excel", delimiter = ";")
		self.filterObjectSize = filterObjectSize
		self.timepoint = -1  
		self.volumes = []
		self.cogs = []
		self.avgints = []
		self.objects = []
		
	def getObjects(self):
		"""
		Created: 25.11.2006, KP
		Description: Return the list of object "intensity" values
		"""
		return self.objects
	
	def getVolumes(self):
		"""
		Created: 25.11.2006, KP
		Description: return a list of the object volumes (sorted)
		"""
		return self.volumes

	def getCentersOfMass(self):
		"""
		Created: 25.11.2006, KP
		Description: return a list of the mass centers of the objects (sorted)
		"""
		return self.cogs
		
	def getAverageIntensities(self):
		"""
		Created: 25.11.2006, KP
		Description: return a list of the avereage intensities of the objects (sorted)
		"""
		return self.avgints		
		
	def read(self, statsTimepoint  = 0):
		"""
		Created: KP
		Description: Read the particles from the filename and create corresponding instances of Particle class
		"""
		
		ret = []
		#([str(i),str(volumeum),str(volume),str(cog),str(umcog),str(avgint)])		 
		skipNext = 0
		curr = []
		for line in self.rdr:
			if skipNext:
				skipNext = 0
				continue
			if len(line) == 1:
				timePoint = int(line[0].split(" ")[1])
				#print "Current timepoint = ", timePoint
				if curr:
					ret.append(curr) #TODO: the last line is ignored as in TrackReader
				curr = []
				self.timepoint = timePoint
				skipNext = 1
				continue
			else:
				obj, sizemicro, size, cog, umcog, avgint = line
			try:
				size = int(size)
				sizemicro = float(sizemicro)
			except ValueError:
				continue
			obj = int(obj)
			#cog = map(float, cog[1:-1].split(", "))
			cog = [float(coordinate) for coordinate in cog[1:-1].split(", ")]
			#cog = eval(cog)
			umcog = [float(coordinate) for coordinate in umcog[1:-1].split(", ")]
			#umcog = map(float, umcog[1:-1].split(", "))
			#umcog = eval(umcog)
			avgint = float(avgint)			  
			if size >= self.filterObjectSize and obj != 0: #TODO: why is obj == 0 not accepted?
				particle = Particle(umcog, cog, self.timepoint, size, avgint, obj)
				curr.append(particle)
			if self.timepoint == statsTimepoint:
				self.objects.append(obj)
				self.cogs.append((int(cog[0]), int(cog[1]), int(cog[2])))
				self.volumes.append((size, sizemicro))
				self.avgints.append(avgint)
		if curr: ret.append(curr)
		return ret

class Particle:
	"""
	Created: KP
	Description: A class representing a particle. Stores all relevant info and can calculate the distance
				 between two particles
	
	Pre: Valid coordinates
	Notes: A compare - method could be implemented to make testing straightforward
	"""
	def __init__(self, pos = (0, 0, 0), intpos = (0, 0, 0), timePoint = 0, size = 1, avgint = 20, obj = -1):
		self.pos = pos
		self.intval = obj
		self.timePoint = timePoint
		self.size = size
		self.averageIntensity = avgint
		self.inTrack = 0
		self.flag = 0
		self.trackNum = -1
		self.posInPixels = intpos
		self.matchScore = 99999999999999
		
	def getCenterOfMass(self):
		"""
		Created: 26.11.2006, KP
		Description: Return the center of mass component
		"""
		return self.posInPixels
		
	def objectNumber(self):
		"""
		Created: Unknown, KP
		Description: Get intval
		"""
		return self.intval
		
	def distance(self, particle):	 
		"""
		Created: KP
		Description: Return the distance between this particle and p

		Pre: Valid coordinates
		Post: A distance, with a max error of ...
		"""
		particleXPos, particleYPos, particleZPos = particle.pos
		selfXPos, selfYPos, selfZPos = self.pos
		distanceX = particleXPos - selfXPos
		distanceY = particleYPos - selfYPos
		distanceZ = particleZPos - selfZPos
		return math.sqrt(distanceX * distanceX + distanceY * distanceY + distanceZ * distanceZ)
		
	def copy(self, particle):
		"""
		Created: KP
		Description: Copy information over from particle p

		Pre: Valid properties in particle p
		Post: Particle self has valid properties
		
		inTrack is used as both a 0 / 1 "boolean" and a true boolean, could this be made clearer?
		"""
		self.pos = particle.pos
		self.averageIntensity = particle.averageIntensity
		self.posInPixels = particle.posInPixels
		self.inTrack = particle.inTrack
		self.flag = particle.flag
		self.timePoint = particle.timePoint
		self.intval = particle.intval
		self.matchScore = particle.matchScore

	def __str__(self):
		try:
			xPosition, yPosition, zPosition = self.posInPixels 
			return "<Obj#%d (%d, %d, %d) t = %d, inTrack = %s>" \
					% (self.intval, xPosition, yPosition, zPosition, self.timePoint, bool(self.inTrack))
		except:
			raise "Bad pos", self.pos	# TODO: When does this get raised?

	def __repr__(self):
		return self.__str__()


class ParticleTracker:
	"""
	Created: 11.09.2006, KP
	Description: A class that will utilize the different tracking related
				 classes to create tracks of a set of particles
	"""
	def __init__(self):

		self.velocityWeight = 0.25
		self.directionWeight = 0.25
		self.sizeWeight = 0.25
		self.intensityWeight = 0.25
		
		self.distanceChange = None
		self.sizeChange = None
		self.intensityChange = None
		self.angleChange = None
	
		self.filterObjectSize = 2  
		self.minimumTrackLength = 3

		self.maxIntensity = None
		self.maxSize = None
		self.maxVelocity = None

		self.reader = None
		self.particles = None	 
		self.tracks = []

		if psyco and sys.platform != 'darwin':
			psyco.bind(self.getStats)
			psyco.bind(self.angle)
			psyco.bind(Particle.distance)
			psyco.bind(self.track)
		
	def setMinimumTrackLength(self, minlen):
		"""
		Created: 11.09.2006, KP
		Description: Set the minimum length that tracks need to have
					 in order to be written to disk
		"""
		self.minimumTrackLength = minlen
		
	def setWeights(self, velocityWeight, sizeWeight, intensityWeight, directionWeight):	

		"""
		Created: 25.11.2006, KP
		Description: Set the weighting factors for velocity change, 
					size change, intensity change and direction change
		"""
		self.velocityWeight = velocityWeight
		self.sizeWeight = sizeWeight
		self.intensityWeight = intensityWeight
		self.directionWeight = directionWeight
		
	def getReader(self):	
		"""
		Created: 25.11.2006, KP
		Description: Return the particle reader
		"""
		return self.reader
		
	def readFromFile(self, filename, statsTimepoint = 0):
		"""
		Created: 11.09.2006, KP
		Description: Read the particles from a given .CSV filename
		"""
		self.particles = []
		#n = 999
		print "Reading from file = '", filename, "'"
		#for i in range(0,n+1):
		#	 file="%s_%d.csv"%(filename,i)			  
		if os.path.exists(filename):
			#print "Reading from ", file
			self.reader = ParticleReader(filename, filterObjectSize = self.filterObjectSize)
			self.particles = self.reader.read(statsTimepoint = statsTimepoint)
				
	def getParticles(self, timepoint, objs):
		"""
		Created: 26.11.2006, KP
		Description: return the particles in given timepoint with given int.values
		"""
		print "getParticles(", timepoint, ",", objs, ")"
		pts = self.particles[timepoint]
		ret = []
		for i in pts:
			if i.objectNumber() in objs:
				ret.append(i)
				
		return ret
		
	def getTracks(self):
		"""
		Created: 27.11.2006, KP
		Description: return the tracks
		"""
		return self.tracks
		
	def writeTracks(self, filename):			# TODO: Test when tracks != []
		"""
		Created: 11.09.2006, KP
		Description: Write the calculated tracks to a file
		"""
		fileToOpen = codecs.open(filename, "wb", "latin1")
			
		writer = csv.writer(fileToOpen, dialect = "excel", delimiter = ";")
		writer.writerow(["Track #", "Object #", "Timepoint", "X", "Y", "Z"])
		for i, track in enumerate(self.tracks):
			if len(track) < self.minimumTrackLength:
				continue
			for particle in track:
				particleXPos, particleYPos, particleZPos = particle.posInPixels
				writer.writerow([str(i), str(particle.intval), str(particle.timePoint), \
				str(particleXPos), str(particleYPos), str(particleZPos)])		
		fileToOpen.close()
						
	def setFilterObjectSize(self, filterSize):
		"""
		Created: 11.09.2006, KP
		Description: Set the minimum size (in pixels) objects must have to be
					 considered for the tracking
		"""
		print "Setting filter object size to", filterSize
		self.filterObjectSize = filterSize

	def getStats(self):
		"""
		Created: KP
		Description: Given a set of particles, calculate their minimum, maximum and
					 average distances in each timepoint
		"""
		
		print "Calculating statistics for particles"
		mindists = []
		maxdists = []
		avgdists = []
		minSize = 9999999
		maxSize = 0
		minInt = 9999999999
		maxInt = 0
		for i, pts in enumerate(self.particles):
			avgdist = 0
			numberOfParticles = 0
			mindist = 999999999
			maxdist = 0
			print "There are %d particles in timepoint %d" % (len(pts), i)

			# this loop calculates every particles distance to every
			# other particle in the same timepoint. it returns the
			# highest distance between two particles in a timepoint
			for particle in pts:
				if particle.averageIntensity > maxInt:
					maxInt = particle.averageIntensity
				elif particle.averageIntensity < minInt:
					minInt = particle.averageIntensity
				if particle.size > maxSize:
					maxSize = particle.size
				elif particle.size < minSize:
					minSize = particle.size

				for particle2 in pts:
					if particle.intval == particle2.intval:
						continue
					distance = particle2.distance(particle)					
					if distance < mindist:
						mindist = distance
					if distance > maxdist:
						maxdist = distance
					avgdist += distance
					numberOfParticles += 1
			avgdist /= float(numberOfParticles)
			mindists.append(mindist)
			maxdists.append(maxdist)
			avgdists.append(avgdist)
		return mindists, maxdists, avgdists, minSize, maxSize, minInt, maxInt
		
	def setDistanceChange(self, distChange):
		"""
		Created: 11.09.2006, KP
		Description: Set the parameter that defines maximum change in the distance (in percents
					 of the maximum change) of two particles that will still be considered to be
					 able to belong to the same track.
		"""
		self.distanceChange = distChange
	
	def setSizeChange(self, sizeChange):
		"""
		Created: 11.09.2006, KP
		Description: Set the parameter that defines maximum change in the size (in percents
					 of the maximum change) of two particles that will still be considered to be
					 able to belong to the same track.
		"""
		self.sizeChange = sizeChange
		
	def setIntensityChange(self, intChange):
		"""
		Created: 11.09.2006, KP
		Description: Set the parameter that defines maximum change in the average intensity
					 (in percents of the maximum change) of two particles that will still
					 be considered to be able to belong to the same track.
		"""
		self.intensityChange = intChange
		
	def setAngleChange(self, angleChange):	
		"""
		Created: 11.09.2006, KP
		Description: Set the parameter that defines maximum change in the angle of the track
					 (in degrees) that is calculated betwee two particles so  that the particles
					 will still be considered to be able to belong to the same track.
					 The angle is the total "cone of change", so if the track can veer 15 degrees
					 in either direction, then the Angle Change should be set to 30 degrees
		"""
		self.angleChange = angleChange
		
	def score(self, testParticle, oldParticle):
		"""
		Created: 24.09.2006, KP
		Description: Measure the match score between two particles. Returns 
					 a 3 - tuple (distFactor, sizeFactor, intFactor )if there's a match
					and none otherwise	  
		"""
					 
		distance = testParticle.distance(oldParticle)
		# If a particle is within search radius and doesn't belong in a
		# track yet
		distFactor = float(distance) / self.maxVelocity
		failed = 0
		if distFactor > self.distanceChange:
			failed = 1
		else:
			sizeFactor = float(abs(testParticle.size - oldParticle.size))
			sizeFactor /= self.maxSize
			if sizeFactor > self.sizeChange:
				failed = 1
			else:
				intFactor =  float(abs(testParticle.averageIntensity - oldParticle.averageIntensity))
				intFactor /= self.maxIntensity
				if intFactor > self.intensityChange:
					failed = 1		
		if failed: 
			return None, None, None
		return (distFactor, sizeFactor, intFactor)
				
	@staticmethod
	def angle(particle1, particle2):
		"""
		Created: 25.09.2006, KP
		Description: Measure the "angle" between horizontal axis and the line defined
					 by the two particles
		"""
		particle1X, particle1Y = particle1.posInPixels[0:2]
		particle2X, particle2Y = particle2.posInPixels[0:2]
		ang = math.atan2(particle2Y - particle1Y, particle2X - particle1X) * 180.0 / math.pi
		ang2 = ang
		if ang < 0:
			ang2 = 180 + ang
		return ang, ang2
		
	def toScore(self, distFactor, sizeFactor, intFactor, angleFactor = 1):	
		"""
		Created: 25.09.2006, KP
		Description: Return a score that unifies the different factors into a single score
		"""
		#return 0.50*distFactor+0.2*angleFactor+0.15*sizeFactor+0.15*intFactor
		return self.velocityWeight * distFactor + \
				self.sizeWeight * sizeFactor + \
				self.intensityWeight * intFactor + \
				self.directionWeight * angleFactor
	
	def track(self, fromTimepoint = 0, seedParticles = []):		# TODO: Test for this
		"""
		Created: KP
		Description: Perform the actual tracking using the given particles and tracking
		parameters.
		"""
		tracks = []
		print "seedparticles =", seedParticles
		trackCount = 0
		totalTimepoints = len(self.particles)
		searchOn = False
		foundOne = False
		print "Total timepoints =", totalTimepoints
		#minDists, maxDists, avgDists, minSiz, maxSiz, minInt, maxInt = self.getStats()
		minDists, maxDists, minSiz, maxSiz, minInt, maxInt = self.getStats()[0:2] + self.getStats()[3:]
	
		print "minDists =", minDists
		print "maxDists =", maxDists
		
		maxDist = max(maxDists)
		minDist = min(minDists)
		self.maxVelocity = maxDist - minDist
		self.maxSize = maxSiz - minSiz
		self.maxIntensity = maxInt - minInt
		
		print "Maximum change in distance =", self.maxVelocity
		print "Maximum change in size =", self.maxSize
		print "Maximum change in intensity =", self.maxIntensity
		
		
		
		if seedParticles:
		# The seed particles are organized as follows:
		#[ [t1_p1, t1_p2, t1_p3], [t2_p1,t2_p2, t2_p3], ...]
		# where t1_p1 = first particle in timepoint 1,
		# t1_p2 = second particle in timepoint 1 etc
		# Therefore, we can determine e.g. how many tracks there are to be calculated
		# by looking at how many seed particles we are given

			trackCount = len(seedParticles[0])
			tracks = []
			for i in range(trackCount):
				tracks.append([])
			print "Track count =", trackCount
			
			particleList = copy.deepcopy(self.particles)
			toRemove = []
			
			# First remove all particles in the seed timepoints
			# that are not listed as seed points
			for timePoint, col in enumerate(seedParticles):
				fromTimepoint = timePoint 
				toRemove = []
				objToParticle = {}
				for i in particleList[timePoint]:
					objval = i.objectNumber()
					if objval not in col:
						toRemove.append(i)
					else:
						objToParticle[objval] = i
						
				# remove the non-seed objects from the timepoint timePoint
				for i in toRemove:
					particleList[timePoint].remove(i)
				for tracknum, objVal in enumerate(col):
					if objVal not in objToParticle:
						print "Object", objVal, "not found"
						if objVal in toRemove:
							print objVal, "was removed"
						continue
					particle = objToParticle[objVal]
					particle.inTrack = 1
					particle.trackNum = tracknum
					print "Adding particle", objVal, "to track", tracknum
					tracks[tracknum].append(particle)
						   
					
		else:
			particleList = self.particles
			
		
			
		# Iterate over all timepoints
		#for timePoint in range(totalTimepoints): 
		
		#print "Tracking from %d particles"%len(particleList[fromTimepoint])
		print "Seed tracks =", tracks
		for timePoint in [fromTimepoint]:
			# Iterate over all particles in given timepoint
							
			
			for i, particle in enumerate(particleList[timePoint]):
				if not seedParticles and particle.inTrack:
				# If particle is in track, just let the user know
					#if particle.inTrack:
					print "\nParticle %d / %d in timepoint %d is already in track %d" % \
						(i, len(particleList[timePoint]), timePoint, particle.trackNum)
				else:
					print "\nTracking particle %d / %d in timepoint %d" % (i, len(particleList[timePoint]), timePoint)
					
					# If we have seed particles, then the track has already been constructed to
					# this point and we can just search for the following particles

					oldParticle = Particle()
					currCandidate = Particle()
					# Make a copy of the particle 
					oldParticle.copy(particle)					  
					if not seedParticles:
						# Create a new track that starts from this point
						track = []
						trackCount += 1
						particle.inTrack = True
						particle.trackNum = trackCount
						track.append(particle)
						
					else:
						track = None
						for ctrack in tracks:
							if particle in ctrack:
								track = ctrack
						
						if not track:
							raise "Did not find track for seed particle", particle
					searchOn = True
					# Search the next timepoints for more particles
					for search_timePoint in range(timePoint + 1, totalTimepoints):
						# If no match was found, then this track is over
						if not searchOn:
							print "Track", i, "is over"
							break
						foundOne = False
						currentMatch = Particle()
						for testParticle in self.particles[search_timePoint]:
							#print "Searching for match in timepoint %d"%search_timePoint
							# Calculate the factors between the particle that is being tested against
							# the previous particle  (= oldParticle)
							distFactor, sizeFactor, intFactor = self.score(testParticle, oldParticle)
							failed = (distFactor == None)    
							angleFactor = 0
							# If the particle being tested passed the previous tests
							# and there is already a particle before the current one,
							# then calculate the angle and see that it fits in the margin
							if not failed and len(track) > 1:
								angle, absang = self.angle(track[-2], track[-1])
								angle2, absang2	= self.angle(track[-1], testParticle)
								
								angdiff = abs(absang - absang2)
								# If angle*angle2 < 0 then either (but not both) of the angles 
								# is negative, so the particle being tested is in wrong direction
								if angle * angle2 < 0:
									failed = 1															
								elif  angdiff > self.angleChange:									 
									failed = 1							
								else:																		 
									angleFactor = float(angdiff) / self.angleChange
									
							
							#if not failed:
							#	 print "Factors = ",distFactor, sizeFactor, intFactor
						 
							# If we got a match between the previous particle (oldParticle)
							# and the currently tested particle (testParticle) and testParticle
							# is not in a track
							if (not failed) and (not testParticle.inTrack):
								currScore = self.toScore(distFactor, sizeFactor, intFactor, angleFactor)
								# if there's no other particle that fits the criteria
								if not foundOne:
									# Mark the particle being tested as the current candidate
									currCandidate = testParticle
									testParticle.inTrack = True
									testParticle.matchScore = currScore
									testParticle.trackNum = trackCount
									currentMatch.copy(testParticle)
									foundOne = True
									
								else:
									# if we've already found one, then use this instead if
									# this one is closer. In any case, flag the particle
									testParticle.flag = True
									# Compare the distance calculated between the particle
									# that is currently being tested, and the old candidate particle
									
									if currScore < currentMatch.matchScore:
									#if dist < currentMatch.distance(oldParticle):
										testParticle.inTrack = True
										testParticle.trackNum = trackCount
										currentMatch.copy(testParticle)
										currCandidate.inTrack = False
										currCandidate.trackNum = -1
										currCandidate = testParticle
									else:
										currentMatch.flag = True
							#elif dist < self.maxVelocity:
							#	 # If the particle is already in a track but could also be in this
							#	 # track, we have a few options
							#	 # 1. Sort out to which track this particle really belongs (but how?)
							#	 # 2. Stop this track
							#	 # 3. Stop this track, and also delete the remainder of the other one
							#	 # 4. Stop this track and flag this particle:
							#	 testParticle.flag = True
						if foundOne:
							sys.stdout.write(".")
	#						 print "Particle added to track %d" % trackCount
							track.append(currentMatch)
						else:
							sys.stdout.write("^")
							#print "Found no particles that belong to track %d" % trackCount
							searchOn = False
						oldParticle.copy(currentMatch)
					tracks.append(track)
		self.tracks = tracks
