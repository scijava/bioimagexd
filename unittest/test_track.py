# TestCase for lib.Track

import math
import os.path
import sys
import unittest

runningScriptPath = sys.argv[0]
unittestPath = os.path.dirname(runningScriptPath)

import lib.Track

class TrackTest(unittest.TestCase):
	
	def setUp(self):
		"""
		Description: Create a test Track and other test data
		"""
		self.testMintp = 1
		self.testMaxtp = 5
	
		self.testTrack = lib.Track.Track()
		self.testTrack.mintp = self.testMintp
		self.testTrack.maxtp = self.testMaxtp

		self.point1 = (0, 0, 0)
		self.point2 = (3, 3, 3)
		self.point3 = (5, 5, 5)
		self.point4 = (7, 7, 7)
		self.point5 = (2, 2, 2)

	def testDistance(self):
		"""
		Created: 14.8.2007, SS
		Description: Test the method Distance()
		"""
		t1 = 1
		t2 = 2
		t3 = 3
		t4 = 4
		self.testTrack.points[t1] = self.point1
		self.testTrack.points[t2] = self.point2
		self.testTrack.points[t3] = self.point3

		errormsg = "this timepoint should not exist, should give result 0"

		# check that we get the result '0' for timepoints that dont exist
		self.assertEqual(self.testTrack.distance(t1, t4), 0, errormsg)
		self.assertEqual(self.testTrack.distance(t4, t3), 0, errormsg)
		self.assertEqual(self.testTrack.distance(t4, t4), 0, errormsg)

		# check that returns correct results for other values
		self.assertEqual(self.testTrack.distance(t1, t2), math.sqrt(27))
		self.assertEqual(self.testTrack.distance(t3, t3), 0)

	def testGetLengthSmallValues(self):
		"""
		Created: 14.8.2007, SS
		Description: Test the method getLength() and how it reacts on small values
		"""
		# in initialization length should be -1
		self.assertEqual(self.testTrack.length, -1)

		# after initialization length is -1 and getLength() should return 0
		# length should change to 0
		self.assertEqual(self.testTrack.getLength(), 0)
		self.assertEqual(self.testTrack.length, 0)

		# if length has value 0, getLength() should return 0
		self.assertEqual(self.testTrack.getLength(), 0)

	def testGetLength(self):
		"""
		Created: 14.8.2007, SS
		Description: Test the method getLength(), this should return the total length of the track
		"""
		t1 = 1
		t2 = 2
		t3 = 3
		t4 = 4
		t5 = 5

		self.testTrack.mintp = t1
		self.testTrack.maxtp = t5

		self.testTrack.points[t1] = self.point1
		self.testTrack.points[t2] = self.point2
		self.testTrack.points[t3] = self.point3
		self.testTrack.points[t4] = self.point4
		self.testTrack.points[t5] = self.point5

		totalLength = math.sqrt(27) + math.sqrt(12) + math.sqrt(12) + math.sqrt(75)
		self.assertEqual(self.testTrack.getLength(), totalLength)

	def testGetSpeedNone(self):
		"""
		Created: 14.8.2007, SS
		Description: Test the method getSpeed() with a 0 speed value
		"""
		# in initialization, getLength() should return 0
		# maxtp - mintp (5 - 1) should return 4
		self.assertEqual(self.testTrack.getSpeed(), 0)

	def testGetSpeed(self):
		"""
		Created: 14.8.2007, SS
		Description: Test the method getSpeed()
		"""
		# we use the same values as in testGetLength()
		t1 = 1
		t2 = 2
		t3 = 3
		t4 = 4
		t5 = 5

		self.testTrack.mintp = t1
		self.testTrack.maxtp = t5

		self.testTrack.points[t1] = self.point1
		self.testTrack.points[t2] = self.point2
		self.testTrack.points[t3] = self.point3
		self.testTrack.points[t4] = self.point4
		self.testTrack.points[t5] = self.point5

		totalLength = math.sqrt(27) + math.sqrt(12) + math.sqrt(12) + math.sqrt(75)
		tpDifference = t5 - t1

		self.assertEqual(self.testTrack.getSpeed(), (totalLength/tpDifference))

	def testGetDirectionalPersistence(self):
		"""
		Created: 14.8.2007, SS
		Description: Test the method getDirectionalPersistence()
		"""
		# we use the same values as in testGetLength()
		t1 = 1
		t2 = 2
		t3 = 3
		t4 = 4
		t5 = 5

		self.testTrack.mintp = t1
		self.testTrack.maxtp = t5

		self.testTrack.points[t1] = self.point1
		self.testTrack.points[t2] = self.point2
		self.testTrack.points[t3] = self.point3
		self.testTrack.points[t4] = self.point4
		self.testTrack.points[t5] = self.point5

		totalLength = math.sqrt(27) + math.sqrt(12) + math.sqrt(12) + math.sqrt(75)
		totalMovement = math.sqrt(12)
		expectedDirectionalPersistence = totalMovement / totalLength

		self.assertEqual(self.testTrack.getDirectionalPersistence(), expectedDirectionalPersistence)

	def testGetAverageAngle(self):
		"""
		Created: 14.8.2007, SS
		Description: Test the method getAverageAngle()
		"""
		pass

	def testAddTrackPointMintp(self):
		"""
		Description: Test the method addTrackPoint()
		Test that mintp gets a new value if timepoint is less than it
		"""	
		timepoint = -1
		objval = 4
		position = (1, 2, 3)

		self.testTrack.addTrackPoint(timepoint, objval, position)
		self.assertEqual(self.testTrack.mintp, timepoint)
		self.assertEqual(self.testTrack.maxtp, self.testMaxtp)

		# Test that position and objval values are correct

		self.assertEqual(self.testTrack.points[timepoint], position)
		self.assertEqual(self.testTrack.values[timepoint], objval)

	def testAddTrackPointMaxtp(self):
		"""
		Description: Test the method addTrackPoint()
		Test that maxtp gets a new value if timepoint is greater than it
		"""
		timepoint = 6
		objval = 5
		position = (3, 2, 1)

		self.testTrack.addTrackPoint(timepoint, objval, position)
		self.assertEqual(self.testTrack.maxtp, timepoint)
		self.assertEqual(self.testTrack.mintp, self.testMintp)

		# Test that position and objval values are correct

		self.assertEqual(self.testTrack.points[timepoint], position)
		self.assertEqual(self.testTrack.values[timepoint], objval)

	def testGetTimeRange(self):
		"""
		Description: Test the method getTimeRange()
		Test that mintp and maxtp are correct
		"""
		self.assertEqual(self.testTrack.getTimeRange(), (self.testMintp, self.testMaxtp))

	def testGetObjectAtTime(self):
		"""
		Description: Test the method getObjectAtTime()
		getObjectAtTime should return (objval, position) if timepoint exists in track,
		else it should return (-1, (-1,-1,-1))
		"""
		timepoint = 2
		falsetimepoint = 22
		objval = 2
		position = (2, 2, 2)

		self.testTrack.addTrackPoint(timepoint, objval, position)
		self.assertEqual((self.testTrack.getObjectAtTime(timepoint)), (objval, position))
		self.assertEqual((self.testTrack.getObjectAtTime(falsetimepoint)), (-1, (-1, -1, -1)))

