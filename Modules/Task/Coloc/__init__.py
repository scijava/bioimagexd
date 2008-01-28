import Colocalization
from ColocalizationSettings import *
from ColocalizationPanel import *
from lib.DataUnit.CombinedDataUnit import CombinedDataUnit

class ColocalizationDataUnit(CombinedDataUnit):

	def getSettingsClass(self):
		return ColocalizationSettings

	def getColorTransferFunction(self):
		"""
		Returns the ctf of the source dataunit
		"""
		return self.settings.get("ColorTransferFunction")

def getClass():
	return Colocalization.Colocalization

def getConfigPanel():
	return ColocalizationPanel

def getName():
	return "Colocalization"

def getDesc():
	return "Calculate the colocalization between channels and create a corresponding colocalization map"

def getIcon():
	return "task_colocalization.jpg"

def getInputLimits():
	return (2, 2)

def getToolbarPos():
	return 2

def getDataUnit():
	return ColocalizationDataUnit

def getSettingsClass():
	return ColocalizationSettings
