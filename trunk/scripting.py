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

import sys, os, os.path
import imp
import platform
import getpass
import vtk
import pickle
import ConfigParser
import Logging

import optimize as mem

from optimize import execute_limited

import Configuration

class MyConfigParser(ConfigParser.RawConfigParser):
	def optionxform(self, optionstr):
		return optionstr

settingsCache = {}

def getCacheKey(paths, names, taskname):
	"""
	Created: 23.10.2006, KP
	Description: Return a key for caching of settings data based on the task name and the filepaths
	"""
	lst = paths[:]
	lst.append(taskname)
	lst.extend(names)
	return tuple(lst)

def getSettingsFromCache(key):
	"""
	Created: 23.10.2006, KP
	Description: Return the settings stored under a given key in the cache
	"""
	global settingsCache
	from lib import DataUnit
	data = settingsCache.get(tuple(key), None)
	value = None
	parser = None
	if data:
		value = []
		for (n, cp) in data:
		  
			#value=pickle.loads(data)
			
			settings = DataUnit.DataUnitSettings(n)            
			settings.set("Type", None)
			#settings = eval(settingsclass)
			settings = settings.readFrom(cp)
			value.append(settings)
			parser = cp
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
	for i, setting in enumerate(settingsList):
		cp = MyConfigParser()
		setting.writeTo(cp)
		value.append((setting.n, cp))
		
	
	settingsCache[key] = value
	

record = 0
conf = None

app = None
mainWindow = None
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

WHOLE_DATASET           = -1
WHOLE_DATASET_NO_ALPHA  = -2
COLOR_BEGINNER = (200, 200, 200)
COLOR_INTERMEDIATE = (202, 202, 226)
COLOR_EXPERIENCED = (224, 188, 232)

dialogs = {}

def registerDialog(name, dlg):
	global dialogs
	dialogs[name] = dlg
	
def unregisterDialog(name):
	del dialogs[name]


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
	if platform.system() == "Darwin":
		return os.path.expanduser("~/Library/Logs/BioImageXD")
	elif platform.system() == "Windows":
		if "AppData" in os.environ:
			appbase = os.environ["AppData"]
		else:
			appbase = os.path.join("C:\\", "Documents and Settings", getpass.getuser(), "Application Data")
		appdir = os.path.join(appbase, "BioImageXD")
		if not os.access(appdir, os.F_OK):
			try:
				os.mkdir(appdir)
			except:
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
		if "AppData" in os.environ:
			appbase = os.environ["AppData"]
		else:
			appbase = os.path.join("C:\\", "Documents and Settings", getpass.getuser(), "Application Data")
		appdir = os.path.join(appbase, "BioImageXD")
		if not os.access(appdir, os.F_OK):
			try:
				os.mkdir(appdir)
			except:
				pass
			if not os.access(appdir, os.F_OK):
				 Logging.info("Cannot write preview to application data, using current directory", kw = "io")
				 appdir = "."
		
		if not os.path.exists(appdir):
			os.mkdir(appdir)
		appdir = os.path.join(appdir, "Previews")
		if not os.path.exists(appdir):
			os.mkdir(appdir)
		return appdir
	else:
		appdir = os.path.expanduser("~/.BioImageXD")
		if not os.path.exists(appdir):
			os.mkdir(appdir)
		appdir = os.path.join(appdir, "Previews")
		if not os.path.exists(appdir):
			os.mkdir(appdir)
		return appdir
	
def get_config_dir():
	if platform.system() == "Darwin":
		return os.path.expanduser("~/Library/Preferences")
	elif platform.system() == "Windows": 
		if "AppData" in os.environ:
			appbase = os.environ["AppData"]
		else:
			appbase = os.path.join("C:\\", "Documents and Settings", getpass.getuser(), "Application Data")
		appdir = os.path.join(appbase, "BioImageXD")
		if not os.access(appdir, os.F_OK):
			try:
				os.mkdir(appdir)
			except:
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
#        return get_main_dir() 

def get_help_dir():
	if platform.system() == "Darwin" and main_is_frozen():
		dir = os.environ['RESOURCEPATH']
		path = os.path.join(dir, "Help")
		return path
	else:
		return os.path.join(".", "Help")
		
	
		
def get_icon_dir():
	if platform.system() == "Darwin" and main_is_frozen():
		dir = os.environ['RESOURCEPATH']
		path = os.path.join(dir, "Icons")
		return path
	else:
		return os.path.join(".", "Icons")
		
		
def get_module_dir():
	if platform.system() == "Darwin" and main_is_frozen():
		dir = os.environ['RESOURCEPATH']
		path = os.path.join(dir, "Modules")
		return path
	else:
		return "Modules"

