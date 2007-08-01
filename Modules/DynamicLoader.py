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
mcache = {}

def getRenderingModules(callback = None):
	"""
	Created: Unknown, KP
	Description: Helper method for getting the Rendering modules
	"""
	return getModules("Rendering", callback = callback, moduleType = "3D rendering module")

def getVisualizationModes(callback = None):
	"""
	Created: Unknown, KP
	Description: Helper method for getting the Visualization modules
	"""
	return getModules("Visualization", callback = callback, moduleType = "")

def getReaders(callback = None):
	"""
	Created: Unknown, KP
	Description: Helper method for getting the Reader modules
	"""
	return getModules("Readers", callback = callback, moduleType = "Image format reader")

def getTaskModules(callback = None):
	"""
	Created: Unknown, KP
	Description: Helper method for getting the Task modules
	"""
	return getModules("Task", "*", callback = callback, moduleType = "Task module")

# One problem with ignore is that it does not care about the directory of the module.
# We can't load ModuleDir1/ModuleName.py and ignore ModuleDir2/ModuleName.py at the same time.

ignore = ["ScaleBar.py", "Spline.py", "ArbitrarySlicer.py"]

def _removeIgnoredModules(moduleNameList):
	"""
	Created: 18.06.2007, SG
	Description: Helper method for removing the modules to ignore from a list of method names
	"""
	toRemoveList = []
	for fileName in moduleNameList:
		for ignoreName in ignore:
			if ignoreName == os.path.basename(fileName):
				toRemoveList.append(fileName)
	for moduleName in toRemoveList:
		moduleNameList.remove(moduleName)
	return moduleNameList

def _createGlobPathAndSysPath(moduleSubDir, globExtension):
	"""
	Created: 19.06.2007, SG
	Description: Creates a path to be used in a glob expression and a path to add to sys.path
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

def _createModuleNameToLoad(modulePathWithExtension):
	"""
	Created: 19.06.2007, SG
	Description: Takes a path to a module or a path to a package. If the path ends with .py this extension is removed.
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

def getModules(moduleSubDir, globExtension = "*.py", callback = None, moduleType = "Module"):
	"""
	Created: 02.07.2005, KP
	Description: Loads dynamically classes in a directory and returns a dictionary that contains information about
	them. The return directory will contain entries like:
	moddict["BXCDataSource"] -> (moduleClass, settingClass, loadedModule)
	"""    
	globPath, pathForSysPath = _createGlobPathAndSysPath(moduleSubDir, globExtension)
	modulePathList = glob.glob(globPath)
	modulePathList = _removeIgnoredModules(modulePathList)
	Logging.info("Modules from path %s are %s" % (globPath, str(modulePathList)), kw = "modules")
	# Add ModuleDirectory/RequestedModuleDirectory to sys.path
	#print "Adding", pathForSysPath, "to sys.path"
	#print "sys.path is now", sys.path
	sys.path.append(pathForSysPath)
	global mcache
	# Return cached result, if it exists
	if moduleSubDir in mcache:
		return mcache[moduleSubDir]
	moddict = {}
	for modulePathWithExtension in modulePathList:
		moduleName = _createModuleNameToLoad(modulePathWithExtension)
		try:
			#print "__import__(%s, globals(), locals(), [])" % moduleName
			loadedModule = __import__(moduleName, globals(), locals(), [])
		except ImportError:
			print "Failed to load module:", moduleName
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
		Logging.info("Using" + moduleNameInDictionary + "as name", kw = "modules")
		if callback:
			callback("Loading %s %s..." % (moduleType, moduleNameInDictionary))
		moduleClass = loadedModule.getClass()
		settingClass = None
		if hasattr(loadedModule, "getConfigPanel"):
			settingClass = loadedModule.getConfigPanel()
		moddict[moduleNameInDictionary] = (moduleClass, settingClass, loadedModule)
	mcache[moduleSubDir] = moddict
	return moddict
