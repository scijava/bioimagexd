# TestCase for GUI.MenuManager

import unittest
import GUI.MenuManager

class MenuManagerTest(unittest.TestCase):
	
	def setUp(self):
		"""
		Created: 16.07.2007, SS
		Description:
		"""
		self.testMenuManager = GUI.MenuManager.MenuManager(None)

		self.testCommand = "lol"
		self.testCommand2 = "loller"

	def testAddCommand(self):
		"""
		Created: 16.07.2007, SS
		Description: Test for method addCommand()
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
		Created: 16.07.2007, SS
		Description: Test for method getLastCommand()
		"""
		lastOne = 8
		self.testMenuManager.commands = [1, 4, 7, lastOne]
		self.assertEqual(self.testMenuManager.getLastCommand(), lastOne)

	def testRemoveSeparator(self):
		"""
		Created: 16.07.2007, SS
		Description: Test for method 
		"""
		pass

	def testCheck(self):
		"""
		Created: 16.07.2007, SS
		Description: Test for method 
		"""
		pass

	def testIsChecked(self):
		"""
		Created: 16.07.2007, SS
		Description: Test for method 
		"""
		pass

	def testAddSubMenu(self):
		"""
		Created: 16.07.2007, SS
		Description: Test for method 
		"""
		pass

#run
if __name__ == "__main__":
	unittest.main()
