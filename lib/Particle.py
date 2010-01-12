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
import ParticleReader
try:
	import psyco
except ImportError:
	psyco = None

class Particle:
	"""
	Description: A class representing a particle. Stores all relevant info and can calculate the distance
				 between two particles
	
	Pre: Valid coordinates
	Notes: A compare - method could be implemented to make testing straightforward
	"""
	def __init__(self, pos = (0, 0, 0), intpos = (0, 0, 0), timePoint = 0, volume = 1, avgint = 20, obj = -1):
		self.pos = pos
		self.intval = obj
		self.timePoint = timePoint
		self.volume = volume
		self.averageIntensity = avgint
		self.inTrack = False
		self.flag = 0
		self.trackNum = -1
		self.posInPixels = intpos
		self.matchScore = 0
		self.trackCount = 0
		self.seedParticles = []
		self.totalTimepoints = 1
		self.voxelSize = [1.0,1.0,1.0]
		
	def getCenterOfMass(self):
		"""
		Return the center of mass component
		"""
		return self.posInPixels
		
	def objectNumber(self):
		"""
		Get intval
		"""
		return self.intval
		
	def distance3D(self, x,y,z, x2,y2,z2):
		"""
		@return the distance in 3D between points (x,y,z) and (x2,y2,z2)
		"""
		distanceX = x - x2
		distanceY = y - y2
		distanceZ = z - z2
		return math.sqrt(distanceX * distanceX + distanceY * distanceY + distanceZ * distanceZ)
		
	def distance(self, particle):	 
		"""
		Return the distance between this particle and p

		Pre: Valid coordinates
		Post: A distance, with a max error of ...
		"""
		particleXPos, particleYPos, particleZPos = [particle.posInPixels[i] for i in range(0,3)]
		selfXPos, selfYPos, selfZPos = [self.posInPixels[i] for i in range(0,3)]
		return self.distance3D(particleXPos, particleYPos, particleZPos, selfXPos, selfYPos, selfZPos)
		
	def copy(self, particle):
		"""
		Copy information over from particle p

		Pre: Valid properties in particle p
		Post: Particle self has valid properties
		"""
		self.volume = particle.volume
		self.pos = particle.pos
		self.averageIntensity = particle.averageIntensity
		self.posInPixels = particle.posInPixels
		self.inTrack = particle.inTrack
		self.flag = particle.flag
		self.timePoint = particle.timePoint
		self.intval = particle.intval
		self.matchScore = particle.matchScore
		self.voxelSize = particle.voxelSize

	def __str__(self):
		try:
			xPosition, yPosition, zPosition = self.posInPixels 
			return "<Obj#%d (%d,%d,%d) T%d, %s>" \
					% (self.intval, round(xPosition), round(yPosition), round(zPosition), self.timePoint, bool(self.inTrack))
		except:
			raise "Bad pos", self.pos	# TODO: When does this get raised?

	def __repr__(self):
		return self.__str__()

	def setVoxelSize(self, voxelSize):
		"""
		Set voxel size of particle for length and speed calculations
		"""
		if len(voxelSize) == 3:
			self.voxelSize = voxelSize
			

