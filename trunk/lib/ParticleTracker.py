"""
 Unit: ParticleTracker
 Project: BioImageXD
 Description:

 A module containing classes related to particle tracking
							
 Copyright (C) 2005	 BioImageXD Project
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
 Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111 - 1307	 USA

"""
__author__ = "BioImageXD Project < http://www.bioimagexd.org/>"
__version__ = "$Revision: 1.42 $"
__date__ = "$Date: 2005 / 01 / 13 14:52:39 $"

import ParticleReader
import Particle
import os
import math

class DimensionMapper:
	def __init__(self):
		pass
		
	def calculateInitialInfo(self, timepoint, pointA, pointB):
		"""
		This method is given all the points in each timepoint, that the DimensionMapper can use to calculate
		any global statistics on the search space that it requires to operate
		"""
		pass
		
	def value(self, point):
		"""
		Return the value of a point in this DimensionMapper as a coordinate scaled to [0, 1]
		"""
		return 0
		
class DistanceDimensionMapper(DimensionMapper):
	"""
	A DimensionMapper that maps the physical position of a particle into a 3D space with values in range [0,1]
	"""
	def __init__(self):
		self.maxDistance = 0
		self.minDistance = 9999999999999
		self.minX, self.minY, self.minZ = 99999999,99999999,999999999
		self.maxX, self.maxY, self.maxZ = 0,0,0
		
	def calculateInitialInfo(self, timepoint, pointA, pointB):
		#d = dist2(pointA.physicalPosition, pointB.physicalPosition)
		#self.minDistance = min(d, self.minDistance)
		#self.maxDistance = max(d, self.maxDistance)
		#self.minX = min(self.minX, pointA.physicalPosition[0], pointB.physicalPosition[0])
		#self.minY = min(self.minY, pointA.physicalPosition[1], pointB.physicalPosition[1])
		#self.minZ = min(self.minZ, pointA.physicalPosition[2], pointB.physicalPosition[2])
		self.maxX = max(self.maxX, pointA.physicalPosition[0], pointB.physicalPosition[0])
		self.maxY = max(self.maxY, pointA.physicalPosition[1], pointB.physicalPosition[1])
		self.maxZ = max(self.maxZ, pointA.physicalPosition[2], pointB.physicalPosition[2])
		self.maxPos = (self.maxX, self.maxY, self.maxZ)
		
	def value(self, point):
		"""
		Scale the position coordinates to range 0-1
		"""
		return [point.physicalPosition[i] / self.maxPos[i] for i in range(0,3)]

class SizeDimensionMapper(DimensionMapper):
	"""
	A DimensionMapper that maps the physical size of the particle into a dimension with values in range [0,1]
	"""
	def __init__(self):
		self.maxSize = 0
		
	def calculateInitialInfo(self, timepoint, pointA, pointB):
		self.maxSize = max(self.maxSize, pointA.size, pointB.size)
		
	def value(self, point):
		"""
		Scale the size to range [0-1]
		"""
		return [point.size / float(self.maxSize)]
		
class IntensityDimensionMapper(DimensionMapper):
	"""
	A DimensionMapper that maps the average intensity of the particle into range [0,1]
	"""
	def __init__(self):
		self.maxIntensity = 0
		
	def calculateInitialInfo(self, timepoint, pointA, pointB):
		self.maxIntensity = max(self.maxIntensity, pointA.intensityValue, pointB.intensityValue)
		
	def value(self, point):
		return [point.intensityValue / float(self.maxIntensity)]
		
def dist2(p,q):
	"""Squared distance between p and q."""
	d = 0
	for i in range(len(p)):
		d += (p[i]-q[i])**2
	return d

def dist(p, q):
	d = 0
	for i in range(len(p)):
		d += (p[i]-q[i])**2
	return math.sqrt(d)

