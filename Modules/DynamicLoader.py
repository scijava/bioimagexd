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
import traceback

PLOADER = None
def getPluginLoader():
	global PLOADER
	if not PLOADER:
		PLOADER = PluginLoader()
	return PLOADER

class PluginLoader:
	def __init__(self):
		self.mcache = {}
		# One problem with ignore is that it does not care about the directory of the module.
		# We can't load ModuleDir1/ModuleName.py and ignore ModuleDir2/ModuleName.py at the same time.
		self.ignore = ["Modules/Rendering/ScaleBar.py", "Modules/Rendering/Spline.py", "Modules/Rendering/ArbitrarySlicer.py", "Modules/Task/__init__.py", "Modules/Filters/GradientMagnitudeITK.py", "Modules/Filters/ImplicitModelling.py", "Modules/Filters/Watershed.py"]
		
		self.moduleTypes = {"Filters":"*", "Task":"*"}
		
	def getPluginModule(self, variety, name):
		"""
		return a plugin module of a given type with the given name
		"""
		return self.getPluginItem(variety, name, 2)
		
	def getPluginClass(self, variety, name):
		"""
		return a plugin class of a given type with the given name
		"""
		return self.getPluginItem(variety, name, 0)
		
	def getPluginItem(self, variety, name, entry):
		"""
		return the selected entry from the module table
		"""
		if not variety in self.mcache:
			self.getModules(variety)
		if name in self.mcache[variety]:
			return self.mcache[variety][name][entry]
		else:
			raise Exception(""+name,"not in",self.mcache[variety].keys())
			
	def _removeIgnoredModules(self, moduleNameList):
		"""
		Helper method for removing the modules to ignore from a list of method names
		"""
		toRemoveList = []
		for fileName in moduleNameList:

			fixedFileName = fileName
			if os.path.sep != '/':
				fixedFileName = fileName.replace(os.path.sep, '/')
			for ignoreName in self.ignore:
				#if ignoreName == os.path.basename(fileName):
				if ignoreName == fixedFileName:
					toRemoveList.append(fileName)
		for moduleName in toRemoveList:
			moduleNameList.remove(moduleName)
		return moduleNameList
	
	def _createGlobPathAndSysPath(self, moduleSubDir, globExtension):
		"""
		Creates a path to be used in a glob expression and a path to add to sys.path
		so that modules that the glob expression will fetch can be imported. Returns these in a tuple:
		(globPath, pathForSysPath)
		Ex. ("moduleSubDir = Readers, globExtension = *.py") -> (Modules/Readers/*.py, Modules/Readers)
		"""
		# Create list of Module-files to load based on extension
		modulePath = scripting.get_module_dir()
		Logging.info("Module dir=%s" % modulePath, kw = "modules")
		pathForSysPath = os.path.join(modulePath, moduleSubDir)
		globPath = pathForSysPath
		if globExtension:
			globPath = os.path.join(globPath, globExtension)
		Logging.info("Path to modes: %s" % pathForSysPath, kw = "modules")
		return globPath, pathForSysPath
	
	def _createModuleNameToLoad(self, modulePathWithExtension):
		"""
		Takes a path to a module or a path to a package. If the path ends with .py this extension is removed.
		The "/" and "\" in the path are changed to ".". However only the last part of the module name is required.
		Example "Modules/Readers/BioradDataSource.py" -> "BioradDataSource"
		"""
		moduleName = modulePathWithExtension
		if modulePathWithExtension.endswith(".py"):
			moduleName = modulePathWithExtension[:-3]
			Logging.info("modulePathWithExtension %s corresponds to %s" %
					(moduleName, modulePathWithExtension), kw = "modules")
		moduleName = moduleName.replace("/", ".")
		moduleName = moduleName.replace("\\", ".")
		moduleNameParts = moduleName.split(".")
		moduleName = moduleNameParts[-1]
		fromPath = ".".join(moduleNameParts[:-1])
		Logging.info("Importing %s = %s from %s" % (modulePathWithExtension, moduleName, fromPath), kw = "modules")
		return moduleName
	
	def getModules(self, moduleSubDir, globExtension = None, callback = None, moduleType = "Module", classEndsWith = ""):
		"""
		Dynamically loads classes in a directory and returns a dictionary that contains information about
		them. The returned directory will contain entries like:
		moddict["BXCDataSource"] -> (moduleClass, settingClass, loadedModule)
		The method adds a relative path with the dir that contains the modules to load, to sys.path. It then uses
		__import__ to load them with their basenames. This means that the dynamic loading relies on the current working
		directory being set to the "main source	dir".
		"""    
		if not globExtension:
			globExtension = self.moduleTypes.get(moduleSubDir,"*.py")
		globPath, pathForSysPath = self._createGlobPathAndSysPath(moduleSubDir, globExtension)
		modulePathList = glob.glob(globPath)
		modulePathList = self._removeIgnoredModules(modulePathList)
		Logging.info("Modules from path %s are %s" % (globPath, str(modulePathList)), kw = "modules")
		sys.path.insert(0, pathForSysPath)
		# Return cached result, if it exists
		if moduleSubDir in self.mcache:
			return self.mcache[moduleSubDir]
		moddict = {}
		for modulePathWithExtension in modulePathList:
			if modulePathWithExtension.endswith(".pyc"):
				continue
			moduleName = self._createModuleNameToLoad(modulePathWithExtension)
			try:
				loadedModule = __import__(moduleName, globals(), locals(), [])
			except ImportError:
				traceback.print_exc()
				Logging.info("Failed to load module %s" % moduleName, kw = "modules")
				continue
			moduleNameInDictionary = None
			# Try to set the moduleName first from getName, then getShortDesc, finally setting it to mod
			# if these don't exist
			try:
				moduleNameInDictionary = loadedModule.getName()
			except AttributeError:
				try:
					moduleNameInDictionary = loadedModule.getShortDesc()
				except AttributeError:
					moduleNameInDictionary = moduleName
			if callback:
				callback("Loading %s %s..." % (moduleType, moduleNameInDictionary))
			if hasattr(loadedModule, "getClass"):
				moduleClass = loadedModule.getClass()
			else:
				try:
					moduleClass = loadedModule.__dict__["%s%s"%(moduleName,classEndsWith)]
				except:
					continue
			settingClass = None
			if hasattr(loadedModule, "getConfigPanel"):
				settingClass = loadedModule.getConfigPanel()
			moddict[moduleNameInDictionary] = (moduleClass, settingClass, loadedModule)
		self.mcache[moduleSubDir] = moddict
		return moddict
	
def getRenderingModules(callback = None):
	"""
	Helper method for getting the Rendering modules
	"""
	pl = getPluginLoader()
	return pl.getModules("Rendering", callback = callback, moduleType = "3D rendering module")
	
def getFilterModules(callback = None):
	"""
	Return the filter modules for use in process task and similiar
	"""
	pl = getPluginLoader()
	return pl.getModules("Filters",callback = callback, moduleType = "Image processing filters", classEndsWith = "Filter")

def getVisualizationModes(callback = None):
	"""
	Helper method for getting the Visualization modules
	"""
	pl = getPluginLoader()	
	return pl.getModules("Visualization", callback = callback, moduleType = "")

def getReaders(callback = None):
	"""
	Helper method for getting the Reader modules
	"""
	pl = getPluginLoader()
	return pl.getModules("Readers", callback = callback, moduleType = "Image format reader")

def getTaskModules(callback = None):
	"""
	Helper method for getting the Task modules
	"""
	pl = getPluginLoader()
	return pl.getModules("Task", callback = callback, moduleType = "Task module")

