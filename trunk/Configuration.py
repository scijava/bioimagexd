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

import ConfigParser
import codecs
import Logging
import platform
import scripting
import os.path
import sys
import types

conf = None

class FlexConfigParser(ConfigParser.ConfigParser):
	"""
	Created: 29.08.2007, KP
	Description: a config parser that doesn't ignore the case of the options and sections, but converts unicode characters to their xml reprsentation
	"""
	def set(self, section, option, value):
		"""
		Created: 29.08.2007, KP
		Description: tranform the value
		"""
		if type(value) == types.UnicodeType:
			ConfigParser.ConfigParser.set(self, section, option, codecs.encode(value, "ascii", "xmlcharrefreplace"))
		else:
			ConfigParser.ConfigParser.set(self, section, option, value)
	def optionxform(self, optionstr):
		"""
		Created: KP
		Description: A method used to transform the option names. Does not transform the names in any way
		"""
		return optionstr

def getConfiguration():
	"""
	Created: Unknown date, KP
	Description: Returns the current configuration
	"""
	global conf
	if not conf:
		conf = Configuration()
	return conf

def getNumberTupleFromString(inString):
	"""
	Created: 23.08.07, TW
	Description: Takes a string of form '(number, number ..., number)' 
				 and returns a tuple consisting of the numbers.
	"""
	withoutBraces = inString[1:-1]
	return tuple( int(number) for number in withoutBraces.split(","))

