# TestCase for lib.Command

import unittest
import lib.Command

class CommandTest(unittest.TestCase):
	
	def setUp(self):
		"""
		Creating a test Command and other test data
		"""
		self.testUndocmd = "Test UndoCommand"
		self.testCategory = "Test Category"
		self.testDesc = "Test Description"
		self.testCommand = lib.Command.Command(self.testCategory, None, None, \
							"", "", None, self.testDesc)
		self.testImports = []
		self.testCode = "I\nam\na\npiece\nof\ntest\ncode"
		self.testCodeEmpty = ""
		self.test_Undoed = 1

		# in Command.py functionize() adds following string before codestrings
		self.functionizeString = "	"

	def tearDown(self):
		pass

	def testFunctionizeEmptyValues(self):
		"""
		A test for the functionize() method
		Tests that functionize modifies the inputtext, even with empty values
		"""
		testCodeModified = self.testCommand.functionize(self.testCodeEmpty, self.testImports)
		self.assertNotEqual(self.testCodeEmpty, testCodeModified, msg = "Original input equals modified")
		
	def testFunctionize(self):
		"""
		A test for the functionize() method
		Tests that functionize modifies the text correctly
		Every line in modifiedLines[i] should be equal to ("    " + originalLines[i])
		"""
		testCodeModified = self.testCommand.functionize(self.testCode, self.testImports)
		modifiedLines = testCodeModified.split("\n")
		originalLines = self.testCode.split("\n")

		for i, line in enumerate(originalLines):
			self.assertEqual(modifiedLines[i], (self.functionizeString + originalLines[i]))

	def testGetDesc(self):
		"""
		A test for the getDesc() method
		Checks that getDesc() returns the "desc" input value of a Command object
		"""
		self.assertEqual(self.testDesc, self.testCommand.getDesc())

	def testIsUndoed(self):
		"""
		A test for the isUndoed() method
		Tests that isUndoed() returns the correct "_undoed" value
		"""
		self.testCommand._undoed = self.test_Undoed
		self.assertEqual(self.testCommand.isUndoed(), self.test_Undoed)

	def testCanUndo(self):
		"""
		A test for the CanUndo() method
		Tests that the output is true or false
		"""
		self.assertEqual(self.testCommand.canUndo(), bool(self.testCommand.undocmd))

	def testRun(self):

		pass

	def testUndo(self):

		pass

	def testGetCategory(self):
		"""
		A test for the getCategory() method
		Tests that getCategory() returns the "category" input value of a Command object
		"""
		self.assertEqual(self.testCategory, self.testCommand.getCategory())

#run
if __name__ == "__main__":
	unittest.main()
