#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

"""
 Unit: Main.py
 Project: Selli
 Created: 01.11.2004, KP
 Description:

 Main program for the LSM Module

 Modified: 03.11.2004 KP - Added the LSMApplication class to encapsulate Tk root
                           creation
           10.1.2005 KP - Changed class to use wxPython classes

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
__author__ = "Selli Project <http://sovellusprojektit.it.jyu.fi/selli/>"
__version__ = "$Revision: 1.22 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import os.path
import sys

import glob
try:
    import py2exe
    from distutils.core import setup
except:
    pass
import Configuration

#sys.path.insert(0,"C:\\Mingw\\lib")
# This will fix the VTK paths using either values from the
# configuration file, or sensible defaults
cfg=Configuration.Configuration("BioImageXD.ini")

import wx

import GUI


class LSMApplication(wx.App):
    """
    Class: LSMApplication
    Created: 03.11.2004, KP
    Description: Encapsulates the wxPython initialization and mainwindow creation
    """

    def OnInit(self):
        """
        Method: OnInit
        Created: 10.1.2005, KP
        Description: Create the application's main window
        """
        self.mainwin=GUI.MainWindow(None,-1,self)
        self.mainwin.Show(True)
        self.SetTopWindow(self.mainwin)
        return True

    def run(self):
        """
        Method: run
        Created: 03.11.2004, KP
        Description: Run the wxPython main loop
        """
        self.MainLoop()

if __name__=='__main__':

    if "py2exe" in sys.argv:
       setup(console=["Main.py"],
       data_files=[("Icons",glob.glob("Icons\\*.*")),("Binaries",glob.glob("bin\\*.*"))],
       options = {"py2exe": { "excludes": ['MayaViUserReader', 'PyShell', 'dl', 'dotblas', 'hexdump', 'libvtkCommonPython', 'libvtkFilteringPython', 'libvtkGraphicsPython', 'libvtkHybridPython', 'libvtkIOPython', 'libvtkImagingPython', 'libvtkParallelPython', 'libvtkPatentedPython', 'libvtkRenderingPython', 'mx', 'win32com.gen_py'],
       "packages": ["encodings"]}})
    else:
        # Import Psyco if available
        #try:
        #    import psyco
        #    psyco.full()
        #except ImportError:
        #    pass
        app=LSMApplication(0)
        app.run()



