# -*- coding: iso-8859-1 -*-

"""
 Unit: scripting
 Project: BioImageXD
 Created: 13.02.2006, KP
 Description:

 A module containing various shortcuts for ease of scripting the app
 
 Copyright (C) 2006  BioImageXD Project
 See CREDITS.txt for details

 This program is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program; if not, write to the Free Software
 Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
"""

__author__ = "BioImageXD Project <http://www.bioimagexd.org/>"
__version__ = "$Revision: 1.21 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import sys,os, os.path
import imp
import platform
import getpass
import vtk


import Configuration

record = 0
conf = None

app = None
mainWindow = None
visualizer = None
processingManager = None
memLimit = None
resamplingDisabled = 0
processingTimepoint = -1


def execute_limited(pipeline):
    limit = get_memory_limit()
    if not limit:
        pipeline.Update()
        return pipeline.GetOutput()
    
    try:
        streamer = vtk.vtkMemoryLimitImageDataStreamer()
        streamer.SetMemoryLimit(1024*limit)
        streamer.SetInput(pipeline.GetOutput())
        streamer.Update()
        return streamer.GetOutput()
    except:
        pipeline.Update()
        return pipeline.GetOutput()

def get_memory_limit():
    global conf,memLimit
    if memLimit:return memLimit
    if not conf:
        conf = Configuration.getConfiguration()
    memLimit = conf.getConfigItem("LimitTo","Performance")
    if memLimit:
        memLimit = eval(memLimit)
    return memLimit

def main_is_frozen():
   return (hasattr(sys, "frozen") or # new py2exe
           hasattr(sys, "importers") # old py2exe
           or imp.is_frozen("__main__")) # tools/freeze



def get_main_dir():
    if "checker.py" in sys.argv[0]:
        return "."
    if main_is_frozen():
        return os.path.dirname(sys.executable)
    return os.path.dirname(sys.argv[0])
    
   
def get_log_dir():
    if platform.system()=="Darwin":
        return os.path.expanduser("~/Library/Logs/BioImageXD")
    elif platform.system() == "Windows":
        appbase=os.path.join("C:\\","Documents and Settings",getpass.getuser(),"Application Data")
        appdir=os.path.join(appbase,"BioImageXD")
        if not os.access(appdir,os.F_OK):
            try:
                os.mkdir(appdir)
            except:
                pass
            if not os.access(appdir,os.F_OK):
                print "Cannot write to application data"
                appdir="."
        
        if not os.path.exists(appdir):
            os.mkdir(appdir)
        return os.path.join(appdir,"Logs")
    else:
        appdir=os.path.expanduser("~/.BioImageXD")
        if not os.path.exists(appdir):
            os.mkdir(appdir)
        return os.path.join(appdir,"Logs")
    
def get_config_dir():
    if platform.system()=="Darwin":
        return os.path.expanduser("~/Library/Preferences")
    elif platform.system() == "Windows": 
        appbase=os.path.join("C:\\","Documents and Settings",getpass.getuser(),"Application Data")
        appdir=os.path.join(appbase,"BioImageXD")
        if not os.access(appdir,os.F_OK):
            try:
                os.mkdir(appdir)
            except:
                pass
            if not os.access(appdir,os.F_OK):
                appdir="."
        if not os.path.exists(appdir):
            os.mkdir(appdir)        
        return appdir
    else:
        confdir=os.path.expanduser("~/.BioImageXD")
    if not os.path.exists(confdir):
        os.mkdir(confdir)
    return confdir
#        return get_main_dir() 
        
def get_icon_dir():
    if platform.system()=="Darwin" and main_is_frozen():
        dir=os.environ['RESOURCEPATH']
        path=os.path.join(dir,"Icons")
        return path
    else:
        return os.path.join(".","Icons")
        
        
def get_module_dir():
    if platform.system()=="Darwin" and main_is_frozen():
        dir=os.environ['RESOURCEPATH']
        path=os.path.join(dir,"Modules")
        return path
    else:
        return "Modules"
        
#def loadITK(filters=0):
#    global ITKIO,ITKCommonA,ItkVtkGlue,ITKBasicFiltersA,ITKAlgorithms
#    import messenger
#    messenger.send(None,"update_progress",0.2,"Loading BioRad support.")        
#    import ITKIO
#    messenger.send(None,"update_progress",0.4,"Loading BioRad support..")  
#    import ITKCommonA
#    messenger.send(None,"update_progress",0.6,"Loading BioRad support...")        
#    import ItkVtkGlue
#    messenger.send(None,"update_progress",0.7,"Loading BioRad support....")       
#    if filters:
#        import ITKBasicFiltersA
#        import ITKAlgorithms
#    messenger.send(None,"update_progress",1.0,"BioRad support loaded.")           
