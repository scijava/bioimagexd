# TestCase for lib.Particle

import sys
import os.path
import math
import random
import csv
import unittest

runningScriptPath = sys.argv[0]
unittestPath = os.path.dirname(runningScriptPath)

import lib.Particle

class ParticleReaderTest(unittest.TestCase):
	
	def setUp(self):
	
		# Read the file before each test, this should probably be optimized 
		# so that it does not need to be run again for every test
		# because there will be an large overhead for reading the file (6MB) multiple times

		self.filename = os.path.join(unittestPath, "testdata", "particles.csv")
		self.testReader = lib.Particle.ParticleReader(self.filename)
#		self.testReader = lib.Particle.ParticleReader("unittest/testdata/particles.csv")
		self.particleList = self.testReader.read()

	def testRead(self):
	
		# Test the read()-method to see that we get the correct amount of objects 
		# and verify that all the objects that we read contain all the required info
		# There should be the exact same amount of objects, volumes, centres of masses and intensities
	
		self.objectList = self.testReader.getObjects()
		objectCount = len(self.objectList)
		volumeCount = len(self.testReader.getVolumes())
		centerOfMassCount = len(self.testReader.getCentersOfMass())
		intensityCount = len(self.testReader.getAverageIntensities())
		
		self.assertEqual(objectCount, 13)
		self.assertEqual(objectCount, volumeCount)
		self.assertEqual(objectCount, centerOfMassCount)
		self.assertEqual(objectCount, intensityCount)

	def testIfObjectsExistForAllTimepoints(self):

		# Test that no list of objects is empty, that is, that every timePoint has at least one object in it

		for currList in self.particleList:
			self.assertNotEqual(len(currList), 0)

class ParticleTest(unittest.TestCase):	
	
	def setUp(self):
		self.p1 = lib.Particle.Particle((0, 0, 0), (3, 3, 3), 1, 2, 50, -2)
	
	def testCopy(self):
		
		# Test copy() and all the get-functions
		
		p8 = lib.Particle.Particle()
		p8.copy(self.p1)
		distance = self.p1.distance(p8)
		centerOfMassX, centerOfMassY, centerOfMassZ = p8.getCenterOfMass()
		objectNumber = p8.objectNumber()
		self.assertEqual(distance, 0)
		self.assertEqual(centerOfMassX, 3)
		self.assertEqual(centerOfMassY, 3)
		self.assertEqual(centerOfMassZ, 3)
		self.assertEqual(objectNumber, -2)		
	
	def testSelfDistance(self):
		
		# Test distance to self
		# This must give 0 for any particle, so we use random
		
		particle = lib.Particle.Particle((random.randint(-1000, 1000), random.randint(-1000, 1000), \
											random.randint(-1000, 1000)))
		distance = particle.distance(particle)
		self.assertEqual(distance, 0)

	def testDistanceZOf1(self):
		
		# Test distance to particles on a range of 1, one test per dimension
		
		p2 = lib.Particle.Particle((0, 0, 1))
		distanceZ = self.p1.distance(p2)
		self.assertEqual(distanceZ, 1)

	def testDistanceYOf1(self):
		
		p3 = lib.Particle.Particle((0, 1, 0))
		distanceY = self.p1.distance(p3)
		self.assertEqual(distanceY, 1)

	def testDistanceXOf1(self):
		
		p4 = lib.Particle.Particle((1, 0, 0))
		distanceX = self.p1.distance(p4)
		self.assertEqual(distanceX, 1)

	def testDistanceToNegativeZ(self):
	
		# Test distance to a particle with negative X, Z and Y-coordinates
		
		p7a = lib.Particle.Particle((0, 0, -1))
		distance = self.p1.distance(p7a)	
		self.assertEqual(distance, 1)

	def testDistanceToNegativeY(self):
		p7b = lib.Particle.Particle((0, -1, 0)) 
		distance = self.p1.distance(p7b)	
		self.assertEqual(distance, 1)

	def testDistanceToNegativeX(self):
		p7c = lib.Particle.Particle((-1, 0, 0))
		distance = self.p1.distance(p7c)	
		self.assertEqual(distance, 1)

	def testDistance2Dims(self):		 
		
		# Test distance to a particle with coordinates differing with 1 unit in 2 dimensions
		
		p5 = lib.Particle.Particle((0, 1, 1))
		distance = self.p1.distance(p5)
		self.assertAlmostEqual(distance, math.sqrt(2), 10)		

	def testDistance3Dims(self):		
		
		# Test distance when the particles differ in 3 dimensional coordinates
		
		p6 = lib.Particle.Particle((1, 1, 1))
		distance = self.p1.distance(p6)
		self.assertAlmostEqual(distance, math.sqrt(3), 10)

	def testDistanceFarFarAway(self):
		
		# Test distance to a particle located far away
		
		p9 = lib.Particle.Particle((800, 800, 50))	
		distance = self.p1.distance(p9)
		self.assertAlmostEqual(distance, math.sqrt(800*800+800*800+50*50))

	def testDistanceRandom(self):
		
		# Test distance between two randomly generated particles
		# I am sure this can be shortened by some obscure code ;)

		x1 = random.randint(-1000, 1000)
		y1 = random.randint(-1000, 1000)
		z1 = random.randint(-1000, 1000)
		x2 = random.randint(-1000, 1000)
		y2 = random.randint(-1000, 1000)
		z2 = random.randint(-1000, 1000)

		part1 = lib.Particle.Particle((x1, y1, z1))
		part2 = lib.Particle.Particle((x2, y2, z2))
		distance1to2 = part1.distance(part2)
		distance2to1 = part2.distance(part1)
		self.assertEqual(distance1to2, distance2to1)
		dx = x1 - x2
		dy = y1 - y2
		dz = z1 - z2
		self.assertEqual(distance1to2, math.sqrt(dx*dx+dy*dy+dz*dz))

	def testStr(self):
		
		# Test that the __str__ function returns what is expected of it

		strInfo = self.p1.__str__()
		self.assertEqual(strInfo, r"<Obj#-2 (3,3,3) t=1, inTrack=False>")
		reprInfo = self.p1.__repr__()
		self.assertEqual(strInfo, reprInfo)

