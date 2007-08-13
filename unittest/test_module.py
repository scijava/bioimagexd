# TestCase for lib.Module


#import Configuration
#import os.path
#import scripting

import lib.Module
import unittest

class ModuleTest(unittest.TestCase):

	def setUp(self):
		"""
		Created: 02.07.2007, MB
		Description: Initialization, test data
		"""

#		conffile = os.path.join(scripting.get_config_dir(), "BioImageXD.ini")
#		cfg = Configuration.Configuration(conffile)

		self.testModule = lib.Module.Module()

		self.oldControlUnitValue = None
		self.newControlUnitValue = "Testvalue"
		self.testModule.controlUnit = self.oldControlUnitValue

		self.oldTimepoint = -1
		self.newTimepoint = 23
		self.testModule.timepoint = self.oldTimepoint

		self.oldSettings = None
		self.newSettings = "lol"
		self.testModule.settings = self.oldSettings
		
		self.oldZoomFactor = 1
		self.newZoomFactor = 2333
		self.testModule.ZoomFactor = self.oldZoomFactor

		self.testDataset = [1.11, 1.345, 4.4]

		self.testImages = ['lol', 'lol2']
		self.testExtent = 1
		self.testXSize, self.testYSize, self.testZSize = 1, 2, 3
		self.testShift = 2
		self.testScale = 43

		self.testImageDataOld = (0, 0, 0)
		self.testImageDataNew = (1, 2, 3)
		self.testImageDataToShort = (1, 1)
		self.testImageDataToLong = (2, 3, 4, 5)
		self.testImageDataEmpty = ()
		self.testDataunitOld = []
		self.testDataunitNew = 'lol'
		self.testExtentOld = None
		self.testExtentNew = self.testImageDataNew

		self.zDepthOld = 0
		self.zDepthNew = 134

		self.testNewDataOld = 'lol'
		self.testToZ = 2

	def testSetControlDataUnit(self):
		"""
		Created: 02.07.2007, MB
		Description: A test for the method setControlDataUnit
		"""
		self.assertEqual(self.testModule.controlUnit, self.oldControlUnitValue)
		self.testModule.setControlDataUnit(self.newControlUnitValue)
		self.assertEqual(self.testModule.controlUnit, self.newControlUnitValue)

	def testGetControlDataUnit(self):
		"""
		Created: 02.07.2007, MB
		Description: A test for the method getControlDataUnit
		"""
		self.assertEqual(self.testModule.controlUnit, self.testModule.getControlDataUnit())
		
	def testUpdateProgress(self):
		"""
		Created: 02.07.2007, MB
		Description: 
		"""
		pass

	def testSetTimepoint(self):
		"""
		Created: 02.07.2007, MB
		Description: A test for the method setTimepoint
		"""
		self.assertEqual(self.testModule.timepoint, self.oldTimepoint)
		self.testModule.setTimepoint(self.newTimepoint)
		self.assertEqual(self.testModule.timepoint, self.newTimepoint)

	def testSetSettings(self):
		"""
		Created: 02.07.2007, MB
		Description: A test for the method setSettings
		"""
		self.assertEqual(self.testModule.settings, self.oldSettings)
		self.testModule.setSettings(self.newSettings)
		self.assertEqual(self.testModule.settings, self.newSettings)

	def testReset(self):
		"""
		Created: 02.07.2007, MB
		Description: A test for the method reset
		"""
		self.testModule.images = self.testImages
		self.testModule.extent = self.testExtent
		self.testModule.xSize = self.testXSize
		self.testModule.ySize = self.testYSize
		self.testModule.zSize = self.testZSize
		self.testModule.shift = self.testShift
		self.testModule.scale = self.testScale

		self.testModule.reset()
#		self.testModule.reset(self.extent)
		self.assertEqual(self.testModule.images, [])
		self.assertEqual(self.testModule.extent, None)
		self.assertEqual(self.testModule.xSize, 0)
		self.assertEqual(self.testModule.ySize, 0)
		self.assertEqual(self.testModule.zSize, 0)
		self.assertEqual(self.testModule.shift, 0)
		self.assertEqual(self.testModule.scale, 1)

	def testAddInput(self):
		"""
		Created: 02.07.2007, MB
		Description:
		"""
		#Test

#		self.assertEqual(self.testModule.addInput, self.testImageDataOld)
#		self.testModule.addInput(self.testDataunitOld, self.testImageDataNew)
#		self.assertEqual(self.testModule.addInput, self.testImageDataNew)
		pass

	def testGetPreview(self):
		"""
		Created: 02.07.2007, MB
		Description:
		"""
		self.testModule.images = self.testImages
		self.assertEqual(self.testModule.getPreview(self.zDepthOld), self.testImages[0])
		self.assertEqual(self.testModule.getPreview(self.zDepthNew), self.testImages[0])

	def testProcessData(self):
		"""
		Created: 02.07.2007, MB
		Description:
		"""
		self.testModule.images = self.testImages
		self.assertEqual(self.testModule.processData(self.zDepthOld, self.testNewDataOld, 
				self.testToZ ), self.testImages[0])
		self.assertEqual(self.testModule.processData(self.zDepthNew, self.testNewDataOld, 
				self.testToZ ), self.testImages[0])

	def testDoOperation(self):
		"""
		Created: 02.07.2007, MB
		Description:
		"""
		self.testModule.images = self.testImages
		self.assertEqual(self.testModule.doOperation(), self.testImages[0])

#run
if __name__ == "__main__":
	unittest.main()
