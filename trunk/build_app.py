#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

"""
 Unit: Main
 Project: BioImageXD
 Created: 01.11.2004, KP
 Description:

 Module for building an application bundle for Windows or MacOS X

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
__version__ = "$Revision: 1.22 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

try:
	from distutils.core import setup
except ImportError, importError:
	print importError
import os, os.path, glob
import platform

excludeFiles = ["SurfaceConstruction", "Reslice"]

def get_files(directory, asmodule=0):
	"""
	Created: Unknown date, KP
	Description: Get all files from a directory, excluding SVN files
	Docstring: 15.06.2007 twikstro
	"""
	modules = []
	for root, dirs, files in os.walk(directory):
		if '.svn' in dirs:
			dirs.remove(".svn")
		incurrent = []
		for currFile in files:
			for exf in excludeFiles:
				if exf in currFile:
					continue
			if currFile[-3:] == ".py":
				if not asmodule:
					incurrent.append(os.path.join(root, currFile))
				else:
					currFile = currFile[:-3] # remove the .py
					modroot = root.replace("\\",".")
					modroot = modroot.replace("/",".")
					modules.append(modroot+"."+currFile)
		if not asmodule:
			modules.append((root, incurrent))
	return modules

def build():
	"""
	Created: Unknown date, KP
	Description: Builds the appropriate command-line options 
	Docstring: 15.06.2007 twikstro
	"""
	print "build()"
	excludeList = ['PyShell', 'dl', 'dotblas', 'hexdump', 'mx', 'win32com.gen_py',
	"pywin", "pywin.debugger", "pywin.debugger.dbgcon",
	"pywin.dialogs", "pywin.dialogs.list",
	"Tkconstants", "Tkinter", "tcl", "tcl84", "tk84", "qt-mt3", "itkExtras", "itk",
	"itkBase ", "itkConfig", "itkLazy", "itkTemplates", "itkTypes"
	]
	# Exclude the sources because they will be packaged as plain python files
	#SOURCES=["GUI","Modules","Visualizer"]
	#excludeList+=SOURCES
	incl_modules = get_files("GUI", asmodule=1)
	incl_modules.extend(get_files("Visualizer", asmodule=1))
	incl_modules.extend(get_files("lib", asmodule=1))
	incl_modules.extend(["wx.lib.mixins.listctrl"])
	incl_modules.extend(["wx.grid", "email","Image"])
	print "Included modules=", incl_modules
	modules = get_files("Modules")
	iconFiles = os.path.join("Icons","*.*")
	binFiles = os.path.join("bin","*.*")
	helpFiles = os.path.join("Help","*.*")
	dataFiles = [
				("Icons",glob.glob(iconFiles)),
				("Bin",glob.glob(binFiles)),
				("Help",glob.glob(helpFiles))
	]
	dataFiles.extend(modules)

	if platform.system() == "Darwin":
		import py2app
		# A custom plist for letting it associate with all files.
		pList = dict(CFBundleDocumentTypes=[dict(CFBundleTypeExtensions=["lsm"],
									 CFBundleTypeName="Carl Zeiss LSM file",
									 CFBundleTypeRole="Viewer"),
									 dict(CFBundleTypeExtensions=["bxd"],
									 CFBundleTypeName="BioImageXD Data file",
									 CFBundleTypeRole="Editor"),
									 dict(CFBundleTypeExtensions=["oif"],
									 CFBundleTypeName="Olympus OIF file",
									 CFBundleTypeRole="Viewer"),
								]
		 )
		# Note that you must replace hypens '-' with underscores '_'
		# when converting option names from the command line to a script.
		# For example, the --argv-emulation option is passed as 
		# argv_emulation in an options dict.
		py2app_options = dict(
		# Map "open document" events to sys.argv.
		# Scripts that expect files as command line arguments
		# can be trivially used as "droplets" using this option.
		# Without this option, sys.argv should not be used at all
		# as it will contain only Mac OS X specific stuff.
		argv_emulation=True,
			# This is a shortcut that will place MyApplication.icns
			# in the Contents/Resources folder of the application bundle,
		# and make sure the CFBundleIcon plist key is set appropriately.
		iconfile = 'Icons/BioImageXD.icns',
		plist = pList, 
		excludes = excludeList,
		includes = incl_modules,
		packages = ["encodings"],
		)
		dataFiles.append("/Library/Frameworks/Python.framework/Versions/2.5/lib/InsightToolkit")
		#dataFiles.append( ('../Frameworks', [
		#'/usr/local/lib/wxPython-unicode-2.5.5.1/lib/libwx_macud-2.5.5.rsrc',
		#appending the .rsrc file no longer needed in wx2.6
		#'/opt/intel/cc/9.1.027/lib/libguide.dylib',
		#this get the libguide.dylib into Frameworks but the app doenst see it.
		#sometihng to do with DLYD env vars set by intel script at 
		#/opt/intel/cc/9.1.024/bin/iccvars.sh which must be sourced before
		#using intel compilers, and before python2.4 BioImageXD.py works
		#Maybe dont need this if libguide install name is set correctly to its acrualy path
		#using install_name_tool -id old new]))
		setup(
			app=['BioImageXD.py'],
			data_files = dataFiles, 
			options = dict( py2app = py2app_options )
		)		 

	elif platform.system() == "Windows":
		# importing py2exe causes the windows specific magic to take place
		import py2exe


		# use windows=[{... to not show the console
		# use console=[{ to show the console
		setup(name="BioImageXD",
			   windows=[{"script":"BioImageXD.py",
			   #console=[{"script":"BioImageXD.py",
						 "icon_resources": [(1, "Icons\\logo.ico")]} ],
			   data_files = dataFiles,
			   options = {"py2exe":
						 { "excludes": excludeList,
						   "includes": incl_modules,
						   "packages": ["encodings"]}},
			   zipfile = "python_libs.zip")
