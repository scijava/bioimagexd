# TestCase for lib.ImageOperations

import sys
import os.path
import unittest
import wx

runningScriptPath = sys.argv[0]
unittestPath = os.path.dirname(runningScriptPath)
bioimagepath = os.path.abspath(os.path.join(unittestPath, ".."))

import ImageOperations
import filecmp

class ImageOperationsTest(unittest.TestCase):
	
	def setUp(self):
		pass
	
	def testloadLut(self):
		
		# Test that a sequence of loadLut() and saveLUT() produces a file identical to the original
		
		testFileIn = bioimagepath + "/LUT/ICA.lut"
		testFileOut = bioimagepath + "/unittest/testdata/Temp/.tmp_bxdtestloadLut.lut"
		testctf = ImageOperations.loadLUT(testFileIn)
		ImageOperations.saveLUT(testctf, testFileOut)
		self.assertEqual(filecmp.cmp(testFileIn, testFileOut), 1)
		os.remove(testFileOut)

	def testpaintCTFValues(self):

		try:
			wxApp = wx.App()
		# gives nothing, because segmentation faults thrown by wx.App() cannot be caught
		except Exception,exc:
			print exc
		testCTFFileIn = bioimagepath + "/LUT/ICA.lut"
		testBMPOriginal = bioimagepath + "/unittest/testdata/ComparisonData/Images/paintCTFValues.bmp"
		testTemporaryBmp = bioimagepath + "/unittest/testdata/Temp/.tmp_bxdtestpaintCTFValues.bmp"
		
		testCTF = ImageOperations.loadLUT(testCTFFileIn)
		bitMap = ImageOperations.paintCTFValues(testCTF, paintScale = 0)
		bitMap.SaveFile(testTemporaryBmp, wx.BITMAP_TYPE_BMP)
		
		self.assertTrue(filecmp.cmp(testBMPOriginal, testTemporaryBmp))
		os.remove(testTemporaryBmp)

#TODO: Test for paintLogarithmicScale. Cannot be done yet, however, as it requires special conditions 

# run
if __name__ == "__main__":
	unittest.main()
