from Manipulation import *
from ManipulationPanel import *
from DataUnit import CombinedDataUnit
from ManipulationDataUnit import *
import ManipulationSettings

def getClass(): return Manipulation
def getConfigPanel(): return ManipulationPanel
def getName(): return "Manipulation"
def getIcon(): return "task_manipulate.jpg"
def getInputLimits(): return (1,-1)    
def getToolbarPos(): return 999
def getDataUnit(): return ManipulationDataUnit
def getSettingsClass(): return ManipulationSettings.ManipulationSettings
