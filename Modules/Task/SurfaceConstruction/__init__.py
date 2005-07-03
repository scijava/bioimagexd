from SurfaceConstruction import *
from SurfaceConstructionPanel import *
from DataUnit import CombinedDataUnit

class SurfaceConstructionDataUnit(CombinedDataUnit):
        def getSettingsClass(self): return SurfaceConstructionSettings
def getClass(): return SurfaceConstruction
def getConfigPanel(): return SurfaceConstructionPanel
def getName(): return "Surface Construction"
def getDataUnit(): return SurfaceConstructionDataUnit
def getSettingsClass(): return SurfaceConstructionSettings