class KDTree:
	count=0
	def __init__(self,dim=2,index=0, pointList = []):
		self.dim = dim
		self.index = index
		self.split = None
		if pointList:
			k = len(pointList[0])
			pointList.sort(cmp=lambda y,x: cmp(x[self.index], y[self.index]))
			median = len(pointList)/2
			self.split = pointList[median]
			self.left = KDTree(self.dim, (self.index+1)%self.dim, pointList[0:median])
			self.right = KDTree(self.dim, (self.index+1)%self.dim, pointList[median+1:])

	def addPoint(self, p):
		"""Include another point in the kD-tree."""
		if self.split is None:
			self.split = p
			self.left = KDTree(self.dim, (self.index + 1) % self.dim)
			self.right = KDTree(self.dim, (self.index + 1) % self.dim)
		elif self.split[self.index] < p[self.index]:
			self.left.addPoint(p)
		else:
			self.right.addPoint(p)
		
	def inCircle(self, searchNode, radius, testNode):
		return (dist2(searchNode, testNode)<radius*radius)
		
	def neighborsInRange(self, point, radius):
		KDTree.count = 0
		return self.nearestNeighborsAll(point, radius)

	def nearestNeighborsAll(self,q,radius):
		"""Find pair (d,p) where p is nearest neighbor and d is squared
		distance to p. Returned distance must be within maxdist2; if
		not, no point itself is returned.
		"""
		results = []
		if self.split is not None:
			KDTree.count+=1
			if self.inCircle(q, radius, self.split):
				results.append(self.split)

			splitdist = (self.split[self.index] - q[self.index])

			# Determine whether the searched node lies to the left or to the right
			trees = [self.right, self.left]
			if self.split[self.index] < q[self.index]:
				# If this node's coord in current axis is smaller than the searched
				# node's, then search left first
				trees = [self.left, self.right]
				
			# Pick the minimum of the current solution and a search of the
			# subtree 
			results.extend(trees[0].nearestNeighborsAll(q,radius))
			
			# If the distance in the current axis is smaller than the solution we found
			# then we search the other side of the tree as well
			if splitdist < radius:
				results.extend(trees[1].nearestNeighborsAll(q,radius))
		return results
		
	def nearestNeighbor(self,q,maxdist2):
		"""Find pair (d,p) where p is nearest neighbor and d is squared
		distance to p. Returned distance must be within maxdist2; if
		not, no point itself is returned.
		"""
		solution = (maxdist2+1,None)
		if self.split is not None:
			KDTree.count+=1
			# Pick a minimum of the current solution and the split
			solution = min(solution, (dist2(self.split,q),self.split))
			
			# This is a distance^2 in the current axis 
			# from the split point to the target node
			d2split = (self.split[self.index] - q[self.index])**2

			# Determine whether the searched node lies to the left or to the right
			trees = [self.right, self.left]
			if self.split[self.index] < q[self.index]:
				# If this node's coord in current axis is smaller than the searched
				# node's, then search left first
				trees = [self.left, self.right]
				
			# Pick the minimum of the current solution and a search of the
			# subtree 
			solution = min(solution,
				trees[0].nearestNeighbor(q,solution[0]))
			
			# If the distance in the current axis is smaller than the solution we found
			# then we search the other side of the tree as well
			if d2split < solution[0]:
				solution = min(solution,
					trees[1].nearestNeighbor(q,solution[0]))
		return solution

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
	
		self.filterObjectSize = 2  

		self.maxIntensity = None
		self.maxSize = None
		self.maxVelocity = None

		self.reader = None
		self.particles = None	 
		self.tracks = []
		
		self.measures = [DistanceDimensionMapper(), SizeDimensionMapper(), IntensityDimensionMapper()]
		self.kdTrees = []
		
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
		print "Reading from file = '%s'"%filename
		
		if os.path.exists(filename):
			self.reader = ParticleReader.ParticleReader(filename, filterObjectSize = self.filterObjectSize)
			self.particles = self.reader.read(statsTimepoint = statsTimepoint)
				
	def getParticles(self, timepoint, objs):
		"""
		return the particles in given timepoint with given int.values
		"""
		# Return all the particles in given timepoint where the object number is within the given
		# objects
		return [i for i in self.particles[timepoint] if i.objectNumber() in objs]
				
		
	def getTracks(self):
		"""
		@return the tracks
		"""
		return self.tracks
		

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
		for i, pts in enumerate(self.particles):
			print "There are %d particles in timepoint %d" % (len(pts), i)
			for particle in pts:
				#print "Calculating initial information for timepoint %d"%i
				#for particle2 in pts:
				#	if particle.intensityValue == particle2.intensityValue:
				#		continue
					#for measure in self.measures:
					#	measure.calculateInitialInfo(i, particle, particle2)
				self.maxIntensity = max(self.maxIntensity, particle.intensityValue)#, particle2.intensityValue)

			print "Creating KD-tree"
			kdTree = KDTree(2, 0, pts)
			self.kdTrees.append(kdTree)
			
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
		
	def score(self, testParticle, oldParticle, track):
		"""
		Measure the match score between two particles. Returns 
					 a 3 - tuple (distFactor, sizeFactor, intFactor )if there's a match
					and none otherwise	  
		"""
		sizeChange = float(abs(testParticle.size - oldParticle.size))
		sizeFactor = sizeChange / oldParticle.size
		
		if sizeFactor > self.sizeChange:
			return 99999999999999
		
		intFactor = float(abs(testParticle.averageIntensity - oldParticle.averageIntensity))
		intFactor /= self.maxIntensity

		angleFactor = 1
		if len(track)>1:
			angleFactor = self.calculateAngleFactor(testParticle, track)
