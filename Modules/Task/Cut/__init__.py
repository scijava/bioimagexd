from Segmentation import *
from SegmentationPanel import *
from DataUnit import CombinedDataUnit
from SegmentationDataUnit import *
import SegmentationSettings

def getClass(): return Segmentation
def getConfigPanel(): return SegmentationPanel
def getName(): return "Segmentation"
def getDesc(): return "Segment individual objects from images"
def getIcon(): return "task_measure.jpg"
def getInputLimits(): return (1,-1)    
def getToolbarPos(): return 999
def getDataUnit(): return SegmentationDataUnit
def getSettingsClass(): return SegmentationSettings.SegmentationSettings
