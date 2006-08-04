from Cut import *
from CutPanel import *
from DataUnit import CombinedDataUnit
from CutDataUnit import *
import CutSettings

def getClass(): return Cut
def getConfigPanel(): return CutPanel
def getName(): return "Cut"
def getDesc(): return "Cut the dataset to a smaller size"
def getIcon(): return "task_cut.gif"
def getInputLimits(): return (1,1)    
def getToolbarPos(): return 999
def getDataUnit(): return CutDataUnit
def getSettingsClass(): return CutSettings.CutSettings
