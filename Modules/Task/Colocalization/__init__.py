from Colocalization import *
from ColocalizationPanel import *
from DataUnit import CombinedDataUnit

class ColocalizationDataUnit(CombinedDataUnit):
        def getSettingsClass(self): return ColocalizationSettings
def getClass(): return Colocalization
def getConfigPanel(): return ColocalizationPanel
def getName(): return "Colocalization"
def getDataUnit(): return ColocalizationDataUnit
def getSettingsClass(): return ColocalizationSettings