class ParticleTrackerTest(unittest.TestCase):

	def setUp(self):
		"""
		Created: 08.06.2007, SS
		Description: Create a test particleTracker and other test data

		Particle parameters:
		The first parameter defines the distance (p.pos)
		The second parameter defines the position in pixels (p.intpos)
		The third parameters defines the current timepoint
		The fourth parameter defines the size of the particle
		The fifth parameter defines the average intensity of the particle
		The sixth parameter defines the object number
		"""

		self.p1  = lib.Particle.Particle( (0, 0, 0), ( 0, 0, 0), 0, 1, 20, -1)
		self.p2  = lib.Particle.Particle( (5, 5, 5), ( 5, 5, 5), 0, 6, 25, -1)

		self.p3  = lib.Particle.Particle( (0, 0, 0), ( 0, 1, 0), 0, 1, 20, -1)
		self.p4  = lib.Particle.Particle( (0, 0, 0), ( 0, -1, 0), 0, 1, 20, -1)

		self.p5  = lib.Particle.Particle( (0, 0, 0), ( 1, 0, 0), 0, 1, 20, -1)
		self.p6  = lib.Particle.Particle( (0, 0, 0), (-1, 0, 0), 0, 1, 20, -1)

		self.p7  = lib.Particle.Particle( (0, 0, 0), ( 1, 1, 0), 0, 1, 20, -1)
		self.p8  = lib.Particle.Particle( (0, 0, 0), (-1, 1, 0), 0, 1, 20, -1)
		self.p9  = lib.Particle.Particle( (0, 0, 0), ( 1, -1, 0), 0, 1, 20, -1)
		self.p10 = lib.Particle.Particle( (0, 0, 0), (-1, -1, 0), 0, 1, 20, -1)

		self.partTracker = lib.Particle.ParticleTracker()

		self.testMinimumTrackLength = 10
		self.testFilterObjectSize = 10
		self.filename = os.path.join(unittestPath, "testdata", "particles.csv")
		self.filenameWrite = os.path.join(unittestPath, "testdata", "tracksWrite.csv")

		self.oldDistanceChange = 1
		self.oldSizeChange = 1
		self.oldIntensityChange = 1
		self.oldAngleChange = 1

		self.testDistanceChange = 3
		self.testSizeChange = 3
		self.testIntensityChange = 3
		self.testAngleChange = 1.5
	
		self.partTracker.distanceChange = self.oldDistanceChange 
		self.partTracker.sizeChange = self.oldSizeChange
		self.partTracker.intensityChange = self.oldIntensityChange
		self.partTracker.angleChange = self.oldAngleChange
	
		self.testMaxVelocity = 10
		self.testMaxSize = 10
		self.testMaxIntensity = 10

		self.testVelocityWeight = 10
		self.testIntensityWeight = 10
		self.testDirectionWeight = 10
		self.testSizeWeight = 10

		self.testDistanceFactor = 4
		self.testSizeFactor = 4
		self.testIntensityFactor = 4
		self.testAngleFactor = 4

		self.partTracker.maxVelocity = self.testMaxVelocity
		self.partTracker.maxSize = self.testMaxSize
		self.partTracker.maxIntensity = self.testMaxIntensity

		# these values work for the current: the 0 particle is not consider
		# self.expectedMinSize == 1 is not accepted because 1 < ParticleReader.filterObjectSize (== 2)
		# self.expectedMinInt == 1.7392614922 is not accepted because the particle is not (check previous line)
		# self.expectedMaxInt == 74442.22681067 is not accepted because it is the 0 particle

		self.expectedMinSize = 2
		self.expectedMaxSize = 94443
		self.expectedMinInt = 2.7392614922
		self.expectedMaxInt = 64442.22681067

		self.testTimepoint = 0
		self.testObjectNumbers = [1, 2, 3, 4, 5, 6, 7, 8, 9] # "0" is not accepted in ParticleReader

	def testSetMinimumTrackLength(self):
		"""
		Created: 25.06.2007, SS
		Description: A test for method setMinimumTrackLength()
		"""

		oldTrackLength = self.partTracker.minimumTrackLength
		self.partTracker.minimumTrackLength = self.testMinimumTrackLength
		self.assertNotEqual(oldTrackLength, self.partTracker.minimumTrackLength)

	def testSetWeights(self):
		"""
		Created: 25.06.2007, SS
		Description: A test for method setWeights()
		"""

		oldVelocityWeight = self.partTracker.velocityWeight
		oldIntensityWeight = self.partTracker.intensityWeight
		oldDirectionWeight = self.partTracker.directionWeight
		oldSizeWeight = self.partTracker.sizeWeight

		self.partTracker.setWeights(self.testVelocityWeight, \
									self.testSizeWeight, \
									self.testIntensityWeight, \
									self.testDirectionWeight)

		self.assertNotEqual(oldVelocityWeight, self.partTracker.velocityWeight)
		self.assertNotEqual(oldIntensityWeight, self.partTracker.intensityWeight)
		self.assertNotEqual(oldDirectionWeight, self.partTracker.directionWeight)
		self.assertNotEqual(oldSizeWeight, self.partTracker.sizeWeight)

	def testGetReader(self):
		"""
		Created: 25.06.2007, SS
		Description: A test for method getReader()
		"""

		self.assertEqual(self.partTracker.reader, self.partTracker.getReader())

	def testReadFromFile(self):
		"""
		Created: 27.06.2007, SS
		Description: A test for method readFromFile()
		"""

		self.assertEqual(self.partTracker.reader, None)
		self.assertEqual(self.partTracker.particles, None)
		self.partTracker.readFromFile(self.filename)
		self.assertNotEqual(self.partTracker.reader, None)		
		self.assertNotEqual(self.partTracker.particles, None)
		
	def testGetParticles(self):
		"""
		Created: 27.06.2007, SS
		Description: A test for method getParticles()

		Reading particles 1-9 in timepoint 0 and compare the values
		"""

		self.partTracker.readFromFile(self.filename)
		tempParticles = self.partTracker.getParticles(self.testTimepoint, self.testObjectNumbers)

		# The element tempParticles[0] is actually element number 1 in particles.csv
		# This is because ParticleReader.read() skips index 0 in the file

		self.assertEqual(len(tempParticles), len(self.testObjectNumbers))

		self.assertEqual(tempParticles[0].timePoint, self.testTimepoint)
		self.assertEqual(tempParticles[0].size, 795)
		self.assertAlmostEqual(tempParticles[0].averageIntensity, 63.7433962264, 10)

		self.assertAlmostEqual(tempParticles[0].posInPixels[0], 258.34591194968556, 14)
		self.assertAlmostEqual(tempParticles[0].posInPixels[1], 105.5433962264151, 13)
		self.assertAlmostEqual(tempParticles[0].posInPixels[2], 1.9471698113207547, 16)

		self.assertAlmostEqual(tempParticles[0].pos[0], 29.210179878039526, 15)
		self.assertAlmostEqual(tempParticles[0].pos[1], 11.933386386672163, 15)
		self.assertAlmostEqual(tempParticles[0].pos[2], 0.89887781556162416, 17)

	def testGetTracks(self):
		"""
		Created: 25.06.2007, SS
		Description: A test for method getTracks()
		"""

		self.assertEqual(self.partTracker.tracks, self.partTracker.getTracks())

	def testWriteTracks(self):
		"""
		Created: 28.06.2007, SS
		Description: A test for method writeTracks()

		Opening and writing to an empty file tracksWrite.csv
		"""

		self.assertEqual(self.partTracker.tracks, []) #at the moment
		self.partTracker.writeTracks(self.filenameWrite)
		reader = csv.reader(open(self.filenameWrite), dialect = "excel", delimiter = ";")
		self.assertEqual(list(reader), [["Track #", "Object #", "Timepoint", "X", "Y", "Z"]])
		os.remove(self.filenameWrite)

	def testSetFilterObjectSize(self):
		"""
		Created: 26.06.2007, SS
		Description: A test for method setFilterObjectSize()
		"""

		self.assertEqual(self.partTracker.filterObjectSize, 2, "the number 2 comes from ParticleTracker()")
		self.partTracker.setFilterObjectSize(self.testFilterObjectSize)
		self.assertEqual(self.partTracker.filterObjectSize, self.testFilterObjectSize)

	def testGetStats(self):
		"""
		Created: 28.06.2007, SS
		Description: A test for method getStats()

		* warning! this takes about 150 minutes to execute with code coverage...
		- the getStats() method is really complex and takes time to run, also in make test
		- here only the minsize, maxsize, minint and maxint values are tested
		  because it would be too time-consuming to also test for dist[] values
		  (it would involve a nested for-loop)
		"""

		self.partTracker.readFromFile(self.filename)
		mindists, maxdists, avgdists, minSize, maxSize, minInt, maxInt = self.partTracker.getStats()

		self.assertEqual(minSize, self.expectedMinSize)
		self.assertEqual(maxSize, self.expectedMaxSize)
		self.assertAlmostEqual(minInt, self.expectedMinInt, 10)
		self.assertAlmostEqual(maxInt, self.expectedMaxInt, 8)

	def testSetDistanceChange(self):
		"""
		Created: 26.06.2007, SS
		Description: A test for method setDistanceChange()
		"""

		self.assertEqual(self.partTracker.distanceChange, self.oldDistanceChange)
		self.partTracker.setDistanceChange(self.testDistanceChange)
		self.assertEqual(self.partTracker.distanceChange, self.testDistanceChange)

	def testSetSizeChange(self):
		"""
		Created: 26.06.2007, SS
		Description: A test for method setSizeChange()
		"""

		self.assertEqual(self.partTracker.sizeChange, self.oldSizeChange)
		self.partTracker.setSizeChange(self.testSizeChange)
		self.assertEqual(self.partTracker.sizeChange, self.testSizeChange)

	def testSetIntensityChange(self):
		"""
		Created: 26.06.2007, SS
		Description: A test for method setIntensityChange()
		"""

		self.assertEqual(self.partTracker.intensityChange, self.oldIntensityChange)
		self.partTracker.setIntensityChange(self.testIntensityChange)
		self.assertEqual(self.partTracker.intensityChange, self.testIntensityChange)

	def testSetAngleChange(self):
		"""
		Created: 26.06.2007, SS
		Description: A test for method setAngleChange()
		"""

		self.assertEqual(self.partTracker.angleChange, self.oldAngleChange)
		self.partTracker.setAngleChange(self.testAngleChange)
		self.assertEqual(self.partTracker.angleChange, self.testAngleChange)
	
	def testScoreNiceValues(self):
		"""
		Created: 08.06.2007, SS
		Description: A test for method score()

		Tests for distance, size and average intensity values that should give !(None) output
		(p.pos is used)
		"""

		self.assertNotEqual( (self.partTracker.score(self.p1, self.p2)), (None, None, None))

	def testScoreEqualDistance(self):
		"""
		Created: 08.06.2007, SS
		Description: A test for method score()

		Tests for distance values that are equal to biggest allowed values
		The size and intensity values are within the allowed limits
		Output should be !(None)
		(p.pos is used)
		"""

		self.partTracker.maxVelocity = float((self.p1.distance(self.p2)))
		self.assertNotEqual( (self.partTracker.score(self.p1, self.p2)), (None, None, None))

	def testScoreEqualSize(self):
		"""
		Created: 08.06.2007, SS
		Description: A test for method score()

		Tests for size values that are equal to biggest allowed values
		The distance and intensity values are within the allowed limits
		Output should be !(None)
		(p.pos is used)
		"""

		self.partTracker.maxSize = float(abs((self.p1.size) - (self.p2.size)))
		self.assertNotEqual( (self.partTracker.score(self.p1, self.p2)), (None, None, None))

	def testScoreEqualIntensity(self):
		"""
		Created: 08.06.2007, SS
		Description: A test for method score()

		Tests for average intensity values that are the biggest allowed
		The distance and size values are within the allowed limits
		Output should be !(None)
		(p.pos is used)
		"""

		self.partTracker.maxIntensity = float(abs((self.p1.averageIntensity) - (self.p2.averageIntensity)))
		self.assertNotEqual( (self.partTracker.score(self.p1, self.p2)), (None, None, None))


	def testScoreTooBigDistance(self):
		"""
		Created: 08.06.2007, SS
		Description: A test for method score()

		Tests for too big distance values
		(p.pos is used)
		"""

		self.partTracker.maxVelocity = 1
		self.assertEqual( (self.partTracker.score(self.p1, self.p2)), (None, None, None))

	def testScoreTooBigSize(self):
		"""
		Created: 08.06.2007, SS
		Description: A test for method score()

		Tests for too big size values and distance values between allowed limit
		(p.pos is used)
		"""
		
		self.partTracker.maxSize = 1
		self.assertEqual( (self.partTracker.score(self.p1, self.p2)), (None, None, None))

	def testScoreTooBigIntensity(self):
		"""
		Created: 08.06.2007, SS
		Description: A test for method score()

		Tests for too big average intensity values and distance and size values between allowed limit
		(p.pos is used)
		"""

		self.partTracker.maxIntensity = 1
		self.assertEqual( (self.partTracker.score(self.p1, self.p2)), (None, None, None))

	def testAngleNoLine(self):
		"""
		Created: 08.06.2007, SS
		Description: A test for method angle()

		Tests that no angle between horizontal axis and a single point can exist
		(p.intpos is used)
		At the moment, however, the code gives as result (0.0, 0.0) if no angle
		"""

		pcopy = self.p1
		self.assertNotEqual(self.partTracker.angle(self.p1, pcopy), (0.0, 0.0), "This fails with the old code")

	def testAngleZeroDegrees(self):
		"""
		Created: 26.06.2007, SS
		Description: A test for method angle()

		Tests for angle between horizontal axis and a line with 0 or 180 degrees to it
		"""

		self.assertEqual((self.partTracker.angle(self.p1, self.p5)), (  0.0,   0.0))
		self.assertEqual((self.partTracker.angle(self.p1, self.p6)), (180.0, 180.0))

	def testAngleNinetyDegrees(self):
		"""
		Created: 26.06.2007, SS
		Description: A test for method angle()

		Tests for angle between horizontal axis and a line with 90 degrees angle to it,
		and also for the -90 degrees angle
		"""

		self.assertEqual((self.partTracker.angle(self.p1, self.p3)), ( 90.0, 90.0))
		self.assertEqual((self.partTracker.angle(self.p1, self.p4)), (-90.0, 90.0))

	def testAngleFortyfiveDegrees(self):
		"""
		Created: 26.06.2007, SS
		Description: A test for method angle()

		Tests for angle between horizontal axis and a line with 
		45, 135, -45 and -135 degrees angle to it
		"""

		self.assertEqual((self.partTracker.angle(self.p1, self.p7 )), (  45.0,  45.0))
		self.assertEqual((self.partTracker.angle(self.p1, self.p8 )), ( 135.0, 135.0))
		self.assertEqual((self.partTracker.angle(self.p1, self.p9 )), ( -45.0, 135.0))
		self.assertEqual((self.partTracker.angle(self.p1, self.p10)), (-135.0,  45.0))

	def testToScore(self):
		"""
		Created: 26.06.2007, SS
		Description: A test for method toScore()
		"""

		testScore = self.partTracker.toScore(self.testDistanceFactor, \
												self.testSizeFactor, \
												self.testIntensityFactor, \
												self.testAngleFactor)

		toScoreValue = (self.testDistanceFactor * self.partTracker.velocityWeight) + \
						(self.testSizeFactor * self.partTracker.sizeWeight) + \
						(self.testIntensityFactor * self.partTracker.intensityWeight) + \
						(self.testAngleFactor * self.partTracker.directionWeight)

		self.assertEqual(testScore, toScoreValue)

	def testToScoreNoAngleFactor(self):
		"""
		Created: 26.06.2007, SS
		Description: A test for method toScore()

		No parameter given for angleFactor
		"""

		testScore = self.partTracker.toScore(self.testDistanceFactor, \
												self.testSizeFactor, \
												self.testIntensityFactor)

		toScoreValue = (self.testDistanceFactor * self.partTracker.velocityWeight) + \
						(self.testSizeFactor * self.partTracker.sizeWeight) + \
						(self.testIntensityFactor * self.partTracker.intensityWeight) + \
						self.partTracker.directionWeight

		self.assertEqual(testScore, toScoreValue)

	def testTrack(self):

		pass


#run
if __name__ == "__main__":
	unittest.main()
