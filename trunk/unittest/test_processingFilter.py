# TestCase for lib.ProcessingFilter

import unittest
import lib.ProcessingFilter

class ProcessingFilterTest(unittest.TestCase):
	"""
	Created: 11.07.2007, SS
	Description: A test class for Module ProcessingFilter
	"""
	
	def setUp(self):
		"""
		Description:
		"""

		self.testProcessingFilter = lib.ProcessingFilter.ProcessingFilter()

		self.oldImageType = "UC3"
		self.newImageType = "imagetype"

		self.oldTaskPanel = None
		self.newTaskPanel = "taskpanel"

		self.oldDataUnit = None
		self.newDataUnit = "dataunit"

		self.oldEnabled = 1
		self.newEnabled = 0

		self.oldInputs = []
		self.newInputs = "inputs"

	def testOnRemove(self):
		"""
		Description:
		"""

		pass
	
	def testSet(self):
		"""
		Description:
		"""

		pass
	
	def testSetParameter(self):
		"""
		Description:
		"""

		pass
	
	def testWriteOutput(self):
		"""
		Description:
		"""

		pass
	
	def testNotifyTaskPanel(self):
		"""
		Description:
		"""

		pass
	
	def testSetImageType(self):
		"""
		Description:
		"""
		self.assertEqual(self.testProcessingFilter.imageType, self.oldImageType)
		self.testProcessingFilter.setImageType(self.newImageType)
		self.assertEqual(self.testProcessingFilter.imageType, self.newImageType)
	
	def testGetImageType(self):
		"""
		Description:
		"""
		self.assertEqual(self.testProcessingFilter.getImageType(), self.testProcessingFilter.imageType)
	
	def testSetTaskPanel(self):
		"""
		Description:
		"""
		self.assertEqual(self.testProcessingFilter.taskPanel, self.oldTaskPanel)
		self.testProcessingFilter.setTaskPanel(self.newTaskPanel)
		self.assertEqual(self.testProcessingFilter.taskPanel, self.newTaskPanel)
	
	def testConvertVTKToITK(self):
		"""
		Description:
		"""

		pass
	
	def testConvertITKToVTK(self):
		"""
		Description:
		"""

		pass
	
	def testSetNextFilter(self):
		"""
		Description:
		"""

		pass
	
	def testSetPrevFilter(self):
		"""
		Description:
		"""

		pass
	
	def testGetITK(self):
		"""
		Description:
		"""
		self.assertEqual(self.testProcessingFilter.getITK(), self.testProcessingFilter.itkFlag)
	
	def testGetEnabled(self):
		"""
		Description:
		"""
		self.assertEqual(self.testProcessingFilter.getEnabled(), self.testProcessingFilter.enabled)
	
	def testSetDataUnit(self):
		"""
		Description:
		"""
		self.assertEqual(self.testProcessingFilter.dataUnit, self.oldDataUnit)
		self.testProcessingFilter.setDataUnit(self.newDataUnit)
		self.assertEqual(self.testProcessingFilter.dataUnit, self.newDataUnit)
	
	def testGetDataUnit(self):
		"""
		Description:
		"""
		self.assertEqual(self.testProcessingFilter.getDataUnit(), self.testProcessingFilter.dataUnit)
	
	def testSetEnabled(self):
		"""
		Description:
		"""
		self.assertEqual(self.testProcessingFilter.enabled, self.oldEnabled)
		self.testProcessingFilter.setEnabled(self.newEnabled)
		self.assertEqual(self.testProcessingFilter.enabled, self.newEnabled)

	def testGetGUI(self):
		"""
		a test for the method getGUI()

		Have to set the parent value but havent yet figured out what that would be
		"""
#		self.assertEqual(self.testProcessingFilter.taskPanel, self.oldTaskPanel)
#		self.testProcessingFilter.getGUI(parent, self.newTaskPanel)
#		self.assertEqual(self.testProcessingFilter.taskPanel, self.newTaskPanel)
		pass
	
	def testGetName(self):
		"""
		Description:
		"""
#		print "name:", self.testProcessingFilter.getName()
		pass
	
	def testGetCategory(self):
		"""
		Description:
		"""
#		print "category:", self.testProcessingFilter.getCategory()
		pass
	
	def testExecute(self):
		"""
		Description:
		"""
		self.assertEqual(self.testProcessingFilter.inputs, self.oldInputs)
		self.assertEqual(self.testProcessingFilter.execute(self.newInputs), 1)
		self.assertEqual(self.testProcessingFilter.inputs, self.newInputs)
		

#run
if __name__ == "__main__":
	unittest.main()