class ParticleTracker:
	"""
	A class that will utilize the different tracking related
				 classes to create tracks of a set of particles
	"""
	def __init__(self):
		self.velocityWeight = 0.25
		self.directionWeight = 0.25
		self.sizeWeight = 0.25
		self.intensityWeight = 0.25
		self.minSpeed = 5
		self.maxSpeed = 25
		self.speedDeviation = 0.3
		self.distanceChange = None
		self.sizeChange = None
		self.intensityChange = None
		self.angleChange = None

		self.voxelSize = [1.0,1.0,1.0]
		self.filterObjectSize = 2  
		self.minimumTrackLength = 3

		self.maxIntensity = None
		self.maxSize = None
		self.maxVelocity = None

		self.reader = None
		self.particles = None	 
		self.tracks = []
		self.timeStamps = []
		self.useNew = 1

		if psyco and sys.platform != 'darwin':
			psyco.bind(self.getStats)
			psyco.bind(self.angle)
			psyco.bind(Particle.distance)
			psyco.bind(self.track)
		
	def setMinimumTrackLength(self, minlen):
		"""
		Set the minimum length that tracks need to have
					 in order to be written to disk
		"""
		self.minimumTrackLength = minlen
		
	def setWeights(self, velocityWeight, sizeWeight, intensityWeight, directionWeight):	

		"""
		Set the weighting factors for velocity change, 
					size change, intensity change and direction change
		"""
		self.velocityWeight = velocityWeight
		self.sizeWeight = sizeWeight
		self.intensityWeight = intensityWeight
		self.directionWeight = directionWeight
		
	def getReader(self):	
		"""
		Return the particle reader
		"""
		return self.reader
		
	def readFromFile(self, filename, statsTimepoint = 0):
		"""
		Read the particles from a given .CSV filename
		"""
		self.particles = []
		#n = 999
		print "Reading from file = '", filename, "'"

		if os.path.exists(filename):
			self.reader = ParticleReader(filename, filterObjectVolume = self.filterObjectSize)
			self.particles = self.reader.read(statsTimepoint = statsTimepoint)
			for particleList in self.particles:
				for particle in particleList:
					particle.setVoxelSize(self.voxelSize)
				
	def getParticles(self, timepoint, objs):
		"""
		return the particles in given timepoint with given int.values
		"""
		pts = self.particles[timepoint]
		ret = []
		for i in pts:
			if i.objectNumber() in objs:
				ret.append(i)
				
		return ret
		
	def getTracks(self):
		"""
		return the tracks
		"""
		return self.tracks
		
	def writeTracks(self, filename):			# TODO: Test when tracks != []
		"""
		Write the calculated tracks to a file
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
		Set the minimum size (in pixels) objects must have to be
					 considered for the tracking
		"""
		self.filterObjectSize = filterSize

	def getStats(self):
		"""
		Given a set of particles, calculate their minimum, maximum and
					 average distances in each timepoint
		"""
		mindists = []
		maxdists = []
		avgdists = []
		minSize = 999999999
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
				if particle.volume > maxSize:
					maxSize = particle.volume
				elif particle.volume < minSize:
					minSize = particle.volume

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
			if numberOfParticles == 0:
				avgdist = 0
				mindist = 0
				maxdist = 0
			else:
				avgdist /= float(numberOfParticles)
				
			mindists.append(mindist)
			maxdists.append(maxdist)
			avgdists.append(avgdist)
		return mindists, maxdists, avgdists, minSize, maxSize, minInt, maxInt
		
	def setDistanceChange(self, distChange):
		"""
		Set the parameter that defines maximum change in the distance (in percents
					 of the maximum change) of two particles that will still be considered to be
					 able to belong to the same track.
		"""
		self.distanceChange = distChange
		
	def setMaxSpeed(self, maxSpeed):
		"""
		Set the maximum speed (in um) of an object between timepoints
		"""
		self.maxSpeed = maxSpeed
		
	def setMinSpeed(self, minSpeed):
		"""
		Set the minimum speed (in um) of an object between timepoints
		"""
		self.minSpeed = minSpeed
		
	def setSpeedDeviation(self, dev):
		"""
		Set the deviation (in percentage) allowed from min or max
		"""
		self.speedDeviation = dev
	
	def setSizeChange(self, sizeChange):
		"""
		Set the parameter that defines maximum change in the size (in percents
					 of the maximum change) of two particles that will still be considered to be
					 able to belong to the same track.
		"""
		self.sizeChange = sizeChange
		
	def setIntensityChange(self, intChange):
		"""
		Set the parameter that defines maximum change in the average intensity
					 (in percents of the maximum change) of two particles that will still
					 be considered to be able to belong to the same track.
		"""
		self.intensityChange = intChange
		
	def setAngleChange(self, angleChange):	
		"""
		Set the parameter that defines maximum change in the angle of the track
					 (in degrees) that is calculated betwee two particles so  that the particles
					 will still be considered to be able to belong to the same track.
					 The angle is the total "cone of change", so if the track can veer 15 degrees
					 in either direction, then the Angle Change should be set to 30 degrees
		"""
		self.angleChange = angleChange
		
	def score(self, testParticle, oldParticle):
		"""
		Measure the match score between two particles. Returns 
					 a 3 - tuple (distFactor, sizeFactor, intFactor )if there's a match
					and none otherwise	  
		"""
		distance = testParticle.distance(oldParticle)
		# If a particle is within search radius +- tolerance and doesn't belong in a
		# track yet
		if distance > self.maxSpeed*(1+self.speedDeviation):
