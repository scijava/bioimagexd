from Merging import *
from MergingPanel import *
from lib.DataUnit import CombinedDataUnit
import MergingSettings
from MergingDataUnit import *

def getClass():
	return Merging

def getConfigPanel():
	return MergingPanel

def getName():
	return "Merging"

def getDesc():
	return "Merge multiple channels to form one RGB dataset"

def getShortDesc():
	return "Merge"

def getIcon():
	return "Task_Merge.png"

def getInputLimits():
	return (2, -1)    

def getToolbarPos():
	return 2

def getDataUnit():
	return MergingDataUnit

def getSettingsClass():
	return MergingSettings.MergingSettings
