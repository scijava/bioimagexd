#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

"""
 Unit: Configuration.py
 Project: BioImageXD
 Created: 23.02.2004
 Creator: KP
 Description:

 A module that loads / saves a configuration file and gives information
 about the current configuration. Also handles path management.

 Modified: 23.02.2005 KP - Created the class

 BioImageXD includes the following persons:
 DW - Dan White, dan@chalkie.org.uk
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 PK - Pasi Kankaanpää, ppkank@bytl.jyu.fi

 Copyright (c) 2005 BioImageXD Project.
"""
__author__ = "BioImageXD Project"
__version__ = "$Revision: 1.22 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import os.path
import sys, types
import ConfigParser

conf=None

def getConfiguration():
    return conf

class Configuration:
    def __init__(self,configFile):
        global conf
        conf=self
        self.configItems={}
        self.installPath=os.getcwd()
        self.parser=ConfigParser.ConfigParser()
        cfgfile=self.getPath(configFile)
        self.parser.read([cfgfile])
    
        # Set the initial values
        #vtkpath=self.getPath(["Libraries","VTK"])
        vtkpath=self.getPath(["C:\\VTK"])
        mayavipath=self.getPath(["Libraries","mayavi"])
        self.setConfigItem("RemoveOldVTK","VTK",0);
        self.setConfigItem("VTKPath","VTK",vtkpath)
        self.setConfigItem("UseSystemMayavi","Mayavi",0)
        self.setConfigItem("MayaviPath","Mayavi",mayavipath)
        
        self.setConfigItem("ImageFormat","Output","png")
        
        # Then read the settings file
        self.readPathSettings()
        
        self.insertModuleDirectories()
        self.processPathSettings()
        print sys.path
        
        
    def insertModuleDirectories(self):
        self.insertPath(self.getPath("LSM"))
        self.insertPath(self.getPath("Modules"))
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
        self.insertPath(self.getConfigItem("MayaviPath","Mayavi"))
        
    def setConfigItem(self,configItem, section,value):
        self.configItems[configItem]=value
        if self.parser.has_section(section) == False:
            self.parser.add_section(section)
        self.parser.set(section,configItem,value)
        
    def readConfigItem(self,configItem,section):
        try:
            configItemvalue=self.parser.get(section,configItem)
            self.configItems[configItem]=configItemvalue
        except:
            return None
        return configItemvalue
        
    def getConfigItem(self,configItem,section):
        if not configItem in self.configItems:
            self.readConfigItem(section,configItem)
        return self.configItems[configItem]
        
    def readPathSettings(self):
        self.readConfigItem("RemoveOldVTK","VTK")
        self.readConfigItem("VTKPath","VTK")
        self.readConfigItem("UseSystemMayavi","Mayavi")
        self.readConfigItem("MayaviPath","Mayavi")        
            
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
        print "Removing following path entries: ",", ".join(removethese)
        for i in removethese:
            try:
                sys.path.remove(i)
            except:
                print "Failed to remove ",i

            
    def insertPath(self,path,n=0):
        sys.path.insert(n,path)
        
