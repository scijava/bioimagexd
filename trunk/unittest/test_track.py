# TestCase for lib.Track

import os.path
import sys
import unittest

runningScriptPath = sys.argv[0]
unittestPath = os.path.dirname(runningScriptPath)

import lib.Track

class TrackTest(unittest.TestCase):
	
	def setUp(self):
		"""
		Description: Create a test Track and a test Time range (mintp - maxtp)
		"""
		self.testMintp = 1
		self.testMaxtp = 5
	
		self.testTrack = lib.Track.Track()
		self.testTrack.mintp = self.testMintp
		self.testTrack.maxtp = self.testMaxtp

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
