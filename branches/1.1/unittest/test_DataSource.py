import unittest
from lib.DataSource.DataSource import DataSource

class TestSample(unittest.TestCase):

	def setUp(self):
#		dataSource = DataSource()
		pass

	def tearDown(self):
		pass

	def testGetCacheKey(self):
		winFileName = "Data\\DataFile"
		unixFileName = "Data/DataFile"
#		macFileName = "Data:DataFile"
		channelName = "DataChannel"
		purpose = "Purpose"
		resultKey = "Data_DataFile_DataChannel_Purpose"
		self.assertEquals(DataSource.getCacheKey(winFileName, channelName, purpose), resultKey)
		self.assertEquals(DataSource.getCacheKey(unixFileName, channelName, purpose), resultKey)
		self.assertEquals(DataSource.getCacheKey(winFileName, channelName, purpose), resultKey)

if __name__ == "__main__":
	unittest.main()