#			print "Distance",distance,"is too large",self.maxSpeed, self.speedDeviation
			return None, None, None
		if distance < self.minSpeed*(1-self.speedDeviation):
#			print "Distance",distance,"is too small",self.minSpeed, self.speedDeviation
			return None,None,None

		#print "Found a particle with matching distance",distance		
		if distance <= self.maxSpeed and distance >= self.minSpeed:
			distFactor = 1
		elif distance < self.minSpeed:
			distFactor = distance / self.minSpeed
		elif distance > self.maxSpeed:
			distFactor = self.maxSpeed / distance
		#print "new size=",testParticle.size, "old size=",oldParticle.size
		sizeChange = float(abs(testParticle.volume - oldParticle.volume))
		#print "sizeChange=",sizeChange, "old size=",oldParticle.size
		sizeFactor = sizeChange / oldParticle.volume
		
		if sizeFactor > self.sizeChange:
			#print "Size change=",self.sizeChange,"size factor=",sizeFactor
			return None,None,None
		sizeFactor /= self.sizeChange
		sizeFactor = abs(sizeFactor - 1)
		
		intChange =  float(abs(testParticle.averageIntensity - oldParticle.averageIntensity))
		if oldParticle.averageIntensity == 0:
			return None, None, None
		
		intFactor = intChange / oldParticle.averageIntensity
		if intFactor > self.intensityChange:
			return None, None, None
		intFactor /= self.intensityChange
		intFactor = abs(intFactor - 1)
		return (distFactor, sizeFactor, intFactor)
				
	@staticmethod
	def angle(vector1, vector2):
		"""
		Measure the angle between two unit vectors
		"""
		inner = 0.0
		for i in range(3):
			inner += vector1[i] * vector2[i]

		try: # There can be rounding problems
			ang = abs(math.acos(inner) * 180 / math.pi)
		except:
			ang = 0.0
		return ang
		
	def toScore(self, distFactor, sizeFactor, intFactor, angleFactor = 0):
		"""
		Return a score that unifies the different factors into a single score
		"""
		return self.velocityWeight * distFactor + \
				self.sizeWeight * sizeFactor + \
				self.intensityWeight * intFactor + \
				self.directionWeight * angleFactor
	
	def getParticlesFromSeedpoints(self, fromTimepoint, seedParticles):
		"""
		get the particle list based on the given seed particles
		"""
		# The seed particles are organized as follows:
		#[ [t1_p1, t1_p2, t1_p3], [t2_p1,t2_p2, t2_p3], ...]
		# where t1_p1 = first particle in timepoint 1,
		# t1_p2 = second particle in timepoint 1 etc
		# Therefore, we can determine e.g. how many tracks there are to be calculated
		# by looking at how many seed particles we are given

		self.trackCount = len(seedParticles[0])
		tracks = []
		for i in range(self.trackCount):
			tracks.append([])
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
				particle.inTrack = True
				particle.trackNum = tracknum
				print "Adding particle", objVal, "to track", tracknum
				tracks[tracknum].append(particle)
		return tracks, particleList
		
	def calculateAngleFactor(self, testParticle, track):
		"""
		"""
		# Return if track[-2] is a None particle
		if not track[-2].posInPixels[0] or not track[-2].posInPixels[1] or not track[-2].posInPixels[2]:
			return 0.0
		
		lenVec1 = 0.0
		lenVec2 = 0.0
		vector1 = []
		vector2 = []
		for i in range(3):
			vector1.append((track[-1].posInPixels[i] - track[-2].posInPixels[i]) * self.voxelSize[i])
			lenVec1 += vector1[i]**2
			vector2.append((testParticle.posInPixels[i] - track[-1].posInPixels[i]) * self.voxelSize[i])
			lenVec2 +=  vector2[i]**2
		if (lenVec1 == 0 or lenVec2 == 0):
			return 0.0
		
		lenVec1 = math.sqrt(lenVec1)
		lenVec2 = math.sqrt(lenVec2)
		for i in range(3):
			vector1[i] /= lenVec1
			vector2[i] /= lenVec2
		vector1 = tuple(vector1)
		vector2 = tuple(vector2)
		
		angle = self.angle(vector1,vector2)
		
		if  angle > self.angleChange:
			return -1
		else: 
			angleFactor = angle / self.angleChange
			angleFactor = abs(angleFactor - 1)
		return angleFactor
		
	def track(self, fromTimepoint = 0, seedParticles = []):# TODO: Test for this
		"""
		Perform the actual tracking using the given particles and tracking
		parameters.
		"""
		tracks = []
		self.trackCount = 0
		self.totalTimepoints = len(self.particles)
		self.seedParticles = seedParticles
		searchOn = False
		foundOne = False
		minDists, maxDists, avgDist, minSiz, maxSiz, minInt, maxInt = self.getStats()

		maxDist = max(maxDists)
		minDist = min(minDists)
		print "minDist=",minDist,"maxDist=",maxDist
		self.maxVelocity = maxDist - minDist
		self.maxSize = maxSiz - minSiz
		self.maxIntensity = maxInt - minInt

		if seedParticles:
			tracks, self.particleList = self.getParticlesFromSeedpoints(fromTimepoint, seedParticles)
		else:
			self.particleList = self.particles

		timePoint = fromTimepoint
		# Iterate over all time points
		if self.useNew:
			for i in range(self.totalTimepoints):
				self.trackTimepointParticles(i,tracks)
		else:
		# Iterate over all particles in given timepoint
			for i, particle in enumerate(self.particleList[timePoint]):
				print "\nTracking particle %d / %d in timepoint %d" % (i, len(self.particleList[timePoint]), timePoint)
				self.trackParticle(particle, fromTimepoint, tracks)
		self.tracks = tracks
			
	def trackParticle(self, particle, timePoint, tracks):
		"""
		Track the given particle from given timepoint on
		@param particle the particle to track
		@param timepoint track from this timepoint on 
		"""
		oldParticle = Particle()
		currCandidate = Particle()
		currCandidate.setVoxelSize(self.voxelSize)
		# Make a copy of the particle 
		oldParticle.copy(particle)
		# if there are no seed particles (and hence, no initial tracks), then create
		# a new track that begins from this timepoint
		if not self.seedParticles:
			track = []
			self.trackCount += 1
			particle.inTrack = True
			particle.trackNum = self.trackCount
			track.append(particle)
		else:
			# if there are seed tracks, then try to find the track that this particle belongs to
			track = None
			for ctrack in tracks:
				if particle in ctrack:
					track = ctrack
			
			if not track:
				raise "Did not find track for seed particle", particle
		searchOn = True

		# Search the next timepoints for more particles
		for search_timePoint in range(timePoint + 1, self.totalTimepoints):
			# If no match was found, then this track is over
			if not searchOn:
				break
			foundOne = False
			currentMatch = Particle()
			currentMatch.setVoxelSize(self.voxelSize)
			for testParticle in self.particles[search_timePoint]:
				# Calculate the factors between the particle that is being tested against
				# the previous particle  (= oldParticle)
				distFactor, sizeFactor, intFactor = self.score(testParticle, oldParticle)
				failed = (distFactor == None)   
				angleFactor = 0
				# If the particle being tested passed the previous tests
				# and there is already a particle before the current one,
				# then calculate the angle and see that it fits in the margin
				if not failed and len(track) > 1:
					angleFactor = self.calculateAngleFactor(testParticle, track)
					if angleFactor==-1:
						failed = 1
				# If we got a match between the previous particle (oldParticle)
				# and the currently tested particle (testParticle) and testParticle
				# is not in a track
				if (not failed):#and (not testParticle.inTrack):
					currScore = self.toScore(distFactor, sizeFactor, intFactor, angleFactor)

					# if there's no other particle that fits the criteria
					if not foundOne:
						#print "Found a candidate",testParticle
						# Mark the particle being tested as the current candidate
						currCandidate = testParticle
						testParticle.inTrack = True
						testParticle.matchScore = currScore
						testParticle.trackNum = self.trackCount
						currentMatch.copy(testParticle)
						foundOne = True
					else:
						# if we've already found one, then use this instead if
						# this one is closer. In any case, flag the particle
						testParticle.flag = True
						# Compare the distance calculated between the particle
						# that is currently being tested, and the old candidate particle
						#if currScore > currentMatch.matchScore:
						testParticle.inTrack = True
						testParticle.trackNum = self.trackCount
						testParticle.matchScore = currScore
						currentMatch.copy(testParticle)
						currCandidate.inTrack = False
						currCandidate.trackNum = -1
						currCandidate = testParticle
						#else:
						#	currentMatch.flag = True
				#	 # If the particle is already in a track but could also be in this
				#	 # track, we have a few options
				#	 # 1. Sort out to which track this particle really belongs (but how?)
				#	 # 2. Stop this track
				#	 # 3. Stop this track, and also delete the remainder of the other one
				#	 # 4. Stop this track and flag this particle:
				#	 testParticle.flag = True
			if foundOne:
				track.append(currentMatch)
				print "-"
				#print "Found match",currentMatch
			else:
				print "|"
				searchOn = False
			oldParticle.copy(currentMatch)
		tracks.append(track)
		
	def setVoxelSize(self, voxelSize):
		"""
		Set size of voxels
		"""
		if (type(voxelSize) == list):
			self.voxelSize = voxelSize
		else:
			vs = []
			for item in voxelSize:
				vs.append(item)
			self.voxelSize = vs

	def setTimeStamps(self, timeStamps):
		"""
		Set timestamps
		"""
		self.timeStamps = timeStamps

	def trackTimepointParticles(self, timePoint, tracks):
		"""
		"""
		if not self.seedParticles and timePoint == 0:
			for i,particle in enumerate(self.particleList[timePoint]):
				track = []
				self.trackCount += 1
				particle.inTrack = True
				particle.trackNum = self.trackCount
				track.append(particle)
				tracks.append(track)
			return

		if timePoint == 0:
			return

		# Search all particles on this timepoint
		oldParticles = {}
		scores = []
		for i,testParticle in enumerate(self.particleList[timePoint]):
			testParticle.inTrack = False
			for j,track in enumerate(tracks):
				# Calculate the factors between the particle that is being tested against
				# the previous particle  (= oldParticle)
				try:
					oldParticle = track[timePoint-1]
				except:
					continue
				
				# Calculate how many times same particle is in different tracks (track only once)
				if not oldParticles.get(tuple(oldParticle.posInPixels), False):
					oldParticles[tuple(oldParticle.posInPixels)] = 0
				oldParticles[tuple(oldParticle.posInPixels)] += 1
				
				distFactor, sizeFactor, intFactor = self.score(testParticle, oldParticle)
				failed = (distFactor == None)
				angleFactor = 0
				# If the particle being tested passed the previous tests
				# and there is already a particle before the current one,
				# then calculate the angle and see that it fits in the margin
				if not failed and len(track) > 1:
					angleFactor = self.calculateAngleFactor(testParticle, track)
					if angleFactor == -1:
						failed = 1
				# If we got a match between the previous particle (oldParticle)
				# and the currently tested particle (testParticle) and testParticle
				# is not in a track
				if (not failed):#and (not testParticle.inTrack):
					currScore = self.toScore(distFactor, sizeFactor, intFactor, angleFactor)
					trackLen = 0
					for trackPart in track:
						if trackPart.posInPixels[0] and trackPart.posInPixels[1] and trackPart.posInPixels[2]:
							trackLen += 1
					scores.append({"Score": currScore, "Track": j, "Particle": i, "TrackLen": trackLen})

		def compareScore(a,b):
			if a["Score"] == b["Score"]:
				return cmp(b["TrackLen"], a["TrackLen"])
			else:
				return cmp(b["Score"], a["Score"])
		scores.sort(compareScore)
		
		trackUsage = {}
		particleUsage = {}
		tracksScores = {}
		changes = True
		numIteration = 1
		# Iterate algorithm as long as changes are made
		while(changes):
			changes = False	
			tmpScores = []
			#isBestScore = {}
			#isBestParticleScore = {}
			for i,score in enumerate(scores):
				trackNum = score["Track"]
				particleNum = score["Particle"]
				usedTrack = trackUsage.get(trackNum,-1)
				usedParticle = particleUsage.get(particleNum,False)
				trackScores = tracksScores.get(trackNum, [])
				if numIteration == 1:
					if len(trackScores) == 0:
						tracksScores[trackNum] = []
					tracksScores[trackNum].append(score)
				
				if usedTrack == -1 and not usedParticle and score["Score"] > 0.75 * tracksScores[trackNum][0]["Score"]:
					if timePoint > 0 and not oldParticles.get(tuple(tracks[trackNum][timePoint-1].posInPixels), True):
						trackUsage[trackNum] = 0 # Don't use this track (some other track tracks the same particle)
						continue
					if timePoint > 0:
						oldParticles[tuple(tracks[trackNum][timePoint-1].posInPixels)] = 0
					trackUsage[trackNum] = particleNum
					particleUsage[particleNum] = True
					matchParticle = Particle()
					matchParticle.copy(self.particleList[timePoint][particleNum])
					matchParticle.inTrack = True
					matchParticle.matchScore = score["Score"]
					matchParticle.trackNum = trackNum
					tracks[trackNum].append(matchParticle)
					changes = True
				else:
					tmpScores.append(score)

				#isBestScore[trackNum] = False
				#isBestParticleScore[particleNum] = False
			numIteration += 1
			scores = tmpScores

		# Try to add particle on tracks that don't have any yet
		for i,track in enumerate(tracks):
			if trackUsage.get(i,-1) != -1:
				continue

			try:
				trackScores = tracksScores[i]
				particleNum = trackScores[0]["Particle"]
				if timePoint > 0 and not oldParticles.get(tuple(tracks[i][timePoint-1].posInPixels), True):
					trackUsage[i] = 0
					continue
					
				if timePoint > 0:
					oldParticles[tuple(tracks[i][timePoint-1].posInPixels)] = 0
				trackUsage[i] = particleNum
				particleUsage[particleNum] = True
				matchParticle = Particle()
				matchParticle.copy(self.particleList[timePoint][particleNum])
				matchParticle.inTrack = True
				matchParticle.matchScore = trackScores[0]["Score"]
				matchParticle.trackNum = i
				tracks[i].append(matchParticle)
				
			except:
				pass

		# Add new tracks for particles that are not used on any track
		for i,particle in enumerate(self.particleList[timePoint]):
			if not particleUsage.get(i,False):
				trackNum = len(tracks)
				trackUsage[trackNum] = i
				particleUsage[i] = True
				newParticle = Particle()
				newParticle.copy(particle)
				newParticle.inTrack = True
				newParticle.matchScore = 0
				newParticle.trackNum = trackNum
				newTrack = []

				for i in range(timePoint):
					noneParticle = Particle()
					noneParticle.inTrack = True
					noneParticle.matchScore = 0
					noneParticle.trackNum = trackNum
					noneParticle.intval = None
					noneParticle.timePoint = i
					noneParticle.posInPixels = [None,None,None]
					noneParticle.voxelSize = particle.voxelSize
					newTrack.append(noneParticle)
				newTrack.append(newParticle)
				tracks.append(newTrack)