#			
			if angleFactor==-1:
				return 9999999
				
		if intFactor > self.intensityChange:
			return 9999999999

		return self.sizeWeight * sizeFactor + self.intensityWeight * intFactor + self.directionWeight * angleFactor
#		return angleFactor+abs(float(testParticle.size-oldParticle.size))/oldParticle.size+abs(float(testParticle.averageIntensity-oldParticle.averageIntensity))/oldParticle.averageIntensity
		
	@staticmethod
	def angle(particle1, particle2):
		"""
		Measure the "angle" between horizontal axis and the line defined
					 by the two particles
		"""
		particle1X, particle1Y = particle1.pixelPosition[0:2]
		particle2X, particle2Y = particle2.pixelPosition[0:2]
		ang = math.atan2(particle2Y - particle1Y, particle2X - particle1X) * 180.0 / math.pi
		ang2 = ang
		if ang < 0:
			ang2 = 180 + ang
		return ang,ang2
		
	def toScore(self, distFactor, sizeFactor, intFactor, angleFactor = 1):	
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
		print track
		lastItem = track[-1]
		secondLast = track[-2]
		rangle, absang = self.angle(secondLast, lastItem)
		rangle2, absang2 = self.angle(lastItem, testParticle)
		
		#print "angles=",absang, absang2
		angdiff = abs(absang - absang2)
		# If angle*angle2 < 0 then either (but not both) of the angles 
		# is negative, so the particle being tested is in wrong direction
		#print angle, angle2
		if rangle * rangle2 < 0:
			return -1
		elif  angdiff > self.angleChange:
			return -1
		else: 
			angleFactor = float(angdiff) / self.angleChange
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
#		minDists, maxDists, avgDist, minSiz, maxSiz, minInt, maxInt = self.getStats()
		self.getStats()

#		maxDist = max(maxDists)
#		minDist = min(minDists)
#		print "minDist=",minDist,"maxDist=",maxDist
#		self.maxVelocity = maxDist - minDist
#		self.maxSize = maxSiz - minSiz
#		self.maxIntensity = maxInt - minInt

		if seedParticles:
			tracks, self.particleList = self.getParticlesFromSeedpoints(fromTimepoint, seedParticles)
		else:
			self.particleList = self.particles

		timePoint = fromTimepoint
		# Iterate over all particles in given timepoint
		print "There are ",len(self.particleList), "timepoints"
		print len(self.particleList[0]), "objects in timepoint 0"
		for i, particle in enumerate(self.particleList[timePoint]):
			print "\nTracking particle %d / %d in timepoint %d" % (i, len(self.particleList[timePoint]), timePoint)
			self.trackParticle(particle, fromTimepoint, tracks)
		self.tracks = tracks
		print "Generated tracks=",tracks
			
	def trackParticle(self, particle, timePoint, tracks):
		"""
		Track the given particle from given timepoint on
		@param particle the particle to track
		@param timepoint track from this timepoint on 
		"""
		if not self.seedParticles:
			print "New track starts"
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
			possibleParticles = self.kdTrees[search_timePoint].neighborsInRange(particle, self.maxSpeed)
			if not possibleParticles:
				print "No possible particles within distance", self.maxSpeed
				break
#			print "Found",len(possibleParticles),"candidates in range",self.maxSpeed
			matching = []
			for matchParticle in possibleParticles:
				if dist2(matchParticle,particle) >= self.minSpeed**2:
					matching.append(matchParticle)
			possibleParticles = matching
			match = None
			matchScore = 9999
			print "Evaluating", len(possibleParticles),"particles"
			for matchParticle in possibleParticles:
				if matchParticle.inTrack: continue
				
				currentScore = self.score(matchParticle, particle,  track)
#				print "Score with distance",particle.physdist(matchParticle),"=",currentScore
				if currentScore < matchScore:
					match = matchParticle
					matchScore = currentScore
				
			if match:
				print "Found match with distance=", match.physdist(particle), "score=", matchScore
				track.append(match)
				match.inTrack = True
				match.trackNum = self.trackCount
				searchOn = True
		print "Generated track of length",len(track)
		tracks.append(track)
		
