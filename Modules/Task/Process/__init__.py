from Process import *
from ProcessPanel import *
from DataUnit import CombinedDataUnit
from ProcessDataUnit import *

def getClass(): return Process
def getConfigPanel(): return ProcessPanel
def getName(): return "Process"
def getDataUnit(): return ProcessDataUnit
def getSettingsClass(): return ProcessSettings
