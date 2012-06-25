# TestCase for lib.RenderingInterface.py

import unittest
import lib.RenderingInterface
import lib.DataUnit.DataUnit

class RenderingInterfaceTest(unittest.TestCase):
	
	def setUp(self):
		"""
		Creates a test RenderingInterface and test variables
		"""
	
#		self.testDataUnit = lib.DataUnit.DataUnit.DataUnit()
#		self.testRenderingInterface = lib.RenderingInterface.RenderingInterface(self.testDataUnit)
#		self.testVisualizer = Visualizer.Visualizer.Visualizer()
		self.testRenderingInterface = lib.RenderingInterface.RenderingInterface()

		self.testImageType = "png"
		self.testCtf = "testCtf value"
		self.testFrameList = [1, 2, 3]

		self.oldTestParentValue = None
		self.newTestParentValue = "new parent"

		self.oldTimepointsValue = []
		self.testTimepoints = [2, 3, 4, 5]

		self.oldDirnameValue = None
		self.testDirname = "testdir"

	def testSetType(self):
		"""
		Tests the method setType()
		Before setType(): self.testRenderingInterface.imageType should be non-equal to self.testImageType
		After setType():self.testRenderingInterface.imageType should be equal to self.testImageType
		"""

		self.assertNotEqual(self.testRenderingInterface.imageType, self.testImageType)
		self.testRenderingInterface.setType(self.testImageType)
		self.assertEqual(self.testRenderingInterface.imageType, self.testImageType)

	def testGetColorTransferFunction(self):
		"""
		Tests the method getColorTransferFunction()
		"""

		self.testRenderingInterface.ctf = self.testCtf
		tempCtf = self.testRenderingInterface.getColorTransferFunction()
		self.assertEqual(tempCtf, self.testCtf)

	def testGetCurrentData(self):
		"""
		Tests the method setCurrentTimepoint()

		nts:	Can't be done before testSetCurrenttimepoint() is working
		"""
		pass


	def testSetCurrentTimepoint(self):
		"""
		Tests the method getCurrentData()

		nts:	TOO COMPLICATED! testRenderingInterface needs a dataUnit as parameter
				and this dataUnit instance needs a dataSource. will leave this
				method untested for a while
		"""
#		print "current tp (-1):", self.testRenderingInterface.currentTimePoint
#		print "current dataUnit (None):", self.testRenderingInterface.dataUnit
#		print "current currentData (None):", self.testRenderingInterface.currentData
#		print "current dimensions (None?): ", self.testRenderingInterface.dimensions
#		self.testRenderingInterface.setCurrentTimepoint(2)
#		print "tp after (2):", self.testRenderingInterface.currentTimePoint
#		print "currentData after (None?):", self.testRenderingInterface.currentData
#		print "dimensions after (None?): ", self.testRenderingInterface.dimensions

		pass		
		
	def testSetRenderWindowSize(self):
		"""
		Tests the method setRenderWindowSize()

		nts:	Have to create a test Visualizer to test this method but gets complicated
		"""
		pass

	def testGetRenderWindow(self):
		"""
		Tests the method GetRenderWindow()

		nts:	Have to create a test Visualizer to test this method but gets complicated
		"""
		pass

	def testSetParent(self):
		"""
		Tests the method setParent()
		"""
		# no parameter "parent" exists
#		self.assertEqual(self.testRenderingInterface.parent, self.oldTestParentValue)
#		self.testRenderingInterface.setParent(self.newTestParentValue)
#		self.assertEqual(self.testRenderingInterface.parent, self.newTestParentValue)
		pass

	def testGetRenderer(self):
		"""
		Tests the method getRenderer()

		nts:	Have to create a test Visualizer to test this method but gets complicated
		"""
		pass

	def testRender(self):
		"""
		Tests the method render()

		nts:	Have to create a test Visualizer to test this method but gets complicated
		"""
		pass

	def testSetVisualizer(self):
		"""
		Tests the method setVisualizer()

		nts:	Have to create a test Visualizer to test this method but gets complicated
		"""
		pass

	def testSetDataUnit(self):
		"""
		Tests the method setDataUnit()
		"""
#		self.assertEqual(self.testRenderingInterface.dataUnit, self.oldDataUnitValue)
#		self.testRenderingInterface.setDataUnit(self.testDataUnit)
		pass		

	def testSetTimePoints(self):
		"""
		Tests the method setTimePoints()
		"""
		self.assertEqual(self.testRenderingInterface.timePoints, self.oldTimepointsValue)
		self.testRenderingInterface.setTimePoints(self.testTimepoints)
		self.assertEqual(self.testRenderingInterface.timePoints, self.testTimepoints)

	def testCreateVisualization(self):
		"""
		Tests the method createVisualization()

		nts:	Have to create a test Visualizer to test this method but gets complicated
		"""
		pass

	def testIsVisualizationSoftwareRunning(self):
		"""
		Tests the method isVisualizationSoftwareRunning()

		nts:	Have to create a test Visualizer to test this method but gets complicated
		"""
		pass

	def testIsVisualizationModuleLoaded(self):
		"""
		Tests the method isVisualizationModuleLoaded()

		nts:	Have to create a test Visualizer to test this method but gets complicated
		"""
		pass

	def testDoRendering(self):
		"""
		Tests the method doRendering()

		nts:	Have to create a test Visualizer to test this method but gets complicated
		"""
		pass

	def testGetFrameList(self):
		"""
		Tests the method getFrameList()
		"""
		self.testRenderingInterface.frameList = self.testFrameList
		tempFrameList = self.testRenderingInterface.getFrameList()
		self.assertEqual(tempFrameList, self.testFrameList)

	def testSetOutputPath(self):
		"""
		Tests the method setOutputPath()
		"""
		# no parameter "dirname" exists
#		self.assertEqual(self.testRenderingInterface.dirname, self.oldDirnameValue)
#		self.testRenderingInterface.setOutputPath(self.testDirname)
#		self.assertEqual(self.testRenderingInterface.dirname, self.testDirname)

	def testRenderData(self):
		"""
		Tests the method renderData()

		nts:	Complicated
		"""
		pass

	def testSaveFrame(self):
		"""
		Tests the method saveFrame()

		nts:	Have to create a test Visualizer to test this method but gets complicated
		"""
		pass

	def testGetFilenamePattern(self):
		"""
		Tests the method getFilenamePattern()
		"""
		# no parameter "format"
#		self.assertEqual(self.testRenderingInterface.getFilenamePattern(), self.testRenderingInterface.format)

	def testGetFrameName(self):
		"""
		Tests the method getFrameName()
		"""
		self.assertEqual(self.testRenderingInterface.getFrameName(), self.testRenderingInterface.frameName)

	def testGetFilename(self):
		"""
		Tests the method getFilename()

		nts:	somehow complicated, format gets a value in setDataUnit() which has not been processed yet
		"""
		pass

	def testGetCenter(self):
		"""
		Tests the method getCenter()

		nts:	complicated, involves a dataUnit and dataSource
		"""
		pass

	def testGetDimensions(self):
		"""
		Tests the method getDimensions()

		nts:	complicated, involves a dataUnit and dataSource
		"""
		pass

	def testUpdateDataset(self):
		"""
		Tests the method updateDataset()

		nts:	Have to create a test Visualizer to test this method but gets complicated
		"""
		pass

#run
if __name__ == "__main__":
	unittest.main()
