#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

"""
 Unit: Main
 Project: BioImageXD
 Created: 01.11.2004, KP
 Description:

 module for building an application bundle for windows or macos ax
 

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
except:
    pass
import sys,os,os.path,glob
import platform

EXCLUDE_FILES=["SurfaceConstruction","Reslice"]

def get_files(directory,asmodule=0):
    modules=[]
    for root,dirs,files in os.walk(directory):
        if '.svn' in dirs:dirs.remove(".svn")
        incurrent=[]
        for f in files:
            for exf in EXCLUDE_FILES:
                if exf in f:continue
            if f[-3:]==".py":
                if not asmodule:
                    incurrent.append(os.path.join(root,f))
                else:
                    f=f[:-3] # remove the .py
                    modroot=root.replace("\\",".")
                    modroot=modroot.replace("/",".")
                    modules.append(modroot+"."+f)
        if not asmodule:
           modules.append((root,incurrent))


    return modules


    


def build():
        EXCLUDES=['PyShell', 'dl', 'dotblas', 'hexdump', 'mx', 'win32com.gen_py',
        "pywin", "pywin.debugger", "pywin.debugger.dbgcon",
            "pywin.dialogs", "pywin.dialogs.list",
            "Tkconstants","Tkinter","tcl"
        ]
        # Exclude the sources because they will be packaged as plain python files
        #SOURCES=["GUI","Modules","Visualizer"]
        #EXCLUDES+=SOURCES
        incl_modules = get_files("GUI",asmodule=1)
        incl_modules.extend(get_files("Visualizer",asmodule=1))
        incl_modules.extend(get_files("lib",asmodule=1))
        incl_modules.extend(["wx.lib.mixins.listctrl"])
        print "Included modules=",incl_modules
        modules = get_files("Modules")
	iconFiles = os.path.join("Icons","*.*")
	binFiles = os.path.join("bin","*.*")
	helpFiles = os.path.join("Help","*.*")
        DATA_FILES=[
                    ("Icons",glob.glob(iconFiles)),
                    ("Bin",glob.glob(binFiles)),
                    ("Help",glob.glob(helpFiles))
        ]
        DATA_FILES.extend(modules)

        if platform.system() == "Darwin":
		import py2app
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
			iconfile='Icons/BioImageXD.icns',
			excludes = EXCLUDES,
			includes = incl_modules,
			packages = ["encodings"]
	        )
		DATA_FILES.append( ('../Frameworks', [
			'/usr/local/lib/wxPython-unicode-2.5.5.1/lib/libwx_macud-2.5.5.rsrc',
		]))
                setup(
				app=['BioImageXD.py'],
				data_files = DATA_FILES, 
				options = dict( py2app = py2app_options )
		)
		
        elif platform.system() == "Linux":
		# freeze code
		file = "/usr/share/doc/python2.4/examples/Tools/freeze/freeze.py"
		excl=""
		for x in EXCLUDES:
		    excl+=" -x %s"%x
		    
		mods=" ".join(incl_modules)
	        cmd_line="python %s -o  linux-build %s BioImageXD.py -m %s"%(file,excl,mods)
		print cmd_line
		os.system(cmd_line)
		
	elif platform.system() == "Windows":
	       		import py2exe

			# use windows=[{... to not show the console
			# use console=[{ to show the console
			setup(name="BioImageXD",
				   windows=[{"script":"BioImageXD.py",
							 "icon_resources": [(1, "Icons\\logo.ico")]} ],
				   data_files = DATA_FILES,
				   options = {"py2exe":
							 { "excludes": EXCLUDES,
							   "includes":incl_modules,
							   "packages": ["encodings"]}},
				   zipfile = "python_libs.zip")

