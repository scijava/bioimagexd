# TestCase for lib.FilterBasedModule

import unittest

import lib.FilterBasedModule

class FilterBasedModuleTest(unittest.TestCase):

	def setUp(self):
		"""
		Creating test data
		"""
		self.testFilterBasedModule = lib.FilterBasedModule.FilterBasedModule()	
		
		self.oldModifiedFlag = 0
		self.newModifiedFlag = 24398238
		self.testFilterBasedModule.modified = self.oldModifiedFlag

		self.testCached = 1
		self.testCachedTimepoint = 10213
		self.testImages = ['lol', 'lol2']
		self.testExtent = 1

		self.testXSize = 1
		self.testYSize = 2
		self.testZSize = 3

		self.testShift = 2
		self.testScale = 43


	def testSetModified(self):
		"""
		A test for setModified()

		A test checking if the parameters are flaged
		"""

		self.assertEqual(self.testFilterBasedModule.modified, self.oldModifiedFlag)
		self.testFilterBasedModule.setModified(self.newModifiedFlag)
		self.assertEqual(self.testFilterBasedModule.modified, self.newModifiedFlag)


	def testReset(self):
		"""
		Testing reset()

		A test to check that the values get reseted
		"""

		self.testFilterBasedModule.cached = self.testCached
		self.testFilterBasedModule.cachedTimepoint = self.testCachedTimepoint
		self.testFilterBasedModule.images = self.testImages
		self.testFilterBasedModule.extent = self.testExtent
		self.testFilterBasedModule.xSize = self.testXSize
		self.testFilterBasedModule.ySize = self.testYSize
		self.testFilterBasedModule.zSize = self.testZSize
		self.testFilterBasedModule.shift = self.testShift
		self.testFilterBasedModule.scale = self.testScale

		self.testFilterBasedModule.reset()
		
		self.assertEqual(self.testFilterBasedModule.cached, None)
		self.assertEqual(self.testFilterBasedModule.cachedTimepoint, -1)
		self.assertEqual(self.testFilterBasedModule.images, [])
		self.assertEqual(self.testFilterBasedModule.extent, None)
		self.assertEqual(self.testFilterBasedModule.xSize, 0)
		self.assertEqual(self.testFilterBasedModule.ySize, 0)
		self.assertEqual(self.testFilterBasedModule.zSize, 0)
		self.assertEqual(self.testFilterBasedModule.shift, 0)
		self.assertEqual(self.testFilterBasedModule.scale, 1)


	def testAddInput(self):
		"""
		Description:
		"""

		pass


	def testGetPreview(self):
		"""
		Description
		"""

		pass


	def testDoOperation(self):
		"""
		Description:
		"""

		pass


#run
if __name__ == "__main__":
	unittest.main()
