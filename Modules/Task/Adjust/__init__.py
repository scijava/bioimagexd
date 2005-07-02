from Adjust import *
from AdjustPanel import *
from AdjustSettings import *

from DataUnit import CombinedDataUnit

class AdjustDataUnit(CombinedDataUnit):
    def getSettingsClass(): return AdjustSettings

def getClass(): return Adjust
def getConfigPanel(): return AdjustPanel
def getName(): return "Adjust"
def getDataUnit(): return AdjustDataUnit
def getSettingsClass(): return AdjustSettings
