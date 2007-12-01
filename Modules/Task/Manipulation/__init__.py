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
	return "Process a dataset with different filters"

def getIcon():
	return "task_process.jpg"

def getInputLimits():
	return (1, -1)    

def getToolbarPos():
	return 999

def getDataUnit():
	return ManipulationDataUnit.ManipulationDataUnit

def getSettingsClass():
	return ManipulationSettings.ManipulationSettings
