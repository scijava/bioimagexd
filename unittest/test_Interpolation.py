# Welcome to unittest example!
#
# Name all testing files starting with 'test_'
# and place them in 'unittest' directory.
# Make runs these files magically.
# This file has been renamed so that it won't be run every time you run make test.
#
# The test result report is placed into 'unittest/results'
# and named after date and time of test execution.
# Also edited the makefile to automatically show the latest results.

import unittest
import bxdexceptions
import Interpolation

class TestSample(unittest.TestCase):
	def setUp(self):
		# write things to be done at setup time
		pass

	def tearDown(self):
		# write things to be done at test end time
		pass

	def testDifferentlySizedParameterLists(self):
		"""
		Created: 08.06.2007, SG
		Description: Check that an exception is raised when two differently sized lists are given as parameters.
		"""
		parameterList1 = [1, 2, 3]
		parameterList2 = [1, 2]
		self.assertRaises(bxdexceptions.IncorrectSizeException, Interpolation.linearInterpolation, \
							parameterList1, parameterList2, 2)
	
	def testCorrectResultForSimpleList(self):
		"""
		Created: 11.06.2007, SG
		Test that a correct result is returned for two small lists.
		"""
		parameterList1 = [2, 4, 3]
		parameterList2 = [12, 9, 3]
		n = 4
		expectedList = [[4, 5, 3], [6, 6, 3], [8, 7, 3], [10, 8, 3]]
		resultList = Interpolation.linearInterpolation(parameterList1, parameterList2, n)
		self.assertEqual(expectedList, resultList)

	def testEmptyListReturnedWhenNIsZero(self):
		"""
		Created: 11.06.2007, SG
		Test that an empty list is returned when n is 0.
		"""
		parameterList1 = [1.2, 3.4, 4.5]
		parameterList2 = [2.0, 5, 6.7]
		self.assertEqual([], Interpolation.linearInterpolation(parameterList1, parameterList2, 0))
	
	def testResultForEmptyLists(self):
		"""
		Created 11.06.2007, SG
		Test that a list of n empty lists is returned when two empty lists are used as input.
		Not sure if this is the intended behaviour though. It's what the method does though.
		"""
		n = 50
		resultList = Interpolation.linearInterpolation([], [], n)
		expectedList = [[] for x in range(n)]
		self.assertEqual(expectedList, resultList)
		self.assertEqual(n, len(resultList))

	def testEmptyListReturnedWhenNIsNegative(self):
		"""
		Created: 11.06.2007, SG
		Test that an empty list is returned when n is negative.
		"""
		parameterList1 = [1.2, 3.4, 4.5]
		parameterList2 = [2.0, 5, 6.7]
		self.assertEqual([], Interpolation.linearInterpolation(parameterList1, parameterList2, -10))


# Include this in all test cases.
# It is used by make to run the tests magically.
if __name__ == "__main__":
	unittest.main()
