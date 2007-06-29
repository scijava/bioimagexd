#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

"""
 Unit: Configuration.py
 Project: BioImageXD
 Created: 23.02.2004, KP
 Description:

 A module that loads / saves a configuration file and gives information
 about the current configuration. Also handles path management.

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

 You should have received a cop of the GNU General Public License
 along with this program; if not, write to the Free Software
 Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
"""
__author__ = "BioImageXD Project"
__version__ = "$Revision: 1.22 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import os.path
import sys, types
import ConfigParser
import Logging
conf=None
import platform

import scripting as bxd
def getConfiguration():
    return conf

class Configuration:
    """
    Created: 23.02.2005, KP
    Description: A module that handles the configuration file 
    """
    def __init__(self,configFile):
        global conf
        conf=self
        self.configItems={}
        self.installPath=os.getcwd()
        self.parser=ConfigParser.ConfigParser()
        cfgfile=self.getPath(configFile)
        self.configFile=cfgfile
        self.parser.read([cfgfile])    
    
        # Set the initial values
        #vtkpath=self.getPath(["Libraries","VTK"])
        if platform.system()=="Windows":
            vtkpath=self.getPath(["C:\\VTK-build"])
        else:
            vtkpath="/home/kalpaha/BioImageXD/VTK-current"
        self.setConfigItem("ShowTip","General","True",0)
        self.setConfigItem("AskOnQuit","General","True",0)
        self.setConfigItem("TipNumber","General",0,0)
        self.setConfigItem("RestoreFiles","General","True",0)
        self.setConfigItem("ReportCrash","General","True",0)
        self.setConfigItem("CleanExit","General","True",0)
        
        self.readConfigItem("ShowTip","General")
        self.readConfigItem("RestoreFiles","General")
        self.readConfigItem("TipNumber","General")
        self.readConfigItem("AskOnQuit","General")
        self.readConfigItem("RescaleOnLoading","Performance")
        self.readConfigItem("RestoreFiles","General")
        self.readConfigItem("ReportCrash","General")
        self.readConfigItem("CleanExit","General")
        
        self.readConfigItem("BeginnerColor","General")
        self.readConfigItem("IntermediateColor","General")
        self.readConfigItem("ExperiencedColor","General")
        
        c = self.getConfigItem("BeginnerColor","General")
        if c:
            bxd.COLOR_BEGINNER = eval(c)
        c = self.getConfigItem("IntermediateColor","General")
        if c:
            bxd.COLOR_INTERMEDIATE =  eval(c)
        c = self.getConfigItem("ExperiencedColor","General")
        if c:
            bxd.COLOR_EXPERIENCED = eval(c)
        
        
        self.setConfigItem("RemoveOldVTK","VTK",1,0);
        self.setConfigItem("VTKPath","VTK",vtkpath,0)
        
        self.setConfigItem("ImageFormat","Output","png",0)
        fpath=os.path.expanduser("~")
        self.setConfigItem("FramePath","Paths",fpath,0)
        self.setConfigItem("VideoPath","Paths",os.path.join(fpath,"video.avi"),0)

        self.setConfigItem("DataPath","Paths","/home/kalpaha/BioImageXD/Data/",0)
        self.setConfigItem("LastPath","Paths","/home/kalpaha/BioImageXD/Data/",0)
        self.setConfigItem("RememberPath","Paths",1)

        # Then read the settings file
        self.readPathSettings()

        self.insertModuleDirectories()
        self.processPathSettings()

    def writeSettings(self):
        """
        Created: 12.03.2005, KP
        Description: A method to write out the settings
        """ 
        fp=open(self.configFile,"w")
        self.parser.write(fp)
        fp.close()
        
    def insertModuleDirectories(self):
        self.insertPath(self.getPath("lib"))
        self.insertPath(self.getPath("GUI"))
        self.insertPath(self.getPath("Libraries"))
        
    def processPathSettings(self):
        vtkdir=self.getConfigItem("VTKPath","VTK")
        if self.getConfigItem("RemoveOldVTK","VTK") and os.path.isdir(vtkdir):
            self.removeWithName(["vtk","VTK","vtk_python"])
        bin=self.getPath([vtkdir,"bin"])
        wrapping=self.getPath([vtkdir,"Wrapping","Python"])
        self.insertPath(bin)
        self.insertPath(wrapping)
        
        
    def setConfigItem(self,configItem, section,value,write=1):
        self.configItems[configItem]=value
        if write:
            if self.parser.has_section(section) == False:
                self.parser.add_section(section)
            self.parser.set(section,configItem,value)
            self.writeSettings()

    def readConfigItem(self,configItem,section):
        try:
            configItemvalue=self.parser.get(section,configItem)
            self.configItems[configItem]=configItemvalue
        except:
            return None
        return configItemvalue
        
    def getConfigItem(self,configItem,section):
        if not configItem in self.configItems:
            self.readConfigItem(configItem,section)
            
        if not configItem in self.configItems:
            return None
            
        return self.configItems[configItem]
        
    def readPathSettings(self):
        self.readConfigItem("RemoveOldVTK","VTK")
        self.readConfigItem("VTKPath","VTK")
        self.readConfigItem("DataPath","Paths")
        self.readConfigItem("ImageFormat","Output")
        self.readConfigItem("FramePath","Paths")
        self.readConfigItem("VideoPath","Paths")
    def setCurrentDir(self,path):
        self.installPath=path

    def getPath(self,path):
        if type(path)==types.StringType:
            path=[path]
        return os.path.normpath(os.path.join(self.installPath,reduce(os.path.join,path)))
    
    def removeWithName(self,names):
        removethese=[]
        for i in sys.path:
            for name in names:
                if i.find(name) != -1:
                    removethese.append(i)
#        Logging.info("Removing following path entries: ",", ".join(removethese),kw="init")
        for i in removethese:
            try:
                sys.path.remove(i)
            except:
                Logging.info("Failed to remove ",i,kw="init")

            
    def insertPath(self,path,n=0):
        sys.path.insert(n,path)
        
    def appendPath(self,path):
        sys.path.append(path)
