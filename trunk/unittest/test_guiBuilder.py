# TestCase for GUI.GUIBuilder

import unittest
import GUI.GUIBuilder

class GUIBuilderBaseTest(unittest.TestCase):
	
	def setUp(self):
		"""
		Created: 11.07.2007, SS
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

	def testGetInput(self):
		"""
		Created: 11.07.2007, SS
		Description:
		"""
		pass

	def testGetInputDataUnit(self):
		"""
		Created: 11.07.2007, SS
		Description:
		"""
		pass

	def testGetCurrentTimepoint(self):
		"""
		Created: 11.07.2007, SS
		Description:

		nts:	difficult to test; bxd.visualizer in GUIBuilder does not exist
		"""
#		print self.testGUIBuilderBase.getCurrentTimepoint()

	def testGetInputFromChannel(self):
		"""
		Created: 11.07.2007, SS
		Description:
		"""
		pass

	def testGetNumberOfInputs(self):
		"""
		Created: 11.07.2007, SS
		Description:
		"""
		pass

	def testSetInputChannel(self):
		"""
		Created: 11.07.2007, SS
		Description:
		"""
		self.assertEqual(self.testGUIBuilderBase.inputMapping, self.oldInputMapping)
		self.testGUIBuilderBase.setInputChannel(self.newInputNumber, self.newChannel)
		self.assertEqual(self.testGUIBuilderBase.inputMapping[self.newInputNumber], self.newChannel)

	def testGetInputName(self):
		"""
		Created: 11.07.2007, SS
		Description:
		"""
		self.assertEqual(self.testGUIBuilderBase.getInputName(self.n), self.nText)

	def testGetParameterLevel(self):
		"""
		Created: 11.07.2007, SS
		Description:
		"""
		pass

	def testSendUpdateGUI(self):
		"""
		Created: 11.07.2007, SS
		Description:
		"""
		pass

	def testCanSelectChannels(self):
		"""
		Created: 11.07.2007, SS
		Description:
		"""
		pass

	def testGetParameters(self):
		"""
		Created: 11.07.2007, SS
		Description:
		"""
		pass

	def testGetPlainParameters(self):
		"""
		Created: 11.07.2007, SS
		Description:
		"""
		pass

	def testSetParameter(self):
		"""
		Created: 11.07.2007, SS
		Description:
		"""
		self.assertEqual(self.testGUIBuilderBase.parameters, self.oldParameters)
		self.testGUIBuilderBase.setParameter(self.parameterKey, self.parameterValue)
		self.assertEqual(self.testGUIBuilderBase.parameters[self.parameterKey], self.parameterValue)

	def testGetParameter(self):
		"""
		Created: 11.07.2007, SS
		Description:
		"""
		self.assertEqual(self.testGUIBuilderBase.getParameter(self.parameterKey), self.emptyValue)
		self.testGUIBuilderBase.parameters[self.parameterKey] = self.parameterValue
		self.assertEqual(self.testGUIBuilderBase.getParameter(self.parameterKey), self.parameterValue)

	def testGetDesc(self):
		"""
		Created: 11.07.2007, SS
		Description:
		"""
		self.assertEqual(self.testGUIBuilderBase.getDesc(self.descKey), self.descEmpty)
		self.testGUIBuilderBase.descs[self.descKey] = self.descValue
		self.assertEqual(self.testGUIBuilderBase.getDesc(self.descKey), self.descValue)

	def testGetLongDesc(self):
		"""
		Created: 11.07.2007, SS
		Description:
		"""
		pass

	def testGetType(self):
		"""
		Created: 11.07.2007, SS
		Description:
		"""
		pass

	def testGetRange(self):
		"""
		Created: 11.07.2007, SS
		Description:
		"""
		pass

	def testGetDefaultValue(self):
		"""
		Created: 11.07.2007, SS
		Description:
		"""
		pass

class GUIBuilder(unittest.TestCase):
	
	def setUp(self):
		"""
		Created: 11.07.2007, SS
		Description:
		"""

#		self.testGUIBuilder = GUI.GUIBuilder.GUIBuilder(parent, myfilter)

	def test(self):
		"""
		Created: 11.07.2007, SS
		Description:
		"""
		pass

	def testa(self):
		"""
		Created: 11.07.2007, SS
		Description:
		"""
		pass

	def testb(self):
		"""
		Created: 11.07.2007, SS
		Description:
		"""
		pass

	def testc(self):
		"""
		Created: 11.07.2007, SS
		Description:
		"""
		pass

		

#run
if __name__ == "__main__":
	unittest.main()