class Configuration:
	"""
	Created: 23.02.2005, KP
	Description: A module that handles the configuration file 
	"""
	def __init__(self, configFile = None):
		global conf
		conf = self
		if not configFile:
			configFile = os.path.join(scripting.get_config_dir(), "BioImageXD.ini")
		self.configItems = {}
		self.installPath = os.getcwd()
		self.parser = FlexConfigParser()
		cfgfile = self.getPath(configFile)
		fp = codecs.open(cfgfile, "r","utf-8")
		self.configFile = cfgfile
		self.parser.readfp(fp, cfgfile)    
	
		# Set the initial values

		if platform.system() == "Windows":
			vtkpath = self.getPath(["C:\\VTK-build"])
		else:
			vtkpath = "/home/kalpaha/BioImageXD/VTK-current"
		self.setConfigItem("ShowTip", "General", "True", 0)
		self.setConfigItem("AskOnQuit", "General", "True", 0)
		self.setConfigItem("TipNumber", "General", 0, 0)
		self.setConfigItem("RestoreFiles", "General", "True", 0)
		self.setConfigItem("ReportCrash", "General", "True", 0)
		self.setConfigItem("CleanExit", "General", "True", 0)
		
		self.readConfigItem("ShowTip", "General")
		self.readConfigItem("RestoreFiles", "General")
		self.readConfigItem("TipNumber", "General")
		self.readConfigItem("AskOnQuit", "General")
		self.readConfigItem("RescaleOnLoading", "Performance")
		self.readConfigItem("RestoreFiles", "General")
		self.readConfigItem("ReportCrash", "General")
		self.readConfigItem("CleanExit", "General")
		
		self.readConfigItem("BeginnerColor", "General")
		self.readConfigItem("IntermediateColor", "General")
		self.readConfigItem("ExperiencedColor", "General")
		
		configItem = self.getConfigItem("BeginnerColor", "General")
		if configItem:
			scripting.COLOR_BEGINNER = eval(configItem)
		configItem = self.getConfigItem("IntermediateColor", "General")
		if configItem:
			scripting.COLOR_INTERMEDIATE =  eval(configItem)
		configItem = self.getConfigItem("ExperiencedColor", "General")
		if configItem:
			scripting.COLOR_EXPERIENCED = eval(configItem)
		
		
		self.setConfigItem("RemoveOldVTK", "VTK", 1, 0)
		self.setConfigItem("VTKPath", "VTK", vtkpath, 0)
		
		self.setConfigItem("ImageFormat", "Output", "png", 0)
		fpath = os.path.expanduser("~")
		self.setConfigItem("FramePath", "Paths", fpath, 0)
		self.setConfigItem("VideoPath", "Paths", os.path.join(fpath, "video.avi"), 0)

		self.setConfigItem("DataPath", "Paths", "/home/kalpaha/BioImageXD/Data/", 0)
		self.setConfigItem("LastPath", "Paths", "/home/kalpaha/BioImageXD/Data/", 0)
		self.setConfigItem("RememberPath", "Paths", 1)

		# Then read the settings file
		self.readPathSettings()

		self.insertModuleDirectories()
		self.processPathSettings()

	def writeSettings(self):
		"""
 		Created: 12.03.2005, KP
 		Description: A method to write out the settings
 		""" 	
		filePointer = codecs.open(self.configFile, "w","utf-8")
		self.parser.write(filePointer)
		filePointer.close()

	def insertModuleDirectories(self):
		"""
		Created: Unknown, KP
		Description: A method that adds the programs subdirectories into the system path
		"""
		self.insertPath(self.getPath("lib"))
		self.insertPath(self.getPath("GUI"))
		self.insertPath(self.getPath("Libraries"))
		
	def processPathSettings(self):
		"""
		Created: Unknown, KP
		Description: A method that inserts the correct bin- and wrapping-folders in the system path
		"""	
		vtkdir = self.getConfigItem("VTKPath", "VTK")
		if self.getConfigItem("RemoveOldVTK", "VTK") and os.path.isdir(vtkdir):
			self.removeWithName(["vtk", "VTK", "vtk_python"])
		bin = self.getPath([vtkdir, "bin"])
		wrapping = self.getPath([vtkdir, "Wrapping", "Python"])
		self.insertPath(bin)
		self.insertPath(wrapping)
		
		
	def setConfigItem(self, configItem, section, value, write = 1):
		"""
		Created: Unknown, KP
		Description: A method that writes a setting in the confiuration, 
		creating the section for it if needed 
		"""
		self.configItems[configItem] = value
		if write:
			if self.parser.has_section(section) == False:
				self.parser.add_section(section)
			self.parser.set(section, configItem, value)
			self.writeSettings()

	def readConfigItem(self, configItem, section):
		"""
		Created: Unknown, KP
		Description: Tries to read a configuration option, returns none if it is not available 
		"""	
		try:
			configItemvalue = self.parser.get(section, configItem)
			self.configItems[configItem] = configItemvalue
		except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
			return None
		return configItemvalue
		
	def getConfigItem(self, configItem, section):
		"""
		Created: Unknown, KP
		Description: Returns configItem from the configItems list if possible
		otherwise tries to read it from the configuration
		"""	
		if not configItem in self.configItems:
			self.readConfigItem(configItem, section)
			
		if not configItem in self.configItems:
			return None
			
		return self.configItems[configItem]
		
	def readPathSettings(self):
		"""
		Created: Unknown, KP
		Description: Reads the necessary paths from the configuration file 
		"""	
		self.readConfigItem("RemoveOldVTK", "VTK")
		self.readConfigItem("VTKPath", "VTK")
		self.readConfigItem("DataPath", "Paths")
		self.readConfigItem("ImageFormat", "Output")
		self.readConfigItem("FramePath", "Paths")
		self.readConfigItem("VideoPath", "Paths")
		
	def setCurrentDir(self, path):
		"""
		Created: Unknown, KP
		Description: Sets the current directory
		"""
		self.installPath = path

	def getPath(self, path):
		"""
		Created: Unknown, KP
		Description: Returns a valid path based on the parameter  
		"""	
		if type(path) == types.StringType:
			path = [path]
		return os.path.normpath(os.path.join(self.installPath, reduce(os.path.join, path)))
	@staticmethod 	
	def removeWithName(names):
		"""
		Created: Unknown, KP
		Description: remove modules with the given names from the system path
		"""
		removethese = []
		for directory in sys.path:
			for directoryToBeRemoved in names:
				if directory.find(directoryToBeRemoved) != -1:
					removethese.append(directory)
 		for i in removethese:
 			try:
 				sys.path.remove(i)
			except ValueError:
 				Logging.info("Failed to remove ", i, kw = "init")
			
	@staticmethod		
	def insertPath(path, beforeIndex = 0):
		"""
		Created: Unknown, KP
		Description: Insert path in the system path before index n
		"""
		sys.path.insert(beforeIndex, path)

