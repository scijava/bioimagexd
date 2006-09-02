from Manipulation import *
from ManipulationPanel import *
from DataUnit import CombinedDataUnit
from ManipulationDataUnit import *
import ManipulationSettings

def getClass(): return Manipulation
def getConfigPanel(): return ManipulationPanel
def getName(): return "Process"
def getDesc(): return "Process a dataset with different filters"
def getIcon(): return "task_process.jpg"
def getInputLimits(): return (1,-1)    
def getToolbarPos(): return 999
def getDataUnit(): return ManipulationDataUnit
def getSettingsClass(): return ManipulationSettings.ManipulationSettings
