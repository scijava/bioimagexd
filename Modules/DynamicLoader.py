# -*- coding: iso-8859-1 -*-

"""
 Unit: DynamicLoader
 Project: BioImageXD
 Created: 02.07.2005, KP
 Description:

 A module for managing the dynamic loading of various modules for
 BioImageXD
           
 Copyright (C) 2005  BioImageXD Project
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
__version__ = "$Revision: 1.9 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import os
import glob

import Logging
import scripting
import os.path
import sys

mcache={}

def getRenderingModules(callback=None): return getModules("Rendering",callback=callback,moduleType="3D rendering module")
def getVisualizationModes(callback=None): return getModules("Visualization",callback=callback,moduleType="")
def getReaders(callback=None): return getModules("Readers",callback=callback,moduleType="Image format reader")
def getTaskModules(callback=None): return getModules("Task","*",callback=callback,moduleType="Task module")
    
IGNORE=["ScaleBar","Spline","Arbitrary","SurfaceConstruction","Reslice","Segment"]

def getModules(name,flag="*.py",callback=None,moduleType="Module"):
    """
    Created: 02.07.2005, KP
    Description: Loads dynamically classes in a directory
                 and returns a dictionary that contains 
                 information about them
    """    
    global mcache
    cname=name
    if name in mcache:
        return mcache[name]
    modpath=scripting.get_module_dir()
    pathlst=[modpath,name]
    if flag:pathlst.append(flag)
    path=reduce(os.path.join,pathlst)
    spath=reduce(os.path.join,[modpath,name])
    Logging.backtrace()
    Logging.info("Path to modes: %s"%spath,kw="modules")
    sys.path=sys.path+[spath]
    
    modules=glob.glob(path)
    moddict={}
    to_remove=[]
    for file in modules:
        for i in IGNORE:
            if i in file:
                to_remove.append(file)
    for i in to_remove:
        modules.remove(i)
    for file in modules:
        Logging.info("About to import ",file,kw="modules")
        if file.find(".") != -1:
            mod=file.split(".")[0:-1]
            mod=".".join(mod)
        else:
            mod=file
        mod=mod.replace("/",".")
        mod=mod.replace("\\",".")
        frompath=mod.split(".")[:-1]
        frompath=".".join(frompath)
        mod=mod.split(".")[-1]
        
        
        Logging.info("Importing %s from %s"%(mod,frompath),kw="modules")
        module = __import__(mod,globals(),locals(),mod)
        if hasattr(module,"getShortDesc"):
            name = module.getShortDesc()
        else:
            try:
                name = module.getName()
            except:
                name = mod
        if callback:
            callback("Loading %s %s..."%(moduleType,name))
        Logging.info("Module=%s"%module,kw="modules")

        if hasattr(module,"getName"):
            name = module.getName()
        else:
            name = mod
        modclass=module.getClass()    
        settingclass=None
        if hasattr(module,"getConfigPanel"):
            settingclass=module.getConfigPanel()
        moddict[name]=(modclass,settingclass,module)
        
    mcache[cname]=moddict
    return moddict
    
