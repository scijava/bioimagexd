from Merging import *
from MergingPanel import *
from DataUnit import CombinedDataUnit
from MergingSettings import *
from MergingDataUnit import *

def getClass(): return Merging
def getConfigPanel(): return MergingPanel
def getName(): return "Merging"
def getDataUnit(): return MergingDataUnit
def getSettingsClass(): return MergingSettings
