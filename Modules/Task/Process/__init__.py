from Process import *
from ProcessPanel import *
from DataUnit import CombinedDataUnit
from ProcessDataUnit import *
import ProcessSettings

def getClass(): return Process
def getConfigPanel(): return ProcessPanel
def getName(): return "Process"
def getIcon(): return "task_process.jpg"
def getInputLimits(): return (1,1)    
def getToolbarPos(): return 5    
def getDataUnit(): return ProcessDataUnit
def getSettingsClass(): return ProcessSettings.ProcessSettings
