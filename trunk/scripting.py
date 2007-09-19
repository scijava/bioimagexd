# -*- coding: iso-8859-1 -*-

"""
 Unit: scripting
 Project: BioImageXD
 Created: 13.02.2006, KP
 Description:

 A module containing various shortcuts for ease of scripting the app
 
 Copyright (C) 2006	 BioImageXD Project
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

from lib.DataUnit.DataUnitSetting import DataUnitSettings
import sys
import os
import os.path
import imp
import platform
import getpass
import Logging
import ConfigParser

class MyConfigParser(ConfigParser.RawConfigParser):
	"""
	Created: KP
	Description: a config parser that doesn't ignore the case of the options and sections
	"""
	def optionxform(self, optionstr):
		"""
		Created: KP
		Description: A method used to transform the option names. Does not transform the names in any way
		"""
		return optionstr

settingsCache = {}
record = 0
conf = None

app = None
mainWindow = None
currentVisualizationMode=""
visualizer = None
processingManager = None
resamplingDisabled = 0
resampleToFit = 0
processingTimepoint = -1
wantAlphaChannel = 1
preferRGB = 1
wantWholeDataset = 0
inIO = 0
uncleanLog = None
logFile = None
recorder = None

WHOLE_DATASET			= -1
WHOLE_DATASET_NO_ALPHA	= -2
COLOR_BEGINNER = (200, 200, 200)
COLOR_INTERMEDIATE = (202, 202, 226)
COLOR_EXPERIENCED = (224, 188, 232)

dialogs = {}

def getCacheKey(paths, names, taskname):
	"""
	Created: 23.10.2006, KP
	Description: Return a key for caching of settings data based on the task name and the filepaths
	"""
	keyList = paths[:]
	keyList.append(taskname)
	keyList.extend(names)
	return tuple(keyList)

def getSettingsFromCache(key):
	"""
	Created: 23.10.2006, KP
	Description: Return the settings stored under a given key in the cache
	"""
	global settingsCache
	data = settingsCache.get(tuple(key), None)
	value = None
	parser = None
	if data:
		value = []
		for (n, configParser) in data:
			if not configParser.sections(): 
				continue
			print "n=",n,"configParser=",configParser
			print configParser.sections()
			settings = DataUnitSettings(n)
			settings.set("Type", None)
			settings = settings.readFrom(configParser)
			value.append(settings)
			parser = configParser
	return value, parser

def storeSettingsToCache(key, settingsList):
	"""
	Created: 23.10.2006, KP
	Description: Store the given settings to cache
	"""
	global settingsCache
	key = tuple(key)
	if key in settingsCache:
		del settingsCache[key]
	value = []
	for setting in settingsList:
		configParser = MyConfigParser()
		setting.writeTo(configParser)
		value.append((setting.getDatasetNumber(), configParser))
	settingsCache[key] = value



def registerDialog(dialogName, dialog):
	"""
	Created: KP
	Description: Register a dialog object with a given name. This can be used when creating
				 a script requires that a dialog be accesible from various different parts
				 of the software.
	"""
	global dialogs
	dialogs[dialogName] = dialog

def unregisterDialog(dialogName):
	"""
	Created: KP
	Description: unregister a dialog with a given name. this just removes the reference
	"""
	del dialogs[dialogName]

def main_is_frozen():
	"""
	Created: Unknown, KP
	Description: Checks if the application is "frozen", ie. packaged with py2exe for windows, py2app for mac or freeze for linux.
	"""
	return (hasattr(sys, "frozen") or # new py2exe
			hasattr(sys, "importers") # old py2exe
			or imp.is_frozen("__main__")) # tools/freeze

def get_main_dir():
	"""
	Created: Unknown, KP
	Description: Gets the main directory. Varies depending on if the app is packaged or run from source
	"""
	if "checker.py" in sys.argv[0]:
		return "."
	if main_is_frozen():
		return os.path.dirname(sys.executable)
	return os.path.dirname(sys.argv[0])
	
def get_windows_appdir():
	"""
	Created: 01.08.2007, KP
	Description: return the base directory where application settings, logs etc. should be stored on windows
	"""
	if "AppData" in os.environ:
		appbase = os.environ["AppData"]
		if not os.path.exists(appbase) and "UserProfile" in os.environ:
			appbase = os.environ["UserProfile"]
		return appbase
	
	return os.path.join("C:\\", "Documents and Settings", getpass.getuser(), "Application Data")		
	
def get_log_dir():
	"""
	Created: Unknown, KP
	Description: Tries to create and return a path to a directory for logging
	"""
	if platform.system()=="Darwin":
		return os.path.expanduser("~/Library/Logs/BioImageXD")
	elif platform.system() == "Windows":
		appbase = get_windows_appdir()
		appdir = os.path.join(appbase, "BioImageXD")
		if not os.access(appdir, os.F_OK):
			try:
				os.mkdir(appdir)
			# Probably want to except an OSError when making a directory
			except OSError:
			#except:
				pass
			if not os.access(appdir, os.F_OK):
				Logging.info("Cannot write to log application data, using current directory", kw = "io")
				appdir = "."
		
		if not os.path.exists(appdir):
			os.mkdir(appdir)
		return os.path.join(appdir, "Logs")
	else:
		appdir = os.path.expanduser("~/.BioImageXD")
		if not os.path.exists(appdir):
			os.mkdir(appdir)
		appdir = os.path.join(appdir, "Logs")
		if not os.path.exists(appdir):
			os.mkdir(appdir)
		return appdir
	
	
def get_preview_dir():
	"""
	Created: 7.11.2006, KP
	Description: Return a directory where preview images can be stored
	"""
	if platform.system() == "Darwin":
		dirpath = os.path.expanduser("~/Library/Caches/BioImageXD")
		if not os.path.exists(dirpath):
			os.mkdir(dirpath)
		return dirpath
	elif platform.system() == "Windows":
		appbase = get_windows_appdir()
		appdir = os.path.join(appbase, "BioImageXD")
		if not os.access(appdir, os.F_OK):
			try:
				os.mkdir(appdir)
			except OSError:
			#except:
				pass
			if not os.access(appdir, os.F_OK):
				Logging.info("Cannot write preview to application data, using current directory", kw = "io")
				appdir = "."
		if not os.path.exists(appdir):
			os.mkdir(appdir)
		appdir = os.path.join(appdir,"Previews")
		if not os.path.exists(appdir):
			os.mkdir(appdir)
		return appdir
	else:
		appdir = os.path.expanduser("~/.BioImageXD")
		if not os.path.exists(appdir):
			os.mkdir(appdir)
		appdir = os.path.join(appdir,"Previews")
		if not os.path.exists(appdir):
			os.mkdir(appdir)
		return appdir
	
def get_config_dir():
	"""
	Created: Unknown, KP
	Description: Returns the path to the config file
	"""
	if platform.system() == "Darwin":
		return os.path.expanduser("~/Library/Preferences")
	elif platform.system() == "Windows": 
		appbase = get_windows_appdir()
		appdir = os.path.join(appbase, "BioImageXD")
		# Check if appdir exists
		if not os.access(appdir, os.F_OK):
			try:
			# Else try to create it
				os.mkdir(appdir)
			except OSError:
			# except:
			# Probably except an OSError if we can't make the directory
				pass
			if not os.access(appdir, os.F_OK):
				appdir = "."
		if not os.path.exists(appdir):
			os.mkdir(appdir)
		return appdir
	else:
		confdir = os.path.expanduser("~/.BioImageXD")
	if not os.path.exists(confdir):
		os.mkdir(confdir)
	return confdir
#		 return get_main_dir() 

def get_help_dir():
	"""
	Created: Unknown, KP
	Description: Returns the path where help files are located
	"""
	if platform.system() == "Darwin" and main_is_frozen():
		resourcePath = os.environ['RESOURCEPATH']
		helpPath = os.path.join(resourcePath, "Help")
		return helpPath
	else:
		return os.path.join(".", "Help")
		
def get_icon_dir():
	"""
	Created: Unknown, KP
	Description: Returns the path where icons are located
	"""
	if platform.system() == "Darwin" and main_is_frozen():
		resourcePath = os.environ['RESOURCEPATH']
		iconPath = os.path.join(resourcePath, "Icons")
		return iconPath
	else:
		return os.path.join(".", "Icons")
		
		
def get_module_dir():
	"""
	Created: Unknown, KP
	Description: Returns the path where modules are located
	"""
	if platform.system() == "Darwin" and main_is_frozen():
		resourcePath = os.environ['RESOURCEPATH']
		modulePath = os.path.join(resourcePath, "Modules")
		return modulePath
	else:
		return "Modules"

