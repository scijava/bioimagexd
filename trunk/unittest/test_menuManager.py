# TestCase for GUI.MenuManager

import unittest
import GUI.MenuManager

class MenuManagerTest(unittest.TestCase):
	
	def setUp(self):
		"""
		Description:
		"""
		self.testMenuManager = GUI.MenuManager.MenuManager(None)

		self.testCommand = "lol"
		self.testCommand2 = "loller"

	def testAddCommand(self):
		"""
		Test for method addCommand()
					Tests that if a command is added, it will appear on the end of the list.
					If the command already exist on the list, it will not be added
		"""
		self.testMenuManager.addCommand(self.testCommand)
		self.assertEqual(self.testMenuManager.commands, [self.testCommand])
		self.testMenuManager.addCommand(self.testCommand)
		self.assertEqual(self.testMenuManager.commands, [self.testCommand])
		self.testMenuManager.addCommand(self.testCommand2)
		self.assertEqual(self.testMenuManager.commands, [self.testCommand, self.testCommand2])

	def testGetLastCommand(self):
		"""
		Test for method getLastCommand()
		"""
		lastOne = 8
		self.testMenuManager.commands = [1, 4, 7, lastOne]
		self.assertEqual(self.testMenuManager.getLastCommand(), lastOne)

	def testRemoveSeparator(self):
		"""
		Test for method 
		"""
		pass

	def testCheck(self):
		"""
		Test for method 
		"""
		pass

	def testIsChecked(self):
		"""
		Test for method 
		"""
		pass

	def testAddSubMenu(self):
		"""
		Test for method 
		"""
		pass

#run
if __name__ == "__main__":
	unittest.main()
