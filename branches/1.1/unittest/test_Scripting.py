import unittest
import scripting

class TestSample(unittest.TestCase):
	def setUp(self):
		pass

	def tearDown(self):
		pass

	def testGetCacheKey(self):
		testPaths = ["path1", "path2"]
		testNames = ['name1', 'name2']
		testTaskname = 'taskname'
		expectedKey = ('path1', 'path2', 'taskname', 'name1', 'name2')
		self.assertEquals(scripting.getCacheKey(testPaths, testNames, testTaskname), expectedKey)

# run
if __name__ == "__main__":
	unittest.main()
