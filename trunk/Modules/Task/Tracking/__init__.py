from Tracking import *
from TrackingPanel import *
from DataUnit import CombinedDataUnit
from TrackingDataUnit import *
import TrackingSettings

def getClass(): return Tracking
def getConfigPanel(): return TrackingPanel
def getName(): return "Tracking"
def getDesc(): return "Track objects from segmented images"
def getIcon(): return "task_measure.jpg"
def getInputLimits(): return (1,-1)    
def getToolbarPos(): return 999
def getDataUnit(): return TrackingDataUnit
def getSettingsClass(): return TrackingSettings.TrackingSettings
