from Adjust import *
from AdjustPanel import *
from AdjustSettings import *
from AdjustDataUnit import *

from DataUnit import CombinedDataUnit


def getClass(): return Adjust
def getConfigPanel(): return AdjustPanel
def getName(): return "Adjust"
def getDesc(): return "Adjust the brightness, contrast and gamma of a dataset"
def getIcon(): return "task_adjust.jpg"
def getInputLimits(): return (1,1)
def getToolbarPos(): return 3
def getDataUnit(): return AdjustDataUnit
def getSettingsClass(): return AdjustSettings.AdjustSettings
