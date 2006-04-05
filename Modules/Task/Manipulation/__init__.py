from Manipulation import *
from ManipulationPanel import *
from DataUnit import CombinedDataUnit
from ManipulationDataUnit import *
import ManipulationSettings

def getClass(): return Manipulation
def getConfigPanel(): return ManipulationPanel
def getName(): return "Manipulation"
def getDataUnit(): return ManipulationDataUnit
def getSettingsClass(): return ManipulationSettings.ManipulationSettings