class TrackReaderTest(unittest.TestCase):	
	
	def setUp(self):
		"""
		Description: Create a test TrackReader and other test data
		"""
		self.filename = os.path.join(unittestPath, "testdata", "tracks.csv")
		self.testTrackReader = lib.Track.TrackReader(self.filename)
		self.expectedAmountOfTracks = 7
		self.expectedAmountOfBigEnoughTracks = 5
		self.expectedLengthOfLongestTrack = 18
	
	def testCountTracks(self):
		"""
		Description: Test that readTracks() returns correct amount of tracks in tracks[]
		Method readTracks() is called from __init__

		This failed with the old code
		"""
		self.assertEqual(len(self.testTrackReader.tracks), self.expectedAmountOfTracks)

	def testReadFromFile(self):
		"""
		Description: Test that readFromFile() changes the value of self.maxLength
		"""
		self.testTrackReader.maxLength = -1
		oldMaxLength = self.testTrackReader.maxLength
		self.testTrackReader.readFromFile(self.filename)
		newMaxLength = self.testTrackReader.maxLength
		self.assertNotEqual(oldMaxLength, newMaxLength)
	
	def testGetMaximumTrackLength(self):
		"""
		Description: Test that getMaximumTrackLength() returns the length of longest track
		"""
		self.assertEqual(self.testTrackReader.getMaximumTrackLength(), self.expectedLengthOfLongestTrack)

	def testGetNumberOfTracks(self):
		"""
		Description: Test that getNumberOfTracks returns correct amount of tracks in tracks[] with length > 3
		"""
		self.assertEqual(self.testTrackReader.getNumberOfTracks(), self.expectedAmountOfBigEnoughTracks)

	def testGetTracks(self):
		"""
		Description: Test that getTracks() returns correct amount of tracks in tracks[] with length > 3
		"""
		temptracks = self.testTrackReader.getTracks()
		self.assertEqual((len(temptracks)), self.expectedAmountOfBigEnoughTracks)

	def testReadTracks(self):
		"""
		Description: Test that readTracks() works correctly and tracks[] is not empty
		"""
		self.assertEqual(bool(self.testTrackReader.tracks), True)

#run
if __name__ == "__main__":
	unittest.main()
