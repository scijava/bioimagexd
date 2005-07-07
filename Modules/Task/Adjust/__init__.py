from Adjust import *
from AdjustPanel import *
from AdjustSettings import *
from AdjustDataUnit import *

from DataUnit import CombinedDataUnit


def getClass(): return Adjust
def getConfigPanel(): return AdjustPanel
def getName(): return "Adjust"
def getDataUnit(): return AdjustDataUnit
def getSettingsClass(): return AdjustSettings.AdjustSettings
