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

import os.path
import sys

def getRenderingModules(): return getModules("Rendering")
def getVisualizationModes(): return getModules("Visualization")
def getTaskModules(): return getModules("Task","*")

def getModules(name,flag="*.py"):
    """
    Function: getModules()
    Created: 02.07.2005, KP
    Description: Loads dynamically classes in a directory
                 and returns a dictionary that contains 
                 information about them
    """    
    pathlst=["Modules",name]
    if flag:pathlst.append(flag)
    path=reduce(os.path.join,pathlst)
    spath=reduce(os.path.join,[os.getcwd(),"Modules",name])
    
    Logging.info("Path to modes: %s"%spath,kw="modules")
    sys.path=sys.path+[spath]
    
    modules=glob.glob(path)
    moddict={}
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
        Logging.info("Module=%s"%module,kw="modules")
        name=module.getName()
        modclass=module.getClass()    
        settingclass=module.getConfigPanel()
        moddict[name]=(modclass,settingclass,module)
    return moddict
    
