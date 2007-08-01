from Merging import *
from MergingPanel import *
from DataUnit import CombinedDataUnit
import MergingSettings
from MergingDataUnit import *

def getClass(): return Merging
def getConfigPanel(): return MergingPanel
def getName(): return "Merging"
def getDesc(): return "Merge multiple channels to form one RGB dataset"
def getIcon(): return "task_merge.jpg"    
def getInputLimits(): return (2, -1)    
def getToolbarPos(): return - 999
def getDataUnit(): return MergingDataUnit
def getSettingsClass(): return MergingSettings.MergingSettings
