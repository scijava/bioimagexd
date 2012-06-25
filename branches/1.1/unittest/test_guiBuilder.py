# TestCase for GUI.GUIBuilder

import unittest
import GUI.GUIBuilder

class GUIBuilderBaseTest(unittest.TestCase):
	
	def setUp(self):
		"""
		Description:
		"""

		self.testGUIBuilderBase = GUI.GUIBuilder.GUIBuilderBase(None)

		self.oldInputMapping = {}
		self.newInputNumber = 10
		self.newChannel = 20

		self.n = 5
		self.nText = "Source dataset %d" % self.n

		self.emptyValue = None

		self.expectedColorBeginnerValue = (200, 200, 200)
		self.expectedChannelValue = 1
		self.expectedParametersValue = []

		self.oldParameters = {}
		self.parameterKey = "key"
		self.parameterValue = "value"

		self.descKey = 2
		self.descValue = 4
		self.descEmpty = ""

		self.testGUIBuilderBase.descs = {}

		self.parameter = None
		self.colorBeginner = (200, 200, 200)

	def testGetInput(self):
		"""
		Description:
		"""
		pass

	def testGetInputDataUnit(self):
		"""
		Description:
		"""
		pass

	def testGetCurrentTimepoint(self):
		"""
		Description:

		nts:	difficult to test; bxd.visualizer in GUIBuilder does not exist
		"""
		
#		print self.testGUIBuilderBase.getCurrentTimepoint()

	def testGetInputFromChannel(self):
		"""
		Description:
		"""
		pass

	def testGetNumberOfInputs(self):
		"""
		Description:
		"""
		pass

	def testSetInputChannel(self):
		"""
		Description:
		"""
		self.assertEqual(self.testGUIBuilderBase.inputMapping, self.oldInputMapping)
		self.testGUIBuilderBase.setInputChannel(self.newInputNumber, self.newChannel)
		self.assertEqual(self.testGUIBuilderBase.inputMapping[self.newInputNumber], self.newChannel)

	def testGetInputName(self):
		"""
		Description:
		"""
		self.assertEqual(self.testGUIBuilderBase.getInputName(self.n), self.nText)

	def testGetParameterLevel(self):
		"""
		Description:
		"""
		self.assertEqual(self.testGUIBuilderBase.getParameterLevel(self.parameter), self.colorBeginner)

	def testSendUpdateGUI(self):
		"""
		Description:
		"""
		pass

	def testCanSelectChannels(self):
		"""
		Description:
		"""
		pass

	def testGetParameters(self):
		"""
		Description:
		"""
		pass

	def testGetPlainParameters(self):
		"""
		Description:
		"""
		pass

	def testSetParameter(self):
		"""
		Description:
		"""
		self.assertEqual(self.testGUIBuilderBase.parameters, self.oldParameters)
		self.testGUIBuilderBase.setParameter(self.parameterKey, self.parameterValue)
		self.assertEqual(self.testGUIBuilderBase.parameters[self.parameterKey], self.parameterValue)

	def testGetParameter(self):
		"""
		Description:
		"""
		self.assertEqual(self.testGUIBuilderBase.getParameter(self.parameterKey), self.emptyValue)
		self.testGUIBuilderBase.parameters[self.parameterKey] = self.parameterValue
		self.assertEqual(self.testGUIBuilderBase.getParameter(self.parameterKey), self.parameterValue)

	def testGetDesc(self):
		"""
		Description:
		"""
		self.assertEqual(self.testGUIBuilderBase.getDesc(self.descKey), self.descEmpty)
		self.testGUIBuilderBase.descs[self.descKey] = self.descValue
		self.assertEqual(self.testGUIBuilderBase.getDesc(self.descKey), self.descValue)

	def testGetLongDesc(self):
		"""
		Description:
		"""
		pass

	def testGetType(self):
		"""
		Description:
		"""
		pass

	def testGetRange(self):
		"""
		Description:
		"""
		pass

	def testGetDefaultValue(self):
		"""
		Description:
		"""
		pass

class GUIBuilder(unittest.TestCase):
	
	def setUp(self):
		"""
		Description:
		"""
#		self.testGUIBuilder = GUI.GUIBuilder.GUIBuilder(parent, myfilter)

	def test(self):
		"""
		Description:
		"""
		pass

	def testa(self):
		"""
		Description:
		"""
		pass

	def testb(self):
		"""
		Description:
		"""
		pass

	def testc(self):
		"""
		Description:
		"""
		pass

		

#run
if __name__ == "__main__":
	unittest.main()
