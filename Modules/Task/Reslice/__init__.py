from Reslice import *
from ReslicePanel import *
from DataUnit import CombinedDataUnit

class ResliceDataUnit(CombinedDataUnit):
        def getSettingsClass(): return ResliceSettings
def getClass(): return Reslice
def getConfigPanel(): return ReslicePanel
def getName(): return "Reslice"
def getDataUnit(): return ResliceDataUnit
def getSettingsClass(): return ResliceSettings
