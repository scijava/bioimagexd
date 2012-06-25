import Manipulation
import ManipulationPanel
import ManipulationDataUnit
import ManipulationSettings
import ManipulationFilters

def getFilterModule():
	return ManipulationFilters

def getClass():
	return Manipulation.Manipulation

def getConfigPanel():
	return ManipulationPanel.ManipulationPanel

def getName():
	return "Process"

def getDesc():
	return "Process a dataset through procedure list"

def getShortDesc():
	return "Procedure list"

def getIcon():
	return "Task_Process.png"

def getInputLimits():
	return (1, -1)    

def getToolbarPos():
	return 4

def getDataUnit():
	return ManipulationDataUnit.ManipulationDataUnit

def getSettingsClass():
	return ManipulationSettings.ManipulationSettings
