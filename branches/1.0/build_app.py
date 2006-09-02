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
    import py2exe
    from distutils.core import setup
except:
    pass
import sys,os,os.path,glob

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
        DATA_FILES=[
                    ("Icons",glob.glob("Icons\\*.*")),
                    ("Bin",glob.glob("bin\\*.*")),
                    ("Help",glob.glob("Help\\*.*"))
        ]
        DATA_FILES.extend(modules)

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


